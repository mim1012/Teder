"""
USDT/KRW 현재 시세 확인 스크립트
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.coinone_client import CoinoneClient

def check_market():
    """시세 정보 확인"""
    try:
        client = CoinoneClient()
        
        # 현재가 조회
        ticker = client.get_ticker('usdt')
        if ticker:
            print('\nUSDT/KRW 현재 시세:')
            print('-' * 40)
            print(f'현재가: {float(ticker.get("last", 0)):,.0f}원')
            print(f'매수1호가: {float(ticker.get("ask", 0)):,.0f}원')
            print(f'매도1호가: {float(ticker.get("bid", 0)):,.0f}원')
            print(f'24시간 거래량: {float(ticker.get("volume", 0)):,.2f} USDT')
            
            # 변동률 계산
            last_price = float(ticker.get("last", 0))
            yesterday_last = float(ticker.get("yesterday_last", 0))
            if yesterday_last > 0:
                change_pct = ((last_price - yesterday_last) / yesterday_last) * 100
                print(f'24시간 변동률: {change_pct:+.2f}%')
        
        # 호가 조회
        orderbook = client.get_orderbook('usdt')
        if orderbook:
            print('\n호가 정보:')
            print('-' * 40)
            print('매도 호가 (상위 5개):')
            asks = orderbook.get('asks', [])
            for i, ask in enumerate(asks[:5]):
                print(f'  {float(ask["price"]):,.0f}원 - {float(ask["qty"]):.4f} USDT')
            
            print('\n매수 호가 (상위 5개):')
            bids = orderbook.get('bids', [])
            for i, bid in enumerate(bids[:5]):
                print(f'  {float(bid["price"]):,.0f}원 - {float(bid["qty"]):.4f} USDT')
        
    except Exception as e:
        print(f'오류 발생: {e}')
        print('\n시세 조회는 API 키 없이도 가능합니다.')
        print('네트워크 연결을 확인하세요.')

if __name__ == "__main__":
    check_market()