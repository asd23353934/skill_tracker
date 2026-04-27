"""
V2 更新下載對話框
顯示版本資訊、下載進度，完成後啟動替換腳本並關閉應用。
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser

from PySide6.QtWidgets import QPushButton, QProgressBar, QApplication
from PySide6.QtCore import Qt, QTimer, Signal

from src.infrastructure.helpers import user_data_path
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.dialogs.base_dialog_v2 import BaseDialogV2


_PROGRESS_EMIT_INTERVAL = 0.1   # 進度回呼節流：最少 100ms 才 emit 一次
_PROGRESS_EMIT_DELTA    = 0.005 # 或進度變化 ≥ 0.5%


class UpdateDialog(BaseDialogV2):
    """V2 更新下載對話框

    建構參數沿用 V1 簽名：(parent, update_info)，方便沿用上層呼叫。
    """

    _progress_signal = Signal(float, str)
    _complete_signal = Signal(str)
    _failed_signal   = Signal()

    def __init__(self, parent, update_info):
        super().__init__(parent, title="版本更新", width=440, height=260)
        self.update_info  = update_info
        self.parent_app   = parent
        self._downloading = False
        self._cancelled   = False
        self._lock        = threading.Lock()
        self._last_emit_t = 0.0
        self._last_emit_p = -1.0

        self._progress_signal.connect(self._update_progress)
        self._complete_signal.connect(self._on_download_complete)
        self._failed_signal.connect(self._on_download_failed)

        self._build_body()
        self._build_footer()

    def _build_body(self):
        L = self.body_layout()

        current = self.update_info.get("current", "?")
        latest  = self.update_info.get("latest", "?")
        ver_lbl = T.make_label(f"v{current}  →  v{latest}", T.FONT_DISPLAY)
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        L.addWidget(ver_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px; }}"
            f"QProgressBar::chunk {{ background: {T.ORANGE};"
            f" border-radius: {T.R_SM}px; }}"
        )
        L.addWidget(self.progress_bar)

        self.status_label = T.make_label("點擊「開始更新」下載並安裝", T.FONT_CAPTION)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        L.addWidget(self.status_label)
        L.addStretch()

    def _build_footer(self):
        F = self.footer_layout()

        manual = QPushButton("手動下載")
        manual.setProperty("kind", "ghost")
        manual.setCursor(Qt.CursorShape.PointingHandCursor)
        manual.setFixedHeight(T.BTN_H)
        manual.clicked.connect(self._open_download_page)
        F.insertWidget(0, manual)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setProperty("kind", "ghost")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setFixedHeight(T.BTN_H)
        self.cancel_btn.clicked.connect(self._on_cancel)
        F.addWidget(self.cancel_btn)

        self.download_btn = QPushButton("開始更新")
        self.download_btn.setProperty("kind", "primary")
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.setFixedHeight(T.BTN_H)
        self.download_btn.clicked.connect(self._start_download)
        F.addWidget(self.download_btn)

    def _start_download(self):
        url = self.update_info.get("download_url")
        if not url:
            latest = self.update_info.get("latest", "")
            if latest:
                url = (
                    f"https://github.com/asd23353934/skill_tracker"
                    f"/releases/download/v{latest}"
                    f"/skill_tracker_v{latest}.zip"
                )
        if not url:
            self._set_status("找不到下載連結，請手動下載", T.RED)
            return

        self.update_info["download_url"] = url
        with self._lock:
            self._downloading = True
            self._cancelled   = False
        self._last_emit_t = 0.0
        self._last_emit_p = -1.0
        self.download_btn.setEnabled(False)
        self.download_btn.setText("下載中...")
        self._set_status("正在下載...", T.color("TEXT"))

        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        from src.infrastructure.updater import Updater
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
                os.remove(dest_path)
            except OSError:
                pass
            return

        if success:
            self._complete_signal.emit(dest_path)
        else:
            self._failed_signal.emit()

    def _on_progress(self, downloaded, total):
        # CPython bool 讀取為 atomic — hot path 不抓 lock
        if self._cancelled:
            return
        progress = (downloaded / total) if total > 0 else 0.0

        # 節流：避免 8KB chunk × N 次塞爆 Qt event queue
        now = time.monotonic()
        complete = total > 0 and downloaded >= total
        if not complete and now - self._last_emit_t < _PROGRESS_EMIT_INTERVAL \
                and abs(progress - self._last_emit_p) < _PROGRESS_EMIT_DELTA:
            return
        self._last_emit_t = now
        self._last_emit_p = progress

        if total > 0:
            mb_dl  = downloaded / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            text = f"下載中... {mb_dl:.1f} / {mb_tot:.1f} MB ({progress * 100:.0f}%)"
        else:
            mb_dl  = downloaded / (1024 * 1024)
            text = f"下載中... {mb_dl:.1f} MB"
        self._progress_signal.emit(progress, text)

    def _update_progress(self, progress: float, text: str):
        try:
            self.progress_bar.setValue(int(min(progress, 1.0) * 100))
            self.status_label.setText(text)
        except RuntimeError:
            # widget 已銷毀（dialog 關閉後晚到的 signal）
            pass

    def _on_download_complete(self, file_path: str):
        self._downloading = False
        self.progress_bar.setValue(100)
        self._set_status("下載完成！正在啟動更新...", T.GREEN)
        self.download_btn.setText("下載完成")
        QTimer.singleShot(1000, lambda: self._launch_updater(file_path))

    def _on_download_failed(self):
        self._downloading = False
        self.progress_bar.setValue(0)
        self._set_status("下載失敗，請手動下載或稍後再試", T.RED)
        self.download_btn.setEnabled(True)
        self.download_btn.setText("重試下載")

    def _set_status(self, text: str, color: str):
        self.status_label.setText(text)
        T.apply_font(self.status_label, T.FONT_CAPTION, color_override=color)

    def _try_launch(self, argv: list, label: str) -> bool:
        """嘗試以 DETACHED_PROCESS 啟動 launcher；失敗只 log。"""
        try:
            subprocess.Popen(
                argv,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
            )
            return True
        except OSError as e:
            print(f"[update] {label} launch failed: {e}", flush=True)
            return False

    def _launch_updater(self, downloaded_file: str):
        try:
            app_dir = user_data_path("")
            pid     = str(os.getpid())
            launched = False

            ps1 = os.path.join(app_dir, "update_launcher.ps1")
            if os.path.exists(ps1):
                launched = self._try_launch(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-WindowStyle", "Hidden",
                        "-ExecutionPolicy", "Bypass",
                        "-File", ps1,
                        "-DownloadFile", downloaded_file,
                        "-AppDir", app_dir,
                        "-AppExe", sys.executable,
                        "-AppPid", pid,
                    ],
                    "ps1",
                )

            if not launched:
                bat = os.path.join(app_dir, "update_launcher.bat")
                if os.path.exists(bat):
                    launched = self._try_launch(
                        [bat, downloaded_file, app_dir, sys.executable, pid],
                        "bat",
                    )

            if not launched:
                self._set_status("找不到更新腳本，請手動更新", T.RED)
                return

            self.status_label.setText("應用程式即將關閉...")
            QTimer.singleShot(500, self._shutdown_app)

        except Exception as e:
            self._set_status(f"啟動更新失敗: {e}", T.RED)

    def _shutdown_app(self):
        try:
            self.reject()
        except RuntimeError:
            pass
        try:
            self.parent_app.close()
        except (RuntimeError, AttributeError):
            pass
        QApplication.quit()
        sys.exit(0)

    def _on_cancel(self):
        with self._lock:
            was_downloading   = self._downloading
            self._cancelled   = True
            self._downloading = False
        if was_downloading:
            self._set_status("已取消下載", T.TEXT_DIM)
            self.download_btn.setEnabled(True)
            self.download_btn.setText("重新下載")
        else:
            self.close()

    def _open_download_page(self):
        webbrowser.open(
            "https://github.com/asd23353934/skill_tracker/releases/latest"
        )

    def close(self):
        with self._lock:
            if self._downloading:
                self._cancelled = True
        super().close()
