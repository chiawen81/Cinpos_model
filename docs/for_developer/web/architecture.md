# 網站架構說明

## 專案重構記錄

**日期**: 2025-11-17
**類型**: 架構重構
**目的**: 將混雜在一起的路由拆分到不同的 Blueprint 模組中，使專案結構更清晰、更易維護

## 新的專案結構

```
src/web/business/detail/
├── app.py                    # 主應用程式（簡化，只負責初始化與註冊）
├── config.py                 # 應用程式配置
├── blueprints/               # 路由模組（新增）
│   ├── __init__.py           # Blueprint 匯出
│   ├── web_routes.py         # 前端頁面路由
│   ├── prediction_api.py     # 預測 API 路由
│   └── movie_api.py          # 電影資料 API 路由
├── services/                 # 業務邏輯層
│   ├── movie_service.py
│   └── prediction_service.py
├── utils/                    # 工具函式
│   ├── formatters.py
│   └── validators.py
├── templates/                # HTML 模板
└── static/                   # 靜態資源
```

## Blueprint 分類說明

### 1. web_routes.py - 前端頁面路由

**責任**: 處理所有返回 HTML 模板的請求

**路由清單**:
- `GET /` - 首頁儀表板
- `GET /movies` - 電影列表頁面
- `GET /movie/<gov_id>` - 單部電影詳細頁面
- `GET /predictions` - 預測分析頁面
- `GET /predict-new` - 新電影預測頁面
- `GET /reports` - 報表中心頁面

**特點**:
- 使用 Jinja2 模板渲染
- 包含圖表資料準備邏輯

### 2. prediction_api.py - 預測 API 路由

**責任**: 處理所有票房預測相關的 API 請求（自己開發的模型服務）

**URL 前綴**: `/api`

**路由清單**:
- `GET /api/movie/<gov_id>` - 取得電影詳細資料
- `GET /api/movie/<gov_id>/predict` - 預測電影票房
- `GET /api/movie/<gov_id>/latest` - 取得最新資料
- `GET /api/export/<gov_id>` - 匯出報表
- `GET /api/warning/<gov_id>` - 取得預警資訊
- `POST /api/predict-new` - 預測新電影票房
- `POST /api/predict-new/export` - 匯出新電影預測報表
- `POST /api/predict-new/download-preprocessed` - 下載預處理資料

**特點**:
- 所有回應均為 JSON 格式
- 包含資料驗證與錯誤處理
- 整合 ML 模型預測服務

### 3. movie_api.py - 電影資料 API 路由

**責任**: 處理電影資料查詢（目前代理外部 API，未來將改用自建資料庫）

**URL 前綴**: `/api`

**路由清單**:
- `GET /api/search-movie` - 搜尋電影
- `GET /api/movie-detail/<movie_id>` - 取得電影詳細資料

**特點**:
- 目前直接呼叫外部 API (boxofficetw.tfai.org.tw)
- TODO: 未來將改為查詢自建資料庫
- 包含 timeout 與錯誤處理機制

## app.py 的職責

重構後的 `app.py` 從原本的 617 行簡化到 80 行，只負責：

1. **應用程式初始化**: 建立 Flask app、載入配置、啟用 CORS
2. **註冊 Blueprint**: 整合所有路由模組
3. **模板過濾器**: 註冊自訂 Jinja2 過濾器
4. **錯誤處理**: 404、500 錯誤頁面
5. **啟動應用**: 開發伺服器啟動邏輯

## 重構的好處

### 1. 關注點分離
- 前端頁面與 API 端點清楚分離
- 不同業務邏輯（預測 vs 資料查詢）獨立管理

### 2. 更容易維護
- 每個檔案職責單一、更容易理解
- 新增功能時只需修改對應的 Blueprint
- 減少程式碼衝突的機會

### 3. 更好的可測試性
- 可以針對單一 Blueprint 撰寫測試
- 各模組可獨立測試

### 4. 更容易擴展
- 未來可以輕鬆新增更多 Blueprint（如管理後台、使用者認證等）
- 方便將來微服務化拆分

## 未來規劃

### 短期
- [ ] 建立自建資料庫取代外部 API 呼叫
- [ ] 為每個 Blueprint 撰寫單元測試
- [ ] 新增 API 文件（使用 Swagger/OpenAPI）

### 中期
- [ ] 實作使用者認證與授權 Blueprint
- [ ] 新增管理後台 Blueprint
- [ ] 實作 API 限流與快取機制

### 長期
- [ ] 考慮將預測服務拆分成獨立微服務
- [ ] 實作 GraphQL API 作為統一查詢介面

## 測試結果

✅ 所有 Blueprint 成功註冊
✅ 所有路由正常運作
✅ Flask 應用程式成功啟動
✅ API 端點回應正常

## 相關文件

- [模型規格文件](../spec_model.md) - 模型規格主索引
- [Pipeline 系統文件](../model/pipeline.md) - Pipeline 詳細流程
- [資料字典](../model/data_dictionary.md) - 資料欄位定義
- [專案指引](../../../CLAUDE.md) - 專案整體說明
