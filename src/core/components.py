"""
UI 組件模組
提供可重用的 UI 組件
"""

import tkinter as tk
from src.utils.styles import Colors, Sizes
from src.utils.helpers import darken_color


class RoundedButton(tk.Canvas):
    """圓角按鈕組件"""
    
    def __init__(self, parent, text, command, bg_color, fg_color='white', 
                 font=('Microsoft JhengHei', 9, 'bold'), 
                 width=100, height=35, **kwargs):
        """初始化圓角按鈕
        
        Args:
            parent: 父容器
            text: 按鈕文字
            command: 點擊回調函數
            bg_color: 背景顏色
            fg_color: 文字顏色
            font: 字型
            width: 寬度
            height: 高度
        """
        super().__init__(parent, width=width, height=height, 
                        bg=parent['bg'], highlightthickness=0, **kwargs)
        
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.text = text
        self.font = font
        self.width = width
        self.height = height
        self.hover_color = darken_color(bg_color)
        self.is_enabled = True
        
        self._draw_button()
        self._bind_events()
    
    def _draw_button(self, color=None):
        """繪製按鈕"""
        self.delete('all')
        color = color or self.bg_color
        radius = Sizes.BORDER_RADIUS
        
        # 繪製圓角矩形
        self.create_arc(0, 0, radius*2, radius*2, 
                       start=90, extent=90, fill=color, outline=color)
        self.create_arc(self.width-radius*2, 0, self.width, radius*2, 
                       start=0, extent=90, fill=color, outline=color)
        self.create_arc(0, self.height-radius*2, radius*2, self.height, 
                       start=180, extent=90, fill=color, outline=color)
        self.create_arc(self.width-radius*2, self.height-radius*2, 
                       self.width, self.height, start=270, extent=90, 
                       fill=color, outline=color)
        self.create_rectangle(radius, 0, self.width-radius, self.height, 
                            fill=color, outline=color)
        self.create_rectangle(0, radius, self.width, self.height-radius, 
                            fill=color, outline=color)
        
        # 繪製文字
        self.create_text(self.width/2, self.height/2, text=self.text, 
                        fill=self.fg_color, font=self.font)
    
    def _bind_events(self):
        """綁定事件"""
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _unbind_events(self):
        """解綁事件"""
        self.unbind('<Button-1>')
        self.unbind('<Enter>')
        self.unbind('<Leave>')
    
    def _on_click(self, event):
        """點擊事件"""
        if self.command and self.is_enabled:
            self.command()
    
    def _on_enter(self, event):
        """滑鼠進入事件"""
        if self.is_enabled:
            self._draw_button(self.hover_color)
    
    def _on_leave(self, event):
        """滑鼠離開事件"""
        if self.is_enabled:
            self._draw_button(self.bg_color)
    
    def config_state(self, state):
        """配置按鈕狀態
        
        Args:
            state: tk.NORMAL 或 tk.DISABLED
        """
        if state == tk.DISABLED:
            self.is_enabled = False
            self._draw_button('#475569')
            self._unbind_events()
        else:
            self.is_enabled = True
            self._draw_button(self.bg_color)
            self._bind_events()
    
    def update_text(self, new_text):
        """更新按鈕文字
        
        Args:
            new_text: 新文字
        """
        self.text = new_text
        self._draw_button()
    
    def update_color(self, new_color, new_fg_color=None):
        """更新按鈕顏色
        
        Args:
            new_color: 新背景顏色
            new_fg_color: 新文字顏色（可選）
        """
        self.bg_color = new_color
        self.hover_color = darken_color(new_color)
        if new_fg_color:
            self.fg_color = new_fg_color
        self._draw_button()


class RoundedFrame(tk.Frame):
    """簡化的圓角框架組件 - 使用 highlightbackground"""
    
    def __init__(self, parent, radius=10, bg=Colors.BG_MEDIUM, border_color=None, border_width=2, fixed_height=False, **kwargs):
        """初始化圓角框架
        
        Args:
            parent: 父容器
            radius: 圓角半徑（此版本忽略，保持接口一致）
            bg: 背景顏色
            border_color: 邊框顏色
            border_width: 邊框寬度
            fixed_height: 是否固定高度
        """
        super().__init__(parent, bg=bg, **kwargs)
        
        # 使用 highlightbackground 創建邊框
        self.configure(
            highlightbackground=border_color or Colors.BG_LIGHT,
            highlightthickness=border_width
        )
        
        # 只在需要固定高度時禁用自動擴展
        if fixed_height:
            self.pack_propagate(False)
    
    def get_content(self):
        """獲取內容框架 - 簡化版本直接返回自己"""
        return self


class BorderedFrame(tk.Frame):
    """帶邊框的框架組件"""
    
    def __init__(self, parent, bg=Colors.BG_MEDIUM, **kwargs):
        """初始化帶邊框框架
        
        Args:
            parent: 父容器
            bg: 背景顏色
        """
        super().__init__(parent, bg=bg, relief=tk.RIDGE, 
                        bd=Sizes.BORDER_WIDTH, **kwargs)


class SectionFrame(tk.Frame):
    """區塊框架組件（帶標題）- 簡化版本"""
    
    def __init__(self, parent, title, bg=Colors.BG_MEDIUM):
        """初始化區塊框架
        
        Args:
            parent: 父容器
            title: 標題文字
            bg: 背景顏色
        """
        super().__init__(parent, bg=bg)
        
        # 添加邊框
        self.configure(
            highlightbackground=Colors.BG_LIGHT,
            highlightthickness=2
        )
        
        # 標題列
        title_bar = tk.Frame(self, bg=Colors.BG_LIGHT)
        title_bar.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        tk.Label(title_bar, text=title, 
                bg=Colors.BG_LIGHT, fg=Colors.TEXT_PRIMARY, 
                font=('Microsoft JhengHei', 10, 'bold')).pack(
                    side=tk.LEFT, padx=10, pady=8)
        
        # 內容區
        self.content = tk.Frame(self, bg=Colors.BG_LIGHT)
        self.content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def get_content(self):
        """獲取內容容器"""
        return self.content


class ScrollableFrame(tk.Frame):
    """可滾動框架組件 - 極簡版本"""
    
    def __init__(self, parent, bg=Colors.BG_DARK):
        """初始化可滾動框架
        
        Args:
            parent: 父容器
            bg: 背景顏色
        """
        super().__init__(parent, bg=bg)
        
        # 創建 Canvas 和 Scrollbar
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", 
                                      command=self.canvas.yview)
        
        # 創建可滾動內容框架
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg)
        
        # 綁定配置事件
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # 創建視窗
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        
        # 綁定 Canvas 大小改變事件
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 佈局
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 綁定滾輪 - 直接綁定到所有子組件
        self._bind_to_mousewheel(self.canvas)
        self._bind_to_mousewheel(self.scrollable_frame)
    
    def _bind_to_mousewheel(self, widget):
        """遞歸綁定滾輪到組件及其所有子組件"""
        widget.bind("<MouseWheel>", self._on_mousewheel, "+")
        widget.bind("<Button-4>", self._on_mousewheel, "+")
        widget.bind("<Button-5>", self._on_mousewheel, "+")
        
        # 綁定到所有子組件
        for child in widget.winfo_children():
            self._bind_to_mousewheel(child)
    
    def bind_widget_to_scroll(self, widget):
        """公開方法：綁定新組件到滾輪"""
        self._bind_to_mousewheel(widget)
    
    def _on_canvas_configure(self, event):
        """Canvas 大小改變時調整內部窗口寬度"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        """滑鼠滾輪事件"""
        # Windows
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # Linux
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
    
    def get_content(self):
        """獲取內容容器"""
        return self.scrollable_frame
