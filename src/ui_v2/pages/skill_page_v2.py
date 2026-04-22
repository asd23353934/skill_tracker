"""
技能倒數頁面 — V2（純 UI 殼，使用假資料）
三欄：玩家 | BOSS | 道具
每欄含子分類標題 + 多張技能卡（左=icon/name，中=2 行控件，右=⋮）
依 docs/DESIGN_V2.md

══════════════════════════════════════════════════════════════
綁定契約（最複雜，最後接）
══════════════════════════════════════════════════════════════
建構參數：
    SkillPageV2(parent, app)

讀取（每張技能卡需要的欄位）：
    元資料（唯讀，來自 config.json）：
        app.skill_manager.get_skills() / get_items()
        每筆：{ id, name, icon, cooldown, category, subcategory }
    狀態（來自當前 profile，via property 委派）：
        app.skill_hotkeys[id]            -> str
        app.skill_permanent[id]          -> bool
        app.skill_loop[id]               -> bool
        app.skill_alert_enabled[id]      -> bool
        app.skill_cooldown_overrides[id] -> int | None
        app.skill_alert_seconds_overrides[id] -> int | None
        app.skill_sound_overrides[id]    -> str | None
        app.skill_alert_sound_overrides[id] -> str | None
    圖片：
        app.skill_pixmap_cache.get_card(skill_id) -> QPixmap

操作（依卡片中各控件）：
    [秒數 InputChip]  → 寫 cooldown_overrides[id]; reset 則 del key
    [按鍵 InputChip]  → app.hotkey_manager.begin_capture(id, name)
                        ；reset 則清空 hotkeys[id] + 解綁
    [常 checkbox]     → permanent[id] = bool
                        True  → window_manager.create_permanent_window(id)
                        False → 關閉常駐視窗
    [循 checkbox]     → loop[id] = bool
    [提 checkbox]     → alert_enabled[id] = bool
    [提秒 pill]       → 編輯 alert_seconds_overrides[id]
    [⋮ 設定]         → SkillDetailDialogV2(app, skill_id) — 含：
                        - 自訂圖示 / 重置圖示
                        - 結束聲音 sound_overrides[id]
                        - 提前聲音 alert_sound_overrides[id]
                        - 試聽 → app.sound_manager.play(...)
                        - 從清單移除（profile 層）

寫回：
    每次變更 → config_manager.save_profile(name, snapshot)
    snapshot 的組合方式沿用 v1 SkillPage._build_profile_snapshot()

刷新時機：
    showEvent: rebuild 全頁
    profile 切換: 由 app 通知 → 全頁 rebuild
    單一卡片狀態變更: 只更新該卡，不 rebuild

執行緒安全：
    hotkey trigger 在 daemon thread；卡片高亮需走 dispatcher.schedule(0)

不在本頁職責：
    - 倒數視窗本身（WindowManager 管理）
    - 全域音量 / 全域提示開關（settings 對話框）
    - 配置切換 UI（status_bar / profile_dialog）
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QCheckBox, QScrollArea,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QPolygon
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import Card, IconBadge, StatusChip
from src.ui_v2.dialogs.skill_detail_dialog_v2 import SkillDetailDialogV2
from src.ui_v2.lucide import lucide_pixmap


# ════════════════════════════════════════════════════════════
# 自繪小按鈕（避免字符渲染不一致）
# ════════════════════════════════════════════════════════════

class _PaintedBtn(QPushButton):
    """自繪圖示按鈕基底"""
    def __init__(self, w: int, h: int, tooltip: str, hover_color: str = None):
        super().__init__()
        self._hover = False
        self._hover_color = hover_color or T.ORANGE
        self.setFixedSize(w, h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none;"
            f" border-radius: {T.R_SM}px; }}"
            f"QPushButton:hover {{ background: {T.BG_INPUT}; }}"
        )

    def enterEvent(self, e):  # noqa: N802
        self._hover = True; self.update(); super().enterEvent(e)
    def leaveEvent(self, e):  # noqa: N802
        self._hover = False; self.update(); super().leaveEvent(e)


class ResetBtn(_PaintedBtn):
    """↺ 重置 — 自繪：3/4 圓 + 箭頭"""
    def __init__(self, tooltip: str = "重置"):
        super().__init__(20, 22, tooltip)

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor(T.RED if self._hover else T.TEXT_DIM)
        pen = QPen(col, 1.3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        cx, cy = self.width() / 2, self.height() / 2
        # 3/4 圓弧 — 缺口在右上
        p.drawArc(int(cx - 5), int(cy - 5), 10, 10, -30 * 16, 300 * 16)
        # 三角箭頭（朝左下，標示「逆時針回轉」）
        tri = QPolygon([
            QPoint(int(cx + 4), int(cy - 6)),
            QPoint(int(cx + 7), int(cy - 2)),
            QPoint(int(cx + 1), int(cy - 2)),
        ])
        p.setBrush(col); p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(tri)
        p.end()


class MoreBtn(_PaintedBtn):
    """詳細設定 — Lucide settings"""
    ICON_SIZE = 16

    def __init__(self, tooltip: str = "詳細設定"):
        super().__init__(28, 28, tooltip)

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        col = T.ORANGE if self._hover else T.TEXT_DIM
        pix = lucide_pixmap("settings", col, self.ICON_SIZE, stroke=1.6)
        p = QPainter(self)
        x = (self.width() - self.ICON_SIZE) // 2
        y = (self.height() - self.ICON_SIZE) // 2
        p.drawPixmap(x, y, pix)
        p.end()


# ════════════════════════════════════════════════════════════
# 假資料 — 加入子分類分組
# (skill_name, cooldown_sec, hotkey)
# ════════════════════════════════════════════════════════════
DEMO_DATA = {
    "player": [
        ("攻擊", [
            ("劍氣縱橫", 30, "F1"),
            ("無雙劍訣", 60, "F2"),
            ("烈焰連斬", 25, ""),
        ]),
        ("輔助", [
            ("怒氣咆哮", 45, "F3"),
            ("守護壁壘", 180, "G"),
        ]),
        ("大絕", [
            ("天降神兵", 90, "F5"),
            ("極光裂閃", 120, ""),
        ]),
    ],
    "boss": [
        ("召喚物", [
            ("骷髏召喚", 90, ""),
            ("詛咒之眼", 120, ""),
        ]),
        ("直接攻擊", [
            ("巴洛古重擊", 25, ""),
            ("黑龍火吼",   60, ""),
            ("地裂衝擊",   45, ""),
        ]),
    ],
    "item": [
        ("補給", [
            ("紅水",   10, "1"),
            ("藍水",   10, "2"),
            ("還元水", 30, "3"),
        ]),
        ("特殊", [
            ("解毒劑", 60, ""),
            ("聖水",  300, ""),
        ]),
    ],
}

CATEGORY_DEFS = [
    ("player", "玩家技能", "swords",        T.BLUE),
    ("boss",   "BOSS 技能", "skull",         T.RED),
    ("item",   "道具",     "flask-conical", T.GREEN),
]


# ════════════════════════════════════════════════════════════
# 小工具：通用按鈕產生
# ════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════
# InputChip — 「值 + ↺」整合成單一視覺單元
# ════════════════════════════════════════════════════════════

class InputChip(QFrame):
    """值 chip + 分離的 ↺ 重置按鈕

    兩個獨立圓角元件，中間有間距，不黏在一起。
    """
    GAP = 6

    def __init__(self, text: str, accent: str = None,
                 reset_tooltip: str = "重置",
                 value_w: int = 46, h: int = 22):
        super().__init__()
        self._accent = accent
        self.setFixedHeight(h)
        self.setStyleSheet("background: transparent;")

        L = QHBoxLayout(self)
        L.setContentsMargins(0, 0, 0, 0)
        L.setSpacing(self.GAP)

        # 值按鈕（獨立圓角）
        self.value_btn = QPushButton(text)
        self.value_btn.setFixedSize(value_w, h)
        self.value_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # 重置按鈕（獨立圓角）
        self.reset_btn = _ChipResetBtn(accent or T.TEXT_DIM, reset_tooltip, h)

        self._apply_style()

        L.addWidget(self.value_btn)
        L.addWidget(self.reset_btn)

    def _apply_style(self):
        if self._accent:
            bg       = T.alpha(self._accent, 38)
            bg_hover = T.alpha(self._accent, 70)
            fg       = self._accent
            self.value_btn.setStyleSheet(
                f"QPushButton {{ color: {fg}; background: {bg};"
                f" border: none; border-radius: {T.R_SM}px; padding: 0;"
                f" font-size: 11px; font-weight: 700; }}"
                f"QPushButton:hover {{ background: {bg_hover}; }}"
            )
            self.reset_btn.set_bg(bg, bg_hover)
        else:
            self.value_btn.setStyleSheet(
                f"QPushButton {{ color: {T.TEXT_DIM};"
                f" background: {T.BG_INPUT}; padding: 0;"
                f" border: 1px solid {T.BORDER};"
                f" border-radius: {T.R_SM}px;"
                f" font-size: 11px; font-weight: 600; }}"
                f"QPushButton:hover {{ color: {T.TEXT_HI};"
                f" border-color: {T.BORDER_HOVER}; }}"
            )
            self.reset_btn.set_bg(T.BG_INPUT, T.BG_HOVER, bordered=True)


class _ChipResetBtn(QPushButton):
    """獨立圓角的 ↺ 重置按鈕"""
    def __init__(self, icon_color: str, tooltip: str, h: int):
        super().__init__()
        self._icon_color = icon_color
        self._hover = False
        self.setFixedSize(h, h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)

    def set_bg(self, bg: str, bg_hover: str, bordered: bool = False):
        border = f"border: 1px solid {T.BORDER};" if bordered else "border: none;"
        self.setStyleSheet(
            f"QPushButton {{ background: {bg}; {border}"
            f" border-radius: {T.R_SM}px; padding: 0; }}"
            f"QPushButton:hover {{ background: {bg_hover}; }}"
        )

    def enterEvent(self, e):  # noqa: N802
        self._hover = True; self.update(); super().enterEvent(e)
    def leaveEvent(self, e):  # noqa: N802
        self._hover = False; self.update(); super().leaveEvent(e)

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        col = T.RED if self._hover else self._icon_color
        pix = lucide_pixmap("rotate-ccw", col, 12, stroke=2.0)
        p = QPainter(self)
        x = (self.width() - 12) // 2
        y = (self.height() - 12) // 2
        p.drawPixmap(x, y, pix)
        p.end()


def _pill_btn(text: str, accent: str = None, w: int = 40, h: int = 22) -> QPushButton:
    """資料 chip 樣式按鈕（cd / hk / alert_secs）"""
    btn = QPushButton(text)
    btn.setFixedSize(w, h)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if accent:
        btn.setStyleSheet(
            f"QPushButton {{ color: {accent};"
            f" background: {T.alpha(accent, 38)};"
            f" border: none; border-radius: {T.R_SM}px;"
            f" padding: 0; font-size: 11px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: {T.alpha(accent, 70)}; }}"
        )
    else:
        btn.setStyleSheet(
            f"QPushButton {{ color: {T.TEXT_DIM};"
            f" background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_SM}px;"
            f" padding: 0; font-size: 11px; font-weight: 600; }}"
            f"QPushButton:hover {{ color: {T.TEXT_HI};"
            f" border-color: {T.BORDER_HOVER}; }}"
        )
    return btn


def _accent_check(label: str, color: str, tooltip: str = "") -> QCheckBox:
    cb = QCheckBox(label)
    cb.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        cb.setToolTip(tooltip)
    cb.setStyleSheet(
        f"QCheckBox {{ color: {T.TEXT}; spacing: 3px;"
        f" background: transparent; font-size: 11px; }}"
        f"QCheckBox::indicator {{ width: 12px; height: 12px;"
        f" border-radius: 3px; border: 1px solid {T.BORDER_HOVER};"
        f" background: {T.BG_INPUT}; }}"
        f"QCheckBox::indicator:hover {{ border-color: {color}; }}"
        f"QCheckBox::indicator:checked {{ background: {color};"
        f" border-color: {color}; }}"
    )
    return cb


# ════════════════════════════════════════════════════════════
# SkillCard — 單張技能卡（2 行控件）
# ════════════════════════════════════════════════════════════

class SkillCard(QFrame):
    HEIGHT = 116

    def __init__(self, parent, name: str, cooldown: int, hotkey: str,
                 accent: str, icon_name: str = "circle"):
        super().__init__(parent)
        self._name   = name
        self._accent = accent
        self._icon   = icon_name
        self.setObjectName("skill_card")
        self.setFixedHeight(self.HEIGHT)
        self.setStyleSheet(
            f"QFrame#skill_card {{ background: {T.BG_ELEVATED};"
            f" border: none; border-radius: {T.R_MD}px; }}"
            f"QFrame#skill_card:hover {{ background: {T.BG_HOVER}; }}"
        )
        self._build(cooldown, hotkey)

    def _build(self, cooldown: int, hotkey: str):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(T.S_MD, T.S_SM, T.S_SM, T.S_SM)
        outer.setSpacing(T.S_MD)

        # ── 左：icon + 名稱（橫向、固定寬度，所有卡片對齊）──
        ICON_SIZE = 44
        NAME_W    = 64
        LEFT_W    = ICON_SIZE + T.S_SM + NAME_W

        left = QHBoxLayout()
        left.setSpacing(T.S_SM)
        left.setContentsMargins(0, 0, 0, 0)
        left.addWidget(IconBadge(self._icon, self._accent, ICON_SIZE))
        name_lbl = T.make_label(self._name, T.FONT_BODY,
                                color_override=T.TEXT_HI)
        name_lbl.setFixedWidth(NAME_W)
        name_lbl.setWordWrap(True)
        left.addWidget(name_lbl)

        left_wrap = QWidget()
        left_wrap.setFixedWidth(LEFT_W)
        lv = QVBoxLayout(left_wrap)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.addStretch()
        lv.addLayout(left)
        lv.addStretch()
        outer.addWidget(left_wrap)

        # ── 中：3 列垂直堆疊 ──
        center = QVBoxLayout()
        center.setSpacing(8)
        center.setContentsMargins(0, 0, 0, 0)
        center.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # row 1：秒數 + 重置秒數
        r1 = QHBoxLayout()
        r1.setSpacing(0); r1.setContentsMargins(0, 0, 0, 0)
        r1.addWidget(InputChip(f"{cooldown}s", T.CYAN, "重置秒數", value_w=46))
        r1.addStretch()
        center.addLayout(r1)

        # row 2：按鍵 + 重置按鍵
        r2 = QHBoxLayout()
        r2.setSpacing(0); r2.setContentsMargins(0, 0, 0, 0)
        hk_text  = hotkey or "未設"
        hk_color = T.YELLOW if hotkey else None
        r2.addWidget(InputChip(hk_text, hk_color, "清除按鍵", value_w=46))
        r2.addStretch()
        center.addLayout(r2)

        # row 3：常 循 提 + 提前秒數
        r3 = QHBoxLayout()
        r3.setSpacing(10); r3.setContentsMargins(0, 0, 0, 0)
        r3.addWidget(_accent_check("常", T.YELLOW, "常駐"))
        r3.addWidget(_accent_check("循", T.GREEN,  "循環"))
        alert_group = QHBoxLayout()
        alert_group.setSpacing(4)
        alert_group.setContentsMargins(0, 0, 0, 0)
        alert_group.addWidget(_accent_check("提", T.ORANGE, "提前提示"))
        alert_group.addWidget(_pill_btn("3s", T.ORANGE, w=30, h=20))
        r3.addLayout(alert_group)
        r3.addStretch()
        center.addLayout(r3)

        outer.addLayout(center, 1)

        # ── 右：設定（垂直置中）──
        more = MoreBtn()
        more.clicked.connect(self._open_detail)
        right_wrap = QWidget()
        rv = QVBoxLayout(right_wrap)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.addStretch()
        rv.addWidget(more)
        rv.addStretch()
        outer.addWidget(right_wrap)

    def _open_detail(self):
        dlg = SkillDetailDialogV2(self.window(), self._name)
        dlg.exec()


# ════════════════════════════════════════════════════════════
# SkillColumn — 一個技能欄（標題 + 子分類 + 卡片 滾動）
# ════════════════════════════════════════════════════════════

class SkillColumn(Card):
    def __init__(self, parent, title: str, glyph: str, accent: str,
                 sections: list):
        """sections = [(subcategory_name, [(name, cd, hk), ...]), ...]"""
        super().__init__(parent)
        L = self.layout()
        L.setSpacing(T.S_MD)

        total = sum(len(items) for _, items in sections)

        # 欄位標題
        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(IconBadge(glyph, accent, 28))
        head.addWidget(T.make_label(title, T.FONT_CARD_TITLE))
        head.addStretch()
        head.addWidget(StatusChip(f"{total}", accent))
        L.addLayout(head)

        # 滾動內容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        inner = QWidget()
        v = QVBoxLayout(inner)
        v.setContentsMargins(0, 0, T.S_XS, 0)
        v.setSpacing(T.S_SM)

        for sub_name, items in sections:
            v.addWidget(self._sub_header(sub_name, len(items), accent))
            for name, cd, hk in items:
                v.addWidget(SkillCard(inner, name, cd, hk, accent, glyph))
            v.addSpacing(T.S_XS)

        v.addStretch()
        scroll.setWidget(inner)
        L.addWidget(scroll, 1)

    def _sub_header(self, name: str, count: int, accent: str) -> QWidget:
        """子分類小標題：橫線 + 文字"""
        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(T.S_XS, T.S_XS, T.S_XS, 0)
        h.setSpacing(T.S_SM)
        lbl = T.make_label(name, T.FONT_LABEL)
        h.addWidget(lbl)
        cnt = QLabel(str(count))
        cnt.setStyleSheet(
            f"color: {T.TEXT_MUTED}; font-size: 10px; background: transparent;"
        )
        h.addWidget(cnt)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {T.BORDER_SOFT}; border: none;")
        h.addWidget(line, 1)
        return wrap


# ════════════════════════════════════════════════════════════
# SkillPageV2 — 主頁面
# ════════════════════════════════════════════════════════════

class SkillPageV2(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self._build()

    def _toast_pending(self):
        if self.app is not None and hasattr(self.app, "toast"):
            self.app.toast.show("此功能尚未接 V2，請暫用 V1 版", "info")

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        # 工具列
        bar = QHBoxLayout()
        bar.setSpacing(T.S_SM)
        bar.addWidget(T.make_label("技能倒數", T.FONT_SECTION))
        bar.addStretch()
        bar.addWidget(T.make_label("快速切換", T.FONT_LABEL))
        for label, color in (
            ("常駐", T.YELLOW),
            ("循環", T.GREEN),
            ("提醒", T.ORANGE),
        ):
            chip = self._toggle_chip(label, color)
            chip.clicked.connect(self._toast_pending)
            bar.addWidget(chip)
        root.addLayout(bar)

        # 三欄
        cols = QHBoxLayout()
        cols.setSpacing(T.S_MD)
        for key, title, glyph, accent in CATEGORY_DEFS:
            cols.addWidget(
                SkillColumn(self, title, glyph, accent, DEMO_DATA[key]),
                1,
            )
        root.addLayout(cols, 1)

    def _toggle_chip(self, label: str, color: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(T.CHIP_H + 4)
        btn.setStyleSheet(
            f"QPushButton {{ color: {color};"
            f" background: {T.alpha(color, 38)};"
            f" border: none; border-radius: {T.R_SM}px;"
            f" padding: 0 12px; font-size: 11px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: {T.alpha(color, 70)}; }}"
        )
        return btn
