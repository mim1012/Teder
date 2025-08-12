"""
코인원 서명 방식 변형 테스트
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

print("=== Signature Variants Test ===\n")

access_token = os.getenv('COINONE_ACCESS_TOKEN')
secret_key = os.getenv('COINONE_SECRET_KEY')

url = 'https://api.coinone.co.kr/v2/account/balance'
nonce = str(int(time.time() * 1000))

payload = {
    'access_token': access_token,
    'nonce': nonce
}

def test_signature_variant(variant_name, signature_func):
    """서명 방식 변형 테스트"""
    try:
        signature = signature_func()
        
        headers = {
            'Content-Type': 'application/json',
            'X-COINONE-SIGNATURE': signature,
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"{variant_name}:")
        print(f"  Signature: {signature[:50]}...")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Result: {data.get('result', 'Unknown')}")
            if data.get('result') == 'success':
                print(f"  SUCCESS! Balance data received")
                return True
            else:
                print(f"  Error: {data.get('errorMsg', data.get('error_msg', 'Unknown'))}")
        else:
            print(f"  HTTP Error: {response.text[:100]}...")
            
        print()
        return False
        
    except Exception as e:
        print(f"{variant_name}: Exception - {e}\n")
        return False

# 다양한 서명 방식 테스트
print("Testing different signature methods...\n")

# 1. JSON 문자열 + raw secret
def sig1():
    payload_str = json.dumps(payload, separators=(',', ':'))
    return hmac.new(
        secret_key.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

test_signature_variant("1. JSON + raw secret", sig1)

# 2. JSON 문자열 + raw secret (다른 순서)
def sig2():
    ordered_payload = {
        'nonce': nonce,
        'access_token': access_token
    }
    payload_str = json.dumps(ordered_payload, separators=(',', ':'))
    return hmac.new(
        secret_key.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

test_signature_variant("2. JSON (reordered) + raw secret", sig2)

# 3. Base64 encoded payload + raw secret
def sig3():
    payload_str = json.dumps(payload, separators=(',', ':'))
    encoded_payload = base64.b64encode(payload_str.encode('utf-8')).decode('utf-8')
    return hmac.new(
        secret_key.encode('utf-8'),
        encoded_payload.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

test_signature_variant("3. Base64 payload + raw secret", sig3)

# 4. SHA256 instead of SHA512
def sig4():
    payload_str = json.dumps(payload, separators=(',', ':'))
    return hmac.new(
        secret_key.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

test_signature_variant("4. JSON + raw secret (SHA256)", sig4)

# 5. Different JSON formatting
def sig5():
    payload_str = json.dumps(payload, sort_keys=True)
    return hmac.new(
        secret_key.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

test_signature_variant("5. JSON sorted + raw secret", sig5)

# 6. Try with uppercase secret
def sig6():
    payload_str = json.dumps(payload, separators=(',', ':'))
    return hmac.new(
        secret_key.upper().encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

test_signature_variant("6. JSON + uppercase secret", sig6)

# 7. Try with lowercase secret
def sig7():
    payload_str = json.dumps(payload, separators=(',', ':'))
    return hmac.new(
        secret_key.lower().encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

test_signature_variant("7. JSON + lowercase secret", sig7)

# 8. Try with secret as hex decoded
def sig8():
    try:
        payload_str = json.dumps(payload, separators=(',', ':'))
        hex_secret = bytes.fromhex(secret_key.replace('-', ''))
        return hmac.new(
            hex_secret,
            payload_str.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
    except:
        return "FAILED_TO_DECODE_HEX"

test_signature_variant("8. JSON + hex decoded secret", sig8)

print("=== Test Complete ===")
print("If none worked, the Secret Key might be incorrect or in a different format.")