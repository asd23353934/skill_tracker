## Context

指令頁（src/ui_v2/pages/command_page_v2.py）改版前對 needs_name 指令渲染一個可編輯下拉（ArrowComboBox）。名稱以單一共用清單 command_recent_names 存於 config_user.json，並在「按複製」時被動寫入。使用者要求：名稱改為可點擊複製的 chips、可增刪改，且每個指令各自一份名單。改版後該共用清單僅保留 ConfigManager.get_recent_command_names 作為升級相容的唯讀來源。

約束：
- 僅複製到剪貼簿，不得注入按鍵（沿用既有安全邊界）。
- UI 一律走 V2Theme 與 lucide（禁止自繪 icon / Unicode 當圖示）。
- config_user.json 為 user 可變區，升級不可遺失既有名稱。

## Goals / Non-Goals

Goals:
- needs_name 卡片以名稱 chips 呈現；點擊 chip 即複製「指令＋該名稱」。
- 每張卡片可新增名稱、刪除單一名稱、就地編輯名稱。
- 名單 per-command 持久化，升級相容舊共用清單。

Non-Goals:
- 不開放指令關鍵字／模板／說明的增刪修。
- 不更動 no-argument 卡片。
- 不做名稱跨指令同步。

## Decisions

### 名稱以 chips 呈現，點擊即複製

每個已存名稱渲染為一顆 chip（QFrame + 文字 + ✎ 改名鈕 + × 刪除鈕），點 chip 本體即把 cmd.template.format(name=該名稱) 複製到剪貼簿並 toast，並把該名稱 MRU 置前後重建 chips。
理由：比「下拉選 → 再按複製」少一步，且常用對象一眼可見。
取代：原 ArrowComboBox + 獨立「複製」鈕（多一步、名稱不可視）。

### 新增同時複製並保存（合併舊 auto-save 行為）

每張 needs_name 卡片保留一個名稱輸入框 + 主要動作鈕。輸入新名稱後送出 → 複製「指令＋名稱」、並把名稱保存為該指令的新 chip（去空白、去重、最近者置前）。
理由：一鍵滿足「用一個新對象」＋「記住它」，等價於舊版 auto-save，但結果以 chip 可見。
空輸入送出 → 維持舊語意：複製「關鍵字＋單一尾空格」，不新增 chip。

### per-command 名稱儲存結構

config_user.json 的 settings 新增 command_names: { <command_key>: [name, ...] }。
ConfigManager 提供 get_command_names(key) / add_command_name(key, name) / remove_command_name(key, name) / rename_command_name(key, old, new)。每個 list 去重、最近者置前、上限沿用既有 _MAX（20）。
理由：交換與密語對象通常不同，per-command 較貼近實際使用。
取代：單一共用 command_recent_names。

### 升級相容（非破壞遷移）

get_command_names(key) 取 command_names[key]；若整個 command_names 不存在但舊 command_recent_names 有值 → 以舊清單作為每個 needs_name 指令的初始來源（唯讀 fallback，不就地改寫舊鍵）。一旦對某指令寫入即建立其 per-command list。
理由：既有使用者名稱零遺失，且不需破壞性 migration step。

## Risks / Trade-offs

- [chips 數量過多時卡片變高] → 名稱列以 FlowLayout 自動換行；上限沿用 20（per-command）。
- [就地編輯誤觸] → 編輯採明確互動（chip 上 ✎ 鈕進入就地編輯；Enter 確認改名、Esc 取消、失焦亦視為取消以免誤改），刪除採 chip 上獨立 × 鈕，避免單擊本體誤刪。
- [舊共用清單同時被多個指令引用造成混淆] → fallback 僅在 per-command 尚未建立時生效；任何寫入後該指令即脫離共用來源。

## Migration Plan

- 讀：優先 command_names[key]，否則 fallback 舊 command_recent_names。
- 寫：一律寫入 command_names[key]；不刪除舊鍵（保留以防回退）。
- 回退：移除新程式後，舊 command_recent_names 仍存在可用。

## Open Questions

(none)
