# 電影票房預測網站 - 單片詳細資訊頁面

## 專案結構
```
movie_prediction_web/
├── pyproject.toml              # uv 套件管理設定
├── app.py                      # Flask 主程式
├── config.py                   # 配置設定
├── models/                     # 資料模型
│   ├── __init__.py
│   ├── movie.py               # 電影資料模型
│   └── prediction.py          # 預測模型介面
├── services/                   # 商業邏輯層
│   ├── __init__.py
│   ├── movie_service.py       # 電影資料服務
│   └── prediction_service.py  # 預測服務
├── static/                     # 靜態資源
│   ├── css/
│   │   ├── main.css          # 主要樣式
│   │   └── components.css    # 元件樣式
│   └── js/
│       ├── main.js           # 主要 JavaScript
│       └── charts.js         # 圖表相關
├── templates/                  # HTML 模板
│   ├── base.html              # 基礎模板
│   ├── movie_detail.html      # 電影詳細頁面
│   └── components/            # 共用元件
│       ├── header.html        # 頁首
│       ├── sidebar.html       # 側邊欄
│       └── alerts.html        # 預警提示
└── utils/                      # 工具函數
    ├── __init__.py
    ├── formatters.py          # 格式化工具
    └── validators.py          # 驗證工具
```

## 功能說明
- 單部電影基本資訊展示
- 歷史票房與未來三週預測
- 票房衰退率預警
- 報表下載功能
- RWD 響應式設計

## UI 設計規範
- 主色：紫藍漸層 (#9C6DFF → #71DDFF)
- 背景：深色系 (#1a1a1a, #2a2a2a)
- 強調色：淺紫色 (#DADAFF)
- 圓角元素、漸層按鈕、現代科技感
