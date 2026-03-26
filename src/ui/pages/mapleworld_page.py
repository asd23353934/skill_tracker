"""
MapleStory Worlds 本機資源瀏覽頁面
讀取本機已安裝遊戲快取（自訂 .win.mod 格式），瀏覽與提取圖片資產。
掃描後自動解碼並儲存至 images/mapleworld/，下次開啟直接顯示快取圖片。
"""

import os
import re
import shutil
import threading
from io import BytesIO

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem,
    QFrame, QFileDialog, QMessageBox, QCheckBox, QProgressBar,
    QStyledItemDelegate, QStyle, QStackedWidget, QButtonGroup,
)
from PySide6.QtCore import Qt, QSize, QRect, QEvent, Signal as _Signal
from PySide6.QtGui import QImage, QIcon, QPixmap, QPainter, QColor

from src.ui.theme import AppTheme
from src.ui.helpers import user_path

# 遊戲快取預設路徑
_DEFAULT_GAME_PATH = os.path.normpath(
    os.path.expandvars(r"%LOCALAPPDATA%\..\LocalLow\nexon\MapleStory Worlds")
)

# 程式內部儲存資料夾（exe 同層 images/mapleworld/）
_MAPLEWORLD_DIR = user_path(os.path.join("images", "mapleworld"))

# 縮圖尺寸（px）
_THUMB = 110


def _pil_to_icon(img) -> QIcon:
    """PIL Image → QIcon（含等比縮放）"""
    thumb = img.copy()
    thumb.thumbnail((_THUMB, _THUMB))
    w, h = thumb.size
    raw = thumb.tobytes("raw", "RGBA")
    qimg = QImage(raw, w, h, QImage.Format.Format_RGBA8888)
    return QIcon(QPixmap.fromImage(qimg))


class _PreviewDialog(QWidget):
    """圖片放大預覽視窗（支援滾輪縮放、拖曳平移）"""

    _ZOOM_STEP = 0.15
    _ZOOM_MIN  = 0.1
    _ZOOM_MAX  = 8.0

    def __init__(self, pil_img, name: str, parent=None):
        super().__init__(parent, Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle(f"預覽 — {name}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(700, 600)

        # PIL → QPixmap（原始尺寸）
        w, h = pil_img.size
        raw = pil_img.tobytes("raw", "RGBA")
        qimg = QImage(raw, w, h, QImage.Format.Format_RGBA8888)
        self._pixmap = QPixmap.fromImage(qimg)
        self._zoom   = 1.0
        self._offset = None   # QPoint 拖曳偏移
        self._drag_start = None

        # 資訊列
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        info = QLabel(f"  {name}  |  {w} × {h} px  |  滾輪縮放  |  拖曳平移")
        info.setFixedHeight(26)
        info.setStyleSheet(
            f"background:{AppTheme.BG_SECONDARY}; color:{AppTheme.TEXT_MUTED};"
            f" font-size:10px; border-bottom:1px solid {AppTheme.GOLD_MUTED};"
        )
        root.addWidget(info)

        # 畫布
        self._canvas = _PreviewCanvas(self._pixmap, self)
        root.addWidget(self._canvas, 1)

        # 底部工具列
        bar = QFrame()
        bar.setFixedHeight(32)
        bar.setStyleSheet(
            f"QFrame {{ background:{AppTheme.BG_SECONDARY};"
            f" border-top:1px solid {AppTheme.GOLD_MUTED}; }}"
        )
        b_lay = QHBoxLayout(bar)
        b_lay.setContentsMargins(8, 2, 8, 2)
        b_lay.setSpacing(6)
        for label, delta in [("－", -self._ZOOM_STEP), ("＋", self._ZOOM_STEP)]:
            btn = QPushButton(label)
            btn.setFixedSize(28, 24)
            btn.setStyleSheet(
                f"QPushButton {{ background:{AppTheme.BG_TERTIARY}; color:{AppTheme.TEXT_PRIMARY};"
                f" border:1px solid {AppTheme.GOLD_MUTED}; border-radius:3px; font-size:13px; }}"
                f"QPushButton:hover {{ background:{AppTheme.BG_CARD}; }}"
            )
            btn.clicked.connect(lambda _, d=delta: self._canvas.zoom_by(d))
            b_lay.addWidget(btn)
        reset_btn = QPushButton("重設")
        reset_btn.setFixedHeight(24)
        reset_btn.setStyleSheet(
            f"QPushButton {{ background:{AppTheme.BG_TERTIARY}; color:{AppTheme.TEXT_PRIMARY};"
            f" border:1px solid {AppTheme.GOLD_MUTED}; border-radius:3px;"
            f" padding:0 8px; font-size:10px; }}"
            f"QPushButton:hover {{ background:{AppTheme.BG_CARD}; }}"
        )
        reset_btn.clicked.connect(self._canvas.reset_view)
        b_lay.addWidget(reset_btn)
        b_lay.addStretch()
        self._zoom_lbl = QLabel("100%")
        self._zoom_lbl.setStyleSheet(
            f"color:{AppTheme.TEXT_MUTED}; font-size:10px; background:transparent;"
        )
        self._canvas.zoom_changed.connect(self._on_zoom_changed)
        b_lay.addWidget(self._zoom_lbl)
        root.addWidget(bar)

        self.setStyleSheet(f"QWidget {{ background:{AppTheme.BG_PRIMARY}; }}")

    def _on_zoom_changed(self, z: float):
        self._zoom_lbl.setText(f"{z * 100:.0f}%")


class _PreviewCanvas(QWidget):
    """可縮放平移的畫布"""

    zoom_changed = _Signal(float)

    _ZOOM_STEP = 0.15
    _ZOOM_MIN  = 0.05
    _ZOOM_MAX  = 10.0

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._pixmap     = pixmap
        self._zoom       = 1.0
        self._offset     = None    # QPoint
        self._drag_start = None
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setStyleSheet(f"background:{AppTheme.BG_DEEP};")

    def reset_view(self):
        self._zoom   = 1.0
        self._offset = None
        self.update()
        self.zoom_changed.emit(self._zoom)

    def zoom_by(self, delta: float):
        self._zoom = max(self._ZOOM_MIN, min(self._ZOOM_MAX, self._zoom + delta))
        self.update()
        self.zoom_changed.emit(self._zoom)

    def paintEvent(self, event):  # noqa: N802
        from PySide6.QtGui import QPainter as _P
        p = _P(self)
        p.setRenderHint(_P.RenderHint.SmoothPixmapTransform)
        pw = int(self._pixmap.width()  * self._zoom)
        ph = int(self._pixmap.height() * self._zoom)
        if self._offset is None:
            x = (self.width()  - pw) // 2
            y = (self.height() - ph) // 2
        else:
            x, y = self._offset.x(), self._offset.y()
        p.drawPixmap(x, y, pw, ph, self._pixmap)

    def wheelEvent(self, event):  # noqa: N802
        delta = self._ZOOM_STEP if event.angleDelta().y() > 0 else -self._ZOOM_STEP
        self.zoom_by(delta)

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.pos()
            pw = int(self._pixmap.width()  * self._zoom)
            ph = int(self._pixmap.height() * self._zoom)
            if self._offset is None:
                from PySide6.QtCore import QPoint
                self._offset = QPoint(
                    (self.width() - pw) // 2,
                    (self.height() - ph) // 2,
                )
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):  # noqa: N802
        if self._drag_start is not None and self._offset is not None:
            diff = event.pos() - self._drag_start
            self._offset = self._offset + diff
            self._drag_start = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):  # noqa: N802
        self._drag_start = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)


class _FluidGrid(QListWidget):
    """IconMode QListWidget：自動均分可用寬度，格子貼滿不留空白"""

    _CELL_H = _THUMB + 52   # 格子固定高度
    _CELL_W = _THUMB + 16   # 格子固定寬度（置中計算基準）

    def __init__(self, parent=None):
        super().__init__(parent)
        self._in_relayout = False
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 捲軸出現/消失時重算，防止 viewport 寬度不一致
        self.verticalScrollBar().rangeChanged.connect(lambda *_: self._relayout())

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._relayout()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._relayout()

    def _relayout(self):
        if self._in_relayout or self.width() <= 0:
            return
        self._in_relayout = True
        try:
            vsb = self.verticalScrollBar()
            sb_w = vsb.width() if vsb.isVisible() else 0
            # avail = 去掉捲軸後的可用寬度（含左右 viewport margin）
            avail = self.width() - sb_w
            if avail <= 0:
                return
            cols = max(1, avail // self._CELL_W)
            used = cols * self._CELL_W
            pad  = max(0, (avail - used) // 2)
            # 兩側等距 margin → 格子置中
            self.setViewportMargins(pad, 0, pad, 0)
            self.setGridSize(QSize(self._CELL_W, self._CELL_H))
        finally:
            self._in_relayout = False


class _ThumbDelegate(QStyledItemDelegate):
    """縮圖格子自訂繪製：圖示置底，文字固定在底部單行顯示，點擊切換勾選"""

    _PAD  = 6    # 外框內距
    _CB   = 13   # checkbox 邊長
    _TH   = 22   # 文字區高度

    def paint(self, painter: QPainter, option, index):  # noqa: N802
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = option.rect.adjusted(2, 2, -2, -2)
        is_sel = bool(option.state & QStyle.StateFlag.State_Selected)

        # ── 背景 ──
        painter.setBrush(QColor(AppTheme.BG_SECONDARY if is_sel else AppTheme.BG_CARD))
        painter.setPen(QColor(AppTheme.GOLD_PRIMARY if is_sel else AppTheme.BORDER_GOLD_SUBTLE))
        painter.drawRoundedRect(r, 5, 5)

        # ── Checkbox（左上角）──
        raw_check = index.data(Qt.ItemDataRole.CheckStateRole)
        checked = raw_check in (Qt.CheckState.Checked, Qt.CheckState.Checked.value)
        cb_r = QRect(r.left() + self._PAD, r.top() + self._PAD, self._CB, self._CB)
        painter.setBrush(QColor(AppTheme.GOLD_PRIMARY if checked else AppTheme.BG_TERTIARY))
        painter.setPen(QColor(AppTheme.GOLD_MUTED))
        painter.drawRoundedRect(cb_r, 2, 2)
        if checked:
            f = painter.font()
            f.setBold(True)
            f.setPointSize(7)
            painter.setFont(f)
            painter.setPen(QColor(AppTheme.BG_DEEP))
            painter.drawText(cb_r, Qt.AlignmentFlag.AlignCenter, "✓")

        # ── 圖示（底部對齊，在文字區上方）──
        icon_bot = r.bottom() - self._TH - self._PAD   # 圖示區底部 y
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if icon and not icon.isNull():
            pix = icon.pixmap(_THUMB, _THUMB)
            ix = r.left() + (r.width() - pix.width()) // 2
            iy = icon_bot - pix.height()
            # 不超出 checkbox 以下
            min_iy = r.top() + self._PAD + self._CB + 2
            painter.drawPixmap(ix, max(min_iy, iy), pix)

        # ── 文字（底部固定）──
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        text_r = QRect(r.left() + 2, r.bottom() - self._TH, r.width() - 4, self._TH)
        painter.setPen(QColor(AppTheme.TEXT_PRIMARY))
        f2 = option.font
        f2.setPointSize(9)
        painter.setFont(f2)
        elided = painter.fontMetrics().elidedText(
            text, Qt.TextElideMode.ElideRight, text_r.width() - 4
        )
        painter.drawText(text_r, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, elided)

        painter.restore()

    def editorEvent(self, event, model, option, index):  # noqa: N802
        """點擊格子任意位置切換勾選狀態"""
        if event.type() == QEvent.Type.MouseButtonRelease:
            raw = index.data(Qt.ItemDataRole.CheckStateRole)
            checked = raw in (Qt.CheckState.Checked, Qt.CheckState.Checked.value)
            model.setData(
                index,
                Qt.CheckState.Unchecked if checked else Qt.CheckState.Checked,
                Qt.ItemDataRole.CheckStateRole,
            )
            return True
        return False

    def sizeHint(self, option, index):  # noqa: N802
        return QSize(_THUMB + 20, _THUMB + 52)



class _FilterBar(QFrame):
    """圖片分類篩選列 — Tag chip 切換（內容類型 × 尺寸 × 來源）"""

    _CONTENT_CATS = ("精靈", "背景", "混合")
    _SIZE_CATS    = ("小圖示", "中圖", "大圖")

    def __init__(self, grid: "_FluidGrid", parent=None):
        super().__init__(parent)
        self._grid = grid
        self._active: set[str] = set()
        self._chips: dict[str, QPushButton] = {}
        self._src_sep_inserted = False
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            f"QFrame {{ background:{AppTheme.BG_SECONDARY};"
            f" border-bottom:1px solid {AppTheme.GOLD_MUTED}; }}"
        )
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(8, 3, 8, 3)
        self._lay.setSpacing(4)

        self._all_btn = QPushButton("全部")
        self._all_btn.setCheckable(True)
        self._all_btn.setChecked(True)
        self._all_btn.setFixedHeight(20)
        self._all_btn.setStyleSheet(self._all_style())
        self._all_btn.clicked.connect(self._reset)
        self._lay.addWidget(self._all_btn)

        self._lay.addWidget(self._make_sep())

        for cat in self._CONTENT_CATS:
            btn = self._make_chip(cat)
            self._lay.addWidget(btn)
            self._chips[cat] = btn

        self._lay.addWidget(self._make_sep())

        for cat in self._SIZE_CATS:
            btn = self._make_chip(cat)
            self._lay.addWidget(btn)
            self._chips[cat] = btn

        self._lay.addStretch()

    def _make_sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(14)
        sep.setStyleSheet(f"QFrame {{ background:{AppTheme.GOLD_MUTED}; border:none; }}")
        return sep

    def _make_chip(self, cat: str) -> QPushButton:
        btn = QPushButton(cat)
        btn.setCheckable(True)
        btn.setChecked(False)
        btn.setFixedHeight(20)
        btn.setStyleSheet(self._chip_style())
        btn.toggled.connect(lambda checked, c=cat: self._on_toggled(c, checked))
        return btn

    def add_source(self, source: str):
        """動態加入資料來源 chip（首次出現該來源時呼叫）"""
        if source in self._chips:
            return
        if not self._src_sep_inserted:
            self._lay.insertWidget(self._lay.count() - 1, self._make_sep())
            self._src_sep_inserted = True
        btn = self._make_chip(source)
        self._lay.insertWidget(self._lay.count() - 1, btn)
        self._chips[source] = btn

    def _reset(self):
        self._active.clear()
        for btn in self._chips.values():
            btn.blockSignals(True)
            btn.setChecked(False)
            btn.blockSignals(False)
        self._all_btn.setChecked(True)
        self._apply()

    def _on_toggled(self, cat: str, checked: bool):
        if checked:
            self._active.add(cat)
            self._all_btn.blockSignals(True)
            self._all_btn.setChecked(False)
            self._all_btn.blockSignals(False)
        else:
            self._active.discard(cat)
            if not self._active:
                self._all_btn.setChecked(True)
        self._apply()

    def refresh(self):
        """重新套用篩選（新增項目後呼叫）"""
        self._apply()

    def _apply(self):
        for i in range(self._grid.count()):
            item = self._grid.item(i)
            tags: frozenset = item.data(Qt.ItemDataRole.UserRole + 1) or frozenset()
            hidden = bool(self._active) and not (self._active & tags)
            item.setHidden(hidden)

    @staticmethod
    def _all_style() -> str:
        return (
            f"QPushButton {{ background:{AppTheme.GOLD_PRIMARY}; color:{AppTheme.BG_DEEP};"
            f" border:none; border-radius:9px; padding:0 8px; font-size:10px; font-weight:bold; }}"
            f"QPushButton:!checked {{ background:{AppTheme.BG_TERTIARY}; color:{AppTheme.TEXT_MUTED};"
            f" border:1px solid {AppTheme.GOLD_MUTED}; font-weight:normal; }}"
        )

    @staticmethod
    def _chip_style() -> str:
        return (
            f"QPushButton {{ background:{AppTheme.BG_TERTIARY}; color:{AppTheme.TEXT_MUTED};"
            f" border:1px solid {AppTheme.GOLD_MUTED}; border-radius:9px;"
            f" padding:0 8px; font-size:10px; }}"
            f"QPushButton:checked {{ background:{AppTheme.BG_CARD}; color:{AppTheme.GOLD_LIGHT};"
            f" border-color:{AppTheme.GOLD_PRIMARY}; font-weight:bold; }}"
            f"QPushButton:hover {{ color:{AppTheme.TEXT_PRIMARY}; }}"
        )


class MapleWorldPage(QWidget):
    """MapleStory Worlds 本機資源瀏覽頁面"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._assets: list[dict] = []        # 目前顯示的資產清單
        self._asset_paths: set[str] = set()  # 已加入的 path 集合（去重用）
        self._scanning = False
        self._cache_loaded = False
        self._cache_loading = False          # 背景載入中旗標
        self._build_ui()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if not self._cache_loaded:
            self._cache_loaded = True
            self._load_cached_images()

    # ──────────────────────────────────────────
    # UI 建構
    # ──────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_progress())
        root.addWidget(self._make_status_bar())
        root.addWidget(self._make_top_panel())

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(
            f"QStackedWidget {{ background:{AppTheme.BG_PRIMARY}; border:none; }}"
        )
        self._stack.addWidget(self._make_unity_page())
        self._stack.addWidget(self._make_web_page())
        root.addWidget(self._stack, 1)

        root.addWidget(self._make_footer())

    # ── 頂部固定區：標題、版權聲明、遊戲路徑、Tab 切換列 ──
    def _make_top_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("mw_top")
        panel.setStyleSheet(f"QWidget#mw_top {{ background:{AppTheme.BG_PRIMARY}; }}")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(10, 6, 10, 0)
        lay.setSpacing(4)

        # 標題
        title = QLabel("🍄 MapleWorld 資源瀏覽")
        title.setStyleSheet(
            f"color:{AppTheme.GOLD_LIGHT}; font-size:14px; font-weight:bold;"
            f" background:transparent; border:none;"
        )
        lay.addWidget(title)

        # 版權聲明
        notice = QLabel(
            "⚠ 本功能僅讀取本機已安裝的 MapleStory Worlds 遊戲快取，"
            "提取圖片版權屬 Nexon，僅限個人使用，請勿重新發布。"
        )
        notice.setWordWrap(True)
        notice.setStyleSheet(
            f"color:{AppTheme.TEXT_MUTED}; font-size:10px; background:transparent; border:none;"
        )
        lay.addWidget(notice)

        # 遊戲路徑（公用）
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        lbl = QLabel("遊戲路徑：")
        lbl.setStyleSheet(self._lbl_style())
        row1.addWidget(lbl)
        self._path_input = QLineEdit(_DEFAULT_GAME_PATH)
        self._path_input.setStyleSheet(self._input_style())
        row1.addWidget(self._path_input, 1)
        browse_btn = QPushButton("瀏覽")
        browse_btn.setFixedHeight(26)
        browse_btn.setStyleSheet(self._btn_sec())
        browse_btn.clicked.connect(self._browse_game_path)
        row1.addWidget(browse_btn)
        lay.addLayout(row1)

        # Tab 切換列
        tab_bar = QFrame()
        tab_bar.setObjectName("mw_tab_bar")
        tab_bar.setStyleSheet(
            f"QFrame#mw_tab_bar {{ background:{AppTheme.BG_TERTIARY};"
            f" border-top:1px solid {AppTheme.GOLD_MUTED};"
            f" border-bottom:1px solid {AppTheme.GOLD_MUTED};"
            f" border-left:none; border-right:none; }}"
        )
        tab_lay = QHBoxLayout(tab_bar)
        tab_lay.setContentsMargins(0, 0, 0, 0)
        tab_lay.setSpacing(0)

        tab_style = (
            f"QPushButton {{ background:{AppTheme.BG_TERTIARY}; color:{AppTheme.TEXT_MUTED};"
            f" border:none; border-bottom:2px solid transparent;"
            f" padding:6px 20px; font-size:11px; }}"
            f"QPushButton:hover {{ color:{AppTheme.TEXT_PRIMARY}; }}"
            f"QPushButton:checked {{ background:{AppTheme.BG_SECONDARY};"
            f" color:{AppTheme.GOLD_LIGHT}; border-bottom:2px solid {AppTheme.GOLD_PRIMARY};"
            f" font-weight:bold; }}"
        )
        self._tab_unity = QPushButton("🎮  Unity 遊戲資源")
        self._tab_unity.setCheckable(True)
        self._tab_unity.setChecked(True)
        self._tab_unity.setFixedHeight(34)
        self._tab_unity.setStyleSheet(tab_style)
        tab_lay.addWidget(self._tab_unity)

        self._tab_web = QPushButton("🌐  WebView 網頁快取")
        self._tab_web.setCheckable(True)
        self._tab_web.setFixedHeight(34)
        self._tab_web.setStyleSheet(tab_style)
        tab_lay.addWidget(self._tab_web)

        tab_lay.addStretch()

        self._tab_group = QButtonGroup(self)
        self._tab_group.addButton(self._tab_unity, 0)
        self._tab_group.addButton(self._tab_web, 1)
        self._tab_group.setExclusive(True)
        self._tab_group.idClicked.connect(self._on_tab_changed)

        lay.addWidget(tab_bar)
        return panel

    def _on_tab_changed(self, idx: int):
        self._stack.setCurrentIndex(idx)

    # ── Unity 頁面 ──
    def _make_unity_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("mw_unity_page")
        page.setStyleSheet(f"QWidget#mw_unity_page {{ background:{AppTheme.BG_PRIMARY}; }}")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(0)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(10, 6, 6, 6)
        top_row.setSpacing(8)
        desc = QLabel(
            "掃描 resource_cache/ 下所有子目錄（msw/、ugc/ 等），"
            "解碼 .win.mod 內的 DDS 紋理圖與 PNG/JPEG 嵌入圖，自動儲存至 images/mapleworld/。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color:{AppTheme.TEXT_MUTED}; font-size:10px; background:transparent; border:none;"
        )
        top_row.addWidget(desc, 1)
        self._scan_btn = QPushButton("🔍 掃描遊戲資源 (Unity)")
        self._scan_btn.setFixedHeight(28)
        self._scan_btn.setStyleSheet(self._btn_pri())
        self._scan_btn.clicked.connect(self._start_scan)
        top_row.addWidget(self._scan_btn)
        lay.addLayout(top_row)

        self._unity_grid = self._make_grid_widget()
        self._unity_filter_bar = _FilterBar(self._unity_grid)
        lay.addWidget(self._unity_filter_bar)
        lay.addWidget(self._unity_grid, 1)
        return page

    # ── WebView 頁面 ──
    def _make_web_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("mw_web_page")
        page.setStyleSheet(f"QWidget#mw_web_page {{ background:{AppTheme.BG_PRIMARY}; }}")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(0)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(10, 6, 6, 6)
        top_row.setSpacing(8)
        desc = QLabel(
            "掃描 Vuplex.WebView/chromium-cache/ 目錄，直接提取 PNG/WebP 圖片，"
            "並從 JSON 內容取得圖片 URL 後下載。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color:{AppTheme.TEXT_MUTED}; font-size:10px; background:transparent; border:none;"
        )
        top_row.addWidget(desc, 1)
        self._scan_web_btn = QPushButton("🌐 掃描網頁快取 (WebView)")
        self._scan_web_btn.setFixedHeight(28)
        self._scan_web_btn.setStyleSheet(self._btn_sec())
        self._scan_web_btn.clicked.connect(self._start_web_scan)
        top_row.addWidget(self._scan_web_btn)
        lay.addLayout(top_row)

        self._web_grid = self._make_grid_widget()
        self._web_filter_bar = _FilterBar(self._web_grid)
        lay.addWidget(self._web_filter_bar)
        lay.addWidget(self._web_grid, 1)
        return page

    def _make_grid_widget(self) -> _FluidGrid:
        """建立並回傳一個配置好的縮圖 grid"""
        grid = _FluidGrid()
        grid.setViewMode(QListWidget.ViewMode.IconMode)
        grid.setIconSize(QSize(_THUMB, _THUMB))
        grid.setUniformItemSizes(True)
        grid.setWordWrap(False)
        grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        grid.setSpacing(0)
        grid.setWrapping(True)
        grid.viewport().setContentsMargins(0, 0, 0, 0)
        grid.setItemDelegate(_ThumbDelegate(grid))
        grid.setStyleSheet(
            f"QListWidget {{ background:{AppTheme.BG_PRIMARY}; border:none; outline:none;"
            f" padding:0; margin:0;"
            f" border-top: 1px solid {AppTheme.GOLD_MUTED}; }}"
            f"QListWidget::item {{ padding:0; margin:0; }}"
        )
        return grid

    # ── 進度列 ──
    def _make_progress(self) -> QProgressBar:
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setFixedHeight(3)
        self._progress_bar.setVisible(False)
        self._progress_bar.setStyleSheet(
            f"QProgressBar {{ background:{AppTheme.BG_SECONDARY}; border:none; }}"
            f"QProgressBar::chunk {{ background:{AppTheme.GOLD_PRIMARY}; }}"
        )
        return self._progress_bar

    # ── 狀態列 ──
    def _make_status_bar(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background:{AppTheme.BG_SECONDARY}; border:none; }}"
        )
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(12, 3, 12, 3)
        self._status_lbl = QLabel("尚未掃描 — 點擊「掃描遊戲資源」載入")
        self._status_lbl.setStyleSheet(
            f"color:{AppTheme.TEXT_MUTED}; font-size:10px; background:transparent; border:none;"
        )
        lay.addWidget(self._status_lbl)
        lay.addStretch()
        # 顯示快取資料夾路徑提示
        cache_lbl = QLabel(f"快取：{os.path.abspath(_MAPLEWORLD_DIR)}")
        cache_lbl.setStyleSheet(
            f"color:{AppTheme.TEXT_MUTED}; font-size:9px; background:transparent; border:none;"
        )
        lay.addWidget(cache_lbl)
        return frame

    # ── 底部工具列 ──
    def _make_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("mw_footer")
        footer.setStyleSheet(
            f"QFrame#mw_footer {{ background:{AppTheme.BG_SECONDARY};"
            f" border-top:1px solid {AppTheme.GOLD_MUTED}; }}"
        )
        lay = QHBoxLayout(footer)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(8)

        self._select_all_cb = QCheckBox("全選")
        self._select_all_cb.setStyleSheet(
            f"QCheckBox {{ color:{AppTheme.TEXT_PRIMARY}; font-size:11px; background:transparent; }}"
            f"QCheckBox::indicator {{ width:14px; height:14px; }}"
            f"QCheckBox::indicator:checked {{ background:{AppTheme.GOLD_PRIMARY}; border-radius:2px; }}"
            f"QCheckBox::indicator:unchecked {{ background:{AppTheme.BG_TERTIARY};"
            f" border:1px solid {AppTheme.GOLD_MUTED}; border-radius:2px; }}"
        )
        self._select_all_cb.stateChanged.connect(self._toggle_select_all)
        lay.addWidget(self._select_all_cb)

        lay.addStretch()

        preview_btn = QPushButton("🔍 放大預覽")
        preview_btn.setFixedHeight(28)
        preview_btn.setStyleSheet(self._btn_sec())
        preview_btn.clicked.connect(self._open_preview)
        lay.addWidget(preview_btn)

        delete_all_btn = QPushButton("🗑 全部刪除")
        delete_all_btn.setFixedHeight(28)
        delete_all_btn.setStyleSheet(
            f"QPushButton {{ background:{AppTheme.BG_TERTIARY}; color:#e05555;"
            f" border:1px solid #7a3333; border-radius:4px;"
            f" padding:0 10px; font-size:11px; }}"
            f"QPushButton:hover {{ background:#3a1a1a; color:#ff8080; }}"
        )
        delete_all_btn.clicked.connect(self._delete_all_cache)
        lay.addWidget(delete_all_btn)

        open_btn = QPushButton("📁 開啟快取資料夾")
        open_btn.setFixedHeight(28)
        open_btn.setStyleSheet(self._btn_sec())
        open_btn.clicked.connect(self._open_cache_folder)
        lay.addWidget(open_btn)

        self._extract_btn = QPushButton("📥 提取選取圖片")
        self._extract_btn.setFixedHeight(28)
        self._extract_btn.setEnabled(False)
        self._extract_btn.setStyleSheet(self._btn_pri())
        self._extract_btn.clicked.connect(self._extract_selected)
        lay.addWidget(self._extract_btn)

        return footer

    # ──────────────────────────────────────────
    # 樣式輔助
    # ──────────────────────────────────────────

    def _btn_pri(self) -> str:
        return (
            f"QPushButton {{ background:{AppTheme.GOLD_PRIMARY}; color:{AppTheme.BG_DEEP};"
            f" border:none; border-radius:4px; padding:0 12px;"
            f" font-size:11px; font-weight:bold; }}"
            f"QPushButton:hover {{ background:{AppTheme.GOLD_LIGHT}; }}"
            f"QPushButton:disabled {{ background:{AppTheme.BG_TERTIARY}; color:{AppTheme.TEXT_MUTED}; }}"
        )

    def _btn_sec(self) -> str:
        return (
            f"QPushButton {{ background:{AppTheme.BG_TERTIARY}; color:{AppTheme.TEXT_PRIMARY};"
            f" border:1px solid {AppTheme.GOLD_MUTED}; border-radius:4px;"
            f" padding:0 10px; font-size:11px; }}"
            f"QPushButton:hover {{ background:{AppTheme.BG_CARD}; color:{AppTheme.GOLD_LIGHT}; }}"
        )

    def _lbl_style(self) -> str:
        return (
            f"color:{AppTheme.TEXT_PRIMARY}; font-size:11px; background:transparent; border:none;"
        )

    def _input_style(self) -> str:
        return (
            f"QLineEdit {{ background:{AppTheme.BG_TERTIARY}; color:{AppTheme.TEXT_PRIMARY};"
            f" border:1px solid {AppTheme.GOLD_MUTED}; border-radius:4px;"
            f" padding:2px 6px; font-size:10px; }}"
            f"QLineEdit:focus {{ border-color:{AppTheme.GOLD_PRIMARY}; }}"
        )

    # ──────────────────────────────────────────
    # 路徑操作
    # ──────────────────────────────────────────

    def _browse_game_path(self):
        current = self._path_input.text().strip()
        path = QFileDialog.getExistingDirectory(
            self, "選擇 MapleStory Worlds 遊戲目錄",
            current if os.path.isdir(current) else ""
        )
        if path:
            self._path_input.setText(os.path.normpath(path))

    def _open_cache_folder(self):
        """用 Explorer 開啟快取資料夾"""
        import subprocess
        folder = os.path.abspath(_MAPLEWORLD_DIR)
        os.makedirs(folder, exist_ok=True)
        subprocess.Popen(f'explorer "{folder}"')

    def _delete_all_cache(self):
        """刪除 images/mapleworld/ 內所有 PNG，並清空清單"""
        if not os.path.isdir(_MAPLEWORLD_DIR):
            self.app.toast.show("快取資料夾不存在或已清空。", "info")
            return
        files = [f for f in os.listdir(_MAPLEWORLD_DIR) if f.lower().endswith(".png")]
        if not files:
            self.app.toast.show("快取資料夾已是空的。", "info")
            return
        ans = QMessageBox.question(
            self, "確認刪除",
            f"確定要刪除快取資料夾內所有 {len(files)} 張圖片嗎？\n\n"
            f"({os.path.abspath(_MAPLEWORLD_DIR)})\n\n此操作無法復原。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        failed = 0
        for f in files:
            try:
                os.remove(os.path.join(_MAPLEWORLD_DIR, f))
            except Exception:
                failed += 1
        self._unity_grid.clear()
        self._web_grid.clear()
        self._assets.clear()
        self._asset_paths.clear()
        self._extract_btn.setEnabled(False)
        msg = f"已刪除 {len(files) - failed} 張"
        if failed:
            msg += f"（{failed} 個失敗）"
        self._status_lbl.setText(msg)

    def _open_preview(self):
        """放大預覽目前選取（單選）或最後勾選的圖片（同時檢查兩個 grid）"""
        idx = None
        # 優先取 Qt 選取項目
        for grid in (self._unity_grid, self._web_grid):
            sel = grid.selectedItems()
            if sel:
                idx = sel[0].data(Qt.ItemDataRole.UserRole)
                break
        # 其次取第一個勾選項目
        if idx is None:
            for grid in (self._unity_grid, self._web_grid):
                for i in range(grid.count()):
                    item = grid.item(i)
                    if item.checkState() == Qt.CheckState.Checked:
                        idx = item.data(Qt.ItemDataRole.UserRole)
                        break
                if idx is not None:
                    break

        if idx is None:
            self.app.toast.show("請先點擊或勾選一張圖片再預覽。", "info")
            return

        asset = self._assets[idx]
        pil_img = asset.get("_pil_img")
        if pil_img is None:
            from PIL import Image as PILImage
            try:
                pil_img = PILImage.open(asset["path"]).convert("RGBA")
            except Exception:
                self.app.toast.show("圖片檔案無法讀取。", "info")
                return

        dlg = _PreviewDialog(pil_img, asset["name"], self)
        dlg.show()

    # ──────────────────────────────────────────
    # 快取圖片載入（頁面開啟時）
    # ──────────────────────────────────────────

    _CACHE_BATCH = 20  # 每批處理張數

    def _load_cached_images(self):
        """讀取 images/mapleworld/ 資料夾，背景執行緒分批載入

        - web_ / cdn_ 前綴 → WebView grid
        - 其他               → Unity grid
        """
        if not os.path.isdir(_MAPLEWORLD_DIR):
            return
        if self._cache_loading:
            return

        self._unity_grid.clear()
        self._web_grid.clear()
        self._assets.clear()
        self._asset_paths.clear()

        files = sorted(f for f in os.listdir(_MAPLEWORLD_DIR) if f.lower().endswith(".png"))
        if not files:
            return

        self._cache_loading = True
        self._cache_stop = False
        self._status_lbl.setText(f"正在載入快取圖片 (0/{len(files)})…")

        t = threading.Thread(
            target=self._cache_load_worker, args=(files,), daemon=True
        )
        t.start()

    def _cache_load_worker(self, files: list[str]):
        """背景執行緒：分批處理 PIL 開檔 / 分類（不建立 QPixmap）"""
        from PIL import Image as PILImage

        batch: list[tuple] = []
        total = len(files)

        for i, fname in enumerate(files):
            if self._cache_stop:
                return
            fp = os.path.join(_MAPLEWORLD_DIR, fname)
            try:
                img = PILImage.open(fp).convert("RGBA")
            except Exception:
                continue
            name = os.path.splitext(fname)[0]
            is_web = fname.startswith("web_") or fname.startswith("cdn_")
            size_cat, content_cat = self._classify_image(img)

            # 預先縮圖並轉為 bytes，避免在背景執行緒建立 QPixmap
            thumb = img.copy()
            thumb.thumbnail((_THUMB, _THUMB))
            thumb_data = (thumb.tobytes("raw", "RGBA"), thumb.size[0], thumb.size[1])

            batch.append((img, name, fp, is_web, thumb_data, size_cat, content_cat))

            if len(batch) >= self._CACHE_BATCH or i == total - 1:
                items = list(batch)
                loaded = i + 1
                batch.clear()
                try:
                    self.app.after(0, lambda b=items, n=loaded, t=total: self._add_cache_batch(b, n, t))
                except RuntimeError:
                    return

        try:
            self.app.after(0, self._on_cache_load_done)
        except RuntimeError:
            pass

    def _add_cache_batch(self, batch, loaded: int, total: int):
        """主執行緒：將一批處理好的項目加入 grid"""
        for img, name, fp, is_web, thumb_data, size_cat, content_cat in batch:
            # 在主執行緒建立 QPixmap / QIcon（執行緒安全）
            raw, tw, th = thumb_data
            qimg = QImage(raw, tw, th, QImage.Format.Format_RGBA8888)
            icon = QIcon(QPixmap.fromImage(qimg))
            if is_web:
                self._add_web_item(img, name, fp, "快取-web",
                                   precomputed=(icon, size_cat, content_cat))
            else:
                self._add_unity_item(img, name, fp, "快取-unity",
                                     precomputed=(icon, size_cat, content_cat))
        self._status_lbl.setText(f"正在載入快取圖片 ({loaded}/{total})…")

    def _on_cache_load_done(self):
        """快取載入完成"""
        self._cache_loading = False
        unity_cnt = sum(1 for a in self._assets if not a["type"].endswith("-web"))
        web_cnt = sum(1 for a in self._assets if a["type"].endswith("-web"))
        self._unity_filter_bar.refresh()
        self._web_filter_bar.refresh()
        if self._assets:
            self._status_lbl.setText(
                f"快取圖片：Unity {unity_cnt} 張 ／ WebView {web_cnt} 張（可重新掃描更新）"
            )
            self._extract_btn.setEnabled(True)
        else:
            self._status_lbl.setText("尚無快取圖片。請使用掃描功能。")

    # ──────────────────────────────────────────
    # 縮圖清單輔助
    # ──────────────────────────────────────────

    def _add_unity_item(self, img, name: str, source_path: str, res_type: str,
                        precomputed=None):
        """新增縮圖到 Unity 手風琴 grid"""
        self._add_to(img, name, source_path, res_type, self._unity_grid,
                     self._unity_filter_bar, precomputed=precomputed)

    def _add_web_item(self, img, name: str, source_path: str, res_type: str,
                      precomputed=None):
        """新增縮圖到 WebView 手風琴 grid"""
        self._add_to(img, name, source_path, res_type, self._web_grid,
                     self._web_filter_bar, precomputed=precomputed)

    @staticmethod
    def _classify_image(img) -> tuple[str, str]:
        """依照圖片屬性分類

        Returns:
            (size_cat, content_cat)：
                size_cat    — 小圖示 / 中圖 / 大圖
                content_cat — 精靈 / 背景 / 混合
        """
        w, h = img.width, img.height
        if w <= 64 and h <= 64:
            size_cat = "小圖示"
        elif w >= 256 or h >= 256:
            size_cat = "大圖"
        else:
            size_cat = "中圖"

        alpha = img.split()[3]
        hist = alpha.histogram()          # 256 個 bin（pixel value 0-255 的計數）
        total = sum(hist)
        if total:
            transp = sum(hist[:128])      # alpha < 128 視為透明
            t_ratio = transp / total
        else:
            t_ratio = 0.0

        if t_ratio > 0.4:
            content_cat = "精靈"
        elif t_ratio < 0.05:
            content_cat = "背景"
        else:
            content_cat = "混合"

        return size_cat, content_cat

    def _add_to(self, img, name: str, source_path: str, res_type: str,
                grid: "_FluidGrid", filter_bar: "_FilterBar | None" = None,
                precomputed=None):
        """新增一個縮圖項目到指定 grid（path 相同則跳過，避免重複）

        Args:
            precomputed: 可選 (icon, size_cat, content_cat)，
                         由背景執行緒預先計算以避免主執行緒阻塞
        """
        abs_path = os.path.abspath(source_path)
        if abs_path in self._asset_paths:
            return
        self._asset_paths.add(abs_path)

        # 分類標籤（使用預計算結果或即時計算）
        if precomputed is not None:
            icon, size_cat, content_cat = precomputed
        else:
            icon = _pil_to_icon(img)
            size_cat, content_cat = self._classify_image(img)
        top_src = res_type.split("/")[0]          # 第一層來源：msw / ugc / web-cache / 快取-unity …
        tags = frozenset({size_cat, content_cat, top_src})

        idx = len(self._assets)
        self._assets.append({
            "name":     name,
            "type":     res_type,
            "path":     source_path,
            "width":    img.width,
            "height":   img.height,
            "tags":     tags,
            "_pil_img": None,
        })

        # 通知篩選列新增來源 chip（幂等操作）
        if filter_bar is not None:
            filter_bar.add_source(top_src)

        # 顯示名稱截斷（避免長度不一造成格子高度異）
        short = name if len(name) <= 11 else name[:10] + "…"
        item = QListWidgetItem(icon, short)
        item.setData(Qt.ItemDataRole.UserRole, idx)
        item.setData(Qt.ItemDataRole.UserRole + 1, tags)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Unchecked)
        item.setToolTip(
            f"{name}\n{img.width}×{img.height} px\n"
            f"類型: {res_type}\n標籤: {size_cat} · {content_cat}"
        )
        grid.addItem(item)

    # ──────────────────────────────────────────
    # 掃描（背景執行緒）
    # ──────────────────────────────────────────

    def _start_scan(self):
        if self._scanning:
            return

        game_path = self._path_input.text().strip()
        resource_cache = os.path.join(game_path, "resource_cache")
        if not os.path.isdir(resource_cache):
            self.app.toast.show(f"找不到資源快取目錄，請確認遊戲路徑是否正確。", "error")
            return

        os.makedirs(_MAPLEWORLD_DIR, exist_ok=True)

        self._scanning = True
        self._scan_btn.setEnabled(False)
        self._scan_btn.setText("掃描中...")
        self._progress_bar.setVisible(True)
        self._status_lbl.setText("掃描中，自動解碼並儲存至 images/mapleworld/ …")
        self._select_all_cb.setChecked(False)

        threading.Thread(
            target=self._scan_worker,
            args=(resource_cache,),
            daemon=True,
        ).start()

    @staticmethod
    def _extract_all_dds(raw: bytes):
        """從原始資料中提取所有 DDS 圖片

        部分 .win.mod 內含多個 DDS 資料塊，逐一掃描並解碼。
        利用 BytesIO.tell() 取得每次 PIL 實際讀取的位元組數，
        以此定位下一個 DDS 的起點。

        Args:
            raw: .win.mod 完整原始資料

        Yields:
            (index, PIL Image RGBA) — 同一檔案的第幾張圖、圖片物件
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
                # 前進到這個 DDS 結束後繼續找
                pos = found + max(consumed, 128)
            except Exception:
                pos = found + 4   # 跳過損壞的 DDS，繼續往後找

    def _scan_worker(self, resource_cache: str):
        """背景掃描：resource_cache/ 下所有子目錄的 .win.mod → PNG

        掃描範圍：
          - resource_cache/msw/  → 內含 DDS 紋理（需翻轉）
          - resource_cache/ugc/  → 內含 PNG 直接嵌入
          - resource_cache/raw/  → 保留

        策略：先找 DDS，沒有 DDS 就用 _extract_images_from_bytes 找 PNG/JPEG/etc。
        命名：{UUID}.png（單圖）/ {UUID}_{index}.png（多圖）
        """
        from PIL import Image as PILImage

        saved: list[tuple] = []
        errors: int = 0

        try:
            # 遞迴收集所有 .win.mod（含 msw/ ugc/ raw/ 等所有子目錄）
            mod_files: list[tuple[str, str]] = []
            for root, _dirs, files in os.walk(resource_cache):
                for f in files:
                    if f.endswith(".win.mod"):
                        # 取前兩層路徑作 dir_type（e.g. msw/avataritem, msw/01-sprite, ugc）
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
            self.app.after(0, lambda: self._status_lbl.setText(
                f"找到 {total} 個 .win.mod，解碼中…"
            ))

            for fi, (mod_path, dir_type) in enumerate(mod_files):
                if fi % 500 == 0:
                    pct = fi * 100 // total if total else 0
                    n = len(saved)
                    self.app.after(0, lambda p=pct, c=n, f=fi, t=total: self._status_lbl.setText(
                        f"解碼中 {f}/{t} ({p}%)  已存 {c} 張…"
                    ))
                try:
                    with open(mod_path, "rb") as fh:
                        raw = fh.read()

                    base_hash = os.path.basename(mod_path).replace(".win.mod", "")

                    # ① 先嘗試 DDS（msw/ 的主要格式，需上下翻轉）
                    dds_imgs = list(self._extract_all_dds(raw))
                    if dds_imgs:
                        for img_idx, img in dds_imgs:
                            suffix = f"_{img_idx}" if len(dds_imgs) > 1 else ""
                            name = f"{base_hash}{suffix}"
                            save_path = os.path.join(_MAPLEWORLD_DIR, f"{name}.png")
                            img.save(save_path, "PNG")
                            saved.append((name, img, save_path, dir_type))
                        continue

                    # ② 沒有 DDS → 找 PNG / JPEG / WebP / GIF（ugc/ 的格式，不翻轉）
                    other_imgs = self._extract_images_from_bytes(raw, PILImage)
                    for img_idx, img in enumerate(other_imgs):
                        suffix = f"_{img_idx}" if len(other_imgs) > 1 else ""
                        name = f"{base_hash}{suffix}"
                        save_path = os.path.join(_MAPLEWORLD_DIR, f"{name}.png")
                        img.save(save_path, "PNG")
                        saved.append((name, img, save_path, dir_type))

                except Exception:
                    errors += 1

        except Exception as e:
            self.app.after(0, lambda: self._on_scan_done([], 0, str(e)))
            return

        self.app.after(0, lambda: self._on_scan_done(saved, errors, None))

    # ──────────────────────────────────────────
    # 網頁快取掃描（Vuplex.WebView Chromium）
    # ──────────────────────────────────────────

    def _start_web_scan(self):
        """啟動 Chromium WebView 快取掃描（自動發現所有快取目錄）"""
        if self._scanning:
            return

        game_path = self._path_input.text().strip()
        vuplex_dir = os.path.join(game_path, "Vuplex.WebView")
        if not os.path.isdir(vuplex_dir):
            self.app.toast.show("找不到 Vuplex.WebView 目錄，請確認遊戲路徑並先啟動遊戲。", "error")
            return

        os.makedirs(_MAPLEWORLD_DIR, exist_ok=True)

        self._scanning = True
        self._scan_btn.setEnabled(False)
        self._scan_web_btn.setEnabled(False)
        self._scan_web_btn.setText("掃描中...")
        self._progress_bar.setVisible(True)
        self._status_lbl.setText("搜尋快取目錄中…")
        self._select_all_cb.setChecked(False)

        threading.Thread(
            target=self._web_cache_worker,
            args=(vuplex_dir,),
            daemon=True,
        ).start()

    def _web_cache_worker(self, vuplex_dir: str):
        """背景：多路徑多格式掃描

        Phase 0 — 自動發現：遞迴走訪 Vuplex.WebView/，收集所有快取相關檔案
                  SimpleCache (f_*)、Blockfile (data_*)、IndexedDB/LocalStorage (*.ldb, *.log)
        Phase 1 — 直接提取：暴力掃描位元組，找 PNG / WebP / JPEG / GIF magic bytes
                  同時嘗試 gzip 解壓後再掃描
        Phase 2 — URL 下載：從文字內容提取圖片 URL，從網路下載
        Phase 3 — Base64 解碼：從 data:image/... base64 字串解出內嵌圖片
        """
        import gzip
        import base64 as _base64
        import re as _re
        from PIL import Image as PILImage
        import requests as _requests

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
            self.app.after(0, lambda: self._on_web_scan_done([], 0, str(e)))
            return

        total_files = len(scan_files)
        if total_files == 0:
            self.app.after(0, lambda: self._on_web_scan_done(
                [], 0, f"在 {vuplex_dir} 下找不到任何快取檔案\n請先啟動遊戲讓 WebView 建立快取。"
            ))
            return

        self.app.after(0, lambda: self._status_lbl.setText(
            f"發現 {total_files} 個快取檔案，掃描中…"
        ))

        # ── Phase 1：暴力掃描全部位元組 ──
        for fi, fpath in enumerate(scan_files):
            if fi % 100 == 0:
                pct = fi * 100 // total_files
                n = len(saved)
                self.app.after(0, lambda p=pct, c=n, f=fi, t=total_files: self._status_lbl.setText(
                    f"掃描中 {f}/{t} ({p}%)  已提取 {c} 張…"
                ))

            fname_base = os.path.basename(fpath)
            try:
                with open(fpath, "rb") as fp:
                    raw_data = fp.read()

                if len(raw_data) < 16:
                    continue

                # 原始 + 所有 gzip 解壓結果
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
                    imgs = self._extract_images_from_bytes(chunk, PILImage)
                    for img_idx, img in enumerate(imgs):
                        base_name = f"web_{fname_base}_{chunk_idx}_{img_idx}"
                        if base_name in seen_names:
                            continue
                        seen_names.add(base_name)
                        save_path = os.path.join(_MAPLEWORLD_DIR, f"{base_name}.png")
                        img.save(save_path, "PNG")
                        saved.append((base_name, img, save_path, "web-cache"))

                    # Phase 1b：從文字內容提取圖片 URL（不限網域，含 gif）
                    try:
                        text = chunk.decode("utf-8", errors="ignore")
                        urls = _re.findall(
                            r'https?://[^\s"\'<>\[\]{}\\]+?\.(?:png|webp|jpg|jpeg|gif)'
                            r'(?:[?#][^\s"\'<>\[\]{}\\]*)?',
                            text,
                        )
                        for url in urls:
                            url_clean = url.split("?")[0].split("#")[0]
                            if url_clean not in seen_urls and len(url_clean) < 512:
                                seen_urls.add(url_clean)
                                cdn_urls.append(url_clean)

                        # Phase 3：提取 data:image/... Base64 內嵌圖片
                        for img_fmt, b64_data in _re.findall(
                            r'data:image/(png|jpeg|gif|webp);base64,([A-Za-z0-9+/=]{100,})',
                            text,
                        ):
                            try:
                                img_bytes = _base64.b64decode(b64_data + "==")
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
        self.app.after(0, lambda: self._status_lbl.setText(
            f"直接提取 {p1_count} 張｜準備下載 {len(cdn_urls)} 個 URL…"
        ))

        # ── Phase 2：從 URL 下載圖片 ──
        session = _requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36",
        })

        for i, url in enumerate(cdn_urls):
            if i % 50 == 0:
                prog = i
                total = len(cdn_urls)
                dl = len(saved) - p1_count
                self.app.after(0, lambda p=prog, t=total, d=dl: self._status_lbl.setText(
                    f"下載中：{p}/{t}  已存 {d} 張…"
                ))

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

        self.app.after(0, lambda: self._on_web_scan_done(saved, errors, None))

    @staticmethod
    def _extract_images_from_bytes(data: bytes, PILImage) -> list:
        """從 bytes 中掃描並提取所有 PNG / WebP 圖片

        Args:
            data:     原始位元組資料
            PILImage: PIL.Image 模組

        Returns:
            PIL Image (RGBA) 清單
        """
        results = []
        seen_offsets: set[int] = set()

        # (magic, extra_check, min_skip)
        # extra_check="WEBP" → 驗證 offset+8 == b"WEBP"
        signatures = [
            (b"\x89PNG\r\n\x1a\n", None,     8),   # PNG
            (b"RIFF",              "WEBP",   12),  # WebP (RIFF container)
            (b"\xff\xd8\xff",      None,      3),   # JPEG
            (b"GIF87a",            None,      6),   # GIF 87a
            (b"GIF89a",            None,      6),   # GIF 89a（含動畫）
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
                    # 過濾太小的圖（< 16x16 通常是 icon 或雜訊）
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

    def _on_web_scan_done(self, saved: list, errors: int, fatal: str | None):
        """網頁快取掃描完成（主執行緒）"""
        self._scanning = False
        self._scan_btn.setEnabled(True)
        self._scan_web_btn.setEnabled(True)
        self._scan_web_btn.setText("🌐 掃描網頁快取 (WebView)")
        self._progress_bar.setVisible(False)

        if fatal:
            self.app.toast.show(f"掃描失敗：{fatal}", "error")
            self._status_lbl.setText("掃描失敗")
            return

        added = 0
        for name, img, save_path, dir_type in saved:
            before = len(self._assets)
            self._add_web_item(img, name, save_path, dir_type)
            if len(self._assets) > before:
                added += 1

        self._web_filter_bar.refresh()
        err_hint = f"（{errors} 個檔案解析失敗）" if errors else ""
        self._status_lbl.setText(
            f"WebView 掃描完成：新增 {added} 張（共 {len(self._assets)} 張）{err_hint}"
        )
        self._extract_btn.setEnabled(bool(self._assets))

    def _on_scan_done(self, saved: list, errors: int, fatal: str | None):
        """掃描完成（主執行緒）"""
        self._scanning = False
        self._scan_btn.setEnabled(True)
        self._scan_btn.setText("🔍 掃描遊戲資源")
        self._progress_bar.setVisible(False)

        if fatal:
            self.app.toast.show(f"掃描失敗：{fatal}", "error")
            self._status_lbl.setText("掃描失敗")
            return

        added = 0
        for name, img, save_path, dir_type in saved:
            before = len(self._assets)
            self._add_unity_item(img, name, save_path, dir_type)
            if len(self._assets) > before:
                added += 1

        self._unity_filter_bar.refresh()
        err_hint = f"（{errors} 個解析失敗）" if errors else ""
        self._status_lbl.setText(
            f"Unity 掃描完成：新增 {added} 張（共 {len(self._assets)} 張）{err_hint}"
        )
        self._extract_btn.setEnabled(bool(self._assets))

    # ──────────────────────────────────────────
    # 全選
    # ──────────────────────────────────────────

    def _toggle_select_all(self, state: int):
        check = (
            Qt.CheckState.Checked
            if state == Qt.CheckState.Checked.value
            else Qt.CheckState.Unchecked
        )
        for grid in (self._unity_grid, self._web_grid):
            for i in range(grid.count()):
                grid.item(i).setCheckState(check)

    # ──────────────────────────────────────────
    # 提取選取圖片（複製到使用者選擇的目錄）
    # ──────────────────────────────────────────

    def _extract_selected(self):
        """勾選的圖片（兩個 grid 皆納入）→ 使用者選擇目的地 → 複製過去"""
        indices = []
        for grid in (self._unity_grid, self._web_grid):
            for i in range(grid.count()):
                item = grid.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    indices.append(item.data(Qt.ItemDataRole.UserRole))
        if not indices:
            self.app.toast.show("請先勾選要提取的圖片。", "info")
            return

        dest = QFileDialog.getExistingDirectory(
            self, f"選擇複製目的地（共 {len(indices)} 張）",
            os.path.expanduser("~")
        )
        if not dest:
            return

        success = skipped = failed = 0
        for idx in indices:
            asset = self._assets[idx]
            src = asset["path"]
            fname = os.path.basename(src)
            dst = os.path.join(dest, fname)
            if os.path.exists(dst):
                skipped += 1
                continue
            try:
                shutil.copy2(src, dst)
                success += 1
            except Exception:
                failed += 1

        msg = f"複製完成：{success} 個成功"
        if skipped:
            msg += f"、{skipped} 個已存在（跳過）"
        if failed:
            msg += f"、{failed} 個失敗"
        toast_type = "error" if failed else "success"
        self.app.toast.show(msg, toast_type)
