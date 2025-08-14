"""
Rich 라이브러리 기반 실시간 모니터링 UI 메인 모듈
비동기 처리로 1초마다 화면을 갱신하는 실시간 모니터링 시스템
"""
import asyncio
import threading
import time
import signal
import sys
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from queue import Queue, Empty
from dataclasses import dataclass, field
from collections import deque

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from .dashboard import TradingDashboard, DashboardDataFormatter
from src.utils.logger import setup_logger


@dataclass
class MonitoringConfig:
    """모니터링 설정"""
    refresh_rate: float = 1.0  # 초 단위
    max_log_entries: int = 100
    max_trade_logs: int = 50
    console_width: Optional[int] = None
    console_height: Optional[int] = None
    debug_mode: bool = False


@dataclass
class LogEntry:
    """로그 엔트리"""
    timestamp: datetime
    level: str
    message: str
    source: str = "system"
    
    def to_string(self) -> str:
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{time_str}] {self.level}: {self.message}"


@dataclass 
class TradeLogEntry:
    """거래 로그 엔트리"""
    timestamp: datetime
    action: str
    message: str
    pnl: float = 0.0
    quantity: float = 0.0
    price: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'message': self.message,
            'pnl': self.pnl,
            'quantity': self.quantity,
            'price': self.price
        }


class MonitoringDataManager:
    """모니터링 데이터 관리 클래스"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.system_logs: deque = deque(maxlen=config.max_log_entries)
        self.trade_logs: deque = deque(maxlen=config.max_trade_logs)
        self.statistics: Dict = self._init_statistics()
        self.alerts: deque = deque(maxlen=10)
        self.start_time = datetime.now()
        
        # 데이터 큐
        self.data_queue = Queue()
        self.log_queue = Queue()
        
    def _init_statistics(self) -> Dict:
        """통계 초기화"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,  
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'avg_profit': 0.0,
            'max_profit': 0.0,
            'max_loss': 0.0,
            'max_drawdown': 0.0,
            'total_volume': 0.0,
            'profit_factor': 0.0
        }
    
    def add_system_log(self, level: str, message: str, source: str = "system") -> None:
        """시스템 로그 추가"""
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            source=source
        )
        self.system_logs.append(log_entry)
        
        # 로그 큐에도 추가 (실시간 처리용)
        try:
            self.log_queue.put_nowait({
                'type': 'system_log',
                'entry': log_entry
            })
        except:
            pass
    
    def add_trade_log(self, action: str, message: str, pnl: float = 0.0, 
                     quantity: float = 0.0, price: float = 0.0) -> None:
        """거래 로그 추가"""
        trade_entry = TradeLogEntry(
            timestamp=datetime.now(),
            action=action,
            message=message,
            pnl=pnl,
            quantity=quantity,
            price=price
        )
        self.trade_logs.append(trade_entry)
        
        # 통계 업데이트
        self._update_statistics(trade_entry)
        
        # 로그 큐에도 추가
        try:
            self.log_queue.put_nowait({
                'type': 'trade_log',
                'entry': trade_entry
            })
        except:
            pass
    
    def _update_statistics(self, trade_entry: TradeLogEntry) -> None:
        """통계 업데이트"""
        if trade_entry.action in ['profit_cycle_completed', 'liquidation_completed']:
            self.statistics['total_trades'] += 1
            self.statistics['total_pnl'] += trade_entry.pnl
            self.statistics['total_volume'] += trade_entry.quantity * trade_entry.price
            
            if trade_entry.pnl > 0:
                self.statistics['winning_trades'] += 1
                self.statistics['max_profit'] = max(self.statistics['max_profit'], trade_entry.pnl)
            else:
                self.statistics['losing_trades'] += 1
                self.statistics['max_loss'] = min(self.statistics['max_loss'], trade_entry.pnl)
            
            # 승률 계산
            if self.statistics['total_trades'] > 0:
                self.statistics['win_rate'] = (
                    self.statistics['winning_trades'] / self.statistics['total_trades']
                ) * 100
            
            # 평균 수익 계산
            if self.statistics['total_trades'] > 0:
                self.statistics['avg_profit'] = (
                    self.statistics['total_pnl'] / self.statistics['total_trades']
                )
    
    def add_alert(self, message: str, alert_type: str = "info") -> None:
        """알림 추가"""
        alert = {
            'timestamp': datetime.now(),
            'message': message,
            'type': alert_type
        }
        self.alerts.append(alert)
    
    def get_system_logs(self) -> List[str]:
        """시스템 로그 문자열 리스트 반환"""
        return [log.to_string() for log in self.system_logs]
    
    def get_trade_logs(self) -> List[Dict]:
        """거래 로그 딕셔너리 리스트 반환"""
        return [log.to_dict() for log in self.trade_logs]
    
    def get_statistics(self) -> Dict:
        """통계 반환"""
        return self.statistics.copy()
    
    def get_alerts(self) -> List[Dict]:
        """알림 리스트 반환"""
        return list(self.alerts)


class TradingMonitor:
    """실시간 거래 모니터링 클래스"""
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.console = Console(
            width=self.config.console_width,
            height=self.config.console_height
        )
        
        # 컴포넌트 초기화
        self.dashboard = TradingDashboard(self.console)
        self.data_manager = MonitoringDataManager(self.config)
        self.formatter = DashboardDataFormatter()
        
        # 상태 관리
        self.is_running = False
        self.data_callback: Optional[Callable] = None
        self.live_display: Optional[Live] = None
        
        # 로거 설정
        self.logger = setup_logger("trading_monitor", debug=self.config.debug_mode)
        
        # 신호 처리
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Trading monitor initialized")
    
    def set_data_callback(self, callback: Callable[[], Dict]) -> None:
        """데이터 콜백 함수 설정"""
        self.data_callback = callback
        self.logger.info("Data callback function set")
    
    def start_monitoring(self) -> None:
        """모니터링 시작"""
        if self.is_running:
            self.logger.warning("Monitor is already running")
            return
        
        self.is_running = True
        self.data_manager.add_system_log("INFO", "Starting trading monitor")
        
        try:
            # 시작 화면 표시
            self.dashboard.show_startup_screen()
            time.sleep(2)
            
            # Live 디스플레이 시작
            with Live(
                self.dashboard.render(),
                console=self.console,
                refresh_per_second=1/self.config.refresh_rate,
                screen=True
            ) as live:
                self.live_display = live
                self._monitoring_loop()
                
        except KeyboardInterrupt:
            self.logger.info("Monitor stopped by user")
        except Exception as e:
            self.logger.error(f"Monitor error: {e}")
            self.data_manager.add_system_log("ERROR", f"Monitor error: {e}")
        finally:
            self.stop_monitoring()
    
    def start_monitoring_async(self) -> None:
        """비동기 모니터링 시작"""
        if self.is_running:
            self.logger.warning("Monitor is already running")
            return
        
        # 별도 스레드에서 모니터링 실행
        monitor_thread = threading.Thread(target=self.start_monitoring, daemon=True)
        monitor_thread.start()
        
        self.logger.info("Async monitoring started")
    
    def stop_monitoring(self) -> None:
        """모니터링 중지"""
        self.is_running = False
        self.data_manager.add_system_log("INFO", "Stopping trading monitor")
        
        if self.live_display:
            self.live_display = None
        
        self.logger.info("Trading monitor stopped")
    
    def _monitoring_loop(self) -> None:
        """메인 모니터링 루프"""
        last_update = 0
        update_interval = self.config.refresh_rate
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # 업데이트 주기 확인
                if current_time - last_update >= update_interval:
                    self._update_display()
                    last_update = current_time
                
                # 로그 큐 처리
                self._process_log_queue()
                
                # CPU 사용률 절약
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                self.data_manager.add_system_log("ERROR", f"Loop error: {e}")
                time.sleep(1)  # 에러 시 잠시 대기
    
    def _update_display(self) -> None:
        """화면 업데이트"""
        try:
            # 데이터 수집
            dashboard_data = self._collect_dashboard_data()
            
            # 대시보드 업데이트
            self.dashboard.update_dashboard(dashboard_data)
            
            # Live 디스플레이 갱신
            if self.live_display:
                self.live_display.update(self.dashboard.render())
            
        except Exception as e:
            self.logger.error(f"Display update error: {e}")
            self.data_manager.add_system_log("ERROR", f"Display update error: {e}")
    
    def _collect_dashboard_data(self) -> Dict:
        """대시보드 데이터 수집"""
        try:
            # 콜백 함수에서 전략 데이터 수집
            strategy_data = {}
            if self.data_callback:
                strategy_data = self.data_callback()
            
            # 대시보드 형식으로 변환
            dashboard_data = self.formatter.format_trading_strategy_data(strategy_data)
            
            # 모니터링 데이터 추가
            dashboard_data.update({
                'trading_logs': self.data_manager.get_trade_logs(),
                'system_logs': self.data_manager.get_system_logs(),
                'statistics': self.data_manager.get_statistics(),
                'alerts': self.data_manager.get_alerts(),
                'system_status': {
                    **dashboard_data.get('system_status', {}),
                    'start_time': self.data_manager.start_time.isoformat(),
                    'uptime': self._calculate_uptime()
                }
            })
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Data collection error: {e}")
            return {
                'error': f"Data collection failed: {e}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _process_log_queue(self) -> None:
        """로그 큐 처리"""
        try:
            while True:
                try:
                    log_item = self.data_manager.log_queue.get_nowait()
                    
                    if log_item['type'] == 'system_log':
                        # 시스템 로그는 이미 추가됨
                        pass
                    elif log_item['type'] == 'trade_log':
                        # 거래 로그 알림 생성
                        trade_entry = log_item['entry']
                        if trade_entry.action in ['profit_cycle_completed', 'liquidation_completed']:
                            alert_type = 'success' if trade_entry.pnl > 0 else 'warning'
                            self.data_manager.add_alert(
                                f"Trade completed: {trade_entry.pnl:+,.0f} KRW",
                                alert_type
                            )
                    
                except Empty:
                    break
                    
        except Exception as e:
            self.logger.error(f"Log queue processing error: {e}")
    
    def _calculate_uptime(self) -> str:
        """업타임 계산"""
        uptime_delta = datetime.now() - self.data_manager.start_time
        total_seconds = int(uptime_delta.total_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _signal_handler(self, signum, frame) -> None:
        """시그널 핸들러"""
        self.logger.info(f"Received signal {signum}, stopping monitor")
        self.stop_monitoring()
        sys.exit(0)
    
    # 외부 인터페이스 메서드들
    def log_system_event(self, level: str, message: str, source: str = "system") -> None:
        """시스템 이벤트 로깅"""
        self.data_manager.add_system_log(level, message, source)
    
    def log_trade_event(self, action: str, message: str, pnl: float = 0.0,
                       quantity: float = 0.0, price: float = 0.0) -> None:
        """거래 이벤트 로깅"""
        self.data_manager.add_trade_log(action, message, pnl, quantity, price)
    
    def add_alert(self, message: str, alert_type: str = "info") -> None:
        """알림 추가"""
        self.data_manager.add_alert(message, alert_type)
    
    def get_monitor_status(self) -> Dict:
        """모니터 상태 반환"""
        return {
            'is_running': self.is_running,
            'start_time': self.data_manager.start_time.isoformat(),
            'uptime': self._calculate_uptime(),
            'total_logs': len(self.data_manager.system_logs),
            'total_trades': self.data_manager.statistics['total_trades'],
            'config': {
                'refresh_rate': self.config.refresh_rate,
                'max_log_entries': self.config.max_log_entries,
                'debug_mode': self.config.debug_mode
            }
        }
    
    def update_strategy_result(self, strategy_result: Dict) -> None:
        """전략 실행 결과 업데이트"""
        try:
            # 액션별 로깅
            action = strategy_result.get('action', '')
            message = strategy_result.get('message', '')
            
            if action == 'buy_order_filled':
                quantity = strategy_result.get('filled_quantity', 0)
                price = strategy_result.get('price', 0)
                self.log_trade_event('buy_order_filled', message, 0, quantity, price)
                
            elif action == 'profit_cycle_completed':
                pnl = strategy_result.get('profit', 0)
                quantity = strategy_result.get('quantity', 0)
                price = strategy_result.get('price', 0)
                self.log_trade_event('profit_cycle_completed', message, pnl, quantity, price)
                
            elif action == 'liquidation_completed':
                quantity = strategy_result.get('quantity', 0)
                price = strategy_result.get('price', 0)
                # 손실 계산 (대략적)
                pnl = -abs(quantity * price * 0.01)  # 임시 계산
                self.log_trade_event('liquidation_completed', message, pnl, quantity, price)
                
            elif action == 'error':
                self.log_system_event('ERROR', message, 'strategy')
                self.add_alert(f"Strategy Error: {message}", 'error')
            
            elif action in ['waiting', 'waiting_restart']:
                self.log_system_event('INFO', message, 'strategy')
            
        except Exception as e:
            self.logger.error(f"Strategy result update error: {e}")


# 편의 함수들
def create_monitor(refresh_rate: float = 1.0, debug: bool = False) -> TradingMonitor:
    """모니터 인스턴스 생성"""
    config = MonitoringConfig(
        refresh_rate=refresh_rate,
        debug_mode=debug
    )
    return TradingMonitor(config)


def run_monitor_with_strategy(strategy_callback: Callable, refresh_rate: float = 1.0) -> None:
    """전략과 함께 모니터 실행"""
    monitor = create_monitor(refresh_rate)
    monitor.set_data_callback(strategy_callback)
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Monitor error: {e}")
    finally:
        monitor.stop_monitoring()