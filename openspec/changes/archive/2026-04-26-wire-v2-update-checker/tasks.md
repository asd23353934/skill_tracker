## 1. 接線 V2 啟動排程

- [x] 1.1 在 `main_v2.py` 的 `PreviewWindow.__init__` 末段（`installEventFilter` 之後）加入 `_schedule_update_check()` 呼叫；對應「V2 preview shell schedules update check on startup」需求
- [x] 1.2 實作 `PreviewWindow._schedule_update_check()`：讀取 `os.environ.get("SKILL_TRACKER_DISABLE_UPDATE_CHECK")`；若為 `"1"` 直接 return（測試模式跳過），否則 `QTimer.singleShot(1000, self._run_update_check)`
- [x] 1.3 實作 `PreviewWindow._run_update_check()`：用 `threading.Thread(target=..., daemon=True)` 呼叫 `Updater().check_for_updates()`；thread 內取得結果後透過 `self.app_ctx.after(0, lambda info=result: self._on_update_result(info))` 回主執行緒

## 2. 接線 V2 對話框 handler

- [x] 2.1 實作 `PreviewWindow._on_update_result(update_info)`：對應「V2 update dialog is shown only when a newer version is available」需求；若 `update_info` 為 None / `available` 為 False / 有 `error`，僅 `print(...)` 後 return，不彈窗、不 toast
- [x] 2.2 在 `_on_update_result` 中當 `available is True` 時，`from src.ui.dialogs.update_dialog import UpdateDialog`，以 `UpdateDialog(self, update_info)` 建構並呼叫 `dlg.exec()`，父視窗為 `PreviewWindow`（`Updater` 契約保證 `available=True` 時 `latest`/`current`/`download_url` 必存在）
- [x] 2.3 用 `try/except Exception as e` 包住 `_on_update_result` 的 dialog 建構與開啟邏輯；異常時 `print(f"[v2-update] dialog error: {type(e).__name__}: {e}")` 後 return，不讓 V2 shell crash

## 3. 撰寫驗證腳本

- [x] 3.1 新增 `verify_v2_update_checker.py`（專案根目錄），用 `monkeypatch` / 直接覆蓋 `Updater.check_for_updates` 模擬三條路徑
- [x] 3.2 驗證 case A（有新版）：覆寫 `Updater.check_for_updates` 回傳 `{"available": True, "current": "1.0.0", "latest": "99.0.0", "download_url": "https://example/x.exe", "release_notes": ""}`，攔截 `UpdateDialog.__init__` 改為記錄呼叫；assert handler 被呼叫一次且父視窗是 `PreviewWindow`
- [x] 3.3 驗證 case B（無新版）：覆寫 `Updater.check_for_updates` 回傳 `{"available": False}`；攔截 `UpdateDialog.__init__`；assert 從未被呼叫、過程中無 exception
- [x] 3.4 驗證 case C（網路失敗）：覆寫 `Updater.check_for_updates` 回傳 `{"available": False, "error": "network unreachable"}`；assert 不彈窗、不 raise；assert stdout 含 `network unreachable` 字樣
- [x] 3.5 驗證 case D（dialog 建構錯誤）：保持有新版回傳，但讓 `UpdateDialog.__init__` raise `RuntimeError("boom")`；assert 主流程不 crash、stdout 含 `dialog error` 與 `RuntimeError`
- [x] 3.6 驗證執行模式：腳本須在 `SKILL_TRACKER_DISABLE_UPDATE_CHECK=1` 環境變數下手動觸發 `_run_update_check()`（繞過 `_schedule_update_check` 的 early return），避免依賴 1 秒等待；同時包含一個直接呼叫 `_schedule_update_check()` 的 case 確認 env=1 時不會註冊 QTimer

## 4. 執行與收尾

- [x] 4.1 在 repo 根執行 `python verify_v2_update_checker.py`；4 個 case 全綠才算通過，將輸出貼入 PR / 變更紀錄
- [x] 4.2 手動 smoke test：`python main_v2.py` 啟動，確認 console 無 traceback；觀察 1 秒後若 `version.py` 的 `VERSION` 低於 GitHub latest，會看到 `UpdateDialog` 跳出
- [x] 4.3 確認 `src/infrastructure/updater.py` 與 `src/ui/dialogs/update_dialog.py` 完全未修改（git diff 應為 0）
