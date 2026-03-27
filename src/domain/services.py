"""
服務層模組
集中業務邏輯，App 成為薄協調層。

此模組零 Qt 依賴，僅依賴 Repository 和 Domain Models。
"""

from __future__ import annotations


class SkillService:
    """技能業務邏輯服務 — 狀態查詢、互斥變更、覆寫管理、配置序列化

    Args:
        skill_repo:           SkillRepository 實例（唯讀元資料）
        skill_loader:         SkillLoader 實例（runtime 技能 dict）
        alert_before_seconds: 全域提前提示秒數
        global_sound:         全域提示音檔名
        global_alert_sound:   全域提前提示音檔名
    """

    def __init__(
        self,
        skill_repo: SkillRepository,
        skill_loader: SkillLoader,
        alert_before_seconds: int = 0,
        global_sound: str = "",
        global_alert_sound: str = "",
    ) -> None:
        self._skill_repo = skill_repo
        self._skill_loader = skill_loader

        # 全域設定（App 會同步更新）
        self.alert_before_seconds = alert_before_seconds
        self.global_sound = global_sound
        self.global_alert_sound = global_alert_sound

        # 狀態 dict（由 App._init_state 遷入，Service 持有）
        self._permanent: dict[str, bool] = {}
        self._loop: dict[str, bool] = {}
        self._alert_enabled: dict[str, bool] = {}
        self._cooldown_overrides: dict[str, int] = {}
        self._alert_seconds_overrides: dict[str, int] = {}
        self._sound_overrides: dict[str, str] = {}
        self._alert_sound_overrides: dict[str, str] = {}
        self._hotkeys: dict[str, str] = {}  # skill_id → hotkey

    # --------------------------------------------------
    # 狀態查詢 (Task 1.2)
    # --------------------------------------------------

    def is_permanent(self, skill_id: str) -> bool:
        """查詢技能是否為常駐"""
        return self._permanent.get(skill_id, False)

    def is_loop(self, skill_id: str) -> bool:
        """查詢技能是否為循環"""
        return self._loop.get(skill_id, False)

    def is_alert_enabled(self, skill_id: str) -> bool:
        """查詢技能是否啟用提前提示"""
        return self._alert_enabled.get(skill_id, False)

    def get_effective_cooldown(self, skill_id: str) -> int:
        """取得有效冷卻時間（覆寫值或原始值）"""
        if skill_id in self._cooldown_overrides:
            return self._cooldown_overrides[skill_id]
        meta = self._skill_repo.get(skill_id)
        return meta.cooldown if meta else 0

    def get_alert_seconds(self, skill_id: str) -> int:
        """取得提前提示秒數（覆寫值或全域預設）"""
        return self._alert_seconds_overrides.get(
            skill_id, self.alert_before_seconds
        )

    def get_sound(self, skill_id: str) -> str:
        """取得提示音（覆寫值或全域預設）"""
        return self._sound_overrides.get(skill_id) or self.global_sound

    def get_alert_sound(self, skill_id: str) -> str:
        """取得提前提示音（覆寫值或全域預設）"""
        return self._alert_sound_overrides.get(skill_id) or self.global_alert_sound

    def get_hotkey(self, skill_id: str) -> str:
        """取得技能快捷鍵"""
        return self._hotkeys.get(skill_id, "")

    def get_original_cooldown(self, skill_id: str) -> int | None:
        """取得技能原始冷卻時間"""
        meta = self._skill_repo.get(skill_id)
        return meta.cooldown if meta else None

    # --------------------------------------------------
    # 互斥狀態變更 (Task 1.3)
    # --------------------------------------------------

    def set_permanent(self, skill_id: str, value: bool) -> dict:
        """設定常駐狀態，啟用時自動關閉循環

        Returns:
            {"permanent": bool, "loop": bool}
        """
        if value:
            self._loop[skill_id] = False
        self._permanent[skill_id] = value
        return {
            "permanent": self._permanent[skill_id],
            "loop": self._loop.get(skill_id, False),
        }

    def set_loop(self, skill_id: str, value: bool) -> dict:
        """設定循環狀態，啟用時自動關閉常駐

        Returns:
            {"permanent": bool, "loop": bool}
        """
        if value:
            self._permanent[skill_id] = False
        self._loop[skill_id] = value
        return {
            "permanent": self._permanent.get(skill_id, False),
            "loop": self._loop[skill_id],
        }

    # --------------------------------------------------
    # 覆寫管理 (Task 1.4)
    # --------------------------------------------------

    def set_cooldown_override(self, skill_id: str, seconds: int) -> bool:
        """設定冷卻時間覆寫

        Returns:
            True 表示與原始值不同（已修改）
        """
        self._cooldown_overrides[skill_id] = seconds
        # 同步 skill_manager runtime dict
        skill = self._skill_loader.get_skill(skill_id)
        if skill:
            skill["cooldown"] = seconds
        original = self.get_original_cooldown(skill_id)
        return original is not None and seconds != original

    def clear_cooldown_override(self, skill_id: str) -> None:
        """清除冷卻時間覆寫，還原為原始值"""
        self._cooldown_overrides.pop(skill_id, None)
        original = self.get_original_cooldown(skill_id)
        if original is not None:
            skill = self._skill_loader.get_skill(skill_id)
            if skill:
                skill["cooldown"] = original

    def set_alert_seconds_override(self, skill_id: str, seconds: int) -> None:
        """設定提前提示秒數覆寫"""
        self._alert_seconds_overrides[skill_id] = seconds

    def clear_alert_seconds_override(self, skill_id: str) -> None:
        """清除提前提示秒數覆寫"""
        self._alert_seconds_overrides.pop(skill_id, None)

    def set_alert_enabled(self, skill_id: str, value: bool) -> None:
        """設定提前提示開關"""
        self._alert_enabled[skill_id] = value

    def set_sound_override(self, skill_id: str, filename: str) -> None:
        """設定提示音覆寫"""
        self._sound_overrides[skill_id] = filename

    def clear_sound_override(self, skill_id: str) -> None:
        """清除提示音覆寫"""
        self._sound_overrides.pop(skill_id, None)

    def set_alert_sound_override(self, skill_id: str, filename: str) -> None:
        """設定提前提示音覆寫"""
        self._alert_sound_overrides[skill_id] = filename

    def clear_alert_sound_override(self, skill_id: str) -> None:
        """清除提前提示音覆寫"""
        self._alert_sound_overrides.pop(skill_id, None)

    # --------------------------------------------------
    # 快捷鍵管理 (Task 1.5)
    # --------------------------------------------------

    def set_hotkey(self, skill_id: str, key_str: str) -> str | None:
        """設定技能快捷鍵（含衝突偵測）

        Returns:
            被替換的 skill_id，或 None 無衝突
        """
        displaced = None
        if key_str:
            existing = self.find_by_hotkey(key_str)
            if existing and existing != skill_id:
                displaced = existing
                self._hotkeys[existing] = ""
                # 同步 skill_manager runtime dict
                skill = self._skill_loader.get_skill(existing)
                if skill:
                    skill["hotkey"] = ""

        self._hotkeys[skill_id] = key_str
        skill = self._skill_loader.get_skill(skill_id)
        if skill:
            skill["hotkey"] = key_str

        return displaced

    def clear_hotkey(self, skill_id: str) -> None:
        """清除技能快捷鍵"""
        self._hotkeys[skill_id] = ""
        skill = self._skill_loader.get_skill(skill_id)
        if skill:
            skill["hotkey"] = ""

    def find_by_hotkey(self, key_str: str) -> str | None:
        """依快捷鍵查詢 skill_id（大小寫不敏感）

        注意：_hotkeys 僅在 load_from_profile / set_hotkey / clear_hotkey 時同步。
        hotkey_manager 目前直接寫 skill_manager dict，不經過此處。
        遷移 hotkey_manager 前，勿以此方法替代 skill_manager.get_skill_by_hotkey()。
        """
        if not key_str:
            return None
        key_upper = key_str.upper()
        for sid, hk in self._hotkeys.items():
            if hk.upper() == key_upper:
                return sid
        return None

    # --------------------------------------------------
    # 批次操作 (Task 1.6)
    # --------------------------------------------------

    def toggle_all_permanent(self) -> dict[str, bool]:
        """切換所有技能的常駐狀態

        Returns:
            {skill_id: new_value} 全部技能的新常駐值
        """
        all_ids = list(self._permanent.keys())
        all_on = all(self._permanent.get(sid, False) for sid in all_ids)
        new_val = not all_on

        if new_val:
            for sid in all_ids:
                self._loop[sid] = False
        for sid in all_ids:
            self._permanent[sid] = new_val

        return {sid: new_val for sid in all_ids}

    def toggle_all_loop(self) -> dict[str, bool]:
        """切換所有技能的循環狀態

        Returns:
            {skill_id: new_value} 全部技能的新循環值
        """
        all_ids = list(self._loop.keys())
        all_on = all(self._loop.get(sid, False) for sid in all_ids)
        new_val = not all_on

        if new_val:
            for sid in all_ids:
                self._permanent[sid] = False
        for sid in all_ids:
            self._loop[sid] = new_val

        return {sid: new_val for sid in all_ids}

    def toggle_all_alert(self) -> dict[str, bool]:
        """切換所有技能的提前提示狀態

        Returns:
            {skill_id: new_value} 全部技能的新提前提示值
        """
        all_ids = list(self._alert_enabled.keys())
        all_on = all(self._alert_enabled.get(sid, False) for sid in all_ids)
        new_val = not all_on

        for sid in all_ids:
            self._alert_enabled[sid] = new_val

        return {sid: new_val for sid in all_ids}

    # --------------------------------------------------
    # 配置序列化 (Task 1.7)
    # --------------------------------------------------

    def serialize_to_dict(self) -> dict:
        """將當前狀態序列化為 profile JSON 格式

        Returns:
            profile 資料字典
        """
        return {
            "hotkeys": {
                sid: skill.get("hotkey", "")
                for sid, skill in self._skill_loader.get_all_skills().items()
            },
            "permanent": self._permanent.copy(),
            "loop": self._loop.copy(),
            "alert_enabled": self._alert_enabled.copy(),
            "cooldown_overrides": self._cooldown_overrides.copy(),
            "alert_seconds_overrides": self._alert_seconds_overrides.copy(),
            "sound_overrides": self._sound_overrides.copy(),
            "alert_sound_overrides": self._alert_sound_overrides.copy(),
        }

    def load_from_profile(self, profile_data: dict) -> None:
        """從 profile dict 載入狀態（替換所有狀態）"""
        self._permanent = profile_data.get("permanent", {}).copy()
        self._loop = profile_data.get("loop", {}).copy()
        self._alert_enabled = profile_data.get("alert_enabled", {}).copy()
        self._alert_seconds_overrides = profile_data.get(
            "alert_seconds_overrides", {}
        ).copy()
        self._sound_overrides = profile_data.get("sound_overrides", {}).copy()
        self._alert_sound_overrides = profile_data.get(
            "alert_sound_overrides", {}
        ).copy()

        # 確保所有技能都有預設值
        for skill_id in self._skill_loader.get_all_skills():
            self._permanent.setdefault(skill_id, False)
            self._loop.setdefault(skill_id, False)
            self._alert_enabled.setdefault(skill_id, False)

        # 同步 hotkeys 到 skill_manager
        self._hotkeys.clear()
        hotkeys = profile_data.get("hotkeys", {})
        for skill_id, skill in self._skill_loader.get_all_skills().items():
            original = self.get_original_cooldown(skill_id)
            if original:
                skill["cooldown"] = original
            skill["hotkey"] = ""

        for skill_id, hotkey in hotkeys.items():
            skill = self._skill_loader.get_skill(skill_id)
            if skill:
                skill["hotkey"] = hotkey
                self._hotkeys[skill_id] = hotkey

        # 同步 cooldown_overrides 到 skill_manager 和 _cooldown_overrides
        self._cooldown_overrides.clear()
        cooldown_overrides = profile_data.get("cooldown_overrides", {})
        for skill_id, cooldown in cooldown_overrides.items():
            skill = self._skill_loader.get_skill(skill_id)
            if skill:
                skill["cooldown"] = cooldown
                self._cooldown_overrides[skill_id] = cooldown

    def reset_all_to_defaults(self) -> None:
        """重置所有狀態為預設值"""
        for skill_id in self._skill_loader.get_all_skills():
            self._permanent[skill_id] = False
            self._loop[skill_id] = False
            self._alert_enabled[skill_id] = False

        self._cooldown_overrides.clear()
        self._alert_seconds_overrides.clear()
        self._sound_overrides.clear()
        self._alert_sound_overrides.clear()
        self._hotkeys.clear()

        # 還原 skill_manager 的 runtime 值
        for skill_id, skill in self._skill_loader.get_all_skills().items():
            original = self.get_original_cooldown(skill_id)
            if original:
                skill["cooldown"] = original
            skill["hotkey"] = ""


class MonsterService:
    """怪物業務邏輯服務 — 狀態查詢、重生時間管理、快捷鍵管理

    Args:
        config_manager: ConfigManager 實例
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        self._cm = config_manager
        # 建立 monster_id → dict 的快取索引
        self._index: dict[str, dict] = {
            m["id"]: m
            for m in self._cm.config.get("monsters", [])
        }

    # --------------------------------------------------
    # 查詢方法 (Task 1.10)
    # --------------------------------------------------

    def get(self, monster_id: str) -> dict | None:
        """取得怪物資料 dict"""
        return self._index.get(monster_id)

    def get_by_hotkey(self, key_str: str) -> dict | None:
        """依快捷鍵查詢怪物（大小寫不敏感）"""
        if not key_str:
            return None
        key_upper = key_str.upper()
        for m in self._index.values():
            if m.get("hotkey", "").upper() == key_upper:
                return m
        return None

    def get_all(self) -> list[dict]:
        """取得所有怪物資料"""
        return self._cm.config.get("monsters", [])

    def get_original_respawn_time(self, monster_id: str) -> int | None:
        """取得怪物原始重生時間"""
        return self._cm.get_original_respawn_time(monster_id)

    # --------------------------------------------------
    # 重生時間管理 (Task 1.11)
    # --------------------------------------------------

    def set_respawn_time(self, monster_id: str, seconds: int) -> bool:
        """設定怪物重生時間

        Returns:
            True 表示與原始值不同（已修改）
        """
        monster = self._index.get(monster_id)
        if not monster:
            return False
        monster["respawn_time"] = seconds
        original = self.get_original_respawn_time(monster_id)
        return original is not None and seconds != original

    def reset_respawn_time(self, monster_id: str) -> int | None:
        """重置怪物重生時間為原始值

        Returns:
            原始重生時間，或 None（找不到怪物或已是原始值）
        """
        monster = self._index.get(monster_id)
        if not monster:
            return None
        original = self.get_original_respawn_time(monster_id)
        if not original or monster.get("respawn_time") == original:
            return None
        monster["respawn_time"] = original
        return original

    # --------------------------------------------------
    # 快捷鍵管理 (Task 1.12)
    # --------------------------------------------------

    def set_hotkey(self, monster_id: str, key_str: str) -> str | None:
        """設定怪物快捷鍵（含衝突偵測）

        Returns:
            被替換的 monster_id，或 None 無衝突
        """
        displaced = None
        if key_str:
            existing = self.get_by_hotkey(key_str)
            if existing and existing["id"] != monster_id:
                displaced = existing["id"]
                existing["hotkey"] = ""

        monster = self._index.get(monster_id)
        if monster:
            monster["hotkey"] = key_str
        return displaced

    def clear_hotkey(self, monster_id: str) -> None:
        """清除怪物快捷鍵"""
        monster = self._index.get(monster_id)
        if monster:
            monster["hotkey"] = ""

    # --------------------------------------------------
    # 狀態管理 (Task 1.13)
    # --------------------------------------------------

    def set_loop(self, monster_id: str, value: bool) -> None:
        """設定怪物循環狀態"""
        monster = self._index.get(monster_id)
        if monster:
            monster["loop"] = value

    def set_permanent(self, monster_id: str, value: bool) -> None:
        """設定怪物常駐狀態"""
        monster = self._index.get(monster_id)
        if monster:
            monster["permanent"] = value

    def set_alert_before(self, monster_id: str, seconds: int) -> None:
        """設定怪物提前提示秒數"""
        monster = self._index.get(monster_id)
        if monster:
            monster["alert_before"] = seconds

    def set_sound(self, monster_id: str, filename: str) -> None:
        """設定怪物結束提示音"""
        monster = self._index.get(monster_id)
        if monster:
            monster["sound"] = filename

    def set_alert_sound(self, monster_id: str, filename: str) -> None:
        """設定怪物提前提示音"""
        monster = self._index.get(monster_id)
        if monster:
            monster["alert_sound"] = filename

    # --------------------------------------------------
    # 持久化 (Task 1.14)
    # --------------------------------------------------

    def save(self) -> bool:
        """持久化怪物資料到 config.json"""
        return self._cm.save()
