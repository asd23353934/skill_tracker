"""
主題系統
集中管理所有顏色、字型、尺寸等樣式設定
RPG 遊戲風格 — 金色邊框、深色卡片、楓之谷質感
"""

import customtkinter as ctk

# 全域外觀設定
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class AppTheme:
    """應用程式主題常量 — RPG Gaming 風格"""

    # ===== 背景色階層（由深到淺）=====
    BG_DARKEST = "#060a14"       # 最深層 (側邊欄底色)
    BG_DEEP = "#0a0e1a"          # 主視窗背景
    BG_PRIMARY = "#0a0e1a"       # 主背景 (= BG_DEEP)
    BG_SECONDARY = "#111827"     # 次要容器
    BG_TERTIARY = "#1e293b"      # 控件/分隔底色
    BG_CARD = "#111827"          # 卡片/面板背景
    BG_CARD_HOVER = "#1a2332"    # 卡片 hover 狀態
    BG_CARD_ACTIVE = "#1e2d42"   # 卡片選中狀態

    # ===== 金色系統 (RPG 主色調) =====
    GOLD_PRIMARY = "#d4a843"     # 主金色 (邊框/標題)
    GOLD_LIGHT = "#f0d78c"       # 亮金色 (hover 高亮)
    GOLD_DARK = "#c9952a"        # 暗金色 (按壓/次要邊框)
    GOLD_MUTED = "#8b7435"       # 柔和金 (細微裝飾)

    # ===== 裝飾邊框 =====
    BORDER_GOLD = "#d4a843"      # 主金色邊框
    BORDER_GOLD_SUBTLE = "#8b7435"  # 柔和金色邊框

    # ===== 強調色 (功能性色彩) =====
    ACCENT_BLUE = "#3b82f6"
    ACCENT_PURPLE = "#8b5cf6"
    ACCENT_GREEN = "#10b981"
    ACCENT_GREEN_HOVER = "#0d9668"   # 綠色 hover
    ACCENT_YELLOW = "#fbbf24"
    ACCENT_YELLOW_HOVER = "#e5a800"  # 黃色 hover
    ACCENT_RED = "#ef4444"
    ACCENT_ORANGE = "#fb923c"
    ACCENT_ORANGE_HOVER = "#e07a2a"  # 橘色 hover

    # ===== 文字色 =====
    TEXT_PRIMARY = "#f1f5f9"     # 主要文字
    TEXT_SECONDARY = "#94a3b8"   # 次要文字
    TEXT_MUTED = "#64748b"       # 淡化文字
    TEXT_GOLD = "#f0d78c"        # 金色文字 (標題/重點)
    TEXT_HIGHLIGHT = "#ffffff"   # 純白強調

    # ===== 字型 =====
    FONT_FAMILY = "Microsoft JhengHei"

    # 標題字型
    FONT_TITLE_LG = (FONT_FAMILY, 22, "bold")
    FONT_TITLE_MD = (FONT_FAMILY, 16, "bold")
    FONT_TITLE_SM = (FONT_FAMILY, 14, "bold")
    FONT_RPG_TITLE = (FONT_FAMILY, 24, "bold")   # RPG 裝飾標題

    # 內容字型
    FONT_BODY_LG = (FONT_FAMILY, 13)
    FONT_BODY_LG_BOLD = (FONT_FAMILY, 13, "bold")
    FONT_BODY_MD = (FONT_FAMILY, 12)
    FONT_BODY_MD_BOLD = (FONT_FAMILY, 12, "bold")
    FONT_BODY_SM = (FONT_FAMILY, 11)
    FONT_BODY_SM_BOLD = (FONT_FAMILY, 11, "bold")

    # 按鈕字型
    FONT_BTN = (FONT_FAMILY, 12, "bold")
    FONT_BTN_SM = (FONT_FAMILY, 11, "bold")

    # 卡片字型
    FONT_CARD_NAME = (FONT_FAMILY, 11, "bold")
    FONT_CARD_BADGE = (FONT_FAMILY, 10, "bold")

    # ===== 側邊欄 =====
    FONT_SIDEBAR_ICON = (FONT_FAMILY, 20)
    SIDEBAR_WIDTH = 56           # 向下相容 (= SIDEBAR_COLLAPSED)
    SIDEBAR_COLLAPSED = 56       # 收合寬度
    SIDEBAR_EXPANDED = 200       # 展開寬度
    SIDEBAR_ANIM_STEPS = 8       # 動畫步數
    SIDEBAR_ANIM_MS = 20         # 每步毫秒
    SIDEBAR_BG = "#080c18"       # 側邊欄背景
    SIDEBAR_HOVER_BG = "#141c2e" # 側邊欄 hover 背景
    SIDEBAR_ACTIVE_BORDER = "#d4a843"  # Active 金色指示條
    SIDEBAR_SEPARATOR = "#1a2332"      # 分隔線
    SIDEBAR_ICON_ACTIVE = "#fbbf24"
    SIDEBAR_ICON_INACTIVE = "#64748b"

    # ===== 卡片尺寸 =====
    CARD_WIDTH = 145             # 卡片寬度
    CARD_HEIGHT = 200            # 卡片高度
    CARD_ICON_SIZE = 64          # 卡片圖示尺寸
    CARD_GAP = 8                 # 卡片間距
    CARD_CORNER = 8              # 卡片圓角

    # ===== 欄位 Banner 色調 =====
    BANNER_PLAYER = "#1a3a5c"    # 藍色調 (玩家技能)
    BANNER_BOSS = "#3a1a1a"      # 紅色調 (BOSS 技能)
    BANNER_ITEM = "#1a3a2a"      # 綠色調 (道具)
    BANNER_BORDER_PLAYER = "#3b82f6"
    BANNER_BORDER_BOSS = "#ef4444"
    BANNER_BORDER_ITEM = "#10b981"

    # ===== 狀態指示色 (暗色版) =====
    STATUS_PERMANENT = "#fbbf24"
    STATUS_LOOP = "#10b981"
    STATUS_ALERT = "#fb923c"
    STATUS_PERMANENT_DIM = "#8b6914"
    STATUS_LOOP_DIM = "#0a7553"
    STATUS_ALERT_DIM = "#9b5a1e"

    # ===== 倒數遮罩 =====
    OVERLAY_COLOR = (0, 0, 0, 140)

    # ===== 圓角 =====
    CORNER_LG = 12
    CORNER_MD = 8
    CORNER_SM = 4

    # ===== 邊框 =====
    BORDER_WIDTH = 2

    # ===== Header =====
    HEADER_HEIGHT = 84           # 含雙重邊框高度
    HEADER_BORDER_OUTER = "#d4a843"
    HEADER_BORDER_INNER = "#8b7435"
