# -*- mode: python ; coding: utf-8 -*-
# PySide6 移植版 spec 檔案

import os

def collect_images():
    """收集 images/ 下所有圖片，排除 mapleworld 子目錄"""
    result = []
    for root, dirs, files in os.walk('images'):
        dirs[:] = [d for d in dirs if not (os.path.normpath(root) == 'images' and d == 'mapleworld')]
        for f in files:
            src = os.path.join(root, f)
            result.append((src, root))
    return result

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        *collect_images(),          # images/ 排除 mapleworld
        ('config.json',         '.'),
        ('icon.ico',            '.'),
        ('icon.png',            '.'),  # V2 sidebar logo runtime 用
        # profiles/ 不打包：第一次啟動由 AppCoreMixin 用 factory default 自建
        # 避免開發者個人 profile 修改流入發布版
        # overlays/ 打包：作為預設浮動圖內容（OverlayManager 找不到 user_data_path
        # 時會 fallback 到 resource_path 載入 bundled 預設）
        ('overlays',            'overlays'),
        ('version.py',          '.'),
        ('update_launcher.bat', '.'),
        ('update_launcher.ps1', '.'),
        # V2 lucide SVG 圖示（src/ui_v2/lucide.py 用 __file__ 解析此路徑）
        ('src/ui_v2/icons',     'src/ui_v2/icons'),
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
        'PIL.PngImagePlugin',
        'PIL.WebPImagePlugin',
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
    name='skill_tracker',
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
    name='skill_tracker',
)
