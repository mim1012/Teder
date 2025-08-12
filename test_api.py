"""
API 연결 테스트 스크립트
"""

import os
import sys
import requests
import json

print("=== Coinone API Test ===\n")

# 1. 공개 API 테스트 (인증 불필요)
print("1. Testing Public API (no auth required)...")
try:
    # 티커 정보 조회
    url = "https://api.coinone.co.kr/public/v2/ticker/KRW/USDT"
    response = requests.get(url)
    print(f"URL: {url}")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Response:", json.dumps(data, indent=2))
        
        if 'tickers' in data and data['tickers']:
            ticker = data['tickers'][0]
            print(f"\nUSDT/KRW 현재가: {ticker.get('last', 'N/A')}원")
    else:
        print(f"Error Response: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50 + "\n")

# 2. 환경 변수 확인
print("2. Checking environment variables...")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    access_token = os.getenv('COINONE_ACCESS_TOKEN')
    secret_key = os.getenv('COINONE_SECRET_KEY')
    
    print(f"ACCESS_TOKEN exists: {'Yes' if access_token else 'No'}")
    print(f"SECRET_KEY exists: {'Yes' if secret_key else 'No'}")
    
    if access_token:
        print(f"ACCESS_TOKEN length: {len(access_token)}")
        print(f"ACCESS_TOKEN format: {access_token[:8]}...{access_token[-4:]}")
    
    if secret_key:
        print(f"SECRET_KEY length: {len(secret_key)}")
        print(f"SECRET_KEY first chars: {secret_key[:4]}...")
        
except Exception as e:
    print(f"Error loading .env: {e}")

print("\n" + "="*50 + "\n")

# 3. 코인원 API 클라이언트 테스트
print("3. Testing Coinone API Client...")
try:
    from src.api.coinone_client import CoinoneClient
    
    client = CoinoneClient()
    print("CoinoneClient initialized successfully")
    
    # 공개 API 테스트
    print("\nTesting get_ticker()...")
    ticker = client.get_ticker('usdt')
    if ticker:
        print(f"Ticker data received: {ticker.get('last', 'N/A')}")
    else:
        print("No ticker data received")
    
    # 인증 필요 API 테스트 (잔고 조회)
    if access_token and secret_key:
        print("\nTesting get_balance()...")
        try:
            balance = client.get_balance()
            if balance:
                print("Balance data received")
                for currency in ['krw', 'usdt']:
                    if currency in balance:
                        print(f"  {currency.upper()}: {balance[currency].get('available', 0)}")
            else:
                print("No balance data received")
        except Exception as e:
            print(f"Balance API error: {e}")
    else:
        print("\nSkipping balance test (API keys not found)")
        
except Exception as e:
    print(f"Error with CoinoneClient: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")