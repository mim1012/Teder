#!/usr/bin/env python3
"""
분할매수 전략 간단 테스트
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=== Split Buy Strategy Simple Test ===")
print("Testing indicator imports...")

try:
    from src.indicators.rsi_short import RSIShort, RSIEMAShort
    print("- RSIShort, RSIEMAShort: OK")
except ImportError as e:
    print(f"- RSIShort, RSIEMAShort: Failed - {e}")

try:
    from src.indicators.price_ema import PriceEMA
    print("- PriceEMA: OK")
except ImportError as e:
    print(f"- PriceEMA: Failed - {e}")

try:
    from src.indicators.rsi import RSICalculator
    print("- RSICalculator: OK")
except ImportError as e:
    print(f"- RSICalculator: Failed - {e}")

print("\nGenerating test data...")
# 샘플 데이터 생성
dates = pd.date_range(end=datetime.now(), periods=100, freq='h')
prices = np.random.normal(1300, 10, 100)
prices = pd.Series(prices).ewm(span=5).mean().values  # 스무딩

data = pd.DataFrame({
    'timestamp': dates,
    'open': prices * 0.99,
    'high': prices * 1.01,
    'low': prices * 0.98,
    'close': prices,
    'volume': np.random.uniform(100, 1000, 100)
})

print(f"Generated {len(data)} hourly candles")
print(f"Price range: {data['close'].min():.2f} ~ {data['close'].max():.2f}")

print("\nTesting indicators...")

# RSI(9) 테스트
try:
    rsi_9 = RSIShort(period=9)
    rsi_values = rsi_9.calculate(data)
    print(f"RSI(9) latest: {rsi_values.iloc[-1]:.2f}")
    
    from src.indicators.base import BaseIndicator
    slopes = BaseIndicator.calculate_slopes(rsi_values, [3])
    print(f"RSI(9) 3-bar slope: {slopes.get('slope_3', 0):.2f}")
except Exception as e:
    print(f"RSI(9) test failed: {e}")

# RSI(9) EMA(5) 테스트
try:
    rsi_ema = RSIEMAShort(rsi_period=9, ema_period=5)
    rsi_ema_values = rsi_ema.calculate(data)
    print(f"RSI(9) EMA(5) latest: {rsi_ema_values.iloc[-1]:.2f}")
    
    slopes = BaseIndicator.calculate_slopes(rsi_ema_values, [2])
    print(f"RSI(9) EMA(5) 2-bar slope: {slopes.get('slope_2', 0):.2f}")
except Exception as e:
    print(f"RSI(9) EMA(5) test failed: {e}")

# Price EMA(5) 테스트
try:
    price_ema = PriceEMA(period=5)
    ema_values = price_ema.calculate(data)
    print(f"Price EMA(5) latest: {ema_values.iloc[-1]:.2f}")
    
    slopes = BaseIndicator.calculate_slopes(ema_values, [2])
    print(f"Price EMA(5) 2-bar slope: {slopes.get('slope_2', 0):.2f}")
except Exception as e:
    print(f"Price EMA(5) test failed: {e}")

# RSI(14) 테스트
try:
    rsi_14 = RSICalculator(period=14)
    rsi_14_values = rsi_14.calculate_rsi(data)
    print(f"RSI(14) latest: {rsi_14_values.iloc[-1]:.2f}")
except Exception as e:
    print(f"RSI(14) test failed: {e}")

# 매수 조건 체크
print("\n=== Buy Condition Check ===")
try:
    rsi_9 = RSIShort(period=9)
    rsi_ema = RSIEMAShort(rsi_period=9, ema_period=5)
    price_ema = PriceEMA(period=5)
    
    # RSI(9) 조건
    rsi_values = rsi_9.calculate(data)
    from src.indicators.base import BaseIndicator
    rsi_slopes = BaseIndicator.calculate_slopes(rsi_values, [3])
    rsi_slope_3 = rsi_slopes.get('slope_3', 0)
    rsi_current = rsi_values.iloc[-1]
    
    # RSI EMA 조건
    rsi_ema_values = rsi_ema.calculate(data)
    rsi_ema_slopes = BaseIndicator.calculate_slopes(rsi_ema_values, [2])
    rsi_ema_slope_2 = rsi_ema_slopes.get('slope_2', 0)
    
    # Price EMA 조건
    ema_values = price_ema.calculate(data)
    ema_slopes = BaseIndicator.calculate_slopes(ema_values, [2])
    ema_slope_2 = ema_slopes.get('slope_2', 0)
    
    print(f"1. RSI(9) 3-bar slope > 3: {rsi_slope_3:.2f} > 3 = {rsi_slope_3 > 3}")
    print(f"2. RSI(9) EMA(5) 2-bar slope > 1: {rsi_ema_slope_2:.2f} > 1 = {rsi_ema_slope_2 > 1}")
    print(f"3. Price EMA(5) 2-bar slope > 0.2: {ema_slope_2:.2f} > 0.2 = {ema_slope_2 > 0.2}")
    print(f"4. RSI(9) < 70: {rsi_current:.2f} < 70 = {rsi_current < 70}")
    
    all_conditions = (
        rsi_slope_3 > 3 and
        rsi_ema_slope_2 > 1 and
        ema_slope_2 > 0.2 and
        rsi_current < 70
    )
    
    print(f"\nBuy Signal: {all_conditions}")
    
except Exception as e:
    print(f"Buy condition check failed: {e}")

print("\n=== Test Complete ===")