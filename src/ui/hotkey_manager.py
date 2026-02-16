"""
快捷鍵管理模組
處理 pynput 鍵盤監聽、快捷鍵捕捉邏輯
"""

from pynput import keyboard
from src.ui.theme import AppTheme


class HotkeyManager:
    """快捷鍵管理器"""

    def __init__(self, app):
        self.app = app
        self.enabled = True
        self.waiting_for = None
        self.waiting_name = None

    def start(self):
        """啟動鍵盤監聽"""
        listener = keyboard.Listener(on_press=self._on_key_press)
        listener.daemon = True
        listener.start()

    def begin_capture(self, skill_id, skill_name):
        """開始捕捉快捷鍵"""
        self.waiting_for = skill_id
        self.waiting_name = skill_name
        self.enabled = False
        self.app.header.show_hotkey_hint(
            f"⌨️ 請按下 '{skill_name}' 的快捷鍵...",
            AppTheme.ACCENT_YELLOW,
        )

    def _on_key_press(self, key):
        """按鍵處理"""
        if self.waiting_for is not None:
            self._capture_hotkey(key)
            return

        if not self.enabled:
            return

        try:
            key_name = key.name if hasattr(key, "name") else str(key.char)

            # 先檢查技能快捷鍵
            skill_id = self.app.skill_manager.get_skill_by_hotkey(key_name)
            if skill_id:
                self.app.after(0, self.app.window_manager.trigger_skill, skill_id)
                return

            # 再檢查怪物快捷鍵
            monster_id = self.app.get_monster_by_hotkey(key_name)
            if monster_id:
                self.app.after(0, self.app.window_manager.trigger_monster, monster_id)
        except Exception:
            pass

    def _capture_hotkey(self, key):
        """捕捉按鍵並設定（支援技能與怪物）"""
        if self.waiting_for is None:
            return

        try:
            key_name = key.name if hasattr(key, "name") else str(key.char)
            key_str = key_name.upper()

            waiting_id = self.waiting_for
            waiting_name = self.waiting_name

            # 判斷是技能還是怪物
            is_monster = self.app.get_monster(waiting_id) is not None
            is_skill = self.app.skill_manager.get_skill(waiting_id) is not None

            # 清除其他技能/怪物的相同快捷鍵
            for sid, skill in self.app.skill_manager.get_all_skills().items():
                if skill.get("hotkey") == key_str and sid != waiting_id:
                    skill["hotkey"] = ""
                    self.app.update_hotkey_display(sid, "", False)

            for monster in self.app.get_all_monsters():
                if monster.get("hotkey", "").upper() == key_str and monster["id"] != waiting_id:
                    monster["hotkey"] = ""
                    # 更新怪物卡牌顯示
                    if hasattr(self.app, "monster_page"):
                        card = self.app.monster_page.cards.get(monster["id"])
                        if card:
                            self.app.after(0, card.update_hotkey_display, "", False)

            if is_monster:
                # 設定怪物快捷鍵
                monster = self.app.get_monster(waiting_id)
                monster["hotkey"] = key_str
                self.app.save_monsters()

                # 更新怪物卡牌 UI
                monster_card = getattr(self, "_monster_card", None)
                if monster_card:
                    self.app.after(0, monster_card.update_hotkey_display, key_str, True)
                    self._monster_card = None

            elif is_skill:
                # 設定技能快捷鍵
                skill = self.app.skill_manager.get_skill(waiting_id)
                skill["hotkey"] = key_str
                self.app.update_hotkey_display(waiting_id, key_str, True)
                self.app.auto_save_current_profile()

            self.app.header.show_hotkey_hint(
                f"✓ '{waiting_name}' 設定為 {key_str}",
                AppTheme.ACCENT_GREEN,
            )
            self.app.after(2000, self.app.header.clear_hotkey_hint)

            self.waiting_for = None
            self.waiting_name = None
            self.enabled = True

        except Exception as e:
            self.app.header.show_hotkey_hint(
                f"✗ 設定失敗: {e}",
                AppTheme.ACCENT_RED,
            )
            self.app.after(3000, self.app.header.clear_hotkey_hint)
            self.waiting_for = None
            self.waiting_name = None
            self.enabled = True
            self._monster_card = None
