#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TederBot Distribution Package Build Script
Protect code while distributing to users
"""

import os
import sys
import locale

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
import shutil
import py_compile
import zipfile
import json
import hashlib
from datetime import datetime
from pathlib import Path

class DistributionBuilder:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.dist_dir = self.root_dir / "dist_release"
        self.version = "1.0.0"
        self.build_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def clean_dist_dir(self):
        """배포 디렉토리 초기화"""
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.dist_dir.mkdir(parents=True)
        print(f"[OK] Created distribution directory: {self.dist_dir}")
        
    def compile_python_files(self):
        """Python 파일을 바이트코드로 컴파일"""
        print("\nCompiling Python files...")
        
        # 컴파일할 파일 목록
        py_files = [
            "main_live.py",
            "main_simple.py",
            "config/settings.py",
            "config/constants.py",
            # src 폴더의 모든 파일
            "src/__init__.py",
            "src/api/__init__.py",
            "src/api/auth.py",
            "src/api/coinone_client.py",
            "src/api/exceptions.py",
            "src/indicators/__init__.py",
            "src/indicators/base.py",
            "src/indicators/rsi.py",
            "src/indicators/ema.py",
            "src/strategy/__init__.py",
            "src/strategy/trading_strategy.py",
            "src/strategy/order_manager.py",
            "src/strategy/position_manager.py",
            "src/ui/__init__.py",
            "src/ui/monitor.py",
            "src/ui/dashboard.py",
            "src/ui/components.py",
            "src/utils/__init__.py",
            "src/utils/logger.py",
            # backtest 폴더 필수 파일
            "backtest/__init__.py",
            "backtest/backtest_engine.py",
            "backtest/data_loader.py",
            "backtest/performance_analyzer.py"
        ]
        
        compiled_dir = self.dist_dir / "bot"
        compiled_dir.mkdir(exist_ok=True)
        
        for py_file in py_files:
            if not Path(py_file).exists():
                print(f"  [SKIP] File not found: {py_file}")
                continue
                
            # 디렉토리 구조 유지
            rel_path = Path(py_file)
            target_dir = compiled_dir / rel_path.parent
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 컴파일
            source = self.root_dir / py_file
            target = target_dir / (rel_path.stem + ".pyc")
            
            try:
                py_compile.compile(
                    str(source),
                    cfile=str(target),
                    doraise=True,
                    optimize=2  # 최적화 레벨 2 (docstring 제거)
                )
                print(f"  [OK] Compiled: {py_file}")
            except Exception as e:
                print(f"  [ERROR] Failed to compile {py_file}: {e}")
                
    def create_runner_script(self):
        """실행 스크립트 생성"""
        runner_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TederBot Runner - Auto Trading Bot Runner"""

import sys
import os

# Add bot directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
bot_dir = os.path.join(script_dir, 'bot')
sys.path.insert(0, bot_dir)

# Set working directory
os.chdir(script_dir)

def main():
    try:
        # Create logs directory if not exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
            print("[INFO] Created logs directory")
            
        # Import compiled main module
        import main_live
        
        # Run main function
        if hasattr(main_live, 'main'):
            main_live.main()
        else:
            print("[ERROR] main() function not found in main_live module")
            sys.exit(1)
            
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Bot directory: {bot_dir}")
        print(f"Directory contents: {os.listdir(bot_dir) if os.path.exists(bot_dir) else 'Not found'}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {e}")
        print(f"Working directory: {os.getcwd()}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Runtime error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        runner_file = self.dist_dir / "run_bot.py"
        runner_file.write_text(runner_content, encoding='utf-8')
        print("[OK] Created runner script")
        
    def create_batch_files(self):
        """Windows 배치 파일 생성"""
        
        # 설치 배치 파일
        install_bat = '''@echo off
chcp 65001 >nul 2>&1
echo ================================
echo TederBot 설치 프로그램
echo ================================
echo.

REM Python 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되지 않았습니다.
    echo Python 3.8 이상을 설치해주세요.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python 확인 완료
echo.

REM 가상환경 생성
if not exist venv (
    echo 가상환경 생성 중...
    python -m venv venv
)

REM 가상환경 활성화
call venv\\Scripts\\activate.bat

REM 패키지 설치
echo 필요한 패키지 설치 중...
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo.
echo ================================
echo 설치 완료!
echo ================================
echo.
echo 다음 단계:
echo 1. .env.example을 .env로 복사
echo 2. .env 파일에 API 키 입력
echo 3. run.bat 실행
echo.
pause
'''
        
        # 실행 배치 파일
        run_bat = '''@echo off
chcp 65001 >nul 2>&1
echo ================================
echo TederBot 실행
echo ================================
echo.

REM .env 파일 확인
if not exist .env (
    echo [오류] .env 파일이 없습니다!
    echo .env.example을 .env로 복사하고 API 키를 입력하세요.
    pause
    exit /b 1
)

REM 가상환경 활성화
if exist venv\\Scripts\\activate.bat (
    call venv\\Scripts\\activate.bat
) else (
    echo [오류] 가상환경이 없습니다. install.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

REM 현재 디렉토리 확인
echo Current directory: %cd%
echo.

REM 봇 실행
echo Starting TederBot...
echo Press Ctrl+C to stop.
echo.
python run_bot.py

pause
'''
        
        (self.dist_dir / "install.bat").write_text(install_bat, encoding='utf-8')
        (self.dist_dir / "run.bat").write_text(run_bat, encoding='utf-8')
        print("[OK] Created batch files")
        
    def copy_required_files(self):
        """필요한 파일 복사"""
        files_to_copy = [
            "requirements.txt",
            ".env.example",
            "README.md"
        ]
        
        for file in files_to_copy:
            source = self.root_dir / file
            if source.exists():
                shutil.copy2(source, self.dist_dir)
                print(f"[OK] Copied: {file}")
                
        # CSV 데이터 파일 복사 (필요한 경우)
        data_files = [
            "backtest/real_usdt_krw_apr_jul_2024.csv",
            "backtest/usdt_krw_complete_apr_jul_2024.csv"
        ]
        
        data_dir = self.dist_dir / "bot" / "backtest"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        for data_file in data_files:
            source = self.root_dir / data_file
            if source.exists():
                shutil.copy2(source, data_dir)
                print(f"[OK] Copied data file: {data_file}")
                
    def create_user_guide(self):
        """사용자 가이드 생성"""
        guide_content = f'''# TederBot v{self.version} 사용 가이드

## 시스템 요구사항
- Windows 10 이상
- Python 3.8 이상
- 인터넷 연결

## 설치 방법

1. **Python 설치 확인**
   - 명령 프롬프트에서: `python --version`
   - 없다면: https://www.python.org/downloads/

2. **봇 설치**
   - `install.bat` 실행
   - 자동으로 필요한 패키지 설치

3. **API 설정**
   - `.env.example`을 `.env`로 복사
   - 메모장으로 `.env` 열기
   - 코인원 API 키 입력:
     ```
     COINONE_ACCESS_TOKEN=여기에_액세스_토큰
     COINONE_SECRET_KEY=여기에_시크릿_키
     DRY_RUN=true  # 모의거래(true) / 실거래(false)
     ```

4. **실행**
   - `run.bat` 더블클릭
   - 또는 명령 프롬프트에서: `python run_bot.py`

## 주의사항

⚠️ **실거래 전 필수 확인**
- DRY_RUN=true로 먼저 테스트
- API 키 권한 확인 (거래 권한 필요)
- 충분한 KRW 잔고 확인

## 문제 해결

### "Python이 설치되지 않았습니다"
→ Python 3.8+ 설치: https://www.python.org

### "모듈을 찾을 수 없습니다"
→ `install.bat` 재실행

### API 오류
→ `.env` 파일의 API 키 확인

## 지원

- 빌드 시간: {self.build_time}
- 버전: {self.version}

---
© 2024 TederBot. All rights reserved.
'''
        (self.dist_dir / "사용가이드.txt").write_text(guide_content, encoding='utf-8')
        print("[OK] Created user guide")
        
    def create_config_template(self):
        """설정 템플릿 생성"""
        config = {
            "version": self.version,
            "build_time": self.build_time,
            "settings": {
                "max_position_size": 1000000,
                "stop_loss_percent": 5,
                "take_profit_won": 4,
                "rsi_period": 14,
                "ema_period": 20
            }
        }
        
        config_file = self.dist_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("[OK] Created config template")
        
    def create_license_file(self):
        """라이센스 파일 생성"""
        license_content = '''TederBot 라이센스

본 소프트웨어는 라이센스가 부여된 사용자에게만 제공됩니다.

1. 사용 제한
   - 개인 사용만 허용
   - 재배포 금지
   - 리버스 엔지니어링 금지

2. 면책 조항
   - 투자 손실에 대한 책임 없음
   - 사용자 본인 책임하에 사용

3. 지원
   - 이메일: support@tederbot.com
   - 라이센스 키: TRIAL-{}-{}

© 2024 TederBot. All rights reserved.
'''.format(
            hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8].upper(),
            self.build_time
        )
        
        (self.dist_dir / "LICENSE.txt").write_text(license_content, encoding='utf-8')
        print("[OK] Created license file")
        
    def create_zip_package(self):
        """ZIP 패키지 생성"""
        zip_name = f"TederBot_v{self.version}_{self.build_time}.zip"
        zip_path = self.root_dir / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.dist_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.dist_dir)
                    zipf.write(file_path, arcname)
                    
        # 파일 크기 확인
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"\n[OK] Distribution package created!")
        print(f"  File: {zip_name}")
        print(f"  Size: {size_mb:.2f} MB")
        
        return zip_path
        
    def build(self):
        """전체 빌드 프로세스"""
        print("=" * 50)
        print(f"TederBot v{self.version} Distribution Package Build")
        print("=" * 50)
        
        try:
            self.clean_dist_dir()
            self.compile_python_files()
            self.create_runner_script()
            self.create_batch_files()
            self.copy_required_files()
            self.create_user_guide()
            self.create_config_template()
            self.create_license_file()
            zip_path = self.create_zip_package()
            
            print("\n" + "=" * 50)
            print("Build Success!")
            print("=" * 50)
            print(f"\nDistribution file: {zip_path}")
            print("\nPlease deliver this ZIP file to users.")
            print("The code is compiled and protected.")
            
        except Exception as e:
            print(f"\n[ERROR] Build failed: {e}")
            sys.exit(1)

def main():
    """메인 함수"""
    builder = DistributionBuilder()
    builder.build()

if __name__ == "__main__":
    main()