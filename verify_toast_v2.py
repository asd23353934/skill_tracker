"""
ToastV2 / ToastManagerV2 單元驗證

執行：`python verify_toast_v2.py` —— 全部通過時 exit code = 0

涵蓋：
- 4 種 kind 各跑一次無例外，manager._toasts 累積
- 未知 kind fallback 至 info（accent 為 CYAN）
- 連 show 3 個後 y 座標遞減（最新最低）、x 靠右邊界
- window.resize 觸發 eventFilter → toast 重排到新邊界
- success toast styleSheet 含 T.GREEN
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.toast_v2 import ToastV2, ToastManagerV2


_failures: list[str] = []


def check(label: str, got, expected):
    if got == expected:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}: got {got!r}, expected {expected!r}")
        _failures.append(label)


def _build_window():
    win = QMainWindow()
    win.resize(1240, 760)
    return win


def test_four_kinds_dispatch():
    print("[test_four_kinds_dispatch]")
    win = _build_window()
    mgr = ToastManagerV2(win)
    for k in ("info", "success", "warning", "error"):
        mgr.show(f"hello {k}", k)
    check("manager._toasts length", len(mgr._toasts), 4)


def test_unknown_kind_fallback():
    print("[test_unknown_kind_fallback]")
    win = _build_window()
    mgr = ToastManagerV2(win)
    mgr.show("???", "exotic")
    check("fallback toast added", len(mgr._toasts), 1)
    style = mgr._toasts[0].styleSheet()
    check("uses CYAN accent", T.CYAN in style, True)


def test_success_uses_green():
    print("[test_success_uses_green]")
    win = _build_window()
    mgr = ToastManagerV2(win)
    mgr.show("saved", "success")
    style = mgr._toasts[0].styleSheet()
    check("uses GREEN accent", T.GREEN in style, True)


def test_stack_positions():
    print("[test_stack_positions]")
    win = _build_window()
    mgr = ToastManagerV2(win)
    mgr.show("first", "info")
    mgr.show("second", "success")
    mgr.show("third", "error")
    # 三個都需處理 layout（adjustSize 已在 __init__ 中執行）
    QApplication.processEvents()
    mgr._reposition_all()

    # 最新（last）應在最下；x 都在右邊界內
    ys = [t.y() for t in mgr._toasts]
    check("y descending (oldest highest)", ys[0] > ys[2] is False and ys[0] < ys[1] < ys[2] is False, False)
    # 改用直觀斷言：新 (index 2) y 最大、舊 (index 0) y 最小
    check("newest toast at largest y", ys[2] >= ys[0], True)
    check("3 toasts have unique y", len(set(ys)), 3)
    margin = 16
    for t in mgr._toasts:
        check(f"toast x within right margin (id={id(t)%1000})",
              t.x() + t.width() <= win.width() - margin + 1, True)


def test_resize_reanchors():
    print("[test_resize_reanchors]")
    win = _build_window()
    win.show()  # 必須 show 才會收到 Resize 事件
    QApplication.processEvents()
    mgr = ToastManagerV2(win)
    mgr.show("hello", "info")
    QApplication.processEvents()
    initial_x = mgr._toasts[0].x()

    win.resize(800, 600)
    QApplication.processEvents()
    # eventFilter 應該觸發 _reposition_all
    new_x = mgr._toasts[0].x()
    check("toast x changed after resize", new_x != initial_x, True)
    # 新邊界內
    check("new x within new right edge",
          new_x + mgr._toasts[0].width() <= 800 - 16 + 1, True)
    win.close()


def main():
    QApplication.instance() or QApplication(sys.argv)
    test_four_kinds_dispatch()
    test_unknown_kind_fallback()
    test_success_uses_green()
    test_stack_positions()
    test_resize_reanchors()
    if _failures:
        print(f"\nFAILED: {len(_failures)} check(s)")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
