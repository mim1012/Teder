"""
매매 전략 테스트 스크립트
State Machine 기반 자동매매 전략 테스트
"""
import os
import sys
import time
import logging
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.coinone_client import CoinoneClient
from src.strategy import TradingStrategy, TradingState
from config.settings import SYSTEM_CONFIG, MONITORING_CONFIG


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=getattr(logging, MONITORING_CONFIG['log_level']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('strategy_test.log')
        ]
    )


def print_strategy_status(strategy: TradingStrategy):
    """전략 상태 출력"""
    status = strategy.get_strategy_status()
    
    print("\n" + "="*60)
    print(f"TRADING STRATEGY STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 현재 상태
    context = status['context']
    print(f"Current State: {context['current_state']}")
    print(f"Restart Count: {context['restart_count']}")
    
    if context['error_message']:
        print(f"Error: {context['error_message']}")
    
    # 포지션 정보
    position = status['position']
    print(f"\nPosition:")
    print(f"  Has Position: {position['has_position']}")
    if position['has_position']:
        print(f"  Quantity: {position['quantity']:.8f}")
        print(f"  Average Price: {position['average_price']:.2f}")
        print(f"  Duration: {position.get('position_duration', 0):.0f}s")
        if 'unrealized_pnl' in position:
            print(f"  Unrealized PnL: {position['unrealized_pnl']:.2f}")
            print(f"  Return %: {position.get('return_percentage', 0):.2f}%")
    
    # 주문 정보
    orders = status['orders']
    print(f"\nOrders:")
    print(f"  Active Orders: {orders['active_orders_count']}")
    print(f"  Has Active Sell Orders: {orders['has_active_sell_orders']}")
    
    # 거래 통계
    stats = status['statistics']
    print(f"\nTrading Statistics:")
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  Win Rate: {stats['win_rate']:.1f}%")
    print(f"  Total Realized PnL: {stats['total_realized_pnl']:.2f}")
    
    print(f"\nDry Run: {status['dry_run']}")
    print("="*60)


def test_single_cycle():
    """단일 사이클 테스트"""
    print("Starting single cycle test...")
    
    try:
        # API 클라이언트 초기화
        client = CoinoneClient()
        
        # 전략 초기화
        strategy = TradingStrategy(client)
        
        # 상태 출력
        print_strategy_status(strategy)
        
        # 사이클 실행
        result = strategy.execute_cycle()
        
        print(f"\nCycle Result:")
        print(f"Action: {result.get('action', 'unknown')}")
        print(f"Message: {result.get('message', 'no message')}")
        
        if 'buy_signal' in result:
            buy_signal = result['buy_signal']
            print(f"Buy Signal: {buy_signal.get('signal', False)}")
            if 'rsi_analysis' in buy_signal:
                rsi = buy_signal['rsi_analysis']
                print(f"  RSI: {rsi.get('current_value', 0):.2f}")
            if 'ema_analysis' in buy_signal:
                ema = buy_signal['ema_analysis']
                print(f"  EMA: {ema.get('current_value', 0):.2f}")
        
        # 업데이트된 상태 출력
        print_strategy_status(strategy)
        
    except Exception as e:
        print(f"Error in single cycle test: {e}")
        import traceback
        traceback.print_exc()


def test_multiple_cycles(cycles: int = 5, interval: int = 10):
    """다중 사이클 테스트"""
    print(f"Starting {cycles} cycles test (interval: {interval}s)...")
    
    try:
        # API 클라이언트 초기화
        client = CoinoneClient()
        
        # 전략 초기화
        strategy = TradingStrategy(client)
        
        for i in range(cycles):
            print(f"\n[Cycle {i+1}/{cycles}]")
            
            # 사이클 실행
            result = strategy.execute_cycle()
            
            print(f"Action: {result.get('action', 'unknown')}")
            print(f"Message: {result.get('message', 'no message')}")
            print(f"State: {result.get('current_state', 'unknown')}")
            
            # 매수/매도 신호 정보
            if 'buy_signal' in result:
                buy_signal = result['buy_signal']
                print(f"Buy Signal: {buy_signal.get('signal', False)}")
            
            if 'liquidation_signal' in result:
                liquidation_signal = result['liquidation_signal']
                print(f"Liquidation Signal: {liquidation_signal.get('signal', False)}")
            
            # 다음 사이클까지 대기
            if i < cycles - 1:
                print(f"Waiting {interval}s for next cycle...")
                time.sleep(interval)
        
        # 최종 상태 출력
        print_strategy_status(strategy)
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error in multiple cycles test: {e}")
        import traceback
        traceback.print_exc()


def test_state_transitions():
    """상태 전이 테스트"""
    print("Testing state transitions...")
    
    try:
        # API 클라이언트 초기화
        client = CoinoneClient()
        
        # 전략 초기화
        strategy = TradingStrategy(client)
        
        # 초기 상태 확인
        assert strategy.context.current_state == TradingState.WAITING_FOR_BUY
        print("Initial state: WAITING_FOR_BUY")
        
        # 포지션 매니저 테스트
        position_manager = strategy.position_manager
        
        # 가상 매수 거래 추가
        success = position_manager.add_buy_trade(100.0, 1300.0, 1.95)
        assert success
        assert position_manager.has_position()
        print("Buy trade added successfully")
        
        # 평균 매수가 확인
        assert position_manager.position.average_price == (100.0 * 1300.0 + 1.95) / 100.0
        print("Average price calculated correctly")
        
        # 익절 목표가 계산
        target_price = position_manager.calculate_profit_target_price()
        expected_target = position_manager.position.average_price + 4.0
        assert abs(target_price - expected_target) < 0.01
        print("Profit target price calculated correctly")
        
        # 가상 매도 거래 추가
        success = position_manager.add_sell_trade(100.0, 1305.0, 1.96)
        assert success
        assert not position_manager.has_position()
        print("Sell trade added successfully")
        
        # 실현 손익 확인
        realized_pnl = position_manager.position.realized_pnl
        expected_pnl = (100.0 * 1305.0 - 1.96) - (100.0 * 1300.0 + 1.95)
        assert abs(realized_pnl - expected_pnl) < 0.01
        print("Realized PnL calculated correctly")
        
        print("All state transition tests passed!")
        
    except AssertionError as e:
        print(f"Test assertion failed: {e}")
    except Exception as e:
        print(f"Error in state transition test: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 함수"""
    setup_logging()
    
    print("Trading Strategy Test Suite")
    print("=" * 40)
    
    while True:
        print("\nSelect test:")
        print("1. Single cycle test")
        print("2. Multiple cycles test")
        print("3. State transitions test")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            test_single_cycle()
        elif choice == '2':
            cycles = int(input("Number of cycles (default 5): ") or "5")
            interval = int(input("Interval in seconds (default 10): ") or "10")
            test_multiple_cycles(cycles, interval)
        elif choice == '3':
            test_state_transitions()
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()