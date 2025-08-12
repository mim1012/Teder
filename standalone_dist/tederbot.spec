# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['tederbot_main.py'],
    pathex=['D:\Project\Teder\standalone_dist'],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('config', 'config'),
        ('backtest', 'backtest'),
    ],
    hiddenimports=[
        'pandas',
        'numpy',
        'requests',
        'dotenv',
        'rich',
        'pandas_ta',
        'src.api.coinone_client',
        'src.indicators.rsi',
        'src.indicators.ema',
        'backtest.backtest_engine',
        'config.settings',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TederBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
