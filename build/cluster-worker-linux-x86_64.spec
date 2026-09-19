# -*- mode: python ; coding: utf-8 -*-
import os

base_dir = os.path.abspath('.')

a = Analysis(
    [os.path.join(base_dir, 'src/worker/main.py')],
    pathex=[],
    binaries=[],
    datas=[(os.path.join(base_dir, 'src/common'), 'common')],
    hiddenimports=['zeroconf', 'psutil', 'yaml', 'rich'],
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
    name='cluster-worker-linux-x86_64',
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
