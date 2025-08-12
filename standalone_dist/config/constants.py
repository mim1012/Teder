"""
상수 정의 파일
"""
from enum import Enum

class OrderType(Enum):
    """주문 유형"""
    LIMIT = "limit"
    MARKET = "market"

class OrderSide(Enum):
    """주문 방향"""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    """주문 상태"""
    PENDING = "pending"
    PARTIAL_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"

class TradingState(Enum):
    """거래 상태"""
    WAITING_FOR_BUY = "waiting_for_buy"
    POSITION_HELD = "position_held"
    WAITING_FOR_SELL = "waiting_for_sell"
    STRATEGY_COMPLETED = "strategy_completed"

class SignalType(Enum):
    """매매 신호 유형"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    EMERGENCY_SELL = "emergency_sell"

# API Endpoints
API_ENDPOINTS = {
    # Public API
    'ticker': '/public/v2/ticker/KRW/{currency}',
    'orderbook': '/public/v2/orderbook/KRW/{currency}',
    'trades': '/public/v2/trades/KRW/{currency}',
    'candles': '/public/v2/chart/KRW/{currency}',
    
    # Private API
    'balance': '/v2/account/balance',
    'order': '/v2.1/order/limit',
    'market_order': '/v2.1/order/market',
    'cancel': '/v2.1/order/cancel',
    'order_info': '/v2.1/order/order_info',
    'orders': '/v2.1/order/orders',
    'trades_history': '/v2.1/order/trades',
}

# Error Messages
ERROR_MESSAGES = {
    'api_key_missing': 'API 키가 설정되지 않았습니다.',
    'connection_error': '네트워크 연결 오류가 발생했습니다.',
    'rate_limit': 'API 요청 한도를 초과했습니다.',
    'insufficient_balance': '잔고가 부족합니다.',
    'order_failed': '주문 실행에 실패했습니다.',
    'invalid_price': '유효하지 않은 가격입니다.',
    'invalid_quantity': '유효하지 않은 수량입니다.',
}

# Success Messages
SUCCESS_MESSAGES = {
    'order_placed': '주문이 성공적으로 접수되었습니다.',
    'order_cancelled': '주문이 취소되었습니다.',
    'position_closed': '포지션이 청산되었습니다.',
    'strategy_started': '전략이 시작되었습니다.',
    'strategy_stopped': '전략이 중지되었습니다.',
}