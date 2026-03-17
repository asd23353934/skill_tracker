"""
RPG 風格技能卡片元件 — PySide6 版本
三欄佈局：左(圖示+名稱) | 中(兩行控件) | 右(設定按鈕)
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QCheckBox, QWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from src.ui.theme import AppTheme


class SkillCard(QFrame):
    """RPG 風格技能卡片 — 三欄佈局"""

    CARD_HEIGHT = 66

    def __init__(self, parent, skill_id, skill, app):
        """初始化技能卡片

        Args:
            parent:   父元件
            skill_id: 技能 ID
            skill:    技能資料字典
            app:      App 主應用實例
        """
        super().__init__(parent)
        self.skill_id = skill_id
        self.skill    = skill
        self.app      = app

        self.setObjectName("skill_card")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFixedHeight(self.CARD_HEIGHT)
        self.setStyleSheet(
            f"QFrame#skill_card {{"
            f" background-color: {AppTheme.BG_DEEP};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 4px; }}"
            f"QFrame#skill_card:hover {{"
            f" background-color: {AppTheme.BG_CARD};"
            f" border: 1px solid {AppTheme.GOLD_PRIMARY}; }}"
        )
        self._build_ui()

    def _build_ui(self):
        """建構卡片 UI — 左中右三欄"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 4, 6)
        layout.setSpacing(2)

        # ===== 左欄：圖示框 =====
        icon_frame = QFrame()
        icon_frame.setFixedSize(46, 46)
        icon_frame.setObjectName("card_icon")
        icon_frame.setStyleSheet(
            f"QFrame#card_icon {{"
            f" background-color: {AppTheme.BG_DEEP};"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: 3px; }}"
        )
        icon_inner = QVBoxLayout(icon_frame)
        icon_inner.setContentsMargins(3, 3, 3, 3)
        icon_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 技能圖片（36×36 卡片尺寸）
        qpixmap = self.app.skill_manager.qpixmaps_card.get(self.skill_id)
        if qpixmap and not qpixmap.isNull():
            img_lbl = QLabel()
            img_lbl.setPixmap(qpixmap)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_lbl.setStyleSheet("background: transparent; border: none;")
            icon_inner.addWidget(img_lbl)

        layout.addWidget(icon_frame)
        layout.addSpacing(4)

        # 名稱標籤（固定寬度，靠左對齊）
        name_lbl = QLabel(self.skill.get("name", ""))
        name_lbl.setFixedWidth(58)
        name_lbl.setWordWrap(True)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        name_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 12px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(name_lbl)
        layout.addSpacing(2)

        # ===== 中欄：兩行控件（垂直置中）=====
        center = QWidget()
        center.setStyleSheet("background: transparent;")
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(2)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # --- 第一行：冷卻秒數 ↺ | 快捷鍵 ↺ ---
        row1 = QWidget()
        row1.setStyleSheet("background: transparent;")
        r1 = QHBoxLayout(row1)
        r1.setContentsMargins(0, 0, 0, 0)
        r1.setSpacing(1)

        original_cooldown = self.app.get_original_cooldown(self.skill_id)
        is_modified = bool(
            original_cooldown and self.skill.get("cooldown") != original_cooldown
        )

        self.cooldown_btn = QPushButton(f"{self.skill.get('cooldown', 0)}秒")
        self.cooldown_btn.setFixedSize(42, 20)
        self.cooldown_btn.clicked.connect(lambda: self.app.edit_cooldown(self.skill_id))
        self.app._apply_btn_style(
            self.cooldown_btn,
            bg    = AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_TERTIARY,
            fg    = AppTheme.TEXT_PRIMARY,
            hover = "#2563eb"            if is_modified else AppTheme.BG_SECONDARY,
        )
        r1.addWidget(self.cooldown_btn)
        self.app.cooldown_buttons[self.skill_id] = self.cooldown_btn

        reset_cd = QPushButton("↺")
        reset_cd.setFixedSize(26, 20)
        reset_cd.setToolTip("重置冷卻秒數")
        reset_cd.clicked.connect(lambda: self.app.reset_cooldown(self.skill_id))
        reset_cd.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none;"
            f" color: {AppTheme.TEXT_SECONDARY}; font-size: 13px; }}"
            f"QPushButton:hover {{ color: {AppTheme.ACCENT_RED};"
            f" background: {AppTheme.BG_TERTIARY}; border-radius: 3px; }}"
        )
        r1.addWidget(reset_cd)
        r1.addSpacing(2)

        hotkey_text = self.skill.get("hotkey", "") or "未設定"
        has_hotkey  = bool(self.skill.get("hotkey"))

        self.hotkey_btn = QPushButton(hotkey_text)
        self.hotkey_btn.setFixedSize(46, 20)
        self.hotkey_btn.clicked.connect(
            lambda: self.app.hotkey_manager.begin_capture(
                self.skill_id, self.skill["name"]
            )
        )
        self.app._apply_btn_style(
            self.hotkey_btn,
            bg    = AppTheme.ACCENT_YELLOW      if has_hotkey else AppTheme.BG_TERTIARY,
            fg    = "#000000"                   if has_hotkey else AppTheme.TEXT_MUTED,
            hover = AppTheme.ACCENT_YELLOW_HOVER if has_hotkey else AppTheme.BG_SECONDARY,
        )
        r1.addWidget(self.hotkey_btn)
        self.app.hotkey_buttons[self.skill_id] = self.hotkey_btn

        reset_hk = QPushButton("↺")
        reset_hk.setFixedSize(26, 20)
        reset_hk.setToolTip("清除快捷鍵")
        reset_hk.clicked.connect(lambda: self.app.reset_hotkey(self.skill_id))
        reset_hk.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none;"
            f" color: {AppTheme.TEXT_SECONDARY}; font-size: 13px; }}"
            f"QPushButton:hover {{ color: {AppTheme.ACCENT_RED};"
            f" background: {AppTheme.BG_TERTIARY}; border-radius: 3px; }}"
        )
        r1.addWidget(reset_hk)
        r1.addStretch()

        center_layout.addWidget(row1)

        # --- 第二行：常駐 | 循環 | 提醒 | 秒數 ---
        row2 = QWidget()
        row2.setStyleSheet("background: transparent;")
        r2 = QHBoxLayout(row2)
        r2.setContentsMargins(0, 0, 0, 0)
        r2.setSpacing(2)

        # checkbox 共用樣式
        _CB_STYLE = (
            f"QCheckBox {{ color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
            f" background: transparent; spacing: 3px; }}"
            f"QCheckBox::indicator {{ width: 13px; height: 13px; border-radius: 3px;"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; background: {AppTheme.BG_TERTIARY}; }}"
            f"QCheckBox::indicator:hover {{ border-color: {AppTheme.GOLD_PRIMARY}; }}"
        )

        # 常駐 Checkbox
        permanent_cb = QCheckBox("常駐")
        permanent_cb.setChecked(self.app.skill_permanent.get(self.skill_id, False))
        permanent_cb.setStyleSheet(
            _CB_STYLE +
            f"QCheckBox::indicator:checked {{"
            f" background: {AppTheme.ACCENT_YELLOW}; border-color: {AppTheme.ACCENT_YELLOW}; }}"
        )
        permanent_cb.stateChanged.connect(
            lambda: self.app.update_skill_setting_exclusive(
                self.skill_id, "permanent", permanent_cb
            )
        )
        r2.addWidget(permanent_cb)
        self.app.permanent_vars[self.skill_id] = permanent_cb

        # 循環 Checkbox
        loop_cb = QCheckBox("循環")
        loop_cb.setChecked(self.app.skill_loop.get(self.skill_id, False))
        loop_cb.setStyleSheet(
            _CB_STYLE +
            f"QCheckBox::indicator:checked {{"
            f" background: {AppTheme.ACCENT_GREEN}; border-color: {AppTheme.ACCENT_GREEN}; }}"
        )
        loop_cb.stateChanged.connect(
            lambda: self.app.update_skill_setting_exclusive(
                self.skill_id, "loop", loop_cb
            )
        )
        r2.addWidget(loop_cb)
        self.app.loop_vars[self.skill_id] = loop_cb

        # 提醒 Checkbox
        alert_cb = QCheckBox("提醒")
        alert_cb.setChecked(self.app.skill_alert_enabled.get(self.skill_id, False))
        alert_cb.setStyleSheet(
            _CB_STYLE +
            f"QCheckBox::indicator:checked {{"
            f" background: {AppTheme.ACCENT_ORANGE}; border-color: {AppTheme.ACCENT_ORANGE}; }}"
        )
        alert_cb.stateChanged.connect(
            lambda: self.app.update_alert_setting(self.skill_id, alert_cb)
        )
        r2.addWidget(alert_cb)
        self.app.alert_enabled_vars[self.skill_id] = alert_cb

        # 提前提示秒數按鈕
        alert_seconds = self.app.skill_alert_seconds_overrides.get(self.skill_id, None)
        if alert_seconds is not None:
            alert_text  = f"{alert_seconds}s"
            alert_bg    = AppTheme.ACCENT_ORANGE
            alert_hover = "#e07a2a"
        else:
            alert_text  = f"{self.app.alert_before_seconds}s"
            alert_bg    = AppTheme.BG_TERTIARY
            alert_hover = AppTheme.BG_SECONDARY

        self.alert_seconds_btn = QPushButton(alert_text)
        self.alert_seconds_btn.setFixedSize(30, 18)
        self.alert_seconds_btn.clicked.connect(
            lambda: self.app.edit_alert_seconds(self.skill_id)
        )
        self.app._apply_btn_style(
            self.alert_seconds_btn, bg=alert_bg, hover=alert_hover
        )
        r2.addWidget(self.alert_seconds_btn)
        self.app.alert_seconds_buttons[self.skill_id] = self.alert_seconds_btn

        r2.addStretch()
        center_layout.addWidget(row2)

        layout.addWidget(center)

        # ===== 右欄：設定按鈕（⋮）=====
        settings_btn = QPushButton("⋮")
        settings_btn.setFixedSize(24, 44)
        settings_btn.setToolTip("技能詳細設定")
        settings_btn.clicked.connect(
            lambda: self.app.show_skill_detail(self.skill_id)
        )
        settings_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none;"
            f" color: {AppTheme.TEXT_SECONDARY}; font-size: 16px; }}"
            f"QPushButton:hover {{"
            f" background: {AppTheme.BG_TERTIARY}; color: {AppTheme.GOLD_PRIMARY};"
            f" border-radius: 4px; }}"
        )
        layout.addWidget(settings_btn)
