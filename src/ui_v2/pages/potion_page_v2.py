"""
練功水錢頁面 — V2（純 UI 殼，假資料）
左：藥水區段 + 楓幣經驗（捲動）｜右：本次摘要 + 數量計算機
依 docs/DESIGN_V2.md

══════════════════════════════════════════════════════════════
綁定契約
══════════════════════════════════════════════════════════════
建構參數：
    PotionPageV2(parent, app)

直接沿用 v1 邏輯（src/ui/pages/potion_cost_page.py）：
    - 計算公式（消耗、水錢、淨收益、速率）抽成 pure function helper 共用

讀取：
    autosave: app.config_manager.load_potion_autosave()  # dict | None
    紀錄列表: app.config_manager.list_potion_saves()      # list[str]
    單筆紀錄: app.config_manager.load_potion_record(name) # dict

操作：
    [新增藥水/清除全部]   → 更新本地 state，觸發重算 + autosave
    [輸入欄變更]          → 即時重算右側摘要 + autosave (debounce 500ms)
    [清除]                → reset 本地 state + autosave
    [全部重置]            → 數值歸零但保留欄位
    [載入紀錄]            → PotionLoadDialogV2 → load_potion_record
    [儲存]                → PotionSaveDialogV2 → save_potion_record(name, data)
    [手動/計時器]         → toggle 練功時間來源；計時器模式下 QTimer 1s tick

寫回：
    所有變更寫入 autosave；具名儲存才寫紀錄檔
    autosave 結構需與 v1 相容：{ hp: [...], mp: [...], comp: [...], meso: {...}, time: {...} }

不在本頁職責：
    - 紀錄檔的 rename / delete UI（在 PotionLoadDialogV2 內處理）
    - 配置切換時是否清空 autosave（由 app 層決定）
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QScrollArea, QLineEdit, QSpinBox,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import IconBadge
from src.ui_v2.lucide import lucide_pixmap, lucide_icon


# ════════════════════════════════════════════════════════════
# 假資料
# ════════════════════════════════════════════════════════════
DEMO_HP = [
    ("紅水",     50,  120, 60),    # name, price, before, after
    ("特紅水",   200, 80,  20),
]
DEMO_MP = [
    ("藍水",     45,  150, 90),
    ("特藍水",   180, 60,  10),
]
DEMO_MIX = [
    ("還元水",   500, 30,  10),
]
DEMO_MESO   = (1_000_000, 1_350_000)   # before, after
DEMO_SHOP   = (1_350_000, 1_580_000)   # before, after sell
DEMO_EXP    = (12_345_678_900, 12_456_789_000)
DEMO_MIN    = 60


# ════════════════════════════════════════════════════════════
# 共用 widget helpers
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
# PotionRow — 單筆藥水
# ════════════════════════════════════════════════════════════

class _PotionRow(QFrame):
    def __init__(self, accent: str, name: str, price: int, before: int, after: int):
        super().__init__()
        self.setStyleSheet(
            f"QFrame {{ background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_MD}px; }}"
        )
        L = QHBoxLayout(self)
        L.setContentsMargins(T.S_SM, 6, T.S_SM, 6)
        L.setSpacing(T.S_SM)

        L.addWidget(IconBadge("droplet", accent, 26))

        L.addWidget(_input(name, w=90, align_right=False, color=T.TEXT_HI))

        unit = QLabel("單價")
        unit.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: 10px; background: transparent;")
        L.addWidget(unit)
        L.addWidget(_input(f"{price:,}", w=70))

        before_lbl = QLabel("練功前")
        before_lbl.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: 10px; background: transparent;")
        L.addWidget(before_lbl)
        L.addWidget(_input(str(before), w=60))

        after_lbl = QLabel("練功後")
        after_lbl.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: 10px; background: transparent;")
        L.addWidget(after_lbl)
        L.addWidget(_input(str(after), w=60))

        used  = before - after
        cost  = used * price
        used_lbl = QLabel(f"消耗 {used}")
        used_lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
        )
        L.addWidget(used_lbl)

        L.addWidget(_readonly_metric(f"{cost:,}", color=T.RED, w=86))

        L.addStretch()
        L.addWidget(_icon_btn("x", "刪除", T.TEXT_DIM, hover_red=True))


# ════════════════════════════════════════════════════════════
# PotionSection — HP / MP / 複合
# ════════════════════════════════════════════════════════════

def _potion_section(title: str, icon: str, accent: str,
                    rows_data: list) -> QFrame:
    total = sum((b - a) * p for _, p, b, a in rows_data)
    card, L = _section_card(title, icon, accent, f"{total:,}")

    # 操作列
    ops = QHBoxLayout()
    ops.setSpacing(T.S_SM)
    add = _text_btn("新增藥水", "plus", "ghost")
    ops.addWidget(add)
    clear = _text_btn("清除全部", "trash-2", "danger")
    ops.addWidget(clear)
    ops.addStretch()
    L.addLayout(ops)

    for n, p, b, a in rows_data:
        L.addWidget(_PotionRow(accent, n, p, b, a))

    return card


# ════════════════════════════════════════════════════════════
# MesoExpSection — 楓幣 / 商店 / 經驗 / 時間
# ════════════════════════════════════════════════════════════

def _meso_exp_section() -> QFrame:
    card, L = _section_card("楓幣 ・ 經驗 ・ 時間", "coins", T.YELLOW)

    def trio(label_text, before, after, accent):
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
        h.addWidget(_input(f"{before:,}", w=120))

        a_lbl = QLabel("後")
        a_lbl.setStyleSheet(f"color: {T.TEXT_MUTED}; font-size: 10px; background: transparent;")
        h.addWidget(a_lbl)
        h.addWidget(_input(f"{after:,}", w=120))

        diff = after - before
        h.addStretch()
        eq = QLabel("=")
        eq.setStyleSheet(f"color: {T.TEXT_MUTED}; background: transparent;")
        h.addWidget(eq)
        h.addWidget(_readonly_metric(f"{diff:+,}", accent, w=120))
        return wrap

    L.addWidget(trio("撿取楓幣", *DEMO_MESO,  T.YELLOW))
    L.addWidget(trio("商店收益", *DEMO_SHOP,  T.GREEN))
    L.addWidget(trio("獲取經驗", *DEMO_EXP,   T.PURPLE))

    # 時間列
    time_wrap = QFrame()
    time_wrap.setStyleSheet(
        f"QFrame {{ background: {T.BG_INPUT};"
        f" border: 1px solid {T.BORDER};"
        f" border-radius: {T.R_MD}px; }}"
    )
    th = QHBoxLayout(time_wrap)
    th.setContentsMargins(T.S_SM, 6, T.S_SM, 6)
    th.setSpacing(T.S_SM)

    icon_lbl = QLabel()
    icon_lbl.setFixedSize(14, 14)
    icon_lbl.setPixmap(lucide_pixmap("clock", T.ORANGE, 14, stroke=1.6))
    icon_lbl.setStyleSheet("background: transparent;")
    th.addWidget(icon_lbl)

    th.addWidget(QLabel("練功時間"))
    th.itemAt(th.count() - 1).widget().setStyleSheet(
        f"color: {T.TEXT}; font-size: 11px; font-weight: 600; background: transparent;"
    )

    th.addStretch()

    # 切換 chip
    for label, active in (("手動", True), ("計時器", False)):
        b = QPushButton(label)
        b.setFixedHeight(24)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        if active:
            b.setStyleSheet(
                f"QPushButton {{ color: {T.ORANGE};"
                f" background: {T.alpha(T.ORANGE, 38)};"
                f" border: none; border-radius: {T.R_SM}px;"
                f" padding: 0 10px; font-size: 11px; font-weight: 700; }}"
            )
        else:
            b.setStyleSheet(
                f"QPushButton {{ color: {T.TEXT_DIM};"
                f" background: transparent; border: 1px solid {T.BORDER};"
                f" border-radius: {T.R_SM}px;"
                f" padding: 0 10px; font-size: 11px; }}"
                f"QPushButton:hover {{ color: {T.TEXT_HI};"
                f" border-color: {T.BORDER_HOVER}; }}"
            )
        th.addWidget(b)

    spin = QSpinBox()
    spin.setRange(1, 600)
    spin.setValue(DEMO_MIN)
    spin.setSuffix(" 分")
    spin.setFixedHeight(26)
    spin.setFixedWidth(86)
    spin.setStyleSheet(
        f"QSpinBox {{ color: {T.TEXT_HI}; background: {T.BG_SURFACE};"
        f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
        f" padding: 0 6px; font-size: 11px; }}"
    )
    th.addWidget(spin)
    L.addWidget(time_wrap)

    return card


# ════════════════════════════════════════════════════════════
# Right panel: 摘要 / 計算機
# ════════════════════════════════════════════════════════════

def _summary_card() -> QFrame:
    card, L = _section_card("本次練功摘要", "trending-up", T.GREEN)

    def line(label, value, color):
        wrap = QHBoxLayout()
        wrap.setSpacing(T.S_SM)
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
        )
        wrap.addWidget(lbl)
        wrap.addStretch()
        val = QLabel(value)
        val.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 700;"
            f" background: transparent;"
        )
        wrap.addWidget(val)
        return wrap

    L.addLayout(line("總收入",   "+1,580,000",     T.GREEN))
    L.addLayout(line("總支出",   "-26,800",        T.RED))
    L.addLayout(line("淨收益",   "+1,553,200",     T.YELLOW))
    L.addLayout(line("獲取經驗", "+111,110,100",   T.PURPLE))

    sep = QFrame()
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {T.BORDER_SOFT}; border: none;")
    L.addWidget(sep)

    rate = QLabel("平均速率")
    rate.setStyleSheet(
        f"color: {T.TEXT_DIM}; font-size: 10px; font-weight: 600;"
        f" background: transparent; letter-spacing: 1px;"
    )
    L.addWidget(rate)

    L.addLayout(line("每 10 分鐘 收益", "258,866", T.YELLOW))
    L.addLayout(line("每 60 分鐘 收益", "1,553,200", T.YELLOW))
    L.addLayout(line("每 60 分鐘 經驗", "111M",     T.PURPLE))

    return card


def _calculator_card() -> QFrame:
    card, L = _section_card("數量計算機", "calculator", T.CYAN)

    cap = QLabel("組數 × 3000 + 剩餘")
    cap.setStyleSheet(
        f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
    )
    L.addWidget(cap)

    row = QHBoxLayout()
    row.setSpacing(T.S_SM)
    row.addWidget(_input("12", w=60))
    row.addWidget(QLabel("×"))
    row.itemAt(row.count() - 1).widget().setStyleSheet(
        f"color: {T.TEXT_DIM}; background: transparent;"
    )
    row.addWidget(_input("3000", w=80))
    row.addWidget(QLabel("+"))
    row.itemAt(row.count() - 1).widget().setStyleSheet(
        f"color: {T.TEXT_DIM}; background: transparent;"
    )
    row.addWidget(_input("450", w=60))
    L.addLayout(row)

    res = QHBoxLayout()
    res.addWidget(_readonly_metric("36,450", T.CYAN, w=120))
    res.addStretch()
    res.addWidget(_text_btn("複製", "copy", "ghost"))
    res.addWidget(_text_btn("重置", "rotate-ccw", "ghost"))
    L.addLayout(res)
    return card


# ════════════════════════════════════════════════════════════
# PotionPageV2
# ════════════════════════════════════════════════════════════

class PotionPageV2(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self._build()

    def _toast_pending(self):
        """完整接線尚未完成（含計算/autosave/save dialog），暫指引到 V1"""
        if self.app is not None and hasattr(self.app, "toast"):
            self.app.toast.show("此功能尚未接 V2，請暫用 V1 版", "info")

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        # ── 工具列 ──
        bar = QHBoxLayout()
        bar.setSpacing(T.S_SM)
        bar.addWidget(T.make_label("練功水錢", T.FONT_SECTION))
        bar.addStretch()
        for label, icon, kind in [
            ("清除",     "trash-2",     "ghost"),
            ("全部重置", "rotate-ccw",  "danger"),
            ("載入紀錄", "folder-open", "ghost"),
            ("儲存",     "save",        "primary"),
        ]:
            btn = _text_btn(label, icon, kind)
            btn.clicked.connect(self._toast_pending)
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

        v.addWidget(_potion_section("HP 藥水",  "heart",         T.RED,    DEMO_HP))
        v.addWidget(_potion_section("MP 藥水",  "droplet",       T.CYAN,   DEMO_MP))
        v.addWidget(_potion_section("複合藥水", "flask-conical", T.PURPLE, DEMO_MIX))
        v.addWidget(_meso_exp_section())
        v.addStretch()

        scroll.setWidget(inner)
        body.addWidget(scroll, 1)

        # 右：摘要 + 計算機（固定寬度）
        right_wrap = QWidget()
        right_wrap.setFixedWidth(320)
        rv = QVBoxLayout(right_wrap)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(T.S_MD)
        rv.addWidget(_summary_card())
        rv.addWidget(_calculator_card())
        rv.addStretch()
        body.addWidget(right_wrap)

        root.addLayout(body, 1)
