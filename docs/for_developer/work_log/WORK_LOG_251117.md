# 工作日誌

## 2025-01-17：自建後端資料庫（因應 Cloudflare 阻擋）

### 背景
呼叫外部 API（boxofficetw.tfai.org.tw）時被 Cloudflare 阻擋，因此改為自建本地資料庫。

### 實作內容

#### 1. API 路由設計
保留 `/api` 前綴，統一命名規範。

#### 2. 已實作的 API 端點

| API 端點 | 功能 | 資料來源 | 開發狀態 |
|---------|------|---------|---------|
| `/api/search-movie` | 搜尋電影 | `data/raw/boxoffice_weekly/2025/*.json` | ✅ 已開發 |
| `/api/movie/info/<movie_id>` | 取得電影基本資訊 | `data/processed/movieInfo_gov/combined/movieInfo_gov_full_*.csv` | ✅ 已開發 |
| `/api/movie/boxoffice/<movid>` | 取得電影完整資料（票房+資訊） | `data/raw/boxoffice_permovie/full/{movid}_*.json` | ✅ 已開發 |

#### 3. 除錯端點（開發用）

| API 端點 | 功能 | 用途 |
|---------|------|------|
| `/api/debug/paths` | 檢查路徑配置 | 驗證資料夾路徑是否正確 |
| `/api/debug/search` | 測試搜尋邏輯 | 除錯搜尋功能，顯示載入的電影數量 |

---

### API 詳細說明

#### `/api/search-movie`
- **方法**：GET
- **參數**：`keyword`（搜尋關鍵字）
- **資料來源**：`data/raw/boxoffice_weekly/2025/*.json`
- **功能**：從 2025 年週票房資料中搜尋電影
- **回傳欄位**：
  - `movieId`：電影 ID
  - `name`：電影名稱
  - `releaseDate`：上映日期
  - `duration`：片長（預設 120 分鐘）
  - `rating`：分級（空值）
- **測試結果**：✅ 成功載入 241 部電影，搜尋功能正常

#### `/api/movie/info/<movie_id>`
- **方法**：GET
- **參數**：`movie_id`（電影 ID，即 gov_id）
- **資料來源**：`data/processed/movieInfo_gov/combined/movieInfo_gov_full_*.csv`（自動選取最新檔案）
- **功能**：查詢電影詳細資料
- **回傳欄位**：
  - `movieId`：電影 ID
  - `name`：中文片名
  - `originalName`：原文片名
  - `releaseDate`：上映日期
  - `rating`：分級
  - `filmLength`：片長（秒）
  - `region`：地區
  - `publisher`：發行商
  - `director`：導演
  - `actors`：演員列表
- **測試結果**：✅ 成功取得《幻愛》(ID: 17126) 完整資料

#### `/api/movie/boxoffice/<movid>`（重點更新）
- **方法**：GET
- **參數**：`movid`（電影 ID，即 gov_id）
- **資料來源**：`data/raw/boxoffice_permovie/full/{movid}_*.json`
- **功能**：一次 API 呼叫取得完整電影資料（票房 + 電影資訊）
- **回傳欄位**：
  - **電影基本資訊**：
    - `movieId`：電影 ID
    - `name`：中文片名
    - `originalName`：原文片名
    - `region`：地區
    - `rating`：分級
    - `releaseDate`：上映日期
    - `publisher`：發行商
    - `filmLength`：片長（秒）
  - **票房資料**：
    - `amountInThisWeek`：本週票房
    - `totalAmount`：累計票房
  - **演員/導演資訊**：
    - `filmMembers`：陣列，包含 id, name, originalName, typeName（演員/導演/編劇）
  - **週末票房歷史**：
    - `weekends`：陣列，包含 date, amount, tickets, totalAmount, totalTickets, rate, theaterCount
- **測試結果**：✅ 成功取得《幻愛》完整資料（12 位演員/導演，263 筆週末票房）

---

### 資料來源架構調整

#### 原始資料儲存（已調整）
- **週次資料**：`data/raw/boxoffice_permovie/{YEAR}/{WEEK}/`
  - 檔名格式：`{movid}_{片名}_{WEEK_LABEL}.json`
  - 用途：保留歷史記錄

- **完整資料（新增）**：`data/raw/boxoffice_permovie/full/`
  - 檔名格式：`{movid}_{片名}.json`（不含週次標籤）
  - 用途：API 快速查詢，自動覆蓋更新
  - 更新機制：爬蟲執行時自動更新

#### 爬蟲調整
- **檔案**：`src/fetch_common_data/crawler/boxoffice_permovie.py`
- **調整內容**：
  1. 新增雙重儲存機制
  2. 同時儲存到週次資料夾（保留歷史）和 full 資料夾（供 API 使用）
  3. 新增路徑常數：`BOXOFFICE_PERMOVIE_FULL`（在 `src/common/path_utils.py`）

---

### 優勢總結

1. **減少 API 呼叫次數**：
   - 原本：需呼叫 `/movie/info` + `/movie/boxoffice`（2 次）
   - 現在：只需呼叫 `/movie/boxoffice`（1 次）

2. **資料完整性**：
   - 包含票房、分級、片長、演員、導演等所有資訊
   - 適合預測頁面使用（提供完整特徵）

3. **查詢效率**：
   - 直接讀取單一 JSON 檔案
   - 不需遍歷多週資料

4. **跨週搜尋**：
   - `full/` 資料夾包含所有電影（含已下檔電影）
   - 解決只查最新週次會遺漏舊電影的問題

5. **維護簡單**：
   - 執行爬蟲時自動更新
   - 不需額外的資料處理 pipeline

---

### 待辦事項

- [ ] 前端預測頁面整合新 API
- [ ] 驗收測試（確認預測功能正常運作）
- [ ] 清理除錯端點（或保留作為管理工具）
- [ ] 補充 API 使用文件

---

### 技術細節

**實作檔案**：
- `src/web/business/detail/blueprints/movie_api.py`（API 端點）
- `src/fetch_common_data/crawler/boxoffice_permovie.py`（爬蟲）
- `src/common/path_utils.py`（路徑配置）

**測試腳本**：
- `test_api.py`（完整測試）
- `test_new_api.py`（新 API 測試）
- `copy_to_full.py`（資料複製工具）
