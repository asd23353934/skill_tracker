"""
UI 樣式常量
集中管理所有顏色、尺寸等樣式設定
"""


class Colors:
    """顏色常量"""
    # 背景色
    BG_DARK = '#0f172a'
    BG_MEDIUM = '#1e293b'
    BG_LIGHT = '#334155'
    
    # 強調色
    ACCENT_BLUE = '#3b82f6'
    ACCENT_PURPLE = '#8b5cf6'
    ACCENT_GREEN = '#10b981'
    ACCENT_YELLOW = '#fbbf24'
    ACCENT_RED = '#ef4444'
    ACCENT_ORANGE = '#fb923c' 
    
    # 文字色
    TEXT_PRIMARY = '#f1f5f9'
    TEXT_SECONDARY = '#94a3b8'


class Sizes:
    """尺寸常量"""
    # 圓角與邊框
    BORDER_RADIUS = 8
    BORDER_WIDTH = 2
    
    # 技能視窗
    SKILL_WINDOW_WIDTH = 100
    SKILL_WINDOW_HEIGHT = 125
    
    # 按鈕尺寸
    BTN_LARGE = (120, 35)
    BTN_MEDIUM = (100, 30)
    BTN_SMALL = (70, 26)
    BTN_TINY = (40, 22)


class Fonts:
    """字型常量"""
    TITLE_LARGE = ('Microsoft JhengHei', 18, 'bold')
    TITLE_MEDIUM = ('Microsoft JhengHei', 14, 'bold')
    TITLE_SMALL = ('Microsoft JhengHei', 12, 'bold')
    
    BODY_LARGE = ('Microsoft JhengHei', 10)
    BODY_LARGE_BOLD = ('Microsoft JhengHei', 10, 'bold')
    BODY_MEDIUM = ('Microsoft JhengHei', 9)
    BODY_MEDIUM_BOLD = ('Microsoft JhengHei', 9, 'bold')
    BODY_SMALL = ('Microsoft JhengHei', 8)
    BODY_SMALL_BOLD = ('Microsoft JhengHei', 8, 'bold')
    
    BUTTON = ('Microsoft JhengHei', 9, 'bold')
    BUTTON_SMALL = ('Microsoft JhengHei', 7, 'bold')
