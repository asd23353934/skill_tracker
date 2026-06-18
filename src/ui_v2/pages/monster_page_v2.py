"""
怪物重生頁面 — V2

橫向捲動大卡牌；每張卡含完整重生 / 聲音 / 循環設定。
依 docs/DESIGN_V2.md。

接線到 V1 既有 MonsterService + WindowManager + HotkeyManager（皆透過
AppCoreMixin 暴露）。卡片所有交互直接呼叫 app.xxx 方法，狀態與 V1 共用。

══════════════════════════════════════════════════════════════
建構參數
══════════════════════════════════════════════════════════════
    MonsterPageV2(parent, app)

  app 必須提供（皆來自 AppCoreMixin）：
    - get_all_monsters() / monster_service.get(id)
    - edit_respawn_time / reset_respawn_time
    - reset_monster_hotkey / edit_monster_alert_before
    - update_monster_loop / update_monster_permanent
    - update_monster_alert_sound / update_monster_end_sound
    - hotkey_manager.begin_capture(id, name) / hotkey_manager._monster_card
    - sound_manager.list_sounds() / get_sound_label() / migrate_sound_filename()
    - monster_respawn_buttons / monster_alert_before_buttons (widget 登錄 dict)

  app 可選：
    - app.monster_page slot —— page 會自註冊到 app.monster_page = self，
      讓 reset_monster_hotkey / hotkey_manager 衝突清除路徑找得到 V2 卡片。

不在本頁職責：
    - 倒數視窗本身（由 WindowManager 管理）
    - 全域聲音開關 / 提示開關（由 settings 對話框處理）
    - 新增 / 刪除怪物（V1 也沒有此 UI；config.json 為 curated boss 清單）
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap

from src.infrastructure.helpers import resource_path
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import ArrowComboBox
from src.ui_v2.lucide import lucide_pixmap
from src.ui_v2.pages.skill_card_v2 import (
    InputChip, _accent_check, _pill_btn,
)


# ════════════════════════════════════════════════════════════
# Icon 載入：優先讀 images/{filename}（與 V1 共用），失敗則 lucide skull
# ════════════════════════════════════════════════════════════

_ICON_CACHE: dict[str, QPixmap | None] = {}


def _load_monster_pixmap(icon_filename: str, size: int) -> QPixmap | None:
    """讀真實怪物 PNG（Qt 原生載入），cache keyed by (filename, size)"""
    if not icon_filename:
        return None
    key = f"{icon_filename}@{size}"
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]
    pm = QPixmap(resource_path(f"images/{icon_filename}"))
    if pm.isNull():
        _ICON_CACHE[key] = None
        return None
    pm = pm.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    _ICON_CACHE[key] = pm
    return pm


# ════════════════════════════════════════════════════════════
# IconArea — 大尺寸 icon 顯示框
# ════════════════════════════════════════════════════════════

class _IconArea(QFrame):
    """大型怪物 icon 框（96px 內容 + 邊框）"""
    def __init__(self, icon_filename: str, accent: str, size: int = 96):
        super().__init__()
        self._accent = accent
        self._size   = size
        self._pix    = _load_monster_pixmap(icon_filename, int(size * 0.7))
        self.setFixedSize(size, size)
        self.setStyleSheet(
            f"QFrame {{ background: {T.alpha(accent, 28)};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
        )

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        p = QPainter(self)
        if self._pix is not None:
            x = (self._size - self._pix.width())  // 2
            y = (self._size - self._pix.height()) // 2
            p.drawPixmap(x, y, self._pix)
        else:
            icon_size = int(self._size * 0.55)
            pix = lucide_pixmap("skull", self._accent, icon_size, stroke=1.6)
            x = (self._size - icon_size) // 2
            y = (self._size - icon_size) // 2
            p.drawPixmap(x, y, pix)
        p.end()


# ════════════════════════════════════════════════════════════
# 小工具
# ════════════════════════════════════════════════════════════

def _label_with_icon(icon: str, text: str, color: str = None) -> QWidget:
    color = color or T.TEXT_DIM
    wrap = QWidget()
    h = QHBoxLayout(wrap)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(6)

    icon_lbl = QLabel()
    icon_lbl.setFixedSize(14, 14)
    icon_lbl.setPixmap(lucide_pixmap(icon, color, 14, stroke=1.6))
    icon_lbl.setStyleSheet("background: transparent;")
    h.addWidget(icon_lbl)

    txt = QLabel(text)
    txt.setStyleSheet(
        f"color: {color}; font-size: 11px; font-weight: 600;"
        f" background: transparent;"
    )
    h.addWidget(txt)
    h.addStretch()
    return wrap


def _section_divider() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background: {T.BORDER_SOFT}; border: none;")
    return line


def _build_sound_combo(sound_manager, current_filename: str) -> tuple[ArrowComboBox, dict]:
    """建立聲音下拉，回 (combo, label→filename map)；首項 — 無 — 對應空字串。"""
    NO_SOUND = "— 無 —"
    label_map = {NO_SOUND: ""}
    if sound_manager is not None:
        for fn in sound_manager.list_sounds():
            label_map[sound_manager.get_sound_label(fn)] = fn

    combo = ArrowComboBox()
    combo.addItems(list(label_map.keys()))
    # 設定當前選項
    current_label = NO_SOUND
    for label, fn in label_map.items():
        if fn == current_filename:
            current_label = label
            break
    combo.setCurrentText(current_label)
    combo.setFixedHeight(26)
    combo.setStyleSheet(
        T.combo_qss(bg=T.BG_INPUT, border=T.BORDER, padding="0 8px", font_size=11)
    )
    return combo, label_map


# ════════════════════════════════════════════════════════════
# MonsterCard — 單張怪物卡牌（接線 V1 manager）
# ════════════════════════════════════════════════════════════

class MonsterCard(QFrame):
    CARD_W = 260
    CARD_H = 440

    def __init__(self, parent, app, monster_id: str):
        super().__init__(parent)
        self.app = app
        self.monster_id = monster_id

        self._hk_chip: InputChip | None = None
        self._end_label_map: dict = {}
        self._alert_label_map: dict = {}

        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setObjectName("monster_card")
        self.setStyleSheet(
            f"QFrame#monster_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
            f"QFrame#monster_card:hover {{ border-color: {T.BORDER_HOVER}; }}"
        )
        self._build()

    @property
    def monster(self) -> dict:
        """每次讀都從 service 取最新；避免快照失同步。"""
        return self.app.monster_service.get(self.monster_id) or {}

    def _build(self):
        m = self.monster
        respawn      = m.get("respawn_time", 0)
        hotkey       = m.get("hotkey", "")
        alert_before = m.get("alert_before", 0)
        loop         = m.get("loop", False)
        permanent    = m.get("permanent", False)
        end_sound    = m.get("sound", "")
        alert_sound  = m.get("alert_sound", "")
        icon_file    = m.get("icon", "")

        L = QVBoxLayout(self)
        L.setContentsMargins(T.S_LG, T.S_MD, T.S_LG, T.S_MD)
        L.setSpacing(T.S_SM)

        # ── 頂部：名稱 ──
        top = QHBoxLayout()
        top.setSpacing(T.S_SM)
        name_lbl = T.make_label(m.get("name", ""), T.FONT_CARD_TITLE,
                                color_override=T.TEXT_HI)
        top.addWidget(name_lbl)
        top.addStretch()
        L.addLayout(top)

        # ── icon 大框 ──
        icon_wrap = QHBoxLayout()
        icon_wrap.setContentsMargins(0, 0, 0, 0)
        icon_wrap.addStretch()
        icon_wrap.addWidget(_IconArea(icon_file, T.RED, 96))
        icon_wrap.addStretch()
        L.addLayout(icon_wrap)

        L.addSpacing(T.S_XS)

        # ── 重生時間 ──
        L.addWidget(_label_with_icon("timer", "重生時間"))
        rs_chip = InputChip(f"{respawn}s", T.CYAN, "重置秒數", value_w=60)
        rs_chip.value_btn.clicked.connect(lambda: self.app.edit_respawn_time(self.monster_id))
        rs_chip.reset_btn.clicked.connect(lambda: self.app.reset_respawn_time(self.monster_id))
        rs = QHBoxLayout()
        rs.setSpacing(0); rs.setContentsMargins(0, 0, 0, 0)
        rs.addWidget(rs_chip)
        rs.addStretch()
        L.addLayout(rs)
        # 註冊到 app dict（供 V1 update helper 共用）
        self.app.monster_respawn_buttons[self.monster_id] = rs_chip.value_btn

        # ── 快捷鍵 ──
        L.addWidget(_label_with_icon("keyboard", "快捷鍵"))
        hk_text  = hotkey or "未設"
        hk_color = T.YELLOW if hotkey else None
        hk_chip  = InputChip(hk_text, hk_color, "清除按鍵", value_w=60)
        hk_chip.value_btn.clicked.connect(self._begin_hotkey_capture)
        hk_chip.reset_btn.clicked.connect(lambda: self.app.reset_monster_hotkey(self.monster_id))
        self._hk_chip = hk_chip
        hk = QHBoxLayout()
        hk.setSpacing(0); hk.setContentsMargins(0, 0, 0, 0)
        hk.addWidget(hk_chip)
        hk.addStretch()
        L.addLayout(hk)

        L.addWidget(_section_divider())

        # ── 提前提示 ──
        L.addWidget(_label_with_icon("bell-ring", "提前提示", T.ORANGE))
        alert_pill = _pill_btn(f"{alert_before}s", T.ORANGE, w=44, h=22)
        alert_pill.clicked.connect(lambda: self.app.edit_monster_alert_before(self.monster_id))
        self.app.monster_alert_before_buttons[self.monster_id] = alert_pill

        sound_mgr = getattr(self.app, "sound_manager", None)
        alert_combo, self._alert_label_map = _build_sound_combo(sound_mgr, alert_sound)
        alert_combo.currentTextChanged.connect(self._on_alert_sound_changed)

        alert_row = QHBoxLayout()
        alert_row.setSpacing(T.S_SM); alert_row.setContentsMargins(0, 0, 0, 0)
        alert_row.addWidget(alert_pill)
        alert_row.addWidget(alert_combo, 1)
        L.addLayout(alert_row)

        # ── 結束聲音 ──
        L.addWidget(_label_with_icon("music", "結束聲音"))
        end_combo, self._end_label_map = _build_sound_combo(sound_mgr, end_sound)
        end_combo.currentTextChanged.connect(self._on_end_sound_changed)

        end_row = QHBoxLayout()
        end_row.setSpacing(T.S_SM); end_row.setContentsMargins(0, 0, 0, 0)
        end_row.addWidget(end_combo, 1)
        L.addLayout(end_row)

        L.addWidget(_section_divider())

        # ── 循環 / 常駐 ──
        cb_row = QHBoxLayout()
        cb_row.setSpacing(T.S_LG); cb_row.setContentsMargins(0, 0, 0, 0)
        loop_cb = _accent_check("循環", T.GREEN)
        loop_cb.setChecked(loop)
        loop_cb.stateChanged.connect(
            lambda state: self.app.update_monster_loop(self.monster_id, bool(state))
        )
        perm_cb = _accent_check("常駐", T.YELLOW)
        perm_cb.setChecked(permanent)
        perm_cb.stateChanged.connect(
            lambda state: self.app.update_monster_permanent(self.monster_id, bool(state))
        )
        cb_row.addWidget(loop_cb)
        cb_row.addWidget(perm_cb)
        cb_row.addStretch()
        L.addLayout(cb_row)

        L.addStretch()

    # ── 對外 API ──
    def set_hotkey_text(self, text: str, has_hotkey: bool):
        """HotkeyManager callback 完成綁定後呼叫；沿用 V2 chip accent 系統。"""
        if self._hk_chip is None:
            return
        display = text if has_hotkey else "未設"
        self._hk_chip.value_btn.setText(display)
        if hasattr(self._hk_chip.value_btn, "_v2_apply_accent"):
            self._hk_chip.value_btn._v2_apply_accent(T.YELLOW if has_hotkey else None)

    # ── callbacks ──
    def _begin_hotkey_capture(self):
        self.app.hotkey_manager._monster_card = self
        self.app.hotkey_manager.begin_capture(self.monster_id, self.monster.get("name", ""))

    def _on_end_sound_changed(self, label: str):
        filename = self._end_label_map.get(label, "")
        self.app.update_monster_end_sound(self.monster_id, filename)

    def _on_alert_sound_changed(self, label: str):
        filename = self._alert_label_map.get(label, "")
        self.app.update_monster_alert_sound(self.monster_id, filename)


# ════════════════════════════════════════════════════════════
# MonsterPageV2
# ════════════════════════════════════════════════════════════

class MonsterPageV2(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.cards: dict = {}        # monster_id → MonsterCard
        self._loaded = False
        self._cards_layout: QHBoxLayout | None = None
        # 自註冊：HotkeyManager 衝突清除走 app.monster_page.cards 找卡片
        if app is not None:
            app.monster_page = self
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        # ── 工具列（保留 title + hint，移除新增按鈕）──
        bar = QHBoxLayout()
        bar.setSpacing(T.S_SM)
        bar.addWidget(T.make_label("怪物重生", T.FONT_SECTION))

        hint = T.make_label("按下快捷鍵開始計時（從 0 數到設定時間）",
                            T.FONT_CAPTION)
        bar.addSpacing(T.S_SM)
        bar.addWidget(hint)
        bar.addStretch()
        root.addLayout(bar)

        # ── 橫向捲動卡牌區 ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        h = QHBoxLayout(inner)
        h.setContentsMargins(T.S_SM, T.S_SM, T.S_SM, T.S_SM)
        h.setSpacing(T.S_MD)
        h.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self._cards_layout = h

        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

    def showEvent(self, e):  # noqa: N802
        super().showEvent(e)
        if self._loaded or self.app is None or self._cards_layout is None:
            return
        for monster in self.app.get_all_monsters():
            mid = monster["id"]
            card = MonsterCard(self._cards_layout.parentWidget(), self.app, mid)
            self._cards_layout.addWidget(card)
            self.cards[mid] = card
        self._loaded = True
