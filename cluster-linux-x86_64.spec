# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/home/ficus-pro/Documents/ai-cluster-auto-connect/cluster.py'],
    pathex=[],
    binaries=[],
    datas=[('/home/ficus-pro/Documents/ai-cluster-auto-connect/src/common', 'common'), ('/home/ficus-pro/Documents/ai-cluster-auto-connect/src/root', 'root'), ('/home/ficus-pro/Documents/ai-cluster-auto-connect/src/worker', 'worker'), ('/home/ficus-pro/Documents/ai-cluster-auto-connect/src/gui', 'gui')],
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
