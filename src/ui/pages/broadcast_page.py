"""
頻道廣播頁面 — PySide6 版本
即時監控 Artale 遊戲頻道廣播訊息，支援篩選、黑名單、FriendTag 複製
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QCheckBox, QComboBox, QLineEdit,
    QMenu, QApplication, QSizePolicy,
)
from PySide6.QtCore import Qt

from src.ui.theme import AppTheme


class _MessageCard(QFrame):
    """單一訊息卡片"""

    def __init__(self, parent, msg, page):
        """初始化訊息卡片

        Args:
            parent: 父元件
            msg:    BroadcastMessage 實例
            page:   BroadcastPage 實例（用於操作回呼）
        """
        super().__init__(parent)
        self.msg = msg
        self.page = page
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("broadcast_card")
        self.setStyleSheet(
            f"QFrame#broadcast_card {{"
            f" background-color: {AppTheme.BG_CARD};"
            f" border: 1px solid {AppTheme.BORDER_GOLD_SUBTLE};"
            f" border-radius: 6px; }}"
            f"QFrame#broadcast_card:hover {{"
            f" background-color: {AppTheme.BG_CARD_HOVER}; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        # 頻道標籤
        if self.msg.channel:
            ch_label = QLabel(self.msg.channel)
            ch_label.setFixedWidth(60)
            ch_label.setStyleSheet(
                f"color: {AppTheme.ACCENT_BLUE};"
                f" font-size: 11px;"
                f" font-weight: bold;"
                f" font-family: {AppTheme.FONT_FAMILY};"
                f" background: transparent;"
            )
            layout.addWidget(ch_label)

        # 暱稱
        nick_label = QLabel(self.msg.nickname)
        nick_label.setFixedWidth(100)
        nick_label.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT};"
            f" font-size: 12px;"
            f" font-weight: bold;"
            f" font-family: {AppTheme.FONT_FAMILY};"
            f" background: transparent;"
        )
        nick_label.setToolTip(self.msg.friend_tag)
        layout.addWidget(nick_label)

        # 訊息內容
        text_label = QLabel(self.msg.text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(
            f"color: {AppTheme.TEXT_PRIMARY};"
            f" font-size: 12px;"
            f" font-family: {AppTheme.FONT_FAMILY};"
            f" background: transparent;"
        )
        text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(text_label)

        # 時間戳
        time_label = QLabel(self.msg.timestamp)
        time_label.setFixedWidth(120)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_label.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED};"
            f" font-size: 10px;"
            f" font-family: {AppTheme.FONT_FAMILY};"
            f" background: transparent;"
        )
        layout.addWidget(time_label)

        # 複製 FriendTag 按鈕
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(28, 28)
        copy_btn.setToolTip("複製 FriendTag")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(
            f"QPushButton {{"
            f" background: transparent;"
            f" border: 1px solid {AppTheme.BORDER_GOLD_SUBTLE};"
            f" border-radius: 4px;"
            f" font-size: 13px; }}"
            f"QPushButton:hover {{"
            f" background: {AppTheme.BG_TERTIARY}; }}"
        )
        copy_btn.clicked.connect(lambda: self.page._copy_friend_tag(self.msg))
        layout.addWidget(copy_btn)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        """右鍵選單"""
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{"
            f" background-color: {AppTheme.BG_SECONDARY};"
            f" color: {AppTheme.TEXT_PRIMARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; }}"
            f"QMenu::item:selected {{"
            f" background-color: {AppTheme.BG_TERTIARY}; }}"
        )
        copy_action = menu.addAction("📋 複製 FriendTag")
        blacklist_action = menu.addAction("🚫 加入黑名單")

        action = menu.exec(self.mapToGlobal(pos))
        if action == copy_action:
            self.page._copy_friend_tag(self.msg)
        elif action == blacklist_action:
            self.page._add_to_blacklist(self.msg)


class BroadcastPage(QWidget):
    """頻道廣播頁面"""

    def __init__(self, parent, app):
        """初始化頁面

        Args:
            parent: 父元件（QStackedWidget）
            app:    App 主應用實例
        """
        super().__init__(parent)
        self.app = app
        self._cards: list[_MessageCard] = []
        self._current_filter = ""  # 空字串 = 全部
        self._build_ui()

    def _build_ui(self):
        """建構頁面 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)

        # ===== 頂部控制列 =====
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        # 標題
        title = QLabel("📡 頻道廣播")
        title.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT};"
            f" font-size: 16px;"
            f" font-weight: bold;"
            f" font-family: {AppTheme.FONT_FAMILY};"
        )
        ctrl_row.addWidget(title)
        ctrl_row.addSpacing(12)

        # 啟動/暫停按鈕
        self._start_btn = QPushButton("▶ 啟動")
        self._start_btn.setFixedHeight(30)
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.setStyleSheet(self._btn_style(AppTheme.ACCENT_GREEN, AppTheme.ACCENT_GREEN_HOVER))
        self._start_btn.clicked.connect(self._toggle_capture)
        ctrl_row.addWidget(self._start_btn)

        # 清除按鈕
        clear_btn = QPushButton("🗑 清除")
        clear_btn.setFixedHeight(30)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(self._btn_style(AppTheme.ACCENT_RED, AppTheme.ACCENT_RED_HOVER))
        clear_btn.clicked.connect(self._clear_messages)
        ctrl_row.addWidget(clear_btn)

        ctrl_row.addSpacing(12)

        # 自動啟動勾選
        self._auto_start_cb = QCheckBox("自動啟動")
        self._auto_start_cb.setStyleSheet(
            f"QCheckBox {{"
            f" color: {AppTheme.TEXT_SECONDARY};"
            f" font-size: 12px;"
            f" font-family: {AppTheme.FONT_FAMILY}; }}"
            f"QCheckBox::indicator {{"
            f" width: 14px; height: 14px; }}"
        )
        auto_start = self.app.config_manager.get_settings("broadcast_auto_start", False)
        self._auto_start_cb.setChecked(auto_start)
        self._auto_start_cb.stateChanged.connect(self._on_auto_start_changed)
        ctrl_row.addWidget(self._auto_start_cb)

        ctrl_row.addStretch()

        # 訊息計數
        self._count_label = QLabel("0 則訊息")
        self._count_label.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED};"
            f" font-size: 11px;"
            f" font-family: {AppTheme.FONT_FAMILY};"
        )
        ctrl_row.addWidget(self._count_label)

        main_layout.addLayout(ctrl_row)

        # ===== 篩選列 =====
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        filter_label = QLabel("分類：")
        filter_label.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY};"
            f" font-size: 12px;"
            f" font-family: {AppTheme.FONT_FAMILY};"
        )
        filter_row.addWidget(filter_label)

        self._filter_combo = QComboBox()
        self._filter_combo.setFixedHeight(28)
        self._filter_combo.setMinimumWidth(120)
        self._filter_combo.setStyleSheet(
            f"QComboBox {{"
            f" background: {AppTheme.BG_TERTIARY};"
            f" color: {AppTheme.TEXT_PRIMARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 4px;"
            f" padding: 2px 8px;"
            f" font-family: {AppTheme.FONT_FAMILY};"
            f" font-size: 12px; }}"
            f"QComboBox::drop-down {{"
            f" border: none; }}"
            f"QComboBox QAbstractItemView {{"
            f" background: {AppTheme.BG_SECONDARY};"
            f" color: {AppTheme.TEXT_PRIMARY};"
            f" selection-background-color: {AppTheme.BG_TERTIARY}; }}"
        )
        self._filter_combo.addItem("全部")
        # 載入已存的關鍵字
        keywords = self.app.config_manager.get_settings("broadcast_keywords", [])
        for kw in keywords:
            self._filter_combo.addItem(kw)
        self._filter_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self._filter_combo)

        # 新增關鍵字
        self._keyword_input = QLineEdit()
        self._keyword_input.setFixedHeight(28)
        self._keyword_input.setFixedWidth(120)
        self._keyword_input.setPlaceholderText("新增關鍵字...")
        self._keyword_input.setStyleSheet(
            f"QLineEdit {{"
            f" background: {AppTheme.BG_TERTIARY};"
            f" color: {AppTheme.TEXT_PRIMARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 4px;"
            f" padding: 2px 8px;"
            f" font-family: {AppTheme.FONT_FAMILY};"
            f" font-size: 12px; }}"
        )
        self._keyword_input.returnPressed.connect(self._add_keyword)
        filter_row.addWidget(self._keyword_input)

        add_kw_btn = QPushButton("＋")
        add_kw_btn.setFixedSize(28, 28)
        add_kw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_kw_btn.setStyleSheet(self._btn_style(AppTheme.ACCENT_BLUE, "#2563eb"))
        add_kw_btn.clicked.connect(self._add_keyword)
        filter_row.addWidget(add_kw_btn)

        del_kw_btn = QPushButton("－")
        del_kw_btn.setFixedSize(28, 28)
        del_kw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_kw_btn.setToolTip("刪除目前選取的關鍵字")
        del_kw_btn.setStyleSheet(self._btn_style(AppTheme.ACCENT_RED, AppTheme.ACCENT_RED_HOVER))
        del_kw_btn.clicked.connect(self._remove_keyword)
        filter_row.addWidget(del_kw_btn)

        filter_row.addStretch()

        # 黑名單管理按鈕
        blacklist_btn = QPushButton("🚫 黑名單管理")
        blacklist_btn.setFixedHeight(28)
        blacklist_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        blacklist_btn.setStyleSheet(self._btn_style(AppTheme.ACCENT_ORANGE, AppTheme.ACCENT_ORANGE_HOVER))
        blacklist_btn.clicked.connect(self._show_blacklist_dialog)
        filter_row.addWidget(blacklist_btn)

        main_layout.addLayout(filter_row)

        # ===== 分隔線 =====
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {AppTheme.BORDER_GOLD_HAIRLINE};")
        main_layout.addWidget(sep)

        # ===== 訊息列表 =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{"
            f" background: transparent;"
            f" border: none; }}"
            f"QScrollBar:vertical {{"
            f" background: {AppTheme.BG_DEEP};"
            f" width: 8px;"
            f" border-radius: 4px; }}"
            f"QScrollBar::handle:vertical {{"
            f" background: {AppTheme.GOLD_MUTED};"
            f" border-radius: 4px;"
            f" min-height: 30px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{"
            f" height: 0px; }}"
        )

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_widget)
        main_layout.addWidget(scroll)

    # --------------------------------------------------
    # 控制列操作
    # --------------------------------------------------

    def _toggle_capture(self):
        """切換啟動/暫停"""
        mgr = self.app.broadcast_manager

        if mgr.is_running:
            mgr.stop()
            self._start_btn.setText("▶ 啟動")
            self._start_btn.setStyleSheet(
                self._btn_style(AppTheme.ACCENT_GREEN, AppTheme.ACCENT_GREEN_HOVER)
            )
        else:
            self._try_start()

    def _try_start(self):
        """嘗試啟動（含免責聲明檢查）"""
        accepted = self.app.config_manager.get_settings("broadcast_disclaimer_accepted", False)
        if not accepted:
            from src.ui.dialogs.broadcast_disclaimer_dialog import BroadcastDisclaimerDialog
            dlg = BroadcastDisclaimerDialog(self.app)
            dlg.exec()
            if not dlg.accepted:
                return
            self.app.config_manager.set_settings("broadcast_disclaimer_accepted", True)
            self.app.config_manager.save()

        self._do_start()

    def _do_start(self):
        """執行啟動"""
        mgr = self.app.broadcast_manager
        err = mgr.start()
        if err:
            self.app.toast.show(err, "error")
            return
        self._start_btn.setText("⏸ 暫停")
        self._start_btn.setStyleSheet(
            self._btn_style(AppTheme.ACCENT_YELLOW, AppTheme.ACCENT_YELLOW_HOVER)
        )

    def _clear_messages(self):
        """清除所有訊息"""
        self.app.broadcast_manager.clear()
        # 清除 UI 卡片
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        self._update_count()

    def _on_auto_start_changed(self, state):
        """自動啟動勾選變更"""
        checked = state == Qt.CheckState.Checked.value
        self.app.config_manager.set_settings("broadcast_auto_start", checked)
        self.app.config_manager.save()

    # --------------------------------------------------
    # 篩選
    # --------------------------------------------------

    def _on_filter_changed(self, text):
        """篩選條件變更"""
        self._current_filter = "" if text == "全部" else text
        self._rebuild_list()

    def _add_keyword(self):
        """新增關鍵字"""
        kw = self._keyword_input.text().strip()
        if not kw:
            return
        # 檢查重複
        keywords = self.app.config_manager.get_settings("broadcast_keywords", [])
        if kw in keywords:
            self._keyword_input.clear()
            return
        keywords.append(kw)
        self.app.config_manager.set_settings("broadcast_keywords", keywords)
        self.app.config_manager.save()
        self._filter_combo.addItem(kw)
        self._keyword_input.clear()

    def _remove_keyword(self):
        """刪除目前選取的關鍵字"""
        current = self._filter_combo.currentText()
        if current == "全部":
            return
        keywords = self.app.config_manager.get_settings("broadcast_keywords", [])
        if current in keywords:
            keywords.remove(current)
            self.app.config_manager.set_settings("broadcast_keywords", keywords)
            self.app.config_manager.save()
        idx = self._filter_combo.currentIndex()
        self._filter_combo.removeItem(idx)
        self._filter_combo.setCurrentIndex(0)

    # --------------------------------------------------
    # 訊息處理
    # --------------------------------------------------

    def on_new_message(self, msg):
        """收到新訊息回呼（由 BroadcastManager 在主執行緒呼叫）"""
        # 篩選檢查
        if self._current_filter and self._current_filter not in msg.text:
            # 訊息仍保留在 manager 中，只是不顯示
            pass
        else:
            self._add_card(msg)

        self._update_count()

    def _add_card(self, msg):
        """新增訊息卡片至列表"""
        card = _MessageCard(self._list_widget, msg, self)
        # 插入到 stretch 之前
        count = self._list_layout.count()
        self._list_layout.insertWidget(count - 1, card)
        self._cards.append(card)

        # UI 上的訊息上限
        max_msgs = self.app.config_manager.get_settings("broadcast_max_messages", 200)
        while len(self._cards) > max_msgs:
            old = self._cards.pop(0)
            old.setParent(None)
            old.deleteLater()

    def _rebuild_list(self):
        """依篩選條件重建訊息列表"""
        # 清除現有卡片
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        # 從 manager 重新載入
        for msg in self.app.broadcast_manager.messages:
            if self._current_filter and self._current_filter not in msg.text:
                continue
            if self.app.broadcast_manager.is_blacklisted(msg.friend_tag):
                continue
            self._add_card(msg)

        self._update_count()

    def _update_count(self):
        """更新訊息計數"""
        self._count_label.setText(f"{len(self._cards)} 則訊息")

    # --------------------------------------------------
    # FriendTag / 黑名單
    # --------------------------------------------------

    def _copy_friend_tag(self, msg):
        """複製 FriendTag 至剪貼簿"""
        clipboard = QApplication.clipboard()
        clipboard.setText(msg.friend_tag)
        self.app.toast.show(f"已複製 {msg.friend_tag}", "success")

    def _add_to_blacklist(self, msg):
        """加入黑名單"""
        self.app.broadcast_manager.add_to_blacklist(msg.friend_tag)
        self.app.toast.show(f"已將 {msg.friend_tag} 加入黑名單", "success")
        self._rebuild_list()

    def _show_blacklist_dialog(self):
        """顯示黑名單管理對話框"""
        from src.ui.dialogs.broadcast_blacklist_dialog import BroadcastBlacklistDialog
        dlg = BroadcastBlacklistDialog(self.app, self)
        dlg.exec()
        # 對話框關閉後重建列表（可能有移除）
        self._rebuild_list()

    # --------------------------------------------------
    # 自動啟動
    # --------------------------------------------------

    def auto_start_if_enabled(self):
        """若設定為自動啟動，則啟動監聽"""
        if self.app.config_manager.get_settings("broadcast_auto_start", False):
            accepted = self.app.config_manager.get_settings("broadcast_disclaimer_accepted", False)
            if accepted:
                self._do_start()

    # --------------------------------------------------
    # 樣式工具
    # --------------------------------------------------

    @staticmethod
    def _btn_style(bg: str, hover: str) -> str:
        """產生按鈕 QSS"""
        return (
            f"QPushButton {{"
            f" background-color: {bg};"
            f" color: {AppTheme.TEXT_PRIMARY};"
            f" border: none;"
            f" border-radius: 4px;"
            f" padding: 4px 12px;"
            f" font-size: 12px;"
            f" font-family: {AppTheme.FONT_FAMILY}; }}"
            f"QPushButton:hover {{"
            f" background-color: {hover}; }}"
        )
