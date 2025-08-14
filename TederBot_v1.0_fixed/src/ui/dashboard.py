"""
Rich 라이브러리 기반 대시보드 레이아웃 모듈
전체 화면 구성과 레이아웃을 관리
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich.text import Text
from rich.align import Align

from .components import UIComponents


class TradingDashboard:
    """거래 대시보드 레이아웃 클래스"""
    
    def __init__(self, console: Console):
        self.console = console
        self.components = UIComponents(console)
        self.layout = self._create_layout()
        
        # 데이터 캐시
        self._last_update = None
        self._cached_data = {}
    
    def _create_layout(self) -> Layout:
        """메인 레이아웃 생성"""
        layout = Layout()
        
        # 전체 화면을 상하로 분할
        layout.split_column(
            Layout(name="header", size=3),      # 헤더 (3줄)
            Layout(name="body"),                # 메인 바디
            Layout(name="footer", size=3)       # 푸터 (3줄)
        )
        
        # 메인 바디를 좌우로 분할
        layout["body"].split_row(
            Layout(name="left_panel", ratio=2),   # 좌측 패널 (2/3)
            Layout(name="right_panel", ratio=1)   # 우측 패널 (1/3)
        )
        
        # 좌측 패널을 상하로 분할
        layout["left_panel"].split_column(
            Layout(name="market_info", size=12),     # 시장 정보 (12줄)
            Layout(name="trading_logs")              # 거래 로그
        )
        
        # 우측 패널을 상하로 분할
        layout["right_panel"].split_column(
            Layout(name="signals", size=10),         # 신호 정보 (10줄)
            Layout(name="orders", size=12),          # 주문 정보 (12줄)
            Layout(name="system_logs")               # 시스템 로그
        )
        
        return layout
    
    def update_dashboard(self, data: Dict) -> None:
        """대시보드 전체 업데이트"""
        try:
            self._last_update = datetime.now()
            self._cached_data = data
            
            # 각 섹션 업데이트
            self._update_header(data.get('system_status', {}))
            self._update_market_info(data.get('market_data', {}), data.get('balance', {}), data.get('position', {}))
            self._update_signals(data.get('signals', {}))
            self._update_orders(data.get('orders', []))
            self._update_trading_logs(data.get('trading_logs', []))
            self._update_system_logs(data.get('system_logs', []))
            self._update_footer(data.get('statistics', {}), data.get('alerts', []))
            
        except Exception as e:
            self._show_error(f"Dashboard update error: {e}")
    
    def _update_header(self, status_data: Dict) -> None:
        """헤더 섹션 업데이트"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subtitle = f"USDT/KRW Auto Trading System | {current_time}"
            
            header_panel = self.components.create_header_panel(
                "Coinone Trading Bot", 
                subtitle
            )
            
            self.layout["header"].update(header_panel)
            
        except Exception as e:
            self.layout["header"].update(Panel(f"Header Error: {e}", style="red"))
    
    def _update_market_info(self, market_data: Dict, balance_data: Dict, position_data: Dict) -> None:
        """시장 정보 섹션 업데이트"""
        try:
            # 시장 정보와 잔고를 좌우로 배치
            market_table = self.components.create_market_info_table(market_data)
            balance_table = self.components.create_balance_table(balance_data)
            position_table = self.components.create_position_table(position_data)
            
            # 상단: 시장 정보와 잔고
            market_balance_panels = Columns([
                Panel(market_table, title="Market Info", box="ROUNDED"),
                Panel(balance_table, title="Balance", box="ROUNDED")
            ], equal=True)
            
            # 하단: 포지션 정보
            position_panel = Panel(position_table, title="Position", box="ROUNDED")
            
            # 전체 레이아웃
            market_layout = Layout()
            market_layout.split_column(
                Layout(market_balance_panels, size=7),
                Layout(position_panel, size=5)
            )
            
            self.layout["market_info"].update(market_layout)
            
        except Exception as e:
            self.layout["market_info"].update(Panel(f"Market Info Error: {e}", style="red"))
    
    def _update_signals(self, signals_data: Dict) -> None:
        """신호 정보 섹션 업데이트"""
        try:
            signals_table = self.components.create_signals_table(signals_data)
            signals_panel = Panel(signals_table, title="Trading Signals", box="ROUNDED")
            
            self.layout["signals"].update(signals_panel)
            
        except Exception as e:
            self.layout["signals"].update(Panel(f"Signals Error: {e}", style="red"))
    
    def _update_orders(self, orders_data: List[Dict]) -> None:
        """주문 정보 섹션 업데이트"""
        try:
            orders_table = self.components.create_orders_table(orders_data)
            orders_panel = Panel(orders_table, title="Active Orders", box="ROUNDED")
            
            self.layout["orders"].update(orders_panel)
            
        except Exception as e:
            self.layout["orders"].update(Panel(f"Orders Error: {e}", style="red"))
    
    def _update_trading_logs(self, log_data: List[Dict]) -> None:
        """거래 로그 섹션 업데이트"""
        try:
            log_table = self.components.create_trading_log_table(log_data)
            log_panel = Panel(log_table, title="Trading Logs", box="ROUNDED")
            
            self.layout["trading_logs"].update(log_panel)
            
        except Exception as e:
            self.layout["trading_logs"].update(Panel(f"Trading Logs Error: {e}", style="red"))
    
    def _update_system_logs(self, log_data: List[str]) -> None:
        """시스템 로그 섹션 업데이트"""
        try:
            log_table = self.components.create_system_log_table(log_data)
            log_panel = Panel(log_table, title="System Logs", box="ROUNDED")
            
            self.layout["system_logs"].update(log_panel)
            
        except Exception as e:
            self.layout["system_logs"].update(Panel(f"System Logs Error: {e}", style="red"))
    
    def _update_footer(self, statistics: Dict, alerts: List[Dict]) -> None:
        """푸터 섹션 업데이트"""
        try:
            # 통계 정보
            stats_panel = self.components.create_statistics_panel(statistics)
            
            # 상태 정보
            status_data = {
                'current_state': self._cached_data.get('system_status', {}).get('current_state', 'UNKNOWN'),
                'dry_run': self._cached_data.get('system_status', {}).get('dry_run', False),
                'uptime': self._calculate_uptime()
            }
            status_panel = self.components.create_status_panel(status_data)
            
            # 알림이 있으면 알림 패널, 없으면 통계 패널
            if alerts:
                latest_alert = alerts[-1]
                alert_panel = self.components.create_alert_panel(
                    latest_alert.get('message', ''),
                    latest_alert.get('type', 'info')
                )
                footer_content = Layout()
                footer_content.split_column(
                    Layout(status_panel, size=1),
                    Layout(alert_panel, size=2)
                )
            else:
                footer_content = Layout()
                footer_content.split_column(
                    Layout(status_panel, size=1),
                    Layout(stats_panel, size=2)
                )
            
            self.layout["footer"].update(footer_content)
            
        except Exception as e:
            self.layout["footer"].update(Panel(f"Footer Error: {e}", style="red"))
    
    def _calculate_uptime(self) -> str:
        """업타임 계산"""
        try:
            start_time = self._cached_data.get('system_status', {}).get('start_time')
            if start_time:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                
                uptime_delta = datetime.now() - start_time.replace(tzinfo=None)
                total_seconds = int(uptime_delta.total_seconds())
                
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            return "00:00:00"
            
        except Exception:
            return "00:00:00"
    
    def _show_error(self, error_message: str) -> None:
        """에러 메시지 표시"""
        error_panel = Panel(
            Text(error_message, style="bold red", justify="center"),
            title="Error",
            box="HEAVY",
            style="red"
        )
        
        # 전체 레이아웃을 에러 메시지로 대체
        self.layout.update(error_panel)
    
    def render(self) -> Layout:
        """렌더링을 위한 레이아웃 반환"""
        return self.layout
    
    def get_layout_info(self) -> Dict:
        """레이아웃 정보 반환"""
        return {
            'last_update': self._last_update.isoformat() if self._last_update else None,
            'sections': {
                'header': 'System title and current time',
                'market_info': 'Current price, balance, position',
                'signals': 'RSI/EMA trading signals',
                'orders': 'Active orders status',
                'trading_logs': 'Trading execution logs',
                'system_logs': 'System operational logs',
                'footer': 'Statistics and alerts'
            },
            'dimensions': {
                'header': 3,
                'market_info': 12,
                'signals': 10,
                'orders': 12,
                'footer': 3
            }
        }
    
    def clear_screen(self) -> None:
        """화면 클리어"""
        self.console.clear()
    
    def show_loading(self, message: str = "Loading...") -> None:
        """로딩 화면 표시"""
        loading_panel = Panel(
            Text(message, style="bold cyan", justify="center"),
            title="System Status",
            box="ROUNDED",
            style="cyan"
        )
        
        self.layout.update(loading_panel)
    
    def show_startup_screen(self) -> None:
        """시작 화면 표시"""
        startup_text = Text()
        startup_text.append("Coinone USDT/KRW Trading Bot\n", style="bold cyan", justify="center")
        startup_text.append("Initializing system...\n", style="dim", justify="center")
        startup_text.append(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim", justify="center")
        
        startup_panel = Panel(
            Align.center(startup_text),
            title="System Startup",
            box="HEAVY",
            style="cyan",
            padding=(2, 4)
        )
        
        self.layout.update(startup_panel)


class DashboardDataFormatter:
    """대시보드 데이터 포맷터"""
    
    @staticmethod
    def format_trading_strategy_data(strategy_result: Dict) -> Dict:
        """거래 전략 결과를 대시보드 형식으로 변환"""
        try:
            market_data = strategy_result.get('market_data', {})
            position_summary = strategy_result.get('position_summary', {})
            order_summary = strategy_result.get('order_summary', {})
            
            # 신호 데이터 추출
            buy_signal = strategy_result.get('buy_signal', {})
            liquidation_signal = strategy_result.get('liquidation_signal', {})
            
            rsi_analysis = buy_signal.get('rsi_analysis', {}) or liquidation_signal.get('rsi_analysis', {})
            ema_analysis = buy_signal.get('ema_analysis', {}) or liquidation_signal.get('ema_analysis', {})
            
            return {
                'market_data': {
                    'current_price': market_data.get('current_price', 0),
                    'price_change': 0,  # 계산 필요
                    'change_percent': 0,  # 계산 필요
                    'volume': market_data.get('ticker', {}).get('volume', 0),
                    'timestamp': market_data.get('timestamp', datetime.now().isoformat())
                },
                'balance': {
                    'krw_balance': 0,  # API에서 조회 필요
                    'usdt_balance': position_summary.get('total_quantity', 0),
                    'current_price': market_data.get('current_price', 0)
                },
                'position': {
                    'has_position': position_summary.get('has_position', False),
                    'average_buy_price': position_summary.get('average_buy_price', 0),
                    'total_quantity': position_summary.get('total_quantity', 0),
                    'current_price': market_data.get('current_price', 0),
                    'unrealized_pnl': position_summary.get('unrealized_pnl', 0),
                    'profit_target_price': position_summary.get('profit_target_price', 0)
                },
                'signals': {
                    'rsi': {
                        'current_value': rsi_analysis.get('current_rsi', 0),
                        'signal': buy_signal.get('rsi_signal', False)
                    },
                    'ema': {
                        'current_value': ema_analysis.get('current_ema', 0),
                        'signal': buy_signal.get('ema_signal', False),
                        'slope_3': ema_analysis.get('slope_3_periods', 0),
                        'slope_5': ema_analysis.get('slope_5_periods', 0)
                    }
                },
                'orders': order_summary.get('active_orders', []),
                'trading_logs': [],  # 별도 관리 필요
                'system_logs': [],   # 별도 관리 필요
                'statistics': {
                    'total_trades': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'avg_profit': 0,
                    'max_drawdown': 0
                },
                'system_status': {
                    'current_state': strategy_result.get('current_state', 'UNKNOWN'),
                    'dry_run': False,  # 설정에서 가져오기
                    'start_time': datetime.now().isoformat()
                },
                'alerts': []
            }
            
        except Exception as e:
            return {
                'error': f"Data formatting error: {e}",
                'timestamp': datetime.now().isoformat()
            }