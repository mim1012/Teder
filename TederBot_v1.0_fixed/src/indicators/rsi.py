import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from .base import BaseIndicator, create_indicator_series, ensure_sufficient_data


class RSICalculator(BaseIndicator):
    """
    RSI 계산 및 분석 클래스
    
    매수 조건: RSI(14) 직전 3봉과 5봉의 기울기가 모두 양수 (0.00 불포함)
    매도 조건: 실시간 RSI(14) > 70
    """
    
    def __init__(self, period: int = 14):
        self.period = period
        self.min_required_data = period + 5
    
    def _calculate_rsi_manual(self, price_series: pd.Series, period: int) -> pd.Series:
        """
        RSI를 수동으로 계산합니다.
        
        Args:
            price_series: 가격 시리즈
            period: RSI 계산 기간
            
        Returns:
            RSI 시리즈
        """
        delta = price_series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_rsi(self, data: pd.DataFrame, column: str = 'close') -> pd.Series:
        """
        RSI를 계산합니다.
        
        Args:
            data: OHLCV 데이터프레임
            column: RSI 계산에 사용할 컴럼
            
        Returns:
            RSI 시리즈
        """
        price_series = create_indicator_series(data, column)
        
        if not ensure_sufficient_data(price_series, self.min_required_data):
            raise ValueError(f"Insufficient data. Need at least {self.min_required_data} periods")
        
        rsi_series = self._calculate_rsi_manual(price_series, self.period)
        
        if rsi_series is None or rsi_series.isna().all():
            raise ValueError("Failed to calculate RSI")
        
        return rsi_series
    
    def calculate_rsi_slopes(self, rsi_series: pd.Series, 
                           periods: List[int] = [3, 5]) -> Dict[str, float]:
        """
        RSI의 기울기를 계산합니다.
        
        Args:
            rsi_series: RSI 시리즈
            periods: 기울기 계산 기간 리스트
            
        Returns:
            기간별 기울기 딕셔너리
        """
        return self.calculate_slopes(rsi_series, periods)
    
    def analyze_rsi_trend(self, rsi_series: pd.Series, 
                         periods: List[int] = [3, 5]) -> Dict:
        """
        RSI 추세를 분석합니다.
        
        Args:
            rsi_series: RSI 시리즈
            periods: 분석할 기간 리스트
            
        Returns:
            RSI 추세 분석 결과
        """
        if len(rsi_series) < max(periods):
            raise ValueError(f"Insufficient data for slope analysis")
        
        current_rsi = float(rsi_series.iloc[-1])
        slopes = self.calculate_rsi_slopes(rsi_series, periods)
        
        # 매수 신호 조건 확인: 모든 기울기가 양수 (0.00 불포함)
        buy_signal = self.is_slopes_positive(slopes, exclude_zero=True)
        
        # 매도 신호 조건 확인: RSI > 70
        sell_signal = current_rsi > 70.0
        
        analysis = {
            'current_rsi': current_rsi,
            'slopes': slopes,
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'all_slopes_positive': buy_signal,
            'rsi_overbought': sell_signal
        }
        
        return {
            'indicator': 'RSI',
            'current_value': round(current_rsi, 4),
            'slopes': {k: round(v, 4) for k, v in slopes.items()},
            'analysis': analysis,
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def get_rsi_signals(self, data: pd.DataFrame, column: str = 'close') -> Dict:
        """RSI 기반 매수/매도 신호를 생성합니다."""
        rsi_series = self.calculate_rsi(data, column)
        return self.analyze_rsi_trend(rsi_series)
    
    def check_buy_condition(self, data: pd.DataFrame, column: str = 'close') -> Tuple[bool, Dict]:
        """RSI 매수 조건을 확인합니다."""
        try:
            signals = self.get_rsi_signals(data, column)
            buy_condition = signals['analysis']['buy_signal']
            return buy_condition, signals
        except Exception as e:
            return False, {'error': str(e)}
    
    def check_sell_condition(self, data: pd.DataFrame, column: str = 'close') -> Tuple[bool, Dict]:
        """RSI 매도 조건을 확인합니다."""
        try:
            signals = self.get_rsi_signals(data, column)
            sell_condition = signals['analysis']['sell_signal']
            return sell_condition, signals
        except Exception as e:
            return False, {'error': str(e)}


class RSIMonitor:
    """
    RSI 실시간 모니터링 클래스
    """
    
    def __init__(self, period: int = 14):
        self.calculator = RSICalculator(period)
        self.alert_levels = {
            'overbought': 70.0,
            'oversold': 30.0
        }
    
    def get_current_status(self, data: pd.DataFrame) -> Dict:
        """현재 RSI 상태를 조회합니다."""
        try:
            signals = self.calculator.get_rsi_signals(data)
            current_rsi = signals['current_value']
            
            alert_level = 'normal'
            if current_rsi >= self.alert_levels['overbought']:
                alert_level = 'overbought'
            elif current_rsi <= self.alert_levels['oversold']:
                alert_level = 'oversold'
            
            return {
                'rsi_value': current_rsi,
                'alert_level': alert_level,
                'buy_signal': signals['analysis']['buy_signal'],
                'sell_signal': signals['analysis']['sell_signal'],
                'slopes': signals['slopes'],
                'timestamp': signals['timestamp']
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': pd.Timestamp.now().isoformat()
            }
    
    def format_status_message(self, status: Dict) -> str:
        """상태를 사람이 읽기 쉬운 메시지로 포맷팅합니다."""
        if 'error' in status:
            return f"RSI Error: {status['error']}"
        
        rsi_val = status['rsi_value']
        alert = status['alert_level']
        
        message = f"RSI({rsi_val:.2f}) - {alert.upper()}"
        
        if status['buy_signal']:
            message += " BUY_SIGNAL"
        if status['sell_signal']:
            message += " SELL_SIGNAL"
        
        return message


# 편의 함수들
def calculate_rsi(data: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
    """
    RSI를 계산하는 편의 함수
    """
    calculator = RSICalculator(period)
    return calculator.calculate_rsi(data, column)


def get_rsi_buy_signal(data: pd.DataFrame, period: int = 14) -> Tuple[bool, Dict]:
    """
    RSI 매수 신호를 확인하는 편의 함수
    """
    calculator = RSICalculator(period)
    return calculator.check_buy_condition(data)


def get_rsi_sell_signal(data: pd.DataFrame, period: int = 14) -> Tuple[bool, Dict]:
    """
    RSI 매도 신호를 확인하는 편의 함수
    """
    calculator = RSICalculator(period)
    return calculator.check_sell_condition(data)