#!/usr/bin/env python3
"""
코인원 USDT/KRW 분할매수 자동매매 메인 실행 파일
실시간 모니터링 포함
"""

import os
import sys
import time
import signal
from datetime import datetime
from typing import Optional

# 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.coinone_client import CoinoneClient
from src.strategy.split_buy_strategy import SplitBuyStrategy
from src.utils.logger import Logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.align import Align


class SplitStrategyBot:
    """분할매수 전략 봇"""
    
    def __init__(self):
        self.console = Console()
        self.logger = Logger()
        self.running = False
        
        # API 클라이언트 초기화
        self.client = self._init_client()
        if not self.client:
            self.console.print("[red]Error: Failed to initialize Coinone client[/red]")
            sys.exit(1)
        
        # 전략 초기화
        self.strategy = SplitBuyStrategy(self.client, self.logger)
        
        # 통계
        self.stats = {
            'start_time': datetime.now(),
            'total_cycles': 0,
            'successful_cycles': 0,
            'total_trades': 0,
            'total_profit': 0.0,
            'last_error': None
        }
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _init_client(self) -> Optional[CoinoneClient]:
        """API 클라이언트 초기화"""
        try:
            from config.api_keys import API_KEY, SECRET_KEY
            
            if not API_KEY or not SECRET_KEY:
                self.console.print("[red]Error: API keys not found in config/api_keys.py[/red]")
                return None
            
            client = CoinoneClient(API_KEY, SECRET_KEY)
            
            # 연결 테스트
            balance = client.get_balance()
            if not balance:
                self.console.print("[red]Error: Failed to connect to Coinone API[/red]")
                return None
            
            self.console.print("[green]Successfully connected to Coinone API[/green]")
            return client
            
        except ImportError:
            self.console.print("[red]Error: config/api_keys.py not found[/red]")
            self.console.print("Please create config/api_keys.py with your API keys:")
            self.console.print("API_KEY = 'your_api_key'")
            self.console.print("SECRET_KEY = 'your_secret_key'")
            return None
        except Exception as e:
            self.console.print(f"[red]Error initializing client: {e}[/red]")
            return None
    
    def _signal_handler(self, signum, frame):
        """종료 시그널 핸들러"""
        self.console.print("\n[yellow]Received shutdown signal. Stopping bot...[/yellow]")
        self.running = False
    
    def create_dashboard(self) -> Layout:
        """대시보드 레이아웃 생성"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=8)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        return layout
    
    def update_header(self, layout: Layout):
        """헤더 업데이트"""
        elapsed = datetime.now() - self.stats['start_time']
        header_text = Text()
        header_text.append("COINONE USDT/KRW SPLIT BUY STRATEGY BOT", style="bold blue")
        header_text.append(f" | Running: {str(elapsed).split('.')[0]}", style="green")
        header_text.append(f" | Cycles: {self.stats['total_cycles']}", style="cyan")
        
        layout["header"].update(
            Panel(
                Align.center(header_text),
                title="System Status",
                border_style="blue"
            )
        )
    
    def update_position_panel(self, layout: Layout):
        """포지션 정보 패널 업데이트"""
        position = self.strategy.get_position_status()
        
        table = Table(title="Position Status", show_header=False)
        table.add_column("Item", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        # 상태 색상 설정
        state_colors = {
            'WAITING': 'yellow',
            'PHASE1': 'blue',
            'PHASE2': 'magenta',
            'PHASE3': 'orange',
            'SELLING': 'green'
        }
        
        state_color = state_colors.get(position['state'], 'white')
        
        table.add_row("State", f"[{state_color}]{position['state']}[/{state_color}]")
        table.add_row("Avg Buy Price", f"{position['avg_buy_price']:.2f} KRW" if position['avg_buy_price'] > 0 else "N/A")
        table.add_row("Total Quantity", f"{position['total_quantity']:.4f} USDT" if position['total_quantity'] > 0 else "0")
        table.add_row("Total Invested", f"{position['total_invested']:,.0f} KRW" if position['total_invested'] > 0 else "0")
        table.add_row("Target Price", f"{position['target_profit_price']:.2f} KRW" if position['target_profit_price'] > 0 else "N/A")
        table.add_row("Stop Price", f"{position['stop_loss_price']:.2f} KRW" if position['stop_loss_price'] > 0 else "N/A")
        table.add_row("Buy Count", str(position['buy_count']))
        
        if position['created_at']:
            table.add_row("Created At", position['created_at'].strftime("%H:%M:%S"))
        
        layout["left"].update(Panel(table, border_style="green"))
    
    def update_market_panel(self, layout: Layout, market_data=None, conditions=None):
        """시장 정보 패널 업데이트"""
        table = Table(title="Market & Conditions", show_header=False)
        table.add_column("Item", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        if market_data is not None and not market_data.empty:
            current_price = market_data['close'].iloc[-1]
            table.add_row("Current Price", f"{current_price:.2f} KRW")
            
            # 24시간 변화율 (간단 계산)
            if len(market_data) >= 24:
                price_24h_ago = market_data['close'].iloc[-24]
                change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
                change_color = "green" if change_24h >= 0 else "red"
                table.add_row("24h Change", f"[{change_color}]{change_24h:+.2f}%[/{change_color}]")
        
        # 조건 정보
        if conditions:
            if 'rsi_condition' in conditions:
                rsi_cond = conditions['rsi_condition']
                rsi_color = "green" if rsi_cond['condition_met'] else "red"
                table.add_row("RSI(9) Condition", f"[{rsi_color}]{'✓' if rsi_cond['condition_met'] else '✗'}[/{rsi_color}]")
                if 'rsi_value' in rsi_cond and rsi_cond['rsi_value']:
                    table.add_row("RSI(9) Value", f"{rsi_cond['rsi_value']:.2f}")
                if 'slope_3' in rsi_cond:
                    table.add_row("RSI(9) Slope", f"{rsi_cond['slope_3']:.3f}")
            
            if 'rsi_ema_condition' in conditions:
                rsi_ema_cond = conditions['rsi_ema_condition']
                rsi_ema_color = "green" if rsi_ema_cond['condition_met'] else "red"
                table.add_row("RSI EMA Condition", f"[{rsi_ema_color}]{'✓' if rsi_ema_cond['condition_met'] else '✗'}[/{rsi_ema_color}]")
                if 'slope_2' in rsi_ema_cond:
                    table.add_row("RSI EMA Slope", f"{rsi_ema_cond['slope_2']:.3f}")
            
            if 'price_ema_condition' in conditions:
                price_ema_cond = conditions['price_ema_condition']
                price_ema_color = "green" if price_ema_cond['condition_met'] else "red"
                table.add_row("Price EMA Condition", f"[{price_ema_color}]{'✓' if price_ema_cond['condition_met'] else '✗'}[/{price_ema_color}]")
                if 'slope_2' in price_ema_cond:
                    table.add_row("Price EMA Slope", f"{price_ema_cond['slope_2']:.3f}")
        
        layout["right"].update(Panel(table, border_style="yellow"))
    
    def update_footer(self, layout: Layout):
        """풋터 통계 패널 업데이트"""
        try:
            # 잔고 조회
            balance = self.client.get_balance()
            krw_balance = float(balance.get('KRW', {}).get('available', 0)) if balance else 0
            usdt_balance = float(balance.get('USDT', {}).get('available', 0)) if balance else 0
            
        except:
            krw_balance = 0
            usdt_balance = 0
        
        # 통계 테이블
        stats_table = Table(show_header=True, header_style="bold magenta")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")
        
        stats_table.add_row("Available KRW", f"{krw_balance:,.0f}")
        stats_table.add_row("Available USDT", f"{usdt_balance:.4f}")
        stats_table.add_row("Total Cycles", str(self.stats['total_cycles']))
        stats_table.add_row("Success Rate", f"{(self.stats['successful_cycles']/max(1, self.stats['total_cycles'])*100):.1f}%")
        stats_table.add_row("Total Trades", str(self.stats['total_trades']))
        
        if self.stats['last_error']:
            stats_table.add_row("Last Error", f"[red]{self.stats['last_error']}[/red]")
        
        layout["footer"].update(Panel(stats_table, title="Statistics", border_style="magenta"))
    
    def run_single_cycle(self) -> dict:
        """단일 사이클 실행"""
        try:
            result = self.strategy.run_strategy_cycle()
            self.stats['total_cycles'] += 1
            
            if result.get('success', False):
                self.stats['successful_cycles'] += 1
                self.stats['last_error'] = None
                
                # 거래 발생시 카운트 증가
                if result.get('action') in ['phase1_buy', 'phase2_buy', 'phase3_buy', 'sell']:
                    self.stats['total_trades'] += 1
                    self.logger.info(f"Trade executed: {result['action']}")
            else:
                error_msg = result.get('error', 'Unknown error')
                self.stats['last_error'] = error_msg
                self.logger.error(f"Cycle failed: {error_msg}")
            
            return result
            
        except Exception as e:
            self.stats['total_cycles'] += 1
            error_msg = str(e)
            self.stats['last_error'] = error_msg
            self.logger.error(f"Exception in cycle: {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def run(self):
        """메인 실행 루프"""
        self.console.print("[green]Starting Split Buy Strategy Bot...[/green]")
        self.console.print("[cyan]Press Ctrl+C to stop[/cyan]")
        
        self.running = True
        layout = self.create_dashboard()
        
        with Live(layout, refresh_per_second=1, screen=True):
            while self.running:
                try:
                    # 사이클 실행
                    cycle_result = self.run_single_cycle()
                    
                    # 시장 데이터 조회 (대시보드용)
                    market_data = self.strategy.get_market_data()
                    conditions = cycle_result.get('conditions')
                    
                    # 대시보드 업데이트
                    self.update_header(layout)
                    self.update_position_panel(layout)
                    self.update_market_panel(layout, market_data, conditions)
                    self.update_footer(layout)
                    
                    # 30초 대기 (1시간봉 기반이므로 자주 체크할 필요 없음)
                    time.sleep(30)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    self.stats['last_error'] = str(e)
                    time.sleep(10)  # 오류시 10초 대기
        
        self.console.print("[yellow]Bot stopped.[/yellow]")
        
        # 종료시 포지션 상태 출력
        position = self.strategy.get_position_status()
        if position['state'] != 'WAITING':
            self.console.print(f"[orange]Warning: Bot stopped with active position in state: {position['state']}[/orange]")
            self.console.print("Please check your positions manually on the exchange.")


def main():
    """메인 함수"""
    try:
        bot = SplitStrategyBot()
        bot.run()
    except KeyboardInterrupt:
        print("\nBot interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()