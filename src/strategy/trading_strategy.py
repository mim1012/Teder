"""
State Machine 패턴을 사용한 매매 전략 구현
- WAITING_FOR_BUY: 매수 대기
- POSITION_HELD: 포지션 보유중  
- WAITING_FOR_SELL: 매도 대기
- STRATEGY_COMPLETED: 전략 완료
"""
import time
import logging
import pandas as pd
from typing import Dict, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone

from config.settings import TRADING_CONFIG, INDICATORS_CONFIG, SYSTEM_CONFIG
from src.api.coinone_client import CoinoneClient
from src.indicators.rsi import RSICalculator
from src.indicators.ema import EMACalculator
from .position_manager import PositionManager
from .order_manager import OrderManager, OrderStatus


class TradingState(Enum):
    """거래 상태"""
    WAITING_FOR_BUY = "waiting_for_buy"
    POSITION_HELD = "position_held"
    WAITING_FOR_SELL = "waiting_for_sell"
    STRATEGY_COMPLETED = "strategy_completed"
    ERROR = "error"


@dataclass
class StrategyContext:
    """전략 컨텍스트"""
    current_state: TradingState = TradingState.WAITING_FOR_BUY
    buy_order_id: Optional[str] = None
    sell_order_id: Optional[str] = None
    last_buy_signal_time: Optional[datetime] = None
    last_sell_signal_time: Optional[datetime] = None
    cycle_start_time: Optional[datetime] = None
    error_message: Optional[str] = None
    restart_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'current_state': self.current_state.value,
            'buy_order_id': self.buy_order_id,
            'sell_order_id': self.sell_order_id,
            'last_buy_signal_time': self.last_buy_signal_time.isoformat() if self.last_buy_signal_time else None,
            'last_sell_signal_time': self.last_sell_signal_time.isoformat() if self.last_sell_signal_time else None,
            'cycle_start_time': self.cycle_start_time.isoformat() if self.cycle_start_time else None,
            'error_message': self.error_message,
            'restart_count': self.restart_count
        }


class TradingStrategy:
    """State Machine 기반 매매 전략"""
    
    def __init__(self, api_client: CoinoneClient):
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        # 매니저 초기화
        self.position_manager = PositionManager()
        self.order_manager = OrderManager(api_client)
        
        # 기술적 지표 계산기
        self.rsi_calculator = RSICalculator(INDICATORS_CONFIG['rsi_period'])
        self.ema_calculator = EMACalculator(INDICATORS_CONFIG['ema_period'])
        
        # 전략 컨텍스트
        self.context = StrategyContext()
        
        # 설정값
        self.symbol = TRADING_CONFIG['symbol']
        self.currency = TRADING_CONFIG['currency']
        self.dry_run = SYSTEM_CONFIG['dry_run']
        
        # 상태별 핸들러 매핑
        self.state_handlers = {
            TradingState.WAITING_FOR_BUY: self._handle_waiting_for_buy,
            TradingState.POSITION_HELD: self._handle_position_held,
            TradingState.WAITING_FOR_SELL: self._handle_waiting_for_sell,
            TradingState.STRATEGY_COMPLETED: self._handle_strategy_completed,
            TradingState.ERROR: self._handle_error
        }
        
        self.logger.info(f"Trading strategy initialized (dry_run: {self.dry_run})")
    
    def execute_cycle(self) -> Dict:
        """
        전략 사이클 실행
        
        Returns:
            실행 결과
        """
        try:
            # 현재 시장 데이터 조회
            market_data = self._get_market_data()
            if not market_data:
                return self._create_error_result("Failed to get market data")
            
            # 상태별 핸들러 실행
            handler = self.state_handlers.get(self.context.current_state)
            if not handler:
                return self._create_error_result(f"No handler for state: {self.context.current_state}")
            
            result = handler(market_data)
            
            # 결과에 공통 정보 추가
            result.update({
                'current_state': self.context.current_state.value,
                'timestamp': datetime.now().isoformat(),
                'market_data': market_data,
                'position_summary': self.position_manager.get_position_summary(market_data['current_price']),
                'order_summary': self.order_manager.get_order_summary()
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in execute_cycle: {e}")
            return self._create_error_result(str(e))
    
    def _handle_waiting_for_buy(self, market_data: Dict) -> Dict:
        """매수 대기 상태 처리"""
        self.logger.debug("Handling WAITING_FOR_BUY state")
        
        # 매수 조건 확인
        buy_signal = self._check_buy_conditions(market_data)
        
        if buy_signal['signal']:
            # 매수 신호 발생 - 매수 주문 실행
            return self._execute_buy_order(market_data, buy_signal)
        
        return {
            'action': 'waiting',
            'message': 'Waiting for buy signal',
            'buy_signal': buy_signal
        }
    
    def _handle_position_held(self, market_data: Dict) -> Dict:
        """포지션 보유 상태 처리"""
        self.logger.debug("Handling POSITION_HELD state")
        
        # 익절 매도 주문 실행 (평균매수가 + 4원)
        profit_target_price = self.position_manager.calculate_profit_target_price()
        current_price = market_data['current_price']
        
        # 즉시 익절 주문 실행
        return self._execute_profit_sell_order(profit_target_price)
    
    def _handle_waiting_for_sell(self, market_data: Dict) -> Dict:
        """매도 대기 상태 처리"""
        self.logger.debug("Handling WAITING_FOR_SELL state")
        
        # 손절/청산 조건 확인
        liquidation_signal = self._check_liquidation_conditions(market_data)
        
        if liquidation_signal['signal']:
            # 손절/청산 신호 발생 - 시장가 매도
            return self._execute_liquidation_sell_order(liquidation_signal)
        
        # 익절 주문 상태 확인
        if self.context.sell_order_id:
            order_info = self.order_manager.update_order_status(self.context.sell_order_id)
            
            if order_info and order_info.status == OrderStatus.FILLED:
                # 익절 완료
                return self._complete_profitable_cycle(order_info)
            
            elif order_info and order_info.status == OrderStatus.CANCELLED:
                # 익절 주문 취소됨 - 다시 주문하거나 청산
                return self._handle_sell_order_cancelled(market_data)
        
        return {
            'action': 'waiting',
            'message': 'Waiting for sell order execution or liquidation signal',
            'liquidation_signal': liquidation_signal,
            'sell_order_id': self.context.sell_order_id
        }
    
    def _handle_strategy_completed(self, market_data: Dict) -> Dict:
        """전략 완료 상태 처리"""
        self.logger.debug("Handling STRATEGY_COMPLETED state")
        
        # 재시작 대기 시간 확인
        restart_delay = TRADING_CONFIG['restart_delay']  # 1시간
        
        if self.context.cycle_start_time:
            elapsed = (datetime.now(timezone.utc) - self.context.cycle_start_time).total_seconds()
            
            if elapsed >= restart_delay:
                # 새 사이클 시작
                self._reset_for_new_cycle()
                return {
                    'action': 'restarted',
                    'message': 'Starting new trading cycle',
                    'cycle_count': self.context.restart_count
                }
        
        remaining_time = restart_delay - elapsed if self.context.cycle_start_time else restart_delay
        
        return {
            'action': 'waiting_restart',
            'message': f'Waiting for restart ({remaining_time:.0f}s remaining)',
            'remaining_time': remaining_time
        }
    
    def _handle_error(self, market_data: Dict) -> Dict:
        """에러 상태 처리"""
        self.logger.error(f"Handling ERROR state: {self.context.error_message}")
        
        # 모든 활성 주문 취소
        self.order_manager.cancel_all_active_orders()
        
        # 포지션이 있다면 시장가로 청산
        if self.position_manager.has_position():
            quantity = self.position_manager.position.total_quantity
            success, order_info = self.order_manager.place_market_sell_order(quantity)
            
            if success:
                self.position_manager.add_sell_trade(
                    quantity=order_info.filled_quantity,
                    price=order_info.average_price,
                    trade_id=order_info.order_id
                )
        
        # 상태 초기화
        self._reset_for_new_cycle()
        
        return {
            'action': 'error_recovered',
            'message': 'Recovered from error state',
            'previous_error': self.context.error_message
        }
    
    def _check_buy_conditions(self, market_data: Dict) -> Dict:
        """매수 조건 확인"""
        try:
            chart_data = market_data['chart_data']
            
            # RSI 조건 확인
            rsi_signal, rsi_analysis = self.rsi_calculator.check_buy_condition(chart_data)
            
            # EMA 조건 확인  
            ema_signal, ema_analysis = self.ema_calculator.check_buy_condition(chart_data)
            
            # 모든 조건 충족 여부
            buy_signal = rsi_signal and ema_signal
            
            return {
                'signal': buy_signal,
                'rsi_signal': rsi_signal,
                'ema_signal': ema_signal,
                'rsi_analysis': rsi_analysis,
                'ema_analysis': ema_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking buy conditions: {e}")
            return {
                'signal': False,
                'error': str(e)
            }
    
    def _check_liquidation_conditions(self, market_data: Dict) -> Dict:
        """손절/청산 조건 확인"""
        try:
            chart_data = market_data['chart_data']
            
            # 1. 24시간 경과 확인
            timeout_signal = self.position_manager.is_position_timeout()
            
            # 2. RSI > 70 확인
            rsi_signal, rsi_analysis = self.rsi_calculator.check_sell_condition(chart_data)
            
            # 3. EMA 기울기 지속 감소 확인
            ema_signal, ema_analysis = self.ema_calculator.check_sell_condition(chart_data)
            
            # 하나라도 충족하면 청산 신호
            liquidation_signal = timeout_signal or rsi_signal or ema_signal
            
            return {
                'signal': liquidation_signal,
                'timeout_signal': timeout_signal,
                'rsi_signal': rsi_signal,
                'ema_signal': ema_signal,
                'rsi_analysis': rsi_analysis,
                'ema_analysis': ema_analysis,
                'position_duration': self.position_manager.get_position_duration(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking liquidation conditions: {e}")
            return {
                'signal': False,
                'error': str(e)
            }
    
    def _execute_buy_order(self, market_data: Dict, buy_signal: Dict) -> Dict:
        """매수 주문 실행"""
        try:
            # 매도1호가 조회
            ask_price = self.order_manager.get_best_ask_price()
            if not ask_price:
                return self._create_error_result("Failed to get ask price")
            
            # 보유 원화 전량으로 수량 계산
            krw_balance = self.api_client.get_account_balance('KRW')
            if krw_balance <= 0:
                return self._create_error_result("Insufficient KRW balance")
            
            quantity = krw_balance / ask_price
            
            # 올림 처리 (요구사항)
            quantity = self.position_manager.calculate_ceil_quantity(quantity)
            
            if self.dry_run:
                # 모의 거래
                self.logger.info(f"DRY RUN: Buy {quantity} {self.symbol} at {ask_price}")
                self.context.current_state = TradingState.POSITION_HELD
                
                # 모의 포지션 추가
                self.position_manager.add_buy_trade(quantity, ask_price)
                
                return {
                    'action': 'buy_order_placed',
                    'message': 'DRY RUN: Buy order placed',
                    'quantity': quantity,
                    'price': ask_price,
                    'buy_signal': buy_signal
                }
            
            # 실제 매수 주문
            success, order_info = self.order_manager.place_limit_buy_order(quantity, ask_price)
            
            if success:
                self.context.buy_order_id = order_info.order_id
                self.context.last_buy_signal_time = datetime.now(timezone.utc)
                
                # 부분 체결 대기
                is_filled, filled_quantity = self.order_manager.wait_for_partial_fill_timeout(order_info.order_id)
                
                if filled_quantity > 0:
                    # 체결된 수량만큼 포지션 추가
                    self.position_manager.add_buy_trade(filled_quantity, ask_price, order_id=order_info.order_id)
                    
                    self.context.current_state = TradingState.POSITION_HELD
                    
                    return {
                        'action': 'buy_order_filled',
                        'message': f'Buy order filled: {filled_quantity}/{quantity}',
                        'filled_quantity': filled_quantity,
                        'total_quantity': quantity,
                        'price': ask_price,
                        'is_partial': not is_filled,
                        'buy_signal': buy_signal
                    }
                else:
                    return self._create_error_result("Buy order not filled")
            
            else:
                return self._create_error_result(f"Buy order failed: {order_info.error_message}")
                
        except Exception as e:
            self.logger.error(f"Error executing buy order: {e}")
            return self._create_error_result(str(e))
    
    def _execute_profit_sell_order(self, target_price: float) -> Dict:
        """익절 매도 주문 실행"""
        try:
            quantity = self.position_manager.position.total_quantity
            
            if self.dry_run:
                # 모의 거래
                self.logger.info(f"DRY RUN: Sell {quantity} {self.symbol} at {target_price}")
                self.context.current_state = TradingState.WAITING_FOR_SELL
                self.context.sell_order_id = f"dry_sell_{int(time.time())}"
                
                return {
                    'action': 'profit_sell_order_placed',
                    'message': 'DRY RUN: Profit sell order placed',
                    'quantity': quantity,
                    'target_price': target_price
                }
            
            # 실제 익절 매도 주문
            success, order_info = self.order_manager.place_limit_sell_order(quantity, target_price)
            
            if success:
                self.context.sell_order_id = order_info.order_id
                self.context.current_state = TradingState.WAITING_FOR_SELL
                
                return {
                    'action': 'profit_sell_order_placed',
                    'message': 'Profit sell order placed',
                    'quantity': quantity,
                    'target_price': target_price,
                    'order_id': order_info.order_id
                }
            else:
                return self._create_error_result(f"Profit sell order failed: {order_info.error_message}")
                
        except Exception as e:
            self.logger.error(f"Error executing profit sell order: {e}")
            return self._create_error_result(str(e))
    
    def _execute_liquidation_sell_order(self, liquidation_signal: Dict) -> Dict:
        """손절/청산 매도 실행"""
        try:
            quantity = self.position_manager.position.total_quantity
            
            # 기존 익절 주문 취소
            if self.context.sell_order_id:
                self.order_manager.cancel_order(self.context.sell_order_id)
            
            if self.dry_run:
                # 모의 거래 - 현재가로 즉시 매도
                current_price = liquidation_signal.get('current_price', 0)
                self.logger.info(f"DRY RUN: Market sell {quantity} {self.symbol} at {current_price}")
                
                self.position_manager.add_sell_trade(quantity, current_price)
                self.context.current_state = TradingState.STRATEGY_COMPLETED
                self.context.cycle_start_time = datetime.now(timezone.utc)
                
                return {
                    'action': 'liquidation_completed',
                    'message': 'DRY RUN: Liquidation completed',
                    'quantity': quantity,
                    'price': current_price,
                    'liquidation_signal': liquidation_signal
                }
            
            # 실제 시장가 매도
            success, order_info = self.order_manager.place_market_sell_order(quantity)
            
            if success:
                # 시장가는 즉시 체결
                self.position_manager.add_sell_trade(
                    quantity=order_info.filled_quantity,
                    price=order_info.average_price,
                    trade_id=order_info.order_id
                )
                
                self.context.current_state = TradingState.STRATEGY_COMPLETED
                self.context.cycle_start_time = datetime.now(timezone.utc)
                
                return {
                    'action': 'liquidation_completed',
                    'message': 'Liquidation completed',
                    'quantity': order_info.filled_quantity,
                    'price': order_info.average_price,
                    'liquidation_signal': liquidation_signal
                }
            else:
                return self._create_error_result(f"Liquidation failed: {order_info.error_message}")
                
        except Exception as e:
            self.logger.error(f"Error executing liquidation: {e}")
            return self._create_error_result(str(e))
    
    def _complete_profitable_cycle(self, order_info) -> Dict:
        """익절 완료 처리"""
        try:
            # 매도 거래 기록
            self.position_manager.add_sell_trade(
                quantity=order_info.filled_quantity,
                price=order_info.average_price,
                trade_id=order_info.order_id
            )
            
            self.context.current_state = TradingState.STRATEGY_COMPLETED
            self.context.cycle_start_time = datetime.now(timezone.utc)
            
            return {
                'action': 'profit_cycle_completed',
                'message': 'Profitable cycle completed',
                'quantity': order_info.filled_quantity,
                'price': order_info.average_price,
                'profit': self.position_manager.position.realized_pnl
            }
            
        except Exception as e:
            self.logger.error(f"Error completing profitable cycle: {e}")
            return self._create_error_result(str(e))
    
    def _handle_sell_order_cancelled(self, market_data: Dict) -> Dict:
        """익절 주문 취소 처리"""
        # 청산 조건 재확인
        liquidation_signal = self._check_liquidation_conditions(market_data)
        
        if liquidation_signal['signal']:
            # 청산 신호 발생 - 시장가 매도
            return self._execute_liquidation_sell_order(liquidation_signal)
        else:
            # 익절 주문 재실행
            profit_target_price = self.position_manager.calculate_profit_target_price()
            return self._execute_profit_sell_order(profit_target_price)
    
    def _get_market_data(self) -> Optional[Dict]:
        """시장 데이터 조회"""
        try:
            # 현재가 정보
            ticker = self.api_client.get_ticker(self.symbol)
            current_price = float(ticker['last'])
            
            # 차트 데이터 (1시간봉)
            candles_data = self.api_client.get_candles(self.symbol, '1h', 100)
            
            # DataFrame으로 변환
            chart_data = pd.DataFrame(candles_data['candles'])
            chart_data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            chart_data = chart_data.astype({
                'open': float, 'high': float, 'low': float, 
                'close': float, 'volume': float
            })
            
            return {
                'current_price': current_price,
                'ticker': ticker,
                'chart_data': chart_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return None
    
    def _reset_for_new_cycle(self):
        """새 사이클을 위한 초기화"""
        self.context.current_state = TradingState.WAITING_FOR_BUY
        self.context.buy_order_id = None
        self.context.sell_order_id = None
        self.context.last_buy_signal_time = None
        self.context.last_sell_signal_time = None
        self.context.cycle_start_time = None
        self.context.error_message = None
        self.context.restart_count += 1
        
        self.logger.info(f"Starting new trading cycle #{self.context.restart_count}")
    
    def _create_error_result(self, error_message: str) -> Dict:
        """에러 결과 생성"""
        self.context.current_state = TradingState.ERROR
        self.context.error_message = error_message
        
        return {
            'action': 'error',
            'message': error_message,
            'error': True
        }
    
    def get_strategy_status(self) -> Dict:
        """전략 상태 정보"""
        return {
            'context': self.context.to_dict(),
            'position': self.position_manager.get_position_summary(),
            'orders': self.order_manager.get_order_summary(),
            'statistics': self.position_manager.get_trading_statistics(),
            'dry_run': self.dry_run,
            'timestamp': datetime.now().isoformat()
        }
    
    def emergency_stop(self):
        """긴급 정지"""
        self.logger.warning("Emergency stop activated")
        
        # 모든 활성 주문 취소
        self.order_manager.cancel_all_active_orders()
        
        # 포지션이 있다면 시장가로 청산
        if self.position_manager.has_position():
            quantity = self.position_manager.position.total_quantity
            success, order_info = self.order_manager.place_market_sell_order(quantity)
            
            if success:
                self.position_manager.add_sell_trade(
                    quantity=order_info.filled_quantity,
                    price=order_info.average_price,
                    trade_id=order_info.order_id
                )
        
        self.context.current_state = TradingState.ERROR
        self.context.error_message = "Emergency stop activated"