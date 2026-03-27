"""
覆蓋圖片管理器模組
管理所有浮動圖片視窗的生命週期、透明度與位置持久化
"""

import os
import shutil
import uuid

from src.infrastructure.helpers import user_data_path


class OverlayManager:
    """覆蓋圖片浮動視窗管理器

    負責：開啟/關閉視窗、更新透明度、持久化位置、新增/刪除覆蓋圖
    """

    _OVERLAYS_DIR = "overlays"

    def __init__(self, app):
        self.app = app
        self.active_windows: dict = {}   # overlay_id → OverlayWindow

        # 確保 overlays 目錄存在
        os.makedirs(user_data_path(self._OVERLAYS_DIR), exist_ok=True)

        # 確保 config 有 "overlays" key
        if "overlays" not in app.config_manager.config:
            app.config_manager.config["overlays"] = []

    # --------------------------------------------------
    # 視窗開關
    # --------------------------------------------------
    def toggle(self, overlay_id: str):
        """切換覆蓋圖片視窗的顯示狀態"""
        if overlay_id in self.active_windows:
            self.close_window(overlay_id)
        else:
            self.open_window(overlay_id)

    def open_window(self, overlay_id: str):
        """開啟指定 ID 的覆蓋圖片視窗"""
        if overlay_id in self.active_windows:
            return

        data = self._get_data(overlay_id)
        if not data:
            return

        image_path = user_data_path(f"{self._OVERLAYS_DIR}/{data['file']}")
        if not os.path.exists(image_path):
            return

        from src.ui.overlay_window import OverlayWindow

        win = OverlayWindow(
            overlay_id=overlay_id,
            image_path=image_path,
            alpha=data.get("alpha", 0.9),
            position=(data.get("x", 100), data.get("y", 100)),
            on_close=self._on_window_close,
            on_position_change=self._on_position_change,
            on_size_change=self._on_size_change,
            width=data.get("width"),
            height=data.get("height"),
        )
        self.active_windows[overlay_id] = win

    def close_window(self, overlay_id: str):
        """關閉指定 ID 的覆蓋圖片視窗"""
        win = self.active_windows.get(overlay_id)
        if win:
            win.close()

    def close_all(self):
        """關閉所有覆蓋圖片視窗"""
        for oid in list(self.active_windows.keys()):
            self.close_window(oid)

    # --------------------------------------------------
    # 參數更新
    # --------------------------------------------------
    def set_alpha(self, overlay_id: str, alpha: float):
        """即時更新指定覆蓋圖的透明度並儲存設定

        Args:
            overlay_id: 覆蓋圖 ID
            alpha:      0.1 ~ 1.0
        """
        win = self.active_windows.get(overlay_id)
        if win:
            win.set_alpha(alpha)

        data = self._get_data(overlay_id)
        if data:
            data["alpha"] = round(alpha, 2)
            self.app.config_manager.save()

    def resize_window(self, overlay_id: str, w: int, h: int):
        """調整覆蓋圖片的顯示尺寸並持久化

        若視窗目前為開啟狀態，先記錄位置再關閉，50ms 後以新尺寸重新開啟

        Args:
            overlay_id: 覆蓋圖 ID
            w:          新寬度（px），最小 10
            h:          新高度（px），最小 10
        """
        w = max(10, w)
        h = max(10, h)

        data = self._get_data(overlay_id)
        if data:
            # 若視窗開啟中，先保存當前位置
            win = self.active_windows.get(overlay_id)
            if win:
                try:
                    data["x"] = win.x()
                    data["y"] = win.y()
                except Exception:
                    pass
            data["width"] = w
            data["height"] = h
            self.app.config_manager.save()

        was_open = overlay_id in self.active_windows
        if was_open:
            self.close_window(overlay_id)

            def _reopen():
                self.open_window(overlay_id)
                # 同步更新 toggle 按鈕為「顯示中」
                try:
                    self.app.overlay_page.refresh_toggle(overlay_id)
                except Exception:
                    pass

            self.app.after(50, _reopen)

    # --------------------------------------------------
    # 新增 / 刪除
    # --------------------------------------------------
    def add_overlay(self, src_path: str, name: str) -> dict | None:
        """新增一個覆蓋圖片項目

        將檔案複製到 overlays/ 目錄，並寫入 config

        Args:
            src_path: 使用者選擇的原始檔案路徑
            name:     顯示名稱

        Returns:
            新增的 overlay 資料字典，失敗則回傳 None
        """
        ext = os.path.splitext(src_path)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"):
            return None

        # 以 uuid 命名避免衝突
        filename = f"{uuid.uuid4().hex[:8]}{ext}"
        dest = user_data_path(f"{self._OVERLAYS_DIR}/{filename}")
        try:
            shutil.copy2(src_path, dest)
        except Exception:
            return None

        # 計算圖片初始顯示尺寸（最長邊不超過 600px）
        try:
            from PIL import Image
            with Image.open(dest) as img:
                ow, oh = img.size
            max_dim = 600
            scale = min(1.0, max_dim / max(ow, oh))
            init_w = max(1, int(ow * scale))
            init_h = max(1, int(oh * scale))
        except Exception:
            init_w, init_h = 200, 200

        # 螢幕中央作為預設位置
        try:
            from PySide6.QtWidgets import QApplication
            geo = QApplication.primaryScreen().geometry()
            screen_w = geo.width()
            screen_h = geo.height()
        except Exception:
            screen_w, screen_h = 1920, 1080

        item = {
            "id":     f"ov_{uuid.uuid4().hex[:12]}",
            "name":   name or os.path.splitext(os.path.basename(src_path))[0],
            "file":   filename,
            "alpha":  0.9,
            "x":      screen_w // 2,
            "y":      screen_h // 2,
            "width":  init_w,
            "height": init_h,
        }
        self.app.config_manager.config["overlays"].append(item)
        self.app.config_manager.save()
        return item

    def delete_overlay(self, overlay_id: str, delete_file: bool = False):
        """刪除覆蓋圖片項目

        Args:
            overlay_id:  要刪除的 ID
            delete_file: 是否同時刪除磁碟上的圖片檔案
        """
        # 先關閉視窗
        self.close_window(overlay_id)

        data = self._get_data(overlay_id)
        if data and delete_file:
            try:
                file_path = user_data_path(f"{self._OVERLAYS_DIR}/{data['file']}")
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

        overlays = self.app.config_manager.config.get("overlays", [])
        self.app.config_manager.config["overlays"] = [
            o for o in overlays if o["id"] != overlay_id
        ]
        self.app.config_manager.save()

    def get_all(self) -> list:
        """取得所有覆蓋圖片資料列表"""
        return self.app.config_manager.config.get("overlays", [])

    # --------------------------------------------------
    # 回調
    # --------------------------------------------------
    def _on_window_close(self, overlay_id: str):
        """視窗被 X 按鈕關閉時的回調"""
        self.active_windows.pop(overlay_id, None)
        # 通知頁面更新 toggle 按鈕狀態
        try:
            self.app.overlay_page.refresh_toggle(overlay_id)
        except Exception:
            pass

    def _on_position_change(self, overlay_id: str, x: int, y: int):
        """拖曳結束時持久化位置"""
        data = self._get_data(overlay_id)
        if data:
            data["x"] = x
            data["y"] = y
            self.app.config_manager.save()

    def _on_size_change(self, overlay_id: str, w: int, h: int):
        """方向鍵調整尺寸後持久化"""
        data = self._get_data(overlay_id)
        if data:
            data["width"]  = w
            data["height"] = h
            self.app.config_manager.save()

    # --------------------------------------------------
    # 工具
    # --------------------------------------------------
    def _get_data(self, overlay_id: str) -> dict | None:
        """根據 ID 取得 overlay 資料字典（O(n)，列表通常很短）"""
        for item in self.app.config_manager.config.get("overlays", []):
            if item["id"] == overlay_id:
                return item
        return None
