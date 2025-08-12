#!/usr/bin/env python3
"""
분할매수 전략 백테스트 및 테스트
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.indicators.rsi_short import RSIShort, RSIEMAShort
from src.indicators.price_ema import PriceEMA
from src.indicators.rsi import RSICalculator


class SplitStrategyBacktest:
    """분할매수 전략 백테스트"""
    
    def __init__(self):
        # 지표 초기화
        self.rsi_short = RSIShort(period=9)
        self.rsi_ema_short = RSIEMAShort(rsi_period=9, ema_period=5)
        self.price_ema = PriceEMA(period=5)
        self.rsi_14 = RSICalculator(period=14)
        
        # 분할 비율
        self.split_ratios = [0.3, 0.3, 0.4]  # 30%, 30%, 40%
        
        # 백테스트 결과
        self.results = []
        self.trades = []
    
    def generate_sample_data(self, days=30) -> pd.DataFrame:
        """샘플 데이터 생성 (1시간봉)"""
        np.random.seed(42)
        
        # 기본 가격 (USDT/KRW 약 1,300)
        base_price = 1300
        hours = days * 24
        
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=days),
            periods=hours,
            freq='H'
        )
        
        # 랜덤 워크로 가격 생성
        price_changes = np.random.normal(0, 0.002, hours)  # 0.2% 표준편차
        price_changes[0] = 0
        cumulative_changes = np.cumsum(price_changes)
        prices = base_price * (1 + cumulative_changes)
        
        # 트렌드 추가 (일부 구간에서 상승/하락 트렌드)
        trend_periods = [
            (hours//4, hours//4 + hours//8, 0.001),      # 상승 구간
            (hours//2, hours//2 + hours//6, -0.0005),    # 하락 구간
            (3*hours//4, 3*hours//4 + hours//10, 0.0008) # 상승 구간
        ]
        
        for start, end, trend in trend_periods:
            if end <= hours:
                trend_array = np.linspace(0, trend * (end - start), end - start)
                prices[start:end] *= (1 + trend_array)
        
        # OHLCV 데이터 생성
        data = []
        for i in range(hours):
            base = prices[i]
            volatility = base * 0.005  # 0.5% 변동성
            
            high = base + np.random.uniform(0, volatility)
            low = base - np.random.uniform(0, volatility)
            
            # Open은 이전 종가 기준
            if i == 0:
                open_price = base
            else:
                open_price = data[i-1]['close']
            
            close = base
            volume = np.random.uniform(100, 1000)  # 임의 거래량
            
            data.append({
                'timestamp': dates[i],
                'open': open_price,
                'high': max(open_price, high, close),
                'low': min(open_price, low, close),
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        return df
    
    def check_phase1_conditions(self, data: pd.DataFrame, idx: int) -> dict:
        """1차 매수 조건 체크"""
        if idx < 20:  # 충분한 데이터가 없으면 False
            return {'condition_met': False, 'reason': 'Insufficient data'}
        
        # 현재까지의 데이터로 지표 계산
        current_data = data.iloc[:idx+1].copy()
        
        try:
            # RSI(9) 조건
            rsi_result = self.rsi_short.check_buy_condition(current_data)
            
            # RSI EMA 조건
            rsi_ema_result = self.rsi_ema_short.check_buy_condition(current_data)
            
            # 가격 EMA 조건
            price_ema_result = self.price_ema.check_buy_condition(current_data)
            
            # 모든 조건 확인
            all_met = (
                rsi_result['condition_met'] and
                rsi_ema_result['condition_met'] and
                price_ema_result['condition_met']
            )
            
            return {
                'condition_met': all_met,
                'rsi': rsi_result,
                'rsi_ema': rsi_ema_result,
                'price_ema': price_ema_result
            }
            
        except Exception as e:
            return {'condition_met': False, 'error': str(e)}
    
    def simulate_trade(self, data: pd.DataFrame, start_idx: int, initial_balance: float = 1000000) -> dict:
        """단일 거래 시뮬레이션"""
        current_price = data.iloc[start_idx]['close']
        
        # 분할매수 시뮬레이션
        phases = []
        total_quantity = 0
        total_invested = 0
        remaining_balance = initial_balance
        
        # 1차 매수 (30%)
        phase1_amount = initial_balance * self.split_ratios[0]
        phase1_quantity = phase1_amount / current_price
        total_quantity += phase1_quantity
        total_invested += phase1_amount
        remaining_balance -= phase1_amount
        avg_price = current_price
        
        phases.append({
            'phase': 1,
            'price': current_price,
            'quantity': phase1_quantity,
            'amount': phase1_amount
        })
        
        # 2차, 3차 매수 가격 계산
        phase2_price = avg_price - 2
        phase3_price = avg_price - 2  # 추가 하락시
        
        # 이후 가격 변동 확인하여 2차, 3차 매수 여부 결정
        max_check_periods = min(48, len(data) - start_idx - 1)  # 최대 48시간 또는 데이터 끝까지
        
        phase2_executed = False
        phase3_executed = False
        sell_idx = None
        sell_price = 0
        sell_reason = ""
        
        for i in range(1, max_check_periods + 1):
            if start_idx + i >= len(data):
                break
                
            current_price = data.iloc[start_idx + i]['close']
            
            # 2차 매수 체크 (가격이 phase2_price 이하로 떨어졌을 때)
            if not phase2_executed and current_price <= phase2_price:
                phase2_amount = initial_balance * self.split_ratios[1]
                if remaining_balance >= phase2_amount:
                    phase2_quantity = phase2_amount / current_price
                    total_quantity += phase2_quantity
                    total_invested += phase2_amount
                    remaining_balance -= phase2_amount
                    
                    # 평균가 재계산
                    avg_price = total_invested / total_quantity
                    
                    phases.append({
                        'phase': 2,
                        'price': current_price,
                        'quantity': phase2_quantity,
                        'amount': phase2_amount
                    })
                    phase2_executed = True
            
            # 3차 매수 체크 (2차 매수 후 추가 하락시)
            if phase2_executed and not phase3_executed and current_price <= phase3_price:
                phase3_amount = remaining_balance  # 남은 금액 전부
                if phase3_amount > 0:
                    phase3_quantity = phase3_amount / current_price
                    total_quantity += phase3_quantity
                    total_invested += phase3_amount
                    remaining_balance = 0
                    
                    # 평균가 재계산
                    avg_price = total_invested / total_quantity
                    
                    phases.append({
                        'phase': 3,
                        'price': current_price,
                        'quantity': phase3_quantity,
                        'amount': phase3_amount
                    })
                    phase3_executed = True
            
            # 매도 조건 체크
            target_price = avg_price + 3  # 익절 목표가
            stop_loss_price = avg_price - 2  # 손절가 (3차 매수 후에만)
            
            # 익절 조건
            if current_price >= target_price:
                sell_idx = start_idx + i
                sell_price = target_price
                sell_reason = "Take Profit"
                break
            
            # 손절 조건 (3차 매수 후)
            if phase3_executed and current_price <= stop_loss_price:
                sell_idx = start_idx + i
                sell_price = stop_loss_price
                sell_reason = "Stop Loss"
                break
            
            # 24시간 경과 조건
            if i >= 24:
                sell_idx = start_idx + i
                sell_price = current_price
                sell_reason = "24H Time Limit"
                break
            
            # RSI(14) > 70 조건 체크
            if start_idx + i >= 14:
                current_data = data.iloc[:start_idx + i + 1]
                rsi_14_values = self.rsi_14.calculate_rsi(current_data)
                if len(rsi_14_values) > 0 and rsi_14_values.iloc[-1] > 70:
                    sell_idx = start_idx + i
                    sell_price = current_price
                    sell_reason = "RSI > 70"
                    break
        
        # 매도가 실행되지 않았으면 마지막 가격으로 매도
        if sell_idx is None:
            sell_idx = start_idx + max_check_periods
            if sell_idx >= len(data):
                sell_idx = len(data) - 1
            sell_price = data.iloc[sell_idx]['close']
            sell_reason = "End of Period"
        
        # 수익 계산
        total_sell_amount = total_quantity * sell_price
        profit = total_sell_amount - total_invested
        profit_rate = (profit / total_invested) * 100
        
        return {
            'start_idx': start_idx,
            'sell_idx': sell_idx,
            'start_time': data.iloc[start_idx]['timestamp'],
            'sell_time': data.iloc[sell_idx]['timestamp'],
            'phases': phases,
            'avg_buy_price': avg_price,
            'sell_price': sell_price,
            'sell_reason': sell_reason,
            'total_quantity': total_quantity,
            'total_invested': total_invested,
            'total_sell_amount': total_sell_amount,
            'profit': profit,
            'profit_rate': profit_rate,
            'holding_hours': sell_idx - start_idx
        }
    
    def run_backtest(self, data: pd.DataFrame, initial_balance: float = 1000000):
        """백테스트 실행"""
        print(f"Starting backtest with {len(data)} candles...")
        
        i = 20  # 충분한 데이터가 확보된 시점부터 시작
        balance = initial_balance
        total_trades = 0
        successful_trades = 0
        
        while i < len(data) - 50:  # 최소 50개 캔들은 남겨둠
            # 1차 매수 조건 체크
            conditions = self.check_phase1_conditions(data, i)
            
            if conditions['condition_met']:
                print(f"\nBuy signal detected at {data.iloc[i]['timestamp']} (index {i})")
                print(f"Price: {data.iloc[i]['close']:.2f} KRW")
                
                # 거래 시뮬레이션
                trade_result = self.simulate_trade(data, i, balance)
                
                print(f"Trade completed:")
                print(f"  - Phases: {len(trade_result['phases'])}")
                print(f"  - Avg buy price: {trade_result['avg_buy_price']:.2f}")
                print(f"  - Sell price: {trade_result['sell_price']:.2f}")
                print(f"  - Profit: {trade_result['profit']:,.0f} KRW ({trade_result['profit_rate']:.2f}%)")
                print(f"  - Holding time: {trade_result['holding_hours']} hours")
                print(f"  - Sell reason: {trade_result['sell_reason']}")
                
                # 결과 저장
                self.results.append(trade_result)
                
                # 다음 거래를 위해 인덱스 이동 (매도 시점 이후)
                i = trade_result['sell_idx'] + 24  # 24시간 후부터 다시 신호 탐지
                total_trades += 1
                
                if trade_result['profit'] > 0:
                    successful_trades += 1
                
                # 잔고 업데이트 (단순화: 손실은 반영하지 않음)
                if trade_result['profit'] > 0:
                    balance += trade_result['profit']
            else:
                i += 1
        
        # 백테스트 결과 요약
        if self.results:
            total_profit = sum(r['profit'] for r in self.results)
            avg_profit_rate = np.mean([r['profit_rate'] for r in self.results])
            win_rate = (successful_trades / total_trades) * 100
            
            print(f"\n=== BACKTEST RESULTS ===")
            print(f"Total trades: {total_trades}")
            print(f"Successful trades: {successful_trades}")
            print(f"Win rate: {win_rate:.1f}%")
            print(f"Total profit: {total_profit:,.0f} KRW")
            print(f"Average profit rate: {avg_profit_rate:.2f}%")
            print(f"Final balance: {balance:,.0f} KRW")
            print(f"Total return: {((balance - initial_balance) / initial_balance) * 100:.2f}%")
        else:
            print("\nNo trades were executed during the backtest period.")
    
    def plot_results(self, data: pd.DataFrame):
        """결과 시각화"""
        if not self.results:
            print("No results to plot")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # 가격 차트와 매매 신호
        ax1.plot(data['timestamp'], data['close'], label='USDT/KRW Price', alpha=0.7)
        
        # 매수/매도 포인트 표시
        for result in self.results:
            start_time = result['start_time']
            sell_time = result['sell_time']
            start_price = result['phases'][0]['price']
            sell_price = result['sell_price']
            
            ax1.scatter(start_time, start_price, color='green', marker='^', s=100, alpha=0.8)
            ax1.scatter(sell_time, sell_price, color='red', marker='v', s=100, alpha=0.8)
        
        ax1.set_title('Price Chart with Buy/Sell Signals')
        ax1.set_ylabel('Price (KRW)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 수익률 차트
        profit_rates = [r['profit_rate'] for r in self.results]
        cumulative_returns = np.cumsum(profit_rates)
        
        ax2.bar(range(len(profit_rates)), profit_rates, alpha=0.7, 
                color=['green' if p > 0 else 'red' for p in profit_rates])
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.set_title('Profit Rate per Trade')
        ax2.set_xlabel('Trade Number')
        ax2.set_ylabel('Profit Rate (%)')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


def main():
    """메인 함수"""
    print("Split Buy Strategy Backtest")
    print("=" * 50)
    
    # 백테스트 인스턴스 생성
    backtest = SplitStrategyBacktest()
    
    # 샘플 데이터 생성 (30일)
    print("Generating sample data...")
    sample_data = backtest.generate_sample_data(days=30)
    print(f"Generated {len(sample_data)} hourly candles")
    
    # 백테스트 실행
    backtest.run_backtest(sample_data)
    
    # 결과 시각화 (matplotlib 사용 가능한 환경에서)
    try:
        backtest.plot_results(sample_data)
    except ImportError:
        print("matplotlib not available for plotting")
    except Exception as e:
        print(f"Error plotting results: {e}")


if __name__ == "__main__":
    main()