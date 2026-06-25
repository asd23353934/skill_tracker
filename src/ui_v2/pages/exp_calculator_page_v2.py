"""經驗值計算器頁 — V2（升級時間估算）

輸入：目前等級、目前經驗 %、目標等級、經驗來源（每小時經驗 或 每隻經驗 × 每小時隻數）。
結果：還需總經驗、距下一級還需、需打隻數、預估時間。

計算全部委派給 src/domain/exp_service.py（零 Qt 純邏輯）；本頁僅收集輸入、即時重算、顯示。
不持久化輸入（見提案 Non-Goals）。

建構參數：
    ExpCalculatorPageV2(parent=None, app=None)
        app 目前未使用（無持久化）；保留簽名與其他頁一致。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QSpinBox,
    QDoubleSpinBox, QLineEdit, QComboBox,
)
from PySide6.QtCore import Qt

from src.domain import exp_service
from src.domain.exp_table import MAX_LEVEL
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import IconBadge


def _fmt(value: int) -> str:
    return f"{value:,}"


def _parse_int(text: str) -> int:
    """安全解析整數字串；空白、非法、負值一律回 0"""
    try:
        return max(0, int((text or "").strip().replace(",", "")))
    except (ValueError, AttributeError):
        return 0


class ExpCalculatorPageV2(QWidget):
    """經驗值計算器頁 — V2"""

    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self._result_labels: dict[str, QLabel] = {}
        self._build()
        self._recalc()

    # ════════════════════════════════════════════════════════
    # UI
    # ════════════════════════════════════════════════════════
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        root.addWidget(T.make_label("經驗值計算器", T.FONT_SECTION))
        hint = QLabel("輸入目前等級與經驗、目標等級、練功效率，估算升級還需的經驗與時間。")
        hint.setTextFormat(Qt.TextFormat.PlainText)
        hint.setStyleSheet(f"color: {T.TEXT_DIM}; background: transparent; font-size: 12px;")
        root.addWidget(hint)

        body = QHBoxLayout()
        body.setSpacing(T.S_LG)
        body.addWidget(self._build_input_card(), 1)
        body.addWidget(self._build_result_card(), 1)
        root.addLayout(body)
        root.addStretch()

    # ── 共用樣式 helper ──
    def _spin(self, lo: int, hi: int, value: int) -> QSpinBox:
        sp = QSpinBox()
        sp.setRange(lo, hi)
        sp.setValue(value)
        sp.setFixedHeight(28)
        sp.setStyleSheet(
            f"QSpinBox {{ color: {T.TEXT_HI}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 8px; font-size: 12px; }}"
            f"QSpinBox:focus {{ border-color: {T.ORANGE}; }}")
        sp.valueChanged.connect(self._recalc)
        return sp

    def _line(self, placeholder: str = "") -> QLineEdit:
        le = QLineEdit()
        le.setFixedHeight(28)
        le.setPlaceholderText(placeholder)
        le.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        le.setStyleSheet(
            f"QLineEdit {{ color: {T.TEXT_HI}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 8px; font-size: 12px; }}"
            f"QLineEdit:focus {{ border-color: {T.ORANGE}; }}")
        le.textChanged.connect(self._recalc)
        return le

    def _field_row(self, label: str, widget: QWidget, suffix: str = "") -> QWidget:
        row = QHBoxLayout()
        row.setSpacing(T.S_SM)
        lbl = QLabel(label)
        lbl.setFixedWidth(96)
        lbl.setStyleSheet(
            f"color: {T.TEXT}; font-size: 12px; font-weight: 600; background: transparent;")
        row.addWidget(lbl)
        row.addWidget(widget, 1)
        if suffix:
            sfx = QLabel(suffix)
            sfx.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: 12px; background: transparent;")
            row.addWidget(sfx)
        wrap = QWidget()
        wrap.setLayout(row)
        return wrap

    def _card(self, title: str, icon: str, accent: str) -> tuple[QFrame, QVBoxLayout]:
        f = QFrame()
        f.setObjectName("sec_card")
        f.setStyleSheet(
            f"QFrame#sec_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_LG}px; }}")
        L = QVBoxLayout(f)
        L.setContentsMargins(T.S_LG, T.S_MD, T.S_LG, T.S_MD)
        L.setSpacing(T.S_MD)
        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(IconBadge(icon, accent, 28))
        head.addWidget(T.make_label(title, T.FONT_CARD_TITLE))
        head.addStretch()
        L.addLayout(head)
        return f, L

    # ── 輸入卡 ──
    def _build_input_card(self) -> QFrame:
        card, L = self._card("輸入", "calculator", T.ORANGE)

        self._level_spin = self._spin(1, MAX_LEVEL, 1)
        self._pct_spin = QDoubleSpinBox()
        self._pct_spin.setRange(0.0, 100.0)
        self._pct_spin.setDecimals(2)
        self._pct_spin.setValue(0.0)
        self._pct_spin.setSuffix(" %")
        self._pct_spin.setFixedHeight(28)
        self._pct_spin.setStyleSheet(
            f"QDoubleSpinBox {{ color: {T.TEXT_HI}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 8px; font-size: 12px; }}"
            f"QDoubleSpinBox:focus {{ border-color: {T.ORANGE}; }}")
        self._pct_spin.valueChanged.connect(self._recalc)
        self._target_spin = self._spin(1, MAX_LEVEL, 2)

        L.addWidget(self._field_row("目前等級", self._level_spin))
        L.addWidget(self._field_row("目前經驗", self._pct_spin))
        L.addWidget(self._field_row("目標等級", self._target_spin))

        # 練功效率：在 N 分鐘內獲得的經驗（[經驗] / 每 [10分/30分/1小時]）
        self._exp_input = self._line("例如 500000")
        self._interval_combo = QComboBox()
        self._interval_combo.setFixedHeight(28)
        self._interval_combo.setMinimumWidth(96)
        self._interval_combo.setStyleSheet(
            T.combo_qss(bg=T.BG_INPUT, border=T.BORDER, padding="0 8px"))
        for label, mins in (("10 分鐘", 10), ("30 分鐘", 30), ("1 小時", 60)):
            self._interval_combo.addItem(label, mins)
        self._interval_combo.setCurrentIndex(0)
        self._interval_combo.currentIndexChanged.connect(self._recalc)

        rate_row = QHBoxLayout()
        rate_row.setSpacing(T.S_SM)
        rlbl = QLabel("練功效率")
        rlbl.setFixedWidth(96)
        rlbl.setStyleSheet(
            f"color: {T.TEXT}; font-size: 12px; font-weight: 600; background: transparent;")
        rate_row.addWidget(rlbl)
        rate_row.addWidget(self._exp_input, 1)
        slash = QLabel("經驗 / 每")
        slash.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;")
        rate_row.addWidget(slash)
        rate_row.addWidget(self._interval_combo)
        rw = QWidget()
        rw.setLayout(rate_row)
        L.addWidget(rw)

        L.addStretch()
        return card

    # ── 結果卡 ──
    def _build_result_card(self) -> QFrame:
        card, L = self._card("結果", "trending-up", T.GREEN)

        def add_line(label: str, key: str, color: str, big: bool = False):
            row = QHBoxLayout()
            row.setSpacing(T.S_SM)
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color: {T.TEXT_DIM}; font-size: 12px; background: transparent;")
            row.addWidget(lbl)
            row.addStretch()
            val = QLabel("0")
            size = 18 if big else 13
            val.setStyleSheet(
                f"color: {color}; font-size: {size}px; font-weight: 700;"
                f" background: transparent;")
            row.addWidget(val)
            L.addLayout(row)
            self._result_labels[key] = val

        add_line("還需總經驗", "total", T.PURPLE, big=True)
        add_line("距下一級還需", "in_level", T.CYAN)
        add_line("預估時間", "time", T.GREEN, big=True)
        L.addStretch()
        return card

    # ════════════════════════════════════════════════════════
    # 計算
    # ════════════════════════════════════════════════════════
    def _recalc(self, *_):
        level = self._level_spin.value()
        pct = self._pct_spin.value()
        target = self._target_spin.value()
        exp_per_interval = _parse_int(self._exp_input.text())
        minutes = self._interval_combo.currentData() or 60

        total = exp_service.exp_remaining(level, pct, target)
        in_level = exp_service.exp_remaining_in_level(level, pct)
        rate = exp_service.hourly_rate(exp_per_interval, minutes)
        time_str = exp_service.format_duration(exp_service.time_hours(total, rate))

        self._result_labels["total"].setText(_fmt(total))
        self._result_labels["in_level"].setText(_fmt(in_level))
        self._result_labels["time"].setText(time_str)
