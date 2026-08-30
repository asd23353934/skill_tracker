"""測 WindowManager 的置頂重申 watcher — 前景視窗換了才重申，純邏輯不需 Qt"""
import os

# _topmost_tick / reassert_topmost 都不碰 Qt，但 import 鏈上有 PySide6 的模組
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from src.ui import window_manager as wm_mod
from src.ui.window_manager import WindowManager


class _FakeWindow:
    """記錄 raise_to_top 呼叫次數與參數的小窗替身"""

    def __init__(self, boom: bool = False):
        self.calls: list[bool] = []
        self._boom = boom

    def raise_to_top(self, *, show: bool = True):
        if self._boom:
            raise RuntimeError("widget 已銷毀")
        self.calls.append(show)


@pytest.fixture
def manager():
    """不啟動 QTimer 的 WindowManager（直接驅動 _topmost_tick）"""
    return WindowManager(app=object())


def _set_foreground(monkeypatch, hwnd: int):
    monkeypatch.setattr(wm_mod, "get_foreground_hwnd", lambda: hwnd)


def test_no_windows_skips_foreground_query(manager, monkeypatch):
    """沒有小窗時連前景都不查 —— 穩態成本只有一次 dict 判斷"""
    queried = []

    def _spy():
        queried.append(1)
        return 1234

    monkeypatch.setattr(wm_mod, "get_foreground_hwnd", _spy)

    manager._topmost_tick()

    assert queried == []
    assert manager._last_foreground_hwnd == 0


def test_foreground_unchanged_does_not_reassert(manager, monkeypatch):
    """前景沒換就不動 z-order（避免無謂的 SetWindowPos）"""
    win = _FakeWindow()
    manager.active_windows["s1"] = win
    _set_foreground(monkeypatch, 1234)

    manager._topmost_tick()      # 第一次：0 → 1234，視為換了
    assert win.calls == [False]

    manager._topmost_tick()      # 第二次：沒變
    manager._topmost_tick()
    assert win.calls == [False]


def test_foreground_changed_reasserts_all_windows(manager, monkeypatch):
    """前景換了 → 每個小窗各重申一次，且不帶 SWP_SHOWWINDOW"""
    a, b = _FakeWindow(), _FakeWindow()
    manager.active_windows.update({"s1": a, "s2": b})

    _set_foreground(monkeypatch, 1111)
    manager._topmost_tick()
    _set_foreground(monkeypatch, 2222)
    manager._topmost_tick()

    assert a.calls == [False, False]
    assert b.calls == [False, False]
    assert manager._last_foreground_hwnd == 2222


def test_zero_foreground_is_ignored(manager, monkeypatch):
    """切換瞬間 / 鎖定畫面可能取到 0 —— 略過且不污染快取值"""
    win = _FakeWindow()
    manager.active_windows["s1"] = win

    _set_foreground(monkeypatch, 1111)
    manager._topmost_tick()
    assert win.calls == [False]

    _set_foreground(monkeypatch, 0)
    manager._topmost_tick()
    assert win.calls == [False]
    assert manager._last_foreground_hwnd == 1111


def test_one_broken_window_does_not_stop_the_rest(manager, monkeypatch):
    """單一小窗已銷毀不該中斷整批重申"""
    boom, ok = _FakeWindow(boom=True), _FakeWindow()
    manager.active_windows.update({"bad": boom, "good": ok})

    _set_foreground(monkeypatch, 1111)
    manager._topmost_tick()

    assert ok.calls == [False]


def test_reassert_tolerates_window_dict_mutation(manager, monkeypatch):
    """重申途中小窗自我關閉（改動 active_windows）不該拋 RuntimeError"""
    class _SelfClosing(_FakeWindow):
        def raise_to_top(self, *, show: bool = True):
            manager.active_windows.pop("other", None)
            super().raise_to_top(show=show)

    closer = _SelfClosing()
    manager.active_windows.update({"closer": closer, "other": _FakeWindow()})

    manager.reassert_topmost()

    assert closer.calls == [False]


def test_stop_watch_without_start_is_safe(manager):
    """沒啟動過就呼叫 stop 不該炸（關閉流程可能重複呼叫）"""
    manager.stop_topmost_watch()
    assert manager._topmost_timer is None
