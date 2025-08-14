"""
백테스트 성과 분석 모듈
거래 결과의 다양한 성과 지표 계산 및 분석
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """성과 지표 데이터 클래스"""
    # 기본 지표
    total_return: float = 0.0  # 총 수익률 (%)
    total_return_abs: float = 0.0  # 절대 수익 (원)
    
    # 거래 통계
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0  # 승률 (%)
    
    # 손익 분석
    avg_win: float = 0.0  # 평균 수익
    avg_loss: float = 0.0  # 평균 손실
    profit_factor: float = 0.0  # 수익 팩터 (총수익/총손실)
    avg_trade_pnl: float = 0.0  # 평균 거래 손익
    
    # 리스크 지표
    max_drawdown: float = 0.0  # 최대 낙폭 (%)
    max_drawdown_abs: float = 0.0  # 최대 낙폭 절대값
    sharpe_ratio: float = 0.0  # 샤프 비율
    sortino_ratio: float = 0.0  # 소르티노 비율
    calmar_ratio: float = 0.0  # 칼마 비율
    
    # 변동성 지표
    volatility: float = 0.0  # 연간 변동성 (%)
    downside_volatility: float = 0.0  # 하향 변동성
    
    # 시간 관련
    avg_holding_period: float = 0.0  # 평균 보유 기간 (시간)
    max_holding_period: float = 0.0  # 최대 보유 기간 (시간)
    
    # 기타
    recovery_factor: float = 0.0  # 회복 팩터
    expectancy: float = 0.0  # 기댓값
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'total_return_pct': self.total_return,
            'total_return_abs': self.total_return_abs,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate_pct': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'avg_trade_pnl': self.avg_trade_pnl,
            'max_drawdown_pct': self.max_drawdown,
            'max_drawdown_abs': self.max_drawdown_abs,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'volatility_annual_pct': self.volatility,
            'downside_volatility': self.downside_volatility,
            'avg_holding_hours': self.avg_holding_period,
            'max_holding_hours': self.max_holding_period,
            'recovery_factor': self.recovery_factor,
            'expectancy': self.expectancy
        }


class PerformanceAnalyzer:
    """성과 분석기"""
    
    def __init__(self):
        self.risk_free_rate = 0.025  # 무위험 수익률 (연 2.5%)
    
    def analyze_backtest_result(self, backtest_result: Dict[str, Any]) -> PerformanceMetrics:
        """
        백테스트 결과 종합 분석
        
        Args:
            backtest_result: 백테스트 엔진 결과
            
        Returns:
            PerformanceMetrics: 성과 지표
        """
        trades = backtest_result.get('trades', [])
        equity_curve = backtest_result.get('equity_curve', [])
        initial_balance = backtest_result.get('initial_balance', 0)
        final_balance = backtest_result.get('final_balance', 0)
        
        metrics = PerformanceMetrics()
        
        # 기본 수익률 계산
        if initial_balance > 0:
            metrics.total_return = ((final_balance / initial_balance) - 1) * 100
            metrics.total_return_abs = final_balance - initial_balance
        
        # 거래 분석
        if trades:
            metrics = self._analyze_trades(trades, metrics)
        
        # 자산 곡선 분석
        if equity_curve:
            metrics = self._analyze_equity_curve(equity_curve, metrics, initial_balance)
        
        return metrics
    
    def _analyze_trades(self, trades: List, metrics: PerformanceMetrics) -> PerformanceMetrics:
        """거래 내역 분석"""
        metrics.total_trades = len(trades)
        
        if not trades:
            return metrics
        
        # 승패 분석
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        metrics.winning_trades = len(winning_trades)
        metrics.losing_trades = len(losing_trades)
        metrics.win_rate = (metrics.winning_trades / metrics.total_trades) * 100
        
        # 손익 분석
        if winning_trades:
            metrics.avg_win = np.mean([t.pnl for t in winning_trades])
        
        if losing_trades:
            metrics.avg_loss = np.mean([t.pnl for t in losing_trades])
        
        # 수익 팩터
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        
        if total_losses > 0:
            metrics.profit_factor = total_wins / total_losses
        
        # 평균 거래 손익
        metrics.avg_trade_pnl = np.mean([t.pnl for t in trades])
        
        # 보유 기간 분석
        holding_periods = []
        for trade in trades:
            if trade.entry_time and trade.exit_time:
                duration = trade.exit_time - trade.entry_time
                holding_periods.append(duration.total_seconds() / 3600)  # 시간 단위
        
        if holding_periods:
            metrics.avg_holding_period = np.mean(holding_periods)
            metrics.max_holding_period = max(holding_periods)
        
        # 기댓값 계산
        if metrics.total_trades > 0:
            win_prob = metrics.win_rate / 100
            loss_prob = 1 - win_prob
            
            if metrics.avg_win > 0 and metrics.avg_loss < 0:
                metrics.expectancy = (win_prob * metrics.avg_win) + (loss_prob * metrics.avg_loss)
        
        return metrics
    
    def _analyze_equity_curve(
        self, 
        equity_curve: List[Dict], 
        metrics: PerformanceMetrics,
        initial_balance: float
    ) -> PerformanceMetrics:
        """자산 곡선 분석"""
        if not equity_curve:
            return metrics
        
        df = pd.DataFrame(equity_curve)
        
        # 수익률 시리즈 계산
        returns = df['total_equity'].pct_change().dropna()
        
        if len(returns) == 0:
            return metrics
        
        # 변동성 계산 (연환산)
        if len(returns) > 1:
            # 시간당 수익률의 표준편차를 연간으로 환산 (24시간 * 365일)
            metrics.volatility = returns.std() * np.sqrt(24 * 365) * 100
        
        # 최대 낙폭 계산
        equity_series = df['total_equity']
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        
        metrics.max_drawdown = abs(drawdown.min())
        metrics.max_drawdown_abs = abs((equity_series - running_max).min())
        
        # 샤프 비율 계산
        if len(returns) > 1 and returns.std() > 0:
            # 시간당 무위험 수익률
            hourly_risk_free = (1 + self.risk_free_rate) ** (1 / (365 * 24)) - 1
            excess_returns = returns - hourly_risk_free
            metrics.sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(24 * 365)
        
        # 소르티노 비율 계산
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 1:
            downside_std = negative_returns.std()
            metrics.downside_volatility = downside_std * np.sqrt(24 * 365) * 100
            
            if downside_std > 0:
                hourly_risk_free = (1 + self.risk_free_rate) ** (1 / (365 * 24)) - 1
                excess_returns = returns - hourly_risk_free
                metrics.sortino_ratio = excess_returns.mean() / downside_std * np.sqrt(24 * 365)
        
        # 칼마 비율 계산
        if metrics.max_drawdown > 0:
            annualized_return = ((equity_series.iloc[-1] / equity_series.iloc[0]) ** 
                               (365 * 24 / len(equity_series)) - 1) * 100
            metrics.calmar_ratio = annualized_return / metrics.max_drawdown
        
        # 회복 팩터 계산
        if metrics.max_drawdown > 0:
            metrics.recovery_factor = metrics.total_return / metrics.max_drawdown
        
        return metrics
    
    def calculate_monthly_returns(self, equity_curve: List[Dict]) -> pd.DataFrame:
        """월별 수익률 계산"""
        if not equity_curve:
            return pd.DataFrame()
        
        df = pd.DataFrame(equity_curve)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # 월별 리샘플링
        monthly = df.resample('M')['total_equity'].last()
        monthly_returns = monthly.pct_change().dropna() * 100
        
        return monthly_returns.to_frame('return_pct')
    
    def calculate_trade_distribution(self, trades: List) -> Dict[str, Any]:
        """거래 분포 분석"""
        if not trades:
            return {}
        
        pnl_list = [t.pnl for t in trades]
        pnl_pct_list = [t.pnl_pct for t in trades]
        
        return {
            'pnl_distribution': {
                'mean': np.mean(pnl_list),
                'std': np.std(pnl_list),
                'min': min(pnl_list),
                'max': max(pnl_list),
                'median': np.median(pnl_list),
                'q25': np.percentile(pnl_list, 25),
                'q75': np.percentile(pnl_list, 75)
            },
            'pnl_pct_distribution': {
                'mean': np.mean(pnl_pct_list),
                'std': np.std(pnl_pct_list),
                'min': min(pnl_pct_list),
                'max': max(pnl_pct_list),
                'median': np.median(pnl_pct_list),
                'q25': np.percentile(pnl_pct_list, 25),
                'q75': np.percentile(pnl_pct_list, 75)
            }
        }
    
    def analyze_drawdown_periods(self, equity_curve: List[Dict]) -> List[Dict]:
        """낙폭 기간 분석"""
        if not equity_curve:
            return []
        
        df = pd.DataFrame(equity_curve)
        equity_series = df['total_equity']
        timestamps = pd.to_datetime(df['timestamp'])
        
        # 누적 최고값 계산
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        
        # 낙폭 기간 찾기
        drawdown_periods = []
        in_drawdown = False
        start_idx = 0
        
        for i, dd in enumerate(drawdown):
            if dd < -0.01 and not in_drawdown:  # 1% 이상 하락시 낙폭 시작
                in_drawdown = True
                start_idx = i
            elif dd >= 0 and in_drawdown:  # 회복시 낙폭 종료
                in_drawdown = False
                
                # 낙폭 기간 정보 저장
                period_drawdown = drawdown[start_idx:i+1]
                max_dd = abs(period_drawdown.min())
                
                if max_dd > 0.01:  # 1% 이상인 낙폭만 기록
                    drawdown_periods.append({
                        'start_date': timestamps.iloc[start_idx],
                        'end_date': timestamps.iloc[i],
                        'duration_hours': (timestamps.iloc[i] - timestamps.iloc[start_idx]).total_seconds() / 3600,
                        'max_drawdown_pct': max_dd * 100,
                        'start_equity': equity_series.iloc[start_idx],
                        'min_equity': equity_series[start_idx:i+1].min(),
                        'end_equity': equity_series.iloc[i]
                    })
        
        # 정렬 (최대 낙폭 순)
        drawdown_periods.sort(key=lambda x: x['max_drawdown_pct'], reverse=True)
        
        return drawdown_periods
    
    def compare_to_buy_and_hold(
        self, 
        backtest_result: Dict[str, Any], 
        price_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """바이앤드홀드 전략과 비교"""
        if price_data.empty:
            return {}
        
        initial_balance = backtest_result.get('initial_balance', 0)
        final_balance = backtest_result.get('final_balance', 0)
        
        # 바이앤드홀드 수익률 계산
        start_price = price_data['close'].iloc[0]
        end_price = price_data['close'].iloc[-1]
        bh_return = ((end_price / start_price) - 1) * 100
        
        # 전략 수익률
        strategy_return = ((final_balance / initial_balance) - 1) * 100 if initial_balance > 0 else 0
        
        return {
            'strategy_return_pct': strategy_return,
            'buy_hold_return_pct': bh_return,
            'outperformance_pct': strategy_return - bh_return,
            'start_price': start_price,
            'end_price': end_price
        }


def analyze_backtest_performance(backtest_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    백테스트 성과 종합 분석 함수
    
    Args:
        backtest_result: 백테스트 엔진 결과
        
    Returns:
        Dict: 종합 성과 분석 결과
    """
    analyzer = PerformanceAnalyzer()
    
    # 기본 성과 지표
    metrics = analyzer.analyze_backtest_result(backtest_result)
    
    # 추가 분석
    trades = backtest_result.get('trades', [])
    equity_curve = backtest_result.get('equity_curve', [])
    
    analysis_result = {
        'metrics': metrics.to_dict(),
        'trade_distribution': analyzer.calculate_trade_distribution(trades),
        'drawdown_periods': analyzer.analyze_drawdown_periods(equity_curve),
        'monthly_returns': analyzer.calculate_monthly_returns(equity_curve).to_dict() if equity_curve else {}
    }
    
    # 바이앤드홀드 비교 (데이터가 있는 경우)
    if 'data_with_indicators' in backtest_result:
        comparison = analyzer.compare_to_buy_and_hold(
            backtest_result, 
            backtest_result['data_with_indicators']
        )
        analysis_result['buy_hold_comparison'] = comparison
    
    return analysis_result


if __name__ == "__main__":
    # 테스트 실행
    logging.basicConfig(level=logging.INFO)
    
    print("성과 분석 모듈 테스트")
    print("=" * 50)
    
    # 샘플 백테스트 결과로 테스트
    from backtest_engine import run_quick_backtest, BacktestConfig
    from data_loader import SampleDataGenerator
    
    # 샘플 데이터 생성
    sample_df = SampleDataGenerator.generate_realistic_data(hours=1000)
    
    # 백테스트 실행
    config = BacktestConfig(initial_balance=1000000)
    backtest_result = run_quick_backtest(sample_df, config)
    
    # 성과 분석
    analysis = analyze_backtest_performance(backtest_result)
    
    # 결과 출력
    metrics = analysis['metrics']
    print(f"\n=== 기본 성과 지표 ===")
    print(f"총 수익률: {metrics['total_return_pct']:.2f}%")
    print(f"총 거래 수: {metrics['total_trades']}개")
    print(f"승률: {metrics['win_rate_pct']:.1f}%")
    print(f"수익 팩터: {metrics['profit_factor']:.2f}")
    print(f"최대 낙폭: {metrics['max_drawdown_pct']:.2f}%")
    print(f"샤프 비율: {metrics['sharpe_ratio']:.2f}")
    print(f"평균 보유 시간: {metrics['avg_holding_hours']:.1f}시간")
    
    if 'buy_hold_comparison' in analysis:
        comparison = analysis['buy_hold_comparison']
        print(f"\n=== 바이앤드홀드 비교 ===")
        print(f"전략 수익률: {comparison['strategy_return_pct']:.2f}%")
        print(f"바이앤드홀드 수익률: {comparison['buy_hold_return_pct']:.2f}%")
        print(f"초과 수익률: {comparison['outperformance_pct']:.2f}%")