"""
覆蓋圖片浮動視窗模組
在畫面上顯示靜態圖片或動態 GIF，支援拖曳移動、透明度調整
hover 才顯示 X 關閉按鈕，視窗背景全透明
"""

import tkinter as tk


class OverlayWindow:
    """覆蓋圖片浮動視窗

    支援 PNG / JPG / GIF（含動畫）；全透明背景，hover 才顯示 X 按鈕
    """

    # 關閉按鈕尺寸
    _CLOSE_R = 10   # 圓形半徑（px）
    _TRANSPARENT = "#010101"

    def __init__(
        self,
        overlay_id: str,
        image_path: str,
        alpha: float,
        position: tuple,
        on_close,
        on_position_change,
        width: int = None,
        height: int = None,
    ):
        """
        Args:
            overlay_id:          覆蓋圖唯一 ID
            image_path:          圖片絕對路徑
            alpha:               視窗透明度 0.1-1.0
            position:            (x, y) 螢幕座標
            on_close:            callback(overlay_id) 視窗關閉時呼叫
            on_position_change:  callback(overlay_id, x, y) 拖曳結束時呼叫
            width:               指定顯示寬度（px），None 則自動計算
            height:              指定顯示高度（px），None 則自動計算
        """
        self.overlay_id = overlay_id
        self.on_close = on_close
        self.on_position_change = on_position_change

        # GIF 動畫狀態
        self._frames: list = []
        self._delays: list = []
        self._frame_idx = 0
        self._anim_id = None

        # 拖曳暫存
        self._drag_x = 0
        self._drag_y = 0
        self._clicking_close = False

        self._load_image(image_path, width, height)
        self._create_window(alpha, position)

    # --------------------------------------------------
    # 圖片載入
    # --------------------------------------------------
    def _load_image(self, path: str, target_w: int = None, target_h: int = None):
        """載入圖片（靜態或 GIF 動畫）並預先產生 PhotoImage

        若指定 target_w / target_h 則使用該尺寸；否則最長邊超過 600px 時等比縮小

        Args:
            path:     圖片絕對路徑
            target_w: 目標寬度（px），None 則自動
            target_h: 目標高度（px），None 則自動
        """
        from PIL import Image, ImageTk, ImageSequence

        with Image.open(path) as src:
            is_gif = src.format == "GIF"

            # 計算顯示尺寸
            ow, oh = src.size
            if target_w and target_h:
                self.img_w = max(1, target_w)
                self.img_h = max(1, target_h)
            else:
                max_dim = 600
                scale = min(1.0, max_dim / max(ow, oh))
                self.img_w = max(1, int(ow * scale))
                self.img_h = max(1, int(oh * scale))
            size = (self.img_w, self.img_h)

            if is_gif:
                # 逐幀載入（copy 後再處理，避免 seek 競爭）
                raw_frames = []
                raw_delays = []
                for frame in ImageSequence.Iterator(src):
                    raw_frames.append(frame.copy())
                    raw_delays.append(max(frame.info.get("duration", 100), 30))

                for frame, delay in zip(raw_frames, raw_delays):
                    f = frame.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                    self._frames.append(ImageTk.PhotoImage(f))
                    self._delays.append(delay)
            else:
                f = src.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                self._frames.append(ImageTk.PhotoImage(f))
                self._delays.append(0)

    # --------------------------------------------------
    # 視窗建立
    # --------------------------------------------------
    def _create_window(self, alpha: float, position: tuple):
        """建立 Toplevel 並繪製 Canvas"""
        tc = self._TRANSPARENT

        self.window = tk.Toplevel()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", max(0.1, min(1.0, alpha)))
        self.window.configure(bg=tc)
        try:
            self.window.attributes("-transparentcolor", tc)
        except Exception:
            pass

        w = self.img_w
        h = self.img_h

        self.canvas = tk.Canvas(
            self.window,
            width=w, height=h,
            bg=tc,
            highlightthickness=0,
        )
        self.canvas.pack()

        # 圖片
        self._img_item = self.canvas.create_image(
            0, 0, image=self._frames[0], anchor="nw"
        )

        # ── X 關閉按鈕（預設隱藏）──
        # 右上角圓形背景 + 文字
        r = self._CLOSE_R
        cx = w - r - 4
        cy = r + 4

        self._close_bg = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill="#cc2222", outline="#ff5555", width=1,
            state="hidden", tags="close",
        )
        self._close_text = self.canvas.create_text(
            cx, cy,
            text="✕", fill="#ffffff",
            font=("Arial", 9, "bold"),
            state="hidden", tags="close",
        )

        # 綁定事件
        self.canvas.bind("<Enter>",          lambda e: self._show_close())
        self.canvas.bind("<Leave>",          lambda e: self._hide_close())
        self.canvas.bind("<Button-1>",       self._on_press)
        self.canvas.bind("<B1-Motion>",      self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        self.window.geometry(f"+{position[0]}+{position[1]}")

        # 啟動 GIF 動畫
        if len(self._frames) > 1:
            self._animate()

    # --------------------------------------------------
    # 動畫
    # --------------------------------------------------
    def _animate(self):
        """GIF 動畫 tick（每幀根據 delay 排程下一幀）"""
        if not self._frames or len(self._frames) <= 1:
            return
        self._frame_idx = (self._frame_idx + 1) % len(self._frames)
        try:
            self.canvas.itemconfig(
                self._img_item, image=self._frames[self._frame_idx]
            )
            self._anim_id = self.window.after(
                self._delays[self._frame_idx], self._animate
            )
        except Exception:
            pass

    # --------------------------------------------------
    # Hover（X 按鈕顯示/隱藏）
    # --------------------------------------------------
    def _show_close(self):
        """顯示 X 關閉按鈕"""
        try:
            self.canvas.itemconfig(self._close_bg,  state="normal")
            self.canvas.itemconfig(self._close_text, state="normal")
        except Exception:
            pass

    def _hide_close(self):
        """隱藏 X 關閉按鈕"""
        try:
            self.canvas.itemconfig(self._close_bg,  state="hidden")
            self.canvas.itemconfig(self._close_text, state="hidden")
        except Exception:
            pass

    # --------------------------------------------------
    # 拖曳
    # --------------------------------------------------
    def _on_press(self, event):
        """判斷點擊目標：X 按鈕 or 拖曳起點"""
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        if self._close_bg in items or self._close_text in items:
            self._clicking_close = True
        else:
            self._clicking_close = False
            self._drag_x = event.x_root - self.window.winfo_x()
            self._drag_y = event.y_root - self.window.winfo_y()

    def _on_drag(self, event):
        """拖曳移動視窗"""
        if self._clicking_close:
            return
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.window.geometry(f"+{x}+{y}")

    def _on_release(self, event):
        """拖曳結束：若在 X 上則關閉，否則儲存位置"""
        if self._clicking_close:
            items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            if self._close_bg in items or self._close_text in items:
                self.close()
            self._clicking_close = False
            return

        if self.on_position_change:
            try:
                self.on_position_change(
                    self.overlay_id,
                    self.window.winfo_x(),
                    self.window.winfo_y(),
                )
            except Exception:
                pass

    # --------------------------------------------------
    # 公開 API
    # --------------------------------------------------
    def set_alpha(self, alpha: float):
        """即時更新視窗透明度

        Args:
            alpha: 0.1 ~ 1.0
        """
        try:
            self.window.attributes("-alpha", max(0.1, min(1.0, alpha)))
        except Exception:
            pass

    def update_position(self, x: int, y: int):
        """更新視窗位置"""
        try:
            self.window.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def close(self):
        """關閉視窗並觸發 on_close 回調"""
        if self._anim_id:
            try:
                self.window.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None
        try:
            self.window.destroy()
        except Exception:
            pass
        if self.on_close:
            self.on_close(self.overlay_id)
