"""
技能倒數視窗模組
處理單個技能的倒數顯示視窗
"""

import tkinter as tk
import winsound
from src.ui.styles import Colors


class SkillWindow:
    """技能倒數視窗"""

    def __init__(
        self, skill, player, position, skill_image, on_close,
        enable_sound, skill_id, is_permanent, is_loop=False,
        start_at_zero=False, window_alpha=None,
        alert_enabled=False, alert_before_seconds=0, on_alert=None,  # 🆕 提前提示參數
        on_drag_start=None, on_drag_motion=None, on_drag_end=None  # 🔧 拖曳回調參數
    ):
        self.skill = skill
        self.player = player
        self.on_close = on_close
        self.enable_sound = enable_sound
        self.skill_id = skill_id
        self.is_permanent = is_permanent
        self.is_loop = is_loop
        self.skill_image = skill_image

        self.window_alpha = window_alpha if window_alpha is not None else 0.95

        # 🆕 提前提示設定
        self.alert_enabled = alert_enabled
        self.alert_before_seconds = alert_before_seconds
        self.on_alert = on_alert  # 回調函數
        self.alert_triggered = False  # 是否已觸發提示
        
        # 🔧 拖曳回調函數
        self.on_drag_start = on_drag_start
        self.on_drag_motion = on_drag_motion
        self.on_drag_end = on_drag_end

        self.total = skill["cooldown"]
        self.remaining = 0 if start_at_zero else self.total

        self.after_id = None
        self.running = False
        
        # 🔧 使用時間戳計時（更精確）
        self.start_time = None
        self.end_time = None

        self._create_window(position)

        if not start_at_zero:
            self.start_countdown()
        else:
            self._update_display()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def _create_window(self, position):
        from PIL import Image, ImageTk

        window_size = 64

        self.window = tk.Toplevel()
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", self.window_alpha)
        self.window.overrideredirect(True)
        self.window.configure(bg="black")

        self.canvas = tk.Canvas(
            self.window,
            width=window_size,
            height=window_size,
            bg="black",
            highlightthickness=0
        )
        self.canvas.pack()

        # 背景圖片
        if self.skill_image:
            try:
                self.bg_image = self.skill_image
            except:
                skill_img_pil = Image.new("RGB", (window_size, window_size), "black")
                mask = Image.new("L", (window_size, window_size), 255)
                output = Image.new("RGBA", (window_size, window_size))
                output.paste(skill_img_pil, (0, 0))
                output.putalpha(mask)
                self.bg_image = ImageTk.PhotoImage(output)
        else:
            skill_img_pil = Image.new("RGB", (window_size, window_size), "black")
            mask = Image.new("L", (window_size, window_size), 255)
            output = Image.new("RGBA", (window_size, window_size))
            output.paste(skill_img_pil, (0, 0))
            output.putalpha(mask)
            self.bg_image = ImageTk.PhotoImage(output)

        self.canvas.create_image(
            window_size // 2,
            window_size // 2,
            image=self.bg_image
        )

        # 倒數文字
        self.timer_text = self.canvas.create_text(
            window_size // 2,
            window_size // 2,
            text=str(self.remaining),
            fill="black",
            font=("Arial", 24, "bold"),
            anchor="center"
        )

        # 關閉按鈕
        border_size = 16
        padding = 2

        self.close_border = self.canvas.create_rectangle(
            window_size - border_size - padding,
            padding,
            window_size - padding,
            border_size + padding,
            outline="#FF0000",
            width=2
        )

        self.close_btn = self.canvas.create_text(
            window_size - border_size // 2 - padding,
            border_size // 2 + padding,
            text="✕",
            fill="#FF0000",
            font=("Arial", 12, "bold"),
            anchor="center"
        )

        for item in (self.close_border, self.close_btn):
            self.canvas.tag_bind(item, "<Button-1>", lambda e: self.close())
            self.canvas.tag_bind(
                item, "<Enter>",
                lambda e: self.canvas.itemconfig(self.close_border, outline="#FF6666")
            )
            self.canvas.tag_bind(
                item, "<Leave>",
                lambda e: self.canvas.itemconfig(self.close_border, outline="#FF0000")
            )

        self.window.geometry(f"+{position[0]}+{position[1]}")
        
        # 🔧 綁定拖曳事件到 canvas（排除關閉按鈕區域）
        self._bind_drag_events()

    # --------------------------------------------------
    # 🔧 拖曳事件
    # --------------------------------------------------
    def _bind_drag_events(self):
        """綁定拖曳事件"""
        # 綁定到整個視窗
        self.window.bind('<Button-1>', self._on_window_drag_start)
        self.window.bind('<B1-Motion>', self._on_window_drag_motion)
        self.window.bind('<ButtonRelease-1>', self._on_window_drag_end)
        
        # 綁定到 canvas（排除關閉按鈕）
        self.canvas.bind('<Button-1>', self._on_canvas_click)
        self.canvas.bind('<B1-Motion>', self._on_window_drag_motion)
        self.canvas.bind('<ButtonRelease-1>', self._on_window_drag_end)
        
        # 🔧 設定游標樣式
        self.canvas.bind('<Enter>', lambda e: self.canvas.config(cursor='hand2'))
        self.canvas.bind('<Leave>', lambda e: self.canvas.config(cursor=''))
        
        # 關閉按鈕區域要保持原來的游標
        for item in (self.close_border, self.close_btn):
            self.canvas.tag_bind(item, '<Enter>', 
                lambda e: self.canvas.config(cursor='hand2'))
    
    def _on_canvas_click(self, event):
        """Canvas 點擊事件（判斷是否點在關閉按鈕上）"""
        # 檢查是否點在關閉按鈕上
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        if self.close_border in items or self.close_btn in items:
            return  # 點在關閉按鈕上，不處理拖曳
        
        # 觸發拖曳開始
        self._on_window_drag_start(event)
    
    def _on_window_drag_start(self, event):
        """拖曳開始"""
        if self.on_drag_start:
            self.on_drag_start(event)
    
    def _on_window_drag_motion(self, event):
        """拖曳中"""
        if self.on_drag_motion:
            self.on_drag_motion(event)
    
    def _on_window_drag_end(self, event):
        """拖曳結束"""
        if self.on_drag_end:
            self.on_drag_end(event)

    # --------------------------------------------------
    # Countdown Logic
    # --------------------------------------------------
    def start_countdown(self):
        import time
        self.stop_countdown()
        self.running = True
        self.alert_triggered = False
        
        # 🔧 記錄開始和結束時間戳
        self.start_time = time.time()
        self.end_time = self.start_time + self.total
        
        self._update_display()
        self.after_id = self.window.after(100, self._tick)  # 🔧 100ms 更新一次（更流暢）

    def stop_countdown(self):
        self.running = False
        if self.after_id:
            self.window.after_cancel(self.after_id)
            self.after_id = None

    def reset_countdown(self):
        self.remaining = self.total
        self.alert_triggered = False
        self._update_display()
        self.start_countdown()

    def restart_countdown(self):
        self.reset_countdown()

    def _tick(self):
        import time
        import math
        if not self.running:
            return

        # 🔧 根據時間戳計算剩餘秒數（精確）
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # 🔧 向上取整：確保剩餘時間不會提前減少
        # 例如：total=150, elapsed=0.1 → remaining = ceil(149.9) = 150 ✅
        # 例如：total=150, elapsed=1.1 → remaining = ceil(148.9) = 149 ✅
        new_remaining = max(0, math.ceil(self.total - elapsed))
        
        # 🔧 只在秒數改變時才更新顯示
        if new_remaining != self.remaining:
            self.remaining = new_remaining
            self._update_display()
            
            # 檢查是否需要觸發提前提示
            if (self.alert_enabled and 
                not self.alert_triggered and 
                self.alert_before_seconds > 0 and 
                self.remaining <= self.alert_before_seconds):
                self._trigger_alert()
        
        if self.remaining > 0:
            # 🔧 繼續倒數（100ms 間隔檢查）
            self.after_id = self.window.after(100, self._tick)
        else:
            # 倒數結束
            self._on_finish()

    def _on_finish(self):
        # 如果設為 0 秒提示，在結束時才觸發
        if self.alert_enabled and not self.alert_triggered and self.alert_before_seconds == 0:
            self._trigger_alert()
        
        if self.enable_sound:
            self._play_sound()

        if self.is_loop:
            # 🔧 停止當前倒數
            self.running = False
            if self.after_id:
                self.window.after_cancel(self.after_id)
                self.after_id = None
            
            # 🔧 隨機延遲 50-500ms 再重新開始（分散負載）
            import random
            delay = random.randint(50, 500)
            self.window.after(delay, self._loop_restart)
        elif not self.is_permanent:
            self.after_id = self.window.after(2000, self.close)
        else:
            self._update_display()
    
    def _loop_restart(self):
        """循環重新開始（延遲執行避免卡頓）"""
        import time
        
        # 🔧 重要：開始時間要設為「現在」，而不是過去
        # 這樣第一次 _tick() 時 elapsed 接近 0，remaining 才會是完整秒數
        self.start_time = time.time()
        self.end_time = self.start_time + self.total
        
        # 🔧 設定剩餘秒數為完整值
        self.remaining = self.total
        self.alert_triggered = False
        
        # 🔧 先更新顯示（顯示完整秒數）
        self._update_display()
        
        # 🔧 然後才開始倒數（立即開始，不要延遲）
        self.running = True
        self._tick()  # 🔧 直接調用而不是 after，這樣時間戳更精確

    # 🆕 觸發提前提示
    def _trigger_alert(self):
        """觸發提前提示音和視窗"""
        self.alert_triggered = True
        
        # 播放提示音
        if self.enable_sound:
            try:
                # 使用不同音調區別提前提示和結束提示
                winsound.Beep(1000, 200)  # 較高音調，較短時間
            except:
                pass
        
        # 顯示提示視窗
        if self.on_alert:
            self.on_alert(self.skill['name'])

    # --------------------------------------------------
    # Utils
    # --------------------------------------------------
    def _update_display(self):
        if self.remaining > 0:
            self.canvas.itemconfig(
                self.timer_text,
                text=str(self.remaining),
                fill="black"
            )
        else:
            self.canvas.itemconfig(
                self.timer_text,
                text="0",
                fill="black"
            )

    def _play_sound(self):
        try:
            winsound.Beep(800, 300)
        except:
            pass

    def update_position(self, x, y):
        try:
            self.window.geometry(f"+{x}+{y}")
        except:
            pass

    def close(self):
        self.stop_countdown()
        try:
            self.window.destroy()
        except:
            pass
        self.on_close(self)