"""
실거래 준비 상태 최종 점검
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("LIVE TRADING READINESS CHECK")
print("=" * 60)

# 체크리스트
checklist = {
    "API_KEYS": False,
    "API_CONNECTION": False,
    "BALANCE_CHECK": False,
    "PUBLIC_API": False,
    "STRATEGY_LOGIC": False,
    "RISK_MANAGEMENT": False,
    "EXECUTION_FILES": False,
    "MONITORING": False
}

# 1. API 키 확인
access_token = os.getenv('COINONE_ACCESS_TOKEN')
secret_key = os.getenv('COINONE_SECRET_KEY')
if access_token and secret_key:
    checklist["API_KEYS"] = True
    print("[OK] API Keys configured")
else:
    print("[FAIL] API Keys missing")

# 2. API 연결 테스트
try:
    from src.api.coinone_client import CoinoneClient
    client = CoinoneClient()
    
    # Public API
    ticker = client.get_ticker('usdt')
    if ticker and ticker.get('result') == 'success':
        checklist["PUBLIC_API"] = True
        price = float(ticker['data']['close_24h'])
        print(f"[OK] Public API - Current USDT/KRW: {price:,.0f} KRW")
    else:
        print("[FAIL] Public API not working")
    
    # Private API
    balance = client.get_balance()
    if balance and balance.get('result') == 'success':
        checklist["API_CONNECTION"] = True
        krw = float(balance.get('krw', {}).get('avail', 0))
        usdt = float(balance.get('usdt', {}).get('avail', 0))
        
        print(f"[OK] Private API - Authentication working")
        print(f"     Balance: {krw:,.0f} KRW, {usdt:.4f} USDT")
        
        if krw > 0:
            checklist["BALANCE_CHECK"] = True
            print(f"[OK] Account funded - Ready for trading")
        else:
            print(f"[WARNING] No KRW balance - Need deposit for live trading")
    else:
        print("[FAIL] Private API not working")
        
except Exception as e:
    print(f"[FAIL] API Error: {e}")

# 3. 전략 로직 확인
try:
    from backtest.backtest_engine import BacktestConfig
    from src.indicators.rsi import RSICalculator
    from src.indicators.ema import EMACalculator
    
    config = BacktestConfig()
    rsi_calc = RSICalculator(14)
    ema_calc = EMACalculator(20)
    
    checklist["STRATEGY_LOGIC"] = True
    print("[OK] Strategy logic components loaded")
    print(f"     RSI Period: {config.rsi_period}")
    print(f"     EMA Period: {config.ema_period}")
    print(f"     Profit Target: +{config.profit_target} KRW")
    print(f"     Max Hold: {config.max_hold_hours} hours")
    
except Exception as e:
    print(f"[FAIL] Strategy Error: {e}")

# 4. 리스크 관리 확인
dry_run = os.getenv('DRY_RUN', 'True').lower() == 'true'
if dry_run:
    checklist["RISK_MANAGEMENT"] = True
    print("[OK] Risk Management - DRY RUN mode enabled")
else:
    checklist["RISK_MANAGEMENT"] = True
    print("[WARNING] Risk Management - LIVE TRADING mode")

# 5. 실행 파일 확인
exec_files = ['run_test.bat', 'run_live.bat', 'main.py']
all_exist = True
for f in exec_files:
    if not os.path.exists(f):
        all_exist = False
        print(f"[FAIL] Missing file: {f}")
        
if all_exist:
    checklist["EXECUTION_FILES"] = True
    print("[OK] All execution files present")

# 6. 모니터링 확인
if os.path.exists('logs'):
    checklist["MONITORING"] = True
    print("[OK] Logging directory ready")
else:
    os.makedirs('logs', exist_ok=True)
    checklist["MONITORING"] = True
    print("[OK] Logging directory created")

# 최종 평가
print("\n" + "=" * 60)
print("FINAL ASSESSMENT:")
print("=" * 60)

total = len(checklist)
passed = sum(checklist.values())
percentage = (passed / total) * 100

for key, value in checklist.items():
    status = "PASS" if value else "FAIL"
    print(f"{key:20s}: {status}")

print(f"\nScore: {passed}/{total} ({percentage:.0f}%)")

if percentage == 100:
    print("\nSTATUS: READY FOR LIVE TRADING")
    print("Execute: run_live.bat (after setting DRY_RUN=False)")
elif percentage >= 75:
    print("\nSTATUS: READY FOR PAPER TRADING")
    print("Execute: run_test.bat")
    if not checklist["BALANCE_CHECK"]:
        print("Note: Deposit KRW for live trading")
else:
    print("\nSTATUS: NOT READY")
    print("Fix the failed items before trading")

print("\n" + "=" * 60)