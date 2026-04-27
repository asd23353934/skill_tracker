"""infrastructure.config_manager 測試 — 檔名驗證 / config+user split /
profile CRUD / potion save CRUD / autosave。所有 I/O 都走 tmp_path。"""

import json
import os

import pytest

from src.infrastructure.config_manager import ConfigManager


# ── fixtures ───────────────────────────────────────────────

def _write_config(tmp_path, stripped=False, settings=None, monsters=None, overlays=None):
    """寫一份 config.json 到 tmp_path，回傳其絕對路徑"""
    data = {
        "skills":  [{"id": "s1", "name": "S", "icon": "s.png", "cooldown": 30, "category": "player"}],
        "items":   [],
        "settings": settings if settings is not None else {"current_profile": "預設配置"},
        "monsters": monsters if monsters is not None else [{"id": "m1", "respawn_time": 60, "name": "M", "icon": "i"}],
        "overlays": overlays if overlays is not None else [],
    }
    if stripped:
        data["_user_data_stripped"] = True
        data["settings"] = {}
        data["monsters"] = []
        data["overlays"] = []
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)


@pytest.fixture
def cm(tmp_path):
    return ConfigManager(_write_config(tmp_path))


# ── _validate_filename ────────────────────────────────────

@pytest.mark.parametrize("name,ok", [
    ("normal",           True),
    ("中文名稱",         True),
    ("with space",       True),
    ("",                 False),
    ("../escape",        False),
    ("../../root",       False),
    ("a/b",              False),
    ("a\\b",             False),
    ("trailing ",        False),
    ("trailing.",        False),
    ("CON",              False),
    ("con",              False),
    ("PRN.txt",          False),
    ("COM1",             False),
    ("LPT9",             False),
    ("AUX",              False),
    ("NUL",              False),
    ("notcon",           True),
])
def test_validate_filename(name, ok):
    assert ConfigManager._validate_filename(name) is ok


# ── config + user split ───────────────────────────────────

def test_load_creates_user_config_on_first_run(tmp_path):
    cfg = _write_config(tmp_path)
    user_path = tmp_path / "config_user.json"
    assert not user_path.exists()
    ConfigManager(cfg)
    # 第一次跑就應該寫出 user 檔
    assert user_path.exists()


def test_stripped_config_uses_default_settings(tmp_path):
    cfg = _write_config(tmp_path, stripped=True)
    cm = ConfigManager(cfg)
    assert cm.config["settings"]["player_name"] == "玩家1"
    # monsters 允許跟著 ship default（空 list）
    assert cm.config["monsters"] == []


def test_existing_user_config_overrides_inmemory(tmp_path):
    cfg = _write_config(tmp_path)
    # 先建一個 user 檔，跟 config.json 不同內容
    (tmp_path / "config_user.json").write_text(json.dumps({
        "settings": {"player_name": "custom"},
        "monsters": [{"id": "m2", "respawn_time": 99, "name": "M2", "icon": "i2"}],
        "overlays": [],
    }, ensure_ascii=False), encoding="utf-8")
    cm = ConfigManager(cfg)
    assert cm.config["settings"]["player_name"] == "custom"
    assert cm.config["monsters"][0]["id"] == "m2"


def test_save_only_writes_user_config(tmp_path):
    cfg_path = _write_config(tmp_path)
    cm = ConfigManager(cfg_path)
    # 記錄 config.json 原始 mtime
    cfg_mtime = os.path.getmtime(cfg_path)
    cm.set_settings("player_name", "changed")
    # 避免 mtime 解析度問題，讓 save 寫到不同內容即可
    assert cm.save() is True
    # config.json 磁碟內容不變（靜態區不被 save 動到）
    with open(cfg_path, encoding="utf-8") as f:
        disk = json.load(f)
    assert disk["settings"].get("player_name") != "changed"
    # user 檔內容確實改變
    with open(tmp_path / "config_user.json", encoding="utf-8") as f:
        user = json.load(f)
    assert user["settings"]["player_name"] == "changed"


# ── initial_skills / initial_items / initial_monsters ────

def test_initial_snapshots_available(cm):
    assert len(cm.initial_skills) == 1
    assert cm.initial_skills[0]["id"] == "s1"
    assert cm.initial_items == []
    assert cm.initial_monsters == {"m1": 60}


def test_get_original_respawn_time(cm):
    assert cm.get_original_respawn_time("m1") == 60
    assert cm.get_original_respawn_time("missing") is None


# ── profile CRUD ──────────────────────────────────────────

def test_profile_save_load_roundtrip(cm):
    data = {"hotkeys": {"a": "F1"}, "permanent": {"a": True}}
    assert cm.save_profile("test", data) is True
    loaded = cm.load_profile("test")
    assert loaded["hotkeys"] == {"a": "F1"}
    assert loaded["permanent"] == {"a": True}


def test_profile_load_fills_missing_keys(cm):
    cm.save_profile("minimal", {"hotkeys": {}})
    loaded = cm.load_profile("minimal")
    for key in ("hotkeys", "permanent", "loop", "alert_enabled", "cooldown_overrides"):
        assert key in loaded


def test_profile_save_rejects_bad_name(cm):
    assert cm.save_profile("../hack", {}) is False
    assert cm.save_profile("CON", {}) is False
    assert cm.save_profile("", {}) is False


def test_profile_load_rejects_bad_name(cm):
    assert cm.load_profile("../hack") is None


def test_profile_load_missing_file_returns_none(cm):
    assert cm.load_profile("nonexistent") is None


def test_profile_list_sorted(cm):
    cm.save_profile("b", {})
    cm.save_profile("a", {})
    cm.save_profile("c", {})
    profiles = cm.list_profiles()
    assert profiles == sorted(profiles)
    assert set(profiles) >= {"a", "b", "c"}


def test_profile_delete(cm):
    cm.save_profile("target", {})
    assert "target" in cm.list_profiles()
    assert cm.delete_profile("target") is True
    assert "target" not in cm.list_profiles()


def test_profile_delete_rejects_bad_name(cm):
    assert cm.delete_profile("../hack") is False


def test_profile_rename(cm):
    cm.save_profile("old", {"hotkeys": {"a": "F1"}})
    assert cm.rename_profile("old", "new") is True
    assert cm.load_profile("old") is None
    assert cm.load_profile("new")["hotkeys"] == {"a": "F1"}


def test_profile_rename_rejects_bad_names(cm):
    cm.save_profile("old", {})
    assert cm.rename_profile("old", "../hack") is False
    assert cm.rename_profile("../hack", "new") is False


def test_ensure_default_profile_creates(cm):
    assert "預設配置" not in cm.list_profiles()
    cm.ensure_default_profile()
    assert "預設配置" in cm.list_profiles()


def test_ensure_default_profile_idempotent(cm):
    cm.ensure_default_profile()
    cm.ensure_default_profile()
    count = cm.list_profiles().count("預設配置")
    assert count == 1


# ── potion record CRUD ──────────────────────────────────

def test_potion_save_load_roundtrip(cm):
    data = {"duration_minutes": 30, "mesos_start": 100}
    assert cm.save_potion_record("run1", data) is True
    loaded = cm.load_potion_record("run1")
    assert loaded == data


def test_potion_save_rejects_bad_name(cm):
    assert cm.save_potion_record("../hack", {}) is False


def test_potion_list_sorted_by_mtime_desc(cm, tmp_path):
    saves_dir = tmp_path / "potion_saves"
    saves_dir.mkdir(exist_ok=True)
    # 手動建三個檔，依 mtime 設定新舊
    for i, name in enumerate(["old", "mid", "new"]):
        p = saves_dir / f"{name}.json"
        p.write_text("{}", encoding="utf-8")
        # old=1, mid=2, new=3（大=新）
        os.utime(p, (i + 1, i + 1))
    listed = cm.list_potion_saves()
    assert listed == ["new", "mid", "old"]


def test_potion_delete(cm):
    cm.save_potion_record("tmp", {})
    assert cm.delete_potion_record("tmp") is True
    assert cm.load_potion_record("tmp") is None


def test_potion_rename(cm):
    cm.save_potion_record("a", {"x": 1})
    assert cm.rename_potion_record("a", "b") is True
    assert cm.load_potion_record("a") is None
    assert cm.load_potion_record("b") == {"x": 1}


# ── potion autosave ─────────────────────────────────────

def test_potion_autosave_roundtrip(cm):
    assert cm.save_potion_autosave({"v": 1}) is True
    assert cm.load_potion_autosave() == {"v": 1}
    assert cm.delete_potion_autosave() is True
    assert cm.load_potion_autosave() is None


def test_potion_autosave_delete_nonexistent_succeeds(cm):
    # 沒檔也視為成功
    assert cm.delete_potion_autosave() is True


def test_potion_autosave_corrupt_returns_none(cm, tmp_path):
    path = tmp_path / "potion_autosave.json"
    path.write_text("not json {{", encoding="utf-8")
    assert cm.load_potion_autosave() is None
