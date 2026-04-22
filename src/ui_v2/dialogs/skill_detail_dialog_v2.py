"""
技能詳細設定 dialog — V2
僅 UI（純殼，不接 App 狀態）
"""

from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget, QLabel, QSpinBox, QCheckBox, QPushButton,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import ArrowComboBox
from src.ui_v2.dialogs.base_dialog_v2 import BaseDialogV2
from src.ui_v2.lucide import lucide_pixmap


class _PlayBtn(QPushButton):
    """自繪播放三角按鈕"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(T.BTN_H, T.BTN_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton {{ background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px; }}"
            f"QPushButton:hover {{ background: {T.BG_HOVER};"
            f" border-color: {T.ORANGE}; }}"
        )

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        pix = lucide_pixmap("play", T.TEXT_HI, 14, stroke=1.8)
        p = QPainter(self)
        x = (self.width() - 14) // 2
        y = (self.height() - 14) // 2
        p.drawPixmap(x, y, pix)
        p.end()


class SkillDetailDialogV2(BaseDialogV2):
    """技能詳細設定（V2）— 純 UI 殼"""

    def __init__(self, parent=None, skill_name: str = "技能"):
        super().__init__(parent, title=f"技能設定 — {skill_name}", width=440, height=520)
        self._build_body()
        self._build_footer()

    # ════════════════════════════════════════════════════════
    # 主內容
    # ════════════════════════════════════════════════════════
    def _build_body(self):
        L = self.body_layout()

        # ── 區塊：提前提示 ──
        L.addWidget(self._section_label("提前提示"))

        alert_row = QHBoxLayout()
        alert_row.setSpacing(T.S_SM)
        self.alert_spin = QSpinBox()
        self.alert_spin.setRange(0, 60)
        self.alert_spin.setValue(3)
        self.alert_spin.setFixedHeight(T.BTN_H)
        self.alert_spin.setFixedWidth(80)
        alert_row.addWidget(self.alert_spin)
        alert_row.addWidget(self._caption("秒前提示"))
        alert_row.addStretch()
        L.addLayout(alert_row)

        self.use_global_cb = QCheckBox("使用全域秒數設定")
        self.use_global_cb.setChecked(True)
        L.addWidget(self.use_global_cb)

        L.addSpacing(T.S_SM)

        # ── 區塊：音效 ──
        L.addWidget(self._section_label("音效"))
        L.addLayout(self._sound_row("冷卻完成", ["預設", "鈴聲 A", "鈴聲 B", "無"]))
        L.addLayout(self._sound_row("提前提示", ["預設", "鈴聲 A", "鈴聲 B", "無"]))

        import_btn = QPushButton("+ 匯入音效檔案")
        import_btn.setProperty("kind", "ghost")
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.setFixedHeight(T.BTN_H)
        L.addWidget(import_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        L.addSpacing(T.S_SM)

        # ── 區塊：自動套用 ──
        L.addWidget(self._section_label("自動套用"))
        L.addWidget(self._caption("未手動切換時的預設狀態"))

        auto = QHBoxLayout()
        auto.setSpacing(T.S_LG)
        self.auto_perm = QCheckBox("常駐")
        self.auto_loop = QCheckBox("循環")
        self.auto_alert = QCheckBox("提醒")
        for cb in (self.auto_perm, self.auto_loop, self.auto_alert):
            auto.addWidget(cb)
        auto.addStretch()
        L.addLayout(auto)

        L.addStretch()

    # ════════════════════════════════════════════════════════
    # 底部按鈕
    # ════════════════════════════════════════════════════════
    def _build_footer(self):
        F = self.footer_layout()

        cancel = QPushButton("取消")
        cancel.setProperty("kind", "ghost")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setFixedHeight(T.BTN_H)
        cancel.clicked.connect(self.reject)
        F.addWidget(cancel)

        save = QPushButton("儲存")
        save.setProperty("kind", "primary")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.setFixedHeight(T.BTN_H)
        save.clicked.connect(self.accept)
        F.addWidget(save)

    # ════════════════════════════════════════════════════════
    # 子元件
    # ════════════════════════════════════════════════════════
    def _section_label(self, text: str) -> QLabel:
        return T.make_label(text, T.FONT_LABEL)

    def _caption(self, text: str) -> QLabel:
        return T.make_label(text, T.FONT_CAPTION)

    def _sound_row(self, label: str, items: list[str]) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setSpacing(T.S_SM)
        lbl = T.make_label(label, T.FONT_BODY)
        lbl.setFixedWidth(60)
        h.addWidget(lbl)
        combo = ArrowComboBox()
        combo.addItems(items)
        combo.setFixedHeight(T.BTN_H)
        h.addWidget(combo, 1)
        h.addWidget(_PlayBtn())
        return h
