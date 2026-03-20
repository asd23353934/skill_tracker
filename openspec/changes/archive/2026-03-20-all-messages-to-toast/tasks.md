## 1. 主視窗與頁面替換

- [x] 1.1 替換 `src/ui/app.py`：將所有 non-blocking messages displayed via Toast（all non-blocking messages displayed via Toast），QMessageBox.warning 對應 Toast 類型為 `"info"`（QMessageBox.warning 對應 Toast 類型），critical 為 `"error"`；保留 pre-initialization errors remain as modal dialogs（啟動前 `critical(None,...)` 不替換）及 QMessageBox.question
- [x] 1.2 替換 `src/ui/pages/mapleworld_page.py` 中所有 non-blocking messages displayed via Toast：透過 `self.app.toast.show()` 存取 Toast（mapleworld_page.py 的 Toast 存取），QMessageBox.question 確認對話框保留
- [x] 1.3 替換 `src/ui/pages/overlay_page.py` 中的 `QMessageBox.critical` 為 `self.app.toast.show(..., "error")`；QMessageBox.question 確認對話框保留（confirmation dialogs remain as modal dialogs）

## 2. 對話框替換

- [x] 2.1 替換 `src/ui/dialogs/profile_dialog.py` 中的 QMessageBox.information/warning/critical 為 `self.app.toast.show()`（對話框存取 app.toast 的方式）；QMessageBox.question 確認對話框保留
- [x] 2.2 替換 `src/ui/dialogs/settings_dialog.py` 中的 QMessageBox.information/critical 為 `self.app.toast.show()`（對話框存取 app.toast 的方式）
- [x] 2.3 替換 `src/ui/dialogs/potion_save_dialog.py` 中的 QMessageBox.information/warning/critical 為 `self.app.toast.show()`；QMessageBox.question 確認對話框保留
- [x] 2.4 替換 `src/ui/dialogs/skill_detail_dialog.py` 中的 QMessageBox.information/critical 為 `self.app.toast.show()`

## 3. 驗證

- [x] 3.1 執行 `python main.py`，觸發各頁面與對話框的成功/失敗/警告操作，確認所有 non-blocking messages 改以左下角 Toast 顯示，且 QMessageBox.question 確認對話框及 pre-initialization errors 保持原樣
