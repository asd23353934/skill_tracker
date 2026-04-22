"""
Lucide SVG 圖示載入器
讀取 src/ui_v2/icons/*.svg，替換 currentColor → 實際色，回傳 QPixmap / QIcon
"""

import os
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap, QPainter, QIcon
from PySide6.QtCore import Qt, QByteArray

ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
_cache: dict = {}


def lucide_pixmap(name: str, color: str = "#ffffff",
                  size: int = 16, stroke: float = 2.0) -> QPixmap:
    key = (name, color, size, stroke)
    if key in _cache:
        return _cache[key]

    path = os.path.join(ICON_DIR, f"{name}.svg")
    with open(path, "r", encoding="utf-8") as f:
        svg = f.read()
    svg = svg.replace("currentColor", color)
    if stroke != 2.0:
        svg = svg.replace('stroke-width="2"', f'stroke-width="{stroke}"')

    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p)
    p.end()
    _cache[key] = pix
    return pix


def lucide_icon(name: str, color: str = "#ffffff",
                size: int = 16, stroke: float = 2.0) -> QIcon:
    return QIcon(lucide_pixmap(name, color, size, stroke))
