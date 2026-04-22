"""
練功水錢頁面 — V2（已接線，透過 PotionService）
左：藥水區段 + 楓幣經驗（捲動）｜右：本次摘要
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

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QScrollArea, QLineEdit, QSpinBox, QMessageBox, QDialog,
)
from PySide6.QtCore import Qt, QSize, QTimer

from src.domain.potion_service import PotionService
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import IconBadge
from src.ui_v2.lucide import lucide_pixmap, lucide_icon
from src.ui_v2.dialogs import PotionSaveDialogV2, PotionLoadDialogV2


# ════════════════════════════════════════════════════════════
# 格式化 helpers
# ════════════════════════════════════════════════════════════

def _parse_int(text: str) -> int:
    """安全解析整數字串；空白、非法、負值一律回 0"""
    try:
        return max(0, int((text or "").strip().replace(",", "")))
    except (ValueError, AttributeError):
        return 0


def _fmt(value: int) -> str:
    return f"{value:,}"


def _fmt_signed(value: int) -> str:
    return f"{value:+,}"


def _fmt_elapsed(seconds: int) -> str:
    """HH:MM:SS 格式（> 99 小時也能顯示）"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


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
              size: int = 28, hover_red: bool = False) -> QPushButton:
    color = color or T.TEXT_DIM
    btn = QPushButton()
    btn.setIcon(lucide_icon(icon, color, 14, stroke=1.6))
    btn.setIconSize(QSize(14, 14))
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
        btn.setStyleSheet(
            f"QPushButton {{ color: #ffffff; background: {T.ORANGE};"
            f" border: none; border-radius: {T.R_SM}px;"
            f" padding: 0 14px; font-size: 12px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: #ff9d5a; }}"
        )
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
# _PotionRowV2 — 單筆藥水
# ════════════════════════════════════════════════════════════

class _PotionRowV2(QFrame):
    """單列藥水：名稱 / 單價 / 前 / 後 / 消耗 / 水錢 / 刪除

    透過 `parent_page._on_input_changed` 接收任一輸入變動。
    刪除按鈕呼叫 `parent_section.remove_row(self)`。
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

        L = QHBoxLayout(self)
        L.setContentsMargins(T.S_SM, 6, T.S_SM, 6)
        L.setSpacing(T.S_SM)

        L.addWidget(IconBadge("droplet", accent, 26))

        self.name_edit = _input(str(data.get("name", "")), w=96,
                                align_right=False, color=T.TEXT_HI)
        L.addWidget(self.name_edit)

        L.addWidget(self._caption("單價"))
        self.price_edit = _input(self._init_int(data.get("price")), w=78)
        L.addWidget(self.price_edit)

        L.addWidget(self._caption("練功前"))
        self.before_edit = _input(self._init_int(data.get("before")), w=60)
        L.addWidget(self.before_edit)

        L.addWidget(self._caption("練功後"))
        self.after_edit = _input(self._init_int(data.get("after")), w=60)
        L.addWidget(self.after_edit)

        self._consumed_lbl = QLabel("消耗 0")
        self._consumed_lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
        )
        L.addWidget(self._consumed_lbl)

        self._cost_metric = _readonly_metric("0", color=T.RED, w=96)
        L.addWidget(self._cost_metric)

        L.addStretch()
        del_btn = _icon_btn("x", "刪除此列", T.TEXT_DIM, hover_red=True)
        del_btn.clicked.connect(lambda: self._section.remove_row(self))
        L.addWidget(del_btn)

        # 所有輸入都匯流到頁面 _on_input_changed
        for edit in (self.name_edit, self.price_edit,
                     self.before_edit, self.after_edit):
            edit.textChanged.connect(self._page._on_input_changed)

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
        before = _parse_int(self.before_edit.text())
        after  = _parse_int(self.after_edit.text())
        consumed = max(0, before - after)
        cost = PotionService.calc_row_cost(
            {"price": price, "before": before, "after": after}
        )
        return {
            "name":     self.name_edit.text().strip(),
            "price":    price,
            "before":   before,
            "after":    after,
            "consumed": consumed,
            "cost":     cost,
        }

    def refresh_derived(self):
        """更新消耗與水錢顯示（由 section 在重算時呼叫）"""
        data = self.get_data()
        self._consumed_lbl.setText(f"消耗 {data['consumed']}")
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

        # 操作列：新增 + 清除全部
        ops = QHBoxLayout()
        ops.setSpacing(T.S_SM)
        add_btn = _text_btn("新增藥水", "plus", "ghost")
        add_btn.clicked.connect(lambda: self.add_row({}))
        ops.addWidget(add_btn)
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
# PotionPageV2
# ════════════════════════════════════════════════════════════

class PotionPageV2(QWidget):
    """V2 練功水錢頁 — 透過 PotionService 完成資料計算、autosave、紀錄序列化。"""

    # 摘要面板的 8 個數值鍵（對應 PotionService.calc_summary 回傳）
    _SUMMARY_KEYS = (
        "income", "expense", "net", "exp_total",
        "net_10", "exp_10", "net_60", "exp_60",
    )

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

        # 計時狀態
        self._timer_elapsed: int = 0
        self._mode: str = "manual"
        self._loading: bool = False

        # 防抖 autosave
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(500)
        self._autosave_timer.timeout.connect(self._do_autosave)

        # 每秒 tick 計時器
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._on_tick)

        # 延後綁定的 widget refs（由 _build 填入）
        self._sections: dict[str, _PotionSectionV2] = {}
        self._summary_labels: dict[str, QLabel] = {}
        self._mode_chips: dict[str, QPushButton] = {}
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
        bar.addWidget(T.make_label("練功水錢", T.FONT_SECTION))
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

        # ── 主體：左右雙欄 ──
        body = QHBoxLayout()
        body.setSpacing(T.S_LG)

        # 左：捲動表單
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        v = QVBoxLayout(inner)
        v.setContentsMargins(0, 0, T.S_XS, 0)
        v.setSpacing(T.S_MD)
        v.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 藥水區塊（初始為空，使用者手動新增）
        for potion_type, title, icon, accent in self._SECTIONS:
            sec = _PotionSectionV2(self, potion_type, title, icon, accent)
            self._sections[potion_type] = sec
            v.addWidget(sec)

        # 楓幣 / 商店 / 經驗 + 時間
        v.addWidget(self._build_meso_exp_section())
        v.addStretch()

        scroll.setWidget(inner)
        body.addWidget(scroll, 1)

        # 右：摘要（固定寬）
        right_wrap = QWidget()
        right_wrap.setFixedWidth(320)
        rv = QVBoxLayout(right_wrap)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(T.S_MD)
        rv.addWidget(self._build_summary_card())
        rv.addStretch()
        body.addWidget(right_wrap)

        root.addLayout(body, 1)

        # UI 全部綁定完畢，觸發首次重算（初始為空狀態）
        self._recalc_all()
        self._apply_timer_controls_visibility()

    def _build_meso_exp_section(self) -> QFrame:
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

        # 標頭
        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(IconBadge("coins", T.YELLOW, 28))
        head.addWidget(T.make_label("楓幣 ・ 經驗 ・ 時間", T.FONT_CARD_TITLE))
        head.addStretch()
        L.addLayout(head)

        # 三列：楓幣、商店、經驗
        self._mesos_start_input = _input("", w=120)
        self._mesos_end_input   = _input("", w=120)
        L.addWidget(self._build_trio_row(
            "撿取楓幣", self._mesos_start_input, self._mesos_end_input, T.YELLOW))

        self._shop_before_input = _input("", w=120)
        self._shop_after_input  = _input("", w=120)
        L.addWidget(self._build_trio_row(
            "商店收益", self._shop_before_input, self._shop_after_input, T.GREEN))

        self._exp_start_input = _input("", w=120)
        self._exp_end_input   = _input("", w=120)
        L.addWidget(self._build_trio_row(
            "獲取經驗", self._exp_start_input, self._exp_end_input, T.PURPLE))

        # 時間列
        L.addWidget(self._build_time_row())
        return card

    def _build_trio_row(self, label_text: str,
                        before_edit: QLineEdit, after_edit: QLineEdit,
                        accent: str) -> QFrame:
        wrap = QFrame()
        wrap.setStyleSheet(
            f"QFrame {{ background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_MD}px; }}"
        )
        h = QHBoxLayout(wrap)
        h.setContentsMargins(T.S_SM, 6, T.S_SM, 6)
        h.setSpacing(T.S_SM)

        lbl = QLabel(label_text)
        lbl.setFixedWidth(90)
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

        diff_lbl = _readonly_metric("+0", accent, w=120)
        h.addWidget(diff_lbl)
        self._diff_labels.append((before_edit, after_edit, diff_lbl))
        return wrap

    def _build_time_row(self) -> QFrame:
        wrap = QFrame()
        wrap.setStyleSheet(
            f"QFrame {{ background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_MD}px; }}"
        )
        h = QHBoxLayout(wrap)
        h.setContentsMargins(T.S_SM, 6, T.S_SM, 6)
        h.setSpacing(T.S_SM)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(14, 14)
        icon_lbl.setPixmap(lucide_pixmap("clock", T.ORANGE, 14, stroke=1.6))
        icon_lbl.setStyleSheet("background: transparent;")
        h.addWidget(icon_lbl)

        title = QLabel("練功時間")
        title.setStyleSheet(
            f"color: {T.TEXT}; font-size: 11px; font-weight: 600; background: transparent;"
        )
        h.addWidget(title)

        # 計時顯示
        self._timer_display = QLabel(_fmt_elapsed(0))
        self._timer_display.setStyleSheet(
            f"color: {T.TEXT_HI}; background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 2px 10px; font-size: 12px; font-weight: 700;"
            f" font-family: Consolas, 'Courier New', monospace;"
        )
        h.addWidget(self._timer_display)

        h.addStretch()

        # 模式切換 chips
        for mode, label in (("manual", "手動"), ("timer", "計時器")):
            b = QPushButton(label)
            b.setFixedHeight(24)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, m=mode: self._on_mode_toggle(m))
            self._mode_chips[mode] = b
            h.addWidget(b)
        self._apply_mode_styles()

        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 600)
        self._duration_spin.setValue(1)
        self._duration_spin.setSuffix(" 分")
        self._duration_spin.setFixedHeight(26)
        self._duration_spin.setFixedWidth(86)
        self._duration_spin.setStyleSheet(
            f"QSpinBox {{ color: {T.TEXT_HI}; background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 6px; font-size: 11px; }}"
        )
        self._duration_spin.valueChanged.connect(self._on_input_changed)
        h.addWidget(self._duration_spin)

        # 計時器控制：開始/停止 toggle + 重置（僅計時器模式顯示）
        self._timer_start_btn = _text_btn("開始", "play", "primary")
        self._timer_start_btn.clicked.connect(self._on_timer_start_stop)
        h.addWidget(self._timer_start_btn)

        self._timer_reset_btn = _text_btn("重置", "rotate-ccw", "ghost")
        self._timer_reset_btn.clicked.connect(self._on_timer_reset)
        h.addWidget(self._timer_reset_btn)

        return wrap

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
        head.addWidget(T.make_label("本次練功摘要", T.FONT_CARD_TITLE))
        head.addStretch()
        L.addLayout(head)

        def add_line(label: str, key: str, color: str):
            row = QHBoxLayout()
            row.setSpacing(T.S_SM)
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
            )
            row.addWidget(lbl)
            row.addStretch()
            val = QLabel("0")
            val.setStyleSheet(
                f"color: {color}; font-size: 13px; font-weight: 700;"
                f" background: transparent;"
            )
            row.addWidget(val)
            L.addLayout(row)
            self._summary_labels[key] = val

        add_line("總收入",   "income",    T.GREEN)
        add_line("總支出",   "expense",   T.RED)
        add_line("淨收益",   "net",       T.YELLOW)
        add_line("獲取經驗", "exp_total", T.PURPLE)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {T.BORDER_SOFT}; border: none;")
        L.addWidget(sep)

        rate_lbl = QLabel("平均速率")
        rate_lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 10px; font-weight: 600;"
            f" background: transparent; letter-spacing: 1px;"
        )
        L.addWidget(rate_lbl)

        add_line("每 10 分鐘 收益", "net_10", T.YELLOW)
        add_line("每 60 分鐘 收益", "net_60", T.YELLOW)
        add_line("每 10 分鐘 經驗", "exp_10", T.PURPLE)
        add_line("每 60 分鐘 經驗", "exp_60", T.PURPLE)

        return card

    # ════════════════════════════════════════════════════════
    # 資料流
    # ════════════════════════════════════════════════════════
    def _collect_form(self) -> dict:
        """UI → PotionFormData（供 Service 計算與序列化）"""
        return {
            "duration_minutes": self._duration_spin.value(),
            "hp_potions":       self._sections["hp"].get_rows_data(),
            "mp_potions":       self._sections["mp"].get_rows_data(),
            "combined_potions": self._sections["combined"].get_rows_data(),
            "mesos_start": _parse_int(self._mesos_start_input.text()),
            "mesos_end":   _parse_int(self._mesos_end_input.text()),
            "shop_before": _parse_int(self._shop_before_input.text()),
            "shop_after":  _parse_int(self._shop_after_input.text()),
            "exp_start":   _parse_int(self._exp_start_input.text()),
            "exp_end":     _parse_int(self._exp_end_input.text()),
        }

    def _on_input_changed(self, *_):
        """所有輸入變更的單一匯流入口"""
        if self._loading:
            return
        self._recalc_all()
        self._schedule_autosave()

    def _recalc_all(self):
        """重算摘要、區塊小計、trio 差值"""
        form = self._collect_form()
        summary = PotionService.calc_summary(form)

        # 摘要面板
        for key in self._SUMMARY_KEYS:
            lbl = self._summary_labels.get(key)
            if lbl is None:
                continue
            value = summary.get(key, 0)
            if key == "income" or key == "exp_total":
                lbl.setText(f"+{_fmt(value)}" if value else "+0")
            elif key == "expense":
                lbl.setText(f"-{_fmt(value)}" if value else "-0")
            else:
                lbl.setText(_fmt_signed(value))

        # 各區塊合計 + 每列 consumed/cost
        for sec in self._sections.values():
            sec.refresh_subtotal()

        # trio 差值
        for before_edit, after_edit, diff_lbl in self._diff_labels:
            diff = _parse_int(after_edit.text()) - _parse_int(before_edit.text())
            diff_lbl.setText(f"{diff:+,}")

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
        self._service.save_autosave(
            self._collect_form(), timer_elapsed=self._timer_elapsed
        )

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
            elapsed = int(record.get("_timer_elapsed", 0) or 0)
            if elapsed > 0:
                self._timer_elapsed = elapsed
                self._timer_display.setText(_fmt_elapsed(elapsed))
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
            if value in (None, 0, "", "0"):
                edit.setText("")
            else:
                edit.setText(str(value))

        _set(self._mesos_start_input, data.get("mesos_start"))
        _set(self._mesos_end_input,   data.get("mesos_end"))
        _set(self._shop_before_input, data.get("shop_before"))
        _set(self._shop_after_input,  data.get("shop_after"))
        _set(self._exp_start_input,   data.get("exp_start"))
        _set(self._exp_end_input,     data.get("exp_end"))

        minutes = data.get("duration_minutes", 1)
        self._duration_spin.setValue(
            max(1, int(minutes)) if minutes else 1
        )

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
            self._timer_elapsed = 0
            self._timer_display.setText(_fmt_elapsed(0))
            self._tick_timer.stop()
            self._mode = "manual"
            self._apply_mode_styles()
            self._duration_spin.setReadOnly(False)
        finally:
            self._loading = False
        self._apply_timer_controls_visibility()
        self._refresh_timer_start_btn()
        self._autosave_timer.stop()
        if self._service is not None:
            self._service.clear_autosave()
        self._recalc_all()

    def _clear_all_inputs(self):
        for sec in self._sections.values():
            sec.clear()
        for edit in (self._mesos_start_input, self._mesos_end_input,
                     self._shop_before_input, self._shop_after_input,
                     self._exp_start_input, self._exp_end_input):
            edit.clear()
        self._duration_spin.setValue(1)

    # ════════════════════════════════════════════════════════
    # 時間來源 manual / timer
    # ════════════════════════════════════════════════════════
    def _on_mode_toggle(self, mode: str):
        if mode == self._mode:
            return
        self._mode = mode
        if mode == "manual":
            self._tick_timer.stop()
            self._duration_spin.setReadOnly(False)
        else:
            # 切到計時器：鎖住 spin，但不自動啟動，等使用者按「開始」
            self._duration_spin.setReadOnly(True)
        self._apply_mode_styles()
        self._apply_timer_controls_visibility()
        self._refresh_timer_start_btn()

    def _on_timer_start_stop(self):
        """計時器模式下切換開始/停止"""
        if self._mode != "timer":
            return
        if self._tick_timer.isActive():
            self._tick_timer.stop()
        else:
            self._tick_timer.start()
        self._refresh_timer_start_btn()

    def _on_timer_reset(self):
        """計時器模式下清空累積秒數（不影響藥水/楓幣/經驗輸入）"""
        if self._mode != "timer":
            return
        self._tick_timer.stop()
        self._timer_elapsed = 0
        self._timer_display.setText(_fmt_elapsed(0))
        self._duration_spin.setValue(1)
        self._refresh_timer_start_btn()
        self._schedule_autosave()

    def _apply_timer_controls_visibility(self):
        """計時器模式顯示 開始/重置；手動模式隱藏"""
        visible = (self._mode == "timer")
        self._timer_start_btn.setVisible(visible)
        self._timer_reset_btn.setVisible(visible)

    def _refresh_timer_start_btn(self):
        """依 tick_timer 狀態切換按鈕文字/圖示"""
        if self._tick_timer.isActive():
            self._timer_start_btn.setText("  停止")
            self._timer_start_btn.setIcon(lucide_icon("square", "#ffffff", 14, stroke=1.6))
        else:
            self._timer_start_btn.setText("  開始")
            self._timer_start_btn.setIcon(lucide_icon("play", "#ffffff", 14, stroke=1.6))

    def _apply_mode_styles(self):
        for name, btn in self._mode_chips.items():
            active = (name == self._mode)
            if active:
                btn.setStyleSheet(
                    f"QPushButton {{ color: {T.ORANGE};"
                    f" background: {T.alpha(T.ORANGE, 38)};"
                    f" border: none; border-radius: {T.R_SM}px;"
                    f" padding: 0 10px; font-size: 11px; font-weight: 700; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ color: {T.TEXT_DIM};"
                    f" background: transparent; border: 1px solid {T.BORDER};"
                    f" border-radius: {T.R_SM}px;"
                    f" padding: 0 10px; font-size: 11px; }}"
                    f"QPushButton:hover {{ color: {T.TEXT_HI};"
                    f" border-color: {T.BORDER_HOVER}; }}"
                )

    def _on_tick(self):
        self._timer_elapsed += 1
        self._timer_display.setText(_fmt_elapsed(self._timer_elapsed))
        if self._timer_elapsed % 60 == 0:
            self._duration_spin.setValue(max(1, self._timer_elapsed // 60))
            self._on_input_changed()
