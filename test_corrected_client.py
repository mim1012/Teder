"""
수정된 클라이언트 테스트
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.coinone_client import CoinoneClient

print("=== Corrected Client Test ===\n")

try:
    client = CoinoneClient()
    
    print("1. Testing get_balance()...")
    balance = client.get_balance()
    
    if balance and balance.get('result') == 'success':
        print("SUCCESS! Balance retrieved:")
        
        # KRW 잔고
        krw = balance.get('krw', {})
        krw_avail = float(krw.get('avail', 0))
        krw_balance = float(krw.get('balance', 0))
        
        print(f"KRW (Korean Won):")
        print(f"  Available: {krw_avail:,.0f} KRW")
        print(f"  Total: {krw_balance:,.0f} KRW")
        
        # USDT 잔고
        usdt = balance.get('usdt', {})
        usdt_avail = float(usdt.get('avail', 0))
        usdt_balance = float(usdt.get('balance', 0))
        
        print(f"\nUSDT (Tether):")
        print(f"  Available: {usdt_avail:.4f} USDT")
        print(f"  Total: {usdt_balance:.4f} USDT")
        
        # 기타 코인 중 잔고가 있는 것만 표시
        print(f"\nOther cryptocurrencies with non-zero balance:")
        other_balances = []
        for currency, info in balance.items():
            if currency not in ['result', 'errorCode', 'normalWallets', 'krw', 'usdt']:
                if isinstance(info, dict):
                    avail = float(info.get('avail', 0))
                    total = float(info.get('balance', 0))
                    if avail > 0 or total > 0:
                        other_balances.append((currency.upper(), avail, total))
        
        if other_balances:
            for currency, avail, total in other_balances:
                print(f"  {currency}: {avail:.4f} (available), {total:.4f} (total)")
        else:
            print("  None")
            
        print(f"\nAPI Authentication Working!")
        
    else:
        print("Failed to get balance")
        print(f"Response: {balance}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")