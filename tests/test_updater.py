"""infrastructure.updater 純邏輯測試

只測不需要實際打網路的部分：
- current_version 為 None 時不檢查（C11 修法）
- _compare_versions 對極值的容錯
"""

from src.infrastructure.updater import Updater


# ── C11：current_version 未知時 skip ────────────────────────

def test_check_skipped_when_current_version_none(monkeypatch):
    """import version 失敗 fallback 為 None → check_for_updates 立即回 not-available。

    防止舊版本（過去硬編 "1.0.8"）導致每次啟動都被判為「有新版」、誤觸下載
    流程把 user 從新版降級回舊版。
    """
    upd = Updater()
    upd.current_version = None

    result = upd.check_for_updates()
    assert result["available"] is False
    assert "unknown" in result.get("error", "").lower()


def test_check_skipped_does_not_hit_network(monkeypatch):
    """current_version=None 路徑早於 requests 呼叫返回，不應產生網路 I/O。"""
    import src.infrastructure.updater as upd_mod

    called = {"n": 0}

    def _fake_get(*args, **kwargs):
        called["n"] += 1
        raise AssertionError("network should not be called")

    monkeypatch.setattr(upd_mod.requests, "get", _fake_get)

    upd = Updater()
    upd.current_version = None
    upd.check_for_updates()

    assert called["n"] == 0


# ── _compare_versions 容錯 ──────────────────────────────────

def test_compare_versions_normal_case():
    upd = Updater()
    assert upd._compare_versions("4.3.7", "4.3.6") is True
    assert upd._compare_versions("4.3.6", "4.3.7") is False
    assert upd._compare_versions("4.3.6", "4.3.6") is False


def test_compare_versions_garbage_returns_false():
    """malformed 版本字串應 return False（不更新），不可 raise。"""
    upd = Updater()
    assert upd._compare_versions("not.a.version", "4.3.6") is False
    assert upd._compare_versions("", "4.3.6") is False
