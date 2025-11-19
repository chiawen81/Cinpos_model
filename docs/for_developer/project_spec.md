## 首頁

### 統計卡片

#### 近一個月上映電影
- **資料來源**：`data/raw/boxoffice_weekly`
- **API 端點**：`/api/stats/recent-movies`
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
    - `loadRecentMoviesStats()` - 載入並顯示統計資料

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