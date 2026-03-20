"""
羅茱工具頁面 — PySide6 版本
每格顯示數字（1–4），選中後變為當前玩家顏色
每位玩家每層只能選一個數字（選新的自動取代）
玩家列表 + 格子工具並排置中
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QApplication, QLineEdit,
)
from PySide6.QtCore import Qt, QPoint, QSize, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygon

from src.ui.theme import AppTheme

NUM_PLAYERS = 4
NUM_FLOORS  = 10
NUM_COLS    = 4   # 數字 1–4


# ─────────────────────────────────────────
# 格子元件：顯示數字，選中後填滿玩家顏色
# ─────────────────────────────────────────

class _Cell(QWidget):
    """格子 — 顯示數字（1–4），由擁有者顏色填滿；空格為暗色"""

    clicked = Signal(int, int)   # floor_idx, col_idx

    _CELL_W = 44
    _CELL_H = 38

    def __init__(self, floor_idx: int, col_idx: int, parent=None):
        super().__init__(parent)
        self.floor_idx = floor_idx
        self.col_idx   = col_idx
        self._number   = str(col_idx + 1)
        self._owner    = -1      # -1 = 空, 0-3 = 玩家索引
        self._hovered  = False
        self.setFixedSize(self._CELL_W, self._CELL_H)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_owner(self, owner: int):
        """設定擁有者 (-1=空, 0-3=玩家)"""
        if self._owner != owner:
            self._owner = owner
            self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        if self._owner >= 0:
            # 已選：玩家顏色背景
            base = QColor(AppTheme.PLAYER_COLORS[self._owner])
            bg   = base.darker(115) if self._hovered else base
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(rect, 6, 6)
            # 數字：白色粗體
            text_color = QColor(AppTheme.TEXT_HIGHLIGHT)
        else:
            # 空：暗色背景
            bg = QColor(AppTheme.ROJA_CELL_BG_HOVER if self._hovered else AppTheme.ROJA_CELL_BG)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(rect, 6, 6)
            # 邊框
            painter.setPen(QPen(QColor(AppTheme.ROJA_CELL_BORDER), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 6, 6)
            # 數字：暗色
            text_color = QColor(AppTheme.ROJA_CELL_TEXT_HOVER if self._hovered else AppTheme.ROJA_CELL_TEXT)

        font = QFont()
        font.setPixelSize(15)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._number)

    def enterEvent(self, event):  # noqa: N802
        self._hovered = True
        self.update()

    def leaveEvent(self, event):  # noqa: N802
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.floor_idx, self.col_idx)


# ─────────────────────────────────────────
# 共用輔助：建立格子 GridLayout
# ─────────────────────────────────────────

def _make_cells_grid(
    page: "RojaPage",
    cell_dict: dict,
    click_handler,
    *,
    grid_margins: tuple = (0, 0, 0, 0),
    h_spacing: int = 5,
    v_spacing: int = 4,
    label_w: int = 26,
    label_h: int = _Cell._CELL_H,
    cell_size: "tuple | None" = None,
) -> QWidget:
    """建立樓層 × 數字的格子 Grid 元件

    Args:
        page:          RojaPage 實例，提供 _owner 擁有者資料
        cell_dict:     用於儲存建立的 _Cell 物件，格式為 {(floor_idx, col_idx): cell}
        click_handler: 連接 cell.clicked 的 slot
        grid_margins:  QGridLayout contentsMargins (left, top, right, bottom)
        h_spacing:     水平間距
        v_spacing:     垂直間距
        label_w:       樓層標籤寬度
        label_h:       樓層標籤高度
        cell_size:     (w, h) 強制設定格子尺寸，None 使用預設值

    Returns:
        包含 QGridLayout 的透明 QWidget
    """
    gw = QWidget()
    gw.setStyleSheet("background:transparent;")
    gl = QGridLayout(gw)
    gl.setContentsMargins(*grid_margins)
    gl.setHorizontalSpacing(h_spacing)
    gl.setVerticalSpacing(v_spacing)

    for r, floor in enumerate(range(NUM_FLOORS, 0, -1)):
        floor_idx = floor - 1

        fl = QLabel(str(floor))
        fl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.setFixedSize(label_w, label_h)
        fl.setStyleSheet(
            f"color:{AppTheme.TEXT_GOLD}; font-size:12px; font-weight:bold; background:transparent;"
        )
        gl.addWidget(fl, r, 0)

        for c in range(NUM_COLS):
            cell = _Cell(floor_idx, c)
            if cell_size:
                cell.setFixedSize(*cell_size)
            cell.set_owner(page._owner[floor_idx][c])
            cell.clicked.connect(click_handler)
            cell_dict[(floor_idx, c)] = cell
            gl.addWidget(cell, r, c + 1)

    return gw


# ─────────────────────────────────────────
# 可拖曳標題列（浮動視窗用）
# ─────────────────────────────────────────

class _DragHeader(QFrame):
    """浮動視窗可拖曳標題列"""

    def __init__(self, parent_win: QWidget):
        super().__init__(parent_win)
        self._win      = parent_win
        self._offset   = QPoint()
        self._dragging = False

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._offset   = (
                event.globalPosition().toPoint()
                - self._win.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):  # noqa: N802
        if self._dragging:
            self._win.move(event.globalPosition().toPoint() - self._offset)

    def mouseReleaseEvent(self, event):  # noqa: N802
        self._dragging = False


# ─────────────────────────────────────────
# 浮動視窗
# ─────────────────────────────────────────

class RojaFloatWindow(QWidget):
    """羅茱工具浮動視窗 — 無邊框、置頂、可拖曳、可縮放"""

    _RESIZE_ZONE = 10

    def __init__(self, roja_page: "RojaPage", position: tuple = (200, 200)):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setMouseTracking(True)
        self.roja_page = roja_page

        self._resizing      = False
        self._resize_edge   = (False, False)
        self._resize_origin = QPoint()
        self._resize_size   = QSize()

        self._float_cells: dict[tuple, _Cell] = {}
        self._sel_btns:    list[QPushButton]   = []
        self._curr_lbl:    QLabel              = None

        self._build_ui()
        self.resize(220, 450)
        self.move(position[0], position[1])
        self.show()
        self.refresh()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(2, 2, 2, 2)
        outer.setSpacing(0)

        # ── Header ──
        hdr = _DragHeader(self)
        hdr.setFixedHeight(30)
        hdr.setStyleSheet(
            f"QFrame {{ background:{AppTheme.BG_SECONDARY};"
            f" border-bottom:1px solid {AppTheme.GOLD_MUTED}; }}"
        )
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(8, 2, 4, 2)
        hdr_lay.setSpacing(4)

        title = QLabel("⛩ 羅茱")
        title.setStyleSheet(
            f"color:{AppTheme.GOLD_LIGHT}; font-weight:bold; font-size:11px;"
            f" background:transparent; border:none;"
        )
        hdr_lay.addWidget(title)
        hdr_lay.addStretch()

        for i in range(NUM_PLAYERS):
            btn = QPushButton()
            btn.setFixedSize(20, 20)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(self.roja_page._player_names[i])
            btn.clicked.connect(lambda _, idx=i: self._select_player(idx))
            self._sel_btns.append(btn)
            hdr_lay.addWidget(btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 20)
        close_btn.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{AppTheme.TEXT_MUTED};"
            f" border:none; font-size:11px; }}"
            f"QPushButton:hover {{ background:{AppTheme.ACCENT_RED}; color:#fff; }}"
        )
        close_btn.clicked.connect(self._on_close)
        hdr_lay.addWidget(close_btn)
        outer.addWidget(hdr)

        # ── 當前玩家列 ──
        curr_bar = QFrame()
        curr_bar.setStyleSheet(
            f"QFrame {{ background:{AppTheme.BG_CARD}; border-bottom:1px solid {AppTheme.ROJA_CURR_BAR_BORDER}; }}"
        )
        curr_lay = QHBoxLayout(curr_bar)
        curr_lay.setContentsMargins(8, 3, 8, 3)
        self._curr_lbl = QLabel()
        self._curr_lbl.setStyleSheet("font-size:10px; font-weight:bold; background:transparent;")
        curr_lay.addWidget(self._curr_lbl)
        curr_lay.addStretch()
        copy_btn = QPushButton("📋 複製")
        copy_btn.setFixedHeight(22)
        copy_btn.setStyleSheet(
            f"QPushButton {{ background:transparent; border:1px solid {AppTheme.GOLD_MUTED}44;"
            f" border-radius:3px; font-size:10px; color:{AppTheme.TEXT_SECONDARY}; padding:0 4px; }}"
            f"QPushButton:hover {{ background:{AppTheme.BG_TERTIARY}; border-color:{AppTheme.GOLD_MUTED}; }}"
        )
        copy_btn.clicked.connect(
            lambda: self.roja_page._copy_player(self.roja_page._selected_player)
        )
        curr_lay.addWidget(copy_btn)
        reset_btn = QPushButton("🔄 重置")
        reset_btn.setFixedHeight(22)
        reset_btn.setStyleSheet(
            f"QPushButton {{ background:transparent; border:1px solid {AppTheme.ACCENT_RED}44;"
            f" border-radius:3px; font-size:10px; color:{AppTheme.ACCENT_RED}; padding:0 4px; }}"
            f"QPushButton:hover {{ background:{AppTheme.ACCENT_RED}22; border-color:{AppTheme.ACCENT_RED}; }}"
        )
        reset_btn.clicked.connect(
            lambda: self.roja_page._reset_player_idx(self.roja_page._selected_player)
        )
        curr_lay.addWidget(reset_btn)
        reset_all_btn = QPushButton("🗑 全部")
        reset_all_btn.setFixedHeight(22)
        reset_all_btn.setToolTip("清除所有玩家的進度")
        reset_all_btn.setStyleSheet(
            f"QPushButton {{ background:{AppTheme.ACCENT_RED}22; border:1px solid {AppTheme.ACCENT_RED}88;"
            f" border-radius:3px; font-size:10px; color:{AppTheme.ACCENT_RED}; padding:0 4px;"
            f" font-weight:bold; }}"
            f"QPushButton:hover {{ background:{AppTheme.ACCENT_RED}; color:#fff; }}"
        )
        reset_all_btn.clicked.connect(self.roja_page._reset_all)
        curr_lay.addWidget(reset_all_btn)
        outer.addWidget(curr_bar)

        # ── 格子 ──
        outer.addWidget(self._build_grid(), 1)

    def _build_grid(self) -> QWidget:
        w = QWidget(self)
        w.setStyleSheet(f"background:{AppTheme.BG_CARD};")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        gw = _make_cells_grid(
            self.roja_page,
            self._float_cells,
            self._on_cell_click,
            grid_margins=(10, 8, 10, 8),
            h_spacing=4,
            v_spacing=3,
            label_w=22,
            label_h=32,
            cell_size=(38, 32),
        )
        outer.addWidget(gw)
        return w

    def refresh(self):
        page = self.roja_page
        sel  = page._selected_player

        for (fi, ci), cell in self._float_cells.items():
            cell.set_owner(page._owner[fi][ci])

        for i, btn in enumerate(self._sel_btns):
            is_sel = (i == sel)
            btn.setToolTip(page._player_names[i])
            btn.setStyleSheet(
                f"QPushButton {{ background:{AppTheme.PLAYER_COLORS[i]}; border-radius:10px;"
                f" border:2px solid {AppTheme.GOLD_PRIMARY if is_sel else 'transparent'}; }}"
                f"QPushButton:hover {{ border-color:{AppTheme.GOLD_LIGHT}; }}"
            )

        color = AppTheme.PLAYER_COLORS[sel]
        name  = page._player_names[sel]
        self._curr_lbl.setText(f"▶ {name}")
        self._curr_lbl.setStyleSheet(
            f"color:{color}; font-size:10px; font-weight:bold; background:transparent;"
        )

    def _select_player(self, idx: int):
        self.roja_page._selected_player = idx
        self.roja_page._refresh_player_ui()
        self.refresh()

    def _on_cell_click(self, fi: int, ci: int):
        p       = self.roja_page._selected_player
        current = self.roja_page._owner[fi][ci]
        if current == p:
            self.roja_page._owner[fi][ci] = -1
        elif current == -1:
            # 清除同層舊選擇
            for old_ci in range(NUM_COLS):
                if self.roja_page._owner[fi][old_ci] == p:
                    self.roja_page._owner[fi][old_ci] = -1
            self.roja_page._owner[fi][ci] = p
        # else: 其他玩家 → 不操作
        self.roja_page._refresh_all()

    def _on_close(self):
        self.roja_page._float_win = None
        self.close()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(AppTheme.BG_CARD))
        painter.drawRect(self.rect())
        painter.setPen(QPen(QColor(AppTheme.GOLD_MUTED), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        sz   = 8
        x, y = self.width() - 1, self.height() - 1
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(AppTheme.GOLD_MUTED))
        painter.drawPolygon(QPolygon([QPoint(x - sz, y), QPoint(x, y - sz), QPoint(x, y)]))

    def _in_resize_zone(self, pos: QPoint):
        w, h = self.width(), self.height()
        return pos.x() >= w - self._RESIZE_ZONE, pos.y() >= h - self._RESIZE_ZONE

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            lpos          = event.position().toPoint()
            right, bottom = self._in_resize_zone(lpos)
            if right or bottom:
                self._resizing      = True
                self._resize_edge   = (right, bottom)
                self._resize_origin = event.globalPosition().toPoint()
                self._resize_size   = self.size()

    def mouseMoveEvent(self, event):  # noqa: N802
        lpos = event.position().toPoint()
        if self._resizing:
            delta = event.globalPosition().toPoint() - self._resize_origin
            r, b  = self._resize_edge
            self.resize(
                max(200, self._resize_size.width()  + (delta.x() if r else 0)),
                max(420, self._resize_size.height() + (delta.y() if b else 0)),
            )
        else:
            right, bottom = self._in_resize_zone(lpos)
            if right and bottom:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif right:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif bottom:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):  # noqa: N802
        self._resizing = False
        self.setCursor(Qt.CursorShape.ArrowCursor)


# ─────────────────────────────────────────
# 主頁面
# ─────────────────────────────────────────

class RojaPage(QWidget):
    """羅茱工具頁面 — 格子顯示數字，選中後變為玩家顏色，每層只能選一格"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app           = app
        self._player_names = ["1", "2", "3", "4"]
        self._selected_player = 0
        # _owner[floor][col] = player index (-1 = 空)
        self._owner: list[list[int]] = [
            [-1] * NUM_COLS for _ in range(NUM_FLOORS)
        ]
        self._float_win: "RojaFloatWindow | None" = None

        self._cells:       dict[tuple, _Cell]  = {}
        self._player_rows: list[QFrame]         = []
        self._player_dots: list[QLabel]         = []   # ▶ 選中指示標籤
        self._name_edits:  list[QLineEdit]      = []
        self._curr_lbl:    QLabel               = None

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 頂列 ──
        top_bar = QFrame()
        top_bar.setObjectName("roja_page_bar")
        top_bar.setStyleSheet(
            f"QFrame#roja_page_bar {{"
            f" background: {AppTheme.BG_SECONDARY};"
            f" border-bottom: 1px solid {AppTheme.GOLD_MUTED}; }}"
        )
        top_lay = QHBoxLayout(top_bar)
        top_lay.setContentsMargins(12, 6, 12, 6)
        top_lay.setSpacing(8)

        title = QLabel("⛩ 羅茱工具")
        title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {AppTheme.GOLD_LIGHT};"
            f" background: transparent; border: none;"
        )
        top_lay.addWidget(title)

        vsep = QFrame()
        vsep.setFrameShape(QFrame.Shape.VLine)
        vsep.setFixedHeight(20)
        vsep.setStyleSheet(f"background:{AppTheme.GOLD_MUTED}44;")
        top_lay.addWidget(vsep)

        self._curr_lbl = QLabel()
        self._curr_lbl.setFixedWidth(80)
        top_lay.addWidget(self._curr_lbl)

        copy_btn = QPushButton("📋 複製")
        copy_btn.clicked.connect(lambda: self._copy_player(self._selected_player))
        top_lay.addWidget(copy_btn)

        reset_btn = QPushButton("🔄 重置")
        reset_btn.setStyleSheet(
            f"QPushButton {{ background:{AppTheme.BG_TERTIARY}; color:{AppTheme.ACCENT_RED};"
            f" border:1px solid {AppTheme.ACCENT_RED}55; border-radius:4px; padding:2px 8px; }}"
            f"QPushButton:hover {{ background:{AppTheme.ACCENT_RED}; color:#fff; }}"
        )
        reset_btn.clicked.connect(lambda: self._reset_player_idx(self._selected_player))
        top_lay.addWidget(reset_btn)

        reset_all_btn = QPushButton("🗑 全部重置")
        reset_all_btn.setToolTip("清除所有玩家的進度")
        reset_all_btn.setStyleSheet(
            f"QPushButton {{ background:{AppTheme.ACCENT_RED}22; color:{AppTheme.ACCENT_RED};"
            f" border:1px solid {AppTheme.ACCENT_RED}88; border-radius:4px; padding:2px 8px;"
            f" font-weight:bold; }}"
            f"QPushButton:hover {{ background:{AppTheme.ACCENT_RED}; color:#fff; }}"
        )
        reset_all_btn.clicked.connect(self._reset_all)
        top_lay.addWidget(reset_all_btn)

        top_lay.addStretch()

        root.addWidget(top_bar)

        # ── 主內容（上下左右置中）──
        content = QWidget()
        content.setStyleSheet(f"background:{AppTheme.BG_PRIMARY};")
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(24, 24, 24, 24)
        content_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 玩家列表 + 格子並排，各自高度自適應，頂部對齊
        center_row = QHBoxLayout()
        center_row.setSpacing(16)
        center_row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        center_row.addWidget(self._build_player_panel())
        center_row.addWidget(self._build_grid_container())

        content_lay.addLayout(center_row)
        root.addWidget(content, 1)

        self._refresh_player_ui()

    def _build_player_panel(self) -> QFrame:
        """建構玩家選擇面板（左側）— 固定寬度，每列含選擇 + 複製按鈕"""
        # ▶(14) + name(90) + 選擇(52) + 複製(62) + gaps(6×3) + row-margins(8×2) + panel-margins(10×2)
        _PANEL_W = 14 + 90 + 52 + 62 + 18 + 16 + 20   # = 272
        panel = QFrame()
        panel.setObjectName("roja_player_panel")
        panel.setFixedWidth(_PANEL_W)
        panel.setStyleSheet(
            f"QFrame#roja_player_panel {{"
            f" background:{AppTheme.BG_CARD};"
            f" border:1px solid {AppTheme.GOLD_MUTED}55;"
            f" border-radius:12px;"
            f"}}"
        )
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        hdr = QLabel("玩 家")
        hdr.setStyleSheet(
            f"color:{AppTheme.TEXT_MUTED}; font-size:10px;"
            f" font-weight:bold; letter-spacing:2px; background:transparent;"
        )
        lay.addWidget(hdr)

        for i in range(NUM_PLAYERS):
            row = QFrame()
            row.setObjectName(f"player_row_{i}")
            self._player_rows.append(row)

            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(8, 6, 8, 6)
            row_lay.setSpacing(6)

            # ▶ 選中指示（純 label，不可點擊）
            sel_lbl = QLabel()
            sel_lbl.setFixedSize(14, 26)
            sel_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sel_lbl.setObjectName(f"sel_lbl_{i}")
            sel_lbl.setStyleSheet(
                "color:#d4a843; font-size:13px; font-weight:bold; background:transparent;"
            )
            self._player_dots.append(sel_lbl)
            row_lay.addWidget(sel_lbl)

            # 名稱輸入（固定寬度）
            name_edit = QLineEdit(self._player_names[i])
            name_edit.setPlaceholderText(f"玩家 {i + 1}")
            name_edit.setFixedWidth(90)
            name_edit.setFixedHeight(30)
            name_edit.setStyleSheet(
                f"QLineEdit {{ background:{AppTheme.BG_TERTIARY};"
                f" color:{AppTheme.PLAYER_COLORS[i]}; font-weight:bold;"
                f" border:1px solid {AppTheme.PLAYER_COLORS[i]}44;"
                f" border-radius:4px; padding:2px 6px; font-size:13px; }}"
                f"QLineEdit:focus {{ border:1px solid {AppTheme.PLAYER_COLORS[i]}; }}"
            )
            name_edit.textChanged.connect(
                lambda text, idx=i: self._on_name_changed(idx, text)
            )
            self._name_edits.append(name_edit)
            row_lay.addWidget(name_edit)

            # 選擇按鈕
            pick_btn = QPushButton("▶ 選擇")
            pick_btn.setFixedSize(52, 30)
            pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pick_btn.setToolTip(f"選擇玩家 {i + 1} 為當前操作對象")
            pick_btn.setStyleSheet(
                f"QPushButton {{ background:{AppTheme.BG_TERTIARY};"
                f" color:{AppTheme.PLAYER_COLORS[i]}; font-size:11px; font-weight:bold;"
                f" border:1px solid {AppTheme.PLAYER_COLORS[i]}44; border-radius:4px; }}"
                f"QPushButton:hover {{ background:{AppTheme.PLAYER_COLORS[i]}33;"
                f" border-color:{AppTheme.PLAYER_COLORS[i]}; }}"
            )
            pick_btn.clicked.connect(lambda _, idx=i: self._select_player(idx))
            row_lay.addWidget(pick_btn)

            # 複製按鈕
            copy_btn = QPushButton("📋 複製")
            copy_btn.setFixedSize(62, 30)
            copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            copy_btn.setToolTip(f"複製玩家 {i + 1} 的進度")
            copy_btn.setStyleSheet(
                f"QPushButton {{ background:transparent;"
                f" color:{AppTheme.TEXT_SECONDARY};"
                f" border:1px solid {AppTheme.GOLD_MUTED}44;"
                f" border-radius:4px; font-size:11px; }}"
                f"QPushButton:hover {{ background:{AppTheme.BG_TERTIARY};"
                f" border-color:{AppTheme.GOLD_MUTED}; color:{AppTheme.TEXT_PRIMARY}; }}"
            )
            copy_btn.clicked.connect(lambda _, idx=i: self._copy_player(idx))
            row_lay.addWidget(copy_btn)

            lay.addWidget(row)

        return panel

    def _build_grid_container(self) -> QFrame:
        """建構格子容器（圓角卡片，固定寬度）"""
        container_w = (
            14 * 2
            + 26 + 5
            + _Cell._CELL_W * NUM_COLS + 5 * (NUM_COLS - 1)
        )
        container = QFrame()
        container.setObjectName("roja_grid_container")
        container.setFixedWidth(container_w)
        container.setStyleSheet(
            f"QFrame#roja_grid_container {{"
            f" background:{AppTheme.BG_CARD};"
            f" border:1px solid {AppTheme.GOLD_MUTED}55;"
            f" border-radius:12px;"
            f"}}"
        )
        ct_lay = QVBoxLayout(container)
        ct_lay.setContentsMargins(14, 8, 14, 12)
        ct_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 浮動視窗按鈕（右上角）
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        float_btn = QPushButton("🎮 浮動視窗")
        float_btn.setToolTip("開啟 / 關閉浮動視窗（遊戲中使用）")
        float_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        float_btn.clicked.connect(self._toggle_float)
        btn_row.addWidget(float_btn)
        ct_lay.addLayout(btn_row)

        gw = _make_cells_grid(
            self,
            self._cells,
            self._on_cell_click,
        )
        ct_lay.addWidget(gw)
        return container

    # ── 動作處理 ──

    def _select_player(self, idx: int):
        self._selected_player = idx
        self._refresh_player_ui()
        if self._float_win and self._float_win.isVisible():
            self._float_win.refresh()

    def _on_cell_click(self, fi: int, ci: int):
        """點擊格子：
        - 當前玩家已選此格 → 取消
        - 格子為空 → 歸屬當前玩家（自動清除同層舊選擇）
        - 其他玩家擁有 → 不操作
        """
        p       = self._selected_player
        current = self._owner[fi][ci]

        if current == p:
            self._owner[fi][ci] = -1
        elif current == -1:
            # 清除同層舊選擇
            for old_ci in range(NUM_COLS):
                if self._owner[fi][old_ci] == p:
                    self._owner[fi][old_ci] = -1
            self._owner[fi][ci] = p
        # else: 其他玩家的格子 → 不操作

        self._refresh_all()

    def _on_name_changed(self, idx: int, text: str):
        name = text.strip() or str(idx + 1)
        self._player_names[idx] = name
        if idx == self._selected_player:
            self._refresh_curr_label()
        if self._float_win and self._float_win.isVisible():
            self._float_win.refresh()

    def _copy_player(self, idx: int):
        """複製指定玩家的進度

        格式：各層選擇的數字依序排列，每 4 層一組空格分隔
        例如：「1234 2341 12」
        """
        digits = []
        for fi in range(NUM_FLOORS):
            for ci in range(NUM_COLS):
                if self._owner[fi][ci] == idx:
                    digits.append(str(ci + 1))
                    break

        if not digits:
            msg = "（尚無進度）"
        else:
            groups = ["".join(digits[i:i + 4]) for i in range(0, len(digits), 4)]
            msg = " ".join(groups)

        QApplication.clipboard().setText(msg)
        if hasattr(self.app, "toast") and self.app.toast:
            self.app.toast.show(f"已複製 {self._player_names[idx]} 的進度")

    def _reset_player_idx(self, idx: int):
        """重置指定玩家進度"""
        for fi in range(NUM_FLOORS):
            for ci in range(NUM_COLS):
                if self._owner[fi][ci] == idx:
                    self._owner[fi][ci] = -1
        self._refresh_all()

    def _reset_all(self):
        """重置所有玩家進度"""
        for fi in range(NUM_FLOORS):
            for ci in range(NUM_COLS):
                self._owner[fi][ci] = -1
        self._refresh_all()

    def _toggle_float(self):
        if self._float_win is not None and self._float_win.isVisible():
            self._float_win.close()
            self._float_win = None
            return
        self._float_win = None
        geo = self.app.geometry()
        self._float_win = RojaFloatWindow(
            self, position=(geo.right() + 10, geo.top() + 50)
        )

    # ── 刷新 ──

    def _refresh_all(self):
        for (fi, ci), cell in self._cells.items():
            cell.set_owner(self._owner[fi][ci])
        if self._float_win and self._float_win.isVisible():
            self._float_win.refresh()

    def _refresh_player_ui(self):
        sel = self._selected_player
        for i in range(NUM_PLAYERS):
            is_sel = (i == sel)

            # ▶ 指示 label：選中顯示，未選中隱藏
            lbl = self._player_dots[i]
            lbl.setText("▶" if is_sel else "")

            # 列框線：選中時加玩家顏色細邊框
            self._player_rows[i].setStyleSheet(
                f"QFrame {{ background:{AppTheme.ROJA_PLAYER_ROW_SEL_BG if is_sel else 'transparent'};"
                f" border:{'1px solid ' + AppTheme.PLAYER_COLORS[i] + '66' if is_sel else '1px solid transparent'};"
                f" border-radius:6px; }}"
            )
        self._refresh_curr_label()

    def _refresh_curr_label(self):
        if self._curr_lbl is None:
            return
        sel   = self._selected_player
        color = AppTheme.PLAYER_COLORS[sel]
        name  = self._player_names[sel]
        self._curr_lbl.setText(f"▶ {name}")
        self._curr_lbl.setStyleSheet(
            f"color:{color}; font-size:11px; font-weight:bold;"
        )
