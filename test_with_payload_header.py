"""
X-COINONE-PAYLOAD 헤더 포함 테스트
"""

import os
import sys
import requests
import json
import hmac
import hashlib
import time
import base64

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("=== Payload Header Test ===\n")

access_token = os.getenv('COINONE_ACCESS_TOKEN')
secret_key = os.getenv('COINONE_SECRET_KEY')

url = 'https://api.coinone.co.kr/v2/account/balance'
nonce = str(int(time.time() * 1000))

payload = {
    'access_token': access_token,
    'nonce': nonce
}

def test_with_payload_header():
    """X-COINONE-PAYLOAD 헤더 포함 테스트"""
    
    # JSON 페이로드 문자열
    payload_str = json.dumps(payload, separators=(',', ':'))
    
    # Base64 인코딩된 페이로드
    encoded_payload = base64.b64encode(payload_str.encode('utf-8')).decode('utf-8')
    
    # 서명 생성 (인코딩된 페이로드 사용)
    signature = hmac.new(
        secret_key.encode('utf-8'),
        encoded_payload.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    # 헤더 설정
    headers = {
        'Content-Type': 'application/json',
        'X-COINONE-SIGNATURE': signature,
        'X-COINONE-PAYLOAD': encoded_payload
    }
    
    print(f"Payload: {payload_str}")
    print(f"Encoded Payload: {encoded_payload}")
    print(f"Signature: {signature[:50]}...")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response:")
            print(json.dumps(data, indent=2))
            
            if data.get('result') == 'success':
                print("\nSUCCESS! Balance retrieved!")
                return True
            else:
                error_code = data.get('errorCode', data.get('error_code', 'Unknown'))
                error_msg = data.get('errorMsg', data.get('error_msg', 'Unknown'))
                print(f"\nAPI Error {error_code}: {error_msg}")
        else:
            print("HTTP Error Response:")
            print(response.text)
        
        return False
        
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_alternative_methods():
    """다른 방식들도 테스트"""
    
    print("\n" + "="*50)
    print("Testing alternative methods...")
    
    # Method 1: 원본 페이로드로 서명
    payload_str = json.dumps(payload, separators=(',', ':'))
    encoded_payload = base64.b64encode(payload_str.encode('utf-8')).decode('utf-8')
    
    signature = hmac.new(
        secret_key.encode('utf-8'),
        payload_str.encode('utf-8'),  # 인코딩 전 페이로드로 서명
        hashlib.sha512
    ).hexdigest()
    
    headers = {
        'Content-Type': 'application/json',
        'X-COINONE-SIGNATURE': signature,
        'X-COINONE-PAYLOAD': encoded_payload
    }
    
    print(f"\nMethod 1: Original payload signature")
    print(f"Signature: {signature[:50]}...")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('result') == 'success':
                print("Method 1 SUCCESS!")
                return True
            else:
                print(f"Method 1 Error: {data.get('errorMsg', data.get('error_msg'))}")
    except Exception as e:
        print(f"Method 1 Exception: {e}")
    
    # Method 2: POST 본문 없이 헤더만
    headers_only = {
        'X-COINONE-SIGNATURE': signature,
        'X-COINONE-PAYLOAD': encoded_payload
    }
    
    print(f"\nMethod 2: Headers only (no POST body)")
    
    try:
        response = requests.post(url, headers=headers_only, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('result') == 'success':
                print("Method 2 SUCCESS!")
                return True
            else:
                print(f"Method 2 Error: {data.get('errorMsg', data.get('error_msg'))}")
    except Exception as e:
        print(f"Method 2 Exception: {e}")
    
    return False

# 테스트 실행
print("Testing with X-COINONE-PAYLOAD header...")
success = test_with_payload_header()

if not success:
    success = test_alternative_methods()

if success:
    print(f"\nAUTHENTICATION SUCCESSFUL!")
    print("Your API keys are working correctly!")
else:
    print(f"\nAll methods failed.")
    print("Please double-check your API keys on Coinone website.")

print("\n=== Test Complete ===")