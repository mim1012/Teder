#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
        
        data.append({\n            'timestamp': dates[i],\n            'open': open_price,\n            'high': high,\n            'low': low,\n            'close': close_price,\n            'volume': volume\n        })\n    \n    return pd.DataFrame(data)\n\n\ndef main():\n    print(\"=== 기술적 지표 모듈 테스트 ===\")\n    \n    # 샘플 데이터 생성\n    print(\"1. 샘플 데이터 생성...\")\n    data = create_sample_data(periods=50, start_price=1000)\n    print(f\"   완료: {len(data)}개 봉 데이터\")\n    \n    # RSI 테스트\n    print(\"\\n2. RSI 테스트\")\n    try:\n        rsi_calc = RSICalculator(period=14)\n        rsi_buy, rsi_analysis = rsi_calc.check_buy_condition(data)\n        print(f\"   RSI 매수 신호: {rsi_buy}\")\n        \n        if 'error' not in rsi_analysis:\n            print(f\"   현재 RSI: {rsi_analysis['current_value']:.2f}\")\n            print(f\"   RSI 기울기: {rsi_analysis['slopes']}\")\n        else:\n            print(f\"   오류: {rsi_analysis['error']}\")\n    except Exception as e:\n        print(f\"   RSI 오류: {e}\")\n    \n    # EMA 테스트\n    print(\"\\n3. EMA 테스트\")\n    try:\n        ema_calc = EMACalculator(period=20)\n        ema_buy, ema_analysis = ema_calc.check_buy_condition(data)\n        print(f\"   EMA 매수 신호: {ema_buy}\")\n        \n        if 'error' not in ema_analysis:\n            print(f\"   현재 EMA: {ema_analysis['current_value']:.2f}\")\n            print(f\"   EMA 기울기: {ema_analysis['slopes']}\")\n            threshold_checks = ema_analysis['analysis']['threshold_checks']\n            print(f\"   임계값 확인: {threshold_checks}\")\n        else:\n            print(f\"   오류: {ema_analysis['error']}\")\n    except Exception as e:\n        print(f\"   EMA 오류: {e}\")\n    \n    # 복합 신호\n    print(\"\\n4. 복합 매수 신호\")\n    try:\n        rsi_buy_simple, _ = get_rsi_buy_signal(data)\n        ema_buy_simple, _ = get_ema_buy_signal(data)\n        combined_signal = rsi_buy_simple and ema_buy_simple\n        \n        print(f\"   RSI 신호: {rsi_buy_simple}\")\n        print(f\"   EMA 신호: {ema_buy_simple}\")\n        print(f\"   최종 매수 신호: {combined_signal}\")\n    except Exception as e:\n        print(f\"   복합 신호 오류: {e}\")\n    \n    # 모니터링\n    print(\"\\n5. 모니터링 테스트\")\n    try:\n        rsi_monitor = RSIMonitor()\n        ema_monitor = EMAMonitor()\n        \n        rsi_status = rsi_monitor.get_current_status(data)\n        ema_status = ema_monitor.get_current_status(data)\n        \n        print(f\"   RSI: {rsi_monitor.format_status_message(rsi_status)}\")\n        print(f\"   EMA: {ema_monitor.format_status_message(ema_status)}\")\n    except Exception as e:\n        print(f\"   모니터링 오류: {e}\")\n    \n    print(\"\\n=== 테스트 완료 ===\")\n\n\nif __name__ == \"__main__\":\n    main()