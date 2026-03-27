"""
怪物重生頁面 — PySide6 版本
橫向捲動大卡牌，按鍵觸發浮動計時視窗（從 0 數到設定時間）
卡牌包含：圖示、名稱、重生時間、快捷鍵、提前/結束聲音、循環/常駐設定
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton, QCheckBox, QComboBox, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

from src.ui.theme import AppTheme
from src.infrastructure.helpers import resource_path


def _load_monster_icon(icon_filename: str, size: tuple) -> QPixmap | None:
    """載入怪物圖示並回傳 QPixmap

    Args:
        icon_filename: 圖示檔名（位於 images/ 目錄）
        size:          (w, h)

    Returns:
        QPixmap 或 None（載入失敗）
    """
    if not icon_filename:
        return None
    try:
        from PIL import Image
        path = resource_path(f"images/{icon_filename}")
        img  = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        data = img.tobytes("raw", "RGBA")
        qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg)
    except Exception:
        return None


def _build_sound_combo(sound_manager, current_filename: str) -> tuple[QComboBox, dict]:
    """建立聲音下拉選單

    Args:
        sound_manager:    SoundManager 實例
        current_filename: 目前已選聲音檔名

    Returns:
        (QComboBox, label_to_filename_map)
    """
    NO_SOUND = "— 無 —"
    label_map = {NO_SOUND: ""}
    if sound_manager:
        for fn in sound_manager.list_sounds():
            label = sound_manager.get_sound_label(fn)
            label_map[label] = fn

    combo = QComboBox()
    combo.setStyleSheet(
        f"QComboBox {{ background: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_PRIMARY};"
        f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: 3px;"
        f" padding: 1px 4px; font-size: 10px; }}"
        f"QComboBox::drop-down {{ border: none; width: 14px; }}"
        f"QComboBox QAbstractItemView {{ background: {AppTheme.BG_SECONDARY};"
        f" color: {AppTheme.TEXT_PRIMARY}; selection-background-color: {AppTheme.GOLD_DARK}; }}"
    )
    for label in label_map:
        combo.addItem(label)

    # 設定目前值
    current_label = NO_SOUND
    if current_filename:
        for lbl, fn in label_map.items():
            if fn == current_filename:
                current_label = lbl
                break
    combo.setCurrentText(current_label)

    return combo, label_map


class _MonsterCard(QFrame):
    """怪物卡牌 — 大型垂直卡牌，含完整設定"""

    CARD_W = 280
    CARD_H = 480

    def __init__(self, parent, monster: dict, app):
        """初始化怪物卡片

        Args:
            parent:  父元件
            monster: 怪物資料字典
            app:     App 主應用實例
        """
        super().__init__(parent)
        self.monster    = monster
        self.app        = app
        self.monster_id = monster["id"]

        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setStyleSheet(
            f"QFrame {{"
            f" background-color: {AppTheme.BG_CARD};"
            f" border: 2px solid {AppTheme.BORDER_GOLD_SUBTLE};"
            f" border-radius: {AppTheme.CORNER_MD}px; }}"
        )
        self._build_ui()

    def _build_ui(self):
        """建構卡牌 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── 名稱 ──
        name_lbl = QLabel(self.monster.get("name", ""))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 14px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(name_lbl)

        # ── 圖示 ──
        icon_w = QWidget()
        icon_w.setStyleSheet(f"background: transparent;")
        icon_row = QHBoxLayout(icon_w)
        icon_row.setContentsMargins(0, 0, 0, 0)
        icon_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(100, 100)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background: {AppTheme.BG_DEEP};"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: 8px;"
        )
        qpixmap = _load_monster_icon(self.monster.get("icon", ""), (80, 80))
        if qpixmap and not qpixmap.isNull():
            icon_lbl.setPixmap(qpixmap)
        else:
            icon_lbl.setText("👾")
            icon_lbl.setStyleSheet(
                f"font-size: 40px; background: {AppTheme.BG_DEEP};"
                f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: 8px; padding: 10px;"
            )
        icon_row.addWidget(icon_lbl)
        layout.addWidget(icon_w)

        # ── 重生時間 ──
        layout.addWidget(self._sep())

        respawn  = self.monster.get("respawn_time", 0)
        original = self.app.config_manager.get_original_respawn_time(self.monster_id)
        is_modified = original is not None and respawn != original

        rs_w, rs_row = self._hrow()
        self.respawn_btn = QPushButton(f"{respawn}秒")
        self.respawn_btn.clicked.connect(lambda: self.app.edit_respawn_time(self.monster_id))
        self.respawn_btn.setFixedHeight(28)
        self.respawn_btn.setStyleSheet(
            f"QPushButton {{"
            f" background-color: {AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_TERTIARY};"
            f" color: {AppTheme.TEXT_PRIMARY}; border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 4px; padding: 2px 8px; font-size: 11px; }}"
            f"QPushButton:hover {{ border-color: {AppTheme.GOLD_PRIMARY}; }}"
        )
        self.app.monster_respawn_buttons[self.monster_id] = self.respawn_btn
        rs_row.addWidget(self.respawn_btn)

        reset_rs = self._small_reset_btn("重置重生時間")
        reset_rs.clicked.connect(lambda: self.app.reset_respawn_time(self.monster_id))
        rs_row.addWidget(reset_rs)
        rs_row.addStretch()
        layout.addWidget(rs_w)

        # ── 快捷鍵 ──
        hk_w, hk_row = self._hrow()
        hk_lbl = QLabel("快捷鍵:")
        hk_lbl.setStyleSheet(f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
                              f" background: transparent; border: none;")
        hk_row.addWidget(hk_lbl)

        hotkey_text = self.monster.get("hotkey", "") or "未設定"
        has_hotkey  = bool(self.monster.get("hotkey"))
        self.hotkey_btn = QPushButton(hotkey_text)
        self.hotkey_btn.clicked.connect(self._begin_hotkey_capture)
        self.hotkey_btn.setFixedHeight(24)
        self.app._apply_btn_style(
            self.hotkey_btn,
            bg    = AppTheme.ACCENT_YELLOW       if has_hotkey else AppTheme.BG_TERTIARY,
            fg    = "#000000"                    if has_hotkey else AppTheme.TEXT_MUTED,
            hover = AppTheme.ACCENT_YELLOW_HOVER if has_hotkey else AppTheme.BG_SECONDARY,
        )
        hk_row.addWidget(self.hotkey_btn)

        reset_hk = self._small_reset_btn("清除快捷鍵")
        reset_hk.clicked.connect(lambda: self.app.reset_monster_hotkey(self.monster_id))
        hk_row.addWidget(reset_hk)
        hk_row.addStretch()
        layout.addWidget(hk_w)

        # ── 提前提示 ──
        layout.addWidget(self._sep())
        layout.addWidget(self._section_label("提前提示"))

        alert_w, alert_row = self._hrow()
        before_lbl = QLabel("提前秒數:")
        before_lbl.setStyleSheet(f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
                                  f" background: transparent; border: none;")
        alert_row.addWidget(before_lbl)

        alert_before = self.monster.get("alert_before", 10)
        self.alert_before_btn = QPushButton(f"{alert_before}秒")
        self.alert_before_btn.setFixedHeight(24)
        self.alert_before_btn.clicked.connect(
            lambda: self.app.edit_monster_alert_before(self.monster_id)
        )
        self.app._apply_btn_style(
            self.alert_before_btn,
            bg    = AppTheme.ACCENT_ORANGE if alert_before > 0 else AppTheme.BG_TERTIARY,
            hover = "#e07a2a"              if alert_before > 0 else AppTheme.BG_SECONDARY,
        )
        self.app.monster_alert_before_buttons[self.monster_id] = self.alert_before_btn
        alert_row.addWidget(self.alert_before_btn)
        alert_row.addStretch()
        layout.addWidget(alert_w)

        # 提前聲音
        asound_w, asound_row = self._hrow()
        asound_lbl = QLabel("提前聲音:")
        asound_lbl.setStyleSheet(f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
                                  f" background: transparent; border: none;")
        asound_row.addWidget(asound_lbl)

        self.alert_sound_combo, self._alert_sound_map = _build_sound_combo(
            self.app.sound_manager, self.monster.get("alert_sound", "")
        )
        self.alert_sound_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.alert_sound_combo.currentTextChanged.connect(self._on_alert_sound_changed)
        asound_row.addWidget(self.alert_sound_combo)
        layout.addWidget(asound_w)

        # ── 結束聲音 ──
        layout.addWidget(self._sep())
        layout.addWidget(self._section_label("結束聲音"))

        esound_w, esound_row = self._hrow()
        esound_lbl = QLabel("結束聲音:")
        esound_lbl.setStyleSheet(f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
                                  f" background: transparent; border: none;")
        esound_row.addWidget(esound_lbl)

        self.end_sound_combo, self._end_sound_map = _build_sound_combo(
            self.app.sound_manager, self.monster.get("sound", "")
        )
        self.end_sound_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.end_sound_combo.currentTextChanged.connect(self._on_end_sound_changed)
        esound_row.addWidget(self.end_sound_combo)
        layout.addWidget(esound_w)

        # ── 循環 / 常駐 ──
        layout.addWidget(self._sep())

        check_w, check_row = self._hrow()
        check_row.setSpacing(12)

        _CB_STYLE = (
            f"QCheckBox {{ color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
            f" background: transparent; spacing: 4px; }}"
            f"QCheckBox::indicator {{ width: 14px; height: 14px; border-radius: 3px;"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; background: {AppTheme.BG_TERTIARY}; }}"
            f"QCheckBox::indicator:hover {{ border-color: {AppTheme.GOLD_PRIMARY}; }}"
        )

        loop_cb = QCheckBox("循環")
        loop_cb.setChecked(self.monster.get("loop", True))
        loop_cb.setStyleSheet(
            _CB_STYLE +
            f"QCheckBox::indicator:checked {{"
            f" background: {AppTheme.ACCENT_GREEN}; border-color: {AppTheme.ACCENT_GREEN}; }}"
        )
        loop_cb.stateChanged.connect(
            lambda state: self.app.update_monster_loop(
                self.monster_id, state == Qt.CheckState.Checked.value
            )
        )
        check_row.addWidget(loop_cb)

        perm_cb = QCheckBox("常駐")
        perm_cb.setChecked(self.monster.get("permanent", False))
        perm_cb.setStyleSheet(
            _CB_STYLE +
            f"QCheckBox::indicator:checked {{"
            f" background: {AppTheme.ACCENT_YELLOW}; border-color: {AppTheme.ACCENT_YELLOW}; }}"
        )
        perm_cb.stateChanged.connect(
            lambda state: self.app.update_monster_permanent(
                self.monster_id, state == Qt.CheckState.Checked.value
            )
        )
        check_row.addWidget(perm_cb)
        check_row.addStretch()
        layout.addWidget(check_w)

        layout.addStretch()

    # ── 輔助 ──

    def _hrow(self) -> tuple:
        """建立透明橫向容器，回傳 (QWidget, QHBoxLayout)"""
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        return row, lay

    def _sep(self) -> QFrame:
        """建立分隔線"""
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {AppTheme.GOLD_MUTED}; border: none;")
        return sep

    def _section_label(self, text: str) -> QLabel:
        """建立區段標籤"""
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 11px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        return lbl

    def _small_reset_btn(self, tooltip: str) -> QPushButton:
        """建立小型重置按鈕"""
        btn = QPushButton("↺")
        btn.setFixedSize(24, 24)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none;"
            f" color: {AppTheme.TEXT_SECONDARY}; font-size: 13px; }}"
            f"QPushButton:hover {{ color: {AppTheme.ACCENT_RED};"
            f" background: {AppTheme.BG_TERTIARY}; border-radius: 3px; }}"
        )
        return btn

    # ── 事件 ──

    def _begin_hotkey_capture(self):
        """開始捕捉快捷鍵"""
        self.app.hotkey_manager._monster_card = self
        self.app.hotkey_manager.begin_capture(self.monster_id, self.monster["name"])

    def _on_alert_sound_changed(self, label: str):
        """提前聲音下拉變更"""
        filename = self._alert_sound_map.get(label, "")
        self.app.update_monster_alert_sound(self.monster_id, filename)

    def _on_end_sound_changed(self, label: str):
        """結束聲音下拉變更"""
        filename = self._end_sound_map.get(label, "")
        self.app.update_monster_end_sound(self.monster_id, filename)

    # ── 公開 API ──

    def update_hotkey_display(self, key_str: str, has_hotkey: bool):
        """更新快捷鍵按鈕顯示

        Args:
            key_str:   快捷鍵字串（空字串表示未設定）
            has_hotkey: 是否有快捷鍵
        """
        self.hotkey_btn.setText(key_str if key_str else "未設定")
        self.app._apply_btn_style(
            self.hotkey_btn,
            bg    = AppTheme.ACCENT_YELLOW       if has_hotkey else AppTheme.BG_TERTIARY,
            fg    = "#000000"                    if has_hotkey else AppTheme.TEXT_MUTED,
            hover = AppTheme.ACCENT_YELLOW_HOVER if has_hotkey else AppTheme.BG_SECONDARY,
        )


class MonsterPage(QWidget):
    """怪物重生頁面 — 橫向捲動卡牌（置中）"""

    def __init__(self, parent, app):
        """初始化怪物頁

        Args:
            parent: 父元件
            app:    App 主應用實例
        """
        super().__init__(parent)
        self.app = app
        self.cards: dict = {}
        self._build_ui()

    def _build_ui(self):
        """建構頁面 UI"""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── 頁首列 ──
        hdr = QFrame()
        hdr.setObjectName("monster_page_bar")
        hdr.setStyleSheet(
            f"QFrame#monster_page_bar {{"
            f" background: {AppTheme.BG_SECONDARY};"
            f" border-bottom: 1px solid {AppTheme.GOLD_MUTED}; }}"
        )
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(12, 6, 12, 6)
        hdr_lay.setSpacing(8)

        title_lbl = QLabel("👾 怪物重生")
        title_lbl.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT}; font-size: 14px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        hdr_lay.addWidget(title_lbl)

        hint_lbl = QLabel("按下快捷鍵開始計時（從 0 數到設定時間）")
        hint_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 11px;"
            f" background: transparent; border: none;"
        )
        hdr_lay.addWidget(hint_lbl)
        hdr_lay.addStretch()
        outer.addWidget(hdr)

        # 橫向捲動區域（卡牌置中）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        card_container = QWidget()
        card_container.setStyleSheet("background: transparent;")
        card_layout = QHBoxLayout(card_container)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(12)
        # 置中：少量怪物時卡牌水平置中，大量時靠左展開
        card_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self._card_layout = card_layout
        self._card_container = card_container
        scroll.setWidget(card_container)
        outer.addWidget(scroll)

        self._load_monsters()

    def _load_monsters(self):
        """從 config 載入怪物資料並建立卡牌"""
        monsters = self.app.config_manager.config.get("monsters", [])
        for monster in monsters:
            card = _MonsterCard(self._card_container, monster, self.app)
            self._card_layout.addWidget(card)
            self.cards[monster["id"]] = card
