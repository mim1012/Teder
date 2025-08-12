"""
디버깅용 API 테스트
"""

import os
import sys
import requests
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.constants import API_ENDPOINTS

print("=== Debug API Test ===\n")

# 1. Direct URL test
base_url = "https://api.coinone.co.kr"
ticker_endpoint = API_ENDPOINTS['ticker'].format(currency='USDT')
full_url = base_url + ticker_endpoint

print(f"Full URL: {full_url}")

try:
    response = requests.get(full_url, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Check for errors
        if 'errorCode' in data:
            print(f"\nError Code: {data['errorCode']}")
            if data['errorCode'] != 0:
                print(f"Error Message: {data.get('errorMsg', 'No message')}")
        
    else:
        print("Raw response:")
        print(response.text)
        
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")

print("\n" + "="*50)

# 2. Test all public endpoints
print("\n2. Testing all public endpoints:")

currencies = ['USDT', 'BTC', 'ETH']
for curr in currencies:
    print(f"\nTesting currency: {curr}")
    
    for endpoint_name, endpoint_template in API_ENDPOINTS.items():
        if endpoint_name in ['ticker', 'orderbook', 'trades', 'candles']:
            endpoint = endpoint_template.format(currency=curr)
            url = base_url + endpoint
            
            try:
                response = requests.get(url, timeout=10)
                status = "OK" if response.status_code == 200 else f"FAIL ({response.status_code})"
                print(f"  {endpoint_name}: {status}")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'errorCode' in data and data['errorCode'] != 0:
                        print(f"    API Error: {data.get('errorMsg', 'Unknown')}")
                        
            except Exception as e:
                print(f"  {endpoint_name}: ERROR - {type(e).__name__}")

print("\n=== Debug Complete ===")