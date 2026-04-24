"""
MapleWorld 資源中心 — V2
頂部：路徑列 + 掃描；中段：Tab（Unity / WebView）+ 過濾列；底部：縮圖瀑布
依 docs/DESIGN_V2.md

══════════════════════════════════════════════════════════════
綁定契約（限縮版）
══════════════════════════════════════════════════════════════
建構參數：
    MapleWorldPageV2(parent, app=None)

接線範圍（本次只接讀已快取部分）：
    - showEvent 第一次顯示 → 列出 _MAPLEWORLD_DIR 內現有 PNG
    - 依檔名前綴 web_/cdn_ 分到 WebView，其餘到 Unity tab
    - 縮圖以 QPixmap 同步載入（每 tab 限 _MAX_RENDER 張，避免慢）
    - 搜尋框即時 filter
    - Tab 切換 → 重渲對應分類

延後（標 TODO，沿用 v1 / 共用 helper 待議）：
    - [掃描資源]：v1 mapleworld_page._start_scan，含 .win.mod 解碼
    - [瀏覽] 寫回 settings
    - [縮圖點擊] 放大預覽 dialog
    - 類別 chip（角色/怪物/地圖…）

不在本頁職責：
    - 解碼 / 下載 / 檔案寫入
    - 圖片版權 / 法務聲明文字（已由 UI 顯示）
"""

import os
import json
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QScrollArea, QGridLayout, QFileDialog, QDialog,
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QPainter, QPixmap

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_pixmap, lucide_icon
from src.infrastructure.helpers import user_data_path
from src.infrastructure import mapleworld_scanner


_MAPLEWORLD_DIR = user_data_path(os.path.join("images", "mapleworld"))
# cache 放在 exe 同層，與圖片目錄分開（避免備份 / 壓縮時被帶走）
_CLASSIFY_CACHE = user_data_path("mapleworld_classify_cache.json")
_LEGACY_CACHE   = os.path.join(_MAPLEWORLD_DIR, "_classify_cache.json")
_DEFAULT_GAME_PATH = os.path.normpath(
    os.path.expandvars(r"%LOCALAPPDATA%\..\LocalLow\nexon\MapleStory Worlds")
)
_RENDER_STEP = 120       # 每次「載入更多」增加的卡片數（避免 14k+ 一次塞爆 UI）

# 縮圖快取：避免搜尋/換 tab 時對相同檔重複從硬碟解碼
# key=image_path, value=(scaled QPixmap, orig_w, orig_h)
_THUMB_CACHE: dict[str, tuple[QPixmap, int, int]] = {}


# Tab 定義：(key, label, lucide-icon, accent)
TABS = [
    ("unity", "Unity 遊戲資源",  "gamepad-2", T.ORANGE),
    ("web",   "WebView 網頁快取", "globe",    T.CYAN),
]

# 分類 chip 顯示色 — 冷到暖漸進，代表尺寸由小到大
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


def _load_classify_cache() -> dict:
    # 優先讀新位置；舊位置（images/mapleworld/_classify_cache.json）自動遷移後刪除
    path = _CLASSIFY_CACHE
    if not os.path.isfile(path) and os.path.isfile(_LEGACY_CACHE):
        path = _LEGACY_CACHE
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            valid = set(mapleworld_scanner.CATEGORIES)
            if any(v not in valid for v in data.values()):
                return {}
            if path == _LEGACY_CACHE:
                _save_classify_cache(data)
                try:
                    os.remove(_LEGACY_CACHE)
                except OSError:
                    pass
            return data
    except Exception:
        return {}


def _save_classify_cache(tags: dict):
    """原子寫入；worker thread / 主執行緒皆可呼叫"""
    try:
        os.makedirs(os.path.dirname(_CLASSIFY_CACHE) or ".", exist_ok=True)
        tmp = _CLASSIFY_CACHE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(tags, f, ensure_ascii=False)
        os.replace(tmp, _CLASSIFY_CACHE)
    except Exception:
        pass


# ════════════════════════════════════════════════════════════
# AssetCard
# ════════════════════════════════════════════════════════════

class _PreviewDialog(QDialog):
    """點卡片後彈出的原尺寸預覽對話框（超過螢幕會等比縮放）"""

    def __init__(self, parent, name: str, image_path: str):
        super().__init__(parent)
        self.setWindowTitle(name)
        self.setStyleSheet(f"background: {T.BG_BASE};")

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

    def __init__(self, name: str, image_path: str | None, accent: str,
                 category: str | None = None, page=None):
        super().__init__()
        self._name       = name
        self._accent     = accent
        self._image_path = image_path
        self._category   = category
        self._page       = page
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pix: QPixmap | None = None
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
    def __init__(self, pix: QPixmap | None, accent: str, height: int):
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
# Tab 列
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


# ════════════════════════════════════════════════════════════
# 分類 chip
# ════════════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════════════
# MapleWorldPageV2
# ════════════════════════════════════════════════════════════

class MapleWorldPageV2(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self._current_tab = "unity"
        self._current_cat = "全部"
        self._search_text = ""
        self._loaded = False
        self._scanning = False
        self._classify_token = 0
        self._render_token = 0
        self._render_limit = _RENDER_STEP
        self._append_from: int | None = None
        self._more_btn: QPushButton | None = None
        self._cancel_evt: threading.Event | None = None
        # 全部檔名列表（一次列目錄，不重複 IO）
        self._files: dict[str, list[str]] = {"unity": [], "web": []}
        # fname → category；從磁碟 cache 預載，避免每次進頁重分類
        self._tags: dict[str, str] = _load_classify_cache()
        self._build()

    def showEvent(self, e):  # noqa: N802
        super().showEvent(e)
        if not self._loaded:
            self._loaded = True
            self._scan_dir()
            self._render_grid()

    # ──────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        # 標題
        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(T.make_label("資源中心", T.FONT_SECTION))
        head.addSpacing(T.S_SM)
        head.addWidget(T.make_label(
            "讀取本機 MapleStory Worlds 快取 · 圖片版權屬 Nexon · 僅供個人使用",
            T.FONT_CAPTION,
        ))
        head.addStretch()
        root.addLayout(head)

        # 路徑列
        root.addWidget(self._build_path_card())

        # Tab 列 + 統計
        tab_row = QHBoxLayout()
        tab_row.setSpacing(T.S_XS)
        self._tab_btns: dict[str, _TabBtn] = {}
        for key, label, icon, accent in TABS:
            btn = _TabBtn(label, icon, accent,
                          active=(key == self._current_tab),
                          on_click=lambda _=False, k=key: self._switch_tab(k))
            self._tab_btns[key] = btn
            tab_row.addWidget(btn)
        tab_row.addStretch()

        self._stat_lbl = QLabel("尚未載入")
        self._stat_lbl.setStyleSheet(
            f"color: {T.TEXT_MUTED}; font-size: 11px; background: transparent;"
        )
        tab_row.addWidget(self._stat_lbl)
        root.addLayout(tab_row)

        # 搜尋列
        filt_row = QHBoxLayout()
        filt_row.setSpacing(T.S_XS)
        search = QLineEdit()
        search.setPlaceholderText("搜尋資源名稱…")
        search.setFixedHeight(28)
        search.setFixedWidth(260)
        search.setStyleSheet(
            f"QLineEdit {{ color: {T.TEXT}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 10px; font-size: 11px; }}"
            f"QLineEdit:focus {{ border-color: {T.ORANGE}; }}"
        )
        search.textChanged.connect(self._on_search)
        filt_row.addWidget(search)
        filt_row.addStretch()
        root.addLayout(filt_row)

        # 分類 chip 列
        chip_row = QHBoxLayout()
        chip_row.setSpacing(T.S_XS)
        self._chips: dict[str, _CatChip] = {}
        chips_def = [("全部", T.ORANGE)] + [(c, _CAT_COLORS[c]) for c in _CAT_ORDER]
        for label, color in chips_def:
            chip = _CatChip(label, color,
                            active=(label == self._current_cat),
                            on_click=lambda _=False, k=label: self._switch_cat(k))
            self._chips[label] = chip
            chip_row.addWidget(chip)
        chip_row.addStretch()
        root.addLayout(chip_row)

        # 縮圖 grid
        scroll = QScrollArea()
        self._scroll = scroll
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        self._grid = QGridLayout(self._inner)
        self._grid.setContentsMargins(0, 0, T.S_XS, 0)
        self._grid.setHorizontalSpacing(T.S_SM)
        self._grid.setVerticalSpacing(T.S_SM)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self._inner)
        root.addWidget(scroll, 1)

    def _build_path_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("path_card")
        card.setStyleSheet(
            f"QFrame#path_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
        )
        card.setFixedHeight(56)
        ph = QHBoxLayout(card)
        ph.setContentsMargins(T.S_LG, T.S_SM, T.S_SM, T.S_SM)
        ph.setSpacing(T.S_SM)

        folder_lbl = QLabel()
        folder_lbl.setFixedSize(18, 18)
        folder_lbl.setPixmap(lucide_pixmap("folder-open", T.YELLOW, 18, stroke=1.6))
        folder_lbl.setStyleSheet("background: transparent;")
        ph.addWidget(folder_lbl)

        ph.addWidget(T.make_label("遊戲路徑", T.FONT_BODY,
                                  color_override=T.TEXT_DIM))

        self._path_input = QLineEdit(_DEFAULT_GAME_PATH)
        self._path_input.setFixedHeight(30)
        self._path_input.setStyleSheet(
            f"QLineEdit {{ color: {T.TEXT}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 10px; font-size: 11px;"
            f" font-family: 'Consolas', monospace; }}"
            f"QLineEdit:focus {{ border-color: {T.ORANGE}; }}"
        )
        ph.addWidget(self._path_input, 1)

        browse_btn = QPushButton("瀏覽")
        browse_btn.setFixedHeight(30)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setIcon(lucide_icon("folder-open", T.TEXT, 13, stroke=1.6))
        browse_btn.setIconSize(QSize(13, 13))
        browse_btn.setStyleSheet(
            f"QPushButton {{ color: {T.TEXT}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 12px; font-size: 11px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {T.BG_HOVER};"
            f" border-color: {T.BORDER_HOVER}; }}"
        )
        browse_btn.clicked.connect(self._browse)
        ph.addWidget(browse_btn)

        scan_btn = QPushButton("掃描資源")
        self._scan_btn = scan_btn
        scan_btn.setFixedHeight(30)
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.setIcon(lucide_icon("search", "#ffffff", 13, stroke=1.8))
        scan_btn.setIconSize(QSize(13, 13))
        scan_btn.setStyleSheet(
            f"QPushButton {{ color: #ffffff; background: {T.ORANGE};"
            f" border: none; border-radius: {T.R_SM}px;"
            f" padding: 0 14px; font-size: 11px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: #ff9d5a; }}"
        )
        scan_btn.clicked.connect(self._on_scan)
        ph.addWidget(scan_btn)

        return card

    # ──────────────────────────────────────────
    # 操作
    # ──────────────────────────────────────────
    def _scan_dir(self):
        if not os.path.isdir(_MAPLEWORLD_DIR):
            return
        try:
            files = sorted(
                f for f in os.listdir(_MAPLEWORLD_DIR)
                if f.lower().endswith(".png")
            )
        except OSError:
            return
        for f in files:
            if f.startswith("web_") or f.startswith("cdn_"):
                self._files["web"].append(f)
            else:
                self._files["unity"].append(f)
        self._kickoff_classify()

    def _kickoff_classify(self):
        """背景分類尚未入 cache 的 PNG — ThreadPool 併發，過程僅更新統計文字"""
        if self.app is None:
            return
        self._classify_token += 1
        token = self._classify_token
        all_files: set[str] = set()
        for bucket in self._files.values():
            all_files.update(bucket)

        # 清掉 cache 中已不存在的檔案（避免 cache 無限膨脹）
        stale = [k for k in self._tags if k not in all_files]
        for k in stale:
            del self._tags[k]

        todo = [f for f in all_files if f not in self._tags]
        if not todo and not stale:
            return
        if not todo:
            _save_classify_cache(self._tags)
            return

        def classify_one(fname: str) -> tuple[str, str]:
            path = os.path.join(_MAPLEWORLD_DIR, fname)
            try:
                return fname, mapleworld_scanner.classify_image(path)
            except Exception:
                return fname, ">1024"

        # 基準快照：worker flush 到磁碟時會合併這份 + 當前 batch
        baseline = dict(self._tags)

        def dispatcher():
            # 4 條 worker 並行讀 PNG header（PIL.open 讀 header 會釋放 GIL）
            batch: dict[str, str] = {}
            done = 0
            total = len(todo)
            with ThreadPoolExecutor(max_workers=4) as pool:
                for fname, cat in pool.map(classify_one, todo, chunksize=32):
                    if token != self._classify_token:
                        return
                    batch[fname] = cat
                    done += 1
                    if done % 500 == 0:
                        self.app.after(0, lambda d=done, t=total, tok=token:
                                       self._update_classify_stat(d, t, tok))
                    # 每 1000 張 flush 一次磁碟；中途關閉程式仍保留已分類進度
                    if done % 1000 == 0:
                        _save_classify_cache({**baseline, **batch})
            self.app.after(0, lambda b=batch, tok=token:
                           self._classify_done(b, tok))

        threading.Thread(target=dispatcher, daemon=True).start()

    def _update_classify_stat(self, done: int, total: int, token: int):
        if token != self._classify_token:
            return
        self._stat_lbl.setText(f"分類中 {done}/{total} …")

    def _classify_done(self, batch: dict, token: int):
        if token != self._classify_token:
            return
        self._tags.update(batch)
        _save_classify_cache(self._tags)
        self._render_grid()

    def _switch_tab(self, key: str):
        if key == self._current_tab:
            self._tab_btns[key].setChecked(True)
            return
        self._current_tab = key
        for k, btn in self._tab_btns.items():
            btn.setChecked(k == key)
        self._render_limit = _RENDER_STEP
        self._scroll.verticalScrollBar().setValue(0)
        self._render_grid()

    def _on_search(self, text: str):
        self._search_text = text.strip().lower()
        self._render_limit = _RENDER_STEP
        self._render_grid()

    def _switch_cat(self, key: str):
        if key == self._current_cat:
            self._chips[key].setChecked(True)
            return
        self._current_cat = key
        for k, chip in self._chips.items():
            chip.setChecked(k == key)
        self._render_limit = _RENDER_STEP
        self._scroll.verticalScrollBar().setValue(0)
        self._render_grid()

    def _load_more(self):
        # 不清空 grid，直接從上次結尾 append 新卡，避免捲動軸閃動
        self._append_from = self._render_limit
        self._render_limit += _RENDER_STEP
        self._render_grid()

    def _on_scan(self):
        """Unity 資源掃描 — 委派給 infrastructure.mapleworld_scanner

        路徑驗證 → 鎖按鈕 + toast 提示 → 背景掃描 → callback 走 app.after 回主執行緒
        掃描中按鈕切換為「取消」，再按一次會設 cancel_evt 讓 worker 中止。
        """
        if self.app is None:
            return
        if self._scanning:
            if self._cancel_evt is not None:
                self._cancel_evt.set()
                self._scan_btn.setEnabled(False)
                self._stat_lbl.setText("取消中…")
            return

        game_path = self._path_input.text().strip()
        resource_cache = os.path.join(game_path, "resource_cache")
        if not os.path.isdir(resource_cache):
            if hasattr(self.app, "toast"):
                self.app.toast.show("找不到資源快取目錄，請確認遊戲路徑是否正確。", "error")
            return

        self._scanning = True
        self._cancel_evt = threading.Event()
        self._scan_btn.setText("取消")
        self._stat_lbl.setText("掃描中，自動解碼並儲存至 images/mapleworld/ …")
        if hasattr(self.app, "toast"):
            self.app.toast.show("掃描中…", "info")

        evt = self._cancel_evt
        mapleworld_scanner.scan_unity(
            game_path,
            on_progress=lambda msg: self.app.after(0, lambda m=msg: self._stat_lbl.setText(m)),
            on_done=lambda saved, errors, fatal:
                self.app.after(0, lambda: self._on_scan_done(saved, errors, fatal)),
            should_cancel=evt.is_set,
        )

    def _on_scan_done(self, saved: list, errors: int, fatal: "str | None"):
        """掃描結束（主執行緒）— 重掃目錄後重繪 grid"""
        self._scanning = False
        self._cancel_evt = None
        self._scan_btn.setEnabled(True)
        self._scan_btn.setText("掃描資源")

        if fatal == "已取消":
            if hasattr(self.app, "toast"):
                self.app.toast.show(f"已取消，已儲存 {len(saved)} 張", "info")
            self._stat_lbl.setText(f"已取消（已儲存 {len(saved)} 張）")
            # 取消後仍重掃，讓已儲存的檔案顯示出來
            self._files = {"unity": [], "web": []}
            self._scan_dir()
            self._loaded = True
            _THUMB_CACHE.clear()
            self._render_limit = _RENDER_STEP
            self._render_grid()
            return

        if fatal:
            if hasattr(self.app, "toast"):
                self.app.toast.show(f"掃描失敗：{fatal}", "error")
            self._stat_lbl.setText("掃描失敗")
            return

        # 清掉上次快照並重掃 images/mapleworld/
        self._files = {"unity": [], "web": []}
        # 保留 _tags cache，_kickoff_classify 只會分類新檔
        self._scan_dir()
        self._loaded = True
        _THUMB_CACHE.clear()
        self._render_limit = _RENDER_STEP
        self._render_grid()

        err_hint = f"（{errors} 個解析失敗）" if errors else ""
        msg = f"Unity 掃描完成：新增 {len(saved)} 張{err_hint}"
        if hasattr(self.app, "toast"):
            self.app.toast.show(msg, "success")

    def _browse(self):
        path = QFileDialog.getExistingDirectory(
            self, "選擇遊戲資料夾", self._path_input.text()
        )
        if path:
            self._path_input.setText(os.path.normpath(path))

    # ──────────────────────────────────────────
    # 渲染
    # ──────────────────────────────────────────
    def _render_grid(self):
        append_from = self._append_from
        self._append_from = None

        files = self._files.get(self._current_tab, [])
        if self._search_text:
            files = [f for f in files if self._search_text in f.lower()]
        if self._current_cat != "全部":
            matches = [f for f in files if self._tags.get(f) == self._current_cat]
        else:
            matches = files

        total = len(matches)
        shown = min(total, self._render_limit)

        if append_from is None:
            # 整頁重畫 — 清空 grid
            while self._grid.count():
                item = self._grid.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()
            self._more_btn = None
            start = 0
        else:
            # append 模式 — 先鎖住 inner 高度（避免移除 more_btn 造成 scroll 跳動），
            # 再移除舊「載入更多」按鈕，保留既有卡片
            self._inner.setMinimumHeight(self._inner.height())
            if self._more_btn is not None:
                self._grid.removeWidget(self._more_btn)
                self._more_btn.deleteLater()
                self._more_btn = None
            start = min(append_from, shown)

        self._stat_tmpl = self._build_stat_text(total, shown)
        self._stat_lbl.setText(self._stat_tmpl)

        if shown == 0:
            empty = QLabel("沒有符合的資源" if self._search_text else
                           "此 tab 尚無已快取的圖片")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color: {T.TEXT_MUTED}; font-size: 13px;"
                f" background: transparent; padding: 40px;"
            )
            self._grid.addWidget(empty, 0, 0, 1, 7)
            return

        # 拆批渲染：每 CHUNK 張讓一次主執行緒，避免整批 QPixmap 阻塞 UI
        self._render_token += 1
        token = self._render_token
        self._render_queue = matches[:shown]
        self._render_total = total
        self._render_shown = shown
        self._render_idx = start
        QTimer.singleShot(0, lambda: self._render_chunk(token))

    def _build_stat_text(self, total: int, shown: int) -> str:
        full_total = sum(len(v) for v in self._files.values())
        classified = len(self._tags)
        pending = max(0, full_total - classified)
        cat_hint = "" if self._current_cat == "全部" else f" · 分類 {self._current_cat}"
        progress_hint = f" · 分類中 {classified}/{full_total}" if pending else ""
        if not self._loaded or full_total == 0:
            return "尚未載入快取（執行 V1 掃描以填入 images/mapleworld/）"
        if self._search_text:
            return f"搜尋結果 {total}（顯示 {shown}） · 全庫 {full_total}{cat_hint}{progress_hint}"
        return f"本 tab {total}（顯示 {shown}） · 全庫 {full_total}{cat_hint}{progress_hint}"

    def _render_chunk(self, token: int):
        if token != self._render_token:
            return
        CHUNK = 24
        cols = 7
        accent = next((a for k, _, _, a in TABS if k == self._current_tab),
                      T.PURPLE)
        end = min(self._render_idx + CHUNK, len(self._render_queue))
        for i in range(self._render_idx, end):
            fname = self._render_queue[i]
            r, c = divmod(i, cols)
            name = os.path.splitext(fname)[0]
            path = os.path.join(_MAPLEWORLD_DIR, fname)
            cat = self._tags.get(fname)
            self._grid.addWidget(_AssetCard(name, path, accent, cat, self), r, c)
        self._render_idx = end

        if end < len(self._render_queue):
            self._stat_lbl.setText(
                f"載入中 {end}/{len(self._render_queue)} … · {self._stat_tmpl}"
            )
            QTimer.singleShot(0, lambda: self._render_chunk(token))
            return

        # 全部畫完 — 補「載入更多」按鈕
        self._stat_lbl.setText(self._stat_tmpl)
        total = self._render_total
        shown = self._render_shown
        if shown < total:
            more_btn = QPushButton(f"載入更多（{total - shown} 張剩餘）")
            more_btn.setFixedHeight(34)
            more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            more_btn.setStyleSheet(
                f"QPushButton {{ color: {T.TEXT}; background: {T.BG_INPUT};"
                f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
                f" padding: 0 18px; font-size: 12px; font-weight: 600; }}"
                f"QPushButton:hover {{ background: {T.BG_HOVER};"
                f" border-color: {T.BORDER_HOVER}; }}"
            )
            more_btn.clicked.connect(self._load_more)
            next_row = (shown + cols - 1) // cols
            self._grid.addWidget(more_btn, next_row, 0, 1, cols,
                                 Qt.AlignmentFlag.AlignCenter)
            self._more_btn = more_btn

        # 渲染完成後解除高度鎖定
        self._inner.setMinimumHeight(0)
