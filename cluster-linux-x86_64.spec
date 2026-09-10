# -*- mode: python ; coding: utf-8 -*-
import os

base_dir = os.path.abspath('.')

a = Analysis(
    [os.path.join(base_dir, 'cluster.py')],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(base_dir, 'src/common'), 'common'),
        (os.path.join(base_dir, 'src/root'), 'root'),
        (os.path.join(base_dir, 'src/worker'), 'worker'),
        (os.path.join(base_dir, 'src/gui'), 'gui')
    ],
    hiddenimports=['PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'zeroconf', 'psutil', 'yaml', 'rich', 'rich.console', 'rich.table', 'rich.panel', 'rich.layout', 'rich.text', 'rich.live', 'rich.columns'],
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
    name='cluster-linux-x86_64',
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
