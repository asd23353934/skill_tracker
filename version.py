"""
版本管理
統一管理程式版本號
"""

# 當前版本
VERSION = "4.10.0"

# 版本歷史
CHANGELOG = """
v4.10.0 (2026-07-23)
-------------------
🎯 新增技能
  - 艾畢奈亞「瞬移」50s ＋ 圖示
🎨 指令頁排序調整
  - 「邀請組隊」移到「常用」分組最前面
✨ 指令快捷鍵（可綁實體按鍵快速複製）
  - 每個指令卡可綁一把指令層級快捷鍵（觸發＝複製最近使用的名稱）
  - needs_name 指令的每個名稱 chip 可各自綁專屬快捷鍵，觸發時固定複製該名稱、不看 MRU
  - 改名／刪除名稱時專屬快捷鍵自動遷移／清除，不留孤兒綁定
  - 指令與技能／怪物是各自獨立的快捷鍵命名空間；同按鍵若已被技能/怪物占用則指令不觸發
  - 新增「啟用快捷鍵觸發」總開關（預設開啟）：關閉後任何指令快捷鍵按下都不觸發複製，
    但設定／清除快捷鍵本身不受影響
  - 新增「顯示快捷鍵小窗」：透明浮動小窗列出目前所有「按鍵→指令」對照，供切回遊戲時參考
  - 快捷鍵觸發複製時，除了 in-app toast，額外在螢幕最上層跳出「已複製：<內容>」浮動提示
    （遊戲全螢幕時也看得到），淡入顯示後自動淡出關閉
  - 新增「新增並複製」按鈕文字（needs_name 指令新增名稱那顆鈕），與純複製按鈕做出區分
  - 新增「重置名稱」／「全部重置按鍵」（危險操作，點擊皆先跳確認對話框才執行）
    - 重置名稱：清空所有指令記住的名稱，連帶清除其專屬快捷鍵
    - 全部重置按鍵：清空指令層級 + 每個名稱的專屬快捷鍵（不動已記住的名稱清單）
✨ 快捷鍵設定提示小窗
  - 技能／怪物／指令快捷鍵進入捕捉模式時，螢幕上緣跳出提示視窗（黃框「請按下…」→
    綠框「✓ 設定為 …」2 秒後自動關閉；失敗則紅框 3 秒後關閉）
  - 修正先前 V2 UI 完全無提示的問題（HotkeyManager 呼叫的 header 提示介面原本是純
    console print 的 stub，封裝成 exe 後使用者完全看不到）
✨ 技能倒數卡片新增靜音切換按鈕
  - 完成提示音／提前提示音各自一顆小圖示，未靜音灰色、靜音後變紅色＋叉燒圖示，一眼可辨
  - 獨立一列不與常/循/提前 checkbox 搶橫向空間，避免預設視窗寬度下被裁切看不到
✅ 測試：238 pytest 全綠

v4.9.5 (2026-07-05)
-------------------
🎯 新增技能
  - 艾畢奈亞「瀑布」60s / 「月牙天沖」75s ＋ 圖示
  - 劍士「降魔咒」45s（Threaten）＋ 圖示
  - 預設語音自動念出新技能名稱（TTS）
🎨 圖示更新
  - 艾畢奈亞：召喚小怪 / 視線 / 標槍 / 花朵 換用新特效圖

v4.9.4 (2026-07-02)
-------------------
🎯 艾畢奈亞「毒流星」更名為「標槍」（預設語音同步念新名稱）
🎨 技能倒數小窗：圖片下方按鍵加深黑灰底
  - 按鍵字幕鋪不透明深黑灰底、方正小圓角，寬度與小窗一致、與圖片留一點間距
🎨 技能音效改「模式勾選」：念名稱 / 選擇音效 / 靜音 三選一
  - 下拉不再混入念名稱語音（TTS）檔名，只在「選擇音效」時列出實體音檔

v4.9.3 (2026-06-28)
-------------------
✨ 技能倒數小窗：圖片下方顯示快捷鍵
  - 版面改為 時間 → 圖片 → 按鍵（橘色 ＋ 描邊）
  - 窗寬不變，按鍵字級自動縮放避免跑版，過長才 elide（…）
  - 未設快捷鍵的技能不顯示按鍵列、版面維持原樣
🎯 新增技能
  - 海盜「炸彈投擲」10s（Grenade，2 轉減防 debuff）＋ 圖示
  - 法師「魔法封印」18s ＋ 圖示

v4.9.2 (2026-06-28)
-------------------
🎯 艾畢奈亞新增「召喚小怪」技能倒數（60s）＋ 圖示；預設語音自動念名稱

v4.9.1 (2026-06-28)
-------------------
🐛 指令頁名稱刪除修復 — per-command fallback 改逐 key 判斷
  - 舊版有共用名單時，對任一指令首次刪除會連帶清空其他「尚未操作指令」的繼承名單
  - get_command_names 改以「key 是否在 command_names map 中」判斷 fallback（而非「map 是否存在」）
  - 刪到空的指令維持空清單、不回填舊清單；新增 2 個回歸測試
✨ 資源中心改依日期排序（最新在頂部）＋ 卡片顯示日期
  - _scan_dir 改用 os.scandir 取 mtime，依 mtime 由新到舊排序（同時間以檔名穩定排序）
  - 卡片 meta 列顯示日期（YYYY-MM-DD · 寬×高）
🎯 新增王「艾畢奈亞」技能倒數
  - 視線 60s / 花朵 50s / 毒流星 10s / 花瓣 100s / 蝴蝶翅膀 10s / 精煉毒藥 3s / 黑色芽孢 3s
  - 預設語音自動念出技能名稱（TTS）
🎨 圖示更新
  - 艾畢奈亞 7 招 icon
  - 暗黑龍王：黑鎖 / 大電 改用新圖
  - 殘暴炎魔：黑水一 / 黑水二 顯示名稱統一「黑水」＋ 換用新特效圖
✅ 測試：238 pytest 全綠

v4.9.0 (2026-06-25)
-------------------
✨ 新增「經驗值計算器」頁 — 升級時間估算
  - 輸入目前等級 / 經驗 % / 目標等級 ＋ 練功效率（一個經驗數字 ＋ 區間下拉
    每 10 / 30 / 60 分鐘，預設 10 分鐘）
  - 即時算出：還需總經驗、距下一級還需、預估時間（HH:MM:SS）
  - 純邏輯 domain/exp_service + exp_table（經典 pre-Big-Bang Lv1–199 每級經驗表，
    跨來源核對；MAX_LEVEL=200），輸入不持久化
✨ 「練功水錢」重構為「收支分析」頁
  - 三區：支出（藥水）/ 收入（楓幣商店差 ＋ 物品取得）/ 總結（總支出 / 總收入 / 淨收益）
  - 移除頁面內所有經驗與計時 / 速率計算
  - 數量改用「組數 × 組大小▼ ＋ 餘數」輸入（組大小 3000 / 9900；藥水預設 3000、物品 9900）
  - 收入「物品取得」可選練功地圖自動帶出掉落（domain/training_maps，15 張 Artale
    熱門練功圖 Lv72–128），附 maplestory.io 物品圖示（images/item_icons/，
    缺圖 fallback 套件徽章）
  - 切換地圖先清現有列再帶新圖、下拉保留所選；「清除全部」清列並重置下拉
  - 龍系列雜物（幼年龍的巢 210 / 蛋殼碎片 200 / 老舊的骨頭 209 / 斷裂的角 221）帶
    預設賣價，選地圖自動帶入、同一道具跨地圖同價（training_maps.DEFAULT_UNIT_PRICES）
🐛 _StackQty 改用 _as_int 安全轉換存檔數值，載入損壞 autosave 不再崩潰（spectra-audit 修補）
✨ 「指令」頁「需玩家名稱」改為名稱 chip
  - 每個名稱為可點擊複製的小方塊，可增 / 刪 / 改（✎ 就地改名：Enter 確認 / Esc 或失焦取消）
  - 各指令各自一份名稱清單（per-command，最近在前、去重、上限 20），名稱可含 #代碼
  - config_manager 新增 per-command command_names API（向後相容舊單一共用 command_recent_names）
🔧 新增 src/ui_v2/page_registry.py — 頁面導覽單一來源，main_v2 / sidebar_v2 共讀，
   新增 / 移除頁面只改一處
✅ 文件同步：README 功能清單、docs/PROJECT、docs/DATA_FORMAT；三份 openspec change
   spec 對齊實作（spectra validate --strict 全過）
✅ 測試：236 pytest + verify_exp_service / verify_potion_service / verify_potion_page_v2 全綠

v4.8.0 (2026-06-18)
-------------------
✨ 「指令」頁擴充為完整 Artale 指令清單 + 按情境分組
  - 依遊戲 /幫助 補齊至 24 條（新增 /位置 /搜尋 /全體 /地區 /隊伍 /公會 /建立隊伍
    /退出隊伍 /邀請組隊 /踢出隊伍 /邀請進入公會 /封鎖 /解除封鎖 /離開突擊
    /離開練習突擊 /刪除聊天 等）
  - 校正官方名稱：/r → /回覆（說明保留可打 /r）、/desummon → /刪除召喚獸；
    移除官方清單沒有的 /mute
  - 按使用情境分 6 組（常用 / 交易私訊 / 聊天頻道 / 隊伍公會 / 封鎖 / 其他），常用置頂好找
  - 卡片改兩欄排列 + 壓低高度，一屏顯示更多；需名稱指令沿用可填名稱下拉
  - 指令資料集中於 _GROUPS，增刪 / 調整分組順序只動一處

v4.7.1 (2026-06-17)
-------------------
🔧 自動更新重啟加速 — 安裝時的 ZIP 解壓改用 .NET ZipFile 逐 entry 覆寫
  - 取代 PowerShell 5.1 較慢的 Expand-Archive（onedir 數百檔，實測解壓 ~3.2x）
  - 快速解壓任何失敗自動 fallback 回 Expand-Archive，行為不退步
  - launcher [1/4] 等待關閉由「無條件睡 3 秒」改為條件式輪詢（app 早關就早往下走）
🔒 更新解壓加 zip-slip（路徑穿越）防護：拒絕解析後逸出目標目錄的壓縮 entry
  （註：launcher 隨 app 一起打包，此加速於本版發布後、之後的更新才生效；
   .bat 備援 launcher 維持原 Expand-Archive 路徑以降低風險）

v4.7.0 (2026-06-17)
-------------------
✨ 新增「指令」頁 — Artale 遊戲內聊天指令一鍵複製
  - 側邊欄新增「指令」（鍵盤圖示）；常用指令卡片，按「複製」寫入剪貼簿、切回遊戲貼上即可
  - 內建：/箭頭、/r、/關閉、/放煙火、/mute、/desummon（無參數）、/交換、/密語（需玩家名稱）
  - 需名稱的指令可填玩家名（含 #代碼）並自動記住用過的，下拉快速重用
    （存於 config_user.json：最近在前、去重、上限 20、向後相容）
  - 僅複製到剪貼簿、不自動輸入遊戲（避免反作弊判定）

v4.6.0 (2026-06-17)
-------------------
✨ 所有技能預設念出名稱（語音 TTS）
  - 完成 / 提前提示的預設音從「僅 boss 念名稱」擴大為「所有技能」
  - 啟動時為全部技能背景批次生成「{name}」/「{name}準備」TTS（缺檔才生，不阻塞 UI）
  - 仍可在技能詳細設定改回指定音效或靜音
✨ 內建提示音更大聲（合成振幅 0.5 → 0.95；_SOUND_VERSION 6 → 7，升級自動重生）
✨ 對話框改為非 modal（設定 / 技能詳細 / 配置管理 / 視窗挑選器等）
  - 開著對話框仍可操作主視窗與遊戲；關閉即銷毀（WA_DeleteOnClose）
✨ 技能倒數頁頁首新增「!」使用說明
  - 常駐 / 循環 / 提前提示 / 快捷鍵 / 語音 / 快捷鍵限定逐項說明
🐛 快捷鍵限定「選擇視窗」修正
  - 列表排除本程式自己的視窗（主視窗 / 對話框 / 浮動技能窗）
  - 截圖縮圖卡片改為整片可點選：半透明視窗在 alpha=0 區會發生 Windows 視窗層級
    「點擊穿透」（事件到不了挑選器），改為不透明視窗修正
🔧 skill_detail_dialog 清理：全技能 TTS 後移除恆真旗標 _tts_default 的死分支與過時註解

v4.5.0 (2026-06-07)
-------------------
✨ boss 技能 TTS 語音預設提示音
  - 啟動時為 boss 類技能背景批次生成「{name}」/「{name}準備」TTS WAV
    （Windows SAPI 經 PowerShell 子程序，無新增 Python 套件依賴）
  - SkillService 對 boss 類技能無 override 時自動回對應 TTS 檔
  - 新增 src/infrastructure/tts.py（generate_tts_batch + 中文語音優先挑選）
✨ 技能 / 全域設定的「靜音」改為獨立 checkbox
  - 技能詳細設定：原下拉「靜音（不播放）」拆出為下拉右側的「靜音」checkbox；
    boss 類下拉預設顯示對應 TTS 檔，移除「使用全域設定」選項
  - 全域設定：「音效開關」整列移除，「靜音」併入「全域結束聲音」/「全域提前聲音」
    各列右側；勾起 = 對應全域功能關閉
  - 全域設定：「快捷鍵限定」+「目標視窗」併為單列
🎯 暗黑龍王 boss 技能補齊（依粉圓計時器）
  - 新增：吐火 60s / 魅惑 85s
  - 改名：右頭狂暴 → 大電 / 鎖鏈 → 黑鎖
  - 調整：輕踩 20s → 40s
🎨 新增 icon：吐火.jpg / 魅惑.jpg；更新左手消技 icon

v4.4.0 (2026-06-01)
-------------------
✨ 提示音可分別禁音（全域 + 每技能）
  - 設定的單一「啟用聲音」拆成「完成提示音」「提前提示音」兩個獨立開關
  - 技能細節音效下拉新增「靜音（不播放）」，可單獨靜音某技能
    （sentinel 三態：使用全域 / 指定音效 / 靜音）
  - 舊 enable_sound 設定自動遷移為兩個新開關（原關→兩者關，原開→兩者開）
✨ 快捷鍵可限定只在指定前景視窗時觸發（可開關）
  - 設定新增「只在指定視窗觸發快捷鍵」+ 視窗挑選器（縮圖卡片網格，看畫面選目標）
  - 以前景程式 exe 比對；只在按到已註冊快捷鍵後才查前景，平常打字零成本
  - 新增 src/infrastructure/window_enum.py（ctypes：視窗列舉 / 前景 exe / PrintWindow 縮圖）
  - 未選目標前開關停用，避免「啟用卻無目標」的靜默無效
  - 已知限制：GPU / Chromium 視窗被遮擋時縮圖可能空白（標題仍可辨識），待實測遊戲再評估
🐛 修復技能長時間循環累積秒差
  - _loop_restart 改錨定「上一輪理論結束點」並移除隨機延遲，
    30s 循環技能由 ~+40 秒/小時 → ~0；落後一輪以上（休眠/卡頓）才重新對齊
✅ 新增 tests/test_sound_mute.py（9 cases：sentinel 三態解析 + 設定預設）

v4.3.7 (2026-05-06)
-------------------
✨ 資源中心支援 RWD（依視窗寬度動態調整每行欄數）
  - mapleworld_page_v2._compute_cols 依 viewport().width() / CARD_W / spacing 計算
  - resizeEvent 80ms debounce → cols 變動才整頁重畫,避免 resize 抖動
  - 各寬度欄數實測：320→2 / 800→5 / 1280→8 / 1920→12 / 2560→16
✨ 資源中心滾動到底部自動加載
  - QScrollBar.valueChanged 監聽,距底部 200px 內 trigger _load_more
  - _loading_more 旗標 + token 失效時整頁重畫分支重置,防止連續 emit 重複觸發
  - 渲染最後一 chunk 後若 viewport 仍未填滿（無捲動軸）主動補載一輪
  - 「載入更多」按鈕保留為 fallback,文字改「繼續向下捲動以自動載入 · 還有 X 張」
✅ 新增 tests/test_mapleworld_rwd.py（_compute_cols 在 9 個寬度下的 smoke test）

v4.3.6 (2026-04-30)
-------------------
✨ 新增三個 buff 道具
  - 經驗加倍（cooldown 1800s）
  - 掉寶加倍（cooldown 1800s）
  - HT加倍（Hot Time，cooldown 3600s）
✨ 道具類提前提示預設啟用
  - SkillService.is_alert_enabled fallback：dict 無 key 時，category=item 走 True，
    其他走 False。既有 profile 升上 v4.3.6 後新加道具自動帶提前提示
🎨 技能倒數小窗時間 >600s 改用「Xm」分鐘顯示
  - SkillWindow._fmt_seconds（>600 嚴格大於才轉分鐘；600 仍以「600」秒顯示）
  - 避免長 buff 倒數時整排數字塞滿小窗
🔒 SkillPixmapCache._index_all_paths 加 path traversal 防禦
  - reject `..` / `/` / `\\` / Windows drive-letter 開頭的 icon 字串，
    防同 user 改 config.json 寫惡意路徑
✅ 新增 tests/test_skill_window_fmt.py（5 cases）+ test_services.py 5 個
   alert_enabled fallback 測試（item / player / boss / explicit-set / unknown-id）
🔧 scripts/gen_buff_icons.py — Pillow placeholder generator（一次性）
   含 --force 旗標，預設不覆蓋既有圖避免蓋掉使用者真實 icon

v4.3.5 (2026-04-30)
-------------------
🐛 修復 v4.3.0+ 自動更新流程下載完不重啟的 bug
  - update_dialog_v2 啟動 launcher 時用 DETACHED_PROCESS | CREATE_NO_WINDOW，
    DETACHED_PROCESS 讓 powershell.exe 啟動後立刻死亡（exit 0 但 script body
    完全沒執行），導致 launcher 從未跑 → ZIP 沒解、新 exe 沒被啟動
  - 改成只用 CREATE_NO_WINDOW；launcher [1/4]–[4/4] 全程跑通
✨ 偵測到新版不再自動跳 modal dialog
  - 改用 header 右側橘色提示 chip（lucide arrow-up-circle + 「v4.3.5」）
  - toast 同步通知「有新版本 v4.3.5 可下載 — 點頂部按鈕開始更新」
  - 使用者點 chip 才開 UpdateDialog（自動 modal 太擾）
🛡️ launcher 失敗時雙保險提示
  - launcher (ps1 / bat) 失敗路徑（解壓失敗 / exe 鎖定 / 無法重啟 / unhandled）會：
    1) 立即跳 Windows MessageBox 告知使用者
    2) 寫 update_failed.txt marker 到 AppDir
  - 主程式啟動讀 marker → toast warning 顯示 reason → 刪檔
  - SKILL_TRACKER_DISABLE_UPDATE_CHECK=1 同時抑制 update check 與 marker scan
🔒 Marker 偽造防禦
  - reason 限 200 字、剔除控制字元、含 URL 直接 fallback「未知原因」
  - 防同 user 惡意 process 用 marker 寫釣魚訊息
🔧 launcher bat :show_dialog 改用 env var 傳遞訊息（避免 PowerShell 單引號注入）
🔧 main_v2 marker 讀檔走 utf-8-sig 防禦 PS 5.1 Out-File 的 BOM
✅ 新增 verify_update_failure_marker.py（9 cases）+ verify_update_e2e.py
   verify_v2_update_checker.py 擴 7 cases（chip + _open_update_dialog 路徑）
   tmp dir + monkeypatch user_data_path 避免 stale marker 污染

v4.3.4 (2026-04-27)
-------------------
🐛 召喚銀隼 icon 再修正：改用 skill 3221005 (Frostprey 藍色冰鳥)
   Artale 命名與全球版不同：Artale 的「銀隼」對應全球版 4 轉
   神射手的 Frostprey，而非全球版 3 轉獵人的 Silver Hawk

v4.3.3 (2026-04-27)
-------------------
🐛 召喚銀隼 icon 修正：原本誤用 3211005（Crossbowman 的 Golden Eagle 金鳥），
   改用正確的 3111005（Hunter 的 Silver Hawk 銀鳥）
📝 openspec/specs/auto-update/spec.md 同步現況：
   Purpose 補上實際說明、UpdateDialog 路徑改指 V2、清理 @trace 雜訊

v4.3.2 (2026-04-27)
-------------------
✨ 弓箭手技能調整
  - 新增：召喚鳳凰（300s）/ 召喚銀隼（300s）
  - 移除：替身術

v4.3.1 (2026-04-27)
-------------------
✨ 新增弓箭手技能：念力集中（cooldown 360s）

v4.3.0 (2026-04-27)
-------------------
✨ V2 預覽 shell 接上自動更新檢查
  - 啟動 1 秒後背景查 GitHub Release，有新版時開 V2 UpdateDialog
  - V2 UpdateDialog（src/ui_v2/dialogs/update_dialog_v2.py）：
    BaseDialogV2 + V2Theme，繼承 V1 下載 / 啟動 launcher 流程
  - 進度回呼節流（100ms 或 0.5% delta），避免大檔下載塞爆 event queue
  - SKILL_TRACKER_DISABLE_UPDATE_CHECK=1 可關閉（測試用）
  - verify_v2_update_checker.py：6 cases 全綠
🔧 移除 verify_lucide_hidpi.py（DPR 路線已被 v4.2.4 4x 超採樣取代）

v4.2.5 (2026-04-24)
-------------------
✨ 技能卡片冷卻/熱鍵 chip 加寬（value_w 46 → 64）
  長按鍵名（如 CTRL+F12）不再被截斷
🐛 右側數字鍵 / numpad 快捷鍵判斷修復
  pynput 在 Num Lock off 或 NUM+/-/*/÷ 等鍵回傳 KeyCode(char=None)
  舊邏輯 str(None) → "None"，顯示成 "NONE" 無法使用
  新增 _key_to_name 走 VK 對應表：NUM0..9 / NUM+ / NUM- / NUM* / NUM/ / NUM.
  副作用：numpad 與主排數字為不同快捷鍵（可分別指派）

v4.2.4 (2026-04-24)
-------------------
🎨 浮動視窗 icon 統一走 lucide + HiDPI 銳利化
  - lucide_pixmap 改為 devicePixelRatio aware：
    renders at size*dpr, setDevicePixelRatio(dpr) → HiDPI 螢幕不再模糊
  - skill_window 關閉鈕：改用 lucide "x"（移除自繪 drawLine / drawText "✕"）
    常態深灰圓底 + ORANGE 細框，hover ORANGE 填色，icon 永遠幾何置中
  - overlay_window 關閉鈕：同改 lucide "x"（移除 drawText "✕"）
  - 統一規範：UI 圖示一律走 lucide，禁止自繪 / Unicode 符號當 icon

v4.2.3 (2026-04-24)
-------------------
🎨 技能倒數小窗視覺整合 V2 調性（尺寸/位置計算完全未動）
  - 外框改 V2 ORANGE + 圓角（R_SM=6），alert 時閃 YELLOW
  - 內框改 V2 BORDER_HOVER 低調灰紫
  - 倒數文字 / 標題改 TEXT_HI + BG_BOTTOM 深描邊，字型統一 Microsoft JhengHei
  - 關閉鈕 hover 改 ORANGE 圓角填色底 + 亮 X（常態僅 dim X 無底）
  - BORDER_W / INNER_BORDER_W / 所有 QRect / window_size 計算維持原樣
  - 驗證：64/80/96 三種尺寸最終 window size 與 v4.2.2 一致

v4.2.2 (2026-04-24)
-------------------
🔧 SkillPixmapCache 改 lazy load（啟動零 QPixmap 解碼）
  - 啟動只掃 icon 路徑索引，不開檔；首次 .get(skill_id) 才解碼
  - 一次解碼產四尺寸（50 / 28 / 64 / 36），後續命中走 dict
  - 對外 qpixmaps / qpixmaps_small / qpixmaps_medium / qpixmaps_card
    仍是 dict-like（.get / [] / in / 指派）— 現有呼叫端零改動
  - 缺圖 / 解碼失敗 → 四個 dict 都寫 None，不重試
  - 新增 preload_all() 供測試 / 舊行為還原
  - 新增 tests/test_skill_pixmap_cache.py（10 cases）
  - 全 pytest：150 → 160 passing

v4.2.1 (2026-04-24)
-------------------
✅ 補 domain / infrastructure 測試：72 → 150 passing
  - tests/test_services.py — SkillService / MonsterService（34 cases）
    互斥狀態、快捷鍵衝突 displace、批次 toggle、serialize/load、
    MonsterService 重生時間 + 狀態 setter + save
  - tests/test_config_manager.py — ConfigManager（44 cases）
    檔名驗證（Path Traversal / Windows 保留字）、config+user 分檔三情境、
    profile CRUD / list sort / rename、potion record CRUD /
    mtime 排序、potion autosave（含 corrupt 容錯）

v4.2.0 (2026-04-24)
-------------------
🎉 V1 UI 正式下架 — V2 為唯一 UI
  - 移除 src/ui/app.py / pages/ / dialogs/ / header / sidebar / status_bar /
    skill_column / skill_card / toast
  - main.py 不再支援 --v1 opt-in，直接進 V2
  - app_core.py 清掉 V1-only show_skill_detail（V2 SkillCardV2 直呼 V2 dialog）
  - src/ui/ 只留 V2 共用基礎：app_core / dispatcher / hotkey_manager /
    window_manager / overlay_manager / skill_window / overlay_window /
    skill_pixmap_cache / theme
  - 文件同步：PROJECT.md / ARCHITECTURE.md

v4.1.9 (2026-04-24)
-------------------
🐛 修復：點卡片預覽時 AttributeError: V2Theme has no attribute 'BG_BASE'
  - _PreviewDialog 誤用不存在的 T.BG_BASE，改為 T.BG_WINDOW

v4.1.8 (2026-04-24)
-------------------
🔧 V2 資源中心分類 chip 改用 FlowLayout，視窗變窄時自動折行
  - 新增 src/ui_v2/flow_layout.py（Qt 官方 FlowLayout 範例 Python 版）

v4.1.7 (2026-04-24)
-------------------
✨ V2 資源中心新增掃描進度條（QProgressBar, indeterminate → 0-100）
  - scanner on_progress 簽章改為 (msg, pct)；pct=-1 視為 indeterminate
  - Unity 掃描直接回報百分比；Web 掃描 Phase 1 / Phase 2 各佔 50%

v4.1.6 (2026-04-24)
-------------------
🔧 分類 cache 加 version 欄位（v2 schema：{"version": 2, "tags": {...}}）
  - 未來 CATEGORIES 變動只要 +1 version 即可全量失效重分類
  - 完全相容 v1 純 dict 舊檔；下次存檔自動升級

v4.1.5 (2026-04-24)
-------------------
🔧 重構：拆分 mapleworld_page_v2.py（897 行 → 573 行）
  - 新增 mapleworld_widgets_v2.py：_PreviewDialog / _AssetCard / _ThumbBox /
    _TabBtn / _CatChip / _LRUPixCache / 分類色表 / classify cache I/O
  - 原頁面只留 layout / 掃描 / filter 主流程

v4.1.4 (2026-04-24)
-------------------
🔧 V2 資源中心縮圖快取改 LRU（上限 800 張），避免長時瀏覽記憶體無限膨脹

v4.1.3 (2026-04-24)
-------------------
✨ V2 資源中心掃描支援取消
  - scanner 新增 should_cancel callback，Unity 每 500 檔 / Web Phase 1 每 100 檔、Phase 2 每 50 URL 檢查一次
  - 掃描中按鈕切換為「取消」，再按一次會中止 worker 並回報已存張數
  - 取消後仍重掃目錄顯示已儲存的檔案

v4.1.2 (2026-04-24)
-------------------
🔧 分類 cache 檔案移出 images/mapleworld/，放至 exe 同層（mapleworld_classify_cache.json）
  - 避免備份 / 壓縮 images/ 時被帶上無關的 JSON
  - 自動遷移舊位置 _classify_cache.json 並刪除
🔧 分類 worker 每 1000 張 flush 一次磁碟，中途關閉程式仍保留已分類進度
🔧 分類 badge 改 8 色漸層（cyan → teal → green → lime → yellow → orange → deep-orange → red），一眼辨識尺寸級數

v4.1.1 (2026-04-24)
-------------------
✨ V2 資源中心卡片點擊彈出原尺寸預覽（超過螢幕等比縮放）
🔧 「另存新檔」失敗/成功改走 toast 通知，不再只 print
🔧 歸檔 openspec change extract-mapleworld-scanner（23 task 全部完成）

v4.1.0 (2026-04-24)
-------------------
✨ V2 資源中心完整接線
  - 「掃描資源」按鈕啟用，委派給新 src/infrastructure/mapleworld_scanner 模組（V1/V2 共用）
  - 圖片分類：依 max(寬,高) 分 8 級 chip 篩選（≤16 / 17-32 / … / >1024），支援「全部」
  - 分類結果快取至 _classify_cache.json，再進頁面直接讀取不重跑
  - 4 執行緒 ThreadPoolExecutor 並行分類，分類過程不重渲 grid（只更新統計文字）
  - 每張卡片右下角「另存新檔」按鈕（shutil.copy2 保留時間戳）
✨ V2 grid 分批渲染：每 24 張 yield 主執行緒，避免整批 QPixmap 解碼卡頓
✨ V2「載入更多」按鈕：append-only 續畫、鎖定 inner 高度避免捲動軸跳動
✨ V2 切 tab / 切分類自動回頂；載入更多保持捲動位置
🔧 MapleWorld 掃描邏輯從 V1 page 抽出成 infrastructure 模組（Qt-free，callback 介面）
🐛 V2 練功水錢新增藥水時 AttributeError（_rows_layout 在錯誤位置初始化）
🐛 V2 QComboBox 下拉選單在部分裝置背景透明難以辨識（theme_v2 新增 combo_popup_qss helper）
🔧 V2 怪物重生卡片移除多餘齒輪按鈕（從未接線）

v4.0.0 (2026-04-23)
-------------------
🎉 重大版本：V2 介面正式預設、設定 / 配置管理 / 通知全面升級

✨ V2 UI 正式預設
  - 新介面：紫色漸層 dashboard、橘色 maple icon、Lucide 線條圖示、卡片式佈局
  - 全 5 頁完整接線：技能倒數 / 怪物重生 / 浮動圖片 / 練功水錢 / MapleStory 資源
  - 雙擊 exe 直接進 V2；舊版仍可用 `--v1` opt-in 保留
✨ V2 全域設定對話框（音量 / 視窗位置 / 全域聲音 / 提前提示秒）—— sidebar 齒輪開啟
✨ V2 配置管理對話框（切換 / 新增 / 複製 / 重命名 / 刪除）—— skill 頁旁齒輪開啟
✨ V2 Toast 通知：右下角浮層、4 色 fade-out（success / warning / error / info）
✨ 設按鍵後欄位 chip「N/總數」即時更新；切換 profile 自動 toast 回饋
✨ 新 profile 預設「提前提示」boss=關 / 其他=開（配合短秒數技能需求）
🔧 ConfigManager 分檔：static config.json 與 user config_user.json 拆開
  - 升級覆蓋安裝不再重置音量 / 視窗位置 / 自訂 monsters / overlays
  - release ZIP 內 config.json 已 strip 個人 settings
🔧 單一實例 lock：第二次啟動靜默退出，防多開
🔧 main.py 入口：V2 預設、`--v1` opt-in
🐛 暗黑龍王輕踩 / 重踩 cooldown 10s → 20s
🐛 V2 切換 profile 後常駐技能視窗未依新 profile 重建（已修）
🐛 V2 monster 頁設按鍵後 column 計數未即時更新（已修）
🔧 多項清理：BUILD.md 刪除（合併到 docs/RELEASE.md）、docs/PROJECT.md 結構樹重寫對齊

⚠️ 升級提醒
  - 從 v3.x 直接升級：升級瞬間 ZIP 會覆蓋 config.json，個人 settings /
    monsters / overlays 會回到預設
  - 解法：升級前手動備份 config.json，或預先 copy settings/monsters/overlays
    區段成 config_user.json（與 config.json 同層），新版會優先讀此檔
  - 從 v4.0.0 起此問題不再發生（後續版本不會覆蓋 user 可變區）

v3.8.0 (2026-04-22)
-------------------
- ✨ 練功水錢頁面藥水列新增圖示顯示：依名稱載入 images/{name}.png，找不到時 fallback 到分類 emoji
- ✨ config.json 新增 7 筆 buff 道具（速度/命中/敏捷藥丸、雙份日式炒麵、加量章魚燒、疼痛舒緩劑、龍寶寶的副食品），CD 10~20min
- ✨ 新增 20 張練功常用藥水圖示 + 9 張道具圖示（來源：artalemaplestory.com）
- 🔧 練功水錢預設「白水」改名為「白色藥水」以對齊遊戲內名稱
- 🔧 _load_potion_icon 以 lru_cache 避免逐鍵輸入重複讀檔

v3.7.0 (2026-04-22)
-------------------
- ✨ 練功水錢頁面預設不載入任何藥水列（使用者自行從下拉選單新增）
- ✨ 練功水錢頁面新增自動保存：任何編輯 500ms 後寫入 potion_autosave.json，開啟頁面自動還原（含計時器秒數）
- ✨ 練功水錢頁面新增「🔄 全部重置」按鈕：確認後清空所有藥水列、楓幣/經驗/商店欄位、計時器，並刪除自動保存
- 🔧 ConfigManager 新增 save/load/delete_potion_autosave 管理獨立 autosave 檔（與 config.json 同層）
- 🔧 _PotionSection 將 _clear_all_rows 改為公開的 remove_all_rows，消除跨類別呼叫私有方法

v3.6.0 (2026-04-21)
-------------------
- ✨ 視覺升級：頁首/狀態列/卡片/對話框深色漸層 + 金色光暈標題
- ✨ 側欄新增浮動金色活動指示器（切換頁面平滑滑動 220ms）
- ✨ 頁面切換、對話框、Toast、技能倒數視窗全面加入淡入動畫
- ✨ Toast 滑入/淡出動畫 + 堆疊自動平滑重排
- 🔧 AppTheme 新增 make_shadow / make_anim 共用工廠，收斂動畫樣板
- 🔧 Toast 動畫生命週期管理：切換前停止前一個動畫避免重疊

v3.5.2 (2026-04-21)
-------------------
- 🐛 修復關閉程式時呼叫不存在的 window_manager.close_all_windows()（方法實為 close_all()），
  導致浮動技能視窗未正確清理（原錯誤被 except 靜默吞掉）
- 🔧 補齊 Qt override 方法的 # noqa: N802 標註（header / overlay_window / sidebar / skill_window）

v3.5.1 (2026-04-21)
-------------------
- 🐛 修復設定對話框/技能細節變更後參數不生效，必須手動關閉再開啟視窗才套用
- 🐛 修復切換配置後前一個配置的常駐技能視窗殘留
- 🔧 window_size 變更才重建視窗，其他參數原地更新避免閃爍

v3.5.0 (2026-04-21)
-------------------
- ✨ 新增音效音量設定（0-100% 滑桿，設定對話框即時預覽）
- 🔧 WAV 透過 waveOutSetVolume 行程層級控制；MP3 透過 MCI setaudio 指令控制

v3.4.2 (2026-04-21)
-------------------
- 🐛 修復 update_launcher.bat 的 ZIP 解壓縮失敗（PARENT_DIR 延遲展開、PS 5.1 不支援的 ExtractToDirectory 3 參數 overload）
- 🐛 修復 update_launcher.bat [4/4] 重啟區塊 else if 誤判雙分支都執行（改用 goto 結構）
- 🔧 update_launcher.bat 解壓時加 -WindowStyle Hidden，消除 PowerShell 閃窗

v3.4.1 (2026-04-21)
-------------------
- ✨ 新增暗黑龍王技能（鎖鏈 30s / 右頭狂暴 80s / 左手消技 90s）

v3.4.0 (2026-03-27)
-------------------
- ✨ 新增廣播擷取頁面（BroadcastPage）
- 🔧 程式架構重整：導入 infrastructure 層 + domain services，精簡 app.py

v3.3.0 (2026-03-23)
-------------------
- ✨ 練功水錢頁面：新增藥水下拉選單、單列刪除按鈕、全部清除按鈕
- ✨ MapleWorld 頁面：快取圖片改為延遲載入（showEvent）+ 背景執行緒分批載入
- ✨ 自動更新系統：ps1 → bat fallback 機制；PID 偵測取代程序名偵測；新增 update_log.txt 日誌
- 🔧 打包名稱由「技能追蹤器」改為「skill_tracker」（spec / release.bat / zip_release.py / BUILD.md）
- 🔧 移除羅茱工具頁面（roja_page.py）及相關主題常量
- 🔧 主視窗 resize 感應距離由 8px 縮為 4px

v3.2.0 (2026-03-20)
-------------------
- ✨ 新增 MapleWorld 資源瀏覽頁面（側邊欄 🍄）
- ✨ 新增練功水數量計算機（PotionCostPage _QuantityCalcSection）
- ✨ 羅茱工具：新增「全部重置」按鈕；按鈕加文字說明；面板加寬；浮動視窗按鈕移至右上角
- 🔧 config.json 移除 skills 靜態區殘留 hotkey 欄位（符合 DATA_FORMAT 規範）
- 🔧 profile_dialog、settings_dialog、overlay_page 全面改用 Toast 取代 QMessageBox
- 🔧 settings_dialog 新增 app 參數以支援 Toast 通知
- 🔧 skill_manager.update_hotkey() 不再直接寫入 config["skills"]（僅更新記憶體）
- 🔧 hotkey_manager 補充命名空間與執行緒安全說明 docstring
- 🔧 CLAUDE.md 重構為 Spectra 格式，改用 @docs/* 引用
- 🐛 修復 mapleworld_page.py 使用相對路徑（改用 user_path() 確保 exe 打包正確）
- 🐛 修復 skill_detail_dialog.py 提前秒數輸入錯誤時靜默失敗（改為顯示 Toast 提示）
- 🔧 新增 AppTheme.ACCENT_RED_HOVER 常量；新增 helpers.user_path() 函數
- 🔧 hotkey_manager.py _on_hotkey 錯誤改輸出至 stderr
- 🔧 skill_tracker.spec 補充 PIL.PngImagePlugin / PIL.WebPImagePlugin hidden import
- 🔧 .gitignore 移除無效 pattern，新增 profiles/ 與 sounds/ 排除
- 📝 PROJECT.md 補充 potion_cost_page、roja_page、mapleworld_page、potion_save_dialog

v3.1.1 (2026-03-18)
-------------------
- 🐛 修復自動更新腳本路徑錯誤（PS1/BAT 未放於 exe 同層，導致找不到更新腳本）
- 🐛 修復 update_launcher.ps1 使用 Start-Process -LiteralPath（PS 5.1 不支援，改為 -FilePath）

v3.1.0 (2026-03-18)
-------------------
- ✨ 新增練功水錢頁面（PotionCostPage）
- ✨ 新增羅茱工具頁面（RojaPage）
- ✨ 新增練功水錢儲存對話框（PotionSaveDialog）
- ✨ 新增自動更新啟動腳本（update_launcher.ps1）
- ✨ 技能頁功能增強
- 🔧 Header 大幅重構精簡
- 🔧 ConfigManager 擴充

v3.0.1 (2026-03-17)
-------------------
- 🐛 更改壓縮檔案名稱

v3.0.0 (2026-03-17)
-------------------
- 🎉 GUI 框架全面移植至 PySide6（原 customtkinter），架構重寫
- ✨ 新增浮動圖片頁（OverlayPage）— 支援 PNG / JPG / GIF 動畫覆蓋於畫面
- ✨ 新增底部狀態列（StatusBar）— 顯示配置名稱、版本號、拖曳縮放控制點
- ✨ 新增左側導覽列（Sidebar）— 技能倒數 / 怪物重生 / 浮動圖片頁面切換
- ✨ 新增 zip_release.py，打包後一鍵壓縮為發布用 ZIP
- ✨ 發布流程強化：clean / check 腳本補上 overlays 清空與驗證
- 🐛 修復自動更新 ZIP 解壓縮路徑錯誤（雙層目錄問題）
- 🐛 修復自動更新 fallback URL 名稱與實際 ZIP 不符
- 🐛 修復 overlay 頁縮圖顯示佔位符，改為讀取實際圖片
- 🐛 修復發布前未清空 overlays 記錄，導致 dist 無法顯示圖片
- 🐛 修復 skill_window mouseMoveEvent event.pos() PySide6 相容性錯誤
- 🐛 修復最小化按鈕符號垂直位置偏下
- ✨ Header / StatusBar 分隔線改為極細半透明金色

v2.1.5 (2026-03-04)
-------------------
- 🐛 測試自動更新

v2.1.4 (2026-03-04)
-------------------
- ✨ 新增浮動圖片視窗
- 🐛 修復自動更新連接錯誤

v2.1.3 (2026-03-03)
-------------------
- 🐛 修復自動更新連接錯誤

v2.1.2 (2026-03-03)
-------------------
- 🐛 修復自動更新連接錯誤

v2.1.1 (2026-03-03)
-------------------
- 🐛 修復自動更新連接錯誤

v2.1.0 (2026-03-03)
-------------------
- ✨ 怪物重生卡片完整功能
- ✨ 新增與修改部分技能

v2.0.0 (2025-02-16)
-------------------
- 🎉 全新 RPG 金色主題介面
- ✨ 新增側邊欄導航（技能倒數 / 怪物重生頁面切換）
- ✨ 新增多樣聲音提示並可上傳音檔使用
- ✨ 新增怪物重生系統 — 快捷鍵觸發正數計時（從 0 數到設定時間）
- ✨ 技能細部設定 — 完成音效與提前提示音效分開設定
- ✨ 新增 Toast 通知系統（取代彈窗提示，底部左側顯示）
- ✨ 音效系統支援 MP3 格式（透過 Windows MCI 播放）
- ✨ 音效系統改用 winsound + MCI，移除 pygame 依賴
- ✨ 程式圖示與標題統一更換為楓葉 🍁
- 🐛 修復側邊欄 tooltip 殘留在螢幕上的問題
- 🐛 修復音效選擇後試聽只有系統預設聲音的問題
- 🐛 修復技能卡片中間內容未垂直置中的問題

v1.1.8 (2025-01-20)
-------------------
- 🐛 修復初始載入與點擊常駐或循環時, 顯示的技能窗大小不正確

v1.1.7 (2025-01-20)
-------------------
- ✨ 新增更改技能窗大小
- ✨ 新增殘暴研磨黑水一黑水二

v1.1.6 (2025-01-04)
-------------------
- 🐛 修復初始時間多扣1秒

v1.1.5 (2025-01-03)
-------------------
- 🐛 修復倒數計時不準確

v1.1.4 (2025-01-03)
-------------------
- ✨ 新增提前提示
- ✨ 新增可直接拖曳技能位置
- ✨ 補充技能(力量消除, 神聖之火)

v1.1.3 (2025-01-03)
-------------------
- 🐛 修復新增配置與複製配置錯誤

v1.1.2 (2025-01-03)
-------------------
- 🐛 修復保存設定錯誤

v1.1.1 (2025-01-03)
-------------------
- 🐛 修復圖片路徑問題

v1.1.0 (2025-01-03)
-------------------
- ✅ 新增技能配置
- ✨ 新增「循環」功能（到0後自動重啟倒數）
- 🐛 修復重置時秒數越扣越快的 bug

v1.0.1 (2025-01-01)
-------------------
- ✅ 新增四欄布局（房間/玩家/BOSS/道具）
- ✅ 秒數按鈕化，可點擊修改
- ✅ 配置管理系統完善
- ✅ 自動更新檢查功能
- ✅ config.json 保護機制
- ✅ 自訂應用程式圖示（楓葉）
- 🐛 修復配置切換時的狀態污染問題
- 🐛 修復 messagebox 導入錯誤

v1.0.0 (2025-01-XX)
-------------------
- 🎉 初始版本發布
- ✅ 基本技能追蹤功能
- ✅ 配置檔案管理
"""

def get_version():
    """獲取當前版本號"""
    return VERSION

def get_changelog():
    """獲取版本歷史"""
    return CHANGELOG

def get_version_info():
    """獲取完整版本資訊"""
    return {
        'version': VERSION,
        'changelog': CHANGELOG
    }
