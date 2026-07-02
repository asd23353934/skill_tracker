"""
主題 V2 — 黑灰漸層 Dashboard
所有 token 集中於此；新增元件禁止寫死數值。
完整規範見 docs/DESIGN_V2.md
"""

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel


class V2Theme:
    """V2 設計 Token + 全域 QSS"""

    # ═════════════ 色彩 — 中性 ═════════════
    BG_TOP        = "#1f1f24"
    BG_MID        = "#141418"
    BG_BOTTOM     = "#08080a"
    BG_WINDOW     = "#141418"
    BG_SURFACE    = "#1d1d22"
    BG_ELEVATED   = "#26262c"
    BG_HOVER      = "#2d2d34"
    BG_INPUT      = "#1a1a1e"

    BORDER        = "#2a2a30"
    BORDER_SOFT   = "#1d1d22"
    BORDER_HOVER  = "#42424a"

    TEXT_HI       = "#f1f2f5"
    TEXT          = "#a8aab2"
    TEXT_DIM      = "#6e7079"
    TEXT_MUTED    = "#454650"

    # ═════════════ 色彩 — 強調 ═════════════
    ORANGE        = "#ff8c42"     # 主 CTA / active
    ORANGE_HOVER  = "#ff9d5a"     # 主 CTA hover（橘色加亮）
    PURPLE        = "#9b6df1"     # 強度
    BLUE          = "#5c8df5"     # 資料
    CYAN          = "#4dd2e8"     # 速度
    PINK          = "#f06b9b"     # 特殊
    GREEN         = "#56d99a"     # 正向
    RED           = "#ef5b6d"     # 負向 / 錯誤
    YELLOW        = "#fbbf24"     # warning

    # ═════════════ 間距（4 / 8 / 12 / 16 / 20 / 24）═════════════
    S_XS  = 4
    S_SM  = 8
    S_MD  = 12
    S_LG  = 16
    S_XL  = 20
    S_2XL = 24

    # ═════════════ 圓角 ═════════════
    R_SM = 6
    R_MD = 10
    R_LG = 14

    # ═════════════ 字型 ═════════════
    FONT_FAMILY  = "Microsoft JhengHei"

    # (size, weight, color, letter_spacing) — letter_spacing 為 px
    FONT_DISPLAY     = (18, 700, "TEXT_HI",  0)
    FONT_SECTION     = (14, 700, "TEXT_HI",  0)
    FONT_CARD_TITLE  = (13, 700, "TEXT_HI",  0)
    FONT_BODY        = (12, 500, "TEXT",     0)
    FONT_CAPTION     = (11, 500, "TEXT_DIM", 0)
    FONT_LABEL       = (10, 700, "TEXT_DIM", 1)
    FONT_METRIC      = (22, 700, "TEXT_HI",  0)
    FONT_METRIC_SM   = (16, 700, "TEXT_HI",  0)
    FONT_DELTA       = (11, 700, "TEXT_HI",  0)

    # ═════════════ 元件尺寸 ═════════════
    SIDEBAR_W        = 60
    HEADER_H         = 80
    ICON_BADGE       = 36       # IconBadge 預設邊長
    CARD_STAT_H      = 138      # StatCard 固定高
    CARD_SERVICE_H   = 104      # ServiceCard 固定高
    CHIP_H           = 22       # Chip 高度
    BTN_H            = 32       # 按鈕標準高
    CTRL_BTN         = 30       # 視窗控制按鈕（正方）

    # ═════════════ 工具方法 ═════════════
    @classmethod
    def bg_gradient(cls) -> str:
        return (
            f"qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            f" stop:0 {cls.BG_TOP}, stop:0.55 {cls.BG_MID},"
            f" stop:1 {cls.BG_BOTTOM})"
        )

    @classmethod
    def color(cls, name: str) -> str:
        """依 token 名稱取色（例：'TEXT_HI'）"""
        return getattr(cls, name)

    @classmethod
    def combo_popup_qss(cls) -> str:
        """QComboBox 下拉列表樣式 — 個別 widget 覆寫 QComboBox 時須附加此規則，
        否則 popup 會失去全域背景、在部分裝置呈現透明。"""
        return (
            f"QComboBox QAbstractItemView {{"
            f" background: {cls.BG_ELEVATED}; color: {cls.TEXT_HI};"
            f" border: 1px solid {cls.BORDER};"
            f" selection-background-color: {cls.BG_HOVER};"
            f" selection-color: {cls.TEXT_HI};"
            f" outline: none; padding: 4px; }}"
        )

    @classmethod
    def combo_qss(cls, *, bg: str = None, border: str = None,
                  padding: str = "0 10px", font_size: int = 12) -> str:
        """可編輯/一般下拉 QComboBox 的共用樣式樣板（含 hover / drop-down / popup）。

        各頁/對話框逐字重複的 QComboBox QSS 收斂於此。已自動附加
        combo_popup_qss()，呼叫端不必再手動拼接。

        Args:
            bg: 背景色，預設 BG_SURFACE；表單/對話框慣用 BG_INPUT
            border: 邊框色，預設 BORDER_SOFT；搭配 BG_INPUT 時慣用 BORDER
            padding: 內距，預設 "0 10px"（緊湊版傳 "0 8px"）
            font_size: 字級（px），預設 12

        Returns:
            完整 QComboBox QSS 字串
        """
        bg = bg or cls.BG_SURFACE
        border = border or cls.BORDER_SOFT
        return (
            f"QComboBox {{ background: {bg}; color: {cls.TEXT};"
            f" border: 1px solid {border}; border-radius: {cls.R_SM}px;"
            f" padding: {padding}; font-size: {font_size}px; }}"
            f"QComboBox:hover {{ border-color: {cls.BORDER_HOVER}; }}"
            f"QComboBox::drop-down {{ border: none; width: 16px; }}"
            + cls.combo_popup_qss()
        )

    @classmethod
    def primary_button_qss(cls, *, padding: str = "0 14px", font_size: int = 12,
                           weight: int = 600, radius: int = None) -> str:
        """橘色主行動按鈕（CTA）的共用 QSS 樣板。

        ORANGE 底 + 白字 + 無邊框 + ORANGE_HOVER hover；各頁/對話框逐字重複的
        橘色按鈕 QSS 收斂於此。元件層的 make_primary_button() 亦委派至此。

        Args:
            padding: 內距，預設 "0 14px"
            font_size: 字級（px），預設 12
            weight: 字重，預設 600
            radius: 圓角（px），預設 R_SM；膠囊鈕傳 14

        Returns:
            完整 QPushButton QSS 字串
        """
        radius = cls.R_SM if radius is None else radius
        return (
            f"QPushButton {{ background: {cls.ORANGE}; color: #ffffff; border: none;"
            f" border-radius: {radius}px; padding: {padding};"
            f" font-size: {font_size}px; font-weight: {weight}; }}"
            f"QPushButton:hover {{ background: {cls.ORANGE_HOVER}; }}"
        )

    @classmethod
    def radio_button_qss(cls) -> str:
        """QRadioButton 的共用 QSS（圓形 indicator，ORANGE 選中）。

        對齊全域 QCheckBox 的觀感（同 border / hover / checked 配色），
        收斂逐字重複的 radio 樣式，供對話框/頁面共用。
        """
        return (
            f"QRadioButton {{ color: {cls.TEXT}; background: transparent;"
            f" font-size: 12px; spacing: 5px; }}"
            f"QRadioButton::indicator {{ width: 13px; height: 13px;"
            f" border-radius: 7px; border: 1px solid {cls.BORDER_HOVER};"
            f" background: {cls.BG_INPUT}; }}"
            f"QRadioButton::indicator:hover {{ border-color: {cls.ORANGE}; }}"
            f"QRadioButton::indicator:checked {{ background: {cls.ORANGE};"
            f" border-color: {cls.ORANGE}; }}"
        )

    @classmethod
    def alpha(cls, hex_color: str, alpha_int: int) -> str:
        """產生 rgba 字串（hex_color = '#rrggbb'，alpha 0-255）"""
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha_int})"

    @classmethod
    def mix_hex(cls, base: str, accent: str, ratio: float) -> str:
        """合成不透明 hex 色：ratio=0 → base；ratio=1 → accent"""
        b = base.lstrip("#")
        a = accent.lstrip("#")
        return "#" + "".join(
            f"{int(int(b[i:i+2], 16) * (1 - ratio) + int(a[i:i+2], 16) * ratio):02x}"
            for i in (0, 2, 4)
        )

    # ═════════════ 字型套用 ═════════════
    @classmethod
    def apply_font(cls, label: QLabel, spec: tuple, color_override: str = None):
        """套字級到 QLabel
        spec = (size, weight, color_token_name, letter_spacing)
        """
        size, weight, color_name, ls = spec
        color = color_override or cls.color(color_name)
        label.setStyleSheet(
            f"color: {color}; font-size: {size}px; font-weight: {weight};"
            f" letter-spacing: {ls}px; background: transparent;"
        )
        return label

    @classmethod
    def make_label(cls, text: str, spec: tuple, color_override: str = None) -> QLabel:
        """快速建立套好字級的 QLabel"""
        l = QLabel(text)
        cls.apply_font(l, spec, color_override)
        return l

    # ═════════════ 全域 QSS ═════════════
    @classmethod
    def global_qss(cls) -> str:
        c = cls
        return f"""
        * {{ font-family: "{c.FONT_FAMILY}"; }}
        QWidget {{ background: transparent; color: {c.TEXT}; font-size: 12px; }}

        /* 按鈕 */
        QPushButton {{
            background: {c.BG_INPUT}; color: {c.TEXT_HI};
            border: 1px solid {c.BORDER}; border-radius: {c.R_SM}px;
            padding: 6px 14px; font-size: 12px; font-weight: 500;
        }}
        QPushButton:hover {{ background: {c.BG_HOVER}; border-color: {c.BORDER_HOVER}; }}
        QPushButton:pressed {{ background: {c.BG_SURFACE}; }}
        QPushButton:disabled {{ color: {c.TEXT_MUTED}; background: {c.BG_SURFACE}; }}
        QPushButton[kind="primary"] {{
            background: {c.ORANGE}; color: #ffffff;
            border: 1px solid {c.ORANGE}; font-weight: 600;
        }}
        QPushButton[kind="primary"]:hover {{
            background: {c.ORANGE_HOVER}; border-color: {c.ORANGE_HOVER};
        }}
        QPushButton[kind="ghost"] {{
            background: transparent; border: 1px solid transparent; color: {c.TEXT_DIM};
        }}
        QPushButton[kind="ghost"]:hover {{ background: {c.BG_SURFACE}; color: {c.TEXT_HI}; }}

        /* 輸入 */
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
            background: {c.BG_INPUT}; color: {c.TEXT_HI};
            border: 1px solid {c.BORDER}; border-radius: {c.R_SM}px;
            padding: 6px 10px; selection-background-color: {c.ORANGE};
            selection-color: #ffffff;
        }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
        QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {{
            border-color: {c.ORANGE};
        }}
        QComboBox::drop-down {{ border: none; width: 18px; }}
        /* down-arrow 不自繪，交由 Qt 預設樣式畫小三角 */
        QComboBox QAbstractItemView {{
            background: {c.BG_ELEVATED}; color: {c.TEXT_HI};
            border: 1px solid {c.BORDER}; selection-background-color: {c.BG_HOVER};
            selection-color: {c.TEXT_HI}; outline: none; padding: 4px;
        }}

        /* checkbox */
        QCheckBox {{ color: {c.TEXT}; spacing: 6px; background: transparent; }}
        QCheckBox::indicator {{
            width: 14px; height: 14px; border-radius: 3px;
            border: 1px solid {c.BORDER_HOVER}; background: {c.BG_INPUT};
        }}
        QCheckBox::indicator:hover {{ border-color: {c.ORANGE}; }}
        QCheckBox::indicator:checked {{ background: {c.ORANGE}; border-color: {c.ORANGE}; }}

        /* 捲軸 */
        QScrollBar:vertical {{
            background: transparent; width: 8px; margin: 2px; border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {c.BORDER_HOVER}; border-radius: 4px; min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {c.ORANGE}; }}
        QScrollBar::add-line, QScrollBar::sub-line,
        QScrollBar::add-page, QScrollBar::sub-page {{
            background: none; height: 0; width: 0;
        }}
        QScrollBar:horizontal {{
            background: transparent; height: 8px; margin: 2px; border: none;
        }}
        QScrollBar::handle:horizontal {{
            background: {c.BORDER_HOVER}; border-radius: 4px; min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: {c.ORANGE}; }}

        QDialog {{ background: {c.BG_SURFACE}; }}

        QToolTip {{
            background: {c.BG_ELEVATED}; color: {c.TEXT_HI};
            border: 1px solid {c.BORDER_HOVER}; border-radius: {c.R_SM}px;
            padding: 5px 10px; font-size: 11px;
        }}

        QLabel {{ background: transparent; color: {c.TEXT}; }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollArea > QWidget > QWidget {{ background: transparent; }}
        """
