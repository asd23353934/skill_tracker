"""
V2 UI 入口 — Soft Purple Gradient Dashboard（V2 為預設 UI）

頁首無底線；唯一邊線在側邊欄右側；背景使用紫色漸層。
直接跑 `python main_v2.py` 或走 `python main.py`（預設）進入。
"""

import os
import sys
import threading
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
)
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QIcon
from src.ui.dispatcher import Dispatcher
from src.ui_v2.toast_v2 import ToastManagerV2
from src.ui_v2.dialogs import SettingsDialogV2

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.header_v2 import HeaderV2
from src.ui_v2.sidebar_v2 import SidebarV2
from src.ui_v2.page_registry import PAGE_REGISTRY

from src.infrastructure.config_manager import ConfigManager
from src.infrastructure.helpers import resource_path, user_data_path
from src.ui.app_core import AppCoreMixin


class V2AppContext(AppCoreMixin):
    """V2 app backing — 透過 AppCoreMixin 取得完整 domain 層。

    繼承 AppCoreMixin 後即可呼叫所有 V1/V2 共用方法（edit_cooldown / toggle_all
    / show_skill_detail / …），並擁有 SkillManager / HotkeyManager /
    WindowManager / SoundManager / OverlayManager 等 backing。

    額外提供：
        toast (NoopToast) / after / overlay_page slot
    """

    def __init__(self):
        # 跨執行緒安全 dispatcher（pynput daemon → 主執行緒）；
        # 必須在 _init_domain_backing 前建好，因 hotkey/window manager 之後會 capture self
        self._dispatcher = Dispatcher(QApplication.instance())
        self._init_domain_backing(ConfigManager(resource_path("config.json")))
        self.overlay_page = None
        # toast 在此暫設 console bridge；PreviewWindow.__init__ 末段會替換為 ToastManagerV2
        self.toast = _ConsoleToastBridge()
        # V1 UI 元件 stub —— HotkeyManager / WindowManager 會呼叫
        self.header = _NoopHeader()
        self.monster_page = _NoopMonsterPage()
        # 啟動 hotkey + 還原常駐視窗，行為與 V1 等價
        self.hotkey_manager.start()
        self.window_manager.initialize_persistent_skills()

    def after(self, ms: int, fn):
        """執行緒安全：透過 _Dispatcher 排回主執行緒（V1 等價）"""
        self._dispatcher.schedule(ms, fn)


class _ConsoleToastBridge:
    """V2AppContext 建構期間的暫時 toast 槽；PreviewWindow 建好即替換為 ToastManagerV2。"""
    def show(self, msg, kind="info"):
        print(f"[toast/{kind}] {msg}")


class _NoopHeader:
    """V1 Header stub — HotkeyManager hint 接收後 print 到 console。"""
    def show_hotkey_hint(self, *args, **kwargs):
        print(f"[hotkey-hint] {args} {kwargs}")
    def clear_hotkey_hint(self):
        pass


class _NoopMonsterPage:
    """V1 MonsterPage stub — V2 monster page 接線後可移除。"""
    cards: dict = {}


# 跨 launcher（ps1 / bat）的 marker 契約 — 一旦修改需要同步更新
# update_launcher.{ps1,bat} 內的 update_failed.txt 寫入路徑
_UPDATE_MARKER_FILENAME = "update_failed.txt"
_UPDATE_MARKER_FALLBACK_REASON = "未知原因"
_UPDATE_MARKER_REASON_MAX_LEN = 200


def _sanitize_marker_reason(raw: str) -> str:
    """過濾 marker 內 reason 字串，避免 marker 偽造攻擊。

    AppDir 是同 user 可寫，惡意 process 可在 update_failed.txt 寫入帶 URL 的
    釣魚訊息，讓我們的 toast 看起來像合法更新提示。reason 只保留純文字短摘要：
    剔除控制字元、含 URL 標記直接 fallback、過長截斷。
    """
    if not raw:
        return _UPDATE_MARKER_FALLBACK_REASON
    if "://" in raw.lower():
        return _UPDATE_MARKER_FALLBACK_REASON
    cleaned = "".join(c for c in raw if c.isprintable()).strip()
    if not cleaned:
        return _UPDATE_MARKER_FALLBACK_REASON
    if len(cleaned) > _UPDATE_MARKER_REASON_MAX_LEN:
        cleaned = cleaned[:_UPDATE_MARKER_REASON_MAX_LEN] + "…"
    return cleaned


class PreviewWindow(QMainWindow):
    """V2 主視窗 — 無框 1240x760"""

    _RESIZE_MARGIN = 4   # 邊框 resize 感應距離（像素）

    def __init__(self):
        super().__init__()
        self._pending_update_info = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.resize(1240, 760)
        self.setMinimumSize(1000, 640)
        self.app_ctx = V2AppContext()
        self._build()
        # 替換 console bridge 為真實 ToastManagerV2（要求 PreviewWindow 已存在）
        self.app_ctx.toast = ToastManagerV2(self)
        # header 更新 chip 點擊 → 開 UpdateDialog
        self.header.update_requested.connect(self._open_update_dialog)
        # 安裝全域事件過濾器：攔截邊框附近滑鼠事件以實現原生 resize
        QApplication.instance().installEventFilter(self)
        # 500ms 等主視窗 paint 完成 + toast 容器 layout 完成，避免 toast 動畫 jitter
        QTimer.singleShot(500, self._check_update_failure_marker)
        # 啟動 1 秒後背景檢查 GitHub Release（與 V1 等價）
        self._schedule_update_check()

    def _build(self):
        # 主背景：紫色漸層
        root = QWidget()
        root.setObjectName("root_v2")
        root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        root.setStyleSheet(
            f"QWidget#root_v2 {{ background: {T.bg_gradient()}; }}"
        )

        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── 側邊欄（左）──
        self.sidebar = SidebarV2(
            root,
            self._on_page_change,
            on_settings_click=self._open_settings,
        )
        outer.addWidget(self.sidebar)

        # ── 右側：header + content ──
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        self.header = HeaderV2(root, self)
        right.addWidget(self.header)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self.pages = {}
        for spec in PAGE_REGISTRY:
            page = spec.factory(self.stack, self.app_ctx)
            self.stack.addWidget(page)
            self.pages[spec.key] = page
        right.addWidget(self.stack, 1)

        right_wrap = QWidget()
        right_wrap.setLayout(right)
        outer.addWidget(right_wrap, 1)

        self.setCentralWidget(root)
        self._on_page_change("skill")

    def _on_page_change(self, key):
        page = self.pages.get(key)
        if page:
            self.stack.setCurrentWidget(page)

    def _open_settings(self):
        try:
            dlg = SettingsDialogV2(self, self.app_ctx)
            dlg.show()           # 非 modal：開著仍可操作主視窗 / 遊戲
            dlg.raise_()
            dlg.activateWindow()
        except Exception as e:
            # exe console=False；把錯誤寫到檔案方便 debug
            import traceback
            try:
                from src.infrastructure.helpers import user_data_path
                log_path = user_data_path("error.log")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"[_open_settings] {type(e).__name__}: {e}\n")
                    f.write(traceback.format_exc())
                    f.write("\n---\n")
            except Exception:
                pass
            # 若 toast 可用則彈錯（至少 user 看到有問題）
            toast = getattr(self.app_ctx, "toast", None)
            if toast is not None:
                toast.show(f"設定無法開啟：{type(e).__name__}", "error")

    # --------------------------------------------------
    # 自動更新檢查（與 V1 App._check_for_updates 等價）
    # --------------------------------------------------
    def _schedule_update_check(self):
        """1 秒後排程背景更新檢查；測試模式（env=1）跳過"""
        if os.environ.get("SKILL_TRACKER_DISABLE_UPDATE_CHECK") == "1":
            return
        QTimer.singleShot(1000, self._run_update_check)

    def _run_update_check(self):
        """daemon thread 內呼叫 Updater，結果透過 app_ctx.after(0,…) 排回主執行緒"""
        def _worker():
            try:
                from src.infrastructure.updater import Updater
                update_info = Updater().check_for_updates()
            except Exception as e:
                print(f"[v2-update] check error: {type(e).__name__}: {e}")
                return
            self.app_ctx.after(0, lambda info=update_info: self._on_update_result(info))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_update_result(self, update_info):
        """主執行緒 handler：有新版時亮 header chip + toast 通知，不主動跳 dialog。

        使用者點 header 右側 chip 才開 UpdateDialog（自動 modal 太擾）。
        """
        if not update_info or not update_info.get("available"):
            err = (update_info or {}).get("error")
            if err:
                print(f"[v2-update] no update: {err}")
            return
        self._pending_update_info = update_info
        latest = update_info.get("latest", "")
        try:
            self.header.set_update_available(latest)
        except Exception as e:
            print(f"[v2-update] header chip error: {type(e).__name__}: {e}")
        toast = getattr(self.app_ctx, "toast", None)
        if toast is not None:
            toast.show(f"有新版本 v{latest} 可下載 — 點頂部按鈕開始更新", "info")

    def _open_update_dialog(self):
        """header chip clicked → 開 UpdateDialog 走完整流程"""
        info = getattr(self, "_pending_update_info", None)
        if not info:
            return
        try:
            from src.ui_v2.dialogs.update_dialog_v2 import UpdateDialog
            dlg = UpdateDialog(self, info)
            dlg.exec()
        except Exception as e:
            print(f"[v2-update] dialog error: {type(e).__name__}: {e}")

    def _check_update_failure_marker(self):
        """偵測 launcher 寫的 update_failed.txt → toast 提示 + 刪除

        雙保險之一：MessageBox 在 launcher 端立刻彈出；marker 是備援，
        確保使用者即使 miss 了 MessageBox（例如下班才回來）也會被告知。
        utf-8-sig 防禦 PS 5.1 Out-File -Encoding utf8 寫入的 BOM。
        SKILL_TRACKER_DISABLE_UPDATE_CHECK=1 同時抑制 update check 與 marker scan，
        讓 test 環境留下的 stale marker 不污染下次啟動。
        讀檔失敗（OSError）→ toast 仍以 fallback reason 觸發；意圖讓使用者知道
        launcher 曾經失敗，即使我們無法解讀詳細原因。
        """
        if os.environ.get("SKILL_TRACKER_DISABLE_UPDATE_CHECK") == "1":
            return
        marker_path = Path(user_data_path(_UPDATE_MARKER_FILENAME))
        if not marker_path.exists():
            return
        raw_reason = ""
        try:
            # 只取第一筆 reason: 行；未來欄位需避開此 prefix（例如 reason_code 等）
            for line in marker_path.read_text(encoding="utf-8-sig").splitlines():
                if line.lower().startswith("reason:"):
                    raw_reason = line.split(":", 1)[1].strip()
                    break
        except OSError as e:
            print(f"[v2-update] read marker failed: {e}")
        try:
            marker_path.unlink(missing_ok=True)
        except OSError as e:
            # missing_ok 只吞 FileNotFoundError；防毒鎖檔等 PermissionError 走這裡
            print(f"[v2-update] unlink marker failed: {e}")
        reason = _sanitize_marker_reason(raw_reason)
        toast = getattr(self.app_ctx, "toast", None)
        if toast is not None:
            toast.show(f"上次自動更新失敗：{reason}，請手動下載", "warning")

    # --------------------------------------------------
    # 無邊框視窗 Resize（QApplication 全域事件過濾 + startSystemResize）
    # --------------------------------------------------
    def eventFilter(self, obj, event):
        if not isinstance(obj, QWidget):
            return super().eventFilter(obj, event)
        if obj.window() is not self:
            return super().eventFilter(obj, event)

        etype = event.type()
        if etype == QEvent.Type.MouseMove:
            try:
                lp = self.mapFromGlobal(event.globalPosition().toPoint())
                self._update_resize_cursor(lp)
            except Exception:
                pass
        elif etype == QEvent.Type.MouseButtonPress:
            try:
                if event.button() == Qt.MouseButton.LeftButton:
                    lp = self.mapFromGlobal(event.globalPosition().toPoint())
                    edges = self._compute_resize_edges(lp)
                    if edges:
                        self.windowHandle().startSystemResize(edges)
                        return True
            except Exception:
                pass
        return super().eventFilter(obj, event)

    def _compute_resize_edges(self, local_pos):
        px, py = local_pos.x(), local_pos.y()
        m = self._RESIZE_MARGIN
        w, h = self.width(), self.height()
        left, right  = px < m, px > w - m
        top,  bottom = py < m, py > h - m
        if not (left or right or top or bottom):
            return None
        edges = Qt.Edges()
        if left:   edges |= Qt.Edge.LeftEdge
        if right:  edges |= Qt.Edge.RightEdge
        if top:    edges |= Qt.Edge.TopEdge
        if bottom: edges |= Qt.Edge.BottomEdge
        return edges

    def _update_resize_cursor(self, local_pos):
        px, py = local_pos.x(), local_pos.y()
        m = self._RESIZE_MARGIN
        w, h = self.width(), self.height()
        l, r = px < m, px > w - m
        t, b = py < m, py > h - m
        if   (t and l) or (b and r): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif (t and r) or (b and l): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif l or r:                  self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif t or b:                  self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:                         self.unsetCursor()


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(T.global_qss())
    win = PreviewWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
