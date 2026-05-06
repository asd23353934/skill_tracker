"""
技能倒數頁面 — V2

三欄：玩家 | BOSS | 道具
依 docs/DESIGN_V2.md

綁定契約
═══════════════════════════════════════════════════════════
建構參數：SkillPageV2(parent, app)

讀取：
- 元資料（唯讀，來自 config.json）：app.skill_manager.get_skills() / get_items()
- 狀態（當前 profile）：app.skill_permanent / skill_loop / skill_alert_enabled /
  skill_alert_seconds_overrides
- 冷卻 / 熱鍵：app.skill_manager.get_skill(id) 的 'cooldown' / 'hotkey'
- 圖片：app.skill_manager.qpixmaps_card.get(skill_id)

操作（於 SkillCardV2 內綁定 App 方法）：
- 冷卻 chip  → app.edit_cooldown / reset_cooldown
- 熱鍵 chip  → app.hotkey_manager.begin_capture / app.reset_hotkey
- 常 / 循    → app.update_skill_setting_exclusive
- 提        → app.update_alert_setting
- 提秒 pill  → app.edit_alert_seconds
- ⋮        → V2 SkillDetailDialogV2

頁首 chip（快速切換）→ app.toggle_all('permanent'|'loop'|'alert')

刷新時機：
- showEvent: 首次 rebuild 全頁
- profile 切換: profile_changed handler → 全頁 rebuild
- 單張卡片狀態變更: 只呼叫 refresh_card(skill_id)

執行緒安全：
- hotkey 觸發在 daemon thread；App / hotkey_manager 會透過 app.after(0, ...)
  排回主執行緒，V2 Card.refresh() 不應直接從 daemon thread 呼叫。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QScrollArea,
)
from PySide6.QtCore import Qt

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import ArrowComboBox
from src.ui_v2.pages.skill_column_v2 import SkillColumnV2
from src.ui_v2.pages.skill_card_v2 import SkillCardV2


_CATEGORY_DEFS = [
    ("player", "玩家技能", "swords",        T.BLUE),
    ("boss",   "BOSS 技能", "skull",         T.RED),
    ("item",   "道具",     "flask-conical", T.GREEN),
]


def _clear_layout_widgets(layout):
    """清空 QLayout 內所有 widget（detach + deleteLater）"""
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.setParent(None)
            w.deleteLater()


class SkillPageV2(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self._columns: list[SkillColumnV2] = []
        self._registered_ids: set[str] = set()
        self._content_layout: QHBoxLayout | None = None
        self._built = False
        # 自註冊：AppCoreMixin.switch_profile 走 app.skill_page_v2.rebuild()
        if app is not None:
            app.skill_page_v2 = self
        self._build_shell()

    # --------------------------------------------------
    # 頁面骨架（只建一次；資料區隨 rebuild 重填）
    # --------------------------------------------------
    def _build_shell(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        bar = QHBoxLayout()
        bar.setSpacing(T.S_SM)
        bar.addWidget(T.make_label("技能倒數", T.FONT_SECTION))
        bar.addSpacing(T.S_MD)
        bar.addWidget(self._build_profile_selector())
        bar.addStretch()
        bar.addWidget(self._build_hotkey_bar(), 0)
        bar.addSpacing(T.S_SM)
        bar.addWidget(T.make_label("快速切換", T.FONT_LABEL))
        for label, color, key in (
            ("常駐", T.YELLOW, "permanent"),
            ("循環", T.GREEN,  "loop"),
            ("提醒", T.ORANGE, "alert"),
        ):
            chip = self._toggle_chip(label, color)
            chip.clicked.connect(lambda _=False, k=key: self._on_toggle_all(k))
            bar.addWidget(chip)
        root.addLayout(bar)

        self._content_layout = QHBoxLayout()
        self._content_layout.setSpacing(T.S_MD)
        root.addLayout(self._content_layout, 1)

    def _build_profile_selector(self) -> QWidget:
        """ProfileSelector — combo + 管理小按鈕，水平包裝為一個 QWidget"""
        combo = ArrowComboBox()
        combo.setFixedHeight(30)
        combo.setMinimumWidth(140)
        combo.setStyleSheet(
            f"QComboBox {{ background: {T.BG_SURFACE}; color: {T.TEXT};"
            f" border: 1px solid {T.BORDER_SOFT};"
            f" border-radius: {T.R_SM}px; padding: 0 10px;"
            f" font-size: 12px; }}"
            f"QComboBox:hover {{ border-color: {T.BORDER_HOVER}; }}"
            f"QComboBox::drop-down {{ border: none; width: 16px; }}"
            + T.combo_popup_qss()
        )
        self._profile_combo = combo
        if self.app is not None and hasattr(self.app, "config_manager"):
            cm = self.app.config_manager
            combo.blockSignals(True)
            combo.addItems(cm.list_profiles())
            current = cm.get_current_profile()
            if current:
                combo.setCurrentText(current)
            combo.blockSignals(False)
            combo.currentTextChanged.connect(
                lambda name: self.app.switch_profile(name)
            )

        # ── 管理按鈕（齒輪 icon → ProfileManagerDialogV2） ──
        from src.ui_v2.lucide import lucide_pixmap
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize as _QSize
        manage_btn = QPushButton()
        manage_btn.setIcon(QIcon(lucide_pixmap("settings", T.TEXT_DIM, 14, stroke=1.6)))
        manage_btn.setIconSize(_QSize(14, 14))
        manage_btn.setFixedSize(28, 28)
        manage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        manage_btn.setToolTip("配置管理")
        manage_btn.setStyleSheet(
            f"QPushButton {{ background: transparent;"
            f" border: 1px solid {T.BORDER_SOFT};"
            f" border-radius: {T.R_SM}px; padding: 0; }}"
            f"QPushButton:hover {{ background: {T.BG_HOVER};"
            f" border-color: {T.BORDER_HOVER}; }}"
        )
        manage_btn.clicked.connect(self._open_profile_manager)

        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(T.S_XS)
        h.addWidget(combo)
        h.addWidget(manage_btn)
        return wrap

    def refresh_profile_selector(self):
        """CRUD 後重整 dropdown（不觸發 switch_profile）"""
        combo = getattr(self, "_profile_combo", None)
        if combo is None or self.app is None or not hasattr(self.app, "config_manager"):
            return
        cm = self.app.config_manager
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(cm.list_profiles())
        current = cm.get_current_profile()
        if current:
            combo.setCurrentText(current)
        combo.blockSignals(False)

    def _open_profile_manager(self):
        if self.app is None:
            return
        from src.ui_v2.dialogs import ProfileManagerDialogV2
        ProfileManagerDialogV2(self.window(), self.app).exec()

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

    # --------------------------------------------------
    # 頁首右側：當前已設按鍵 橫軸
    # --------------------------------------------------
    def _build_hotkey_bar(self) -> QWidget:
        """頁首右側「當前已設按鍵」橫軸容器（QScrollArea + chip flow）"""
        wrap = QFrame()
        wrap.setObjectName("hk_bar")
        wrap.setStyleSheet(
            f"QFrame#hk_bar {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER_SOFT};"
            f" border-radius: {T.R_SM}px; }}"
        )
        wrap.setFixedHeight(30)
        wrap.setMaximumWidth(480)

        outer = QHBoxLayout(wrap)
        outer.setContentsMargins(6, 0, 6, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        self._hotkey_bar_layout = QHBoxLayout(inner)
        self._hotkey_bar_layout.setContentsMargins(0, 0, 0, 0)
        self._hotkey_bar_layout.setSpacing(T.S_XS)
        self._hotkey_bar_layout.addWidget(self._hotkey_bar_placeholder())
        self._hotkey_bar_layout.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return wrap

    def _hotkey_bar_placeholder(self) -> QLabel:
        lbl = T.make_label("尚無設置按鍵", T.FONT_CAPTION)
        lbl.setContentsMargins(8, 0, 8, 0)
        return lbl

    def _make_hotkey_chip(self, sid: str, name: str, key: str,
                          accent: str) -> QFrame:
        """單一 chip：[技能 icon] [key]，accent 染色，技能名給 tooltip"""
        chip = QFrame()
        chip.setStyleSheet(
            f"QFrame {{ background: {T.alpha(accent, 50)};"
            f" border-radius: {T.CHIP_H // 2}px; }}"
        )
        chip.setFixedHeight(22)
        chip.setToolTip(f"{name} · {key}")

        h = QHBoxLayout(chip)
        h.setContentsMargins(4, 0, 8, 0)
        h.setSpacing(4)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(16, 16)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        sm = self.app.skill_manager
        cache = (getattr(sm, "qpixmaps_card", None)
                 or getattr(sm, "qpixmaps_medium", None))
        pixmap = cache.get(sid) if cache else None
        if pixmap is not None and not pixmap.isNull():
            icon_lbl.setPixmap(pixmap.scaled(
                16, 16,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        h.addWidget(icon_lbl)

        key_lbl = QLabel(key)
        key_lbl.setStyleSheet(
            f"color: {accent}; background: transparent;"
            f" font-size: 11px; font-weight: 700;"
        )
        h.addWidget(key_lbl)
        return chip

    def _iter_set_hotkeys(self):
        """yield (sid, name, hotkey, accent)，依三欄與子分類序"""
        sm = self.app.skill_manager
        for category_key, _, _, accent in _CATEGORY_DEFS:
            for ids in (sm.get_categories(category_key) or {}).values():
                for sid in ids:
                    meta = sm.get_skill(sid)
                    if not meta:
                        continue
                    hotkey = meta.get("hotkey", "") or ""
                    if not hotkey:
                        continue
                    yield sid, meta.get("name", sid), hotkey, accent

    def _refresh_hotkey_bar(self):
        """重建頁首橫軸所有 chip"""
        layout = getattr(self, "_hotkey_bar_layout", None)
        if layout is None or self.app is None:
            return
        if getattr(self.app, "skill_manager", None) is None:
            return

        _clear_layout_widgets(layout)
        has_any = False
        for sid, name, hotkey, accent in self._iter_set_hotkeys():
            layout.addWidget(self._make_hotkey_chip(sid, name, hotkey, accent))
            has_any = True
        if not has_any:
            layout.addWidget(self._hotkey_bar_placeholder())
        layout.addStretch()

    # --------------------------------------------------
    # rebuild / clear
    # --------------------------------------------------
    def rebuild(self):
        """rebuild 三欄內容。safe to call 多次。"""
        if self.app is None or not hasattr(self.app, "skill_manager"):
            return
        self._clear_layout()
        self._populate_layout()
        self._refresh_hotkey_bar()
        self._built = True

    def refresh_status_counts(self):
        """重算所有欄位的「已設按鍵 / 總數」chip 文字 + 頁首橫軸（hotkey 變動後呼叫）"""
        for col in self._columns:
            col.refresh_status()
        self._refresh_hotkey_bar()

    def _clear_layout(self):
        # 清除 App dict 內的殘留 widget 註冊
        for sid in list(self._registered_ids):
            SkillCardV2.unregister_from_app(self.app, sid)
        self._registered_ids.clear()
        _clear_layout_widgets(self._content_layout)
        self._columns.clear()

    def _populate_layout(self):
        for category_key, title, glyph, accent in _CATEGORY_DEFS:
            sections = self._collect_sections(category_key)
            col = SkillColumnV2(self, self.app, title, glyph, accent, sections)
            self._content_layout.addWidget(col, 1)
            self._columns.append(col)
            self._registered_ids.update(col.cards.keys())

    def _collect_sections(self, category_key: str) -> list[tuple[str, list[str]]]:
        """依 config.json 首次出現順序回傳 [(subcategory, [skill_id, ...])]"""
        categories = self.app.skill_manager.get_categories(category_key) or {}
        # dict 在 Python 3.7+ 保留插入順序；SkillLoader 按 config.json 順序建立
        return [(sub, list(ids)) for sub, ids in categories.items()]

    # --------------------------------------------------
    # 局部 refresh
    # --------------------------------------------------
    def refresh_card(self, skill_id: str):
        """單卡 refresh，不 rebuild。"""
        cards = getattr(self.app, "skill_card_widgets", None)
        if not isinstance(cards, dict):
            return
        card = cards.get(skill_id)
        if card is not None:
            card.refresh()

    # --------------------------------------------------
    # 事件
    # --------------------------------------------------
    def showEvent(self, e):  # noqa: N802
        super().showEvent(e)
        if not self._built:
            self.rebuild()

    def _on_toggle_all(self, key: str):
        if self.app is not None and hasattr(self.app, "toggle_all"):
            self.app.toggle_all(key)
