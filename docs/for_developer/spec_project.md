# 需求文件

本文件記錄電影票房預測系統的所有頁面開發需求、互動邏輯。

## 首頁

### 統計卡片

首頁顯示三個統計卡片，提供快速概覽：

#### 1. 近一個月上映電影

顯示近期（1-4週內）上映的電影數量及較上週的變化。

- **資料來源**：`data/raw/boxoffice_weekly`
- **API 端點**：
  - `GET /api/stats/recent-movies` - 單獨取得近期電影統計
  - `POST /api/stats/all` - 取得所有統計（推薦）

- **計算邏輯**：
  - 從 boxoffice_weekly 目錄讀取最近的 JSON 檔案
  - 統計上映天數 ≤ 28 天（4週）的電影數量
  - 比較本週與上週的近期上映電影數量
  - 計算變化量（正數表示增加，負數表示減少）

- **實作檔案**：
  - 服務層：`src/web/business/detail/services/stats_service.py`
    - `StatsService.get_recent_movies_stats()` - 計算近期上映電影統計
    - `StatsService._count_recent_movies()` - 計算符合條件的電影數量
  - API：`src/web/business/detail/blueprints/stats_api.py`
    - `GET /api/stats/recent-movies` - 取得統計資料
  - 前端：`src/web/business/detail/static/js/pages/index.js`
    - `loadAllStats()` - 載入所有統計資料（推薦）
    - `loadRecentMoviesStats()` - 僅載入近期電影統計（已棄用）

- **API 回應格式**：
```json
{
  "success": true,
  "data": {
    "recent_count": 97,           // 近期上映電影數量
    "change_from_last_week": 8,   // 較上週的變化
    "last_week_count": 89         // 上週的數量
  }
}
```

- **顯示邏輯**：
  - 變化為正數：顯示綠色，格式為 "+X 較上週"
  - 變化為負數：顯示紅色，格式為 "X 較上週"
  - 變化為零：顯示 "與上週持平"

#### 2. 追蹤中電影

顯示使用者追蹤的電影數量。

- **資料來源**：
  - ⚠️ **臨時方案**：前端 localStorage（`tracked_movies`）
  - 🔄 **未來改進**：後端資料庫（使用者追蹤記錄表）

- **API 端點**：
  - `POST /api/stats/all` - 取得所有統計資料

- **計算邏輯**：
  - ⚠️ **臨時方案**：前端從 localStorage 取得追蹤的電影 ID 列表，傳給後端 API，後端返回列表長度
  - 🔄 **未來改進**：後端根據使用者 ID 從資料庫查詢追蹤記錄，計算數量

- **實作檔案**：
  - 服務層：`src/web/business/detail/services/stats_service.py`
    - `StatsService.get_all_stats(tracked_movie_ids)` - 計算追蹤數量
  - API：`src/web/business/detail/blueprints/stats_api.py`
    - `POST /api/stats/all` - 取得所有統計資料
  - 前端：
    - `src/web/business/detail/static/js/common/tracking.js`
      - `TrackingManager` - 管理追蹤清單（localStorage）
    - `src/web/business/detail/static/js/pages/index.js`
      - `loadAllStats()` - 載入統計資料
      - `updateTrackingCount()` - 更新追蹤數量

- **追蹤功能**：
  - **儲存位置**：localStorage 的 `tracked_movies` 鍵
  - **資料格式**：電影 ID 字串陣列，如 `["32462", "32514", "31965"]`
  - **操作方法**：
    - `trackingManager.addTracking(govId)` - 加入追蹤
    - `trackingManager.removeTracking(govId)` - 取消追蹤
    - `trackingManager.toggleTracking(govId)` - 切換追蹤狀態
    - `trackingManager.isTracked(govId)` - 檢查是否已追蹤

- **顯示邏輯**：
  - 顯示追蹤中電影的數量
  - 副標題固定為「個人追蹤」

#### 3. 預警電影

顯示追蹤中的電影裡，需要關注的預警電影數量（注意 + 嚴重）。

- **定義**：計算在「我的追蹤」的電影中，被判定為「注意」或「嚴重」的電影數量

- **資料來源**：
  - ⚠️ **臨時方案**：前端 localStorage（追蹤清單）+ 後端計算預警狀態
  - 🔄 **未來改進**：後端資料庫（使用者追蹤記錄 + 電影預警狀態）

- **API 端點**：
  - `POST /api/stats/all` - 取得所有統計資料

- **計算邏輯**：
  1. ⚠️ **臨時方案**：前端從 localStorage 取得追蹤的電影 ID 列表
  2. 前端將追蹤清單傳給後端 API
  3. 後端載入所有最近的電影資料
  4. 篩選出追蹤的電影
  5. 計算每部電影的預警狀態（正常/注意/嚴重）
  6. 統計「注意」和「嚴重」狀態的電影數量
  7. 🔄 **未來改進**：後端根據使用者 ID 從資料庫查詢追蹤清單和預警狀態

- **實作檔案**：
  - 服務層：`src/web/business/detail/services/stats_service.py`
    - `StatsService.get_warning_stats(tracked_movie_ids)` - 計算預警統計
    - `StatsService.get_all_stats(tracked_movie_ids)` - 取得所有統計
  - 預警判斷：`src/web/business/detail/services/boxoffice_list_service.py`
    - `BoxOfficeListService._calculate_warning_status()` - 計算預警狀態
  - API：`src/web/business/detail/blueprints/stats_api.py`
    - `POST /api/stats/all` - 取得所有統計資料
  - 前端：`src/web/business/detail/static/js/pages/index.js`
    - `loadAllStats()` - 載入統計資料並更新 UI

- **API 回應格式**：
```json
{
  "success": true,
  "data": {
    "warning_movies": {
      "total_count": 2,          // 預警電影總數（注意 + 嚴重）
      "attention_count": 1,      // 注意狀態的電影數量
      "critical_count": 1        // 嚴重狀態的電影數量
    }
  }
}
```

- **預警判斷標準**（簡化版）：
  - **第 1-3 週**：
    - 衰退率 < -50%：嚴重
    - 衰退率 < -30%：注意
    - 其他：正常
  - **第 4 週以後**：
    - 衰退率 < -40%：嚴重
    - 衰退率 < -25%：注意
    - 其他：正常

  完整預警邏輯請參考[衰退預警系統](#衰退預警系統)。

- **顯示邏輯**：
  - 主數值：顯示預警電影總數（`total_count`）
  - 副標題：
    - 有預警時：顯示「注意 X 部 / 嚴重 Y 部」（紅色）
    - 無預警時：顯示「無需關注」

---

### 票房預測結果

顯示電影票房預測的列表，支援篩選和追蹤功能。

#### 資料欄位定義

票房預測結果表格包含以下欄位：

| 欄位名稱 | 說明 | 資料來源 | 計算邏輯 |
|---------|------|---------|---------|
| **電影名稱** | 電影的中文名稱 | `boxoffice_permovie/full/{movie_id}_{name}.json` 的 `data.name` | 直接讀取 |
| **當前週次** | 電影當前所在的週次 | 計算得出 | `len(weeks_data) + 1`<br>例如：有 3 筆歷史資料（第 1、2、3 週已結束），當前週次為第 4 週 |
| **當週預測** | 預測當前週的票房（萬元） | 預測模型 | 使用所有歷史資料預測下一週<br>需要至少 2 週歷史資料<br>例如：有 3 週歷史，使用第 1、2、3 週預測第 4 週 |
| **上週預測** | 預測上一週的票房（萬元） | 預測模型 | 使用上一週之前的資料預測上一週<br>需要至少 2 週歷史資料<br>例如：有 3 週歷史，使用第 1、2 週預測第 3 週 |
| **上週實際** | 上一週的實際票房（萬元） | `weeks_data[-1].amount` | 最後一筆歷史資料的票房金額 |
| **上週衰退率** | 上一週相對於上上週的衰退率（%） | `weeks_data[-1].rate` | 直接讀取原始資料的 rate 欄位<br>公式：`(上週票房 - 上上週票房) / 上上週票房` |
| **預測差距%** | 上週預測與實際的差距百分比 | 計算得出 | `(上週實際 - 上週預測) / 上週預測 × 100%`<br>正數表示實際高於預測，負數表示實際低於預測 |
| **預警狀態** | 衰退預警等級 | 計算得出 | 根據上週衰退率和當前週次判斷<br>等級：正常 / 注意 / 嚴重<br>詳見[衰退預警系統](#衰退預警系統) |
| **追蹤** | 追蹤操作按鈕 | localStorage（臨時方案） | 加入追蹤 / 取消追蹤 |

#### 資料格式說明

- **票房金額**：
  - 後端 API 返回單位為「元」
  - 前端顯示時轉換為「萬元」：`金額(元) / 10000`
  - 例如：1,603,550 元 → 160.36 萬元

- **衰退率**：
  - 後端 API 返回小數格式（如 -0.3）
  - 前端顯示時轉換為百分比：`衰退率 × 100%`
  - 例如：-0.3 → -30%

- **預測差距**：
  - 後端 API 返回小數格式（如 0.1166）
  - 前端顯示時轉換為百分比：`差距 × 100%`
  - 例如：0.1166 → 11.66%

#### 資料邏輯說明

**當前週次的計算**：
- `weeks_data` 包含的是已結束週次的資料
- 當前週次 = 歷史資料筆數 + 1
- 例如：
  - 有 2 筆歷史資料（第 1、2 週已結束）→ 當前週次 = 3
  - 有 3 筆歷史資料（第 1、2、3 週已結束）→ 當前週次 = 4

**預測邏輯**：
- 預測模型需要至少 2 週的歷史資料才能進行預測
- **當週預測**：使用所有歷史資料（N 週）預測第 N+1 週
  - 例如：有 3 週歷史 → 預測第 4 週
- **上週預測**：使用前 N-1 週資料預測第 N 週
  - 例如：有 3 週歷史 → 使用第 1、2 週預測第 3 週
  - 例如：有 2 週歷史 → 使用第 1 週預測第 2 週（資料不足，返回 null）

**預測值為 null 的情況**：
- 歷史資料不足 2 週
- 歷史資料只有 2 週時，上週預測會是 null（因為只有 1 週資料無法預測）
- 預測模型執行失敗

#### 篩選功能

- **近期上映**：顯示最近 30 天內上映且狀態為「上映中」的電影
- **我的追蹤**：顯示使用者追蹤的電影

#### 追蹤功能

- **追蹤按鈕**：
  - 未追蹤：顯示「加入追蹤」按鈕
  - 已追蹤：顯示「取消追蹤」按鈕（高亮樣式）

- **追蹤操作**：
  - 點擊按鈕切換追蹤狀態
  - 顯示操作提示訊息（成功/取消）
  - 自動更新統計卡片的「追蹤中電影」數量
  - 若在「我的追蹤」篩選下，取消追蹤後自動重新篩選列表

- **實作方式**：
  - ⚠️ **臨時方案**：使用 localStorage 儲存追蹤清單
  - 🔄 **未來改進**：使用後端 API 儲存到資料庫

- **我的追蹤篩選邏輯**：
  - ⚠️ **臨時方案**：前端從 localStorage 取得追蹤清單，調用 API 取得所有電影，前端篩選出追蹤的電影
  - 🔄 **未來改進**：後端根據使用者 ID 從資料庫查詢追蹤的電影，直接返回結果

- **實作檔案**：
  - 服務層：`src/web/business/detail/services/boxoffice_list_service.py`
    - `BoxOfficeListService.get_boxoffice_list()` - 取得票房列表
    - `BoxOfficeListService._predict_boxoffice_for_week()` - 預測指定週次票房
    - `BoxOfficeListService._calculate_warning_status()` - 計算預警狀態
  - API：`src/web/business/detail/blueprints/boxoffice_list_api.py`
    - `GET /api/boxoffice/list` - 取得票房列表
  - 追蹤管理：`src/web/business/detail/static/js/common/tracking.js`
  - 列表顯示：`src/web/business/detail/static/js/pages/index.js`
    - `filterMovies(filterType)` - 篩選電影
    - `loadBoxOfficeList(filters)` - 載入票房列表
    - `handleTrackingToggle(button, govId)` - 處理追蹤切換

#### 分頁器功能

顯示在票房預測結果表格下方，支援多頁瀏覽和頁碼跳轉。

- **UI 結構**：
  - 上一頁按鈕：切換到前一頁
  - 頁碼按鈕區域：顯示可點擊的頁碼，當前頁高亮顯示
  - 下一頁按鈕：切換到下一頁

- **顯示邏輯**：
  - **智能頁碼顯示**：
    - 最多顯示 5 個頁碼按鈕
    - 當總頁數超過 5 頁時，使用省略符號（...）
    - 永遠顯示第 1 頁和最後一頁
    - 當前頁碼置中顯示（前後各顯示 2 頁）
  - **按鈕狀態**：
    - 第一頁時：「上一頁」按鈕禁用
    - 最後一頁時：「下一頁」按鈕禁用
    - 當前頁碼：高亮顯示（漸層背景 + 陰影效果）
  - **自動隱藏**：
    - 只有 1 頁或沒有資料時：隱藏整個分頁器
    - 載入失敗時：隱藏分頁器

- **互動邏輯**：
  - **點擊頁碼**：跳轉到指定頁面
  - **點擊上一頁/下一頁**：切換到相鄰頁面
  - **切換篩選條件**：自動重置為第 1 頁
  - **API 整合**：
    - 每次切換頁面重新呼叫 `/api/boxoffice/list?page=N&page_size=10`
    - 保留當前的篩選條件（日期、預警狀態等）

- **分頁參數**：
  - `page`：當前頁碼（預設 1）
  - `page_size`：每頁筆數（預設 10）
  - 從 API 回應的 `pagination` 物件取得總頁數

- **實作檔案**：
  - 模板：`src/web/business/detail/templates/index.html`
    - 分頁器 HTML 結構（card-footer 區塊）
  - 腳本：`src/web/business/detail/static/js/pages/index.js`
    - `initializePagination()` - 初始化分頁器事件
    - `renderPagination(current, total)` - 渲染分頁器按鈕
    - `createPageButton(pageNum, currentPageNum)` - 創建頁碼按鈕
  - 樣式：`src/web/business/detail/static/css/ui-kits.css`
    - `.pagination-container` - 分頁器容器
    - `.pagination-btn` - 上一頁/下一頁按鈕
    - `.pagination-page` - 頁碼按鈕
    - `.pagination-ellipsis` - 省略符號

- **範例**：
  ```
  總頁數 = 12，當前頁 = 6
  顯示：[1] [...] [4] [5] [6] [7] [8] [...] [12]

  總頁數 = 5，當前頁 = 3
  顯示：[1] [2] [3] [4] [5]

  總頁數 = 1
  隱藏分頁器
  ```

---

### 統一 API 端點

為了減少 API 請求次數，三個統計卡片共用一個 API 端點：

- **端點**：`POST /api/stats/all`
- **請求參數**：
  ```json
  {
    "tracked_movie_ids": ["32462", "32514", "31965"]
  }
  ```
- **回應格式**：
  ```json
  {
    "success": true,
    "data": {
      "recent_movies": {
        "recent_count": 97,
        "change_from_last_week": 8,
        "last_week_count": 89
      },
      "tracked_movies": {
        "count": 3
      },
      "warning_movies": {
        "total_count": 2,
        "attention_count": 1,
        "critical_count": 1
      }
    }
  }
  ```

詳細 API 規格請參考 [API 規格文件](spec_api.md#取得所有統計資料)。

---

## 單一電影頁

---

## 預測頁

---

## 共同功能

### 衰退預警系統

#### 概述
衰退預警系統用於判斷電影票房衰退是否異常，提供三級預警（正常/注意/嚴重）。系統基於歷史訓練資料的統計分析，將預測的衰退率與同量級電影的歷史平均進行比較。

#### 核心邏輯

##### 1. 電影量級分類
根據電影的**開片實力**（前兩周日均票房）分為 4 個量級：

- **tier_1**：< P25（小片）
- **tier_2**：P25 ~ P75（中片）
- **tier_3**：P75 ~ P90（中大片）
- **tier_4**：> P90（大片）

**開片實力計算公式**：
```python
opening_strength = (week_1_boxoffice / week_1_days + week_2_boxoffice) / 2
```

##### 2. 歷史平均衰退率
- 從訓練資料（`preprocessed_full.csv`）計算每個量級在每一週的平均衰退率
- 使用前兩周日均票房作為分組依據
- 統計資料儲存在快取檔案中，避免重複計算

##### 3. 預警分級標準

比較**預測衰退率**與**歷史平均衰退率**：

| 預警等級 | 判斷條件 | 衰退速度比較 |
|---------|---------|-------------|
| **正常** | 衰退速度比平均快 < 30% | 符合預期 |
| **注意** | 衰退速度比平均快 30% ~ 50% | 略快於預期 |
| **嚴重** | 衰退速度比平均快 > 50% | 明顯異常 |

**計算公式**：
```python
decline_speed_ratio = (predicted_decline_rate - avg_decline_rate) / abs(avg_decline_rate)

# 範例：預測 -60%，平均 -40%
# ratio = (-0.6 - (-0.4)) / 0.4 = -0.5 (衰退快 50%)
```

##### 4. 預警示例

**示例 1：中片正常衰退**
```
電影量級：tier_2（中片）
當前週次：第 4 週
預測衰退率：-60%
歷史平均：-59.6%
衰退速度：比平均快 0.7%
→ 預警等級：正常
```

**示例 2：大片異常衰退**
```
電影量級：tier_4（大片）
當前週次：第 3 週
預測衰退率：-80%
歷史平均：-40%
衰退速度：比平均快 100%
→ 預警等級：嚴重
```

#### 實作檔案

##### 後端服務

**1. 衰退率統計服務**
- **檔案**：`src/web/business/detail/services/decline_statistics.py`
- **類別**：`DeclineStatistics`
- **主要方法**：
  - `calculate_statistics()` - 計算並快取統計資料
  - `get_tier_for_strength(opening_strength)` - 判斷電影量級
  - `get_average_decline_rate(tier, week)` - 取得平均衰退率

**2. 衰退預警服務**
- **檔案**：`src/web/business/detail/services/decline_warning_service.py`
- **類別**：`DeclineWarningService`
- **主要方法**：
  - `check_decline_warning(opening_strength, current_week, predicted_decline_rate)` - 檢查單週預警
  - `batch_check_warnings(opening_strength, predictions)` - 批次檢查多週預測

**3. 預測服務整合**
- **檔案**：`src/web/business/detail/services/prediction_service.py`
- **修改方法**：
  - `check_decline_warning(gov_id)` - 已上映電影的預警檢查
  - `predict_new_movie(week_data, movie_info, predict_weeks)` - 新電影預測時加入預警

##### 前端顯示

**1. 電影詳細頁面**
- **檔案**：`src/web/business/detail/templates/movie_detail.html`
- **顯示位置**：
  - 頂部預警提示：根據預警等級顯示黃色（注意）或紅色（嚴重）警告框
  - 表格欄位「衰退預警」：顯示預警徽章（正常/注意/嚴重）

**2. 預測頁面**
- **檔案**：
  - 模板：`src/web/business/detail/templates/predict.html`
  - 腳本：`src/web/business/detail/static/js/pages/predict.js`
- **顯示位置**：
  - 預測結果表格的「衰退預警」欄位
  - 根據 `result.warnings` 數組動態顯示預警徽章

#### 資料結構

##### API 回應格式（check_decline_warning）

```json
{
  "level": "嚴重",                          // 預警等級：正常/注意/嚴重
  "has_warning": true,                      // 是否有預警（相容舊 API）
  "message": "預測衰退率 -80.0%，比歷史平均快 100%",
  "next_week_decline": -0.8,                // 預測衰退率
  "average_decline_rate": -0.4,             // 歷史平均衰退率
  "tier": "tier_4"                          // 電影量級
}
```

##### 新電影預測回應（predict_new_movie）

```json
{
  "success": true,
  "predictions": [
    {
      "week": 3,
      "boxoffice": 8500000,
      "decline_rate": -0.65
    }
  ],
  "warnings": [
    {
      "week": 3,
      "level": "注意",
      "message": "預測衰退率 -65.0%，比歷史平均快 35%"
    }
  ]
}
```

#### 快取機制

**快取檔案**：`src/web/business/detail/services/decline_statistics_cache.json`

**快取內容**：
- 分位數資訊（P25、P75、P90）
- 每個量級在每一週的平均衰退率統計
- 總電影數和總記錄數

**更新時機**：
- 首次執行時自動計算
- 訓練資料更新後需手動重新計算

**手動更新方法**：
```python
from services.decline_statistics import get_decline_statistics
stats = get_decline_statistics()
stats.calculate_statistics(force_recalculate=True)
```

或直接刪除快取檔案，系統會自動重新計算。

#### 統計資料來源

**訓練資料路徑**：
```
data/ML_boxoffice/phase4_models/M1/[最新版本]/prepared_data/preprocessed_full.csv
```

**使用欄位**：
- `gov_id` - 電影識別碼
- `current_week_active_idx` - 當前週次
- `open_week1_boxoffice_daily_avg` - 首週日均票房
- `open_week2_boxoffice` - 第二週票房
- `boxoffice_week_1` - 上週票房
- `amount` - 當週票房（用於計算衰退率）

#### 注意事項

1. **資料依賴**：系統依賴訓練資料的統計，確保訓練資料品質
2. **量級判斷**：開片實力的計算假設第 1 週有 7 天，實際應使用 `open_week1_days`
3. **邊界情況**：
   - 歷史資料不足 2 週：無法判斷預警
   - 當前週次超出歷史統計範圍：返回「無法判斷」
   - 歷史平均接近 0：衰退速度比率設為 0
4. **快取更新**：當訓練資料更新時記得重新計算統計快取