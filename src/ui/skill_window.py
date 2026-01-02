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
        start_at_zero=False, window_alpha=None
    ):
        self.skill = skill
        self.player = player
        self.on_close = on_close
        self.enable_sound = enable_sound
        self.skill_id = skill_id
        self.is_permanent = is_permanent
        self.is_loop = is_loop
        self.skill_image = skill_image  # 儲存傳入的圖片

        self.window_alpha = window_alpha if window_alpha is not None else 0.95

        self.total = skill["cooldown"]
        self.remaining = 0 if start_at_zero else self.total

        self.after_id = None
        self.running = False

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

        # ---------- 背景圖片（使用傳入的 skill_image）----------
        if self.skill_image:
            # 如果傳入的是 PhotoImage，直接使用
            # 如果需要調整大小，可以在外部處理好再傳入
            try:
                # 嘗試將 PhotoImage 轉換為 PIL Image 以便處理
                # 這裡假設外部已經處理好圖片大小
                self.bg_image = self.skill_image
            except:
                # 如果轉換失敗，創建默認圖片
                skill_img_pil = Image.new("RGB", (window_size, window_size), "black")
                mask = Image.new("L", (window_size, window_size), 255)
                output = Image.new("RGBA", (window_size, window_size))
                output.paste(skill_img_pil, (0, 0))
                output.putalpha(mask)
                self.bg_image = ImageTk.PhotoImage(output)
        else:
            # 如果沒有圖片，創建默認黑色背景
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

        # ---------- 倒數文字（黑色） ----------
        self.timer_text = self.canvas.create_text(
            window_size // 2,
            window_size // 2,
            text=str(self.remaining),
            fill="black",
            font=("Arial", 24, "bold"),
            anchor="center"
        )

        # ---------- 關閉 X 紅色邊框 ----------
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

    # --------------------------------------------------
    # Countdown Logic (NO THREADING)
    # --------------------------------------------------
    def start_countdown(self):
        self.stop_countdown()
        self.running = True
        self._update_display()
        self.after_id = self.window.after(1000, self._tick)

    def stop_countdown(self):
        self.running = False
        if self.after_id:
            self.window.after_cancel(self.after_id)
            self.after_id = None

    def reset_countdown(self):
        self.remaining = self.total
        self._update_display()
        self.start_countdown()

    def restart_countdown(self):
        self.reset_countdown()

    def _tick(self):
        if not self.running:
            return

        if self.remaining > 0:
            self.remaining -= 1
            self._update_display()

            if self.remaining > 0:
                self.after_id = self.window.after(1000, self._tick)
            else:
                self._on_finish()

    def _on_finish(self):
        if self.enable_sound:
            self._play_sound()

        if self.is_loop:
            self.remaining = self.total
            self._update_display()
            self.after_id = self.window.after(1000, self._tick)
        elif not self.is_permanent:
            self.after_id = self.window.after(2000, self.close)
        else:
            self._update_display()

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