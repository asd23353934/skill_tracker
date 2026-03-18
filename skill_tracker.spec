# -*- mode: python ; coding: utf-8 -*-
# PySide6 移植版 spec 檔案

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('images',              'images'),
        ('config.json',         '.'),
        ('icon.ico',            '.'),
        ('profiles',            'profiles'),
        ('version.py',          '.'),
        ('update_launcher.bat', '.'),
        ('update_launcher.ps1', '.'),
    ],
    hiddenimports=[
        # pynput Windows 後端
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        # PySide6 核心模組
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtXml',
        # Pillow
        'PIL._imagingtk',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFilter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'customtkinter',
        'tkinter',
        '_tkinter',
        'pygame',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='技能追蹤器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='技能追蹤器',
)
