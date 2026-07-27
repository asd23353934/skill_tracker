"""
指令快捷鍵小窗 / 複製回饋小窗 — V2

CommandHotkeyOverlayV2：透明無邊框浮動小窗，列出目前所有「已綁定按鍵 → 指令」，
方便切回遊戲時對照（不需切回主視窗查）。可拖曳移動；右上角 X 關閉，關閉時回呼
on_close 讓 CommandPageV2 的勾選框同步取消勾選。

不持久化位置／開關狀態：每次開啟從預設座標出現，關閉即銷毀，下次重新勾選
會用最新的快捷鍵清單重建 —— 這是一次性的「快速對照」小窗，非常駐設定。

CommandCopyFlashV2：觸發指令快捷鍵複製後的短暫回饋小窗（「已複製：<內容>」），
獨立頂層視窗顯示在螢幕最上層並自動淡出關閉 —— 觸發當下使用者通常切在遊戲
視窗，看不到主視窗裡的 in-app toast，需要一個遊戲畫面上也看得到的確認。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_pixmap
from src.ui.window_geometry import clamp_to_screen

_DEFAULT_POSITION = (80, 80)


class CommandHotkeyOverlayV2(QWidget):
    """指令快捷鍵清單小窗：[(KEY, 指令關鍵字), ...] → 逐行顯示"""

    def __init__(self, bindings: list[tuple[str, str]], on_close,
                 position: tuple[int, int] = _DEFAULT_POSITION):
        # WindowDoesNotAcceptFocus（Windows 上即 WS_EX_NOACTIVATE）：這是常駐的
        # 對照窗，使用者會在遊戲進行中拖它或按關閉鈕 —— 不能因此把焦點搶走。
        # 用它而非 WA_ShowWithoutActivating，後者只管首次 show，之後的點擊照樣搶焦點。
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        self._on_close = on_close
        self._closed = False
        self._drag_offset = QPoint()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame(self)
        self._card.setObjectName("cmd_hotkey_overlay")
        self._card.setStyleSheet(
            f"QFrame#cmd_hotkey_overlay {{ background: {T.alpha(T.BG_BOTTOM, 225)};"
            f" border: 1px solid {T.alpha(T.ORANGE, 120)}; border-radius: {T.R_MD}px; }}"
        )
        outer.addWidget(self._card)

        root = QVBoxLayout(self._card)
        root.setContentsMargins(T.S_MD, T.S_SM, T.S_MD, T.S_MD)
        root.setSpacing(T.S_XS)

        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        title = QLabel("指令快捷鍵")
        title.setStyleSheet(
            f"color: {T.TEXT_HI}; background: transparent;"
            f" font-size: 12px; font-weight: 700;")
        head.addWidget(title)
        head.addStretch()
        close_btn = QLabel()
        close_btn.setPixmap(lucide_pixmap("x", T.TEXT_DIM, 14, stroke=1.8))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("background: transparent;")
        close_btn.mousePressEvent = lambda e: self.close()
        head.addWidget(close_btn)
        root.addLayout(head)

        self._list_layout = QVBoxLayout()
        self._list_layout.setSpacing(3)
        root.addLayout(self._list_layout)

        self.set_bindings(bindings)

        self.adjustSize()
        cx, cy = clamp_to_screen(position[0], position[1], self.width(), self.height())
        self.move(cx, cy)
        self.show()

    def set_bindings(self, bindings: list[tuple[str, str]]):
        """依目前快捷鍵重建清單內容

        每一列都是獨立的 QWidget 容器（而非裸 QHBoxLayout）—— 清空時
        `takeAt(0).widget()` 才取得到東西可刪。改綁按鍵會呼叫本方法就地刷新，
        若列是裸 layout，其中的 QLabel 仍掛在 _card 上，脫離 layout 後會留在
        原位繼續顯示，畫面上就會看到舊按鍵沒被清掉、與新按鍵並存。

        Args:
            bindings: [(KEY, 指令關鍵字), ...]；空清單顯示提示文字
        """
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        if not bindings:
            empty = QLabel("尚未設定任何指令快捷鍵")
            empty.setTextFormat(Qt.TextFormat.PlainText)
            empty.setStyleSheet(
                f"color: {T.TEXT_MUTED}; background: transparent; font-size: 11px;")
            self._list_layout.addWidget(empty)
        else:
            for key, label in bindings:
                self._list_layout.addWidget(self._make_row(key, label))

        # 重建後 _card 的 sizeHint 雖已更新，失效鏈卻止於 _card 自己的 layout，
        # self 的 outer layout 從未被 dirty → 不 activate 的話 adjustSize() 讀到
        # 的還是舊 hint，視窗刪到剩一列時外框會停在舊高度。
        self._card.layout().activate()
        self.adjustSize()

    def _make_row(self, key: str, label: str) -> QWidget:
        """建立一列「按鍵 → 指令」的顯示元件

        Args:
            key:   實體按鍵名稱
            label: 指令關鍵字（含名稱）

        Returns:
            承載該列的 QWidget（供 _list_layout 以 addWidget 管理）
        """
        row_w = QWidget()
        row_w.setStyleSheet("background: transparent;")
        row = QHBoxLayout(row_w)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(T.S_SM)

        key_lbl = QLabel(key)
        key_lbl.setTextFormat(Qt.TextFormat.PlainText)
        key_lbl.setFixedWidth(48)
        key_lbl.setStyleSheet(
            f"color: {T.ORANGE}; background: transparent;"
            f" font-size: 12px; font-weight: 700;")
        row.addWidget(key_lbl)

        cmd_lbl = QLabel(label)
        cmd_lbl.setTextFormat(Qt.TextFormat.PlainText)
        cmd_lbl.setStyleSheet(
            f"color: {T.TEXT_HI}; background: transparent; font-size: 12px;")
        row.addWidget(cmd_lbl, 1)
        return row_w

    # ── 拖曳移動（點卡片背景任一處皆可拖曳，關閉鈕自行消化點擊）──
    def mousePressEvent(self, e):  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = e.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, e):  # noqa: N802
        if e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_offset)

    def close(self):  # noqa: A003
        """關閉小窗並通知 CommandPageV2 同步取消勾選"""
        if self._closed:
            return
        self._closed = True
        if self._on_close:
            try:
                self._on_close()
            except Exception:
                pass
        super().close()


class CommandCopyFlashV2(QWidget):
    """快捷鍵觸發複製後的短暫回饋小窗：綠底「已複製：<內容>」，淡入顯示、停留後淡出自關

    獨立頂層視窗（非主視窗子元件），確保觸發當下即使焦點在遊戲視窗也看得到。
    """

    _VISIBLE_MS = 1600
    _FADE_IN_MS = 160
    _FADE_OUT_MS = 220

    def __init__(self, text: str, position: tuple[int, int] | None = None,
                 on_close=None):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        # 不搶焦點：顯示當下不應打斷使用者在遊戲視窗的操作
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._on_close = on_close
        self._closed = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame(self)
        card.setObjectName("cmd_copy_flash")
        card.setStyleSheet(
            f"QFrame#cmd_copy_flash {{ background: {T.alpha(T.GREEN, 235)};"
            f" border: 1px solid {T.GREEN}; border-radius: {T.R_MD}px; }}"
        )
        outer.addWidget(card)

        lay = QHBoxLayout(card)
        lay.setContentsMargins(T.S_MD, T.S_SM, T.S_MD, T.S_SM)
        lay.setSpacing(T.S_SM)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(lucide_pixmap("copy", "#ffffff", 14, stroke=2.0))
        icon_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(icon_lbl)
        text_lbl = QLabel(f"已複製：{text}")
        text_lbl.setTextFormat(Qt.TextFormat.PlainText)
        text_lbl.setStyleSheet(
            "color: #ffffff; background: transparent; font-size: 12px; font-weight: 700;")
        lay.addWidget(text_lbl)

        self.adjustSize()
        x, y = position if position is not None else self._default_position()
        cx, cy = clamp_to_screen(x, y, self.width(), self.height())
        self.move(cx, cy)

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        self.show()
        self._fade_in = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade_in.setDuration(self._FADE_IN_MS)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.finished.connect(
            lambda: QTimer.singleShot(self._VISIBLE_MS, self._begin_fade_out))
        self._fade_in.start()
        self._fade_out: QPropertyAnimation | None = None

    def _default_position(self) -> tuple[int, int]:
        """預設出現在主螢幕上緣置中；取不到螢幕資訊則退回固定座標"""
        screen = QApplication.primaryScreen()
        if screen is None:
            return 200, 60
        geo = screen.availableGeometry()
        return geo.center().x() - self.width() // 2, geo.top() + 60

    def _begin_fade_out(self):
        self._fade_out = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade_out.setDuration(self._FADE_OUT_MS)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.finished.connect(self.close)
        self._fade_out.start()

    def close(self):  # noqa: A003
        """關閉小窗並通知呼叫端清除引用（idempotent，防重複關閉已刪除的 C++ 物件）"""
        if self._closed:
            return
        self._closed = True
        if self._on_close:
            try:
                self._on_close()
            except Exception:
                pass
        super().close()
