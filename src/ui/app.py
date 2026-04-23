"""
主應用程式模組
QMainWindow 主應用殼層，初始化管理器、組合佈局、業務邏輯協調
PySide6 版本
"""

import sys
import threading

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QMessageBox, QInputDialog, QApplication,
    QFrame,
)
from PySide6.QtCore import Qt, QEvent, QTimer, QPropertyAnimation
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QGraphicsOpacityEffect

from src.ui.theme import AppTheme
from src.infrastructure.config_manager import ConfigManager
from src.infrastructure.helpers import resource_path
from src.ui.sidebar import Sidebar
from src.ui.header import Header
from src.ui.status_bar import StatusBar
from src.ui.pages import SkillPage, SkillPageV2, MonsterPage, OverlayPage, PotionCostPage, MapleWorldPage
from src.ui.toast import ToastManager
from src.ui.app_core import AppCoreMixin
from src.ui.dispatcher import Dispatcher




class App(QMainWindow, AppCoreMixin):
    """主應用程式 — PySide6 QMainWindow"""

    _RESIZE_MARGIN = 4   # 邊框 resize 感應距離（像素）

    def __init__(self):
        super().__init__()

        # 版本號
        try:
            from version import get_version
            version_str = f" v{get_version()}"
        except Exception:
            version_str = ""

        self.setWindowTitle(f"技能追蹤器 - Artale 楓之谷{version_str}")
        # 無邊框視窗 + 置頂（PyDracula 風格，自訂標題列）
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # 視窗圖示
        icon_path = resource_path("icon.ico")
        try:
            import os
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        # 視窗大小與位置
        self.setGeometry(100, 50, 1000, 720)
        self.setMinimumSize(1100, 580)

        # 執行緒安全排程器（模擬 tkinter after()）
        self._dispatcher = Dispatcher(self)

        # Manager / Service 鏈 + profile 載入 + widget 登錄 dict
        # —— 全部委派給 AppCoreMixin._init_domain_backing
        try:
            self._init_domain_backing(ConfigManager(resource_path("config.json")))
        except Exception as e:
            QMessageBox.critical(None, "錯誤", f"初始化失敗: {e}")
            sys.exit(1)

        # 建構 UI
        self._build_ui()

        # Toast 通知（需在 UI 建構後初始化）
        self.toast = ToastManager(self)

        # 啟動服務
        self.hotkey_manager.start()
        self.window_manager.initialize_persistent_skills()

        # 顯示視窗（稍微透明，與原版一致）
        self.setWindowOpacity(0.96)
        self.show()

        # 安裝全域事件過濾器以實現邊框 resize（startSystemResize 方式）
        QApplication.instance().installEventFilter(self)

        # 檢查更新（非阻塞）
        QTimer.singleShot(1000, self._check_for_updates)

    # --------------------------------------------------
    # tkinter after() 相容介面（供 HotkeyManager / OverlayManager 呼叫）
    # --------------------------------------------------

    def after(self, ms: int, func):
        """模擬 tkinter after()，執行緒安全地排程 func 在主執行緒執行

        Args:
            ms:   延遲毫秒（0 = 立即排隊）
            func: 要執行的 callable
        """
        self._dispatcher.schedule(ms, func)

    # --------------------------------------------------
    # UI 建構
    # --------------------------------------------------

    def _build_ui(self):
        """建構主要 UI — VS Code 式版面（Header 全寬 + Sidebar 左 + StatusBar 全寬）"""
        main_widget = QWidget()

        # ── 外層：QVBoxLayout（上→中→下）──
        outer_layout = QVBoxLayout(main_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # 1. Header — 全寬最上方（含 sidebar 上方區域）
        self.header = Header(main_widget, self)
        outer_layout.addWidget(self.header)

        # Header 底部金色分隔線（2px，確保可見）
        _sep_top = QFrame()
        _sep_top.setObjectName("sep_header_bottom")
        _sep_top.setFixedHeight(2)
        _sep_top.setStyleSheet(
            "QFrame#sep_header_bottom { background-color: #d4a843; border: none; }"
        )
        outer_layout.addWidget(_sep_top)

        # 2. 中段：Sidebar（左）+ page_stack（右，佔滿剩餘空間）
        middle_widget = QWidget()
        middle_widget.setStyleSheet(f"background-color: {AppTheme.BG_PRIMARY};")
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        self.sidebar = Sidebar(middle_widget, self._switch_page, self)
        self.sidebar.setFixedWidth(AppTheme.SIDEBAR_COLLAPSED)
        middle_layout.addWidget(self.sidebar)

        # 頁面堆疊（QStackedWidget 取代 tkraise）
        self.page_stack = QStackedWidget()
        middle_layout.addWidget(self.page_stack)

        outer_layout.addWidget(middle_widget)

        # StatusBar 頂部金色分隔線（2px，確保可見）
        _sep_bot = QFrame()
        _sep_bot.setObjectName("sep_statusbar_top")
        _sep_bot.setFixedHeight(2)
        _sep_bot.setStyleSheet(
            "QFrame#sep_statusbar_top { background-color: #d4a843; border: none; }"
        )
        outer_layout.addWidget(_sep_bot)

        # 3. StatusBar — 全寬最下方（含 sidebar 下方區域）
        self.status_bar = StatusBar(main_widget, self)
        outer_layout.addWidget(self.status_bar)

        self.setCentralWidget(main_widget)

        # 建立三個頁面
        self.pages = {}

        self.skill_page = SkillPage(self.page_stack, self)
        self.page_stack.addWidget(self.skill_page)
        self.pages["skill"] = self.skill_page

        self.skill_page_v2 = SkillPageV2(self.page_stack, self)
        self.page_stack.addWidget(self.skill_page_v2)
        self.pages["skill_v2"] = self.skill_page_v2

        self.monster_page = MonsterPage(self.page_stack, self)
        self.page_stack.addWidget(self.monster_page)
        self.pages["monster"] = self.monster_page

        self.overlay_page = OverlayPage(self.page_stack, self)
        self.page_stack.addWidget(self.overlay_page)
        self.pages["overlay"] = self.overlay_page

        self.potion_page = PotionCostPage(self.page_stack, self)
        self.page_stack.addWidget(self.potion_page)
        self.pages["potion"] = self.potion_page

        self.mapleworld_page = MapleWorldPage(self.page_stack, self)
        self.page_stack.addWidget(self.mapleworld_page)
        self.pages["mapleworld"] = self.mapleworld_page

        # 預設顯示技能頁
        self._switch_page("skill")

    def _switch_page(self, page_name):
        """切換頁面（QStackedWidget 不銷毀/重建，無閃爍）

        Args:
            page_name: 'skill' | 'monster' | 'overlay' | 'potion'
        """
        if page_name not in self.pages:
            return
        page = self.pages[page_name]
        self.page_stack.setCurrentWidget(page)
        self._play_page_fade_in(page)

    def _play_page_fade_in(self, page):
        """頁面切換淡入動畫（180ms，opacity 0→1）

        Args:
            page: 目標頁面 QWidget
        """
        prev = getattr(self, "_page_fade_anim", None)
        if prev is not None and prev.state() == QPropertyAnimation.State.Running:
            prev.stop()

        effect = QGraphicsOpacityEffect(page)
        effect.setOpacity(0.0)
        page.setGraphicsEffect(effect)

        anim = AppTheme.make_anim(effect, b"opacity", 0.0, 1.0, duration=180, parent=page)
        # 動畫結束後移除效果，避免影響子元件（例如卡片陰影）
        anim.finished.connect(lambda: page.setGraphicsEffect(None))
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._page_fade_anim = anim

    # --------------------------------------------------
    # 靜態輔助：動態設定 QPushButton 樣式
    # --------------------------------------------------

    # --------------------------------------------------
    # 怪物 API
    # --------------------------------------------------

    def edit_respawn_time(self, monster_id):
        """編輯怪物重生時間（委派到 MonsterService）

        Args:
            monster_id: 怪物 ID
        """
        monster = self.get_monster(monster_id)
        if not monster:
            return

        self.hotkey_manager.enabled = False
        original = self.monster_service.get_original_respawn_time(monster_id)
        current  = monster.get("respawn_time", 0)

        new_val, ok = QInputDialog.getInt(
            self, "修改重生時間",
            f"請輸入 '{monster['name']}' 的重生時間（秒）:\n(原始值: {original}秒)",
            current, 1, 9999,
        )
        self.hotkey_manager.enabled = True

        if ok and new_val != current:
            is_modified = self.monster_service.set_respawn_time(monster_id, new_val)
            self.monster_service.save()

            btn = self.monster_respawn_buttons.get(monster_id)
            if btn:
                btn.setText(f"{new_val}秒")
                self._apply_btn_style(
                    btn,
                    bg    = AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_TERTIARY,
                    hover = "#2563eb"             if is_modified else AppTheme.BG_SECONDARY,
                )

    def reset_respawn_time(self, monster_id):
        """重置怪物重生時間為原始值（委派到 MonsterService）

        Args:
            monster_id: 怪物 ID
        """
        original = self.monster_service.reset_respawn_time(monster_id)
        if original is None:
            return

        self.monster_service.save()

        btn = self.monster_respawn_buttons.get(monster_id)
        if btn:
            btn.setText(f"{original}秒")
            self._apply_btn_style(btn, bg=AppTheme.BG_TERTIARY, hover=AppTheme.BG_SECONDARY)

    def reset_monster_hotkey(self, monster_id):
        """重置怪物快捷鍵（委派到 MonsterService）

        Args:
            monster_id: 怪物 ID
        """
        monster = self.get_monster(monster_id)
        if not monster or not monster.get("hotkey"):
            return
        self.monster_service.clear_hotkey(monster_id)
        self.monster_service.save()
        card = self.monster_page.cards.get(monster_id)
        if card:
            self.after(0, lambda c=card: c.update_hotkey_display("", False))

    def edit_monster_alert_before(self, monster_id):
        """編輯怪物提前提示秒數（委派到 MonsterService）

        Args:
            monster_id: 怪物 ID
        """
        monster = self.get_monster(monster_id)
        if not monster:
            return

        self.hotkey_manager.enabled = False
        current = monster.get("alert_before", 10)

        new_val, ok = QInputDialog.getInt(
            self, "提前提示秒數",
            f"請輸入 '{monster['name']}' 的提前提示秒數:\n(0 = 不提示)",
            current, 0, 9999,
        )
        self.hotkey_manager.enabled = True

        if ok and new_val != current:
            self.monster_service.set_alert_before(monster_id, new_val)
            self.monster_service.save()
            btn = self.monster_alert_before_buttons.get(monster_id)
            if btn:
                btn.setText(f"{new_val}秒")
                self._apply_btn_style(
                    btn,
                    bg    = AppTheme.ACCENT_ORANGE if new_val > 0 else AppTheme.BG_TERTIARY,
                    hover = "#e07a2a"              if new_val > 0 else AppTheme.BG_SECONDARY,
                )

    def update_monster_alert_sound(self, monster_id, filename: str):
        """更新怪物提前提示聲音（委派到 MonsterService）

        Args:
            monster_id: 怪物 ID
            filename:   聲音檔名（空字串 = 使用全域）
        """
        self.monster_service.set_alert_sound(monster_id, filename)
        self.monster_service.save()

    def update_monster_end_sound(self, monster_id, filename: str):
        """更新怪物結束聲音（委派到 MonsterService）

        Args:
            monster_id: 怪物 ID
            filename:   聲音檔名（空字串 = 使用全域）
        """
        self.monster_service.set_sound(monster_id, filename)
        self.monster_service.save()

    def update_monster_loop(self, monster_id, loop_value):
        """更新怪物循環設定（委派到 MonsterService）

        Args:
            monster_id:  怪物 ID
            loop_value:  bool
        """
        self.monster_service.set_loop(monster_id, loop_value)
        self.monster_service.save()
        if monster_id in self.window_manager.active_windows:
            self.window_manager.active_windows[monster_id].is_loop = loop_value

    def update_monster_permanent(self, monster_id, permanent_value):
        """更新怪物常駐設定（委派到 MonsterService）

        Args:
            monster_id:      怪物 ID
            permanent_value: bool
        """
        self.monster_service.set_permanent(monster_id, permanent_value)
        self.monster_service.save()
        if permanent_value:
            if monster_id not in self.window_manager.active_windows:
                self.window_manager.create_permanent_monster_window(monster_id)
        else:
            if monster_id in self.window_manager.active_windows:
                self.window_manager.active_windows[monster_id].close()

    # --------------------------------------------------
    # 公開 API（供子元件呼叫）
    # --------------------------------------------------

    def clear_all_hotkeys(self):
        """清空所有快捷鍵和秒數覆寫（含確認對話框，委派到 SkillService）"""
        reply = QMessageBox.question(
            self, "確認",
            "確定要清空所有技能的快捷鍵和自訂秒數嗎?\n（會恢復預設秒數）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for skill_id in self.skill_loader.get_all_skills():
                self.skill_service.clear_hotkey(skill_id)
                self.skill_service.clear_cooldown_override(skill_id)

                self.update_hotkey_display(skill_id, "", False)

                original = self.skill_service.get_original_cooldown(skill_id)
                btn = self.cooldown_buttons.get(skill_id)
                if btn and original:
                    btn.setText(f"{original}秒")
                    self._apply_btn_style(
                        btn, bg=AppTheme.BG_TERTIARY, fg=AppTheme.TEXT_PRIMARY
                    )

            self.auto_save_current_profile()
            self.toast.show("已清空所有快捷鍵並恢復預設秒數", "success")

    def show_settings(self):
        """顯示設定對話框"""
        self.hotkey_manager.enabled = False

        from src.ui.dialogs import SettingsDialog

        dialog = SettingsDialog(self, {
            "x":                  self.skill_start_x,
            "y":                  self.skill_start_y,
            "sound":              self.enable_sound,
            "alert_before_seconds": self.alert_before_seconds,
            "window_size":        self.window_size,
            "global_sound":       self.global_sound,
            "global_alert_sound": self.global_alert_sound,
            "sound_volume":       self.sound_volume,
            "sound_manager":      self.sound_manager,
        }, app=self)

        dialog.exec()
        result = dialog.result

        if result:
            old_window_size = self.window_size
            old_x, old_y    = self.skill_start_x, self.skill_start_y

            self.skill_start_x        = result["x"]
            self.skill_start_y        = result["y"]
            self.enable_sound         = result["sound"]
            self.alert_before_seconds = result["alert_before_seconds"]
            self.window_size          = result["window_size"]
            self.global_sound         = result.get("global_sound", "")
            self.global_alert_sound   = result.get("global_alert_sound", "")
            self.sound_volume         = result.get("sound_volume", 100)
            self.sound_manager.set_volume(self.sound_volume / 100.0)

            # 同步全域設定到 SkillService
            self.skill_service.alert_before_seconds = self.alert_before_seconds
            self.skill_service.global_sound = self.global_sound
            self.skill_service.global_alert_sound = self.global_alert_sound

            self.config_manager.set_settings("skill_start_x",        self.skill_start_x)
            self.config_manager.set_settings("skill_start_y",        self.skill_start_y)
            self.config_manager.set_settings("enable_sound",         self.enable_sound)
            self.config_manager.set_settings("alert_before_seconds", self.alert_before_seconds)
            self.config_manager.set_settings("window_size",          self.window_size)
            self.config_manager.set_settings("global_sound",         self.global_sound)
            self.config_manager.set_settings("global_alert_sound",   self.global_alert_sound)
            self.config_manager.set_settings("sound_volume",         self.sound_volume)
            self.config_manager.save()

            # 更新使用全域預設的提前秒數按鈕
            for skill_id, btn in self.alert_seconds_buttons.items():
                if skill_id not in self.skill_alert_seconds_overrides:
                    btn.setText(f"{self.alert_before_seconds}s")

            # window_size 變更需重建視窗（影響版面/圖片快取）；否則原地更新即可
            if self.window_size != old_window_size:
                self.window_manager.close_all()
                self.window_manager.initialize_persistent_skills()
            else:
                for sid, win in self.window_manager.active_windows.items():
                    win.enable_sound = self.enable_sound
                    self.window_manager.refresh_window_sound_params(sid)
                if (old_x, old_y) != (self.skill_start_x, self.skill_start_y):
                    self.window_manager.reposition_all()

            self.toast.show("設定已保存並套用", "success")

        self.hotkey_manager.enabled = True

    def show_profile_manager(self):
        """顯示配置管理視窗"""
        self.hotkey_manager.enabled = False

        from src.ui.dialogs import ProfileManagerDialog

        dialog = ProfileManagerDialog(
            self, self.config_manager, self._get_current_settings(), self
        )
        dialog.exec()
        result = dialog.result

        if result:
            self._apply_profile(result)

        self.hotkey_manager.enabled = True

    def show_update_dialog(self):
        """顯示更新對話框"""
        if not hasattr(self, "update_info"):
            return

        from src.ui.dialogs.update_dialog import UpdateDialog

        dialog = UpdateDialog(self, self.update_info)
        dialog.exec()

    # --------------------------------------------------
    # 內部方法
    # --------------------------------------------------

    def _get_current_settings(self):
        """獲取當前設定（委派到 SkillService）

        Returns:
            設定字典
        """
        return self.skill_service.serialize_to_dict()

    def _apply_profile(self, profile_data):
        """套用配置（委派到 SkillService）

        Args:
            profile_data: 配置字典
        """
        self.current_profile_name = self.config_manager.get_current_profile()
        self.skill_service.load_from_profile(profile_data)
        self._save_config()
        self._reload_ui()

    def _reload_ui(self):
        """重新載入 UI（替換中央元件，等同 tkinter withdraw→rebuild→deiconify）"""
        self.hide()

        # 先關閉所有技能視窗，避免前一個配置的常駐/計時視窗殘留
        self.window_manager.close_all()

        # 銷毀舊的中央元件（Qt 負責清理子元件）
        old = self.centralWidget()
        if old:
            old.setParent(None)
            old.deleteLater()

        # 重置 UI 字典
        self.permanent_vars        = {}
        self.loop_vars             = {}
        self.alert_enabled_vars    = {}
        self.hotkey_buttons        = {}
        self.cooldown_buttons      = {}
        self.alert_seconds_buttons = {}
        self.monster_respawn_buttons = {}
        self.monster_alert_before_buttons = {}

        self._build_ui()
        self.window_manager.initialize_persistent_skills()
        self.show()

    def _check_for_updates(self):
        """在背景執行緒檢查更新，避免網路請求阻塞主執行緒"""
        def _worker():
            try:
                from src.infrastructure.updater import Updater
                updater    = Updater()
                update_info = updater.check_for_updates()
                if update_info.get("available"):
                    # 跨執行緒安全地回到主執行緒更新 UI
                    self.after(0, lambda: self._on_update_found(update_info))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _on_update_found(self, update_info):
        """有新版本時顯示更新按鈕（主執行緒）

        Args:
            update_info: 更新資訊字典
        """
        self.update_info = update_info
        try:
            self.header.show_update_button()
        except Exception:
            pass

    # --------------------------------------------------
    # 無邊框視窗 Resize（QApplication 全域事件過濾 + startSystemResize）
    # --------------------------------------------------

    def eventFilter(self, obj, event):
        """攔截全視窗子元件的滑鼠事件，實現邊框游標顯示與原生 resize"""
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
                        return True   # 消費事件，讓 OS 接管 resize
            except Exception:
                pass

        return super().eventFilter(obj, event)

    def _compute_resize_edges(self, local_pos):
        """計算滑鼠所在的 resize 邊緣（回傳 Qt.Edges 或 None）"""
        px, py = local_pos.x(), local_pos.y()
        m = self._RESIZE_MARGIN
        w, h = self.width(), self.height()

        left   = px < m
        right  = px > w - m
        top    = py < m
        bottom = py > h - m

        if not (left or right or top or bottom):
            return None

        edges = Qt.Edges()
        if left:   edges |= Qt.Edge.LeftEdge
        if right:  edges |= Qt.Edge.RightEdge
        if top:    edges |= Qt.Edge.TopEdge
        if bottom: edges |= Qt.Edge.BottomEdge
        return edges

    def _update_resize_cursor(self, local_pos):
        """根據滑鼠距視窗邊緣的位置，更新游標形狀"""
        px, py = local_pos.x(), local_pos.y()
        m = self._RESIZE_MARGIN
        w, h = self.width(), self.height()

        l = px < m;  r = px > w - m
        t = py < m;  b = py > h - m

        if   (t and l) or (b and r): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif (t and r) or (b and l): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif l or r:                  self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif t or b:                  self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:                         self.unsetCursor()

    def closeEvent(self, event):  # noqa: N802
        """視窗關閉時停止所有背景服務並結束程式"""
        try:
            if hasattr(self.mapleworld_page, '_cache_stop'):
                self.mapleworld_page._cache_stop = True
        except Exception:
            pass
        try:
            self.hotkey_manager.stop()
        except Exception:
            pass
        try:
            self.window_manager.close_all()
        except Exception:
            pass
        event.accept()
        QApplication.quit()

    def run(self):
        """應用程式已由 main.py 的 qt_app.exec() 啟動，此方法保留相容性"""
        pass
