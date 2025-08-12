"""
코인원 API 클라이언트 테스트
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api import CoinoneClient, CoinoneAuth
from src.api.exceptions import AuthenticationError, NetworkError
from config.constants import OrderSide


class TestCoinoneAuth:
    """코인원 인증 테스트"""
    
    def test_auth_initialization_success(self):
        """정상적인 인증 객체 초기화 테스트"""
        auth = CoinoneAuth("test_token", "test_secret")
        assert auth.access_token == "test_token"
        assert auth.secret_key == "test_secret"
    
    def test_auth_initialization_failure(self):
        """인증 정보 누락시 예외 발생 테스트"""
        with pytest.raises(AuthenticationError):
            CoinoneAuth(None, None)
    
    def test_nonce_generation(self):
        """nonce 생성 테스트"""
        auth = CoinoneAuth("test_token", "test_secret")
        nonce1 = auth._generate_nonce()
        nonce2 = auth._generate_nonce()
        assert isinstance(nonce1, int)
        assert isinstance(nonce2, int)
        assert nonce2 > nonce1
    
    def test_headers_generation(self):
        """인증 헤더 생성 테스트"""
        auth = CoinoneAuth("test_token", "test_secret")
        headers = auth.get_headers({'test': 'value'})
        
        assert 'X-COINONE-PAYLOAD' in headers
        assert 'X-COINONE-SIGNATURE' in headers
        assert headers['Content-Type'] == 'application/json'


class TestCoinoneClient:
    """코인원 클라이언트 테스트"""
    
    @patch('src.api.coinone_client.CoinoneAuth')
    def test_client_initialization(self, mock_auth):
        """클라이언트 초기화 테스트"""
        client = CoinoneClient("test_token", "test_secret")
        assert client.base_url == "https://api.coinone.co.kr"
        assert client.timeout == 30
        mock_auth.assert_called_once()
    
    @patch('requests.Session.get')
    def test_get_ticker_success(self, mock_get):
        """현재가 조회 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'errorCode': 0,
            'last': '1350000',
            'high': '1360000',
            'low': '1340000',
            'volume': '1000.123'
        }
        mock_get.return_value = mock_response
        
        with patch('src.api.coinone_client.CoinoneAuth'):
            client = CoinoneClient("test_token", "test_secret")
            result = client.get_ticker('USDT')
            
            assert result['errorCode'] == 0
            assert 'last' in result
    
    @patch('requests.Session.get')
    def test_get_orderbook_success(self, mock_get):
        """호가 조회 성공 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'errorCode': 0,
            'bid': [{'price': '1349000', 'qty': '10.123'}],
            'ask': [{'price': '1351000', 'qty': '5.456'}]
        }
        mock_get.return_value = mock_response
        
        with patch('src.api.coinone_client.CoinoneAuth'):
            client = CoinoneClient("test_token", "test_secret")
            result = client.get_orderbook('USDT')
            
            assert result['errorCode'] == 0
            assert 'bid' in result
            assert 'ask' in result
    
    @patch('requests.Session.post')
    def test_place_limit_order_success(self, mock_post):
        """지정가 주문 성공 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'errorCode': 0,
            'orderId': '12345',
            'result': 'success'
        }
        mock_post.return_value = mock_response
        
        with patch('src.api.coinone_client.CoinoneAuth'):
            client = CoinoneClient("test_token", "test_secret")
            result = client.place_limit_order(
                OrderSide.BUY, 'USDT', 1350000, 100
            )
            
            assert result['errorCode'] == 0
            assert result['orderId'] == '12345'
    
    @patch('requests.Session.post')
    def test_get_balance_success(self, mock_post):
        """잔고 조회 성공 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'errorCode': 0,
            'KRW': {'avail': '1000000.0', 'balance': '1000000.0'},
            'USDT': {'avail': '100.0', 'balance': '100.0'}
        }
        mock_post.return_value = mock_response
        
        with patch('src.api.coinone_client.CoinoneAuth'):
            client = CoinoneClient("test_token", "test_secret")
            result = client.get_balance()
            
            assert result['errorCode'] == 0
            assert 'KRW' in result
            assert 'USDT' in result
    
    def test_get_best_bid_ask(self):
        """최우선 호가 조회 테스트"""
        with patch('src.api.coinone_client.CoinoneAuth'):
            client = CoinoneClient("test_token", "test_secret")
            
            # get_orderbook 메서드를 모킹
            mock_orderbook = {
                'bid': [{'price': '1349000'}],
                'ask': [{'price': '1351000'}]
            }
            client.get_orderbook = Mock(return_value=mock_orderbook)
            
            bid, ask = client.get_best_bid_ask('USDT')
            assert bid == 1349000.0
            assert ask == 1351000.0
    
    @patch('requests.Session.get')
    def test_network_error_handling(self, mock_get):
        """네트워크 오류 처리 테스트"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with patch('src.api.coinone_client.CoinoneAuth'):
            client = CoinoneClient("test_token", "test_secret")
            
            with pytest.raises(NetworkError):
                client.get_ticker('USDT')


if __name__ == "__main__":
    # 간단한 실행 테스트
    print("코인원 API 클라이언트 테스트를 실행합니다...")
    
    # 환경변수에서 API 키를 가져와서 테스트 (실제 키가 있는 경우)
    try:
        client = CoinoneClient()
        print("클라이언트 초기화 성공")
        
        # Public API 테스트 (실제 API 호출)
        try:
            ticker = client.get_ticker('USDT')
            print("현재가 조회 성공")
            print(f"  - 현재가: {ticker.get('last', 'N/A')}")
        except Exception as e:
            print(f"현재가 조회 실패: {e}")
        
        try:
            orderbook = client.get_orderbook('USDT')
            print("호가 조회 성공")
            if orderbook.get('bid') and orderbook.get('ask'):
                bid_price = orderbook['bid'][0]['price']
                ask_price = orderbook['ask'][0]['price']
                print(f"  - 매수1호가: {bid_price}")
                print(f"  - 매도1호가: {ask_price}")
        except Exception as e:
            print(f"호가 조회 실패: {e}")
            
    except AuthenticationError:
        print("환경변수에 API 키가 설정되지 않았습니다.")
        print("실제 API 테스트를 위해서는 .env 파일에 다음을 설정하세요:")
        print("COINONE_ACCESS_TOKEN=your_access_token")
        print("COINONE_SECRET_KEY=your_secret_key")
    except Exception as e:
        print(f"클라이언트 초기화 실패: {e}")
    
    print("\n테스트 완료!")