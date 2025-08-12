"""
최종 전체 확인 스크립트
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("COINONE USDT/KRW AUTO TRADING BOT - FINAL CHECK")
print("=" * 60)

# 1. 환경 설정 확인
print("\n1. ENVIRONMENT CHECK:")
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    access_token = os.getenv('COINONE_ACCESS_TOKEN')
    secret_key = os.getenv('COINONE_SECRET_KEY')
    dry_run = os.getenv('DRY_RUN', 'True')
    
    print(f"   .env file: {'OK' if os.path.exists('.env') else 'MISSING'}")
    print(f"   Access Token: {'OK' if access_token else 'MISSING'}")
    print(f"   Secret Key: {'OK' if secret_key else 'MISSING'}")
    print(f"   Trading Mode: {'DRY RUN' if dry_run.lower() == 'true' else 'LIVE'}")
    
except Exception as e:
    print(f"   ERROR: {e}")

# 2. API 연결 테스트
print("\n2. API CONNECTION TEST:")
try:
    from src.api.coinone_client import CoinoneClient
    
    client = CoinoneClient()
    
    # Public API 테스트
    ticker = client.get_ticker('usdt')
    if ticker and ticker.get('result') == 'success':
        price = ticker['data']['close_24h']
        print(f"   Public API (Ticker): OK - USDT/KRW = {price} KRW")
    else:
        print(f"   Public API (Ticker): FAILED")
    
    # Private API 테스트
    balance = client.get_balance()
    if balance and balance.get('result') == 'success':
        krw_balance = float(balance.get('krw', {}).get('avail', 0))
        usdt_balance = float(balance.get('usdt', {}).get('avail', 0))
        print(f"   Private API (Balance): OK")
        print(f"     KRW Available: {krw_balance:,.0f} KRW")
        print(f"     USDT Available: {usdt_balance:.4f} USDT")
    else:
        print(f"   Private API (Balance): FAILED - {balance}")
        
except Exception as e:
    print(f"   ERROR: {e}")

# 3. 기술적 지표 테스트
print("\n3. TECHNICAL INDICATORS TEST:")
try:
    from src.indicators.rsi import RSICalculator
    from src.indicators.ema import EMACalculator
    import pandas as pd
    import numpy as np
    
    # 샘플 데이터 생성
    sample_data = pd.DataFrame({
        'close': [1390, 1392, 1395, 1393, 1396, 1398, 1397, 1399, 1401, 1400] * 3
    })
    
    # RSI 계산
    rsi_calc = RSICalculator(period=14)
    rsi_values = rsi_calc.calculate_rsi(sample_data, 'close')
    print(f"   RSI Calculation: {'OK' if not pd.isna(rsi_values.iloc[-1]) else 'FAILED'}")
    
    # EMA 계산
    ema_calc = EMACalculator(period=20)
    ema_values = ema_calc.calculate_ema(sample_data, 'close')
    print(f"   EMA Calculation: {'OK' if not pd.isna(ema_values.iloc[-1]) else 'FAILED'}")
    
except Exception as e:
    print(f"   ERROR: {e}")

# 4. 백테스트 엔진 테스트
print("\n4. BACKTEST ENGINE TEST:")
try:
    from backtest.backtest_engine import BacktestConfig, BacktestEngine
    from backtest.data_loader import SampleDataGenerator
    
    # 샘플 데이터 생성
    sample_df = SampleDataGenerator.generate_realistic_data(hours=50)
    
    # 백테스트 설정
    config = BacktestConfig(
        initial_balance=100000,
        limit_order_fee=0.0000,
        market_order_fee=0.0002
    )
    
    # 백테스트 실행
    engine = BacktestEngine(config)
    result = engine.run_backtest(sample_df)
    
    print(f"   Backtest Engine: OK")
    print(f"     Trades Executed: {len(result['trades'])}")
    print(f"     Final Balance: {result['final_balance']:,.0f} KRW")
    
except Exception as e:
    print(f"   ERROR: {e}")

# 5. 메인 트레이딩 봇 테스트
print("\n5. MAIN TRADING BOT TEST:")
try:
    from main import USDTKRWTradingBot
    
    # 모의거래 모드로 봇 초기화
    bot = USDTKRWTradingBot(dry_run=True)
    
    print(f"   Bot Initialization: OK")
    print(f"   Trading Mode: {'DRY RUN' if bot.dry_run else 'LIVE'}")
    print(f"   API Client: {'OK' if bot.client else 'FAILED'}")
    print(f"   Strategy Config: {'OK' if bot.config else 'FAILED'}")
    
except Exception as e:
    print(f"   ERROR: {e}")

# 6. 배치 파일 확인
print("\n6. BATCH FILES CHECK:")
batch_files = [
    'run_test.bat',
    'run_live.bat', 
    'check_balance_simple.bat',
    'check_market_simple.bat'
]

for batch_file in batch_files:
    exists = os.path.exists(batch_file)
    print(f"   {batch_file}: {'OK' if exists else 'MISSING'}")

# 7. 필수 파일 확인
print("\n7. REQUIRED FILES CHECK:")
required_files = [
    '.env',
    'main.py',
    'requirements.txt',
    'src/api/coinone_client.py',
    'src/indicators/rsi.py',
    'src/indicators/ema.py',
    'backtest/backtest_engine.py'
]

for req_file in required_files:
    exists = os.path.exists(req_file)
    print(f"   {req_file}: {'OK' if exists else 'MISSING'}")

# 8. 최종 상태 요약
print("\n" + "=" * 60)
print("FINAL STATUS SUMMARY:")
print("=" * 60)

# API 키 확인
if access_token and secret_key:
    print("✓ API Keys: CONFIGURED")
else:
    print("✗ API Keys: MISSING")

# API 연결 확인
try:
    client = CoinoneClient()
    balance = client.get_balance()
    if balance and balance.get('result') == 'success':
        krw_bal = float(balance.get('krw', {}).get('avail', 0))
        print("✓ API Connection: WORKING")
        if krw_bal > 0:
            print("✓ Account Funding: AVAILABLE")
        else:
            print("⚠ Account Funding: EMPTY (Need to deposit KRW)")
    else:
        print("✗ API Connection: FAILED")
except:
    print("✗ API Connection: ERROR")

print("\nREADY FOR TRADING:")
print("- For paper trading: run_test.bat")
print("- For live trading: run_live.bat (after funding)")
print("- For balance check: check_balance_simple.bat")
print("- For market check: check_market_simple.bat")

print("\n" + "=" * 60)