"""domain.models 測試 — SkillState 互斥規則、Profile 自動建立、其他 dataclass default"""

from src.domain.models import (
    SkillMetadata, SkillState, Profile,
    MonsterData, OverlayData, GlobalSettings,
)


# ── SkillState 互斥 ─────────────────────────────────────────

def test_skillstate_set_permanent_clears_loop():
    s = SkillState(loop=True)
    s.set_permanent(True)
    assert s.permanent is True
    assert s.loop is False


def test_skillstate_set_loop_clears_permanent():
    s = SkillState(permanent=True)
    s.set_loop(True)
    assert s.loop is True
    assert s.permanent is False


def test_skillstate_disable_permanent_does_not_touch_loop():
    s = SkillState(permanent=True, loop=False)
    s.set_permanent(False)
    assert s.permanent is False
    assert s.loop is False  # 原本就 False，不會被翻


def test_skillstate_disable_loop_does_not_touch_permanent():
    s = SkillState(permanent=False, loop=True)
    s.set_loop(False)
    assert s.loop is False
    assert s.permanent is False


# ── Profile.get_state 自動建立 ─────────────────────────────

def test_profile_get_state_creates_default_on_miss():
    p = Profile(name="test")
    st = p.get_state("new_skill")
    assert isinstance(st, SkillState)
    assert st.hotkey == ""
    assert "new_skill" in p.skill_states


def test_profile_get_state_returns_existing():
    p = Profile(name="test")
    first = p.get_state("aaa")
    first.hotkey = "F1"
    second = p.get_state("aaa")
    assert second is first
    assert second.hotkey == "F1"


# ── SkillMetadata 不可變 ────────────────────────────────────

def test_skill_metadata_is_frozen():
    import dataclasses
    import pytest as _pytest
    m = SkillMetadata(
        id="x", name="x", icon="x.png", cooldown=0, category="c", subcategory="s",
    )
    with _pytest.raises(dataclasses.FrozenInstanceError):
        m.name = "y"  # type: ignore[misc]


# ── 其他 dataclass default 值 ──────────────────────────────

def test_monster_data_defaults():
    m = MonsterData(id="1", name="n", icon="i", respawn_time=10)
    assert m.hotkey == ""
    assert m.alert_before == 0
    assert m.loop is False
    assert m.permanent is False


def test_overlay_data_defaults():
    o = OverlayData(id="1", name="n", file="f.png")
    assert o.alpha == 1.0
    assert o.x == 0 and o.y == 0
    assert o.width == 0 and o.height == 0


def test_global_settings_defaults():
    g = GlobalSettings()
    assert g.enable_sound is True
    assert g.window_size == 64
    assert g.current_profile == "預設配置"
