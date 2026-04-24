"""
版本管理
統一管理程式版本號
"""

# 當前版本
VERSION = "4.2.1"

# 版本歷史
CHANGELOG = """
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
