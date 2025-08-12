# 코드 보호 배포 가이드

## 배포 방법별 비교

### 1. PyInstaller (실행파일) ⭐⭐⭐⭐
**장점**: 단일 exe 파일, 설치 불필요
**단점**: 리버싱 가능, 파일 크기 큼
**보안 수준**: 중간

### 2. Docker 이미지 ⭐⭐⭐⭐⭐
**장점**: 환경 포함, 코드 숨김 가능
**단점**: Docker 필요
**보안 수준**: 높음

### 3. Cython 컴파일 ⭐⭐⭐⭐
**장점**: C 코드로 컴파일, 속도 향상
**단점**: 복잡한 빌드 과정
**보안 수준**: 높음

### 4. 클라우드 API 서비스 ⭐⭐⭐⭐⭐
**장점**: 완벽한 코드 보호
**단점**: 서버 비용, 네트워크 의존
**보안 수준**: 최고

## 방법 1: PyInstaller 실행파일 생성

### 설치
```bash
pip install pyinstaller pyarmor
```

### build_exe.bat 생성
```batch
@echo off
echo Building Trading Bot Executable...

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM PyInstaller로 빌드
pyinstaller --onefile ^
    --windowed ^
    --icon=icon.ico ^
    --name=TederBot ^
    --hidden-import=pandas ^
    --hidden-import=numpy ^
    --hidden-import=requests ^
    --add-data=".env.example;." ^
    main_live.py

echo Build complete! Check dist/TederBot.exe
pause
```

### 난독화 추가 (PyArmor)
```bash
# 난독화 후 빌드
pyarmor pack -e "--onefile --windowed" main_live.py
```

## 방법 2: Docker 이미지 배포

### Dockerfile.dist (배포용)
```dockerfile
FROM python:3.9-slim
WORKDIR /app

# 의존성만 복사
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 컴파일된 파이썬 파일만 복사
COPY *.pyc ./
COPY config/*.pyc ./config/
COPY strategies/*.pyc ./strategies/

# 환경변수 템플릿
COPY .env.example .

# 실행
CMD ["python", "main_live.pyc"]
```

### 컴파일 및 이미지 빌드
```bash
# Python 파일 컴파일
python -m compileall -b .

# Docker 이미지 빌드
docker build -f Dockerfile.dist -t tederbot:latest .

# 이미지 저장
docker save tederbot:latest > tederbot.tar
```

### 사용자 배포 스크립트
```batch
@echo off
echo Loading TederBot...
docker load < tederbot.tar
docker run -d --name tederbot --env-file .env tederbot:latest
```

## 방법 3: Cython 컴파일

### setup.py 생성
```python
from setuptools import setup
from Cython.Build import cythonize
import glob

# 모든 .py 파일 찾기
python_files = glob.glob("**/*.py", recursive=True)
exclude_files = ["setup.py", "build_dist.py"]
files_to_compile = [f for f in python_files if f not in exclude_files]

setup(
    name="TederBot",
    ext_modules=cythonize(
        files_to_compile,
        compiler_directives={'language_level': "3"}
    ),
    zip_safe=False,
)
```

### 빌드 스크립트
```bash
# Cython 설치
pip install cython

# 컴파일
python setup.py build_ext --inplace

# .py 파일 삭제, .pyd/.so 파일만 남김
find . -name "*.py" -not -name "main.py" -delete
```

## 방법 4: 웹 API 서비스

### 서버 구조
```
서버 (당신이 관리)
├── 실제 거래 로직
├── API 인증
└── 사용자별 설정

클라이언트 (사용자)
├── API 키 입력
├── 설정 UI
└── 모니터링
```

### 간단한 클라이언트
```python
# client.py (사용자에게 제공)
import requests

class TederBotClient:
    def __init__(self, api_key, server_url):
        self.api_key = api_key
        self.server_url = server_url
    
    def start_trading(self):
        response = requests.post(
            f"{self.server_url}/start",
            headers={"X-API-Key": self.api_key}
        )
        return response.json()
    
    def get_status(self):
        response = requests.get(
            f"{self.server_url}/status",
            headers={"X-API-Key": self.api_key}
        )
        return response.json()
```

## 방법 5: 하이브리드 (추천) ⭐⭐⭐⭐⭐

### 구조
1. **핵심 로직**: 서버 API
2. **UI/모니터링**: PyInstaller exe
3. **인증**: 라이센스 키

### license_manager.py
```python
import hashlib
import requests
from datetime import datetime

class LicenseManager:
    def __init__(self):
        self.server = "https://your-server.com/api"
    
    def validate_license(self, license_key):
        """라이센스 키 검증"""
        response = requests.post(
            f"{self.server}/validate",
            json={"key": license_key}
        )
        return response.json()["valid"]
    
    def get_trading_config(self, license_key):
        """서버에서 거래 설정 받기"""
        response = requests.get(
            f"{self.server}/config",
            headers={"X-License": license_key}
        )
        return response.json()
```

## 빠른 배포 스크립트

### build_distribution.py
```python
import os
import shutil
import py_compile
import zipfile

def build_distribution():
    """배포 패키지 생성"""
    
    # 1. 디렉토리 생성
    dist_dir = "dist_package"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # 2. 필요한 파일만 복사
    files_to_include = [
        "main_live.py",
        "config/",
        "strategies/",
        "requirements.txt",
        ".env.example",
        "run_live_final.bat"
    ]
    
    for item in files_to_include:
        if os.path.isdir(item):
            shutil.copytree(item, f"{dist_dir}/{item}")
        else:
            shutil.copy2(item, dist_dir)
    
    # 3. Python 파일 컴파일
    for root, dirs, files in os.walk(dist_dir):
        for file in files:
            if file.endswith('.py'):
                py_file = os.path.join(root, file)
                pyc_file = py_file + 'c'
                py_compile.compile(py_file, pyc_file)
                os.remove(py_file)  # 원본 삭제
    
    # 4. ZIP 압축
    with zipfile.ZipFile('TederBot_v1.0.zip', 'w') as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_dir)
                zipf.write(file_path, arcname)
    
    print("Distribution package created: TederBot_v1.0.zip")

if __name__ == "__main__":
    build_distribution()
```

## 사용자 제공 패키지

### 최종 배포 구조
```
TederBot_v1.0.zip
├── TederBot.exe (또는 .pyc 파일들)
├── config/
│   └── settings.json
├── .env.example
├── README.txt
├── install.bat
└── license.key
```

### 사용자 설치 가이드 (README.txt)
```
1. .env.example을 .env로 복사
2. 코인원 API 키 입력
3. install.bat 실행
4. TederBot.exe 실행
```

## 보안 강화 팁

1. **코드 분리**
   - 핵심 로직: 서버
   - UI/설정: 클라이언트

2. **라이센스 시스템**
   - MAC 주소 바인딩
   - 만료일 설정
   - 온라인 검증

3. **로그 암호화**
   - 민감한 정보 마스킹
   - 로그 파일 암호화

4. **API 키 보호**
   - 환경변수 사용
   - 암호화 저장

## 추천 배포 방식

### 개인 사용자
→ **Docker 이미지** (쉬운 설치, 코드 보호)

### 상업용 배포
→ **하이브리드** (서버 API + 클라이언트 exe)

### 오픈소스
→ **GitHub + Docker Hub** (투명성)

---

**선택하신 방식에 따라 구체적인 구현을 도와드리겠습니다.**