"""
거래 전략과 모니터링 UI를 통합한 메인 실행 스크립트
실제 거래 전략과 실시간 모니터링을 함께 실행
"""
import time
import threading
import signal
import sys
from typing import Dict, Optional
from datetime import datetime

from config.settings import load_config
from src.api.coinone_client import CoinoneClient
from src.strategy.trading_strategy import TradingStrategy
from src.ui.monitor import TradingMonitor, MonitoringConfig
from src.utils.logger import setup_logger


class TradingSystemManager:
    """거래 시스템 통합 관리 클래스"""
    
    def __init__(self, config_path: str = None):
        # 설정 로드
        self.config = load_config(config_path)
        
        # 로거 설정
        self.logger = setup_logger("trading_system", debug=self.config.get('debug', False))
        
        # API 클라이언트 초기화
        self.api_client = None
        self.trading_strategy = None
        self.monitor = None
        
        # 시스템 상태
        self.is_running = False
        self.startup_time = datetime.now()
        self.last_strategy_result = {}
        
        # 스레드 안전성을 위한 락
        self._result_lock = threading.Lock()
        
        # 종료 시그널 핸들러
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Trading system manager initialized")
    
    def initialize_components(self) -> bool:
        """시스템 컴포넌트 초기화"""
        try:
            self.logger.info("Initializing system components...")
            
            # API 클라이언트 초기화
            self.api_client = CoinoneClient()
            
            # 연결 테스트
            if not self._test_api_connection():
                return False
            
            # 거래 전략 초기화
            self.trading_strategy = TradingStrategy(self.api_client)
            
            # 모니터링 UI 초기화
            monitor_config = MonitoringConfig(
                refresh_rate=self.config.get('monitor', {}).get('refresh_rate', 1.0),
                debug_mode=self.config.get('debug', False)
            )
            
            self.monitor = TradingMonitor(monitor_config)
            self.monitor.set_data_callback(self._get_strategy_data)
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            return False
    
    def _test_api_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            self.logger.info("Testing API connection...")
            
            # 서버 시간 조회 테스트
            server_time = self.api_client.get_server_time()
            if server_time:
                self.logger.info(f"API connection successful. Server time: {server_time}")
                return True
            else:
                self.logger.error("API connection failed")
                return False
                
        except Exception as e:
            self.logger.error(f"API connection test failed: {e}")
            return False
    
    def start_system(self) -> None:
        """시스템 시작"""
        if self.is_running:
            self.logger.warning("System is already running")
            return
        
        try:
            self.logger.info("Starting trading system...")
            
            # 컴포넌트 초기화
            if not self.initialize_components():
                self.logger.error("Failed to initialize components")
                return
            
            self.is_running = True
            
            # 모니터링 시작 (별도 스레드)
            self.logger.info("Starting monitoring UI...")
            monitor_thread = threading.Thread(target=self._run_monitor, daemon=True)
            monitor_thread.start()
            
            # 초기 시스템 로그
            self.monitor.log_system_event("INFO", "Trading system started")
            self.monitor.log_system_event("INFO", f"Mode: {'DRY RUN' if self.config.get('dry_run', True) else 'LIVE TRADING'}")
            self.monitor.add_alert("System started successfully", "success")
            
            # 거래 전략 실행 (메인 스레드)
            self.logger.info("Starting trading strategy...")
            self._run_trading_strategy()
            
        except Exception as e:
            self.logger.error(f"System startup failed: {e}")
            self.stop_system()
    
    def _run_monitor(self) -> None:
        """모니터링 UI 실행"""
        try:
            self.monitor.start_monitoring()
        except Exception as e:
            self.logger.error(f"Monitor error: {e}")
    
    def _run_trading_strategy(self) -> None:
        """거래 전략 실행 루프"""
        strategy_interval = self.config.get('strategy', {}).get('execution_interval', 60)  # 60초 기본값
        
        self.logger.info(f"Starting strategy execution loop (interval: {strategy_interval}s)")
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # 전략 실행
                result = self.trading_strategy.execute_cycle()
                
                # 결과 저장 (스레드 안전)
                with self._result_lock:
                    self.last_strategy_result = result
                
                # 모니터에 결과 전달
                if self.monitor:
                    self.monitor.update_strategy_result(result)
                
                # 실행 시간 로깅
                execution_time = time.time() - start_time
                self.logger.debug(f"Strategy cycle completed in {execution_time:.2f}s")
                
                # 다음 실행까지 대기
                time.sleep(max(0, strategy_interval - execution_time))
                
            except Exception as e:
                self.logger.error(f"Strategy execution error: {e}")
                if self.monitor:
                    self.monitor.log_system_event("ERROR", f"Strategy error: {e}")
                
                # 에러 시 잠시 대기
                time.sleep(10)
    
    def _get_strategy_data(self) -> Dict:
        """모니터를 위한 전략 데이터 반환"""
        with self._result_lock:
            return self.last_strategy_result.copy()
    
    def stop_system(self) -> None:
        """시스템 종료"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping trading system...")
        self.is_running = False
        
        try:
            # 거래 전략 긴급 정지
            if self.trading_strategy:
                self.trading_strategy.emergency_stop()
                self.logger.info("Trading strategy stopped")
            
            # 모니터 종료
            if self.monitor:
                self.monitor.log_system_event("INFO", "System shutdown initiated")
                self.monitor.stop_monitoring()
                self.logger.info("Monitor stopped")
            
            self.logger.info("Trading system stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error during system shutdown: {e}")
    
    def _signal_handler(self, signum, frame) -> None:
        """시그널 핸들러"""
        self.logger.info(f"Received signal {signum}, stopping system...")
        self.stop_system()
        sys.exit(0)
    
    def get_system_status(self) -> Dict:
        """시스템 상태 반환"""
        return {
            'is_running': self.is_running,
            'startup_time': self.startup_time.isoformat(),
            'uptime': str(datetime.now() - self.startup_time),
            'components': {
                'api_client': self.api_client is not None,
                'trading_strategy': self.trading_strategy is not None,
                'monitor': self.monitor is not None
            },
            'strategy_state': self.trading_strategy.context.current_state.value if self.trading_strategy else None,
            'last_strategy_action': self.last_strategy_result.get('action', 'none'),
            'config': {
                'dry_run': self.config.get('dry_run', True),
                'symbol': self.config.get('trading', {}).get('symbol', 'USDT'),
                'currency': self.config.get('trading', {}).get('currency', 'KRW')
            }
        }


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("Coinone USDT/KRW Auto Trading System")
    print("=" * 60)
    print()
    
    try:
        # 시스템 매니저 생성
        system_manager = TradingSystemManager()
        
        # 시작 전 확인
        dry_run = system_manager.config.get('dry_run', True)
        if not dry_run:
            print("WARNING: LIVE TRADING MODE ENABLED!")
            print("   This will execute real trades with real money.")
            response = input("   Are you sure you want to continue? (yes/no): ").lower().strip()
            
            if response != 'yes':
                print("Trading cancelled by user.")
                return
        else:
            print("DRY RUN MODE: No real trades will be executed.")
        
        print()
        print("Starting system... Press Ctrl+C to stop")
        print("-" * 60)
        
        # 시스템 시작
        system_manager.start_system()
        
    except KeyboardInterrupt:
        print("\n\nSystem stopped by user")
    except Exception as e:
        print(f"\n\nSystem error: {e}")
    finally:
        print("\nShutdown complete.")


def run_monitor_only():
    """모니터링 UI만 실행 (테스트용)"""
    from test_monitor_ui import test_monitor_ui
    test_monitor_ui()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor-only":
        run_monitor_only()
    else:
        main()