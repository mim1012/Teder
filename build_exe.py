"""
PyInstaller EXE 빌드 스크립트
코인원 자동매매 봇을 exe 파일로 패키징
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 빌드 설정
BUILD_CONFIG = {
    'app_name': 'TederBot',
    'main_script': 'main_executable.py',
    'icon_file': None,  # 아이콘 파일이 있다면 여기에 경로 지정
    'console': True,    # 콘솔 창 표시 여부
    'onefile': True,    # 단일 파일로 빌드할지 여부
    'clean_build': True,  # 빌드 전 기존 빌드 파일 삭제
}

# 포함할 추가 데이터 파일들
ADDITIONAL_DATA = [
    ('config.ini.template', '.'),  # 설정 파일 템플릿
]

# 포함할 패키지들 (자동 감지되지 않을 수 있는 패키지)
HIDDEN_IMPORTS = [
    'pandas',
    'pandas_ta', 
    'numpy',
    'requests',
    'urllib3',
    'certifi',
    'configparser',
    'logging.handlers',
    'datetime',
    'json',
    'hashlib',
    'hmac',
    'base64',
    'decimal',
    'enum',
]

def clean_build_dirs():
    """빌드 디렉토리 정리"""
    build_dirs = ['build', 'dist', '__pycache__']
    spec_files = [f'{BUILD_CONFIG["app_name"]}.spec']
    
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f"기존 {dir_name} 디렉토리 삭제 중...")
            shutil.rmtree(dir_name)
    
    for spec_file in spec_files:
        if os.path.exists(spec_file):
            print(f"기존 {spec_file} 파일 삭제 중...")
            os.remove(spec_file)

def create_spec_file():
    """PyInstaller spec 파일 생성"""
    
    # 숨겨진 import 문자열 생성
    hidden_imports_str = "'" + "',\n    '".join(HIDDEN_IMPORTS) + "'"
    
    # 추가 데이터 문자열 생성
    data_files_str = ""
    if ADDITIONAL_DATA:
        data_list = [f"('{src}', '{dst}')" for src, dst in ADDITIONAL_DATA]
        data_files_str = ",\n    ".join(data_list)
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['{BUILD_CONFIG["main_script"]}'],
    pathex=[],
    binaries=[],
    datas=[
        {data_files_str}
    ],
    hiddenimports=[
        {hidden_imports_str}
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='{BUILD_CONFIG["app_name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={str(BUILD_CONFIG["console"]).lower()},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {f'icon="{BUILD_CONFIG["icon_file"]}",' if BUILD_CONFIG["icon_file"] else ""}
)
'''

    spec_file_path = f'{BUILD_CONFIG["app_name"]}.spec'
    with open(spec_file_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"Spec 파일 생성: {spec_file_path}")
    return spec_file_path

def install_dependencies():
    """필수 의존성 패키지 설치 확인"""
    required_packages = [
        'pyinstaller',
        'pandas',
        'pandas-ta',
        'numpy',
        'requests',
        'python-dotenv',
        'rich'
    ]
    
    print("필수 의존성 패키지 확인 중...")
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} - 설치됨")
        except ImportError:
            print(f"✗ {package} - 설치되지 않음")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✓ {package} - 설치 완료")
            except subprocess.CalledProcessError:
                print(f"✗ {package} - 설치 실패")
                return False
    
    return True

def build_exe():
    """EXE 파일 빌드"""
    print(f"\n{BUILD_CONFIG['app_name']} EXE 빌드 시작...")
    
    # 1. 의존성 확인
    if not install_dependencies():
        print("의존성 설치 실패. 빌드를 중단합니다.")
        return False
    
    # 2. 기존 빌드 파일 정리
    if BUILD_CONFIG['clean_build']:
        clean_build_dirs()
    
    # 3. spec 파일 생성
    spec_file = create_spec_file()
    
    # 4. PyInstaller 실행
    cmd = [
        'pyinstaller',
        '--clean',  # 임시 파일 정리
        spec_file
    ]
    
    print(f"PyInstaller 명령어: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        print("PyInstaller 실행 성공!")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("PyInstaller 실행 실패!")
        print(f"오류 코드: {e.returncode}")
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        return False
    
    # 5. 빌드 결과 확인
    exe_path = Path('dist') / f'{BUILD_CONFIG["app_name"]}.exe'
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
        print(f"\n✓ EXE 파일 빌드 성공!")
        print(f"파일 경로: {exe_path.absolute()}")
        print(f"파일 크기: {file_size:.2f} MB")
        return True
    else:
        print("✗ EXE 파일을 찾을 수 없습니다.")
        return False

def create_distribution_package():
    """배포용 패키지 생성"""
    print("\n배포용 패키지 생성 중...")
    
    dist_dir = Path('dist')
    if not dist_dir.exists():
        print("dist 디렉토리가 없습니다.")
        return False
    
    # config.ini.template을 config.ini로 복사
    template_path = Path('config.ini.template')
    if template_path.exists():
        config_path = dist_dir / 'config.ini'
        shutil.copy2(template_path, config_path)
        print(f"설정 파일 복사: {config_path}")
    
    # README_dist.txt를 README.txt로 복사
    readme_dist_path = Path('README_dist.txt')
    if readme_dist_path.exists():
        readme_path = dist_dir / 'README.txt'
        shutil.copy2(readme_dist_path, readme_path)
        print(f"사용 설명서 복사: {readme_path}")
    
    # logs 디렉토리 생성
    logs_dir = dist_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    print(f"로그 디렉토리 생성: {logs_dir}")
    
    # .gitkeep 파일 생성 (빈 디렉토리 유지용)
    gitkeep_path = logs_dir / '.gitkeep'
    gitkeep_path.touch()
    
    print("배포용 패키지 생성 완료!")
    return True

def main():
    """메인 함수"""
    print("="*70)
    print("TEDER BOT EXE 빌드 스크립트")
    print("="*70)
    
    # 현재 디렉토리가 프로젝트 루트인지 확인
    if not Path(BUILD_CONFIG['main_script']).exists():
        print(f"오류: {BUILD_CONFIG['main_script']} 파일을 찾을 수 없습니다.")
        print("프로젝트 루트 디렉토리에서 실행해주세요.")
        return
    
    # EXE 빌드
    if build_exe():
        # 배포용 패키지 생성
        create_distribution_package()
        
        print("\n" + "="*70)
        print("빌드 완료!")
        print(f"실행 파일: dist/{BUILD_CONFIG['app_name']}.exe")
        print("설정 파일: dist/config.ini")
        print("로그 폴더: dist/logs/")
        print("="*70)
        
        print("\n사용 방법:")
        print("1. dist/config.ini 파일을 편집하여 API 키를 설정하세요")
        print("2. TederBot.exe를 실행하세요")
        print("3. 로그는 logs/ 폴더에 저장됩니다")
        
    else:
        print("\n빌드 실패!")
        print("오류를 확인하고 다시 시도해주세요.")

if __name__ == "__main__":
    main()