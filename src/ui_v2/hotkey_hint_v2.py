"""
快捷鍵設定提示小窗 — V2

實作 HotkeyManager 期待的 header.show_hotkey_hint(text, color) / clear_hotkey_hint()
介面，取代 main_v2.py 原本的 _NoopHeader（只印 console，封裝成 exe 後使用者完全看不到，
等於整個捕捉流程沒有任何提示）。用一個置頂浮動小窗清楚顯示提示，涵蓋所有走
HotkeyManager.begin_capture 的情境：技能／怪物／指令（含指令下特定名稱）快捷鍵設定。

顯示流程（HotkeyManager 既有邏輯，本模組只負責「顯示」這一半，不改動觸發時機）：
    進入捕捉模式 → show_hotkey_hint(黃字「請按下…」)         —— 一直顯示到按下按鍵為止
    設定成功     → show_hotkey_hint(綠字「✓ 設定為 …」)      —— 2 秒後 clear_hotkey_hint()
    設定失敗     → show_hotkey_hint(紅字「✗ 設定失敗…」)      —— 3 秒後 clear_hotkey_hint()
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication
from PySide6.QtCore import Qt

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui.window_geometry import clamp_to_screen


class _HotkeyHintWindow(QWidget):
    """單一提示小窗：文字 + 依 color 上色的邊框；無邊框置頂、不搶焦點、螢幕上緣置中"""

    def __init__(self, text: str, color: str):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # 不搶焦點：跳出時使用者可能還在其他輸入框打字（例如剛按下設定鍵的卡片）
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(self)
        self._card.setObjectName("hotkey_hint")
        outer.addWidget(self._card)

        lay = QHBoxLayout(self._card)
        lay.setContentsMargins(T.S_LG, T.S_MD, T.S_LG, T.S_MD)
        self._label = QLabel(text)
        self._label.setTextFormat(Qt.TextFormat.PlainText)
        lay.addWidget(self._label)

        self._apply_color(color)
        self.adjustSize()
        self._recenter()
        self.show()

    def _apply_color(self, color: str):
        self._card.setStyleSheet(
            f"QFrame#hotkey_hint {{ background: {T.alpha(T.BG_BOTTOM, 235)};"
            f" border: 2px solid {color}; border-radius: {T.R_MD}px; }}"
        )
        self._label.setStyleSheet(
            f"color: {color}; background: transparent;"
            f" font-size: 14px; font-weight: 700;")

    def _recenter(self):
        """螢幕上緣置中；每次更新內容後寬度可能變化，重新置中一次"""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = geo.center().x() - self.width() // 2
        y = geo.top() + 100
        cx, cy = clamp_to_screen(x, y, self.width(), self.height())
        self.move(cx, cy)

    def update_content(self, text: str, color: str):
        self._label.setText(text)
        self._apply_color(color)
        self.adjustSize()
        self._recenter()


class HotkeyHintV2:
    """V2AppContext.header 的實作：管理單一提示小窗的顯示／更新／關閉

    HotkeyManager 只呼叫 show_hotkey_hint / clear_hotkey_hint 這兩個方法，
    介面與 V1 Header 對齊，可直接替換 main_v2.py 原本的 _NoopHeader。
    """

    def __init__(self):
        self._win: _HotkeyHintWindow | None = None

    def show_hotkey_hint(self, text: str, color: str):
        if self._win is None:
            self._win = _HotkeyHintWindow(text, color)
        else:
            self._win.update_content(text, color)

    def clear_hotkey_hint(self):
        if self._win is not None:
            self._win.close()
            self._win = None
