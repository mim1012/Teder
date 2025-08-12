# USDT/KRW 자동매매 전략 개선 계획

## 현재 상황 요약

### 백테스트 결과 (2024년 4-7월)
- **최초 결과**: -53.69% 손실 (289회 거래)
- **임계값 최적화 후**: -31.18% 손실 (124회 거래)
- **개선폭**: 22.5%p, 그러나 여전히 손실

### 기울기 계산 수정
```python
# 올바른 계산식 적용
기울기 = (마지막값 - 처음값) / (봉 수 - 1)
```

## 발견된 핵심 문제점

### 1. 전략 구조의 한계
- **과도한 단순성**: RSI/EMA 기울기만으로 판단
- **시장 맥락 부재**: 추세장/횡보장 구분 없음
- **위험 관리 부족**: 명확한 손절선 없음

### 2. 매수/매도 불균형
- **익절**: +4원 (약 0.3%)
- **손절**: 시간/기술적 신호에만 의존
- **결과**: 평균 손실 > 평균 수익

### 3. 임계값 문제
- **원래 설정**: 너무 낮아 과매매 발생
- **높은 설정**: 거래 감소하나 여전히 손실

## 단계별 개선 방안

### 1단계: 즉시 적용 가능한 개선 (1주)

#### A. 손절선 추가
```python
# 현재: 손절선 없음
# 개선안:
- 고정 손절: 평균매수가 - 3원
- 또는 ATR 기반 동적 손절
```

#### B. 추가 필터 조건
```python
# 현재: RSI/EMA 기울기만 확인
# 개선안:
- 거래량 증가 조건 추가
- 변동성 필터 (ATR 기반)
- 상위 시간대 추세 확인
```

#### C. 임계값 동적 조정
```python
# 현재: 고정 임계값
# 개선안:
- 시장 변동성에 따라 임계값 조정
- 최근 N봉의 평균 변화량 기준
```

### 2단계: 전략 재설계 (2-4주)

#### A. 다중 시간대 분석
```python
# 1시간봉 + 4시간봉 조합
- 4시간봉: 전체 추세 판단
- 1시간봉: 진입 타이밍
```

#### B. 시장 상태 분류
```python
# 시장 상태별 다른 전략
- 상승 추세: 추세 추종
- 하락 추세: 매수 자제
- 횡보: 범위 거래
```

#### C. 리스크 관리 강화
```python
# 포지션 사이징
- 켈리 공식 적용
- 최대 손실 제한 (일/주/월)
- 연속 손실 시 거래 중단
```

### 3단계: 고급 기법 도입 (1-3개월)

#### A. 기계학습 적용
- 과거 패턴 학습
- 매수/매도 신호 예측
- 실시간 파라미터 최적화

#### B. 포트폴리오 다변화
- 다른 암호화폐 추가
- 상관관계 낮은 전략 조합
- 리스크 분산

## 구체적 구현 예시

### 개선된 매수 조건
```python
def improved_buy_conditions(df, idx):
    # 1. 기존 기울기 조건 (임계값 상향)
    rsi_slope_3 = df.iloc[idx]['rsi_slope_3']
    rsi_slope_5 = df.iloc[idx]['rsi_slope_5']
    ema_slope_3 = df.iloc[idx]['ema_slope_3']
    ema_slope_5 = df.iloc[idx]['ema_slope_5']
    
    if not (rsi_slope_3 > 0.5 and rsi_slope_5 > 0.3):
        return False
    
    if not (ema_slope_3 >= 2.0 and ema_slope_5 >= 1.5):
        return False
    
    # 2. 추가 필터: 거래량
    volume_ma = df['volume'].rolling(20).mean()
    if df.iloc[idx]['volume'] < volume_ma.iloc[idx] * 1.2:
        return False
    
    # 3. 추가 필터: RSI 범위
    current_rsi = df.iloc[idx]['rsi']
    if current_rsi < 30 or current_rsi > 70:
        return False
    
    # 4. 추가 필터: 변동성
    atr = calculate_atr(df, 14)
    if atr.iloc[idx] > df.iloc[idx]['close'] * 0.02:  # 2% 이상 변동성
        return False
    
    return True
```

### 개선된 매도 조건
```python
def improved_sell_conditions(df, idx, position):
    current_price = df.iloc[idx]['close']
    
    # 1. 익절 (동적)
    atr = calculate_atr(df, 14)
    profit_target = position.avg_price + (atr.iloc[idx] * 2)  # 2 ATR
    if current_price >= profit_target:
        return True, "익절"
    
    # 2. 손절 (고정 + 트레일링)
    stop_loss = position.avg_price - 5  # 5원 손절
    if current_price <= stop_loss:
        return True, "손절"
    
    # 3. 트레일링 스톱
    if position.max_price:
        trailing_stop = position.max_price - (atr.iloc[idx] * 1.5)
        if current_price <= trailing_stop:
            return True, "트레일링스톱"
    
    # 4. 기존 조건들...
    return False, ""
```

## 예상 개선 효과

### 단기 (1-2주)
- 손실 감소: -31% → -15~20%
- 승률 개선: 38% → 45-50%
- 리스크 감소: 최대 낙폭 제한

### 중기 (1-2개월)
- 손익분기점 도달: -15% → 0~5%
- 안정적 수익: 월 2-5%
- 거래 최적화: 질 높은 거래만 선별

### 장기 (3-6개월)
- 지속 가능한 수익: 월 5-10%
- 시장 적응력: 다양한 시장 상황 대응
- 확장 가능성: 다른 거래쌍 추가

## 다음 단계 권장사항

1. **즉시**: 손절선 추가 및 임계값 조정
2. **1주 내**: 추가 필터 구현 및 백테스트
3. **2주 내**: 개선된 전략으로 모의 거래
4. **1개월 내**: 소액 실전 테스트
5. **3개월 내**: 전체 시스템 최적화

현재 시스템의 **기술적 기반은 훌륭**하므로, 전략 개선에 집중하면 수익성 있는 자동매매 시스템 구축이 가능합니다.