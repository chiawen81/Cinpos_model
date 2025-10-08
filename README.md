🎬 Movie Recommendation System

一個以 Python + uv 建構的電影推薦與話題分析系統
目前專注於自動爬取 IMDb、台灣票房資料，並計算推薦分數。
未來將整合社群輿情（PTT / Dcard / 巴哈姆特）作為話題熱度指標。

📁 專案結構說明
movie_recommendation/
│
├── .venv/                      # 虛擬環境 (由 uv 自動管理)
│
├── data/
│   ├── raw/                    # 原始爬下來的資料 (JSON/CSV)
│   └── processed/              # 清理後、可用於模型訓練或展示的資料
│
├── src/
│   ├── movie_recommendation/   # 🎯 推薦模型模組
│   │   ├── __init__.py
│   │   ├── crawler/
│   │   │   ├── imdb_crawler.py     # IMDb 資料爬取
│   │   │   ├── tw_boxoffice.py     # 台灣票房資料
│   │   │   └── now_showing.py      # 目前上映清單
│   │   ├── compute_score.py        # 計算推薦分數
│   │   ├── data_cleaning.py        # 整理與標準化資料
│   │   └── utils.py                # 共用函式
│   │
│   ├── trend/                  # 💬 話題風向模組
│   │   ├── __init__.py
│   │   ├── crawler/
│   │   │   ├── ptt_crawler.py      # PTT 熱門關鍵字
│   │   │   ├── dcard_crawler.py    # Dcard 熱門討論
│   │   │   └── bahamut_crawler.py  # 巴哈姆特熱度追蹤
│   │   ├── keyword_extract.py      # 關鍵詞抽取
│   │   ├── topic_summary.py        # 熱門話題摘要
│   │   └── utils.py
│   │
│   ├── __init__.py
│   └── main.py                 # 專案執行入口（整合推薦＋話題模組）
│
├── config/
│   └── settings.yaml           # 統一設定檔 (API key、爬蟲 URL、權重參數等)
│
├── logs/                       # 紀錄爬蟲或模型運行日誌
│
├── pyproject.toml              # uv 專案設定檔（取代 requirements.txt）
├── .gitignore                  # 忽略不需追蹤的檔案
└── README.md                   # 專案說明文件（本檔）

⚙️ 專案初始化與環境設定
1️⃣ 建立虛擬環境（自動生成 .venv/）
python -m venv .venv

2️⃣ 安裝依賴套件
uv sync


pyproject.toml 會自動安裝 requests、beautifulsoup4、pandas、lxml 等依賴。

3️⃣ 進入虛擬環境
.venv/Scripts/activate


（或在 VSCode 的 Python Interpreter 選擇 .venv）

🚀 執行主程式
uv run python src/main.py


預設流程：

抓取目前上映中電影清單

取得 IMDb 與票房資料

計算推薦分數

（未來）更新話題風向資料

🧩 常用開發指令
功能	指令
新增套件	uv add <package>
移除套件	uv remove <package>
查看套件	uv tree
執行程式	uv run python src/main.py
匯出依賴清單	uv export > requirements.txt
更新環境	uv sync
🧠 專案開發階段
階段	目標	內容
Lv1	推薦分數模型	IMDb + 台灣票房資料
Lv2	自動化爬蟲	每週更新電影資料
Lv3	社群熱度分析	整合 PTT / Dcard / 巴哈姆特
Lv4	儀表板展示	數據視覺化、推薦排行、熱門話題呈現
📜 License

本專案僅作為個人學習與研究用途，不用於商業發行。
部分資料來源自 IMDb、台灣政府開放資料平台、PTT、Dcard、巴哈姆特等公共網站。