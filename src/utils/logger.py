"""
로깅 설정 모듈
"""
import sys
from pathlib import Path
from loguru import logger
from config.settings import MONITORING_CONFIG

def setup_logger(name: str = "trading_bot", debug: bool = False):
    """로거 설정"""
    # 기존 핸들러 제거
    logger.remove()
    
    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 로그 레벨 설정
    log_level = "DEBUG" if debug else MONITORING_CONFIG.get('log_level', 'INFO')
    
    # 콘솔 출력 설정
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # 파일 출력 설정
    logger.add(
        log_dir / "trading_bot.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation=MONITORING_CONFIG.get('max_log_size', '10MB'),
        retention=MONITORING_CONFIG.get('backup_count', 5),
        encoding="utf-8"
    )
    
    # 에러 로그 별도 파일
    logger.add(
        log_dir / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="1 day",
        retention="30 days",
        encoding="utf-8"
    )
    
    logger.info(f"로거 초기화 완료 (레벨: {log_level})")
    return logger