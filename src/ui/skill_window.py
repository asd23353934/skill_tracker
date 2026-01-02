"""
技能倒數視窗模組
處理單個技能的倒數顯示視窗
"""

import tkinter as tk
import threading
import time
import winsound
from src.utils.styles import Colors, Sizes


class SkillWindow:
    """技能倒數視窗"""
    
    def __init__(self, skill, player, position, skill_image, on_close, 
                 enable_sound, skill_id, is_permanent, start_at_zero=False):
        """初始化技能視窗
        
        Args:
            skill: 技能資料字典
            player: 玩家名稱
            position: 視窗位置 (x, y)
            skill_image: 技能圖片
            on_close: 關閉回調函數
            enable_sound: 是否啟用音效
            skill_id: 技能 ID
            is_permanent: 是否為常駐技能
            start_at_zero: 是否從 0 秒開始
        """
        self.skill = skill
        self.player = player
        self.on_close = on_close
        self.enable_sound = enable_sound
        self.skill_id = skill_id
        self.is_permanent = is_permanent
        self.running = True
        
        if start_at_zero:
            self.remaining = 0
            self.total = skill['cooldown']
        else:
            self.remaining = skill['cooldown']
            self.total = skill['cooldown']
        
        self._create_window(position, skill_image)
        
        if not start_at_zero:
            threading.Thread(target=self._countdown, daemon=True).start()
        else:
            self._update_display()
    
    def _create_window(self, position, skill_image):
        """創建視窗"""
        self.window = tk.Toplevel()
        self.window.title("")
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.95)
        self.window.overrideredirect(True)
        self.window.configure(bg=Colors.BG_DARK)
        
        # 容器
        container = tk.Frame(
            self.window, bg=Colors.BG_MEDIUM, 
            highlightbackground=Colors.ACCENT_BLUE, 
            highlightthickness=Sizes.BORDER_WIDTH
        )
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 技能名稱
        tk.Label(
            container, text=self.skill['name'], 
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_YELLOW,
            font=('Microsoft JhengHei', 8, 'bold')
        ).pack(pady=(3, 1))
        
        # 技能圖示
        if skill_image:
            img_label = tk.Label(container, image=skill_image, bg=Colors.BG_MEDIUM)
            img_label.image = skill_image
            img_label.pack(pady=2)
        
        # 倒數時間
        self.timer_label = tk.Label(
            container, text=f"{self.remaining}秒", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_PRIMARY,
            font=('Microsoft JhengHei', 18, 'bold')
        )
        self.timer_label.pack(pady=2)
        
        # 玩家名稱
        tk.Label(
            container, text=f"{self.player}", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_SECONDARY,
            font=('Microsoft JhengHei', 6)
        ).pack(pady=(0, 1))
        
        # 重置按鈕
        reset_btn = tk.Button(
            container,
            text="🔄 重置",
            bg=Colors.BG_DARK,
            fg=Colors.TEXT_SECONDARY,
            font=('Microsoft JhengHei', 6),
            relief=tk.FLAT,
            cursor='hand2',
            command=self.reset_countdown
        )
        reset_btn.pack(pady=(0, 3))
        
        # 設定位置
        self.window.geometry(
            f"{Sizes.SKILL_WINDOW_WIDTH}x{Sizes.SKILL_WINDOW_HEIGHT}"
            f"+{position[0]}+{position[1]}"
        )
    
    def restart_countdown(self):
        """重新開始倒數（用於常駐技能）"""
        if self.remaining == 0:
            self.remaining = self.total
            self.running = True
            threading.Thread(target=self._countdown, daemon=True).start()
    
    def reset_countdown(self):
        """重置倒數（重置到初始秒數）"""
        self.remaining = self.total
        self.running = True
        threading.Thread(target=self._countdown, daemon=True).start()
        self._update_display()
    
    def update_position(self, x, y):
        """更新視窗位置
        
        Args:
            x: X 座標
            y: Y 座標
        """
        try:
            self.window.geometry(
                f"{Sizes.SKILL_WINDOW_WIDTH}x{Sizes.SKILL_WINDOW_HEIGHT}+{x}+{y}"
            )
        except:
            pass
    
    def _countdown(self):
        """倒數計時"""
        while self.running and self.remaining > 0:
            time.sleep(1)
            self.remaining -= 1
            if self.running:
                try:
                    self._update_display()
                except:
                    break
        
        if self.running:
            if self.enable_sound:
                self._play_sound()
            
            if not self.is_permanent:
                time.sleep(2)
                self.close()
            else:
                self._update_display()
    
    def _update_display(self):
        """更新顯示"""
        if self.remaining > 0:
            self.timer_label.config(text=f"{self.remaining}秒", fg=Colors.TEXT_PRIMARY)
        else:
            self.timer_label.config(text="0秒", fg=Colors.ACCENT_GREEN)
    
    def _play_sound(self):
        """播放音效"""
        try:
            winsound.Beep(800, 300)
        except:
            pass
    
    def close(self):
        """關閉視窗"""
        self.running = False
        try:
            self.window.destroy()
        except:
            pass
        self.on_close(self)
