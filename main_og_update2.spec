# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_og_update2.py'],
    pathex=[],
    binaries=[],
    datas=[('images/photo_button.png', 'images'), ('images/video_button.png', 'images'), ('images/stop_button.png', 'images'), ('images/pause_button.png', 'images'), ('images/resume_button.png', 'images'), ('images/gallery_button.png', 'images')],
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
    name='main_og_update2',
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
