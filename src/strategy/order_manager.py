"""
주문 관리 모듈
- 지정가/시장가 주문 관리
- 부분 체결 처리
- 주문 상태 추적
- 미체결 주문 취소
"""
import time
import logging
import asyncio
from typing import Dict, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone

from config.settings import TRADING_CONFIG, SAFETY_CONFIG
from config.constants import OrderSide, OrderType
from src.api.coinone_client import CoinoneClient
from src.api.exceptions import CoinoneAPIError


class OrderStatus(Enum):
    """주문 상태"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class OrderInfo:
    """주문 정보"""
    order_id: Optional[str] = None
    symbol: str = ""
    side: str = ""  # 'buy' or 'sell'
    order_type: str = ""  # 'limit' or 'market'
    quantity: float = 0.0
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0
    average_price: float = 0.0
    created_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'remaining_quantity': self.remaining_quantity,
            'average_price': self.average_price,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'updated_time': self.updated_time.isoformat() if self.updated_time else None,
            'error_message': self.error_message
        }


class OrderManager:
    """주문 관리 클래스"""
    
    def __init__(self, api_client: CoinoneClient):
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        self.symbol = TRADING_CONFIG['symbol']
        self.currency = TRADING_CONFIG['currency']
        
        # 활성 주문 추적
        self.active_orders: Dict[str, OrderInfo] = {}
        self.order_history: List[OrderInfo] = []
        
        # 설정
        self.partial_fill_wait_time = TRADING_CONFIG['partial_fill_wait_time']  # 10분
        self.max_order_amount = SAFETY_CONFIG['max_order_amount']
    
    def place_limit_buy_order(
        self, 
        quantity: float, 
        price: float
    ) -> Tuple[bool, OrderInfo]:
        """
        지정가 매수 주문
        
        Args:
            quantity: 주문 수량
            price: 주문 가격
            
        Returns:
            (성공 여부, 주문 정보)
        """
        order_info = OrderInfo(
            symbol=self.symbol,
            side='buy',
            order_type='limit',
            quantity=quantity,
            price=price,
            status=OrderStatus.PENDING,
            remaining_quantity=quantity,
            created_time=datetime.now(timezone.utc)
        )
        
        try:
            # 금액 검증
            total_amount = quantity * price
            if not self._validate_order_amount(total_amount):
                order_info.status = OrderStatus.FAILED
                order_info.error_message = "Order amount validation failed"
                return False, order_info
            
            # API 호출
            self.logger.info(f"Placing limit buy order: {quantity} {self.symbol} at {price}")
            
            response = self.api_client.place_limit_order(
                side=OrderSide.BUY,
                currency=self.symbol,
                price=price,
                qty=quantity
            )
            
            # 응답 처리
            if 'orderId' in response:
                order_info.order_id = response['orderId']
                order_info.status = OrderStatus.SUBMITTED
                order_info.updated_time = datetime.now(timezone.utc)
                
                # 활성 주문에 추가
                self.active_orders[order_info.order_id] = order_info
                
                self.logger.info(f"Buy order placed successfully: {order_info.order_id}")
                return True, order_info
                
            else:
                order_info.status = OrderStatus.FAILED
                order_info.error_message = "No order ID in response"
                self.logger.error(f"Buy order failed: {response}")
                return False, order_info
                
        except CoinoneAPIError as e:
            order_info.status = OrderStatus.FAILED
            order_info.error_message = str(e)
            self.logger.error(f"API error placing buy order: {e}")
            return False, order_info
        
        except Exception as e:
            order_info.status = OrderStatus.FAILED
            order_info.error_message = str(e)
            self.logger.error(f"Unexpected error placing buy order: {e}")
            return False, order_info
    
    def place_limit_sell_order(
        self, 
        quantity: float, 
        price: float
    ) -> Tuple[bool, OrderInfo]:
        """
        지정가 매도 주문 (익절용)
        
        Args:
            quantity: 주문 수량
            price: 주문 가격
            
        Returns:
            (성공 여부, 주문 정보)
        """
        order_info = OrderInfo(
            symbol=self.symbol,
            side='sell',
            order_type='limit',
            quantity=quantity,
            price=price,
            status=OrderStatus.PENDING,
            remaining_quantity=quantity,
            created_time=datetime.now(timezone.utc)
        )
        
        try:
            # API 호출
            self.logger.info(f"Placing limit sell order: {quantity} {self.symbol} at {price}")
            
            response = self.api_client.place_limit_order(
                side=OrderSide.SELL,
                currency=self.symbol,
                price=price,
                qty=quantity
            )
            
            # 응답 처리
            if 'orderId' in response:
                order_info.order_id = response['orderId']
                order_info.status = OrderStatus.SUBMITTED
                order_info.updated_time = datetime.now(timezone.utc)
                
                # 활성 주문에 추가
                self.active_orders[order_info.order_id] = order_info
                
                self.logger.info(f"Sell order placed successfully: {order_info.order_id}")
                return True, order_info
                
            else:
                order_info.status = OrderStatus.FAILED
                order_info.error_message = "No order ID in response"
                self.logger.error(f"Sell order failed: {response}")
                return False, order_info
                
        except CoinoneAPIError as e:
            order_info.status = OrderStatus.FAILED
            order_info.error_message = str(e)
            self.logger.error(f"API error placing sell order: {e}")
            return False, order_info
        
        except Exception as e:
            order_info.status = OrderStatus.FAILED
            order_info.error_message = str(e)
            self.logger.error(f"Unexpected error placing sell order: {e}")
            return False, order_info
    
    def place_market_sell_order(self, quantity: float) -> Tuple[bool, OrderInfo]:
        """
        시장가 매도 주문 (손절/청산용)
        
        Args:
            quantity: 주문 수량
            
        Returns:
            (성공 여부, 주문 정보)
        """
        order_info = OrderInfo(
            symbol=self.symbol,
            side='sell',
            order_type='market',
            quantity=quantity,
            status=OrderStatus.PENDING,
            remaining_quantity=quantity,
            created_time=datetime.now(timezone.utc)
        )
        
        try:
            # API 호출
            self.logger.info(f"Placing market sell order: {quantity} {self.symbol}")
            
            response = self.api_client.place_market_order(
                side=OrderSide.SELL,
                currency=self.symbol,
                qty=quantity
            )
            
            # 시장가 주문은 즉시 체결되므로 FILLED 상태로 처리
            if 'orderId' in response:
                order_info.order_id = response['orderId']
                order_info.status = OrderStatus.FILLED
                order_info.filled_quantity = quantity
                order_info.remaining_quantity = 0.0
                order_info.updated_time = datetime.now(timezone.utc)
                
                # 체결 가격 정보가 있으면 설정
                if 'price' in response:
                    order_info.average_price = float(response['price'])
                
                self.logger.info(f"Market sell order executed: {order_info.order_id}")
                return True, order_info
                
            else:
                order_info.status = OrderStatus.FAILED
                order_info.error_message = "No order ID in response"
                self.logger.error(f"Market sell order failed: {response}")
                return False, order_info
                
        except CoinoneAPIError as e:
            order_info.status = OrderStatus.FAILED
            order_info.error_message = str(e)
            self.logger.error(f"API error placing market sell order: {e}")
            return False, order_info
        
        except Exception as e:
            order_info.status = OrderStatus.FAILED
            order_info.error_message = str(e)
            self.logger.error(f"Unexpected error placing market sell order: {e}")
            return False, order_info
    
    def cancel_order(self, order_id: str) -> bool:
        """
        주문 취소
        
        Args:
            order_id: 주문 ID
            
        Returns:
            취소 성공 여부
        """
        try:
            self.logger.info(f"Cancelling order: {order_id}")
            
            response = self.api_client.cancel_order(order_id, self.symbol)
            
            # 활성 주문에서 제거하고 히스토리에 추가
            if order_id in self.active_orders:
                order_info = self.active_orders[order_id]
                order_info.status = OrderStatus.CANCELLED
                order_info.updated_time = datetime.now(timezone.utc)
                
                self.order_history.append(order_info)
                del self.active_orders[order_id]
            
            self.logger.info(f"Order cancelled successfully: {order_id}")
            return True
            
        except CoinoneAPIError as e:
            self.logger.error(f"API error cancelling order {order_id}: {e}")
            return False
        
        except Exception as e:
            self.logger.error(f"Unexpected error cancelling order {order_id}: {e}")
            return False
    
    def update_order_status(self, order_id: str) -> Optional[OrderInfo]:
        """
        주문 상태 업데이트
        
        Args:
            order_id: 주문 ID
            
        Returns:
            업데이트된 주문 정보
        """
        try:
            response = self.api_client.get_order_info(order_id, self.symbol)
            
            if order_id in self.active_orders:
                order_info = self.active_orders[order_id]
                
                # 상태 업데이트
                api_status = response.get('status', '')
                if api_status == 'filled':
                    order_info.status = OrderStatus.FILLED
                    order_info.filled_quantity = float(response.get('filledQty', 0))
                    order_info.remaining_quantity = 0.0
                elif api_status == 'partially_filled':
                    order_info.status = OrderStatus.PARTIALLY_FILLED
                    order_info.filled_quantity = float(response.get('filledQty', 0))
                    order_info.remaining_quantity = order_info.quantity - order_info.filled_quantity
                elif api_status == 'cancelled':
                    order_info.status = OrderStatus.CANCELLED
                
                # 평균 체결가 업데이트
                if 'avgPrice' in response:
                    order_info.average_price = float(response['avgPrice'])
                
                order_info.updated_time = datetime.now(timezone.utc)
                
                # 완전 체결 또는 취소된 경우 히스토리로 이동
                if order_info.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                    self.order_history.append(order_info)
                    del self.active_orders[order_id]
                
                return order_info
            
        except CoinoneAPIError as e:
            self.logger.error(f"API error updating order status {order_id}: {e}")
        
        except Exception as e:
            self.logger.error(f"Unexpected error updating order status {order_id}: {e}")
        
        return None
    
    def wait_for_partial_fill_timeout(self, order_id: str) -> Tuple[bool, float]:
        """
        부분 체결 대기 및 타임아웃 처리
        
        Args:
            order_id: 주문 ID
            
        Returns:
            (체결 완료 여부, 체결된 수량)
        """
        start_time = time.time()
        
        while time.time() - start_time < self.partial_fill_wait_time:
            # 주문 상태 업데이트
            order_info = self.update_order_status(order_id)
            
            if order_info:
                if order_info.status == OrderStatus.FILLED:
                    self.logger.info(f"Order {order_id} fully filled: {order_info.filled_quantity}")
                    return True, order_info.filled_quantity
                
                elif order_info.status == OrderStatus.PARTIALLY_FILLED:
                    self.logger.info(f"Order {order_id} partially filled: {order_info.filled_quantity}")
                
                elif order_info.status == OrderStatus.CANCELLED:
                    self.logger.info(f"Order {order_id} was cancelled")
                    return False, order_info.filled_quantity
            
            # 5초 대기
            time.sleep(5)
        
        # 타임아웃 발생 - 미체결량 취소
        self.logger.info(f"Partial fill timeout for order {order_id}, cancelling remaining")
        
        order_info = self.active_orders.get(order_id)
        filled_quantity = order_info.filled_quantity if order_info else 0.0
        
        # 미체결량 취소
        self.cancel_order(order_id)
        
        return False, filled_quantity
    
    def get_best_ask_price(self) -> Optional[float]:
        """
        매도1호가 조회
        
        Returns:
            매도1호가
        """
        try:
            _, ask_price = self.api_client.get_best_bid_ask(self.symbol)
            return ask_price
        except Exception as e:
            self.logger.error(f"Error getting best ask price: {e}")
            return None
    
    def cancel_all_active_orders(self) -> int:
        """
        모든 활성 주문 취소
        
        Returns:
            취소된 주문 수
        """
        cancelled_count = 0
        active_order_ids = list(self.active_orders.keys())
        
        for order_id in active_order_ids:
            if self.cancel_order(order_id):
                cancelled_count += 1
        
        self.logger.info(f"Cancelled {cancelled_count} active orders")
        return cancelled_count
    
    def get_active_orders(self) -> List[Dict]:
        """활성 주문 목록 조회"""
        return [order.to_dict() for order in self.active_orders.values()]
    
    def get_order_history(self, limit: int = 20) -> List[Dict]:
        """주문 히스토리 조회"""
        recent_orders = self.order_history[-limit:] if self.order_history else []
        return [order.to_dict() for order in recent_orders]
    
    def has_active_orders(self) -> bool:
        """활성 주문 존재 여부"""
        return len(self.active_orders) > 0
    
    def has_active_sell_orders(self) -> bool:
        """활성 매도 주문 존재 여부"""
        return any(order.side == 'sell' for order in self.active_orders.values())
    
    def _validate_order_amount(self, amount: float) -> bool:
        """주문 금액 유효성 검사"""
        if amount <= 0:
            self.logger.error(f"Invalid order amount: {amount}")
            return False
        
        if amount > self.max_order_amount:
            self.logger.error(f"Order amount exceeds limit: {amount} > {self.max_order_amount}")
            return False
        
        return True
    
    def get_order_summary(self) -> Dict:
        """주문 요약 정보"""
        return {
            'active_orders_count': len(self.active_orders),
            'total_orders_today': len(self.order_history),
            'has_active_orders': self.has_active_orders(),
            'has_active_sell_orders': self.has_active_sell_orders(),
            'active_orders': self.get_active_orders()
        }