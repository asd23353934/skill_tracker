"""
MapleStory Worlds 資源掃描器 — 純 infrastructure 層
將 .win.mod 與 Vuplex.WebView 快取解碼成 PNG 寫入 images/mapleworld/。

設計原則：
- 本模組不得 import PySide6 或任何 Qt 符號
- 對外公開 scan_unity / scan_web 兩個非同步 API，內部啟動 daemon thread
- on_progress / on_done callback 會在「worker thread」被呼叫
  UI 呼叫端必須自行以 app.after(0, ...) 之類機制排回主執行緒後才能動 UI

Public API：
- scan_unity(game_path, on_progress, on_done)
- scan_web(game_path, on_progress, on_done)
- extract_all_dds(raw_bytes)                 → Iterator[(index, PIL.Image)]
- extract_images_from_bytes(raw_bytes)       → list[PIL.Image]
- classify_image(path_or_image)              → str   # 圖示 / UI / 精靈 / 背景 / 長條 / 其他

saved tuple 格式（與 V1 相容）：
- Unity: (name, PIL.Image, save_path, dir_type)
- Web  : (name, PIL.Image, save_path, source_tag)  # source_tag ∈ {"web-cache","base64","cdn"}
"""

import os
import re
import gzip
import base64
import threading
from io import BytesIO
from typing import Callable, Iterator

from src.infrastructure.helpers import user_data_path


# 輸出目錄（exe 同層 images/mapleworld/）
_MAPLEWORLD_DIR = user_data_path(os.path.join("images", "mapleworld"))

# Callback 型別別名
ProgressCB = Callable[[str], None]
DoneCB     = Callable[[list, int, "str | None"], None]


# ════════════════════════════════════════════════════════════
# 解碼 helper — 模組級、無狀態
# ════════════════════════════════════════════════════════════

def extract_all_dds(raw: bytes) -> Iterator[tuple]:
    """從原始資料中提取所有 DDS 圖片

    部分 .win.mod 內含多個 DDS 資料塊，逐一掃描並解碼。
    利用 BytesIO.tell() 取得每次 PIL 實際讀取的位元組數，
    以此定位下一個 DDS 的起點。

    Args:
        raw: .win.mod 完整原始資料

    Yields:
        (index, PIL Image RGBA) — 同一檔案的第幾張圖、已翻轉 / RGBA 的影像
    """
    from PIL import Image as PILImage

    pos = 0
    idx = 0
    while True:
        found = raw.find(b"DDS ", pos)
        if found == -1:
            break
        try:
            buf = BytesIO(raw[found:])
            img = PILImage.open(buf)
            img.load()                      # 強制讀入像素，確保 tell() 正確
            consumed = buf.tell()
            img = img.convert("RGBA")
            img = img.transpose(PILImage.Transpose.FLIP_TOP_BOTTOM)
            yield idx, img
            idx += 1
            pos = found + max(consumed, 128)
        except Exception:
            pos = found + 4   # 跳過損壞的 DDS，繼續往後找


CATEGORIES = (
    "≤16", "17-32", "33-64", "65-128",
    "129-256", "257-512", "513-1024", ">1024",
)

# max(w, h) 閾值表 — 有序
_SIZE_TIERS = (
    (16,   "≤16"),
    (32,   "17-32"),
    (64,   "33-64"),
    (128,  "65-128"),
    (256,  "129-256"),
    (512,  "257-512"),
    (1024, "513-1024"),
)


def classify_image(source) -> str:
    """依 max(w, h) 將圖片分到 8 級尺寸桶。

    Args:
        source: 檔案路徑 (str) 或 PIL Image

    Returns:
        CATEGORIES 之一
    """
    from PIL import Image as PILImage

    owns = False
    if isinstance(source, str):
        try:
            img = PILImage.open(source)
            owns = True
        except Exception:
            return ">1024"
    else:
        img = source

    try:
        w, h = img.width, img.height
        if w <= 0 or h <= 0:
            return ">1024"
        max_d = max(w, h)
        for limit, label in _SIZE_TIERS:
            if max_d <= limit:
                return label
        return ">1024"
    finally:
        if owns:
            img.close()


def extract_images_from_bytes(data: bytes) -> list:
    """從 bytes 中掃描並提取所有 PNG / WebP / JPEG / GIF 圖片

    Args:
        data: 原始位元組資料

    Returns:
        PIL Image (RGBA) 清單；< 16×16 的影像會被過濾
    """
    from PIL import Image as PILImage

    results = []
    seen_offsets: set[int] = set()

    # (magic, extra_check, min_skip)
    signatures = [
        (b"\x89PNG\r\n\x1a\n", None,   8),
        (b"RIFF",              "WEBP", 12),
        (b"\xff\xd8\xff",      None,    3),
        (b"GIF87a",            None,    6),
        (b"GIF89a",            None,    6),
    ]

    for magic, extra, min_skip in signatures:
        pos = 0
        while True:
            found = data.find(magic, pos)
            if found == -1:
                break

            if extra == "WEBP":
                if data[found + 8: found + 12] != b"WEBP":
                    pos = found + 4
                    continue

            if found in seen_offsets:
                pos = found + min_skip
                continue
            seen_offsets.add(found)

            try:
                buf = BytesIO(data[found:])
                img = PILImage.open(buf)
                if img.width >= 16 and img.height >= 16:
                    img.load()
                    consumed = buf.tell()
                    results.append(img.convert("RGBA"))
                    pos = found + max(consumed, min_skip)
                    continue
            except Exception:
                pass
            pos = found + min_skip

    return results


# ════════════════════════════════════════════════════════════
# Unity 掃描 — resource_cache/**/*.win.mod
# ════════════════════════════════════════════════════════════

def scan_unity(game_path: str, on_progress: ProgressCB, on_done: DoneCB) -> None:
    """背景掃描 .win.mod → PNG

    立即返回；實際工作在 daemon thread 進行。
    on_progress(msg) / on_done(saved, errors, fatal) 都在 worker thread 被呼叫，
    呼叫端必須自行排回主執行緒才能更新 UI。
    """
    resource_cache = os.path.join(game_path, "resource_cache")
    if not os.path.isdir(resource_cache):
        on_done([], 0, f"找不到資源快取目錄：{resource_cache}")
        return

    os.makedirs(_MAPLEWORLD_DIR, exist_ok=True)

    threading.Thread(
        target=_unity_worker,
        args=(resource_cache, on_progress, on_done),
        daemon=True,
    ).start()


def _unity_worker(resource_cache: str, on_progress: ProgressCB, on_done: DoneCB) -> None:
    """背景掃描：resource_cache/ 下所有子目錄的 .win.mod → PNG

    掃描範圍：
      - resource_cache/msw/  → 內含 DDS 紋理（需翻轉）
      - resource_cache/ugc/  → 內含 PNG 直接嵌入
      - resource_cache/raw/  → 保留

    策略：先找 DDS，沒有 DDS 就用 extract_images_from_bytes 找 PNG/JPEG/etc。
    命名：{UUID}.png（單圖）/ {UUID}_{index}.png（多圖）
    """
    saved: list[tuple] = []
    errors: int = 0

    try:
        mod_files: list[tuple[str, str]] = []
        for root, _dirs, files in os.walk(resource_cache):
            for f in files:
                if f.endswith(".win.mod"):
                    rel = os.path.relpath(root, resource_cache)
                    parts = rel.split(os.sep) if rel != "." else []
                    if len(parts) >= 2:
                        dir_type = parts[0] + "/" + parts[1]
                    elif parts:
                        dir_type = parts[0]
                    else:
                        dir_type = "unknown"
                    mod_files.append((os.path.join(root, f), dir_type))

        total = len(mod_files)
        on_progress(f"找到 {total} 個 .win.mod，解碼中…")

        for fi, (mod_path, dir_type) in enumerate(mod_files):
            if fi % 500 == 0 and total:
                pct = fi * 100 // total
                on_progress(f"解碼中 {fi}/{total} ({pct}%)  已存 {len(saved)} 張…")

            try:
                with open(mod_path, "rb") as fh:
                    raw = fh.read()

                base_hash = os.path.basename(mod_path).replace(".win.mod", "")

                # ① 先嘗試 DDS（msw/ 的主要格式，需上下翻轉）
                dds_imgs = list(extract_all_dds(raw))
                if dds_imgs:
                    for img_idx, img in dds_imgs:
                        suffix = f"_{img_idx}" if len(dds_imgs) > 1 else ""
                        name = f"{base_hash}{suffix}"
                        save_path = os.path.join(_MAPLEWORLD_DIR, f"{name}.png")
                        img.save(save_path, "PNG")
                        saved.append((name, img, save_path, dir_type))
                    continue

                # ② 沒有 DDS → 找 PNG / JPEG / WebP / GIF（ugc/ 的格式，不翻轉）
                other_imgs = extract_images_from_bytes(raw)
                for img_idx, img in enumerate(other_imgs):
                    suffix = f"_{img_idx}" if len(other_imgs) > 1 else ""
                    name = f"{base_hash}{suffix}"
                    save_path = os.path.join(_MAPLEWORLD_DIR, f"{name}.png")
                    img.save(save_path, "PNG")
                    saved.append((name, img, save_path, dir_type))

            except Exception:
                errors += 1

    except Exception as e:
        on_done([], 0, str(e))
        return

    on_done(saved, errors, None)


# ════════════════════════════════════════════════════════════
# WebView 快取掃描 — Vuplex.WebView/
# ════════════════════════════════════════════════════════════

def scan_web(game_path: str, on_progress: ProgressCB, on_done: DoneCB) -> None:
    """背景掃描 Chromium WebView 快取 → PNG

    立即返回；實際工作在 daemon thread 進行。
    on_progress / on_done 均於 worker thread 被呼叫。
    """
    vuplex_dir = os.path.join(game_path, "Vuplex.WebView")
    if not os.path.isdir(vuplex_dir):
        on_done([], 0, f"找不到 Vuplex.WebView 目錄：{vuplex_dir}")
        return

    os.makedirs(_MAPLEWORLD_DIR, exist_ok=True)

    threading.Thread(
        target=_web_worker,
        args=(vuplex_dir, on_progress, on_done),
        daemon=True,
    ).start()


def _web_worker(vuplex_dir: str, on_progress: ProgressCB, on_done: DoneCB) -> None:
    """背景：多路徑多格式掃描

    Phase 0 — 自動發現：遞迴走訪 Vuplex.WebView/，收集所有快取相關檔案
              SimpleCache (f_*)、Blockfile (data_*)、IndexedDB/LocalStorage (*.ldb, *.log)
    Phase 1 — 直接提取：暴力掃描位元組，找 PNG / WebP / JPEG / GIF magic bytes
              同時嘗試 gzip 解壓後再掃描
    Phase 2 — URL 下載：從文字內容提取圖片 URL，從網路下載
    Phase 3 — Base64 解碼：從 data:image/... base64 字串解出內嵌圖片
    """
    from PIL import Image as PILImage
    import requests

    saved: list[tuple] = []
    errors = 0
    seen_names: set[str] = set()
    seen_urls:  set[str] = set()
    cdn_urls:   list[str] = []

    # ── Phase 0：自動發現所有快取相關檔案 ──
    scan_files: list[str] = []
    _SCAN_EXTS = (".ldb", ".log", ".sst")
    _SCAN_PFXS = ("f_", "data_")
    try:
        for root, _dirs, files in os.walk(vuplex_dir):
            for fname in files:
                if (any(fname.startswith(p) for p in _SCAN_PFXS)
                        or any(fname.endswith(e) for e in _SCAN_EXTS)):
                    scan_files.append(os.path.join(root, fname))
    except Exception as e:
        on_done([], 0, str(e))
        return

    total_files = len(scan_files)
    if total_files == 0:
        on_done(
            [], 0,
            f"在 {vuplex_dir} 下找不到任何快取檔案\n"
            f"請先啟動遊戲讓 WebView 建立快取。"
        )
        return

    on_progress(f"發現 {total_files} 個快取檔案，掃描中…")

    # ── Phase 1：暴力掃描全部位元組 ──
    for fi, fpath in enumerate(scan_files):
        if fi % 100 == 0:
            pct = fi * 100 // total_files
            on_progress(
                f"掃描中 {fi}/{total_files} ({pct}%)  已提取 {len(saved)} 張…"
            )

        fname_base = os.path.basename(fpath)
        try:
            with open(fpath, "rb") as fp:
                raw_data = fp.read()

            if len(raw_data) < 16:
                continue

            chunks: list[bytes] = [raw_data]
            gz_pos = 0
            while True:
                gz_pos = raw_data.find(b"\x1f\x8b", gz_pos)
                if gz_pos == -1:
                    break
                try:
                    dec = gzip.decompress(raw_data[gz_pos:])
                    if dec:
                        chunks.append(dec)
                except Exception:
                    pass
                gz_pos += 2

            for chunk_idx, chunk in enumerate(chunks):
                # Phase 1a：直接提取 PNG / WebP / JPEG / GIF
                imgs = extract_images_from_bytes(chunk)
                for img_idx, img in enumerate(imgs):
                    base_name = f"web_{fname_base}_{chunk_idx}_{img_idx}"
                    if base_name in seen_names:
                        continue
                    seen_names.add(base_name)
                    save_path = os.path.join(_MAPLEWORLD_DIR, f"{base_name}.png")
                    img.save(save_path, "PNG")
                    saved.append((base_name, img, save_path, "web-cache"))

                # Phase 1b：從文字內容提取圖片 URL
                try:
                    text = chunk.decode("utf-8", errors="ignore")
                    urls = re.findall(
                        r'https?://[^\s"\'<>\[\]{}\\]+?\.(?:png|webp|jpg|jpeg|gif)'
                        r'(?:[?#][^\s"\'<>\[\]{}\\]*)?',
                        text,
                    )
                    for url in urls:
                        url_clean = url.split("?")[0].split("#")[0]
                        if url_clean not in seen_urls and len(url_clean) < 512:
                            seen_urls.add(url_clean)
                            cdn_urls.append(url_clean)

                    # Phase 3：data:image/... Base64 內嵌圖片
                    for img_fmt, b64_data in re.findall(
                        r'data:image/(png|jpeg|gif|webp);base64,([A-Za-z0-9+/=]{100,})',
                        text,
                    ):
                        try:
                            img_bytes = base64.b64decode(b64_data + "==")
                            img = PILImage.open(BytesIO(img_bytes)).convert("RGBA")
                            if img.width < 16 or img.height < 16:
                                continue
                            h = abs(hash(b64_data[:80])) % 0xFFFFFF
                            base_name = f"web_b64_{fname_base}_{h}"
                            if base_name in seen_names:
                                continue
                            seen_names.add(base_name)
                            save_path = os.path.join(_MAPLEWORLD_DIR, f"{base_name}.png")
                            img.save(save_path, "PNG")
                            saved.append((base_name, img, save_path, "base64"))
                        except Exception:
                            pass
                except Exception:
                    pass

        except Exception:
            errors += 1

    p1_count = len(saved)
    on_progress(f"直接提取 {p1_count} 張｜準備下載 {len(cdn_urls)} 個 URL…")

    # ── Phase 2：從 URL 下載圖片 ──
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0.0.0 Safari/537.36",
    })

    for i, url in enumerate(cdn_urls):
        if i % 50 == 0:
            dl = len(saved) - p1_count
            on_progress(f"下載中：{i}/{len(cdn_urls)}  已存 {dl} 張…")

        try:
            url_fname = url.rsplit("/", 1)[-1]
            safe_fname = re.sub(r'[\\/:*?"<>|]', "_", url_fname)
            stem = os.path.splitext(f"cdn_{safe_fname}")[0]

            save_path = os.path.join(_MAPLEWORLD_DIR, f"{stem}.png")
            if os.path.exists(save_path):
                continue

            resp = session.get(url, timeout=12)
            if resp.status_code != 200 or not resp.content:
                continue

            img = PILImage.open(BytesIO(resp.content)).convert("RGBA")
            if img.width < 8 or img.height < 8:
                continue

            img.save(save_path, "PNG")
            saved.append((stem, img, save_path, "cdn"))

        except Exception:
            errors += 1

    on_done(saved, errors, None)
