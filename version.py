"""
版本管理
統一管理程式版本號
"""

# 當前版本
VERSION = "3.5.2"

# 版本歷史
CHANGELOG = """
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
