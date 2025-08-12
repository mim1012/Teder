"""
USDT/KRW 자동매매 프로그램 - 간단한 메인 실행 파일
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleTradingBot:
    """간단한 USDT/KRW 자동매매 봇"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.client = CoinoneClient()
        self.config = BacktestConfig()
        self.rsi_calc = RSICalculator(self.config.rsi_period)
        self.ema_calc = EMACalculator(self.config.ema_period)
        
        # 상태 변수
        self.position = None
        self.balance_krw = 0
        self.balance_usdt = 0
        
        logger.info(f"Trading bot initialized - Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    
    def update_balance(self):
        """잔고 업데이트"""
        try:
            balance = self.client.get_balance()
            if balance and balance.get('result') == 'success':
                self.balance_krw = float(balance.get('krw', {}).get('avail', 0))
                self.balance_usdt = float(balance.get('usdt', {}).get('avail', 0))
                logger.info(f"Balance: {self.balance_krw:,.0f} KRW, {self.balance_usdt:.4f} USDT")
                return True
        except Exception as e:
            logger.error(f"Failed to update balance: {e}")
        return False
    
    def get_market_data(self, hours: int = 24):
        """시장 데이터 조회 (시뮬레이션)"""
        try:
            # 현재가 조회
            ticker = self.client.get_ticker('usdt')
            if ticker and ticker.get('result') == 'success':
                current_price = float(ticker['data']['close_24h'])
                
                # 간단한 시뮬레이션 데이터 생성
                prices = [current_price] * hours
                timestamps = [datetime.now() - timedelta(hours=i) for i in range(hours)]
                
                df = pd.DataFrame({
                    'timestamp': timestamps[::-1],
                    'close': prices,
                    'open': prices,
                    'high': prices,
                    'low': prices,
                    'volume': [100000] * hours
                })
                
                # 지표 계산
                df['rsi'] = self.rsi_calc.calculate_rsi(df, 'close')
                df['ema'] = self.ema_calc.calculate_ema(df, 'close')
                
                return df, current_price
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
        return None, None
    
    def check_buy_signal(self, df):
        """매수 신호 확인"""
        if len(df) < 20:
            return False
        
        try:
            # RSI 기울기 계산 (간단한 버전)
            rsi = df['rsi'].dropna()
            if len(rsi) >= 5:
                rsi_slope_3 = (rsi.iloc[-1] - rsi.iloc[-3]) / 2
                rsi_slope_5 = (rsi.iloc[-1] - rsi.iloc[-5]) / 4
                
                # EMA 기울기 계산
                ema = df['ema'].dropna()
                if len(ema) >= 5:
                    ema_slope_3 = (ema.iloc[-1] - ema.iloc[-3]) / 2
                    ema_slope_5 = (ema.iloc[-1] - ema.iloc[-5]) / 4
                    
                    # 매수 조건 확인
                    if (rsi_slope_3 > 0 and rsi_slope_5 > 0 and 
                        ema_slope_3 >= 0.3 and ema_slope_5 >= 0.2):
                        logger.info(f"Buy signal detected - RSI slopes: {rsi_slope_3:.2f}, {rsi_slope_5:.2f}")
                        return True
        except Exception as e:
            logger.error(f"Error checking buy signal: {e}")
        
        return False
    
    def check_sell_signal(self, df, entry_price, entry_time):
        """매도 신호 확인"""
        if self.position is None:
            return False, ""
        
        current_price = df['close'].iloc[-1]
        current_time = datetime.now()
        
        # 익절 조건
        if current_price >= entry_price + self.config.profit_target:
            return True, "PROFIT_TARGET"
        
        # 시간 초과
        if (current_time - entry_time).total_seconds() / 3600 >= self.config.max_hold_hours:
            return True, "TIMEOUT"
        
        # RSI 과매수
        if df['rsi'].iloc[-1] > self.config.rsi_overbought:
            return True, "RSI_OVERBOUGHT"
        
        return False, ""
    
    def execute_buy(self, price):
        """매수 실행"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would buy USDT at {price:,.0f} KRW")
            self.position = {
                'entry_price': price,
                'entry_time': datetime.now(),
                'quantity': self.balance_krw / price
            }
            return True
        else:
            # 실제 매수 로직
            logger.warning("Live trading not implemented yet")
            return False
    
    def execute_sell(self, price, reason):
        """매도 실행"""
        if self.dry_run:
            pnl = (price - self.position['entry_price']) * self.position['quantity']
            pnl_pct = ((price - self.position['entry_price']) / self.position['entry_price']) * 100
            logger.info(f"[DRY RUN] Would sell USDT at {price:,.0f} KRW - Reason: {reason}")
            logger.info(f"[DRY RUN] PnL: {pnl:,.0f} KRW ({pnl_pct:.2f}%)")
            self.position = None
            return True
        else:
            # 실제 매도 로직
            logger.warning("Live trading not implemented yet")
            return False
    
    def run(self):
        """메인 실행 루프"""
        logger.info("Starting trading bot...")
        
        # 초기 잔고 확인
        self.update_balance()
        
        while True:
            try:
                # 시장 데이터 조회
                df, current_price = self.get_market_data()
                if df is None:
                    logger.warning("Failed to get market data")
                    time.sleep(60)
                    continue
                
                logger.info(f"Current price: {current_price:,.0f} KRW")
                
                # 포지션이 없으면 매수 신호 확인
                if self.position is None:
                    if self.check_buy_signal(df):
                        self.execute_buy(current_price)
                
                # 포지션이 있으면 매도 신호 확인
                else:
                    should_sell, reason = self.check_sell_signal(
                        df, 
                        self.position['entry_price'],
                        self.position['entry_time']
                    )
                    if should_sell:
                        self.execute_sell(current_price, reason)
                
                # 1분 대기
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)


def main():
    """메인 함수"""
    # DRY_RUN 설정 확인
    dry_run = os.getenv('DRY_RUN', 'True').lower() == 'true'
    
    # 봇 실행
    bot = SimpleTradingBot(dry_run=dry_run)
    bot.run()


if __name__ == "__main__":
    main()