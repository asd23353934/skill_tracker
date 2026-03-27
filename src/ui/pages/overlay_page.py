"""
畫面覆蓋圖片管理頁面 — PySide6 版本
以卡片列表管理浮動圖片視窗（支援靜態圖片與 GIF）
Phase 5 實作完整版本
"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QFileDialog, QMessageBox,
    QSlider, QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from src.ui.theme import AppTheme
from src.infrastructure.helpers import user_data_path

# 支援的圖片格式過濾字串（Qt 格式）
_SUPPORTED_FILTER = "圖片與 GIF (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;所有檔案 (*.*)"


class _OverlayCardStub(QFrame):
    """覆蓋圖片卡片（Phase 5 將替換為完整實作）"""

    _CARD_H = 138

    def __init__(self, parent, data: dict, app, page):
        super().__init__(parent)
        self.data       = data
        self.app        = app
        self.page       = page
        self.overlay_id = data["id"]

        self.setFixedHeight(self._CARD_H)
        self.setStyleSheet(
            f"QFrame {{"
            f" background-color: {AppTheme.BG_CARD};"
            f" border: 1px solid {AppTheme.BORDER_GOLD_SUBTLE};"
            f" border-radius: {AppTheme.CORNER_MD}px; }}"
        )
        self._build_ui()

    def _build_ui(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(10)

        # 縮圖：讀取實際圖片（支援 PNG / JPG / GIF 首幀）
        thumb_lbl = QLabel()
        thumb_lbl.setFixedSize(90, 90)
        thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_lbl.setStyleSheet(
            f"background: {AppTheme.BG_SECONDARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: 4px;"
        )
        image_path = user_data_path(f"overlays/{self.data.get('file', '')}")
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            thumb_lbl.setPixmap(
                pixmap.scaled(88, 88,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
            )
        else:
            thumb_lbl.setText("🖼️")
            thumb_lbl.setStyleSheet(
                thumb_lbl.styleSheet()
                + f" font-size: 30px; color: {AppTheme.TEXT_MUTED};"
            )
        row.addWidget(thumb_lbl)

        # 右側資訊 + 控制
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        name_lbl = QLabel(self.data.get("name", "未命名"))
        name_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        right_layout.addWidget(name_lbl)

        file_lbl = QLabel(self.data.get("file", ""))
        file_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 10px;"
            f" background: transparent; border: none;"
        )
        right_layout.addWidget(file_lbl)

        # 控制列
        ctrl = QWidget()
        ctrl.setStyleSheet("background: transparent;")
        ctrl_layout = QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(8)

        is_open = self.overlay_id in self.app.overlay_manager.active_windows
        self._toggle_btn = QPushButton("● 顯示中" if is_open else "○ 已隱藏")
        self._toggle_btn.setFixedHeight(26)
        self._toggle_btn.clicked.connect(self._toggle)
        self._toggle_btn.setStyleSheet(
            f"QPushButton {{"
            f" background-color: {AppTheme.ACCENT_GREEN if is_open else AppTheme.BG_TERTIARY};"
            f" color: white; border: none; border-radius: 4px;"
            f" padding: 2px 8px; font-size: 10px; font-weight: bold; }}"
        )
        ctrl_layout.addWidget(self._toggle_btn)

        # 透明度滑桿
        alpha_val = self.data.get("alpha", 0.9)
        self._alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self._alpha_slider.setRange(10, 100)
        self._alpha_slider.setValue(int(alpha_val * 100))
        self._alpha_slider.setFixedWidth(100)
        self._alpha_slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ background: {AppTheme.BG_TERTIARY};"
            f" height: 4px; border-radius: 2px; }}"
            f"QSlider::handle:horizontal {{ background: {AppTheme.GOLD_PRIMARY};"
            f" width: 12px; height: 12px; border-radius: 6px; margin: -4px 0; }}"
            f"QSlider::sub-page:horizontal {{ background: {AppTheme.GOLD_DARK}; border-radius: 2px; }}"
        )
        self._alpha_slider.valueChanged.connect(self._on_alpha)
        ctrl_layout.addWidget(self._alpha_slider)

        self._alpha_lbl = QLabel(f"{int(alpha_val * 100)}%")
        self._alpha_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 10px;"
            f" background: transparent; border: none;"
        )
        ctrl_layout.addWidget(self._alpha_lbl)

        # 刪除按鈕
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(28, 26)
        del_btn.clicked.connect(self._delete)
        del_btn.setStyleSheet(
            f"QPushButton {{ background: {AppTheme.BG_TERTIARY}; border: none;"
            f" border-radius: 4px; font-size: 12px; color: {AppTheme.TEXT_MUTED}; }}"
            f"QPushButton:hover {{ background: {AppTheme.ACCENT_RED}; color: white; }}"
        )
        ctrl_layout.addWidget(del_btn)
        ctrl_layout.addStretch()

        right_layout.addWidget(ctrl)
        right_layout.addStretch()
        row.addWidget(right)

    def _toggle(self):
        self.app.overlay_manager.toggle(self.overlay_id)
        self._sync_toggle()

    def _on_alpha(self, value: int):
        alpha = value / 100.0
        self._alpha_lbl.setText(f"{value}%")
        self.app.overlay_manager.set_alpha(self.overlay_id, alpha)

    def _delete(self):
        name = self.data.get("name", "此圖片")
        reply = QMessageBox.question(
            self, "刪除確認",
            f"確定要刪除「{name}」嗎？\n（僅移除設定，不刪除圖片檔案）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.app.overlay_manager.delete_overlay(self.overlay_id, delete_file=False)
            self.page.rebuild_cards()

    def _sync_toggle(self):
        is_open = self.overlay_id in self.app.overlay_manager.active_windows
        self._toggle_btn.setText("● 顯示中" if is_open else "○ 已隱藏")
        self._toggle_btn.setStyleSheet(
            f"QPushButton {{"
            f" background-color: {AppTheme.ACCENT_GREEN if is_open else AppTheme.BG_TERTIARY};"
            f" color: white; border: none; border-radius: 4px;"
            f" padding: 2px 8px; font-size: 10px; font-weight: bold; }}"
        )

    def sync_toggle_state(self):
        """從外部同步 toggle 按鈕狀態"""
        self._sync_toggle()


class OverlayPage(QWidget):
    """畫面覆蓋圖片管理頁面"""

    def __init__(self, parent, app):
        """初始化覆蓋頁

        Args:
            parent: 父元件
            app:    App 主應用實例
        """
        super().__init__(parent)
        self.app    = app
        self._cards: dict = {}   # overlay_id → _OverlayCardStub
        self._build_ui()

    def _build_ui(self):
        """建構頁面 UI"""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── 頂部標題列 ──
        hdr = QFrame()
        hdr.setObjectName("overlay_page_bar")
        hdr.setStyleSheet(
            f"QFrame#overlay_page_bar {{"
            f" background: {AppTheme.BG_SECONDARY};"
            f" border-bottom: 1px solid {AppTheme.GOLD_MUTED}; }}"
        )
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(12, 6, 12, 6)
        hdr_layout.setSpacing(8)

        title_lbl = QLabel("🖼️ 畫面覆蓋圖片")
        title_lbl.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT}; font-size: 14px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        hdr_layout.addWidget(title_lbl)

        hint_lbl = QLabel("支援 PNG / JPG / GIF（動畫）| 拖曳移動 | hover 顯示 X 關閉")
        hint_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 11px;"
            f" background: transparent; border: none;"
        )
        hdr_layout.addWidget(hint_lbl)

        hdr_layout.addStretch()

        add_btn = QPushButton("＋ 新增圖片")
        add_btn.setFixedHeight(28)
        add_btn.clicked.connect(self._add_image)
        add_btn.setStyleSheet(
            f"QPushButton {{"
            f" background: {AppTheme.GOLD_PRIMARY}; color: {AppTheme.BG_DEEP};"
            f" border: none; border-radius: 4px;"
            f" padding: 0 12px; font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {AppTheme.GOLD_LIGHT}; }}"
        )
        hdr_layout.addWidget(add_btn)

        outer.addWidget(hdr)

        # ── 可捲動卡片區 ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )

        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: transparent;")
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(10, 10, 10, 10)
        self._scroll_layout.setSpacing(6)
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._scroll_content)
        outer.addWidget(self._scroll)

        self.rebuild_cards()

    def rebuild_cards(self):
        """清除並重建所有覆蓋圖片卡片"""
        # 清除現有卡片
        while self._scroll_layout.count():
            item = self._scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        overlays = self.app.overlay_manager.get_all()

        if not overlays:
            empty_lbl = QLabel(
                "尚未新增任何圖片\n點擊「＋ 新增圖片」上傳 PNG / JPG / GIF"
            )
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet(
                f"color: {AppTheme.TEXT_MUTED}; font-size: 14px; background: transparent;"
            )
            self._scroll_layout.addWidget(empty_lbl)
            return

        for data in overlays:
            card = _OverlayCardStub(self._scroll_content, data, self.app, self)
            self._scroll_layout.addWidget(card)
            self._cards[data["id"]] = card

    def _add_image(self):
        """開啟檔案選擇對話框，上傳圖片"""
        path, _ = QFileDialog.getOpenFileName(
            self, "選擇圖片或 GIF", "", _SUPPORTED_FILTER
        )
        if not path:
            return

        name = os.path.splitext(os.path.basename(path))[0]
        item = self.app.overlay_manager.add_overlay(path, name)
        if item is None:
            self.app.toast.show("上傳失敗，不支援的圖片格式或檔案複製失敗。", "error")
            return

        self.rebuild_cards()

    def refresh_toggle(self, overlay_id: str):
        """視窗被 X 關閉時，更新對應卡片的 toggle 按鈕狀態

        Args:
            overlay_id: 被關閉視窗的 overlay ID
        """
        card = self._cards.get(overlay_id)
        if card:
            card.sync_toggle_state()
