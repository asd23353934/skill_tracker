"""
主應用程式模組
CTk 主應用殼層，初始化管理器、組合佈局、業務邏輯協調
"""

import customtkinter as ctk
from tkinter import messagebox, simpledialog

from src.ui.theme import AppTheme
from src.ui.config_manager import ConfigManager
from src.ui.skill_manager import SkillManager
from src.ui.hotkey_manager import HotkeyManager
from src.ui.window_manager import WindowManager
from src.ui.sidebar import Sidebar
from src.ui.pages import SkillPage, MonsterPage, OverlayPage
from src.ui.helpers import resource_path
from src.ui.toast import ToastManager


class App(ctk.CTk):
    """主應用程式"""

    def __init__(self):
        super().__init__()

        # 版本號
        try:
            from version import get_version
            version_str = f" v{get_version()}"
        except Exception:
            version_str = ""

        self.title(f"技能追蹤器 - Artale 楓之谷{version_str}")
        self.attributes("-topmost", True)
        self.configure(fg_color=AppTheme.BG_PRIMARY)

        # 設定視窗圖示（落葉 icon）
        icon_path = resource_path("icon.ico")
        try:
            import os
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        # 先將視窗移到螢幕外 + 透明，等 UI 建構完成後再移回
        self.attributes("-alpha", 0.0)
        self.geometry("1660x900+100+50")

        # 初始化管理器
        try:
            self.config_manager = ConfigManager(resource_path("config.json"))
            self.skill_manager = SkillManager(self.config_manager)
        except Exception as e:
            messagebox.showerror("錯誤", f"初始化失敗: {e}")
            self.destroy()
            return

        # 初始化音效管理器
        from src.ui.sound_manager import SoundManager
        self.sound_manager = SoundManager()

        # 初始化狀態
        self._init_state()

        # 初始化子管理器
        self.hotkey_manager = HotkeyManager(self)
        self.window_manager = WindowManager(self)

        from src.ui.overlay_manager import OverlayManager
        self.overlay_manager = OverlayManager(self)

        # 建構 UI
        self._build_ui()

        # Toast 通知管理器（需在 UI 建構後初始化）
        self.toast = ToastManager(self)

        # 啟動服務
        self.hotkey_manager.start()
        self.window_manager.initialize_persistent_skills()

        # UI 建構完成，強制渲染後淡入顯示
        self.update_idletasks()
        self.attributes("-alpha", 0.96)

        # 檢查更新（非阻塞）
        self.after(1000, self._check_for_updates)

    def _init_state(self):
        """初始化狀態"""
        self.config_manager.ensure_default_profile()
        self.current_profile_name = self.config_manager.get_current_profile()

        profile_data = self.config_manager.load_profile(self.current_profile_name)
        settings = self.config_manager.config.get("settings", {})

        # 螢幕尺寸計算預設位置
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        default_x = screen_width // 2
        default_y = screen_height // 2

        # 設定
        self.player_name = settings.get("player_name", "玩家1")
        self.skill_start_x = settings.get("skill_start_x", default_x)
        self.skill_start_y = settings.get("skill_start_y", default_y)
        self.enable_sound = settings.get("enable_sound", True)
        self.window_alpha = 0.95
        self.window_size = settings.get("window_size", 64)
        self.alert_before_seconds = settings.get("alert_before_seconds", 0)

        # 音效設定（遷移舊音效檔名）
        self.global_sound = self.sound_manager.migrate_sound_filename(
            settings.get("global_sound", "")
        )
        self.global_alert_sound = self.sound_manager.migrate_sound_filename(
            settings.get("global_alert_sound", "")
        )

        # 技能設定
        if profile_data:
            self.skill_permanent = profile_data.get("permanent", {})
            self.skill_loop = profile_data.get("loop", {})
            self.skill_alert_enabled = profile_data.get("alert_enabled", {})
            self.skill_alert_seconds_overrides = profile_data.get("alert_seconds_overrides", {})
            self.skill_sound_overrides = {
                k: self.sound_manager.migrate_sound_filename(v)
                for k, v in profile_data.get("sound_overrides", {}).items()
            }
            self.skill_alert_sound_overrides = {
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
            self.skill_permanent = {}
            self.skill_loop = {}
            self.skill_alert_enabled = {}
            self.skill_alert_seconds_overrides = {}
            self.skill_sound_overrides = {}
            self.skill_alert_sound_overrides = {}

        # 預設值
        for skill_id in self.skill_manager.get_all_skills():
            self.skill_permanent.setdefault(skill_id, False)
            self.skill_loop.setdefault(skill_id, False)
            self.skill_alert_enabled.setdefault(skill_id, False)

        # 怪物 ID → 怪物字典的快取索引（O(1) 查詢）
        # 怪物清單來自 config，不會在執行時增刪；屬性變更為 in-place，索引始終有效
        self._monster_index: dict = {
            m["id"]: m
            for m in self.config_manager.config.get("monsters", [])
        }

        # UI 元件字典
        self.permanent_vars = {}
        self.loop_vars = {}
        self.alert_enabled_vars = {}
        self.hotkey_buttons = {}
        self.cooldown_buttons = {}
        self.alert_seconds_buttons = {}
        self.monster_respawn_buttons = {}

    def _build_ui(self):
        """建構主要 UI（側邊欄 + 頁面容器）"""
        # 最外層水平佈局
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)

        # 側邊欄（使用 place 避免展開時擠壓主內容）
        self.sidebar = Sidebar(self.main_frame, self, self._switch_page)
        self.sidebar.place(x=0, y=0, relheight=1.0)
        self.sidebar.lift()  # 確保側邊欄在最上層

        # 頁面容器（左側留出側邊欄收合寬度的間距）
        self.page_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.page_container.pack(
            side="left", fill="both", expand=True,
            padx=(AppTheme.SIDEBAR_COLLAPSED, 0),
        )

        # 使用 grid 堆疊所有頁面在同一格，切換時用 tkraise 提升
        self.page_container.rowconfigure(0, weight=1)
        self.page_container.columnconfigure(0, weight=1)

        # 建立頁面（全部用 grid 放在 row=0, column=0）
        self.pages = {}
        self.skill_page = SkillPage(self.page_container, self)
        self.skill_page.grid(row=0, column=0, sticky="nsew")
        self.pages["skill"] = self.skill_page

        self.monster_page = MonsterPage(self.page_container, self)
        self.monster_page.grid(row=0, column=0, sticky="nsew")
        self.pages["monster"] = self.monster_page

        self.overlay_page = OverlayPage(self.page_container, self)
        self.overlay_page.grid(row=0, column=0, sticky="nsew")
        self.pages["overlay"] = self.overlay_page

        # 預設顯示技能頁
        self._switch_page("skill")

    def _switch_page(self, page_name):
        """切換頁面（使用 tkraise 提升，不銷毀/重建，無閃爍）"""
        if page_name in self.pages:
            self.pages[page_name].tkraise()

    # ==================== 怪物 API ====================

    def get_monster(self, monster_id):
        """根據 ID 取得怪物資料（O(1) 索引查詢）"""
        return self._monster_index.get(monster_id)

    def get_monster_by_hotkey(self, key_name):
        """根據按鍵名稱取得怪物 ID"""
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
        """編輯怪物重生時間"""
        monster = self.get_monster(monster_id)
        if not monster:
            return

        self.hotkey_manager.enabled = False
        original = self.config_manager.get_original_respawn_time(monster_id)
        current = monster.get("respawn_time", 0)

        new_val = simpledialog.askinteger(
            "修改重生時間",
            f"請輸入 '{monster['name']}' 的重生時間（秒）:\n(原始值: {original}秒)",
            initialvalue=current,
            minvalue=1,
            maxvalue=9999,
            parent=self,
        )

        self.hotkey_manager.enabled = True

        if new_val is not None and new_val != current:
            monster["respawn_time"] = new_val
            self.save_monsters()

            btn = self.monster_respawn_buttons.get(monster_id)
            if btn:
                is_modified = original and new_val != original
                btn.configure(
                    text=f"{new_val}秒",
                    fg_color=AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_TERTIARY,
                    hover_color=AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_SECONDARY,
                )

    def reset_respawn_time(self, monster_id):
        """重置怪物重生時間為原始值"""
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
            btn.configure(
                text=f"{original}秒",
                fg_color=AppTheme.BG_TERTIARY,
                hover_color=AppTheme.BG_SECONDARY,
            )

    def update_monster_loop(self, monster_id, loop_value):
        """更新怪物循環設定"""
        monster = self.get_monster(monster_id)
        if not monster:
            return

        monster["loop"] = loop_value
        self.save_monsters()

        # 同步更新已開啟的視窗
        if monster_id in self.window_manager.active_windows:
            self.window_manager.active_windows[monster_id].is_loop = loop_value

    def update_monster_permanent(self, monster_id, permanent_value):
        """更新怪物常駐設定"""
        monster = self.get_monster(monster_id)
        if not monster:
            return

        monster["permanent"] = permanent_value
        self.save_monsters()

        if permanent_value:
            # 開啟常駐：若視窗不存在，建立 idle 狀態視窗
            if monster_id not in self.window_manager.active_windows:
                self.window_manager.create_permanent_monster_window(monster_id)
        else:
            # 關閉常駐：關閉現有視窗（若有）
            if monster_id in self.window_manager.active_windows:
                self.window_manager.active_windows[monster_id].close()

    # ==================== 公開 API (供子元件呼叫) ====================

    def get_original_cooldown(self, skill_id):
        """獲取技能的原始秒數"""
        for skill_data in self.config_manager.initial_skills:
            if skill_data["id"] == skill_id:
                return skill_data.get("cooldown")
        for item_data in self.config_manager.initial_items:
            if item_data["id"] == skill_id:
                return item_data.get("cooldown")
        return None

    def get_alert_seconds(self, skill_id):
        """獲取技能的提前提示秒數（優先使用個別設定，否則使用全域）

        Args:
            skill_id: 技能 ID

        Returns:
            提前提示的秒數
        """
        return self.skill_alert_seconds_overrides.get(
            skill_id, self.alert_before_seconds
        )

    def get_sound_for_skill(self, skill_id):
        """獲取技能的完成音效檔案名稱

        Args:
            skill_id: 技能 ID

        Returns:
            音效檔案名稱（空字串表示使用系統 beep）
        """
        override = self.skill_sound_overrides.get(skill_id)
        if override:
            return override
        return self.global_sound

    def get_alert_sound_for_skill(self, skill_id):
        """獲取技能的提前提示音效檔案名稱"""
        override = self.skill_alert_sound_overrides.get(skill_id)
        if override:
            return override
        return self.global_alert_sound

    def auto_save_current_profile(self):
        """自動保存當前配置"""
        current_settings = self._get_current_settings()
        self.config_manager.save_profile(self.current_profile_name, current_settings)

    def update_hotkey_display(self, skill_id, key_str, has_hotkey):
        """更新快捷鍵按鈕顯示"""
        btn = self.hotkey_buttons.get(skill_id)
        if btn:
            btn.configure(
                text=key_str if has_hotkey else "未設定",
                fg_color=AppTheme.ACCENT_YELLOW if has_hotkey else AppTheme.BG_TERTIARY,
                hover_color=AppTheme.ACCENT_YELLOW_HOVER if has_hotkey else AppTheme.BG_SECONDARY,
                text_color="#000000" if has_hotkey else AppTheme.TEXT_SECONDARY,
            )

    def update_skill_setting_exclusive(self, skill_id, setting_type, var):
        """更新技能設定（常駐 / 循環互斥）"""
        new_value = var.get()

        if new_value:
            if setting_type == "permanent":
                if self.skill_loop.get(skill_id, False):
                    self.skill_loop[skill_id] = False
                    if skill_id in self.loop_vars:
                        self.loop_vars[skill_id].set(False)
                    if skill_id in self.window_manager.active_windows:
                        self.window_manager.active_windows[skill_id].close()

                self.skill_permanent[skill_id] = True
                if skill_id not in self.window_manager.active_windows:
                    self.window_manager.create_permanent_window(skill_id)

            elif setting_type == "loop":
                if self.skill_permanent.get(skill_id, False):
                    self.skill_permanent[skill_id] = False
                    if skill_id in self.permanent_vars:
                        self.permanent_vars[skill_id].set(False)
                    if skill_id in self.window_manager.active_windows:
                        self.window_manager.active_windows[skill_id].close()

                # 循環模式：只標記狀態，不建立視窗（等待按鍵觸發）
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
        """更新提前提示設定"""
        new_value = var.get()
        self.skill_alert_enabled[skill_id] = new_value

        if skill_id in self.window_manager.active_windows:
            win = self.window_manager.active_windows[skill_id]
            win.alert_enabled = new_value
            win.alert_before_seconds = self.get_alert_seconds(skill_id)

        self._save_config()
        self.auto_save_current_profile()

    def edit_alert_seconds(self, skill_id):
        """編輯技能的個別提前提示秒數"""
        self.hotkey_manager.enabled = False
        current = self.skill_alert_seconds_overrides.get(
            skill_id, self.alert_before_seconds
        )

        new_val = simpledialog.askinteger(
            "提前提示秒數",
            f"請輸入提前幾秒提示:\n"
            f"(全域預設: {self.alert_before_seconds}秒)\n"
            f"輸入 -1 恢復使用全域設定",
            initialvalue=current,
            minvalue=-1,
            maxvalue=999,
            parent=self,
        )

        self.hotkey_manager.enabled = True

        if new_val is not None:
            if new_val == -1:
                self.skill_alert_seconds_overrides.pop(skill_id, None)
            else:
                self.skill_alert_seconds_overrides[skill_id] = new_val

            # 更新按鈕顯示
            btn = self.alert_seconds_buttons.get(skill_id)
            if btn:
                if skill_id in self.skill_alert_seconds_overrides:
                    btn.configure(
                        text=f"{self.skill_alert_seconds_overrides[skill_id]}s",
                        fg_color=AppTheme.ACCENT_ORANGE,
                    )
                else:
                    btn.configure(
                        text=f"{self.alert_before_seconds}s",
                        fg_color=AppTheme.BG_TERTIARY,
                    )

            # 更新活躍視窗
            if skill_id in self.window_manager.active_windows:
                win = self.window_manager.active_windows[skill_id]
                win.alert_before_seconds = self.get_alert_seconds(skill_id)

            self.auto_save_current_profile()

    def toggle_all(self, setting_type):
        """切換所有技能的設定"""
        all_skills = self.skill_manager.get_all_skills().keys()

        if setting_type == "permanent":
            all_checked = all(
                self.skill_permanent.get(sid, False) for sid in all_skills
            )
            new_val = not all_checked

            if new_val:
                for sid in all_skills:
                    if self.skill_loop.get(sid, False):
                        self.skill_loop[sid] = False
                        if sid in self.loop_vars:
                            self.loop_vars[sid].set(False)
                        if sid in self.window_manager.active_windows:
                            self.window_manager.active_windows[sid].close()

            for sid in all_skills:
                self._update_permanent_skill(sid, new_val)
                self.skill_permanent[sid] = new_val
                if sid in self.permanent_vars:
                    self.permanent_vars[sid].set(new_val)

        elif setting_type == "loop":
            all_checked = all(
                self.skill_loop.get(sid, False) for sid in all_skills
            )
            new_val = not all_checked

            if new_val:
                for sid in all_skills:
                    if self.skill_permanent.get(sid, False):
                        self._update_permanent_skill(sid, False)
                        self.skill_permanent[sid] = False
                        if sid in self.permanent_vars:
                            self.permanent_vars[sid].set(False)

            # 循環模式：只更新布林值，不建立視窗
            for sid in all_skills:
                self.skill_loop[sid] = new_val
                if sid in self.loop_vars:
                    self.loop_vars[sid].set(new_val)
                if not new_val and sid in self.window_manager.active_windows:
                    self.window_manager.active_windows[sid].close()

        elif setting_type == "alert":
            all_checked = all(
                self.skill_alert_enabled.get(sid, False) for sid in all_skills
            )
            new_val = not all_checked

            for sid in all_skills:
                self.skill_alert_enabled[sid] = new_val
                if sid in self.alert_enabled_vars:
                    self.alert_enabled_vars[sid].set(new_val)

        self._save_config()
        self.auto_save_current_profile()

    def clear_all_hotkeys(self):
        """清空所有快捷鍵和秒數覆寫"""
        if messagebox.askyesno(
            "確認",
            "確定要清空所有技能的快捷鍵和自訂秒數嗎?\n（會恢復預設秒數）",
            parent=self,
        ):
            for skill_id, skill in self.skill_manager.get_all_skills().items():
                skill["hotkey"] = ""
                original = self.get_original_cooldown(skill_id)
                if original:
                    skill["cooldown"] = original

                self.update_hotkey_display(skill_id, "", False)

                btn = self.cooldown_buttons.get(skill_id)
                if btn and original:
                    btn.configure(
                        text=f"{original}秒",
                        fg_color=AppTheme.BG_TERTIARY,
                        text_color=AppTheme.TEXT_PRIMARY,
                    )

            self.auto_save_current_profile()
            self.toast.show("已清空所有快捷鍵並恢復預設秒數", "success")

    def edit_cooldown(self, skill_id):
        """編輯技能冷卻時間"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return

        self.hotkey_manager.enabled = False
        original = self.get_original_cooldown(skill_id)

        new_cooldown = simpledialog.askinteger(
            "修改冷卻時間",
            f"請輸入 {skill['name']} 的新冷卻時間（秒）:\n(原始值: {original}秒)",
            initialvalue=skill["cooldown"],
            minvalue=1,
            maxvalue=999,
            parent=self,
        )

        self.hotkey_manager.enabled = True

        if new_cooldown is not None and new_cooldown != skill["cooldown"]:
            skill["cooldown"] = new_cooldown

            btn = self.cooldown_buttons.get(skill_id)
            if btn:
                is_modified = original and new_cooldown != original
                btn.configure(
                    text=f"{new_cooldown}秒",
                    fg_color=AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_TERTIARY,
                    text_color=AppTheme.TEXT_PRIMARY,
                )

            self.auto_save_current_profile()

    def reset_cooldown(self, skill_id):
        """重置技能冷卻時間為預設值"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return

        original = self.get_original_cooldown(skill_id)
        if not original or skill["cooldown"] == original:
            return

        skill["cooldown"] = original

        btn = self.cooldown_buttons.get(skill_id)
        if btn:
            btn.configure(
                text=f"{original}秒",
                fg_color=AppTheme.BG_TERTIARY,
                text_color=AppTheme.TEXT_PRIMARY,
            )

        self.auto_save_current_profile()

    def reset_hotkey(self, skill_id):
        """重置技能快捷鍵"""
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
            "x": self.skill_start_x,
            "y": self.skill_start_y,
            "sound": self.enable_sound,
            "alert_before_seconds": self.alert_before_seconds,
            "window_size": self.window_size,
            "global_sound": self.global_sound,
            "global_alert_sound": self.global_alert_sound,
            "sound_manager": self.sound_manager,
        })

        result = dialog.show()

        if result:
            old_x, old_y = self.skill_start_x, self.skill_start_y

            self.skill_start_x = result["x"]
            self.skill_start_y = result["y"]
            self.enable_sound = result["sound"]
            self.alert_before_seconds = result["alert_before_seconds"]
            self.window_size = result["window_size"]
            self.global_sound = result.get("global_sound", "")
            self.global_alert_sound = result.get("global_alert_sound", "")

            self.config_manager.set_settings("skill_start_x", self.skill_start_x)
            self.config_manager.set_settings("skill_start_y", self.skill_start_y)
            self.config_manager.set_settings("enable_sound", self.enable_sound)
            self.config_manager.set_settings("alert_before_seconds", self.alert_before_seconds)
            self.config_manager.set_settings("window_size", self.window_size)
            self.config_manager.set_settings("global_sound", self.global_sound)
            self.config_manager.set_settings("global_alert_sound", self.global_alert_sound)
            self.config_manager.save()

            for window in self.window_manager.active_windows.values():
                window.enable_sound = self.enable_sound
                window.alert_before_seconds = self.alert_before_seconds

            # 更新所有使用全域的提前秒數按鈕
            for skill_id, btn in self.alert_seconds_buttons.items():
                if skill_id not in self.skill_alert_seconds_overrides:
                    btn.configure(text=f"{self.alert_before_seconds}s")

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
        result = dialog.show()

        if result:
            self._apply_profile(result)

        self.hotkey_manager.enabled = True

    def show_skill_detail(self, skill_id):
        """顯示技能細部設定對話框"""
        self.hotkey_manager.enabled = False

        from src.ui.dialogs import SkillDetailDialog

        dialog = SkillDetailDialog(self, skill_id, self)
        dialog.show()

        self.hotkey_manager.enabled = True

    def show_update_dialog(self):
        """顯示更新對話框"""
        if not hasattr(self, "update_info"):
            return

        from src.ui.dialogs.update_dialog import UpdateDialog

        dialog = UpdateDialog(self, self.update_info)
        dialog.show()

    # ==================== 內部方法 ====================

    def _get_current_settings(self):
        """獲取當前設定"""
        cooldown_overrides = {}
        for skill_id, skill in self.skill_manager.get_all_skills().items():
            original = self.get_original_cooldown(skill_id)
            current = skill.get("cooldown")
            if original and current != original:
                cooldown_overrides[skill_id] = current

        return {
            "hotkeys": {
                sid: skill.get("hotkey", "")
                for sid, skill in self.skill_manager.get_all_skills().items()
            },
            "permanent": self.skill_permanent.copy(),
            "loop": self.skill_loop.copy(),
            "alert_enabled": self.skill_alert_enabled.copy(),
            "cooldown_overrides": cooldown_overrides,
            "alert_seconds_overrides": self.skill_alert_seconds_overrides.copy(),
            "sound_overrides": self.skill_sound_overrides.copy(),
            "alert_sound_overrides": self.skill_alert_sound_overrides.copy(),
        }

    def _apply_profile(self, profile_data):
        """套用配置"""
        self.current_profile_name = self.config_manager.get_current_profile()

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

        self.skill_permanent = profile_data.get("permanent", {}).copy()
        self.skill_loop = profile_data.get("loop", {}).copy()
        self.skill_alert_enabled = profile_data.get("alert_enabled", {}).copy()
        self.skill_alert_seconds_overrides = profile_data.get("alert_seconds_overrides", {}).copy()
        self.skill_sound_overrides = profile_data.get("sound_overrides", {}).copy()
        self.skill_alert_sound_overrides = profile_data.get("alert_sound_overrides", {}).copy()

        for skill_id in self.skill_manager.get_all_skills():
            self.skill_permanent.setdefault(skill_id, False)
            self.skill_loop.setdefault(skill_id, False)
            self.skill_alert_enabled.setdefault(skill_id, False)

        self._save_config()
        self._reload_ui()

    def _reload_ui(self):
        """重新載入 UI（隱藏 → 清理 → 重建，避免殘影）"""
        # 先隱藏主視窗內容，避免清理時閃爍
        self.withdraw()

        for widget in self.winfo_children():
            widget.destroy()

        self.permanent_vars = {}
        self.loop_vars = {}
        self.alert_enabled_vars = {}
        self.hotkey_buttons = {}
        self.cooldown_buttons = {}
        self.alert_seconds_buttons = {}
        self.monster_respawn_buttons = {}

        self._build_ui()
        self.window_manager.initialize_persistent_skills()

        # 重建完成後再顯示
        self.update_idletasks()
        self.deiconify()

    def _update_permanent_skill(self, skill_id, is_permanent):
        """更新常駐技能"""
        was = self.skill_permanent.get(skill_id, False)
        if is_permanent and not was:
            if skill_id not in self.window_manager.active_windows:
                self.window_manager.create_permanent_window(skill_id)
        elif not is_permanent and was:
            if skill_id in self.window_manager.active_windows:
                self.window_manager.active_windows[skill_id].close()

    def _save_config(self):
        """保存配置"""
        self.config_manager.set_settings("skill_permanent", self.skill_permanent)
        self.config_manager.save()

    def _check_for_updates(self):
        """在背景執行緒檢查更新，避免網路請求阻塞主執行緒"""
        import threading

        def _worker():
            try:
                from src.ui.updater import Updater
                updater = Updater()
                update_info = updater.check_for_updates()
                if update_info.get("available"):
                    # 回到主執行緒更新 UI（tkinter 不是執行緒安全的）
                    self.after(0, lambda: self._on_update_found(update_info))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _on_update_found(self, update_info):
        """有新版本時在主執行緒顯示更新按鈕"""
        self.update_info = update_info
        try:
            self.header.show_update_button()
        except Exception:
            pass

    def run(self):
        """運行應用程式"""
        self.mainloop()
