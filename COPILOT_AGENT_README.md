# GitHub Copilot AI Agent

~~~yaml
# 機器用 metadata（Agent 可先讀此區）
agent_target: "github_copilot"
language: "zh-Hant"            # 回覆偏好：繁體中文
virtualenv: ".venv"
package_manager: "uv"
python_version_file: ".python-version"
project_name: "Cinpos_model"
~~~

## 1. Agent 的角色與回覆語言
- 角色：協助專案開發、執行 pipeline、產文件與自動化任務的 GitHub Copilot AI Agent。
- 回覆語言：**全部回覆請使用繁體中文（正體中文）**，並以台灣口吻呈現（簡潔、親切、務實）。

## 2. 虛擬環境與執行原則（必讀）
- 虛擬環境位置：`.venv/`
- 不管在哪個情境下，**執行 Python 指令或腳本時一律使用 `uv run ...`**，不要直接呼叫 `python`、`pip`、或系統上的其他 Python。
- 常用指令：
~~~bash
# 安裝 / 移除 / 同步
uv add <package>
uv remove <package>
uv sync

# 執行腳本、測試、linters
uv run src/path/to/script.py
uv run pytest
uv run ruff
uv run python  # 需要互動 python 時
~~~
- 注意事項：
  - `uv run` 會自動使用 .venv（因此 Agent 不需要先手動 activate）。
  - 若要執行 CLI 命令也請用 `uv run <command>` 包裹。

## 3. 套件管理與禁止事項
- **只能**使用 `uv` 來管理相依（安裝 / 移除 / sync / lock）。
- 禁止直接使用：`pip install`、`poetry`、`pip-tools`、`conda` 等來改變專案相依。

## 4. Pipeline 修改規範（When modifying pipeline）
- 目的：保持 Pipeline、controller script 與目標腳本之間參數與行為一致。
- 三大原則（Agent 每次修改前請檢查）：
  1. **同步性**：`pipeline_config.yaml`、`run_pipeline.py`、以及被呼叫腳本的 CLI 參數介面需一致。
  2. **測試性**：支援 dry-run / 模擬執行確認輸出路徑與參數。
  3. **靈活性**：所有參數預設為合理值（non-breaking），非必要參數設為 optional。
- 參考文件位置：`docs/shared/pipeline_修改指南.md`

## 5. 文件同步規則（人類文件 vs 機器文件）
- 每次新增或變動 feature 欄位，**必須同時更新**：
  1. `docs/model/data_資料欄位定義.md` （人類可讀、含範例與計算邏輯）
  2. `docs/model/ml_特徵配置.yaml` （機器可讀、供 Agent/自動化工具使用）
- 其他重要 doc：
  - `docs/spec_model.md` - 模型規格主索引
  - `docs/spec_web.md` - 網站業務邏輯主索引
  - `docs/spec_web_api.md` - API 規格主索引
  - `docs/model/data_資料處理流程.md` - Pipeline 詳細流程
  - `docs/model/data_資料處理規則.md` - 資料處理規則
- 文件放置原則：所有開發文件放 `docs/`；採用「主索引 + 詳細文件」架構；**不要**把規格文件放在 `src/`。

## 6. 安全與敏感資訊
- 絕對不要把 API keys 或敏感檔案提交到 Git。
- `.gitignore` 建議包含：
~~~
.env
.env.local
.env.api
docs/set_claude_use_mode/use-api.bat
~~~
- 若 Agent 需要使用 API key：優先從 CI secret 或使用者環境變數讀取；勿把 key 寫入 repo。

## 7. 專案目錄（快速參考）

> **完整專案結構請參考**: [README.md - 專案結構說明](./README.md#-專案結構說明)

**重點目錄**：
- **docs/** - 開發文件
  - `spec_model.md`、`spec_web.md`、`spec_web_api.md` - 主索引文件
  - `model/` - 模型詳細文件（Pipeline、資料字典、特徵工程等）
  - `web/` - 網站詳細文件
  - `shared/` - 共用文件（Pipeline 配置系統）
- **src/ML_boxoffice/** - 模型相關程式碼
- **src/web/** - 網站相關程式碼
- **data/** - 原始與處理後資料存放區
- **.venv/** - 虛擬環境（由 uv 管理）

## 8. 常見問題（Agent 指南版）
- Q: 為何 Claude Code 使用舊身分／環境變數沒生效？  
  A: 環境變數在該終端視窗有效；若在 VS Code extension 使用，重新載入視窗或把 env 加到 extension 設定。不要把 API key 寫死到 repo。
- Q: 如何在 Agent 執行時確保使用正確 Python 版本？  
  A: 讀取 `.python-version`，並透過 `uv run` 執行以確保一致性。

## 9. Agent 操作範例（Copilot 可直接執行或參考）
- 更新欄位後檢查步驟（自動化流程）：
~~~bash
# 1. 更新 feature_config.yaml 與 data_dictionary.md
# 2. 執行單元測試
uv run pytest -q
# 3. 執行資料處理 dry-run
uv run src/ML_recommend/data_integration/master_data_builder.py --dry-run
# 4. 檢查輸出檔案時間戳與路徑是否符合規範
~~~
- 新增相依（範例）
~~~bash
uv add pandas==2.0.3
uv sync
~~~

## 10. 建議放置檔名（方便 Agent / 人類辨識）
- `COPILOT_AGENT_README.md`（放在專案根目錄，供 Copilot/GitHub action/Reviewer 讀取）
- `docs/model/ml_特徵配置.yaml`（機器用欄位定義）
- `docs/spec_*.md`（開發規格主索引）