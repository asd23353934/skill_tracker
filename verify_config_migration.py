"""
ConfigManager 分檔載入 / migration 單元驗證

執行：`python verify_config_migration.py` —— 全部通過 exit code = 0
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

from src.infrastructure.config_manager import ConfigManager


_failures: list[str] = []


def check(label: str, got, expected):
    if got == expected:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}: got {got!r}, expected {expected!r}")
        _failures.append(label)


def _write(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _stripped_config():
    """模擬 release ZIP 內 config.json"""
    return {
        "skills":   [{"id": "s1", "name": "技能 A"}],
        "items":    [],
        "settings": {"sound_volume": 100, "player_name": "玩家1"},
        "monsters": [],
        "overlays": [],
        "_user_data_stripped": True,
    }


def _pre_split_config():
    """模擬 pre-split 版本 user 本機 config.json（含個人 user data）"""
    return {
        "skills":   [{"id": "s1", "name": "技能 A"}],
        "items":    [],
        "settings": {"sound_volume": 50, "player_name": "Alice"},
        "monsters": [{"id": "m1", "name": "魚屋"}],
        "overlays": [{"id": "ov1", "file": "x.png"}],
    }


# ════════════════════════════════════════════════════════════
# Tests
# ════════════════════════════════════════════════════════════

def test_fresh_install_creates_user_file():
    print("[test_fresh_install_creates_user_file]")
    with tempfile.TemporaryDirectory() as d:
        cfg_path = os.path.join(d, "config.json")
        user_path = os.path.join(d, "config_user.json")
        _write(cfg_path, _stripped_config())

        ConfigManager(cfg_path)
        check("config_user.json created", os.path.exists(user_path), True)

        user = _read(user_path)
        check("settings is default sound_volume",
              user["settings"].get("sound_volume"), 100)
        check("monsters empty", user["monsters"], [])
        check("overlays empty", user["overlays"], [])


def test_migration_from_pre_split():
    print("[test_migration_from_pre_split]")
    with tempfile.TemporaryDirectory() as d:
        cfg_path = os.path.join(d, "config.json")
        user_path = os.path.join(d, "config_user.json")
        _write(cfg_path, _pre_split_config())

        ConfigManager(cfg_path)
        check("config_user.json created", os.path.exists(user_path), True)

        user = _read(user_path)
        check("migrated sound_volume", user["settings"].get("sound_volume"), 50)
        check("migrated player_name",
              user["settings"].get("player_name"), "Alice")
        check("migrated monsters preserved", len(user["monsters"]), 1)
        check("migrated overlays preserved", len(user["overlays"]), 1)


def test_existing_user_file_wins():
    print("[test_existing_user_file_wins]")
    with tempfile.TemporaryDirectory() as d:
        cfg_path = os.path.join(d, "config.json")
        user_path = os.path.join(d, "config_user.json")
        _write(cfg_path, _stripped_config())  # config has sound_volume=100
        _write(user_path, {
            "settings": {"sound_volume": 50},
            "monsters": [],
            "overlays": [],
        })

        cm = ConfigManager(cfg_path)
        check("user file wins", cm.get_settings("sound_volume"), 50)


def test_save_writes_only_user_file():
    print("[test_save_writes_only_user_file]")
    with tempfile.TemporaryDirectory() as d:
        cfg_path = os.path.join(d, "config.json")
        user_path = os.path.join(d, "config_user.json")
        _write(cfg_path, _stripped_config())

        cm = ConfigManager(cfg_path)
        # 記下 config.json 的 byte 內容
        with open(cfg_path, "rb") as f:
            cfg_before = f.read()

        cm.set_settings("sound_volume", 75)
        cm.save()

        with open(cfg_path, "rb") as f:
            cfg_after = f.read()
        check("config.json byte-for-byte unchanged", cfg_after, cfg_before)

        user = _read(user_path)
        check("user file got new sound_volume",
              user["settings"].get("sound_volume"), 75)


def test_static_zone_refreshed_from_bundled():
    print("[test_static_zone_refreshed_from_bundled]")
    with tempfile.TemporaryDirectory() as d:
        cfg_path = os.path.join(d, "config.json")
        user_path = os.path.join(d, "config_user.json")
        _write(cfg_path, _stripped_config())  # has 1 skill
        ConfigManager(cfg_path)  # creates user file

        # 模擬升級：bundled config.json 加入新技能
        new_cfg = _stripped_config()
        new_cfg["skills"].append({"id": "s2", "name": "新技能 B"})
        _write(cfg_path, new_cfg)

        # 同時 user 檔已有自訂值
        _write(user_path, {
            "settings": {"sound_volume": 30},
            "monsters": [{"id": "boss"}],
            "overlays": [],
        })

        cm = ConfigManager(cfg_path)
        skills_ids = [s["id"] for s in cm.config.get("skills", [])]
        check("bundled new skill picked up", "s2" in skills_ids, True)
        check("user sound_volume preserved",
              cm.get_settings("sound_volume"), 30)
        check("user monsters preserved", len(cm.config["monsters"]), 1)


# ════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════

def main():
    test_fresh_install_creates_user_file()
    test_migration_from_pre_split()
    test_existing_user_file_wins()
    test_save_writes_only_user_file()
    test_static_zone_refreshed_from_bundled()
    if _failures:
        print(f"\nFAILED: {len(_failures)} check(s)")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
