"""
更新下載對話框 — PySide6 版本
顯示下載進度條，完成後啟動替換腳本並關閉應用
RPG 金色邊框風格
"""

import os
import sys
import subprocess
import threading

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QWidget, QApplication,
)
from PySide6.QtCore import Qt, QTimer, Signal
from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme


class UpdateDialog(BaseDialog):
    """更新下載對話框"""

    # Qt signals — 供背景執行緒安全回到主執行緒更新 UI
    _progress_signal = Signal(float, str)
    _complete_signal = Signal(str)
    _failed_signal   = Signal()

    def __init__(self, parent, update_info):
        super().__init__(parent, "版本更新", 440, 280)
        self.update_info = update_info
        self.parent_app  = parent
        self._downloading = False
        self._cancelled   = False
        self._lock        = threading.Lock()  # 保護 _cancelled / _downloading 跨執行緒存取

        # 連接 signals → slots
        self._progress_signal.connect(self._update_progress)
        self._complete_signal.connect(self._on_download_complete)
        self._failed_signal.connect(self._on_download_failed)

        self._build_ui()

    def _build_ui(self):
        """建構 UI"""
        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # 標題
        title_lbl = QLabel("🔄 發現新版本")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 16px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(title_lbl)

        # 版本資訊
        current = self.update_info.get("current", "?")
        latest  = self.update_info.get("latest", "?")
        ver_lbl = QLabel(f"v{current}  →  v{latest}")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT}; font-size: 14px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(ver_lbl)

        # 進度條（金色調）
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background-color: {AppTheme.BG_CARD};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_SM}px; }}"
            f"QProgressBar::chunk {{ background-color: {AppTheme.GOLD_PRIMARY};"
            f" border-radius: {AppTheme.CORNER_SM}px; }}"
        )
        layout.addWidget(self.progress_bar)

        # 狀態文字
        self.status_label = QLabel("點擊「開始更新」下載並安裝")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 12px;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(self.status_label)

        # 按鈕列
        btn_row = QWidget()
        btn_row.setStyleSheet("background: transparent;")
        br = QHBoxLayout(btn_row)
        br.setContentsMargins(0, 0, 0, 0)
        br.setSpacing(12)
        br.addStretch()

        self.download_btn = QPushButton("⬇ 開始更新")
        self.download_btn.setFixedSize(140, 40)
        self.download_btn.clicked.connect(self._start_download)
        self.download_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.GOLD_PRIMARY};"
            f" color: {AppTheme.BG_DEEP}; border: 1px solid {AppTheme.GOLD_DARK};"
            f" border-radius: {AppTheme.CORNER_MD}px;"
            f" font-size: 12px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.GOLD_LIGHT}; }}"
            f"QPushButton:disabled {{ background-color: {AppTheme.GOLD_MUTED}; color: #888; }}"
        )
        br.addWidget(self.download_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(100, 40)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.BG_CARD};"
            f" color: {AppTheme.TEXT_PRIMARY}; border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_MD}px; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.BG_CARD_HOVER}; }}"
        )
        br.addWidget(self.cancel_btn)
        br.addStretch()
        layout.addWidget(btn_row)

        # 手動下載連結
        manual_btn = QPushButton("📎 手動下載頁面")
        manual_btn.setFixedHeight(28)
        manual_btn.clicked.connect(self._open_download_page)
        manual_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent;"
            f" color: {AppTheme.GOLD_MUTED}; border: none; font-size: 11px; }}"
            f"QPushButton:hover {{ color: {AppTheme.GOLD_PRIMARY}; }}"
        )
        layout.addWidget(manual_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

    # --------------------------------------------------
    # 下載邏輯
    # --------------------------------------------------

    def _start_download(self):
        """開始下載更新"""
        url = self.update_info.get("download_url")

        # 備用：依版本號組合下載路徑
        if not url:
            latest = self.update_info.get("latest", "")
            if latest:
                url = (
                    f"https://github.com/asd23353934/skill_tracker"
                    f"/releases/download/v{latest}"
                    f"/skill_tracker_v{latest}.zip"
                )
        if not url:
            self._set_status("找不到下載連結，請手動下載", AppTheme.ACCENT_RED)
            return

        self.update_info["download_url"] = url
        with self._lock:
            self._downloading = True
            self._cancelled   = False
        self.download_btn.setEnabled(False)
        self.download_btn.setText("下載中...")
        self._set_status("正在下載...", AppTheme.TEXT_SECONDARY)

        threading.Thread(target=self._download_thread, daemon=True).start()

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

        with self._lock:
            cancelled = self._cancelled

        if cancelled:
            try:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
            except Exception:
                pass
            return

        if success:
            self._complete_signal.emit(dest_path)
        else:
            self._failed_signal.emit()

    def _on_progress(self, downloaded, total):
        """下載進度回調（背景執行緒中呼叫）"""
        with self._lock:
            cancelled = self._cancelled
        if cancelled:
            return
        if total > 0:
            progress  = downloaded / total
            mb_dl     = downloaded / (1024 * 1024)
            mb_tot    = total / (1024 * 1024)
            text = f"下載中... {mb_dl:.1f} / {mb_tot:.1f} MB ({progress * 100:.0f}%)"
        else:
            progress  = 0
            mb_dl     = downloaded / (1024 * 1024)
            text = f"下載中... {mb_dl:.1f} MB"
        self._progress_signal.emit(progress, text)

    # --------------------------------------------------
    # UI 更新（主執行緒）
    # --------------------------------------------------

    def _update_progress(self, progress: float, text: str):
        """更新進度條 UI（主執行緒）"""
        try:
            self.progress_bar.setValue(int(min(progress, 1.0) * 100))
            self.status_label.setText(text)
        except Exception:
            pass

    def _on_download_complete(self, file_path: str):
        """下載完成處理"""
        self._downloading = False
        self.progress_bar.setValue(100)
        self._set_status("下載完成！正在啟動更新...", AppTheme.ACCENT_GREEN)
        self.download_btn.setText("✓ 下載完成")
        QTimer.singleShot(1000, lambda: self._launch_updater(file_path))

    def _on_download_failed(self):
        """下載失敗處理"""
        self._downloading = False
        self.progress_bar.setValue(0)
        self._set_status("下載失敗，請手動下載或稍後再試", AppTheme.ACCENT_RED)
        self.download_btn.setEnabled(True)
        self.download_btn.setText("⬇ 重試下載")

    def _set_status(self, text: str, color: str):
        """更新狀態文字顏色"""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 12px; background: transparent; border: none;"
        )

    # --------------------------------------------------
    # 更新啟動 / 關閉
    # --------------------------------------------------

    def _launch_updater(self, downloaded_file: str):
        """啟動更新替換腳本並關閉應用"""
        try:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

            pid = str(os.getpid())
            launched = False

            # 優先用 PowerShell 執行 ps1
            ps1_launcher = os.path.join(app_dir, "update_launcher.ps1")
            if os.path.exists(ps1_launcher):
                try:
                    subprocess.Popen(
                        [
                            'powershell.exe',
                            '-NoProfile',
                            '-WindowStyle', 'Hidden',
                            '-ExecutionPolicy', 'Bypass',
                            '-File', ps1_launcher,
                            '-DownloadFile', downloaded_file,
                            '-AppDir', app_dir,
                            '-AppExe', sys.executable,
                            '-AppPid', pid,
                        ],
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
                    )
                    launched = True
                except Exception as e:
                    print(f"[update] ps1 launch failed: {e}", flush=True)

            # Fallback: .bat
            if not launched:
                bat_launcher = os.path.join(app_dir, "update_launcher.bat")
                if os.path.exists(bat_launcher):
                    try:
                        subprocess.Popen(
                            [bat_launcher, downloaded_file, app_dir,
                             sys.executable, pid],
                            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
                        )
                        launched = True
                    except Exception as e:
                        print(f"[update] bat launch failed: {e}", flush=True)

            if not launched:
                self._set_status("找不到更新腳本，請手動更新", AppTheme.ACCENT_RED)
                return

            self.status_label.setText("應用程式即將關閉...")
            QTimer.singleShot(500, self._shutdown_app)

        except Exception as e:
            self._set_status(f"啟動更新失敗: {e}", AppTheme.ACCENT_RED)

    def _shutdown_app(self):
        """關閉整個應用程式"""
        try:
            self.reject()
        except Exception:
            pass
        try:
            self.parent_app.close()
        except Exception:
            pass
        QApplication.quit()
        sys.exit(0)

    def _on_cancel(self):
        """取消下載或關閉對話框"""
        with self._lock:
            was_downloading   = self._downloading
            self._cancelled   = True
            self._downloading = False
        if was_downloading:
            self._set_status("已取消下載", AppTheme.TEXT_MUTED)
            self.download_btn.setEnabled(True)
            self.download_btn.setText("⬇ 重新下載")
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
        with self._lock:
            if self._downloading:
                self._cancelled = True
        super().close()
