#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기술적 지표 모듈 사용 예제

Author: trading-strategy-analyzer
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.indicators import (
    RSICalculator, EMACalculator, RSIMonitor, EMAMonitor,
    calculate_rsi, calculate_ema, get_rsi_buy_signal, get_ema_buy_signal
)


def create_sample_data(periods=100, start_price=1000.0):
    """테스트용 샘플 OHLCV 데이터 생성"""
    np.random.seed(42)
    
    dates = pd.date_range(start=datetime.now() - timedelta(hours=periods), 
                         end=datetime.now(), freq='H')[:periods]
    
    # 가격 시뮬레이션
    price_changes = np.random.normal(0, 10, periods)
    prices = [start_price]
    
    for change in price_changes[1:]:
        new_price = max(prices[-1] + change, 100)
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


def main():
    """메인 함수"""
    print("=== 기술적 지표 모듈 사용 예제 ===")
    
    # 샘플 데이터 생성
    print("1. 샘플 데이터 생성 중...")
    data = create_sample_data(periods=100, start_price=1000)
    print(f"   완료: {len(data)}개 봉 데이터 생성")
    
    # RSI 분석
    print("\n2. RSI 분석")
    rsi_calc = RSICalculator(period=14)
    
    try:
        rsi_buy, rsi_analysis = rsi_calc.check_buy_condition(data)
        print(f"   RSI 매수 신호: {rsi_buy}")
        
        if 'error' not in rsi_analysis:
            print(f"   현재 RSI: {rsi_analysis['current_value']:.2f}")
            print(f"   RSI 기울기: {rsi_analysis['slopes']}")
        else:
            print(f"   오류: {rsi_analysis['error']}")
    except Exception as e:
        print(f"   RSI 계산 오류: {e}")
    
    # EMA 분석
    print("\n3. EMA 분석")
    ema_calc = EMACalculator(period=20)
    
    try:
        ema_buy, ema_analysis = ema_calc.check_buy_condition(data)
        print(f"   EMA 매수 신호: {ema_buy}")
        
        if 'error' not in ema_analysis:
            print(f"   현재 EMA: {ema_analysis['current_value']:.2f}")
            print(f"   EMA 기울기: {ema_analysis['slopes']}")
            if 'analysis' in ema_analysis:
                threshold_checks = ema_analysis['analysis']['signal_details']['threshold_checks']
                print(f"   임계값 확인: {threshold_checks}")
        else:
            print(f"   오류: {ema_analysis['error']}")
    except Exception as e:
        print(f"   EMA 계산 오류: {e}")
    
    # 복합 신호 판단
    print("\n4. 복합 매수 신호 판단")
    try:
        rsi_buy_simple, _ = get_rsi_buy_signal(data)
        ema_buy_simple, _ = get_ema_buy_signal(data)
        combined_signal = rsi_buy_simple and ema_buy_simple
        
        print(f"   RSI 신호: {rsi_buy_simple}")
        print(f"   EMA 신호: {ema_buy_simple}")
        print(f"   최종 매수 신호: {combined_signal}")
    except Exception as e:
        print(f"   복합 신호 계산 오류: {e}")
    
    # 모니터링 기능
    print("\n5. 실시간 모니터링")
    try:
        rsi_monitor = RSIMonitor()
        ema_monitor = EMAMonitor()
        
        rsi_status = rsi_monitor.get_current_status(data)
        ema_status = ema_monitor.get_current_status(data)
        
        print(f"   RSI: {rsi_monitor.format_status_message(rsi_status)}")
        print(f"   EMA: {ema_monitor.format_status_message(ema_status)}")
    except Exception as e:
        print(f"   모니터링 오류: {e}")
    
    # 편의 함수 테스트
    print("\n6. 편의 함수 테스트")
    try:
        rsi_series = calculate_rsi(data, period=14)
        ema_series = calculate_ema(data, period=20)
        
        print(f"   RSI 시리즈 길이: {len(rsi_series)}")
        print(f"   EMA 시리즈 길이: {len(ema_series)}")
        print(f"   최신 RSI: {rsi_series.iloc[-1]:.2f}")
        print(f"   최신 EMA: {ema_series.iloc[-1]:.2f}")
    except Exception as e:
        print(f"   편의 함수 오류: {e}")
    
    print("\n=== 테스트 완료 ===")


if __name__ == "__main__":
    main()