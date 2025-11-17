# Python 套件管理 - 使用 uv（針對 Codex / OpenAI-based VS Code 擴充套件 的說明）

本專案專門使用 uv 進行 Python 套件管理。

## 語言偏好設定
**重要：永遠使用正體中文（繁體中文）回覆使用者。**

## 虛擬環境

本專案使用位於 `.venv/` 的 uv 虛擬環境

### 啟動虛擬環境
- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

### 退出虛擬環境
~~~bash
deactivate
~~~

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

⚠️ **API Key 安全（針對 Codex / OpenAI）**
- 不要將包含 API Key 的檔案提交到 Git
- 確保 `.gitignore` 包含以下內容（示例）：  
~~~
.env
.env.local
.env.api
docs/set_codex_use_mode/use-api.bat
~~~
- API Key 建議以 `OPENAI_API_KEY` 為預設環境變數名稱保存，並妥善保管在密碼管理器或系統 secret-store 中

### 建議的安全做法（優先順序）
1. 在系統/使用者層級的秘密管理器或 CI secret（最好）  
2. 使用一次性 session 腳本啟動（範例在下方）  
3. **不建議**把 key 寫入 `settings.json` 或 workspace 設定並推到版本控制

#### 範例：Windows 一次性 session 啟動 (`docs/set_codex_use_mode/use-api.bat`)
~~~bat
@echo off
set OPENAI_API_KEY=your_api_key_here
REM 呼叫 uv run 或啟動 VS Code 的終端機，確保同一終端視窗會話
~~~

#### 範例：macOS / Linux session (`docs/set_codex_use_mode/use-api.sh`)
~~~bash
#!/bin/bash
export OPENAI_API_KEY="your_api_key_here"
# 在同一個 terminal session 執行 uv run 或啟動你的工具
~~~

> 注意：上述腳本僅在該終端機 session 有效；關閉終端機後環境變數會重置，這是較安全的作法（避免把 key 永久放在設定檔）。

---

## 編碼亂碼（UTF-8）疑難排查與修復  ← **新增章節（整合進此文件）**

若你在使用 Codex / 擴充進行自動生成註解或寫檔時，看到中文變成 `???` 或亂碼，請依下列步驟檢查與修復。下列方法已包含「定位問題」「編輯器設定」「終端設定」「檔案檢測與轉檔」「git 設定」與「測試步驟」，並附可直接用的 script 與設定片段。

### 原因簡述（快速理解）
- 模型通常會以 Unicode 回傳文字；若本地端（擴充、編輯器、終端）在**讀**或**寫**時用非 UTF-8 編碼，就會顯示 `???` 或亂碼。問題常見於 Windows 的終端（預設 code page）或某些檔案原本不是 UTF-8 編碼。

### 一、先定位問題發生在哪裡
1. 開檔就看到 `???` → 檔案編碼不是 UTF-8。  
2. 只有在 Codex 自動插入後變 `???`（但你手動貼相同字串正常）→ 擴充在寫檔時做了錯誤的編碼轉換或終端/Output 捕獲問題。  
3. Output/Terminal 顯示 `???` → 終端編碼或 extension 的 stdout encoding 有問題。

### 二、VS Code（編輯器）設定：統一為 UTF-8
- 在 VS Code 右下角檢查目前檔案編碼（會顯示 `UTF-8` 或其它）；若不是 UTF-8，請 Reopen with Encoding → UTF-8，並 Save with Encoding → UTF-8。  
- 將以下加入你的 user 或 workspace `settings.json`：
~~~json
{
  "files.encoding": "utf8",
  "files.autoGuessEncoding": false
}
~~~

### 三、Terminal 編碼（重要，尤其是 Windows）
- Windows cmd（臨時修復）：執行 `chcp 65001` 切換到 UTF-8 code page。  
- PowerShell 建議在 `$PROFILE` 加入以下（永久於該 user session 生效）：
~~~powershell
# 放入 $PROFILE（例如 C:\Users\<you>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1）
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:LANG = "en_US.UTF-8"
~~~
- macOS / Linux：確認 `echo $LANG` 包含 `UTF-8`（例如 `en_US.UTF-8`）。若沒有，執行 `export LANG=en_US.UTF-8` 作短期測試。

### 四、檢查並轉換非 UTF-8 檔案（實作腳本）
#### 1) Python 檢測腳本（放在 repo 根，執行後列出不能用 UTF-8 讀的檔案）
~~~python
# detect_non_utf8.py
import glob

bad = []
for p in glob.glob("**/*", recursive=True):
    if p.endswith(('.png','.jpg','.jpeg','.gif','.exe','.bin','.so')): 
        continue
    try:
        with open(p, encoding='utf-8') as f:
            f.read()
    except (UnicodeDecodeError, PermissionError, IsADirectoryError):
        bad.append(p)

if bad:
    print("非 UTF-8 或無法以 UTF-8 開啟：")
    for b in bad:
        print(" -", b)
else:
    print("所有檔案都可用 UTF-8 讀取。")
~~~

#### 2) Bash 檢測（WSL / macOS / Git Bash）
~~~bash
# detect-non-utf8.sh
#!/bin/bash
shopt -s globstar
for f in **/*; do
  if [[ -d "$f" ]]; then continue; fi
  case "$f" in
    *.png|*.jpg|*.jpeg|*.gif|*.exe|*.bin|*.so) continue ;;
  esac
  if ! iconv -f utf-8 -t utf-8 "$f" >/dev/null 2>&1; then
    echo "非 UTF-8: $f"
  fi
done
~~~

#### 3) 轉檔範例（先備份再轉換，示範從 CP950/GBK → UTF-8）
- 若你確定原本是 CP950（繁體 Windows），可用：
~~~bash
iconv -f CP950 -t UTF-8 file.py -o file.py.utf8 && mv file.py.utf8 file.py
~~~
- 若原本可能是 GBK（簡體 Windows）：
~~~bash
iconv -f CP936 -t UTF-8 file.py -o file.py.utf8 && mv file.py.utf8 file.py
~~~
> 若不確定原始編碼，可使用 `file`、`enca`、`chardet` 等工具先偵測。

### 五、git 設定（減少不同開發者間的差異）
在 repo 根新增 `.gitattributes` 強制文字處理：
~~~text
# .gitattributes
* text=auto
*.py text
*.md text
*.json text
~~~
轉換後執行：
~~~bash
git add --renormalize .
git commit -m "Normalize text files to ensure consistent encoding"
~~~
> 注意：`.gitattributes` 幫助行尾與文本屬性一致，但不會自動轉編碼；請先用 iconv 等工具將檔案轉成 UTF-8 再 commit。

### 六、檢查 VS Code extension / Codex 的輸出
1. 在 VS Code 打開「Output」視窗，從下拉清單選擇 Codex / OpenAI 相關的 extension，檢視 log 是否有編碼或寫檔錯誤。  
2. 檢查 extension 設定（齒輪）是否有與 encoding/charset 相關的選項，若有，改為 UTF-8 或關閉自動轉碼。  
3. 若問題只在 extension 自動寫入時發生，請暫時改成 copy/paste（手動）或在 extension 設定中找「write encoding」選項。

### 七、短期快速驗證（確認修復有效）
- 在同一個已設 `OPENAI_API_KEY` 的終端（或已執行 `use-api.bat` / `use-api.sh` 的 session）執行：
~~~bash
# 檢查環境變數
printenv OPENAI_API_KEY || echo %OPENAI_API_KEY%
# 簡單測試：在 terminal 輸出中文（檢查是否正確顯示）
echo "測試：中文顯示是否正常"
~~~
- 在 VS Code 中用 Codex 讓它生成一小段繁體中文註解，觀察 Output 與檔案是否正確顯示。

### 八、如果以上仍沒解決（後續排查）
1. 把 Codex 的 Output log 貼出（Output 面板選 Codex / OpenAI extension）。  
2. 把「出問題的檔案」上傳或貼前後 50 行內容給我，我可以協助判別檔案原編碼並給出轉檔命令。  
3. 若懷疑是 extension 的 bug，提供擴充名稱與版本，並考慮回退擴充版本或在擴充的 issue tracker 提交 bug report（附上 log 與重現步驟）。

---

## Codex / VS Code 擴充套件 的設定說明（通用建議）

1. **環境變數**：多數基於 OpenAI 的擴充套件會讀取 `OPENAI_API_KEY`。若擴充套件需要其它設定，請參考該擴充套件官方說明。  
2. **在 VS Code 裡測試**：啟動 session（使用上述腳本），在同一終端機視窗執行 `uv run <script>`，或在 VS Code 中開啟「新終端」並確保該終端是由你執行過腳本的那個 session。  
3. **避免把 key 存在 workspace settings**：若不得已需要在 settings 中設定（某些擴充會有 API key 欄位），務必不要把該設定檔加入版本控制，或使用 VS Code 的「擴充設定 UI」在本機手動填入（但仍有風險）。  
4. **如何確認已生效**：在已設定 `OPENAI_API_KEY` 的終端機執行簡單的健康檢查腳本，或在擴充套件的調試面板觀察是否能成功連線。

---

## 📋 文件維護規則

### [工作日誌](docs\WORK_LOG.md)
1. 每次開啟時，請前往工作日誌了解當前情況  
2. 若有重大進展或改變，請更新工作日誌  
3. 若工作日誌的內容與現況差距太大時，請主動提醒（可能太久沒更新）

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

## 📦 專案文件結構（範例）
~~~text
docs/
├── ML_boxoffice/
│   ├── pipeline.md              # Pipeline 流程 + 建模策略
│   ├── data_dictionary.md       # 欄位定義（人類可讀）
│   ├── data_processing_rules.md # 資料處理規則
│   └── feature_config.yaml      # 欄位定義（機器可讀）
├── shared/ (共用文件) 
    ├── docs\shared\pipeline_config_usage.md   # Pipeline 配置系統使用說明
    └── docs\shared\pipeline_modification_guide.md # Pipeline 系統的修改檢查清單
~~~

---

## 常見問題（FAQ）

### Q: 為什麼切換後 Codex（或 OpenAI 擴充套件）還是使用舊的身分（API key）？
**A:** 環境變數只在當前終端機視窗有效。請確保：  
1. 在執行腳本的同一個終端機視窗中使用該擴充套件或執行命令（不要在不同終端或不同 shell session 切換）。  
2. 若使用 VS Code 擴充功能，若有改動環境變數或 session，請重新載入視窗（`Ctrl + Shift + P` → `Reload Window`）以確保擴充套件讀到最新環境。  
3. 最穩妥的作法是使用一次性 session 腳本（上方 `use-api.bat` / `use-api.sh`），在該終端內啟動你的工作流程。

### Q: 關閉終端機後模式會改變嗎？
**A:** 會的。關閉終端機後環境變數會重置，預設會回到系統或擴充套件預設的行為（通常為未設定 API key 的狀態）。

### Q: 如何永久設定使用 API Key？
**A:** 如果你真的需要「在此台機器上長期使用」，可以在系統層級（Windows Credential Manager / macOS Keychain / Linux secret store）或 CI secret 中設定；**不建議**把 API key 直接寫入 VS Code 的 `settings.json`。若擴充套件提供「安全的 key 管理」界面，請優先使用該功能。  

---

## 專案資訊

- **專案名稱**：Cinpos_model  
- **Python 版本**：使用 `.python-version` 檔案中指定的版本  
- **套件管理工具**：uv  
- **虛擬環境位置**：`.venv/`

