"""
Test candle data API
"""

import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from src.api.coinone_client import CoinoneClient

# Load environment variables
load_dotenv()

def test_candles():
    """Test candle data retrieval"""
    client = CoinoneClient()
    
    print("Testing candle data API...")
    print("="*60)
    
    # Test ticker first
    print("\n1. Testing ticker API...")
    ticker = client.get_ticker('usdt')
    if ticker:
        print(f"Ticker result: {ticker.get('result')}")
        if ticker.get('result') == 'success':
            print(f"Current price: {ticker.get('data', {}).get('close_24h')} KRW")
    
    # Test candles
    print("\n2. Testing candles API...")
    candles = client.get_candles('usdt', interval='1h', limit=5)
    
    if candles:
        print(f"Candles result: {candles.get('result')}")
        print(f"Response keys: {list(candles.keys())}")
        
        # Print full response structure for debugging
        print("\nFull response structure (first 500 chars):")
        response_str = json.dumps(candles, indent=2)
        print(response_str[:500])
        
        # Try to extract data
        if candles.get('result') == 'success':
            # Check different possible data structures
            if 'data' in candles:
                print(f"\nData keys: {list(candles['data'].keys())}")
                if 'chart' in candles['data']:
                    chart_data = candles['data']['chart']
                    print(f"Chart data length: {len(chart_data)}")
                    if chart_data:
                        print(f"First candle: {chart_data[0]}")
                elif isinstance(candles['data'], list):
                    print(f"Data is a list with {len(candles['data'])} items")
                    if candles['data']:
                        print(f"First item: {candles['data'][0]}")
            elif 'chart' in candles:
                print(f"Chart data found at root level")
                chart_data = candles['chart']
                print(f"Chart data length: {len(chart_data)}")
                if chart_data:
                    print(f"First candle: {chart_data[0]}")
    else:
        print("No response from candles API")

if __name__ == "__main__":
    test_candles()