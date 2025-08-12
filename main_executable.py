"""
USDT/KRW 자동매매 프로그램 - EXE 실행 파일용 메인
exe 패키징에 최적화된 메인 실행 파일
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import signal
import traceback

# exe 실행 시 경로 설정
if getattr(sys, 'frozen', False):
    # PyInstaller로 패키징된 경우
    app_dir = Path(sys.executable).parent
    sys.path.insert(0, str(app_dir))
else:
    # 개발 환경
    app_dir = Path(__file__).parent
    sys.path.insert(0, str(app_dir))

# 로그 디렉토리 생성
logs_dir = app_dir / "logs"
logs_dir.mkdir(exist_ok=True)

# 설정 관리자 import
from config_manager import get_config

# 설정 로드
config = get_config()
api_config = config.get_api_config()
trading_config = config.get_trading_config()
system_config = config.get_system_config()

# 로깅 설정
log_file = logs_dir / "trading_bot.log"
logging.basicConfig(
    level=getattr(logging, api_config['log_level'], logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 프로젝트 모듈 import
try:
    from src.api.coinone_client import CoinoneClient
    from src.indicators.rsi import RSICalculator
    from src.indicators.ema import EMACalculator
    from src.strategy.trading_strategy import TradingStrategy
    from src.strategy.position_manager import PositionManager
    from backtest.improved_backtest_engine import ImprovedTradingStrategy
    from backtest.backtest_engine import BacktestConfig, Position
except ImportError as e:
    logger.error(f"필수 모듈 import 실패: {e}")
    input("아무 키나 누르면 종료합니다...")
    sys.exit(1)

# 상태 머신 정의
from enum import Enum

class TradingState(Enum):
    WAITING_FOR_SIGNAL = "신호대기"
    POSITION_HELD = "포지션보유"
    ERROR = "오류상태"

class TradingStateMachine:
    """거래 상태 머신"""
    def __init__(self):
        self.current_state = TradingState.WAITING_FOR_SIGNAL
    
    def transition_to(self, new_state: TradingState):
        """상태 전환"""
        old_state = self.current_state
        self.current_state = new_state
        logger.info(f"상태 전환: {old_state.value} -> {new_state.value}")


class USDTKRWTradingBot:
    """USDT/KRW 자동매매 봇 - EXE 버전"""
    
    def __init__(self):
        """봇 초기화"""
        self.running = False
        
        # 설정 유효성 검사
        if not api_config['dry_run'] and not config.validate_api_keys():
            logger.error("실거래 모드인데 API 키가 설정되지 않았습니다!")
            input("config.ini 파일에 API 키를 설정하고 다시 실행해주세요. 아무 키나 누르면 종료합니다...")
            sys.exit(1)
        
        # API 클라이언트 초기화
        try:
            os.environ['COINONE_ACCESS_TOKEN'] = api_config['access_token']
            os.environ['COINONE_SECRET_KEY'] = api_config['secret_key']
            self.client = CoinoneClient()
        except Exception as e:
            logger.error(f"API 클라이언트 초기화 실패: {e}")
            input("아무 키나 누르면 종료합니다...")
            sys.exit(1)
        
        # 전략 설정
        self.config = BacktestConfig(
            rsi_period=trading_config['rsi_period'],
            ema_period=trading_config['ema_period'],
            rsi_slope_periods=trading_config['rsi_slope_periods'],
            ema_slope_thresholds=trading_config['ema_slope_thresholds'],
            profit_target=trading_config['profit_target'],
            max_hold_hours=trading_config['max_hold_hours'],
            rsi_overbought=trading_config['rsi_overbought']
        )
        
        # 전략 초기화
        self.strategy = ImprovedTradingStrategy(self.config)
        
        # 상태 머신 초기화
        self.state_machine = TradingStateMachine()
        
        # 현재 포지션 정보
        self.position = {
            'is_open': False,
            'avg_price': 0.0,
            'quantity': 0.0,
            'entry_time': None
        }
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        mode_text = "모의거래" if api_config['dry_run'] else "실거래"
        logger.info(f"Trading Bot 초기화 완료 (모드: {mode_text})")
    
    def _signal_handler(self, signum, frame):
        """종료 시그널 처리"""
        logger.info("종료 신호 받음. 안전하게 종료합니다...")
        self.running = False
    
    def get_market_data(self, hours: int = 100) -> Optional[dict]:
        """최근 시장 데이터 조회"""
        try:
            # 캔들 데이터 조회
            candles = self.client.get_candles(
                currency='usdt',
                interval='1h',
                limit=hours
            )
            
            if not candles:
                logger.error("캔들 데이터를 가져올 수 없습니다")
                return None
            
            # 지표 계산을 위한 데이터 준비
            import pandas as pd
            df = pd.DataFrame(candles)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('timestamp')
            
            # 지표 계산
            df_with_indicators = self.strategy.calculate_indicators(df)
            
            return df_with_indicators
            
        except Exception as e:
            logger.error(f"시장 데이터 조회 실패: {e}")
            return None
    
    def check_buy_signal(self, df) -> bool:
        """매수 신호 확인"""
        if len(df) < 20:
            return False
        
        # 최신 데이터로 매수 조건 확인
        return self.strategy.check_buy_conditions(df, len(df) - 1)
    
    def check_sell_signal(self, df) -> tuple:
        """매도 신호 확인"""
        if not self.position['is_open']:
            return False, ""
        
        # Position 객체 생성
        pos = Position()
        pos.is_open = True
        pos.avg_price = self.position['avg_price']
        pos.quantity = self.position['quantity']
        pos.entry_time = self.position['entry_time']
        
        return self.strategy.check_sell_conditions(df, len(df) - 1, pos)
    
    def execute_buy(self, price: float):
        """매수 실행"""
        try:
            # 계좌 잔고 조회
            balance = self.client.get_balance()
            krw_balance = float(balance.get('krw', {}).get('available', 0))
            
            if krw_balance < 10000:  # 최소 1만원
                logger.warning(f"잔고 부족: {krw_balance}원")
                return False
            
            # 매수 수량 계산 (전액 매수)
            quantity = krw_balance / price * 0.999  # 0.1% 여유
            quantity = round(quantity, 4)  # 소수점 4자리까지
            
            logger.info(f"매수 시도: 가격 {price}원, 수량 {quantity}개")
            
            if api_config['dry_run']:
                logger.info("[모의거래] 매수 주문 성공")
                self.position = {
                    'is_open': True,
                    'avg_price': price,
                    'quantity': quantity,
                    'entry_time': datetime.now()
                }
                self.state_machine.transition_to(TradingState.POSITION_HELD)
                return True
            else:
                # 실제 매수 주문
                order = self.client.place_order(
                    currency='usdt',
                    side='buy',
                    order_type='limit',
                    price=str(price),
                    quantity=str(quantity)
                )
                
                if order and order.get('result') == 'success':
                    logger.info(f"매수 주문 성공: {order}")
                    self.position = {
                        'is_open': True,
                        'avg_price': price,
                        'quantity': quantity,
                        'entry_time': datetime.now()
                    }
                    self.state_machine.transition_to(TradingState.POSITION_HELD)
                    
                    # 즉시 익절 주문
                    self.place_profit_target_order()
                    return True
                else:
                    logger.error(f"매수 주문 실패: {order}")
                    return False
                    
        except Exception as e:
            logger.error(f"매수 실행 오류: {e}")
            return False
    
    def execute_sell(self, price: float, reason: str):
        """매도 실행"""
        try:
            if not self.position['is_open']:
                return False
            
            quantity = self.position['quantity']
            logger.info(f"매도 시도: 가격 {price}원, 수량 {quantity}개, 이유: {reason}")
            
            if api_config['dry_run']:
                logger.info("[모의거래] 매도 주문 성공")
                # 손익 계산
                pnl = (price - self.position['avg_price']) * quantity
                pnl_pct = (pnl / (self.position['avg_price'] * quantity)) * 100
                logger.info(f"손익: {pnl:.0f}원 ({pnl_pct:.2f}%)")
                
                self.position = {
                    'is_open': False,
                    'avg_price': 0.0,
                    'quantity': 0.0,
                    'entry_time': None
                }
                self.state_machine.transition_to(TradingState.WAITING_FOR_SIGNAL)
                return True
            else:
                # 실제 매도 주문
                order_type = 'limit' if reason == '익절' else 'market'
                order = self.client.place_order(
                    currency='usdt',
                    side='sell',
                    order_type=order_type,
                    price=str(price) if order_type == 'limit' else None,
                    quantity=str(quantity)
                )
                
                if order and order.get('result') == 'success':
                    logger.info(f"매도 주문 성공: {order}")
                    # 손익 계산
                    pnl = (price - self.position['avg_price']) * quantity
                    pnl_pct = (pnl / (self.position['avg_price'] * quantity)) * 100
                    logger.info(f"손익: {pnl:.0f}원 ({pnl_pct:.2f}%)")
                    
                    self.position = {
                        'is_open': False,
                        'avg_price': 0.0,
                        'quantity': 0.0,
                        'entry_time': None
                    }
                    self.state_machine.transition_to(TradingState.WAITING_FOR_SIGNAL)
                    return True
                else:
                    logger.error(f"매도 주문 실패: {order}")
                    return False
                    
        except Exception as e:
            logger.error(f"매도 실행 오류: {e}")
            return False
    
    def place_profit_target_order(self):
        """익절 주문 설정"""
        if not self.position['is_open']:
            return
        
        profit_target_price = self.position['avg_price'] + self.config.profit_target
        quantity = self.position['quantity']
        
        logger.info(f"익절 주문 설정: {profit_target_price}원")
        
        if not api_config['dry_run']:
            # 실제 익절 주문
            order = self.client.place_order(
                currency='usdt',
                side='sell',
                order_type='limit',
                price=str(profit_target_price),
                quantity=str(quantity)
            )
            
            if order and order.get('result') == 'success':
                logger.info(f"익절 주문 성공: {order}")
            else:
                logger.error(f"익절 주문 실패: {order}")
    
    def run_trading_loop(self):
        """메인 거래 루프"""
        self.running = True
        logger.info("자동매매 시작...")
        
        while self.running:
            try:
                # 시장 데이터 조회
                df = self.get_market_data()
                if df is None or len(df) == 0:
                    logger.warning("시장 데이터를 가져올 수 없습니다")
                    time.sleep(system_config['check_interval'])
                    continue
                
                current_price = df.iloc[-1]['close']
                
                # 현재 상태에 따른 처리
                current_state = self.state_machine.current_state
                
                if current_state == TradingState.WAITING_FOR_SIGNAL:
                    # 매수 신호 확인
                    if self.check_buy_signal(df):
                        logger.info("매수 신호 감지!")
                        # 매도1호가 조회
                        orderbook = self.client.get_orderbook('usdt')
                        if orderbook:
                            buy_price = float(orderbook['asks'][0]['price'])
                            self.execute_buy(buy_price)
                
                elif current_state == TradingState.POSITION_HELD:
                    # 매도 신호 확인
                    should_sell, reason = self.check_sell_signal(df)
                    if should_sell:
                        logger.info(f"매도 신호 감지: {reason}")
                        self.execute_sell(current_price, reason)
                
                # 상태 출력
                print(f"\r현재 상태: {current_state.value}, 가격: {current_price}원", end="")
                if self.position['is_open']:
                    unrealized_pnl = (current_price - self.position['avg_price']) * self.position['quantity']
                    print(f", 포지션: {self.position['quantity']:.4f}개@{self.position['avg_price']:.0f}원, 미실현P&L: {unrealized_pnl:.0f}원", end="")
                
                # 대기
                time.sleep(system_config['check_interval'])
                
            except KeyboardInterrupt:
                logger.info("사용자에 의해 중단됨")
                break
            except Exception as e:
                logger.error(f"거래 루프 오류: {e}")
                logger.error(traceback.format_exc())
                time.sleep(system_config['check_interval'])
        
        logger.info("자동매매 종료")


def print_banner():
    """프로그램 배너 출력"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                          TEDER BOT - 코인원 자동매매                          ║
║                               USDT/KRW 거래봇                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """메인 함수"""
    print_banner()
    
    # 설정 확인
    print("설정 확인 중...")
    print(f"- 모드: {'모의거래' if api_config['dry_run'] else '실거래'}")
    print(f"- 로그 레벨: {api_config['log_level']}")
    print(f"- RSI 기간: {trading_config['rsi_period']}")
    print(f"- EMA 기간: {trading_config['ema_period']}")
    print(f"- 익절 목표: +{trading_config['profit_target']}원")
    print(f"- 최대 보유시간: {trading_config['max_hold_hours']}시간")
    print(f"- 체크 주기: {system_config['check_interval']}초")
    print()
    
    # 실거래 경고
    if not api_config['dry_run']:
        print("*" * 80)
        print("* 경고: 실거래 모드로 실행됩니다!")
        print("* 실제 자금으로 거래가 실행됩니다!")
        print("* 계속하시려면 10초 후 시작됩니다...")
        print("* 중단하시려면 Ctrl+C를 누르세요.")
        print("*" * 80)
        
        try:
            for i in range(10, 0, -1):
                print(f"\r{i}초 후 시작... ", end="", flush=True)
                time.sleep(1)
            print("\n시작합니다!")
        except KeyboardInterrupt:
            print("\n사용자에 의해 취소되었습니다.")
            return
    else:
        print("모의거래 모드로 실행합니다. 5초 후 시작...")
        time.sleep(5)
    
    # 봇 실행
    bot = USDTKRWTradingBot()
    
    try:
        bot.run_trading_loop()
    except Exception as e:
        logger.error(f"프로그램 오류: {e}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("프로그램 종료")
        input("아무 키나 누르면 종료합니다...")


if __name__ == "__main__":
    main()