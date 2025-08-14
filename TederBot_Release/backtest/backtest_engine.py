"""
백테스트 엔진
USDT/KRW 자동매매 전략의 백테스트 실행 엔진
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.indicators.rsi import RSICalculator
from src.indicators.ema import EMACalculator

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """개별 거래 정보"""
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    quantity: float = 0.0
    side: str = "buy"  # "buy" or "sell"
    pnl: float = 0.0
    pnl_pct: float = 0.0
    fee: float = 0.0
    reason: str = ""  # 매도 이유 (익절, 손절, 시간초과 등)


@dataclass 
class Position:
    """현재 포지션 정보"""
    quantity: float = 0.0
    avg_price: float = 0.0
    entry_time: Optional[datetime] = None
    is_open: bool = False
    
    def open_position(self, price: float, quantity: float, timestamp: datetime):
        """포지션 오픈"""
        self.quantity = quantity
        self.avg_price = price
        self.entry_time = timestamp
        self.is_open = True
    
    def close_position(self):
        """포지션 클로즈"""
        self.quantity = 0.0
        self.avg_price = 0.0
        self.entry_time = None
        self.is_open = False


@dataclass
class BacktestConfig:
    """백테스트 설정"""
    initial_balance: float = 1000000.0  # 초기 자금 (원화)
    limit_order_fee: float = 0.0000  # 지정가 수수료 0%
    market_order_fee: float = 0.0002  # 시장가 수수료 0.02%
    slippage_rate: float = 0.0001  # 슬리피지 0.01%
    
    # 매수 조건 파라미터
    rsi_period: int = 14
    ema_period: int = 20
    rsi_slope_periods: List[int] = field(default_factory=lambda: [3, 5])
    ema_slope_thresholds: List[float] = field(default_factory=lambda: [0.3, 0.2])
    
    # 매도 조건 파라미터
    profit_target: float = 4.0  # 익절 목표 (원)
    max_hold_hours: int = 24  # 최대 보유 시간
    rsi_overbought: float = 70.0  # RSI 과매수 기준
    
    # 백테스트 기간
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TradingStrategy:
    """거래 전략 구현"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.rsi_calc = RSICalculator(period=config.rsi_period)
        self.ema_calc = EMACalculator(period=config.ema_period)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산"""
        df = df.copy()
        
        # RSI 계산
        df['rsi'] = self.rsi_calc.calculate_rsi(df, 'close')
        
        # EMA 계산  
        df['ema'] = self.ema_calc.calculate_ema(df, 'close')
        
        # RSI 기울기 계산 (봉 수 - 1로 나누기)
        for period in self.config.rsi_slope_periods:
            df[f'rsi_slope_{period}'] = df['rsi'].diff(period) / (period - 1)
        
        # EMA 기울기 계산 (봉 수 - 1로 나누기)
        for i, period in enumerate([3, 5]):
            df[f'ema_slope_{period}'] = df['ema'].diff(period) / (period - 1)
        
        return df
    
    def check_buy_conditions(self, df: pd.DataFrame, idx: int) -> bool:
        """매수 조건 확인"""
        if idx < max(self.config.rsi_slope_periods + [3, 5]):
            return False
        
        try:
            # RSI 기울기 조건 확인
            rsi_slope_3 = df.iloc[idx][f'rsi_slope_{self.config.rsi_slope_periods[0]}']
            rsi_slope_5 = df.iloc[idx][f'rsi_slope_{self.config.rsi_slope_periods[1]}']
            
            if pd.isna(rsi_slope_3) or pd.isna(rsi_slope_5):
                return False
            
            if rsi_slope_3 <= 0 or rsi_slope_5 <= 0:
                return False
            
            # EMA 기울기 조건 확인
            ema_slope_3 = df.iloc[idx]['ema_slope_3']
            ema_slope_5 = df.iloc[idx]['ema_slope_5']
            
            if pd.isna(ema_slope_3) or pd.isna(ema_slope_5):
                return False
            
            if ema_slope_3 < self.config.ema_slope_thresholds[0]:
                return False
            
            if ema_slope_5 < self.config.ema_slope_thresholds[1]:
                return False
            
            return True
            
        except (KeyError, IndexError):
            return False
    
    def check_sell_conditions(
        self, 
        df: pd.DataFrame, 
        idx: int, 
        position: Position
    ) -> Tuple[bool, str]:
        """매도 조건 확인"""
        if not position.is_open:
            return False, ""
        
        current_price = df.iloc[idx]['close']
        current_time = df.iloc[idx]['timestamp']
        
        # 익절 조건
        if current_price >= position.avg_price + self.config.profit_target:
            return True, "익절"
        
        # 시간 초과 조건
        if position.entry_time:
            hold_duration = current_time - position.entry_time
            if hold_duration >= timedelta(hours=self.config.max_hold_hours):
                return True, "시간초과"
        
        # RSI 과매수 조건
        try:
            current_rsi = df.iloc[idx]['rsi']
            if not pd.isna(current_rsi) and current_rsi > self.config.rsi_overbought:
                return True, "RSI과매수"
        except (KeyError, IndexError):
            pass
        
        # EMA 기울기 하락 조건
        try:
            if idx >= 3:
                ema_slope_3_current = df.iloc[idx]['ema_slope_3']
                ema_slope_3_prev = df.iloc[idx-1]['ema_slope_3']
                ema_slope_3_prev2 = df.iloc[idx-2]['ema_slope_3']
                
                # 연속적으로 감소하는지 확인
                if (not pd.isna(ema_slope_3_current) and 
                    not pd.isna(ema_slope_3_prev) and 
                    not pd.isna(ema_slope_3_prev2)):
                    
                    if (ema_slope_3_current < ema_slope_3_prev < ema_slope_3_prev2):
                        return True, "EMA하락"
        except (KeyError, IndexError):
            pass
        
        return False, ""


class BacktestEngine:
    """백테스트 엔진"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.strategy = TradingStrategy(config)
        self.reset()
    
    def reset(self):
        """백테스트 상태 초기화"""
        self.balance = self.config.initial_balance
        self.position = Position()
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        self.current_trade: Optional[Trade] = None
    
    def calculate_fees_and_slippage(self, price: float, quantity: float, is_limit_order: bool = True) -> float:
        """수수료 및 슬리피지 계산"""
        trade_value = price * quantity
        # 지정가 주문은 수수료 0%, 시장가 주문은 0.02%
        fee_rate = self.config.limit_order_fee if is_limit_order else self.config.market_order_fee
        fee = trade_value * fee_rate
        slippage = trade_value * self.config.slippage_rate
        return fee + slippage
    
    def execute_buy(self, price: float, timestamp: datetime) -> bool:
        """매수 실행"""
        if self.position.is_open or self.balance <= 0:
            return False
        
        # 슬리피지 적용된 실제 매수가
        actual_price = price * (1 + self.config.slippage_rate)
        
        # 전량 매수 (지정가 주문이므로 수수료 0%)
        total_cost_ratio = 1 + self.config.limit_order_fee
        quantity = self.balance / (actual_price * total_cost_ratio)
        
        if quantity <= 0:
            return False
        
        # 수수료 계산 (지정가 주문)
        fee = self.calculate_fees_and_slippage(actual_price, quantity, is_limit_order=True)
        
        # 포지션 오픈
        self.position.open_position(actual_price, quantity, timestamp)
        
        # 거래 기록
        self.current_trade = Trade(
            entry_time=timestamp,
            entry_price=actual_price,
            quantity=quantity,
            side="buy",
            fee=fee
        )
        
        # 잔고 업데이트
        self.balance = 0.0
        
        logger.debug(f"매수 실행: {timestamp}, 가격: {actual_price:.2f}, 수량: {quantity:.4f}")
        
        return True
    
    def execute_sell(self, price: float, timestamp: datetime, reason: str) -> bool:
        """매도 실행"""
        if not self.position.is_open or not self.current_trade:
            return False
        
        # 슬리피지 적용된 실제 매도가
        actual_price = price * (1 - self.config.slippage_rate)
        
        # 전량 매도
        quantity = self.position.quantity
        
        # 수수료 계산 (익절은 지정가, 나머지는 시장가)
        is_limit_order = (reason == "익절")
        fee = self.calculate_fees_and_slippage(actual_price, quantity, is_limit_order=is_limit_order)
        
        # 매도 수익 계산
        gross_proceeds = actual_price * quantity
        net_proceeds = gross_proceeds - fee
        
        # 손익 계산
        entry_cost = self.current_trade.entry_price * quantity + self.current_trade.fee
        pnl = net_proceeds - entry_cost
        pnl_pct = (pnl / entry_cost) * 100 if entry_cost > 0 else 0
        
        # 거래 완료
        self.current_trade.exit_time = timestamp
        self.current_trade.exit_price = actual_price
        self.current_trade.pnl = pnl
        self.current_trade.pnl_pct = pnl_pct
        self.current_trade.fee += fee
        self.current_trade.reason = reason
        
        self.trades.append(self.current_trade)
        
        # 잔고 업데이트
        self.balance = net_proceeds
        
        # 포지션 클로즈
        self.position.close_position()
        self.current_trade = None
        
        logger.debug(f"매도 실행: {timestamp}, 가격: {actual_price:.2f}, 손익: {pnl:.2f} ({pnl_pct:.2f}%), 이유: {reason}")
        
        return True
    
    def update_equity_curve(self, timestamp: datetime, price: float):
        """자산 곡선 업데이트"""
        if self.position.is_open:
            # 포지션이 열려있으면 현재 가격으로 평가
            unrealized_value = self.position.quantity * price
            total_equity = unrealized_value
            unrealized_pnl = unrealized_value - (self.position.quantity * self.position.avg_price)
        else:
            total_equity = self.balance
            unrealized_pnl = 0.0
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'price': price,
            'balance': self.balance,
            'total_equity': total_equity,
            'unrealized_pnl': unrealized_pnl,
            'position_size': self.position.quantity if self.position.is_open else 0.0
        })
    
    def run_backtest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """백테스트 실행"""
        logger.info("백테스트 시작")
        
        # 초기화
        self.reset()
        
        # 기술적 지표 계산
        df_with_indicators = self.strategy.calculate_indicators(df)
        
        # 백테스트 기간 필터링
        if self.config.start_date or self.config.end_date:
            if self.config.start_date:
                df_with_indicators = df_with_indicators[df_with_indicators['timestamp'] >= self.config.start_date]
            if self.config.end_date:
                df_with_indicators = df_with_indicators[df_with_indicators['timestamp'] <= self.config.end_date]
        
        if len(df_with_indicators) == 0:
            raise ValueError("백테스트 데이터가 없습니다")
        
        # 각 시점별 백테스트 실행
        for idx in range(len(df_with_indicators)):
            row = df_with_indicators.iloc[idx]
            timestamp = row['timestamp']
            price = row['close']
            
            # 매도 조건 확인 (매수보다 우선)
            if self.position.is_open:
                should_sell, sell_reason = self.strategy.check_sell_conditions(
                    df_with_indicators, idx, self.position
                )
                
                if should_sell:
                    self.execute_sell(price, timestamp, sell_reason)
            
            # 매수 조건 확인
            elif self.strategy.check_buy_conditions(df_with_indicators, idx):
                self.execute_buy(price, timestamp)
            
            # 자산 곡선 업데이트
            self.update_equity_curve(timestamp, price)
        
        # 미청산 포지션 처리
        if self.position.is_open and len(df_with_indicators) > 0:
            last_row = df_with_indicators.iloc[-1]
            self.execute_sell(last_row['close'], last_row['timestamp'], "백테스트종료")
        
        # 결과 반환
        result = {
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'final_balance': self.balance,
            'initial_balance': self.config.initial_balance,
            'data_with_indicators': df_with_indicators
        }
        
        logger.info(f"백테스트 완료: {len(self.trades)}개 거래, 최종 잔고: {self.balance:.2f}")
        
        return result


def run_quick_backtest(
    df: pd.DataFrame, 
    config: Optional[BacktestConfig] = None
) -> Dict[str, Any]:
    """
    빠른 백테스트 실행 함수
    
    Args:
        df: OHLCV 데이터
        config: 백테스트 설정 (None이면 기본값 사용)
        
    Returns:
        Dict: 백테스트 결과
    """
    if config is None:
        config = BacktestConfig()
    
    engine = BacktestEngine(config)
    return engine.run_backtest(df)


if __name__ == "__main__":
    # 테스트 실행
    logging.basicConfig(level=logging.INFO)
    
    print("백테스트 엔진 테스트")
    print("=" * 50)
    
    # 샘플 데이터로 테스트
    from data_loader import SampleDataGenerator
    
    sample_df = SampleDataGenerator.generate_realistic_data(hours=500)
    
    config = BacktestConfig(
        initial_balance=1000000,
        fee_rate=0.0015,
        slippage_rate=0.0001
    )
    
    result = run_quick_backtest(sample_df, config)
    
    print(f"\n백테스트 결과:")
    print(f"초기 자금: {result['initial_balance']:,.0f}원")
    print(f"최종 자금: {result['final_balance']:,.0f}원")
    print(f"총 수익률: {((result['final_balance'] / result['initial_balance']) - 1) * 100:.2f}%")
    print(f"총 거래 수: {len(result['trades'])}개")
    
    if result['trades']:
        winning_trades = [t for t in result['trades'] if t.pnl > 0]
        print(f"승률: {len(winning_trades) / len(result['trades']) * 100:.1f}%")
        
        total_pnl = sum(t.pnl for t in result['trades'])
        print(f"총 손익: {total_pnl:,.0f}원")
        
        avg_pnl = total_pnl / len(result['trades'])
        print(f"평균 손익: {avg_pnl:,.0f}원")