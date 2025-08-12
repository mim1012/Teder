"""
Rich 라이브러리 기반 UI 컴포넌트 모듈
재사용 가능한 UI 컴포넌트들을 정의
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.layout import Layout
from rich.align import Align
from rich.columns import Columns
from rich.box import ROUNDED, SIMPLE, HEAVY


class ColorScheme:
    """색상 스키마 정의"""
    PROFIT = "green"
    LOSS = "red" 
    BUY_SIGNAL = "blue"
    SELL_SIGNAL = "yellow"
    NEUTRAL = "white"
    ACCENT = "cyan"
    SECONDARY = "dim"
    WARNING = "orange3"
    SUCCESS = "green3"
    ERROR = "red3"


class UIComponents:
    """UI 컴포넌트 생성 클래스"""
    
    def __init__(self, console: Console):
        self.console = console
        self.colors = ColorScheme()
    
    def create_header_panel(self, title: str, subtitle: str = "") -> Panel:
        """헤더 패널 생성"""
        header_text = Text(title, style="bold cyan", justify="center")
        if subtitle:
            header_text.append(f"\n{subtitle}", style="dim")
        
        return Panel(
            header_text,
            box=HEAVY,
            style="cyan",
            padding=(0, 1)
        )
    
    def create_market_info_table(self, market_data: Dict) -> Table:
        """시장 정보 테이블 생성"""
        table = Table(show_header=False, box=SIMPLE, padding=(0, 1))
        table.add_column("Label", style="dim", width=12)
        table.add_column("Value", style="bold")
        
        current_price = market_data.get('current_price', 0)
        price_change = market_data.get('price_change', 0)
        change_percent = market_data.get('change_percent', 0)
        
        # 가격 변동에 따른 색상 결정
        price_color = self.colors.PROFIT if price_change >= 0 else self.colors.LOSS
        
        table.add_row("Current Price", f"{current_price:,.0f} KRW")
        table.add_row(
            "Change", 
            f"{price_change:+,.0f} ({change_percent:+.2f}%)",
            style=price_color
        )
        table.add_row("Volume", f"{market_data.get('volume', 0):,.0f}")
        table.add_row("Last Update", market_data.get('timestamp', 'N/A'))
        
        return table
    
    def create_balance_table(self, balance_data: Dict) -> Table:
        """잔고 정보 테이블 생성"""
        table = Table(show_header=False, box=SIMPLE, padding=(0, 1))
        table.add_column("Asset", style="dim", width=8)
        table.add_column("Amount", style="bold", justify="right")
        table.add_column("Value", style="bold", justify="right")
        
        krw_balance = balance_data.get('krw_balance', 0)
        usdt_balance = balance_data.get('usdt_balance', 0)
        current_price = balance_data.get('current_price', 0)
        usdt_value = usdt_balance * current_price
        total_value = krw_balance + usdt_value
        
        table.add_row("KRW", f"{krw_balance:,.0f}", f"{krw_balance:,.0f} KRW")
        table.add_row("USDT", f"{usdt_balance:.4f}", f"{usdt_value:,.0f} KRW")
        table.add_row("Total", "", f"{total_value:,.0f} KRW", style="bold cyan")
        
        return table
    
    def create_position_table(self, position_data: Dict) -> Table:
        """포지션 정보 테이블 생성"""
        table = Table(show_header=False, box=SIMPLE, padding=(0, 1))
        table.add_column("Metric", style="dim", width=15)
        table.add_column("Value", style="bold")
        
        if not position_data.get('has_position', False):
            table.add_row("Status", "No Position", style="dim")
            return table
        
        avg_price = position_data.get('average_buy_price', 0)
        quantity = position_data.get('total_quantity', 0)
        current_price = position_data.get('current_price', 0)
        unrealized_pnl = position_data.get('unrealized_pnl', 0)
        profit_target = position_data.get('profit_target_price', 0)
        
        # 수익률 계산
        if avg_price > 0:
            profit_rate = ((current_price - avg_price) / avg_price) * 100
        else:
            profit_rate = 0
        
        # 수익/손실에 따른 색상
        pnl_color = self.colors.PROFIT if unrealized_pnl >= 0 else self.colors.LOSS
        
        table.add_row("Avg Buy Price", f"{avg_price:,.0f} KRW")
        table.add_row("Quantity", f"{quantity:.4f} USDT")
        table.add_row("Current Price", f"{current_price:,.0f} KRW")
        table.add_row("Profit Target", f"{profit_target:,.0f} KRW", style=self.colors.SUCCESS)
        table.add_row(
            "Unrealized P&L", 
            f"{unrealized_pnl:+,.0f} KRW ({profit_rate:+.2f}%)",
            style=pnl_color
        )
        
        return table
    
    def create_signals_table(self, signals_data: Dict) -> Table:
        """신호 정보 테이블 생성"""
        table = Table(show_header=True, box=SIMPLE, padding=(0, 1))
        table.add_column("Indicator", style="dim", width=8)
        table.add_column("Value", justify="right")
        table.add_column("Signal", justify="center", width=8)
        table.add_column("Status", justify="center", width=10)
        
        # RSI 정보
        rsi_data = signals_data.get('rsi', {})
        rsi_value = rsi_data.get('current_value', 0)
        rsi_signal = rsi_data.get('signal', False)
        
        table.add_row(
            "RSI(14)",
            f"{rsi_value:.2f}",
            "BUY" if rsi_signal else "-",
            "[green]ACTIVE[/]" if rsi_signal else "[dim]WAITING[/]"
        )
        
        # EMA 정보
        ema_data = signals_data.get('ema', {})
        ema_value = ema_data.get('current_value', 0)
        ema_signal = ema_data.get('signal', False)
        ema_slope_3 = ema_data.get('slope_3', 0)
        ema_slope_5 = ema_data.get('slope_5', 0)
        
        table.add_row(
            "EMA(20)",
            f"{ema_value:.2f}",
            "BUY" if ema_signal else "-",
            "[green]ACTIVE[/]" if ema_signal else "[dim]WAITING[/]"
        )
        
        table.add_row(
            "EMA Slope3",
            f"{ema_slope_3:.3f}",
            ">" if ema_slope_3 >= 0.3 else "<",
            "[green]OK[/]" if ema_slope_3 >= 0.3 else "[red]NO[/]"
        )
        
        table.add_row(
            "EMA Slope5", 
            f"{ema_slope_5:.3f}",
            ">" if ema_slope_5 >= 0.2 else "<",
            "[green]OK[/]" if ema_slope_5 >= 0.2 else "[red]NO[/]"
        )
        
        return table
    
    def create_orders_table(self, orders_data: List[Dict]) -> Table:
        """주문 정보 테이블 생성"""
        table = Table(show_header=True, box=SIMPLE, padding=(0, 1))
        table.add_column("Time", width=8)
        table.add_column("Type", width=4)
        table.add_column("Side", width=4)
        table.add_column("Quantity", justify="right", width=10)
        table.add_column("Price", justify="right", width=10)
        table.add_column("Status", justify="center", width=8)
        
        if not orders_data:
            table.add_row("No active orders", "", "", "", "", "", style="dim")
            return table
        
        for order in orders_data[-10:]:  # 최근 10개만 표시
            order_time = order.get('timestamp', '')[:8]  # HH:MM:SS
            order_type = order.get('type', 'LIMIT')
            side = order.get('side', 'BUY')
            quantity = order.get('quantity', 0)
            price = order.get('price', 0)
            status = order.get('status', 'PENDING')
            
            # 상태에 따른 색상
            status_color = {
                'FILLED': 'green',
                'CANCELLED': 'red',
                'PENDING': 'yellow',
                'PARTIAL': 'orange3'
            }.get(status, 'white')
            
            # 매수/매도에 따른 색상
            side_color = self.colors.BUY_SIGNAL if side == 'BUY' else self.colors.SELL_SIGNAL
            
            table.add_row(
                order_time,
                order_type,
                f"[{side_color}]{side}[/]",
                f"{quantity:.4f}",
                f"{price:,.0f}",
                f"[{status_color}]{status}[/]"
            )
        
        return table
    
    def create_trading_log_table(self, log_data: List[Dict]) -> Table:
        """거래 로그 테이블 생성"""
        table = Table(show_header=True, box=SIMPLE, padding=(0, 1))
        table.add_column("Time", width=8)
        table.add_column("Action", width=12)
        table.add_column("Message", min_width=30)
        table.add_column("P&L", justify="right", width=10)
        
        if not log_data:
            table.add_row("No trading logs", "", "", "", style="dim")
            return table
        
        for log in log_data[-15:]:  # 최근 15개만 표시
            log_time = log.get('timestamp', '')[:8]
            action = log.get('action', '')
            message = log.get('message', '')
            pnl = log.get('pnl', 0)
            
            # 액션에 따른 색상
            action_color = {
                'buy_order_filled': self.colors.BUY_SIGNAL,
                'sell_order_filled': self.colors.SELL_SIGNAL,
                'profit_cycle_completed': self.colors.SUCCESS,
                'liquidation_completed': self.colors.WARNING,
                'error': self.colors.ERROR
            }.get(action, self.colors.NEUTRAL)
            
            # P&L 색상
            pnl_color = self.colors.PROFIT if pnl >= 0 else self.colors.LOSS
            pnl_text = f"{pnl:+,.0f}" if pnl != 0 else "-"
            
            table.add_row(
                log_time,
                f"[{action_color}]{action}[/]",
                message[:50] + "..." if len(message) > 50 else message,
                f"[{pnl_color}]{pnl_text}[/]"
            )
        
        return table
    
    def create_system_log_table(self, log_data: List[str]) -> Table:
        """시스템 로그 테이블 생성"""
        table = Table(show_header=False, box=SIMPLE, padding=(0, 1))
        table.add_column("Log", style="dim")
        
        if not log_data:
            table.add_row("No system logs", style="dim")
            return table
        
        for log in log_data[-10:]:  # 최근 10개만 표시
            # 로그 레벨에 따른 색상
            if "ERROR" in log:
                style = self.colors.ERROR
            elif "WARNING" in log:
                style = self.colors.WARNING
            elif "INFO" in log:
                style = self.colors.ACCENT
            else:
                style = self.colors.SECONDARY
            
            table.add_row(log, style=style)
        
        return table
    
    def create_status_panel(self, status_data: Dict) -> Panel:
        """상태 패널 생성"""
        current_state = status_data.get('current_state', 'UNKNOWN')
        dry_run = status_data.get('dry_run', False)
        uptime = status_data.get('uptime', '00:00:00')
        
        # 상태에 따른 색상
        state_colors = {
            'waiting_for_buy': self.colors.NEUTRAL,
            'position_held': self.colors.BUY_SIGNAL,
            'waiting_for_sell': self.colors.SELL_SIGNAL,
            'strategy_completed': self.colors.SUCCESS,
            'error': self.colors.ERROR
        }
        
        state_color = state_colors.get(current_state, self.colors.NEUTRAL)
        mode_text = "DRY RUN" if dry_run else "LIVE TRADING"
        mode_color = self.colors.WARNING if dry_run else self.colors.SUCCESS
        
        status_text = Text()
        status_text.append(f"State: ", style="dim")
        status_text.append(f"{current_state.upper()}", style=f"bold {state_color}")
        status_text.append(f" | Mode: ", style="dim")
        status_text.append(f"{mode_text}", style=f"bold {mode_color}")
        status_text.append(f" | Uptime: ", style="dim")
        status_text.append(f"{uptime}", style="bold")
        
        return Panel(
            Align.center(status_text),
            box=ROUNDED,
            style="dim"
        )
    
    def create_progress_bar(self, description: str, progress: float = 0, total: float = 100) -> Progress:
        """진행률 바 생성"""
        progress_bar = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
            transient=True
        )
        
        task = progress_bar.add_task(description, total=total)
        progress_bar.update(task, completed=progress)
        
        return progress_bar
    
    def create_statistics_panel(self, stats_data: Dict) -> Panel:
        """통계 패널 생성"""
        total_trades = stats_data.get('total_trades', 0)
        win_rate = stats_data.get('win_rate', 0)
        total_pnl = stats_data.get('total_pnl', 0)
        avg_profit = stats_data.get('avg_profit', 0)
        max_drawdown = stats_data.get('max_drawdown', 0)
        
        stats_text = Text()
        stats_text.append(f"Trades: {total_trades} | ", style="dim")
        stats_text.append(f"Win Rate: {win_rate:.1f}% | ", style="cyan")
        
        # 총 수익에 따른 색상
        pnl_color = self.colors.PROFIT if total_pnl >= 0 else self.colors.LOSS
        stats_text.append(f"Total P&L: ", style="dim")
        stats_text.append(f"{total_pnl:+,.0f} KRW | ", style=pnl_color)
        
        stats_text.append(f"Avg: {avg_profit:+,.0f} KRW | ", style="dim")
        stats_text.append(f"Max DD: {max_drawdown:,.0f} KRW", style=self.colors.WARNING)
        
        return Panel(
            Align.center(stats_text),
            title="Trading Statistics",
            box=ROUNDED,
            style="dim"
        )
    
    def create_alert_panel(self, alert_message: str, alert_type: str = "info") -> Panel:
        """알림 패널 생성"""
        colors = {
            'info': self.colors.ACCENT,
            'success': self.colors.SUCCESS,
            'warning': self.colors.WARNING,
            'error': self.colors.ERROR
        }
        
        color = colors.get(alert_type, self.colors.NEUTRAL)
        
        return Panel(
            Text(alert_message, style=f"bold {color}", justify="center"),
            box=HEAVY,
            style=color,
            padding=(0, 1)
        )