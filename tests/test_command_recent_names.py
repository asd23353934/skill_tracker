"""指令頁「最近使用玩家名稱」記憶測試。

- promote_recent 純函式：提前 / 去重 / 上限 / 空名稱（對應 Remember used player names）
- ConfigManager 讀寫：缺鍵讀空、持久化、防禦非 list/非 str（對應 Backward-compatible recent-names storage）

所有 I/O 走 tmp_path。
"""

import json

from src.infrastructure.config_manager import (
    ConfigManager, promote_recent, _MAX_RECENT_COMMAND_NAMES,
)


def _make_cm(tmp_path, recent=None):
    """在 tmp_path 寫一份 config.json 並回傳 ConfigManager；recent 為 settings 內的初始值"""
    settings = {"current_profile": "預設配置"}
    if recent is not None:
        settings["command_recent_names"] = recent
    data = {"skills": [], "items": [], "settings": settings, "monsters": [], "overlays": []}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return ConfigManager(str(path))


# ── promote_recent 純函式 ──

def test_promote_new_name_prepends():
    assert promote_recent(["A", "B", "C"], "D") == ["D", "A", "B", "C"]


def test_promote_existing_moves_to_front_without_dup():
    assert promote_recent(["A", "B", "C"], "B") == ["B", "A", "C"]


def test_promote_dedupes_existing_list():
    assert promote_recent(["A", "A", "B"], "C") == ["C", "A", "B"]


def test_promote_empty_name_only_dedupes():
    # 空名稱不新增，僅回傳去重後的既有清單
    assert promote_recent(["A", "B"], "") == ["A", "B"]
    assert promote_recent(["A", "A", "B"], "") == ["A", "B"]


def test_promote_caps_at_limit():
    names = [f"n{i}" for i in range(_MAX_RECENT_COMMAND_NAMES)]  # 20 個相異
    out = promote_recent(names, "new")
    assert len(out) == _MAX_RECENT_COMMAND_NAMES
    assert out == ["new"] + names[:_MAX_RECENT_COMMAND_NAMES - 1]


def test_promote_preserves_hash_code():
    assert promote_recent([], "Apple#aSqOX") == ["Apple#aSqOX"]


# ── ConfigManager 讀寫（缺鍵 / 持久化 / 防禦）──

def test_get_recent_missing_key_returns_empty(tmp_path):
    cm = _make_cm(tmp_path)  # settings 無 command_recent_names
    assert cm.get_recent_command_names() == []


def test_add_then_get_persists_and_promotes(tmp_path):
    cm = _make_cm(tmp_path)
    cm.add_recent_command_name("Apple#aSqOX")
    cm.add_recent_command_name("Bob#1a2b3")
    cm.add_recent_command_name("Apple#aSqOX")  # 重用 → 提到最前
    assert cm.get_recent_command_names() == ["Apple#aSqOX", "Bob#1a2b3"]
    # 重新載入驗證持久化（save 寫入 config_user.json）
    cm2 = ConfigManager(cm.config_path)
    assert cm2.get_recent_command_names() == ["Apple#aSqOX", "Bob#1a2b3"]


def test_add_blank_name_is_noop(tmp_path):
    cm = _make_cm(tmp_path)
    cm.add_recent_command_name("   ")
    cm.add_recent_command_name("")
    assert cm.get_recent_command_names() == []


def test_get_recent_non_list_returns_empty(tmp_path):
    cm = _make_cm(tmp_path, recent="oops")  # 非 list（手改壞檔）
    assert cm.get_recent_command_names() == []


def test_get_recent_filters_non_str_elements(tmp_path):
    cm = _make_cm(tmp_path, recent=["ok", 123, "", None, "good"])
    assert cm.get_recent_command_names() == ["ok", "good"]
