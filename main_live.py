"""
USDT/KRW 자동매매 프로그램 - 실거래 버전
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import pandas as pd

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from src.api.coinone_client import CoinoneClient
from src.indicators.rsi import RSICalculator
from src.indicators.ema import EMACalculator
from backtest.backtest_engine import BacktestConfig

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/live_trading.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LiveTradingBot:
    """실거래 USDT/KRW 자동매매 봇"""
    
    def __init__(self, dry_run: bool = True):
        """
        Args:
            dry_run: True면 모의거래, False면 실거래
        """
        self.dry_run = dry_run
        self.client = CoinoneClient()
        self.config = BacktestConfig()
        
        # 지표 계산기
        self.rsi_calc = RSICalculator(self.config.rsi_period)
        self.ema_calc = EMACalculator(self.config.ema_period)
        
        # 상태 변수
        self.position = None  # 현재 포지션
        self.pending_order = None  # 대기 중인 주문
        self.balance_krw = 0
        self.balance_usdt = 0
        self.candle_data = []  # 캔들 데이터 저장
        
        logger.info("="*60)
        logger.info(f"Trading Bot Started - Mode: {'DRY RUN' if dry_run else '*** LIVE TRADING ***'}")
        logger.info(f"Profit Target: +{self.config.profit_target} KRW")
        logger.info(f"Max Hold: {self.config.max_hold_hours} hours")
        logger.info("="*60)
    
    def update_balance(self) -> bool:
        """잔고 업데이트"""
        try:
            balance = self.client.get_balance()
            if balance and balance.get('result') == 'success':
                self.balance_krw = float(balance.get('krw', {}).get('avail', 0))
                self.balance_usdt = float(balance.get('usdt', {}).get('avail', 0))
                
                logger.info(f"Balance Updated - KRW: {self.balance_krw:,.0f}, USDT: {self.balance_usdt:.4f}")
                return True
            else:
                logger.error(f"Failed to get balance: {balance}")
                return False
        except Exception as e:
            logger.error(f"Error updating balance: {e}")
            return False
    
    def get_current_price(self) -> Optional[float]:
        """현재가 조회"""
        try:
            ticker = self.client.get_ticker('usdt')
            if ticker and ticker.get('result') == 'success':
                return float(ticker['data']['close_24h'])
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
        return None
    
    def get_orderbook(self) -> Optional[Dict]:
        """호가 정보 조회"""
        try:
            orderbook = self.client.get_orderbook('usdt')
            if orderbook and orderbook.get('result') == 'success':
                return {
                    'ask': float(orderbook['asks'][0]['price']) if orderbook.get('asks') else None,
                    'bid': float(orderbook['bids'][0]['price']) if orderbook.get('bids') else None
                }
        except Exception as e:
            logger.error(f"Error getting orderbook: {e}")
        return None
    
    def get_candle_data(self, hours: int = 24) -> Optional[pd.DataFrame]:
        """캔들 데이터 조회"""
        try:
            candles = self.client.get_candles('usdt', interval='1h', limit=hours)
            if candles and candles.get('result') == 'success':
                # chart 데이터가 루트 레벨에 있음
                data = candles.get('chart', [])
                if data:
                    df = pd.DataFrame(data)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df['close'] = df['close'].astype(float)
                    df['open'] = df['open'].astype(float)
                    df['high'] = df['high'].astype(float)
                    df['low'] = df['low'].astype(float)
                    # volume 필드명 수정 (target_volume 사용)
                    df['volume'] = df['target_volume'].astype(float)
                    
                    # 지표 계산
                    df['rsi'] = self.rsi_calc.calculate_rsi(df, 'close')
                    df['ema'] = self.ema_calc.calculate_ema(df, 'close')
                    
                    return df
        except Exception as e:
            logger.error(f"Error getting candle data: {e}")
        return None
    
    def calculate_slopes(self, series: pd.Series, bars: int) -> float:
        """기울기 계산"""
        if len(series) < bars:
            return 0
        segment = series.iloc[-bars:]
        return (segment.iloc[-1] - segment.iloc[0]) / (bars - 1)
    
    def check_buy_conditions(self, df: pd.DataFrame) -> bool:
        """매수 조건 확인"""
        if len(df) < 20 or self.position is not None:
            return False
        
        try:
            # RSI 기울기
            rsi = df['rsi'].dropna()
            if len(rsi) >= 5:
                rsi_slope_3 = self.calculate_slopes(rsi, 3)
                rsi_slope_5 = self.calculate_slopes(rsi, 5)
                
                # EMA 기울기
                ema = df['ema'].dropna()
                if len(ema) >= 5:
                    ema_slope_3 = self.calculate_slopes(ema, 3)
                    ema_slope_5 = self.calculate_slopes(ema, 5)
                    
                    # 현재 지표 상태 로깅 (디버깅용)
                    current_rsi = rsi.iloc[-1]
                    current_ema = ema.iloc[-1]
                    logger.debug(f"Current RSI: {current_rsi:.2f}, EMA: {current_ema:.2f}")
                    logger.debug(f"RSI slopes: 3-bar={rsi_slope_3:.4f}, 5-bar={rsi_slope_5:.4f}")
                    logger.debug(f"EMA slopes: 3-bar={ema_slope_3:.4f}, 5-bar={ema_slope_5:.4f}")
                    
                    # 매수 조건
                    if (rsi_slope_3 > 0 and rsi_slope_5 > 0 and 
                        ema_slope_3 >= 0.3 and ema_slope_5 >= 0.2):
                        
                        logger.info("BUY SIGNAL DETECTED!")
                        logger.info(f"  RSI slopes: 3-bar={rsi_slope_3:.4f}, 5-bar={rsi_slope_5:.4f}")
                        logger.info(f"  EMA slopes: 3-bar={ema_slope_3:.4f}, 5-bar={ema_slope_5:.4f}")
                        return True
        except Exception as e:
            logger.error(f"Error checking buy conditions: {e}")
        
        return False
    
    def check_sell_conditions(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """매도 조건 확인"""
        if self.position is None:
            return False, ""
        
        current_price = df['close'].iloc[-1]
        current_time = datetime.now()
        entry_price = self.position['entry_price']
        entry_time = self.position['entry_time']
        
        # 익절 조건
        if current_price >= entry_price + self.config.profit_target:
            return True, "PROFIT_TARGET"
        
        # 시간 초과
        hold_hours = (current_time - entry_time).total_seconds() / 3600
        if hold_hours >= self.config.max_hold_hours:
            return True, f"TIMEOUT ({hold_hours:.1f}h)"
        
        # RSI 과매수
        current_rsi = df['rsi'].iloc[-1]
        if not pd.isna(current_rsi) and current_rsi > self.config.rsi_overbought:
            return True, f"RSI_OVERBOUGHT ({current_rsi:.1f})"
        
        # EMA 하락 추세
        ema = df['ema'].dropna()
        if len(ema) >= 9:
            slopes = []
            for i in range(3):
                start_idx = -9 + (i * 3)
                end_idx = -6 + (i * 3) if i < 2 else None
                segment = ema.iloc[start_idx:end_idx]
                slopes.append(self.calculate_slopes(segment, 3))
            
            if slopes[0] > slopes[1] > slopes[2]:
                return True, "EMA_DECLINING"
        
        return False, ""
    
    def place_buy_order(self, price: float) -> bool:
        """매수 주문"""
        if self.balance_krw < 10000:  # 최소 주문 금액
            logger.warning(f"Insufficient KRW balance: {self.balance_krw:,.0f}")
            return False
        
        # 수량 계산 (수수료 고려)
        quantity = (self.balance_krw * 0.999) / price  # 0.1% 여유
        quantity = round(quantity, 4)  # 소수점 4자리
        
        if self.dry_run:
            logger.info(f"[DRY RUN] BUY ORDER: {quantity:.4f} USDT at {price:,.0f} KRW")
            logger.info(f"[DRY RUN] Total: {price * quantity:,.0f} KRW")
            
            self.position = {
                'entry_price': price,
                'entry_time': datetime.now(),
                'quantity': quantity,
                'order_id': 'DRY_RUN_BUY'
            }
            return True
        else:
            # 실제 매수 주문
            logger.info(f"[LIVE] Placing BUY order: {quantity:.4f} USDT at {price:,.0f} KRW")
            
            try:
                order = self.client.place_limit_order(
                    currency='usdt',
                    side='buy',
                    price=price,
                    quantity=quantity
                )
                
                if order and order.get('result') == 'success':
                    order_id = order.get('order_id')
                    logger.info(f"[LIVE] Buy order placed successfully. Order ID: {order_id}")
                    
                    self.pending_order = {
                        'order_id': order_id,
                        'side': 'buy',
                        'price': price,
                        'quantity': quantity,
                        'time': datetime.now()
                    }
                    return True
                else:
                    logger.error(f"[LIVE] Failed to place buy order: {order}")
                    return False
                    
            except Exception as e:
                logger.error(f"[LIVE] Error placing buy order: {e}")
                return False
    
    def place_sell_order(self, price: float, reason: str) -> bool:
        """매도 주문"""
        if self.position is None:
            return False
        
        quantity = self.position['quantity']
        entry_price = self.position['entry_price']
        
        # 손익 계산
        pnl = (price - entry_price) * quantity
        pnl_pct = ((price - entry_price) / entry_price) * 100
        
        # 시장가/지정가 결정
        is_limit = (reason == "PROFIT_TARGET")
        
        if self.dry_run:
            logger.info(f"[DRY RUN] SELL ORDER: {quantity:.4f} USDT at {price:,.0f} KRW")
            logger.info(f"[DRY RUN] Reason: {reason}")
            logger.info(f"[DRY RUN] PnL: {pnl:,.0f} KRW ({pnl_pct:+.2f}%)")
            
            self.position = None
            return True
        else:
            # 실제 매도 주문
            order_type = "LIMIT" if is_limit else "MARKET"
            logger.info(f"[LIVE] Placing {order_type} SELL order: {quantity:.4f} USDT")
            logger.info(f"[LIVE] Reason: {reason}")
            
            try:
                if is_limit:
                    order = self.client.place_limit_order(
                        currency='usdt',
                        side='sell',
                        price=price,
                        quantity=quantity
                    )
                else:
                    order = self.client.place_market_order(
                        currency='usdt',
                        side='sell',
                        quantity=quantity
                    )
                
                if order and order.get('result') == 'success':
                    order_id = order.get('order_id')
                    logger.info(f"[LIVE] Sell order placed. Order ID: {order_id}")
                    logger.info(f"[LIVE] Est. PnL: {pnl:,.0f} KRW ({pnl_pct:+.2f}%)")
                    
                    self.position = None
                    return True
                else:
                    logger.error(f"[LIVE] Failed to place sell order: {order}")
                    return False
                    
            except Exception as e:
                logger.error(f"[LIVE] Error placing sell order: {e}")
                return False
    
    def check_pending_order(self) -> bool:
        """대기 주문 확인"""
        if self.pending_order is None:
            return True
        
        # 10분 경과시 취소
        elapsed = (datetime.now() - self.pending_order['time']).total_seconds()
        if elapsed > 600:  # 10분
            logger.warning(f"Order timeout. Cancelling order {self.pending_order['order_id']}")
            
            if not self.dry_run:
                try:
                    self.client.cancel_order(
                        currency='usdt',
                        order_id=self.pending_order['order_id']
                    )
                except Exception as e:
                    logger.error(f"Error cancelling order: {e}")
            
            self.pending_order = None
            return False
        
        # 주문 상태 확인
        if not self.dry_run:
            try:
                order_info = self.client.get_order_info(
                    currency='usdt',
                    order_id=self.pending_order['order_id']
                )
                
                if order_info and order_info.get('status') == 'filled':
                    logger.info(f"Order {self.pending_order['order_id']} filled!")
                    
                    if self.pending_order['side'] == 'buy':
                        self.position = {
                            'entry_price': self.pending_order['price'],
                            'entry_time': datetime.now(),
                            'quantity': self.pending_order['quantity'],
                            'order_id': self.pending_order['order_id']
                        }
                    
                    self.pending_order = None
                    return True
                    
            except Exception as e:
                logger.error(f"Error checking order status: {e}")
        
        return True
    
    def run_strategy(self):
        """전략 실행 (1회)"""
        # 잔고 업데이트
        if not self.update_balance():
            return
        
        # 캔들 데이터 조회 (RSI 계산을 위해 더 많은 데이터 필요)
        df = self.get_candle_data(50)  # 최소 25개 이상 필요
        if df is None or df.empty:
            logger.warning("No candle data available")
            return
        
        current_price = df['close'].iloc[-1]
        logger.info(f"Current Price: {current_price:,.0f} KRW")
        
        # 대기 주문 확인
        if not self.check_pending_order():
            return
        
        # 포지션 없음 - 매수 확인
        if self.position is None and self.pending_order is None:
            if self.check_buy_conditions(df):
                # 매도1호가로 매수
                orderbook = self.get_orderbook()
                if orderbook and orderbook['ask']:
                    buy_price = orderbook['ask']
                    self.place_buy_order(buy_price)
        
        # 포지션 있음 - 매도 확인
        elif self.position is not None:
            should_sell, reason = self.check_sell_conditions(df)
            if should_sell:
                if reason == "PROFIT_TARGET":
                    # 지정가 매도
                    sell_price = self.position['entry_price'] + self.config.profit_target
                    self.place_sell_order(sell_price, reason)
                else:
                    # 시장가 매도
                    self.place_sell_order(current_price, reason)
        
        # 현재 상태 로깅
        if self.position:
            hold_time = (datetime.now() - self.position['entry_time']).total_seconds() / 3600
            unrealized_pnl = (current_price - self.position['entry_price']) * self.position['quantity']
            logger.info(f"Position: {self.position['quantity']:.4f} USDT @ {self.position['entry_price']:,.0f}")
            logger.info(f"Hold Time: {hold_time:.1f}h, Unrealized PnL: {unrealized_pnl:,.0f} KRW")
    
    def run(self):
        """메인 실행 루프"""
        logger.info("Starting main trading loop...")
        logger.info("Press Ctrl+C to stop")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                logger.info(f"\n--- Cycle #{cycle_count} ---")
                
                # 전략 실행
                self.run_strategy()
                
                # 1분 대기
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("\nShutting down gracefully...")
                
                # 포지션 정리
                if self.position and not self.dry_run:
                    logger.warning("Warning: Open position exists!")
                    logger.info("Consider manual closing if needed")
                
                break
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                time.sleep(60)
        
        logger.info("Trading bot stopped")


def main():
    """메인 함수"""
    # 환경 설정
    dry_run = os.getenv('DRY_RUN', 'True').lower() == 'true'
    
    if not dry_run:
        logger.warning("="*60)
        logger.warning("LIVE TRADING MODE ACTIVATED!")
        logger.warning("Real money will be used for trading")
        logger.warning("="*60)
        
        # 10초 대기
        for i in range(10, 0, -1):
            print(f"Starting in {i} seconds... (Press Ctrl+C to cancel)")
            time.sleep(1)
    
    # 봇 실행
    bot = LiveTradingBot(dry_run=dry_run)
    bot.run()


if __name__ == "__main__":
    import traceback
    main()