"""
Generate USDT/KRW Historical Data for April-July 2024
4개월간 백테스트용 데이터 생성 스크립트
"""

import logging
from data_loader import load_april_july_2024_data

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    print("USDT/KRW 2024년 4월-7월 과거 데이터 생성")
    print("=" * 50)
    
    # 데이터 생성/로드
    df = load_april_july_2024_data()
    
    if df.empty:
        print("데이터 생성 실패!")
        return
    
    # 결과 정보 출력
    print(f"\n데이터 생성 완료:")
    print(f"- 기간: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
    print(f"- 총 데이터 포인트: {len(df)}개")
    print(f"- 실제 일수: {(df['timestamp'].max() - df['timestamp'].min()).days + 1}일")
    print(f"- 시간당 데이터: {len(df) / ((df['timestamp'].max() - df['timestamp'].min()).days + 1) / 24:.1f}개/일")
    
    # 가격 정보
    print(f"\n가격 정보:")
    print(f"- 시작 가격: {df['close'].iloc[0]:.2f} KRW")
    print(f"- 종료 가격: {df['close'].iloc[-1]:.2f} KRW")
    print(f"- 최고가: {df['close'].max():.2f} KRW")
    print(f"- 최저가: {df['close'].min():.2f} KRW")
    print(f"- 평균가: {df['close'].mean():.2f} KRW")
    
    # 거래량 정보
    print(f"\n거래량 정보:")
    print(f"- 평균 거래량: {df['volume'].mean():,.0f}")
    print(f"- 최대 거래량: {df['volume'].max():,.0f}")
    print(f"- 최소 거래량: {df['volume'].min():,.0f}")
    
    # 월별 통계
    df['month'] = df['timestamp'].dt.month
    monthly_stats = df.groupby('month').agg({
        'close': ['mean', 'min', 'max', 'std'],
        'volume': ['mean', 'sum']
    }).round(2)
    
    print(f"\n월별 통계:")
    print(monthly_stats)
    
    # 첫 5개와 마지막 5개 데이터 표시
    print(f"\n첫 5개 레코드:")
    print(df.head()[['timestamp', 'open', 'high', 'low', 'close', 'volume']])
    
    print(f"\n마지막 5개 레코드:")
    print(df.tail()[['timestamp', 'open', 'high', 'low', 'close', 'volume']])
    
    # 데이터 품질 검증
    print(f"\n데이터 품질:")
    print(f"- 결측값: {df.isnull().sum().sum()}개")
    print(f"- 중복 타임스탬프: {df['timestamp'].duplicated().sum()}개")
    
    # 시간 간격 검증
    time_diffs = df['timestamp'].diff().dropna()
    one_hour = time_diffs.mode()[0] if not time_diffs.empty else None
    consistent_intervals = (time_diffs == one_hour).mean() * 100 if one_hour else 0
    
    print(f"- 시간 간격 일관성: {consistent_intervals:.1f}%")
    print(f"- 예상 4개월 데이터 포인트: {24 * 122}개 (122일)")
    
    return df

if __name__ == "__main__":
    result_df = main()
    print("\n데이터 생성이 완료되었습니다!")
    print("이제 백테스트에서 load_april_july_2024_data() 함수를 사용하여 이 데이터를 로드할 수 있습니다.")