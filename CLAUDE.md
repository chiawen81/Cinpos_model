# Python 套件管理 - 使用 uv

本專案專門使用 uv 進行 Python 套件管理。

## 語言偏好設定
**重要：永遠使用正體中文（繁體中文）回覆使用者。**

## 虛擬環境

本專案使用位於 `.venv/` 的 uv 虛擬環境

### 啟動虛擬環境
- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

### 退出虛擬環境
```bash
deactivate
```

## 套件管理命令

所有 Python 相依套件**必須**使用 uv 來安裝、同步和鎖定。絕對不要直接使用 pip、pip-tools、poetry 或 conda 進行相依套件管理。

### 基本命令
- 安裝套件：`uv add <套件名稱>`
- 移除套件：`uv remove <套件名稱>`
- 同步套件：`uv sync`
- 從 pyproject.toml 安裝所有套件：`uv sync`

## 執行 Python 程式碼

- 執行 Python 腳本：`uv run <腳本名稱>.py`
- 執行 Python 工具：`uv run pytest` 或 `uv run ruff`
- 啟動 Python REPL：`uv run python`
- 在虛擬環境中執行命令：`uv run <命令>`

### 重要提醒
- 永遠使用 `uv run` 來執行 Python 腳本，它會自動使用虛擬環境
- 使用 `uv run` 時不需要手動啟動虛擬環境
- 執行 `uv sync` 時會自動建立虛擬環境

---

## Pipeline 系統修改指南

### 目的
確保當 Pipeline 系統 有新增或修改腳本時，所有相關檔案都能保持同步和一致性

### 原則
修改 Pipeline 系統時，記住三個核心原則：
   1. **同步性**：`pipeline_config.yaml`、`run_pipeline.py`、目標腳本三者參數介面必須一致
   2. **測試性**：務必使用 dry-run 模式測試命令生成
   3. **靈活性**：參數設為選填，提供合理的預設行為

### 參考文件
docs\shared\pipeline_modification_guide.md

---

## 安全提醒

⚠️ **API Key 安全**
- 不要將包含 API Key 的檔案提交到 Git
- 確保 `.gitignore` 包含以下內容：
  ```
  .env
  .env.local
  .env.api
  docs/set_claude_use_mode/use-api.bat
  ```
- API Key 應妥善保管在密碼管理器中

---

## 📋 文件維護規則

### [工作日誌](docs\WORK_LOG.md)
1. 每次開啟時，請前往工作日誌了解當前情況
2. 若有重大進展或改變，請更新工作日誌:
3. 若工作日誌的內容與現況差距太大時，請主動提醒(可能太久沒更新)


### 開發規格文件

專案的開發規格文件已統一整理至 `docs/for_developer/`：

#### 主索引文件
- **docs/for_developer/spec_model.md**: 模型規格主索引
- **docs/for_developer/spec_web.md**: 網站業務邏輯主索引
- **docs/for_developer/spec_web_api.md**: API 規格主索引
- **docs/for_developer/spec_guidelines.md**: 規格文件編寫規範

#### 詳細文件
- **模型相關**: `docs/for_developer/model/` - 包含 Pipeline、資料欄位定義、資料處理規則等
- **網站相關**: `docs/for_developer/web/` - 包含架構說明、使用指南等
- **共用文件**: `docs/for_developer/shared/` - Pipeline 配置系統使用說明

### 欄位定義文件（同步更新）

當修改特徵欄位時，必須同時更新：

1. **docs/for_developer/model/data_dictionary.md**
   - 人類可讀的欄位說明
   - 包含範例、計算邏輯

2. **docs/for_developer/model/feature_config.yaml**
   - 機器可讀的欄位定義
   - 供 AI Agent 和自動化工具讀取

### 文件組織原則
- ✅ 所有開發文檔統一放在 `docs/for_developer/` 下
- ✅ 採用「主索引 + 詳細文件」的兩層架構
- ❌ 不要在 `src/` 下放規格說明文件

---

## 📦 專案文件結構

```
docs/for_developer/
├── spec_model.md              # 模型規格（主索引）
├── spec_web.md                # 網站業務邏輯（主索引）
├── spec_web_api.md            # API 規格（主索引）
├── spec_guidelines.md         # 編寫規範
│
├── model/                     # 模型詳細文件
│   ├── pipeline.md
│   ├── data_dictionary.md
│   ├── data_processing_rules.md
│   ├── feature_engineering_refactoring.md
│   ├── feature_config.yaml
│   └── filter_data_tool.md
│
├── web/                       # 網站詳細文件
│   ├── architecture.md
│   └── download_preprocessed_data_guide.md
│
└── shared/                    # 共用文件
    ├── pipeline_config_usage.md
    └── pipeline_modification_guide.md
```

---

## 常見問題

### Q: 為什麼切換後 Claude Code 還是使用舊的身分？
**A:** 環境變數只在當前終端機視窗有效。請確保：
1. 在執行腳本的同一個終端機視窗中使用 Claude Code
2. 如果使用 VS Code 擴充功能，請重新載入視窗（`Ctrl + Shift + P` → `Reload Window`）

### Q: 關閉終端機後模式會改變嗎？
**A:** 會的。關閉終端機後環境變數會重置，預設會使用訂閱身分模式。

### Q: 如何永久設定使用 API Key？
**A:** 可以在 VS Code 設定中配置：
1. 按 `Ctrl + ,` 開啟設定
2. 搜尋 `claude-code.environmentVariables`
3. 新增 `"ANTHROPIC_API_KEY": "your-api-key"`

但不建議這樣做，因為會將 API Key 儲存在設定檔中。

---

## 專案資訊

- **專案名稱**：Cinpos_model
- **Python 版本**：使用 `.python-version` 檔案中指定的版本
- **套件管理工具**：uv
- **虛擬環境位置**：`.venv/`