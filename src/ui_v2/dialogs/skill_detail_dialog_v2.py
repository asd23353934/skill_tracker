"""
技能詳細設定 dialog — V2

綁定契約
═══════════════════════════════════════════════════════════
建構參數：SkillDetailDialogV2(parent, app, skill_id)

讀取：
- skill_manager.get_skill(id) 取得名稱/元資料
- 提前秒數：app.skill_alert_seconds_overrides.get(id) / app.alert_before_seconds
- 完成音效：app.skill_sound_overrides.get(id) / app.global_sound
- 提前音效：app.skill_alert_sound_overrides.get(id) / app.global_alert_sound
- 音效清單：app.sound_manager.list_sounds() / get_sound_label(filename)
- 自動設定：app.skill_permanent / skill_loop / skill_alert_enabled

寫入（accept 時）：
- 寫入上列四個 override dict
- 呼叫 app.auto_save_current_profile()
- 同步常駐視窗生命週期（與 V1 _save 一致）
- 透過 app.skill_card_widgets[id].refresh() 讓 V2 卡片重繪

Cancel：完全不寫入 app state。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QSpinBox, QCheckBox, QPushButton, QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import ArrowComboBox
from src.ui_v2.dialogs.base_dialog_v2 import BaseDialogV2
from src.ui_v2.lucide import lucide_pixmap
from src.domain.services import MUTE_SENTINEL


class _PlayBtn(QPushButton):
    """自繪播放三角按鈕"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(T.BTN_H, T.BTN_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton {{ background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px; }}"
            f"QPushButton:hover {{ background: {T.BG_HOVER};"
            f" border-color: {T.ORANGE}; }}"
        )

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        pix = lucide_pixmap("play", T.TEXT_HI, 14, stroke=1.8)
        p = QPainter(self)
        x = (self.width() - 14) // 2
        y = (self.height() - 14) // 2
        p.drawPixmap(x, y, pix)
        p.end()


class SkillDetailDialogV2(BaseDialogV2):
    """技能詳細設定（V2）— 與 V1 SkillDetailDialog 等價功能"""

    def __init__(self, parent=None, app=None, skill_id: str | None = None):
        self.app = app
        self.skill_id = skill_id
        self._sound_label_map: dict[str, str] = {}
        meta = None
        if app is not None and skill_id and hasattr(app, "skill_manager"):
            meta = app.skill_manager.get_skill(skill_id)
        self._meta = meta or {}
        # 所有技能預設念名稱（TTS）：下拉預設顯示對應 TTS 檔，無「使用全域設定」選項
        skill_name = self._meta.get("name", skill_id or "技能")
        self._build_sound_options()

        super().__init__(parent, title=f"技能設定 — {skill_name}",
                         width=460, height=560)
        self._build_body()
        self._build_footer()

    # --------------------------------------------------
    # 音效選項
    # --------------------------------------------------
    def _build_sound_options(self):
        # 靜音 不再放入下拉（改由獨立 checkbox 控制）
        # 所有技能直接列音檔，預設 = 對應 TTS（無「使用全域設定」項）
        self._sound_label_map = {}
        sm = getattr(self.app, "sound_manager", None)
        if sm is None:
            return
        for filename in sm.list_sounds():
            self._sound_label_map[sm.get_sound_label(filename)] = filename

    def _default_filename(self, *, alert: bool) -> str:
        """無 override 時應顯示的預設音檔（念技能名稱的 TTS）"""
        name = (self._meta.get("name") or "").strip()
        if not name:
            return ""
        text = f"{name}準備" if alert else name
        sm = getattr(self.app, "sound_manager", None)
        if sm is None:
            return ""
        return sm.tts_filename(text)

    def _label_for_filename(self, filename: str, *, alert: bool = False) -> str:
        """檔名 → 下拉顯示 label

        - MUTE_SENTINEL / 空字串：顯示對應的預設 TTS
        - 指定檔名：對映 label；找不到 fallback 到預設
        """
        if filename in ("", MUTE_SENTINEL):
            default_file = self._default_filename(alert=alert)
            for label, fname in self._sound_label_map.items():
                if fname == default_file:
                    return label
            return next(iter(self._sound_label_map.keys()), "")
        for label, fname in self._sound_label_map.items():
            if fname == filename:
                return label
        # override 指向已刪除檔 → fallback 到預設
        return self._label_for_filename("", alert=alert)

    # --------------------------------------------------
    # 主內容
    # --------------------------------------------------
    def _build_body(self):
        L = self.body_layout()
        app = self.app
        sid = self.skill_id

        # ── 提前提示 ──
        L.addWidget(self._section_label("提前提示"))

        override = None
        if app is not None and sid:
            override = app.skill_alert_seconds_overrides.get(sid)
        current = override if override is not None else (
            getattr(app, "alert_before_seconds", 3) if app else 3
        )

        alert_row = QHBoxLayout()
        alert_row.setSpacing(T.S_SM)
        self.alert_spin = QSpinBox()
        self.alert_spin.setRange(0, 60)
        self.alert_spin.setValue(int(current))
        self.alert_spin.setFixedHeight(T.BTN_H)
        self.alert_spin.setFixedWidth(80)
        alert_row.addWidget(self.alert_spin)
        alert_row.addWidget(self._caption("秒前提示"))
        alert_row.addStretch()
        L.addLayout(alert_row)

        self.use_global_cb = QCheckBox(
            f"使用全域秒數設定（目前：{getattr(app, 'alert_before_seconds', 3)}秒）"
            if app else "使用全域秒數設定"
        )
        self.use_global_cb.setChecked(override is None)
        self.use_global_cb.stateChanged.connect(self._on_toggle_global_alert)
        L.addWidget(self.use_global_cb)

        L.addSpacing(T.S_SM)

        # ── 音效 ──
        L.addWidget(self._section_label("音效"))

        cur_end = ""
        cur_alert = ""
        if app is not None and sid:
            cur_end = app.skill_sound_overrides.get(sid, "")
            cur_alert = app.skill_alert_sound_overrides.get(sid, "")

        end_row, self.sound_combo, end_play, self.end_mute_cb = self._sound_row("冷卻完成")
        self.sound_combo.setCurrentText(self._label_for_filename(cur_end, alert=False))
        self.end_mute_cb.setChecked(cur_end == MUTE_SENTINEL)
        self._apply_mute_state(self.sound_combo, end_play, self.end_mute_cb.isChecked())
        self.end_mute_cb.toggled.connect(
            lambda checked: self._apply_mute_state(self.sound_combo, end_play, checked)
        )
        end_play.clicked.connect(self._preview_completion)
        L.addLayout(end_row)

        alert_sound_row, self.alert_sound_combo, alert_play, self.alert_mute_cb = self._sound_row("提前提示")
        self.alert_sound_combo.setCurrentText(self._label_for_filename(cur_alert, alert=True))
        self.alert_mute_cb.setChecked(cur_alert == MUTE_SENTINEL)
        self._apply_mute_state(self.alert_sound_combo, alert_play, self.alert_mute_cb.isChecked())
        self.alert_mute_cb.toggled.connect(
            lambda checked: self._apply_mute_state(self.alert_sound_combo, alert_play, checked)
        )
        alert_play.clicked.connect(self._preview_alert)
        L.addLayout(alert_sound_row)

        import_btn = QPushButton("+ 匯入音效檔案")
        import_btn.setProperty("kind", "ghost")
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.setFixedHeight(T.BTN_H)
        import_btn.clicked.connect(self._import_sound)
        L.addWidget(import_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        L.addSpacing(T.S_SM)

        # ── 自動套用 ──
        L.addWidget(self._section_label("自動套用"))
        L.addWidget(self._caption("未手動切換時的預設狀態"))

        auto = QHBoxLayout()
        auto.setSpacing(T.S_LG)
        self.auto_perm = QCheckBox("常駐")
        self.auto_loop = QCheckBox("循環")
        self.auto_alert = QCheckBox("提醒")
        if app is not None and sid:
            self.auto_perm.setChecked(bool(app.skill_permanent.get(sid, False)))
            self.auto_loop.setChecked(bool(app.skill_loop.get(sid, False)))
            self.auto_alert.setChecked(bool(app.skill_alert_enabled.get(sid, False)))
        for cb in (self.auto_perm, self.auto_loop, self.auto_alert):
            auto.addWidget(cb)
        auto.addStretch()
        L.addLayout(auto)

        L.addStretch()

    # --------------------------------------------------
    # 底部
    # --------------------------------------------------
    def _build_footer(self):
        F = self.footer_layout()

        cancel = QPushButton("取消")
        cancel.setProperty("kind", "ghost")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setFixedHeight(T.BTN_H)
        cancel.clicked.connect(self.reject)
        F.addWidget(cancel)

        save = QPushButton("儲存")
        save.setProperty("kind", "primary")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.setFixedHeight(T.BTN_H)
        save.clicked.connect(self._on_save)
        F.addWidget(save)

    # --------------------------------------------------
    # 輔助
    # --------------------------------------------------
    def _section_label(self, text: str) -> QLabel:
        return T.make_label(text, T.FONT_LABEL)

    def _caption(self, text: str) -> QLabel:
        return T.make_label(text, T.FONT_CAPTION)

    def _sound_row(self, label: str) -> tuple[QHBoxLayout, ArrowComboBox, _PlayBtn, QCheckBox]:
        h = QHBoxLayout()
        h.setSpacing(T.S_SM)
        lbl = T.make_label(label, T.FONT_BODY)
        lbl.setFixedWidth(60)
        h.addWidget(lbl)
        combo = ArrowComboBox()
        combo.addItems(list(self._sound_label_map.keys()))
        combo.setFixedHeight(T.BTN_H)
        h.addWidget(combo, 1)
        play = _PlayBtn()
        h.addWidget(play)
        mute = QCheckBox("靜音")
        mute.setCursor(Qt.CursorShape.PointingHandCursor)
        mute.setStyleSheet(
            f"QCheckBox {{ color: {T.TEXT}; background: transparent;"
            f" font-size: 12px; spacing: 4px; }}"
        )
        h.addWidget(mute)
        return h, combo, play, mute

    @staticmethod
    def _apply_mute_state(combo: ArrowComboBox, play: _PlayBtn, muted: bool):
        """靜音切換：禁用下拉與試聽，視覺上半透明表達 disabled"""
        combo.setEnabled(not muted)
        play.setEnabled(not muted)

    # --------------------------------------------------
    # 聲音操作
    # --------------------------------------------------
    def _effective_filename(self, combo: ArrowComboBox, fallback: str) -> str:
        filename = self._sound_label_map.get(combo.currentText(), "")
        if filename == MUTE_SENTINEL:
            return ""          # 靜音：試聽不播放
        return filename if filename else fallback

    def _preview_completion(self):
        if self.app is None:
            return
        filename = self._effective_filename(
            self.sound_combo, getattr(self.app, "global_sound", "")
        )
        if filename and self.app.sound_manager:
            self.app.sound_manager.play(filename)

    def _preview_alert(self):
        if self.app is None:
            return
        filename = self._effective_filename(
            self.alert_sound_combo, getattr(self.app, "global_alert_sound", "")
        )
        if filename and self.app.sound_manager:
            self.app.sound_manager.play(filename)

    def _import_sound(self):
        if self.app is None or self.app.sound_manager is None:
            return
        filepath, _ = QFileDialog.getOpenFileName(
            self, "選擇音效檔案", "",
            "音效檔案 (*.wav *.mp3);;WAV (*.wav);;MP3 (*.mp3)"
        )
        if not filepath:
            return
        new_name = self.app.sound_manager.import_sound(filepath)
        if not new_name:
            if hasattr(self.app, "toast"):
                self.app.toast.show("音效格式不支援（僅限 .wav / .mp3）", "error")
            return
        self._build_sound_options()
        values = list(self._sound_label_map.keys())
        cur_end = self.sound_combo.currentText()
        cur_alert = self.alert_sound_combo.currentText()
        self.sound_combo.clear(); self.sound_combo.addItems(values)
        self.alert_sound_combo.clear(); self.alert_sound_combo.addItems(values)
        new_label = self.app.sound_manager.get_sound_label(new_name)
        # 若使用者目前還停在「預設」/「使用全域」狀態，自動切到剛匯入的檔；否則維持原選擇
        default_end_label = self._label_for_filename("", alert=False)
        default_alert_label = self._label_for_filename("", alert=True)
        self.sound_combo.setCurrentText(
            new_label if cur_end == default_end_label else cur_end
        )
        self.alert_sound_combo.setCurrentText(
            new_label if cur_alert == default_alert_label else cur_alert
        )
        if hasattr(self.app, "toast"):
            self.app.toast.show(f"已匯入音效：{new_name}", "success")

    def _on_toggle_global_alert(self):
        if self.use_global_cb.isChecked() and self.app is not None:
            self.alert_spin.setValue(int(getattr(self.app, "alert_before_seconds", 3)))

    # --------------------------------------------------
    # 儲存
    # --------------------------------------------------
    def _on_save(self):
        app = self.app
        sid = self.skill_id
        if app is None or sid is None:
            self.accept()
            return

        # 提前秒數 override
        if self.use_global_cb.isChecked():
            app.skill_alert_seconds_overrides.pop(sid, None)
        else:
            app.skill_alert_seconds_overrides[sid] = max(0, self.alert_spin.value())

        # 完成音效
        if self.end_mute_cb.isChecked():
            app.skill_sound_overrides[sid] = MUTE_SENTINEL
        else:
            end_file = self._sound_label_map.get(self.sound_combo.currentText(), "")
            # 選的就是預設 TTS → 不寫 override，讓 SkillService 走預設
            if end_file == self._default_filename(alert=False):
                app.skill_sound_overrides.pop(sid, None)
            elif end_file:
                app.skill_sound_overrides[sid] = end_file
            else:
                app.skill_sound_overrides.pop(sid, None)

        # 提前音效
        if self.alert_mute_cb.isChecked():
            app.skill_alert_sound_overrides[sid] = MUTE_SENTINEL
        else:
            alert_file = self._sound_label_map.get(
                self.alert_sound_combo.currentText(), "")
            if alert_file == self._default_filename(alert=True):
                app.skill_alert_sound_overrides.pop(sid, None)
            elif alert_file:
                app.skill_alert_sound_overrides[sid] = alert_file
            else:
                app.skill_alert_sound_overrides.pop(sid, None)

        # 自動套用（與 V1 一致：常駐與循環互斥）
        new_perm = self.auto_perm.isChecked()
        new_loop = self.auto_loop.isChecked()
        new_alert = self.auto_alert.isChecked()
        if new_perm and new_loop:
            new_loop = False
        app.skill_permanent[sid]     = new_perm
        app.skill_loop[sid]          = new_loop
        app.skill_alert_enabled[sid] = new_alert

        # 常駐視窗生命週期
        wm = getattr(app, "window_manager", None)
        if wm is not None:
            win = wm.active_windows.get(sid)
            if new_perm and win is None:
                wm.create_permanent_window(sid)
            elif not new_perm and win is not None and not new_loop:
                win.close()
            elif win is not None:
                win.is_permanent  = new_perm
                win.is_loop       = new_loop
                win.alert_enabled = new_alert
                if hasattr(wm, "refresh_window_sound_params"):
                    wm.refresh_window_sound_params(sid)

        if hasattr(app, "auto_save_current_profile"):
            app.auto_save_current_profile()

        # 卡片局部 refresh
        cards = getattr(app, "skill_card_widgets", None)
        if isinstance(cards, dict) and sid in cards:
            cards[sid].refresh()

        self.accept()
