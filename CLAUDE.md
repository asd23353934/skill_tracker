<!-- SPECTRA:START v1.0.2 -->

# Spectra Instructions

This project uses Spectra for Spec-Driven Development(SDD). Specs live in `openspec/specs/`, change proposals in `openspec/changes/`.

## Use `/spectra-*` skills when:

- A discussion needs structure before coding → `/spectra-discuss`
- User wants to plan, propose, or design a change → `/spectra-propose`
- Tasks are ready to implement → `/spectra-apply`
- There's an in-progress change to continue → `/spectra-ingest`
- User asks about specs or how something works → `/spectra-ask`
- Implementation is done → `/spectra-archive`
- Commit only files related to a specific change → `/spectra-commit`

## Workflow

discuss? → propose → apply ⇄ ingest → archive

- `discuss` is optional — skip if requirements are clear
- Requirements change mid-work? Plan mode → `ingest` → resume `apply`

## Parked Changes

Changes can be parked（暫存）— temporarily moved out of `openspec/changes/`. Parked changes won't appear in `spectra list` but can be found with `spectra list --parked`. To restore: `spectra unpark <name>`. The `/spectra-apply` and `/spectra-ingest` skills handle parked changes automatically.

<!-- SPECTRA:END -->


# 參考來源 — hsin-dev-notes

本專案開發時請同時參考 `~/Desktop/gitlab/hsin-dev-notes/`（個人跨專案知識庫）。對話開始時依需要讀以下檔案：

- `_global/rules.md` — 全域長期指令（語言、回覆風格、版本驗證、debug 流程；最高優先）
- `_shared/spectra.md` — Spectra SDD 慣例（本專案有用 Spectra）
- `python/conventions.md` — Python 共通寫法慣例（型別 hint、命名、logging、try/except）
- `python/errors.md` — Python 踩坑紀錄（遇錯先查）

## 本專案版本（以 requirements.txt / spec 為準）

| 項目 | 版本 | 備註 |
|------|------|------|
| Python | 3.10+ | 用新型別語法（`list[T]` / `X \| None`） |
| PySide6 | ≥ 6.7.0 | GUI 主框架 |
| Pillow | ≥ 11.0.0 | 圖片處理 |
| requests | ≥ 2.31.0 | 僅用於更新檢查（同步即可） |
| pynput | 1.7.6 | 全域鍵盤監聽（daemon thread） |
| 打包 | PyInstaller | `skill_tracker.spec` |

## 與 dev-notes 的差異 / 限制

dev-notes/python 預設是**爬蟲 / Worker 專案**（Playwright + httpx + bs4 + asyncio）。本專案是 **PySide6 GUI 桌面應用**，形態不同，**以下不適用**：

- `scrape_<platform>` 模組規範、`_price_utils.py` 等 scraper helper
- Playwright `timeout=15_000` / httpx `timeout=15` 約定
- `asyncio.gather(*tasks, return_exceptions=True)` async scraper 模板
- 「改用 `httpx`、棄用 `requests`」的建議 — 本專案僅做版本檢查，同步 `requests` 已足夠

**仍適用**：

- 型別 hint 用 Python 3.10+ 新語法（`list[T]` / `X | None`，禁用 `typing.List/Optional`）
- 命名規範（snake_case 模組、PascalCase 類別、`_` 前綴內部 helper）
- Logging 用 lazy `%` 格式（**不用 f-string**），module level 宣告 logger，錯誤用 `logger.exception()`
- `try/except Exception`，不裸 `except`
- 版本驗證三步驟（任何具體版本號都先驗證，不可憑記憶）
- 不主動重構與當前需求無關的程式碼

## 對話結束時

依 dev-notes/_global/rules.md 規則，主要任務完成後**主動提議**：本次重點是否寫入 `~/Desktop/gitlab/hsin-dev-notes/_global/session-log.md`（Python 踩坑解法則寫 `python/errors.md`）。skill_tracker 本身的開發紀錄不寫進 dev-notes。


# 技能追蹤器 開發規範

@docs/PROJECT.md
@docs/CODE_STYLE.md
@docs/ARCHITECTURE.md
@docs/DATA_FORMAT.md
@docs/RELEASE.md
