"""
技能欄位 — V2

一個分類（玩家 / BOSS / 道具）的容器：標題 + 子分類分組 + 卡片滾動。
由 SkillPageV2 從 app.skill_manager 讀取資料後建立。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QScrollArea,
)
from PySide6.QtCore import Qt

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import Card, IconBadge, StatusChip
from src.ui_v2.pages.skill_card_v2 import SkillCardV2


class SkillColumnV2(Card):
    """sections: list[tuple[str, list[str]]]
    每項為 `(subcategory_name, [skill_id, ...])`；skill_id 依 config.json
    首次出現順序排列，SkillPageV2 負責保證這個順序。
    """

    def __init__(self, parent, app, title: str, glyph: str, accent: str,
                 sections: list[tuple[str, list[str]]]):
        super().__init__(parent)
        self.app   = app
        self.cards: dict[str, SkillCardV2] = {}

        L = self.layout()
        L.setSpacing(T.S_MD)

        total = sum(len(ids) for _, ids in sections)
        self._all_ids = [sid for _, ids in sections for sid in ids]
        self._total = total
        self._accent = accent
        hk_total = self._count_hotkeys_set(self._all_ids)

        # 欄位標題（chip 顯示「已設按鍵 / 總數」）
        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(IconBadge(glyph, accent, 28))
        head.addWidget(T.make_label(title, T.FONT_CARD_TITLE))
        head.addStretch()
        self._status_chip = StatusChip(f"{hk_total}/{total}", accent)
        head.addWidget(self._status_chip)
        L.addLayout(head)

        # 滾動內容（永遠關閉橫向捲軸；只允許垂直捲動）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("background: transparent;")

        inner = QWidget()
        v = QVBoxLayout(inner)
        v.setContentsMargins(0, 0, T.S_XS, 0)
        v.setSpacing(T.S_SM)

        if not sections:
            v.addStretch()
        else:
            for sub_name, skill_ids in sections:
                v.addWidget(self._sub_header(sub_name, len(skill_ids), accent))
                for sid in skill_ids:
                    meta = self.app.skill_manager.get_skill(sid)
                    if not meta:
                        continue
                    card = SkillCardV2(inner, self.app, sid, meta, accent)
                    v.addWidget(card)
                    self.cards[sid] = card
                v.addSpacing(T.S_XS)
            v.addStretch()

        scroll.setWidget(inner)
        L.addWidget(scroll, 1)

    def _sub_header(self, name: str, count: int, accent: str) -> QWidget:
        """子分類小標題：name + 總數 + 橫線"""
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

    def refresh_status(self):
        """重算 hk_count 並更新 chip 文字（被 SkillPageV2.refresh_status_counts 呼叫）"""
        chip = getattr(self, "_status_chip", None)
        if chip is None:
            return
        hk_total = self._count_hotkeys_set(self._all_ids)
        chip.setText(f"{hk_total}/{self._total}")

    def _count_hotkeys_set(self, skill_ids) -> int:
        """計算 skill_ids 內已設熱鍵的數量（不算空字串）

        讀真正 source-of-truth：skill_manager.get_skill(sid)["hotkey"]。
        SkillService._hotkeys 在 hotkey_manager 綁定後不會同步（見
        src/domain/services.py:219 註解），所以不能讀 svc.get_hotkey。
        """
        sm = getattr(self.app, "skill_manager", None)
        if sm is None:
            return 0
        n = 0
        for sid in skill_ids:
            meta = sm.get_skill(sid)
            if meta and meta.get("hotkey"):
                n += 1
        return n
