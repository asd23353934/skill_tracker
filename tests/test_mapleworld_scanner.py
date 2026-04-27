"""infrastructure.mapleworld_scanner 純邏輯測試

只測無 Qt、無檔案 I/O 依賴的 helper：
- classify_image
- extract_images_from_bytes
- scan_unity / scan_web 對不存在路徑的錯誤處理
"""

from io import BytesIO

import pytest
from PIL import Image

from src.infrastructure import mapleworld_scanner as mw


# ════════════════════════════════════════════════════════════
# classify_image — max(w, h) 8 級桶
# ════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "w,h,expected",
    [
        (1,    1,    "≤16"),
        (16,   16,   "≤16"),
        (17,   10,   "17-32"),
        (32,   32,   "17-32"),
        (33,   10,   "33-64"),
        (64,   64,   "33-64"),
        (100,  65,   "65-128"),
        (128,  128,  "65-128"),
        (129,  10,   "129-256"),
        (256,  200,  "129-256"),
        (300,  300,  "257-512"),
        (512,  10,   "257-512"),
        (800,  400,  "513-1024"),
        (1024, 1024, "513-1024"),
        (1025, 10,   ">1024"),
        (2048, 2048, ">1024"),
    ],
)
def test_classify_image_by_max_dimension(w, h, expected):
    img = Image.new("RGBA", (w, h))
    assert mw.classify_image(img) == expected


def test_classify_image_bad_path_returns_last_bucket():
    # 無法打開的路徑 → fallback ">1024"
    assert mw.classify_image("nonexistent_____.png") == ">1024"


def test_categories_cover_size_tiers():
    # 所有 _SIZE_TIERS 的 label 應該都在 CATEGORIES 裡
    for _, label in mw._SIZE_TIERS:
        assert label in mw.CATEGORIES
    # 最後一桶 ">1024" 也必須存在
    assert ">1024" in mw.CATEGORIES


# ════════════════════════════════════════════════════════════
# extract_images_from_bytes — 從雜亂 bytes 抽 PNG / WebP / JPEG
# ════════════════════════════════════════════════════════════

def _png_bytes(size=(32, 32), color=(255, 0, 0, 255)) -> bytes:
    buf = BytesIO()
    Image.new("RGBA", size, color).save(buf, format="PNG")
    return buf.getvalue()


def _jpeg_bytes(size=(40, 40), color=(0, 128, 0)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


def _webp_bytes(size=(48, 48), color=(0, 0, 255, 255)) -> bytes:
    buf = BytesIO()
    Image.new("RGBA", size, color).save(buf, format="WEBP")
    return buf.getvalue()


def test_extract_finds_png_embedded_in_prefix_and_suffix():
    data = b"\x00\x11\x22GARBAGE" + _png_bytes() + b"TAIL_NOISE" * 10
    imgs = mw.extract_images_from_bytes(data)
    assert len(imgs) == 1
    assert imgs[0].size == (32, 32)


def test_extract_finds_multiple_formats():
    data = (
        b"HEAD" + _png_bytes(size=(32, 32))
        + b"|MID|" + _jpeg_bytes(size=(40, 40))
        + b"|END|" + _webp_bytes(size=(48, 48))
    )
    imgs = mw.extract_images_from_bytes(data)
    sizes = sorted(im.size for im in imgs)
    assert (32, 32) in sizes
    assert (40, 40) in sizes
    assert (48, 48) in sizes


def test_extract_filters_images_smaller_than_16x16():
    data = _png_bytes(size=(8, 8))
    assert mw.extract_images_from_bytes(data) == []


def test_extract_returns_empty_on_garbage():
    data = b"\x00" * 256 + b"no image here" + b"\xff" * 256
    assert mw.extract_images_from_bytes(data) == []


def test_extract_deduplicates_same_offset():
    # 同一張 PNG 只會被抓一次（seen_offsets 保證）
    data = _png_bytes()
    imgs = mw.extract_images_from_bytes(data)
    assert len(imgs) == 1


# ════════════════════════════════════════════════════════════
# scan_unity / scan_web — 無效路徑應該立即 on_done(fatal=...)
# ════════════════════════════════════════════════════════════

def test_scan_unity_reports_fatal_when_resource_cache_missing(tmp_path):
    captured = {}

    def on_done(saved, errors, fatal):
        captured["saved"] = saved
        captured["errors"] = errors
        captured["fatal"] = fatal

    mw.scan_unity(str(tmp_path), on_progress=lambda _m, _p: None, on_done=on_done)
    assert captured["saved"] == []
    assert captured["errors"] == 0
    assert captured["fatal"] and "resource_cache" in captured["fatal"]


def test_scan_web_reports_fatal_when_vuplex_missing(tmp_path):
    captured = {}

    def on_done(saved, errors, fatal):
        captured["fatal"] = fatal

    mw.scan_web(str(tmp_path), on_progress=lambda _m, _p: None, on_done=on_done)
    assert captured["fatal"] and "Vuplex.WebView" in captured["fatal"]
