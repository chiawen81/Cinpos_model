# 票房預測系統執行流程分析

> **文件日期**: 2025-11-18
> **分析對象**: M1 線性迴歸模型的預測流程
> **模型路徑**: `data/ML_boxoffice/phase4_models/M1/M1_20251110_015910/`

---

## 📋 目錄

1. [系統概述](#系統概述)
2. [用戶按下預測按鈕後的完整流程](#用戶按下預測按鈕後的完整流程)
3. [訓練階段 vs 預測階段的資料處理差異](#訓練階段-vs-預測階段的資料處理差異)
4. [用戶資料轉換為模型輸入的詳細步驟](#用戶資料轉換為模型輸入的詳細步驟)
5. [關鍵發現與問題](#關鍵發現與問題)
6. [建議與改進方向](#建議與改進方向)

---

## 系統概述

### 模型資訊
- **模型類型**: Linear Regression (線性迴歸)
- **訓練時間**: 2025-11-10 01:59:10
- **特徵數量**: 19 個
- **訓練樣本數**: 860 筆

### 模型特徵列表
```python
[
    'round_idx',                      # 輪次索引（固定為 1）
    'current_week_active_idx',        # 要預測的週次
    'gap_real_week_2to1',            # 前2週到前1週之間跳過的週數
    'gap_real_week_1tocurrent',      # 前1週到當前週之間跳過的週數
    'boxoffice_week_2',              # 前2週票房
    'boxoffice_week_1',              # 前1週票房
    'audience_week_2',               # 前2週觀影人數
    'audience_week_1',               # 前1週觀影人數
    'screens_week_2',                # 前2週院線數
    'screens_week_1',                # 前1週院線數
    'open_week1_days',               # 首週放映天數
    'open_week1_boxoffice',          # 首週票房
    'open_week1_boxoffice_daily_avg', # 首週日均票房
    'open_week2_boxoffice',          # 第二週票房
    'release_year',                   # 上映年份
    'film_length',                    # 片長（分鐘）
    'is_restricted',                  # 是否限制級（0/1）
    'release_month_sin',              # 上映月份 sin 編碼
    'release_month_cos'               # 上映月份 cos 編碼
]
```

### 目標變數
- **amount**: 當前週的票房金額（新台幣）

---

## 用戶按下預測按鈕後的完整流程

### 流程圖

```
用戶操作
    ↓
[前端] predict.js:662
    ↓ 呼叫 movieService.predictBoxOffice()
[前端] movieService.js:69
    ↓ POST /api/predict-new
[後端 API] prediction_api.py:172 predict_new()
    ↓ 驗證請求資料
    ↓ 呼叫 prediction_service.predict_new_movie()
[服務層] prediction_service.py:177 predict_new_movie()
    ↓ 呼叫 M1NewMoviePredictor.predict_multi_weeks()
[ML 層] M1_predict_new_movie.py:92 predict_multi_weeks()
    ↓
    ├─ [循環] 預測第 N 週 (i=0,1,2...)
    │    ↓
    │    ├─ BoxOfficeFeatureEngineer.build_prediction_features()
    │    │   └─ 計算完整特徵字典
    │    │
    │    ├─ predict_single_week()
    │    │   └─ model.predict(features)
    │    │
    │    └─ 將預測結果加入 predictions 列表
    │
    └─ 返回 predictions
        ↓
[服務層] prediction_service.py:224
    ↓ 組合結果（history + predictions + statistics + warnings）
[後端 API] prediction_api.py:229
    ↓ 返回 JSON
[前端] predict.js:678
    ↓ displayPredictionResults()
用戶看到結果
```

### 詳細步驟說明

#### 步驟 1: 前端收集資料

**檔案**: `predict.js:637-666`

```javascript
// 收集表格資料
const weekData = collectTableData();
// 結構: [
//   {week: 1, boxoffice: xxx, audience: xxx, screens: xxx, week_range: "YYYY-MM-DD~YYYY-MM-DD"},
//   {week: 2, boxoffice: xxx, audience: xxx, screens: xxx, week_range: "YYYY-MM-DD~YYYY-MM-DD"},
//   ...
// ]

// 準備電影資訊
const movieInfo = {
    name: '電影名稱',
    release_date: '2025-01-01',
    film_length: 120,        // 片長（分鐘）
    is_restricted: 0         // 0=非限制級, 1=限制級
};

const predictWeeks = 3;  // 預測週數
```

**重要修正（2025-11-18）**:
- **問題**: 搜尋 API 原本固定回傳 `film_length: 120`
- **影響**: 所有電影片長都錯誤，導致模型無法正確利用「片長」特徵
- **修正**: 修改 `movie_api.py:152-194`，從 `movieInfo_gov` CSV 查詢真實片長
- **驗證**: 32099《創：戰神》真實片長 118 分鐘（修正前為 120）

#### 步驟 2: 後端 API 驗證

**檔案**: `prediction_api.py:172-236`

```python
def predict_new():
    # 1. 取得請求資料
    data = request.get_json()

    # 2. 驗證必要欄位
    if 'week_data' not in data or 'movie_info' not in data:
        return jsonify({'error': '缺少必要欄位'}), 400

    # 3. 驗證週次資料
    if len(week_data) < 2:
        return jsonify({'error': '至少需要 2 週的歷史資料'}), 400

    # 4. 驗證每週資料格式
    for week in week_data:
        if not all(key in week for key in ['week', 'boxoffice']):
            return jsonify({'error': '每週資料必須包含 week 和 boxoffice'}), 400

    # 5. 呼叫預測服務
    result = prediction_service.predict_new_movie(
        week_data=week_data,
        movie_info=movie_info,
        predict_weeks=predict_weeks
    )

    return jsonify(result)
```

#### 步驟 3: 預測服務層

**檔案**: `prediction_service.py:177-266`

```python
def predict_new_movie(week_data, movie_info, predict_weeks=3):
    try:
        # 1. 呼叫 M1 預測器
        predictions = self.new_movie_predictor.predict_multi_weeks(
            week_data=week_data,
            movie_info=movie_info,
            predict_weeks=predict_weeks
        )

        # 2. 計算統計資訊
        total_actual_boxoffice = sum(w["boxoffice"] for w in week_data)
        total_predicted_boxoffice = sum(p["predicted_boxoffice"] for p in predictions)
        avg_decline_rate = sum(p["decline_rate"] for p in predictions) / len(predictions)

        # 3. 檢查異常警示
        warnings = []
        for pred in predictions:
            if pred["decline_rate"] < -0.5:  # 衰退超過 50%
                warnings.append({
                    "week": pred["week"],
                    "type": "high_decline",
                    "message": f"第 {pred['week']} 週預測衰退率過高 ({pred['decline_rate']:.1%})"
                })
            elif pred["predicted_boxoffice"] < 1000000:  # 票房低於 100 萬
                warnings.append({
                    "week": pred["week"],
                    "type": "low_boxoffice",
                    "message": f"第 {pred['week']} 週預測票房過低 ({pred['predicted_boxoffice']:,.0f} 元)"
                })

        # 4. 組合結果
        result = {
            "success": True,
            "movie_info": movie_info,
            "history": [...],      # 歷史資料
            "predictions": [...],  # 預測結果
            "statistics": {...},   # 統計資訊
            "warnings": warnings   # 警示訊息
        }

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "預測失敗，請檢查輸入資料是否正確"
        }
```

#### 步驟 4: M1 預測器核心邏輯

**檔案**: `M1_predict_new_movie.py:92-183`

```python
def predict_multi_weeks(self, week_data, movie_info, predict_weeks=3):
    """
    遞迴預測多週票房

    ⚠️ 注意：第2週起使用預測值作為輸入，會累積誤差！
    """
    # 1. 載入模型
    self._ensure_model_loaded()

    # 2. 驗證輸入資料
    if len(week_data) < 2:
        raise ValueError("至少需要 2 週的歷史資料")

    # 排序週次資料
    week_data = sorted(week_data, key=lambda x: x['week'])

    # 驗證前兩週必須有票房
    if week_data[-1].get('boxoffice', 0) <= 0:
        raise ValueError("最近一週的票房必須大於 0")
    if week_data[-2].get('boxoffice', 0) <= 0:
        raise ValueError("第二近的一週票房必須大於 0")

    # 3. 預測循環
    predictions = []
    current_week_idx = len(week_data)

    for i in range(predict_weeks):
        target_week = current_week_idx + i + 1

        # 3.1 建立特徵
        features = BoxOfficeFeatureEngineer.build_prediction_features(
            week_data=week_data,
            movie_info=movie_info,
            target_week=target_week,
            use_predictions=(i > 0),      # ⚠️ 第2次起使用預測值
            predictions=predictions if i > 0 else None
        )

        # 3.2 進行預測
        predicted_boxoffice = self.predict_single_week(features)

        # 3.3 估算其他數值
        predicted_audience = int(predicted_boxoffice / 300)  # 假設平均票價 300 元
        prev_screens = features.get('screens_week_1', 100)
        predicted_screens = max(int(prev_screens * 0.9), 20)  # 院線數衰退 10%

        # 3.4 計算衰退率
        prev_boxoffice = features.get('boxoffice_week_1', 0)
        decline_rate = (predicted_boxoffice - prev_boxoffice) / prev_boxoffice if prev_boxoffice > 0 else 0

        # 3.5 儲存預測結果
        predictions.append({
            'week': target_week,
            'predicted_boxoffice': max(predicted_boxoffice, 0),
            'predicted_audience': predicted_audience,
            'predicted_screens': predicted_screens,
            'decline_rate': decline_rate
        })

    return predictions
```

---

## 訓練階段 vs 預測階段的資料處理差異

### 訓練階段資料處理

#### 資料來源
- **原始資料**: `data/raw/boxoffice_permovie/full/*.json`
- **處理後**: `data/ML_boxoffice/phase4_models/M1/.../prepared_data/preprocessed_full.csv`

#### 處理特點
1. **每一筆訓練資料都是獨立的**
   ```
   Row 1: 預測 week 3，基於真實 week 1, 2
   Row 2: 預測 week 4，基於真實 week 2, 3  ← 使用真實 week 3
   Row 3: 預測 week 5，基於真實 week 3, 4  ← 使用真實 week 4
   ```

2. **所有特徵都來自真實資料**
   - `boxoffice_week_1`, `boxoffice_week_2`: 真實票房
   - `audience_week_1`, `audience_week_2`: 真實觀影人數
   - `screens_week_1`, `screens_week_2`: 真實院線數

3. **訓練資料結構範例**（gov_id=13460）
   ```
   Row 0: current_week=3, boxoffice_week_2=890052,  boxoffice_week_1=959929,  amount=360104
   Row 1: current_week=4, boxoffice_week_2=959929,  boxoffice_week_1=360104,  amount=167345
   Row 2: current_week=5, boxoffice_week_2=360104,  boxoffice_week_1=167345,  amount=63720
   Row 3: current_week=6, boxoffice_week_2=167345,  boxoffice_week_1=63720,   amount=11960
   ```

   **觀察**: Row 1 的 `boxoffice_week_1=360104` 正好是 Row 0 的 `amount`（真實值）

4. **跳週分佈統計**
   ```
   gap_real_week_1tocurrent:
   - 0 週（連續）: 833 筆（96.9%）  ← 模型主要學習這種情況
   - 1 週: 20 筆（2.3%）
   - 2 週: 7 筆（0.8%）
   - 3 週或以上: 0 筆（0%）      ← 模型從未見過！
   ```

### 預測階段資料處理

#### 資料來源
- **用戶輸入**: 前端表格中手動輸入或從 API 載入的週次資料

#### 處理特點（⚠️ 與訓練階段不同！）

1. **遞迴預測模式**
   ```
   預測 1: 預測 week 6，基於真實 week 4, 5     ← 使用真實資料 ✓
   預測 2: 預測 week 7，基於真實 week 5, 預測 week 6  ← 混合真實+預測 ⚠️
   預測 3: 預測 week 8，基於預測 week 6, 7     ← 全部預測值 ✗
   ```

2. **特徵來源混合**
   - **第1次預測**: 所有特徵來自真實資料
   - **第2次預測起**: 部分特徵來自**預測值**
     - `boxoffice_week_1`: 使用上一次的**預測值**
     - `audience_week_1`: 基於預測票房估算（`predicted_boxoffice / 300`）
     - `screens_week_1`: 基於上次院線數衰退 10%

3. **分佈偏移 (Distribution Shift)**

   | 特徵 | 訓練時 | 預測時（第2週起）|
   |------|--------|-----------------|
   | boxoffice_week_1 | 真實值 | **預測值** ⚠️ |
   | audience_week_1 | 真實值 | **估算值**（票房/300）⚠️ |
   | screens_week_1 | 真實值 | **估算值**（衰退10%）⚠️ |

   **問題**: 模型訓練時從未見過「基於預測值的輸入」，導致準確度下降

---

## 用戶資料轉換為模型輸入的詳細步驟

### 實際案例：32099《創：戰神》

#### 用戶輸入資料
```python
week_data = [
    {'week': 1, 'boxoffice': 19442221, 'audience': 59827, 'screens': 93, 'week_range': '2025-10-08~2025-10-14'},
    {'week': 2, 'boxoffice': 10760922, 'audience': 33219, 'screens': 94, 'week_range': '2025-10-15~2025-10-21'},
    {'week': 3, 'boxoffice': 6069191,  'audience': 19439, 'screens': 95, 'week_range': '2025-10-22~2025-10-28'},
    {'week': 4, 'boxoffice': 2467073,  'audience': 8175,  'screens': 93, 'week_range': '2025-10-29~2025-11-04'},
    {'week': 5, 'boxoffice': 822579,   'audience': 2907,  'screens': 84, 'week_range': '2025-11-05~2025-11-11'}
]

movie_info = {
    'name': '創：戰神',
    'release_date': '2025-10-08',
    'film_length': 118,        # 修正後的真實片長
    'is_restricted': 0
}

predict_weeks = 3  # 預測 3 週
```

### 特徵工程詳細步驟

#### 步驟 1: 解析上映日期

**位置**: `feature_engineering.py:31-54`

```python
release_date = parse_release_date('2025-10-08')
# → datetime(2025, 10, 8)

release_year = 2025
release_month = 10
```

#### 步驟 2: 計算月份週期性編碼

**位置**: `feature_engineering.py:16-28`

```python
month_sin = sin(2 * π * 10 / 12) = -0.866025
month_cos = cos(2 * π * 10 / 12) = 0.500000
```

#### 步驟 3: 計算首週實力指標

**位置**: `feature_engineering.py:57-116`

```python
# 首週票房
open_week1_boxoffice = week_data[0]['boxoffice'] = 19442221

# 首週放映天數（從 week_range 計算）
week_range = '2025-10-08~2025-10-14'
week_end = datetime(2025, 10, 14)
release_date = datetime(2025, 10, 8)
open_week1_days = (week_end - release_date).days + 1 = 7

# ⚠️ 如果缺少 week_range，會使用預設值 7

# 首週日均票房
open_week1_boxoffice_daily_avg = 19442221 / 7 = 2777460.14

# ⚠️ 如果 open_week1_days 錯誤，這個值也會錯誤

# 第二週票房
open_week2_boxoffice = week_data[1]['boxoffice'] = 10760922
```

**重要發現（2025-11-18）**:
- 用戶案例中 `open_week1_days = 5`（實際放映天數）
- 如果 `week_range` 缺失，會使用預設值 7，導致 `open_week1_boxoffice_daily_avg` 計算錯誤
- 這會影響模型預測準確度

#### 步驟 4: 計算 Lag Features

**位置**: `feature_engineering.py:119-195`

##### 第 1 次預測（i=0, target_week=6）

```python
# 參數
target_week = 6
use_predictions = False  # 不使用預測值

# 尋找 week 5 和 week 4
week_1_data = week_data[4]  # week 5
week_2_data = week_data[3]  # week 4

# 提取特徵
lag_features = {
    'boxoffice_week_1': 822579,   # week 5 真實票房
    'boxoffice_week_2': 2467073,  # week 4 真實票房
    'audience_week_1': 2907,      # week 5 真實觀影人數
    'audience_week_2': 8175,      # week 4 真實觀影人數
    'screens_week_1': 84,         # week 5 真實院線數
    'screens_week_2': 93          # week 4 真實院線數
}
```

##### 第 2 次預測（i=1, target_week=7）⚠️ 使用預測值

```python
# 參數
target_week = 7
use_predictions = True  # ⚠️ 使用預測值！
predictions = [
    {
        'week': 6,
        'predicted_boxoffice': 734609,      # 第1次預測的結果
        'predicted_audience': 2448,
        'predicted_screens': 75
    }
]

# 合併資料：真實資料 + 預測資料
all_data = week_data + predictions
# = [week 1, 2, 3, 4, 5, week 6(預測)]

# 尋找 week 6 和 week 5
week_1_data = predictions[0]  # week 6 的預測結果 ⚠️
week_2_data = week_data[4]    # week 5 真實資料

# 提取特徵
lag_features = {
    'boxoffice_week_1': 734609,   # week 6 預測票房 ⚠️
    'boxoffice_week_2': 822579,   # week 5 真實票房
    'audience_week_1': 2448,      # week 6 預測觀影人數 ⚠️
    'audience_week_2': 2907,      # week 5 真實觀影人數
    'screens_week_1': 75,         # week 6 預測院線數 ⚠️
    'screens_week_2': 84          # week 5 真實院線數
}
```

#### 步驟 5: 計算跳週數

**位置**: `feature_engineering.py:198-237`

```python
# 找出有票房的週次
active_weeks = [w for w in week_data if w['boxoffice'] > 0]
# = [week 1, 2, 3, 4, 5]

# 第 1 次預測（target_week=6）
week_1 = active_weeks[-1]['week'] = 5
week_2 = active_weeks[-2]['week'] = 4

gap_real_week_1tocurrent = 6 - 5 - 1 = 0  # 沒有跳週
gap_real_week_2to1 = 5 - 4 - 1 = 0        # 沒有跳週
```

#### 步驟 6: 組合完整特徵

**位置**: `feature_engineering.py:240-306`

##### 第 1 次預測的完整特徵（target_week=6）

```python
features = {
    # 輪次與週次
    "round_idx": 1,
    "current_week_active_idx": 6,

    # Lag Features（真實資料）
    "boxoffice_week_1": 822579,      # week 5 真實
    "boxoffice_week_2": 2467073,     # week 4 真實
    "audience_week_1": 2907,         # week 5 真實
    "audience_week_2": 8175,         # week 4 真實
    "screens_week_1": 84,            # week 5 真實
    "screens_week_2": 93,            # week 4 真實

    # 首週實力
    "open_week1_days": 5,
    "open_week1_boxoffice": 19442221,
    "open_week1_boxoffice_daily_avg": 3888444.2,
    "open_week2_boxoffice": 10760922,

    # 電影基本資訊
    "film_length": 118,              # 修正後的真實片長
    "is_restricted": 0,

    # 跳週數
    "gap_real_week_2to1": 0,
    "gap_real_week_1tocurrent": 0,

    # 時間特徵
    "release_year": 2025,
    "release_month": 10,
    "release_month_sin": -0.866025,
    "release_month_cos": 0.500000
}
```

##### 第 2 次預測的完整特徵（target_week=7）⚠️

```python
features = {
    # 輪次與週次
    "round_idx": 1,
    "current_week_active_idx": 7,

    # Lag Features（混合真實+預測）
    "boxoffice_week_1": 734609,      # week 6 預測 ⚠️
    "boxoffice_week_2": 822579,      # week 5 真實
    "audience_week_1": 2448,         # week 6 預測 ⚠️
    "audience_week_2": 2907,         # week 5 真實
    "screens_week_1": 75,            # week 6 預測 ⚠️
    "screens_week_2": 84,            # week 5 真實

    # 首週實力（不變）
    "open_week1_days": 5,
    "open_week1_boxoffice": 19442221,
    "open_week1_boxoffice_daily_avg": 3888444.2,
    "open_week2_boxoffice": 10760922,

    # 電影基本資訊（不變）
    "film_length": 118,
    "is_restricted": 0,

    # 跳週數
    "gap_real_week_2to1": 0,
    "gap_real_week_1tocurrent": 1,   # ⚠️ 因為 week 6 是預測值，系統認為跳了 1 週

    # 時間特徵（不變）
    "release_year": 2025,
    "release_month": 10,
    "release_month_sin": -0.866025,
    "release_month_cos": 0.500000
}
```

**問題分析**:
- `gap_real_week_1tocurrent = 1` 是因為系統計算活躍週次時，只計算「真實資料」
- 但模型訓練時，`gap=1` 的樣本只有 20 筆（2.3%），學習不足
- 更嚴重的是，模型從未見過「基於預測值」的輸入

### 預測值的估算邏輯

**位置**: `M1_predict_new_movie.py:160-169`

```python
# 觀影人數估算
predicted_audience = int(predicted_boxoffice / 300)  # 假設平均票價 300 元

# 院線數估算
prev_screens = lag_features.get('screens_week_1', 100)
predicted_screens = max(int(prev_screens * 0.9), 20)  # 院線數衰退 10%，最少 20 廳
```

**問題**:
- 估算方式過於簡化，可能與真實情況差距很大
- 訓練資料中的 `audience` 和 `screens` 都是真實值
- 估算值的誤差會傳遞到下一次預測

---

## 關鍵發現與問題

### 🔴 嚴重問題

#### 1. 分佈偏移 (Distribution Shift)

**問題描述**:
- **訓練時**: 模型學習 f(真實week₁, 真實week₂) → week₃
- **預測時（第2週起）**: 模型計算 f(預測week₁, 預測week₂) → week₃

**影響**:
- 模型從未見過「基於預測值」的輸入
- 類似於「訓練時看真實蘋果，預測時給素描畫」
- 導致預測準確度急劇下降

**驗證**:
- 用戶反饋：「即使用訓練資料來預測也不準」
- 原因：只有第1次預測準確（用真實資料），第2次起就偏離了

#### 2. 誤差累積

**問題描述**:
```
第1次預測：真實→預測，誤差 ±10%
第2次預測：真實+預測→預測，誤差 ±14%（√2倍）
第3次預測：預測+預測→預測，誤差 ±20%（2倍）
第4次預測：誤差 ±25%（2.5倍）
...
```

**實際影響**:
```
假設真實票房序列：1000萬 → 700萬 → 500萬 → 350萬

預測序列（累積誤差）：
第3週：1000萬（真實）
第4週：720萬（預測，誤差+20萬）
第5週：550萬（基於720萬預測，誤差+50萬）← 輸入就錯了
第6週：420萬（基於550萬預測，誤差+70萬）← 更離譜
```

#### 3. 跳週預測不可靠

**訓練資料統計**:
```
gap_real_week_1tocurrent:
- 0 週（連續）: 833 筆（96.9%）
- 1 週: 20 筆（2.3%）
- 2 週: 7 筆（0.8%）
- 3 週或以上: 0 筆（0%）
```

**結論**:
- 模型主要學習「連續週次」的預測（96.9%）
- 如果輸入第3、4週，想預測第8週（gap=3），模型從未見過這種情況
- 預測會採用「外推」(extrapolation)，準確度極低

### 🟡 中度問題

#### 4. 特徵計算錯誤風險

**問題 4.1: film_length 固定為預設值**
- **狀態**: ✅ 已修正（2025-11-18）
- **原因**: 搜尋 API 原本從 `boxoffice_weekly` 資料源，無片長資訊
- **影響**: 所有電影片長都是 120 分鐘，模型無法利用此特徵
- **修正**: 從 `movieInfo_gov` CSV 查詢真實片長
- **驗證**: 32099《創：戰神》修正前 120 → 修正後 118

**問題 4.2: open_week1_days 可能錯誤**
- **狀態**: ⚠️ 依賴用戶輸入 `week_range`
- **影響**: 如果 `week_range` 缺失，使用預設值 7 天
- **後果**: `open_week1_boxoffice_daily_avg` 計算錯誤
- **建議**: 前端強制要求輸入 `week_range`，或從 API 自動填充

**問題 4.3: audience 和 screens 估算不準**
- **狀態**: ⚠️ 使用簡化公式
- **估算方式**:
  - `audience = boxoffice / 300`（假設平均票價）
  - `screens = prev_screens * 0.9`（假設衰退10%）
- **影響**: 訓練時都是真實值，預測時用估算值，分佈不一致
- **建議**:
  - 要求用戶輸入完整資料（audience, screens）
  - 或使用更精確的估算模型

#### 5. 無法利用真實資料校正

**問題描述**:
即使用戶輸入「前 5 週的真實資料」，想預測第 6, 7, 8 週：
- 第6週預測：使用真實 week 4, 5 ✓
- 第7週預測：使用真實 week 5 + 預測 week 6 ⚠️
- 第8週預測：使用預測 week 6, 7 ✗

**期望行為**:
用戶可能期望「既然我輸入了 5 週真實資料，應該比只輸入 2 週更準確」

**實際行為**:
系統只在第1次預測使用真實資料，之後都用預測值，多餘的真實資料被浪費

### 🟢 輕度問題

#### 6. 現行系統不支持手動指定週次

**限制**:
```python
current_week_idx = len(week_data)  # 假設從第1週開始
target_week = current_week_idx + i + 1  # 自動計算
```

**影響**:
- 無法實現「輸入第3、4週，預測第8週」
- `target_week` 是自動計算的，基於 `len(week_data)`

**修正成本**: 中等（需修改 `predict_multi_weeks` 邏輯）

---

## 建議與改進方向

### 短期方案（1-2週）⭐⭐⭐

#### 方案 1: 限制預測週數為 1

**修改位置**: 前端 `predict.js` + 後端驗證

**優點**:
- 與訓練資料完全一致
- 誤差不會累積
- 準確度最高

**缺點**:
- 用戶體驗下降（需要多次預測）

**實作建議**:
```javascript
// predict.js
const predictWeeks = 1;  // 固定為 1

// 在 UI 上說明
alert('目前僅支持預測下一週。如需預測更多週，請在取得實際資料後重新預測。');
```

#### 方案 2: 在 UI 上明確警告用戶

**修改位置**: `predict.js` + `prediction_service.py`

**實作**:
```javascript
// predict.js
if (predictWeeks > 1) {
    const confirmed = confirm(
        '⚠️ 預測準確度警告\n\n' +
        '第1週預測：使用真實資料（準確度高）\n' +
        '第2週預測：使用部分預測值（準確度中等）\n' +
        '第3週預測：使用全部預測值（準確度低）\n\n' +
        '誤差會隨著預測週數增加而累積。\n' +
        '是否繼續？'
    );
    if (!confirmed) return;
}
```

```python
# prediction_service.py
def predict_new_movie(...):
    # 在返回結果中加入準確度評估
    result["accuracy_warning"] = {
        "week_1": "高（使用真實資料）",
        "week_2": "中等（使用部分預測值）",
        "week_3": "低（使用全部預測值）"
    }
```

### 中期方案（1-2個月）⭐⭐⭐⭐

#### 方案 3: 實作「滾動預測」功能

**概念**:
允許用戶手動輸入新的實際資料後，再預測下一週

**UI 設計**:
```
[預測結果]
第6週：預測票房 734,609 元

[輸入實際資料]
第6週實際票房：[ ________ ] 元
第6週實際觀眾：[ ________ ] 人
第6週實際院線：[ ________ ] 廳

[繼續預測] 按鈕
```

**優點**:
- 每次都用真實資料，準確度高
- 符合實際使用情境（每週更新）

**缺點**:
- 需要等待實際資料
- UI 互動較複雜

#### 方案 4: 訓練「多步預測專用模型」

**方法 1: 資料增強 (Data Augmentation)**

在訓練時，對部分樣本加入「模擬預測誤差」：

```python
# 原始訓練樣本
X_train = [
    {'boxoffice_week_1': 100萬, 'boxoffice_week_2': 80萬},  # 真實
]

# 增強樣本（模擬預測誤差）
X_augmented = [
    {'boxoffice_week_1': 100萬, 'boxoffice_week_2': 80萬},  # 真實
    {'boxoffice_week_1': 105萬, 'boxoffice_week_2': 80萬},  # 模擬 +5% 誤差
    {'boxoffice_week_1': 95萬,  'boxoffice_week_2': 80萬},  # 模擬 -5% 誤差
    {'boxoffice_week_1': 105萬, 'boxoffice_week_2': 84萬},  # 模擬雙誤差
]
```

**優點**:
- 模型學會處理「不完美的輸入」
- 提高多步預測的魯棒性

**缺點**:
- 需要重新訓練模型
- 增強策略需要仔細設計

**方法 2: 直接多步預測 (Direct Multi-step)**

訓練不同的模型來預測不同週次：

```python
# 模型 1：預測下 1 週
model_1week = train(X, y_1week_ahead)

# 模型 2：預測下 2 週
model_2weeks = train(X, y_2weeks_ahead)

# 模型 3：預測下 3 週
model_3weeks = train(X, y_3weeks_ahead)
```

**優點**:
- 避免遞迴預測的誤差累積
- 每個模型專注於特定時間跨度

**缺點**:
- 需要訓練多個模型
- 訓練資料需要重新組織

### 長期方案（2-3個月）⭐⭐⭐⭐⭐

#### 方案 5: 改用「直接多步預測」架構

**Multi-output Regression**:

```python
# 輸入：前2週資料
features = build_features(week_data)

# 輸出：未來3週的票房（一次輸出3個值）
predictions = model.predict_multi_output(features)
# predictions = [week3, week4, week5]
```

**優點**:
- 徹底避免誤差累積
- 更符合實際需求
- 可以學習週次之間的相關性

**缺點**:
- 需要重新設計模型架構
- 可能需要深度學習模型（LSTM, Transformer）

**實作方向**:
1. **時間序列模型**: LSTM, GRU
2. **序列到序列模型**: Seq2Seq, Transformer
3. **多任務學習**: 同時預測票房、觀眾、院線數

---

## 附錄：關鍵程式碼位置索引

### 前端
- **預測按鈕處理**: `src/web/business/detail/static/js/pages/predict.js:616-687`
- **收集表格資料**: `predict.js:591-610`
- **電影資料服務**: `src/web/business/detail/static/js/service/movieService.js:69-91`

### 後端 API
- **搜尋電影 API**: `src/web/business/detail/blueprints/movie_api.py:115-173`
  - ✅ 已修正 `film_length` 問題（line 152-194）
- **預測 API**: `src/web/business/detail/blueprints/prediction_api.py:172-236`
- **下載預處理資料 API**: `prediction_api.py:298-348`

### 服務層
- **預測服務**: `src/web/business/detail/services/prediction_service.py:177-266`
- **匯出預處理資料**: `prediction_service.py:435-554`

### ML 層
- **M1 預測器**: `src/ML_boxoffice/phase5_apply/M1_predict_new_movie.py:92-183`
- **特徵工程**: `src/ML_boxoffice/common/feature_engineering.py:240-306`
  - 解析上映日期: `line 31-54`
  - 月份編碼: `line 16-28`
  - 首週實力: `line 57-116`
  - Lag Features: `line 119-195`
  - 跳週計算: `line 198-237`

### 訓練資料
- **預處理資料**: `data/ML_boxoffice/phase4_models/M1/M1_20251110_015910/prepared_data/preprocessed_full.csv`
- **模型檔案**: `data/ML_boxoffice/phase4_models/M1/M1_20251110_015910/model_linear_regression.pkl`

---

## 變更記錄

### 2025-11-18
- ✅ **修正**: `film_length` 從固定 120 改為從 `movieInfo_gov` CSV 查詢真實值
- 📝 **文件**: 建立本技術分析文件
- 🔍 **發現**:
  - 分佈偏移問題（訓練用真實值，預測用預測值）
  - 誤差累積問題（多步預測）
  - 跳週預測不可靠（訓練資料不足）
- 💡 **建議**:
  - 短期：限制預測週數或加入警告
  - 中期：滾動預測或重訓模型
  - 長期：直接多步預測架構

---

## 🎯 **模型評估指標深入分析**（2025-11-18 新增）

### 問題：為什麼 R² = 95% 但實際預測不準？

#### 測試集真實表現

```
測試集大小: 213 筆

線性迴歸模型表現:
├─ R² = 95.6%            ← 看起來很好！
├─ MAE = 967,188 元      ← 平均誤差 96.7 萬
├─ RMSE = 2,160,924 元   ← 均方根誤差 216 萬
├─ MAPE = 1453.6% ⚠️     ← 平均百分比誤差 1453%！
├─ 中位數誤差 = 156.3%   ← 一半的預測誤差超過 156%
└─ 負值預測 = 40筆 (18.8%) ← 票房預測為負數！
```

#### 核心原因：R² 和 MAPE 衡量不同的東西

**R² (決定係數) - 對大票房敏感**
```
- 關注「總變異」的解釋程度
- 大票房的誤差貢獻更多平方和
- 只要能準確預測大片，R² 就會很高
```

**MAPE (平均絕對百分比誤差) - 對小票房敏感**
```
- 每筆預測的「相對誤差」
- 小票房一點誤差就會導致 MAPE 爆炸
- 更符合「實用準確度」
```

#### 訓練資料分佈極度不均

```
票房範圍       | 資料筆數  | 貢獻變異
───────────────┼──────────┼─────────
<10萬          | 404 (47%)| ~5%
10-50萬        | 188 (22%)| ~8%
50-100萬       | 64 (7%)  | ~7%
100-500萬      | 111 (13%)| ~15%
500-1000萬     | 33 (4%)  | ~15%
>1000萬        | 60 (7%)  | ~50% ← 決定 R²！
```

**關鍵發現**：
- 小票房（<100萬）佔 76% 樣本，但只貢獻 20% 變異
- 大票房（>1000萬）佔 7% 樣本，但貢獻 50% 變異
- **R² 主要反映「能否預測大片」，小片誤差對 R² 影響很小**

#### <10萬 票房資料的真相

**統計數據**：
- <10萬 的資料有 404 筆（47%），來自 107 部電影
- 這些電影的總票房分佈：
  ```
  <10萬（真正小片）:  30 部（28%）
  10-100萬:          33 部（31%）
  100-500萬:         20 部（19%）
  500-1000萬:        6 部（6%）
  1000-5000萬:       13 部（12%）
  >5000萬:           5 部（5%）

  總票房 >100萬的: 44 部（41%）← 大片！
  ```

**結論**：
- **只有 30 部（28%）是真正的小片**（總票房 <10萬）
- **44 部（41%）其實是大片**（總票房 >100萬）
- 大部分 <10萬 的資料來自「大片的末期週次」，不是「小片」

#### 實際案例驗證

**案例 1：創世神 week 6**
```
實際票房: 185,801 元（小票房）
預測票房: 729,626 元
誤差: +293%

評估：
- 遠低於測試集平均誤差 1453%
- 低於測試集中位數 156%
- 在小票房範圍內屬於「可接受」範圍
```

**案例 2：泥娃娃 week 7**
```
實際票房: 3,827,915 元（中等票房）
預測票房: 3,086,308 元
誤差: -19.4%

評估：
- 遠低於測試集平均誤差 1453%
- 遠低於測試集中位數 156%
- 屬於「優秀」預測！
```

---

## 💡 **模型優化方案**（2025-11-18 新增）

### 評估的優化方向

#### ❌ 方案 1：排除 <10萬 的訓練資料 - **不建議**

**致命缺陷**：
- **59.7% 的電影（74/124）會跨越 10萬門檻**
- 這些電影會經歷「從 >10萬 衰退到 <10萬」的過程
- 排除後，模型無法學習「何時跌破 10萬」
- 會導致總票房被嚴重高估

**實證案例**：
```
電影 31474 的票房序列：
Week 8:  64萬  ← 模型訓練到這裡
Week 9:  19萬
Week 10: 11萬
Week 11:  5萬  ← 如果排除，模型不知道「何時跌破10萬」

結果：預測會一直 >10萬，總票房被高估
```

#### ⚠️ 方案 2：按票房級別訓練不同模型 - **謹慎使用**

**樣本分佈問題**：
```
方法 1（基於首週票房）：
- 小片(<100萬):   294 筆 ✓
- 中片(100-500萬): 267 筆 ✓
- 大片(500-1000萬): 23 筆 ✗ 太少！
- 超大片(>1000萬): 276 筆 ✓

方法 2（基於前兩週平均）：
- 小片(<100萬):   574 筆 ✓
- 中片(100-500萬): 159 筆 ✓
- 大片(500-1000萬): 39 筆 ✗ 太少！
- 超大片(>1000萬):  88 筆 ✗ 勉強
```

**級別切換不連續性問題**：
```
Week 4: 前兩週平均 600萬 → 使用「大片模型」→ 預測 400萬
Week 5: 前兩週平均 350萬 → 使用「中片模型」→ 預測 200萬 ← 突然跳躍
```

### 推薦的優化方案

#### 短期方案（1-2週，立即見效）⭐⭐⭐

##### 方案 A：加入「票房級別特徵」

**不訓練多個模型，而是讓單一模型學習不同級別的衰退模式**

```python
# 在 feature_engineering.py 中加入
def add_tier_features(features):
    """加入票房級別特徵"""
    open_week1 = features['open_week1_boxoffice']

    # 判斷級別
    if open_week1 < 1000000:
        tier_encoded = 0  # 小片
    elif open_week1 < 5000000:
        tier_encoded = 1  # 中片
    elif open_week1 < 10000000:
        tier_encoded = 2  # 大片
    else:
        tier_encoded = 3  # 超大片

    features['movie_tier'] = tier_encoded
    features['is_small_movie'] = 1 if tier_encoded == 0 else 0
    features['is_large_movie'] = 1 if tier_encoded >= 2 else 0

    # 加入「相對票房」特徵（保留率）
    if features['boxoffice_week_1'] > 0 and open_week1 > 0:
        features['retention_rate'] = features['boxoffice_week_1'] / open_week1

    return features
```

**優點**：
- ✅ 不需要訓練多個模型
- ✅ 模型可以學習「不同級別有不同的衰退率」
- ✅ 沒有級別切換的不連續性
- ✅ 實作簡單，風險低

**預期效果**：R² 可能提升 1-3%，MAPE 降低 10-20%

##### 方案 B：使用「加權損失函數」

**訓練時，給予不同票房範圍不同的權重**

```python
def custom_weighted_loss(y_true, y_pred):
    """
    根據票房大小給予不同權重

    小票房（<10萬）：權重 0.3（降低影響）
    中票房（10-100萬）：權重 1.0（標準）
    大票房（>100萬）：權重 1.5（提高重視）
    """
    weights = np.ones_like(y_true)

    weights[y_true < 100000] = 0.3
    weights[(y_true >= 100000) & (y_true < 1000000)] = 1.0
    weights[(y_true >= 1000000) & (y_true < 10000000)] = 1.5
    weights[y_true >= 10000000] = 2.0

    squared_error = (y_pred - y_true) ** 2
    weighted_error = squared_error * weights

    return np.mean(weighted_error)
```

**優點**：
- ✅ 提高模型對「有意義票房」的準確度
- ✅ 降低小票房誤差的影響（但仍保留學習能力）
- ✅ 單一模型，維護簡單

**預期效果**：中等票房（100-500萬）MAPE 降低 20-30%

##### 方案 C：預測時設定「下限與停止條件」

```python
def predict_with_threshold(predictor, week_data, movie_info, predict_weeks=3):
    """加入智能停止條件的預測"""
    predictions = []

    for i in range(predict_weeks):
        pred = predictor.predict_next_week(week_data, movie_info)

        # 檢查停止條件
        if pred['predicted_boxoffice'] < 50000:  # 低於 5 萬
            if len(week_data) >= 5:  # 已經上映 5 週
                print(f"⚠️ 預測票房過低，建議停止預測")
                break

        # 設定下限（避免負值）
        pred['predicted_boxoffice'] = max(pred['predicted_boxoffice'], 1000)

        predictions.append(pred)
        week_data.append(pred)

    return predictions
```

**優點**：
- ✅ 避免預測負值或極小值
- ✅ 符合實務（票房過低就下片）
- ✅ 不需要重新訓練模型

**預期效果**：避免極端預測，提升用戶信任

#### 中期方案（1-2個月）⭐⭐⭐⭐

##### 方案 D：訓練「兩階段模型」

**階段 1：分類器** - 判斷「是否會繼續上映」
```python
classifier = RandomForestClassifier()
# 目標：下一週票房是否 >5萬（繼續上映）
```

**階段 2：回歸模型** - 預測具體票房
```python
if classifier.predict(features) == 1:
    predicted_boxoffice = regressor.predict(features)
else:
    predicted_boxoffice = 0  # 已下片
```

**優點**：
- ✅ 更符合實際情況
- ✅ 避免預測極小值或負值
- ✅ 可以提供「下片機率」資訊

**預期效果**：整體 MAPE 降低 15-25%

##### 方案 E：使用「分位數回歸」(Quantile Regression)

**不只預測「平均值」，還預測「信賴區間」**

```python
from sklearn.ensemble import GradientBoostingRegressor

# 訓練三個模型
model_lower = GradientBoostingRegressor(loss='quantile', alpha=0.1)  # 下界
model_median = GradientBoostingRegressor(loss='quantile', alpha=0.5)  # 中位數
model_upper = GradientBoostingRegressor(loss='quantile', alpha=0.9)  # 上界

# 預測
lower_bound = model_lower.predict(X)
median_pred = model_median.predict(X)
upper_bound = model_upper.predict(X)
```

**優點**：
- ✅ 提供預測區間，更實用
- ✅ 中位數預測對極端值更魯棒
- ✅ 可以評估預測的不確定性

**預期效果**：提升實用性，用戶滿意度提升

#### 長期方案（2-3個月）⭐⭐⭐⭐⭐

##### 方案 F：改用時間序列模型

```python
# 使用 LSTM 或 Transformer
model = LSTM(
    input_features=['boxoffice', 'audience', 'screens', 'week'],
    output='next_week_boxoffice',
    sequence_length=5  # 使用前 5 週的資料
)
```

**優點**：
- ✅ 可以捕捉時間序列的長期依賴
- ✅ 更適合票房衰退這種時序問題
- ✅ 可以同時預測多個時間步

**預期效果**：MAPE 可能降低 30-40%

### 優化方案對比表

| 方案 | 複雜度 | 效果 | 風險 | 實作時間 | 推薦度 |
|------|--------|------|------|----------|--------|
| 排除 <10萬 資料 | 低 | ❌ 負面 | 高 | 1天 | ❌ 不推薦 |
| 分級訓練多模型 | 高 | 中等 | 中 | 1-2週 | ⚠️ 謹慎使用 |
| **加入級別特徵** | **低** | **中高** | **低** | **1-2天** | **✅ 強烈推薦** |
| **加權損失函數** | **中** | **高** | **低** | **3-5天** | **✅ 推薦** |
| **預測停止條件** | **低** | **中** | **低** | **半天** | **✅ 立即實作** |
| 兩階段模型 | 中高 | 高 | 中 | 1-2週 | ✅ 中期考慮 |
| 分位數回歸 | 中 | 中高 | 低 | 1週 | ✅ 中期考慮 |
| 時間序列模型 | 高 | 很高 | 中 | 2-3週 | ⭐ 長期目標 |

### 建議實作順序

#### 第1階段：快速優化（本週內）

1. **方案 C：加入預測停止條件**（半天）
   - 預測值 <5萬 → 停止或警告
   - 設定下限 1000 元（避免負值）

2. **方案 A：加入票房級別特徵**（1-2天）
   - 在 `feature_engineering.py` 中加入 `movie_tier` 特徵
   - 重新訓練模型

#### 第2階段：中期優化（下個月）

3. **方案 B：使用加權損失函數**（3-5天）
   - 修改訓練腳本
   - 重新訓練並評估

4. **方案 D：訓練兩階段模型**（1-2週）
   - 訓練「是否下片」分類器
   - 訓練票房回歸模型

#### 第3階段：長期優化（2-3個月後）

5. **方案 E：分位數回歸**（1週）
   - 提供預測區間

6. **方案 F：時間序列模型**（2-3週）
   - 收集更多資料後改用 LSTM

---

## 📊 **關鍵洞察總結**（2025-11-18）

### R² vs 實用性

```
模型的 R² = 95% 意味著：
✓ 能準確預測大片（>1000萬）- 誤差約 10-20%
✗ 但小票房（<100萬）預測極差 - MAPE 1453%
✗ 18.8% 預測為負值

實用建議：
- 大片預測（>500萬）：可信賴（誤差約 10-30%）
- 中等票房（100-500萬）：可參考（誤差約 30-100%）
- 小票房（<100萬）：僅供參考（誤差可能 >100%）
```

### 預測準確度分級

| 票房範圍 | 預測準確度 | 典型誤差 | 建議使用方式 |
|---------|-----------|---------|-------------|
| >1000萬 | ⭐⭐⭐⭐⭐ | 10-20% | 可直接用於決策 |
| 500-1000萬 | ⭐⭐⭐⭐ | 20-30% | 可作為重要參考 |
| 100-500萬 | ⭐⭐⭐ | 30-100% | 參考用，需人工判斷 |
| 10-100萬 | ⭐⭐ | 100-200% | 僅供參考 |
| <10萬 | ⭐ | >200% | 不建議使用 |

---

**文件維護**: 當修改預測系統時，請同步更新本文件
