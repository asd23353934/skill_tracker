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


_OVERSAMPLE = 4   # 內部以此倍率渲染 SVG，再平滑縮回目標尺寸


def lucide_pixmap(name: str, color: str = "#ffffff",
                  size: int = 16, stroke: float = 2.0) -> QPixmap:
    """載入 Lucide SVG 並回傳 QPixmap（size × size 邏輯像素）。

    內部以 4x 超採樣渲染後平滑縮回，避免小尺寸 icon 的對角線因
    抗鋸齒落在奇偶像素格而視覺歪斜。不依賴 devicePixelRatio，
    在不同 Qt / Windows 版本行為一致。
    """
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
    hi = max(1, size * _OVERSAMPLE)
    hi_pix = QPixmap(hi, hi)
    hi_pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(hi_pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p)
    p.end()

    pix = hi_pix.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    _cache[key] = pix
    return pix


def lucide_icon(name: str, color: str = "#ffffff",
                size: int = 16, stroke: float = 2.0) -> QIcon:
    return QIcon(lucide_pixmap(name, color, size, stroke))
