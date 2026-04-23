## Summary

把 V2 monster 頁從目前的最小接線（所有按鈕都 `_toast_pending`）升級為完整接線：實際列出當前 profile 內的怪物卡片、抓 hotkey、編輯 respawn time / alert 秒數 / loop / permanent / 音效，與 V1 共用同一份 MonsterService + WindowManager + HotkeyManager 狀態。

## Motivation

V2 preview shell（`python main.py --v2`）目前 monster 頁只顯示 4 張 demo 卡片（DEMO_MONSTERS hardcoded），所有交互都跳「此功能尚未接 V2」toast。`wire-v2-app-context` 已把 SkillManager / HotkeyManager / WindowManager / SoundManager 連同 6 個 SkillService delegate property 全部上抬到 `AppCoreMixin`，V2AppContext 已可呼叫；缺的只剩 V1 App 內 8 個怪物互動方法（`edit_respawn_time` / `reset_respawn_time` / `reset_monster_hotkey` / `edit_monster_alert_before` / `update_monster_alert_sound` / `update_monster_end_sound` / `update_monster_loop` / `update_monster_permanent`）尚在 `src/ui/app.py` 而非 `app_core.py`。

把這 8 個方法上移 mixin、再讓 V2 MonsterCard 直接呼叫 `app.xxx`、列表改讀 `app.get_all_monsters()` 即可完成接線。MonsterService 既有 API 完備，無需擴充。

## Proposed Solution

1. **AppCoreMixin 補齊 8 個怪物方法**：把 V1 App 內的 `edit_respawn_time` / `reset_respawn_time` / `reset_monster_hotkey` / `edit_monster_alert_before` / `update_monster_alert_sound` / `update_monster_end_sound` / `update_monster_loop` / `update_monster_permanent` 整批搬到 `src/ui/app_core.py`，與 12 個技能方法平行。V1 App 透過 mixin 繼承；V2AppContext 自動取得。簽名 / 行為一字不變，避免 V1 regression。

2. **V2 monster 頁列表動態化**：`MonsterPageV2._build` 移除 `DEMO_MONSTERS` 迴圈，改在 `showEvent` 第一次顯示時呼叫 `self.app.get_all_monsters()` 取得 profile 內所有怪物，逐一 instantiate `MonsterCard(parent, app, monster_dict)`。卡片 `__init__` 介面從現行 (parent, name, icon_name, respawn, hotkey, alert_before, loop, permanent, alert_sound, end_sound) 簡化為 (parent, app, monster_id)，內部讀 `monster_service.get(id)` 取最新狀態，與 SkillCardV2 一致。

3. **MonsterCard 接線**：cooldown chip → `app.edit_respawn_time(id)`、reset → `app.reset_respawn_time(id)`；hotkey chip → `app.hotkey_manager.begin_capture(id, name)`、reset → `app.reset_monster_hotkey(id)`；alert pill → `app.edit_monster_alert_before(id)`；loop / permanent checkbox → `app.update_monster_loop / update_monster_permanent`；音效 combo → `app.update_monster_end_sound / update_monster_alert_sound`。所有按鈕在 `app.monster_respawn_buttons[id]` / `app.monster_alert_before_buttons[id]` 註冊，與 V1 共用 dict。

4. **HotkeyManager 解耦**：V1 在 `_MonsterCard._begin_hotkey_capture` 內設了 `self.app.hotkey_manager._monster_card = self` 供事後 callback 找回卡片。V2 MonsterCard 沿用同欄位但寫的是 V2 卡片實例；HotkeyManager callback 在綁定完成後 setText 用 `getattr(card, "set_hotkey_text", card.update_hotkey_display)` 容錯呼叫，V1 / V2 卡片各自實作對應 method。

5. **移除 V2 monster 頁「新增怪物」按鈕**：V1 沒有此 UI，怪物清單由 `config.json` curated；按鈕保留只會永遠 toast_pending。直接刪除 `add_btn` 區塊，header 留 title + hint。

## Non-Goals

- **不實作 add / delete monster CRUD**：V1 沒有此 UI，怪物為 game-defined boss；移除 V2 「新增怪物」按鈕，相關 MonsterService.add() / delete() 方法不引入。
- **不簡化全域 HeaderV2**（greeting / 鈴鐺 / 人 / + button / 配置 dropdown 移位）：另開獨立 spec。
- **不改 MonsterService 公開 API**：所有方法（set_respawn_time / set_hotkey / set_loop / …）維持現狀。
- **不改 `config.json` 的 monsters schema**。
- **不重做 V2 monster card 視覺**：沿用 wire-v2-skill-page 的 V2 chip / pill / checkbox 元件。
- **不接 V1 SoundDialog**：V2 卡片暫不支援 quickly-edit-sound（可在後續 spec 補；現行 V1 也只在 detail dialog 內改）。

## Alternatives Considered

- **不搬方法、V2 直接呼叫 `app.monster_service.set_respawn_time(...)`**：跳過 V1 的 dialog wrapper、行為不一致（V1 點 chip 開 input dialog；V2 直接寫值）。否決。
- **沿用 DEMO_MONSTERS 但加 toggle**：仍是假資料，不解決核心問題。否決。
- **同時實作 add / delete CRUD**：超出本次需要、V1 也沒有，後續 spec 再評估是否要做。否決。

## Impact

- Affected specs: `monster-respawn-timer`（無變更，僅引用）、`app-core-backing`（追加 8 個共用方法）；新增 `monster-respawn-ui-v2`
- Affected code:
  - Modified: `src/ui/app_core.py`（追加 8 方法）、`src/ui/app.py`（移除 8 方法、留 stub 註解）、`src/ui_v2/pages/monster_page_v2.py`（移除 DEMO_MONSTERS / add_btn、卡片改為 (app, monster_id) 介面、加 showEvent 載入）、`src/ui/hotkey_manager.py`（容錯 callback 呼叫 V1 / V2 卡片）
  - New: `verify_monster_page_v2.py`（仿 verify_skill_page_v2.py 的 fake-app harness）
  - Removed: 無
