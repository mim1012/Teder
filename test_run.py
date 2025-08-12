"""
Quick test to check if everything is working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

# Core imports
try:
    import pandas
    print("OK pandas")
except:
    print("FAIL pandas")

try:
    import numpy
    print("OK numpy")
except:
    print("FAIL numpy")

try:
    import requests
    print("OK requests")
except:
    print("FAIL requests")

try:
    from dotenv import load_dotenv
    print("OK python-dotenv")
except:
    print("FAIL python-dotenv")

# Project imports
try:
    from src.api.coinone_client import CoinoneClient
    print("OK CoinoneClient")
except Exception as e:
    print(f"FAIL CoinoneClient: {e}")

try:
    from src.indicators.rsi import RSICalculator
    print("OK RSICalculator")
except Exception as e:
    print(f"FAIL RSICalculator: {e}")

try:
    from src.indicators.ema import EMACalculator
    print("OK EMACalculator")
except Exception as e:
    print(f"FAIL EMACalculator: {e}")

# Optional imports
try:
    import loguru
    print("OK loguru (optional)")
except:
    print("- loguru not installed (optional)")

try:
    import rich
    print("OK rich (optional)")
except:
    print("- rich not installed (optional)")

print("\n" + "="*50)
print("Testing API connection...")

try:
    load_dotenv()
    client = CoinoneClient()
    ticker = client.get_ticker('usdt')
    if ticker and ticker.get('result') == 'success':
        price = ticker['data']['close_24h']
        print(f"OK API Connection OK - USDT/KRW: {price} KRW")
    else:
        print("FAIL API Connection Failed")
except Exception as e:
    print(f"FAIL API Error: {e}")

print("\nIf all core components show OK, you can run the bot!")
print("="*50)