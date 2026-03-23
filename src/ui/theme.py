"""
主題系統 — PySide6 QSS 版本
集中管理所有顏色、字型、尺寸等樣式設定，並提供 QSS 全域樣式表
RPG 遊戲風格 — 金色邊框、深色卡片、楓之谷質感
"""

from PySide6.QtGui import QFont


class AppTheme:
    """應用程式主題常量 — RPG Gaming 風格"""

    # ===== 背景色階層（由深到淺）=====
    BG_DARKEST    = "#02040a"       # 最深層 (側邊欄底色)
    BG_DEEP       = "#06090f"       # 主視窗背景
    BG_PRIMARY    = "#06090f"       # 主背景 (= BG_DEEP)
    BG_SECONDARY  = "#0d1117"       # 次要容器 (Header)
    BG_TERTIARY   = "#1a2130"       # 控件/分隔底色
    BG_CARD        = "#131c2e"       # 卡片/面板背景（深藍黑，搭配金色邊框對比清晰）
    BG_CARD_HOVER  = "#1a2840"       # 卡片 hover 狀態
    BG_CARD_ACTIVE = "#213250"       # 卡片選中狀態

    # ===== 金色系統 (RPG 主色調) =====
    GOLD_PRIMARY = "#d4a843"        # 主金色 (邊框/標題)
    GOLD_LIGHT   = "#f0d78c"        # 亮金色 (hover 高亮)
    GOLD_DARK    = "#c9952a"        # 暗金色 (按壓/次要邊框)
    GOLD_MUTED   = "#8b7435"        # 柔和金 (細微裝飾)

    # ===== 裝飾邊框 =====
    BORDER_GOLD         = "#d4a843"
    BORDER_GOLD_SUBTLE  = "#8b7435"
    BORDER_GOLD_HAIRLINE = "rgba(139, 116, 53, 35)"   # 極細分隔線（約 14% 不透明）

    # ===== 強調色 (功能性色彩) =====
    ACCENT_BLUE         = "#3b82f6"
    ACCENT_PURPLE       = "#8b5cf6"
    ACCENT_GREEN        = "#10b981"
    ACCENT_GREEN_HOVER  = "#0d9668"
    ACCENT_YELLOW       = "#fbbf24"
    ACCENT_YELLOW_HOVER = "#e5a800"
    ACCENT_RED          = "#ef4444"
    ACCENT_RED_HOVER    = "#dc2626"
    ACCENT_ORANGE       = "#fb923c"
    ACCENT_ORANGE_HOVER = "#e07a2a"

    # ===== 文字色 =====
    TEXT_PRIMARY   = "#f1f5f9"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED     = "#64748b"
    TEXT_GOLD      = "#f0d78c"
    TEXT_HIGHLIGHT = "#ffffff"

    # ===== 字型 =====
    FONT_FAMILY = "Microsoft JhengHei"

    # ===== 側邊欄 =====
    SIDEBAR_WIDTH          = 44
    SIDEBAR_COLLAPSED      = 44
    SIDEBAR_EXPANDED       = 200
    SIDEBAR_BG             = "#02040a"       # 極深，接近 PyDracula 側欄黑
    SIDEBAR_HOVER_BG       = "#0d1420"       # hover 背景
    SIDEBAR_ACTIVE_BORDER  = "#d4a843"
    SIDEBAR_SEPARATOR      = "#1a2332"
    SIDEBAR_ICON_ACTIVE    = "#fbbf24"
    SIDEBAR_ICON_INACTIVE  = "#4a5568"       # 稍暗以配合新背景

    # ===== 卡片尺寸（供 SkillWindow 等使用）=====
    CARD_WIDTH    = 145
    CARD_HEIGHT   = 200
    CARD_ICON_SIZE = 64
    CARD_GAP      = 8
    CARD_CORNER   = 8

    # ===== 欄位 Banner 色調 =====
    BANNER_PLAYER        = "#1a3a5c"
    BANNER_BOSS          = "#3a1a1a"
    BANNER_ITEM          = "#1a3a2a"
    BANNER_BORDER_PLAYER = "#3b82f6"
    BANNER_BORDER_BOSS   = "#ef4444"
    BANNER_BORDER_ITEM   = "#10b981"

    # ===== 狀態指示色 =====
    STATUS_PERMANENT     = "#fbbf24"
    STATUS_LOOP          = "#10b981"
    STATUS_ALERT         = "#fb923c"
    STATUS_PERMANENT_DIM = "#8b6914"
    STATUS_LOOP_DIM      = "#0a7553"
    STATUS_ALERT_DIM     = "#9b5a1e"

    # ===== 倒數遮罩 (SkillWindow PIL 合成用) =====
    OVERLAY_COLOR = (0, 0, 0, 140)

    # ===== 圓角 =====
    CORNER_LG = 12
    CORNER_MD = 8
    CORNER_SM = 4

    # ===== 邊框 =====
    BORDER_WIDTH = 2

    # ===== Header =====
    HEADER_HEIGHT       = 44
    HEADER_BORDER_OUTER = "#d4a843"
    HEADER_BORDER_INNER = "#8b7435"

    @classmethod
    def build_stylesheet(cls) -> str:
        """回傳完整 QSS 全域樣式表字串

        Returns:
            QSS 字串，供 QApplication.setStyleSheet() 套用
        """
        return f"""
        /* ===== 全域基底 ===== */
        QWidget {{
            background-color: {cls.BG_PRIMARY};
            color: {cls.TEXT_PRIMARY};
            font-family: "{cls.FONT_FAMILY}";
            font-size: 12px;
        }}
        QMainWindow {{
            background-color: {cls.BG_PRIMARY};
        }}

        /* ===== 按鈕 ===== */
        QPushButton {{
            background-color: {cls.BG_TERTIARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GOLD_MUTED};
            border-radius: 4px;
            padding: 2px 8px;
            font-family: "{cls.FONT_FAMILY}";
            font-size: 11px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {cls.BG_SECONDARY};
            border-color: {cls.GOLD_PRIMARY};
            color: {cls.TEXT_HIGHLIGHT};
        }}
        QPushButton:pressed {{
            background-color: {cls.BG_DARKEST};
            border-color: {cls.GOLD_DARK};
        }}
        QPushButton:disabled {{
            color: {cls.TEXT_MUTED};
            border-color: {cls.BG_TERTIARY};
        }}

        /* 金色主按鈕 */
        QPushButton[class="btn-gold"] {{
            background-color: {cls.GOLD_PRIMARY};
            color: #000000;
            border-color: {cls.GOLD_LIGHT};
        }}
        QPushButton[class="btn-gold"]:hover {{
            background-color: {cls.GOLD_LIGHT};
        }}

        /* 危險紅色按鈕 */
        QPushButton[class="btn-danger"] {{
            background-color: {cls.ACCENT_RED};
            color: #ffffff;
            border-color: #dc2626;
        }}
        QPushButton[class="btn-danger"]:hover {{
            background-color: #dc2626;
        }}

        /* 綠色按鈕 */
        QPushButton[class="btn-success"] {{
            background-color: {cls.ACCENT_GREEN};
            color: #ffffff;
            border-color: {cls.ACCENT_GREEN_HOVER};
        }}
        QPushButton[class="btn-success"]:hover {{
            background-color: {cls.ACCENT_GREEN_HOVER};
        }}

        /* 透明按鈕 */
        QPushButton[class="btn-flat"] {{
            background-color: transparent;
            border: none;
            color: {cls.TEXT_MUTED};
        }}
        QPushButton[class="btn-flat"]:hover {{
            color: {cls.TEXT_PRIMARY};
            background-color: {cls.BG_TERTIARY};
        }}

        /* ===== 核取方塊 ===== */
        QCheckBox {{
            color: {cls.TEXT_SECONDARY};
            font-size: 10px;
            spacing: 4px;
            background-color: transparent;
        }}
        QCheckBox::indicator {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
            border: 1px solid {cls.GOLD_MUTED};
            background-color: {cls.BG_TERTIARY};
        }}
        QCheckBox::indicator:checked {{
            background-color: {cls.ACCENT_YELLOW};
            border-color: {cls.ACCENT_YELLOW};
            image: none;
        }}
        QCheckBox::indicator:hover {{
            border-color: {cls.GOLD_PRIMARY};
        }}

        /* ===== 下拉選單 ===== */
        QComboBox {{
            background-color: {cls.BG_TERTIARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GOLD_MUTED};
            border-radius: 4px;
            padding: 2px 8px;
            font-family: "{cls.FONT_FAMILY}";
            font-size: 11px;
        }}
        QComboBox:hover {{
            border-color: {cls.GOLD_PRIMARY};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 4px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {cls.GOLD_PRIMARY};
            width: 0;
            height: 0;
        }}
        QComboBox QAbstractItemView {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GOLD_MUTED};
            selection-background-color: {cls.GOLD_DARK};
            selection-color: #000000;
            outline: none;
        }}

        /* ===== 捲軸 ===== */
        QScrollBar:vertical {{
            background: {cls.BG_SECONDARY};
            width: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {cls.BG_TERTIARY};
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {cls.GOLD_PRIMARY};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}
        QScrollBar:horizontal {{
            background: {cls.BG_SECONDARY};
            height: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {cls.BG_TERTIARY};
            border-radius: 4px;
            min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {cls.GOLD_PRIMARY};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
            background: none;
        }}

        /* ===== 對話框 ===== */
        QDialog {{
            background-color: {cls.BG_DEEP};
        }}

        /* ===== 輸入框 ===== */
        QLineEdit {{
            background-color: {cls.BG_TERTIARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GOLD_MUTED};
            border-radius: 4px;
            padding: 3px 6px;
            font-family: "{cls.FONT_FAMILY}";
        }}
        QLineEdit:focus {{
            border-color: {cls.GOLD_PRIMARY};
        }}
        QSpinBox, QDoubleSpinBox {{
            background-color: {cls.BG_TERTIARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GOLD_MUTED};
            border-radius: 4px;
            padding: 3px 6px;
            font-family: "{cls.FONT_FAMILY}";
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {cls.GOLD_PRIMARY};
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: {cls.BG_SECONDARY};
            border: none;
            width: 16px;
        }}

        /* ===== 標籤 ===== */
        QLabel {{
            color: {cls.TEXT_PRIMARY};
            background-color: transparent;
        }}

        /* ===== 清單 ===== */
        QListWidget {{
            background-color: {cls.BG_SECONDARY};
            border: 1px solid {cls.GOLD_MUTED};
            border-radius: 4px;
            color: {cls.TEXT_PRIMARY};
            outline: none;
        }}
        QListWidget::item {{
            padding: 4px 8px;
            border-radius: 3px;
        }}
        QListWidget::item:selected {{
            background-color: {cls.GOLD_DARK};
            color: #000000;
        }}
        QListWidget::item:hover {{
            background-color: {cls.BG_TERTIARY};
        }}

        /* ===== 滑桿 ===== */
        QSlider::groove:horizontal {{
            background: {cls.BG_TERTIARY};
            height: 4px;
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {cls.GOLD_PRIMARY};
            width: 14px;
            height: 14px;
            border-radius: 7px;
            margin: -5px 0;
        }}
        QSlider::handle:horizontal:hover {{
            background: {cls.GOLD_LIGHT};
        }}
        QSlider::sub-page:horizontal {{
            background: {cls.GOLD_DARK};
            border-radius: 2px;
        }}

        /* ===== 分隔線 ===== */
        QFrame[frameShape="4"], QFrame[frameShape="5"] {{
            color: {cls.GOLD_MUTED};
        }}

        /* ===== ToolTip ===== */
        QToolTip {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GOLD_DARK};
            border-radius: 4px;
            padding: 4px 10px;
            font-family: "{cls.FONT_FAMILY}";
            font-size: 11px;
        }}

        /* ===== ScrollArea ===== */
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}
        """

    @classmethod
    def get_font(cls, size: int, bold: bool = False) -> QFont:
        """取得 QFont 物件

        Args:
            size: 字體大小 (pt)
            bold: 是否粗體

        Returns:
            QFont 物件
        """
        f = QFont(cls.FONT_FAMILY, size)
        if bold:
            f.setBold(True)
        return f
