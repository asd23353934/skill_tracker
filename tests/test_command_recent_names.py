"""指令頁 per-command 名稱記憶測試。

- promote_recent 純函式：提前 / 去重 / 上限 / 空名稱（對應 Remember used player names）
- ConfigManager per-command 讀寫：新增 / 刪除 / 改名 / per-command 隔離 / 持久化 / 型別防禦
- 升級相容：command_names map 缺 → 以舊共用 command_recent_names 為唯讀 fallback
  （對應 Backward-compatible recent-names storage）

所有 I/O 走 tmp_path。
"""

import json

from src.infrastructure.config_manager import (
    ConfigManager, promote_recent, _MAX_RECENT_COMMAND_NAMES,
)


def _make_cm(tmp_path, *, recent=None, command_names=None):
    """在 tmp_path 寫一份 config.json 並回傳 ConfigManager。

    recent          → settings.command_recent_names（legacy 共用清單）初值
    command_names   → settings.command_names（per-command map）初值
    """
    settings = {"current_profile": "預設配置"}
    if recent is not None:
        settings["command_recent_names"] = recent
    if command_names is not None:
        settings["command_names"] = command_names
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


# ── per-command 新增 / 取得 / 持久化 ──

def test_add_then_get_persists_and_promotes(tmp_path):
    cm = _make_cm(tmp_path)
    cm.add_command_name("trade", "Apple#aSqOX")
    cm.add_command_name("trade", "Bob#1a2b3")
    cm.add_command_name("trade", "Apple#aSqOX")  # 重用 → 提到最前
    assert cm.get_command_names("trade") == ["Apple#aSqOX", "Bob#1a2b3"]
    # 重新載入驗證持久化（save 寫入 config_user.json）
    cm2 = ConfigManager(cm.config_path)
    assert cm2.get_command_names("trade") == ["Apple#aSqOX", "Bob#1a2b3"]


def test_names_isolated_per_command(tmp_path):
    cm = _make_cm(tmp_path)
    cm.add_command_name("trade", "Carol#9z9z9")
    assert cm.get_command_names("trade") == ["Carol#9z9z9"]
    # 另一指令不受影響
    assert cm.get_command_names("whisper") == []


def test_add_blank_name_is_noop(tmp_path):
    cm = _make_cm(tmp_path)
    cm.add_command_name("trade", "   ")
    cm.add_command_name("trade", "")
    assert cm.get_command_names("trade") == []


def test_add_returns_updated_list(tmp_path):
    cm = _make_cm(tmp_path)
    assert cm.add_command_name("trade", "X") == ["X"]
    assert cm.add_command_name("trade", "Y") == ["Y", "X"]


def test_invalid_key_is_safe(tmp_path):
    cm = _make_cm(tmp_path)
    assert cm.add_command_name("", "X") == []
    assert cm.get_command_names("") == []
    assert cm.remove_command_name("", "X") == []
    assert cm.rename_command_name("", "a", "b") == []


# ── per-command 刪除 / 改名 ──

def test_remove_command_name(tmp_path):
    cm = _make_cm(tmp_path, command_names={"whisper": ["Bob#1a2b3", "Eve#2c2c2"]})
    assert cm.remove_command_name("whisper", "Bob#1a2b3") == ["Eve#2c2c2"]
    cm2 = ConfigManager(cm.config_path)
    assert cm2.get_command_names("whisper") == ["Eve#2c2c2"]


def test_rename_in_place_preserves_position(tmp_path):
    cm = _make_cm(tmp_path, command_names={"whisper": ["A", "Bob#1a2b3", "C"]})
    assert cm.rename_command_name("whisper", "Bob#1a2b3", "Bob#4c5d6") == ["A", "Bob#4c5d6", "C"]


def test_rename_empty_deletes(tmp_path):
    cm = _make_cm(tmp_path, command_names={"whisper": ["A", "B"]})
    assert cm.rename_command_name("whisper", "A", "  ") == ["B"]


def test_rename_dedupes_against_existing(tmp_path):
    cm = _make_cm(tmp_path, command_names={"whisper": ["A", "B", "C"]})
    # 把 C 改成 A → 與既有 A 重複，去重保留最前
    assert cm.rename_command_name("whisper", "C", "A") == ["A", "B"]


def test_rename_missing_old_adds_when_new_nonempty(tmp_path):
    cm = _make_cm(tmp_path, command_names={"whisper": ["A"]})
    assert cm.rename_command_name("whisper", "ZZZ", "New") == ["New", "A"]


# ── 升級相容：command_names map 缺 → 舊共用清單作 fallback ──

def test_legacy_fallback_seeds_every_command(tmp_path):
    # 只有 legacy 共用清單、無 command_names map
    cm = _make_cm(tmp_path, recent=["Old1", "Old2"])
    assert cm.get_command_names("trade") == ["Old1", "Old2"]
    assert cm.get_command_names("whisper") == ["Old1", "Old2"]


def test_legacy_key_untouched_after_per_command_write(tmp_path):
    cm = _make_cm(tmp_path, recent=["Old1", "Old2"])
    cm.add_command_name("trade", "New")
    # legacy 共用清單原樣保留（唯讀 fallback，不就地改寫）
    assert cm.get_settings("command_recent_names") == ["Old1", "Old2"]
    # per-key fallback：已寫入的 trade 以 map 為準；尚未寫入的 whisper 仍繼承 legacy
    assert cm.get_command_names("trade") == ["New", "Old1", "Old2"]
    assert cm.get_command_names("whisper") == ["Old1", "Old2"]


def test_delete_one_command_does_not_clear_others(tmp_path):
    # 回歸：對一個指令首次刪除名稱，不可連帶清空其他尚未操作指令的繼承名單
    cm = _make_cm(tmp_path, recent=["X", "Y", "Z"])
    assert cm.remove_command_name("trade", "Y") == ["X", "Z"]
    # 其他未操作指令仍保有繼承的 legacy 名單
    assert cm.get_command_names("whisper") == ["X", "Y", "Z"]


def test_emptied_key_does_not_refill_from_legacy(tmp_path):
    # 已寫入並刪到空的 key 維持空清單，不回填 legacy（仍區分「從未寫入」）
    cm = _make_cm(tmp_path, recent=["X", "Y"])
    cm.remove_command_name("trade", "X")
    cm.remove_command_name("trade", "Y")
    assert cm.get_command_names("trade") == []
    assert cm.get_command_names("whisper") == ["X", "Y"]


def test_no_fields_returns_empty(tmp_path):
    cm = _make_cm(tmp_path)
    assert cm.get_command_names("trade") == []


# ── 型別防禦 ──

def test_get_command_names_non_dict_map_falls_back(tmp_path):
    # command_names 非 dict（手改壞檔）→ 視為缺 map，走 legacy fallback
    cm = _make_cm(tmp_path, recent=["L"], command_names="oops")
    assert cm.get_command_names("trade") == ["L"]


def test_get_command_names_filters_non_str(tmp_path):
    cm = _make_cm(tmp_path, command_names={"trade": ["ok", 123, "", None, "good"]})
    assert cm.get_command_names("trade") == ["ok", "good"]
