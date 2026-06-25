"""
指令快速複製頁 — V2

列出 Artale 遊戲內常用聊天指令（按使用情境分組、常用置頂），每個一鍵複製到系統剪貼簿
（玩家切回遊戲貼上即可送出）。

需玩家名稱的指令（標 needs_name 者，如 交換 / 密語 / 邀請 / 封鎖）以「名稱 chips」呈現：
- 點擊某個名稱 chip → 立即把「指令模板填入該名稱」複製到剪貼簿（cmd.template 的 {name}）。
- chip 上的 ✎ 就地改名、× 刪除。
- 下方「新增名稱」輸入送出 → 複製「指令＋名稱」並把名稱保存為新 chip；空送出 → 複製
  「關鍵字＋單一尾空格」且不新增。

名單為「每個指令各自一份」，存於 config_user.json 的 settings.command_names（以指令 key 分組），
讀寫委派給 ConfigManager.get/add/remove/rename_command_name；升級相容舊共用 command_recent_names。

指令按使用情境分組定義於 _GROUPS（再攤平為 _COMMANDS 供共用）；增刪指令或調整分組／順序只需改 _GROUPS。

建構參數：
    CommandPageV2(parent, app=None)
        app 提供 config_manager（名稱 CRUD）/ toast（複製回饋）
        app=None 仍可渲染（純預覽；複製到剪貼簿可用，名稱 CRUD 靜默略過）
"""

import logging
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QScrollArea, QApplication, QLineEdit, QPushButton,
)
from PySide6.QtCore import Qt, QSize

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_icon
from src.ui_v2.components import make_primary_button
from src.ui_v2.flow_layout import FlowLayout

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Command:
    """單一指令定義（資料驅動：增刪指令只動 _GROUPS）"""
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

# 攤平為單一指令清單（共用；保留向後相容）
_COMMANDS: list[_Command] = [cmd for _, cmds in _GROUPS for cmd in cmds]

_NAME_PLACEHOLDER = "輸入玩家名稱（含 #代碼）後按複製"


# ════════════════════════════════════════════════════════════
# _NameChip — 單一名稱 chip（點本體複製 / ✎ 改名 / × 刪除）
# ════════════════════════════════════════════════════════════

class _ChipLineEdit(QLineEdit):
    """chip 就地編輯用輸入框：Esc 取消編輯（透過 callback）"""

    def __init__(self, text: str, on_cancel):
        super().__init__(text)
        self._on_cancel = on_cancel

    def keyPressEvent(self, e):  # noqa: N802
        if e.key() == Qt.Key.Key_Escape:
            self._on_cancel()
            return
        super().keyPressEvent(e)


class _NameChip(QFrame):
    """名稱 chip：點本體 → 複製；✎ → 就地改名；× → 刪除。

    所有持久化／複製委派給 callback（由 _NeedsNameCard 提供）：
        on_copy(name) / on_delete(name) / on_rename(old, new)
    改名／刪除後由上層重建 chips，本 widget 會被回收。
    """

    def __init__(self, name: str, on_copy, on_delete, on_rename):
        super().__init__()
        self._name = name
        self._on_copy = on_copy
        self._on_delete = on_delete
        self._on_rename = on_rename
        self._editing = False
        self._committed = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QFrame {{ background: {T.BG_INPUT}; border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_SM}px; }}"
            f"QFrame:hover {{ border-color: {T.ORANGE}; }}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(T.S_SM, 2, 4, 2)
        lay.setSpacing(4)

        self._label = QLabel(name)
        self._label.setTextFormat(Qt.TextFormat.PlainText)
        self._label.setToolTip("點擊複製此名稱的指令")
        self._label.setStyleSheet(
            f"color: {T.TEXT_HI}; background: transparent; font-size: 12px;"
            f" font-weight: 600;")
        lay.addWidget(self._label)

        self._edit = _ChipLineEdit(name, self._cancel_edit)
        self._edit.setFixedHeight(20)
        self._edit.setMinimumWidth(120)
        self._edit.setStyleSheet(
            f"QLineEdit {{ color: {T.TEXT_HI}; background: {T.BG_SURFACE};"
            f" border: 1px solid {T.ORANGE}; border-radius: {T.R_SM}px;"
            f" padding: 0 4px; font-size: 12px; }}")
        self._edit.returnPressed.connect(self._commit_edit)
        self._edit.editingFinished.connect(self._on_edit_finished)
        self._edit.hide()
        lay.addWidget(self._edit)

        self._edit_btn = self._mini_btn("pencil", "改名", T.TEXT_DIM, self._enter_edit)
        lay.addWidget(self._edit_btn)
        self._del_btn = self._mini_btn("x", "刪除", T.TEXT_DIM, self._on_delete_clicked,
                                       hover_red=True)
        lay.addWidget(self._del_btn)

    def _mini_btn(self, icon: str, tip: str, color: str, slot, hover_red: bool = False):
        b = QPushButton()
        b.setIcon(lucide_icon(icon, color, 12, stroke=1.8))
        b.setIconSize(QSize(12, 12))
        b.setFixedSize(18, 18)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setToolTip(tip)
        hover_bg = T.RED if hover_red else T.BG_HOVER
        b.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none;"
            f" border-radius: {T.R_SM}px; padding: 0; }}"
            f"QPushButton:hover {{ background: {hover_bg}; }}")
        b.clicked.connect(slot)
        return b

    # ── 互動 ──
    def mousePressEvent(self, e):  # noqa: N802
        # 編輯中或點到子按鈕時不觸發複製（按鈕會自行消化點擊）
        if not self._editing and e.button() == Qt.MouseButton.LeftButton:
            self._on_copy(self._name)
        super().mousePressEvent(e)

    def _on_delete_clicked(self):
        self._on_delete(self._name)

    def _enter_edit(self):
        self._editing = True
        self._label.hide()
        self._edit_btn.hide()
        self._del_btn.hide()
        self._edit.setText(self._name)
        self._edit.show()
        self._edit.setFocus()
        self._edit.selectAll()

    def _cancel_edit(self):
        """Esc：放棄編輯，還原顯示（不改名）"""
        if not self._editing:
            return
        self._editing = False
        self._edit.hide()
        self._label.show()
        self._edit_btn.show()
        self._del_btn.show()

    def _on_edit_finished(self):
        # 失焦：視為取消（只有 Enter 才提交），避免誤改
        if self._editing:
            self._cancel_edit()

    def _commit_edit(self):
        if self._committed:
            return
        self._committed = True
        self._editing = False
        new = self._edit.text().strip()
        # 交給上層處理改名＋重建（本 widget 即將被回收）
        self._on_rename(self._name, new)


# ════════════════════════════════════════════════════════════
# _NeedsNameCard — 需玩家名稱指令卡（名稱 chips ＋ 新增輸入）
# ════════════════════════════════════════════════════════════

class _NeedsNameCard(QFrame):
    """需玩家名稱指令的卡片：上方關鍵字＋說明、中段名稱 chips、下方新增輸入。"""

    def __init__(self, cmd: _Command, page: "CommandPageV2"):
        super().__init__()
        self._cmd = cmd
        self._page = page
        self.setStyleSheet(
            f"QFrame {{ background: {T.BG_ELEVATED}; border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_SM}px; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_MD, T.S_SM, T.S_MD, T.S_SM)
        root.setSpacing(T.S_XS)

        # 上：關鍵字 + 說明
        head = QVBoxLayout()
        head.setSpacing(1)
        cmd_lbl = QLabel(cmd.label)
        cmd_lbl.setTextFormat(Qt.TextFormat.PlainText)
        cmd_lbl.setStyleSheet(
            f"color: {T.ORANGE}; background: transparent; font-size: 13px; font-weight: 700;")
        head.addWidget(cmd_lbl)
        desc = QLabel(cmd.description)
        desc.setTextFormat(Qt.TextFormat.PlainText)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {T.TEXT_DIM}; background: transparent; font-size: 11px;")
        head.addWidget(desc)
        root.addLayout(head)

        # 中：名稱 chips（FlowLayout 自動換行）
        self._chips_host = QWidget()
        self._chips_host.setStyleSheet("background: transparent;")
        self._chips_flow = FlowLayout(self._chips_host, margin=0, h_spacing=6, v_spacing=6)
        root.addWidget(self._chips_host)

        self._empty_hint = QLabel("尚無常用名稱，於下方輸入後按「複製」即記住")
        self._empty_hint.setTextFormat(Qt.TextFormat.PlainText)
        self._empty_hint.setStyleSheet(
            f"color: {T.TEXT_MUTED}; background: transparent; font-size: 11px;")
        root.addWidget(self._empty_hint)

        # 下：新增名稱輸入 + 複製鈕
        add_row = QHBoxLayout()
        add_row.setSpacing(T.S_SM)
        self._input = QLineEdit()
        self._input.setFixedHeight(26)
        self._input.setStyleSheet(
            f"QLineEdit {{ color: {T.TEXT_HI}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 8px; font-size: 12px; }}"
            f"QLineEdit:focus {{ border-color: {T.ORANGE}; }}")
        self._input.setPlaceholderText(_NAME_PLACEHOLDER)
        self._input.returnPressed.connect(self._on_add_submit)
        add_row.addWidget(self._input, 1)

        copy_btn = make_primary_button("複製", padding="0 16px", weight=700, height=26)
        copy_btn.setIcon(lucide_icon("copy", "#ffffff", 14, stroke=1.8))
        copy_btn.setIconSize(QSize(14, 14))
        copy_btn.clicked.connect(self._on_add_submit)
        add_row.addWidget(copy_btn)
        root.addLayout(add_row)

        self.reload_chips()

    # ── chips ──
    def reload_chips(self):
        """清空並依目前名單重建 chips"""
        while self._chips_flow.count():
            item = self._chips_flow.takeAt(0)
            w = item.widget() if item is not None else None
            if w is not None:
                w.setParent(None)   # 立即脫離父層（deleteLater 為非同步，避免殘留 chip）
                w.deleteLater()
        names = self._page.names_for(self._cmd.key)
        for name in names:
            self._chips_flow.addWidget(
                _NameChip(name, self._on_chip_copy, self._on_chip_delete, self._on_chip_rename)
            )
        self._empty_hint.setVisible(not names)
        self._chips_host.setVisible(bool(names))

    def _on_chip_copy(self, name: str):
        self._page.copy_with_name(self._cmd, name)
        self.reload_chips()   # 使用後 MRU 置前，重排 chips

    def _on_chip_delete(self, name: str):
        self._page.delete_name(self._cmd.key, name)
        self.reload_chips()

    def _on_chip_rename(self, old: str, new: str):
        self._page.rename_name(self._cmd.key, old, new)
        self.reload_chips()

    def _on_add_submit(self):
        name = self._input.text().strip()
        self._page.copy_and_remember(self._cmd, name)
        self._input.clear()
        self.reload_chips()


class CommandPageV2(QWidget):
    """指令快速複製頁 — V2"""

    def __init__(self, parent, app=None):
        super().__init__(parent)
        self.app = app
        self._build()

    # ── UI ──
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        root.addWidget(T.make_label("指令", T.FONT_SECTION))
        hint = QLabel("點「複製」或名稱小塊把指令複製到剪貼簿，切回遊戲貼上即可送出。")
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
            col.addWidget(self._build_group_body(cmds))
        col.addStretch()
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

    def _build_group_header(self, title: str, first: bool = False) -> QLabel:
        """分組小標題（非首組上方留白以區隔分組）"""
        lbl = T.make_label(title, T.FONT_LABEL, T.TEXT)
        lbl.setContentsMargins(T.S_XS, 0 if first else T.S_SM, 0, 1)
        return lbl

    def _build_group_body(self, cmds: list[_Command]) -> QWidget:
        """一組指令：no-arg 卡片兩欄並排、needs_name 卡片整列（保留 _GROUPS 順序）"""
        host = QWidget()
        v = QVBoxLayout(host)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(T.S_XS)

        pending: list[_Command] = []   # 暫存待配對的 no-arg 卡片

        def flush_pair():
            if not pending:
                return
            v.addWidget(self._build_pair_row(pending))
            pending.clear()

        for cmd in cmds:
            if cmd.needs_name:
                flush_pair()
                v.addWidget(_NeedsNameCard(cmd, self))
            else:
                pending.append(cmd)
                if len(pending) == 2:
                    flush_pair()
        flush_pair()
        return host

    def _build_pair_row(self, cmds: list[_Command]) -> QWidget:
        """把 1–2 個 no-arg 指令卡片排成一列（不足兩個則左半佔位）"""
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(T.S_SM)
        for cmd in cmds:
            h.addWidget(self._build_simple_card(cmd), 1)
        if len(cmds) == 1:
            h.addStretch(1)
        return row

    def _build_simple_card(self, cmd: _Command) -> QFrame:
        """no-argument 指令卡片：關鍵字 + 說明 + 複製鈕"""
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {T.BG_ELEVATED}; border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_SM}px; }}")
        lay = QHBoxLayout(card)
        lay.setContentsMargins(T.S_MD, T.S_XS, T.S_MD, T.S_XS)
        lay.setSpacing(T.S_SM)

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

        copy_btn = make_primary_button("複製", padding="0 16px", weight=700, height=26)
        copy_btn.setIcon(lucide_icon("copy", "#ffffff", 14, stroke=1.8))
        copy_btn.setIconSize(QSize(14, 14))
        copy_btn.clicked.connect(lambda _=False, c=cmd: self._copy(c.template))
        lay.addWidget(copy_btn)
        return card

    # ── 名稱 CRUD（委派 ConfigManager；app / config_manager 缺席則安全略過）──
    def _cm(self):
        return getattr(self.app, "config_manager", None)

    def names_for(self, key: str) -> list[str]:
        cm = self._cm()
        if cm is None:
            return []
        try:
            return cm.get_command_names(key)
        except Exception:
            logger.exception("讀取指令名稱失敗：%s", key)
            return []

    def delete_name(self, key: str, name: str):
        cm = self._cm()
        if cm is None:
            return
        try:
            cm.remove_command_name(key, name)
        except Exception:
            logger.exception("刪除指令名稱失敗：%s / %s", key, name)

    def rename_name(self, key: str, old: str, new: str):
        cm = self._cm()
        if cm is None:
            return
        try:
            cm.rename_command_name(key, old, new)
        except Exception:
            logger.exception("改名指令名稱失敗：%s / %s → %s", key, old, new)

    def _remember(self, key: str, name: str):
        cm = self._cm()
        if cm is None:
            return
        try:
            cm.add_command_name(key, name)
        except Exception:
            logger.exception("記錄指令名稱失敗：%s / %s", key, name)

    # ── 複製 ──
    def copy_with_name(self, cmd: _Command, name: str):
        """以指定名稱複製指令（點 chip 用）；非空名稱使用後 MRU 置前"""
        self._copy(cmd.template.format(name=name))
        if name:
            self._remember(cmd.key, name)

    def copy_and_remember(self, cmd: _Command, name: str):
        """新增輸入送出：非空 → 複製並記住（MRU 置前）；空 → 複製關鍵字＋單一尾空格不新增"""
        if name:
            self.copy_with_name(cmd, name)
        else:
            self._copy(cmd.template.format(name=""))

    def _copy(self, text: str):
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
