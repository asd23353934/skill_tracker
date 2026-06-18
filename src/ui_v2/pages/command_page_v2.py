"""
指令快速複製頁 — V2

列出 Artale 遊戲內常用聊天指令（按使用情境分組、常用置頂），每個一鍵複製到系統剪貼簿
（玩家切回遊戲貼上即可送出）。
需玩家名稱的指令（標「(玩家)」者，如 交換 / 密語 / 邀請 / 封鎖）提供可編輯下拉：可直接打新名稱、也可選最近用過的；
複製時把名稱填入指令模板的 {name}，並把該名稱記到 config_user.json
（見 ConfigManager.add_recent_command_name），下次直接從下拉選取。

指令按使用情境分組定義於 _GROUPS（再攤平為 _COMMANDS 供名稱記憶等共用）；
增刪指令或調整分組／順序只需改 _GROUPS。

建構參數：
    CommandPageV2(parent, app=None)
        app 提供 config_manager（名稱記憶）/ toast（複製回饋）
        app=None 仍可渲染（純預覽；複製到剪貼簿可用，名稱記憶靜默略過）
"""

import logging
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel, QPushButton,
    QScrollArea, QApplication,
)
from PySide6.QtCore import Qt, QSize

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_icon
from src.ui_v2.components import ArrowComboBox

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Command:
    """單一指令定義（資料驅動：增刪指令只動 _COMMANDS）"""
    key: str            # 唯一識別
    label: str          # 卡片顯示的指令關鍵字（需參數者不含 {name}）
    template: str       # 複製用模板；需參數者含 {name} 佔位
    description: str    # 用途說明
    needs_name: bool    # 是否需要玩家名稱參數


# ── 指令目錄（按使用情境分組；分組順序＝頁面呈現順序，常用置頂）──
# 增刪指令或調整分組／順序，只動這份 _GROUPS。
_GROUPS: list[tuple[str, list[_Command]]] = [
    ("常用", [
        _Command("marker", "/箭頭", "/箭頭", "頭頂顯示箭頭標記，Boss 戰找自己很好用", False),
        _Command("hidefx", "/關閉", "/關閉", "關閉其他玩家的攻擊特效與音效，畫面清爽", False),
        _Command("reply", "/回覆", "/回覆", "秒回最後一封密語（也可打 /r）", False),
        _Command("firework", "/放煙火", "/放煙火", "放煙火慶祝（強化成功必備）", False),
    ]),
    ("交易 / 私訊", [
        _Command("trade", "/交換", "/交換 {name}", "遠距交易指定玩家（免擠自由市場）", True),
        _Command("whisper", "/密語", "/密語 {name}", "私訊指定玩家（名稱需含 #代碼，如 Apple#aSqOX）", True),
        _Command("find", "/搜尋", "/搜尋 {name}", "尋找同頻道的指定玩家", True),
    ]),
    ("聊天頻道", [
        _Command("all_chat", "/全體", "/全體", "切換為全體聊天（向頻道內所有玩家發送）", False),
        _Command("area_chat", "/地區", "/地區", "切換為地區聊天（向同張地圖內的玩家發送）", False),
        _Command("party_chat", "/隊伍", "/隊伍", "切換為隊伍聊天（發送給隊員）", False),
        _Command("guild_chat", "/公會", "/公會", "切換為公會聊天（發送給公會成員）", False),
    ]),
    ("隊伍 / 公會", [
        _Command("party_create", "/建立隊伍", "/建立隊伍", "建立一個隊伍", False),
        _Command("party_leave", "/退出隊伍", "/退出隊伍", "離開目前的隊伍", False),
        _Command("party_invite", "/邀請組隊", "/邀請組隊 {name}", "邀請指定玩家加入隊伍（限隊長使用）", True),
        _Command("party_kick", "/踢出隊伍", "/踢出隊伍 {name}", "將指定玩家從隊伍中踢出（限隊長使用）", True),
        _Command("guild_invite", "/邀請進入公會", "/邀請進入公會 {name}", "邀請指定玩家加入公會（限公會長可用）", True),
    ]),
    ("封鎖", [
        _Command("block", "/封鎖", "/封鎖 {name}", "封鎖指定玩家的聊天內容", True),
        _Command("unblock", "/解除封鎖", "/解除封鎖 {name}", "解除對指定玩家的聊天封鎖", True),
    ]),
    ("其他", [
        _Command("location", "/位置", "/位置", "確認目前地圖的位置情況", False),
        _Command("leave_raid", "/離開突擊", "/離開突擊", "離開突擊地圖（限突擊中使用）", False),
        _Command("leave_practice_raid", "/離開練習突擊", "/離開練習突擊", "離開突擊練習地圖（僅限突擊練習中使用）", False),
        _Command("clear_chat", "/刪除聊天", "/刪除聊天", "刪除所有聊天紀錄", False),
        _Command("desummon", "/刪除召喚獸", "/刪除召喚獸", "刪除召喚獸（僅限三眼章魚）", False),
        _Command("help", "/幫助", "/幫助", "查看聊天指令清單", False),
    ]),
]

# 攤平為單一指令清單（名稱記憶刷新等共用；保留向後相容）
_COMMANDS: list[_Command] = [cmd for _, cmds in _GROUPS for cmd in cmds]

_NAME_PLACEHOLDER = "玩家名稱（含 #代碼）"


class CommandPageV2(QWidget):
    """指令快速複製頁 — V2"""

    def __init__(self, parent, app=None):
        super().__init__(parent)
        self.app = app
        self._name_combos: list[ArrowComboBox] = []   # 需參數卡片的名稱下拉，供記憶後統一刷新
        self._build()

    # ── UI ──
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        root.addWidget(T.make_label("指令", T.FONT_SECTION))
        hint = QLabel("點「複製」把指令複製到剪貼簿，切回遊戲貼上即可送出。")
        hint.setTextFormat(Qt.TextFormat.PlainText)
        hint.setStyleSheet(f"color: {T.TEXT_DIM}; background: transparent; font-size: 12px;")
        root.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        host = QWidget()
        col = QVBoxLayout(host)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(T.S_XS)
        for gi, (title, cmds) in enumerate(_GROUPS):
            col.addWidget(self._build_group_header(title, first=(gi == 0)))
            col.addWidget(self._build_group_grid(cmds))
        col.addStretch()
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

    def _build_group_header(self, title: str, first: bool = False) -> QLabel:
        """分組小標題（非首組上方留白以區隔分組）"""
        lbl = T.make_label(title, T.FONT_LABEL, T.TEXT)
        lbl.setContentsMargins(T.S_XS, 0 if first else T.S_SM, 0, 1)
        return lbl

    def _build_group_grid(self, cmds: list[_Command]) -> QWidget:
        """把一組指令卡片排成兩欄（利用橫向空間、一屏塞更多、減少捲動）"""
        host = QWidget()
        grid = QGridLayout(host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(T.S_SM)
        grid.setVerticalSpacing(T.S_XS)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        for i, cmd in enumerate(cmds):
            grid.addWidget(self._build_card(cmd), i // 2, i % 2)
        return host

    def _build_card(self, cmd: _Command) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {T.BG_ELEVATED}; border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_SM}px; }}"
        )
        lay = QHBoxLayout(card)
        lay.setContentsMargins(T.S_MD, T.S_XS, T.S_MD, T.S_XS)
        lay.setSpacing(T.S_SM)

        # 左：指令關鍵字 + 用途說明
        left = QVBoxLayout()
        left.setSpacing(1)
        cmd_lbl = QLabel(cmd.label)
        cmd_lbl.setTextFormat(Qt.TextFormat.PlainText)
        cmd_lbl.setStyleSheet(
            f"color: {T.ORANGE}; background: transparent; font-size: 13px; font-weight: 700;")
        left.addWidget(cmd_lbl)
        desc = QLabel(cmd.description)
        desc.setTextFormat(Qt.TextFormat.PlainText)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {T.TEXT_DIM}; background: transparent; font-size: 11px;")
        left.addWidget(desc)
        lay.addLayout(left, 1)

        # 中：需參數 → 可編輯名稱下拉（打新的或選最近用過的）
        combo = None
        if cmd.needs_name:
            combo = ArrowComboBox()
            combo.setEditable(True)
            combo.setFixedHeight(26)
            combo.setMinimumWidth(150)
            combo.setStyleSheet(
                f"QComboBox {{ background: {T.BG_SURFACE}; color: {T.TEXT};"
                f" border: 1px solid {T.BORDER_SOFT}; border-radius: {T.R_SM}px;"
                f" padding: 0 10px; font-size: 12px; }}"
                f"QComboBox:hover {{ border-color: {T.BORDER_HOVER}; }}"
                f"QComboBox::drop-down {{ border: none; width: 16px; }}"
                + T.combo_popup_qss()
            )
            combo.lineEdit().setPlaceholderText(_NAME_PLACEHOLDER)
            self._refresh_combo(combo)
            self._name_combos.append(combo)
            lay.addWidget(combo)

        # 右：複製鈕
        copy_btn = QPushButton("複製")
        copy_btn.setIcon(lucide_icon("copy", "#ffffff", 14, stroke=1.8))
        copy_btn.setIconSize(QSize(14, 14))
        copy_btn.setFixedHeight(26)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(
            f"QPushButton {{ background: {T.ORANGE}; color: #ffffff; border: none;"
            f" border-radius: {T.R_SM}px; padding: 0 16px; font-size: 12px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: #ff9d5a; }}"
        )
        copy_btn.clicked.connect(
            lambda _=False, c=cmd, cb=combo: self._on_copy(c, cb))
        lay.addWidget(copy_btn)
        return card

    # ── 名稱記憶 ──
    def _recent_names(self) -> list[str]:
        cm = getattr(self.app, "config_manager", None)
        if cm is None:
            return []
        try:
            return cm.get_recent_command_names()
        except Exception:
            logger.exception("讀取最近指令玩家名稱失敗")
            return []

    def _remember_name(self, name: str):
        """記住一個玩家名稱（委派給 config_manager；app / config_manager 缺席則略過）"""
        cm = getattr(self.app, "config_manager", None)
        if cm is None:
            return
        try:
            cm.add_recent_command_name(name)
        except Exception:
            logger.exception("記錄指令玩家名稱失敗")

    def _refresh_combo(self, combo: ArrowComboBox):
        """以最近用過的名稱填充下拉，保留使用者正在輸入的文字"""
        cur = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(self._recent_names())
        combo.setCurrentText(cur)
        combo.blockSignals(False)

    def _refresh_all_combos(self):
        for combo in self._name_combos:
            self._refresh_combo(combo)

    # ── 複製 ──
    def _on_copy(self, cmd: _Command, combo: ArrowComboBox | None):
        if cmd.needs_name:
            name = (combo.currentText().strip() if combo is not None else "")
            # name 為空 → format 後為「關鍵字 + 空格」（如 "/交換 "）
            text = cmd.template.format(name=name)
            if name:
                self._remember_name(name)
                self._refresh_all_combos()
        else:
            text = cmd.template

        QApplication.clipboard().setText(text)
        self._toast(f"已複製：{text}")

    def _toast(self, msg: str):
        toast = getattr(self.app, "toast", None)
        if toast is None:
            return
        try:
            toast.show(msg, "success")
        except Exception:
            logger.exception("顯示 toast 失敗")
