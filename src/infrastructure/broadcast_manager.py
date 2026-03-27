"""
頻道廣播管理模組
封包擷取、訊息解析、黑名單過濾、訊息上限管理
參考 Artale-Channel-Broadcast-System 的 ChatParser 實作
"""

import struct
import threading
import logging
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)

# Scapy 可能未安裝或 Npcap 不可用
SCAPY_AVAILABLE = False
try:
    from scapy.all import AsyncSniffer, TCP
    SCAPY_AVAILABLE = True
except Exception:
    logger.warning("Scapy 不可用，頻道廣播功能將無法使用")


class ChatParser:
    """Artale 遊戲頻道廣播封包解析器"""

    @staticmethod
    def _parse_struct(data: bytes) -> dict:
        """解析 TOZ 封包內的欄位結構

        Args:
            data: TOZ 標記後的二進位資料（已跳過 8 bytes header）

        Returns:
            解析後的欄位字典
        """
        out = {}
        i, length = 0, len(data)

        while i + 4 <= length:
            name_len = int.from_bytes(data[i:i + 4], "little")
            if not 0 < name_len <= 64 or i + 4 + name_len + 6 > length:
                i += 1
                continue

            try:
                name = data[i + 4:i + 4 + name_len].decode("ascii")
            except UnicodeDecodeError:
                i += 1
                continue

            cur = i + 4 + name_len
            # type_tag = int.from_bytes(data[cur:cur + 2], "little")  # noqa: E800
            val_len = int.from_bytes(data[cur + 2:cur + 6], "little")

            if val_len > 256 or cur + 6 + val_len > length:
                i += 1
                continue

            value = data[cur + 6:cur + 6 + val_len].decode("utf-8", "replace")
            out[name] = value
            i = cur + 6 + val_len

        # 頻道偵測：搜尋 02 XX XX XX XX 04 模式
        for k in range(len(data) - 5):
            if data[k] == 0x02 and data[k + 5] == 0x04:
                ch_val = int.from_bytes(data[k + 1:k + 5], "little")
                if 1 <= ch_val <= 9999:
                    out["Channel"] = f"CH{ch_val}"
                    break

        return out

    @classmethod
    def parse_packet_bytes(cls, blob: bytes) -> dict | None:
        """解析完整 TOZ 封包

        Args:
            blob: 包含 TOZ 標記的完整封包資料

        Returns:
            解析結果字典，或 None（若解析失敗）
        """
        if len(blob) <= 8:
            return None
        result = cls._parse_struct(blob[8:])
        if not result.get("Nickname") or not result.get("Text"):
            return None
        return result


class BroadcastMessage:
    """單一廣播訊息"""

    __slots__ = ("channel", "nickname", "user_id", "text", "timestamp", "friend_tag")

    def __init__(self, channel: str, nickname: str, user_id: str, text: str):
        self.channel = channel
        self.nickname = nickname
        self.user_id = user_id
        self.text = text
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.friend_tag = f"{nickname}#{user_id}" if user_id else nickname


class BroadcastManager:
    """頻道廣播管理器 — 封包擷取與訊息管理"""

    SNIFF_PORT = 32800

    def __init__(self, app):
        """初始化管理器

        Args:
            app: App 主應用實例
        """
        self.app = app
        self._sniffer = None
        self._running = False
        self._messages: deque[BroadcastMessage] = deque()
        self._on_message_callback = None
        self._max_messages = self.app.config_manager.get_settings(
            "broadcast_max_messages", 200
        )

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def messages(self) -> list[BroadcastMessage]:
        return list(self._messages)

    def set_on_message(self, callback):
        """設定新訊息回呼

        Args:
            callback: 接收 BroadcastMessage 的回呼函數（在主執行緒呼叫）
        """
        self._on_message_callback = callback

    def start(self) -> str | None:
        """啟動封包監聽

        Returns:
            錯誤訊息（str）或 None（成功）
        """
        if self._running:
            return None

        if not SCAPY_AVAILABLE:
            return "Scapy 未安裝或 Npcap 不可用，請先安裝 Npcap"

        try:
            self._sniffer = AsyncSniffer(
                filter=f"tcp port {self.SNIFF_PORT}",
                prn=self._on_packet,
                store=False,
            )
            self._sniffer.start()
            self._running = True
            return None
        except Exception as e:
            logger.error("封包監聽啟動失敗: %s", e)
            return f"啟動失敗：{e}\n請確認已安裝 Npcap 並以管理員身分執行"

    def stop(self):
        """停止封包監聽"""
        if not self._running:
            return
        self._running = False
        if self._sniffer:
            try:
                self._sniffer.stop()
            except Exception:
                pass
            self._sniffer = None

    def clear(self):
        """清除所有訊息"""
        self._messages.clear()

    def is_blacklisted(self, friend_tag: str) -> bool:
        """檢查是否在黑名單"""
        blacklist = self.app.config_manager.get_settings("broadcast_blacklist", [])
        return friend_tag in blacklist

    def add_to_blacklist(self, friend_tag: str):
        """加入黑名單"""
        blacklist = self.app.config_manager.get_settings("broadcast_blacklist", [])
        if friend_tag not in blacklist:
            blacklist.append(friend_tag)
            self.app.config_manager.set_settings("broadcast_blacklist", blacklist)
            self.app.config_manager.save()

    def remove_from_blacklist(self, friend_tag: str):
        """從黑名單移除"""
        blacklist = self.app.config_manager.get_settings("broadcast_blacklist", [])
        if friend_tag in blacklist:
            blacklist.remove(friend_tag)
            self.app.config_manager.set_settings("broadcast_blacklist", blacklist)
            self.app.config_manager.save()

    def get_blacklist(self) -> list[str]:
        """取得黑名單"""
        return self.app.config_manager.get_settings("broadcast_blacklist", [])

    # --------------------------------------------------
    # 封包處理（daemon thread 中執行）
    # --------------------------------------------------

    def _on_packet(self, pkt):
        """Scapy 封包回呼 — 在 sniffer thread 中執行，不可直接操作 UI"""
        try:
            if not pkt.haslayer(TCP):
                return
            payload = bytes(pkt[TCP].payload)
            if not payload:
                return

            idx = payload.find(b"TOZ ")
            while idx >= 0 and idx + 8 <= len(payload):
                size = int.from_bytes(payload[idx + 4:idx + 8], "little")
                if idx + 8 + size > len(payload):
                    break

                blob = payload[idx:idx + 8 + size]
                parsed = ChatParser.parse_packet_bytes(blob)
                if parsed:
                    self._dispatch_message(parsed)

                idx = payload.find(b"TOZ ", idx + 1)
        except Exception:
            pass  # 靜默丟棄格式錯誤的封包

    def _dispatch_message(self, parsed: dict):
        """將解析後的訊息排回主執行緒"""
        msg = BroadcastMessage(
            channel=parsed.get("Channel", ""),
            nickname=parsed.get("Nickname", ""),
            user_id=parsed.get("UserId", ""),
            text=parsed.get("Text", ""),
        )

        # 黑名單過濾
        if self.is_blacklisted(msg.friend_tag):
            return

        # 訊息上限
        if len(self._messages) >= self._max_messages:
            self._messages.popleft()
        self._messages.append(msg)

        # 排回主執行緒
        if self._on_message_callback:
            self.app.after(0, lambda: self._on_message_callback(msg))
