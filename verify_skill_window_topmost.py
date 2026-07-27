"""
技能倒數小窗置頂行為驗證（Windows 專屬，需真實桌面）

驗證三件事：
1. SkillWindow 帶 WS_EX_NOACTIVATE（Qt.WindowDoesNotAcceptFocus）
   → 拖曳 / 點關閉鈕不會把焦點從遊戲搶走
2. SkillWindow 帶 WS_EX_TOPMOST
3. 被後來出現的其他置頂視窗蓋住後，restart_countdown()（= 按鍵再次觸發）
   能把小窗重新拉回 z-order 最前面

第 3 點用 EnumWindows 的回呼順序判定 —— 該順序即為 z-order（前→後）。

執行：python verify_skill_window_topmost.py
"""

import ctypes
import os
import sys
from ctypes import wintypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

from src.infrastructure.window_enum import GWL_EXSTYLE, WNDENUMPROC, user32
from src.ui.skill_window import SkillWindow

HERE = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(HERE, "icon.png")

# window_enum 已宣告 GetWindowLongW / EnumWindows 的 argtypes，這裡只補常量
WS_EX_TOPMOST = 0x00000008
WS_EX_NOACTIVATE = 0x08000000

_failures: list[str] = []


def check(label: str, got, expected):
    if got == expected:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}: got {got!r}, expected {expected!r}")
        _failures.append(label)


def ex_style(hwnd: int) -> int:
    return user32.GetWindowLongW(wintypes.HWND(hwnd), GWL_EXSTYLE) & 0xFFFFFFFF


def z_index(target_hwnd: int) -> int:
    """回傳 hwnd 在 z-order 中的名次（0 = 最前面）；找不到回 -1"""
    order = []

    def _cb(hwnd, _lparam):
        order.append(int(hwnd))
        return True

    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return order.index(target_hwnd) if target_hwnd in order else -1


def main():
    if sys.platform != "win32":
        print("⚠️  非 Windows，略過")
        return 0

    app = QApplication.instance() or QApplication(sys.argv)

    win = SkillWindow(
        skill={"name": "置頂測試", "cooldown": 60, "hotkey": "F1"},
        player="",
        position=(400, 300),
        skill_image=None,
        on_close=lambda w: None,
        enable_sound=False,
        skill_id="topmost_demo",
        window_size=96,
        skill_image_path=ICON if os.path.exists(ICON) else None,
        sound_manager=None,
        title="置頂測試",
    )
    app.processEvents()
    hwnd = int(win.winId())

    print("[1] 視窗擴充樣式")
    style = ex_style(hwnd)
    check("WS_EX_NOACTIVATE 已設", bool(style & WS_EX_NOACTIVATE), True)
    check("WS_EX_TOPMOST 已設", bool(style & WS_EX_TOPMOST), True)

    print("[2] 被後來的置頂視窗遮擋")
    # 模擬「遊戲 / 其他置頂工具」：後建立的 topmost 視窗會排到既有 topmost 前面
    intruder = QWidget(None, Qt.WindowType.WindowStaysOnTopHint
                       | Qt.WindowType.FramelessWindowHint
                       | Qt.WindowType.Tool)
    intruder.setGeometry(380, 280, 200, 200)
    intruder.show()
    app.processEvents()
    intruder_hwnd = int(intruder.winId())

    before = z_index(hwnd)
    intruder_z = z_index(intruder_hwnd)
    print(f"     小窗 z={before}, 後來的置頂視窗 z={intruder_z}")
    check("小窗確實被壓在後面", before > intruder_z, True)

    print("[3] 按鍵再次觸發 → restart_countdown 重申置頂")
    win.restart_countdown()
    app.processEvents()

    after = z_index(hwnd)
    intruder_z2 = z_index(intruder_hwnd)
    print(f"     小窗 z={after}, 後來的置頂視窗 z={intruder_z2}")
    check("小窗已回到前面", after < intruder_z2, True)

    print("[4] 提前提示也重申置頂")
    intruder.raise_()
    app.processEvents()
    win._trigger_alert()
    app.processEvents()
    check("alert 後小窗在前面", z_index(hwnd) < z_index(intruder_hwnd), True)

    intruder.close()
    win.close()
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
