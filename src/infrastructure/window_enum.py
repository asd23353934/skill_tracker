"""
視窗列舉與縮圖擷取（Windows 專屬，ctypes，Qt-free）

供「快捷鍵限定前景視窗」功能使用：
- list_windows()：列出目前可見、有標題的頂層視窗（hwnd / title / pid / exe）
- get_foreground_exe()：取得前景視窗的執行檔名稱（小寫 basename），供 hotkey 比對
- get_foreground_hwnd()：只取前景視窗 handle（不查 process），供前景切換輪詢
- capture_window_thumbnail(hwnd)：用 PrintWindow 擷取視窗畫面為 BGRA bytes，
  與 z-order 無關（挑選器在最前景也能抓到背景視窗內容）；最小化或失敗回 None

僅依賴標準庫 ctypes，不依賴 Qt / PIL；bytes → 影像由 UI 層負責。
非 Windows 平台呼叫時各函式安全回傳空結果（[] / "" / None）。
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    gdi32 = ctypes.windll.gdi32

    GWL_EXSTYLE = -20
    WS_EX_TOOLWINDOW = 0x00000080
    PW_RENDERFULLCONTENT = 0x00000002
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    DIB_RGB_COLORS = 0
    BI_RGB = 0
    SRCCOPY = 0x00CC0020
    HALFTONE = 4

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    # argtypes / restypes — 64-bit pointer 安全（未宣告時 ctypes 預設 c_int 會截斷 HWND/HANDLE）
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = wintypes.LONG
    user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowDC.argtypes = [wintypes.HWND]
    user32.GetWindowDC.restype = wintypes.HDC
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
    user32.PrintWindow.restype = wintypes.BOOL

    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteDC.argtypes = [wintypes.HDC]
    gdi32.SetStretchBltMode.argtypes = [wintypes.HDC, ctypes.c_int]
    gdi32.StretchBlt.argtypes = [
        wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
    gdi32.GetDIBits.argtypes = [
        wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
        ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]

    class _BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG), ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD),
        ]

    class _BITMAPINFO(ctypes.Structure):
        _fields_ = [("bmiHeader", _BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def _exe_for_pid(pid: int) -> str:
    """以 PID 取執行檔小寫 basename；失敗回 ""。"""
    if not pid:
        return ""
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(512)
        size = wintypes.DWORD(512)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value).lower()
        return ""
    finally:
        kernel32.CloseHandle(handle)


def get_foreground_exe() -> str:
    """取得前景視窗執行檔名稱（小寫 basename）；非 Windows / 失敗回 ""。

    僅用 ctypes（user32 / kernel32），無 Qt 依賴，可於 pynput daemon thread 呼叫。
    """
    if not _IS_WINDOWS:
        return ""
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ""
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return _exe_for_pid(pid.value)
    except Exception:
        logger.debug("get_foreground_exe 失敗", exc_info=True)
        return ""


def get_foreground_hwnd() -> int:
    """取得目前前景視窗的 handle；非 Windows / 失敗回 0。

    只做一次 user32 呼叫、不查 process，成本遠低於 get_foreground_exe()，
    供「前景是否換了」這種高頻比對使用；需要執行檔名稱請改用 get_foreground_exe()。

    Returns:
        前景視窗 hwnd（整數）；取不到回 0
    """
    if not _IS_WINDOWS:
        return 0
    try:
        return int(user32.GetForegroundWindow() or 0)
    except Exception:
        logger.debug("get_foreground_hwnd 失敗", exc_info=True)
        return 0


def list_windows() -> list[dict]:
    """列出目前可見、有標題的頂層視窗。

    Returns:
        list[dict]：每筆 {hwnd: int, title: str, pid: int, exe: str}（exe 小寫 basename）
    """
    if not _IS_WINDOWS:
        return []
    results: list[dict] = []

    def _cb(hwnd, _lparam):  # noqa: ANN001
        try:
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if ex_style & WS_EX_TOOLWINDOW:
                return True  # 跳過工具視窗（不該被當成目標）
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            if not title or not title.strip():
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == os.getpid():
                return True  # 排除本程式自己的視窗（主視窗 / dialog / 浮動技能窗）
            results.append({
                "hwnd": int(hwnd),
                "title": title,
                "pid": int(pid.value),
                "exe": _exe_for_pid(pid.value),
            })
        except Exception:
            pass
        return True

    try:
        user32.EnumWindows(WNDENUMPROC(_cb), 0)
    except Exception:
        pass
    return results


def capture_window_thumbnail(hwnd: int, max_w: int = 240, max_h: int = 150):
    """用 PrintWindow 擷取視窗畫面，縮放後回傳 (bgra_bytes, width, height)。

    與 z-order 無關（挑選器在最前景也能抓到被遮擋的視窗內容）。回傳 BGRA、
    top-down；UI 可直接餵 QImage Format_RGB32（小端序對應 BGRX）。最小化視窗或
    擷取失敗回 None（UI 退回顯示程式圖示 + 標題）。

    Args:
        hwnd: 視窗 handle（list_windows 給的 int）
        max_w / max_h: 縮圖最大寬高（保持比例，不放大）
    """
    if not _IS_WINDOWS or not hwnd:
        return None
    handle = wintypes.HWND(hwnd)
    hdc_win = hdc_full = hdc_small = None
    hbmp_full = hbmp_small = None
    try:
        if user32.IsIconic(handle):
            return None
        rect = wintypes.RECT()
        if not user32.GetWindowRect(handle, ctypes.byref(rect)):
            return None
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        if w <= 0 or h <= 0:
            return None
        scale = min(max_w / w, max_h / h, 1.0)
        tw = max(1, int(w * scale))
        th = max(1, int(h * scale))

        hdc_win = user32.GetWindowDC(handle)
        hdc_full = gdi32.CreateCompatibleDC(hdc_win)
        hbmp_full = gdi32.CreateCompatibleBitmap(hdc_win, w, h)
        old_full = gdi32.SelectObject(hdc_full, hbmp_full)

        if not user32.PrintWindow(handle, hdc_full, PW_RENDERFULLCONTENT):
            user32.PrintWindow(handle, hdc_full, 0)  # 退回不帶旗標再試

        hdc_small = gdi32.CreateCompatibleDC(hdc_win)
        hbmp_small = gdi32.CreateCompatibleBitmap(hdc_win, tw, th)
        old_small = gdi32.SelectObject(hdc_small, hbmp_small)
        gdi32.SetStretchBltMode(hdc_small, HALFTONE)
        gdi32.StretchBlt(hdc_small, 0, 0, tw, th, hdc_full, 0, 0, w, h, SRCCOPY)

        bmi = _BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = tw
        bmi.bmiHeader.biHeight = -th  # 負 = top-down
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = BI_RGB
        buf_len = tw * th * 4
        buffer = (ctypes.c_char * buf_len)()
        got = gdi32.GetDIBits(hdc_small, hbmp_small, 0, th, buffer,
                              ctypes.byref(bmi), DIB_RGB_COLORS)

        gdi32.SelectObject(hdc_small, old_small)
        gdi32.SelectObject(hdc_full, old_full)
        if not got:
            return None
        return (bytes(buffer), tw, th)
    except Exception:
        logger.debug("capture_window_thumbnail 失敗 hwnd=%r", hwnd, exc_info=True)
        return None
    finally:
        # 確保 GDI 物件全數釋放，避免 handle 洩漏
        try:
            if hbmp_small:
                gdi32.DeleteObject(hbmp_small)
            if hbmp_full:
                gdi32.DeleteObject(hbmp_full)
            if hdc_small:
                gdi32.DeleteDC(hdc_small)
            if hdc_full:
                gdi32.DeleteDC(hdc_full)
            if hdc_win:
                user32.ReleaseDC(handle, hdc_win)
        except Exception:
            pass
