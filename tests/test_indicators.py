"""
기술적 지표 모듈 테스트

Author: trading-strategy-analyzer
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.indicators import (
    RSICalculator, EMACalculator, RSIMonitor, EMAMonitor,
    calculate_rsi, calculate_ema, get_rsi_buy_signal, get_ema_buy_signal
)


def create_sample_data(periods: int = 100, start_price: float = 1000.0) -> pd.DataFrame:
    """
    테스트용 샘플 OHLCV 데이터 생성
    
    Args:
        periods: 데이터 기간
        start_price: 시작 가격
        
    Returns:
        샘플 OHLCV 데이터프레임
    """
    np.random.seed(42)  # 재현 가능한 결과를 위한 시드 설정
    
    dates = pd.date_range(start=datetime.now() - timedelta(hours=periods), 
                         end=datetime.now(), freq='H')[:periods]
    
    # 가격 시뮬레이션 (랜덤 워크)
    price_changes = np.random.normal(0, 10, periods)  # 평균 0, 표준편차 10
    prices = [start_price]
    
    for change in price_changes[1:]:
        new_price = max(prices[-1] + change, 100)  # 최소 가격 100원
        prices.append(new_price)
    
    # OHLCV 데이터 생성
    data = []
    for i, price in enumerate(prices):
        high = price + abs(np.random.normal(0, 5))
        low = price - abs(np.random.normal(0, 5))
        open_price = prices[i-1] if i > 0 else price
        close_price = price
        volume = np.random.randint(1000, 10000)
        
        data.append({
            'timestamp': dates[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })
    
    return pd.DataFrame(data)


class TestRSICalculator:
    """RSI 계산기 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.rsi_calc = RSICalculator(period=14)
        self.sample_data = create_sample_data(periods=50)
    
    def test_rsi_calculation(self):
        """RSI 계산 테스트"""
        rsi_series = self.rsi_calc.calculate_rsi(self.sample_data)
        
        assert isinstance(rsi_series, pd.Series)
        assert len(rsi_series) > 0
        assert not rsi_series.isna().all()
        
        # RSI 값이 0-100 범위에 있는지 확인
        valid_rsi = rsi_series.dropna()
        assert all(0 <= val <= 100 for val in valid_rsi)
    
    def test_rsi_slopes_calculation(self):
        """RSI 기울기 계산 테스트"""
        rsi_series = self.rsi_calc.calculate_rsi(self.sample_data)
        slopes = self.rsi_calc.calculate_rsi_slopes(rsi_series)
        
        assert isinstance(slopes, dict)
        assert 'slope_3' in slopes
        assert 'slope_5' in slopes
        assert isinstance(slopes['slope_3'], float)
        assert isinstance(slopes['slope_5'], float)
    
    def test_rsi_buy_condition(self):
        """RSI 매수 조건 테스트"""
        buy_condition, analysis = self.rsi_calc.check_buy_condition(self.sample_data)
        
        assert isinstance(buy_condition, bool)
        assert isinstance(analysis, dict)
        
        if 'error' not in analysis:
            assert 'analysis' in analysis
            assert 'slopes' in analysis


class TestEMACalculator:
    """EMA 계산기 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.ema_calc = EMACalculator(period=20)
        self.sample_data = create_sample_data(periods=50)
    
    def test_ema_calculation(self):
        """EMA 계산 테스트"""
        ema_series = self.ema_calc.calculate_ema(self.sample_data)
        
        assert isinstance(ema_series, pd.Series)
        assert len(ema_series) > 0
        assert not ema_series.isna().all()
        
        # EMA 값이 양수인지 확인
        valid_ema = ema_series.dropna()
        assert all(val > 0 for val in valid_ema)
    
    def test_ema_slopes_calculation(self):
        """EMA 기울기 계산 테스트"""
        ema_series = self.ema_calc.calculate_ema(self.sample_data)
        slopes = self.ema_calc.calculate_ema_slopes(ema_series)
        
        assert isinstance(slopes, dict)
        assert 'slope_3' in slopes
        assert 'slope_5' in slopes
        assert isinstance(slopes['slope_3'], float)
        assert isinstance(slopes['slope_5'], float)
    
    def test_ema_buy_thresholds(self):
        """EMA 매수 임계값 확인 테스트"""
        ema_series = self.ema_calc.calculate_ema(self.sample_data)
        slopes = self.ema_calc.calculate_ema_slopes(ema_series)
        threshold_checks = self.ema_calc.check_buy_thresholds(slopes)
        
        assert isinstance(threshold_checks, dict)
        assert 'threshold_3' in threshold_checks
        assert 'threshold_5' in threshold_checks
        assert isinstance(threshold_checks['threshold_3'], bool)
        assert isinstance(threshold_checks['threshold_5'], bool)


class TestIndicatorIntegration:
    """지표 통합 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.sample_data = create_sample_data(periods=100)
    
    def test_convenience_functions(self):
        """편의 함수 테스트"""
        # RSI 편의 함수
        rsi_series = calculate_rsi(self.sample_data)
        assert isinstance(rsi_series, pd.Series)
        
        rsi_buy_signal, rsi_analysis = get_rsi_buy_signal(self.sample_data)
        assert isinstance(rsi_buy_signal, bool)
        assert isinstance(rsi_analysis, dict)
        
        # EMA 편의 함수
        ema_series = calculate_ema(self.sample_data)
        assert isinstance(ema_series, pd.Series)
        
        ema_buy_signal, ema_analysis = get_ema_buy_signal(self.sample_data)
        assert isinstance(ema_buy_signal, bool)
        assert isinstance(ema_analysis, dict)
    
    def test_combined_trading_signals(self):
        """복합 매매 신호 테스트"""
        rsi_buy, rsi_data = get_rsi_buy_signal(self.sample_data)
        ema_buy, ema_data = get_ema_buy_signal(self.sample_data)
        
        # 두 신호가 모두 True일 때만 매수
        combined_buy_signal = rsi_buy and ema_buy
        
        print(f"RSI Buy Signal: {rsi_buy}")
        print(f"EMA Buy Signal: {ema_buy}")
        print(f"Combined Buy Signal: {combined_buy_signal}")
        
        assert isinstance(combined_buy_signal, bool)


class TestMonitoringClasses:
    """모니터링 클래스 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.sample_data = create_sample_data(periods=100)
        self.rsi_monitor = RSIMonitor()
        self.ema_monitor = EMAMonitor()
    
    def test_rsi_monitor(self):
        """RSI 모니터 테스트"""
        status = self.rsi_monitor.get_current_status(self.sample_data)
        
        if 'error' not in status:
            assert 'rsi_value' in status
            assert 'alert_level' in status
            assert 'buy_signal' in status
            assert 'sell_signal' in status
            
            # 메시지 포맷팅 테스트
            message = self.rsi_monitor.format_status_message(status)
            assert isinstance(message, str)
            assert len(message) > 0
    
    def test_ema_monitor(self):
        """EMA 모니터 테스트"""
        status = self.ema_monitor.get_current_status(self.sample_data)
        
        if 'error' not in status:
            assert 'ema_value' in status
            assert 'current_price' in status
            assert 'distance_info' in status
            assert 'trend_level' in status
            
            # 메시지 포맷팅 테스트
            message = self.ema_monitor.format_status_message(status)
            assert isinstance(message, str)
            assert len(message) > 0


def test_sample_usage():
    """샘플 사용법 데모"""
    print("\n=== 기술적 지표 모듈 사용 예제 ===")
    
    # 샘플 데이터 생성
    data = create_sample_data(periods=100, start_price=1000)
    print(f"샘플 데이터 생성 완료: {len(data)}개 봉")
    
    # RSI 분석
    rsi_calc = RSICalculator()
    rsi_buy, rsi_analysis = rsi_calc.check_buy_condition(data)
    print(f"\nRSI 매수 신호: {rsi_buy}")
    if 'analysis' in rsi_analysis:
        print(f"현재 RSI: {rsi_analysis['current_value']:.2f}")
        print(f"RSI 기울기: {rsi_analysis['slopes']}")
    
    # EMA 분석
    ema_calc = EMACalculator()
    ema_buy, ema_analysis = ema_calc.check_buy_condition(data)
    print(f"\nEMA 매수 신호: {ema_buy}")
    if 'analysis' in ema_analysis:
        print(f"현재 EMA: {ema_analysis['current_value']:.2f}")
        print(f"EMA 기울기: {ema_analysis['slopes']}")
    
    # 복합 신호
    combined_signal = rsi_buy and ema_buy
    print(f"\n=== 최종 매수 신호: {combined_signal} ===")
    
    # 모니터링
    rsi_monitor = RSIMonitor()
    ema_monitor = EMAMonitor()
    
    print(f"\nRSI 상태: {rsi_monitor.format_status_message(rsi_monitor.get_current_status(data))}")
    print(f"EMA 상태: {ema_monitor.format_status_message(ema_monitor.get_current_status(data))}")


if __name__ == "__main__":
    # 직접 실행시 샘플 사용법 실행
    test_sample_usage()