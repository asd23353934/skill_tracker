"""
技能倒數視窗模組
處理單個技能的倒數顯示視窗，含灰色順時針遮罩與快秒顯示
RPG 金色邊框 + 金色倒數文字風格
"""

import tkinter as tk
import time
import math

from src.ui.theme import AppTheme


class SkillWindow:
    """技能倒數視窗"""

    # 金色調常量（Canvas 繪製用，不經 AppTheme 因為是原生 tkinter）
    GOLD_BORDER = "#d4a843"
    GOLD_BORDER_INNER = "#8b7435"
    GOLD_TEXT = "#f0d78c"
    GOLD_OUTLINE = "#8b7435"
    GOLD_CLOSE = "#d4a843"
    GOLD_CLOSE_HOVER = "#f0d78c"
    GOLD_FLASH = "#f0d78c"

    def __init__(
        self, skill, player, position, skill_image, on_close,
        enable_sound, skill_id, is_permanent, is_loop=False,
        start_at_zero=False, window_alpha=None,
        alert_enabled=False, alert_before_seconds=0, on_alert=None,
        on_drag_start=None, on_drag_motion=None, on_drag_end=None,
        window_size=64,
        skill_image_path=None,
        sound_manager=None,
        sound_filename="",
        alert_sound_filename="",
        count_up=False,
        title=None,
        idle_start=False,
    ):
        self.skill = skill
        self.player = player
        self.on_close = on_close
        self.enable_sound = enable_sound
        self.skill_id = skill_id
        self.is_permanent = is_permanent
        self.is_loop = is_loop
        self.skill_image = skill_image
        self._skill_image_path = skill_image_path
        self.count_up = count_up
        self.title = title
        self.idle_start = idle_start

        self.window_alpha = window_alpha if window_alpha is not None else 0.95
        self.window_size = window_size

        # 提前提示設定
        self.alert_enabled = alert_enabled
        self.alert_before_seconds = alert_before_seconds
        self.on_alert = on_alert
        self.alert_triggered = False

        # 音效設定
        self.sound_manager = sound_manager
        self.sound_filename = sound_filename
        self.alert_sound_filename = alert_sound_filename

        # 拖曳回調函數
        self.on_drag_start = on_drag_start
        self.on_drag_motion = on_drag_motion
        self.on_drag_end = on_drag_end

        self.total = skill.get("cooldown") or skill.get("respawn_time", 0)
        self.remaining = 0 if (start_at_zero or count_up) else self.total

        self.after_id = None
        self.running = False

        # 使用時間戳計時（更精確）
        self.start_time = None
        self.end_time = None

        # PIL 基底圖片（用於遮罩合成）
        self._base_pil_image = None
        self._overlay_photo = None
        self._image_item = None
        self._last_overlay_degree = -1

        # 閃爍狀態
        self._flash_count = 0
        self._flash_after_id = None

        self._create_window(position)

        if count_up:
            # 正數模式：idle_start=True 時停留 idle，等待按鍵觸發
            if not idle_start:
                self.start_countdown()
        elif not start_at_zero:
            self.start_countdown()
        else:
            self._update_display()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def _create_window(self, position):
        """建立倒數視窗 — RPG 金色邊框風格"""
        from PIL import Image, ImageTk

        window_size = self.window_size
        border_w = 2  # 外層金色邊框寬度
        inner_border_w = 1  # 內層暗金邊框寬度

        self.window = tk.Toplevel()
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", self.window_alpha)
        self.window.overrideredirect(True)

        # Windows 透明背景設定
        transparent_color = '#010101'
        self.window.configure(bg=transparent_color)
        try:
            self.window.attributes('-transparentcolor', transparent_color)
        except Exception:
            pass

        # 計算各區塊高度與計時文字位置
        # 兩種模式都是：秒數文字在上，圖示在下
        # count_up（怪物）用 0.5 係數讓文字有足夠空間，避免頂端被裁切
        if self.count_up:
            text_height = int(window_size * 0.5)            # 比技能略高，留足頂部空間
            title_height = 0
            img_y0 = text_height                            # 秒數在上，圖示在下
            img_y1 = text_height + window_size + border_w * 2
            text_y = text_height // 2
        else:
            title_height = max(18, int(window_size * 0.28)) if self.title else 0
            text_height = int(window_size * 0.4)
            img_y0 = text_height + title_height             # 文字在圖示上方
            img_y1 = text_height + title_height + window_size + border_w * 2
            text_y = text_height // 2

        total_height = text_height + title_height + window_size + border_w * 2

        canvas_width = window_size + border_w * 2

        self.canvas = tk.Canvas(
            self.window,
            width=canvas_width,
            height=total_height,
            bg=transparent_color,
            highlightthickness=0
        )
        self.canvas.pack()

        # ===== 標題文字（技能模式，緊貼卡片上方置中；count_up 不顯示）=====
        if self.title and not self.count_up:
            title_font_size = max(9, int(window_size * 0.17))
            title_x = canvas_width // 2
            title_y = text_height + title_height // 2
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1),
                           (0, -1), (0, 1),
                           (1, -1), (1, 0), (1, 1)]:
                self.canvas.create_text(
                    title_x + dx,
                    title_y + dy,
                    text=self.title,
                    fill=self.GOLD_OUTLINE,
                    font=("Arial", title_font_size, "bold"),
                    anchor="center",
                    tags="title_outline"
                )
            self.canvas.create_text(
                title_x,
                title_y,
                text=self.title,
                fill=self.GOLD_TEXT,
                font=("Arial", title_font_size, "bold"),
                anchor="center",
                tags="title_text"
            )

        # ===== 金色邊框 (圖片區域) =====
        img_x0 = 0
        img_x1 = canvas_width

        # 外層金色邊框
        self._border_outer = self.canvas.create_rectangle(
            img_x0, img_y0, img_x1, img_y1,
            outline=self.GOLD_BORDER,
            width=border_w,
            tags="gold_border"
        )

        # 內層暗金邊框
        self.canvas.create_rectangle(
            img_x0 + border_w, img_y0 + border_w,
            img_x1 - border_w, img_y1 - border_w,
            outline=self.GOLD_BORDER_INNER,
            width=inner_border_w,
            tags="gold_border"
        )

        # ===== 載入並縮放技能圖片 =====
        if self._skill_image_path:
            try:
                img = Image.open(self._skill_image_path).convert("RGBA")
                img = img.resize((window_size, window_size), Image.Resampling.LANCZOS)
                self._base_pil_image = img
                self.bg_image = ImageTk.PhotoImage(img)
            except Exception:
                img = Image.new("RGBA", (window_size, window_size), (128, 128, 128, 255))
                self._base_pil_image = img
                self.bg_image = ImageTk.PhotoImage(img)
        else:
            img = Image.new("RGBA", (window_size, window_size), (128, 128, 128, 255))
            self._base_pil_image = img
            self.bg_image = ImageTk.PhotoImage(img)

        # 圖片放在邊框內
        self._image_item = self.canvas.create_image(
            canvas_width // 2,
            img_y0 + border_w + window_size // 2,
            image=self.bg_image
        )

        # ===== 計時文字（技能倒數 / 怪物正數 均顯示）=====
        # count_up 初始為 "0"，countdown 初始為剩餘秒數
        font_size = max(18, int(window_size * 0.4))
        text_x = canvas_width // 2
        initial_text = "0" if self.count_up else str(self.remaining)

        offset = 2
        for dx, dy in [(-offset, -offset), (-offset, 0), (-offset, offset),
                       (0, -offset), (0, offset),
                       (offset, -offset), (offset, 0), (offset, offset)]:
            self.canvas.create_text(
                text_x + dx,
                text_y + dy,
                text=initial_text,
                fill=self.GOLD_OUTLINE,
                font=("Arial", font_size, "bold"),
                anchor="center",
                tags="timer_outline"
            )

        self.timer_text = self.canvas.create_text(
            text_x,
            text_y,
            text=initial_text,
            fill=self.GOLD_TEXT,
            font=("Arial", font_size, "bold"),
            anchor="center"
        )

        # ===== 關閉按鈕（金色調）=====
        close_size = 16
        padding = 2
        close_x0 = canvas_width - close_size - padding - border_w
        close_y0 = img_y0 + padding + border_w
        close_x1 = canvas_width - padding - border_w
        close_y1 = img_y0 + close_size + padding + border_w

        self.close_border = self.canvas.create_rectangle(
            close_x0, close_y0, close_x1, close_y1,
            outline=self.GOLD_CLOSE,
            width=2
        )

        self.close_btn = self.canvas.create_text(
            (close_x0 + close_x1) // 2,
            (close_y0 + close_y1) // 2,
            text="✕",
            fill=self.GOLD_CLOSE,
            font=("Arial", 12, "bold"),
            anchor="center"
        )

        for item in (self.close_border, self.close_btn):
            self.canvas.tag_bind(item, "<Button-1>", lambda e: self.close())
            self.canvas.tag_bind(
                item, "<Enter>",
                lambda e: (
                    self.canvas.itemconfig(self.close_border, outline=self.GOLD_CLOSE_HOVER),
                    self.canvas.itemconfig(self.close_btn, fill=self.GOLD_CLOSE_HOVER),
                )
            )
            self.canvas.tag_bind(
                item, "<Leave>",
                lambda e: (
                    self.canvas.itemconfig(self.close_border, outline=self.GOLD_CLOSE),
                    self.canvas.itemconfig(self.close_btn, fill=self.GOLD_CLOSE),
                )
            )

        self.window.geometry(f"+{position[0]}+{position[1]}")

        # 綁定拖曳事件
        self._bind_drag_events()

    # --------------------------------------------------
    # 金色邊框閃爍（提前提示觸發時）
    # --------------------------------------------------
    def _flash_border(self):
        """短暫閃爍金色邊框 — 亮金 ↔ 原金切換"""
        if self._flash_count >= 6:
            # 復原邊框
            self.canvas.itemconfig(self._border_outer, outline=self.GOLD_BORDER)
            self._flash_count = 0
            self._flash_after_id = None
            return

        # 切換亮金/原金
        if self._flash_count % 2 == 0:
            self.canvas.itemconfig(self._border_outer, outline=self.GOLD_FLASH)
        else:
            self.canvas.itemconfig(self._border_outer, outline=self.GOLD_BORDER)

        self._flash_count += 1
        self._flash_after_id = self.window.after(120, self._flash_border)

    # --------------------------------------------------
    # 灰色矩形遮罩（從下往上填滿）
    # --------------------------------------------------
    def _create_overlay_image(self, progress):
        """建立帶有灰色矩形遮罩的技能圖片

        遮罩從底部向上填滿，progress=0 無遮罩，progress=1 全部遮蔽。

        Args:
            progress: 進度 0.0 ~ 1.0 (0=剛開始, 1=時間結束)

        Returns:
            ImageTk.PhotoImage 合成後的圖片
        """
        from PIL import Image, ImageDraw, ImageTk

        if self._base_pil_image is None:
            return None

        base = self._base_pil_image.copy()

        if progress <= 0:
            return ImageTk.PhotoImage(base)

        # 建立半透明灰色遮罩
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        w, h = base.size
        # 矩形從底部向上覆蓋
        fill_h = int(min(progress, 1.0) * h)
        if fill_h > 0:
            draw.rectangle([0, h - fill_h, w, h], fill=AppTheme.OVERLAY_COLOR)

        # 合成
        result = Image.alpha_composite(base, overlay)
        return ImageTk.PhotoImage(result)

    def _update_overlay(self, progress):
        """更新遮罩圖片（僅在像素高度變化時更新以優化效能）"""
        pixel_h = int(progress * self.window_size)
        if pixel_h == self._last_overlay_degree:
            return

        self._last_overlay_degree = pixel_h
        new_photo = self._create_overlay_image(progress)
        if new_photo:
            self._overlay_photo = new_photo  # 防止 GC 回收
            self.canvas.itemconfig(self._image_item, image=self._overlay_photo)

    # --------------------------------------------------
    # 拖曳事件
    # --------------------------------------------------
    def _bind_drag_events(self):
        """綁定拖曳事件"""
        self.window.bind('<Button-1>', self._on_window_drag_start)
        self.window.bind('<B1-Motion>', self._on_window_drag_motion)
        self.window.bind('<ButtonRelease-1>', self._on_window_drag_end)

        self.canvas.bind('<Button-1>', self._on_canvas_click)
        self.canvas.bind('<B1-Motion>', self._on_window_drag_motion)
        self.canvas.bind('<ButtonRelease-1>', self._on_window_drag_end)

        self.canvas.bind('<Enter>', lambda e: self.canvas.config(cursor='hand2'))
        self.canvas.bind('<Leave>', lambda e: self.canvas.config(cursor=''))

        for item in (self.close_border, self.close_btn):
            self.canvas.tag_bind(item, '<Enter>',
                lambda e: self.canvas.config(cursor='hand2'))

    def _on_canvas_click(self, event):
        """Canvas 點擊事件（判斷是否點在關閉按鈕上）"""
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        if self.close_border in items or self.close_btn in items:
            return
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
        """開始倒數"""
        self.stop_countdown()
        self.running = True
        self.alert_triggered = False

        self.start_time = time.time()
        self.end_time = self.start_time + self.total

        self._update_display()
        self._update_overlay(0)
        self.after_id = self.window.after(100, self._tick)

    def stop_countdown(self):
        """停止倒數"""
        self.running = False
        if self.after_id:
            self.window.after_cancel(self.after_id)
            self.after_id = None

    def reset_countdown(self):
        """重置並重新開始倒數"""
        self.remaining = self.total
        self.alert_triggered = False
        self._last_overlay_degree = -1
        self._update_display()
        self.start_countdown()

    def restart_countdown(self):
        """重新開始倒數"""
        self.reset_countdown()

    def _tick(self):
        """計時器 tick（每 100ms 或 50ms 呼叫一次）"""
        if not self.running:
            return

        current_time = time.time()
        elapsed = current_time - self.start_time

        if self.count_up:
            self._tick_count_up(elapsed)
        else:
            self._tick_count_down(elapsed)

    def _tick_count_up(self, elapsed):
        """正數模式 tick — 從 0 數到目標"""
        elapsed_sec = int(elapsed)

        # 計算遮罩進度（從 0 到 1）
        progress = min(1.0, elapsed / self.total) if self.total > 0 else 1.0
        self._update_overlay(progress)

        # 提前提示：剩餘秒數 <= alert_before_seconds
        remaining_to_target = self.total - elapsed_sec
        if (self.alert_enabled and not self.alert_triggered and
                self.alert_before_seconds > 0 and
                0 < remaining_to_target <= self.alert_before_seconds):
            self._trigger_alert()

        if elapsed >= self.total:
            # 到達目標
            self.remaining = self.total
            self._update_display_text(str(self.total))
            self._update_overlay(1.0)
            self._on_finish()
        else:
            # 更新顯示
            if elapsed_sec != self.remaining:
                self.remaining = elapsed_sec
                self._update_display_text(str(self.remaining))

            self.after_id = self.window.after(100, self._tick)

    def _tick_count_down(self, elapsed):
        """倒數模式 tick — 從目標數到 0"""
        raw_remaining = self.total - elapsed

        # 計算遮罩進度
        progress = min(1.0, elapsed / self.total) if self.total > 0 else 1.0
        self._update_overlay(progress)

        # 快秒顯示：<1 秒時顯示小數
        if 0 < raw_remaining < 1.0:
            text = f"{raw_remaining:.1f}"
            self._update_display_text(text)

            # 檢查提前提示
            new_remaining = max(0, math.ceil(raw_remaining))
            if new_remaining != self.remaining:
                self.remaining = new_remaining
                self._check_alert()

            # 更快的 tick 間隔使快秒動畫更流暢
            self.after_id = self.window.after(50, self._tick)
        elif raw_remaining <= 0:
            # 倒數結束
            self.remaining = 0
            self._update_display_text("0")
            self._update_overlay(1.0)
            self._on_finish()
        else:
            # 正常秒數顯示
            new_remaining = max(0, math.ceil(raw_remaining))
            if new_remaining != self.remaining:
                self.remaining = new_remaining
                self._update_display()
                self._check_alert()

            self.after_id = self.window.after(100, self._tick)

    def _check_alert(self):
        """檢查是否需要觸發提前提示"""
        if (self.alert_enabled and
            not self.alert_triggered and
            self.alert_before_seconds > 0 and
            self.remaining <= self.alert_before_seconds):
            self._trigger_alert()

    def _on_finish(self):
        """倒數結束處理"""
        # 如果設為 0 秒提示，在結束時才觸發
        if self.alert_enabled and not self.alert_triggered and self.alert_before_seconds == 0:
            self._trigger_alert()

        if self.enable_sound:
            self._play_sound()

        if self.is_loop:
            self.running = False
            if self.after_id:
                self.window.after_cancel(self.after_id)
                self.after_id = None

            import random
            delay = random.randint(50, 500)
            self.window.after(delay, self._loop_restart)
        elif self.is_permanent and self.count_up:
            # 常駐怪物：時間到後重置為 idle（遮罩清空，秒數歸零，等待下次按鍵）
            self.running = False
            self.remaining = 0
            self._last_overlay_degree = -1
            self._update_overlay(0)
            self._update_display_text("0")
        elif self.count_up:
            # 非常駐怪物：時間到後停留在畫面上（遮罩全滿），不自動關閉
            self.running = False
        elif not self.is_permanent:
            self.after_id = self.window.after(2000, self.close)
        else:
            self._update_display()
            # 常駐技能結束時重置遮罩
            self._last_overlay_degree = -1
            self._update_overlay(0)

    def _loop_restart(self):
        """循環重新開始"""
        self.start_time = time.time()
        self.end_time = self.start_time + self.total

        # count_up：elapsed 從 0 開始；countdown：remaining 從 total 開始
        self.remaining = 0 if self.count_up else self.total
        self.alert_triggered = False
        self._last_overlay_degree = -1

        self._update_display()
        self._update_overlay(0)

        self.running = True
        self._tick()

    # --------------------------------------------------
    # 提前提示
    # --------------------------------------------------
    def _trigger_alert(self):
        """觸發提前提示音和視窗"""
        self.alert_triggered = True

        # 觸發邊框閃爍效果
        self._flash_count = 0
        self._flash_border()

        if self.enable_sound and self.sound_manager and self.alert_sound_filename:
            self.sound_manager.play_alert(self.alert_sound_filename)

        if self.on_alert:
            self.on_alert(self.skill['name'])

    # --------------------------------------------------
    # Utils
    # --------------------------------------------------
    def _update_display(self):
        """更新倒數秒數顯示"""
        text = "0" if self.remaining <= 0 else str(self.remaining)
        self._update_display_text(text)

    def _update_display_text(self, text):
        """更新所有顯示文字（count_up 模式無文字元件，直接略過）"""
        if self.timer_text is None:
            return
        for item in self.canvas.find_withtag("timer_outline"):
            self.canvas.itemconfig(item, text=text)
        self.canvas.itemconfig(self.timer_text, text=text, fill=self.GOLD_TEXT)

    def _play_sound(self):
        """播放完成音效"""
        if self.sound_manager and self.sound_filename:
            self.sound_manager.play(self.sound_filename)

    def update_position(self, x, y):
        """更新視窗位置"""
        try:
            self.window.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def close(self):
        """關閉視窗"""
        self.stop_countdown()
        # 取消閃爍動畫
        if self._flash_after_id:
            try:
                self.window.after_cancel(self._flash_after_id)
            except Exception:
                pass
            self._flash_after_id = None
        try:
            self.window.destroy()
        except Exception:
            pass
        self.on_close(self)
