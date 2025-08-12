"""
오더북 테스트
"""

import os
import sys
import requests
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.coinone_client import CoinoneClient

print("=== Orderbook Test ===\n")

# Direct API call
print("1. Direct orderbook API call:")
url = "https://api.coinone.co.kr/public/v2/orderbook/KRW/USDT"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2))
else:
    print(f"Failed: {response.status_code}")

print("\n" + "="*50)

# Using client
print("\n2. Using CoinoneClient:")
try:
    client = CoinoneClient()
    orderbook = client.get_orderbook('usdt')
    print("Orderbook response:")
    print(json.dumps(orderbook, indent=2))
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")