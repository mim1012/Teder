"""
RSI(9) 및 RSI(9)의 EMA(5) 계산 모듈
분할매수 전략을 위한 짧은 기간 RSI 지표
"""

import pandas as pd
import numpy as np
import pandas_ta as ta
from .base import BaseIndicator


class RSIShort(BaseIndicator):
    """RSI(9) 계산 및 기울기 분석"""
    
    def __init__(self, period=9):
        super().__init__()
        self.period = period
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        RSI(9) 계산
        
        Args:
            data: OHLCV 데이터프레임 (close 컬럼 필요)
            
        Returns:
            pd.Series: RSI(9) 값
        """
        if len(data) < self.period:
            return pd.Series(dtype=float)
            
        return ta.rsi(data['close'], length=self.period)
    
    def calculate_slope(self, rsi_values: pd.Series, periods: int) -> float:
        """
        RSI 기울기 계산 (선형 회귀)
        
        Args:
            rsi_values: RSI 값들
            periods: 기울기 계산할 기간
            
        Returns:
            float: 기울기 값 (NaN이면 0.0 반환)
        """
        if len(rsi_values) < periods:
            return 0.0
            
        # 최근 periods개 데이터 사용
        recent_values = rsi_values.tail(periods).dropna()
        
        if len(recent_values) < periods:
            return 0.0
            
        # 선형 회귀로 기울기 계산
        x = np.arange(len(recent_values))
        y = recent_values.values
        
        try:
            slope = np.polyfit(x, y, 1)[0]
            return float(slope) if not np.isnan(slope) else 0.0
        except:
            return 0.0
    
    def check_buy_condition(self, data: pd.DataFrame) -> dict:
        """
        RSI(9) 매수 조건 체크
        - RSI(9) 직전 3봉 기울기 > 3
        - RSI(9) 값 < 70
        
        Args:
            data: OHLCV 데이터
            
        Returns:
            dict: 조건 체크 결과
        """
        rsi = self.calculate(data)
        
        if len(rsi) < 3:
            return {
                'condition_met': False,
                'rsi_value': None,
                'slope_3': 0.0,
                'reason': 'Insufficient data'
            }
        
        current_rsi = rsi.iloc[-1]
        slope_3 = self.calculate_slope(rsi, 3)
        
        # 조건 체크
        rsi_condition = current_rsi < 70
        slope_condition = slope_3 > 3
        
        return {
            'condition_met': rsi_condition and slope_condition,
            'rsi_value': current_rsi,
            'slope_3': slope_3,
            'rsi_below_70': rsi_condition,
            'slope_above_3': slope_condition,
            'reason': self._get_condition_reason(rsi_condition, slope_condition)
        }
    
    def _get_condition_reason(self, rsi_condition: bool, slope_condition: bool) -> str:
        """조건 불만족 이유 반환"""
        if not rsi_condition and not slope_condition:
            return 'RSI >= 70 and slope <= 3'
        elif not rsi_condition:
            return 'RSI >= 70'
        elif not slope_condition:
            return 'RSI slope <= 3'
        else:
            return 'All conditions met'


class RSIEMAShort(BaseIndicator):
    """RSI(9)의 EMA(5) 계산 및 기울기 분석"""
    
    def __init__(self, rsi_period=9, ema_period=5):
        super().__init__()
        self.rsi_period = rsi_period
        self.ema_period = ema_period
        self.rsi_calculator = RSIShort(rsi_period)
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        RSI(9)의 EMA(5) 계산
        
        Args:
            data: OHLCV 데이터프레임
            
        Returns:
            pd.Series: RSI EMA 값
        """
        # RSI(9) 계산
        rsi = self.rsi_calculator.calculate(data)
        
        if len(rsi) < self.ema_period:
            return pd.Series(dtype=float)
        
        # RSI의 EMA(5) 계산
        return ta.ema(rsi, length=self.ema_period)
    
    def calculate_slope(self, rsi_ema_values: pd.Series, periods: int) -> float:
        """
        RSI EMA 기울기 계산
        
        Args:
            rsi_ema_values: RSI EMA 값들
            periods: 기울기 계산할 기간
            
        Returns:
            float: 기울기 값
        """
        if len(rsi_ema_values) < periods:
            return 0.0
            
        # 최근 periods개 데이터 사용
        recent_values = rsi_ema_values.tail(periods).dropna()
        
        if len(recent_values) < periods:
            return 0.0
            
        # 선형 회귀로 기울기 계산
        x = np.arange(len(recent_values))
        y = recent_values.values
        
        try:
            slope = np.polyfit(x, y, 1)[0]
            return float(slope) if not np.isnan(slope) else 0.0
        except:
            return 0.0
    
    def check_buy_condition(self, data: pd.DataFrame) -> dict:
        """
        RSI EMA 매수 조건 체크
        - RSI(9)의 EMA(5) 직전 2봉 기울기 > 1
        
        Args:
            data: OHLCV 데이터
            
        Returns:
            dict: 조건 체크 결과
        """
        rsi_ema = self.calculate(data)
        
        if len(rsi_ema) < 2:
            return {
                'condition_met': False,
                'rsi_ema_value': None,
                'slope_2': 0.0,
                'reason': 'Insufficient data'
            }
        
        current_rsi_ema = rsi_ema.iloc[-1]
        slope_2 = self.calculate_slope(rsi_ema, 2)
        
        # 조건 체크
        condition_met = slope_2 > 1
        
        return {
            'condition_met': condition_met,
            'rsi_ema_value': current_rsi_ema,
            'slope_2': slope_2,
            'reason': 'RSI EMA slope > 1' if condition_met else 'RSI EMA slope <= 1'
        }