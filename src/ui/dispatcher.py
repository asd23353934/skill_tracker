"""
Dispatcher — 跨執行緒安全的回呼排程器

V1 App 與 V2AppContext 共用：HotkeyManager / OverlayManager 從 pynput
daemon thread 呼叫 `app.after(ms, fn)`，由本類別將 callable 排回 Qt
主執行緒執行。
"""

from PySide6.QtCore import QObject, Qt, QTimer, Signal


class Dispatcher(QObject):
    """執行緒安全的回呼排程器"""

    _call = Signal(object)

    def __init__(self, parent: QObject):
        super().__init__(parent)
        # QueuedConnection：槽在接收端（主執行緒）的事件迴圈中執行
        self._call.connect(self._dispatch, Qt.ConnectionType.QueuedConnection)

    def schedule(self, ms: int, func):
        """排程 func 在主執行緒執行（ms=0 立即排隊）"""
        if ms == 0:
            self._call.emit(func)
        else:
            # 先跨執行緒送到主執行緒，再用 QTimer 延遲
            self._call.emit(lambda: QTimer.singleShot(ms, func))

    def _dispatch(self, func):
        func()
