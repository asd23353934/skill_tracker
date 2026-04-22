"""
V2 狀態列 — 26px 高，極簡
左：配置名（楓葉點綴） | 中：提示訊息 | 右：版本 + resize grip
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizeGrip
from src.ui_v2.theme_v2 import V2Theme as T


class StatusBarV2(QFrame):
    """極簡狀態列"""

    def __init__(self, parent, profile_name="默認配置", version="0.0.0"):
        super().__init__(parent)
        self._build(profile_name, version)

    def _build(self, profile_name, version):
        self.setFixedHeight(T.STATUS_H)
        self.setObjectName("status_v2")
        self.setStyleSheet(
            f"QFrame#status_v2 {{"
            f" background: {T.BG_SURFACE};"
            f" border-top: 1px solid {T.BORDER}; }}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 4, 0)
        lay.setSpacing(8)

        # 左：配置名
        dot = QLabel("●")
        dot.setStyleSheet(
            f"color: {T.GREEN}; font-size: 10px; background: transparent;"
        )
        lay.addWidget(dot)

        self.profile_lbl = QLabel(profile_name)
        self.profile_lbl.setStyleSheet(
            f"color: {T.TEXT}; font-size: 11px; background: transparent;"
        )
        lay.addWidget(self.profile_lbl)

        # 分隔
        sep = QLabel("·")
        sep.setStyleSheet(
            f"color: {T.TEXT_MUTED}; background: transparent;"
        )
        lay.addWidget(sep)

        # 中：提示訊息
        self.msg_lbl = QLabel("")
        self.msg_lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
        )
        lay.addWidget(self.msg_lbl)

        lay.addStretch()

        # 右：版本
        ver = QLabel(f"v{version}")
        ver.setStyleSheet(
            f"color: {T.TEXT_MUTED}; font-size: 10px; background: transparent;"
            f" padding-right: 8px;"
        )
        lay.addWidget(ver)

        # resize grip（右下角原生）
        grip = QSizeGrip(self)
        grip.setStyleSheet("background: transparent;")
        lay.addWidget(grip)

    def set_profile(self, name: str):
        self.profile_lbl.setText(name)

    def set_message(self, text: str):
        self.msg_lbl.setText(text)
