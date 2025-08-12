"""
코인원 API v2 클라이언트
Public API와 Private API 모두 지원
"""
import time
import logging
from typing import Dict, Any, Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import API_CONFIG, TRADING_CONFIG
from config.constants import API_ENDPOINTS, OrderType, OrderSide
from .auth import CoinoneAuth
from .exceptions import (
    CoinoneAPIError, NetworkError, RateLimitError,
    get_exception_from_code, ServerError
)


class CoinoneClient:
    """코인원 API v2 클라이언트"""
    
    def __init__(self, access_token: Optional[str] = None, secret_key: Optional[str] = None):
        """
        클라이언트 초기화
        
        Args:
            access_token: API 액세스 토큰
            secret_key: API 시크릿 키
        """
        self.base_url = API_CONFIG['base_url']
        self.timeout = API_CONFIG['timeout']
        self.max_retries = API_CONFIG['max_retries']
        self.retry_delay = API_CONFIG['retry_delay']
        
        # 인증 객체 초기화
        self.auth = CoinoneAuth(access_token, secret_key)
        
        # 세션 설정
        self.session = requests.Session()
        self._setup_session()
        
        # 로깅 설정
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting 설정
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms
    
    def _setup_session(self):
        """HTTP 세션 설정 (재시도 로직 포함)"""
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _rate_limit_check(self):
        """Rate limiting 체크"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        is_private: bool = False
    ) -> Dict[str, Any]:
        """
        API 요청 수행
        
        Args:
            method: HTTP 메소드
            endpoint: API 엔드포인트
            params: 요청 파라미터
            is_private: Private API 여부
            
        Returns:
            API 응답 데이터
        """
        # Rate limiting 체크
        self._rate_limit_check()
        
        url = f"{self.base_url}{endpoint}"
        
        # 헤더 설정
        if is_private:
            if not self.auth.is_authenticated:
                raise CoinoneAPIError("Private API 호출을 위해서는 API 키가 필요합니다.")
            headers, json_data = self.auth.get_headers(params or {})
        else:
            headers = self.auth.get_public_headers()
            json_data = params if method == 'POST' else None
        
        try:
            if method == 'GET':
                response = self.session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=self.timeout
                )
            else:
                response = self.session.post(
                    url, 
                    json=json_data, 
                    headers=headers, 
                    timeout=self.timeout
                )
            
            # 응답 상태 코드 확인
            if response.status_code == 429:
                raise RateLimitError("API 호출 한도를 초과했습니다.")
            
            response.raise_for_status()
            
            # JSON 응답 파싱
            data = response.json()
            
            # API 에러 코드 확인
            if 'errorCode' in data:
                error_code = str(data['errorCode'])
                if error_code != '0':
                    message = data.get('errorMsg', '알 수 없는 오류')
                    raise get_exception_from_code(int(error_code), message)
            
            return data
            
        except requests.exceptions.Timeout:
            raise NetworkError("요청 시간이 초과되었습니다.")
        except requests.exceptions.ConnectionError:
            raise NetworkError("네트워크 연결 오류가 발생했습니다.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                raise ServerError(f"서버 오류: {e.response.status_code}")
            else:
                raise CoinoneAPIError(f"HTTP 오류: {e.response.status_code}")
        except Exception as e:
            if isinstance(e, CoinoneAPIError):
                raise
            else:
                raise CoinoneAPIError(f"예상치 못한 오류: {str(e)}")
    
    # =================
    # Public API Methods
    # =================
    
    def get_ticker(self, currency: str = None) -> Dict[str, Any]:
        """
        현재가 정보 조회
        
        Args:
            currency: 통화 코드 (기본값: USDT)
            
        Returns:
            현재가 정보
        """
        currency = (currency or TRADING_CONFIG['symbol']).upper()
        endpoint = API_ENDPOINTS['ticker'].format(currency=currency)
        return self._make_request('GET', endpoint)
    
    def get_orderbook(self, currency: str = None) -> Dict[str, Any]:
        """
        호가 정보 조회
        
        Args:
            currency: 통화 코드 (기본값: USDT)
            
        Returns:
            호가 정보
        """
        currency = currency or TRADING_CONFIG['symbol']
        endpoint = API_ENDPOINTS['orderbook'].format(currency=currency)
        return self._make_request('GET', endpoint)
    
    def get_trades(self, currency: str = None, period: str = 'hour') -> Dict[str, Any]:
        """
        체결 내역 조회
        
        Args:
            currency: 통화 코드 (기본값: USDT)
            period: 조회 기간
            
        Returns:
            체결 내역
        """
        currency = currency or TRADING_CONFIG['symbol']
        endpoint = API_ENDPOINTS['trades'].format(currency=currency)
        params = {'period': period}
        return self._make_request('GET', endpoint, params)
    
    def get_candles(
        self, 
        currency: str = None, 
        interval: str = '1h',
        limit: int = 200
    ) -> Dict[str, Any]:
        """
        차트 데이터 조회 (캔들스틱)
        
        Args:
            currency: 통화 코드 (기본값: USDT)
            interval: 차트 간격 (1h, 1d 등)
            limit: 조회할 캔들 개수 (기본값: 200, 최대 500)
            
        Returns:
            차트 데이터
        """
        currency = (currency or TRADING_CONFIG['symbol']).upper()
        endpoint = API_ENDPOINTS['candles'].format(currency=currency)
        params = {
            'interval': interval,
            'size': min(limit, 500)  # API 최대 제한, 파라미터명 'size' 사용
        }
        return self._make_request('GET', endpoint, params)
    
    # ==================
    # Private API Methods
    # ==================
    
    def get_balance(self) -> Dict[str, Any]:
        """
        잔고 조회
        
        Returns:
            잔고 정보
        """
        endpoint = API_ENDPOINTS['balance']
        return self._make_request('POST', endpoint, is_private=True)
    
    def place_limit_order(
        self,
        side: OrderSide,
        currency: str,
        price: float,
        qty: float
    ) -> Dict[str, Any]:
        """
        지정가 주문
        
        Args:
            side: 주문 방향 (buy/sell)
            currency: 통화 코드
            price: 주문 가격
            qty: 주문 수량
            
        Returns:
            주문 결과
        """
        params = {
            'price': str(price),
            'qty': str(qty),
            'currency': currency,
            'is_ask': 1 if side == OrderSide.SELL else 0
        }
        
        endpoint = API_ENDPOINTS['order']
        return self._make_request('POST', endpoint, params, is_private=True)
    
    def place_market_order(
        self,
        side: OrderSide,
        currency: str,
        qty: float = None,
        fiat_qty: float = None
    ) -> Dict[str, Any]:
        """
        시장가 주문
        
        Args:
            side: 주문 방향 (buy/sell)
            currency: 통화 코드
            qty: 주문 수량 (코인 수량)
            fiat_qty: 주문 금액 (원화 금액, 매수시만)
            
        Returns:
            주문 결과
        """
        params = {
            'currency': currency,
            'is_ask': 1 if side == OrderSide.SELL else 0
        }
        
        if side == OrderSide.BUY and fiat_qty:
            params['fiat_qty'] = str(fiat_qty)
        elif qty:
            params['qty'] = str(qty)
        else:
            raise ValueError("qty 또는 fiat_qty 중 하나는 필수입니다.")
        
        endpoint = API_ENDPOINTS['market_order']
        return self._make_request('POST', endpoint, params, is_private=True)
    
    def cancel_order(self, order_id: str, currency: str) -> Dict[str, Any]:
        """
        주문 취소
        
        Args:
            order_id: 주문 ID
            currency: 통화 코드
            
        Returns:
            취소 결과
        """
        params = {
            'order_id': order_id,
            'currency': currency
        }
        
        endpoint = API_ENDPOINTS['cancel']
        return self._make_request('POST', endpoint, params, is_private=True)
    
    def get_order_info(self, order_id: str, currency: str) -> Dict[str, Any]:
        """
        주문 정보 조회
        
        Args:
            order_id: 주문 ID
            currency: 통화 코드
            
        Returns:
            주문 정보
        """
        params = {
            'order_id': order_id,
            'currency': currency
        }
        
        endpoint = API_ENDPOINTS['order_info']
        return self._make_request('POST', endpoint, params, is_private=True)
    
    def get_orders(
        self, 
        currency: str = None,
        status: str = 'open'
    ) -> Dict[str, Any]:
        """
        주문 목록 조회
        
        Args:
            currency: 통화 코드
            status: 주문 상태 (open, filled, cancelled)
            
        Returns:
            주문 목록
        """
        params = {}
        if currency:
            params['currency'] = currency
        if status:
            params['status'] = status
        
        endpoint = API_ENDPOINTS['orders']
        return self._make_request('POST', endpoint, params, is_private=True)
    
    def get_trades_history(
        self,
        currency: str = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        거래 내역 조회
        
        Args:
            currency: 통화 코드
            limit: 조회할 거래 개수
            
        Returns:
            거래 내역
        """
        params = {'limit': limit}
        if currency:
            params['currency'] = currency
        
        endpoint = API_ENDPOINTS['trades_history']
        return self._make_request('POST', endpoint, params, is_private=True)
    
    # ===============
    # Utility Methods
    # ===============
    
    def get_best_bid_ask(self, currency: str = None) -> tuple:
        """
        최우선 매수/매도 호가 조회
        
        Args:
            currency: 통화 코드
            
        Returns:
            (최우선 매수가, 최우선 매도가)
        """
        orderbook = self.get_orderbook(currency)
        
        bid_price = float(orderbook['bid'][0]['price']) if orderbook['bid'] else 0
        ask_price = float(orderbook['ask'][0]['price']) if orderbook['ask'] else 0
        
        return bid_price, ask_price
    
    def get_account_balance(self, currency: str = 'KRW') -> float:
        """
        특정 통화의 잔고 조회
        
        Args:
            currency: 통화 코드
            
        Returns:
            해당 통화 잔고
        """
        balance_data = self.get_balance()
        
        if currency in balance_data:
            return float(balance_data[currency]['avail'])
        return 0.0
    
    def is_order_filled(self, order_id: str, currency: str) -> bool:
        """
        주문 체결 여부 확인
        
        Args:
            order_id: 주문 ID
            currency: 통화 코드
            
        Returns:
            체결 여부
        """
        try:
            order_info = self.get_order_info(order_id, currency)
            return order_info.get('status') == 'filled'
        except Exception:
            return False
    
    def wait_for_order_fill(
        self, 
        order_id: str, 
        currency: str, 
        timeout: int = 600,
        check_interval: int = 5
    ) -> bool:
        """
        주문 체결 대기
        
        Args:
            order_id: 주문 ID
            currency: 통화 코드
            timeout: 최대 대기 시간 (초)
            check_interval: 확인 간격 (초)
            
        Returns:
            체결 완료 여부
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_order_filled(order_id, currency):
                return True
            time.sleep(check_interval)
        
        return False