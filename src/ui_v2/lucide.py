"""
Lucide SVG 圖示載入器
讀取 src/ui_v2/icons/*.svg，替換 currentColor → 實際色，回傳 QPixmap / QIcon
"""

import os
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap, QPainter, QIcon, QGuiApplication
from PySide6.QtCore import Qt, QByteArray

ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
_cache: dict = {}


def _device_pixel_ratio() -> float:
    """取得目前主螢幕的 device pixel ratio（high-DPI 支援）"""
    screen = QGuiApplication.primaryScreen()
    return float(screen.devicePixelRatio()) if screen is not None else 1.0


def lucide_pixmap(name: str, color: str = "#ffffff",
                  size: int = 16, stroke: float = 2.0) -> QPixmap:
    dpr = _device_pixel_ratio()
    key = (name, color, size, stroke, dpr)
    if key in _cache:
        return _cache[key]

    path = os.path.join(ICON_DIR, f"{name}.svg")
    with open(path, "r", encoding="utf-8") as f:
        svg = f.read()
    svg = svg.replace("currentColor", color)
    if stroke != 2.0:
        svg = svg.replace('stroke-width="2"', f'stroke-width="{stroke}"')

    # 以物理像素建立 pixmap，再透過 setDevicePixelRatio 讓 Qt 以 logical size 顯示，
    # 避免 high-DPI（125% / 150% / 200%）下 SVG 被點陣放大造成糊邊。
    phys = max(1, int(round(size * dpr)))
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(phys, phys)
    pix.fill(Qt.GlobalColor.transparent)
    pix.setDevicePixelRatio(dpr)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(p)
    p.end()
    _cache[key] = pix
    return pix


def lucide_icon(name: str, color: str = "#ffffff",
                size: int = 16, stroke: float = 2.0) -> QIcon:
    return QIcon(lucide_pixmap(name, color, size, stroke))
