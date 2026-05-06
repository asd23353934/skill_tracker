"""ui.window_geometry — clamp_pos 純邏輯測試（B3）

clamp_pos 不依賴 QApplication，只用 QRect 純資料類別，可直接 unit-test。
"""

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect  # noqa: E402

from src.ui.window_geometry import clamp_pos  # noqa: E402


# 模擬 1920x1080 主螢幕（左上 0,0）
SCREEN = QRect(0, 0, 1920, 1080)


# ── 在範圍內：原樣返回 ─────────────────────────────────────

def test_pos_inside_screen_unchanged():
    assert clamp_pos(100, 100, 200, 200, SCREEN, margin=20) == (100, 100)


def test_pos_at_safe_top_left_unchanged():
    """剛好在 margin 邊界內。"""
    assert clamp_pos(20, 20, 200, 200, SCREEN, margin=20) == (20, 20)


# ── 超出邊界：被 clamp 回 ─────────────────────────────────

def test_pos_negative_clamped_to_left_top():
    """B3 主場景：multi-screen 拔除後座標 -9999 → clamp 回主螢幕。"""
    x, y = clamp_pos(-9999, -9999, 200, 200, SCREEN, margin=20)
    assert x == 20
    assert y == 20


def test_pos_far_right_clamped():
    """超出右邊界 → clamp 到 max_x。"""
    x, _ = clamp_pos(99999, 100, 200, 200, SCREEN, margin=20)
    # max_x = right(1919) - 200 - 20 = 1699（QRect.right 是 inclusive）
    assert x == 1699


def test_pos_far_bottom_clamped():
    _, y = clamp_pos(100, 99999, 200, 200, SCREEN, margin=20)
    # max_y = bottom(1079) - 200 - 20 = 859
    assert y == 859


def test_pos_off_screen_corner_clamped_diagonally():
    x, y = clamp_pos(5000, 5000, 200, 200, SCREEN, margin=20)
    assert x == 1699
    assert y == 859


# ── 視窗比螢幕大 ──────────────────────────────────────────

def test_window_larger_than_screen_falls_back_to_top_left():
    """視窗寬高比螢幕大 → max < min，退回左上對齊（不 crash）。"""
    huge_w, huge_h = 3000, 2000
    x, y = clamp_pos(500, 500, huge_w, huge_h, SCREEN, margin=20)
    assert x == 20
    assert y == 20


# ── 副螢幕情境：union geometry 行為 ────────────────────────

def test_secondary_screen_position_preserved():
    """副螢幕 (1920,0) 上的視窗座標 (2500, 100) 應在 union geometry 內被保留。"""
    main = QRect(0, 0, 1920, 1080)
    side = QRect(1920, 0, 1920, 1080)
    union = main.united(side)
    # union 應該是 (0, 0, 3840, 1080)
    assert union.right() == 3839
    # 副螢幕內座標應保留
    x, y = clamp_pos(2500, 100, 200, 200, union, margin=20)
    assert x == 2500
    assert y == 100


def test_secondary_screen_disconnected_position_clamped():
    """副螢幕拔除後 union 只剩主螢幕，原 (2500, 100) 該被拉回主螢幕內。"""
    main_only = QRect(0, 0, 1920, 1080)
    x, y = clamp_pos(2500, 100, 200, 200, main_only, margin=20)
    # max_x = right(1919) - 200 - 20 = 1699
    assert x == 1699
    assert y == 100


# ── margin 行為 ──────────────────────────────────────────

def test_zero_margin():
    """margin=0 時邊界貼緊螢幕。"""
    x, y = clamp_pos(0, 0, 100, 100, SCREEN, margin=0)
    assert x == 0
    assert y == 0
