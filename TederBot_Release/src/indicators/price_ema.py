"""
가격 EMA(5) 계산 모듈
분할매수 전략을 위한 가격 추세 분석
"""

import pandas as pd
import numpy as np
import pandas_ta as ta
from .base import BaseIndicator


class PriceEMA(BaseIndicator):
    """가격 EMA(5) 계산 및 기울기 분석"""
    
    def __init__(self, period=5):
        super().__init__()
        self.period = period
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        가격 EMA(5) 계산
        
        Args:
            data: OHLCV 데이터프레임 (close 컬럼 필요)
            
        Returns:
            pd.Series: EMA(5) 값
        """
        if len(data) < self.period:
            return pd.Series(dtype=float)
            
        return ta.ema(data['close'], length=self.period)
    
    def calculate_slope(self, ema_values: pd.Series, periods: int) -> float:
        """
        EMA 기울기 계산 (선형 회귀)
        
        Args:
            ema_values: EMA 값들
            periods: 기울기 계산할 기간
            
        Returns:
            float: 기울기 값 (NaN이면 0.0 반환)
        """
        if len(ema_values) < periods:
            return 0.0
            
        # 최근 periods개 데이터 사용
        recent_values = ema_values.tail(periods).dropna()
        
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
    
    def calculate_simple_slope(self, ema_values: pd.Series, periods: int) -> float:
        """
        단순 기울기 계산 (차분 방법)
        
        Args:
            ema_values: EMA 값들
            periods: 기울기 계산할 기간
            
        Returns:
            float: 기울기 값
        """
        if len(ema_values) < periods:
            return 0.0
            
        recent_values = ema_values.tail(periods).dropna()
        
        if len(recent_values) < periods:
            return 0.0
            
        # 첫번째와 마지막 값의 차이를 기간으로 나눔
        try:
            slope = (recent_values.iloc[-1] - recent_values.iloc[0]) / (periods - 1)
            return float(slope) if not np.isnan(slope) else 0.0
        except:
            return 0.0
    
    def check_buy_condition(self, data: pd.DataFrame) -> dict:
        """
        가격 EMA 매수 조건 체크
        - 가격 캔들의 EMA(5) 직전 2봉 기울기 > 0.2
        
        Args:
            data: OHLCV 데이터
            
        Returns:
            dict: 조건 체크 결과
        """
        ema = self.calculate(data)
        
        if len(ema) < 2:
            return {
                'condition_met': False,
                'ema_value': None,
                'slope_2': 0.0,
                'reason': 'Insufficient data'
            }
        
        current_ema = ema.iloc[-1]
        slope_2 = self.calculate_slope(ema, 2)
        
        # 조건 체크
        condition_met = slope_2 > 0.2
        
        return {
            'condition_met': condition_met,
            'ema_value': current_ema,
            'slope_2': slope_2,
            'reason': 'Price EMA slope > 0.2' if condition_met else f'Price EMA slope {slope_2:.3f} <= 0.2'
        }
    
    def get_current_price_info(self, data: pd.DataFrame) -> dict:
        """
        현재 가격 정보 반환
        
        Args:
            data: OHLCV 데이터
            
        Returns:
            dict: 현재 가격 정보
        """
        if len(data) == 0:
            return {
                'current_price': None,
                'ema_value': None,
                'price_above_ema': False
            }
        
        current_price = data['close'].iloc[-1]
        ema = self.calculate(data)
        current_ema = ema.iloc[-1] if len(ema) > 0 else None
        
        return {
            'current_price': current_price,
            'ema_value': current_ema,
            'price_above_ema': current_price > current_ema if current_ema is not None else False,
            'price_ema_diff': current_price - current_ema if current_ema is not None else 0
        }