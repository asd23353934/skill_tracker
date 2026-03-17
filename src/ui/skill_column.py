"""
技能欄位元件 — PySide6 版本
RPG 風格 Banner 標題 + 卡片垂直排列（QScrollArea）
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QScrollArea,
)
from PySide6.QtCore import Qt
from src.ui.theme import AppTheme
from src.ui.skill_card import SkillCard


class SkillColumn(QWidget):
    """PyDracula 風格技能欄位 — 極簡 Banner + 可捲動卡片列表"""

    def __init__(self, parent, title, category, app,
                 banner_color=None, border_color=None):
        """初始化技能欄位

        Args:
            parent:       父元件
            title:        欄位標題
            category:     技能分類 ('player' | 'boss' | 'item')
            app:          App 主應用實例
            banner_color: 已棄用，保留相容性（傳 None 即可）
            border_color: 欄位底線強調色（玩家→藍、BOSS→紅、道具→綠）
        """
        super().__init__(parent)
        self.app         = app
        self.category    = category
        self.skill_items = {}

        if border_color is None:
            border_color = AppTheme.GOLD_MUTED

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ===== 欄位標題 (極簡 Banner：透明背景 + 彩色底線) =====
        banner = QFrame()
        banner.setObjectName("column_banner")
        banner.setFixedHeight(34)
        banner.setStyleSheet(
            f"QFrame#column_banner {{"
            f" background-color: transparent;"
            f" border: none;"
            f" border-bottom: 2px solid {border_color}; }}"
        )
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(10, 2, 10, 4)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            f"color: {border_color}; font-size: 13px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        banner_layout.addWidget(title_lbl)
        layout.addWidget(banner)

        # ===== 可捲動卡片區域 =====
        # 外層容器：持有圓角邊框，內縮 3px 讓 scroll 不覆蓋圓角
        scroll_wrapper = QFrame()
        scroll_wrapper.setObjectName("scroll_wrapper")
        scroll_wrapper.setStyleSheet(
            f"QFrame#scroll_wrapper {{"
            f" border: 1px solid {AppTheme.BORDER_GOLD_SUBTLE};"
            f" border-radius: {AppTheme.CORNER_MD}px;"
            f" background-color: {AppTheme.BG_DEEP}; }}"
        )
        wrapper_layout = QVBoxLayout(scroll_wrapper)
        wrapper_layout.setContentsMargins(3, 3, 3, 3)
        wrapper_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(
            # ── QScrollArea 無邊框（邊框由外層容器負責）──
            f"QScrollArea {{"
            f" border: none;"
            f" background-color: {AppTheme.BG_DEEP};"
            f" border-radius: 0px; }}"
            # ── 垂直捲軸深色主題 ──
            f"QScrollBar:vertical {{"
            f" background: {AppTheme.BG_DEEP}; width: 8px;"
            f" margin: 0; border: none; border-radius: 4px; }}"
            f"QScrollBar::handle:vertical {{"
            f" background: #2d4a72;"
            f" border-radius: 4px; min-height: 24px; }}"
            f"QScrollBar::handle:vertical:hover {{"
            f" background: {AppTheme.GOLD_PRIMARY}; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{"
            f" height: 0; background: none; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{"
            f" background: none; }}"
        )

        self._content = QWidget()
        self._content.setStyleSheet(f"background-color: {AppTheme.BG_DEEP};")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(5, 8, 5, 8)
        self._content_layout.setSpacing(4)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._content)
        wrapper_layout.addWidget(scroll)
        layout.addWidget(scroll_wrapper)

        self._populate(category)

    def _populate(self, category):
        """填充技能分組"""
        categories = self.app.skill_manager.get_categories(category)
        if not categories:
            return

        for subcategory, skill_ids in sorted(categories.items()):
            self._create_group(subcategory, skill_ids)

    def _create_group(self, subcategory, skill_ids):
        """建立技能分組 — RPG 分隔線 + 卡片垂直排列

        Args:
            subcategory: 子分類名稱
            skill_ids:   技能 ID 列表
        """
        # 分組標題（RPG 分隔線風格）
        header = QFrame()
        header.setObjectName("group_header")
        header.setFixedHeight(22)
        header.setStyleSheet(
            f"QFrame#group_header {{"
            f" background-color: {AppTheme.BG_SECONDARY};"
            f" border-left: 3px solid {AppTheme.GOLD_PRIMARY};"
            f" border-top: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-bottom: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-right: none;"
            f" border-radius: 2px; }}"
        )
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 2, 8, 2)

        h_lbl = QLabel(subcategory)
        h_lbl.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT}; font-size: 11px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        h_layout.addWidget(h_lbl)
        self._content_layout.addWidget(header)

        # 卡片垂直排列
        for skill_id in skill_ids:
            skill = self.app.skill_manager.get_skill(skill_id)
            if skill:
                card = SkillCard(self._content, skill_id, skill, self.app)
                self._content_layout.addWidget(card)
                self.skill_items[skill_id] = card
