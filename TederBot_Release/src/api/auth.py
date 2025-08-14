"""
코인원 API 인증 시스템
HMAC-SHA512 서명 생성 및 인증 헤더 처리
"""
import hashlib
import hmac
import json
import time
import urllib.parse
from typing import Dict, Any, Optional

from config.settings import API_CONFIG
from .exceptions import AuthenticationError


class CoinoneAuth:
    """코인원 API 인증 클래스"""
    
    def __init__(self, access_token: Optional[str] = None, secret_key: Optional[str] = None):
        """
        인증 객체 초기화
        
        Args:
            access_token: 코인원 API 액세스 토큰
            secret_key: 코인원 API 시크릿 키
        """
        self.access_token = access_token or API_CONFIG.get('access_token')
        self.secret_key = secret_key or API_CONFIG.get('secret_key')
        
        # Public API만 사용하는 경우 인증 정보가 없어도 허용
        self.is_authenticated = bool(self.access_token and self.secret_key)
    
    def _generate_nonce(self) -> str:
        """밀리초 타임스탬프 nonce 생성"""
        return str(int(time.time() * 1000))
    
    def _create_payload(self, params: Dict[str, Any]) -> tuple:
        """
        요청 파라미터를 payload 문자열로 변환
        
        Args:
            params: API 요청 파라미터
            
        Returns:
            (payload_json, payload_encoded) 튜플
        """
        # nonce와 access_token 추가
        payload_params = {
            'access_token': self.access_token,
            'nonce': self._generate_nonce(),
            **params
        }
        
        # JSON 문자열로 변환
        payload_json = json.dumps(payload_params, separators=(',', ':'))
        
        # base64 인코딩
        import base64
        payload_encoded = base64.b64encode(payload_json.encode('utf-8')).decode('utf-8')
        
        return payload_json, payload_encoded
    
    def _generate_signature(self, payload_encoded: str) -> str:
        """
        HMAC-SHA512 서명 생성
        
        Args:
            payload_encoded: base64로 인코딩된 payload
            
        Returns:
            HMAC-SHA512 서명 (hex)
        """
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload_encoded.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return signature
    
    def get_headers(self, params: Dict[str, Any] = None) -> tuple:
        """
        Private API 요청용 인증 헤더 생성
        
        Args:
            params: API 요청 파라미터
            
        Returns:
            (headers, payload_data) 튜플
        """
        if params is None:
            params = {}
            
        payload_json, payload_encoded = self._create_payload(params)
        signature = self._generate_signature(payload_encoded)
        
        headers = {
            'Content-Type': 'application/json',
            'X-COINONE-PAYLOAD': payload_encoded,
            'X-COINONE-SIGNATURE': signature,
            'User-Agent': 'CoinoneAutoTrading/1.0'
        }
        
        # payload_json을 파싱하여 딕셔너리로 반환
        payload_data = json.loads(payload_json)
        
        return headers, payload_data
    
    def get_public_headers(self) -> Dict[str, str]:
        """
        Public API 요청용 기본 헤더 생성
        
        Returns:
            기본 헤더 딕셔너리
        """
        return {
            'Content-Type': 'application/json',
            'User-Agent': 'CoinoneAutoTrading/1.0'
        }
    
    def validate_credentials(self) -> bool:
        """
        API 인증 정보 유효성 검증
        
        Returns:
            인증 정보 유효성 여부
        """
        if not self.access_token or not self.secret_key:
            return False
            
        # 액세스 토큰 길이 검증 (일반적으로 32자)
        if len(self.access_token) < 20:
            return False
            
        # 시크릿 키 길이 검증 (일반적으로 64자 hex)
        if len(self.secret_key) < 40:
            return False
            
        return True