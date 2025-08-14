import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from .base import BaseIndicator, create_indicator_series, ensure_sufficient_data


class EMACalculator(BaseIndicator):
    """
    EMA 계산 및 분석 클래스
    
    매수 조건:
    - 직전 3봉 기울기 >= 0.3
    - 직전 5봉 기울기 >= 0.2
    
    매도 조건:
    - EMA(20) 직전 3봉 기울기가 지속적으로 감소
    """
    
    def __init__(self, period: int = 20):
        self.period = period
        self.min_required_data = period + 5
        
        # 매수 조건 임계값
        self.buy_thresholds = {
            3: 0.3,  # 직전 3봉 기울기 >= 0.3
            5: 0.2   # 직전 5봉 기울기 >= 0.2
        }
    
    def _calculate_ema_manual(self, price_series: pd.Series, period: int) -> pd.Series:
        """
        EMA를 수동으로 계산합니다.
        
        Args:
            price_series: 가격 시리즈
            period: EMA 계산 기간
            
        Returns:
            EMA 시리즈
        """
        return price_series.ewm(span=period, adjust=False).mean()
    
    def calculate_ema(self, data: pd.DataFrame, column: str = 'close') -> pd.Series:
        """
        EMA를 계산합니다.
        
        Args:
            data: OHLCV 데이터프레임
            column: EMA 계산에 사용할 컴럼
            
        Returns:
            EMA 시리즈
        """
        price_series = create_indicator_series(data, column)
        
        if not ensure_sufficient_data(price_series, self.min_required_data):
            raise ValueError(f"Insufficient data. Need at least {self.min_required_data} periods")
        
        ema_series = self._calculate_ema_manual(price_series, self.period)
        
        if ema_series is None or ema_series.isna().all():
            raise ValueError("Failed to calculate EMA")
        
        return ema_series
    
    def calculate_ema_slopes(self, ema_series: pd.Series, 
                           periods: List[int] = [3, 5]) -> Dict[str, float]:
        """
        EMA의 기울기를 계산합니다.
        
        Args:
            ema_series: EMA 시리즈
            periods: 기울기 계산 기간 리스트
            
        Returns:
            기간별 기울기 딕셔너리
        """
        return self.calculate_slopes(ema_series, periods)
    
    def check_buy_thresholds(self, slopes: Dict[str, float]) -> Dict[str, bool]:
        """
        매수 조건 임계값을 확인합니다.
        
        Args:
            slopes: 기울기 딕셔너리
            
        Returns:
            각 기간별 임계값 충족 여부
        """
        threshold_checks = {}
        
        for slope_key, slope_value in slopes.items():
            period = int(slope_key.split('_')[1])
            threshold = self.buy_thresholds.get(period, 0.0)
            threshold_checks[f'threshold_{period}'] = slope_value >= threshold
        
        return threshold_checks
    
    def analyze_ema_trend(self, ema_series: pd.Series, 
                         periods: List[int] = [3, 5]) -> Dict:
        """
        EMA 추세를 분석합니다.
        
        Args:
            ema_series: EMA 시리즈
            periods: 분석할 기간 리스트
            
        Returns:
            EMA 추세 분석 결과
        """
        if len(ema_series) < max(periods):
            raise ValueError(f"Insufficient data for slope analysis")
        
        current_ema = float(ema_series.iloc[-1])
        slopes = self.calculate_ema_slopes(ema_series, periods)
        
        # 매수 신호 조건 확인: 임계값 조건
        threshold_checks = self.check_buy_thresholds(slopes)
        buy_signal = all(threshold_checks.values())
        
        # 매도 신호 조건 확인: 3봉 기울기가 지속적으로 감소
        sell_signal = self.is_declining_trend(ema_series, lookback_periods=3)
        
        analysis = {
            'current_ema': current_ema,
            'slopes': slopes,
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'threshold_checks': threshold_checks,
            'all_thresholds_met': buy_signal,
            'declining_trend': sell_signal
        }
        
        return {
            'indicator': 'EMA',
            'current_value': round(current_ema, 4),
            'slopes': {k: round(v, 4) for k, v in slopes.items()},
            'analysis': analysis,
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def get_ema_signals(self, data: pd.DataFrame, column: str = 'close') -> Dict:
        """EMA 기반 매수/매도 신호를 생성합니다."""
        ema_series = self.calculate_ema(data, column)
        return self.analyze_ema_trend(ema_series)
    
    def check_buy_condition(self, data: pd.DataFrame, column: str = 'close') -> Tuple[bool, Dict]:
        """EMA 매수 조건을 확인합니다."""
        try:
            signals = self.get_ema_signals(data, column)
            buy_condition = signals['analysis']['buy_signal']
            return buy_condition, signals
        except Exception as e:
            return False, {'error': str(e)}
    
    def check_sell_condition(self, data: pd.DataFrame, column: str = 'close') -> Tuple[bool, Dict]:
        """EMA 매도 조건을 확인합니다."""
        try:
            signals = self.get_ema_signals(data, column)
            sell_condition = signals['analysis']['sell_signal']
            return sell_condition, signals
        except Exception as e:
            return False, {'error': str(e)}
    
    def is_declining_trend(self, ema_series: pd.Series, lookback_periods: int = 3) -> bool:
        """
        EMA가 지속적으로 감소하는 추세인지 확인합니다.
        
        Args:
            ema_series: EMA 시리즈
            lookback_periods: 확인할 기간
            
        Returns:
            감소 추세이면 True
        """
        if len(ema_series) < lookback_periods + 1:
            return False
        
        recent_values = ema_series.iloc[-lookback_periods-1:].values
        
        # 연속적으로 감소하는지 확인
        for i in range(1, len(recent_values)):
            if recent_values[i] >= recent_values[i-1]:
                return False
        
        return True


class EMAMonitor:
    """
    EMA 실시간 모니터링 클래스
    """
    
    def __init__(self, period: int = 20):
        self.calculator = EMACalculator(period)
    
    def get_current_status(self, data: pd.DataFrame) -> Dict:
        """현재 EMA 상태를 조회합니다."""
        try:
            signals = self.calculator.get_ema_signals(data)
            current_ema = signals['current_value']
            current_price = float(data['close'].iloc[-1])
            
            distance = current_price - current_ema
            distance_pct = (distance / current_ema) * 100 if current_ema != 0 else 0
            
            return {
                'ema_value': current_ema,
                'current_price': current_price,
                'distance': distance,
                'distance_percentage': distance_pct,
                'above_ema': distance > 0,
                'buy_signal': signals['analysis']['buy_signal'],
                'sell_signal': signals['analysis']['sell_signal'],
                'slopes': signals['slopes'],
                'threshold_checks': signals['analysis']['threshold_checks'],
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
            return f"EMA Error: {status['error']}"
        
        ema_val = status['ema_value']
        price = status['current_price']
        distance = status['distance_percentage']
        
        message = f"EMA({ema_val:.2f}) Price({price:.0f}) Distance({distance:+.2f}%)"
        
        if status['buy_signal']:
            message += " BUY_SIGNAL"
        if status['sell_signal']:
            message += " SELL_SIGNAL"
        
        return message


# 편의 함수들
def calculate_ema(data: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
    """
    EMA를 계산하는 편의 함수
    """
    calculator = EMACalculator(period)
    return calculator.calculate_ema(data, column)


def get_ema_buy_signal(data: pd.DataFrame, period: int = 20) -> Tuple[bool, Dict]:
    """
    EMA 매수 신호를 확인하는 편의 함수
    """
    calculator = EMACalculator(period)
    return calculator.check_buy_condition(data)


def get_ema_sell_signal(data: pd.DataFrame, period: int = 20) -> Tuple[bool, Dict]:
    """
    EMA 매도 신호를 확인하는 편의 함수
    """
    calculator = EMACalculator(period)
    return calculator.check_sell_condition(data)