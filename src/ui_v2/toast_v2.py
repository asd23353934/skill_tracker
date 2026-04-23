"""
V2 Toast 通知系統

ToastV2(QFrame)        — 單則 toast widget；fade-in / 3000ms / fade-out
ToastManagerV2(QObject) — 容器與堆疊管理；API 同 V1 ToastManager
                          show(message: str, kind: str = "info")

kind ∈ {"info", "success", "warning", "error"}；未知 kind fallback 至 info。
浮現位置：PreviewWindow 右下角；多則 toast 由新到舊由下往上堆疊。
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import (
    Qt, QObject, QEvent, QTimer, QPropertyAnimation, QEasingCurve, Signal,
)

from src.ui_v2.theme_v2 import V2Theme as T


_KIND_ACCENT = {
    "info":    T.CYAN,
    "success": T.GREEN,
    "warning": T.ORANGE,
    "error":   T.RED,
}

_AUTO_DISMISS_MS = 3000
_FADE_IN_MS      = 200
_FADE_OUT_MS     = 250
_EDGE_MARGIN     = 16
_STACK_GAP       = 8


class ToastV2(QFrame):
    """單則 V2 toast 浮層。"""

    dismissed = Signal(object)  # 自身 emit 出去通知 manager 移除

    def __init__(self, parent, message: str, kind: str = "info"):
        super().__init__(parent)
        accent = _KIND_ACCENT.get(kind, _KIND_ACCENT["info"])

        self.setObjectName("toast_v2")
        self.setStyleSheet(
            f"QFrame#toast_v2 {{"
            f" background: {T.alpha(accent, 32)};"
            f" border: 1px solid {accent};"
            f" border-radius: {T.R_MD}px; }}"
        )
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # 不奪游標 / 不擋下方 widget hover
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(0)
        lbl = QLabel(message)
        lbl.setTextFormat(Qt.TextFormat.PlainText)  # 防 HTML 注入
        lbl.setStyleSheet(
            f"color: {T.TEXT_HI}; background: transparent; border: none;"
            f" font-size: 11px; font-weight: 600;"
        )
        lay.addWidget(lbl)
        self.adjustSize()

        # 透明度動畫
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        self._fade_in: QPropertyAnimation | None = None
        self._fade_out: QPropertyAnimation | None = None
        self._dismiss_timer: QTimer | None = None
        self._dismissing = False

    def show_animated(self):
        """顯示 + 200ms fade-in；fade-in 完後自動排定 dismiss。"""
        self.show()
        self.raise_()
        self._fade_in = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade_in.setDuration(_FADE_IN_MS)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._fade_in.finished.connect(self._schedule_dismiss)
        self._fade_in.start()

    def _schedule_dismiss(self):
        if self._dismissing:
            return
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._begin_dismiss)
        self._dismiss_timer.start(_AUTO_DISMISS_MS)

    def _begin_dismiss(self):
        if self._dismissing:
            return
        self._dismissing = True
        self._fade_out = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade_out.setDuration(_FADE_OUT_MS)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InQuad)
        self._fade_out.finished.connect(self._finalize)
        self._fade_out.start()

    def _finalize(self):
        self.dismissed.emit(self)
        self.deleteLater()


class ToastManagerV2(QObject):
    """V2 ToastManager — 容器、堆疊、視窗 resize 重排。

    與 V1 ToastManager 共用 `show(message, kind)` 介面但獨立實作。
    必須由主執行緒呼叫；跨執行緒請走 `app.after(0, lambda: toast.show(...))`。
    """

    def __init__(self, window):
        # 先設 _window，避免 super().__init__(window) 期間 ChildAdded 事件
        # 觸發 eventFilter 卻找不到屬性
        self._window = window
        self._toasts: list[ToastV2] = []
        super().__init__(window)
        window.installEventFilter(self)

    # ── 對外 API ──
    def show(self, message: str, kind: str = "info"):
        toast = ToastV2(self._window, message, kind)
        toast.dismissed.connect(self._remove_toast)
        self._toasts.append(toast)
        toast.show_animated()
        self._reposition_all()

    # ── 內部 ──
    def _remove_toast(self, toast):
        try:
            self._toasts.remove(toast)
        except ValueError:
            pass
        self._reposition_all()

    def _reposition_all(self):
        win = self._window
        if win is None:
            return
        # 從最新（list 末尾）開始排到右下角，往上累積
        y_cursor = win.height() - _EDGE_MARGIN
        for toast in reversed(self._toasts):
            tw = toast.width()
            th = toast.height()
            x = win.width() - _EDGE_MARGIN - tw
            y = y_cursor - th
            toast.move(x, y)
            y_cursor = y - _STACK_GAP

    def eventFilter(self, obj, event):
        # 防護：Python 端 attribute 可能在 C++ 物件還活著時就被 gc 掉
        win = getattr(self, "_window", None)
        if win is not None and obj is win and event.type() == QEvent.Type.Resize:
            self._reposition_all()
        return super().eventFilter(obj, event)
