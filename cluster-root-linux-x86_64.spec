# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/home/ficus-pro/Desktop/ai-cluster-auto-connect/src/root/main.py'],
    pathex=[],
    binaries=[],
    datas=[('/home/ficus-pro/Desktop/ai-cluster-auto-connect/src/common', 'common')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='cluster-root-linux-x86_64',
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
