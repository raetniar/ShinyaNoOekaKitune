# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

datas = (
    collect_data_files('customtkinter') +
    collect_data_files('whisper') +
    copy_metadata('imageio') +
    copy_metadata('moviepy') +
    copy_metadata('openai-whisper') +
    copy_metadata('torch')
)

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'customtkinter',
        'moviepy.editor',
        'imageio_ffmpeg',
        'whisper',
        'whisper.audio',
        'torch',
        'cv2',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.ImageTk',
        'utils',
        'audio',
        'video',
        'config',
        'app'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'IPython', 'notebook'],
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
    name='きりぬきつーる',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/icon.ico' if os.path.exists('src/icon.ico') else None,
)
