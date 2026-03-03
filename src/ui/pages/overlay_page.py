"""
畫面覆蓋圖片管理頁面
以卡片列表管理浮動圖片視窗（支援靜態圖片與 GIF）
每張卡片可獨立開關、調整透明度；使用者可自行上傳圖片
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from src.ui.theme import AppTheme

# 支援的圖片格式
_SUPPORTED_EXTS = (
    ("圖片與 GIF", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
    ("所有檔案", "*.*"),
)
_MAX_THUMB = 80   # 縮圖最大邊長（px）


def _make_thumb(image_path: str) -> "ctk.CTkImage | None":
    """從圖片路徑產生縮圖 CTkImage

    GIF 只取第一幀；失敗則回傳 None

    Args:
        image_path: 圖片絕對路徑

    Returns:
        CTkImage 或 None
    """
    try:
        img = Image.open(image_path)
        img.seek(0)               # GIF → 第一幀
        img = img.convert("RGBA")
        ow, oh = img.size
        scale = min(1.0, _MAX_THUMB / max(ow, oh))
        tw = max(1, int(ow * scale))
        th = max(1, int(oh * scale))
        img = img.resize((tw, th), Image.Resampling.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=(tw, th))
    except Exception:
        return None


class _OverlayCard(ctk.CTkFrame):
    """單張覆蓋圖片卡片

    顯示縮圖、名稱、開關按鈕、透明度滑桿、刪除按鈕
    """

    _CARD_H = 138

    def __init__(self, parent, data: dict, app, page):
        super().__init__(
            parent,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.BG_CARD,
            border_width=1,
            border_color=AppTheme.BORDER_GOLD_SUBTLE,
            height=self._CARD_H,
        )
        self.pack_propagate(False)
        self.data = data
        self.app = app
        self.page = page
        self.overlay_id = data["id"]

        self._build_ui()

    def _build_ui(self):
        """建構卡片 UI"""
        # ── 左側縮圖 ──
        from src.ui.overlay_manager import _user_path
        img_path = _user_path(f"overlays/{self.data['file']}")
        thumb = _make_thumb(img_path)

        thumb_frame = ctk.CTkFrame(
            self,
            width=_MAX_THUMB + 10,
            fg_color=AppTheme.BG_SECONDARY,
            corner_radius=AppTheme.CORNER_SM,
        )
        thumb_frame.pack(side="left", fill="y", padx=(8, 0), pady=8)
        thumb_frame.pack_propagate(False)

        if thumb:
            ctk.CTkLabel(
                thumb_frame, text="", image=thumb,
            ).pack(expand=True)
        else:
            ctk.CTkLabel(
                thumb_frame, text="🖼️",
                font=("Arial", 28),
                text_color=AppTheme.TEXT_MUTED,
            ).pack(expand=True)

        # ── 右側內容 ──
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        # 名稱
        ctk.CTkLabel(
            right,
            text=self.data.get("name", "未命名"),
            font=AppTheme.FONT_BODY_MD_BOLD,
            text_color=AppTheme.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x")

        # 副標（檔名）
        ctk.CTkLabel(
            right,
            text=self.data.get("file", ""),
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x")

        # ── 控制列 ──
        ctrl = ctk.CTkFrame(right, fg_color="transparent")
        ctrl.pack(fill="x", pady=(4, 0))

        # 開關按鈕
        is_open = self.overlay_id in self.app.overlay_manager.active_windows
        self._toggle_btn = ctk.CTkButton(
            ctrl,
            text="● 顯示中" if is_open else "○ 已隱藏",
            command=self._toggle,
            width=82, height=26,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.ACCENT_GREEN if is_open else AppTheme.BG_TERTIARY,
            hover_color=(
                AppTheme.ACCENT_GREEN if is_open else AppTheme.BG_CARD_HOVER
            ),
            font=AppTheme.FONT_BTN_SM,
        )
        self._toggle_btn.pack(side="left", padx=(0, 8))

        # 透明度滑桿 + 標籤
        alpha_val = self.data.get("alpha", 0.9)
        self._alpha_var = tk.DoubleVar(value=alpha_val)

        ctk.CTkLabel(
            ctrl, text="透明度",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(side="left")

        self._alpha_slider = ctk.CTkSlider(
            ctrl,
            variable=self._alpha_var,
            from_=0.1, to=1.0,
            number_of_steps=18,
            width=110,
            fg_color=AppTheme.BG_TERTIARY,
            progress_color=AppTheme.GOLD_PRIMARY,
            button_color=AppTheme.GOLD_LIGHT,
            button_hover_color=AppTheme.GOLD_LIGHT,
            command=self._on_alpha,
        )
        self._alpha_slider.pack(side="left", padx=(4, 4))

        self._alpha_lbl = ctk.CTkLabel(
            ctrl,
            text=f"{int(alpha_val * 100)}%",
            font=("Consolas", 10),
            text_color=AppTheme.TEXT_GOLD,
            width=32,
            anchor="w",
        )
        self._alpha_lbl.pack(side="left")

        # 刪除按鈕
        ctk.CTkButton(
            ctrl,
            text="🗑",
            command=self._delete,
            width=30, height=26,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.ACCENT_RED,
            font=AppTheme.FONT_BODY_MD,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(side="right", padx=(4, 0))

        # ── 尺寸控制列 ──
        size_row = ctk.CTkFrame(right, fg_color="transparent")
        size_row.pack(fill="x", pady=(2, 0))

        # 初始長寬與比例
        init_w = self.data.get("width", 200) or 200
        init_h = self.data.get("height", 200) or 200
        self._aspect = init_w / init_h if init_h else 1.0
        self._updating_ratio = False

        # 寬度輸入
        ctk.CTkLabel(
            size_row, text="寬",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(side="left")
        self._w_var = tk.StringVar(value=str(init_w))
        ctk.CTkEntry(
            size_row, textvariable=self._w_var,
            width=58, height=24,
            font=AppTheme.FONT_BODY_SM,
            fg_color=AppTheme.BG_TERTIARY,
            border_color=AppTheme.BORDER_GOLD_SUBTLE,
            text_color=AppTheme.TEXT_PRIMARY,
        ).pack(side="left", padx=(2, 6))

        # 高度輸入
        ctk.CTkLabel(
            size_row, text="高",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(side="left")
        self._h_var = tk.StringVar(value=str(init_h))
        ctk.CTkEntry(
            size_row, textvariable=self._h_var,
            width=58, height=24,
            font=AppTheme.FONT_BODY_SM,
            fg_color=AppTheme.BG_TERTIARY,
            border_color=AppTheme.BORDER_GOLD_SUBTLE,
            text_color=AppTheme.TEXT_PRIMARY,
        ).pack(side="left", padx=(2, 6))

        # 鎖定比例核取框
        self._lock_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            size_row,
            text="🔒",
            variable=self._lock_var,
            width=44, height=24,
            checkbox_width=14, checkbox_height=14,
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
            fg_color=AppTheme.GOLD_PRIMARY,
            hover_color=AppTheme.GOLD_MUTED,
            border_color=AppTheme.BORDER_GOLD_SUBTLE,
        ).pack(side="left", padx=(0, 6))

        # 套用按鈕
        ctk.CTkButton(
            size_row,
            text="套用",
            command=self._apply_size,
            width=48, height=24,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.GOLD_PRIMARY,
            hover_color=AppTheme.GOLD_LIGHT,
            text_color=AppTheme.BG_DEEP,
            font=AppTheme.FONT_BTN_SM,
        ).pack(side="left")

        # 綁定比例連動事件
        self._w_var.trace_add("write", self._on_w_changed)
        self._h_var.trace_add("write", self._on_h_changed)

    # --------------------------------------------------
    # 事件
    # --------------------------------------------------
    def _toggle(self):
        """開關浮動視窗"""
        self.app.overlay_manager.toggle(self.overlay_id)
        self._sync_toggle()

    def _on_alpha(self, val):
        """透明度滑桿變動"""
        alpha = float(val)
        self._alpha_lbl.configure(text=f"{int(alpha * 100)}%")
        self.app.overlay_manager.set_alpha(self.overlay_id, alpha)

    def _delete(self):
        """刪除此覆蓋圖片"""
        name = self.data.get("name", "此圖片")
        if not messagebox.askyesno(
            "刪除確認",
            f"確定要刪除「{name}」嗎？\n（僅移除設定，不刪除圖片檔案）",
            parent=self.app,
        ):
            return
        self.app.overlay_manager.delete_overlay(self.overlay_id, delete_file=False)
        self.page.rebuild_cards()

    def _on_w_changed(self, *_):
        """寬度輸入變動時，若鎖定比例則同步更新高度"""
        if self._updating_ratio or not self._lock_var.get():
            return
        try:
            w = int(self._w_var.get())
            if w > 0 and self._aspect > 0:
                self._updating_ratio = True
                self._h_var.set(str(max(1, round(w / self._aspect))))
                self._updating_ratio = False
        except (ValueError, ZeroDivisionError):
            pass

    def _on_h_changed(self, *_):
        """高度輸入變動時，若鎖定比例則同步更新寬度"""
        if self._updating_ratio or not self._lock_var.get():
            return
        try:
            h = int(self._h_var.get())
            if h > 0 and self._aspect > 0:
                self._updating_ratio = True
                self._w_var.set(str(max(1, round(h * self._aspect))))
                self._updating_ratio = False
        except (ValueError, ZeroDivisionError):
            pass

    def _apply_size(self):
        """套用新的寬高至覆蓋視窗"""
        try:
            w = max(10, int(self._w_var.get()))
            h = max(10, int(self._h_var.get()))
        except ValueError:
            return
        # 套用後更新本地比例記錄
        self.data["width"] = w
        self.data["height"] = h
        self._aspect = w / h if h else 1.0
        self.app.overlay_manager.resize_window(self.overlay_id, w, h)

    # --------------------------------------------------
    # 公開方法
    # --------------------------------------------------
    def sync_toggle_state(self):
        """從外部同步 toggle 按鈕狀態（如：X 按鈕關閉視窗後呼叫）"""
        self._sync_toggle()

    def _sync_toggle(self):
        """根據 active_windows 更新 toggle 按鈕外觀"""
        is_open = self.overlay_id in self.app.overlay_manager.active_windows
        self._toggle_btn.configure(
            text="● 顯示中" if is_open else "○ 已隱藏",
            fg_color=AppTheme.ACCENT_GREEN if is_open else AppTheme.BG_TERTIARY,
            hover_color=(
                AppTheme.ACCENT_GREEN if is_open else AppTheme.BG_CARD_HOVER
            ),
        )


class OverlayPage(ctk.CTkFrame):
    """畫面覆蓋圖片管理頁面"""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._cards: dict[str, _OverlayCard] = {}  # overlay_id → card
        self._build_ui()

    # --------------------------------------------------
    # UI 建構
    # --------------------------------------------------
    def _build_ui(self):
        """建構頁面頂部標題與可捲動卡片區"""
        # ── 頂部標題列 ──
        hdr_outer = ctk.CTkFrame(
            self,
            corner_radius=AppTheme.CORNER_LG,
            fg_color=AppTheme.GOLD_PRIMARY,
            height=56,
        )
        hdr_outer.pack(fill="x", padx=10, pady=(10, 6))
        hdr_outer.pack_propagate(False)

        hdr_inner = ctk.CTkFrame(
            hdr_outer,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.BG_CARD,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        )
        hdr_inner.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(
            hdr_inner,
            text="🖼️ 畫面覆蓋圖片",
            font=AppTheme.FONT_TITLE_MD,
            text_color=AppTheme.TEXT_GOLD,
        ).pack(side="left", padx=16)

        ctk.CTkLabel(
            hdr_inner,
            text="支援 PNG / JPG / GIF（動畫）  |  拖曳移動  |  hover 顯示 X 關閉",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(side="left")

        # 新增按鈕（放右側）
        ctk.CTkButton(
            hdr_inner,
            text="＋ 新增圖片",
            command=self._add_image,
            width=110, height=34,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.GOLD_PRIMARY,
            hover_color=AppTheme.GOLD_LIGHT,
            text_color=AppTheme.BG_DEEP,
            font=AppTheme.FONT_BTN,
            border_width=1,
            border_color=AppTheme.GOLD_DARK,
        ).pack(side="right", padx=12)

        # ── 可捲動卡片區 ──
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=AppTheme.GOLD_MUTED,
            scrollbar_button_hover_color=AppTheme.GOLD_PRIMARY,
        )
        self._scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._scroll.columnconfigure(0, weight=1)

        # 空白提示（無圖片時顯示）
        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="尚未新增任何圖片\n點擊「＋ 新增圖片」上傳 PNG / JPG / GIF",
            font=AppTheme.FONT_BODY_LG,
            text_color=AppTheme.TEXT_MUTED,
            justify="center",
        )

        self.rebuild_cards()

    # --------------------------------------------------
    # 卡片管理
    # --------------------------------------------------
    def rebuild_cards(self):
        """清除並重建所有覆蓋圖片卡片"""
        # 清除現有卡片與空白提示
        for widget in self._scroll.winfo_children():
            widget.destroy()
        self._cards.clear()

        overlays = self.app.overlay_manager.get_all()

        if not overlays:
            # 顯示空白提示
            empty = ctk.CTkLabel(
                self._scroll,
                text="尚未新增任何圖片\n點擊「＋ 新增圖片」上傳 PNG / JPG / GIF",
                font=AppTheme.FONT_BODY_LG,
                text_color=AppTheme.TEXT_MUTED,
                justify="center",
            )
            empty.grid(row=0, column=0, pady=80)
            return

        for row, data in enumerate(overlays):
            card = _OverlayCard(self._scroll, data, self.app, self)
            card.grid(row=row, column=0, sticky="ew", padx=4, pady=4)
            self._cards[data["id"]] = card

    # --------------------------------------------------
    # 動作
    # --------------------------------------------------
    def _add_image(self):
        """開啟檔案選擇對話框，上傳圖片"""
        path = filedialog.askopenfilename(
            title="選擇圖片或 GIF",
            filetypes=_SUPPORTED_EXTS,
            parent=self.app,
        )
        if not path:
            return

        name = os.path.splitext(os.path.basename(path))[0]
        item = self.app.overlay_manager.add_overlay(path, name)
        if item is None:
            messagebox.showerror(
                "上傳失敗",
                "不支援的圖片格式或檔案複製失敗，請確認檔案格式。",
                parent=self.app,
            )
            return

        self.rebuild_cards()

    # --------------------------------------------------
    # 公開 API（供 OverlayManager 回調呼叫）
    # --------------------------------------------------
    def refresh_toggle(self, overlay_id: str):
        """視窗被 X 關閉時，更新對應卡片的 toggle 按鈕狀態

        Args:
            overlay_id: 被關閉視窗的 overlay ID
        """
        card = self._cards.get(overlay_id)
        if card:
            card.sync_toggle_state()
