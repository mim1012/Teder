"""
코인원 API 인증 방식 테스트
"""

import os
import sys
import requests
import json
import hmac
import hashlib
import time
import base64
from urllib.parse import urlencode

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("=== Auth Methods Test ===\n")

access_token = os.getenv('COINONE_ACCESS_TOKEN')
secret_key = os.getenv('COINONE_SECRET_KEY')

# Different endpoints to test
endpoints = [
    {
        'name': 'v2.1/account/balance',
        'url': 'https://api.coinone.co.kr/v2.1/account/balance',
        'method': 'POST'
    },
    {
        'name': 'v2/account/balance',
        'url': 'https://api.coinone.co.kr/v2/account/balance',
        'method': 'POST'
    },
    {
        'name': 'account/balance', 
        'url': 'https://api.coinone.co.kr/account/balance',
        'method': 'POST'
    }
]

def test_auth_method(endpoint, payload_format, signature_method):
    """다양한 인증 방식 테스트"""
    
    url = endpoint['url']
    nonce = str(int(time.time() * 1000))
    
    payload = {
        'access_token': access_token,
        'nonce': nonce
    }
    
    try:
        # 페이로드 형식 결정
        if payload_format == 'json':
            payload_str = json.dumps(payload, separators=(',', ':'))
            content_type = 'application/json'
            request_data = payload
        elif payload_format == 'urlencoded':
            payload_str = urlencode(payload)
            content_type = 'application/x-www-form-urlencoded'
            request_data = payload
        else:
            return f"Unknown payload format: {payload_format}"
        
        # 서명 생성
        if signature_method == 'raw_secret':
            signature = hmac.new(
                secret_key.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
        elif signature_method == 'base64_secret':
            decoded_secret = base64.b64decode(secret_key + '==')  # padding 추가
            signature = hmac.new(
                decoded_secret,
                payload_str.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
        else:
            return f"Unknown signature method: {signature_method}"
        
        # 요청 헤더
        headers = {
            'Content-Type': content_type,
            'X-COINONE-SIGNATURE': signature,
            'X-COINONE-PAYLOAD': base64.b64encode(payload_str.encode('utf-8')).decode('utf-8')
        }
        
        # API 호출
        if endpoint['method'] == 'POST':
            if payload_format == 'json':
                response = requests.post(url, json=request_data, headers=headers, timeout=10)
            else:
                response = requests.post(url, data=request_data, headers=headers, timeout=10)
        
        result = {
            'status_code': response.status_code,
            'response': response.json() if response.status_code == 200 else response.text[:200]
        }
        
        return result
        
    except Exception as e:
        return f"Exception: {str(e)}"

# 테스트 실행
test_cases = [
    ('json', 'raw_secret'),
    ('json', 'base64_secret'),
    ('urlencoded', 'raw_secret'),
    ('urlencoded', 'base64_secret')
]

for endpoint in endpoints:
    print(f"\n{'='*60}")
    print(f"Testing endpoint: {endpoint['name']}")
    print(f"URL: {endpoint['url']}")
    
    for payload_format, signature_method in test_cases:
        print(f"\n  Test: {payload_format} + {signature_method}")
        result = test_auth_method(endpoint, payload_format, signature_method)
        
        if isinstance(result, dict):
            print(f"    Status: {result['status_code']}")
            if result['status_code'] == 200:
                print(f"    SUCCESS!")
                print(f"    Response: {json.dumps(result['response'], indent=6)}")
            else:
                print(f"    Response: {result['response']}")
        else:
            print(f"    Error: {result}")

print(f"\n{'='*60}")
print("Test Complete")