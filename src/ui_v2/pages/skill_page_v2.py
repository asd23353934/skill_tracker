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
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
)
from PySide6.QtCore import Qt

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.pages.skill_column_v2 import SkillColumnV2
from src.ui_v2.pages.skill_card_v2 import SkillCardV2


_CATEGORY_DEFS = [
    ("player", "玩家技能", "swords",        T.BLUE),
    ("boss",   "BOSS 技能", "skull",         T.RED),
    ("item",   "道具",     "flask-conical", T.GREEN),
]


class SkillPageV2(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self._columns: list[SkillColumnV2] = []
        self._registered_ids: set[str] = set()
        self._content_layout: QHBoxLayout | None = None
        self._built = False
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
        bar.addStretch()
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
    # rebuild / clear
    # --------------------------------------------------
    def rebuild(self):
        """rebuild 三欄內容。safe to call 多次。"""
        if self.app is None or not hasattr(self.app, "skill_manager"):
            return
        self._clear_layout()
        self._populate_layout()
        self._built = True

    def _clear_layout(self):
        # 清除 App dict 內的殘留 widget 註冊
        for sid in list(self._registered_ids):
            SkillCardV2.unregister_from_app(self.app, sid)
        self._registered_ids.clear()

        # 清除 column widget
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
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
