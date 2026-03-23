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
from PySide6.QtCore import Qt, QEvent, QTimer, QObject, Signal
from PySide6.QtGui import QIcon

from src.ui.theme import AppTheme
from src.ui.config_manager import ConfigManager
from src.ui.skill_manager import SkillManager
from src.ui.hotkey_manager import HotkeyManager
from src.ui.window_manager import WindowManager
from src.ui.sidebar import Sidebar
from src.ui.header import Header
from src.ui.status_bar import StatusBar
from src.ui.pages import SkillPage, MonsterPage, OverlayPage, PotionCostPage, MapleWorldPage
from src.ui.helpers import resource_path
from src.ui.toast import ToastManager


class _Dispatcher(QObject):
    """執行緒安全的回呼排程器 — 供 HotkeyManager / OverlayManager 從 daemon thread 呼叫"""

    _call = Signal(object)  # 傳遞 callable

    def __init__(self, parent: QObject):
        super().__init__(parent)
        # QueuedConnection：槽在接收端（主執行緒）的事件迴圈中執行
        self._call.connect(self._dispatch, Qt.ConnectionType.QueuedConnection)

    def schedule(self, ms: int, func):
        """排程 func 在主執行緒執行（ms=0 立即排隊）"""
        if ms == 0:
            self._call.emit(func)
        else:
            # 先跨執行緒送到主執行緒，再用 QTimer 延遲
            self._call.emit(lambda: QTimer.singleShot(ms, func))

    def _dispatch(self, func):
        func()


class App(QMainWindow):
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
        self._dispatcher = _Dispatcher(self)

        # 初始化管理器
        try:
            self.config_manager = ConfigManager(resource_path("config.json"))
            self.skill_manager = SkillManager(self.config_manager)
        except Exception as e:
            QMessageBox.critical(None, "錯誤", f"初始化失敗: {e}")
            sys.exit(1)

        # 音效管理器
        from src.ui.sound_manager import SoundManager
        self.sound_manager = SoundManager()

        # 初始化狀態
        self._init_state()

        # 子管理器
        self.hotkey_manager = HotkeyManager(self)
        self.window_manager = WindowManager(self)

        from src.ui.overlay_manager import OverlayManager
        self.overlay_manager = OverlayManager(self)

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
    # 狀態初始化
    # --------------------------------------------------

    def _init_state(self):
        """初始化應用程式狀態"""
        self.config_manager.ensure_default_profile()
        self.current_profile_name = self.config_manager.get_current_profile()

        profile_data = self.config_manager.load_profile(self.current_profile_name)
        settings = self.config_manager.config.get("settings", {})

        # 螢幕尺寸 → 計算預設技能視窗位置
        screen = QApplication.primaryScreen().geometry()
        default_x = screen.width() // 2
        default_y = screen.height() // 2

        # 一般設定
        self.player_name          = settings.get("player_name", "玩家1")
        self.skill_start_x        = settings.get("skill_start_x", default_x)
        self.skill_start_y        = settings.get("skill_start_y", default_y)
        self.enable_sound         = settings.get("enable_sound", True)
        self.window_alpha         = 0.95
        self.window_size          = settings.get("window_size", 64)
        self.alert_before_seconds = settings.get("alert_before_seconds", 0)

        # 音效設定（遷移舊檔名）
        self.global_sound = self.sound_manager.migrate_sound_filename(
            settings.get("global_sound", "")
        )
        self.global_alert_sound = self.sound_manager.migrate_sound_filename(
            settings.get("global_alert_sound", "")
        )

        # 技能設定（從配置檔載入）
        if profile_data:
            self.skill_permanent              = profile_data.get("permanent", {})
            self.skill_loop                   = profile_data.get("loop", {})
            self.skill_alert_enabled          = profile_data.get("alert_enabled", {})
            self.skill_alert_seconds_overrides= profile_data.get("alert_seconds_overrides", {})
            self.skill_sound_overrides        = {
                k: self.sound_manager.migrate_sound_filename(v)
                for k, v in profile_data.get("sound_overrides", {}).items()
            }
            self.skill_alert_sound_overrides  = {
                k: self.sound_manager.migrate_sound_filename(v)
                for k, v in profile_data.get("alert_sound_overrides", {}).items()
            }

            hotkeys = profile_data.get("hotkeys", {})
            for skill_id, hotkey in hotkeys.items():
                skill = self.skill_manager.get_skill(skill_id)
                if skill:
                    skill["hotkey"] = hotkey

            cooldown_overrides = profile_data.get("cooldown_overrides", {})
            for skill_id, cooldown in cooldown_overrides.items():
                skill = self.skill_manager.get_skill(skill_id)
                if skill:
                    skill["cooldown"] = cooldown
        else:
            self.skill_permanent               = {}
            self.skill_loop                    = {}
            self.skill_alert_enabled           = {}
            self.skill_alert_seconds_overrides = {}
            self.skill_sound_overrides         = {}
            self.skill_alert_sound_overrides   = {}

        # 確保所有技能都有預設值
        for skill_id in self.skill_manager.get_all_skills():
            self.skill_permanent.setdefault(skill_id, False)
            self.skill_loop.setdefault(skill_id, False)
            self.skill_alert_enabled.setdefault(skill_id, False)

        # 怪物 ID → 怪物字典快取（O(1) 查詢）
        self._monster_index: dict = {
            m["id"]: m
            for m in self.config_manager.config.get("monsters", [])
        }

        # UI 元件字典（儲存 QPushButton / QCheckBox 引用）
        self.permanent_vars        = {}  # skill_id → QCheckBox
        self.loop_vars             = {}  # skill_id → QCheckBox
        self.alert_enabled_vars    = {}  # skill_id → QCheckBox
        self.hotkey_buttons        = {}  # skill_id → QPushButton
        self.cooldown_buttons      = {}  # skill_id → QPushButton
        self.alert_seconds_buttons = {}  # skill_id → QPushButton
        self.monster_respawn_buttons     = {}  # monster_id → QPushButton
        self.monster_alert_before_buttons = {}  # monster_id → QPushButton

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
        if page_name in self.pages:
            self.page_stack.setCurrentWidget(self.pages[page_name])

    # --------------------------------------------------
    # 靜態輔助：動態設定 QPushButton 樣式
    # --------------------------------------------------

    @staticmethod
    def _apply_btn_style(btn, bg=None, fg=None, hover=None):
        """動態設定 QPushButton 的內聯樣式

        Args:
            btn:   QPushButton 實例
            bg:    背景色 hex（None 使用預設）
            fg:    前景文字色 hex（None 使用預設）
            hover: Hover 背景色 hex（None 不設定 hover 規則）
        """
        _bg    = bg    or AppTheme.BG_TERTIARY
        _fg    = fg    or AppTheme.TEXT_PRIMARY
        _bdr   = AppTheme.GOLD_MUTED
        style = (
            f"QPushButton {{"
            f" background-color:{_bg}; color:{_fg};"
            f" border:1px solid {_bdr}; border-radius:3px;"
            f" padding:0px 4px; font-size:10px; font-weight:bold; }}"
        )
        if hover:
            style += f" QPushButton:hover {{ background-color:{hover}; }}"
        btn.setStyleSheet(style)

    # --------------------------------------------------
    # 怪物 API
    # --------------------------------------------------

    def get_monster(self, monster_id):
        """根據 ID 取得怪物資料（O(1）

        Args:
            monster_id: 怪物 ID

        Returns:
            怪物字典或 None
        """
        return self._monster_index.get(monster_id)

    def get_monster_by_hotkey(self, key_name):
        """根據按鍵名稱取得怪物 ID

        Args:
            key_name: 按鍵名稱字串

        Returns:
            怪物 ID 或 None
        """
        key_upper = key_name.upper()
        for m in self.config_manager.config.get("monsters", []):
            if m.get("hotkey", "").upper() == key_upper:
                return m["id"]
        return None

    def get_all_monsters(self):
        """取得所有怪物資料"""
        return self.config_manager.config.get("monsters", [])

    def save_monsters(self):
        """儲存怪物資料到 config.json"""
        self.config_manager.save()

    def edit_respawn_time(self, monster_id):
        """編輯怪物重生時間

        Args:
            monster_id: 怪物 ID
        """
        monster = self.get_monster(monster_id)
        if not monster:
            return

        self.hotkey_manager.enabled = False
        original = self.config_manager.get_original_respawn_time(monster_id)
        current  = monster.get("respawn_time", 0)

        new_val, ok = QInputDialog.getInt(
            self, "修改重生時間",
            f"請輸入 '{monster['name']}' 的重生時間（秒）:\n(原始值: {original}秒)",
            current, 1, 9999,
        )
        self.hotkey_manager.enabled = True

        if ok and new_val != current:
            monster["respawn_time"] = new_val
            self.save_monsters()

            btn = self.monster_respawn_buttons.get(monster_id)
            if btn:
                is_modified = original and new_val != original
                btn.setText(f"{new_val}秒")
                self._apply_btn_style(
                    btn,
                    bg    = AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_TERTIARY,
                    hover = "#2563eb"             if is_modified else AppTheme.BG_SECONDARY,
                )

    def reset_respawn_time(self, monster_id):
        """重置怪物重生時間為原始值

        Args:
            monster_id: 怪物 ID
        """
        monster = self.get_monster(monster_id)
        if not monster:
            return

        original = self.config_manager.get_original_respawn_time(monster_id)
        if not original or monster.get("respawn_time") == original:
            return

        monster["respawn_time"] = original
        self.save_monsters()

        btn = self.monster_respawn_buttons.get(monster_id)
        if btn:
            btn.setText(f"{original}秒")
            self._apply_btn_style(btn, bg=AppTheme.BG_TERTIARY, hover=AppTheme.BG_SECONDARY)

    def reset_monster_hotkey(self, monster_id):
        """重置怪物快捷鍵

        Args:
            monster_id: 怪物 ID
        """
        monster = self.get_monster(monster_id)
        if not monster or not monster.get("hotkey"):
            return
        monster["hotkey"] = ""
        self.save_monsters()
        card = self.monster_page.cards.get(monster_id)
        if card:
            self.after(0, lambda c=card: c.update_hotkey_display("", False))

    def edit_monster_alert_before(self, monster_id):
        """編輯怪物提前提示秒數

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
            monster["alert_before"] = new_val
            self.save_monsters()
            btn = self.monster_alert_before_buttons.get(monster_id)
            if btn:
                btn.setText(f"{new_val}秒")
                self._apply_btn_style(
                    btn,
                    bg    = AppTheme.ACCENT_ORANGE if new_val > 0 else AppTheme.BG_TERTIARY,
                    hover = "#e07a2a"              if new_val > 0 else AppTheme.BG_SECONDARY,
                )

    def update_monster_alert_sound(self, monster_id, filename: str):
        """更新怪物提前提示聲音

        Args:
            monster_id: 怪物 ID
            filename:   聲音檔名（空字串 = 使用全域）
        """
        monster = self.get_monster(monster_id)
        if not monster:
            return
        monster["alert_sound"] = filename
        self.save_monsters()

    def update_monster_end_sound(self, monster_id, filename: str):
        """更新怪物結束聲音

        Args:
            monster_id: 怪物 ID
            filename:   聲音檔名（空字串 = 使用全域）
        """
        monster = self.get_monster(monster_id)
        if not monster:
            return
        monster["sound"] = filename
        self.save_monsters()

    def update_monster_loop(self, monster_id, loop_value):
        """更新怪物循環設定

        Args:
            monster_id:  怪物 ID
            loop_value:  bool
        """
        monster = self.get_monster(monster_id)
        if not monster:
            return
        monster["loop"] = loop_value
        self.save_monsters()
        if monster_id in self.window_manager.active_windows:
            self.window_manager.active_windows[monster_id].is_loop = loop_value

    def update_monster_permanent(self, monster_id, permanent_value):
        """更新怪物常駐設定

        Args:
            monster_id:      怪物 ID
            permanent_value: bool
        """
        monster = self.get_monster(monster_id)
        if not monster:
            return
        monster["permanent"] = permanent_value
        self.save_monsters()
        if permanent_value:
            if monster_id not in self.window_manager.active_windows:
                self.window_manager.create_permanent_monster_window(monster_id)
        else:
            if monster_id in self.window_manager.active_windows:
                self.window_manager.active_windows[monster_id].close()

    # --------------------------------------------------
    # 公開 API（供子元件呼叫）
    # --------------------------------------------------

    def get_original_cooldown(self, skill_id):
        """獲取技能的原始冷卻秒數

        Args:
            skill_id: 技能 ID

        Returns:
            原始秒數或 None
        """
        for skill_data in self.config_manager.initial_skills:
            if skill_data["id"] == skill_id:
                return skill_data.get("cooldown")
        for item_data in self.config_manager.initial_items:
            if item_data["id"] == skill_id:
                return item_data.get("cooldown")
        return None

    def get_alert_seconds(self, skill_id):
        """獲取技能的提前提示秒數（個別 > 全域）

        Args:
            skill_id: 技能 ID

        Returns:
            提前提示秒數
        """
        return self.skill_alert_seconds_overrides.get(
            skill_id, self.alert_before_seconds
        )

    def get_sound_for_skill(self, skill_id):
        """獲取技能的完成音效檔名

        Args:
            skill_id: 技能 ID

        Returns:
            音效檔名（空字串 = 系統 beep）
        """
        override = self.skill_sound_overrides.get(skill_id)
        return override if override else self.global_sound

    def get_alert_sound_for_skill(self, skill_id):
        """獲取技能的提前提示音效檔名

        Args:
            skill_id: 技能 ID

        Returns:
            音效檔名
        """
        override = self.skill_alert_sound_overrides.get(skill_id)
        return override if override else self.global_alert_sound

    def auto_save_current_profile(self):
        """自動保存當前配置到檔案"""
        current_settings = self._get_current_settings()
        self.config_manager.save_profile(self.current_profile_name, current_settings)

    def update_hotkey_display(self, skill_id, key_str, has_hotkey):
        """更新快捷鍵按鈕顯示

        Args:
            skill_id:   技能 ID
            key_str:    快捷鍵字串
            has_hotkey: 是否有快捷鍵
        """
        btn = self.hotkey_buttons.get(skill_id)
        if btn:
            btn.setText(key_str if has_hotkey else "未設定")
            self._apply_btn_style(
                btn,
                bg    = AppTheme.ACCENT_YELLOW      if has_hotkey else AppTheme.BG_TERTIARY,
                fg    = "#000000"                   if has_hotkey else AppTheme.TEXT_SECONDARY,
                hover = AppTheme.ACCENT_YELLOW_HOVER if has_hotkey else AppTheme.BG_SECONDARY,
            )

    def update_skill_setting_exclusive(self, skill_id, setting_type, var):
        """更新技能設定（常駐 / 循環互斥）

        Args:
            skill_id:     技能 ID
            setting_type: 'permanent' | 'loop'
            var:          觸發變更的 QCheckBox 實例
        """
        new_value = var.isChecked()

        if new_value:
            if setting_type == "permanent":
                # 開常駐時取消循環
                if self.skill_loop.get(skill_id, False):
                    self.skill_loop[skill_id] = False
                    if skill_id in self.loop_vars:
                        self.loop_vars[skill_id].setChecked(False)
                    if skill_id in self.window_manager.active_windows:
                        self.window_manager.active_windows[skill_id].close()

                self.skill_permanent[skill_id] = True
                if skill_id not in self.window_manager.active_windows:
                    self.window_manager.create_permanent_window(skill_id)

            elif setting_type == "loop":
                # 開循環時取消常駐
                if self.skill_permanent.get(skill_id, False):
                    self.skill_permanent[skill_id] = False
                    if skill_id in self.permanent_vars:
                        self.permanent_vars[skill_id].setChecked(False)
                    if skill_id in self.window_manager.active_windows:
                        self.window_manager.active_windows[skill_id].close()

                # 循環模式：只標記狀態，等待按鍵觸發
                self.skill_loop[skill_id] = True
        else:
            if skill_id in self.window_manager.active_windows:
                self.window_manager.active_windows[skill_id].close()

            if setting_type == "permanent":
                self.skill_permanent[skill_id] = False
            elif setting_type == "loop":
                self.skill_loop[skill_id] = False

        self._save_config()
        self.auto_save_current_profile()

    def update_alert_setting(self, skill_id, var):
        """更新提前提示設定

        Args:
            skill_id: 技能 ID
            var:      觸發變更的 QCheckBox 實例
        """
        new_value = var.isChecked()
        self.skill_alert_enabled[skill_id] = new_value

        if skill_id in self.window_manager.active_windows:
            win = self.window_manager.active_windows[skill_id]
            win.alert_enabled        = new_value
            win.alert_before_seconds = self.get_alert_seconds(skill_id)

        self._save_config()
        self.auto_save_current_profile()

    def edit_alert_seconds(self, skill_id):
        """編輯技能的個別提前提示秒數

        Args:
            skill_id: 技能 ID
        """
        self.hotkey_manager.enabled = False
        current = self.skill_alert_seconds_overrides.get(
            skill_id, self.alert_before_seconds
        )

        new_val, ok = QInputDialog.getInt(
            self, "提前提示秒數",
            f"請輸入提前幾秒提示:\n"
            f"(全域預設: {self.alert_before_seconds}秒)\n"
            f"輸入 -1 恢復使用全域設定",
            current, -1, 999,
        )
        self.hotkey_manager.enabled = True

        if ok:
            if new_val == -1:
                self.skill_alert_seconds_overrides.pop(skill_id, None)
            else:
                self.skill_alert_seconds_overrides[skill_id] = new_val

            btn = self.alert_seconds_buttons.get(skill_id)
            if btn:
                if skill_id in self.skill_alert_seconds_overrides:
                    btn.setText(f"{self.skill_alert_seconds_overrides[skill_id]}s")
                    self._apply_btn_style(btn, bg=AppTheme.ACCENT_ORANGE)
                else:
                    btn.setText(f"{self.alert_before_seconds}s")
                    self._apply_btn_style(btn, bg=AppTheme.BG_TERTIARY)

            if skill_id in self.window_manager.active_windows:
                self.window_manager.active_windows[skill_id].alert_before_seconds = \
                    self.get_alert_seconds(skill_id)

            self.auto_save_current_profile()

    def toggle_all(self, setting_type):
        """切換所有技能的設定（全開或全關）

        Args:
            setting_type: 'permanent' | 'loop' | 'alert'
        """
        all_skills = list(self.skill_manager.get_all_skills().keys())

        if setting_type == "permanent":
            all_checked = all(self.skill_permanent.get(sid, False) for sid in all_skills)
            new_val = not all_checked

            if new_val:
                for sid in all_skills:
                    if self.skill_loop.get(sid, False):
                        self.skill_loop[sid] = False
                        if sid in self.loop_vars:
                            self.loop_vars[sid].setChecked(False)
                        if sid in self.window_manager.active_windows:
                            self.window_manager.active_windows[sid].close()

            for sid in all_skills:
                self._update_permanent_skill(sid, new_val)
                self.skill_permanent[sid] = new_val
                if sid in self.permanent_vars:
                    self.permanent_vars[sid].setChecked(new_val)

        elif setting_type == "loop":
            all_checked = all(self.skill_loop.get(sid, False) for sid in all_skills)
            new_val = not all_checked

            if new_val:
                for sid in all_skills:
                    if self.skill_permanent.get(sid, False):
                        self._update_permanent_skill(sid, False)
                        self.skill_permanent[sid] = False
                        if sid in self.permanent_vars:
                            self.permanent_vars[sid].setChecked(False)

            for sid in all_skills:
                self.skill_loop[sid] = new_val
                if sid in self.loop_vars:
                    self.loop_vars[sid].setChecked(new_val)
                if not new_val and sid in self.window_manager.active_windows:
                    self.window_manager.active_windows[sid].close()

        elif setting_type == "alert":
            all_checked = all(self.skill_alert_enabled.get(sid, False) for sid in all_skills)
            new_val = not all_checked

            for sid in all_skills:
                self.skill_alert_enabled[sid] = new_val
                if sid in self.alert_enabled_vars:
                    self.alert_enabled_vars[sid].setChecked(new_val)

        self._save_config()
        self.auto_save_current_profile()

    def clear_all_hotkeys(self):
        """清空所有快捷鍵和秒數覆寫（含確認對話框）"""
        reply = QMessageBox.question(
            self, "確認",
            "確定要清空所有技能的快捷鍵和自訂秒數嗎?\n（會恢復預設秒數）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for skill_id, skill in self.skill_manager.get_all_skills().items():
                skill["hotkey"] = ""
                original = self.get_original_cooldown(skill_id)
                if original:
                    skill["cooldown"] = original

                self.update_hotkey_display(skill_id, "", False)

                btn = self.cooldown_buttons.get(skill_id)
                if btn and original:
                    btn.setText(f"{original}秒")
                    self._apply_btn_style(
                        btn, bg=AppTheme.BG_TERTIARY, fg=AppTheme.TEXT_PRIMARY
                    )

            self.auto_save_current_profile()
            self.toast.show("已清空所有快捷鍵並恢復預設秒數", "success")

    def edit_cooldown(self, skill_id):
        """編輯技能冷卻時間

        Args:
            skill_id: 技能 ID
        """
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return

        self.hotkey_manager.enabled = False
        original = self.get_original_cooldown(skill_id)

        new_cooldown, ok = QInputDialog.getInt(
            self, "修改冷卻時間",
            f"請輸入 {skill['name']} 的新冷卻時間（秒）:\n(原始值: {original}秒)",
            skill["cooldown"], 1, 999,
        )
        self.hotkey_manager.enabled = True

        if ok and new_cooldown != skill["cooldown"]:
            skill["cooldown"] = new_cooldown

            btn = self.cooldown_buttons.get(skill_id)
            if btn:
                is_modified = original and new_cooldown != original
                btn.setText(f"{new_cooldown}秒")
                self._apply_btn_style(
                    btn,
                    bg = AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_TERTIARY,
                    fg = AppTheme.TEXT_PRIMARY,
                )

            self.auto_save_current_profile()

    def reset_cooldown(self, skill_id):
        """重置技能冷卻時間為預設值

        Args:
            skill_id: 技能 ID
        """
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return

        original = self.get_original_cooldown(skill_id)
        if not original or skill["cooldown"] == original:
            return

        skill["cooldown"] = original

        btn = self.cooldown_buttons.get(skill_id)
        if btn:
            btn.setText(f"{original}秒")
            self._apply_btn_style(btn, bg=AppTheme.BG_TERTIARY, fg=AppTheme.TEXT_PRIMARY)

        self.auto_save_current_profile()

    def reset_hotkey(self, skill_id):
        """重置技能快捷鍵

        Args:
            skill_id: 技能 ID
        """
        skill = self.skill_manager.get_skill(skill_id)
        if not skill or not skill.get("hotkey"):
            return

        skill["hotkey"] = ""
        self.update_hotkey_display(skill_id, "", False)
        self.auto_save_current_profile()

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
            "sound_manager":      self.sound_manager,
        }, app=self)

        dialog.exec()
        result = dialog.result

        if result:
            old_x, old_y = self.skill_start_x, self.skill_start_y

            self.skill_start_x        = result["x"]
            self.skill_start_y        = result["y"]
            self.enable_sound         = result["sound"]
            self.alert_before_seconds = result["alert_before_seconds"]
            self.window_size          = result["window_size"]
            self.global_sound         = result.get("global_sound", "")
            self.global_alert_sound   = result.get("global_alert_sound", "")

            self.config_manager.set_settings("skill_start_x",        self.skill_start_x)
            self.config_manager.set_settings("skill_start_y",        self.skill_start_y)
            self.config_manager.set_settings("enable_sound",         self.enable_sound)
            self.config_manager.set_settings("alert_before_seconds", self.alert_before_seconds)
            self.config_manager.set_settings("window_size",          self.window_size)
            self.config_manager.set_settings("global_sound",         self.global_sound)
            self.config_manager.set_settings("global_alert_sound",   self.global_alert_sound)
            self.config_manager.save()

            for window in self.window_manager.active_windows.values():
                window.enable_sound         = self.enable_sound
                window.alert_before_seconds = self.alert_before_seconds

            # 更新使用全域預設的提前秒數按鈕
            for skill_id, btn in self.alert_seconds_buttons.items():
                if skill_id not in self.skill_alert_seconds_overrides:
                    btn.setText(f"{self.alert_before_seconds}s")

            if old_x != self.skill_start_x or old_y != self.skill_start_y:
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

    def show_skill_detail(self, skill_id):
        """顯示技能細部設定對話框

        Args:
            skill_id: 技能 ID
        """
        self.hotkey_manager.enabled = False

        from src.ui.dialogs import SkillDetailDialog

        dialog = SkillDetailDialog(self, skill_id, self)
        dialog.exec()

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
        """獲取當前設定（用於保存配置檔）

        Returns:
            設定字典
        """
        cooldown_overrides = {}
        for skill_id, skill in self.skill_manager.get_all_skills().items():
            original = self.get_original_cooldown(skill_id)
            current  = skill.get("cooldown")
            if original and current != original:
                cooldown_overrides[skill_id] = current

        return {
            "hotkeys": {
                sid: skill.get("hotkey", "")
                for sid, skill in self.skill_manager.get_all_skills().items()
            },
            "permanent":              self.skill_permanent.copy(),
            "loop":                   self.skill_loop.copy(),
            "alert_enabled":          self.skill_alert_enabled.copy(),
            "cooldown_overrides":     cooldown_overrides,
            "alert_seconds_overrides":self.skill_alert_seconds_overrides.copy(),
            "sound_overrides":        self.skill_sound_overrides.copy(),
            "alert_sound_overrides":  self.skill_alert_sound_overrides.copy(),
        }

    def _apply_profile(self, profile_data):
        """套用配置（切換配置後呼叫）

        執行順序（先重置後套用，確保無舊配置殘留）：
          1. 所有技能 hotkey 清空、cooldown 還原為原始值
          2. 套用 profile 的 hotkeys / cooldown_overrides
          3. 套用 profile 的 permanent / loop / alert_enabled 與各 override

        Args:
            profile_data: 配置字典
        """
        self.current_profile_name = self.config_manager.get_current_profile()

        # 重置技能資料
        for skill_id, skill in self.skill_manager.get_all_skills().items():
            original = self.get_original_cooldown(skill_id)
            if original:
                skill["cooldown"] = original
            skill["hotkey"] = ""

        hotkeys = profile_data.get("hotkeys", {})
        for skill_id, hotkey in hotkeys.items():
            skill = self.skill_manager.get_skill(skill_id)
            if skill:
                skill["hotkey"] = hotkey

        cooldown_overrides = profile_data.get("cooldown_overrides", {})
        for skill_id, cooldown in cooldown_overrides.items():
            skill = self.skill_manager.get_skill(skill_id)
            if skill:
                skill["cooldown"] = cooldown

        self.skill_permanent               = profile_data.get("permanent", {}).copy()
        self.skill_loop                    = profile_data.get("loop", {}).copy()
        self.skill_alert_enabled           = profile_data.get("alert_enabled", {}).copy()
        self.skill_alert_seconds_overrides = profile_data.get("alert_seconds_overrides", {}).copy()
        self.skill_sound_overrides         = profile_data.get("sound_overrides", {}).copy()
        self.skill_alert_sound_overrides   = profile_data.get("alert_sound_overrides", {}).copy()

        for skill_id in self.skill_manager.get_all_skills():
            self.skill_permanent.setdefault(skill_id, False)
            self.skill_loop.setdefault(skill_id, False)
            self.skill_alert_enabled.setdefault(skill_id, False)

        self._save_config()
        self._reload_ui()

    def _reload_ui(self):
        """重新載入 UI（替換中央元件，等同 tkinter withdraw→rebuild→deiconify）"""
        self.hide()

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

        self._build_ui()
        self.window_manager.initialize_persistent_skills()
        self.show()

    def _update_permanent_skill(self, skill_id, is_permanent):
        """依照 is_permanent 開啟或關閉常駐視窗

        Args:
            skill_id:     技能 ID
            is_permanent: 目標狀態
        """
        was = self.skill_permanent.get(skill_id, False)
        if is_permanent and not was:
            if skill_id not in self.window_manager.active_windows:
                self.window_manager.create_permanent_window(skill_id)
        elif not is_permanent and was:
            if skill_id in self.window_manager.active_windows:
                self.window_manager.active_windows[skill_id].close()

    def _save_config(self):
        """保存配置到檔案（全域設定；skill_permanent 屬配置可變區，由 auto_save_current_profile 持久化）"""
        self.config_manager.save()

    def _check_for_updates(self):
        """在背景執行緒檢查更新，避免網路請求阻塞主執行緒"""
        def _worker():
            try:
                from src.ui.updater import Updater
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

    def closeEvent(self, event):
        """視窗關閉時停止所有背景服務並結束程式"""
        try:
            self.hotkey_manager.stop()
        except Exception:
            pass
        try:
            self.window_manager.close_all_windows()
        except Exception:
            pass
        event.accept()
        QApplication.quit()

    def run(self):
        """應用程式已由 main.py 的 qt_app.exec() 啟動，此方法保留相容性"""
        pass
