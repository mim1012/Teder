"""
직접 API 호출 테스트
"""

import requests
import json

print("=== Direct Coinone API Test ===\n")

# 공개 API 엔드포인트들 테스트
endpoints = [
    # v2 API
    "https://api.coinone.co.kr/public/v2/ticker/KRW/USDT",
    "https://api.coinone.co.kr/public/v2/orderbook/KRW/USDT",
    "https://api.coinone.co.kr/public/v2/chart/KRW/USDT?interval=1h",
    
    # v1 API (legacy)
    "https://api.coinone.co.kr/ticker?currency=usdt",
    "https://api.coinone.co.kr/orderbook?currency=usdt",
    
    # 다른 형식들
    "https://api.coinone.co.kr/public/ticker/krw/usdt",
    "https://api.coinone.co.kr/ticker/usdt",
]

for url in endpoints:
    print(f"\nTesting: {url}")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and data['result'] == 'success':
                print("OK - Success")
                if 'errorCode' in data:
                    print(f"  Error Code: {data['errorCode']}")
                # 데이터 구조 확인
                if 'data' in data:
                    print(f"  Data keys: {list(data['data'].keys())[:5]}...")
                elif 'tickers' in data:
                    print(f"  Tickers: {len(data['tickers'])} items")
                elif 'last' in data:
                    print(f"  Last price: {data['last']}")
            else:
                print("FAIL - API returned error")
                print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"FAIL - HTTP Error: {response.text[:100]}...")
            
    except Exception as e:
        print(f"FAIL - Exception: {type(e).__name__}: {str(e)}")

print("\n=== Test Complete ===")