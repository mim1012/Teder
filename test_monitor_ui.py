"""
모니터링 UI 테스트 스크립트
실제 거래 전략 없이 모의 데이터로 UI 테스트
"""
import time
import random
from datetime import datetime, timedelta
from typing import Dict
import threading

from src.ui.monitor import TradingMonitor, MonitoringConfig
from src.strategy.trading_strategy import TradingState


class MockTradingStrategy:
    """모의 거래 전략 클래스"""
    
    def __init__(self):
        self.current_state = TradingState.WAITING_FOR_BUY
        self.mock_price = 1200.0
        self.mock_balance = 1000000.0  # 100만원
        self.mock_position = None
        self.cycle_count = 0
        
        # 모의 차트 데이터
        self.price_history = [1200.0 + random.uniform(-50, 50) for _ in range(100)]
        
    def get_mock_strategy_result(self) -> Dict:
        """모의 전략 실행 결과 반환"""
        
        # 가격 변동 시뮬레이션
        self._simulate_price_movement()
        
        # 상태별 처리
        if self.current_state == TradingState.WAITING_FOR_BUY:
            return self._simulate_waiting_for_buy()
        elif self.current_state == TradingState.POSITION_HELD:
            return self._simulate_position_held()
        elif self.current_state == TradingState.WAITING_FOR_SELL:
            return self._simulate_waiting_for_sell()
        elif self.current_state == TradingState.STRATEGY_COMPLETED:
            return self._simulate_strategy_completed()
        else:
            return self._simulate_error()
    
    def _simulate_price_movement(self):
        """가격 변동 시뮬레이션"""
        # 랜덤 가격 변동
        change = random.uniform(-20, 20)
        self.mock_price = max(1000, self.mock_price + change)
        
        # 가격 히스토리 업데이트
        self.price_history.append(self.mock_price)
        if len(self.price_history) > 100:
            self.price_history.pop(0)
    
    def _simulate_waiting_for_buy(self) -> Dict:
        """매수 대기 상태 시뮬레이션"""
        # 10% 확률로 매수 신호 발생
        if random.random() < 0.1:
            self.current_state = TradingState.POSITION_HELD
            self.mock_position = {
                'buy_price': self.mock_price,
                'quantity': self.mock_balance / self.mock_price,
                'timestamp': datetime.now()
            }
            
            return {
                'action': 'buy_order_filled',
                'message': f'Buy order filled at {self.mock_price:,.0f}',
                'current_state': self.current_state.value,
                'filled_quantity': self.mock_position['quantity'],
                'price': self.mock_price,
                'market_data': self._get_mock_market_data(),
                'position_summary': self._get_mock_position_summary(),
                'order_summary': {'active_orders': []},
                'buy_signal': {
                    'signal': True,
                    'rsi_signal': True,
                    'ema_signal': True,
                    'rsi_analysis': {'current_rsi': random.uniform(30, 40)},
                    'ema_analysis': {
                        'current_ema': self.mock_price - 10,
                        'slope_3_periods': 0.5,
                        'slope_5_periods': 0.3
                    }
                }
            }
        
        return {
            'action': 'waiting',
            'message': 'Waiting for buy signal',
            'current_state': self.current_state.value,
            'market_data': self._get_mock_market_data(),
            'position_summary': self._get_mock_position_summary(),
            'order_summary': {'active_orders': []},
            'buy_signal': {
                'signal': False,
                'rsi_signal': random.choice([True, False]),
                'ema_signal': random.choice([True, False]),
                'rsi_analysis': {'current_rsi': random.uniform(20, 80)},
                'ema_analysis': {
                    'current_ema': self.mock_price - random.uniform(5, 15),
                    'slope_3_periods': random.uniform(-0.1, 0.5),
                    'slope_5_periods': random.uniform(-0.1, 0.4)
                }
            }
        }
    
    def _simulate_position_held(self) -> Dict:
        """포지션 보유 상태 시뮬레이션"""
        # 익절 주문 생성
        self.current_state = TradingState.WAITING_FOR_SELL
        profit_target = self.mock_position['buy_price'] + 4
        
        return {
            'action': 'profit_sell_order_placed',
            'message': f'Profit sell order placed at {profit_target:,.0f}',
            'current_state': self.current_state.value,
            'quantity': self.mock_position['quantity'],
            'target_price': profit_target,
            'market_data': self._get_mock_market_data(),
            'position_summary': self._get_mock_position_summary(),
            'order_summary': {
                'active_orders': [{
                    'timestamp': datetime.now().isoformat(),
                    'type': 'LIMIT',
                    'side': 'SELL',
                    'quantity': self.mock_position['quantity'],
                    'price': profit_target,
                    'status': 'PENDING'
                }]
            }
        }
    
    def _simulate_waiting_for_sell(self) -> Dict:
        """매도 대기 상태 시뮬레이션"""
        # 30% 확률로 익절 체결, 10% 확률로 손절
        rand = random.random()
        
        if rand < 0.3:  # 익절 체결
            profit = (self.mock_price - self.mock_position['buy_price']) * self.mock_position['quantity']
            self.current_state = TradingState.STRATEGY_COMPLETED
            self.cycle_count += 1
            
            return {
                'action': 'profit_cycle_completed',
                'message': 'Profit cycle completed successfully',
                'current_state': self.current_state.value,
                'quantity': self.mock_position['quantity'],
                'price': self.mock_price,
                'profit': profit,
                'market_data': self._get_mock_market_data(),
                'position_summary': {'has_position': False},
                'order_summary': {'active_orders': []}
            }
            
        elif rand < 0.4:  # 손절 체결
            loss = (self.mock_price - self.mock_position['buy_price']) * self.mock_position['quantity']
            self.current_state = TradingState.STRATEGY_COMPLETED
            self.cycle_count += 1
            
            return {
                'action': 'liquidation_completed',
                'message': 'Position liquidated',
                'current_state': self.current_state.value,
                'quantity': self.mock_position['quantity'],
                'price': self.mock_price,
                'market_data': self._get_mock_market_data(),
                'position_summary': {'has_position': False},
                'order_summary': {'active_orders': []},
                'liquidation_signal': {
                    'signal': True,
                    'timeout_signal': random.choice([True, False]),
                    'rsi_signal': random.choice([True, False]),
                    'ema_signal': random.choice([True, False])
                }
            }
        
        return {
            'action': 'waiting',
            'message': 'Waiting for sell order execution',
            'current_state': self.current_state.value,
            'market_data': self._get_mock_market_data(),
            'position_summary': self._get_mock_position_summary(),
            'order_summary': {
                'active_orders': [{
                    'timestamp': datetime.now().isoformat(),
                    'type': 'LIMIT',
                    'side': 'SELL',
                    'quantity': self.mock_position['quantity'],
                    'price': self.mock_position['buy_price'] + 4,
                    'status': 'PENDING'
                }]
            }
        }
    
    def _simulate_strategy_completed(self) -> Dict:
        """전략 완료 상태 시뮬레이션"""
        # 5초 후 재시작
        if random.random() < 0.2:
            self.current_state = TradingState.WAITING_FOR_BUY
            self.mock_position = None
            
            return {
                'action': 'restarted',
                'message': f'Starting new trading cycle #{self.cycle_count + 1}',
                'current_state': self.current_state.value,
                'cycle_count': self.cycle_count + 1,
                'market_data': self._get_mock_market_data(),
                'position_summary': {'has_position': False},
                'order_summary': {'active_orders': []}
            }
        
        return {
            'action': 'waiting_restart',
            'message': 'Waiting for restart (cooldown period)',
            'current_state': self.current_state.value,
            'remaining_time': random.randint(1, 30),
            'market_data': self._get_mock_market_data(),
            'position_summary': {'has_position': False},
            'order_summary': {'active_orders': []}
        }
    
    def _simulate_error(self) -> Dict:
        """에러 상태 시뮬레이션"""
        return {
            'action': 'error',
            'message': 'Simulated error for testing',
            'current_state': self.current_state.value,
            'error': True,
            'market_data': self._get_mock_market_data(),
            'position_summary': {'has_position': False},
            'order_summary': {'active_orders': []}
        }
    
    def _get_mock_market_data(self) -> Dict:
        """모의 시장 데이터"""
        return {
            'current_price': self.mock_price,
            'ticker': {
                'last': str(self.mock_price),
                'volume': str(random.randint(1000000, 5000000))
            },
            'chart_data': None,  # 실제로는 DataFrame
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_mock_position_summary(self) -> Dict:
        """모의 포지션 요약"""
        if not self.mock_position:
            return {'has_position': False}
        
        quantity = self.mock_position['quantity']
        avg_price = self.mock_position['buy_price']
        current_price = self.mock_price
        unrealized_pnl = (current_price - avg_price) * quantity
        
        return {
            'has_position': True,
            'total_quantity': quantity,
            'average_buy_price': avg_price,
            'current_price': current_price,
            'unrealized_pnl': unrealized_pnl,
            'profit_target_price': avg_price + 4
        }


def test_monitor_ui():
    """모니터링 UI 테스트"""
    print("Starting Monitor UI Test...")
    print("Press Ctrl+C to stop")
    
    # 모의 전략 생성
    mock_strategy = MockTradingStrategy()
    
    # 모니터 설정
    config = MonitoringConfig(
        refresh_rate=1.0,  # 1초마다 업데이트
        debug_mode=True
    )
    
    # 모니터 생성
    monitor = TradingMonitor(config)
    
    # 데이터 콜백 설정
    monitor.set_data_callback(mock_strategy.get_mock_strategy_result)
    
    # 초기 시스템 로그 추가
    monitor.log_system_event("INFO", "Monitor UI test started")
    monitor.log_system_event("INFO", "Using mock trading strategy")
    monitor.add_alert("System initialized successfully", "success")
    
    # 백그라운드에서 추가 이벤트 시뮬레이션
    def simulate_background_events():
        """백그라운드 이벤트 시뮬레이션"""
        time.sleep(5)  # 5초 후 시작
        
        events = [
            ("INFO", "Market data updated"),
            ("INFO", "Balance checked"),
            ("WARNING", "High RSI detected"),
            ("INFO", "EMA condition met"),
            ("ERROR", "Connection timeout (recovered)"),
            ("INFO", "Order book updated"),
        ]
        
        for level, message in events:
            if not monitor.is_running:
                break
            monitor.log_system_event(level, message, "background")
            time.sleep(random.uniform(3, 8))
    
    # 백그라운드 스레드 시작
    bg_thread = threading.Thread(target=simulate_background_events, daemon=True)
    bg_thread.start()
    
    try:
        # 모니터링 시작
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        monitor.stop_monitoring()
        print("Monitor UI test completed")


def test_components_only():
    """컴포넌트만 개별 테스트"""
    from rich.console import Console
    from src.ui.components import UIComponents
    
    console = Console()
    components = UIComponents(console)
    
    # 테스트 데이터
    market_data = {
        'current_price': 1250.0,
        'price_change': 25.0,
        'change_percent': 2.04,
        'volume': 1500000,
        'timestamp': '2024-01-01 12:00:00'
    }
    
    balance_data = {
        'krw_balance': 500000,
        'usdt_balance': 0.8456,
        'current_price': 1250.0
    }
    
    position_data = {
        'has_position': True,
        'average_buy_price': 1200.0,
        'total_quantity': 0.8333,
        'current_price': 1250.0,
        'unrealized_pnl': 41665,
        'profit_target_price': 1204.0
    }
    
    # 개별 컴포넌트 테스트
    console.print(components.create_header_panel("Test Header", "Subtitle"))
    console.print(components.create_market_info_table(market_data))
    console.print(components.create_balance_table(balance_data))
    console.print(components.create_position_table(position_data))


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "components":
        test_components_only()
    else:
        test_monitor_ui()