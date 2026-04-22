"""
練功水錢計算頁面 — PySide6 版本
追蹤 MapleStory 練功消耗的藥水費用、楓幣變化與經驗值
支援命名存檔、載入、刪除、重命名
"""

import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QSpinBox, QSizePolicy,
    QApplication, QComboBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIntValidator

from src.ui.theme import AppTheme


# ===== 預設藥水資料 =====
_POTION_DEFAULTS = {
    "hp": [
        {"name": "馴鹿奶",   "price": 5600},
        {"name": "乳酪",     "price": 4500},
        {"name": "棒冰棒",   "price": 2185},
        {"name": "中華拉麵", "price": 1600},
        {"name": "烤鰻魚",   "price": 1045},
        {"name": "熱狗堡",   "price": 503},
        {"name": "白水",     "price": 304},
        {"name": "蘋果",     "price": 28},
    ],
    "mp": [
        {"name": "黃昏之露", "price": 9690},
        {"name": "清晨之露", "price": 7695},
        {"name": "紅豆刨冰", "price": 3800},
        {"name": "礦泉水",   "price": 1567},
        {"name": "活力藥水", "price": 589},
        {"name": "藍水",     "price": 190},
    ],
    "combined": [
        {"name": "超級藥水", "price": 35000},
        {"name": "特殊藥水", "price": 24000},
        {"name": "櫻桃派",   "price": 3000},
        {"name": "西瓜",     "price": 3034},
        {"name": "蛋糕",     "price": 304},
        {"name": "巧克力",   "price": 2850},
    ],
}

_SECTION_EMOJI = {"hp": "💊", "mp": "💧", "combined": "✨"}
_SECTION_LABEL = {"hp": "HP 藥水", "mp": "MP 藥水", "combined": "綜合藥水"}

_INT_VALIDATOR_LARGE = (0, 999_999_999)
_INT_VALIDATOR_QTY   = (0, 99_999)

_INPUT_STYLE = (
    f"QLineEdit {{"
    f" background: {AppTheme.BG_TERTIARY};"
    f" color: {AppTheme.TEXT_PRIMARY};"
    f" border: 1px solid {AppTheme.GOLD_MUTED};"
    f" border-radius: 3px;"
    f" padding: 1px 4px;"
    f" font-size: 11px; }}"
    f"QLineEdit:focus {{"
    f" border-color: {AppTheme.GOLD_PRIMARY}; }}"
)


def _make_int_edit(placeholder: str, validator_range: tuple, width: int) -> QLineEdit:
    """建立整數輸入框

    Args:
        placeholder:     提示文字
        validator_range: (min, max)
        width:           固定寬度

    Returns:
        設定好的 QLineEdit
    """
    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    edit.setValidator(QIntValidator(*validator_range))
    edit.setFixedWidth(width)
    edit.setStyleSheet(_INPUT_STYLE)
    return edit


def _parse_int(text: str) -> int:
    """安全解析整數字串，空白或非法視為 0"""
    try:
        return max(0, int(text.strip()))
    except (ValueError, AttributeError):
        return 0


def _fmt(value: int) -> str:
    """格式化整數為千分位顯示"""
    return f"{value:,}"


# ──────────────────────────────────────────────────────────
# _PotionRow：單一藥水列元件
# ──────────────────────────────────────────────────────────

class _PotionRow(QFrame):
    """單一藥水列 — 圖示 + 名稱 + 單價 + 數量前/後 + 自動消耗量/水錢"""

    ROW_H = 34

    def __init__(self, parent, potion_type: str, default_data: dict, on_change, on_remove=None):
        """初始化藥水列

        Args:
            parent:       父元件
            potion_type:  'hp' | 'mp' | 'combined'
            default_data: {"name", "price"}
            on_change:    頁面重算回呼 callable()
            on_remove:    刪除本列回呼 callable(row)
        """
        super().__init__(parent)
        self._on_change = on_change
        self._on_remove = on_remove
        self._potion_type = potion_type
        self.setFixedHeight(self.ROW_H)
        self.setStyleSheet(
            f"QFrame {{"
            f" background: transparent;"
            f" border: none; }}"
        )
        self._build_ui(default_data)

    def _build_ui(self, default_data: dict):
        """建構列 UI"""
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(6)

        # ── 圖示 ──
        emoji_lbl = QLabel(_SECTION_EMOJI.get(self._potion_type, "💊"))
        emoji_lbl.setFixedWidth(20)
        emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_lbl.setStyleSheet("background: transparent; font-size: 14px;")
        lay.addWidget(emoji_lbl)

        # ── 名稱 ──
        self.name_edit = QLineEdit(default_data.get("name", ""))
        self.name_edit.setFixedWidth(100)
        self.name_edit.setStyleSheet(_INPUT_STYLE)
        lay.addWidget(self.name_edit)

        # ── 單價 ──
        price_lbl = QLabel("單價:")
        price_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 10px; background: transparent;"
        )
        lay.addWidget(price_lbl)
        self.price_edit = _make_int_edit(str(default_data.get("price", "")),
                                          _INT_VALIDATOR_LARGE, 90)
        self.price_edit.setText(str(default_data.get("price", "")))
        lay.addWidget(self.price_edit)

        # ── 數量前 ──
        before_lbl = QLabel("前:")
        before_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 10px; background: transparent;"
        )
        lay.addWidget(before_lbl)
        self.before_edit = _make_int_edit("0", _INT_VALIDATOR_QTY, 70)
        lay.addWidget(self.before_edit)

        # ── 數量後 ──
        after_lbl = QLabel("後:")
        after_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 10px; background: transparent;"
        )
        lay.addWidget(after_lbl)
        self.after_edit = _make_int_edit("0", _INT_VALIDATOR_QTY, 70)
        lay.addWidget(self.after_edit)

        # ── 消耗量（自動）──
        consumed_sep = QLabel("消耗:")
        consumed_sep.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 10px; background: transparent;"
        )
        lay.addWidget(consumed_sep)
        self.consumed_lbl = QLabel("0")
        self.consumed_lbl.setFixedWidth(38)
        self.consumed_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.consumed_lbl.setStyleSheet(
            f"color: {AppTheme.ACCENT_YELLOW}; font-size: 11px;"
            f" font-weight: bold; background: transparent;"
        )
        lay.addWidget(self.consumed_lbl)

        # ── 水錢（自動）──
        cost_sep = QLabel("水錢:")
        cost_sep.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 10px; background: transparent;"
        )
        lay.addWidget(cost_sep)
        self.cost_lbl = QLabel("0")
        self.cost_lbl.setMinimumWidth(70)
        self.cost_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.cost_lbl.setStyleSheet(
            f"color: {AppTheme.ACCENT_GREEN}; font-size: 11px;"
            f" font-weight: bold; background: transparent;"
        )
        lay.addWidget(self.cost_lbl)
        lay.addStretch()

        # ── 刪除按鈕 ──
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(22, 22)
        del_btn.setToolTip("刪除此藥水")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(
            f"QPushButton {{"
            f" background: {AppTheme.ACCENT_RED}; color: #fff;"
            f" border: none; border-radius: 3px; font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {AppTheme.ACCENT_RED_HOVER}; }}"
        )
        if self._on_remove:
            del_btn.clicked.connect(lambda: self._on_remove(self))
        lay.addWidget(del_btn)

        # 連接信號
        self.price_edit.textChanged.connect(self._recalc)
        self.before_edit.textChanged.connect(self._recalc)
        self.after_edit.textChanged.connect(self._recalc)

    def _recalc(self):
        """重新計算消耗量與水錢"""
        before   = _parse_int(self.before_edit.text())
        after    = _parse_int(self.after_edit.text())
        price    = _parse_int(self.price_edit.text())
        consumed = max(0, before - after)
        cost     = consumed * price
        self.consumed_lbl.setText(_fmt(consumed))
        self.cost_lbl.setText(_fmt(cost))
        self._on_change()

    def get_cost(self) -> int:
        """回傳本列水錢"""
        before   = _parse_int(self.before_edit.text())
        after    = _parse_int(self.after_edit.text())
        price    = _parse_int(self.price_edit.text())
        return max(0, before - after) * price

    def get_data(self) -> dict:
        """序列化列資料為字典"""
        before   = _parse_int(self.before_edit.text())
        after    = _parse_int(self.after_edit.text())
        price    = _parse_int(self.price_edit.text())
        consumed = max(0, before - after)
        return {
            "name":     self.name_edit.text().strip(),
            "price":    price,
            "before":   before,
            "after":    after,
            "consumed": consumed,
            "cost":     consumed * price,
        }

    def load_data(self, data: dict):
        """從字典還原列資料

        Args:
            data: {"name", "price", "before", "after"}
        """
        self.name_edit.setText(data.get("name", ""))
        self.price_edit.setText(str(data.get("price", "")))
        before = data.get("before", "")
        after  = data.get("after", "")
        self.before_edit.setText(str(before) if before else "")
        self.after_edit.setText(str(after) if after else "")

    def clear_values(self):
        """清空前後數量（保留名稱與單價）"""
        self.before_edit.clear()
        self.after_edit.clear()


# ──────────────────────────────────────────────────────────
# _PotionSection：一類藥水區塊（含 header + rows）
# ──────────────────────────────────────────────────────────

class _PotionSection(QFrame):
    """藥水類型區塊 — 含標頭、藥水列、新增按鈕、小計"""

    def __init__(self, parent, potion_type: str, on_change):
        """初始化藥水區塊

        Args:
            parent:      父元件
            potion_type: 'hp' | 'mp' | 'combined'
            on_change:   頁面重算回呼 callable()
        """
        super().__init__(parent)
        self._potion_type = potion_type
        self._on_change = on_change
        self._rows: list[_PotionRow] = []

        self.setStyleSheet(
            f"QFrame {{"
            f" background-color: {AppTheme.BG_CARD};"
            f" border: 1px solid {AppTheme.BORDER_GOLD_SUBTLE};"
            f" border-radius: {AppTheme.CORNER_MD}px; }}"
        )
        self._build_ui()

    def _build_ui(self):
        """建構區塊 UI"""
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(8, 6, 8, 8)
        self._outer.setSpacing(4)

        # ── 標頭列 ──
        hdr = QWidget()
        hdr.setStyleSheet("background: transparent;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(0, 0, 0, 0)
        hdr_lay.setSpacing(6)

        emoji = _SECTION_EMOJI.get(self._potion_type, "")
        label = _SECTION_LABEL.get(self._potion_type, "")
        title_lbl = QLabel(f"{emoji} {label}")
        title_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 13px; font-weight: bold;"
            f" background: transparent;"
        )
        hdr_lay.addWidget(title_lbl)

        # 分隔線
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sep.setStyleSheet(f"color: {AppTheme.GOLD_MUTED}; background: {AppTheme.GOLD_MUTED};")
        hdr_lay.addWidget(sep)

        # 新增藥水下拉選單
        self._add_combo = QComboBox()
        self._add_combo.setPlaceholderText("＋ 新增藥水")
        self._add_combo.setFixedHeight(22)
        self._add_combo.setFixedWidth(130)
        self._add_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        defaults = _POTION_DEFAULTS.get(self._potion_type, [])
        for d in defaults:
            self._add_combo.addItem(f"{d['name']} (${d['price']:,})")
        self._add_combo.addItem("自訂（空白）")
        self._add_combo.setCurrentIndex(-1)
        self._add_combo.activated.connect(self._on_combo_select)
        hdr_lay.addWidget(self._add_combo)

        # 全部清除按鈕
        clear_all_btn = QPushButton("清除所有")
        clear_all_btn.setFixedHeight(22)
        clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_all_btn.setStyleSheet(
            f"QPushButton {{"
            f" background: {AppTheme.ACCENT_RED}; color: #fff;"
            f" border: none; border-radius: 3px; padding: 0 8px;"
            f" font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {AppTheme.ACCENT_RED_HOVER}; }}"
        )
        clear_all_btn.clicked.connect(self._clear_all_rows)
        hdr_lay.addWidget(clear_all_btn)

        # 小計
        subtotal_lbl = QLabel("合計:")
        subtotal_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px; background: transparent;"
        )
        hdr_lay.addWidget(subtotal_lbl)

        self._subtotal_lbl = QLabel("0")
        self._subtotal_lbl.setMinimumWidth(70)
        self._subtotal_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._subtotal_lbl.setStyleSheet(
            f"color: {AppTheme.ACCENT_RED}; font-size: 12px;"
            f" font-weight: bold; background: transparent;"
        )
        hdr_lay.addWidget(self._subtotal_lbl)

        self._outer.addWidget(hdr)

        # ── 列容器 ──
        self._rows_widget = QWidget()
        self._rows_widget.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(1)
        self._outer.addWidget(self._rows_widget)

    def _add_row(self, default_data: dict):
        """新增一列藥水

        Args:
            default_data: {"name", "price"} 或空字典
        """
        row = _PotionRow(
            self._rows_widget, self._potion_type, default_data,
            self._on_row_change, self._remove_row,
        )
        self._rows_layout.addWidget(row)
        self._rows.append(row)
        self._on_row_change()

    def _on_combo_select(self, index: int):
        """下拉選單選擇後新增藥水列"""
        defaults = _POTION_DEFAULTS.get(self._potion_type, [])
        if index < len(defaults):
            self._add_row(defaults[index])
        else:
            self._add_row({})
        self._add_combo.setCurrentIndex(-1)

    def _remove_row(self, row: _PotionRow):
        """移除單一藥水列"""
        if row in self._rows:
            self._rows.remove(row)
            self._rows_layout.removeWidget(row)
            row.deleteLater()
            self._on_row_change()

    def remove_all_rows(self):
        """移除所有藥水列"""
        for row in self._rows:
            self._rows_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()
        self._on_row_change()

    def _on_row_change(self):
        """任意列變更時更新小計並通知頁面"""
        total = self.get_subtotal()
        self._subtotal_lbl.setText(_fmt(total))
        self._on_change()

    def get_subtotal(self) -> int:
        """回傳所有列水錢合計"""
        return sum(r.get_cost() for r in self._rows)

    def get_data(self) -> list:
        """序列化所有列資料

        Returns:
            資料字典列表
        """
        return [r.get_data() for r in self._rows]

    def load_rows(self, data_list: list):
        """從存檔還原列資料

        Args:
            data_list: 列資料字典列表
        """
        # 清除現有列後依存檔重建
        self.remove_all_rows()
        for row_data in data_list:
            row = _PotionRow(
                self._rows_widget, self._potion_type, {},
                self._on_row_change, self._remove_row,
            )
            self._rows_layout.addWidget(row)
            self._rows.append(row)
            row.load_data(row_data)
        self._on_row_change()

    def clear_rows(self):
        """清空所有列的輸入值（保留列結構與名稱/單價）"""
        for row in self._rows:
            row.clear_values()
        self._on_row_change()


# ──────────────────────────────────────────────────────────
# _QuantityCalcSection：練功水數量計算機
# ──────────────────────────────────────────────────────────

class _QuantityCalcSection(QFrame):
    """練功水數量計算機 — 組數 × 3000 + 剩餘"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedWidth(210)
        self.setStyleSheet(
            f"QFrame {{"
            f" background-color: {AppTheme.BG_CARD};"
            f" border: 2px solid {AppTheme.BORDER_GOLD_SUBTLE};"
            f" border-radius: {AppTheme.CORNER_MD}px; }}"
        )
        self._build_ui()

    def _build_ui(self):
        """建構計算機 UI"""
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)

        # ── 標題列 ──
        title_row = QWidget()
        title_row.setStyleSheet("background: transparent;")
        title_lay = QHBoxLayout(title_row)
        title_lay.setContentsMargins(0, 0, 0, 0)
        title_lay.setSpacing(4)

        title_lbl = QLabel("🧮 數量計算機")
        title_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 12px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        title_lay.addWidget(title_lbl)
        title_lay.addStretch()

        reset_btn = QPushButton("重置")
        reset_btn.setFixedHeight(22)
        reset_btn.setFixedWidth(44)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet(
            f"QPushButton {{"
            f" background: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_SECONDARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: 3px;"
            f" font-size: 10px; }}"
            f"QPushButton:hover {{"
            f" border-color: {AppTheme.GOLD_PRIMARY}; color: {AppTheme.TEXT_GOLD}; }}"
        )
        reset_btn.clicked.connect(self._on_reset)
        title_lay.addWidget(reset_btn)

        lay.addWidget(title_row)

        # ── 分隔線 ──
        sep0 = QFrame()
        sep0.setFixedHeight(1)
        sep0.setStyleSheet(f"background: {AppTheme.GOLD_MUTED}; border: none;")
        lay.addWidget(sep0)

        _lbl_style = (
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
            f" background: transparent; border: none;"
        )
        _hint_style = (
            f"color: {AppTheme.TEXT_MUTED}; font-size: 10px;"
            f" background: transparent; border: none;"
        )

        # ── 組數輸入 ──
        row1 = QWidget()
        row1.setStyleSheet("background: transparent;")
        r1_lay = QHBoxLayout(row1)
        r1_lay.setContentsMargins(0, 0, 0, 0)
        r1_lay.setSpacing(4)

        lbl1 = QLabel("組數")
        lbl1.setStyleSheet(_lbl_style)
        lbl1.setFixedWidth(30)
        r1_lay.addWidget(lbl1)

        self._sets_edit = _make_int_edit("0", _INT_VALIDATOR_LARGE, 64)
        r1_lay.addWidget(self._sets_edit)

        hint1 = QLabel("× 3000")
        hint1.setStyleSheet(_hint_style)
        r1_lay.addWidget(hint1)
        r1_lay.addStretch()

        lay.addWidget(row1)

        # ── 剩餘輸入 ──
        row2 = QWidget()
        row2.setStyleSheet("background: transparent;")
        r2_lay = QHBoxLayout(row2)
        r2_lay.setContentsMargins(0, 0, 0, 0)
        r2_lay.setSpacing(4)

        lbl2 = QLabel("剩餘")
        lbl2.setStyleSheet(_lbl_style)
        lbl2.setFixedWidth(30)
        r2_lay.addWidget(lbl2)

        self._rem_edit = _make_int_edit("0", _INT_VALIDATOR_LARGE, 64)
        r2_lay.addWidget(self._rem_edit)

        hint2 = QLabel("個")
        hint2.setStyleSheet(_hint_style)
        r2_lay.addWidget(hint2)
        r2_lay.addStretch()

        lay.addWidget(row2)

        # ── 分隔線 ──
        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background: {AppTheme.GOLD_MUTED}; border: none;")
        lay.addWidget(sep1)

        # ── 總計列 ──
        total_row = QWidget()
        total_row.setStyleSheet("background: transparent;")
        t_lay = QHBoxLayout(total_row)
        t_lay.setContentsMargins(0, 0, 0, 0)
        t_lay.setSpacing(4)

        total_lbl = QLabel("總計")
        total_lbl.setStyleSheet(_lbl_style)
        total_lbl.setFixedWidth(30)
        t_lay.addWidget(total_lbl)

        self._total_lbl = QLabel("0 個")
        self._total_lbl.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT}; font-size: 12px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        t_lay.addWidget(self._total_lbl)
        t_lay.addStretch()

        copy_btn = QPushButton("📋 複製")
        copy_btn.setFixedHeight(22)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(
            f"QPushButton {{"
            f" background: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_SECONDARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: 3px;"
            f" font-size: 10px; padding: 0 6px; }}"
            f"QPushButton:hover {{"
            f" border-color: {AppTheme.GOLD_PRIMARY}; color: {AppTheme.TEXT_GOLD}; }}"
        )
        copy_btn.clicked.connect(self._on_copy)
        t_lay.addWidget(copy_btn)

        lay.addWidget(total_row)

        # 連接訊號
        self._sets_edit.textChanged.connect(self._recalc)
        self._rem_edit.textChanged.connect(self._recalc)

    def _recalc(self):
        """重新計算總計"""
        sets = _parse_int(self._sets_edit.text())
        rem  = _parse_int(self._rem_edit.text())
        total = sets * 3000 + rem
        self._total_lbl.setText(f"{total:,} 個")

    def _on_copy(self):
        """複製總計數字到剪貼簿"""
        sets  = _parse_int(self._sets_edit.text())
        rem   = _parse_int(self._rem_edit.text())
        total = sets * 3000 + rem
        QApplication.clipboard().setText(str(total))

    def _on_reset(self):
        """重置兩個輸入欄位"""
        self._sets_edit.clear()
        self._rem_edit.clear()
        self._total_lbl.setText("0 個")


# ──────────────────────────────────────────────────────────
# _SummaryPanel：右側只讀摘要面板
# ──────────────────────────────────────────────────────────

class _SummaryPanel(QFrame):
    """練功摘要面板 — 顯示總收入/支出/收支/經驗及每10/60分速率"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedWidth(210)
        self.setStyleSheet(
            f"QFrame {{"
            f" background-color: {AppTheme.BG_CARD};"
            f" border: 2px solid {AppTheme.BORDER_GOLD_SUBTLE};"
            f" border-radius: {AppTheme.CORNER_MD}px; }}"
        )
        self._value_labels: dict[str, QLabel] = {}
        self._build_ui()

    def _build_ui(self):
        """建構摘要面板 UI"""
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        # 標題
        title = QLabel("📊 本次練功摘要")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 13px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        lay.addWidget(title)

        self._add_sep(lay)

        # ── 收支區 ──
        self._add_stat(lay, "income",  "💹 總收入", AppTheme.ACCENT_GREEN)
        self._add_stat(lay, "expense", "💸 總支出", AppTheme.ACCENT_RED)
        self._add_stat(lay, "net",     "📈 總收支", AppTheme.GOLD_LIGHT)

        self._add_sep(lay)

        # ── 每10分鐘 ──
        rate10_lbl = QLabel("每 10 分鐘")
        rate10_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rate10_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
            f" background: transparent; border: none;"
        )
        lay.addWidget(rate10_lbl)
        self._add_stat(lay, "net_10",  "  收支", AppTheme.GOLD_LIGHT, small=True)
        self._add_stat(lay, "exp_10",  "  經驗", AppTheme.ACCENT_YELLOW, small=True)

        self._add_sep(lay)

        # ── 每60分鐘 ──
        rate60_lbl = QLabel("每 60 分鐘")
        rate60_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rate60_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
            f" background: transparent; border: none;"
        )
        lay.addWidget(rate60_lbl)
        self._add_stat(lay, "net_60",  "  收支", AppTheme.GOLD_LIGHT, small=True)
        self._add_stat(lay, "exp_60",  "  經驗", AppTheme.ACCENT_YELLOW, small=True)

        self._add_sep(lay)

        # ── 經驗總計 ──
        self._add_stat(lay, "exp_total", "🌟 總經驗", AppTheme.ACCENT_YELLOW)

        lay.addStretch()

    def _add_sep(self, layout):
        """新增細分隔線"""
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            f"background: {AppTheme.GOLD_MUTED}; border: none;"
        )
        layout.addWidget(sep)

    def _add_stat(self, layout, key: str, label: str, color: str, small: bool = False):
        """新增一個統計列

        Args:
            layout: 父 QVBoxLayout
            key:    值標籤的 dict key
            label:  顯示文字
            color:  數值顏色
            small:  是否為小字體
        """
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        row_lay = QHBoxLayout(row)
        row_lay.setContentsMargins(0, 1, 0, 1)
        row_lay.setSpacing(4)

        name_lbl = QLabel(label)
        name_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY};"
            f" font-size: {'10' if small else '11'}px;"
            f" background: transparent; border: none;"
        )
        row_lay.addWidget(name_lbl)
        row_lay.addStretch()

        val_lbl = QLabel("—")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val_lbl.setStyleSheet(
            f"color: {color};"
            f" font-size: {'10' if small else '12'}px;"
            f" font-weight: bold;"
            f" background: transparent; border: none;"
        )
        row_lay.addWidget(val_lbl)
        self._value_labels[key] = val_lbl
        layout.addWidget(row)

    def refresh(self, totals: dict):
        """更新所有統計值

        Args:
            totals: 包含 income/expense/net/exp_total/net_10/exp_10/net_60/exp_60
        """
        def _set(key: str, value: int, positive_green: bool = True, fixed_color: str = None):
            lbl = self._value_labels.get(key)
            if not lbl:
                return
            lbl.setText(_fmt(value))
            if fixed_color:
                color = fixed_color
            elif positive_green:
                if value > 0:
                    color = AppTheme.ACCENT_GREEN
                elif value < 0:
                    color = AppTheme.ACCENT_RED
                else:
                    color = AppTheme.TEXT_MUTED
            else:
                color = AppTheme.ACCENT_RED if value > 0 else AppTheme.TEXT_MUTED
            lbl.setStyleSheet(
                f"color: {color}; font-weight: bold;"
                f" background: transparent; border: none;"
            )

        _set("income",    totals.get("income",    0), True)
        _set("expense",   totals.get("expense",   0), False)
        _set("net",       totals.get("net",        0), True)
        _set("net_10",    totals.get("net_10",     0), True)
        _set("exp_10",    totals.get("exp_10",     0), fixed_color=AppTheme.ACCENT_YELLOW)
        _set("net_60",    totals.get("net_60",     0), True)
        _set("exp_60",    totals.get("exp_60",     0), fixed_color=AppTheme.ACCENT_YELLOW)
        _set("exp_total", totals.get("exp_total",  0), fixed_color=AppTheme.ACCENT_YELLOW)


# ──────────────────────────────────────────────────────────
# PotionCostPage：主頁面
# ──────────────────────────────────────────────────────────

class PotionCostPage(QWidget):
    """練功水錢計算頁面"""

    def __init__(self, parent, app):
        """初始化頁面

        Args:
            parent: 父元件
            app:    App 主應用實例
        """
        super().__init__(parent)
        self.app = app

        # 計時器狀態
        self._timer_running: bool = False
        self._timer_elapsed: int  = 0   # 已計時秒數
        self._qt_timer = QTimer(self)
        self._qt_timer.setInterval(1000)
        self._qt_timer.timeout.connect(self._on_timer_tick)

        # 自動保存狀態
        self._loading: bool = False
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(500)
        self._autosave_timer.timeout.connect(self._do_autosave)

        self._build_ui()
        self._try_load_autosave()

    def _build_ui(self):
        """建構頁面 UI"""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ===== Header =====
        hdr_outer = QFrame()
        hdr_outer.setObjectName("potion_hdr_outer")
        hdr_outer.setStyleSheet(
            f"QFrame#potion_hdr_outer {{"
            f" background: {AppTheme.BG_SECONDARY};"
            f" border-bottom: 1px solid {AppTheme.GOLD_MUTED}; }}"
        )
        hdr_lay = QHBoxLayout(hdr_outer)
        hdr_lay.setContentsMargins(12, 6, 12, 6)
        hdr_lay.setSpacing(8)

        title_lbl = QLabel("💰 練功水錢")
        title_lbl.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT}; font-size: 14px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        hdr_lay.addWidget(title_lbl)
        hdr_lay.addStretch()

        _BTN_STYLE_NEUTRAL = (
            f"QPushButton {{"
            f" background: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_PRIMARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: 4px;"
            f" padding: 3px 10px; font-size: 11px; }}"
            f"QPushButton:hover {{ border-color: {AppTheme.GOLD_PRIMARY}; color: {AppTheme.TEXT_GOLD}; }}"
        )
        _BTN_STYLE_GREEN = (
            f"QPushButton {{"
            f" background: {AppTheme.ACCENT_GREEN}; color: #fff;"
            f" border: 1px solid {AppTheme.ACCENT_GREEN}; border-radius: 4px;"
            f" padding: 3px 10px; font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {AppTheme.ACCENT_GREEN_HOVER}; }}"
        )
        _BTN_STYLE_GOLD = (
            f"QPushButton {{"
            f" background: {AppTheme.GOLD_DARK}; color: {AppTheme.BG_DEEP};"
            f" border: 1px solid {AppTheme.GOLD_PRIMARY}; border-radius: 4px;"
            f" padding: 3px 10px; font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {AppTheme.GOLD_PRIMARY}; }}"
        )

        clear_btn = QPushButton("🗑 清除")
        clear_btn.setFixedHeight(28)
        clear_btn.setStyleSheet(_BTN_STYLE_NEUTRAL)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._on_clear)
        hdr_lay.addWidget(clear_btn)

        reset_all_btn = QPushButton("🔄 全部重置")
        reset_all_btn.setFixedHeight(28)
        reset_all_btn.setStyleSheet(
            f"QPushButton {{"
            f" background: {AppTheme.ACCENT_RED}; color: #fff;"
            f" border: 1px solid {AppTheme.ACCENT_RED}; border-radius: 4px;"
            f" padding: 3px 10px; font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {AppTheme.ACCENT_RED_HOVER}; }}"
        )
        reset_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_all_btn.clicked.connect(self._on_reset_all)
        hdr_lay.addWidget(reset_all_btn)

        save_btn = QPushButton("💾 儲存")
        save_btn.setFixedHeight(28)
        save_btn.setStyleSheet(_BTN_STYLE_GREEN)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        hdr_lay.addWidget(save_btn)

        load_btn = QPushButton("📂 載入紀錄")
        load_btn.setFixedHeight(28)
        load_btn.setStyleSheet(_BTN_STYLE_GOLD)
        load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        load_btn.clicked.connect(self._on_load)
        hdr_lay.addWidget(load_btn)

        outer.addWidget(hdr_outer)

        # ===== 主體 (左: 表單 | 右: 摘要) =====
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(10, 8, 10, 8)
        body_lay.setSpacing(10)

        # ── 左側: 可捲動表單 ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            f"QScrollBar:vertical {{ background: {AppTheme.BG_SECONDARY}; width: 8px; border: none; }}"
            f"QScrollBar::handle:vertical {{ background: {AppTheme.GOLD_MUTED}; border-radius: 4px; }}"
        )

        form_widget = QWidget()
        form_widget.setStyleSheet("background: transparent;")
        form_lay = QVBoxLayout(form_widget)
        form_lay.setContentsMargins(0, 0, 6, 0)
        form_lay.setSpacing(8)

        # 三個藥水區塊
        self._hp_section       = _PotionSection(form_widget, "hp",       self._recalc_all)
        self._mp_section       = _PotionSection(form_widget, "mp",       self._recalc_all)
        self._combined_section = _PotionSection(form_widget, "combined", self._recalc_all)

        form_lay.addWidget(self._hp_section)
        form_lay.addWidget(self._mp_section)
        form_lay.addWidget(self._combined_section)

        # ── 楓幣 & 經驗 區塊 ──
        form_lay.addWidget(self._build_meso_exp_section(form_widget))

        form_lay.addStretch()
        scroll.setWidget(form_widget)
        body_lay.addWidget(scroll)

        # ── 右側: 摘要面板 + 計算機 ──
        right_widget = QWidget(body)
        right_widget.setFixedWidth(210)
        right_widget.setStyleSheet("background: transparent;")
        right_lay = QVBoxLayout(right_widget)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(8)

        self._summary_panel = _SummaryPanel(right_widget)
        right_lay.addWidget(self._summary_panel)

        self._qty_calc = _QuantityCalcSection(right_widget)
        right_lay.addWidget(self._qty_calc)
        right_lay.addStretch()

        body_lay.addWidget(right_widget, 0, Qt.AlignmentFlag.AlignTop)

        outer.addWidget(body)

    def _build_meso_exp_section(self, parent: QWidget) -> QFrame:
        """建構楓幣/商店/經驗/練功時間區塊

        Returns:
            QFrame 元件
        """
        frame = QFrame(parent)
        frame.setStyleSheet(
            f"QFrame {{"
            f" background-color: {AppTheme.BG_CARD};"
            f" border: 1px solid {AppTheme.BORDER_GOLD_SUBTLE};"
            f" border-radius: {AppTheme.CORNER_MD}px; }}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        # 標題
        me_title = QLabel("💰 楓幣 & 🌟 經驗")
        me_title.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 13px; font-weight: bold;"
            f" background: transparent;"
        )
        lay.addWidget(me_title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {AppTheme.GOLD_MUTED}; border: none;")
        lay.addWidget(sep)

        _LBL = f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px; background: transparent;"
        _AUTO_LBL = (
            f"color: {AppTheme.ACCENT_GREEN}; font-size: 12px;"
            f" font-weight: bold; background: transparent;"
        )

        def _row(*widgets) -> QWidget:
            w = QWidget()
            w.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(w)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(8)
            for wgt in widgets:
                rl.addWidget(wgt)
            rl.addStretch()
            return w

        def _lbl(text, style=_LBL) -> QLabel:
            l = QLabel(text)
            l.setStyleSheet(style)
            return l

        def _auto_lbl(key: str) -> QLabel:
            l = QLabel("0")
            l.setStyleSheet(_AUTO_LBL)
            l.setMinimumWidth(80)
            setattr(self, key, l)
            return l

        # 楓幣列
        self._mesos_start_edit = _make_int_edit("初始楓幣", _INT_VALIDATOR_LARGE, 100)
        self._mesos_end_edit   = _make_int_edit("練完楓幣", _INT_VALIDATOR_LARGE, 100)
        lay.addWidget(_row(
            _lbl("初始楓幣:"), self._mesos_start_edit,
            _lbl("練完楓幣:"), self._mesos_end_edit,
        ))
        lay.addWidget(_row(_lbl("撿取楓幣 (自動):"), _auto_lbl("_mesos_pickup_lbl")))

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {AppTheme.BG_TERTIARY}; border: none;")
        lay.addWidget(sep2)

        # 商店列
        self._shop_before_edit = _make_int_edit("賣裝前", _INT_VALIDATOR_LARGE, 100)
        self._shop_after_edit  = _make_int_edit("賣裝後", _INT_VALIDATOR_LARGE, 100)
        lay.addWidget(_row(
            _lbl("商店賣裝前:"), self._shop_before_edit,
            _lbl("賣裝後:"), self._shop_after_edit,
        ))
        lay.addWidget(_row(_lbl("裝備掉落物收益 (自動):"), _auto_lbl("_shop_profit_lbl")))

        sep3 = QFrame()
        sep3.setFixedHeight(1)
        sep3.setStyleSheet(f"background: {AppTheme.BG_TERTIARY}; border: none;")
        lay.addWidget(sep3)

        # 經驗列
        self._exp_start_edit = _make_int_edit("初始經驗", _INT_VALIDATOR_LARGE, 100)
        self._exp_end_edit   = _make_int_edit("練完經驗", _INT_VALIDATOR_LARGE, 100)
        lay.addWidget(_row(
            _lbl("初始經驗:"), self._exp_start_edit,
            _lbl("練完經驗:"), self._exp_end_edit,
        ))
        lay.addWidget(_row(_lbl("獲取經驗 (自動):"), _auto_lbl("_exp_gained_lbl")))

        sep4 = QFrame()
        sep4.setFixedHeight(1)
        sep4.setStyleSheet(f"background: {AppTheme.BG_TERTIARY}; border: none;")
        lay.addWidget(sep4)

        # ── 練功時間（雙模式）──
        _SPIN_STYLE = (
            f"QSpinBox {{"
            f" background: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_PRIMARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: 3px;"
            f" padding: 1px 4px; font-size: 11px; }}"
            f"QSpinBox:focus {{ border-color: {AppTheme.GOLD_PRIMARY}; }}"
            f"QSpinBox::up-button, QSpinBox::down-button {{ width: 16px; }}"
        )
        _TAB_ACTIVE = (
            f"QPushButton {{"
            f" background: {AppTheme.GOLD_DARK}; color: {AppTheme.BG_DEEP};"
            f" border: 1px solid {AppTheme.GOLD_PRIMARY};"
            f" border-radius: 3px; padding: 2px 8px; font-size: 10px; font-weight: bold; }}"
        )
        _TAB_INACTIVE = (
            f"QPushButton {{"
            f" background: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_MUTED};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 3px; padding: 2px 8px; font-size: 10px; }}"
            f"QPushButton:hover {{ color: {AppTheme.TEXT_PRIMARY}; }}"
        )

        # 標籤 + 模式切換按鈕
        time_header = QWidget()
        time_header.setStyleSheet("background: transparent;")
        th_lay = QHBoxLayout(time_header)
        th_lay.setContentsMargins(0, 0, 0, 0)
        th_lay.setSpacing(6)
        th_lay.addWidget(_lbl("⏱ 練功時間:"))
        th_lay.addStretch()

        self._mode_manual_btn = QPushButton("📝 手動")
        self._mode_manual_btn.setFixedHeight(22)
        self._mode_manual_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mode_manual_btn.setStyleSheet(_TAB_ACTIVE)
        self._mode_manual_btn.clicked.connect(self._switch_to_manual_mode)
        th_lay.addWidget(self._mode_manual_btn)

        self._mode_timer_btn = QPushButton("⏱ 計時器")
        self._mode_timer_btn.setFixedHeight(22)
        self._mode_timer_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mode_timer_btn.setStyleSheet(_TAB_INACTIVE)
        self._mode_timer_btn.clicked.connect(self._switch_to_timer_mode)
        th_lay.addWidget(self._mode_timer_btn)

        lay.addWidget(time_header)

        # SpinBox（手動模式）
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 9999)
        self._duration_spin.setValue(60)
        self._duration_spin.setSuffix(" 分鐘")
        self._duration_spin.setFixedWidth(110)
        self._duration_spin.setStyleSheet(_SPIN_STYLE)

        self._manual_row = _row(_lbl("時長:"), self._duration_spin)
        lay.addWidget(self._manual_row)

        # 計時器模式 widget（預設隱藏）
        self._timer_widget = QWidget()
        self._timer_widget.setStyleSheet("background: transparent;")
        tw_lay = QHBoxLayout(self._timer_widget)
        tw_lay.setContentsMargins(0, 0, 0, 0)
        tw_lay.setSpacing(8)

        self._timer_display = QLabel("00:00:00")
        self._timer_display.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT}; font-size: 18px; font-weight: bold;"
            f" background: transparent; font-family: monospace;"
        )
        tw_lay.addWidget(self._timer_display)
        tw_lay.addSpacing(8)

        self._start_stop_btn = QPushButton("▶ 開始")
        self._start_stop_btn.setFixedHeight(28)
        self._start_stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_stop_btn.setStyleSheet(
            f"QPushButton {{"
            f" background: {AppTheme.ACCENT_GREEN}; color: #fff;"
            f" border: none; border-radius: 4px;"
            f" padding: 3px 12px; font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {AppTheme.ACCENT_GREEN_HOVER}; }}"
        )
        self._start_stop_btn.clicked.connect(self._toggle_timer)
        tw_lay.addWidget(self._start_stop_btn)

        reset_btn = QPushButton("↺")
        reset_btn.setFixedSize(28, 28)
        reset_btn.setToolTip("重置計時器")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none;"
            f" color: {AppTheme.TEXT_SECONDARY}; font-size: 14px; }}"
            f"QPushButton:hover {{ color: {AppTheme.ACCENT_RED};"
            f" background: {AppTheme.BG_TERTIARY}; border-radius: 3px; }}"
        )
        reset_btn.clicked.connect(self._reset_timer)
        tw_lay.addWidget(reset_btn)

        self._timer_result_lbl = QLabel("")
        self._timer_result_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 10px; background: transparent;"
        )
        tw_lay.addWidget(self._timer_result_lbl)
        tw_lay.addStretch()

        self._timer_widget.setVisible(False)
        lay.addWidget(self._timer_widget)

        # 連接信號
        for edit in [
            self._mesos_start_edit, self._mesos_end_edit,
            self._shop_before_edit, self._shop_after_edit,
            self._exp_start_edit, self._exp_end_edit,
        ]:
            edit.textChanged.connect(self._recalc_all)
        self._duration_spin.valueChanged.connect(self._recalc_all)

        return frame

    # ──────────────────────────────────────────────────────
    # 練功時間模式切換 & 計時器
    # ──────────────────────────────────────────────────────

    def _switch_to_manual_mode(self):
        """切換至手動輸入模式"""
        self._stop_timer_if_running()
        self._manual_row.setVisible(True)
        self._timer_widget.setVisible(False)
        _TAB_ACTIVE = (
            f"QPushButton {{"
            f" background: {AppTheme.GOLD_DARK}; color: {AppTheme.BG_DEEP};"
            f" border: 1px solid {AppTheme.GOLD_PRIMARY};"
            f" border-radius: 3px; padding: 2px 8px; font-size: 10px; font-weight: bold; }}"
        )
        _TAB_INACTIVE = (
            f"QPushButton {{"
            f" background: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_MUTED};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 3px; padding: 2px 8px; font-size: 10px; }}"
            f"QPushButton:hover {{ color: {AppTheme.TEXT_PRIMARY}; }}"
        )
        self._mode_manual_btn.setStyleSheet(_TAB_ACTIVE)
        self._mode_timer_btn.setStyleSheet(_TAB_INACTIVE)

    def _switch_to_timer_mode(self):
        """切換至計時器模式"""
        self._manual_row.setVisible(False)
        self._timer_widget.setVisible(True)
        _TAB_ACTIVE = (
            f"QPushButton {{"
            f" background: {AppTheme.GOLD_DARK}; color: {AppTheme.BG_DEEP};"
            f" border: 1px solid {AppTheme.GOLD_PRIMARY};"
            f" border-radius: 3px; padding: 2px 8px; font-size: 10px; font-weight: bold; }}"
        )
        _TAB_INACTIVE = (
            f"QPushButton {{"
            f" background: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_MUTED};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 3px; padding: 2px 8px; font-size: 10px; }}"
            f"QPushButton:hover {{ color: {AppTheme.TEXT_PRIMARY}; }}"
        )
        self._mode_manual_btn.setStyleSheet(_TAB_INACTIVE)
        self._mode_timer_btn.setStyleSheet(_TAB_ACTIVE)

    def _toggle_timer(self):
        """開始/停止計時器"""
        if self._timer_running:
            self._stop_timer_if_running()
        else:
            self._timer_elapsed = 0
            self._timer_running = True
            self._qt_timer.start()
            self._start_stop_btn.setText("⏹ 停止")
            self._start_stop_btn.setStyleSheet(
                f"QPushButton {{"
                f" background: {AppTheme.ACCENT_RED}; color: #fff;"
                f" border: none; border-radius: 4px;"
                f" padding: 3px 12px; font-size: 11px; font-weight: bold; }}"
                f"QPushButton:hover {{ background: #dc2626; }}"
            )
            self._timer_result_lbl.setText("")
            self._update_timer_display()

    def _stop_timer_if_running(self):
        """停止計時器並將結果寫入 SpinBox"""
        if not self._timer_running:
            return
        self._qt_timer.stop()
        self._timer_running = False
        minutes = max(1, self._timer_elapsed // 60)
        self._duration_spin.setValue(minutes)
        self._start_stop_btn.setText("▶ 開始")
        self._start_stop_btn.setStyleSheet(
            f"QPushButton {{"
            f" background: {AppTheme.ACCENT_GREEN}; color: #fff;"
            f" border: none; border-radius: 4px;"
            f" padding: 3px 12px; font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {AppTheme.ACCENT_GREEN_HOVER}; }}"
        )
        self._timer_result_lbl.setText(f"→ 已記錄 {minutes} 分鐘")

    def _reset_timer(self):
        """重置計時器"""
        self._stop_timer_if_running()
        self._timer_elapsed = 0
        self._update_timer_display()
        self._timer_result_lbl.setText("")

    def _on_timer_tick(self):
        """每秒觸發：更新顯示"""
        self._timer_elapsed += 1
        self._update_timer_display()
        # 每分鐘更新一次摘要速率
        if self._timer_elapsed % 60 == 0:
            self._duration_spin.setValue(max(1, self._timer_elapsed // 60))

    def _update_timer_display(self):
        """更新計時顯示字串 HH:MM:SS"""
        h = self._timer_elapsed // 3600
        m = (self._timer_elapsed % 3600) // 60
        s = self._timer_elapsed % 60
        self._timer_display.setText(f"{h:02d}:{m:02d}:{s:02d}")

    # ──────────────────────────────────────────────────────

    def _recalc_all(self):
        """重新計算所有匯總值並更新摘要面板與自動欄位"""
        hp_total  = self._hp_section.get_subtotal()
        mp_total  = self._mp_section.get_subtotal()
        cmb_total = self._combined_section.get_subtotal()
        expense   = hp_total + mp_total + cmb_total

        mesos_start   = _parse_int(self._mesos_start_edit.text())
        mesos_end     = _parse_int(self._mesos_end_edit.text())
        mesos_pickup  = max(0, mesos_end - mesos_start)

        shop_before   = _parse_int(self._shop_before_edit.text())
        shop_after    = _parse_int(self._shop_after_edit.text())
        shop_profit   = max(0, shop_after - shop_before)

        exp_start     = _parse_int(self._exp_start_edit.text())
        exp_end       = _parse_int(self._exp_end_edit.text())
        exp_gained    = max(0, exp_end - exp_start)

        income  = mesos_pickup + shop_profit
        net     = income - expense
        minutes = max(1, self._duration_spin.value())

        # 更新自動欄位
        self._mesos_pickup_lbl.setText(_fmt(mesos_pickup))
        self._shop_profit_lbl.setText(_fmt(shop_profit))
        self._exp_gained_lbl.setText(_fmt(exp_gained))

        # 更新摘要面板
        self._summary_panel.refresh({
            "income":    income,
            "expense":   expense,
            "net":       net,
            "exp_total": exp_gained,
            "net_10":    int(net / minutes * 10),
            "exp_10":    int(exp_gained / minutes * 10),
            "net_60":    int(net / minutes * 60),
            "exp_60":    int(exp_gained / minutes * 60),
        })

        # 排程自動保存（載入中時略過）
        if not self._loading:
            self._autosave_timer.start()

    # ──────────────────────────────────────────────────────
    # 自動保存
    # ──────────────────────────────────────────────────────

    def _do_autosave(self):
        """執行自動保存（寫入獨立的 autosave 檔）"""
        if self._loading:
            return
        data = self.get_form_data()
        data["_timer_elapsed"] = self._timer_elapsed
        self.app.config_manager.save_potion_autosave(data)

    def _try_load_autosave(self):
        """嘗試還原上次的自動保存內容"""
        record = self.app.config_manager.load_potion_autosave()
        if not record:
            return

        self._loading = True
        try:
            self.load_form_data(record)
            # 還原計時器秒數（不自動續跑；使用者按開始才繼續）
            elapsed = int(record.get("_timer_elapsed", 0) or 0)
            if elapsed > 0:
                self._timer_elapsed = elapsed
                self._update_timer_display()
        finally:
            self._loading = False
        self._recalc_all()
        if getattr(self.app, "toast", None):
            self.app.toast.show("已還原上次編輯內容", "info")

    def _clear_autosave(self):
        """刪除自動保存檔"""
        self.app.config_manager.delete_potion_autosave()

    def _on_reset_all(self):
        """全部重置 — 清空所有藥水列、所有輸入、計時器，並刪除自動保存"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "確認重置",
            "確定要重置所有資料嗎？\n（所有藥水列與輸入值都會清空，且無法復原）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._loading = True
        try:
            # 清空三個區塊所有藥水列
            self._hp_section.remove_all_rows()
            self._mp_section.remove_all_rows()
            self._combined_section.remove_all_rows()
            # 清空楓幣/商店/經驗欄位
            for edit in [
                self._mesos_start_edit, self._mesos_end_edit,
                self._shop_before_edit, self._shop_after_edit,
                self._exp_start_edit, self._exp_end_edit,
            ]:
                edit.clear()
            # 重置計時器與時長
            self._reset_timer()
            self._duration_spin.setValue(60)
        finally:
            self._loading = False

        # 取消任何排程中的 autosave（避免剛 delete 又被寫回空檔）
        self._autosave_timer.stop()
        self._clear_autosave()
        # 直接更新摘要面板，不走 _recalc_all 以免重新排程 autosave
        self._recalc_all_no_autosave()

    def _recalc_all_no_autosave(self):
        """重算一次摘要但不排程 autosave"""
        self._loading = True
        try:
            self._recalc_all()
        finally:
            self._loading = False

    # ──────────────────────────────────────────────────────
    # 存檔 / 載入
    # ──────────────────────────────────────────────────────

    def _on_save(self):
        """開啟儲存對話框"""
        from src.ui.dialogs.potion_save_dialog import PotionSaveDialog
        data = self.get_form_data()
        dlg = PotionSaveDialog(self, self.app.config_manager, mode="save", current_data=data, app=self.app)
        dlg.exec()

    def _on_load(self):
        """開啟載入紀錄對話框"""
        from src.ui.dialogs.potion_save_dialog import PotionSaveDialog
        dlg = PotionSaveDialog(self, self.app.config_manager, mode="load", app=self.app)
        from PySide6.QtWidgets import QDialog
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_data:
            self._loading = True
            try:
                self.load_form_data(dlg.result_data)
            finally:
                self._loading = False
            # 載入完成後才觸發一次 autosave，覆寫成使用者明確選擇的版本
            self._do_autosave()

    def _on_clear(self):
        """清空所有輸入值"""
        self._hp_section.clear_rows()
        self._mp_section.clear_rows()
        self._combined_section.clear_rows()
        for edit in [
            self._mesos_start_edit, self._mesos_end_edit,
            self._shop_before_edit, self._shop_after_edit,
            self._exp_start_edit, self._exp_end_edit,
        ]:
            edit.clear()
        self._reset_timer()
        self._duration_spin.setValue(60)
        self._recalc_all()

    # ──────────────────────────────────────────────────────
    # 序列化 / 還原
    # ──────────────────────────────────────────────────────

    def get_form_data(self) -> dict:
        """序列化表單為存檔字典

        Returns:
            完整資料字典
        """
        mesos_start  = _parse_int(self._mesos_start_edit.text())
        mesos_end    = _parse_int(self._mesos_end_edit.text())
        shop_before  = _parse_int(self._shop_before_edit.text())
        shop_after   = _parse_int(self._shop_after_edit.text())
        exp_start    = _parse_int(self._exp_start_edit.text())
        exp_end      = _parse_int(self._exp_end_edit.text())
        minutes      = self._duration_spin.value()

        hp_total  = self._hp_section.get_subtotal()
        mp_total  = self._mp_section.get_subtotal()
        cmb_total = self._combined_section.get_subtotal()
        expense   = hp_total + mp_total + cmb_total
        income    = max(0, mesos_end - mesos_start) + max(0, shop_after - shop_before)
        net       = income - expense
        exp       = max(0, exp_end - exp_start)

        return {
            "saved_at":        datetime.datetime.now().isoformat(timespec="seconds"),
            "duration_minutes": minutes,
            "hp_potions":      self._hp_section.get_data(),
            "mp_potions":      self._mp_section.get_data(),
            "combined_potions": self._combined_section.get_data(),
            "mesos_start":     mesos_start,
            "mesos_end":       mesos_end,
            "shop_before":     shop_before,
            "shop_after":      shop_after,
            "exp_start":       exp_start,
            "exp_end":         exp_end,
            "summary": {
                "total_income":  income,
                "total_expense": expense,
                "net":           net,
                "exp_gained":    exp,
            },
        }

    def load_form_data(self, data: dict):
        """從存檔字典還原表單

        Args:
            data: get_form_data() 格式的字典
        """
        self._hp_section.load_rows(data.get("hp_potions", []))
        self._mp_section.load_rows(data.get("mp_potions", []))
        self._combined_section.load_rows(data.get("combined_potions", []))

        def _set_edit(edit: QLineEdit, key: str):
            val = data.get(key, "")
            edit.setText(str(val) if val else "")

        _set_edit(self._mesos_start_edit, "mesos_start")
        _set_edit(self._mesos_end_edit,   "mesos_end")
        _set_edit(self._shop_before_edit, "shop_before")
        _set_edit(self._shop_after_edit,  "shop_after")
        _set_edit(self._exp_start_edit,   "exp_start")
        _set_edit(self._exp_end_edit,     "exp_end")

        minutes = data.get("duration_minutes", 60)
        self._duration_spin.setValue(max(1, int(minutes)) if minutes else 60)
        self._recalc_all()
