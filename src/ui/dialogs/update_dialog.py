"""
更新下載對話框
顯示下載進度條，完成後啟動替換腳本並關閉應用
RPG 金色邊框風格
"""

import os
import sys
import subprocess
import threading
import customtkinter as ctk
from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme


class UpdateDialog(BaseDialog):
    """更新下載對話框"""

    def __init__(self, parent, update_info):
        super().__init__(parent, "版本更新", 440, 280)
        self.update_info = update_info
        self.parent_app = parent
        self._downloading = False
        self._cancelled = False
        self._build_ui()

    def _build_ui(self):
        """建構 UI"""
        container = self.inner

        # 標題
        ctk.CTkLabel(
            container,
            text="🔄 發現新版本",
            font=AppTheme.FONT_TITLE_MD,
            text_color=AppTheme.TEXT_GOLD,
        ).pack(pady=(16, 8))

        # 版本資訊
        current = self.update_info.get("current", "?")
        latest = self.update_info.get("latest", "?")

        ctk.CTkLabel(
            container,
            text=f"v{current}  →  v{latest}",
            font=AppTheme.FONT_BODY_LG_BOLD,
            text_color=AppTheme.GOLD_LIGHT,
        ).pack(pady=(0, 16))

        # 進度條 — 金色調
        self.progress_bar = ctk.CTkProgressBar(
            container,
            width=360,
            height=16,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_CARD,
            progress_color=AppTheme.GOLD_PRIMARY,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(0, 8))

        # 狀態文字
        self.status_label = ctk.CTkLabel(
            container,
            text="點擊「開始更新」下載並安裝",
            font=AppTheme.FONT_BODY_MD,
            text_color=AppTheme.TEXT_SECONDARY,
        )
        self.status_label.pack(pady=(0, 16))

        # 按鈕列
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=(0, 16))

        self.download_btn = ctk.CTkButton(
            btn_frame,
            text="⬇ 開始更新",
            command=self._start_download,
            width=140,
            height=40,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.GOLD_PRIMARY,
            hover_color=AppTheme.GOLD_LIGHT,
            text_color=AppTheme.BG_DEEP,
            font=AppTheme.FONT_BTN,
            border_width=1,
            border_color=AppTheme.GOLD_DARK,
        )
        self.download_btn.pack(side="left", padx=(0, 12))

        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            command=self._on_cancel,
            width=100,
            height=40,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.BG_CARD,
            hover_color=AppTheme.BG_CARD_HOVER,
            font=AppTheme.FONT_BTN,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        )
        self.cancel_btn.pack(side="left")

        # 手動下載連結
        ctk.CTkButton(
            container,
            text="📎 手動下載頁面",
            command=self._open_download_page,
            width=140,
            height=28,
            corner_radius=AppTheme.CORNER_SM,
            fg_color="transparent",
            hover_color=AppTheme.BG_CARD_HOVER,
            text_color=AppTheme.GOLD_MUTED,
            font=AppTheme.FONT_BODY_SM,
        ).pack(pady=(0, 8))

    def _start_download(self):
        """開始下載更新"""
        url = self.update_info.get("download_url")

        # 備用：download_url 未帶回時，依版本號組合已知下載路徑
        if not url:
            latest = self.update_info.get("latest", "")
            if latest:
                url = (
                    f"https://github.com/asd23353934/skill_tracker"
                    f"/releases/download/{latest}/default.7z"
                )

        if not url:
            self.status_label.configure(
                text="找不到下載連結，請手動下載",
                text_color=AppTheme.ACCENT_RED,
            )
            return

        # 確保 update_info 裡的 download_url 也一併補齊，供 _download_thread 使用
        self.update_info["download_url"] = url

        self._downloading = True
        self._cancelled = False
        self.download_btn.configure(state="disabled", text="下載中...")
        self.status_label.configure(
            text="正在下載...",
            text_color=AppTheme.TEXT_SECONDARY,
        )

        # 在背景執行緒中下載
        thread = threading.Thread(target=self._download_thread, daemon=True)
        thread.start()

    def _download_thread(self):
        """背景下載執行緒"""
        from src.ui.updater import Updater

        updater = Updater()
        updater.download_url = self.update_info.get("download_url")
        dest_path = updater.get_update_temp_path()

        success = updater.download_update(
            self.update_info["download_url"],
            dest_path,
            progress_callback=self._on_progress,
        )

        if self._cancelled:
            # 使用者取消，清理檔案
            try:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
            except Exception:
                pass
            return

        # 回到主執行緒更新 UI
        if success:
            self.after(0, lambda: self._on_download_complete(dest_path))
        else:
            self.after(0, self._on_download_failed)

    def _on_progress(self, downloaded, total):
        """下載進度回調（在背景執行緒中呼叫）

        Args:
            downloaded: 已下載位元組數
            total: 總位元組數
        """
        if self._cancelled:
            return

        if total > 0:
            progress = downloaded / total
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            text = f"下載中... {mb_downloaded:.1f} / {mb_total:.1f} MB ({progress * 100:.0f}%)"
        else:
            mb_downloaded = downloaded / (1024 * 1024)
            progress = 0
            text = f"下載中... {mb_downloaded:.1f} MB"

        # 排程至主執行緒更新 UI
        self.after(0, lambda p=progress, t=text: self._update_progress(p, t))

    def _update_progress(self, progress, text):
        """更新進度條 UI（主執行緒）

        Args:
            progress: 進度值 0.0 ~ 1.0
            text: 狀態文字
        """
        try:
            self.progress_bar.set(min(progress, 1.0))
            self.status_label.configure(text=text)
        except Exception:
            pass

    def _on_download_complete(self, file_path):
        """下載完成處理

        Args:
            file_path: 下載檔案的路徑
        """
        self._downloading = False
        self.progress_bar.set(1.0)
        self.status_label.configure(
            text="下載完成！正在啟動更新...",
            text_color=AppTheme.ACCENT_GREEN,
        )
        self.download_btn.configure(text="✓ 下載完成")

        # 延遲 1 秒後啟動更新腳本
        self.after(1000, lambda: self._launch_updater(file_path))

    def _on_download_failed(self):
        """下載失敗處理"""
        self._downloading = False
        self.progress_bar.set(0)
        self.status_label.configure(
            text="下載失敗，請手動下載或稍後再試",
            text_color=AppTheme.ACCENT_RED,
        )
        self.download_btn.configure(state="normal", text="⬇ 重試下載")

    def _launch_updater(self, downloaded_file):
        """啟動更新替換腳本並關閉應用

        Args:
            downloaded_file: 已下載的更新檔案路徑
        """
        try:
            from src.ui.helpers import resource_path

            # 取得當前應用程式路徑
            if getattr(sys, 'frozen', False):
                # PyInstaller 打包模式
                app_dir = os.path.dirname(sys.executable)
                app_exe = sys.executable
            else:
                # 開發模式
                app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                app_exe = sys.executable

            launcher = resource_path("update_launcher.bat")

            if not os.path.exists(launcher):
                self.status_label.configure(
                    text="找不到更新腳本，請手動更新",
                    text_color=AppTheme.ACCENT_RED,
                )
                return

            # 啟動替換腳本: update_launcher.bat <downloaded_file> <app_dir> <app_exe>
            # 隱藏 cmd 視窗，不讓使用者看到黑色終端機
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0  # SW_HIDE
            subprocess.Popen(
                [launcher, downloaded_file, app_dir, app_exe],
                startupinfo=si,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
            )

            # 關閉應用
            self.status_label.configure(text="應用程式即將關閉...")
            self.after(500, self._shutdown_app)

        except Exception as e:
            self.status_label.configure(
                text=f"啟動更新失敗: {e}",
                text_color=AppTheme.ACCENT_RED,
            )

    def _shutdown_app(self):
        """關閉整個應用程式"""
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass

        try:
            self.parent_app.destroy()
        except Exception:
            pass

        sys.exit(0)

    def _on_cancel(self):
        """取消下載或關閉對話框"""
        if self._downloading:
            self._cancelled = True
            self._downloading = False
            self.status_label.configure(
                text="已取消下載",
                text_color=AppTheme.TEXT_MUTED,
            )
            self.download_btn.configure(state="normal", text="⬇ 重新下載")
        else:
            self.close()

    def _open_download_page(self):
        """打開手動下載頁面"""
        import webbrowser
        webbrowser.open(
            "https://github.com/asd23353934/skill_tracker/releases/latest"
        )

    def close(self):
        """關閉對話框"""
        if self._downloading:
            self._cancelled = True
        super().close()
