import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

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
    print("=== Technical Indicators Test ===")
    
    # Create sample data
    print("1. Creating sample data...")
    data = create_sample_data(periods=50, start_price=1000)
    print(f"   Complete: {len(data)} bars of data")
    
    # RSI test
    print("\\n2. RSI Test")
    try:
        rsi_calc = RSICalculator(period=14)
        rsi_buy, rsi_analysis = rsi_calc.check_buy_condition(data)
        print(f"   RSI Buy Signal: {rsi_buy}")
        
        if 'error' not in rsi_analysis:
            print(f"   Current RSI: {rsi_analysis['current_value']:.2f}")
            print(f"   RSI Slopes: {rsi_analysis['slopes']}")
        else:
            print(f"   Error: {rsi_analysis['error']}")
    except Exception as e:
        print(f"   RSI Error: {e}")
    
    # EMA test
    print("\\n3. EMA Test")
    try:
        ema_calc = EMACalculator(period=20)
        ema_buy, ema_analysis = ema_calc.check_buy_condition(data)
        print(f"   EMA Buy Signal: {ema_buy}")
        
        if 'error' not in ema_analysis:
            print(f"   Current EMA: {ema_analysis['current_value']:.2f}")
            print(f"   EMA Slopes: {ema_analysis['slopes']}")
            threshold_checks = ema_analysis['analysis']['threshold_checks']
            print(f"   Threshold Checks: {threshold_checks}")
        else:
            print(f"   Error: {ema_analysis['error']}")
    except Exception as e:
        print(f"   EMA Error: {e}")
    
    # Combined signal
    print("\\n4. Combined Buy Signal")
    try:
        rsi_buy_simple, _ = get_rsi_buy_signal(data)
        ema_buy_simple, _ = get_ema_buy_signal(data)
        combined_signal = rsi_buy_simple and ema_buy_simple
        
        print(f"   RSI Signal: {rsi_buy_simple}")
        print(f"   EMA Signal: {ema_buy_simple}")
        print(f"   Final Buy Signal: {combined_signal}")
    except Exception as e:
        print(f"   Combined Signal Error: {e}")
    
    # Monitoring
    print("\\n5. Monitoring Test")
    try:
        rsi_monitor = RSIMonitor()
        ema_monitor = EMAMonitor()
        
        rsi_status = rsi_monitor.get_current_status(data)
        ema_status = ema_monitor.get_current_status(data)
        
        print(f"   RSI: {rsi_monitor.format_status_message(rsi_status)}")
        print(f"   EMA: {ema_monitor.format_status_message(ema_status)}")
    except Exception as e:
        print(f"   Monitoring Error: {e}")
    
    print("\\n=== Test Complete ===")


if __name__ == "__main__":
    main()