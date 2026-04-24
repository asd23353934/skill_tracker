"""mapleworld_widgets_v2 分類 cache load/save schema 測試

僅測 _extract_tags（純函數、無 Qt），load/save 走磁碟的由 integration 驗。
"""

import importlib

import pytest

# mapleworld_widgets_v2 裡面 import 了 PySide6.QtWidgets；測試環境沒有 QApplication
# 也能 import 模組本身（不會 instantiate widget）。以 pytest.importorskip 保底。
w = pytest.importorskip("src.ui_v2.pages.mapleworld_widgets_v2")


def test_v2_format_round_trip():
    tags = {"a.png": "≤16", "b.png": "65-128"}
    payload = {"version": w.CLASSIFY_CACHE_VERSION, "tags": tags}
    assert w._extract_tags(payload) == tags


def test_v2_wrong_version_rejected():
    payload = {"version": 999, "tags": {"a.png": "≤16"}}
    assert w._extract_tags(payload) is None


def test_v2_invalid_category_rejected():
    payload = {"version": w.CLASSIFY_CACHE_VERSION, "tags": {"a.png": "legacy-label"}}
    assert w._extract_tags(payload) is None


def test_v1_plain_dict_compat():
    legacy = {"a.png": "≤16", "b.png": ">1024"}
    assert w._extract_tags(legacy) == legacy


def test_v1_plain_dict_with_bad_value_rejected():
    legacy = {"a.png": "some-old-label"}
    assert w._extract_tags(legacy) is None


def test_non_dict_rejected():
    assert w._extract_tags([1, 2, 3]) is None
    assert w._extract_tags("string") is None
    assert w._extract_tags(None) is None


def test_v2_missing_tags_rejected():
    payload = {"version": w.CLASSIFY_CACHE_VERSION}
    assert w._extract_tags(payload) is None


def test_save_load_roundtrip_on_disk(tmp_path, monkeypatch):
    # 把 cache 路徑重導向到 tmp
    fake_path = tmp_path / "cache.json"
    monkeypatch.setattr(w, "CLASSIFY_CACHE_PATH", str(fake_path))
    monkeypatch.setattr(w, "_LEGACY_CACHE_PATH", str(tmp_path / "_nowhere.json"))

    tags = {"x.png": "33-64", "y.png": "257-512"}
    w.save_classify_cache(tags)
    assert fake_path.exists()

    loaded = w.load_classify_cache()
    assert loaded == tags

    # 確認磁碟格式真的有 version 欄位
    import json as _json
    with open(fake_path, encoding="utf-8") as f:
        raw = _json.load(f)
    assert raw["version"] == w.CLASSIFY_CACHE_VERSION
    assert raw["tags"] == tags
