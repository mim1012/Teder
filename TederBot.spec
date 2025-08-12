# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_live.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src'), ('config', 'config'), ('backtest', 'backtest')],
    hiddenimports=['pandas', 'numpy', 'requests', 'dotenv', 'rich', 'pandas_ta'],
    hookspath=[],
    hooksconfig={},
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
)
