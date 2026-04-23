"""
Release-time strip：把 config.json 內 user 可變區（settings / monsters / overlays）
重設成乾淨預設值，並加上 _user_data_stripped 標記；保留 skills / items 不動。

用法：
    python scripts/strip_config_for_release.py            # strip + 備份
    python scripts/strip_config_for_release.py --restore  # 恢復備份

工作流：
    python scripts/strip_config_for_release.py
    pyinstaller skill_tracker.spec
    python scripts/strip_config_for_release.py --restore
"""

from __future__ import annotations

import argparse
import json
import os
import sys

CONFIG = "config.json"
BACKUP = "config.json.dev_backup"

# 與 ConfigManager.DEFAULT_USER_SETTINGS 一致；避免 import （腳本不依賴 src）
DEFAULT_SETTINGS = {
    "player_name":          "玩家1",
    "skill_start_x":        None,
    "skill_start_y":        None,
    "enable_sound":         True,
    "sound_volume":         100,
    "window_size":          64,
    "alert_before_seconds": 0,
    "hint_position_x":      0,
    "hint_position_y":      0,
    "global_sound":         "",
    "global_alert_sound":   "",
    "current_profile":      "預設配置",
}


def strip():
    if not os.path.exists(CONFIG):
        print(f"找不到 {CONFIG}", file=sys.stderr)
        return 1
    if os.path.exists(BACKUP):
        print(f"備份已存在：{BACKUP}（請先 --restore 或手動處理）",
              file=sys.stderr)
        return 1

    with open(CONFIG, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # 備份原檔
    os.replace(CONFIG, BACKUP)
    print(f"已備份 {CONFIG} → {BACKUP}")

    # 寫 stripped 版本
    cfg["settings"] = dict(DEFAULT_SETTINGS)
    cfg["monsters"] = []
    cfg["overlays"] = []
    cfg["_user_data_stripped"] = True

    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"已寫入 stripped {CONFIG}（settings 重設、monsters/overlays 清空、加 _user_data_stripped 標記）")
    return 0


def restore():
    if not os.path.exists(BACKUP):
        print(f"找不到備份檔 {BACKUP}", file=sys.stderr)
        return 1
    os.replace(BACKUP, CONFIG)
    print(f"已恢復 {BACKUP} → {CONFIG}")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--restore", action="store_true",
                   help="恢復備份（PyInstaller build 完用）")
    args = p.parse_args()
    return restore() if args.restore else strip()


if __name__ == "__main__":
    sys.exit(main())
