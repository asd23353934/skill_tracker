"""
怪物重生頁面 — V2（純 UI 殼，使用假資料）
橫向捲動大卡牌；每張卡含完整重生/聲音/循環設定
依 docs/DESIGN_V2.md

══════════════════════════════════════════════════════════════
綁定契約
══════════════════════════════════════════════════════════════
建構參數：
    MonsterPageV2(parent, app)

讀取：
    monsters: app.config_manager.get("monsters", [])
        每筆：{ id, name, icon, respawn_time, hotkey, alert_before,
                alert_sound?, end_sound?, loop, permanent }
    原始重生秒: app.config_manager.get_original_respawn_time(monster_id)

操作：
    [新增怪物]   → 對話框輸入 → append monsters → save
    [更多 ⋯]    → MonsterDetailDialogV2（圖示選擇、刪除、進階）
    [重生秒數]   → InputChip 編輯 → 寫回 monster["respawn_time"] → save
    [快捷鍵]     → InputChip → app.hotkey_manager.begin_capture(...)
                  ；按下後寫回 monster["hotkey"] + 重綁監聽
    [提前秒數]   → 寫回 alert_before → save
    [提前/結束聲音 combo] → 寫回 alert_sound / end_sound → save
    [循環/常駐 checkbox]  → 寫回 loop/permanent → save
                            permanent=True 時呼叫
                            app.window_manager.create_permanent_monster_window(id)
                            False 時關閉對應視窗

寫回：
    config_manager.save() — monsters 是全域可變區（在 config.json，不在 profile）

執行緒安全：
    hotkey 觸發 trigger_monster 來自 daemon thread，
    UI 顯示更新由 window_manager 自行 dispatch，本頁不參與

不在本頁職責：
    - 倒數視窗本身（由 WindowManager.create_*_monster_window 管理）
    - 全域聲音開關 / 提示開關（由 settings 對話框處理）
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import IconBadge, ArrowComboBox
from src.ui_v2.lucide import lucide_pixmap, lucide_icon
from src.ui_v2.pages.skill_page_v2 import (
    InputChip, MoreBtn, _accent_check, _pill_btn,
)


# ════════════════════════════════════════════════════════════
# 假資料：(名稱, lucide icon, 重生秒, 快捷鍵, 提前秒, 提前聲音, 結束聲音, loop, perm)
# ════════════════════════════════════════════════════════════
DEMO_MONSTERS = [
    ("月妙",     "skull",    120, "F1", 10, "鈴聲 A", "鈴聲 B", True,  False),
    ("巨大蜘蛛", "skull",     90, "F2", 15, "鈴聲 B", "—",      True,  False),
    ("石頭怪",   "skull",     60, "",    5, "—",      "—",      False, True),
    ("骷髏戰士", "skull",    180, "F3", 20, "鈴聲 A", "鈴聲 C", True,  False),
    ("飛行龍",   "skull",    300, "F4", 30, "鈴聲 C", "鈴聲 C", True,  False),
]


# ════════════════════════════════════════════════════════════
# IconArea — 大尺寸 icon 顯示框
# ════════════════════════════════════════════════════════════

class _IconArea(QFrame):
    """大型怪物 icon 框（96px 內容 + 邊框）"""
    def __init__(self, glyph: str, accent: str, size: int = 96):
        super().__init__()
        self._glyph  = glyph
        self._accent = accent
        self._size   = size
        self.setFixedSize(size, size)
        self.setStyleSheet(
            f"QFrame {{ background: {T.alpha(accent, 28)};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
        )

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        icon_size = int(self._size * 0.55)
        pix = lucide_pixmap(self._glyph, self._accent, icon_size, stroke=1.6)
        p = QPainter(self)
        x = (self._size - icon_size) // 2
        y = (self._size - icon_size) // 2
        p.drawPixmap(x, y, pix)
        p.end()


# ════════════════════════════════════════════════════════════
# 小工具
# ════════════════════════════════════════════════════════════

def _label_with_icon(icon: str, text: str, color: str = None) -> QWidget:
    """icon + 文字小標籤"""
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


def _sound_combo(items: list, current: str = "") -> ArrowComboBox:
    combo = ArrowComboBox()
    combo.addItems(items)
    if current and current in items:
        combo.setCurrentText(current)
    combo.setFixedHeight(26)
    combo.setStyleSheet(
        f"QComboBox {{ background: {T.BG_INPUT}; color: {T.TEXT};"
        f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
        f" padding: 0 8px; font-size: 11px; }}"
        f"QComboBox:hover {{ border-color: {T.BORDER_HOVER}; }}"
        f"QComboBox::drop-down {{ border: none; width: 16px; }}"
    )
    return combo


def _section_divider() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background: {T.BORDER_SOFT}; border: none;")
    return line


# ════════════════════════════════════════════════════════════
# MonsterCard — 單張怪物卡牌
# ════════════════════════════════════════════════════════════

class MonsterCard(QFrame):
    CARD_W = 260
    CARD_H = 440

    def __init__(self, parent, name: str, icon_name: str, respawn: int,
                 hotkey: str, alert_before: int,
                 alert_sound: str, end_sound: str,
                 loop: bool, permanent: bool):
        super().__init__(parent)
        self._name  = name
        self._icon  = icon_name
        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setObjectName("monster_card")
        self.setStyleSheet(
            f"QFrame#monster_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
            f"QFrame#monster_card:hover {{ border-color: {T.BORDER_HOVER}; }}"
        )
        self._build(respawn, hotkey, alert_before,
                    alert_sound, end_sound, loop, permanent)

    def _build(self, respawn, hotkey, alert_before,
               alert_sound, end_sound, loop, permanent):
        L = QVBoxLayout(self)
        L.setContentsMargins(T.S_LG, T.S_MD, T.S_LG, T.S_MD)
        L.setSpacing(T.S_SM)

        # ── 頂部：名稱 + 設定 ──
        top = QHBoxLayout()
        top.setSpacing(T.S_SM)
        name_lbl = T.make_label(self._name, T.FONT_CARD_TITLE,
                                color_override=T.TEXT_HI)
        top.addWidget(name_lbl)
        top.addStretch()
        more = MoreBtn("怪物詳細設定")
        top.addWidget(more)
        L.addLayout(top)

        # ── icon 大框 ──
        icon_wrap = QHBoxLayout()
        icon_wrap.setContentsMargins(0, 0, 0, 0)
        icon_wrap.addStretch()
        icon_wrap.addWidget(_IconArea(self._icon, T.RED, 96))
        icon_wrap.addStretch()
        L.addLayout(icon_wrap)

        L.addSpacing(T.S_XS)

        # ── 重生時間 + 快捷鍵 ──
        L.addWidget(_label_with_icon("timer", "重生時間"))
        rs = QHBoxLayout()
        rs.setSpacing(0); rs.setContentsMargins(0, 0, 0, 0)
        rs.addWidget(InputChip(f"{respawn}s", T.CYAN, "重置秒數", value_w=60))
        rs.addStretch()
        L.addLayout(rs)

        L.addWidget(_label_with_icon("keyboard", "快捷鍵"))
        hk = QHBoxLayout()
        hk.setSpacing(0); hk.setContentsMargins(0, 0, 0, 0)
        hk_text  = hotkey or "未設"
        hk_color = T.YELLOW if hotkey else None
        hk.addWidget(InputChip(hk_text, hk_color, "清除按鍵", value_w=60))
        hk.addStretch()
        L.addLayout(hk)

        L.addWidget(_section_divider())

        # ── 提前提示 ──
        L.addWidget(_label_with_icon("bell-ring", "提前提示", T.ORANGE))
        alert_row = QHBoxLayout()
        alert_row.setSpacing(T.S_SM); alert_row.setContentsMargins(0, 0, 0, 0)
        alert_row.addWidget(_pill_btn(f"{alert_before}s", T.ORANGE, w=44, h=22))
        alert_row.addWidget(_sound_combo(["—", "鈴聲 A", "鈴聲 B", "鈴聲 C"],
                                          alert_sound), 1)
        L.addLayout(alert_row)

        # ── 結束聲音 ──
        L.addWidget(_label_with_icon("music", "結束聲音"))
        end_row = QHBoxLayout()
        end_row.setSpacing(T.S_SM); end_row.setContentsMargins(0, 0, 0, 0)
        end_row.addWidget(_sound_combo(["—", "鈴聲 A", "鈴聲 B", "鈴聲 C"],
                                        end_sound), 1)
        L.addLayout(end_row)

        L.addWidget(_section_divider())

        # ── 循環 / 常駐 ──
        cb_row = QHBoxLayout()
        cb_row.setSpacing(T.S_LG); cb_row.setContentsMargins(0, 0, 0, 0)
        loop_cb = _accent_check("循環", T.GREEN)
        loop_cb.setChecked(loop)
        perm_cb = _accent_check("常駐", T.YELLOW)
        perm_cb.setChecked(permanent)
        cb_row.addWidget(loop_cb)
        cb_row.addWidget(perm_cb)
        cb_row.addStretch()
        L.addLayout(cb_row)

        L.addStretch()


# ════════════════════════════════════════════════════════════
# MonsterPageV2
# ════════════════════════════════════════════════════════════

class MonsterPageV2(QWidget):
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

        # ── 工具列 ──
        bar = QHBoxLayout()
        bar.setSpacing(T.S_SM)
        bar.addWidget(T.make_label("怪物重生", T.FONT_SECTION))

        hint = T.make_label("按下快捷鍵開始計時（從 0 數到設定時間）",
                            T.FONT_CAPTION)
        bar.addSpacing(T.S_SM)
        bar.addWidget(hint)
        bar.addStretch()

        add_btn = QPushButton("新增怪物")
        add_btn.setIcon(lucide_icon("plus", "#ffffff", 14, stroke=2.0))
        add_btn.setIconSize(QSize(14, 14))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setFixedHeight(T.BTN_H)
        add_btn.setStyleSheet(
            f"QPushButton {{ color: #ffffff; background: {T.ORANGE};"
            f" border: none; border-radius: {T.R_SM}px;"
            f" padding: 0 14px; font-size: 12px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: #ff9d5a; }}"
        )
        add_btn.clicked.connect(self._toast_pending)
        bar.addWidget(add_btn)
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

        for data in DEMO_MONSTERS:
            h.addWidget(MonsterCard(inner, *data))

        scroll.setWidget(inner)
        root.addWidget(scroll, 1)
