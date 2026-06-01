"""
快捷鍵管理模組
處理 pynput 鍵盤監聽、快捷鍵捕捉邏輯

## 命名空間隔離

系統維護兩個獨立快捷鍵命名空間：**技能** 與 **怪物**。
相同按鍵可同時指定給一個技能與一個怪物，兩者互不衝突。
衝突清除僅在同一命名空間內執行。

## 執行緒安全

pynput Listener 在 daemon thread 執行，所有 UI 操作
必須透過 `app.after(0, func)` 排回 Qt 主執行緒執行。
禁止在此模組中直接操作任何 Qt widget。
"""

from pynput import keyboard
from src.ui.theme import AppTheme


# 右側數字鍵區（numpad）Windows virtual-key code → 顯示名稱
# pynput 在某些狀態下（Num Lock off 或特定按鍵）回傳 KeyCode(char=None, vk=..)
# 直接 str(None) 會變成 "None" / .upper() 成 "NONE"，無法作為快捷鍵使用
_NUMPAD_VK_LABELS = {
    96:  "NUM0", 97:  "NUM1", 98:  "NUM2", 99:  "NUM3", 100: "NUM4",
    101: "NUM5", 102: "NUM6", 103: "NUM7", 104: "NUM8", 105: "NUM9",
    106: "NUM*", 107: "NUM+", 109: "NUM-", 110: "NUM.", 111: "NUM/",
}


def _key_to_name(key) -> str:
    """將 pynput Key / KeyCode 轉為穩定的名稱字串。

    優先順序：
      1. Key.name（特殊鍵：f1 / space / ctrl_l / …）
      2. VK 對應的 numpad 標籤（NUM0..9 / NUM+ / …）
      3. KeyCode.char（一般字元鍵）
      4. fallback "VK{vk}"，完全無法辨識則回 "UNKNOWN"
    """
    name = getattr(key, "name", None)
    if name:
        return name
    vk = getattr(key, "vk", None)
    if vk in _NUMPAD_VK_LABELS:
        return _NUMPAD_VK_LABELS[vk]
    char = getattr(key, "char", None)
    if char:
        return char
    return f"VK{vk}" if vk else "UNKNOWN"


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
        """開始捕捉快捷鍵（進入捕捉模式）

        前置條件：目前不在捕捉模式（waiting_for 為 None）
        後置效果：
          - waiting_for 設為 skill_id（可為技能或怪物 ID）
          - enabled 設為 False（暫停正常快捷鍵觸發）
          - header 顯示等待提示（ACCENT_YELLOW）

        Args:
            skill_id:   目標技能或怪物的 ID
            skill_name: 顯示名稱（用於提示訊息）
        """
        self.waiting_for = skill_id
        self.waiting_name = skill_name
        self.enabled = False
        self.app.header.show_hotkey_hint(
            f"⌨️ 請按下 '{skill_name}' 的快捷鍵...",
            AppTheme.ACCENT_YELLOW,
        )

    def _app_filter_blocks(self) -> bool:
        """快捷鍵限定：已啟用且前景視窗 exe 不符目標時回 True（應忽略此次觸發）。

        只在「已比對到註冊快捷鍵之後」才呼叫，平常按鍵不付出查前景的成本。
        僅用 ctypes（window_enum），無 Qt，於 pynput daemon thread 安全。
        未啟用或未設定目標時一律放行（回 False）。
        """
        if not getattr(self.app, "hotkey_app_filter_enabled", False):
            return False
        target = (getattr(self.app, "hotkey_app_target_exe", "") or "").lower()
        if not target:
            return False
        try:
            from src.infrastructure.window_enum import get_foreground_exe
            return get_foreground_exe() != target
        except Exception:
            return False  # 查詢失敗時不阻擋，避免快捷鍵整個失效

    def _on_key_press(self, key):
        """按鍵處理（pynput daemon thread 回呼）

        觸發優先順序：
          1. 捕捉模式：waiting_for 非 None 時路由到 _capture_hotkey
          2. 技能命名空間：skill_manager.get_skill_by_hotkey() 先查
          3. 怪物命名空間：app.get_monster_by_hotkey() 後查
        所有 UI 操作均透過 app.after(0, ...) 排回 Qt 主執行緒。
        """
        if self.waiting_for is not None:
            self._capture_hotkey(key)
            return

        if not self.enabled:
            return

        try:
            key_name = _key_to_name(key)

            # 先檢查技能快捷鍵
            skill_id = self.app.skill_manager.get_skill_by_hotkey(key_name)
            if skill_id:
                if self._app_filter_blocks():
                    return
                self.app.after(
                    0, lambda sid=skill_id: self.app.window_manager.trigger_skill(sid)
                )
                return

            # 再檢查怪物快捷鍵
            monster_id = self.app.get_monster_by_hotkey(key_name)
            if monster_id:
                if self._app_filter_blocks():
                    return
                self.app.after(
                    0, lambda mid=monster_id: self.app.window_manager.trigger_monster(mid)
                )
        except Exception as e:
            import sys
            print(f"[HotkeyManager] _on_hotkey error: {e}", file=sys.stderr)

    def _capture_hotkey(self, key):
        """捕捉按鍵並設定（支援技能與怪物）"""
        if self.waiting_for is None:
            return

        try:
            key_name = _key_to_name(key)
            key_str = key_name.upper()

            waiting_id = self.waiting_for
            waiting_name = self.waiting_name

            # 判斷是技能還是怪物
            is_monster = self.app.get_monster(waiting_id) is not None
            is_skill = self.app.skill_manager.get_skill(waiting_id) is not None

            # 清除相同快捷鍵（技能與怪物互相獨立，不互相衝突）
            if is_skill:
                # 僅清除其他技能的重複快捷鍵
                for sid, skill in self.app.skill_manager.get_all_skills().items():
                    if skill.get("hotkey") == key_str and sid != waiting_id:
                        skill["hotkey"] = ""
                        self.app.after(
                            0, lambda s=sid: self.app.update_hotkey_display(s, "", False)
                        )
            elif is_monster:
                # 僅清除其他怪物的重複快捷鍵
                for monster in self.app.get_all_monsters():
                    if monster.get("hotkey", "").upper() == key_str and monster["id"] != waiting_id:
                        monster["hotkey"] = ""
                        # 更新怪物卡牌顯示
                        if hasattr(self.app, "monster_page"):
                            card = self.app.monster_page.cards.get(monster["id"])
                            if card:
                                updater = getattr(card, "set_hotkey_text", None) or card.update_hotkey_display
                                self.app.after(
                                    0, lambda u=updater: u("", False)
                                )

            if is_monster:
                # 設定怪物快捷鍵
                monster = self.app.get_monster(waiting_id)
                monster["hotkey"] = key_str
                self.app.save_monsters()

                # 更新怪物卡牌 UI（V1 / V2 卡片各自實作 set_hotkey_text 或 update_hotkey_display）
                monster_card = getattr(self, "_monster_card", None)
                if monster_card:
                    updater = getattr(monster_card, "set_hotkey_text", None) or monster_card.update_hotkey_display
                    self.app.after(
                        0, lambda u=updater, ks=key_str: u(ks, True)
                    )
                    self._monster_card = None

            elif is_skill:
                # 設定技能快捷鍵
                skill = self.app.skill_manager.get_skill(waiting_id)
                skill["hotkey"] = key_str
                self.app.after(
                    0,
                    lambda wid=waiting_id, ks=key_str: (
                        self.app.update_hotkey_display(wid, ks, True),
                        self.app.auto_save_current_profile(),
                    ),
                )

            self.app.after(
                0,
                lambda wn=waiting_name, ks=key_str: self.app.header.show_hotkey_hint(
                    f"✓ '{wn}' 設定為 {ks}",
                    AppTheme.ACCENT_GREEN,
                ),
            )
            self.app.after(2000, self.app.header.clear_hotkey_hint)

            self.waiting_for = None
            self.waiting_name = None
            self.enabled = True

        except Exception as e:
            self.app.after(
                0,
                lambda err=e: self.app.header.show_hotkey_hint(
                    f"✗ 設定失敗: {err}",
                    AppTheme.ACCENT_RED,
                ),
            )
            self.app.after(3000, self.app.header.clear_hotkey_hint)
            self.waiting_for = None
            self.waiting_name = None
            self.enabled = True
            self._monster_card = None
