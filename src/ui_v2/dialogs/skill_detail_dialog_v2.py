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
    QHBoxLayout, QVBoxLayout, QLabel, QSpinBox, QCheckBox, QPushButton,
    QFileDialog, QRadioButton, QButtonGroup,
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
                         width=460, height=650)
        self._build_body()
        self._build_footer()

    # --------------------------------------------------
    # 音效選項
    # --------------------------------------------------
    def _build_sound_options(self):
        # 下拉只列實體音檔；TTS（念名稱）語音檔不列出，改由「念名稱」模式代表。
        self._sound_label_map = {}
        sm = getattr(self.app, "sound_manager", None)
        if sm is None:
            return
        for filename in sm.list_sounds():
            if filename.startswith("tts_"):
                continue
            self._sound_label_map[sm.get_sound_label(filename)] = filename

    def _default_filename(self, *, alert: bool) -> str:
        """「念名稱」模式對應的預設 TTS 檔（念技能名稱）"""
        name = (self._meta.get("name") or "").strip()
        if not name:
            return ""
        text = f"{name}準備" if alert else name
        sm = getattr(self.app, "sound_manager", None)
        if sm is None:
            return ""
        return sm.tts_filename(text)

    def _label_for_real_file(self, filename: str) -> str:
        """實體音檔檔名 → 下拉 label；找不到回空字串"""
        for label, fname in self._sound_label_map.items():
            if fname == filename:
                return label
        return ""

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

        self._end = self._sound_section("冷卻完成")
        self._apply_sound_state(self._end, cur_end)
        self._end["play"].clicked.connect(self._preview_completion)
        L.addLayout(self._end["layout"])

        L.addSpacing(T.S_XS)

        self._alert = self._sound_section("提前提示")
        self._apply_sound_state(self._alert, cur_alert)
        self._alert["play"].clicked.connect(self._preview_alert)
        L.addLayout(self._alert["layout"])

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

    def _sound_section(self, title: str) -> dict:
        """建立一組音效設定：模式（念名稱 / 選擇音效 / 靜音）＋ 下拉 ＋ 試聽。

        Returns:
            dict：layout / group / rb_tts / rb_file / rb_mute / combo / play
        """
        box = QVBoxLayout()
        box.setSpacing(T.S_XS)
        box.addWidget(self._caption(title))

        mode_row = QHBoxLayout()
        mode_row.setSpacing(T.S_MD)
        rb_tts  = QRadioButton("念名稱")
        rb_file = QRadioButton("選擇音效")
        rb_mute = QRadioButton("靜音")
        group = QButtonGroup(self)
        for rb in (rb_tts, rb_file, rb_mute):
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            rb.setStyleSheet(T.radio_button_qss())
            group.addButton(rb)
            mode_row.addWidget(rb)
        mode_row.addStretch()
        box.addLayout(mode_row)

        combo_row = QHBoxLayout()
        combo_row.setSpacing(T.S_SM)
        combo = ArrowComboBox()
        combo.addItems(list(self._sound_label_map.keys()))
        combo.setFixedHeight(T.BTN_H)
        combo_row.addWidget(combo, 1)
        play = _PlayBtn()
        combo_row.addWidget(play)
        box.addLayout(combo_row)

        section = {"layout": box, "group": group, "rb_tts": rb_tts,
                   "rb_file": rb_file, "rb_mute": rb_mute,
                   "combo": combo, "play": play}
        for rb in (rb_tts, rb_file, rb_mute):
            rb.toggled.connect(lambda _checked, s=section: self._sync_sound_enabled(s))
        return section

    def _apply_sound_state(self, section: dict, filename: str):
        """依 override 值設定初始模式與下拉選擇

        - MUTE_SENTINEL → 靜音
        - 指向現存實體音檔 → 選擇音效（下拉選到該檔）
        - 空字串 / TTS / 已刪除檔 → 念名稱（預設語音）
        """
        if filename == MUTE_SENTINEL:
            section["rb_mute"].setChecked(True)
        else:
            label = self._label_for_real_file(filename) if filename else ""
            if label:
                section["rb_file"].setChecked(True)
                section["combo"].setCurrentText(label)
            else:
                section["rb_tts"].setChecked(True)   # 空 / TTS / 已刪除檔
        self._sync_sound_enabled(section)

    @staticmethod
    def _sync_sound_enabled(section: dict):
        """下拉只在「選擇音效」時可用；試聽在非靜音時可用"""
        section["combo"].setEnabled(section["rb_file"].isChecked())
        section["play"].setEnabled(not section["rb_mute"].isChecked())

    # --------------------------------------------------
    # 聲音操作
    # --------------------------------------------------
    def _preview_filename(self, section: dict, fallback: str, *, alert: bool) -> str:
        """依模式決定試聽播放的檔名（靜音回空字串）"""
        if section["rb_mute"].isChecked():
            return ""
        if section["rb_tts"].isChecked():
            return self._default_filename(alert=alert) or fallback
        filename = self._sound_label_map.get(section["combo"].currentText(), "")
        return filename if filename else fallback

    def _preview_completion(self):
        if self.app is None:
            return
        filename = self._preview_filename(
            self._end, getattr(self.app, "global_sound", ""), alert=False
        )
        if filename and self.app.sound_manager:
            self.app.sound_manager.play(filename)

    def _preview_alert(self):
        if self.app is None:
            return
        filename = self._preview_filename(
            self._alert, getattr(self.app, "global_alert_sound", ""), alert=True
        )
        if filename and self.app.sound_manager:
            self.app.sound_manager.play(filename)

    def _save_sound_mode(self, section: dict, overrides: dict, sid: str):
        """依模式寫入 override dict

        - 靜音 → MUTE_SENTINEL
        - 念名稱 → 移除 override（走預設語音）
        - 選擇音效 → 寫入下拉選中的檔名（無檔則移除）
        """
        if section["rb_mute"].isChecked():
            overrides[sid] = MUTE_SENTINEL
        elif section["rb_tts"].isChecked():
            overrides.pop(sid, None)
        else:
            filename = self._sound_label_map.get(section["combo"].currentText(), "")
            if filename:
                overrides[sid] = filename
            else:
                overrides.pop(sid, None)

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
        new_label = self.app.sound_manager.get_sound_label(new_name)
        # 剛匯入的檔切到「選擇音效」模式並選中；同時重整兩個下拉內容
        for section in (self._end, self._alert):
            combo = section["combo"]
            prev = combo.currentText()
            combo.clear(); combo.addItems(values)
            combo.setCurrentText(prev if prev in values else new_label)
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

        # 完成音效 / 提前音效：依模式寫入（靜音→sentinel；念名稱→清 override；選擇音效→檔名）
        self._save_sound_mode(self._end, app.skill_sound_overrides, sid)
        self._save_sound_mode(self._alert, app.skill_alert_sound_overrides, sid)

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
