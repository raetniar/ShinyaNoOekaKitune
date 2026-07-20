from PyInstaller.utils.hooks import copy_metadata, collect_data_files

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src')] + copy_metadata('imageio') + copy_metadata('moviepy') + collect_data_files('whisper'),
    hiddenimports=['moviepy.editor', 'imageio_ffmpeg', 'whisper', 'whisper.audio'],
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
    icon=['src\\icon.ico'],
)
