"""domain.services 測試 — SkillService / MonsterService 業務邏輯

不依賴真實 ConfigManager / SkillLoader，用極簡 fake。
"""

import pytest

from src.domain.models import SkillMetadata
from src.domain.services import SkillService, MonsterService


# ── Fake 依賴 ───────────────────────────────────────────────

class _FakeSkillRepo:
    def __init__(self, meta_by_id: dict[str, SkillMetadata]):
        self._data = meta_by_id

    def get(self, sid):
        return self._data.get(sid)


class _FakeSkillLoader:
    def __init__(self, skills: dict[str, dict]):
        self.skills = skills

    def get_skill(self, sid):
        return self.skills.get(sid)

    def get_all_skills(self):
        return self.skills


def _make_service(extra_skills: dict[str, dict] | None = None) -> SkillService:
    """建立有兩個技能的 SkillService"""
    skills = {
        "a": {"id": "a", "name": "A", "icon": "a.png", "cooldown": 30, "hotkey": ""},
        "b": {"id": "b", "name": "B", "icon": "b.png", "cooldown": 60, "hotkey": ""},
    }
    if extra_skills:
        skills.update(extra_skills)
    metas = {
        sid: SkillMetadata(
            id=s["id"], name=s["name"], icon=s["icon"],
            cooldown=s["cooldown"], category="player", subcategory="",
        )
        for sid, s in skills.items()
    }
    svc = SkillService(_FakeSkillRepo(metas), _FakeSkillLoader(skills))
    # 預設狀態 dict 需要包含所有 id，模擬 load_from_profile 後的狀態
    for sid in skills:
        svc._permanent.setdefault(sid, False)
        svc._loop.setdefault(sid, False)
        svc._alert_enabled.setdefault(sid, False)
    return svc


# ── 狀態查詢 ────────────────────────────────────────────────

def test_get_effective_cooldown_uses_override():
    svc = _make_service()
    assert svc.get_effective_cooldown("a") == 30
    svc.set_cooldown_override("a", 45)
    assert svc.get_effective_cooldown("a") == 45


def test_get_effective_cooldown_unknown_returns_zero():
    svc = _make_service()
    assert svc.get_effective_cooldown("nonexistent") == 0


def test_get_alert_seconds_falls_back_to_global():
    svc = _make_service()
    svc.alert_before_seconds = 5
    assert svc.get_alert_seconds("a") == 5
    svc.set_alert_seconds_override("a", 12)
    assert svc.get_alert_seconds("a") == 12


def test_get_sound_override_wins_over_global():
    svc = _make_service()
    svc.global_sound = "g.wav"
    assert svc.get_sound("a") == "g.wav"
    svc.set_sound_override("a", "s.wav")
    assert svc.get_sound("a") == "s.wav"
    # 空字串 override 視為未設定，fallback global
    svc.set_sound_override("a", "")
    assert svc.get_sound("a") == "g.wav"


# ── 互斥規則 ────────────────────────────────────────────────

def test_set_permanent_clears_loop():
    svc = _make_service()
    svc._loop["a"] = True
    result = svc.set_permanent("a", True)
    assert result == {"permanent": True, "loop": False}


def test_set_loop_clears_permanent():
    svc = _make_service()
    svc._permanent["a"] = True
    result = svc.set_loop("a", True)
    assert result == {"permanent": False, "loop": True}


def test_disable_permanent_leaves_loop_untouched():
    svc = _make_service()
    svc._loop["a"] = True
    svc._permanent["a"] = False
    # set_permanent(False) 不應翻 loop
    svc.set_permanent("a", False)
    assert svc._loop["a"] is True


# ── 覆寫管理 ────────────────────────────────────────────────

def test_set_cooldown_override_syncs_runtime_dict():
    svc = _make_service()
    changed = svc.set_cooldown_override("a", 45)
    assert changed is True
    assert svc._skill_loader.get_skill("a")["cooldown"] == 45


def test_set_cooldown_override_same_as_original_returns_false():
    svc = _make_service()
    # a 原本 cooldown 30，設成 30 應回 False
    assert svc.set_cooldown_override("a", 30) is False


def test_clear_cooldown_override_restores_original():
    svc = _make_service()
    svc.set_cooldown_override("a", 999)
    svc.clear_cooldown_override("a")
    assert "a" not in svc._cooldown_overrides
    assert svc._skill_loader.get_skill("a")["cooldown"] == 30


# ── 快捷鍵管理 ──────────────────────────────────────────────

def test_set_hotkey_no_conflict_returns_none():
    svc = _make_service()
    assert svc.set_hotkey("a", "F1") is None
    assert svc.get_hotkey("a") == "F1"
    assert svc._skill_loader.get_skill("a")["hotkey"] == "F1"


def test_set_hotkey_conflict_displaces_prior_owner():
    svc = _make_service()
    svc.set_hotkey("a", "F1")
    # b 搶 a 的 F1
    displaced = svc.set_hotkey("b", "F1")
    assert displaced == "a"
    assert svc.get_hotkey("a") == ""
    assert svc._skill_loader.get_skill("a")["hotkey"] == ""
    assert svc.get_hotkey("b") == "F1"


def test_set_hotkey_same_skill_same_key_no_displacement():
    svc = _make_service()
    svc.set_hotkey("a", "F1")
    # a 重設 F1 不應 displace 自己
    assert svc.set_hotkey("a", "F1") is None


def test_find_by_hotkey_case_insensitive():
    svc = _make_service()
    svc.set_hotkey("a", "f1")
    assert svc.find_by_hotkey("F1") == "a"
    assert svc.find_by_hotkey("") is None


def test_clear_hotkey():
    svc = _make_service()
    svc.set_hotkey("a", "F1")
    svc.clear_hotkey("a")
    assert svc.get_hotkey("a") == ""
    assert svc._skill_loader.get_skill("a")["hotkey"] == ""


# ── 批次操作 ────────────────────────────────────────────────

def test_toggle_all_permanent_from_none_to_all():
    svc = _make_service()
    result = svc.toggle_all_permanent()
    assert result == {"a": True, "b": True}


def test_toggle_all_permanent_from_all_to_none():
    svc = _make_service()
    svc._permanent = {"a": True, "b": True}
    result = svc.toggle_all_permanent()
    assert result == {"a": False, "b": False}


def test_toggle_all_permanent_clears_loop():
    svc = _make_service()
    svc._loop = {"a": True, "b": True}
    svc.toggle_all_permanent()
    assert svc._loop == {"a": False, "b": False}


def test_toggle_all_loop_clears_permanent():
    svc = _make_service()
    svc._permanent = {"a": True, "b": True}
    svc.toggle_all_loop()
    assert svc._permanent == {"a": False, "b": False}


def test_toggle_all_alert_does_not_touch_permanent_loop():
    svc = _make_service()
    svc._permanent = {"a": True, "b": False}
    svc._loop = {"a": False, "b": True}
    svc.toggle_all_alert()
    assert svc._permanent == {"a": True, "b": False}
    assert svc._loop == {"a": False, "b": True}


# ── serialize / load_from_profile ───────────────────────────

def test_serialize_to_dict_shape():
    svc = _make_service()
    svc.set_hotkey("a", "F1")
    svc.set_cooldown_override("a", 45)
    svc.set_permanent("b", True)
    out = svc.serialize_to_dict()
    assert out["hotkeys"]["a"] == "F1"
    assert out["cooldown_overrides"]["a"] == 45
    assert out["permanent"]["b"] is True
    # 確保是 copy，改回傳值不影響內部
    out["permanent"]["b"] = False
    assert svc._permanent["b"] is True


def test_load_from_profile_replaces_state_and_syncs_runtime():
    svc = _make_service()
    profile = {
        "hotkeys": {"a": "F2"},
        "permanent": {"a": True},
        "loop": {},
        "alert_enabled": {},
        "cooldown_overrides": {"b": 90},
    }
    svc.load_from_profile(profile)
    assert svc.get_hotkey("a") == "F2"
    assert svc.is_permanent("a") is True
    assert svc.get_effective_cooldown("b") == 90
    # runtime dict 同步
    assert svc._skill_loader.get_skill("a")["hotkey"] == "F2"
    assert svc._skill_loader.get_skill("b")["cooldown"] == 90
    # 沒出現在 profile 的技能應被 setdefault 為 False
    assert svc.is_permanent("b") is False


def test_load_from_profile_clears_stale_hotkeys_on_unrelated_skills():
    svc = _make_service()
    svc.set_hotkey("a", "F1")
    svc.set_hotkey("b", "F2")
    # profile 只保留 a
    svc.load_from_profile({"hotkeys": {"a": "F3"}})
    assert svc.get_hotkey("a") == "F3"
    # b 的 hotkey 應被清掉
    assert svc._skill_loader.get_skill("b")["hotkey"] == ""


def test_reset_all_to_defaults():
    svc = _make_service()
    svc.set_hotkey("a", "F1")
    svc.set_cooldown_override("a", 45)
    svc.set_permanent("b", True)
    svc.reset_all_to_defaults()
    assert svc.is_permanent("b") is False
    assert svc.get_hotkey("a") == ""
    assert svc.get_effective_cooldown("a") == 30  # 回到原值
    assert svc._cooldown_overrides == {}


# ── MonsterService ──────────────────────────────────────────

class _FakeCM:
    def __init__(self, monsters, originals):
        self.config = {"monsters": monsters}
        self._originals = originals
        self.saved = False

    def get_original_respawn_time(self, mid):
        return self._originals.get(mid)

    def save(self):
        self.saved = True
        return True


def _make_monster_service():
    monsters = [
        {"id": "m1", "name": "M1", "respawn_time": 120, "hotkey": ""},
        {"id": "m2", "name": "M2", "respawn_time": 60, "hotkey": ""},
    ]
    originals = {"m1": 120, "m2": 60}
    cm = _FakeCM(monsters, originals)
    return MonsterService(cm), cm


def test_monster_get_and_get_all():
    svc, _ = _make_monster_service()
    assert svc.get("m1")["name"] == "M1"
    assert svc.get("missing") is None
    assert len(svc.get_all()) == 2


def test_monster_set_respawn_changed_flag():
    svc, _ = _make_monster_service()
    # 設成跟原本相同 → False
    assert svc.set_respawn_time("m1", 120) is False
    assert svc.set_respawn_time("m1", 90) is True
    assert svc.get("m1")["respawn_time"] == 90


def test_monster_set_respawn_missing_id_returns_false():
    svc, _ = _make_monster_service()
    assert svc.set_respawn_time("ghost", 100) is False


def test_monster_reset_respawn_restores_original():
    svc, _ = _make_monster_service()
    svc.set_respawn_time("m1", 30)
    original = svc.reset_respawn_time("m1")
    assert original == 120
    assert svc.get("m1")["respawn_time"] == 120


def test_monster_reset_respawn_noop_when_already_original():
    svc, _ = _make_monster_service()
    assert svc.reset_respawn_time("m1") is None


def test_monster_hotkey_conflict_displaces():
    svc, _ = _make_monster_service()
    svc.set_hotkey("m1", "F5")
    displaced = svc.set_hotkey("m2", "F5")
    assert displaced == "m1"
    assert svc.get("m1")["hotkey"] == ""
    assert svc.get("m2")["hotkey"] == "F5"


def test_monster_get_by_hotkey_case_insensitive():
    svc, _ = _make_monster_service()
    svc.set_hotkey("m1", "f9")
    assert svc.get_by_hotkey("F9")["id"] == "m1"
    assert svc.get_by_hotkey("") is None


def test_monster_state_setters():
    svc, _ = _make_monster_service()
    svc.set_loop("m1", True)
    svc.set_permanent("m1", True)
    svc.set_alert_before("m1", 15)
    svc.set_sound("m1", "a.wav")
    svc.set_alert_sound("m1", "b.wav")
    m = svc.get("m1")
    assert m["loop"] is True and m["permanent"] is True
    assert m["alert_before"] == 15
    assert m["sound"] == "a.wav" and m["alert_sound"] == "b.wav"


def test_monster_state_setters_ignore_missing():
    svc, _ = _make_monster_service()
    # 不應 raise
    svc.set_loop("ghost", True)
    svc.set_permanent("ghost", True)
    svc.set_alert_before("ghost", 5)


def test_monster_save_delegates_to_cm():
    svc, cm = _make_monster_service()
    assert svc.save() is True
    assert cm.saved is True


# ── is_alert_enabled fallback：item 類預設 True、其他預設 False ────────────

def _make_service_mixed_categories() -> SkillService:
    """建立含 player / item / boss 三類的 SkillService（fallback 邏輯測試用）"""
    skills = {
        "p1": {"id": "p1", "name": "P1", "icon": "p.png", "cooldown": 30},
        "i1": {"id": "i1", "name": "I1", "icon": "i.png", "cooldown": 1800},
        "b1": {"id": "b1", "name": "B1", "icon": "b.png", "cooldown": 600},
    }
    categories = {"p1": "player", "i1": "item", "b1": "boss"}
    metas = {
        sid: SkillMetadata(
            id=s["id"], name=s["name"], icon=s["icon"],
            cooldown=s["cooldown"], category=categories[sid], subcategory="",
        )
        for sid, s in skills.items()
    }
    # SkillLoader fake 也要回傳 category 給 fallback 用
    class _CategoryAwareLoader:
        def __init__(self, skills, cats):
            self.skills = {sid: {**s, "category": cats[sid]} for sid, s in skills.items()}
        def get_skill(self, sid):
            return self.skills.get(sid)
        def get_all_skills(self):
            return self.skills
    return SkillService(_FakeSkillRepo(metas), _CategoryAwareLoader(skills, categories))


def test_alert_enabled_fallback_item_returns_true():
    """道具類在 dict 無 key 時 fallback 為 True（v4.3.6 新行為）"""
    svc = _make_service_mixed_categories()
    assert svc.is_alert_enabled("i1") is True


def test_alert_enabled_fallback_player_returns_false():
    svc = _make_service_mixed_categories()
    assert svc.is_alert_enabled("p1") is False


def test_alert_enabled_fallback_boss_returns_false():
    svc = _make_service_mixed_categories()
    assert svc.is_alert_enabled("b1") is False


def test_alert_enabled_explicit_set_overrides_fallback():
    """user 主動 disable item 後不應被 fallback 蓋回 True"""
    svc = _make_service_mixed_categories()
    svc.set_alert_enabled("i1", False)
    assert svc.is_alert_enabled("i1") is False
    svc.set_alert_enabled("p1", True)
    assert svc.is_alert_enabled("p1") is True


def test_alert_enabled_unknown_skill_returns_false():
    """未知 skill_id（loader 找不到）fallback 走 False"""
    svc = _make_service_mixed_categories()
    assert svc.is_alert_enabled("nonexistent") is False
