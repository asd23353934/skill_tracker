"""
技能倒數頁面 V2 (預覽版) — Modern Dark Dashboard 風格
從零打造，與舊版並存以便對比；不覆蓋舊版任何檔案
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFontMetrics


# ────────────────────────── 調色盤（局部，僅此頁） ──────────────────────────
class V2:
    # 背景層（扁平、低對比）
    BG_PAGE      = "#0b0f17"
    BG_PANEL     = "#121826"
    BG_CARD      = "#161d2d"
    BG_CARD_HOV  = "#1c2438"
    BG_INPUT     = "#1f2738"

    # 邊框：極淡 subtle
    BORDER       = "#232c40"
    BORDER_STRONG = "#2e3a55"

    # 文字
    TXT_HI       = "#e8edf5"
    TXT          = "#aab4c7"
    TXT_DIM      = "#6a7690"

    # 欄位強調色
    COL_PLAYER   = "#5b8def"
    COL_BOSS     = "#ef6d6d"
    COL_ITEM     = "#3dd598"

    # 狀態色（與原專案一致）
    DOT_PERM     = "#fbbf24"   # 常駐
    DOT_LOOP     = "#10b981"   # 循環
    DOT_ALERT    = "#fb923c"   # 提醒


# ────────────────────────── 原子元件 ──────────────────────────

class DotToggle(QPushButton):
    """彩色小圓點 toggle — 填滿=on，空心=off"""
    def __init__(self, parent, color, tooltip):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(14, 14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        self._color = color
        self._apply()
        self.toggled.connect(lambda _: self._apply())

    def _apply(self):
        on = self.isChecked()
        bg = self._color if on else "transparent"
        border = self._color if on else V2.BORDER_STRONG
        self.setStyleSheet(
            f"QPushButton {{ background: {bg}; border: 2px solid {border};"
            f" border-radius: 7px; }}"
            f"QPushButton:hover {{ border-color: {self._color}; }}"
        )


class Chip(QPushButton):
    """圓角小標籤按鈕（快捷鍵、秒數等）"""
    def __init__(self, parent, text, tone="neutral"):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(22)
        self.set_tone(tone)

    def set_tone(self, tone):
        palettes = {
            "neutral": (V2.BG_INPUT,  V2.TXT,     V2.BORDER),
            "active":  ("#2b3a5e",    "#c6d5ff",  "#4169c9"),
            "warn":    ("#3a2c1a",    "#ffd396",  "#8b5a1e"),
            "muted":   ("transparent", V2.TXT_DIM, "transparent"),
        }
        bg, fg, bd = palettes.get(tone, palettes["neutral"])
        self.setStyleSheet(
            f"QPushButton {{ background: {bg}; color: {fg};"
            f" border: 1px solid {bd}; border-radius: 11px;"
            f" padding: 0 10px; font-size: 11px; font-weight: 600; }}"
            f"QPushButton:hover {{ border-color: {V2.COL_PLAYER}; color: {V2.TXT_HI}; }}"
        )


class SegmentedBar(QFrame):
    """頂部『全選』分段控制：三段彩點+文字"""
    def __init__(self, parent, on_click):
        super().__init__(parent)
        self.setObjectName("seg_bar")
        self.setStyleSheet(
            f"QFrame#seg_bar {{ background: {V2.BG_PANEL};"
            f" border: 1px solid {V2.BORDER}; border-radius: 18px; }}"
        )
        self.setFixedHeight(34)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 6, 0)
        lay.setSpacing(8)

        title = QLabel("全選")
        title.setStyleSheet(
            f"color: {V2.TXT_DIM}; font-size: 11px; background: transparent;"
        )
        lay.addWidget(title)

        for text, key, color in [
            ("常駐", "permanent", V2.DOT_PERM),
            ("循環", "loop",      V2.DOT_LOOP),
            ("提醒", "alert",     V2.DOT_ALERT),
        ]:
            btn = QPushButton(f"●  {text}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda _=False, k=key: on_click(k))
            btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {color};"
                f" border: none; padding: 0 10px; font-size: 11px;"
                f" font-weight: 600; border-radius: 13px; }}"
                f"QPushButton:hover {{ background: {V2.BG_CARD_HOV};"
                f" color: {V2.TXT_HI}; }}"
            )
            lay.addWidget(btn)


# ────────────────────────── 技能卡片 ──────────────────────────

class SkillCardV2(QFrame):
    """扁平現代卡片，76px 高

    結構：
      ┌───────────────────────────────────────────┐
      │ [icon]  名稱         F1            ⋮      │
      │ 44x44   60 秒        ● ● ●               │
      └───────────────────────────────────────────┘
    """
    HEIGHT = 76

    def __init__(self, parent, skill_id, skill, app, accent):
        super().__init__(parent)
        self.skill_id = skill_id
        self.skill    = skill
        self.app      = app
        self._accent  = accent

        self.setFixedHeight(self.HEIGHT)
        self.setObjectName("card")
        self._apply_base_style()
        self._build_ui()

    # ── 樣式 ──
    def _apply_base_style(self, hovering=False):
        bg = V2.BG_CARD_HOV if hovering else V2.BG_CARD
        self.setStyleSheet(
            f"QFrame#card {{ background: {bg};"
            f" border: 1px solid {V2.BORDER};"
            f" border-left: 3px solid {self._accent}55;"
            f" border-radius: 10px; }}"
            f"QFrame#card:hover {{ border-color: {self._accent};"
            f" border-left-color: {self._accent}; }}"
        )

    def enterEvent(self, e):  # noqa: N802
        self._set_reset_visible(True)
        super().enterEvent(e)

    def leaveEvent(self, e):  # noqa: N802
        self._set_reset_visible(False)
        super().leaveEvent(e)

    # ── 建構 ──
    def _build_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 8, 8, 8)
        outer.setSpacing(10)

        # ── 圖示 ──
        icon_box = QFrame()
        icon_box.setFixedSize(44, 44)
        icon_box.setStyleSheet(
            f"QFrame {{ background: {V2.BG_INPUT};"
            f" border: 1px solid {V2.BORDER}; border-radius: 8px; }}"
        )
        icon_lay = QVBoxLayout(icon_box)
        icon_lay.setContentsMargins(3, 3, 3, 3)
        icon_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = self.app.skill_manager.qpixmaps_card.get(self.skill_id)
        if pix and not pix.isNull():
            img = QLabel()
            img.setPixmap(pix)
            img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img.setStyleSheet("background: transparent; border: none;")
            icon_lay.addWidget(img)
        outer.addWidget(icon_box)

        # ── 中欄：兩行資訊 ──
        mid = QVBoxLayout()
        mid.setContentsMargins(0, 0, 0, 0)
        mid.setSpacing(2)

        # 第一行：名稱
        name = QLabel(self.skill.get("name", ""))
        name.setStyleSheet(
            f"color: {V2.TXT_HI}; font-size: 12px; font-weight: 600;"
            f" background: transparent; border: none;"
        )
        mid.addWidget(name)

        # 第二行：冷卻秒數（大字，主角）
        cd_row = QHBoxLayout()
        cd_row.setContentsMargins(0, 0, 0, 0)
        cd_row.setSpacing(6)

        self.cd_btn = QPushButton(f"{self.skill.get('cooldown', 0)}")
        self.cd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cd_btn.clicked.connect(lambda: self.app.edit_cooldown(self.skill_id))
        orig = self.app.get_original_cooldown(self.skill_id)
        modified = bool(orig and self.skill.get("cooldown") != orig)
        cd_color = V2.COL_PLAYER if modified else V2.TXT_HI
        self.cd_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none;"
            f" color: {cd_color}; font-size: 18px; font-weight: 700;"
            f" padding: 0; text-align: left; }}"
            f"QPushButton:hover {{ color: {V2.COL_PLAYER}; }}"
        )
        self.cd_btn.setFixedHeight(22)
        fm = QFontMetrics(self.cd_btn.font())
        self.cd_btn.setMinimumWidth(fm.horizontalAdvance("9999") + 4)

        sec_lbl = QLabel("秒")
        sec_lbl.setStyleSheet(
            f"color: {V2.TXT_DIM}; font-size: 11px;"
            f" background: transparent; border: none;"
        )

        cd_row.addWidget(self.cd_btn)
        cd_row.addWidget(sec_lbl)

        # 重置按鈕（hover 顯示）
        self.reset_cd = self._make_reset_btn(
            "↺", "重置冷卻秒數",
            lambda: self.app.reset_cooldown(self.skill_id),
        )
        cd_row.addWidget(self.reset_cd)

        cd_row.addStretch()
        mid.addLayout(cd_row)

        outer.addLayout(mid, 1)

        # ── 右欄：快捷鍵 chip + 三狀態點 + ⋮ ──
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(4)
        right.setAlignment(Qt.AlignmentFlag.AlignRight)

        # 快捷鍵 chip 行
        hk_row = QHBoxLayout()
        hk_row.setContentsMargins(0, 0, 0, 0)
        hk_row.setSpacing(4)
        hk_row.addStretch()

        hk_text = self.skill.get("hotkey", "") or "未設定"
        has_hk  = bool(self.skill.get("hotkey"))
        self.hk_chip = Chip(self, hk_text, "active" if has_hk else "muted")
        self.hk_chip.clicked.connect(
            lambda: self.app.hotkey_manager.begin_capture(
                self.skill_id, self.skill["name"]
            )
        )
        hk_row.addWidget(self.hk_chip)

        self.reset_hk = self._make_reset_btn(
            "✕", "清除快捷鍵",
            lambda: self.app.reset_hotkey(self.skill_id),
        )
        hk_row.addWidget(self.reset_hk)

        # ⋮
        more = QPushButton("⋮")
        more.setFixedSize(22, 22)
        more.setCursor(Qt.CursorShape.PointingHandCursor)
        more.setToolTip("技能詳細設定")
        more.clicked.connect(lambda: self.app.show_skill_detail(self.skill_id))
        more.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none;"
            f" color: {V2.TXT_DIM}; font-size: 16px; border-radius: 4px; }}"
            f"QPushButton:hover {{ background: {V2.BG_INPUT};"
            f" color: {V2.TXT_HI}; }}"
        )
        hk_row.addWidget(more)

        right.addLayout(hk_row)

        # 狀態點 + 提醒秒數 chip
        dot_row = QHBoxLayout()
        dot_row.setContentsMargins(0, 0, 0, 0)
        dot_row.setSpacing(6)
        dot_row.addStretch()

        self.dot_perm = DotToggle(self, V2.DOT_PERM, "常駐顯示")
        self.dot_perm.setChecked(self.app.skill_permanent.get(self.skill_id, False))
        self.dot_perm.toggled.connect(self._on_perm_toggled)
        dot_row.addWidget(self.dot_perm)

        self.dot_loop = DotToggle(self, V2.DOT_LOOP, "循環提醒")
        self.dot_loop.setChecked(self.app.skill_loop.get(self.skill_id, False))
        self.dot_loop.toggled.connect(self._on_loop_toggled)
        dot_row.addWidget(self.dot_loop)

        self.dot_alert = DotToggle(self, V2.DOT_ALERT, "提前提示")
        self.dot_alert.setChecked(self.app.skill_alert_enabled.get(self.skill_id, False))
        self.dot_alert.toggled.connect(self._on_alert_toggled)
        dot_row.addWidget(self.dot_alert)

        # 提醒秒數 chip
        override = self.app.skill_alert_seconds_overrides.get(self.skill_id)
        sec_val  = override if override is not None else self.app.alert_before_seconds
        self.alert_sec_chip = Chip(
            self, f"{sec_val}s",
            "warn" if override is not None else "neutral",
        )
        self.alert_sec_chip.setFixedHeight(18)
        self.alert_sec_chip.setStyleSheet(
            self.alert_sec_chip.styleSheet() + " QPushButton { font-size: 10px; }"
        )
        self.alert_sec_chip.clicked.connect(
            lambda: self.app.edit_alert_seconds(self.skill_id)
        )
        dot_row.addWidget(self.alert_sec_chip)

        right.addLayout(dot_row)

        outer.addLayout(right)

        # 初始隱藏 reset 按鈕
        self._set_reset_visible(False)

    def _make_reset_btn(self, glyph, tip, handler):
        btn = QPushButton(glyph)
        btn.setFixedSize(18, 18)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tip)
        btn.clicked.connect(handler)
        btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none;"
            f" color: {V2.TXT_DIM}; font-size: 11px; border-radius: 3px; }}"
            f"QPushButton:hover {{ color: #ef6d6d; background: {V2.BG_INPUT}; }}"
        )
        return btn

    def _set_reset_visible(self, visible):
        for b in (self.reset_cd, self.reset_hk):
            b.setVisible(visible)

    # ── 狀態 handler：呼叫既有 app 方法，但用 shim 物件替代 QCheckBox ──
    def _shim(self, checked):
        class _S:
            def isChecked(_self): return checked
            def setChecked(_self, v): pass
        return _S()

    def _on_perm_toggled(self, checked):
        self.app.update_skill_setting_exclusive(
            self.skill_id, "permanent", self._shim(checked),
        )
        # 同步互斥（若 app 關閉 loop，回填自身視覺）
        if checked:
            self.dot_loop.blockSignals(True)
            self.dot_loop.setChecked(False)
            self.dot_loop.blockSignals(False)

    def _on_loop_toggled(self, checked):
        self.app.update_skill_setting_exclusive(
            self.skill_id, "loop", self._shim(checked),
        )
        if checked:
            self.dot_perm.blockSignals(True)
            self.dot_perm.setChecked(False)
            self.dot_perm.blockSignals(False)

    def _on_alert_toggled(self, checked):
        self.app.update_alert_setting(self.skill_id, self._shim(checked))


# ────────────────────────── 欄位（玩家/BOSS/道具） ──────────────────────────

class ColumnV2(QFrame):
    """單一欄位：標題列（圓點+名稱+計數 badge）+ 卡片捲動區"""

    def __init__(self, parent, title, category, accent, app):
        super().__init__(parent)
        self.app = app
        self.category = category
        self._accent  = accent

        self.setObjectName("col")
        self.setStyleSheet(
            f"QFrame#col {{ background: {V2.BG_PANEL};"
            f" border: 1px solid {V2.BORDER}; border-radius: 14px; }}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)

        # 頂部：彩色圓點 + 標題 + 數量 badge
        head = QHBoxLayout()
        head.setSpacing(8)
        dot = QLabel("●")
        dot.setStyleSheet(
            f"color: {accent}; font-size: 13px; background: transparent;"
        )
        head.addWidget(dot)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {V2.TXT_HI}; font-size: 13px; font-weight: 700;"
            f" background: transparent;"
        )
        head.addWidget(title_lbl)

        count = self._total_count()
        badge = QLabel(str(count))
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"QLabel {{ background: {V2.BG_CARD}; color: {V2.TXT_DIM};"
            f" border: 1px solid {V2.BORDER}; border-radius: 9px;"
            f" padding: 0 8px; font-size: 10px; font-weight: 600;"
            f" min-height: 18px; min-width: 22px; }}"
        )
        head.addWidget(badge)
        head.addStretch()
        lay.addLayout(head)

        # 捲動區
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            f"QScrollBar:vertical {{ background: transparent; width: 6px;"
            f" margin: 4px 0; }}"
            f"QScrollBar::handle:vertical {{ background: {V2.BORDER_STRONG};"
            f" border-radius: 3px; min-height: 20px; }}"
            f"QScrollBar::handle:vertical:hover {{ background: {accent}; }}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {"
            " height: 0; background: none; }"
        )

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(0, 0, 4, 0)
        c_lay.setSpacing(8)
        c_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._populate(c_lay)

        scroll.setWidget(content)
        lay.addWidget(scroll, 1)

    def _total_count(self):
        cats = self.app.skill_manager.get_categories(self.category) or {}
        return sum(len(v) for v in cats.values())

    def _populate(self, c_lay):
        cats = self.app.skill_manager.get_categories(self.category) or {}
        for sub, ids in sorted(cats.items()):
            # 子分類標題（簡潔、無裝飾）
            sub_lbl = QLabel(sub.upper())
            sub_lbl.setStyleSheet(
                f"color: {V2.TXT_DIM}; font-size: 10px; font-weight: 700;"
                f" letter-spacing: 1px; padding: 4px 2px 2px 2px;"
                f" background: transparent;"
            )
            c_lay.addWidget(sub_lbl)

            for sid in ids:
                skill = self.app.skill_manager.get_skill(sid)
                if not skill:
                    continue
                card = SkillCardV2(None, sid, skill, self.app, self._accent)
                c_lay.addWidget(card)


# ────────────────────────── 頁面主體 ──────────────────────────

class SkillPageV2(QWidget):
    """技能頁 V2 預覽 — Modern Dark Dashboard"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setStyleSheet(f"background: {V2.BG_PAGE};")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(16)

        # ── 頁首：標題 + 副標 + 分段控制 ──
        head = QHBoxLayout()
        head.setSpacing(12)

        title_wrap = QVBoxLayout()
        title_wrap.setSpacing(2)
        title = QLabel("技能倒數")
        title.setStyleSheet(
            f"color: {V2.TXT_HI}; font-size: 20px; font-weight: 700;"
            f" background: transparent;"
        )
        sub = QLabel("管理技能冷卻、快捷鍵與提示")
        sub.setStyleSheet(
            f"color: {V2.TXT_DIM}; font-size: 11px; background: transparent;"
        )
        title_wrap.addWidget(title)
        title_wrap.addWidget(sub)
        head.addLayout(title_wrap)
        head.addStretch()
        head.addWidget(SegmentedBar(self, self.app.toggle_all))
        root.addLayout(head)

        # ── 三欄區 ──
        cols = QHBoxLayout()
        cols.setSpacing(14)
        defs = [
            ("玩家技能", "player", V2.COL_PLAYER),
            ("BOSS 技能", "boss",  V2.COL_BOSS),
            ("道具",     "item",  V2.COL_ITEM),
        ]
        for t, cat, color in defs:
            col = ColumnV2(self, t, cat, color, self.app)
            cols.addWidget(col, 1)
        root.addLayout(cols, 1)
