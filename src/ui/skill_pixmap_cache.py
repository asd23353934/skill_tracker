"""
技能圖片快取模組
處理技能圖片的載入與多尺寸 QPixmap 快取
PySide6 版本：圖片使用 QPixmap 快取（lazy load；首次被 .get() 要求時才解碼）
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image
from PySide6.QtGui import QImage, QPixmap

from src.infrastructure.helpers import resource_path

if TYPE_CHECKING:
    from src.infrastructure.skill_loader import SkillLoader


# 多尺寸：屬性名 → 目標邊長
_SIZE_VARIANTS: dict[str, int] = {
    "qpixmaps":        50,  # 主 UI
    "qpixmaps_small":  28,  # 小圖示
    "qpixmaps_medium": 64,  # 倒數視窗
    "qpixmaps_card":   36,  # 技能卡片
}


def _pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """PIL RGBA Image → QPixmap"""
    pil_img = pil_img.convert("RGBA")
    data = pil_img.tobytes("raw", "RGBA")
    qimg = QImage(data, pil_img.width, pil_img.height,
                  QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)


class _LazyPixmapDict:
    """dict-like 延遲解碼代理。

    首次 `.get(skill_id)` / `[skill_id]` 觸發 cache 把該 skill 的四種尺寸
    全部解碼（一次 I/O 多個 resize 比分別讀取便宜），之後走 dict 命中。

    對外維持 `get()` / `__getitem__` / `__contains__` / `__setitem__` 等
    dict 語義，現有呼叫端（`cache.get(skill_id)`）無需改動。
    """

    __slots__ = ("_cache", "_size", "_data")

    def __init__(self, cache: SkillPixmapCache, size: int) -> None:
        self._cache = cache
        self._size = size
        self._data: dict[str, QPixmap | None] = {}

    def _ensure(self, skill_id: str) -> None:
        if skill_id in self._data:
            return
        self._cache._load_skill_pixmaps(skill_id)

    def get(self, skill_id: str, default=None):
        self._ensure(skill_id)
        return self._data.get(skill_id, default)

    def __getitem__(self, skill_id: str):
        self._ensure(skill_id)
        return self._data[skill_id]

    def __setitem__(self, skill_id: str, value) -> None:
        self._data[skill_id] = value

    def __contains__(self, skill_id: str) -> bool:
        return skill_id in self._data

    def __len__(self) -> int:
        return len(self._data)

    def clear(self) -> None:
        self._data.clear()


class SkillPixmapCache:
    """技能圖片快取 — 包裝 SkillLoader；lazy 解碼 QPixmap。

    啟動只索引檔名（無 I/O）；首次對某 skill_id 取圖才開啟檔案並一次
    解出四種尺寸（50 / 28 / 64 / 36）。
    """

    def __init__(self, skill_loader: SkillLoader) -> None:
        self.skill_loader = skill_loader
        self.skill_image_paths: dict[str, str] = {}

        self.qpixmaps:        _LazyPixmapDict = _LazyPixmapDict(self, 50)
        self.qpixmaps_small:  _LazyPixmapDict = _LazyPixmapDict(self, 28)
        self.qpixmaps_medium: _LazyPixmapDict = _LazyPixmapDict(self, 64)
        self.qpixmaps_card:   _LazyPixmapDict = _LazyPixmapDict(self, 36)

        self._index_all_paths()

    def _index_all_paths(self) -> None:
        """只登錄檔案路徑，不開檔；開檔留給 lazy load。"""
        for skill_id, skill_data in self.skill_loader.get_all_skills().items():
            self.skill_image_paths[skill_id] = resource_path(
                f"images/{skill_data['icon']}"
            )

    def _load_skill_pixmaps(self, skill_id: str) -> None:
        """為單一 skill_id 解出四種尺寸並寫入四個快取 dict。

        缺圖 / 解碼失敗 → 四個 dict 都寫 None，之後命中不重試。
        """
        path = self.skill_image_paths.get(skill_id)
        if not path:
            # 技能不存在；全標 None 以短路後續 lookup
            for attr in _SIZE_VARIANTS:
                getattr(self, attr)._data[skill_id] = None
            return

        try:
            img = Image.open(path).convert("RGBA")
            for attr, size in _SIZE_VARIANTS.items():
                getattr(self, attr)._data[skill_id] = _pil_to_qpixmap(
                    img.resize((size, size), Image.Resampling.LANCZOS)
                )
        except Exception:
            for attr in _SIZE_VARIANTS:
                getattr(self, attr)._data[skill_id] = None

    def preload_all(self) -> None:
        """強制解碼所有技能圖片（測試 / 舊行為還原用）。"""
        for skill_id in self.skill_loader.get_all_skills():
            self._load_skill_pixmaps(skill_id)

    # --------------------------------------------------
    # SkillLoader 委派 API（向後相容）
    # --------------------------------------------------

    @property
    def config_manager(self):
        return self.skill_loader.config_manager

    @property
    def skills(self) -> dict[str, dict]:
        return self.skill_loader.skills

    @property
    def skill_categories(self) -> dict:
        return self.skill_loader.skill_categories

    def get_skill(self, skill_id: str) -> dict | None:
        return self.skill_loader.get_skill(skill_id)

    def get_all_skills(self) -> dict[str, dict]:
        return self.skill_loader.get_all_skills()

    def get_categories(self, category_type: str = None) -> dict:
        return self.skill_loader.get_categories(category_type)

    def update_hotkey(self, skill_id: str, hotkey: str) -> bool:
        return self.skill_loader.update_hotkey(skill_id, hotkey)

    def clear_all_hotkeys(self) -> None:
        self.skill_loader.clear_all_hotkeys()

    def get_skill_by_hotkey(self, hotkey: str) -> str | None:
        return self.skill_loader.get_skill_by_hotkey(hotkey)
