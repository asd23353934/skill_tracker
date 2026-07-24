"""
V2 ChangelogDialog — 更新日記（唯讀，資料來源為 version.get_changelog()）

側邊欄版本號點擊開啟；把 version.py 的 CHANGELOG 字串依 vX.Y.Z (YYYY-MM-DD)
標頭切成一筆一筆版本區塊，最新在最上面，每個版本一張卡片呈現。
"""

from __future__ import annotations

import re

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QScrollArea
from PySide6.QtCore import Qt

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.dialogs.base_dialog_v2 import BaseDialogV2

import version


_VERSION_HEADER_RE = re.compile(
    r"^v(?P<version>\S+)\s*\((?P<date>[^)]*)\)\s*$", re.MULTILINE
)
_SEPARATOR_LINE_RE = re.compile(r"^-+$")


def _strip_leading_separator(body: str) -> str:
    """body 第一行若是純 '-' 組成的分隔線則丟棄該行"""
    lines = body.split("\n", 1)
    if lines and _SEPARATOR_LINE_RE.match(lines[0].strip()):
        return lines[1] if len(lines) > 1 else ""
    return body


def _parse_changelog(text: str) -> list[tuple[str, str, str]]:
    """把 CHANGELOG 原始字串切成 (version, date, body) 的 list，保留原始順序（新到舊）。

    找不到任何 vX.Y.Z (YYYY-MM-DD) 標頭時，整段文字當作單一區塊，
    標頭用目前版本號頂上，不拋例外、不回傳空清單。
    """
    matches = list(_VERSION_HEADER_RE.finditer(text))
    if not matches:
        return [(version.get_version(), "", text.strip())]

    blocks: list[tuple[str, str, str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw_body = text[start:end].strip("\n")
        body = _strip_leading_separator(raw_body).strip()
        blocks.append((m.group("version"), m.group("date"), body))
    return blocks


class ChangelogDialogV2(BaseDialogV2):
    """更新日記對話框（純顯示，無 footer 操作）"""

    def __init__(self, parent=None):
        super().__init__(parent, title="更新日記", width=480, height=560)
        self._build_body()

    def _build_body(self):
        body = self.body_layout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        host = QWidget()
        col = QVBoxLayout(host)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(T.S_SM)

        for ver, date, entry_body in _parse_changelog(version.get_changelog()):
            col.addWidget(self._build_version_card(ver, date, entry_body))
        col.addStretch()

        scroll.setWidget(host)
        body.addWidget(scroll, 1)

    def _build_version_card(self, ver: str, date: str, body: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {T.BG_ELEVATED}; border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_SM}px; }}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(T.S_MD, T.S_SM, T.S_MD, T.S_SM)
        lay.setSpacing(T.S_XS)

        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(T.make_label(f"v{ver}", T.FONT_CARD_TITLE, T.ORANGE))
        if date:
            date_lbl = T.make_label(date, T.FONT_CAPTION)
            date_lbl.setTextFormat(Qt.TextFormat.PlainText)
            head.addWidget(date_lbl)
        head.addStretch()
        lay.addLayout(head)

        body_lbl = T.make_label(body if body else "（無更新內容）", T.FONT_BODY, T.TEXT_DIM)
        body_lbl.setTextFormat(Qt.TextFormat.PlainText)
        body_lbl.setWordWrap(True)
        lay.addWidget(body_lbl)

        return card
