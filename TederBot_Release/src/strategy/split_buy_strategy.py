"""
분할매수 전략 구현
1차: 30% 매수 (조건 만족시)
2차: 30% 매수 (-2원에서)
3차: 40% + 미체결량 매수 (-2원에서)
"""

import math
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import pandas as pd

from ..api.coinone_client import CoinoneClient
from ..indicators.rsi_short import RSIShort, RSIEMAShort
from ..indicators.price_ema import PriceEMA
from ..indicators.rsi import RSI  # RSI(14) for sell conditions
from ..utils.logger import Logger


class SplitBuyStrategy:
    """분할매수 전략"""
    
    def __init__(self, client: CoinoneClient, logger: Optional[Logger] = None):
        self.client = client
        self.logger = logger or Logger()
        
        # 지표 초기화
        self.rsi_short = RSIShort(period=9)
        self.rsi_ema_short = RSIEMAShort(rsi_period=9, ema_period=5)
        self.price_ema = PriceEMA(period=5)
        self.rsi_14 = RSI(period=14)  # 매도 조건용
        
        # 포지션 상태
        self.position = {
            'state': 'WAITING',  # WAITING, PHASE1, PHASE2, PHASE3, SELLING
            'avg_buy_price': 0.0,
            'total_quantity': 0.0,
            'total_invested': 0.0,
            'buy_times': [],
            'target_profit_price': 0.0,
            'stop_loss_price': 0.0,
            'phase1_order_id': None,
            'phase2_order_id': None,
            'phase3_order_id': None,
            'sell_order_id': None,
            'created_at': None
        }
        
        # 분할 비율
        self.split_ratios = {
            'phase1': 0.30,  # 30%
            'phase2': 0.30,  # 30%
            'phase3': 0.40   # 40%
        }
        
    def reset_position(self):
        """포지션 초기화"""
        self.position = {
            'state': 'WAITING',
            'avg_buy_price': 0.0,
            'total_quantity': 0.0,
            'total_invested': 0.0,
            'buy_times': [],
            'target_profit_price': 0.0,
            'stop_loss_price': 0.0,
            'phase1_order_id': None,
            'phase2_order_id': None,
            'phase3_order_id': None,
            'sell_order_id': None,
            'created_at': None
        }
        self.logger.info("Position reset completed")
    
    def get_market_data(self) -> pd.DataFrame:
        """1시간봉 시장 데이터 조회"""
        try:
            # 최근 100개 캔들 조회 (지표 계산을 위해)
            candles = self.client.get_candles('USDT-KRW', '1h', limit=100)
            
            if not candles or len(candles) < 20:
                self.logger.error("Insufficient market data")
                return pd.DataFrame()
            
            # DataFrame으로 변환
            df = pd.DataFrame(candles)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return pd.DataFrame()
    
    def check_phase1_conditions(self, data: pd.DataFrame) -> dict:
        """1차 매수 조건 체크"""
        try:
            # RSI(9) 조건 체크
            rsi_result = self.rsi_short.check_buy_condition(data)
            
            # RSI EMA 조건 체크
            rsi_ema_result = self.rsi_ema_short.check_buy_condition(data)
            
            # 가격 EMA 조건 체크
            price_ema_result = self.price_ema.check_buy_condition(data)
            
            # 모든 조건이 만족되는지 확인
            all_conditions_met = (
                rsi_result['condition_met'] and
                rsi_ema_result['condition_met'] and
                price_ema_result['condition_met']
            )
            
            return {
                'condition_met': all_conditions_met,
                'rsi_condition': rsi_result,
                'rsi_ema_condition': rsi_ema_result,
                'price_ema_condition': price_ema_result,
                'summary': self._get_condition_summary(rsi_result, rsi_ema_result, price_ema_result)
            }
            
        except Exception as e:
            self.logger.error(f"Error checking phase1 conditions: {e}")
            return {'condition_met': False, 'error': str(e)}
    
    def _get_condition_summary(self, rsi_result, rsi_ema_result, price_ema_result) -> str:
        """조건 요약 생성"""
        conditions = []
        
        if not rsi_result['condition_met']:
            conditions.append(f"RSI: {rsi_result['reason']}")
        
        if not rsi_ema_result['condition_met']:
            conditions.append(f"RSI_EMA: {rsi_ema_result['reason']}")
        
        if not price_ema_result['condition_met']:
            conditions.append(f"Price_EMA: {price_ema_result['reason']}")
        
        if not conditions:
            return "All conditions satisfied"
        
        return "; ".join(conditions)
    
    def execute_phase1_buy(self, current_price: float, available_krw: float) -> dict:
        """1차 매수 실행 (30%)"""
        try:
            # 매수 금액 계산 (30%)
            buy_amount = available_krw * self.split_ratios['phase1']
            
            # 수수료 고려 (0.1%)
            fee_rate = 0.001
            effective_amount = buy_amount * (1 - fee_rate)
            
            # 매수 수량 계산 (소수점 올림)
            buy_quantity = math.ceil(effective_amount / current_price)
            
            # 주문 실행 (매도1호가로 지정가 매수)
            orderbook = self.client.get_orderbook('USDT-KRW')
            if not orderbook or 'asks' not in orderbook or len(orderbook['asks']) == 0:
                return {'success': False, 'error': 'No orderbook data'}
            
            ask_price = float(orderbook['asks'][0]['price'])
            
            order_result = self.client.place_order(
                symbol='USDT-KRW',
                side='buy',
                type='limit',
                quantity=buy_quantity,
                price=ask_price
            )
            
            if order_result and 'order_id' in order_result:
                self.position['phase1_order_id'] = order_result['order_id']
                self.position['state'] = 'PHASE1'
                self.position['created_at'] = datetime.now()
                
                self.logger.info(f"Phase1 buy order placed: {buy_quantity} USDT at {ask_price} KRW")
                
                return {
                    'success': True,
                    'order_id': order_result['order_id'],
                    'quantity': buy_quantity,
                    'price': ask_price,
                    'amount': buy_amount
                }
            else:
                return {'success': False, 'error': 'Order placement failed'}
                
        except Exception as e:
            self.logger.error(f"Error in phase1 buy: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_and_handle_phase1_fill(self) -> bool:
        """1차 매수 체결 확인 및 처리"""
        try:
            if not self.position['phase1_order_id']:
                return False
            
            # 주문 상태 확인
            order_status = self.client.get_order_status(
                'USDT-KRW', 
                self.position['phase1_order_id']
            )
            
            if not order_status:
                return False
            
            if order_status['status'] == 'filled':
                # 완전 체결
                filled_quantity = float(order_status['filled_quantity'])
                avg_price = float(order_status['average_price'])
                
                self._update_position_after_fill(filled_quantity, avg_price)
                self.position['state'] = 'PHASE2'
                
                self.logger.info(f"Phase1 completely filled: {filled_quantity} USDT at avg {avg_price} KRW")
                return True
                
            elif order_status['status'] == 'partially_filled':
                # 부분 체결 - 10분 후 처리
                if self._is_order_expired(10):  # 10분
                    filled_quantity = float(order_status['filled_quantity'])
                    
                    if filled_quantity > 0:
                        avg_price = float(order_status['average_price'])
                        self._update_position_after_fill(filled_quantity, avg_price)
                        
                        # 미체결 부분 취소
                        self.client.cancel_order('USDT-KRW', self.position['phase1_order_id'])
                        
                        self.position['state'] = 'PHASE2'
                        self.logger.info(f"Phase1 partial fill handled: {filled_quantity} USDT")
                        return True
                    else:
                        # 체결량 0이면 주문 취소하고 대기 상태로
                        self.client.cancel_order('USDT-KRW', self.position['phase1_order_id'])
                        self.reset_position()
                        return False
                        
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking phase1 fill: {e}")
            return False
    
    def execute_phase2_buy(self, available_krw: float) -> dict:
        """2차 매수 실행 (평균가 -2원에 30%)"""
        try:
            # 2차 매수 가격 = 평균매수가 - 2원
            phase2_price = self.position['avg_buy_price'] - 2.0
            
            # 매수 금액 계산 (30%)
            buy_amount = available_krw * self.split_ratios['phase2']
            
            # 매수 수량 계산 (소수점 올림)
            fee_rate = 0.001
            effective_amount = buy_amount * (1 - fee_rate)
            buy_quantity = math.ceil(effective_amount / phase2_price)
            
            order_result = self.client.place_order(
                symbol='USDT-KRW',
                side='buy',
                type='limit',
                quantity=buy_quantity,
                price=phase2_price
            )
            
            if order_result and 'order_id' in order_result:
                self.position['phase2_order_id'] = order_result['order_id']
                self.position['state'] = 'PHASE2'
                
                self.logger.info(f"Phase2 buy order placed: {buy_quantity} USDT at {phase2_price} KRW")
                
                return {
                    'success': True,
                    'order_id': order_result['order_id'],
                    'quantity': buy_quantity,
                    'price': phase2_price,
                    'amount': buy_amount
                }
            else:
                return {'success': False, 'error': 'Phase2 order placement failed'}
                
        except Exception as e:
            self.logger.error(f"Error in phase2 buy: {e}")
            return {'success': False, 'error': str(e)}
    
    def execute_phase3_buy(self, available_krw: float) -> dict:
        """3차 매수 실행 (평균가 -2원에 40% + 미체결량)"""
        try:
            # 3차 매수 가격 = 현재 평균매수가 - 2원
            phase3_price = self.position['avg_buy_price'] - 2.0
            
            # 매수 금액 계산 (40% + 미체결 여유자금)
            buy_amount = available_krw  # 남은 자금 전량
            
            # 매수 수량 계산 (소수점 올림)
            fee_rate = 0.001
            effective_amount = buy_amount * (1 - fee_rate)
            buy_quantity = math.ceil(effective_amount / phase3_price)
            
            order_result = self.client.place_order(
                symbol='USDT-KRW',
                side='buy',
                type='limit',
                quantity=buy_quantity,
                price=phase3_price
            )
            
            if order_result and 'order_id' in order_result:
                self.position['phase3_order_id'] = order_result['order_id']
                self.position['state'] = 'PHASE3'
                
                self.logger.info(f"Phase3 buy order placed: {buy_quantity} USDT at {phase3_price} KRW")
                
                return {
                    'success': True,
                    'order_id': order_result['order_id'],
                    'quantity': buy_quantity,
                    'price': phase3_price,
                    'amount': buy_amount
                }
            else:
                return {'success': False, 'error': 'Phase3 order placement failed'}
                
        except Exception as e:
            self.logger.error(f"Error in phase3 buy: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_position_after_fill(self, filled_quantity: float, fill_price: float):
        """체결 후 포지션 업데이트"""
        # 기존 포지션과 합산하여 평균가 계산
        total_invested = self.position['total_invested'] + (filled_quantity * fill_price)
        total_quantity = self.position['total_quantity'] + filled_quantity
        
        if total_quantity > 0:
            avg_price = total_invested / total_quantity
            
            self.position['avg_buy_price'] = avg_price
            self.position['total_quantity'] = total_quantity
            self.position['total_invested'] = total_invested
            self.position['buy_times'].append({
                'timestamp': datetime.now(),
                'quantity': filled_quantity,
                'price': fill_price
            })
            
            # 목표가 설정
            self.position['target_profit_price'] = math.ceil(avg_price + 3.0)  # +3원
            self.position['stop_loss_price'] = math.ceil(avg_price - 2.0)  # -2원
            
            self.logger.info(f"Position updated - Avg: {avg_price:.2f}, Qty: {total_quantity}, Target: {self.position['target_profit_price']}")
    
    def check_sell_conditions(self, data: pd.DataFrame, current_price: float) -> dict:
        """매도 조건 체크"""
        try:
            sell_reasons = []
            sell_type = None
            
            # 1. 익절 조건 (평균가 +3원)
            if current_price >= self.position['target_profit_price']:
                sell_reasons.append("Take profit")
                sell_type = "limit"
            
            # 2. 손절 조건 (3차 후 평균가 -2원)
            elif (self.position['state'] == 'PHASE3' and 
                  current_price <= self.position['stop_loss_price']):
                sell_reasons.append("Stop loss after phase3")
                sell_type = "limit"
            
            # 3. 24시간 경과
            elif self._is_position_expired(24 * 60):  # 24시간 = 1440분
                sell_reasons.append("24 hours elapsed")
                sell_type = "market"
            
            # 4. RSI(14) > 70
            else:
                rsi_14 = self.rsi_14.calculate(data)
                if len(rsi_14) > 0 and rsi_14.iloc[-1] > 70:
                    sell_reasons.append("RSI(14) > 70")
                    sell_type = "market"
            
            return {
                'should_sell': len(sell_reasons) > 0,
                'sell_type': sell_type,
                'reasons': sell_reasons,
                'current_price': current_price,
                'target_price': self.position['target_profit_price'],
                'stop_price': self.position['stop_loss_price']
            }
            
        except Exception as e:
            self.logger.error(f"Error checking sell conditions: {e}")
            return {'should_sell': False, 'error': str(e)}
    
    def execute_sell_order(self, sell_type: str, current_price: float) -> dict:
        """매도 주문 실행"""
        try:
            if self.position['total_quantity'] <= 0:
                return {'success': False, 'error': 'No position to sell'}
            
            quantity = self.position['total_quantity']
            
            if sell_type == "limit":
                # 지정가 매도 (익절/손절)
                if current_price >= self.position['target_profit_price']:
                    # 익절 - 목표가로 매도
                    sell_price = self.position['target_profit_price']
                else:
                    # 손절 - 손절가로 매도
                    sell_price = self.position['stop_loss_price']
                
                order_result = self.client.place_order(
                    symbol='USDT-KRW',
                    side='sell',
                    type='limit',
                    quantity=quantity,
                    price=sell_price
                )
                
            else:  # market
                # 시장가 매도
                order_result = self.client.place_order(
                    symbol='USDT-KRW',
                    side='sell',
                    type='market',
                    quantity=quantity
                )
                sell_price = current_price
            
            if order_result and 'order_id' in order_result:
                self.position['sell_order_id'] = order_result['order_id']
                self.position['state'] = 'SELLING'
                
                self.logger.info(f"Sell order placed: {quantity} USDT at {sell_price} KRW ({sell_type})")
                
                return {
                    'success': True,
                    'order_id': order_result['order_id'],
                    'quantity': quantity,
                    'price': sell_price,
                    'type': sell_type
                }
            else:
                return {'success': False, 'error': 'Sell order placement failed'}
                
        except Exception as e:
            self.logger.error(f"Error in sell order: {e}")
            return {'success': False, 'error': str(e)}
    
    def _is_order_expired(self, minutes: int) -> bool:
        """주문이 지정된 시간(분)을 경과했는지 확인"""
        if not self.position['created_at']:
            return False
        
        elapsed = datetime.now() - self.position['created_at']
        return elapsed.total_seconds() >= (minutes * 60)
    
    def _is_position_expired(self, minutes: int) -> bool:
        """포지션이 지정된 시간(분)을 경과했는지 확인"""
        if not self.position['buy_times']:
            return False
        
        first_buy_time = self.position['buy_times'][0]['timestamp']
        elapsed = datetime.now() - first_buy_time
        return elapsed.total_seconds() >= (minutes * 60)
    
    def get_position_status(self) -> dict:
        """현재 포지션 상태 반환"""
        return {
            'state': self.position['state'],
            'avg_buy_price': self.position['avg_buy_price'],
            'total_quantity': self.position['total_quantity'],
            'total_invested': self.position['total_invested'],
            'target_profit_price': self.position['target_profit_price'],
            'stop_loss_price': self.position['stop_loss_price'],
            'buy_count': len(self.position['buy_times']),
            'created_at': self.position['created_at'],
            'phase1_order_id': self.position['phase1_order_id'],
            'phase2_order_id': self.position['phase2_order_id'],
            'phase3_order_id': self.position['phase3_order_id'],
            'sell_order_id': self.position['sell_order_id']
        }
    
    def run_strategy_cycle(self) -> dict:
        """전략 사이클 실행"""
        try:
            # 시장 데이터 조회
            market_data = self.get_market_data()
            if market_data.empty:
                return {'success': False, 'error': 'No market data'}
            
            current_price = market_data['close'].iloc[-1]
            
            # 계좌 잔고 조회
            balance = self.client.get_balance()
            if not balance:
                return {'success': False, 'error': 'Cannot get balance'}
            
            available_krw = float(balance.get('KRW', {}).get('available', 0))
            
            result = {'success': True, 'action': 'none', 'current_price': current_price}
            
            if self.position['state'] == 'WAITING':
                # 1차 매수 조건 체크
                conditions = self.check_phase1_conditions(market_data)
                result['conditions'] = conditions
                
                if conditions['condition_met']:
                    buy_result = self.execute_phase1_buy(current_price, available_krw)
                    result['action'] = 'phase1_buy'
                    result['buy_result'] = buy_result
                    
            elif self.position['state'] == 'PHASE1':
                # 1차 체결 확인
                if self.check_and_handle_phase1_fill():
                    # 2차 매수 실행
                    buy_result = self.execute_phase2_buy(available_krw)
                    result['action'] = 'phase2_buy'
                    result['buy_result'] = buy_result
                    
            elif self.position['state'] == 'PHASE2':
                # 2차 체결 확인 및 3차 매수 (실제 구현에서는 더 세밀한 체결 확인 필요)
                # 간단히 바로 3차 매수 실행
                buy_result = self.execute_phase3_buy(available_krw)
                result['action'] = 'phase3_buy'
                result['buy_result'] = buy_result
                
            elif self.position['state'] in ['PHASE3', 'SELLING']:
                # 매도 조건 체크
                sell_conditions = self.check_sell_conditions(market_data, current_price)
                result['sell_conditions'] = sell_conditions
                
                if sell_conditions['should_sell'] and self.position['state'] != 'SELLING':
                    sell_result = self.execute_sell_order(sell_conditions['sell_type'], current_price)
                    result['action'] = 'sell'
                    result['sell_result'] = sell_result
                    
                elif self.position['state'] == 'SELLING':
                    # 매도 주문 체결 확인 (간단 구현)
                    result['action'] = 'waiting_sell_fill'
            
            result['position'] = self.get_position_status()
            return result
            
        except Exception as e:
            self.logger.error(f"Error in strategy cycle: {e}")
            return {'success': False, 'error': str(e)}