"""
視窗置頂重申（Windows 專屬，ctypes，Qt-free）

`Qt.WindowStaysOnTopHint` 只在視窗建立時把自己放進 topmost 群組一次。Windows 的
topmost 視窗彼此之間仍有 z-order，**後出現的 topmost 視窗會排到既有的前面**
（遊戲全螢幕視窗、Discord overlay、其他置頂工具都會造成這種遮擋）。Qt 的
`raise_()` 只調整同一 process 內的順序，跨程序無效。

唯一可靠的做法是每次要「確保看得見」時，重新對系統宣告一次 topmost：
`SetWindowPos(hwnd, HWND_TOPMOST, SWP_NOACTIVATE)` 會把視窗移到 topmost 群組
最前面。SWP_NOACTIVATE 為必要旗標 —— 少了它會搶走遊戲的鍵盤焦點。

非 Windows 平台呼叫時安全 no-op（回傳 False）。
"""

import logging
import sys

logger = logging.getLogger(__name__)

_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    HWND_TOPMOST = -1
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOACTIVATE = 0x0010
    SWP_SHOWWINDOW = 0x0040

    # argtypes / restype — 64-bit pointer 安全（未宣告時 ctypes 預設 c_int 會截斷 HWND）
    user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.UINT,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL


def bring_to_topmost(hwnd: int) -> bool:
    """把視窗重新拉到 topmost 群組最前面，且不奪取鍵盤焦點。

    供技能倒數小窗在每次按鍵觸發 / 提前提示時呼叫，避免被後來出現的其他置頂
    視窗蓋住。不移動、不改變大小，只調整 z-order。

    Args:
        hwnd: 視窗 handle（Qt 端用 `int(widget.winId())` 取得）

    Returns:
        成功回 True；非 Windows、hwnd 無效或呼叫失敗回 False
    """
    if not _IS_WINDOWS or not hwnd:
        return False
    try:
        return bool(user32.SetWindowPos(
            wintypes.HWND(hwnd), wintypes.HWND(HWND_TOPMOST),
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
        ))
    except Exception:
        logger.debug("bring_to_topmost 失敗 hwnd=%r", hwnd, exc_info=True)
        return False
