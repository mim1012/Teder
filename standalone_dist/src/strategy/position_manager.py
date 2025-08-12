"""
포지션 관리 모듈
- 매수/매도 포지션 추적
- 평균 매수가 계산
- 수익률 계산
- 보유 수량 관리
"""
import time
import logging
from typing import Dict, Optional, List, Tuple
from decimal import Decimal, ROUND_UP
from dataclasses import dataclass
from datetime import datetime, timezone

from config.settings import TRADING_CONFIG, SAFETY_CONFIG


@dataclass
class Position:
    """포지션 정보"""
    symbol: str
    currency: str
    total_quantity: float = 0.0
    average_price: float = 0.0
    total_cost: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    entry_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'symbol': self.symbol,
            'currency': self.currency,
            'total_quantity': self.total_quantity,
            'average_price': self.average_price,
            'total_cost': self.total_cost,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'last_update': self.last_update.isoformat() if self.last_update else None
        }


@dataclass
class Trade:
    """거래 기록"""
    trade_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    cost: float
    fee: float
    timestamp: datetime
    order_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'cost': self.cost,
            'fee': self.fee,
            'timestamp': self.timestamp.isoformat(),
            'order_id': self.order_id
        }


class PositionManager:
    """포지션 관리 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.symbol = TRADING_CONFIG['symbol']
        self.currency = TRADING_CONFIG['currency'] 
        
        # 현재 포지션
        self.position = Position(
            symbol=self.symbol,
            currency=self.currency
        )
        
        # 거래 기록
        self.trades: List[Trade] = []
        
        # 통계
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_fees = 0.0
        
    def has_position(self) -> bool:
        """포지션 보유 여부 확인"""
        return self.position.total_quantity > 0
    
    def get_position_duration(self) -> Optional[float]:
        """포지션 보유 시간 (초) 반환"""
        if not self.has_position() or not self.position.entry_time:
            return None
        
        now = datetime.now(timezone.utc)
        duration = (now - self.position.entry_time).total_seconds()
        return duration
    
    def is_position_timeout(self) -> bool:
        """포지션 타임아웃 여부 확인 (24시간)"""
        duration = self.get_position_duration()
        if duration is None:
            return False
        
        timeout_seconds = TRADING_CONFIG['position_timeout']
        return duration >= timeout_seconds
    
    def add_buy_trade(
        self, 
        quantity: float, 
        price: float, 
        fee: float = 0.0,
        trade_id: str = None,
        order_id: str = None
    ) -> bool:
        """
        매수 거래 추가
        
        Args:
            quantity: 매수 수량
            price: 매수 가격
            fee: 수수료
            trade_id: 거래 ID
            order_id: 주문 ID
            
        Returns:
            처리 성공 여부
        """
        try:
            # 거래 기록 생성
            trade = Trade(
                trade_id=trade_id or f"buy_{int(time.time())}",
                symbol=self.symbol,
                side='buy',
                quantity=quantity,
                price=price,
                cost=quantity * price,
                fee=fee,
                timestamp=datetime.now(timezone.utc),
                order_id=order_id
            )
            
            # 평균 매수가 계산
            new_total_cost = self.position.total_cost + trade.cost + fee
            new_total_quantity = self.position.total_quantity + quantity
            
            if new_total_quantity > 0:
                new_average_price = new_total_cost / new_total_quantity
            else:
                new_average_price = price
            
            # 포지션 업데이트
            self.position.total_quantity = new_total_quantity
            self.position.average_price = new_average_price
            self.position.total_cost = new_total_cost
            self.position.last_update = datetime.now(timezone.utc)
            
            # 첫 매수인 경우 진입 시간 설정
            if self.position.entry_time is None:
                self.position.entry_time = datetime.now(timezone.utc)
            
            # 거래 기록 추가
            self.trades.append(trade)
            self.total_trades += 1
            self.total_fees += fee
            
            self.logger.info(
                f"Buy trade added: {quantity} {self.symbol} at {price} "
                f"(avg_price: {new_average_price:.4f})"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding buy trade: {e}")
            return False
    
    def add_sell_trade(
        self, 
        quantity: float, 
        price: float, 
        fee: float = 0.0,
        trade_id: str = None,
        order_id: str = None
    ) -> bool:
        """
        매도 거래 추가
        
        Args:
            quantity: 매도 수량
            price: 매도 가격
            fee: 수수료
            trade_id: 거래 ID
            order_id: 주문 ID
            
        Returns:
            처리 성공 여부
        """
        try:
            if self.position.total_quantity < quantity:
                self.logger.error("Insufficient position for sell trade")
                return False
            
            # 거래 기록 생성
            trade = Trade(
                trade_id=trade_id or f"sell_{int(time.time())}",
                symbol=self.symbol,
                side='sell',
                quantity=quantity,
                price=price,
                cost=quantity * price,
                fee=fee,
                timestamp=datetime.now(timezone.utc),
                order_id=order_id
            )
            
            # 실현 손익 계산
            cost_basis = quantity * self.position.average_price
            proceeds = trade.cost - fee
            realized_pnl = proceeds - cost_basis
            
            # 포지션 업데이트
            self.position.total_quantity -= quantity
            self.position.total_cost -= cost_basis
            self.position.realized_pnl += realized_pnl
            self.position.last_update = datetime.now(timezone.utc)
            
            # 포지션이 완전히 청산된 경우
            if self.position.total_quantity <= 1e-8:  # 부동소수점 오차 고려
                self.position.total_quantity = 0.0
                self.position.average_price = 0.0
                self.position.total_cost = 0.0
                self.position.entry_time = None
            
            # 거래 기록 추가
            self.trades.append(trade)
            self.total_trades += 1
            self.total_fees += fee
            
            # 손익 통계 업데이트
            if realized_pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            self.logger.info(
                f"Sell trade added: {quantity} {self.symbol} at {price} "
                f"(PnL: {realized_pnl:.2f})"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding sell trade: {e}")
            return False
    
    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """
        미실현 손익 계산
        
        Args:
            current_price: 현재 가격
            
        Returns:
            미실현 손익
        """
        if not self.has_position():
            return 0.0
        
        current_value = self.position.total_quantity * current_price
        unrealized_pnl = current_value - self.position.total_cost
        
        self.position.unrealized_pnl = unrealized_pnl
        return unrealized_pnl
    
    def calculate_profit_target_price(self) -> float:
        """
        익절 목표 가격 계산 (평균매수가 + 4원)
        
        Returns:
            익절 목표 가격
        """
        if not self.has_position():
            return 0.0
        
        profit_target = TRADING_CONFIG['profit_target']
        target_price = self.position.average_price + profit_target
        
        return target_price
    
    def calculate_return_percentage(self, current_price: float) -> float:
        """
        수익률 계산
        
        Args:
            current_price: 현재 가격
            
        Returns:
            수익률 (%)
        """
        if not self.has_position() or self.position.average_price == 0:
            return 0.0
        
        return_pct = ((current_price - self.position.average_price) / self.position.average_price) * 100
        return return_pct
    
    def get_position_summary(self, current_price: float = None) -> Dict:
        """
        포지션 요약 정보
        
        Args:
            current_price: 현재 가격
            
        Returns:
            포지션 요약
        """
        summary = {
            'has_position': self.has_position(),
            'symbol': self.symbol,
            'quantity': self.position.total_quantity,
            'average_price': self.position.average_price,
            'total_cost': self.position.total_cost,
            'realized_pnl': self.position.realized_pnl,
            'entry_time': self.position.entry_time.isoformat() if self.position.entry_time else None,
            'position_duration': self.get_position_duration(),
            'is_timeout': self.is_position_timeout()
        }
        
        if current_price:
            summary.update({
                'current_price': current_price,
                'unrealized_pnl': self.calculate_unrealized_pnl(current_price),
                'return_percentage': self.calculate_return_percentage(current_price),
                'profit_target_price': self.calculate_profit_target_price(),
                'current_value': self.position.total_quantity * current_price
            })
        
        return summary
    
    def get_trading_statistics(self) -> Dict:
        """
        거래 통계 정보
        
        Returns:
            거래 통계
        """
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_fees': self.total_fees,
            'total_realized_pnl': self.position.realized_pnl
        }
    
    def reset_position(self):
        """포지션 초기화"""
        self.position = Position(
            symbol=self.symbol,
            currency=self.currency
        )
        self.logger.info("Position reset")
    
    def validate_trade_amount(self, amount: float, side: str) -> bool:
        """
        거래 금액 유효성 검사
        
        Args:
            amount: 거래 금액
            side: 거래 방향 ('buy' or 'sell')
            
        Returns:
            유효 여부
        """
        max_amount = SAFETY_CONFIG['max_order_amount']
        
        if amount <= 0:
            self.logger.error(f"Invalid trade amount: {amount}")
            return False
        
        if amount > max_amount:
            self.logger.error(f"Trade amount exceeds limit: {amount} > {max_amount}")
            return False
        
        if side == 'sell' and amount > self.position.total_quantity:
            self.logger.error(f"Insufficient position for sell: {amount} > {self.position.total_quantity}")
            return False
        
        return True
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """
        최근 거래 기록 조회
        
        Args:
            limit: 조회할 거래 수
            
        Returns:
            최근 거래 리스트
        """
        recent_trades = self.trades[-limit:] if self.trades else []
        return [trade.to_dict() for trade in recent_trades]
    
    def calculate_ceil_quantity(self, quantity: float, precision: int = 8) -> float:
        """
        수량을 올림 처리 (소수점 계산시 올림 처리 요구사항)
        
        Args:
            quantity: 원본 수량
            precision: 소수점 자릿수
            
        Returns:
            올림 처리된 수량
        """
        decimal_quantity = Decimal(str(quantity))
        factor = Decimal('10') ** precision
        
        # 소수점 이하를 올림 처리
        ceiled = (decimal_quantity * factor).quantize(Decimal('1'), rounding=ROUND_UP) / factor
        
        return float(ceiled)