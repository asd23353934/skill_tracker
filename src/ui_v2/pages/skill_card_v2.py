"""
技能卡片 — V2

單張技能的容器：左=技能圖示+名稱、中=三列控件、右=詳細設定。

與 V1 App 的互動：
- 冷卻 / 熱鍵 / 提前秒數 chip 透過 V2PillButton 提供 `_v2_apply_accent` 入口，
  讓 V1 App._apply_btn_style 經由映射套用 V2 accent，而非覆寫 stylesheet。
- 三 checkbox 直接註冊到 V1 App 的 permanent_vars / loop_vars / alert_enabled_vars。
- Card 實例透過 `app.skill_card_widgets[skill_id]` 登錄，供 refresh_card() 使用。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QCheckBox,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QPolygon

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_pixmap
from src.ui_v2.dialogs.skill_detail_dialog_v2 import SkillDetailDialogV2


# ════════════════════════════════════════════════════════════
# 自繪小按鈕
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
# V2PillButton — chip 樣式按鈕；支援 V1 `_apply_btn_style` 路徑
# ════════════════════════════════════════════════════════════

class V2PillButton(QPushButton):
    """V2 圓角 chip 按鈕，管理自身 accent 樣式。

    V1 App._apply_btn_style 會對按鈕直接覆寫 stylesheet；為了保留 V2 視覺，
    本類別提供 `_v2_apply_accent(v1_bg)`：把 V1 AppTheme 色映射成 V2 accent 後
    重新套用 V2 樣式。App._apply_btn_style 偵測到此方法後會走這條路徑，不再
    直接覆寫 stylesheet。
    """

    _V1_TO_V2: dict[str, str] | None = None

    def __init__(self, text: str = "", w: int = 46, h: int = 22,
                 font_size: int = 11, parent=None):
        super().__init__(text, parent)
        self._accent: str | None = None
        self._font_size = font_size
        self.setFixedSize(w, h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

    def set_accent(self, accent_v2: str | None):
        """以 V2 色直接設定 accent，None 為中性樣式。"""
        self._accent = accent_v2
        self._apply_style()

    def _v2_apply_accent(self, v1_bg_hex: str | None):
        """V1 App._apply_btn_style 的入口：把 V1 bg hex 映射成 V2 accent。"""
        if V2PillButton._V1_TO_V2 is None:
            from src.ui.theme import AppTheme
            V2PillButton._V1_TO_V2 = {
                AppTheme.ACCENT_BLUE.lower():   T.CYAN,
                AppTheme.ACCENT_GREEN.lower():  T.GREEN,
                AppTheme.ACCENT_YELLOW.lower(): T.YELLOW,
                AppTheme.ACCENT_ORANGE.lower(): T.ORANGE,
            }
        accent_v2 = V2PillButton._V1_TO_V2.get((v1_bg_hex or "").lower())
        self.set_accent(accent_v2)

    def _apply_style(self):
        if self._accent:
            bg       = T.alpha(self._accent, 38)
            bg_hover = T.alpha(self._accent, 70)
            fg       = self._accent
            super().setStyleSheet(
                f"QPushButton {{ color: {fg}; background: {bg};"
                f" border: none; border-radius: {T.R_SM}px; padding: 0;"
                f" font-size: {self._font_size}px; font-weight: 700; }}"
                f"QPushButton:hover {{ background: {bg_hover}; }}"
            )
        else:
            super().setStyleSheet(
                f"QPushButton {{ color: {T.TEXT_DIM};"
                f" background: {T.BG_INPUT}; padding: 0;"
                f" border: 1px solid {T.BORDER};"
                f" border-radius: {T.R_SM}px;"
                f" font-size: {self._font_size}px; font-weight: 600; }}"
                f"QPushButton:hover {{ color: {T.TEXT_HI};"
                f" border-color: {T.BORDER_HOVER}; }}"
            )


# ════════════════════════════════════════════════════════════
# InputChip — V2PillButton + 獨立圓角的 ↺ 按鈕
# ════════════════════════════════════════════════════════════

class InputChip(QFrame):
    """值 chip + 重置 chip 的組合。"""

    GAP = 6

    def __init__(self, text: str, accent: str | None = None,
                 reset_tooltip: str = "重置",
                 value_w: int = 46, h: int = 22):
        super().__init__()
        self.setFixedHeight(h)
        self.setStyleSheet("background: transparent;")

        self.value_btn = V2PillButton(text, w=value_w, h=h)
        self.value_btn.set_accent(accent)

        self.reset_btn = _ChipResetBtn(reset_tooltip, h)
        self.reset_btn.sync_accent(accent)

        L = QHBoxLayout(self)
        L.setContentsMargins(0, 0, 0, 0)
        L.setSpacing(self.GAP)
        L.addWidget(self.value_btn)
        L.addWidget(self.reset_btn)

    def set_accent(self, accent: str | None):
        self.value_btn.set_accent(accent)
        self.reset_btn.sync_accent(accent)


class _ChipResetBtn(QPushButton):
    """獨立圓角的 ↺ 重置按鈕"""
    def __init__(self, tooltip: str, h: int):
        super().__init__()
        self._accent: str | None = None
        self._hover = False
        self.setFixedSize(h, h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        self._apply_bg()

    def sync_accent(self, accent: str | None):
        self._accent = accent
        self._apply_bg()
        self.update()

    def _apply_bg(self):
        if self._accent:
            bg       = T.alpha(self._accent, 38)
            bg_hover = T.alpha(self._accent, 70)
            border   = "border: none;"
        else:
            bg       = T.BG_INPUT
            bg_hover = T.BG_HOVER
            border   = f"border: 1px solid {T.BORDER};"
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
        col = T.RED if self._hover else (self._accent or T.TEXT_DIM)
        pix = lucide_pixmap("rotate-ccw", col, 12, stroke=2.0)
        p = QPainter(self)
        x = (self.width() - 12) // 2
        y = (self.height() - 12) // 2
        p.drawPixmap(x, y, pix)
        p.end()


def _pill_btn(text: str, accent: str | None = None, w: int = 40, h: int = 22,
              font_size: int = 11) -> "V2PillButton":
    """相容舊 API：回傳已套用 accent 的 V2PillButton"""
    btn = V2PillButton(text, w=w, h=h, font_size=font_size)
    btn.set_accent(accent)
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
# SkillIconBadge — 顯示技能 QPixmap 的 accent 徽章
# ════════════════════════════════════════════════════════════

class SkillIconBadge(QFrame):
    """accent 色塊 + 中央技能圖片（QPixmap）"""
    def __init__(self, pixmap, accent: str, size: int = 44, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setStyleSheet(
            f"QFrame {{ background: {T.alpha(accent, 38)};"
            f" border-radius: {T.R_MD}px; }}"
        )
        lbl = QLabel(self)
        lbl.setGeometry(0, 0, size, size)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("background: transparent; border: none;")
        if pixmap is not None and not pixmap.isNull():
            icon = min(size - 8, pixmap.width())
            lbl.setPixmap(pixmap.scaled(
                icon, icon,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))


# ════════════════════════════════════════════════════════════
# SkillCardV2 — 單張技能卡
# ════════════════════════════════════════════════════════════

_REGISTRY_KEYS = (
    "cooldown_buttons", "hotkey_buttons", "alert_seconds_buttons",
    "permanent_vars", "loop_vars", "alert_enabled_vars",
)


class SkillCardV2(QFrame):
    HEIGHT = 116

    def __init__(self, parent, app, skill_id: str, skill_meta: dict,
                 accent: str):
        super().__init__(parent)
        self.app        = app
        self.skill_id   = skill_id
        self._meta      = skill_meta
        self._accent    = accent

        self.setObjectName("skill_card")
        self.setFixedHeight(self.HEIGHT)
        self.setStyleSheet(
            f"QFrame#skill_card {{ background: {T.BG_ELEVATED};"
            f" border: none; border-radius: {T.R_MD}px; }}"
            f"QFrame#skill_card:hover {{ background: {T.BG_HOVER}; }}"
        )
        self._build()
        self._register_widgets()
        self.refresh()

    # --------------------------------------------------
    # 建構
    # --------------------------------------------------
    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(T.S_MD, T.S_SM, T.S_SM, T.S_SM)
        outer.setSpacing(T.S_MD)

        # 左：icon + 名稱
        ICON_SIZE = 44
        NAME_W    = 64
        LEFT_W    = ICON_SIZE + T.S_SM + NAME_W

        pixmap = None
        sm = getattr(self.app, "skill_manager", None)
        if sm is not None and hasattr(sm, "qpixmaps_card"):
            pixmap = sm.qpixmaps_card.get(self.skill_id)

        left = QHBoxLayout()
        left.setSpacing(T.S_SM)
        left.setContentsMargins(0, 0, 0, 0)
        left.addWidget(SkillIconBadge(pixmap, self._accent, ICON_SIZE))
        name_lbl = T.make_label(
            self._meta.get("name", ""), T.FONT_BODY, color_override=T.TEXT_HI
        )
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

        # 中：3 列
        center = QVBoxLayout()
        center.setSpacing(8)
        center.setContentsMargins(0, 0, 0, 0)
        center.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # row 1：冷卻秒數 chip
        r1 = QHBoxLayout()
        r1.setSpacing(0); r1.setContentsMargins(0, 0, 0, 0)
        self._cd_chip = InputChip("", reset_tooltip="重置秒數", value_w=46)
        self._cd_chip.value_btn.clicked.connect(self._on_edit_cooldown)
        self._cd_chip.reset_btn.clicked.connect(self._on_reset_cooldown)
        r1.addWidget(self._cd_chip)
        r1.addStretch()
        center.addLayout(r1)

        # row 2：熱鍵 chip
        r2 = QHBoxLayout()
        r2.setSpacing(0); r2.setContentsMargins(0, 0, 0, 0)
        self._hk_chip = InputChip("", reset_tooltip="清除按鍵", value_w=46)
        self._hk_chip.value_btn.clicked.connect(self._on_begin_hotkey)
        self._hk_chip.reset_btn.clicked.connect(self._on_reset_hotkey)
        r2.addWidget(self._hk_chip)
        r2.addStretch()
        center.addLayout(r2)

        # row 3：常 循 提 + 提前秒數
        r3 = QHBoxLayout()
        r3.setSpacing(10); r3.setContentsMargins(0, 0, 0, 0)
        self._cb_perm  = _accent_check("常", T.YELLOW, "常駐")
        self._cb_loop  = _accent_check("循", T.GREEN,  "循環")
        self._cb_alert = _accent_check("提", T.ORANGE, "提前提示")
        self._cb_perm.stateChanged.connect(
            lambda: self.app.update_skill_setting_exclusive(
                self.skill_id, "permanent", self._cb_perm))
        self._cb_loop.stateChanged.connect(
            lambda: self.app.update_skill_setting_exclusive(
                self.skill_id, "loop", self._cb_loop))
        self._cb_alert.stateChanged.connect(
            lambda: self.app.update_alert_setting(self.skill_id, self._cb_alert))

        self._alert_pill = V2PillButton("", w=30, h=20, font_size=10)
        self._alert_pill.clicked.connect(self._on_edit_alert_seconds)

        r3.addWidget(self._cb_perm)
        r3.addWidget(self._cb_loop)
        alert_group = QHBoxLayout()
        alert_group.setSpacing(4)
        alert_group.setContentsMargins(0, 0, 0, 0)
        alert_group.addWidget(self._cb_alert)
        alert_group.addWidget(self._alert_pill)
        r3.addLayout(alert_group)
        r3.addStretch()
        center.addLayout(r3)

        outer.addLayout(center, 1)

        # 右：設定
        more = MoreBtn()
        more.clicked.connect(self._on_open_detail)
        right_wrap = QWidget()
        rv = QVBoxLayout(right_wrap)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.addStretch()
        rv.addWidget(more)
        rv.addStretch()
        outer.addWidget(right_wrap)

    # --------------------------------------------------
    # 註冊 / 清理
    # --------------------------------------------------
    def _register_widgets(self):
        app = self.app
        sid = self.skill_id
        for key in _REGISTRY_KEYS:
            d = getattr(app, key, None)
            if d is None:
                return
        app.cooldown_buttons[sid]      = self._cd_chip.value_btn
        app.hotkey_buttons[sid]        = self._hk_chip.value_btn
        app.alert_seconds_buttons[sid] = self._alert_pill
        app.permanent_vars[sid]        = self._cb_perm
        app.loop_vars[sid]             = self._cb_loop
        app.alert_enabled_vars[sid]    = self._cb_alert

        cards = getattr(app, "skill_card_widgets", None)
        if cards is None:
            app.skill_card_widgets = {}
            cards = app.skill_card_widgets
        cards[sid] = self

    @classmethod
    def unregister_from_app(cls, app, skill_id: str):
        """rebuild 前呼叫：清除指定 skill_id 在 App dict 內的殘留引用。"""
        for key in _REGISTRY_KEYS:
            d = getattr(app, key, None)
            if isinstance(d, dict):
                d.pop(skill_id, None)
        cards = getattr(app, "skill_card_widgets", None)
        if isinstance(cards, dict):
            cards.pop(skill_id, None)

    # --------------------------------------------------
    # 狀態讀取 + refresh
    # --------------------------------------------------
    def refresh(self):
        """重讀 App state 並更新控件文字 / 樣式。"""
        app = self.app
        sid = self.skill_id

        # 冷卻 chip
        meta = app.skill_manager.get_skill(sid) or self._meta
        cooldown = meta.get("cooldown", 0)
        original = app.get_original_cooldown(sid)
        is_cd_modified = bool(original and cooldown != original)
        self._cd_chip.value_btn.setText(f"{cooldown}秒")
        self._cd_chip.set_accent(T.CYAN if is_cd_modified else None)

        # 熱鍵 chip
        hotkey = meta.get("hotkey", "") or ""
        has_hotkey = bool(hotkey)
        self._hk_chip.value_btn.setText(hotkey if has_hotkey else "未設")
        self._hk_chip.set_accent(T.YELLOW if has_hotkey else None)

        # 三 checkbox
        self._set_checked_silent(self._cb_perm,
                                 bool(app.skill_permanent.get(sid, False)))
        self._set_checked_silent(self._cb_loop,
                                 bool(app.skill_loop.get(sid, False)))
        self._set_checked_silent(self._cb_alert,
                                 bool(app.skill_alert_enabled.get(sid, False)))

        # 提前秒數 pill
        override = app.skill_alert_seconds_overrides.get(sid)
        if override is not None:
            self._alert_pill.setText(f"{override}s")
            self._alert_pill.set_accent(T.ORANGE)
        else:
            self._alert_pill.setText(f"{app.alert_before_seconds}s")
            self._alert_pill.set_accent(None)

    @staticmethod
    def _set_checked_silent(cb: QCheckBox, value: bool):
        cb.blockSignals(True)
        try:
            cb.setChecked(value)
        finally:
            cb.blockSignals(False)

    # --------------------------------------------------
    # Callbacks（全部委派 App 方法）
    # --------------------------------------------------
    def _on_edit_cooldown(self):
        self.app.edit_cooldown(self.skill_id)

    def _on_reset_cooldown(self):
        self.app.reset_cooldown(self.skill_id)

    def _on_begin_hotkey(self):
        name = self._meta.get("name", self.skill_id)
        self.app.hotkey_manager.begin_capture(self.skill_id, name)

    def _on_reset_hotkey(self):
        self.app.reset_hotkey(self.skill_id)

    def _on_edit_alert_seconds(self):
        self.app.edit_alert_seconds(self.skill_id)

    def _on_open_detail(self):
        # V1 show_skill_detail 會開 V1 dialog；V2 卡片直接使用 V2 dialog。
        SkillDetailDialogV2(self.window(), self.app, self.skill_id).exec()
