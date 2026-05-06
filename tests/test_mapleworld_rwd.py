"""資源中心 RWD 邏輯 smoke test — 驗證 _compute_cols 在不同 viewport 寬度下的欄數"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

from src.ui_v2.pages.mapleworld_page_v2 import MapleWorldPageV2
from src.ui_v2.pages.mapleworld_widgets_v2 import _AssetCard


class _FakeViewport:
    def __init__(self, w: int):
        self._w = w

    def width(self) -> int:
        return self._w


class _FakeScroll:
    def __init__(self, w: int):
        self._vp = _FakeViewport(w)

    def viewport(self):
        return self._vp


def test_compute_cols_scales_with_width():
    page = MapleWorldPageV2(parent=None, app=None)

    expectations = [
        # (viewport_w, min_cols, max_cols)
        (320,  1, 2),    # 手機等級
        (480,  2, 3),
        (640,  3, 4),
        (800,  4, 5),
        (1024, 5, 7),    # 一般筆電
        (1280, 7, 9),
        (1600, 9, 11),
        (1920, 11, 13),  # 桌機 FHD
        (2560, 15, 17),  # 桌機 2K
    ]
    for w, lo, hi in expectations:
        page._scroll = _FakeScroll(w)
        cols = page._compute_cols()
        card_total = cols * _AssetCard.CARD_W + max(0, cols - 1) * 8
        assert cols >= 1, f"viewport={w}: cols={cols} 必須 >=1"
        assert lo <= cols <= hi, (
            f"viewport={w}: cols={cols} 不在 [{lo},{hi}]; card_total={card_total}"
        )
        assert card_total <= w + 8, (
            f"viewport={w}: cols={cols} 排出來總寬 {card_total} 超過 viewport"
        )
        print(f"viewport_w={w:>5}  cols={cols:>2}  card_total={card_total}")
    print("OK — _compute_cols 在各寬度下都產出合理欄數")


def test_compute_cols_zero_width_fallback():
    """viewport 寬度為 0（widget 還沒 show）時不應 crash，應回 fallback"""
    page = MapleWorldPageV2(parent=None, app=None)
    page._scroll = _FakeScroll(0)
    page._cols = 5
    assert page._compute_cols() == 5
    page._cols = 0
    assert page._compute_cols() == 1
    print("OK — _compute_cols 在 viewport 寬度為 0 時 fallback 正常")


if __name__ == "__main__":
    test_compute_cols_scales_with_width()
    test_compute_cols_zero_width_fallback()
    print("\nall tests passed")
