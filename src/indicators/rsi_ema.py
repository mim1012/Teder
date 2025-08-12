import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from .base import BaseIndicator, create_indicator_series, ensure_sufficient_data
from .rsi import RSICalculator


class RSIEMACalculator(BaseIndicator):
    """
    RSI 값에 대한 EMA 계산 및 분석 클래스
    
    프로세스:
    1. RSI(14) 계산
    2. RSI 값들에 대한 EMA(20) 계산
    3. RSI-EMA 기울기 분석
    
    매수 조건:
    - RSI-EMA 직전 3봉 기울기 >= 0.3
    - RSI-EMA 직전 5봉 기울기 >= 0.2
    
    매도 조건:
    - RSI-EMA 직전 3봉 기울기가 지속적으로 감소
    """
    
    def __init__(self, rsi_period: int = 14, ema_period: int = 20):
        self.rsi_period = rsi_period
        self.ema_period = ema_period
        self.rsi_calculator = RSICalculator(rsi_period)
        
        # 충분한 데이터 요구량: RSI 계산 + EMA 계산 + 기울기 분석
        self.min_required_data = rsi_period + ema_period + 5
        
        # 매수 조건 임계값
        self.buy_thresholds = {
            3: 0.3,  # 직전 3봉 기울기 >= 0.3
            5: 0.2   # 직전 5봉 기울기 >= 0.2
        }
    
    def _calculate_ema_on_series(self, series: pd.Series, period: int) -> pd.Series:
        """
        주어진 시리즈에 대해 EMA를 계산합니다.
        
        Args:
            series: 입력 시리즈
            period: EMA 계산 기간
            
        Returns:
            EMA 시리즈
        """
        return series.ewm(span=period, adjust=False).mean()
    
    def calculate_rsi_ema(self, data: pd.DataFrame, column: str = 'close') -> pd.Series:
        """
        RSI 값에 대한 EMA를 계산합니다.
        
        Args:
            data: OHLCV 데이터프레임
            column: RSI 계산에 사용할 컬럼
            
        Returns:
            RSI-EMA 시리즈
        """
        price_series = create_indicator_series(data, column)
        
        if not ensure_sufficient_data(price_series, self.min_required_data):
            raise ValueError(f"Insufficient data. Need at least {self.min_required_data} periods")
        
        # 1단계: RSI 계산
        rsi_series = self.rsi_calculator.calculate_rsi(data, column)
        
        # 2단계: RSI 값들에 대한 EMA 계산
        rsi_ema_series = self._calculate_ema_on_series(rsi_series, self.ema_period)
        
        if rsi_ema_series is None or rsi_ema_series.isna().all():
            raise ValueError("Failed to calculate RSI-EMA")
        
        return rsi_ema_series
    
    def calculate_rsi_ema_slopes(self, rsi_ema_series: pd.Series, 
                               periods: List[int] = [3, 5]) -> Dict[str, float]:
        """
        RSI-EMA의 기울기를 계산합니다.
        
        Args:
            rsi_ema_series: RSI-EMA 시리즈
            periods: 기울기 계산 기간 리스트
            
        Returns:
            기간별 기울기 딕셔너리
        """
        return self.calculate_slopes(rsi_ema_series, periods)
    
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
    
    def is_declining_trend(self, rsi_ema_series: pd.Series, lookback_periods: int = 3) -> bool:
        """
        RSI-EMA가 지속적으로 감소하는 추세인지 확인합니다.
        
        Args:
            rsi_ema_series: RSI-EMA 시리즈
            lookback_periods: 확인할 기간
            
        Returns:
            감소 추세이면 True
        """
        if len(rsi_ema_series) < lookback_periods + 1:
            return False
        
        recent_values = rsi_ema_series.iloc[-lookback_periods-1:].values
        
        # 연속적으로 감소하는지 확인
        for i in range(1, len(recent_values)):
            if recent_values[i] >= recent_values[i-1]:
                return False
        
        return True
    
    def analyze_rsi_ema_trend(self, rsi_ema_series: pd.Series, 
                            periods: List[int] = [3, 5]) -> Dict:
        """
        RSI-EMA 추세를 분석합니다.
        
        Args:
            rsi_ema_series: RSI-EMA 시리즈
            periods: 분석할 기간 리스트
            
        Returns:
            RSI-EMA 추세 분석 결과
        """
        if len(rsi_ema_series) < max(periods):
            raise ValueError(f"Insufficient data for slope analysis")
        
        current_rsi_ema = float(rsi_ema_series.iloc[-1])
        slopes = self.calculate_rsi_ema_slopes(rsi_ema_series, periods)
        
        # 매수 신호 조건 확인: 임계값 조건
        threshold_checks = self.check_buy_thresholds(slopes)
        buy_signal = all(threshold_checks.values())
        
        # 매도 신호 조건 확인: 3봉 기울기가 지속적으로 감소
        sell_signal = self.is_declining_trend(rsi_ema_series, lookback_periods=3)
        
        analysis = {
            'current_rsi_ema': current_rsi_ema,
            'slopes': slopes,
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'threshold_checks': threshold_checks,
            'all_thresholds_met': buy_signal,
            'declining_trend': sell_signal
        }
        
        return {
            'indicator': 'RSI_EMA',
            'current_value': round(current_rsi_ema, 4),
            'slopes': {k: round(v, 4) for k, v in slopes.items()},
            'analysis': analysis,
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def get_rsi_ema_signals(self, data: pd.DataFrame, column: str = 'close') -> Dict:
        """RSI-EMA 기반 매수/매도 신호를 생성합니다."""
        rsi_ema_series = self.calculate_rsi_ema(data, column)
        return self.analyze_rsi_ema_trend(rsi_ema_series)
    
    def check_buy_condition(self, data: pd.DataFrame, column: str = 'close') -> Tuple[bool, Dict]:
        """RSI-EMA 매수 조건을 확인합니다."""
        try:
            signals = self.get_rsi_ema_signals(data, column)
            buy_condition = signals['analysis']['buy_signal']
            return buy_condition, signals
        except Exception as e:
            return False, {'error': str(e)}
    
    def check_sell_condition(self, data: pd.DataFrame, column: str = 'close') -> Tuple[bool, Dict]:
        """RSI-EMA 매도 조건을 확인합니다."""
        try:
            signals = self.get_rsi_ema_signals(data, column)
            sell_condition = signals['analysis']['sell_signal']
            return sell_condition, signals
        except Exception as e:
            return False, {'error': str(e)}
    
    def get_detailed_analysis(self, data: pd.DataFrame, column: str = 'close') -> Dict:
        """
        RSI-EMA 상세 분석을 제공합니다.
        
        Returns:
            RSI, RSI-EMA, 기울기 등의 상세 정보
        """
        try:
            # RSI 계산
            rsi_series = self.rsi_calculator.calculate_rsi(data, column)
            current_rsi = float(rsi_series.iloc[-1])
            
            # RSI-EMA 계산
            rsi_ema_series = self.calculate_rsi_ema(data, column)
            current_rsi_ema = float(rsi_ema_series.iloc[-1])
            
            # 기울기 및 신호 분석
            signals = self.get_rsi_ema_signals(data, column)
            
            return {
                'rsi_value': round(current_rsi, 4),
                'rsi_ema_value': round(current_rsi_ema, 4),
                'rsi_ema_difference': round(current_rsi - current_rsi_ema, 4),
                'slopes': signals['slopes'],
                'threshold_checks': signals['analysis']['threshold_checks'],
                'buy_signal': signals['analysis']['buy_signal'],
                'sell_signal': signals['analysis']['sell_signal'],
                'analysis_summary': {
                    'rsi_above_ema': current_rsi > current_rsi_ema,
                    'momentum_strength': self._assess_momentum_strength(signals['slopes']),
                    'trend_direction': self._assess_trend_direction(signals['slopes'])
                },
                'timestamp': signals['timestamp']
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': pd.Timestamp.now().isoformat()
            }
    
    def _assess_momentum_strength(self, slopes: Dict[str, float]) -> str:
        """모멘텀 강도를 평가합니다."""
        slope_3 = slopes.get('slope_3', 0.0)
        slope_5 = slopes.get('slope_5', 0.0)
        
        if slope_3 >= 0.5 and slope_5 >= 0.3:
            return 'Strong'
        elif slope_3 >= 0.3 and slope_5 >= 0.2:
            return 'Moderate'
        elif slope_3 > 0 and slope_5 > 0:
            return 'Weak'
        else:
            return 'Negative'
    
    def _assess_trend_direction(self, slopes: Dict[str, float]) -> str:
        """추세 방향을 평가합니다."""
        slope_3 = slopes.get('slope_3', 0.0)
        slope_5 = slopes.get('slope_5', 0.0)
        
        if slope_3 > 0 and slope_5 > 0:
            return 'Uptrend'
        elif slope_3 < 0 and slope_5 < 0:
            return 'Downtrend'
        else:
            return 'Sideways'


class RSIEMAMonitor:
    """
    RSI-EMA 실시간 모니터링 클래스
    """
    
    def __init__(self, rsi_period: int = 14, ema_period: int = 20):
        self.calculator = RSIEMACalculator(rsi_period, ema_period)
        self.alert_levels = {
            'rsi_overbought': 70.0,
            'rsi_oversold': 30.0,
            'strong_momentum_threshold': 0.5
        }
    
    def get_current_status(self, data: pd.DataFrame) -> Dict:
        """현재 RSI-EMA 상태를 조회합니다."""
        try:
            detailed_analysis = self.calculator.get_detailed_analysis(data)
            
            if 'error' in detailed_analysis:
                return detailed_analysis
            
            # 알림 레벨 결정
            alert_level = 'normal'
            rsi_value = detailed_analysis['rsi_value']
            
            if rsi_value >= self.alert_levels['rsi_overbought']:
                alert_level = 'overbought'
            elif rsi_value <= self.alert_levels['rsi_oversold']:
                alert_level = 'oversold'
            elif detailed_analysis['analysis_summary']['momentum_strength'] == 'Strong':
                alert_level = 'strong_momentum'
            
            return {
                'rsi_value': detailed_analysis['rsi_value'],
                'rsi_ema_value': detailed_analysis['rsi_ema_value'],
                'rsi_ema_difference': detailed_analysis['rsi_ema_difference'],
                'alert_level': alert_level,
                'buy_signal': detailed_analysis['buy_signal'],
                'sell_signal': detailed_analysis['sell_signal'],
                'slopes': detailed_analysis['slopes'],
                'momentum_strength': detailed_analysis['analysis_summary']['momentum_strength'],
                'trend_direction': detailed_analysis['analysis_summary']['trend_direction'],
                'threshold_checks': detailed_analysis['threshold_checks'],
                'timestamp': detailed_analysis['timestamp']
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': pd.Timestamp.now().isoformat()
            }
    
    def format_status_message(self, status: Dict) -> str:
        """상태를 사람이 읽기 쉬운 메시지로 포맷팅합니다."""
        if 'error' in status:
            return f"RSI-EMA Error: {status['error']}"
        
        rsi_val = status['rsi_value']
        rsi_ema_val = status['rsi_ema_value']
        momentum = status['momentum_strength']
        trend = status['trend_direction']
        
        message = f"RSI({rsi_val:.2f}) RSI-EMA({rsi_ema_val:.2f}) {momentum} {trend}"
        
        if status['buy_signal']:
            message += " BUY_SIGNAL"
        if status['sell_signal']:
            message += " SELL_SIGNAL"
        
        return message


# 편의 함수들
def calculate_rsi_ema(data: pd.DataFrame, rsi_period: int = 14, ema_period: int = 20, 
                     column: str = 'close') -> pd.Series:
    """
    RSI-EMA를 계산하는 편의 함수
    """
    calculator = RSIEMACalculator(rsi_period, ema_period)
    return calculator.calculate_rsi_ema(data, column)


def get_rsi_ema_buy_signal(data: pd.DataFrame, rsi_period: int = 14, 
                          ema_period: int = 20) -> Tuple[bool, Dict]:
    """
    RSI-EMA 매수 신호를 확인하는 편의 함수
    """
    calculator = RSIEMACalculator(rsi_period, ema_period)
    return calculator.check_buy_condition(data)


def get_rsi_ema_sell_signal(data: pd.DataFrame, rsi_period: int = 14, 
                           ema_period: int = 20) -> Tuple[bool, Dict]:
    """
    RSI-EMA 매도 신호를 확인하는 편의 함수
    """
    calculator = RSIEMACalculator(rsi_period, ema_period)
    return calculator.check_sell_condition(data)


def get_rsi_ema_detailed_analysis(data: pd.DataFrame, rsi_period: int = 14, 
                                 ema_period: int = 20) -> Dict:
    """
    RSI-EMA 상세 분석을 제공하는 편의 함수
    """
    calculator = RSIEMACalculator(rsi_period, ema_period)
    return calculator.get_detailed_analysis(data)