"""
領域模型模組
定義純 Python 領域實體，封裝資料型別與業務規則。

此模組為整潔架構的 Domain Layer，零 Qt 依賴。
現有程式碼仍使用 raw dict，此層為後續遷移的基礎。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SkillMetadata:
    """不可變技能／道具元資料，對應 config.json skills/items 靜態區"""

    id: str
    name: str
    icon: str
    cooldown: int
    category: str
    subcategory: str


@dataclass
class SkillState:
    """每配置可變技能狀態，對應 profiles/{name}.json 的各欄位"""

    hotkey: str = ""
    permanent: bool = False
    loop: bool = False
    alert_enabled: bool = False
    cooldown_override: int | None = None
    alert_seconds_override: int | None = None
    sound_override: str = ""
    alert_sound_override: str = ""

    def set_permanent(self, value: bool) -> None:
        """設定 permanent，啟用時自動關閉 loop（互斥規則）"""
        self.permanent = value
        if value:
            self.loop = False

    def set_loop(self, value: bool) -> None:
        """設定 loop，啟用時自動關閉 permanent（互斥規則）"""
        self.loop = value
        if value:
            self.permanent = False


@dataclass
class Profile:
    """使用者配置，聚合所有技能的 SkillState"""

    name: str
    skill_states: dict[str, SkillState] = field(default_factory=dict)

    def get_state(self, skill_id: str) -> SkillState:
        """取得指定技能的狀態，不存在時自動建立預設值"""
        if skill_id not in self.skill_states:
            self.skill_states[skill_id] = SkillState()
        return self.skill_states[skill_id]


@dataclass
class MonsterData:
    """怪物重生資料，對應 config.json monsters 區"""

    id: str
    name: str
    icon: str
    respawn_time: int
    hotkey: str = ""
    alert_before: int = 0
    loop: bool = False
    permanent: bool = False
    sound: str = ""
    alert_sound: str = ""


@dataclass
class OverlayData:
    """浮動圖片資料，對應 config.json overlays 區"""

    id: str
    name: str
    file: str
    alpha: float = 1.0
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


@dataclass
class GlobalSettings:
    """跨配置全域設定，對應 config.json settings 區"""

    player_name: str = "玩家1"
    skill_start_x: int = 0
    skill_start_y: int = 0
    enable_sound: bool = True
    window_size: int = 64
    alert_before_seconds: int = 0
    global_sound: str = ""
    global_alert_sound: str = ""
    current_profile: str = "預設配置"
