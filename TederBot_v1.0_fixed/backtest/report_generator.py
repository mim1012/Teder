"""
백테스트 리포트 생성 모듈
시각화 및 리포트 생성 기능
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import seaborn as sns
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
import platform
import matplotlib.font_manager as fm
import os

def setup_korean_font():
    """한글 폰트 설정 - Windows 환경 최적화"""
    system = platform.system()
    font_set = False
    
    try:
        if system == 'Windows':
            # Windows에서 사용 가능한 한글 폰트들 (우선순위순)
            font_candidates = [
                'Malgun Gothic',      # 맑은 고딕
                'NanumGothic',        # 나눔고딕
                'NanumBarunGothic',   # 나눔바른고딕
                'Nanum Gothic',       # 나눔고딕 (다른 이름)
                'Gulim',              # 굴림
                'Dotum',              # 돋움
                'Batang',             # 바탕
                'Gungsuh',            # 궁서
                'Microsoft YaHei',    # 중국어지만 한글 일부 지원
                'SimHei'              # 중국어지만 한글 일부 지원
            ]
            
            # Windows 폰트 직접 경로 시도
            windows_font_paths = [
                r'C:\Windows\Fonts\malgun.ttf',      # 맑은 고딕
                r'C:\Windows\Fonts\malgunbd.ttf',    # 맑은 고딕 Bold
                r'C:\Windows\Fonts\gulim.ttc',       # 굴림
                r'C:\Windows\Fonts\batang.ttc',      # 바탕
                r'C:\Windows\Fonts\dotum.ttc',       # 돋움
            ]
            
            # 1. 폰트 이름으로 찾기
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            print(f"사용 가능한 폰트 수: {len(available_fonts)}")
            
            for font in font_candidates:
                if font in available_fonts:
                    plt.rcParams['font.family'] = font
                    print(f"한글 폰트 설정 성공: {font}")
                    font_set = True
                    break
            
            # 2. 폰트 파일 직접 경로로 시도
            if not font_set:
                print("폰트 이름으로 찾기 실패, 직접 경로 시도...")
                for font_path in windows_font_paths:
                    if os.path.exists(font_path):
                        try:
                            font_prop = fm.FontProperties(fname=font_path)
                            plt.rcParams['font.family'] = font_prop.get_name()
                            print(f"직접 경로로 한글 폰트 설정 성공: {font_path}")
                            font_set = True
                            break
                        except Exception as e:
                            print(f"폰트 경로 {font_path} 설정 실패: {e}")
                            continue
            
        elif system == 'Darwin':  # macOS
            font_candidates = ['AppleGothic', 'NanumGothic', 'Nanum Gothic']
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            for font in font_candidates:
                if font in available_fonts:
                    plt.rcParams['font.family'] = font
                    print(f"한글 폰트 설정 성공 (macOS): {font}")
                    font_set = True
                    break
                    
        else:  # Linux
            font_candidates = ['NanumGothic', 'Nanum Gothic', 'DejaVu Sans']
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            for font in font_candidates:
                if font in available_fonts:
                    plt.rcParams['font.family'] = font
                    print(f"한글 폰트 설정 성공 (Linux): {font}")
                    font_set = True
                    break
        
        # 한글 폰트를 찾지 못한 경우 기본 설정
        if not font_set:
            print("한글 폰트를 찾지 못했습니다. 기본 폰트를 사용합니다.")
            # 유니코드 지원이 가능한 기본 폰트들 시도
            fallback_fonts = ['DejaVu Sans', 'Arial Unicode MS', 'Liberation Sans']
            for font in fallback_fonts:
                try:
                    plt.rcParams['font.family'] = font
                    print(f"대체 폰트 설정: {font}")
                    break
                except:
                    continue
            
    except Exception as e:
        print(f"폰트 설정 중 오류 발생: {e}")
        # 최종 안전장치
        try:
            plt.rcParams['font.family'] = 'DejaVu Sans'
            print("안전장치: DejaVu Sans 폰트 사용")
        except:
            print("모든 폰트 설정 실패 - 시스템 기본 폰트 사용")
    
    # 한글 마이너스 기호 문제 해결
    try:
        plt.rcParams['axes.unicode_minus'] = False
        print("한글 마이너스 기호 설정 완료")
    except Exception as e:
        print(f"마이너스 기호 설정 실패: {e}")
    
    # 현재 설정된 폰트 정보 출력
    try:
        current_font = plt.rcParams.get('font.family', ['unknown'])
        if isinstance(current_font, list):
            current_font = current_font[0] if current_font else 'unknown'
        print(f"최종 설정된 폰트: {current_font}")
    except Exception as e:
        print(f"폰트 정보 출력 실패: {e}")

# 한글 폰트 설정 실행
setup_korean_font()

logger = logging.getLogger(__name__)


class BacktestReportGenerator:
    """백테스트 리포트 생성기"""
    
    def __init__(self, figsize: tuple = (15, 12)):
        self.figsize = figsize
        sns.set_style("whitegrid")
        
        # 폰트 캐시 강제 새로고침 (Windows에서 도움이 됨)
        try:
            # matplotlib 버전에 따라 다른 방법 시도
            if hasattr(fm, '_rebuild'):
                fm._rebuild()
            elif hasattr(fm.fontManager, 'addfont'):
                # 새로운 버전의 경우 캐시 업데이트
                pass
        except Exception as e:
            print(f"폰트 캐시 새로고침 실패: {e}")
        
        # 한글 폰트 재설정 (혹시 모를 경우를 대비)
        self._ensure_korean_font()
    
    def _ensure_korean_font(self):
        """한글 폰트 설정 확인 및 재설정"""
        try:
            current_font = plt.rcParams.get('font.family', ['DejaVu Sans'])
            if isinstance(current_font, list):
                current_font = current_font[0] if current_font else 'DejaVu Sans'
            
            # 테스트 문자로 한글 지원 여부 확인
            test_fig, test_ax = plt.subplots(figsize=(1, 1))
            test_ax.text(0.5, 0.5, '한글테스트', ha='center', va='center')
            plt.close(test_fig)
            
        except Exception as e:
            print(f"한글 폰트 테스트 실패, 재설정 시도: {e}")
            # 다시 한번 한글 폰트 설정 시도
            setup_korean_font()
        
    def generate_full_report(
        self, 
        backtest_result: Dict[str, Any], 
        analysis_result: Dict[str, Any],
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        종합 백테스트 리포트 생성
        
        Args:
            backtest_result: 백테스트 결과
            analysis_result: 성과 분석 결과
            save_path: 저장 경로 (None이면 저장하지 않음)
            
        Returns:
            matplotlib.Figure: 생성된 차트
        """
        fig = plt.figure(figsize=(20, 16))
        gs = GridSpec(4, 3, figure=fig, hspace=0.3, wspace=0.3)
        
        # 1. 자산 곡선과 낙폭
        self._plot_equity_and_drawdown(fig, gs[0, :], backtest_result, analysis_result)
        
        # 2. 가격 차트와 거래 포인트
        self._plot_price_and_trades(fig, gs[1, :], backtest_result)
        
        # 3. 성과 지표 테이블
        self._plot_performance_metrics(fig, gs[2, 0], analysis_result)
        
        # 4. 거래 분포
        self._plot_trade_distribution(fig, gs[2, 1], backtest_result)
        
        # 5. 월별 수익률
        self._plot_monthly_returns(fig, gs[2, 2], analysis_result)
        
        # 6. 낙폭 분석
        self._plot_drawdown_periods(fig, gs[3, 0], analysis_result)
        
        # 7. 바이앤드홀드 비교
        self._plot_strategy_comparison(fig, gs[3, 1], analysis_result)
        
        # 8. 거래 통계
        self._plot_trade_statistics(fig, gs[3, 2], backtest_result)
        
        # 제목 설정 (한글 폰트 오류 방지)
        try:
            fig.suptitle('USDT/KRW 자동매매 전략 백테스트 리포트', fontsize=20, fontweight='bold')
        except Exception as e:
            print(f"한글 제목 설정 실패, 영문 제목 사용: {e}")
            fig.suptitle('USDT/KRW Trading Strategy Backtest Report', fontsize=20, fontweight='bold')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
            logger.info(f"리포트 저장됨: {save_path}")
        
        return fig
    
    def _plot_equity_and_drawdown(self, fig, gs_pos, backtest_result, analysis_result):
        """자산 곡선과 낙폭 차트"""
        equity_curve = backtest_result.get('equity_curve', [])
        if not equity_curve:
            return
        
        ax1 = fig.add_subplot(gs_pos)
        
        df = pd.DataFrame(equity_curve)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 자산 곡선
        ax1.plot(df['timestamp'], df['total_equity'], 'b-', linewidth=2, label='포트폴리오 가치')
        try:
            ax1.set_ylabel('자산 가치 (원)', color='b')
        except Exception:
            ax1.set_ylabel('Asset Value (KRW)', color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        ax1.legend(loc='upper left')
        
        # 낙폭
        ax2 = ax1.twinx()
        running_max = df['total_equity'].expanding().max()
        drawdown = (df['total_equity'] - running_max) / running_max * 100
        ax2.fill_between(df['timestamp'], drawdown, 0, alpha=0.3, color='red', label='낙폭')
        try:
            ax2.set_ylabel('낙폭 (%)', color='r')
        except Exception:
            ax2.set_ylabel('Drawdown (%)', color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        ax2.legend(loc='upper right')
        
        # 제목 설정 (한글 폰트 오류 방지)
        try:
            ax1.set_title('포트폴리오 가치 및 낙폭 추이', fontsize=14, fontweight='bold')
        except Exception:
            ax1.set_title('Portfolio Value & Drawdown', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
    
    def _plot_price_and_trades(self, fig, gs_pos, backtest_result):
        """가격 차트와 거래 포인트"""
        data = backtest_result.get('data_with_indicators', pd.DataFrame())
        trades = backtest_result.get('trades', [])
        
        if data.empty:
            return
        
        ax = fig.add_subplot(gs_pos)
        
        # 가격 차트
        ax.plot(data['timestamp'], data['close'], 'k-', linewidth=1, alpha=0.7, label='USDT/KRW')
        
        # EMA
        if 'ema' in data.columns:
            ax.plot(data['timestamp'], data['ema'], 'orange', linewidth=1, alpha=0.8, label='EMA(20)')
        
        # 거래 포인트 표시
        for trade in trades:
            if trade.entry_time and trade.exit_time:
                # 매수 포인트
                entry_idx = data[data['timestamp'] <= trade.entry_time].index
                if len(entry_idx) > 0:
                    entry_price = data.loc[entry_idx[-1], 'close']
                    ax.scatter(trade.entry_time, entry_price, c='green', s=100, marker='^', 
                             alpha=0.7, zorder=5)
                
                # 매도 포인트
                exit_idx = data[data['timestamp'] <= trade.exit_time].index
                if len(exit_idx) > 0:
                    exit_price = data.loc[exit_idx[-1], 'close']
                    color = 'red' if trade.pnl < 0 else 'blue'
                    ax.scatter(trade.exit_time, exit_price, c=color, s=100, marker='v', 
                             alpha=0.7, zorder=5)
        
        # 제목 설정 (한글 폰트 오류 방지)
        try:
            ax.set_title('가격 차트 및 거래 포인트', fontsize=14, fontweight='bold')
        except Exception:
            ax.set_title('Price Chart & Trade Points', fontsize=14, fontweight='bold')
        try:
            ax.set_ylabel('가격 (원)')
        except Exception:
            ax.set_ylabel('Price (KRW)')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_performance_metrics(self, fig, gs_pos, analysis_result):
        """성과 지표 테이블"""
        metrics = analysis_result.get('metrics', {})
        
        ax = fig.add_subplot(gs_pos)
        ax.axis('off')
        
        # 주요 지표 선택
        key_metrics = [
            ('총 수익률', f"{metrics.get('total_return_pct', 0):.2f}%"),
            ('총 거래 수', f"{metrics.get('total_trades', 0)}회"),
            ('승률', f"{metrics.get('win_rate_pct', 0):.1f}%"),
            ('수익 팩터', f"{metrics.get('profit_factor', 0):.2f}"),
            ('최대 낙폭', f"{metrics.get('max_drawdown_pct', 0):.2f}%"),
            ('샤프 비율', f"{metrics.get('sharpe_ratio', 0):.2f}"),
            ('소르티노 비율', f"{metrics.get('sortino_ratio', 0):.2f}"),
            ('평균 보유시간', f"{metrics.get('avg_holding_hours', 0):.1f}시간")
        ]
        
        # 테이블 생성
        table_data = []
        for metric, value in key_metrics:
            table_data.append([metric, value])
        
        table = ax.table(cellText=table_data,
                        colLabels=['지표', '값'],
                        cellLoc='center',
                        loc='center',
                        colWidths=[0.6, 0.4])
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        # 헤더 스타일
        for i in range(2):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # 제목 설정 (한글 폰트 오류 방지)
        try:
            ax.set_title('주요 성과 지표', fontsize=14, fontweight='bold')
        except Exception:
            ax.set_title('Key Performance Metrics', fontsize=14, fontweight='bold')
    
    def _plot_trade_distribution(self, fig, gs_pos, backtest_result):
        """거래 손익 분포"""
        trades = backtest_result.get('trades', [])
        
        if not trades:
            return
        
        ax = fig.add_subplot(gs_pos)
        
        pnl_list = [t.pnl for t in trades]
        
        # 히스토그램
        ax.hist(pnl_list, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax.axvline(0, color='red', linestyle='--', alpha=0.7, label='손익분기점')
        ax.axvline(np.mean(pnl_list), color='green', linestyle='-', alpha=0.7, label=f'평균: {np.mean(pnl_list):.0f}원')
        
        # 제목 설정 (한글 폰트 오류 방지)
        try:
            ax.set_title('거래 손익 분포', fontsize=14, fontweight='bold')
        except Exception:
            ax.set_title('Trade P&L Distribution', fontsize=14, fontweight='bold')
        try:
            ax.set_xlabel('손익 (원)')
            ax.set_ylabel('빈도')
        except Exception:
            ax.set_xlabel('P&L (KRW)')
            ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_monthly_returns(self, fig, gs_pos, analysis_result):
        """월별 수익률"""
        monthly_returns = analysis_result.get('monthly_returns', {})
        
        if not monthly_returns:
            ax = fig.add_subplot(gs_pos)
            try:
                ax.text(0.5, 0.5, '월별 데이터 부족', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('월별 수익률', fontsize=14, fontweight='bold')
            except Exception:
                ax.text(0.5, 0.5, 'Insufficient monthly data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Monthly Returns', fontsize=14, fontweight='bold')
            return
        
        ax = fig.add_subplot(gs_pos)
        
        returns_data = monthly_returns.get('return_pct', {})
        if returns_data:
            months = list(returns_data.keys())
            returns = list(returns_data.values())
            
            colors = ['green' if r > 0 else 'red' for r in returns]
            bars = ax.bar(range(len(months)), returns, color=colors, alpha=0.7)
            
            # 제목 설정 (한글 폰트 오류 방지)
            try:
                ax.set_title('월별 수익률', fontsize=14, fontweight='bold')
            except Exception:
                ax.set_title('Monthly Returns', fontsize=14, fontweight='bold')
            try:
                ax.set_ylabel('수익률 (%)')
            except Exception:
                ax.set_ylabel('Return (%)')
            ax.set_xticks(range(len(months)))
            ax.set_xticklabels([str(m)[:7] for m in months], rotation=45)
            ax.grid(True, alpha=0.3)
            ax.axhline(0, color='black', linewidth=0.5)
    
    def _plot_drawdown_periods(self, fig, gs_pos, analysis_result):
        """주요 낙폭 기간"""
        drawdown_periods = analysis_result.get('drawdown_periods', [])
        
        ax = fig.add_subplot(gs_pos)
        
        if not drawdown_periods:
            try:
                ax.text(0.5, 0.5, '주요 낙폭 없음', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('주요 낙폭 기간', fontsize=14, fontweight='bold')
            except Exception:
                ax.text(0.5, 0.5, 'No major drawdown', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Major Drawdown Periods', fontsize=14, fontweight='bold')
            return
        
        # 상위 5개 낙폭만 표시
        top_drawdowns = drawdown_periods[:5]
        
        periods = [f"{dd['start_date'].strftime('%m/%d')}-{dd['end_date'].strftime('%m/%d')}" 
                  for dd in top_drawdowns]
        drawdowns = [dd['max_drawdown_pct'] for dd in top_drawdowns]
        
        bars = ax.barh(periods, drawdowns, color='red', alpha=0.7)
        # 제목 설정 (한글 폰트 오류 방지)
        try:
            ax.set_title('주요 낙폭 기간 (상위 5개)', fontsize=14, fontweight='bold')
        except Exception:
            ax.set_title('Major Drawdown Periods (Top 5)', fontsize=14, fontweight='bold')
        try:
            ax.set_xlabel('최대 낙폭 (%)')
        except Exception:
            ax.set_xlabel('Max Drawdown (%)')
        
        # 값 표시
        for i, (bar, value) in enumerate(zip(bars, drawdowns)):
            ax.text(value + max(drawdowns) * 0.01, i, f'{value:.1f}%', 
                   va='center', fontsize=9)
    
    def _plot_strategy_comparison(self, fig, gs_pos, analysis_result):
        """전략 vs 바이앤드홀드 비교"""
        comparison = analysis_result.get('buy_hold_comparison', {})
        
        ax = fig.add_subplot(gs_pos)
        
        if not comparison:
            try:
                ax.text(0.5, 0.5, '비교 데이터 없음', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('전략 vs 바이앤드홀드', fontsize=14, fontweight='bold')
            except Exception:
                ax.text(0.5, 0.5, 'No comparison data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Strategy vs Buy & Hold', fontsize=14, fontweight='bold')
            return
        
        strategies = ['자동매매 전략', '바이앤드홀드']
        returns = [
            comparison.get('strategy_return_pct', 0),
            comparison.get('buy_hold_return_pct', 0)
        ]
        
        colors = ['blue', 'gray']
        bars = ax.bar(strategies, returns, color=colors, alpha=0.7)
        
        # 제목 설정 (한글 폰트 오류 방지)
        try:
            ax.set_title('전략 수익률 비교', fontsize=14, fontweight='bold')
        except Exception:
            ax.set_title('Strategy Return Comparison', fontsize=14, fontweight='bold')
        try:
            ax.set_ylabel('수익률 (%)')
        except Exception:
            ax.set_ylabel('Return (%)')
        ax.grid(True, alpha=0.3)
        ax.axhline(0, color='black', linewidth=0.5)
        
        # 값 표시
        for bar, value in zip(bars, returns):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + (max(returns) * 0.01),
                   f'{value:.2f}%', ha='center', va='bottom', fontweight='bold')
    
    def _plot_trade_statistics(self, fig, gs_pos, backtest_result):
        """거래 통계"""
        trades = backtest_result.get('trades', [])
        
        ax = fig.add_subplot(gs_pos)
        
        if not trades:
            try:
                ax.text(0.5, 0.5, '거래 데이터 없음', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('거래 통계', fontsize=14, fontweight='bold')
            except Exception:
                ax.text(0.5, 0.5, 'No trade data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Trade Statistics', fontsize=14, fontweight='bold')
            return
        
        # 매도 이유별 통계
        reasons = {}
        for trade in trades:
            reason = trade.reason or '기타'
            reasons[reason] = reasons.get(reason, 0) + 1
        
        if reasons:
            labels = list(reasons.keys())
            sizes = list(reasons.values())
            
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                             startangle=90, textprops={'fontsize': 9})
            
            # 제목 설정 (한글 폰트 오류 방지)
            try:
                ax.set_title('매도 이유별 분포', fontsize=14, fontweight='bold')
            except Exception:
                ax.set_title('Exit Reason Distribution', fontsize=14, fontweight='bold')
        else:
            try:
                ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center', transform=ax.transAxes)
            except Exception:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
    
    def generate_summary_report(self, analysis_result: Dict[str, Any]) -> str:
        """텍스트 요약 리포트 생성"""
        metrics = analysis_result.get('metrics', {})
        
        report = f"""
USDT/KRW 자동매매 전략 백테스트 요약 리포트
{'='*60}

[ 기본 성과 지표 ]
- 총 수익률: {metrics.get('total_return_pct', 0):.2f}%
- 절대 수익: {metrics.get('total_return_abs', 0):,.0f}원
- 총 거래 수: {metrics.get('total_trades', 0)}회
- 승률: {metrics.get('win_rate_pct', 0):.1f}%

[ 위험 지표 ]
- 최대 낙폭: {metrics.get('max_drawdown_pct', 0):.2f}%
- 샤프 비율: {metrics.get('sharpe_ratio', 0):.2f}
- 소르티노 비율: {metrics.get('sortino_ratio', 0):.2f}
- 연간 변동성: {metrics.get('volatility_annual_pct', 0):.2f}%

[ 거래 분석 ]
- 수익 팩터: {metrics.get('profit_factor', 0):.2f}
- 평균 수익: {metrics.get('avg_win', 0):,.0f}원
- 평균 손실: {metrics.get('avg_loss', 0):,.0f}원
- 평균 보유시간: {metrics.get('avg_holding_hours', 0):.1f}시간

[ 전략 평가 ]"""
        
        # 전략 평가 추가
        total_return = metrics.get('total_return_pct', 0)
        win_rate = metrics.get('win_rate_pct', 0)
        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        max_dd = metrics.get('max_drawdown_pct', 0)
        
        if total_return > 10 and win_rate > 60 and sharpe_ratio > 1:
            evaluation = "우수한 성과"
        elif total_return > 5 and win_rate > 50:
            evaluation = "양호한 성과"
        elif total_return > 0:
            evaluation = "보통 성과"
        else:
            evaluation = "부진한 성과"
        
        report += f"\n- 종합 평가: {evaluation}"
        
        if max_dd > 20:
            report += "\n- 주의사항: 최대 낙폭이 큼 (위험도 높음)"
        elif max_dd > 10:
            report += "\n- 주의사항: 중간 수준의 위험도"
        
        # 바이앤드홀드 비교
        comparison = analysis_result.get('buy_hold_comparison', {})
        if comparison:
            outperformance = comparison.get('outperformance_pct', 0)
            report += f"\n- 바이앤드홀드 대비: {outperformance:.2f}%p"
        
        report += f"\n\n리포트 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return report


def generate_backtest_report(
    backtest_result: Dict[str, Any], 
    analysis_result: Dict[str, Any],
    save_chart_path: Optional[str] = None,
    save_summary_path: Optional[str] = None
) -> tuple:
    """
    종합 백테스트 리포트 생성
    
    Args:
        backtest_result: 백테스트 결과
        analysis_result: 성과 분석 결과
        save_chart_path: 차트 저장 경로
        save_summary_path: 텍스트 리포트 저장 경로
        
    Returns:
        tuple: (matplotlib.Figure, str) - 차트 객체와 텍스트 리포트
    """
    generator = BacktestReportGenerator()
    
    # 차트 리포트 생성
    chart_fig = generator.generate_full_report(
        backtest_result, 
        analysis_result, 
        save_chart_path
    )
    
    # 텍스트 리포트 생성
    text_report = generator.generate_summary_report(analysis_result)
    
    if save_summary_path:
        with open(save_summary_path, 'w', encoding='utf-8') as f:
            f.write(text_report)
        logger.info(f"텍스트 리포트 저장됨: {save_summary_path}")
    
    return chart_fig, text_report


def test_korean_font():
    """한글 폰트 설정 테스트"""
    print("\n=== 한글 폰트 설정 테스트 ===")
    
    try:
        # 현재 폰트 설정 확인
        current_font = plt.rcParams.get('font.family', ['unknown'])
        if isinstance(current_font, list):
            current_font = current_font[0] if current_font else 'unknown'
        print(f"현재 설정된 폰트: {current_font}")
        
        # 간단한 한글 차트 테스트
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # 테스트 데이터
        categories = ['수익', '손실', '무승부']
        values = [30, 20, 10]
        colors = ['green', 'red', 'blue']
        
        bars = ax.bar(categories, values, color=colors, alpha=0.7)
        ax.set_title('한글 폰트 테스트 차트', fontsize=16, fontweight='bold')
        ax.set_ylabel('거래 수 (회)')
        ax.set_xlabel('거래 결과')
        
        # 값 표시
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{value}회', ha='center', va='bottom')
        
        ax.grid(True, alpha=0.3)
        
        print("한글 차트 생성 성공!")
        plt.close(fig)
        return True
        
    except Exception as e:
        print(f"한글 폰트 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    # 테스트 실행
    logging.basicConfig(level=logging.INFO)
    
    print("리포트 생성 모듈 테스트")
    print("=" * 50)
    
    # 한글 폰트 테스트
    test_korean_font()
    
    # 샘플 백테스트 수행
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from backtest_engine import run_quick_backtest, BacktestConfig
    from data_loader import SampleDataGenerator
    from performance_analyzer import analyze_backtest_performance
    
    # 샘플 데이터 및 백테스트
    sample_df = SampleDataGenerator.generate_realistic_data(hours=1000)
    config = BacktestConfig(initial_balance=1000000)
    backtest_result = run_quick_backtest(sample_df, config)
    analysis_result = analyze_backtest_performance(backtest_result)
    
    # 리포트 생성
    chart_fig, text_report = generate_backtest_report(
        backtest_result, 
        analysis_result
    )
    
    # 텍스트 리포트 출력
    print(text_report)
    
    # 차트 표시
    plt.show()