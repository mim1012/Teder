"""
코인원 계좌 잔고 확인 스크립트
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.api.coinone_client import CoinoneClient

def check_balance():
    """계좌 잔고 확인"""
    try:
        client = CoinoneClient()
        balance = client.get_balance()
        
        print('\n계좌 잔고:')
        print('-' * 40)
        
        if balance:
            for currency, info in balance.items():
                if currency in ['krw', 'usdt']:
                    available = float(info.get('available', 0))
                    locked = float(info.get('locked', 0))
                    total = available + locked
                    
                    if currency == 'krw':
                        print(f'KRW (원화):')
                        print(f'  사용가능: {available:,.0f}원')
                        print(f'  거래중: {locked:,.0f}원')
                        print(f'  총액: {total:,.0f}원')
                    else:
                        print(f'USDT (테더):')
                        print(f'  사용가능: {available:.4f}개')
                        print(f'  거래중: {locked:.4f}개')
                        print(f'  총액: {total:.4f}개')
                    print()
        else:
            print('잔고 조회 실패')
            print('API 키를 확인하세요.')
            
    except Exception as e:
        print(f'오류 발생: {e}')
        print('API 키가 올바르게 설정되었는지 확인하세요.')
        print('\n.env 파일 확인사항:')
        print('1. COINONE_ACCESS_TOKEN=your_access_token')
        print('2. COINONE_SECRET_KEY=your_secret_key')

if __name__ == "__main__":
    check_balance()