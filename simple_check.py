"""
간단한 최종 확인
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("COINONE AUTO TRADING BOT - SIMPLE CHECK")
print("=" * 50)

# 1. 환경 설정
from dotenv import load_dotenv
load_dotenv()

access_token = os.getenv('COINONE_ACCESS_TOKEN')
secret_key = os.getenv('COINONE_SECRET_KEY')

print(f"1. Environment:")
print(f"   API Keys: {'OK' if access_token and secret_key else 'MISSING'}")

# 2. API 테스트
try:
    from src.api.coinone_client import CoinoneClient
    
    client = CoinoneClient()
    
    # 시세 확인
    ticker = client.get_ticker('usdt')
    ticker_ok = ticker and ticker.get('result') == 'success'
    
    # 잔고 확인
    balance = client.get_balance()
    balance_ok = balance and balance.get('result') == 'success'
    
    print(f"2. API Connection:")
    print(f"   Public API: {'OK' if ticker_ok else 'FAILED'}")
    print(f"   Private API: {'OK' if balance_ok else 'FAILED'}")
    
    if ticker_ok:
        price = ticker['data']['close_24h']
        print(f"   Current USDT/KRW: {price} KRW")
    
    if balance_ok:
        krw = float(balance.get('krw', {}).get('avail', 0))
        usdt = float(balance.get('usdt', {}).get('avail', 0))
        print(f"   Account: {krw:,.0f} KRW, {usdt:.4f} USDT")

except Exception as e:
    print(f"2. API Connection: ERROR - {e}")

# 3. 기술적 지표
try:
    from src.indicators.rsi import RSICalculator
    from src.indicators.ema import EMACalculator
    import pandas as pd
    
    # 샘플 데이터로 테스트
    data = pd.DataFrame({'close': [1390, 1395, 1400, 1398, 1402] * 6})
    
    rsi_calc = RSICalculator(14)
    ema_calc = EMACalculator(20)
    
    rsi = rsi_calc.calculate_rsi(data, 'close')
    ema = ema_calc.calculate_ema(data, 'close')
    
    print(f"3. Technical Indicators:")
    print(f"   RSI: {'OK' if not pd.isna(rsi.iloc[-1]) else 'FAILED'}")
    print(f"   EMA: {'OK' if not pd.isna(ema.iloc[-1]) else 'FAILED'}")

except Exception as e:
    print(f"3. Technical Indicators: ERROR - {e}")

# 4. 백테스트
try:
    from backtest.backtest_engine import BacktestConfig
    
    config = BacktestConfig()
    print(f"4. Backtest Engine:")
    print(f"   Config: OK")
    print(f"   Initial Balance: {config.initial_balance:,.0f} KRW")
    print(f"   Profit Target: +{config.profit_target} KRW")

except Exception as e:
    print(f"4. Backtest Engine: ERROR - {e}")

# 5. 배치 파일들
batch_files = ['run_test.bat', 'run_live.bat', 'check_balance_simple.bat', 'check_market_simple.bat']
print(f"5. Batch Files:")
for bf in batch_files:
    print(f"   {bf}: {'OK' if os.path.exists(bf) else 'MISSING'}")

print("\n" + "=" * 50)
print("SUMMARY:")

if access_token and secret_key:
    print("SUCCESS: API Keys configured")
else:
    print("FAIL: API Keys missing")

try:
    client = CoinoneClient()
    balance = client.get_balance()
    if balance and balance.get('result') == 'success':
        krw_balance = float(balance.get('krw', {}).get('avail', 0))
        print("SUCCESS: API connection working")
        
        if krw_balance > 0:
            print("SUCCESS: Account funded, ready for live trading")
        else:
            print("WARNING: Account empty, need to deposit KRW for live trading")
            print("INFO: Paper trading available with run_test.bat")
    else:
        print("FAIL: API connection failed")
except:
    print("FAIL: API connection error")

print("\nNext Steps:")
print("- Test paper trading: run_test.bat")
print("- Check balance: check_balance_simple.bat") 
print("- Check market: check_market_simple.bat")
print("- Live trading (after deposit): run_live.bat")

print("=" * 50)