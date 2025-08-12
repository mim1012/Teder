"""
수정된 API 테스트
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.coinone_client import CoinoneClient

print("=== Testing Fixed API ===\n")

try:
    client = CoinoneClient()
    
    # Get ticker
    print("1. Testing get_ticker()...")
    ticker = client.get_ticker('usdt')
    
    if ticker and 'data' in ticker:
        data = ticker['data']
        print(f"Current price: {data.get('close_24h', 'N/A')} KRW")
        print(f"24h volume: {data.get('volume_24h', 'N/A')} USDT")
        print(f"24h change: {data.get('change_rate_24h', 'N/A')}%")
    else:
        print("Failed to get ticker data")
        print(f"Response: {ticker}")
        
    # Get orderbook
    print("\n2. Testing get_orderbook()...")
    orderbook = client.get_orderbook('usdt')
    
    if orderbook and 'data' in orderbook:
        data = orderbook['data']
        asks = data.get('asks', [])
        bids = data.get('bids', [])
        
        if asks:
            print(f"Best ask: {asks[0]['price']} KRW")
        if bids:
            print(f"Best bid: {bids[0]['price']} KRW")
    else:
        print("Failed to get orderbook")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")