"""MapleWorld V2 頁面用的 widgets / 快取 / 分類 cache I/O

從 mapleworld_page_v2.py 抽出，讓主頁面檔只負責 layout / 掃描 / filter 邏輯。
本模組對外公開：
- _PreviewDialog / _AssetCard / _ThumbBox / _TabBtn / _CatChip
- _THUMB_CACHE（LRU QPixmap 快取，單例）
- _CAT_ORDER / _CAT_COLORS
- load_classify_cache() / save_classify_cache()
"""

import os
import json
import shutil
from collections import OrderedDict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QFileDialog, QDialog,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QPixmap

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_pixmap, lucide_icon
from src.infrastructure.helpers import atomic_write_json, user_data_path
from src.infrastructure import mapleworld_scanner


_MAPLEWORLD_DIR = user_data_path(os.path.join("images", "mapleworld"))
# cache 放在 exe 同層，與圖片目錄分開（避免備份 / 壓縮時被帶走）
CLASSIFY_CACHE_PATH = user_data_path("mapleworld_classify_cache.json")
_LEGACY_CACHE_PATH  = os.path.join(_MAPLEWORLD_DIR, "_classify_cache.json")


# ════════════════════════════════════════════════════════════
# 分類顏色 — 冷到暖漸進，代表尺寸由小到大
# ════════════════════════════════════════════════════════════

_CAT_ORDER = (
    "≤16", "17-32", "33-64", "65-128",
    "129-256", "257-512", "513-1024", ">1024",
)
_CAT_COLORS = {
    "≤16":       "#4dd2e8",   # cyan
    "17-32":     "#5ae0c4",   # teal
    "33-64":     "#56d99a",   # green
    "65-128":    "#b3e356",   # lime
    "129-256":   "#fbbf24",   # yellow
    "257-512":   "#ff9d5a",   # light orange
    "513-1024":  "#ff6b35",   # deep orange
    ">1024":     "#ef4444",   # red
}


# ════════════════════════════════════════════════════════════
# 縮圖快取（LRU）
# ════════════════════════════════════════════════════════════

_THUMB_CACHE_MAX = 800


class _LRUPixCache:
    """OrderedDict + move_to_end 實作，避免長時間瀏覽 14k+ 圖片 QPixmap 無限膨脹"""

    def __init__(self, maxsize: int):
        self._d: "OrderedDict[str, tuple[QPixmap, int, int]]" = OrderedDict()
        self._max = maxsize

    def get(self, key):
        v = self._d.get(key)
        if v is not None:
            self._d.move_to_end(key)
        return v

    def __setitem__(self, key, value):
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = value
        while len(self._d) > self._max:
            self._d.popitem(last=False)

    def clear(self):
        self._d.clear()


_THUMB_CACHE = _LRUPixCache(_THUMB_CACHE_MAX)


# ════════════════════════════════════════════════════════════
# 分類 cache I/O
# ════════════════════════════════════════════════════════════

# 分類 cache schema 版本。每次 CATEGORIES 改 label 或分桶規則變動就要 +1，
# 舊版 cache 直接作廢重新分類，避免髒資料殘留。
CLASSIFY_CACHE_VERSION = 2


def load_classify_cache() -> dict:
    """讀取分類 cache；舊位置（images/mapleworld/_classify_cache.json）自動遷移後刪除

    檔案格式：{"version": int, "tags": {fname: category, ...}}
    版本不符或 schema 不合法 → 回傳空 dict（等同全量重分類）。
    相容 v1 純 dict 格式：{fname: category}。
    """
    path = CLASSIFY_CACHE_PATH
    if not os.path.isfile(path) and os.path.isfile(_LEGACY_CACHE_PATH):
        path = _LEGACY_CACHE_PATH
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tags = _extract_tags(data)
        if tags is None:
            return {}
        if path == _LEGACY_CACHE_PATH:
            save_classify_cache(tags)
            try:
                os.remove(_LEGACY_CACHE_PATH)
            except OSError:
                pass
        return tags
    except Exception:
        return {}


def _extract_tags(data) -> "dict | None":
    """把磁碟 JSON 解析成 {fname: category}，格式不合時回 None"""
    if not isinstance(data, dict):
        return None
    valid = set(mapleworld_scanner.CATEGORIES)

    # v2+ 有 version 欄位
    if "version" in data:
        if data.get("version") != CLASSIFY_CACHE_VERSION:
            return None
        tags = data.get("tags")
        if not isinstance(tags, dict):
            return None
    else:
        # v1 純 dict 格式，僅當全部 value 皆為合法 category 才視為可用
        tags = data

    if any(v not in valid for v in tags.values()):
        return None
    return tags


def save_classify_cache(tags: dict):
    """原子寫入；worker thread / 主執行緒皆可呼叫"""
    try:
        os.makedirs(os.path.dirname(CLASSIFY_CACHE_PATH) or ".", exist_ok=True)
        atomic_write_json(
            CLASSIFY_CACHE_PATH,
            {"version": CLASSIFY_CACHE_VERSION, "tags": tags},
        )
    except Exception:
        pass


# ════════════════════════════════════════════════════════════
# 預覽 / 縮圖卡片
# ════════════════════════════════════════════════════════════

class _PreviewDialog(QDialog):
    """點卡片後彈出的原尺寸預覽對話框（超過螢幕會等比縮放）"""

    def __init__(self, parent, name: str, image_path: str):
        super().__init__(parent)
        self.setWindowTitle(name)
        self.setStyleSheet(f"background: {T.BG_WINDOW};")

        pm = QPixmap(image_path)
        screen = self.screen().availableGeometry() if self.screen() else None
        max_w = (screen.width() - 80) if screen else 1600
        max_h = (screen.height() - 120) if screen else 900
        if not pm.isNull() and (pm.width() > max_w or pm.height() > max_h):
            pm = pm.scaled(
                max_w, max_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        L = QVBoxLayout(self)
        L.setContentsMargins(T.S_MD, T.S_MD, T.S_MD, T.S_MD)
        L.setSpacing(T.S_XS)

        img_lbl = QLabel()
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if not pm.isNull():
            img_lbl.setPixmap(pm)
        img_lbl.setStyleSheet(f"background: {T.BG_SURFACE}; border-radius: {T.R_MD}px;")
        L.addWidget(img_lbl)

        info = QLabel(f"{name} · {pm.width()}×{pm.height()}"
                      if not pm.isNull() else name)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet(
            f"color: {T.TEXT_MUTED}; font-size: 11px; background: transparent;"
        )
        L.addWidget(info)


class _AssetCard(QFrame):
    CARD_W = 148
    CARD_H = 190
    THUMB_H = 108

    def __init__(self, name: str, image_path: "str | None", accent: str,
                 category: "str | None" = None, page=None):
        super().__init__()
        self._name       = name
        self._accent     = accent
        self._image_path = image_path
        self._category   = category
        self._page       = page
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pix: "QPixmap | None" = None
        self._w_px = self._h_px = 0
        if image_path:
            cached = _THUMB_CACHE.get(image_path)
            if cached is None:
                pm = QPixmap(image_path)
                if not pm.isNull():
                    scaled = pm.scaled(
                        self.CARD_W - T.S_SM * 2, self.THUMB_H - 4,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    cached = (scaled, pm.width(), pm.height())
                    _THUMB_CACHE[image_path] = cached
            if cached is not None:
                self._pix, self._w_px, self._h_px = cached
        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setObjectName("asset_card")
        self.setStyleSheet(
            f"QFrame#asset_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
            f"QFrame#asset_card:hover {{ border-color: {T.BORDER_HOVER}; }}"
        )
        self._build()

    def _build(self):
        L = QVBoxLayout(self)
        L.setContentsMargins(T.S_SM, T.S_SM, T.S_SM, T.S_SM)
        L.setSpacing(T.S_XS)

        thumb = _ThumbBox(self._pix, self._accent, self.THUMB_H)
        L.addWidget(thumb)

        name_lbl = QLabel(self._name)
        name_lbl.setStyleSheet(
            f"color: {T.TEXT_HI}; font-size: 11px; font-weight: 600;"
            f" background: transparent;"
        )
        L.addWidget(name_lbl)

        meta_text = (f"PNG  ·  {self._w_px}×{self._h_px}"
                     if self._w_px else "PNG")
        meta = QLabel(meta_text)
        meta.setStyleSheet(
            f"color: {T.TEXT_MUTED}; font-size: 9px; background: transparent;"
        )
        L.addWidget(meta)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(T.S_XS)
        if self._category:
            color = _CAT_COLORS.get(self._category, T.TEXT_MUTED)
            badge = QLabel(self._category)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedHeight(16)
            badge.setStyleSheet(
                f"color: {color}; background: {T.alpha(color, 28)};"
                f" border: 1px solid {T.alpha(color, 80)};"
                f" border-radius: 8px; font-size: 9px; font-weight: 700;"
                f" padding: 0 6px;"
            )
            row.addWidget(badge)
        row.addStretch()
        if self._image_path:
            save_btn = QPushButton()
            save_btn.setFixedSize(20, 18)
            save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            save_btn.setToolTip("另存新檔")
            save_btn.setIcon(lucide_icon("save", T.TEXT_DIM, 11, stroke=1.8))
            save_btn.setIconSize(QSize(11, 11))
            save_btn.setStyleSheet(
                f"QPushButton {{ background: {T.BG_INPUT};"
                f" border: 1px solid {T.BORDER}; border-radius: 6px; }}"
                f"QPushButton:hover {{ background: {T.BG_HOVER};"
                f" border-color: {self._accent}; }}"
            )
            save_btn.clicked.connect(self._on_save_as)
            row.addWidget(save_btn)
        L.addLayout(row)

    def _on_save_as(self):
        if not self._image_path or not os.path.isfile(self._image_path):
            return
        default_name = os.path.basename(self._image_path)
        dst, _ = QFileDialog.getSaveFileName(
            self, "另存新檔", default_name, "PNG Image (*.png);;所有檔案 (*.*)"
        )
        if not dst:
            return
        toast = getattr(getattr(self._page, "app", None), "toast", None)
        try:
            shutil.copy2(self._image_path, dst)
        except OSError as e:
            if toast is not None:
                toast.show(f"另存失敗：{e}", "error")
            return
        if toast is not None:
            toast.show(f"已另存：{os.path.basename(dst)}", "success")

    def mousePressEvent(self, e):  # noqa: N802
        # 預覽：整張卡片可點（save 按鈕會先吃掉自己的 click，不衝突）
        if (e.button() == Qt.MouseButton.LeftButton
                and self._image_path and os.path.isfile(self._image_path)):
            dlg = _PreviewDialog(self.window(), self._name, self._image_path)
            dlg.exec()
        super().mousePressEvent(e)


class _ThumbBox(QFrame):
    def __init__(self, pix: "QPixmap | None", accent: str, height: int):
        super().__init__()
        self._pix    = pix
        self._accent = accent
        self.setFixedHeight(height)
        self.setStyleSheet(
            f"QFrame {{ background: {T.alpha(accent, 28)};"
            f" border: 1px solid {T.BORDER_SOFT};"
            f" border-radius: {T.R_MD}px; }}"
        )

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        p = QPainter(self)
        if self._pix is not None:
            x = (self.width()  - self._pix.width())  // 2
            y = (self.height() - self._pix.height()) // 2
            p.drawPixmap(x, y, self._pix)
        else:
            pix = lucide_pixmap("image", self._accent, 36, stroke=1.4)
            x = (self.width()  - 36) // 2
            y = (self.height() - 36) // 2
            p.drawPixmap(x, y, pix)
        p.end()


# ════════════════════════════════════════════════════════════
# Tab 列 / 分類 chip
# ════════════════════════════════════════════════════════════

class _TabBtn(QPushButton):
    def __init__(self, label: str, icon: str, accent: str, active: bool, on_click=None):
        super().__init__()
        self._label  = label
        self._icon   = icon
        self._accent = accent
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        if on_click is not None:
            self.clicked.connect(on_click)
        self.toggled.connect(self._apply)
        self._apply()

    def _apply(self):
        if self.isChecked():
            color = self._accent
            bg    = T.alpha(self._accent, 32)
        else:
            color = T.TEXT_DIM
            bg    = "transparent"
        self.setIcon(lucide_icon(self._icon, color, 14, stroke=1.6))
        self.setIconSize(QSize(14, 14))
        self.setText(f"  {self._label}")
        self.setStyleSheet(
            f"QPushButton {{ color: {color}; background: {bg};"
            f" border: none; border-radius: {T.R_SM}px;"
            f" padding: 0 14px; font-size: 12px; font-weight: 600;"
            f" text-align: left; }}"
            f"QPushButton:hover {{ color: {T.TEXT_HI}; }}"
        )


class _CatChip(QPushButton):
    def __init__(self, label: str, color: str, active: bool, on_click):
        super().__init__()
        self._color = color
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(26)
        self.setText(label)
        self.clicked.connect(on_click)
        self.toggled.connect(self._apply)
        self._apply()

    def _apply(self):
        if self.isChecked():
            bg = T.alpha(self._color, 48)
            fg = self._color
            bd = T.alpha(self._color, 120)
        else:
            bg = "transparent"
            fg = T.TEXT_DIM
            bd = T.BORDER
        self.setStyleSheet(
            f"QPushButton {{ color: {fg}; background: {bg};"
            f" border: 1px solid {bd}; border-radius: 13px;"
            f" padding: 0 12px; font-size: 11px; font-weight: 600; }}"
            f"QPushButton:hover {{ color: {T.TEXT_HI}; }}"
        )
