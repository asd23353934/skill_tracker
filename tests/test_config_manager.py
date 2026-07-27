"""infrastructure.config_manager 測試 — 檔名驗證 / config+user split /
profile CRUD / potion save CRUD / autosave。所有 I/O 都走 tmp_path。"""

import json
import os

import pytest

from src.infrastructure.config_manager import ConfigManager


def _cm(config_path):
    """建 ConfigManager，user 可變區指向 config.json 同層（測試用 tmp 目錄）

    正式預設是 `user_data_path("")`（exe 同層 / 專案根），測試必須明確指定，
    否則會寫進真實專案目錄。
    """
    return ConfigManager(config_path, user_dir=os.path.dirname(config_path))


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
    return _cm(_write_config(tmp_path))


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
    # S5：Windows 不允許字元
    ("a<bad",            False),
    ("a>bad",            False),
    (' "quoted"',        False),
    ("pipe|bad",         False),
    ("ques?",            False),
    ("star*",            False),
    ("ads:stream",       False),    # NTFS Alternate Data Stream
    # S5：開頭空白
    (" leading",         False),
    # S5：控制字元（含 NUL）
    ("name\x00null",     False),
    ("name\x01ctrl",     False),
    ("name\x1fdel",      False),
    # S5：過長
    ("a" * 201,          False),
    ("a" * 200,          True),
])
def test_validate_filename(name, ok):
    assert ConfigManager._validate_filename(name) is ok


# ── config + user split ───────────────────────────────────

def test_load_creates_user_config_on_first_run(tmp_path):
    cfg = _write_config(tmp_path)
    user_path = tmp_path / "config_user.json"
    assert not user_path.exists()
    _cm(cfg)
    # 第一次跑就應該寫出 user 檔
    assert user_path.exists()


def test_stripped_config_uses_default_settings(tmp_path):
    cfg = _write_config(tmp_path, stripped=True)
    cm = _cm(cfg)
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
    cm = _cm(cfg)
    assert cm.config["settings"]["player_name"] == "custom"
    assert cm.config["monsters"][0]["id"] == "m2"


def test_save_only_writes_user_config(tmp_path):
    cfg_path = _write_config(tmp_path)
    cm = _cm(cfg_path)
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


# ── atomic write（_atomic_write_json） ──────────────────────

def test_atomic_write_does_not_touch_target_on_failure(cm, tmp_path, monkeypatch):
    """json.dump 失敗時，原檔不變，且 tmp 已清理。"""
    from src.infrastructure import helpers as helpers_mod

    cm.save_profile("victim", {"hotkeys": {"a": "F1"}})
    profile_path = tmp_path / "profiles" / "victim.json"
    original = profile_path.read_text(encoding="utf-8")

    def _bad_dump(*args, **kwargs):
        raise OSError("disk full")
    monkeypatch.setattr(helpers_mod.json, "dump", _bad_dump)

    assert cm.save_profile("victim", {"hotkeys": {"b": "F2"}}) is False

    assert profile_path.read_text(encoding="utf-8") == original
    leftovers = [p for p in (tmp_path / "profiles").iterdir()
                 if p.name.startswith(".tmp_")]
    assert leftovers == []


def test_atomic_write_user_config_preserves_old_on_failure(tmp_path, monkeypatch):
    """_write_user_config 失敗時，舊 config_user.json 不被截斷。"""
    from src.infrastructure import helpers as helpers_mod

    cfg = _write_config(tmp_path)
    cm = _cm(cfg)
    user_path = tmp_path / "config_user.json"
    original = user_path.read_text(encoding="utf-8")

    def _bad_dump(*args, **kwargs):
        raise OSError("disk full")
    monkeypatch.setattr(helpers_mod.json, "dump", _bad_dump)

    cm.set_settings("player_name", "should_not_persist")
    assert cm.save() is False
    assert user_path.read_text(encoding="utf-8") == original


def test_atomic_write_uses_replace_not_truncate(tmp_path, monkeypatch):
    """確認 atomic_write_json 走 os.replace 而非直接 open(w)。"""
    from src.infrastructure import helpers as helpers_mod

    calls = []
    real_replace = os.replace

    def _spy_replace(src, dst):
        calls.append((src, dst))
        return real_replace(src, dst)

    monkeypatch.setattr(helpers_mod.os, "replace", _spy_replace)

    cm = _cm(_write_config(tmp_path))
    cm.save_profile("foo", {"hotkeys": {}})

    assert any(dst.endswith("foo.json") for _, dst in calls)


# ── user_dir 分離 + legacy 遷移 ────────────────────────────
# 打包後 config.json 位於 PyInstaller 的 _internal/（每次更新被 ZIP 整包覆蓋），
# user 可變區必須放 exe 同層才不會被更新洗掉。以下用兩個 tmp 子目錄模擬。

def _split_dirs(tmp_path):
    """建立 (bundle_dir, user_dir) 兩個目錄，模擬 _internal/ 與 exe 同層"""
    bundle = tmp_path / "_internal"
    user = tmp_path / "app"
    bundle.mkdir()
    user.mkdir()
    return bundle, user


def test_user_dir_keeps_user_data_out_of_bundle_dir(tmp_path):
    """指定 user_dir 後，user 檔只寫進 user_dir，不落在 config.json 同層。"""
    bundle, user = _split_dirs(tmp_path)
    cfg = _write_config(bundle, stripped=True)

    cm = ConfigManager(cfg, user_dir=str(user))
    cm.ensure_default_profile()

    assert (user / "config_user.json").exists()
    assert (user / "profiles" / "預設配置.json").exists()
    assert not (bundle / "config_user.json").exists()
    assert not (bundle / "profiles").exists()


def test_legacy_user_data_migrated_from_bundle_dir(tmp_path):
    """升級情境：舊版寫在 _internal/ 的 user 資料要被接過來，設定不可遺失。"""
    bundle, user = _split_dirs(tmp_path)
    cfg = _write_config(bundle, stripped=True)
    (bundle / "config_user.json").write_text(json.dumps({
        "settings": {"player_name": "老玩家", "window_size": 128},
        "monsters": [], "overlays": [],
    }, ensure_ascii=False), encoding="utf-8")
    (bundle / "profiles").mkdir()
    (bundle / "profiles" / "我的配置.json").write_text(
        json.dumps({"hotkeys": {"s1": "F1"}}), encoding="utf-8")
    (bundle / "potion_autosave.json").write_text("{}", encoding="utf-8")

    cm = ConfigManager(cfg, user_dir=str(user))

    assert cm.config["settings"]["player_name"] == "老玩家"
    assert cm.config["settings"]["window_size"] == 128
    assert "我的配置" in cm.list_profiles()
    assert cm.load_profile("我的配置")["hotkeys"] == {"s1": "F1"}
    assert (user / "potion_autosave.json").exists()


def test_migration_never_overwrites_existing_user_dir_data(tmp_path):
    """更新後回歸：ZIP 帶來的預設 _internal/config_user.json 不得蓋掉使用者的設定。"""
    bundle, user = _split_dirs(tmp_path)
    cfg = _write_config(bundle, stripped=True)
    # 使用者本機（exe 同層）已有自訂設定
    (user / "config_user.json").write_text(json.dumps({
        "settings": {"player_name": "我的名字", "window_size": 128},
        "monsters": [], "overlays": [],
    }, ensure_ascii=False), encoding="utf-8")
    # _internal/ 內是更新解壓帶進來的全預設值
    (bundle / "config_user.json").write_text(json.dumps({
        "settings": {"player_name": "玩家1", "window_size": 96},
        "monsters": [], "overlays": [],
    }, ensure_ascii=False), encoding="utf-8")

    cm = ConfigManager(cfg, user_dir=str(user))

    assert cm.config["settings"]["player_name"] == "我的名字"
    assert cm.config["settings"]["window_size"] == 128


def test_potion_paths_follow_user_dir(tmp_path):
    """練功水錢存檔 / autosave 也要跟著 user_dir，不落在 bundle 目錄。"""
    bundle, user = _split_dirs(tmp_path)
    cm = ConfigManager(_write_config(bundle, stripped=True), user_dir=str(user))

    assert cm.save_potion_record("rec", {"a": 1}) is True
    assert cm.save_potion_autosave({"b": 2}) is True

    assert (user / "potion_saves" / "rec.json").exists()
    assert (user / "potion_autosave.json").exists()
    assert not (bundle / "potion_saves").exists()
    assert not (bundle / "potion_autosave.json").exists()


def test_default_user_dir_stays_beside_config(tmp_path):
    """不傳 user_dir 時維持舊行為（開發模式：與 config.json 同層）。"""
    cm = _cm(_write_config(tmp_path))
    assert os.path.abspath(cm.user_dir) == os.path.abspath(str(tmp_path))
    assert (tmp_path / "config_user.json").exists()
