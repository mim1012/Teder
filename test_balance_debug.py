"""
잔고 조회 디버깅
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

print("=== Balance Debug Test ===\n")

# 환경 변수 확인
access_token = os.getenv('COINONE_ACCESS_TOKEN')
secret_key = os.getenv('COINONE_SECRET_KEY')

print(f"Access Token: {access_token}")
print(f"Secret Key: {secret_key}")
print(f"Access Token Length: {len(access_token) if access_token else 0}")
print(f"Secret Key Length: {len(secret_key) if secret_key else 0}")

if not access_token or not secret_key:
    print("API keys not found!")
    exit(1)

print("\n" + "="*50)

# 1. Try with current keys
print("\n1. Testing with current API keys...")

url = "https://api.coinone.co.kr/v2.1/account/balance"
nonce = str(int(time.time() * 1000))

# 요청 데이터
payload = {
    'access_token': access_token,
    'nonce': nonce
}

# HMAC 서명 생성 시도
try:
    # Method 1: secret_key를 그대로 사용
    encoded_payload = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(
        secret_key.encode('utf-8'),
        encoded_payload,
        hashlib.sha512
    ).hexdigest()
    
    headers = {
        'Content-Type': 'application/json',
        'X-COINONE-SIGNATURE': signature
    }
    
    print(f"Payload: {json.dumps(payload)}")
    print(f"Signature: {signature[:50]}...")
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Response:")
        print(json.dumps(data, indent=2))
    else:
        print("Error Response:")
        print(response.text)

except Exception as e:
    print(f"Method 1 failed: {e}")

print("\n" + "="*50)

# 2. Try with base64 decoded secret
print("\n2. Testing with base64 decoded secret...")

try:
    # secret_key가 base64 인코딩되어 있다고 가정하고 디코드 시도
    decoded_secret = base64.b64decode(secret_key)
    
    signature = hmac.new(
        decoded_secret,
        encoded_payload,
        hashlib.sha512
    ).hexdigest()
    
    headers = {
        'Content-Type': 'application/json',
        'X-COINONE-SIGNATURE': signature
    }
    
    print(f"Base64 decoded signature: {signature[:50]}...")
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Response:")
        print(json.dumps(data, indent=2))
    else:
        print("Error Response:")
        print(response.text)

except Exception as e:
    print(f"Method 2 failed: {e}")

print("\n" + "="*50)

# 3. Check API documentation format
print("\n3. Checking different signature methods...")

# Method 3: 다른 페이로드 형식
try:
    # URL 인코딩 형식으로 시도
    from urllib.parse import urlencode
    
    payload_str = urlencode(payload)
    signature = hmac.new(
        secret_key.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-COINONE-SIGNATURE': signature
    }
    
    print(f"URL encoded payload: {payload_str}")
    print(f"URL encoded signature: {signature[:50]}...")
    
    response = requests.post(url, data=payload, headers=headers, timeout=30)
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Response:")
        print(json.dumps(data, indent=2))
    else:
        print("Error Response:")
        print(response.text)

except Exception as e:
    print(f"Method 3 failed: {e}")

print("\n=== Debug Complete ===")