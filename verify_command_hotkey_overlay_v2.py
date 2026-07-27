"""
指令快捷鍵小窗刷新驗證 — CommandHotkeyOverlayV2.set_bindings

回歸重點：改綁按鍵時 `_refresh_hotkey_overlay()` 會就地呼叫 set_bindings 重建清單。
清單列若以裸 QHBoxLayout 加入（addLayout），清空迴圈的 `takeAt(0).widget()` 會取到
None，其中的 QLabel 仍掛在卡片上、脫離 layout 後留在原位繼續顯示 —— 畫面上就會
看到舊按鍵沒被清掉、與新按鍵並存（且每次刷新持續累積）。

執行：python verify_command_hotkey_overlay_v2.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QLabel

from src.ui_v2.pages.command_hotkey_overlay_v2 import CommandHotkeyOverlayV2

_failures: list[str] = []


def check(label: str, got, expected):
    if got == expected:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}: got {got!r}, expected {expected!r}")
        _failures.append(label)


def visible_texts(app, overlay):
    """卡片上實際還活著的 QLabel 文字（排除標題）"""
    app.processEvents()
    return sorted(
        lb.text() for lb in overlay._card.findChildren(QLabel)
        if lb.text() and lb.text() != "指令快捷鍵"
    )


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    overlay = CommandHotkeyOverlayV2([("1", "/邀請組隊 1234")], on_close=None)

    print("[1] 初始一筆綁定")
    check("顯示內容", visible_texts(app, overlay), ["/邀請組隊 1234", "1"])
    h1 = overlay.height()

    print("[2] 改綁按鍵 1 → 2")
    overlay.set_bindings([("2", "/邀請組隊 1234")])
    texts = visible_texts(app, overlay)
    check("舊按鍵已消失", "1" not in texts, True)
    check("只剩一筆", texts, ["/邀請組隊 1234", "2"])
    check("高度未增長", overlay.height() <= h1, True)

    print("[3] 加到三筆再刪回一筆")
    overlay.set_bindings([("2", "/A"), ("3", "/B"), ("4", "/C")])
    check("三筆都在", len(visible_texts(app, overlay)), 6)
    h3 = overlay.height()
    overlay.set_bindings([("9", "/Z")])
    check("縮回一筆", visible_texts(app, overlay), ["/Z", "9"])
    check("高度有縮回", overlay.height() < h3, True)

    print("[4] 清空為零筆")
    overlay.set_bindings([])
    check("顯示空狀態", visible_texts(app, overlay), ["尚未設定任何指令快捷鍵"])

    overlay.close()
    app.processEvents()

    if _failures:
        print(f"\nFAILED: {len(_failures)} check(s)")
        for f in _failures:
            print(f"  - {f}")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
