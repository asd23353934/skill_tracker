"""
資料存取層模組
提供 Repository 類別，包裝現有 ConfigManager 提供型別化的資料存取介面。

此模組為 Strangler Pattern 的邊界層：
- Repository 在內部呼叫 ConfigManager 的方法
- 將 raw dict 轉為 domain models 回傳
- ConfigManager 保持不變，JSON 格式不變
"""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

from src.domain.models import (
    GlobalSettings,
    MonsterData,
    OverlayData,
    Profile,
    SkillMetadata,
    SkillState,
)

if TYPE_CHECKING:
    from src.ui.config_manager import ConfigManager


class SkillRepository:
    """唯讀技能元資料查詢，合併 skills 和 items"""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._cm = config_manager
        self._cache: dict[str, SkillMetadata] = {}
        self._build_cache()

    def _build_cache(self) -> None:
        """從 ConfigManager 的 initial_skills 和 initial_items 建立快取"""
        for entry in self._cm.initial_skills + self._cm.initial_items:
            skill = SkillMetadata(
                id=entry["id"],
                name=entry["name"],
                icon=entry["icon"],
                cooldown=entry["cooldown"],
                category=entry["category"],
                subcategory=entry.get("subcategory", ""),
            )
            self._cache[skill.id] = skill

    def get_all(self) -> dict[str, SkillMetadata]:
        """取得所有技能與道具元資料"""
        return dict(self._cache)

    def get(self, skill_id: str) -> SkillMetadata | None:
        """取得指定 id 的技能元資料"""
        return self._cache.get(skill_id)

    def get_by_category(self, category: str) -> list[SkillMetadata]:
        """取得指定類別的技能列表"""
        return [s for s in self._cache.values() if s.category == category]


class ProfileRepository:
    """配置檔案 CRUD，轉換 JSON dict ↔ Profile domain model"""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._cm = config_manager

    def load(self, name: str) -> Profile | None:
        """載入配置並轉為 Profile model"""
        data = self._cm.load_profile(name)
        if data is None:
            return None
        return self._dict_to_profile(name, data)

    def save(self, profile: Profile) -> bool:
        """將 Profile model 轉為 JSON dict 並儲存"""
        data = self._profile_to_dict(profile)
        return self._cm.save_profile(profile.name, data)

    def list_all(self) -> list[str]:
        """列出所有配置名稱"""
        return self._cm.list_profiles()

    def delete(self, name: str) -> bool:
        """刪除配置"""
        return self._cm.delete_profile(name)

    def rename(self, old_name: str, new_name: str) -> bool:
        """重命名配置"""
        return self._cm.rename_profile(old_name, new_name)

    def ensure_default(self, all_skill_ids: list[str]) -> None:
        """確保預設配置存在"""
        self._cm.ensure_default_profile()

    @staticmethod
    def _dict_to_profile(name: str, data: dict) -> Profile:
        """將 profile JSON dict 轉為 Profile model

        JSON 格式為多個平行 dict（hotkeys, permanent, loop 等），
        需要樞紐轉換為以 skill_id 為鍵的 SkillState 集合。
        """
        hotkeys = data.get("hotkeys", {})
        permanent = data.get("permanent", {})
        loop = data.get("loop", {})
        alert_enabled = data.get("alert_enabled", {})
        cooldown_overrides = data.get("cooldown_overrides", {})
        alert_seconds_overrides = data.get("alert_seconds_overrides", {})
        sound_overrides = data.get("sound_overrides", {})
        alert_sound_overrides = data.get("alert_sound_overrides", {})

        # 收集所有出現過的 skill_id
        all_ids: set[str] = set()
        for d in (hotkeys, permanent, loop, alert_enabled,
                  cooldown_overrides, alert_seconds_overrides,
                  sound_overrides, alert_sound_overrides):
            all_ids.update(d.keys())

        skill_states: dict[str, SkillState] = {}
        for sid in all_ids:
            skill_states[sid] = SkillState(
                hotkey=hotkeys.get(sid, ""),
                permanent=permanent.get(sid, False),
                loop=loop.get(sid, False),
                alert_enabled=alert_enabled.get(sid, False),
                cooldown_override=cooldown_overrides.get(sid),
                alert_seconds_override=alert_seconds_overrides.get(sid),
                sound_override=sound_overrides.get(sid, ""),
                alert_sound_override=alert_sound_overrides.get(sid, ""),
            )

        return Profile(name=name, skill_states=skill_states)

    @staticmethod
    def _profile_to_dict(profile: Profile) -> dict:
        """將 Profile model 轉回 profile JSON dict 格式

        從以 skill_id 為鍵的 SkillState 集合，
        樞紐轉換回多個平行 dict（hotkeys, permanent, loop 等）。
        """
        hotkeys: dict[str, str] = {}
        permanent: dict[str, bool] = {}
        loop: dict[str, bool] = {}
        alert_enabled: dict[str, bool] = {}
        cooldown_overrides: dict[str, int] = {}
        alert_seconds_overrides: dict[str, int] = {}
        sound_overrides: dict[str, str] = {}
        alert_sound_overrides: dict[str, str] = {}

        for sid, state in profile.skill_states.items():
            hotkeys[sid] = state.hotkey
            permanent[sid] = state.permanent
            loop[sid] = state.loop
            alert_enabled[sid] = state.alert_enabled
            if state.cooldown_override is not None:
                cooldown_overrides[sid] = state.cooldown_override
            if state.alert_seconds_override is not None:
                alert_seconds_overrides[sid] = state.alert_seconds_override
            if state.sound_override:
                sound_overrides[sid] = state.sound_override
            if state.alert_sound_override:
                alert_sound_overrides[sid] = state.alert_sound_override

        return {
            "hotkeys": hotkeys,
            "permanent": permanent,
            "loop": loop,
            "alert_enabled": alert_enabled,
            "cooldown_overrides": cooldown_overrides,
            "alert_seconds_overrides": alert_seconds_overrides,
            "sound_overrides": sound_overrides,
            "alert_sound_overrides": alert_sound_overrides,
        }


class MonsterRepository:
    """怪物資料 CRUD，轉換 dict ↔ MonsterData"""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._cm = config_manager

    def get_all(self) -> list[MonsterData]:
        """取得所有怪物資料"""
        return [self._dict_to_monster(m)
                for m in self._cm.config.get("monsters", [])]

    def get(self, monster_id: str) -> MonsterData | None:
        """取得指定 id 的怪物資料"""
        for m in self._cm.config.get("monsters", []):
            if m["id"] == monster_id:
                return self._dict_to_monster(m)
        return None

    def get_by_hotkey(self, key: str) -> MonsterData | None:
        """依快捷鍵查詢怪物"""
        if not key:
            return None
        for m in self._cm.config.get("monsters", []):
            if m.get("hotkey") == key:
                return self._dict_to_monster(m)
        return None

    def save_all(self, monsters: list[MonsterData]) -> bool:
        """儲存所有怪物資料"""
        self._cm.config["monsters"] = [self._monster_to_dict(m)
                                        for m in monsters]
        return self._cm.save()

    def get_original_respawn_time(self, monster_id: str) -> int | None:
        """取得怪物原始重生時間"""
        return self._cm.get_original_respawn_time(monster_id)

    @staticmethod
    def _dict_to_monster(data: dict) -> MonsterData:
        """將 config.json monster dict 轉為 MonsterData"""
        return MonsterData(
            id=data["id"],
            name=data["name"],
            icon=data["icon"],
            respawn_time=data.get("respawn_time", 0),
            hotkey=data.get("hotkey", ""),
            alert_before=data.get("alert_before", 0),
            loop=data.get("loop", False),
            permanent=data.get("permanent", False),
            sound=data.get("sound", ""),
            alert_sound=data.get("alert_sound", ""),
        )

    @staticmethod
    def _monster_to_dict(monster: MonsterData) -> dict:
        """將 MonsterData 轉回 dict"""
        return asdict(monster)


class OverlayRepository:
    """浮動圖片資料 CRUD"""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._cm = config_manager

    def get_all(self) -> list[OverlayData]:
        """取得所有浮動圖片資料"""
        return [self._dict_to_overlay(o)
                for o in self._cm.config.get("overlays", [])]

    def save_all(self, overlays: list[OverlayData]) -> bool:
        """儲存所有浮動圖片資料"""
        self._cm.config["overlays"] = [asdict(o) for o in overlays]
        return self._cm.save()

    @staticmethod
    def _dict_to_overlay(data: dict) -> OverlayData:
        """將 config.json overlay dict 轉為 OverlayData"""
        return OverlayData(
            id=data["id"],
            name=data["name"],
            file=data["file"],
            alpha=data.get("alpha", 1.0),
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
        )


class SettingsRepository:
    """全域設定讀寫"""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._cm = config_manager

    def load(self) -> GlobalSettings:
        """載入全域設定"""
        s = self._cm.config.get("settings", {})
        return GlobalSettings(
            player_name=s.get("player_name", "玩家1"),
            skill_start_x=s.get("skill_start_x", 0),
            skill_start_y=s.get("skill_start_y", 0),
            enable_sound=s.get("enable_sound", True),
            window_size=s.get("window_size", 64),
            alert_before_seconds=s.get("alert_before_seconds", 0),
            global_sound=s.get("global_sound", ""),
            global_alert_sound=s.get("global_alert_sound", ""),
            current_profile=s.get("current_profile", "預設配置"),
        )

    def save(self, settings: GlobalSettings) -> bool:
        """儲存全域設定"""
        s = self._cm.config.get("settings", {})
        s["player_name"] = settings.player_name
        s["skill_start_x"] = settings.skill_start_x
        s["skill_start_y"] = settings.skill_start_y
        s["enable_sound"] = settings.enable_sound
        s["window_size"] = settings.window_size
        s["alert_before_seconds"] = settings.alert_before_seconds
        s["global_sound"] = settings.global_sound
        s["global_alert_sound"] = settings.global_alert_sound
        s["current_profile"] = settings.current_profile
        self._cm.config["settings"] = s
        return self._cm.save()
