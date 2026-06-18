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
import threading
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QScrollArea, QGridLayout, QFileDialog, QProgressBar,
)
from PySide6.QtCore import Qt, QSize, QTimer

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_pixmap, lucide_icon
from src.ui_v2.components import make_primary_button
from src.ui_v2.flow_layout import FlowLayout
from src.infrastructure.helpers import user_data_path
from src.infrastructure import mapleworld_scanner
from src.ui_v2.pages.mapleworld_widgets_v2 import (
    _AssetCard, _TabBtn, _CatChip,
    _THUMB_CACHE, _CAT_ORDER, _CAT_COLORS,
    load_classify_cache, save_classify_cache,
)


_MAPLEWORLD_DIR = user_data_path(os.path.join("images", "mapleworld"))
_DEFAULT_GAME_PATH = os.path.normpath(
    os.path.expandvars(r"%LOCALAPPDATA%\..\LocalLow\nexon\MapleStory Worlds")
)
_RENDER_STEP = 120       # 每次「載入更多」增加的卡片數（避免 14k+ 一次塞爆 UI）


# Tab 定義：(key, label, lucide-icon, accent)
TABS = [
    ("unity", "Unity 遊戲資源",  "gamepad-2", T.ORANGE),
    ("web",   "WebView 網頁快取", "globe",    T.CYAN),
]

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
        self._render_total = 0
        self._append_from: int | None = None
        self._more_btn: QPushButton | None = None
        self._cancel_evt: threading.Event | None = None
        # 全部檔名列表（一次列目錄，不重複 IO）
        self._files: dict[str, list[str]] = {"unity": [], "web": []}
        # fname → category；從磁碟 cache 預載，避免每次進頁重分類
        self._tags: dict[str, str] = load_classify_cache()
        # RWD：依 viewport 寬度動態算出的每行欄數，resize 後重排
        self._cols = 7
        # 自動加載閘門：避免 valueChanged 連續 emit 時重複觸發 load_more
        self._loading_more = False
        # resize debounce — 視窗縮放會 emit 多次,避免每次都重排 grid
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(80)
        self._resize_timer.timeout.connect(self._on_resize_done)
        self._build()

    def showEvent(self, e):  # noqa: N802
        super().showEvent(e)
        if not self._loaded:
            self._loaded = True
            # 第一次顯示時 viewport 已有實際寬度，先依此算 cols 避免初次以預設值排錯
            self._cols = self._compute_cols()
            self._scan_dir()
            self._render_grid()

    def resizeEvent(self, e):  # noqa: N802
        super().resizeEvent(e)
        if not self._loaded:
            return
        # debounce — 連續 resize 期間不立刻重排，等使用者放手 80ms 後再算
        self._resize_timer.start()

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

        # 掃描進度條：掃描時才顯示（indeterminate → 0-100），設 fixed 2px 保留空間
        self._progress_bar = QProgressBar()
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(2)
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setVisible(False)
        self._progress_bar.setStyleSheet(
            f"QProgressBar {{ background: {T.BG_INPUT};"
            f" border: none; border-radius: 1px; }}"
            f"QProgressBar::chunk {{ background: {T.ORANGE}; border-radius: 1px; }}"
        )
        root.addWidget(self._progress_bar)

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

        # 分類 chip 列 — FlowLayout 讓窄視窗能自動折行
        chip_row = FlowLayout(h_spacing=T.S_XS, v_spacing=T.S_XS)
        self._chips: dict[str, _CatChip] = {}
        chips_def = [("全部", T.ORANGE)] + [(c, _CAT_COLORS[c]) for c in _CAT_ORDER]
        for label, color in chips_def:
            chip = _CatChip(label, color,
                            active=(label == self._current_cat),
                            on_click=lambda _=False, k=label: self._switch_cat(k))
            self._chips[label] = chip
            chip_row.addWidget(chip)
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
        # 滾動到接近底部時自動加載下一批，取代純手動「載入更多」按鈕
        scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)
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

        scan_btn = make_primary_button("掃描資源", font_size=11, weight=700, height=30)
        self._scan_btn = scan_btn
        scan_btn.setIcon(lucide_icon("search", "#ffffff", 13, stroke=1.8))
        scan_btn.setIconSize(QSize(13, 13))
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
            save_classify_cache(self._tags)
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
                        save_classify_cache({**baseline, **batch})
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
        save_classify_cache(self._tags)
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

    def _compute_cols(self) -> int:
        """依 scroll viewport 寬度動態算每行欄數（RWD）"""
        if not getattr(self, "_scroll", None):
            return self._cols or 1
        w = self._scroll.viewport().width()
        if w <= 0:
            return self._cols or 1
        gap = self._grid.horizontalSpacing() or T.S_SM
        margin_right = self._grid.contentsMargins().right()
        avail = max(0, w - margin_right)
        cols = (avail + gap) // (_AssetCard.CARD_W + gap)
        return max(1, int(cols))

    def _on_resize_done(self):
        """resize debounce timer 觸發 — cols 變了才重排，避免無謂重畫"""
        new_cols = self._compute_cols()
        if new_cols == self._cols:
            return
        self._cols = new_cols
        # cols 變動 → 整頁重畫（append 模式 row/col 算法會錯位）
        self._render_grid()

    def _on_scroll(self, value: int):
        """捲到接近底部時自動 load_more —
        讓 200px 安全距離保證使用者捲到底前就已開始載下一批"""
        if self._loading_more:
            return
        if self._render_limit >= self._render_total:
            return
        sb = self._scroll.verticalScrollBar()
        if sb.maximum() <= 0:
            return
        if value < sb.maximum() - 200:
            return
        self._loading_more = True
        self._load_more()

    def _maybe_autoload(self):
        """渲染完一輪後，若 viewport 仍未填滿（沒有捲動軸）就主動再載一輪，
        否則使用者沒捲動觸發不到 valueChanged"""
        if self._loading_more:
            return
        if self._render_limit >= self._render_total:
            return
        sb = self._scroll.verticalScrollBar()
        if sb.maximum() == 0:
            self._loading_more = True
            self._load_more()

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
        self._progress_bar.setRange(0, 0)   # indeterminate 直到第一個 pct 進來
        self._progress_bar.setVisible(True)
        if hasattr(self.app, "toast"):
            self.app.toast.show("掃描中…", "info")

        evt = self._cancel_evt
        mapleworld_scanner.scan_unity(
            game_path,
            on_progress=lambda msg, pct: self.app.after(
                0, lambda m=msg, p=pct: self._on_scan_progress(m, p)),
            on_done=lambda saved, errors, fatal:
                self.app.after(0, lambda: self._on_scan_done(saved, errors, fatal)),
            should_cancel=evt.is_set,
        )

    def _on_scan_progress(self, msg: str, pct: int):
        """主執行緒：更新文字與進度條"""
        self._stat_lbl.setText(msg)
        if pct < 0:
            self._progress_bar.setRange(0, 0)       # indeterminate
        else:
            if self._progress_bar.maximum() == 0:
                self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(pct)

    def _on_scan_done(self, saved: list, errors: int, fatal: "str | None"):
        """掃描結束（主執行緒）— 重掃目錄後重繪 grid"""
        self._scanning = False
        self._cancel_evt = None
        self._scan_btn.setEnabled(True)
        self._scan_btn.setText("掃描資源")
        self._progress_bar.setVisible(False)

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
            # 整頁重畫 — 清空 grid + 解開自動加載閘門
            # （tab/搜尋/chip 切換時舊 chunk token 失效會早退，不會跑到 chunk 結尾解鎖）
            while self._grid.count():
                item = self._grid.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()
            self._more_btn = None
            self._loading_more = False
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
            self._grid.addWidget(empty, 0, 0, 1, max(1, self._cols))
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
        cols = max(1, self._cols)
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

        # 全部畫完 — 補「載入更多」按鈕（保留作 fallback；自動加載走 _on_scroll）
        self._stat_lbl.setText(self._stat_tmpl)
        total = self._render_total
        shown = self._render_shown
        if shown < total:
            more_btn = QPushButton(f"繼續向下捲動以自動載入 · 還有 {total - shown} 張")
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

        # 渲染完成後解除高度鎖定 + 解開自動加載閘門
        self._inner.setMinimumHeight(0)
        self._loading_more = False
        # 若 viewport 仍未塞滿（沒有捲動軸）→ 直接再載一輪，讓使用者一進頁就有足夠內容可捲
        QTimer.singleShot(0, self._maybe_autoload)
