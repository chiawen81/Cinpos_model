# 專案指南（Repository Guidelines）

## 專案結構與模組（Project Structure & Modules）
- 核心 Python 套件位於 `src/`（例如：`common`、`ML_boxoffice`、`ML_recommend`、`web`）。
- 設定檔與 Pipeline 放在 `config/`（例如：`pipeline_config.yaml`）。
- 資料集、匯出結果、日誌與訓練後的模型資料分別位於 `data/`、`exports/`、`logs/`、`saved_models/`。
- API 說明文件、筆記與其他文件放在 `docs/` 與 `README.md`。
- 專案根目錄下的 `test_*.py` 作為整合與功能測試。

## 建置、測試與開發（Build, Test, and Development）
- 使用 `uv sync` 從 `pyproject.toml` / `uv.lock` 安裝與更新相依套件。
- 使用 `uv run pytest` 執行所有測試。
- 使用 `uv run python -m <module>` 執行入口點（範例可見 `README.md` 或 `docs/`）。
- 建議將可重現的指令寫成 `scripts/` 內的腳本，而非臨時命令；並保持腳本具「可重複執行（idempotent）」特性。

## 程式風格與命名（Coding Style & Naming）
- 目標 Python 版本為 `3.13`，採用四格縮排，並在新增或修改的程式碼中加入 type hints。
- 使用 `uv run black src` 格式化程式碼，行寬限制為 100 字元。
- 使用 `uv run isort src` 整理 import。
- 使用 `uv run ruff check src`（規則：`E`、`F`、`I`）進行 Lint，提交前需修正所有警告。
- 命名規則：
  - 函式／變數：`snake_case`
  - 類別：`PascalCase`
  - 常數：`UPPER_SNAKE_CASE`

## 測試指南（Testing Guidelines）
- 所有測試均使用 `pytest`；新測試應放在符合 `test_*.py` 的位置。
- 測試函式命名為 `test_<行為>`，並保持小而精準。
- 每次修 bug 或加入非 trivial 行為，都必須新增測試。
- 優先測試 `src/` 中的純邏輯程式，而非大量 I/O 的路徑；必要時使用 fixtures 或 `data/` 下的樣本檔案。

## Commit 與 Pull Request 原則（Commit & Pull Request Practices）
- Commit message 使用清楚、具指令語氣的句式，例如：
  - `fix: handle empty movie list`
  - `feat: add box office API client`
- Commit 應保持邏輯一致、可回溯，不要混入無關的變更。
- Pull Request 需包含：
  - 簡短摘要
  - 主要實作說明
  - 執行過的測試指令
  - 若 UI / API 有變動，請附截圖或範例 payload
- 若有對應 issue／ticket 請連結，並清楚標示任何 breaking changes。

## 安全性與設定（Security & Configuration）
- 不要提交任何密鑰或個人資料；請使用 `.env` 與環境變數。
- 設定變更應優先放入 `config/*.yaml`，避免寫死在程式碼中。
- 若遇到不確定的假設或邊界情況（edge cases），請在 `docs/` 或 `NOTE.md` 中記錄。

## 程式碼修改原則（AI 必須遵守）
- 僅修改本次任務必要的程式碼（minimal diff）。
- 不得重新格式化整份檔案（禁止大範圍 black / isort）。
- 不得更動無關邏輯、變數命名、註解與排版。
- 非必要不得重構、搬移檔案、抽象化。
- 若需大範圍更動，必須先提出並由我確認後再執行。

此原則的目的：**避免 AI 在自動修復時覆蓋整份檔案，以免破壞既有邏輯、影響 pipeline 稳定性，或造成 git diff 無法檢視。**

