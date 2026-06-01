"""
AppCoreMixin — V1 App 與 V2AppContext 共用的 domain backing。

職責：
    - 建立完整的 Manager / Service 鏈（SkillManager / SkillService /
      HotkeyManager / WindowManager / SoundManager / OverlayManager …）
    - 載入當前 profile 狀態（同步到 SkillService，並暴露常用全域設定屬性）
    - 提供 SkillService 委派 property（skill_permanent / skill_loop / …）
    - 初始化 V1/V2 共用的 widget 登錄 dict（cooldown_buttons /
      hotkey_buttons / skill_card_widgets …）

不負責：
    - UI 建構（Header / Sidebar / Pages 由 V1 App 自行 _build_ui）
    - Toast 系統（V1 用 ToastManager；V2 用 NoopToast）
    - hotkey_manager.start() / window_manager.initialize_persistent_skills()
      — 由呼叫方在適當時機觸發（V1 在 __init__ 末段；V2 視需要）
    - QMessageBox 例外處理（V1 自行包 try）

繼承方式：
    class App(QMainWindow, AppCoreMixin):
        def __init__(self):
            super().__init__()
            ...
            self._init_domain_backing(self.config_manager)

    class V2AppContext(AppCoreMixin):
        def __init__(self):
            cm = ConfigManager(resource_path("config.json"))
            self._init_domain_backing(cm)
"""

from PySide6.QtWidgets import QApplication, QInputDialog, QWidget

from src.infrastructure.repositories import SkillRepository
from src.infrastructure.skill_loader import SkillLoader
from src.infrastructure.sound_manager import SoundManager
from src.domain.services import SkillService, MonsterService
from src.ui.skill_pixmap_cache import SkillPixmapCache
from src.ui.hotkey_manager import HotkeyManager
from src.ui.window_manager import WindowManager
from src.ui.overlay_manager import OverlayManager
from src.ui.theme import AppTheme


class AppCoreMixin:
    """V1 App / V2AppContext 共用的 domain backing。

    呼叫 `_init_domain_backing(config_manager)` 後，self 上會有：
        config_manager / skill_loader / skill_manager / skill_repo /
        sound_manager / skill_service / monster_service /
        hotkey_manager / window_manager / overlay_manager
        + current_profile_name / 各全域設定屬性 + widget 登錄 dict

    注意：呼叫前 QApplication 必須已存在（_load_profile_state 取
    primaryScreen geometry 作預設視窗位置）。
    """

    # --------------------------------------------------
    # SkillService 委派屬性（向後相容；實際狀態由 SkillService 持有）
    # --------------------------------------------------

    @property
    def skill_permanent(self):
        return self.skill_service._permanent

    @skill_permanent.setter
    def skill_permanent(self, value):
        self.skill_service._permanent = value

    @property
    def skill_loop(self):
        return self.skill_service._loop

    @skill_loop.setter
    def skill_loop(self, value):
        self.skill_service._loop = value

    @property
    def skill_alert_enabled(self):
        return self.skill_service._alert_enabled

    @skill_alert_enabled.setter
    def skill_alert_enabled(self, value):
        self.skill_service._alert_enabled = value

    @property
    def skill_alert_seconds_overrides(self):
        return self.skill_service._alert_seconds_overrides

    @skill_alert_seconds_overrides.setter
    def skill_alert_seconds_overrides(self, value):
        self.skill_service._alert_seconds_overrides = value

    @property
    def skill_sound_overrides(self):
        return self.skill_service._sound_overrides

    @skill_sound_overrides.setter
    def skill_sound_overrides(self, value):
        self.skill_service._sound_overrides = value

    @property
    def skill_alert_sound_overrides(self):
        return self.skill_service._alert_sound_overrides

    @skill_alert_sound_overrides.setter
    def skill_alert_sound_overrides(self, value):
        self.skill_service._alert_sound_overrides = value

    # --------------------------------------------------
    # 單一進入點：建構完整 domain 鏈
    # --------------------------------------------------

    def _init_domain_backing(self, config_manager):
        """建立 Manager / Service 鏈 + 載入 profile + 初始化 widget 登錄 dict。

        Args:
            config_manager: 已 ready 的 ConfigManager 實例
        """
        self.config_manager = config_manager

        # 1. 領域層
        self.skill_loader   = SkillLoader(config_manager)
        self.skill_manager  = SkillPixmapCache(self.skill_loader)
        self.skill_repo     = SkillRepository(config_manager)
        self.sound_manager  = SoundManager()
        self.skill_service  = SkillService(
            skill_repo=self.skill_repo,
            skill_loader=self.skill_loader,
        )
        self.monster_service = MonsterService(config_manager)

        # 2. 第一次啟動：用 mixin factory default 自建「預設配置」；之後都跳過
        default_name = "預設配置"
        if default_name not in config_manager.list_profiles():
            config_manager.save_profile(
                default_name, self._build_factory_default_profile_state()
            )
        # safety net：若仍缺（例如儲存失敗）由 ConfigManager 用空殼補
        config_manager.ensure_default_profile()
        self._load_profile_state(config_manager.get_current_profile())

        # 3. 控制管理器（self 作為 owner）
        self.hotkey_manager  = HotkeyManager(self)
        self.window_manager  = WindowManager(self)
        self.overlay_manager = OverlayManager(self)

        # 4. UI widget 登錄 dict（V1 / V2 共用）
        self.permanent_vars               = {}
        self.loop_vars                    = {}
        self.alert_enabled_vars           = {}
        self.hotkey_buttons               = {}
        self.cooldown_buttons             = {}
        self.alert_seconds_buttons        = {}
        self.skill_card_widgets           = {}
        self.monster_respawn_buttons      = {}
        self.monster_alert_before_buttons = {}

    def _load_profile_state(self, profile_name):
        """載入指定 profile，同步到 SkillService 與全域設定屬性。

        被 _init_domain_backing 呼叫；亦可在切 profile 時重呼。
        """
        cm = self.config_manager
        self.current_profile_name = profile_name

        profile_data = cm.load_profile(profile_name)
        settings = cm.config.get("settings", {})

        # 螢幕尺寸 → 計算預設技能視窗位置
        screen = QApplication.primaryScreen().geometry()
        default_x = screen.width() // 2
        default_y = screen.height() // 2

        self.player_name          = settings.get("player_name") or "玩家1"
        # skill_start_x/y 在 DEFAULT_USER_SETTINGS 預設為 None（QApplication 尚未建時無法算螢幕中心），
        # 這裡第一次跑才以 primary screen 計算 fallback；`or` 處理 None / 0 / 缺席
        self.skill_start_x        = settings.get("skill_start_x") or default_x
        self.skill_start_y        = settings.get("skill_start_y") or default_y
        # 完成音 / 提前音各自獨立開關；舊檔僅有 enable_sound 時兩者沿用其值（遷移）
        _legacy_enable_sound      = settings.get("enable_sound", True)
        self.enable_end_sound     = settings.get("enable_end_sound", _legacy_enable_sound)
        self.enable_alert_sound   = settings.get("enable_alert_sound", _legacy_enable_sound)
        self.enable_sound         = self.enable_end_sound or self.enable_alert_sound
        self.sound_volume         = settings.get("sound_volume", 100)
        self.sound_manager.set_volume(self.sound_volume / 100.0)
        self.window_alpha         = 0.95
        self.window_size          = settings.get("window_size", 64)
        self.alert_before_seconds = settings.get("alert_before_seconds", 0)

        # 快捷鍵限定前景視窗
        self.hotkey_app_filter_enabled = settings.get("hotkey_app_filter_enabled", False)
        self.hotkey_app_target_exe     = settings.get("hotkey_app_target_exe", "")
        self.hotkey_app_target_label   = settings.get("hotkey_app_target_label", "")

        # 音效設定（遷移舊檔名）
        self.global_sound = self.sound_manager.migrate_sound_filename(
            settings.get("global_sound", "")
        )
        self.global_alert_sound = self.sound_manager.migrate_sound_filename(
            settings.get("global_alert_sound", "")
        )

        # 同步到 SkillService
        self.skill_service.alert_before_seconds = self.alert_before_seconds
        self.skill_service.global_sound = self.global_sound
        self.skill_service.global_alert_sound = self.global_alert_sound

        if profile_data:
            migrated_data = dict(profile_data)
            migrated_data["sound_overrides"] = {
                k: self.sound_manager.migrate_sound_filename(v)
                for k, v in profile_data.get("sound_overrides", {}).items()
            }
            migrated_data["alert_sound_overrides"] = {
                k: self.sound_manager.migrate_sound_filename(v)
                for k, v in profile_data.get("alert_sound_overrides", {}).items()
            }
            self.skill_service.load_from_profile(migrated_data)
        else:
            self.skill_service.reset_all_to_defaults()

    # --------------------------------------------------
    # 內部 UI helper（V1 widget styling；V2 chip 走自有 _v2_apply_accent）
    # --------------------------------------------------

    @staticmethod
    def _apply_btn_style(btn, bg=None, fg=None, hover=None):
        """動態設定 QPushButton 內聯樣式；V2 chip 透過 _v2_apply_accent 接管。"""
        if hasattr(btn, "_v2_apply_accent"):
            btn._v2_apply_accent(bg)
            return

        _bg  = bg or AppTheme.BG_TERTIARY
        _fg  = fg or AppTheme.TEXT_PRIMARY
        _bdr = AppTheme.GOLD_MUTED
        style = (
            f"QPushButton {{"
            f" background-color:{_bg}; color:{_fg};"
            f" border:1px solid {_bdr}; border-radius:3px;"
            f" padding:0px 4px; font-size:10px; font-weight:bold; }}"
        )
        if hover:
            style += f" QPushButton:hover {{ background-color:{hover}; }}"
        btn.setStyleSheet(style)

    def _save_config(self):
        """保存全域設定（profile 狀態由 auto_save_current_profile 負責）"""
        self.config_manager.save()

    def _update_permanent_skill(self, skill_id, is_permanent):
        """依 is_permanent 開關常駐視窗"""
        was = self.skill_permanent.get(skill_id, False)
        if is_permanent and not was:
            if skill_id not in self.window_manager.active_windows:
                self.window_manager.create_permanent_window(skill_id)
        elif not is_permanent and was:
            if skill_id in self.window_manager.active_windows:
                self.window_manager.active_windows[skill_id].close()

    def _dialog_parent(self):
        """V1 App 為 QMainWindow 自身；V2AppContext 取當前 active window。"""
        if isinstance(self, QWidget):
            return self
        return QApplication.activeWindow()

    # --------------------------------------------------
    # 12 個共通 App 互動方法（V1 / V2 共用）
    # --------------------------------------------------

    def get_original_cooldown(self, skill_id):
        """獲取技能的原始冷卻秒數（委派到 SkillService）"""
        return self.skill_service.get_original_cooldown(skill_id)

    def get_alert_seconds(self, skill_id):
        """獲取技能的提前提示秒數（委派到 SkillService）"""
        return self.skill_service.get_alert_seconds(skill_id)

    def get_sound_for_skill(self, skill_id):
        """獲取技能的完成音效檔名（委派到 SkillService）"""
        return self.skill_service.get_sound(skill_id)

    def get_alert_sound_for_skill(self, skill_id):
        """獲取技能的提前提示音效檔名（委派到 SkillService）"""
        return self.skill_service.get_alert_sound(skill_id)

    def get_monster(self, monster_id):
        """根據 ID 取得怪物資料（委派到 MonsterService）"""
        return self.monster_service.get(monster_id)

    def get_monster_by_hotkey(self, key_name):
        """根據按鍵名稱取得怪物 ID（委派到 MonsterService）"""
        monster = self.monster_service.get_by_hotkey(key_name)
        return monster["id"] if monster else None

    def get_all_monsters(self):
        """取得所有怪物資料（委派到 MonsterService）"""
        return self.monster_service.get_all()

    def save_monsters(self):
        """儲存怪物資料到 config.json（委派到 MonsterService）"""
        self.monster_service.save()

    def auto_save_current_profile(self):
        """自動保存當前配置到檔案（委派到 SkillService）"""
        current_settings = self.skill_service.serialize_to_dict()
        self.config_manager.save_profile(self.current_profile_name, current_settings)

    def update_hotkey_display(self, skill_id, key_str, has_hotkey):
        """更新快捷鍵按鈕顯示"""
        btn = self.hotkey_buttons.get(skill_id)
        if btn:
            btn.setText(key_str if has_hotkey else "未設定")
            self._apply_btn_style(
                btn,
                bg    = AppTheme.ACCENT_YELLOW       if has_hotkey else AppTheme.BG_TERTIARY,
                fg    = "#000000"                    if has_hotkey else AppTheme.TEXT_SECONDARY,
                hover = AppTheme.ACCENT_YELLOW_HOVER if has_hotkey else AppTheme.BG_SECONDARY,
            )
        # V2：通知 SkillPageV2 同步「已設按鍵 / 總數」chip、頁首橫軸、單卡背景
        page = getattr(self, "skill_page_v2", None)
        if page is not None:
            page.refresh_status_counts()
            page.refresh_card(skill_id)

    def update_skill_setting_exclusive(self, skill_id, setting_type, var):
        """更新技能設定（常駐 / 循環互斥，委派到 SkillService）"""
        new_value = var.isChecked()

        if setting_type == "permanent":
            result = self.skill_service.set_permanent(skill_id, new_value)
        elif setting_type == "loop":
            result = self.skill_service.set_loop(skill_id, new_value)
        else:
            return

        if not result["loop"] and skill_id in self.loop_vars:
            self.loop_vars[skill_id].setChecked(False)
        if not result["permanent"] and skill_id in self.permanent_vars:
            self.permanent_vars[skill_id].setChecked(False)

        if new_value:
            if setting_type == "permanent":
                if skill_id in self.window_manager.active_windows:
                    self.window_manager.active_windows[skill_id].close()
                if skill_id not in self.window_manager.active_windows:
                    self.window_manager.create_permanent_window(skill_id)
            elif setting_type == "loop":
                if skill_id in self.window_manager.active_windows:
                    self.window_manager.active_windows[skill_id].close()
        else:
            if skill_id in self.window_manager.active_windows:
                self.window_manager.active_windows[skill_id].close()

        self._save_config()
        self.auto_save_current_profile()

    def update_alert_setting(self, skill_id, var):
        """更新提前提示設定（委派到 SkillService）"""
        new_value = var.isChecked()
        self.skill_service.set_alert_enabled(skill_id, new_value)

        if skill_id in self.window_manager.active_windows:
            win = self.window_manager.active_windows[skill_id]
            win.alert_enabled        = new_value
            win.alert_before_seconds = self.get_alert_seconds(skill_id)

        self._save_config()
        self.auto_save_current_profile()

    def edit_alert_seconds(self, skill_id):
        """編輯技能的個別提前提示秒數"""
        self.hotkey_manager.enabled = False
        current = self.skill_service.get_alert_seconds(skill_id)

        new_val, ok = QInputDialog.getInt(
            self._dialog_parent(), "提前提示秒數",
            f"請輸入提前幾秒提示:\n"
            f"(全域預設: {self.alert_before_seconds}秒)\n"
            f"輸入 -1 恢復使用全域設定",
            current, -1, 999,
        )
        self.hotkey_manager.enabled = True

        if ok:
            if new_val == -1:
                self.skill_service.clear_alert_seconds_override(skill_id)
            else:
                self.skill_service.set_alert_seconds_override(skill_id, new_val)

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
        """切換所有技能的設定（全開或全關，委派到 SkillService）"""
        if setting_type == "permanent":
            results = self.skill_service.toggle_all_permanent()
            new_val = next(iter(results.values()), False)

            if new_val:
                for sid in results:
                    if sid in self.loop_vars:
                        self.loop_vars[sid].setChecked(False)
                    if sid in self.window_manager.active_windows:
                        self.window_manager.active_windows[sid].close()

            for sid, val in results.items():
                self._update_permanent_skill(sid, val)
                if sid in self.permanent_vars:
                    self.permanent_vars[sid].setChecked(val)

        elif setting_type == "loop":
            results = self.skill_service.toggle_all_loop()
            new_val = next(iter(results.values()), False)

            if new_val:
                for sid in results:
                    if sid in self.permanent_vars:
                        self.permanent_vars[sid].setChecked(False)
                    if sid in self.window_manager.active_windows:
                        self.window_manager.active_windows[sid].close()

            for sid, val in results.items():
                if sid in self.loop_vars:
                    self.loop_vars[sid].setChecked(val)
                if not val and sid in self.window_manager.active_windows:
                    self.window_manager.active_windows[sid].close()

        elif setting_type == "alert":
            results = self.skill_service.toggle_all_alert()
            for sid, val in results.items():
                if sid in self.alert_enabled_vars:
                    self.alert_enabled_vars[sid].setChecked(val)

        self._save_config()
        self.auto_save_current_profile()

    def edit_cooldown(self, skill_id):
        """編輯技能冷卻時間（委派到 SkillService）"""
        skill = self.skill_loader.get_skill(skill_id)
        if not skill:
            return

        self.hotkey_manager.enabled = False
        original = self.skill_service.get_original_cooldown(skill_id)

        new_cooldown, ok = QInputDialog.getInt(
            self._dialog_parent(), "修改冷卻時間",
            f"請輸入 {skill['name']} 的新冷卻時間（秒）:\n(原始值: {original}秒)",
            skill["cooldown"], 1, 999,
        )
        self.hotkey_manager.enabled = True

        if ok and new_cooldown != skill["cooldown"]:
            is_modified = self.skill_service.set_cooldown_override(skill_id, new_cooldown)

            btn = self.cooldown_buttons.get(skill_id)
            if btn:
                btn.setText(f"{new_cooldown}秒")
                self._apply_btn_style(
                    btn,
                    bg = AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_TERTIARY,
                    fg = AppTheme.TEXT_PRIMARY,
                )

            self.auto_save_current_profile()

    def reset_cooldown(self, skill_id):
        """重置技能冷卻時間為預設值（委派到 SkillService）"""
        original = self.skill_service.get_original_cooldown(skill_id)
        skill = self.skill_loader.get_skill(skill_id)
        if not skill or not original or skill["cooldown"] == original:
            return

        self.skill_service.clear_cooldown_override(skill_id)

        btn = self.cooldown_buttons.get(skill_id)
        if btn:
            btn.setText(f"{original}秒")
            self._apply_btn_style(btn, bg=AppTheme.BG_TERTIARY, fg=AppTheme.TEXT_PRIMARY)

        self.auto_save_current_profile()

    def reset_hotkey(self, skill_id):
        """重置技能快捷鍵（委派到 SkillService）"""
        skill = self.skill_loader.get_skill(skill_id)
        if not skill or not skill.get("hotkey"):
            return

        self.skill_service.clear_hotkey(skill_id)
        self.update_hotkey_display(skill_id, "", False)
        self.auto_save_current_profile()

    # --------------------------------------------------
    # 8 個共通怪物互動方法

    def edit_respawn_time(self, monster_id):
        """編輯怪物重生時間（委派到 MonsterService）"""
        monster = self.get_monster(monster_id)
        if not monster:
            return

        self.hotkey_manager.enabled = False
        original = self.monster_service.get_original_respawn_time(monster_id)
        current  = monster.get("respawn_time", 0)

        new_val, ok = QInputDialog.getInt(
            self._dialog_parent(), "修改重生時間",
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
        """重置怪物重生時間為原始值（委派到 MonsterService）"""
        original = self.monster_service.reset_respawn_time(monster_id)
        if original is None:
            return

        self.monster_service.save()

        btn = self.monster_respawn_buttons.get(monster_id)
        if btn:
            btn.setText(f"{original}秒")
            self._apply_btn_style(btn, bg=AppTheme.BG_TERTIARY, hover=AppTheme.BG_SECONDARY)

    def reset_monster_hotkey(self, monster_id):
        """重置怪物快捷鍵（委派到 MonsterService）"""
        monster = self.get_monster(monster_id)
        if not monster or not monster.get("hotkey"):
            return
        self.monster_service.clear_hotkey(monster_id)
        self.monster_service.save()
        card = self.monster_page.cards.get(monster_id) if hasattr(self, "monster_page") else None
        if card:
            updater = getattr(card, "set_hotkey_text", None) or card.update_hotkey_display
            self.after(0, lambda u=updater: u("", False))

    def edit_monster_alert_before(self, monster_id):
        """編輯怪物提前提示秒數（委派到 MonsterService）"""
        monster = self.get_monster(monster_id)
        if not monster:
            return

        self.hotkey_manager.enabled = False
        current = monster.get("alert_before", 0)

        new_val, ok = QInputDialog.getInt(
            self._dialog_parent(), "提前提示秒數",
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
        """更新怪物提前提示聲音（委派到 MonsterService）"""
        self.monster_service.set_alert_sound(monster_id, filename)
        self.monster_service.save()

    def update_monster_end_sound(self, monster_id, filename: str):
        """更新怪物結束聲音（委派到 MonsterService）"""
        self.monster_service.set_sound(monster_id, filename)
        self.monster_service.save()

    def update_monster_loop(self, monster_id, loop_value):
        """更新怪物循環設定（委派到 MonsterService）"""
        self.monster_service.set_loop(monster_id, loop_value)
        self.monster_service.save()
        if monster_id in self.window_manager.active_windows:
            self.window_manager.active_windows[monster_id].is_loop = loop_value

    def update_monster_permanent(self, monster_id, permanent_value):
        """更新怪物常駐設定（委派到 MonsterService）"""
        self.monster_service.set_permanent(monster_id, permanent_value)
        self.monster_service.save()
        if permanent_value:
            if monster_id not in self.window_manager.active_windows:
                self.window_manager.create_permanent_monster_window(monster_id)
        else:
            if monster_id in self.window_manager.active_windows:
                self.window_manager.active_windows[monster_id].close()

    # --------------------------------------------------
    # Profile 切換（V2 dropdown 用；V1 走 ProfileManagerDialog）
    # --------------------------------------------------

    def apply_settings(self, result: dict) -> None:
        """套用 SettingsDialog 結果（V1 / V2 共用）

        result 必須含以下 key：
            x / y / enable_end_sound / enable_alert_sound / alert_before_seconds /
            window_size / global_sound / global_alert_sound / sound_volume
        """
        old_window_size = self.window_size
        old_xy          = (self.skill_start_x, self.skill_start_y)

        # 1. 寫回 self
        self.skill_start_x        = result["x"]
        self.skill_start_y        = result["y"]
        self.enable_end_sound     = result.get("enable_end_sound", True)
        self.enable_alert_sound   = result.get("enable_alert_sound", True)
        self.enable_sound         = self.enable_end_sound or self.enable_alert_sound
        self.alert_before_seconds = result["alert_before_seconds"]
        self.window_size          = result["window_size"]
        self.global_sound         = result.get("global_sound", "")
        self.global_alert_sound   = result.get("global_alert_sound", "")
        self.sound_volume         = result.get("sound_volume", 100)
        self.hotkey_app_filter_enabled = result.get(
            "hotkey_app_filter_enabled", self.hotkey_app_filter_enabled)
        self.hotkey_app_target_exe     = result.get(
            "hotkey_app_target_exe", self.hotkey_app_target_exe)
        self.hotkey_app_target_label   = result.get(
            "hotkey_app_target_label", self.hotkey_app_target_label)

        # 2. 音量同步
        self.sound_manager.set_volume(self.sound_volume / 100.0)

        # 3. 同步全域設定到 SkillService
        self.skill_service.alert_before_seconds = self.alert_before_seconds
        self.skill_service.global_sound         = self.global_sound
        self.skill_service.global_alert_sound   = self.global_alert_sound

        # 4. 持久化
        cm = self.config_manager
        cm.set_settings("skill_start_x",        self.skill_start_x)
        cm.set_settings("skill_start_y",        self.skill_start_y)
        cm.set_settings("enable_sound",         self.enable_sound)
        cm.set_settings("enable_end_sound",     self.enable_end_sound)
        cm.set_settings("enable_alert_sound",   self.enable_alert_sound)
        cm.set_settings("alert_before_seconds", self.alert_before_seconds)
        cm.set_settings("window_size",          self.window_size)
        cm.set_settings("global_sound",         self.global_sound)
        cm.set_settings("global_alert_sound",   self.global_alert_sound)
        cm.set_settings("sound_volume",         self.sound_volume)
        cm.set_settings("hotkey_app_filter_enabled", self.hotkey_app_filter_enabled)
        cm.set_settings("hotkey_app_target_exe",     self.hotkey_app_target_exe)
        cm.set_settings("hotkey_app_target_label",   self.hotkey_app_target_label)
        cm.save()

        # 5. 更新使用全域預設的提前秒數按鈕（沒被個別 override 的）
        for sid, btn in self.alert_seconds_buttons.items():
            if sid not in self.skill_alert_seconds_overrides:
                btn.setText(f"{self.alert_before_seconds}s")

        # 6. window_manager 條件式同步
        if self.window_size != old_window_size:
            self.window_manager.close_all()
            self.window_manager.initialize_persistent_skills()
        else:
            for sid, win in self.window_manager.active_windows.items():
                win.enable_end_sound   = self.enable_end_sound
                win.enable_alert_sound = self.enable_alert_sound
                self.window_manager.refresh_window_sound_params(sid)
            if (self.skill_start_x, self.skill_start_y) != old_xy:
                self.window_manager.reposition_all()

        # 7. toast 回饋
        toast = getattr(self, "toast", None)
        if toast is not None:
            toast.show("設定已保存並套用", "success")

    # --------------------------------------------------
    # Profile CRUD（V1 ProfileManagerDialog / V2 ProfileManagerDialogV2 共用）
    # --------------------------------------------------

    def _refresh_skill_page_v2_profile_selector(self):
        """變更 profile 列表後通知 V2 skill page 重整 dropdown。"""
        page = getattr(self, "skill_page_v2", None)
        if page is not None and hasattr(page, "refresh_profile_selector"):
            page.refresh_profile_selector()

    def _toast_or_skip(self, msg: str, kind: str = "info"):
        toast = getattr(self, "toast", None)
        if toast is not None:
            toast.show(msg, kind)

    def _build_factory_default_profile_state(self) -> dict:
        """Factory default profile state（V2 新增 + 第一次啟動共用）。

        - 「提前提示」boss 類秒數長不需要提前 → False；其他（player / item）秒數短 → True
        - 其他全部初始為 False / 空
        """
        all_skills = self.skill_manager.get_all_skills()
        return {
            "hotkeys": {},
            "permanent":     {sid: False for sid in all_skills},
            "loop":          {sid: False for sid in all_skills},
            "alert_enabled": {
                sid: (meta.get("category") != "boss")
                for sid, meta in all_skills.items()
            },
            "cooldown_overrides": {},
        }

    def create_profile(self, name: str) -> bool:
        """新增 profile；name 重複 / 空字串會 toast error 並回 False。"""
        name = (name or "").strip()
        if not name:
            self._toast_or_skip("配置名稱不可為空", "error")
            return False
        if name in self.config_manager.list_profiles():
            self._toast_or_skip(f"配置 '{name}' 已存在！", "error")
            return False
        default_state = self._build_factory_default_profile_state()
        ok = self.config_manager.save_profile(name, default_state)
        if not ok:
            self._toast_or_skip("新增失敗", "error")
            return False
        self._toast_or_skip(f"已新增配置「{name}」", "success")
        self._refresh_skill_page_v2_profile_selector()
        return True

    def duplicate_profile(self, source: str, new_name: str) -> bool:
        new_name = (new_name or "").strip()
        if not new_name:
            self._toast_or_skip("配置名稱不可為空", "error")
            return False
        if new_name in self.config_manager.list_profiles():
            self._toast_or_skip(f"配置 '{new_name}' 已存在！", "error")
            return False
        source_data = self.config_manager.load_profile(source)
        if source_data is None:
            self._toast_or_skip(f"無法載入來源配置 '{source}'", "error")
            return False
        ok = self.config_manager.save_profile(new_name, source_data)
        if not ok:
            self._toast_or_skip("複製失敗", "error")
            return False
        self._toast_or_skip(f"已複製配置「{source}」→「{new_name}」", "success")
        self._refresh_skill_page_v2_profile_selector()
        return True

    def rename_profile(self, old_name: str, new_name: str) -> bool:
        new_name = (new_name or "").strip()
        if not new_name:
            self._toast_or_skip("配置名稱不可為空", "error")
            return False
        if new_name in self.config_manager.list_profiles():
            self._toast_or_skip(f"配置 '{new_name}' 已存在！", "error")
            return False
        ok = self.config_manager.rename_profile(old_name, new_name)
        if not ok:
            self._toast_or_skip("重命名失敗", "error")
            return False
        if old_name == self.current_profile_name:
            self.current_profile_name = new_name
            self.config_manager.set_current_profile(new_name)
        self._toast_or_skip(f"已重命名「{old_name}」→「{new_name}」", "success")
        self._refresh_skill_page_v2_profile_selector()
        return True

    def delete_profile(self, name: str) -> bool:
        if name == self.current_profile_name:
            self._toast_or_skip("無法刪除當前正在使用的配置！", "error")
            return False
        ok = self.config_manager.delete_profile(name)
        if not ok:
            self._toast_or_skip("刪除失敗", "error")
            return False
        self._toast_or_skip(f"已刪除配置「{name}」", "success")
        self._refresh_skill_page_v2_profile_selector()
        return True

    def switch_profile(self, name: str):
        """切換到指定 profile，重載 SkillService、重建常駐視窗、請 V2 skill 頁 rebuild。

        no-op if name == current_profile_name。
        """
        if name == self.current_profile_name:
            return
        self.config_manager.set_current_profile(name)
        self.config_manager.save()
        self._load_profile_state(name)
        # 同步常駐視窗：關掉舊 profile 的所有視窗，依新 profile 重建常駐
        self.window_manager.close_all()
        self.window_manager.initialize_persistent_skills()
        page = getattr(self, "skill_page_v2", None)
        if page is not None:
            if hasattr(page, "rebuild"):
                page.rebuild()
            # 同步 dropdown currentText 到新 profile
            if hasattr(page, "refresh_profile_selector"):
                page.refresh_profile_selector()
        # 使用者回饋
        toast = getattr(self, "toast", None)
        if toast is not None:
            toast.show(f"已切換到「{name}」", "success")
