# 🎬 Movie Recommendation System

> 一個以 Python + uv 建構的電影推薦與話題分析系統。  
> 目前專注於自動爬取 IMDb、台灣票房資料，並計算推薦分數。  
> 並整合社群輿情（PTT / Dcard / 巴哈姆特）作為話題熱度指標。

---
<br>

## 📁 專案結構說明

```plaintext
Cinpos_model/
│
├── .venv/                      # 虛擬環境 (由 uv 自動管理)
├── .gitignore                  # Git 忽略規則
├── CLAUDE.md                   # CLAUDE AI Agent 使用設定
├── NOTE.md                     # 開發備註
├── pyproject.toml              # uv 專案設定（依賴與腳本）
├── uv.lock                     # 鎖定依賴版本
├── .vscode/                    # VSCode 專案設定
│   └── config/
│       └── settings.yaml       # 編輯器設定（格式化、lint 等）
├── config/                     # 專案設定檔（API keys、權重等）
├── data/                       # 原始與處理後資料存放區
│   ├── manual_fix/             # 人工修正與映射檔
│   ├── ML_boxoffice/           # ML 用票房資料集
│   ├── ML_recommend/           # ML 用推薦資料集
│   ├── processed/              # 清理後可直接使用的資料
│   └── raw/                    # 原始爬蟲輸出（JSON/CSV）
├── docs/                       # 專案文件與說
│    ├─── ML_boxoffice/
│    │    ├── pipeline.md         Pipeline 流程 + 建模策略（整合版）
│    │    ├── data_dictionary.md # 欄位定義（人類可讀）
│    │    ├── feature_config.yaml# 欄位定義、資料處理規則（機器可讀）
│    │    └── data_processing_rules.md # 資料處理規則
│    └─── set_claude_use_mode/    # 切換 Claude Code 使用模式
├── logs/                       # 運行與爬蟲日誌
└── src/                        # 程式碼主目錄
    ├── __init__.py
    ├── main.py                 # 執行入口（整合推薦 + 話題模組）
    ├── cinpos_model.egg-info/  # 打包/建置相關資訊
    ├── common/                 # 共用工具函式
    │   ├── file_utils.py       # 檔案操作輔助
    │   ├── path_utils.py       # 路徑與專案根處理
    │   └── date_utils.py       # 日期時間相關工具
    ├── fetch_common_data/      # 爬蟲與資料清理流程
    │   ├── crawler/            # 爬蟲腳本
    │   │   └── __departure__/  # 舊版爬蟲（保留參考）
    │   └── data_cleaning/      # 資料清理 / 合併腳本
    │       ├── __departure__/  # 舊版清理程式
    │       ├── boxoffice_permovie.py   # 單片票房清理
    │       ├── boxoffice_weekly.py     # 週票房清理
    │       ├── omdb.py                 # OMDB/IMDb 資料整理
    │       └── movieInfo_gov_merge.py  # 與政府資料合併
    ├── ML_boxoffice/           # 票房預測模型與訓練程式
    ├── ML_recommend/           # 推薦模型、評分與評估工具
    └── ML_trend/               # 熱度 / 話題分析相關模型
```

<br>

## ⚙️ 專案初始化與環境設定
### 1️⃣ 建立虛擬環境（自動生成 .venv/）
```
python -m venv .venv
```

### 2️⃣ 安裝依賴套件
```
uv sync
```
`pyproject.toml` 會自動安裝 `requests`、`beautifulsoup4`、`pandas`、`lxml` 等依賴。

### 3️⃣ 進入虛擬環境
```
.venv/Scripts/activate
```
（或在 VSCode 的 Python Interpreter 選擇 .venv）

<br>

## 🚀 執行主程式
```
uv run python src/main.py
```

<br>

## 🧩 常用開發指令

| 功能 | 指令 |
|------|------|
| 建立虛擬環境 | `uv venv` |
| 安裝依賴 | `uv sync` |
| 新增套件 | `uv add <package>` |
| 移除套件 | `uv remove <package>` |
| 查看套件 | `uv tree` |
| 匯出依賴清單 | `uv export > requirements.txt` |
| 執行主程式 | `uv run python src/main.py` |

<br>

## 🧠 專案開發階段

| 階段 | 主功能 | 目標與內容 |
|------|------|------|
| Lv1 | 推薦分數模型 | 讓使用者得以評估「是否值得消費進場觀看電影」。<br>ps. 以自動化爬蟲抓取 IMDb + 台灣票房資料等資料 |
| Lv2 | 儀表板展示 | 數據視覺化顯示「票房排行」、「推薦電影」、「票房走勢預測」 |
| Lv3 | 社群熱度分析 | 讓使用者知道最近在夯什麼電影話題。<br>ps. 整合 PTT / Dcard / 巴哈姆特 |

<br>

## 📜 License

本專案僅作為個人學習與研究用途，不用於商業發行。  
部分資料來源自 IMDb、台灣政府開放資料平台、PTT、Dcard、巴哈姆特等公共網站。

