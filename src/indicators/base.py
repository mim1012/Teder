import pandas as pd
import numpy as np
from typing import Union, Optional, List


class BaseIndicator:
    """기술적 지표 계산을 위한 기본 클래스"""
    
    @staticmethod
    def calculate_slope(data: pd.Series, periods: int) -> float:
        """주어진 기간의 기울기를 계산합니다."""
        if len(data) < periods:
            return 0.0
            
        recent_value = data.iloc[-1]
        previous_value = data.iloc[-periods]
        
        return float(recent_value - previous_value)
    
    @staticmethod
    def calculate_slopes(data: pd.Series, periods_list: List[int]) -> dict:
        """여러 기간의 기울기를 한번에 계산합니다."""
        slopes = {}
        for periods in periods_list:
            slopes[f'slope_{periods}'] = BaseIndicator.calculate_slope(data, periods)
        
        return slopes
    
    @staticmethod
    def is_slopes_positive(slopes: dict, exclude_zero: bool = True) -> bool:
        """모든 기울기가 양수인지 확인합니다."""
        for slope_value in slopes.values():
            if exclude_zero and slope_value <= 0.0:
                return False
            elif not exclude_zero and slope_value < 0.0:
                return False
        
        return True
    
    @staticmethod
    def validate_data(data: pd.DataFrame, required_columns: List[str]) -> bool:
        """데이터 유효성을 검증합니다."""
        if data is None or data.empty:
            return False
            
        for col in required_columns:
            if col not in data.columns:
                return False
        
        return True


def create_indicator_series(data: pd.DataFrame, column: str = 'close') -> pd.Series:
    """지표 계산을 위한 시리즈를 생성합니다."""
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")
    
    return data[column].copy()


def ensure_sufficient_data(data: pd.Series, min_periods: int) -> bool:
    """충분한 데이터가 있는지 확인합니다."""
    return len(data) >= min_periods and not data.isna().all()