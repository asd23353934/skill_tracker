"""
視窗座標 clamp helper — 把視窗位置限制在可見螢幕範圍內。

涵蓋：多螢幕拔除後座標仍在已不存在副螢幕、拖曳超出邊界、解析度變更後 saved
座標看不見等情境。

clamp_pos 為純函式版本接受 screen_rect 參數方便單元測試；clamp_to_screen
為便利包裝，用 QApplication 當前所有螢幕的 union geometry。
"""

from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication


def clamp_pos(x: int, y: int, w: int, h: int,
              screen_rect: QRect, margin: int = 20) -> tuple[int, int]:
    """把 (x, y) 視窗左上角座標 clamp 到 screen_rect 範圍內。

    Args:
        x, y:        原始座標
        w, h:        視窗寬高（確保視窗右下角也在範圍內）
        screen_rect: 可用螢幕範圍（多螢幕的 union 或單螢幕的 availableGeometry）
        margin:      留白邊界（px），避免視窗緊貼螢幕邊緣

    Returns:
        (new_x, new_y)
    """
    min_x = screen_rect.left() + margin
    min_y = screen_rect.top() + margin
    max_x = screen_rect.right() - w - margin
    max_y = screen_rect.bottom() - h - margin
    if max_x < min_x:
        max_x = min_x
    if max_y < min_y:
        max_y = min_y
    return (
        max(min_x, min(x, max_x)),
        max(min_y, min(y, max_y)),
    )


def clamp_to_screen(x: int, y: int, w: int, h: int,
                    margin: int = 20) -> tuple[int, int]:
    """便利包裝 — 用 QApplication 當前所有螢幕的 union geometry 做 clamp。

    若 QApplication 尚未建立或無 screen，原樣返回 (x, y)。
    """
    app = QApplication.instance()
    if app is None:
        return x, y

    available = None
    for s in app.screens():
        g = s.availableGeometry()
        available = g if available is None else available.united(g)

    if available is None:
        return x, y

    return clamp_pos(x, y, w, h, available, margin)
