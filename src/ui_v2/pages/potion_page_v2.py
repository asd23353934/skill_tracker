"""
練功收支頁面 — V2（已接線，透過 PotionService）
左：支出（藥水，前/後以組數輸入器填）｜右：收入（物品取得）｜下方：本次收支總結（淨收益＝收入−支出）
數量輸入器 _StackQty：組數 × 組大小(3000/9900) + 餘數；楓幣等收入由使用者以項目列自行加入
依 docs/DESIGN_V2.md

══════════════════════════════════════════════════════════════
綁定契約
══════════════════════════════════════════════════════════════
建構參數：
    PotionPageV2(parent, app)

讀取：
    預設藥水目錄:   PotionService.DEFAULTS
    autosave:      app.config_manager.load_potion_autosave()（由 PotionService 轉發）
    紀錄列表:       app.config_manager.list_potion_saves()
    單筆紀錄:       app.config_manager.load_potion_record(name)

操作：
    [新增藥水/清除全部]   → 更新本地 state，觸發重算 + autosave
    [輸入欄變更]          → 即時重算右側摘要 + autosave (debounce 500ms)
    [清除]                → 清空所有輸入，保留 autosave
    [全部重置]            → 清空所有輸入 + 計時 + 刪除 autosave
    [載入紀錄]            → PotionLoadDialogV2 → load_potion_record
    [儲存]                → PotionSaveDialogV2 → save_potion_record(name, data)
    [手動/計時器]         → toggle 練功時間來源；計時器模式下 QTimer 1s tick

寫回：
    所有變更寫入 autosave（potion_autosave.json，與 V1 共用，最後寫入者勝）；
    具名儲存才寫紀錄檔
"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QScrollArea, QLineEdit, QMessageBox, QDialog, QComboBox,
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QPixmap

from src.domain.potion_service import PotionService
from src.domain import training_maps
from src.infrastructure.helpers import resource_path
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import IconBadge
from src.ui_v2.lucide import lucide_icon
from src.ui_v2.dialogs import PotionSaveDialogV2, PotionLoadDialogV2

# 道具圖示快取（item_id → 縮放後 QPixmap）；打包於 images/item_icons/<id>.png
_ITEM_ICON_DIR = resource_path(os.path.join("images", "item_icons"))
_item_icon_cache: dict[tuple, QPixmap] = {}


def _item_icon(item_id, size: int = 26):
    """載入道具圖示 QPixmap（依 maplestory.io item_id）；無對應檔回 None。"""
    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        return None
    if item_id <= 0:
        return None
    key = (item_id, size)
    if key in _item_icon_cache:
        return _item_icon_cache[key]
    path = os.path.join(_ITEM_ICON_DIR, f"{item_id}.png")
    pix = QPixmap(path) if os.path.exists(path) else QPixmap()
    if pix.isNull():
        _item_icon_cache[key] = None
        return None
    pix = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                     Qt.TransformationMode.SmoothTransformation)
    _item_icon_cache[key] = pix
    return pix


# ════════════════════════════════════════════════════════════
# 格式化 helpers
# ════════════════════════════════════════════════════════════

def _parse_int(text: str) -> int:
    """安全解析整數字串；空白、非法、負值一律回 0"""
    try:
        return max(0, int((text or "").strip().replace(",", "")))
    except (ValueError, AttributeError):
        return 0


def _as_int(value) -> int:
    """把存檔可能來的 int / float / str / None 安全轉成非負整數；非法一律回 0。

    存檔（potion_autosave）若被手改或寫入中斷而含非數值欄位，載入時不應讓整頁崩潰。
    字串走 _parse_int（吃逗號、空白）；數值直接夾為非負；其餘（None…）回 0。
    """
    if isinstance(value, str):
        return _parse_int(value)
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _fmt(value: int) -> str:
    return f"{value:,}"


def _fmt_signed(value: int) -> str:
    return f"{value:+,}"


# ════════════════════════════════════════════════════════════
# 共用 widget helpers（純視覺，維持 V2 設計規範）
# ════════════════════════════════════════════════════════════

def _input(text: str, w: int = 80, align_right: bool = True,
           color: str = None) -> QLineEdit:
    le = QLineEdit(text)
    le.setFixedHeight(26)
    le.setFixedWidth(w)
    if align_right:
        le.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    le.setStyleSheet(
        f"QLineEdit {{ color: {color or T.TEXT_HI}; background: {T.BG_INPUT};"
        f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
        f" padding: 0 8px; font-size: 11px; }}"
        f"QLineEdit:focus {{ border-color: {T.ORANGE}; }}"
    )
    return le


def _icon_btn(icon: str, tooltip: str, color: str = None,
              size: int = 30, hover_red: bool = False) -> QPushButton:
    color = color or T.TEXT_DIM
    btn = QPushButton()
    btn.setIcon(lucide_icon(icon, color, 18, stroke=1.8))
    btn.setIconSize(QSize(18, 18))
    btn.setFixedSize(size, size)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setToolTip(tooltip)
    hover_bg = T.RED if hover_red else T.BG_HOVER
    btn.setStyleSheet(
        f"QPushButton {{ background: transparent;"
        f" border: 1px solid {T.BORDER};"
        f" border-radius: {T.R_SM}px; padding: 0; }}"
        f"QPushButton:hover {{ background: {hover_bg};"
        f" border-color: {hover_bg}; }}"
    )
    return btn


def _text_btn(text: str, icon: str = None,
              kind: str = "ghost") -> QPushButton:
    """文字按鈕（kind: primary / ghost / danger）"""
    btn = QPushButton(f"  {text}" if icon else text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedHeight(T.BTN_H)
    if icon:
        if kind == "primary":
            ic_color = "#ffffff"
        elif kind == "danger":
            ic_color = T.RED
        else:
            ic_color = T.TEXT_DIM
        btn.setIcon(lucide_icon(icon, ic_color, 14, stroke=1.6))
        btn.setIconSize(QSize(14, 14))

    if kind == "primary":
        btn.setStyleSheet(T.primary_button_qss())
    elif kind == "danger":
        btn.setStyleSheet(
            f"QPushButton {{ color: {T.RED}; background: transparent;"
            f" border: 1px solid {T.alpha(T.RED, 110)};"
            f" border-radius: {T.R_SM}px;"
            f" padding: 0 12px; font-size: 11px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {T.alpha(T.RED, 38)}; }}"
        )
    else:
        btn.setStyleSheet(
            f"QPushButton {{ color: {T.TEXT}; background: transparent;"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_SM}px;"
            f" padding: 0 12px; font-size: 11px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {T.BG_HOVER};"
            f" color: {T.TEXT_HI}; border-color: {T.BORDER_HOVER}; }}"
        )
    return btn


def _readonly_metric(value: str, color: str = None,
                     w: int = None) -> QLabel:
    color = color or T.TEXT_HI
    lbl = QLabel(value)
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    if w:
        lbl.setFixedWidth(w)
    lbl.setStyleSheet(
        f"color: {color}; background: {T.BG_INPUT};"
        f" border: 1px dashed {T.BORDER};"
        f" border-radius: {T.R_SM}px;"
        f" padding: 4px 8px; font-size: 11px; font-weight: 700;"
    )
    return lbl


def _section_card(title: str, icon: str, accent: str,
                  total_str: str = None) -> tuple[QFrame, QVBoxLayout]:
    """區段卡：頭部 icon+標題+總計，回傳 (QFrame, body_layout)"""
    f = QFrame()
    f.setObjectName("sec_card")
    f.setStyleSheet(
        f"QFrame#sec_card {{ background: {T.BG_SURFACE};"
        f" border: 1px solid {T.BORDER};"
        f" border-radius: {T.R_LG}px; }}"
    )
    L = QVBoxLayout(f)
    L.setContentsMargins(T.S_LG, T.S_MD, T.S_LG, T.S_MD)
    L.setSpacing(T.S_SM)

    head = QHBoxLayout()
    head.setSpacing(T.S_SM)
    head.addWidget(IconBadge(icon, accent, 28))
    head.addWidget(T.make_label(title, T.FONT_CARD_TITLE))
    head.addStretch()
    if total_str is not None:
        cap = QLabel("合計")
        cap.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
        )
        head.addWidget(cap)
        total = QLabel(total_str)
        total.setStyleSheet(
            f"color: {accent}; background: {T.alpha(accent, 38)};"
            f" border-radius: {T.R_SM}px;"
            f" padding: 2px 10px; font-size: 12px; font-weight: 700;"
        )
        head.addWidget(total)
    L.addLayout(head)
    return f, L


# ════════════════════════════════════════════════════════════
# _StackQty — 數量輸入器：組數 × 組大小(下拉) + 餘數 → 數量
# ════════════════════════════════════════════════════════════

class _StackQty(QWidget):
    """以「整組」方式輸入大數量：[組數] × [組大小▼] + [餘數]。

    遊戲內道具以固定上限堆疊（藥水 3000、一般物品 9900、卷軸 3000…），
    使用者通常知道「幾組 + 餘幾個」而非確切總數。
    qty() = 組數 × 組大小 + 餘數；set_qty(total, stack) 由總數還原為 組/餘。
    """

    STACK_SIZES = (3000, 9900)

    def __init__(self, parent_page, default_stack: int = 3000):
        super().__init__()
        self._page = parent_page
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(3)

        self.groups_edit = _input("", w=40)
        h.addWidget(self.groups_edit)
        h.addWidget(self._sym("×"))

        self.stack_combo = QComboBox()
        self.stack_combo.setFixedSize(74, 26)   # 固定寬，避免下拉膨脹吃掉整列、害前後不對齊
        self.stack_combo.setStyleSheet(
            T.combo_qss(bg=T.BG_SURFACE, border=T.BORDER, padding="0 6px")
        )
        for s in self.STACK_SIZES:
            self.stack_combo.addItem(f"{s:,}", s)
        self._select_stack(default_stack)
        h.addWidget(self.stack_combo)

        h.addWidget(self._sym("＋"))
        self.remainder_edit = _input("", w=56)
        h.addWidget(self.remainder_edit)
        h.addStretch()   # 餘數後吸收剩餘空間，組件靠左不被拉開

        self.groups_edit.textChanged.connect(self._page._on_input_changed)
        self.remainder_edit.textChanged.connect(self._page._on_input_changed)
        self.stack_combo.currentIndexChanged.connect(
            lambda *_: self._page._on_input_changed())

    def _sym(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {T.TEXT_MUTED}; font-size: 11px; background: transparent;")
        return lbl

    def _select_stack(self, stack):
        idx = self.stack_combo.findData(_as_int(stack) or self.STACK_SIZES[0])
        self.stack_combo.setCurrentIndex(idx if idx >= 0 else 0)

    def stack_size(self) -> int:
        d = self.stack_combo.currentData()
        return int(d) if d else self.STACK_SIZES[0]

    def qty(self) -> int:
        return (_parse_int(self.groups_edit.text()) * self.stack_size()
                + _parse_int(self.remainder_edit.text()))

    def set_qty(self, total, stack=None):
        """由總數還原為 組數/餘數（不觸發 _on_input_changed）"""
        widgets = (self.groups_edit, self.remainder_edit, self.stack_combo)
        for w in widgets:
            w.blockSignals(True)
        try:
            if stack:
                self._select_stack(stack)
            total = _as_int(total)
            size = self.stack_size()
            g, r = divmod(total, size) if size else (0, total)
            self.groups_edit.setText(str(g) if g else "")
            self.remainder_edit.setText(str(r) if r else "")
        finally:
            for w in widgets:
                w.blockSignals(False)


# ════════════════════════════════════════════════════════════
# _PotionRowV2 — 單筆藥水（垂直：上排名稱/單價/水錢；前、後各一列）
# ════════════════════════════════════════════════════════════

class _PotionRowV2(QFrame):
    """單列藥水：上排 名稱 / 單價 / 水錢 / 刪除；前、後 各一列以組數輸入器填寫。

    消耗 = max(0, 前 − 後)；水錢 = 消耗 × 單價。
    透過 `parent_page._on_input_changed` 接收任一輸入變動；刪除呼叫 `parent_section.remove_row(self)`。
    """

    def __init__(self, parent_section, parent_page, accent: str, data: dict):
        super().__init__()
        self._section = parent_section
        self._page = parent_page
        self.setStyleSheet(
            f"QFrame {{ background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_MD}px; }}"
        )

        # 外層：內容欄（VBox）＋ 刪除鈕（右側、整列垂直置中）
        root = QHBoxLayout(self)
        root.setContentsMargins(T.S_SM, 6, T.S_SM, 6)
        root.setSpacing(T.S_SM)
        body = QVBoxLayout()
        body.setSpacing(4)

        # 上排：名稱 / 單價 / 水錢
        top = QHBoxLayout()
        top.setSpacing(T.S_XS)
        top.addWidget(IconBadge("droplet", accent, 26))
        self.name_edit = _input(str(data.get("name", "")), w=120,
                                align_right=False, color=T.TEXT_HI)
        self.name_edit.setReadOnly(True)
        self.name_edit.setMinimumWidth(100)
        self.name_edit.setMaximumWidth(16777215)   # 名稱欄隨欄寬伸展
        self.name_edit.setStyleSheet(self.name_edit.styleSheet() +
            " QLineEdit { background: transparent; border: none; }")
        top.addWidget(self.name_edit, 1)
        top.addWidget(self._caption("單價"))
        self.price_edit = _input(self._init_int(data.get("price")), w=80)
        top.addWidget(self.price_edit)
        self._cost_metric = _readonly_metric("0", color=T.RED, w=96)
        top.addWidget(self._cost_metric)
        body.addLayout(top)

        # 前 / 後（各一列，組數輸入器）
        self.before_qty = _StackQty(parent_page, default_stack=data.get("before_stack", 3000))
        self.before_qty.set_qty(data.get("before", 0), data.get("before_stack", 3000))
        self.after_qty = _StackQty(parent_page, default_stack=data.get("after_stack", 3000))
        self.after_qty.set_qty(data.get("after", 0), data.get("after_stack", 3000))

        before_row = QHBoxLayout()
        before_row.setSpacing(T.S_XS)
        before_row.addSpacing(26 + T.S_XS)         # 對齊上排名稱
        before_row.addWidget(self._caption("前"))
        before_row.addWidget(self.before_qty)
        before_row.addStretch()
        body.addLayout(before_row)

        after_row = QHBoxLayout()
        after_row.setSpacing(T.S_XS)
        after_row.addSpacing(26 + T.S_XS)          # 對齊上排名稱
        after_row.addWidget(self._caption("後"))
        after_row.addWidget(self.after_qty)
        self._consumed_lbl = QLabel("消耗 0")
        self._consumed_lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;")
        after_row.addWidget(self._consumed_lbl)
        after_row.addStretch()
        body.addLayout(after_row)

        root.addLayout(body, 1)
        del_btn = _icon_btn("x", "刪除此列", T.TEXT_DIM, hover_red=True)
        del_btn.clicked.connect(lambda: self._section.remove_row(self))
        root.addWidget(del_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self.name_edit.textChanged.connect(self._page._on_input_changed)
        self.price_edit.textChanged.connect(self._page._on_input_changed)
        self.refresh_derived()

    def _caption(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 10px; background: transparent;"
        )
        return lbl

    @staticmethod
    def _init_int(value) -> str:
        """初始化整數輸入框：0/None/空值顯示為空字串"""
        try:
            v = int(value) if value not in (None, "") else 0
        except (TypeError, ValueError):
            v = 0
        return str(v) if v > 0 else ""

    def get_data(self) -> dict:
        price  = _parse_int(self.price_edit.text())
        before = self.before_qty.qty()
        after  = self.after_qty.qty()
        consumed = max(0, before - after)
        cost = PotionService.calc_row_cost(
            {"price": price, "before": before, "after": after}
        )
        return {
            "name":        self.name_edit.text().strip(),
            "price":       price,
            "before":      before,
            "after":       after,
            "before_stack": self.before_qty.stack_size(),
            "after_stack":  self.after_qty.stack_size(),
            "consumed":    consumed,
            "cost":        cost,
        }

    def refresh_derived(self):
        """更新消耗與水錢顯示（由 section 在重算時呼叫）"""
        data = self.get_data()
        self._consumed_lbl.setText(f"消耗 {data['consumed']:,}")
        self._cost_metric.setText(_fmt(data["cost"]))


# ════════════════════════════════════════════════════════════
# _PotionSectionV2 — HP / MP / 複合 區塊
# ════════════════════════════════════════════════════════════

class _PotionSectionV2(QFrame):
    """一類藥水區塊：標題 + 合計 + 操作列 + 列容器

    提供 add_row / remove_row / clear / get_rows_data 四個介面給頁面使用。
    所有 row 操作結束後都會觸發 `parent_page._on_input_changed`。
    """

    def __init__(self, parent_page, potion_type: str,
                 title: str, icon: str, accent: str):
        super().__init__()
        self._page = parent_page
        self._potion_type = potion_type
        self._accent = accent
        self._rows: list[_PotionRowV2] = []

        self._total_label = QLabel("0")

        self.setObjectName("sec_card")
        self.setStyleSheet(
            f"QFrame#sec_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
        )
        outer = QVBoxLayout(self)
        outer.setContentsMargins(T.S_LG, T.S_MD, T.S_LG, T.S_MD)
        outer.setSpacing(T.S_SM)

        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(IconBadge(icon, accent, 28))
        head.addWidget(T.make_label(title, T.FONT_CARD_TITLE))
        head.addStretch()
        cap = QLabel("合計")
        cap.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
        )
        head.addWidget(cap)
        self._total_label.setStyleSheet(
            f"color: {accent}; background: {T.alpha(accent, 38)};"
            f" border-radius: {T.R_SM}px;"
            f" padding: 2px 10px; font-size: 12px; font-weight: 700;"
        )
        head.addWidget(self._total_label)
        outer.addLayout(head)

        # 操作列：藥水下拉（選即新增）+ 清除全部
        ops = QHBoxLayout()
        ops.setSpacing(T.S_SM)
        self._add_combo = QComboBox()
        self._add_combo.setFixedHeight(28)
        self._add_combo.setMinimumWidth(160)
        self._add_combo.setStyleSheet(
            T.combo_qss(bg=T.BG_INPUT, border=T.BORDER, padding="0 8px")
        )
        self._refresh_add_combo()
        self._add_combo.currentIndexChanged.connect(self._on_pick_add)
        ops.addWidget(self._add_combo)
        clear_btn = _text_btn("清除全部", "trash-2", "danger")
        clear_btn.clicked.connect(self.clear)
        ops.addWidget(clear_btn)
        ops.addStretch()
        outer.addLayout(ops)

        # Row 容器
        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(T.S_XS)
        outer.addWidget(self._rows_container)

    def _refresh_add_combo(self):
        """填入該分類所有 PotionService.DEFAULTS（已加入的也保留，可重複加）"""
        combo = self._add_combo
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("＋ 新增藥水…", None)
        for entry in PotionService.DEFAULTS.get(self._potion_type, []):
            combo.addItem(entry["name"], entry)
        combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def _on_pick_add(self, idx: int):
        if idx <= 0:
            return
        entry = self._add_combo.itemData(idx)
        if entry:
            self.add_row({"name": entry["name"], "price": entry["price"]})
        # 重置回 placeholder 並避免立即 re-fire
        self._add_combo.blockSignals(True)
        self._add_combo.setCurrentIndex(0)
        self._add_combo.blockSignals(False)

    # ── 對外 API ──
    def add_row(self, data: dict):
        row = _PotionRowV2(self, self._page, self._accent, data or {})
        self._rows_layout.addWidget(row)
        self._rows.append(row)
        self._page._on_input_changed()

    def remove_row(self, row: _PotionRowV2):
        if row in self._rows:
            self._rows.remove(row)
            self._rows_layout.removeWidget(row)
            row.deleteLater()
            self._page._on_input_changed()

    def clear(self):
        for row in list(self._rows):
            self._rows_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()
        self._page._on_input_changed()

    def get_rows_data(self) -> list:
        return [r.get_data() for r in self._rows]

    def refresh_subtotal(self):
        """重算合計並同步每列的 consumed/cost 顯示"""
        rows_data = self.get_rows_data()
        self._total_label.setText(_fmt(
            PotionService.calc_section_subtotal(rows_data)
        ))
        for row in self._rows:
            row.refresh_derived()


# ════════════════════════════════════════════════════════════
# _ItemRowV2 / _ItemSectionV2 — 物品取得（收入側）
# ════════════════════════════════════════════════════════════

class _ItemRowV2(QFrame):
    """單列物品取得：上排 名稱 / 單價 / 收入 / 刪除；下排 數量（組數輸入器）。

    收入 ＝ 數量 × 單價。物品堆疊組大小預設 9900（卷軸等可下拉選 3000）。
    透過 `parent_page._on_input_changed` 接收輸入變動；刪除呼叫 `parent_section.remove_row(self)`。
    """

    def __init__(self, parent_section, parent_page, data: dict):
        super().__init__()
        self._section = parent_section
        self._page = parent_page
        self._item_id = data.get("item_id", 0)
        self.setStyleSheet(
            f"QFrame {{ background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_MD}px; }}"
        )

        # 外層：內容欄（VBox）＋ 刪除鈕（右側、整列垂直置中）
        root = QHBoxLayout(self)
        root.setContentsMargins(T.S_SM, 6, T.S_SM, 6)
        root.setSpacing(T.S_SM)
        body = QVBoxLayout()
        body.setSpacing(4)

        # 上排：道具圖示 / 名稱（伸展填滿）/ 單價 / 收入
        top = QHBoxLayout()
        top.setSpacing(T.S_XS)
        top.addWidget(self._make_icon(self._item_id))
        self.name_edit = _input(str(data.get("name", "")), w=150,
                                align_right=False, color=T.TEXT_HI)
        self.name_edit.setMinimumWidth(140)
        self.name_edit.setMaximumWidth(16777215)   # 解除固定寬，讓名稱欄隨欄寬伸展
        top.addWidget(self.name_edit, 1)
        top.addWidget(self._caption("單價"))
        self.price_edit = _input(self._init_int(data.get("unit_price")), w=80)
        top.addWidget(self.price_edit)
        self._value_metric = _readonly_metric("0", color=T.GREEN, w=96)
        top.addWidget(self._value_metric)
        body.addLayout(top)

        # 下排：數量（組數輸入器，預設組大小 9900）— 與名稱欄左緣對齊
        self.qty_input = _StackQty(parent_page, default_stack=data.get("stack_size", 9900))
        self.qty_input.set_qty(data.get("qty", 0), data.get("stack_size", 9900))
        qty_row = QHBoxLayout()
        qty_row.setSpacing(T.S_XS)
        qty_row.addSpacing(26 + T.S_XS)            # 對齊上排名稱（讓出 icon 寬）
        qty_row.addWidget(self._caption("數量"))
        qty_row.addWidget(self.qty_input)
        qty_row.addStretch()
        body.addLayout(qty_row)

        root.addLayout(body, 1)
        del_btn = _icon_btn("x", "刪除此列", T.TEXT_DIM, hover_red=True)
        del_btn.clicked.connect(lambda: self._section.remove_row(self))
        root.addWidget(del_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self.name_edit.textChanged.connect(self._page._on_input_changed)
        self.price_edit.textChanged.connect(self._page._on_input_changed)
        self.refresh_derived()

    def _caption(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 10px; background: transparent;"
        )
        return lbl

    @staticmethod
    def _make_icon(item_id) -> QWidget:
        """道具圖示：有對應 PNG 則顯示，否則 fallback 綠色 package 徽章"""
        pix = _item_icon(item_id, 26)
        if pix is None:
            return IconBadge("package", T.GREEN, 28)
        lbl = QLabel()
        lbl.setFixedSize(28, 28)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setPixmap(pix)
        lbl.setStyleSheet("background: transparent;")
        return lbl

    @staticmethod
    def _init_int(value) -> str:
        """初始化整數輸入框：0/None/空值顯示為空字串"""
        try:
            v = int(value) if value not in (None, "") else 0
        except (TypeError, ValueError):
            v = 0
        return str(v) if v > 0 else ""

    def get_data(self) -> dict:
        qty   = self.qty_input.qty()
        price = _parse_int(self.price_edit.text())
        return {
            "name":       self.name_edit.text().strip(),
            "item_id":    self._item_id,
            "qty":        qty,
            "stack_size": self.qty_input.stack_size(),
            "unit_price": price,
            "value":      qty * price,
        }

    def refresh_derived(self):
        """更新該列收入顯示（由 section 在重算時呼叫）"""
        self._value_metric.setText(_fmt(self.get_data()["value"]))


class _ItemSectionV2(QFrame):
    """物品取得收入區：標題 + 合計 + 操作列（選地圖 / 新增道具 / 清除全部）+ 列容器

    對外 API（add_row / remove_row / clear / get_rows_data / refresh_subtotal）與
    `_PotionSectionV2` 同形，供頁面資料流統一處理。
    """

    def __init__(self, parent_page):
        super().__init__()
        self._page = parent_page
        self._rows: list[_ItemRowV2] = []
        self._total_label = QLabel("0")

        self.setObjectName("sec_card")
        self.setStyleSheet(
            f"QFrame#sec_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
        )
        outer = QVBoxLayout(self)
        outer.setContentsMargins(T.S_LG, T.S_MD, T.S_LG, T.S_MD)
        outer.setSpacing(T.S_SM)

        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(IconBadge("package", T.GREEN, 28))
        head.addWidget(T.make_label("物品取得", T.FONT_CARD_TITLE))
        head.addStretch()
        cap = QLabel("合計")
        cap.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
        )
        head.addWidget(cap)
        self._total_label.setStyleSheet(
            f"color: {T.GREEN}; background: {T.alpha(T.GREEN, 38)};"
            f" border-radius: {T.R_SM}px; padding: 2px 10px;"
            f" font-size: 12px; font-weight: 700;"
        )
        head.addWidget(self._total_label)
        outer.addLayout(head)

        # 操作列：選練等地圖帶出掉落 + 新增道具 + 清除全部
        ops = QHBoxLayout()
        ops.setSpacing(T.S_SM)
        self._map_combo = QComboBox()
        self._map_combo.setFixedHeight(28)
        self._map_combo.setMinimumWidth(240)
        self._map_combo.setStyleSheet(
            T.combo_qss(bg=T.BG_INPUT, border=T.BORDER, padding="0 8px")
        )
        self._refresh_map_combo()
        self._map_combo.currentIndexChanged.connect(self._on_pick_map)
        ops.addWidget(self._map_combo)
        add_btn = _text_btn("新增道具", "plus", "ghost")
        add_btn.clicked.connect(lambda: self.add_row({}))
        ops.addWidget(add_btn)
        clear_btn = _text_btn("清除全部", "trash-2", "danger")
        clear_btn.clicked.connect(self._on_clear_all)
        ops.addWidget(clear_btn)
        ops.addStretch()
        outer.addLayout(ops)

        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(T.S_XS)
        outer.addWidget(self._rows_container)

    def _refresh_map_combo(self):
        """填入練等地圖清單（選取即帶出該圖掉落道具列）"""
        c = self._map_combo
        c.blockSignals(True)
        c.clear()
        c.addItem("＋ 選擇練等地圖帶出掉落…", None)
        for name in training_maps.map_names():
            c.addItem(f"Lv{training_maps.map_level(name):<3}｜{name}", name)
        c.setCurrentIndex(0)
        c.blockSignals(False)

    def _on_pick_map(self, idx: int):
        if idx <= 0:
            return
        map_name = self._map_combo.itemData(idx)
        if not map_name:
            return
        # 切換地圖：先清除現有列，再帶出新圖掉落（下拉保留所選地圖，不重置）
        self._page._loading = True
        try:
            self.clear()
            for row in training_maps.drops_for(map_name):
                self.add_row(row)
        finally:
            self._page._loading = False
        self._page._on_input_changed()

    # ── 對外 API（與 _PotionSectionV2 同形）──
    def add_row(self, data: dict):
        row = _ItemRowV2(self, self._page, data or {})
        self._rows_layout.addWidget(row)
        self._rows.append(row)
        self._page._on_input_changed()

    def remove_row(self, row: _ItemRowV2):
        if row in self._rows:
            self._rows.remove(row)
            self._rows_layout.removeWidget(row)
            row.deleteLater()
            self._page._on_input_changed()

    def clear(self):
        for row in list(self._rows):
            self._rows_layout.removeWidget(row)
            row.setParent(None)        # 立即脫離父層（deleteLater 為非同步）
            row.deleteLater()
        self._rows.clear()
        self._page._on_input_changed()

    def _on_clear_all(self):
        """清除全部：清空列並把地圖下拉重置回 placeholder（可重新選同一張）"""
        self.clear()
        c = self._map_combo
        c.blockSignals(True)
        c.setCurrentIndex(0)
        c.blockSignals(False)

    def get_rows_data(self) -> list:
        return [r.get_data() for r in self._rows]

    def refresh_subtotal(self):
        """重算合計並同步每列收入顯示"""
        rows_data = self.get_rows_data()
        self._total_label.setText(_fmt(PotionService.calc_items_total(rows_data)))
        for row in self._rows:
            row.refresh_derived()


# ════════════════════════════════════════════════════════════
# PotionPageV2
# ════════════════════════════════════════════════════════════

class PotionPageV2(QWidget):
    """V2 練功水錢頁 — 透過 PotionService 完成資料計算、autosave、紀錄序列化。"""

    # 摘要面板的數值鍵（對應 PotionService.calc_summary 回傳；收支，不含經驗/速率）
    _SUMMARY_KEYS = ("income", "expense", "net")

    # 藥水區塊定義：(potion_type, 標題, icon, accent)
    _SECTIONS = (
        ("hp",       "HP 藥水",  "heart",         T.RED),
        ("mp",       "MP 藥水",  "droplet",       T.CYAN),
        ("combined", "複合藥水", "flask-conical", T.PURPLE),
    )

    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self._service = (
            PotionService(app.config_manager) if app is not None else None
        )

        self._loading: bool = False

        # 防抖 autosave
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(500)
        self._autosave_timer.timeout.connect(self._do_autosave)

        # 延後綁定的 widget refs（由 _build 填入）
        self._sections: dict[str, _PotionSectionV2] = {}
        self._item_section = None          # _ItemSectionV2（收入：物品取得）
        self._summary_labels: dict[str, QLabel] = {}
        self._diff_labels: list[tuple[QLineEdit, QLineEdit, QLabel]] = []

        self._build()
        self._try_load_autosave()

    # ════════════════════════════════════════════════════════
    # UI
    # ════════════════════════════════════════════════════════
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        # ── 工具列 ──
        bar = QHBoxLayout()
        bar.setSpacing(T.S_SM)
        bar.addWidget(T.make_label("練功收支", T.FONT_SECTION))
        bar.addStretch()
        for label, icon, kind, slot in [
            ("清除",     "trash-2",     "ghost",  self._on_clear),
            ("全部重置", "rotate-ccw",  "danger", self._on_reset_all),
            ("載入紀錄", "folder-open", "ghost",  self._on_load),
            ("儲存",     "save",        "primary", self._on_save),
        ]:
            btn = _text_btn(label, icon, kind)
            btn.clicked.connect(slot)
            bar.addWidget(btn)
        root.addLayout(bar)

        # ── 主體：左支出 / 右收入（各自捲動）──
        mid = QHBoxLayout()
        mid.setSpacing(T.S_LG)
        mid.addWidget(self._build_expense_column(), 1)
        mid.addWidget(self._build_income_column(), 1)
        root.addLayout(mid, 1)

        # ── 下方：本次收支總結（總支出 / 總收入 / 淨收益）──
        root.addWidget(self._build_summary_card())

        # UI 全部綁定完畢，觸發首次重算（初始為空狀態）
        self._recalc_all()

    def _build_column(self, title: str, icon: str, accent: str,
                      sections: list) -> QWidget:
        """左/右欄共用：標頭（icon + 標題）＋ 捲動區（內含若干 section）"""
        col = QWidget()
        col.setStyleSheet("background: transparent;")
        cv = QVBoxLayout(col)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(T.S_SM)

        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(IconBadge(icon, accent, 24))
        head.addWidget(T.make_label(title, T.FONT_CARD_TITLE))
        head.addStretch()
        cv.addLayout(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        # 半寬欄較窄，列若超寬則顯示橫向捲動（避免欄位被裁切隱藏）
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("background: transparent;")
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        iv = QVBoxLayout(inner)
        iv.setContentsMargins(0, 0, T.S_XS, 0)
        iv.setSpacing(T.S_MD)
        iv.setAlignment(Qt.AlignmentFlag.AlignTop)
        for w in sections:
            iv.addWidget(w)
        iv.addStretch()
        scroll.setWidget(inner)
        cv.addWidget(scroll, 1)
        return col

    def _build_expense_column(self) -> QWidget:
        """左欄：支出（HP / MP / 複合藥水，初始為空）"""
        secs = []
        for potion_type, title, icon, accent in self._SECTIONS:
            sec = _PotionSectionV2(self, potion_type, title, icon, accent)
            self._sections[potion_type] = sec
            secs.append(sec)
        return self._build_column("支出", "trending-down", T.RED, secs)

    def _build_income_column(self) -> QWidget:
        """右欄：收入（撿取楓幣 / 商店收益 / 物品取得）"""
        self._item_section = _ItemSectionV2(self)
        return self._build_column(
            "收入", "trending-up", T.GREEN,
            [self._build_meso_shop_card(), self._item_section])

    def _build_meso_shop_card(self) -> QFrame:
        """收入：撿取楓幣（前/後）＋ 商店收益（前/後），差值＝收入貢獻"""
        card = QFrame()
        card.setObjectName("sec_card")
        card.setStyleSheet(
            f"QFrame#sec_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
        )
        L = QVBoxLayout(card)
        L.setContentsMargins(T.S_LG, T.S_MD, T.S_LG, T.S_MD)
        L.setSpacing(T.S_SM)

        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(IconBadge("coins", T.YELLOW, 28))
        head.addWidget(T.make_label("楓幣 ・ 商店", T.FONT_CARD_TITLE))
        head.addStretch()
        L.addLayout(head)

        self._mesos_start_input = _input("", w=96)
        self._mesos_end_input   = _input("", w=96)
        L.addWidget(self._build_trio_row(
            "撿取楓幣", self._mesos_start_input, self._mesos_end_input, T.YELLOW))

        self._shop_before_input = _input("", w=96)
        self._shop_after_input  = _input("", w=96)
        L.addWidget(self._build_trio_row(
            "商店收益", self._shop_before_input, self._shop_after_input, T.GREEN))

        self._mesos_end_input.textChanged.connect(self._sync_shop_before)
        return card

    def _build_trio_row(self, label_text: str,
                        before_edit: QLineEdit, after_edit: QLineEdit,
                        accent: str) -> QFrame:
        """前 / 後 / =收入 一列；收入貢獻＝max(0, 後−前)，不顯示負值"""
        wrap = QFrame()
        wrap.setStyleSheet(
            f"QFrame {{ background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_MD}px; }}"
        )
        h = QHBoxLayout(wrap)
        h.setContentsMargins(T.S_SM, 6, T.S_SM, 6)
        h.setSpacing(T.S_XS)

        lbl = QLabel(label_text)
        lbl.setFixedWidth(72)
        lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 11px; font-weight: 600;"
            f" background: transparent;"
        )
        h.addWidget(lbl)

        b_lbl = QLabel("前")
        b_lbl.setStyleSheet(f"color: {T.TEXT_MUTED}; font-size: 10px; background: transparent;")
        h.addWidget(b_lbl)
        before_edit.textChanged.connect(self._on_input_changed)
        h.addWidget(before_edit)

        a_lbl = QLabel("後")
        a_lbl.setStyleSheet(f"color: {T.TEXT_MUTED}; font-size: 10px; background: transparent;")
        h.addWidget(a_lbl)
        after_edit.textChanged.connect(self._on_input_changed)
        h.addWidget(after_edit)

        h.addStretch()
        eq = QLabel("=")
        eq.setStyleSheet(f"color: {T.TEXT_MUTED}; background: transparent;")
        h.addWidget(eq)

        diff_lbl = _readonly_metric("0", accent, w=100)
        h.addWidget(diff_lbl)
        self._diff_labels.append((before_edit, after_edit, diff_lbl))
        return wrap

    def _sync_shop_before(self, text: str):
        """鏡射撿取楓幣「後」→ 商店收益「前」（拾完錢進商店，初始金額通常相同）"""
        if self._loading or self._shop_before_input.text() == text:
            return
        self._shop_before_input.setText(text)

    def _build_summary_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("sec_card")
        card.setStyleSheet(
            f"QFrame#sec_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
        )
        L = QVBoxLayout(card)
        L.setContentsMargins(T.S_LG, T.S_MD, T.S_LG, T.S_MD)
        L.setSpacing(T.S_SM)

        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(IconBadge("trending-up", T.GREEN, 28))
        head.addWidget(T.make_label("本次收支總結", T.FONT_CARD_TITLE))
        head.addStretch()
        L.addLayout(head)

        # 指標橫排：總支出 | 總收入 | 淨收益
        metrics = QHBoxLayout()
        metrics.setSpacing(T.S_2XL)

        def add_metric(label: str, key: str, color: str):
            cell = QVBoxLayout()
            cell.setSpacing(2)
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
            )
            cell.addWidget(lbl)
            val = QLabel("0")
            val.setStyleSheet(
                f"color: {color}; font-size: 18px; font-weight: 700;"
                f" background: transparent;"
            )
            cell.addWidget(val)
            wrap = QWidget()
            wrap.setLayout(cell)
            metrics.addWidget(wrap)
            self._summary_labels[key] = val

        add_metric("總支出", "expense", T.RED)
        add_metric("總收入", "income",  T.GREEN)
        add_metric("淨收益", "net",     T.YELLOW)
        metrics.addStretch()
        L.addLayout(metrics)

        return card

    # ════════════════════════════════════════════════════════
    # 資料流
    # ════════════════════════════════════════════════════════
    def _collect_form(self) -> dict:
        """UI → PotionFormData（供 Service 計算與序列化）"""
        return {
            "hp_potions":       self._sections["hp"].get_rows_data(),
            "mp_potions":       self._sections["mp"].get_rows_data(),
            "combined_potions": self._sections["combined"].get_rows_data(),
            "mesos_start": _parse_int(self._mesos_start_input.text()),
            "mesos_end":   _parse_int(self._mesos_end_input.text()),
            "shop_before": _parse_int(self._shop_before_input.text()),
            "shop_after":  _parse_int(self._shop_after_input.text()),
            "item_rows":        self._item_section.get_rows_data(),
        }

    def _on_input_changed(self, *_):
        """所有輸入變更的單一匯流入口"""
        if self._loading:
            return
        self._recalc_all()
        self._schedule_autosave()

    def _recalc_all(self):
        """重算摘要、各區塊小計與每列衍生值"""
        form = self._collect_form()
        summary = PotionService.calc_summary(form)

        # 摘要面板
        for key in self._SUMMARY_KEYS:
            lbl = self._summary_labels.get(key)
            if lbl is None:
                continue
            value = summary.get(key, 0)
            if key == "income":
                lbl.setText(f"+{_fmt(value)}" if value else "+0")
            elif key == "expense":
                lbl.setText(f"-{_fmt(value)}" if value else "-0")
            else:
                lbl.setText(_fmt_signed(value))

        # 各區塊合計 + 每列衍生值（藥水支出 + 物品收入）
        for sec in self._sections.values():
            sec.refresh_subtotal()
        self._item_section.refresh_subtotal()

        # 楓幣 / 商店 前後差（收入貢獻＝max(0, 後−前)，不顯示負值）
        for before_edit, after_edit, diff_lbl in self._diff_labels:
            gain = max(0, _parse_int(after_edit.text()) - _parse_int(before_edit.text()))
            diff_lbl.setText(f"+{_fmt(gain)}" if gain else "+0")

    # ════════════════════════════════════════════════════════
    # autosave
    # ════════════════════════════════════════════════════════
    def _schedule_autosave(self):
        if self._loading or self._service is None:
            return
        self._autosave_timer.start()

    def _do_autosave(self):
        if self._loading or self._service is None:
            return
        self._service.save_autosave(self._collect_form())

    def _try_load_autosave(self):
        """啟動時還原 autosave；無檔案則保留預設目錄畫面"""
        if self._service is None:
            return
        record = self._service.load_autosave()
        if not record:
            return

        self._loading = True
        try:
            self._restore_form(record)
        finally:
            self._loading = False

        self._recalc_all()
        toast = getattr(self.app, "toast", None)
        if toast is not None:
            toast.show("已還原上次編輯內容", "info")

    def _restore_form(self, data: dict):
        """把 dict（autosave 原檔或 deserialize 結果）逐欄填入 UI"""
        for potion_type in ("hp", "mp", "combined"):
            sec = self._sections[potion_type]
            sec.clear()
            for row_data in (data.get(f"{potion_type}_potions") or []):
                sec.add_row(row_data)

        def _set(edit: QLineEdit, value):
            edit.setText("" if value in (None, 0, "", "0") else str(value))

        _set(self._mesos_start_input, data.get("mesos_start"))
        _set(self._mesos_end_input,   data.get("mesos_end"))
        _set(self._shop_before_input, data.get("shop_before"))
        _set(self._shop_after_input,  data.get("shop_after"))

        self._item_section.clear()
        for row_data in (data.get("item_rows") or []):
            self._item_section.add_row(row_data)

    # ════════════════════════════════════════════════════════
    # 紀錄 save/load
    # ════════════════════════════════════════════════════════
    def _on_save(self):
        dlg = PotionSaveDialogV2(self)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.name:
            return
        payload = PotionService.serialize(self._collect_form())
        ok = self.app.config_manager.save_potion_record(dlg.name, payload)
        toast = getattr(self.app, "toast", None)
        if toast is not None:
            toast.show(f"已儲存紀錄：{dlg.name}" if ok else "儲存失敗",
                       "info" if ok else "warn")

    def _on_load(self):
        dlg = PotionLoadDialogV2(self, self.app)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.selected_name:
            return
        record = self.app.config_manager.load_potion_record(dlg.selected_name)
        if not record:
            toast = getattr(self.app, "toast", None)
            if toast is not None:
                toast.show("載入失敗", "warn")
            return
        restored = PotionService.deserialize(record)
        self._loading = True
        try:
            self._restore_form(restored)
        finally:
            self._loading = False
        self._recalc_all()
        self._schedule_autosave()

    # ════════════════════════════════════════════════════════
    # 清除 / 重置
    # ════════════════════════════════════════════════════════
    def _on_clear(self):
        reply = QMessageBox.question(
            self, "確認清除",
            "確定要清空所有輸入嗎？\n（autosave 將在下次變動後覆寫）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._loading = True
        try:
            self._clear_all_inputs()
        finally:
            self._loading = False
        self._recalc_all()
        self._schedule_autosave()

    def _on_reset_all(self):
        reply = QMessageBox.question(
            self, "確認全部重置",
            "確定要重置所有資料嗎？\n（autosave 也會一併刪除，且無法復原）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._loading = True
        try:
            self._clear_all_inputs()
        finally:
            self._loading = False
        self._autosave_timer.stop()
        if self._service is not None:
            self._service.clear_autosave()
        self._recalc_all()

    def _clear_all_inputs(self):
        for sec in self._sections.values():
            sec.clear()
        self._item_section.clear()
        for edit in (self._mesos_start_input, self._mesos_end_input,
                     self._shop_before_input, self._shop_after_input):
            edit.clear()
