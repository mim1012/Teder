"""
코인원 API 관련 커스텀 예외 클래스들
"""

class CoinoneAPIError(Exception):
    """코인원 API 기본 예외 클래스"""
    def __init__(self, message, error_code=None, status_code=None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class AuthenticationError(CoinoneAPIError):
    """인증 관련 예외"""
    pass

class RateLimitError(CoinoneAPIError):
    """API 호출 한도 초과 예외"""
    pass

class NetworkError(CoinoneAPIError):
    """네트워크 연결 관련 예외"""
    pass

class ValidationError(CoinoneAPIError):
    """요청 데이터 검증 예외"""
    pass

class InsufficientBalanceError(CoinoneAPIError):
    """잔고 부족 예외"""
    pass

class OrderError(CoinoneAPIError):
    """주문 관련 예외"""
    pass

class ServerError(CoinoneAPIError):
    """서버 오류 예외"""
    pass

# 응답 코드별 예외 매핑
ERROR_CODE_MAPPING = {
    10: AuthenticationError("잘못된 access token입니다."),
    11: AuthenticationError("잘못된 서명입니다."),
    12: AuthenticationError("잘못된 nonce입니다."),
    13: AuthenticationError("API 권한이 없습니다."),
    20: ValidationError("잘못된 요청 파라미터입니다."),
    21: ValidationError("잘못된 통화 코드입니다."),
    22: ValidationError("잘못된 주문 유형입니다."),
    23: ValidationError("잘못된 주문량입니다."),
    24: ValidationError("잘못된 주문 가격입니다."),
    30: InsufficientBalanceError("잔고가 부족합니다."),
    31: OrderError("주문을 찾을 수 없습니다."),
    32: OrderError("이미 취소된 주문입니다."),
    33: OrderError("이미 체결된 주문입니다."),
    40: RateLimitError("API 호출 한도를 초과했습니다."),
    50: ServerError("내부 서버 오류입니다."),
    51: ServerError("거래소 점검 중입니다."),
    52: ServerError("거래 일시 중단입니다."),
}

def get_exception_from_code(error_code, message=None):
    """에러 코드에 따른 적절한 예외 반환"""
    if error_code in ERROR_CODE_MAPPING:
        exception_class = type(ERROR_CODE_MAPPING[error_code])
        return exception_class(message or ERROR_CODE_MAPPING[error_code].message, error_code)
    return CoinoneAPIError(message or f"알 수 없는 에러 (코드: {error_code})", error_code)