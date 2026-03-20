"""
練功水錢存檔管理對話框 — PySide6 版本
支援儲存（命名）、查看列表（含摘要）、載入、刪除、重命名
"""

import datetime

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QWidget,
    QLineEdit, QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme


def _fmt(value) -> str:
    """格式化整數為千分位字串"""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "—"


class PotionSaveDialog(BaseDialog):
    """練功水錢存檔管理對話框

    兩種模式：
      mode='save' — 顯示命名輸入框與儲存按鈕，下方列表可選擇覆蓋
      mode='load' — 只顯示列表與操作按鈕
    """

    def __init__(self, parent, config_manager, mode: str = "save", current_data: dict = None, app=None):
        """初始化對話框

        Args:
            parent:         父元件
            config_manager: ConfigManager 實例
            mode:           'save' | 'load'
            current_data:   儲存模式時的表單資料
            app:            App 實例（用於 toast 通知）
        """
        title = "儲存練功紀錄" if mode == "save" else "練功紀錄列表"
        super().__init__(parent, title, 620, 540)
        self.app            = app
        self.config_manager = config_manager
        self.mode           = mode
        self.current_data   = current_data or {}
        self.result_data    = None   # 載入模式成功後設定
        self._build_ui()

    def _build_ui(self):
        """建構 UI"""
        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(18, 14, 18, 12)
        layout.setSpacing(8)

        # ===== 標題列 =====
        title_row = QWidget()
        title_row.setStyleSheet("background: transparent;")
        tr = QHBoxLayout(title_row)
        tr.setContentsMargins(0, 0, 0, 0)
        tr.setSpacing(8)

        icon = "💾" if self.mode == "save" else "📂"
        title_lbl = QLabel(f"{icon} {'儲存練功紀錄' if self.mode == 'save' else '練功紀錄列表'}")
        title_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 15px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        tr.addWidget(title_lbl)
        tr.addStretch()
        layout.addWidget(title_row)

        # ===== 儲存模式：命名輸入區 =====
        if self.mode == "save":
            save_frame = QFrame()
            save_frame.setObjectName("save_input_frame")
            save_frame.setStyleSheet(
                f"QFrame#save_input_frame {{"
                f" background: {AppTheme.BG_CARD};"
                f" border: 1px solid {AppTheme.GOLD_MUTED};"
                f" border-radius: {AppTheme.CORNER_MD}px; }}"
            )
            sf_lay = QHBoxLayout(save_frame)
            sf_lay.setContentsMargins(10, 8, 10, 8)
            sf_lay.setSpacing(8)

            name_lbl = QLabel("紀錄名稱:")
            name_lbl.setStyleSheet(
                f"color: {AppTheme.TEXT_SECONDARY}; font-size: 12px;"
                f" background: transparent; border: none;"
            )
            sf_lay.addWidget(name_lbl)

            default_name = datetime.date.today().strftime("%Y%m%d") + "_練功紀錄"
            self._name_edit = QLineEdit(default_name)
            self._name_edit.setStyleSheet(
                f"QLineEdit {{"
                f" background: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_PRIMARY};"
                f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: 3px;"
                f" padding: 3px 6px; font-size: 12px; }}"
                f"QLineEdit:focus {{ border-color: {AppTheme.GOLD_PRIMARY}; }}"
            )
            sf_lay.addWidget(self._name_edit)

            confirm_btn = QPushButton("💾 確認儲存")
            confirm_btn.setFixedHeight(30)
            confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            confirm_btn.setStyleSheet(
                f"QPushButton {{"
                f" background: {AppTheme.ACCENT_GREEN}; color: #fff;"
                f" border: none; border-radius: 4px;"
                f" padding: 3px 14px; font-size: 12px; font-weight: bold; }}"
                f"QPushButton:hover {{ background: {AppTheme.ACCENT_GREEN_HOVER}; }}"
            )
            confirm_btn.clicked.connect(self._do_save)
            sf_lay.addWidget(confirm_btn)
            layout.addWidget(save_frame)

        # ===== 列表 + 詳情（橫向分割）=====
        split_w = QWidget()
        split_w.setStyleSheet("background: transparent;")
        split_lay = QHBoxLayout(split_w)
        split_lay.setContentsMargins(0, 0, 0, 0)
        split_lay.setSpacing(8)

        # ── 左: 列表 ──
        list_frame = QFrame()
        list_frame.setObjectName("list_frame")
        list_frame.setStyleSheet(
            f"QFrame#list_frame {{"
            f" background: {AppTheme.BG_CARD};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_MD}px; }}"
        )
        lf_lay = QVBoxLayout(list_frame)
        lf_lay.setContentsMargins(4, 4, 4, 4)
        lf_lay.setSpacing(4)

        list_hdr = QLabel("已儲存的紀錄")
        list_hdr.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
            f" background: transparent; border: none; padding: 2px 6px;"
        )
        lf_lay.addWidget(list_hdr)

        self._list_widget = QListWidget()
        self._list_widget.setStyleSheet(
            f"QListWidget {{ background: {AppTheme.BG_CARD}; border: none;"
            f" color: {AppTheme.TEXT_PRIMARY}; font-size: 12px; }}"
            f"QListWidget::item {{ padding: 5px 10px; border-radius: 3px; }}"
            f"QListWidget::item:hover {{ background: {AppTheme.BG_CARD_HOVER}; }}"
            f"QListWidget::item:selected {{"
            f" background: {AppTheme.BG_CARD_HOVER};"
            f" color: {AppTheme.GOLD_LIGHT}; }}"
        )
        self._list_widget.currentItemChanged.connect(self._on_selection_changed)
        if self.mode == "load":
            self._list_widget.itemDoubleClicked.connect(lambda _: self._do_load())
        lf_lay.addWidget(self._list_widget)
        split_lay.addWidget(list_frame, 1)

        # ── 右: 詳情面板 ──
        detail_frame = QFrame()
        detail_frame.setObjectName("detail_frame")
        detail_frame.setFixedWidth(200)
        detail_frame.setStyleSheet(
            f"QFrame#detail_frame {{"
            f" background: {AppTheme.BG_CARD};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_MD}px; }}"
        )
        detail_v = QVBoxLayout(detail_frame)
        detail_v.setContentsMargins(10, 10, 10, 10)
        detail_v.setSpacing(6)

        detail_title = QLabel("📋 紀錄詳情")
        detail_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail_title.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 12px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        detail_v.addWidget(detail_title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {AppTheme.GOLD_MUTED}; border: none;")
        detail_v.addWidget(sep)

        # 詳情捲動區
        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        detail_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._detail_content = QWidget()
        self._detail_content.setStyleSheet("background: transparent;")
        self._detail_layout = QVBoxLayout(self._detail_content)
        self._detail_layout.setContentsMargins(0, 0, 0, 0)
        self._detail_layout.setSpacing(4)
        self._detail_layout.addStretch()

        detail_scroll.setWidget(self._detail_content)
        detail_v.addWidget(detail_scroll)
        split_lay.addWidget(detail_frame)

        layout.addWidget(split_w)

        # ===== 按鈕列 =====
        btn_row = QWidget()
        btn_row.setStyleSheet("background: transparent;")
        br = QHBoxLayout(btn_row)
        br.setContentsMargins(0, 0, 0, 0)
        br.setSpacing(6)
        br.addStretch()

        if self.mode == "load":
            load_btn = QPushButton("📂 載入選取")
            load_btn.setFixedHeight(30)
            load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            load_btn.setStyleSheet(self._gold_btn_style())
            load_btn.clicked.connect(self._do_load)
            br.addWidget(load_btn)

        rename_btn = QPushButton("✏ 重命名")
        rename_btn.setFixedHeight(30)
        rename_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rename_btn.setStyleSheet(self._neutral_btn_style())
        rename_btn.clicked.connect(self._do_rename)
        br.addWidget(rename_btn)

        delete_btn = QPushButton("🗑 刪除")
        delete_btn.setFixedHeight(30)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(
            f"QPushButton {{"
            f" background: {AppTheme.ACCENT_RED}; color: #fff;"
            f" border: none; border-radius: 4px;"
            f" padding: 3px 10px; font-size: 11px; }}"
            f"QPushButton:hover {{ background: {AppTheme.ACCENT_RED_HOVER}; }}"
        )
        delete_btn.clicked.connect(self._do_delete)
        br.addWidget(delete_btn)

        close_btn = QPushButton("關閉")
        close_btn.setFixedHeight(30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(self._neutral_btn_style())
        close_btn.clicked.connect(self.reject)
        br.addWidget(close_btn)

        br.addStretch()
        layout.addWidget(btn_row)

        # ===== 提示 =====
        if self.mode == "load":
            hint = QLabel("💡 雙擊列表項目可快速載入")
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint.setStyleSheet(
                f"color: {AppTheme.TEXT_MUTED}; font-size: 10px;"
                f" background: transparent; border: none;"
            )
            layout.addWidget(hint)

        self._refresh_list()

    # ──────────────────────────────────────────────────────
    # 樣式輔助
    # ──────────────────────────────────────────────────────

    def _gold_btn_style(self) -> str:
        """金色按鈕 QSS"""
        return (
            f"QPushButton {{"
            f" background: {AppTheme.GOLD_DARK}; color: {AppTheme.BG_DEEP};"
            f" border: 1px solid {AppTheme.GOLD_PRIMARY}; border-radius: 4px;"
            f" padding: 3px 12px; font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {AppTheme.GOLD_PRIMARY}; }}"
        )

    def _neutral_btn_style(self) -> str:
        """中性按鈕 QSS"""
        return (
            f"QPushButton {{"
            f" background: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_PRIMARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: 4px;"
            f" padding: 3px 10px; font-size: 11px; }}"
            f"QPushButton:hover {{ border-color: {AppTheme.GOLD_PRIMARY}; color: {AppTheme.TEXT_GOLD}; }}"
        )

    # ──────────────────────────────────────────────────────
    # 列表管理
    # ──────────────────────────────────────────────────────

    def _refresh_list(self):
        """重新載入存檔列表"""
        self._list_widget.clear()
        saves = self.config_manager.list_potion_saves()
        for name in saves:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, name)
            # 嘗試讀取摘要上色
            record = self.config_manager.load_potion_record(name)
            if record:
                net = record.get("summary", {}).get("net", 0)
                if net > 0:
                    item.setForeground(QColor(AppTheme.ACCENT_GREEN))
                elif net < 0:
                    item.setForeground(QColor(AppTheme.ACCENT_RED))
                saved_at = record.get("saved_at", "")[:10]
                item.setText(f"{name}   ({saved_at}  淨:{_fmt(net)})")
            self._list_widget.addItem(item)

        if self._list_widget.count() == 0:
            empty = QListWidgetItem("（尚無存檔）")
            empty.setForeground(QColor(AppTheme.TEXT_MUTED))
            empty.setFlags(empty.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._list_widget.addItem(empty)

    def _get_selected_name(self) -> str | None:
        """取得選取的存檔名稱"""
        item = self._list_widget.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _on_selection_changed(self, current, _previous):
        """選取存檔時更新詳情面板"""
        if not current:
            return
        name = current.data(Qt.ItemDataRole.UserRole)
        if not name:
            return
        record = self.config_manager.load_potion_record(name)
        self._update_detail(record)

    def _update_detail(self, record: dict | None):
        """更新詳情面板內容

        Args:
            record: 存檔資料字典，None 時清空
        """
        # 清空舊內容
        while self._detail_layout.count() > 1:
            item = self._detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not record:
            return

        _LBL = f"color: {AppTheme.TEXT_SECONDARY}; font-size: 10px; background: transparent;"
        _VAL = f"font-size: 11px; font-weight: bold; background: transparent;"

        def _add(label: str, value: str, color: str = AppTheme.TEXT_PRIMARY):
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(4)
            lbl = QLabel(label)
            lbl.setStyleSheet(_LBL)
            rl.addWidget(lbl)
            rl.addStretch()
            val = QLabel(value)
            val.setStyleSheet(f"color: {color}; {_VAL}")
            rl.addWidget(val)
            self._detail_layout.insertWidget(self._detail_layout.count() - 1, row)

        def _add_sep():
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background: {AppTheme.BG_TERTIARY}; border: none;")
            self._detail_layout.insertWidget(self._detail_layout.count() - 1, sep)

        summary = record.get("summary", {})
        net     = summary.get("net", 0)

        _add("日期", record.get("saved_at", "")[:10])
        _add("時間", f"{record.get('duration_minutes', 0)} 分鐘")
        _add_sep()

        income  = summary.get("total_income", 0)
        expense = summary.get("total_expense", 0)
        _add("總收入", _fmt(income),
             AppTheme.ACCENT_GREEN if income > 0 else AppTheme.TEXT_MUTED)
        _add("總支出", _fmt(expense),
             AppTheme.ACCENT_RED if expense > 0 else AppTheme.TEXT_MUTED)
        _add("總收支", _fmt(net),
             AppTheme.ACCENT_GREEN if net > 0 else (AppTheme.ACCENT_RED if net < 0 else AppTheme.TEXT_MUTED))
        _add_sep()

        _add("獲取經驗", _fmt(summary.get("exp_gained", 0)), AppTheme.ACCENT_YELLOW)
        _add_sep()

        # 各藥水小計
        hp_total  = sum(r.get("cost", 0) for r in record.get("hp_potions",       []))
        mp_total  = sum(r.get("cost", 0) for r in record.get("mp_potions",        []))
        cmb_total = sum(r.get("cost", 0) for r in record.get("combined_potions",  []))
        if hp_total or mp_total or cmb_total:
            _add("💊 HP 小計",  _fmt(hp_total),  AppTheme.ACCENT_RED)
            _add("💧 MP 小計",  _fmt(mp_total),  AppTheme.ACCENT_RED)
            _add("✨ 綜合小計", _fmt(cmb_total), AppTheme.ACCENT_RED)

    # ──────────────────────────────────────────────────────
    # 動作
    # ──────────────────────────────────────────────────────

    def _do_save(self):
        """執行儲存"""
        name = self._name_edit.text().strip()
        if not name:
            if self.app:
                self.app.toast.show("請輸入存檔名稱！", "info")
            return

        existing = self.config_manager.list_potion_saves()
        if name in existing:
            reply = QMessageBox.question(
                self, "確認覆蓋",
                f"存檔「{name}」已存在，確定要覆蓋嗎？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        data = dict(self.current_data)
        data["name"] = name
        if self.config_manager.save_potion_record(name, data):
            self._refresh_list()
            if self.app:
                self.app.toast.show(f"已儲存「{name}」", "success")
        else:
            if self.app:
                self.app.toast.show("儲存失敗，請稍後再試。", "error")

    def _do_load(self):
        """執行載入（載入模式）"""
        name = self._get_selected_name()
        if not name:
            if self.app:
                self.app.toast.show("請先選擇要載入的紀錄！", "info")
            return
        record = self.config_manager.load_potion_record(name)
        if record:
            self.result_data = record
            self.accept()
        else:
            if self.app:
                self.app.toast.show(f"無法載入「{name}」！", "error")

    def _do_rename(self):
        """重命名存檔"""
        old_name = self._get_selected_name()
        if not old_name:
            if self.app:
                self.app.toast.show("請先選擇要重命名的紀錄！", "info")
            return
        new_name, ok = QInputDialog.getText(
            self, "重命名", f"輸入新名稱：\n（目前：{old_name}）"
        )
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        new_name = new_name.strip()
        if new_name in self.config_manager.list_potion_saves():
            if self.app:
                self.app.toast.show(f"「{new_name}」已存在！", "error")
            return
        if self.config_manager.rename_potion_record(old_name, new_name):
            self._refresh_list()
        else:
            if self.app:
                self.app.toast.show("重命名失敗！", "error")

    def _do_delete(self):
        """刪除存檔"""
        name = self._get_selected_name()
        if not name:
            if self.app:
                self.app.toast.show("請先選擇要刪除的紀錄！", "info")
            return
        reply = QMessageBox.question(
            self, "確認刪除",
            f"確定要刪除「{name}」嗎？此操作無法復原。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.config_manager.delete_potion_record(name):
                self._list_widget.setCurrentItem(None)
                self._update_detail(None)
                self._refresh_list()
            else:
                if self.app:
                    self.app.toast.show("刪除失敗！", "error")
