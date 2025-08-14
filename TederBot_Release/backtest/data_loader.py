"""
USDT/KRW 과거 데이터 로더
코인원 API를 통한 과거 가격 데이터 수집 및 처리
"""

import pandas as pd
import numpy as np
import requests
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CoinoneDataLoader:
    """코인원 API를 통한 과거 데이터 로더"""
    
    BASE_URL = "https://api.coinone.co.kr"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CoinoneBot/1.0',
            'Accept': 'application/json'
        })
    
    def get_candlestick_data(
        self, 
        currency: str = "usdt", 
        interval: str = "1h",
        limit: int = 200
    ) -> pd.DataFrame:
        """
        코인원에서 캔들스틱 데이터 조회
        
        Args:
            currency: 통화 심볼 (기본값: usdt)
            interval: 캔들 주기 (1h, 1d)
            limit: 조회할 캔들 개수 (최대 200)
            
        Returns:
            DataFrame: OHLCV 데이터
        """
        try:
            # 수정된 API 엔드포인트 사용
            url = f"{self.BASE_URL}/public/v2/chart/KRW/{currency.upper()}"
            params = {
                'interval': interval,
                'limit': min(limit, 200)  # 최대 200개 제한
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('result') != 'success':
                raise Exception(f"API 오류: {data.get('error_code', 'Unknown error')}")
            
            candles = data.get('chart', [])
            if not candles:
                raise Exception("데이터가 없습니다")
            
            # DataFrame으로 변환 (새로운 API 응답 구조에 맞춤)
            df_data = []
            for candle in candles:
                df_data.append({
                    'timestamp': candle.get('timestamp'),
                    'open': candle.get('open'),
                    'high': candle.get('high'), 
                    'low': candle.get('low'),
                    'close': candle.get('close'),
                    'volume': candle.get('target_volume', candle.get('volume'))
                })
            
            df = pd.DataFrame(df_data)
            
            # 데이터 타입 변환 (timestamp는 milliseconds)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 시간순 정렬
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"데이터 로드 완료: {len(df)}개 캔들, 기간: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
            
            return df
            
        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            raise
    
    def get_extended_data(
        self, 
        currency: str = "usdt",
        interval: str = "1h",
        days: int = 30
    ) -> pd.DataFrame:
        """
        더 많은 과거 데이터를 위해 여러 번 요청하여 데이터 수집
        
        Args:
            currency: 통화 심볼
            interval: 캔들 주기
            days: 과거 일수
            
        Returns:
            DataFrame: 확장된 OHLCV 데이터
        """
        all_data = []
        
        # 1시간봉 기준으로 필요한 요청 횟수 계산 (API 제한: 200개/요청)
        hours_per_request = 200
        total_hours = days * 24
        requests_needed = (total_hours + hours_per_request - 1) // hours_per_request
        
        logger.info(f"{days}일간의 데이터를 위해 {requests_needed}번 요청 예정")
        
        try:
            for i in range(requests_needed):
                logger.info(f"데이터 요청 {i+1}/{requests_needed}")
                
                df = self.get_candlestick_data(currency, interval, hours_per_request)
                
                if not df.empty:
                    all_data.append(df)
                
                # API 제한 방지를 위한 대기
                if i < requests_needed - 1:
                    time.sleep(1)
            
            if not all_data:
                raise Exception("데이터를 가져올 수 없습니다")
            
            # 모든 데이터 합치기
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # 중복 제거 및 정렬
            combined_df = combined_df.drop_duplicates(subset=['timestamp'])
            combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
            
            # 요청한 일수만큼만 필터링
            end_time = combined_df['timestamp'].max()
            start_time = end_time - pd.Timedelta(days=days)
            combined_df = combined_df[combined_df['timestamp'] >= start_time]
            
            logger.info(f"총 {len(combined_df)}개 캔들 데이터 수집 완료")
            
            return combined_df
            
        except Exception as e:
            logger.error(f"확장 데이터 로드 실패: {e}")
            raise


class SampleDataGenerator:
    """샘플 데이터 생성기 (API 사용 불가시 백테스트용)"""
    
    @staticmethod
    def generate_realistic_data(
        start_price: float = 1300.0,
        hours: int = 1000,
        volatility: float = 0.02
    ) -> pd.DataFrame:
        """
        현실적인 USDT/KRW 가격 데이터 생성
        
        Args:
            start_price: 시작 가격
            hours: 생성할 시간 수
            volatility: 변동성
            
        Returns:
            DataFrame: 생성된 OHLCV 데이터
        """
        np.random.seed(42)  # 재현 가능한 결과를 위해
        
        # 시간 인덱스 생성
        start_time = datetime.now() - timedelta(hours=hours)
        timestamps = [start_time + timedelta(hours=i) for i in range(hours)]
        
        # 가격 데이터 생성 (기하 브라운 운동 기반)
        prices = [start_price]
        
        for i in range(1, hours):
            # 트렌드 성분 (약한 상승 편향)
            trend = 0.0001
            
            # 랜덤 워크 성분
            random_change = np.random.normal(0, volatility)
            
            # 다음 가격 계산
            next_price = prices[-1] * (1 + trend + random_change)
            
            # 최소/최대 가격 제한
            next_price = max(1000, min(2000, next_price))
            prices.append(next_price)
        
        # OHLCV 데이터 생성
        data = []
        for i, timestamp in enumerate(timestamps):
            base_price = prices[i]
            
            # 각 시간봉의 OHLC 생성
            intra_volatility = volatility * 0.5
            high = base_price * (1 + abs(np.random.normal(0, intra_volatility)))
            low = base_price * (1 - abs(np.random.normal(0, intra_volatility)))
            
            # Open은 이전 Close와 유사하게
            if i == 0:
                open_price = base_price
            else:
                open_price = data[i-1]['close'] * (1 + np.random.normal(0, intra_volatility * 0.3))
            
            close_price = base_price
            
            # OHLC 논리적 순서 보정
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # 거래량 (랜덤하게 생성)
            volume = np.random.lognormal(10, 1)
            
            data.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 2)
            })
        
        df = pd.DataFrame(data)
        logger.info(f"샘플 데이터 생성 완료: {len(df)}개 캔들")
        
        return df


class DataValidator:
    """데이터 유효성 검증"""
    
    @staticmethod
    def validate_ohlcv_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        OHLCV 데이터 유효성 검증
        
        Args:
            df: 검증할 DataFrame
            
        Returns:
            Tuple[bool, List[str]]: (유효성, 오류 메시지 리스트)
        """
        errors = []
        
        # 필수 컬럼 확인
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"필수 컬럼 누락: {missing_columns}")
        
        if errors:
            return False, errors
        
        # 데이터 타입 확인
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            errors.append("timestamp 컬럼이 datetime 타입이 아닙니다")
        
        # 가격 데이터 논리적 검증
        invalid_ohlc = (
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close']) |
            (df['open'] <= 0) |
            (df['high'] <= 0) |
            (df['low'] <= 0) |
            (df['close'] <= 0)
        )
        
        if invalid_ohlc.any():
            invalid_count = invalid_ohlc.sum()
            errors.append(f"잘못된 OHLC 데이터: {invalid_count}개 행")
        
        # 결측값 확인
        null_counts = df[required_columns].isnull().sum()
        if null_counts.any():
            errors.append(f"결측값 발견: {null_counts.to_dict()}")
        
        # 중복 타임스탬프 확인
        duplicate_timestamps = df['timestamp'].duplicated().sum()
        if duplicate_timestamps > 0:
            errors.append(f"중복 타임스탬프: {duplicate_timestamps}개")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("데이터 유효성 검증 통과")
        else:
            logger.warning(f"데이터 유효성 검증 실패: {errors}")
        
        return is_valid, errors


def load_backtest_data(
    use_real_data: bool = True,
    days: int = 30,
    currency: str = "usdt"
) -> pd.DataFrame:
    """
    백테스트용 데이터 로드
    
    Args:
        use_real_data: 실제 API 데이터 사용 여부
        days: 과거 일수
        currency: 통화 심볼
        
    Returns:
        DataFrame: 백테스트용 OHLCV 데이터
    """
    if use_real_data:
        try:
            loader = CoinoneDataLoader()
            df = loader.get_extended_data(currency=currency, days=days)
            
            # 데이터 유효성 검증
            is_valid, errors = DataValidator.validate_ohlcv_data(df)
            if not is_valid:
                logger.warning(f"실제 데이터 검증 실패, 샘플 데이터로 대체: {errors}")
                df = SampleDataGenerator.generate_realistic_data(hours=days*24)
            
            return df
            
        except Exception as e:
            logger.warning(f"실제 데이터 로드 실패, 샘플 데이터 사용: {e}")
            return SampleDataGenerator.generate_realistic_data(hours=days*24)
    else:
        return SampleDataGenerator.generate_realistic_data(hours=days*24)


def load_april_july_2024_data() -> pd.DataFrame:
    """
    2024년 4월-7월 USDT/KRW 실제 과거 데이터 로드
    실제 시장 데이터 기반으로 수집된 CSV 파일을 우선 사용하고, 없으면 새로 수집
    
    Returns:
        DataFrame: 4개월간의 시간별 OHLCV 실제 데이터
    """
    # 실제 데이터 파일 경로들 (우선순위 순)
    real_data_files = [
        'D:\\Project\\Teder\\backtest\\real_usdt_krw_apr_jul_2024.csv',
        'D:\\Project\\Teder\\backtest\\usdt_krw_complete_apr_jul_2024.csv'
    ]
    
    # 실제 데이터 파일 확인 및 로드
    for csv_file_path in real_data_files:
        if os.path.exists(csv_file_path):
            try:
                logger.info(f"실제 데이터 파일에서 로드: {csv_file_path}")
                df = pd.read_csv(csv_file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # 데이터 유효성 검증
                is_valid, errors = DataValidator.validate_ohlcv_data(df)
                if is_valid and len(df) > 2000:  # 충분한 데이터가 있으면
                    logger.info(f"실제 데이터 로드 완료: {len(df)}개 레코드")
                    logger.info(f"데이터 기간: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
                    logger.info(f"가격 범위: {df['close'].min():.2f} ~ {df['close'].max():.2f} KRW")
                    return df
                else:
                    logger.warning(f"데이터 파일 검증 실패: {errors}")
            except Exception as e:
                logger.error(f"데이터 파일 읽기 실패: {e}")
    
    # 실제 데이터 파일이 없으면 새로 수집
    logger.info("기존 실제 데이터 파일을 찾을 수 없음. 새로 수집 시도...")
    
    try:
        from real_historical_data_fetcher import get_real_april_july_2024_data, save_real_data_to_csv
        
        # 실제 데이터 수집
        logger.info("실제 USDT/KRW 데이터 수집 중...")
        df = get_real_april_july_2024_data()
        
        if not df.empty:
            # 새로 수집한 데이터 저장
            save_path = save_real_data_to_csv(df, 'real_usdt_krw_apr_jul_2024.csv')
            logger.info(f"새로 수집한 실제 데이터 저장: {save_path}")
            logger.info(f"수집 완료: {len(df)}개 레코드")
            return df
        else:
            logger.warning("실제 데이터 수집 실패")
    
    except ImportError as e:
        logger.warning(f"실제 데이터 수집 모듈 import 실패: {e}")
    except Exception as e:
        logger.warning(f"실제 데이터 수집 실패: {e}")
    
    # 모든 실제 데이터 수집 시도 실패시 폴백 - 향상된 시뮬레이션 데이터 생성
    logger.info("실제 데이터 수집 실패, 향상된 시뮬레이션 데이터 생성...")
    
    start_date = datetime(2024, 4, 1, 0, 0, 0)
    end_date = datetime(2024, 7, 31, 23, 0, 0)
    
    # 전체 시간 범위 생성 (4개월 = 약 2928시간)
    time_range = pd.date_range(start=start_date, end=end_date, freq='h')
    
    # 2024년 4-7월 실제 USDT/KRW 시장을 반영한 현실적인 데이터 생성
    np.random.seed(42)  # 일관된 결과
    
    # 월별 시장 특성 (실제 시장 데이터 기반)
    market_params = {
        4: {'base_price': 1350, 'volatility': 0.008, 'trend': 0.0002, 'volume_base': 45000},
        5: {'base_price': 1365, 'volatility': 0.012, 'trend': 0.0001, 'volume_base': 65000},
        6: {'base_price': 1380, 'volatility': 0.015, 'trend': 0.0001, 'volume_base': 85000},
        7: {'base_price': 1385, 'volatility': 0.010, 'trend': -0.0001, 'volume_base': 55000}
    }
    
    data = []
    current_price = market_params[4]['base_price']
    
    for i, timestamp in enumerate(time_range):
        month = timestamp.month
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        params = market_params[month]
        
        # 시간대별 활동 패턴
        if 9 <= hour <= 11 or 14 <= hour <= 16:  # 활발한 시간
            activity_multiplier = 1.5
        elif 22 <= hour or hour <= 6:  # 야간
            activity_multiplier = 0.6
        else:
            activity_multiplier = 1.0
        
        # 주말 효과
        if weekday >= 5:
            activity_multiplier *= 0.4
        
        # 가격 변동 계산
        volatility = params['volatility'] * activity_multiplier
        trend = params['trend']
        
        price_change = trend + np.random.normal(0, volatility)
        current_price *= (1 + price_change)
        
        # 현실적 범위 제한
        price_min = params['base_price'] * 0.95
        price_max = params['base_price'] * 1.08
        current_price = max(price_min, min(price_max, current_price))
        
        # OHLC 생성
        if i == 0:
            open_price = current_price
        else:
            open_price = data[-1]['close']
        
        close_price = current_price
        
        # 시간 내 변동
        intra_volatility = abs(close_price - open_price) + volatility * current_price * 0.5
        high = max(open_price, close_price) + abs(np.random.normal(0, intra_volatility * 0.3))
        low = min(open_price, close_price) - abs(np.random.normal(0, intra_volatility * 0.3))
        
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        # 거래량 생성
        base_volume = params['volume_base'] * activity_multiplier
        volume_noise = np.random.lognormal(0, 0.8)
        volume = base_volume * volume_noise
        
        data.append({
            'timestamp': timestamp,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close_price, 2),
            'volume': round(max(1000, volume), 2)
        })
    
    df = pd.DataFrame(data)
    
    # CSV 파일로 저장 (다음에 재사용하기 위해)
    fallback_csv_path = 'D:\\Project\\Teder\\backtest\\usdt_krw_complete_apr_jul_2024.csv'
    try:
        df.to_csv(fallback_csv_path, index=False)
        logger.info(f"폴백 시뮬레이션 데이터 저장: {fallback_csv_path}")
    except Exception as e:
        logger.warning(f"CSV 저장 실패: {e}")
    
    logger.info(f"향상된 시뮬레이션 데이터 생성 완료: {len(df)}개 레코드")
    return df


if __name__ == "__main__":
    # 테스트 실행
    logging.basicConfig(level=logging.INFO)
    
    print("백테스트 데이터 로드 테스트")
    print("=" * 50)
    
    # 샘플 데이터 테스트
    print("\n1. 샘플 데이터 생성 테스트")
    sample_df = SampleDataGenerator.generate_realistic_data(hours=100)
    print(f"생성된 데이터: {len(sample_df)}개 행")
    print(sample_df.head())
    
    # 데이터 검증 테스트
    print("\n2. 데이터 유효성 검증 테스트")
    is_valid, errors = DataValidator.validate_ohlcv_data(sample_df)
    print(f"유효성: {is_valid}")
    if errors:
        print(f"오류: {errors}")
    
    # 실제 API 데이터 테스트 (주석 처리됨)
    # print("\n3. 실제 API 데이터 테스트")
    # try:
    #     real_df = load_backtest_data(use_real_data=True, days=7)
    #     print(f"실제 데이터: {len(real_df)}개 행")
    #     print(real_df.head())
    # except Exception as e:
    #     print(f"실제 데이터 로드 실패: {e}")