"""SkillPixmapCache 測試 — lazy load 行為（不實際解碼 PIL）"""

import pytest

from src.ui.skill_pixmap_cache import SkillPixmapCache, _LazyPixmapDict


class _FakeLoader:
    def __init__(self, skills):
        self.skills = skills

    def get_all_skills(self):
        return self.skills

    def get_skill(self, sid):
        return self.skills.get(sid)


@pytest.fixture
def cache(monkeypatch):
    """建立 SkillPixmapCache；_load_skill_pixmaps 改為 spy，不真正開檔"""
    loader = _FakeLoader({
        "a": {"id": "a", "icon": "a.png"},
        "b": {"id": "b", "icon": "b.png"},
    })
    load_calls: list[str] = []

    def _spy(self, skill_id):
        load_calls.append(skill_id)
        # 模擬成功載入：四個 dict 都寫個 sentinel
        self.qpixmaps._data[skill_id] = f"pix50:{skill_id}"
        self.qpixmaps_small._data[skill_id] = f"pix28:{skill_id}"
        self.qpixmaps_medium._data[skill_id] = f"pix64:{skill_id}"
        self.qpixmaps_card._data[skill_id] = f"pix36:{skill_id}"

    monkeypatch.setattr(SkillPixmapCache, "_load_skill_pixmaps", _spy)
    c = SkillPixmapCache(loader)
    return c, load_calls


def test_init_does_not_decode_any_image(cache):
    _, calls = cache
    # 啟動時零 load 呼叫
    assert calls == []


def test_init_indexes_all_paths(cache):
    c, _ = cache
    assert "a" in c.skill_image_paths
    assert "b" in c.skill_image_paths
    assert c.skill_image_paths["a"].endswith("a.png")


def test_get_triggers_load_once_per_skill(cache):
    c, calls = cache
    assert c.qpixmaps_medium.get("a") == "pix64:a"
    assert calls == ["a"]
    # 第二次取任何尺寸都不再觸發 load（四個 dict 一次填好）
    assert c.qpixmaps.get("a") == "pix50:a"
    assert c.qpixmaps_card.get("a") == "pix36:a"
    assert calls == ["a"]


def test_get_different_skills_loads_each_once(cache):
    c, calls = cache
    c.qpixmaps.get("a")
    c.qpixmaps.get("b")
    c.qpixmaps.get("a")  # 再拿一次 a
    assert calls == ["a", "b"]


def test_contains_only_after_load(cache):
    c, _ = cache
    assert "a" not in c.qpixmaps
    c.qpixmaps.get("a")
    assert "a" in c.qpixmaps


def test_setitem_manual_override(cache):
    c, calls = cache
    c.qpixmaps_card["a"] = "manual"
    # 手動塞值後再 get 不應再觸發 load
    assert c.qpixmaps_card.get("a") == "manual"
    assert calls == []


def test_preload_all_loads_every_skill(cache):
    c, calls = cache
    c.preload_all()
    assert sorted(calls) == ["a", "b"]


def test_missing_path_writes_none_for_all_sizes():
    """真實 _load_skill_pixmaps：skill_id 無登錄路徑 → 四個 dict 都寫 None"""
    loader = _FakeLoader({})  # 沒有任何技能
    c = SkillPixmapCache(loader)
    # ghost 不在 skill_image_paths，走 short-circuit 分支
    assert c.qpixmaps.get("ghost") is None
    assert c.qpixmaps_small.get("ghost") is None
    assert c.qpixmaps_medium.get("ghost") is None
    assert c.qpixmaps_card.get("ghost") is None
    # 呼叫第二次不重試（已寫 None）— 驗證 cache hit 語義
    assert "ghost" in c.qpixmaps


def test_decode_failure_writes_none_for_all_sizes(tmp_path, monkeypatch):
    """PIL 開檔失敗 → 四個 dict 都寫 None，不 raise"""
    loader = _FakeLoader({"broken": {"id": "broken", "icon": "nope.png"}})
    c = SkillPixmapCache(loader)
    # skill_image_paths["broken"] 指向不存在的檔；PIL.Image.open 應 raise
    assert c.qpixmaps.get("broken") is None
    assert c.qpixmaps_medium.get("broken") is None


def test_delegation_properties(cache):
    c, _ = cache
    assert c.skills == c.skill_loader.skills
    assert c.get_all_skills() is c.skill_loader.skills
    assert c.get_skill("a")["icon"] == "a.png"
    assert c.get_skill("missing") is None
