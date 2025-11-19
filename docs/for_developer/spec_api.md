# API 規格文件

本文件記錄電影票房預測系統的所有 API 端點規格。

## 目錄

- [統計資料 API](#統計資料-api)
  - [取得近期上映電影統計](#取得近期上映電影統計)
  - [取得所有統計資料](#取得所有統計資料)
- [票房列表 API](#票房列表-api)
  - [取得票房列表](#取得票房列表)
- [電影資料 API](#電影資料-api)
- [預測 API](#預測-api)

---

## 統計資料 API

### 取得近期上映電影統計

取得近期（1-4週內）上映電影的數量統計。

#### 基本資訊

- **端點**：`/api/stats/recent-movies`
- **方法**：`GET`
- **實作檔案**：
  - Blueprint：`src/web/business/detail/blueprints/stats_api.py`
  - Service：`src/web/business/detail/services/stats_service.py`

#### 請求參數

無

#### 請求範例

```bash
GET /api/stats/recent-movies
```

```bash
curl http://localhost:5000/api/stats/recent-movies
```

#### 回應格式

```json
{
  "success": true,
  "data": {
    "recent_count": 97,           // 近期上映電影數量（1-4週內）
    "change_from_last_week": 8,   // 較上週的變化
    "last_week_count": 89         // 上週的數量
  }
}
```

#### 錯誤回應

```json
{
  "success": false,
  "error": "取得統計資料失敗: [錯誤訊息]"
}
```

#### 業務邏輯

1. 讀取最近 3 週的週票房資料檔案（`data/raw/boxoffice_weekly/`）
2. 統計本週上映天數 ≤ 28 天的電影數量
3. 統計上週上映天數 ≤ 28 天的電影數量
4. 計算變化量（本週 - 上週）

#### 備註

- 上映天數來自資料檔案的 `dayCount` 欄位
- 4週 = 28天

---

### 取得所有統計資料

取得首頁所有統計卡片的資料，包含近期上映電影、追蹤中電影、預警電影。

#### 基本資訊

- **端點**：`/api/stats/all`
- **方法**：`GET` 或 `POST`
- **實作檔案**：
  - Blueprint：`src/web/business/detail/blueprints/stats_api.py`
  - Service：`src/web/business/detail/services/stats_service.py`

#### 請求參數

##### Query Parameters (GET)

| 參數名稱 | 類型 | 必填 | 說明 |
|---------|------|------|------|
| `tracked_movie_ids` | string | 否 | 追蹤的電影 ID 列表（逗號分隔） |

##### Request Body (POST)

| 參數名稱 | 類型 | 必填 | 說明 |
|---------|------|------|------|
| `tracked_movie_ids` | array | 否 | 追蹤的電影 ID 列表 |

#### 請求範例

**GET 請求**：
```bash
GET /api/stats/all?tracked_movie_ids=32462,32514,31965
```

```bash
curl "http://localhost:5000/api/stats/all?tracked_movie_ids=32462,32514,31965"
```

**POST 請求**：
```bash
POST /api/stats/all
Content-Type: application/json

{
  "tracked_movie_ids": ["32462", "32514", "31965"]
}
```

```bash
curl -X POST http://localhost:5000/api/stats/all \
  -H "Content-Type: application/json" \
  -d '{"tracked_movie_ids": ["32462", "32514", "31965"]}'
```

#### 回應格式

```json
{
  "success": true,
  "data": {
    "recent_movies": {
      "recent_count": 97,           // 近期上映電影數量
      "change_from_last_week": 8,   // 較上週的變化
      "last_week_count": 89         // 上週的數量
    },
    "tracked_movies": {
      "count": 3                     // 追蹤中電影數量
    },
    "warning_movies": {
      "total_count": 2,              // 預警電影總數
      "attention_count": 1,          // 注意狀態的電影數量
      "critical_count": 1            // 嚴重狀態的電影數量
    }
  }
}
```

#### 錯誤回應

```json
{
  "success": false,
  "error": "取得統計資料失敗: [錯誤訊息]"
}
```

#### 業務邏輯

**近期上映電影**：
1. 讀取最近 3 週的週票房資料
2. 統計上映天數 ≤ 28 天的電影數量
3. 計算較上週的變化

**追蹤中電影**：
1. ⚠️ **臨時方案**：從請求參數取得追蹤清單，計算數量
2. 🔄 **未來改進**：從後端資料庫根據使用者 ID 查詢追蹤清單

**預警電影**：
1. ⚠️ **臨時方案**：從請求參數取得追蹤的電影 ID
2. 載入所有最近的電影資料
3. 篩選出追蹤的電影
4. 計算每部電影的預警狀態（正常/注意/嚴重）
5. 統計注意和嚴重狀態的電影數量
6. 🔄 **未來改進**：從後端資料庫查詢使用者追蹤清單

#### 預警狀態判斷標準

參考[衰退預警系統](spec_project.md#衰退預警系統)

簡化版判斷邏輯：
- **第1-3週**：
  - 衰退率 < -50%：嚴重
  - 衰退率 < -30%：注意
  - 其他：正常
- **第4週以後**：
  - 衰退率 < -40%：嚴重
  - 衰退率 < -25%：注意
  - 其他：正常

#### 備註

- 支援 GET 和 POST 兩種請求方式
- 前端建議使用 POST 請求，避免 URL 過長
- `tracked_movie_ids` 為空時，`tracked_movies.count` 和 `warning_movies` 統計均為 0

---

## 票房列表 API

### 取得票房列表

取得電影票房列表資料，支援篩選、排序、分頁。

#### 基本資訊

- **端點**：`/api/boxoffice/list`
- **方法**：`GET`
- **實作檔案**：
  - Blueprint：`src/web/business/detail/blueprints/boxoffice_list_api.py`
  - Service：`src/web/business/detail/services/boxoffice_list_service.py`

#### 請求參數

##### Query Parameters

| 參數名稱 | 類型 | 必填 | 預設值 | 說明 |
|---------|------|------|--------|------|
| `page` | integer | 否 | 1 | 頁碼（從1開始） |
| `page_size` | integer | 否 | 10 | 每頁筆數 |
| `start_date` | string | 否 | - | 起始上映日期（YYYY-MM-DD） |
| `end_date` | string | 否 | - | 結束上映日期（YYYY-MM-DD） |
| `warning_status` | string | 否 | - | 預警狀態（正常/注意/嚴重） |
| `release_status` | string | 否 | - | 上映狀態（即將上映/上映中/已下檔） |
| `is_first_run` | boolean | 否 | - | 是否首輪 |
| `sort_by` | string | 否 | release_date | 排序欄位 |
| `sort_order` | string | 否 | desc | 排序方向（asc/desc） |

##### 可用的 sort_by 欄位

- `release_date` - 上映日期
- `current_week` - 當前週次
- `movie_name` - 電影名稱
- `last_week_decline_rate` - 上週衰退率
- `current_week_predicted` - 當週預測票房

#### 請求範例

**基本查詢**：
```bash
GET /api/boxoffice/list?page=1&page_size=10
```

**篩選近期上映**：
```bash
GET /api/boxoffice/list?start_date=2025-10-20&release_status=上映中
```

**篩選預警電影**：
```bash
GET /api/boxoffice/list?warning_status=嚴重
```

```bash
curl "http://localhost:5000/api/boxoffice/list?page=1&page_size=10&warning_status=嚴重"
```

#### 回應格式

```json
{
  "success": true,
  "data": [
    {
      "movie_id": "31965",
      "movie_name": "自殺通告",
      "release_date": "2025-11-07",
      "current_week": 4,
      "current_week_predicted": 1482454.30,      // 當週預測票房（元）
      "last_week_predicted": 1504281.36,         // 上週預測票房（元）
      "last_week_actual": 1679716.0,             // 上週實際票房（元）
      "last_week_decline_rate": 0.0475,          // 上週衰退率（小數，如 0.0475 = 4.75%）
      "prediction_accuracy": 0.1166,             // 預測差距%（小數，如 0.1166 = 11.66%）
      "warning_status": "正常",                  // 預警狀態
      "release_status": "上映中",                // 上映狀態
      "is_first_run": true,                      // 是否首輪
      "is_tracked": false,                       // 是否追蹤
      "rating": "輔12級",                        // 分級
      "theater_count": 3,                        // 院線數
      "total_amount": 1620350.0                  // 累計票房（元）
    }
  ],
  "pagination": {
    "page": 1,              // 當前頁碼
    "page_size": 10,        // 每頁筆數
    "total_count": 120,     // 總筆數
    "total_pages": 12       // 總頁數
  }
}
```

#### 錯誤回應

```json
{
  "success": false,
  "error": "取得票房列表失敗: [錯誤訊息]"
}
```

#### 業務邏輯

##### 1. 資料來源

- **週票房資料**：`data/raw/boxoffice_weekly/{year}_{week}.json`
  - 包含每週所有上映電影的基本資訊（電影ID、名稱、上映日期、上映天數等）

- **電影詳細資料**：`data/raw/boxoffice_permovie/full/{movie_id}_{name}.json`
  - 包含電影完整的週次票房歷史資料（`data.weeks` 陣列）

##### 2. 當前週次計算

```python
# weeks_data 包含的是已結束的週次資料
total_weeks_with_data = len(weeks_data)
current_week = total_weeks_with_data + 1
```

**說明**：
- `weeks_data` 是從 `boxoffice_permovie/full` 讀取的歷史週次資料
- 每筆資料代表一個已結束的週次
- 當前週次 = 歷史週數 + 1

**範例**：
- 有 3 筆歷史資料（第 1、2、3 週已結束）→ `current_week = 4`
- 有 2 筆歷史資料（第 1、2 週已結束）→ `current_week = 3`

##### 3. 預測計算

使用預測服務（`PredictionService`）進行票房預測，確保與預測頁面的邏輯一致。

**當週預測**（`current_week_predicted`）：
```python
# 使用所有歷史資料（N 週）預測第 N+1 週
target_week = total_weeks_with_data + 1
history_weeks = weeks_data[:total_weeks_with_data]  # 使用所有歷史資料
current_week_predicted = predict_boxoffice_for_week(
    movie_id, movie_detail, weeks_data, target_week
)
```

**上週預測**（`last_week_predicted`）：
```python
# 使用前 N-1 週資料預測第 N 週
target_week = total_weeks_with_data
history_weeks = weeks_data[:total_weeks_with_data - 1]  # 使用前 N-1 週資料
last_week_predicted = predict_boxoffice_for_week(
    movie_id, movie_detail, weeks_data, target_week
)
```

**預測條件**：
- 需要至少 2 週的歷史資料才能進行預測
- 如果 `target_week < 3`，預測會返回 `null`
- 如果 `len(history_weeks) < 2`，預測會返回 `null`

**範例**：
- 有 3 週歷史：
  - 當週預測：使用第 1、2、3 週預測第 4 週 ✅
  - 上週預測：使用第 1、2 週預測第 3 週 ✅
- 有 2 週歷史：
  - 當週預測：使用第 1、2 週預測第 3 週 ✅
  - 上週預測：使用第 1 週預測第 2 週（資料不足）❌ → `null`
- 有 1 週歷史：
  - 當週預測：使用第 1 週預測第 2 週（資料不足）❌ → `null`
  - 上週預測：無法預測 ❌ → `null`

##### 4. 上週實際票房

```python
last_week_actual = weeks_data[-1].get('amount')
```

**說明**：取得 `weeks_data` 的最後一筆資料（最新的已結束週次）的票房金額。

##### 5. 上週衰退率

```python
last_week_decline_rate = weeks_data[-1].get('rate')
```

**說明**：
- 直接讀取原始資料的 `rate` 欄位
- 原始資料的 `rate` 是相對於上一週的變化率
- 公式：`(當週票房 - 上週票房) / 上週票房`

##### 6. 預測差距%

```python
if last_week_predicted and last_week_actual:
    prediction_accuracy = (last_week_actual - last_week_predicted) / last_week_predicted
else:
    prediction_accuracy = None
```

**說明**：
- 正數表示實際高於預測（預測偏低）
- 負數表示實際低於預測（預測偏高）
- 如果上週預測或實際為 `null`，則預測差距也為 `null`

##### 7. 預警判斷

根據上週衰退率和當前週次判斷預警狀態：

```python
warning_status = calculate_warning_status(last_week_decline_rate, current_week)
```

**判斷標準**（簡化版）：
- **第 1-3 週**：
  - 衰退率 < -50%：嚴重
  - 衰退率 < -30%：注意
  - 其他：正常
- **第 4 週以後**：
  - 衰退率 < -40%：嚴重
  - 衰退率 < -25%：注意
  - 其他：正常

完整預警邏輯請參考[衰退預警系統](spec_project.md#衰退預警系統)。

##### 8. 上映狀態判斷

根據上映日期和上映天數判斷上映狀態：

```python
def calculate_release_status(release_date, day_count):
    if release_date > today:
        return "即將上映"
    elif day_count and day_count > 70:
        return "已下檔"
    else:
        return "上映中"
```

**判斷標準**：
- **即將上映**：上映日期在未來
- **上映中**：上映日期在過去且上映天數 ≤ 70 天
- **已下檔**：上映天數 > 70 天

#### 資料格式說明

##### 回應欄位詳細說明

| 欄位名稱 | 資料類型 | 單位/格式 | 說明 | 可能的值 |
|---------|---------|----------|------|---------|
| `movie_id` | string | - | 電影識別碼（政府ID） | "31965" |
| `movie_name` | string | - | 電影中文名稱 | "自殺通告" |
| `release_date` | string | YYYY-MM-DD | 上映日期 | "2025-11-07" |
| `current_week` | integer | 週 | 當前週次（歷史週數 + 1） | 4 |
| `current_week_predicted` | float / null | 元 | 當週預測票房 | 1482454.30 / null |
| `last_week_predicted` | float / null | 元 | 上週預測票房 | 1504281.36 / null |
| `last_week_actual` | float / null | 元 | 上週實際票房 | 1679716.0 / null |
| `last_week_decline_rate` | float / null | 小數 | 上週衰退率（-0.3 = -30%） | 0.0475 / null |
| `prediction_accuracy` | float / null | 小數 | 預測差距%（0.1 = 10%） | 0.1166 / null |
| `warning_status` | string | - | 預警狀態 | "正常" / "注意" / "嚴重" |
| `release_status` | string | - | 上映狀態 | "即將上映" / "上映中" / "已下檔" |
| `is_first_run` | boolean | - | 是否首輪（目前固定 true） | true |
| `is_tracked` | boolean | - | 是否追蹤（目前固定 false） | false |
| `rating` | string | - | 電影分級 | "輔12級" / "普遍級" / "限制級" |
| `theater_count` | integer | 間 | 院線數 | 3 |
| `total_amount` | float | 元 | 累計票房 | 1620350.0 |

##### 數值轉換說明

**票房金額**（`current_week_predicted`, `last_week_predicted`, `last_week_actual`, `total_amount`）：
- 後端 API 返回單位為「元」
- 前端顯示時需轉換為「萬元」：
  ```javascript
  const wan = value / 10000;
  ```
- 範例：1,603,550 元 → 160.36 萬元

**衰退率**（`last_week_decline_rate`）：
- 後端 API 返回小數格式
- 前端顯示時需轉換為百分比：
  ```javascript
  const percentage = value * 100;  // 0.0475 → 4.75%
  ```
- 正數表示成長，負數表示衰退

**預測差距**（`prediction_accuracy`）：
- 後端 API 返回小數格式
- 前端顯示時需轉換為百分比：
  ```javascript
  const percentage = value * 100;  // 0.1166 → 11.66%
  ```
- 正數表示實際高於預測（預測偏低）
- 負數表示實際低於預測（預測偏高）

##### Null 值說明

以下欄位可能返回 `null`：

- **`current_week_predicted`**：
  - 歷史資料不足 2 週
  - 預測模型執行失敗

- **`last_week_predicted`**：
  - 歷史資料不足 3 週（需要至少 2 週資料預測第 3 週）
  - 預測模型執行失敗

- **`last_week_actual`**：
  - 電影沒有歷史票房資料

- **`last_week_decline_rate`**：
  - 電影沒有歷史票房資料

- **`prediction_accuracy`**：
  - `last_week_predicted` 或 `last_week_actual` 為 `null`
  - `last_week_predicted` 為 0（避免除以零）

#### 前端分頁器整合

##### 1. 分頁參數傳遞

前端透過 URL 參數傳遞分頁資訊：

```javascript
const params = new URLSearchParams({
    page: currentPage,           // 當前頁碼（預設 1）
    page_size: 10,               // 每頁筆數（預設 10）
    sort_by: 'release_date',     // 排序欄位
    sort_order: 'desc'           // 排序方向
});

fetch(`/api/boxoffice/list?${params}`)
```

##### 2. 回應處理

從 API 回應取得分頁資訊並渲染分頁器：

```javascript
const response = await fetch(`/api/boxoffice/list?${params}`);
const result = await response.json();

if (result.success) {
    // 渲染電影列表
    renderBoxOfficeList(result.data);

    // 渲染分頁器
    const totalPages = result.pagination.total_pages;
    const currentPage = result.pagination.page;
    renderPagination(currentPage, totalPages);
}
```

##### 3. 分頁器狀態管理

```javascript
// 全域狀態
let currentPage = 1;
let totalPages = 1;
let currentFilters = {};

// 切換頁面
function changePage(newPage) {
    currentPage = newPage;
    loadBoxOfficeList({...currentFilters, page: newPage});
}

// 切換篩選條件時重置頁碼
function filterMovies(filterType) {
    currentPage = 1;
    currentFilters = buildFilters(filterType);
    loadBoxOfficeList(currentFilters);
}
```

##### 4. 分頁器顯示邏輯

- **總頁數 ≤ 1**：隱藏分頁器
- **總頁數 > 1**：顯示分頁器，最多顯示 5 個頁碼
- **當前頁 = 1**：「上一頁」按鈕禁用
- **當前頁 = 總頁數**：「下一頁」按鈕禁用

##### 5. 分頁與篩選整合

當使用者切換篩選條件時，需要重置頁碼為 1：

```javascript
// ❌ 錯誤：保留當前頁碼可能超出新的總頁數
loadBoxOfficeList({
    release_status: '上映中',
    page: currentPage  // 可能 > 新的 total_pages
});

// ✅ 正確：重置為第 1 頁
currentPage = 1;
loadBoxOfficeList({
    release_status: '上映中',
    page: 1
});
```

#### 備註

- **追蹤狀態**：
  - `is_tracked` 欄位目前固定為 `false`（後端無法判斷追蹤狀態）
  - ⚠️ **前端處理追蹤篩選**：當需要篩選「我的追蹤」時，前端從 localStorage 取得追蹤清單，自行篩選
  - 🔄 **未來改進**：後端整合使用者系統後，支援 `is_tracked` 參數篩選

- **首輪狀態**：
  - `is_first_run` 欄位目前固定為 `true`（原始資料無法判斷是否首輪）
  - 🔄 **未來改進**：整合更多資料來源後支援首輪判斷

- **預測一致性**：
  - 預測邏輯與預測頁面完全一致，使用相同的 `PredictionService.predict_new_movie()` 方法
  - 確保列表頁和詳細頁的預測結果相同

- **資料更新**：
  - 票房資料來源於爬蟲定期更新的檔案
  - 建議前端實作快取機制，避免重複請求相同資料

- **分頁實作**：
  - 完整的前端分頁器實作請參考 [專案規格文件](spec_project.md#分頁器功能)
  - 實作檔案：
    - HTML：`src/web/business/detail/templates/index.html`
    - JavaScript：`src/web/business/detail/static/js/pages/index.js`
    - CSS：`src/web/business/detail/static/css/ui-kits.css`

---

## 電影資料 API

（待補充）

---

## 預測 API

（待補充）

---

## API 文件撰寫規範

### 新增 API 端點時

每個新的 API 端點應包含以下章節：

1. **基本資訊**
   - 端點路徑
   - HTTP 方法
   - 實作檔案（Blueprint、Service）

2. **請求參數**
   - 參數表格（參數名稱、類型、必填、預設值、說明）
   - 參數驗證規則
   - 特殊參數說明

3. **請求範例**
   - 基本範例
   - 進階範例（包含篩選、排序等）
   - curl 命令範例

4. **回應格式**
   - 成功回應的 JSON 範例
   - 欄位說明（使用註解）
   - 資料格式說明

5. **錯誤回應**
   - 錯誤訊息格式
   - 常見錯誤情況

6. **業務邏輯**
   - 資料來源
   - 處理流程
   - 計算公式
   - 判斷標準

7. **備註**
   - 重要注意事項
   - 臨時方案標註（⚠️）
   - 未來改進方向（🔄）
   - 相關文件連結

### 文件維護原則

1. **即時更新**：API 修改時同步更新文件
2. **完整範例**：提供可直接執行的 curl 命令
3. **清晰註解**：JSON 範例中加入中文註解
4. **連結參考**：引用其他文件時使用 Markdown 連結
5. **版本標記**：重大變更時記錄版本和變更日期
