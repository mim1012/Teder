@echo off
echo ========================================
echo USDT/KRW 현재 시세 확인
echo ========================================
echo.

REM Python 경로 확인
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python이 설치되어 있지 않습니다.
    pause
    exit /b 1
)

REM 가상환경 활성화
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo 가상환경이 없습니다. run_test.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

REM 시세 확인 스크립트 실행
python -c "
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath('.')))
from src.api.coinone_client import CoinoneClient

try:
    client = CoinoneClient()
    
    # 현재가 조회
    ticker = client.get_ticker('usdt')
    if ticker:
        print('\nUSDT/KRW 현재 시세:')
        print('-' * 40)
        print(f'현재가: {float(ticker.get(\"last\", 0)):,.0f}원')
        print(f'매수1호가: {float(ticker.get(\"ask\", 0)):,.0f}원')
        print(f'매도1호가: {float(ticker.get(\"bid\", 0)):,.0f}원')
        print(f'24시간 거래량: {float(ticker.get(\"volume\", 0)):,.2f} USDT')
        print(f'24시간 변동률: {float(ticker.get(\"yesterday_last\", 0)):+.2f}%')
    
    # 호가 조회
    orderbook = client.get_orderbook('usdt')
    if orderbook:
        print('\n호가 정보:')
        print('-' * 40)
        print('매도 호가 (상위 5개):')
        for i, ask in enumerate(orderbook.get('asks', [])[:5]):
            print(f'  {float(ask[\"price\"]):,.0f}원 - {float(ask[\"qty\"]):.4f} USDT')
        
        print('\n매수 호가 (상위 5개):')
        for i, bid in enumerate(orderbook.get('bids', [])[:5]):
            print(f'  {float(bid[\"price\"]):,.0f}원 - {float(bid[\"qty\"]):.4f} USDT')
    
except Exception as e:
    print(f'오류 발생: {e}')
"

echo.
pause