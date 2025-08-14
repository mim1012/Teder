"""
개선된 백테스트 엔진 - 정확한 기울기 계산 적용
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
from backtest_engine import Trade, Position, BacktestConfig

logger = logging.getLogger(__name__)


class ImprovedTradingStrategy:
    """개선된 거래 전략 구현 - 정확한 기울기 계산"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.rsi_calc = RSICalculator(period=config.rsi_period)
        self.ema_calc = EMACalculator(period=config.ema_period)
    
    def calculate_slope(self, series: pd.Series, bars: int) -> float:
        """
        제공된 공식에 따른 기울기 계산
        slope = (series.iloc[-1] - series.iloc[-bars]) / (bars - 1)
        """
        if len(series) < bars:
            return np.nan
        
        try:
            last_value = series.iloc[-1]
            first_value = series.iloc[-bars]
            slope = (last_value - first_value) / (bars - 1)
            return slope
        except:
            return np.nan
    
    def calculate_sliding_slopes(self, series: pd.Series, window: int = 3, num_slopes: int = 3) -> List[float]:
        """
        슬라이딩 윈도우 방식으로 여러 구간의 기울기 계산
        
        Args:
            series: 데이터 시리즈
            window: 각 기울기 계산에 사용할 봉 수 (기본 3)
            num_slopes: 계산할 기울기 개수 (기본 3)
        
        Returns:
            List[float]: 각 구간의 기울기 리스트
        """
        slopes = []
        
        # 충분한 데이터가 있는지 확인
        required_length = window + num_slopes - 1
        if len(series) < required_length:
            return [np.nan] * num_slopes
        
        # 각 구간의 기울기 계산
        for i in range(num_slopes):
            start_idx = -(required_length - i)
            end_idx = -(num_slopes - i - 1) if (num_slopes - i - 1) > 0 else None
            
            segment = series.iloc[start_idx:end_idx]
            slope = self.calculate_slope(segment, window)
            slopes.append(slope)
        
        return slopes
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산 - 개선된 방식"""
        df = df.copy()
        
        # RSI 계산
        df['rsi'] = self.rsi_calc.calculate_rsi(df, 'close')
        
        # EMA 계산  
        df['ema'] = self.ema_calc.calculate_ema(df, 'close')
        
        # 각 행에 대해 기울기 계산
        for idx in range(len(df)):
            if idx < 10:  # 충분한 데이터가 없으면 스킵
                df.loc[idx, 'rsi_slope_3'] = np.nan
                df.loc[idx, 'rsi_slope_5'] = np.nan
                df.loc[idx, 'ema_slope_3'] = np.nan
                df.loc[idx, 'ema_slope_5'] = np.nan
                df.loc[idx, 'ema_slope_declining'] = False
            else:
                # RSI 기울기 (단일 구간)
                rsi_series = df['rsi'].iloc[:idx+1]
                df.loc[idx, 'rsi_slope_3'] = self.calculate_slope(rsi_series, 3)
                df.loc[idx, 'rsi_slope_5'] = self.calculate_slope(rsi_series, 5)
                
                # EMA 기울기 (단일 구간)
                ema_series = df['ema'].iloc[:idx+1]
                df.loc[idx, 'ema_slope_3'] = self.calculate_slope(ema_series, 3)
                df.loc[idx, 'ema_slope_5'] = self.calculate_slope(ema_series, 5)
                
                # EMA 하락 조건: 3개 구간의 기울기가 연속 감소
                ema_slopes = self.calculate_sliding_slopes(ema_series, window=3, num_slopes=3)
                if all(not pd.isna(s) for s in ema_slopes) and len(ema_slopes) >= 3:
                    # slope1 > slope2 > slope3 확인
                    df.loc[idx, 'ema_slope_declining'] = (ema_slopes[0] > ema_slopes[1] > ema_slopes[2])
                else:
                    df.loc[idx, 'ema_slope_declining'] = False
        
        return df
    
    def check_buy_conditions(self, df: pd.DataFrame, idx: int) -> bool:
        """매수 조건 확인 - 기존과 동일"""
        if idx < max(self.config.rsi_slope_periods + [3, 5]):
            return False
        
        try:
            # RSI 기울기 조건 확인
            rsi_slope_3 = df.iloc[idx]['rsi_slope_3']
            rsi_slope_5 = df.iloc[idx]['rsi_slope_5']
            
            if pd.isna(rsi_slope_3) or pd.isna(rsi_slope_5):
                return False
            
            # RSI 기울기는 모두 양수여야 함 (0 불포함)
            if rsi_slope_3 <= 0 or rsi_slope_5 <= 0:
                return False
            
            # EMA 기울기 조건 확인
            ema_slope_3 = df.iloc[idx]['ema_slope_3']
            ema_slope_5 = df.iloc[idx]['ema_slope_5']
            
            if pd.isna(ema_slope_3) or pd.isna(ema_slope_5):
                return False
            
            # EMA 기울기 임계값 확인
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
        """매도 조건 확인 - EMA 하락 조건 개선"""
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
        
        # 개선된 EMA 하락 조건 - 3개 구간 기울기 연속 감소
        try:
            ema_declining = df.iloc[idx]['ema_slope_declining']
            if ema_declining:
                return True, "EMA하락"
        except (KeyError, IndexError):
            pass
        
        return False, ""


class ImprovedBacktestEngine:
    """개선된 백테스트 엔진"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.strategy = ImprovedTradingStrategy(config)
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
        
        # 전량 매수
        total_cost_ratio = 1 + self.config.limit_order_fee
        quantity = self.balance / (actual_price * total_cost_ratio)
        
        if quantity <= 0:
            return False
        
        # 수수료 계산
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
        
        # 수수료 계산
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
        logger.info("개선된 백테스트 시작")
        
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
        
        logger.info(f"개선된 백테스트 완료: {len(self.trades)}개 거래, 최종 잔고: {self.balance:.2f}")
        
        return result


def run_improved_backtest(
    df: pd.DataFrame, 
    config: Optional[BacktestConfig] = None
) -> Dict[str, Any]:
    """
    개선된 백테스트 실행 함수
    
    Args:
        df: OHLCV 데이터
        config: 백테스트 설정 (None이면 기본값 사용)
        
    Returns:
        Dict: 백테스트 결과
    """
    if config is None:
        config = BacktestConfig()
    
    engine = ImprovedBacktestEngine(config)
    return engine.run_backtest(df)