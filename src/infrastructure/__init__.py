"""
基礎設施層模組
提供檔案 I/O、資料持久化、網路通訊、音效播放等基礎設施功能
"""

from src.infrastructure.config_manager import ConfigManager
from src.infrastructure.helpers import resource_path, user_data_path
from src.infrastructure.skill_loader import SkillLoader

__all__ = [
    "BroadcastManager",
    "ConfigManager",
    "SkillLoader",
    "SoundManager",
    "resource_path",
    "user_data_path",
]


def __getattr__(name: str):
    """延遲載入有副作用的模組，避免 import src.infrastructure 時觸發 DLL 載入"""
    if name == "SoundManager":
        from src.infrastructure.sound_manager import SoundManager
        return SoundManager
    if name == "BroadcastManager":
        from src.infrastructure.broadcast_manager import BroadcastManager
        return BroadcastManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
