"""
Config Manager - ini 파일에서 설정을 읽어오는 모듈
exe 패키징에서 외부 설정 파일 관리
"""

import os
import sys
import configparser
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 로깅 설정
logger = logging.getLogger(__name__)


class ConfigManager:
    """설정 파일 관리자 클래스"""
    
    def __init__(self, config_file: str = "config.ini"):
        """
        Args:
            config_file: 설정 파일명
        """
        # exe 실행 파일의 경로를 기준으로 config 파일 경로 설정
        if getattr(sys, 'frozen', False):
            # PyInstaller로 패키징된 경우
            self.app_dir = Path(sys.executable).parent
        else:
            # 개발 환경에서 실행되는 경우
            self.app_dir = Path(__file__).parent
            
        self.config_path = self.app_dir / config_file
        self.config = configparser.ConfigParser()
        
        # 기본 설정값 정의
        self.default_config = {
            'COINONE': {
                'ACCESS_TOKEN': '',
                'SECRET_KEY': '',
                'DRY_RUN': 'True',
                'LOG_LEVEL': 'INFO'
            },
            'TRADING': {
                'RSI_PERIOD': '14',
                'EMA_PERIOD': '20',
                'RSI_SLOPE_PERIODS_3': '3',
                'RSI_SLOPE_PERIODS_5': '5',
                'EMA_SLOPE_THRESHOLD_3': '2.0',
                'EMA_SLOPE_THRESHOLD_5': '1.5',
                'PROFIT_TARGET': '4.0',
                'MAX_HOLD_HOURS': '24',
                'RSI_OVERBOUGHT': '70.0'
            },
            'SYSTEM': {
                'CHECK_INTERVAL': '60',
                'LOG_FILE': 'logs/trading_bot.log',
                'MAX_LOG_SIZE': '10485760',  # 10MB
                'LOG_BACKUP_COUNT': '5'
            }
        }
        
        self._load_config()
    
    def _load_config(self):
        """설정 파일 로드"""
        try:
            if not self.config_path.exists():
                logger.warning(f"설정 파일이 없습니다: {self.config_path}")
                self._create_default_config()
                return
            
            self.config.read(self.config_path, encoding='utf-8')
            logger.info(f"설정 파일 로드 완료: {self.config_path}")
            
            # 필수 섹션 및 키 확인
            self._validate_config()
            
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """기본 설정 파일 생성"""
        try:
            # 기본 설정값으로 ConfigParser 초기화
            self.config.clear()
            for section, options in self.default_config.items():
                self.config.add_section(section)
                for key, value in options.items():
                    self.config.set(section, key, value)
            
            # 설정 파일 저장
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            logger.info(f"기본 설정 파일 생성: {self.config_path}")
            
        except Exception as e:
            logger.error(f"기본 설정 파일 생성 실패: {e}")
    
    def _validate_config(self):
        """설정 파일 유효성 검사"""
        missing_sections = []
        missing_keys = []
        
        for section, options in self.default_config.items():
            if not self.config.has_section(section):
                missing_sections.append(section)
                continue
                
            for key in options.keys():
                if not self.config.has_option(section, key):
                    missing_keys.append(f"{section}.{key}")
        
        # 누락된 섹션 추가
        for section in missing_sections:
            self.config.add_section(section)
            logger.warning(f"누락된 섹션 추가: {section}")
        
        # 누락된 키 추가
        for missing_key in missing_keys:
            section, key = missing_key.split('.', 1)
            default_value = self.default_config[section][key]
            self.config.set(section, key, default_value)
            logger.warning(f"누락된 키 추가: {missing_key} = {default_value}")
        
        # 변경사항이 있으면 저장
        if missing_sections or missing_keys:
            self.save_config()
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """설정값 조회"""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return str(fallback)
            return ""
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """정수형 설정값 조회"""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """실수형 설정값 조회"""
        try:
            return self.config.getfloat(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """불린형 설정값 조회"""
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def set(self, section: str, key: str, value: Any):
        """설정값 변경"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
    
    def save_config(self):
        """설정 파일 저장"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            logger.info("설정 파일 저장 완료")
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {e}")
    
    def get_api_config(self) -> Dict[str, str]:
        """API 관련 설정 조회"""
        return {
            'access_token': self.get('COINONE', 'ACCESS_TOKEN'),
            'secret_key': self.get('COINONE', 'SECRET_KEY'),
            'dry_run': self.getboolean('COINONE', 'DRY_RUN', True),
            'log_level': self.get('COINONE', 'LOG_LEVEL', 'INFO')
        }
    
    def get_trading_config(self) -> Dict[str, Any]:
        """거래 전략 설정 조회"""
        return {
            'rsi_period': self.getint('TRADING', 'RSI_PERIOD', 14),
            'ema_period': self.getint('TRADING', 'EMA_PERIOD', 20),
            'rsi_slope_periods': [
                self.getint('TRADING', 'RSI_SLOPE_PERIODS_3', 3),
                self.getint('TRADING', 'RSI_SLOPE_PERIODS_5', 5)
            ],
            'ema_slope_thresholds': [
                self.getfloat('TRADING', 'EMA_SLOPE_THRESHOLD_3', 2.0),
                self.getfloat('TRADING', 'EMA_SLOPE_THRESHOLD_5', 1.5)
            ],
            'profit_target': self.getfloat('TRADING', 'PROFIT_TARGET', 4.0),
            'max_hold_hours': self.getint('TRADING', 'MAX_HOLD_HOURS', 24),
            'rsi_overbought': self.getfloat('TRADING', 'RSI_OVERBOUGHT', 70.0)
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """시스템 설정 조회"""
        return {
            'check_interval': self.getint('SYSTEM', 'CHECK_INTERVAL', 60),
            'log_file': self.get('SYSTEM', 'LOG_FILE', 'logs/trading_bot.log'),
            'max_log_size': self.getint('SYSTEM', 'MAX_LOG_SIZE', 10485760),
            'log_backup_count': self.getint('SYSTEM', 'LOG_BACKUP_COUNT', 5)
        }
    
    def validate_api_keys(self) -> bool:
        """API 키 유효성 검사"""
        api_config = self.get_api_config()
        
        if not api_config['access_token']:
            logger.error("ACCESS_TOKEN이 설정되지 않았습니다")
            return False
            
        if not api_config['secret_key']:
            logger.error("SECRET_KEY가 설정되지 않았습니다")
            return False
            
        return True
    
    def get_logs_dir(self) -> Path:
        """로그 디렉토리 경로 반환"""
        logs_dir = self.app_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        return logs_dir


# 전역 설정 관리자 인스턴스
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """설정 관리자 인스턴스 반환"""
    return config_manager