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

## Claude Code 身分驗證

本專案支援兩種身分驗證方式：

### 1. 訂閱身分（預設模式）
- 使用 Claude Pro/Max 訂閱的 OAuth 登入
- 不需要 API Key
- 受訂閱方案的速率限制約束

### 2. API Key（備用模式）
- 使用 Anthropic API 額度
- 需設定環境變數：`ANTHROPIC_API_KEY`
- 當訂閱身分被限流時使用

---

## 切換 Claude Code 使用模式

### 方法 1：執行批次檔（推薦）

在 VS Code 終端機中執行：

```bash
# 切換到訂閱身分模式
docs\set_claude_use_mode\use-subscription.bat

# 切換到 API Key 模式
docs\set_claude_use_mode\use-api.bat

# 檢查當前使用模式
docs\set_claude_use_mode\check-mode.bat
```

**注意事項：**
- 必須在 VS Code 的整合終端機中執行腳本
- 環境變數只在當前終端機視窗有效
- 切換後在同一個終端機視窗中使用 Claude Code
- 關閉終端機後環境變數會重置為預設值

### 方法 2：手動設定環境變數

在 PowerShell 終端機中執行：

```powershell
# 切換到訂閱身分模式
$env:ANTHROPIC_API_KEY=""

# 切換到 API Key 模式
$env:ANTHROPIC_API_KEY="sk-ant-api03-your-api-key-here"
```

切換後，重新啟動 Claude Code 擴充功能。

---

## 檢查當前使用模式

### 方法 1：執行檢查腳本
```bash
docs\set_claude_use_mode\check-mode.bat
```

輸出範例：
```
========================================
檢查當前 Claude Code 模式
========================================
[✓] 當前使用：訂閱身分模式
========================================
```

### 方法 2：手動檢查環境變數

在 PowerShell 中執行：
```powershell
$env:ANTHROPIC_API_KEY
```

**判斷方式：**
- 沒有輸出或輸出為空白 → 訂閱身分模式
- 顯示 API Key → API Key 模式

### 方法 3：在 VS Code 中查看

1. 開啟 Claude Code 擴充功能面板（點擊側邊欄的火花圖示 ⚡）
2. 查看右上角的帳號資訊
   - 顯示訂閱帳號名稱 → 訂閱身分模式
   - 顯示 API 相關資訊 → API Key 模式

---

## 使用建議


### 快速切換步驟
# 1. 檢查當前模式
  - 方法一：在終端機輸入 `docs\set_claude_use_mode\check-mode.bat`
  - 方法二：啟用claude後，輸入 `echo $ANTHROPIC_API_KEY` 查看環境變數是否存在(存在則為API Key模式，不存在則為訂閱身分模式)
# 2. 切換模式（如果需要）
  - 方法一：在終端機輸入 `docs\set_claude_use_mode\use-api.bat` 或 `docs\set_claude_use_mode\use-subscription.bat`
  - 方法二：
  ```
      # 啟用 claude code
      claude 

      # 使用登入切換
      /login

  ```
3. 在同一個終端機中使用 Claude Code

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

### 欄位定義文件（同步更新）

當修改特徵欄位時，必須同時更新：

1. **docs/ML_boxoffice/data_dictionary.md**
   - 人類可讀的欄位說明
   - 包含範例、計算邏輯

2. **docs/ML_boxoffice/feature_config.yaml**
   - 機器可讀的欄位定義
   - 供 AI Agent 和自動化工具讀取

### Pipeline 文件
- **docs/ML_boxoffice/pipeline.md**: Pipeline 流程、建模策略
- **docs/ML_boxoffice/data_processing_rules.md**: 資料處理規則

### 文件組織原則
- ✅ 所有文檔統一放在 `docs/` 下
- ❌ 不要在 `src/` 下放 Pipeline 說明文件

---

## 📦 專案文件結構

```
docs/
└── ML_boxoffice/
    ├── pipeline.md              # Pipeline 流程 + 建模策略
    ├── data_dictionary.md       # 欄位定義（人類可讀）
    ├── feature_config.yaml      # 欄位定義（機器可讀）
    └── data_processing_rules.md # 資料處理規則
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