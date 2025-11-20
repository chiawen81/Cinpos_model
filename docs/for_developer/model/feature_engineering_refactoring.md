# 特徵工程模組化重構總結

**重構日期**: 2025-11-13
**目的**: 將特徵工程邏輯模組化，避免程式碼重複，提升維護性

---

## 📋 重構動機

### 問題描述

原本特徵工程邏輯分散在多個檔案中：

1. `flatten_timeseries.py` - 批量處理訓練資料時的特徵計算
2. `M1_predict_boxoffice.py` - 訓練時的月份編碼
3. `M2_predict_boxoffice.py` - 訓練時的月份編碼
4. `M3_predict_boxoffice.py` - 訓練時的月份編碼
5. `M1_predict_new_movie.py` - 預測時的特徵計算

**維護問題**：
- 相同邏輯在多處重複實作
- 修改特徵工程邏輯需要同步更新多個檔案
- 容易造成訓練和預測階段的特徵計算不一致

---

## 🎯 解決方案

### 建立共用特徵工程模組

**檔案位置**: `src/ML_boxoffice/common/feature_engineering.py`

**核心類別**: `BoxOfficeFeatureEngineer`

#### 提供的功能

1. **時間特徵編碼**
   - `encode_month_cyclical(month)` - 月份的 sin/cos 週期性編碼
   - `parse_release_date(release_date)` - 日期解析（支援多種格式）

2. **開片實力計算**
   - `calculate_opening_strength(week_data, release_date)` - 計算首週相關指標
     - `open_week1_boxoffice` - 首週票房
     - `open_week1_days` - 首週放映天數
     - `open_week1_boxoffice_daily_avg` - 首週日均票房
     - `open_week2_boxoffice` - 第二週票房

3. **Lag Features 計算**
   - `calculate_lag_features(week_data, target_week, ...)` - 計算前1週、前2週的數據
     - `boxoffice_week_1`, `boxoffice_week_2` - 前1週、前2週票房
     - `audience_week_1`, `audience_week_2` - 前1週、前2週觀影人數
     - `screens_week_1`, `screens_week_2` - 前1週、前2週院線數

4. **跳週數計算**
   - `calculate_gap_features(week_data, target_week)` - 計算活躍週次間的跳週數
     - `gap_real_week_2to1` - 前2週到前1週之間跳過的週數
     - `gap_real_week_1tocurrent` - 前1週到當前週之間跳過的週數

5. **完整特徵建立**
   - `build_prediction_features(week_data, movie_info, target_week, ...)` - 一次性建立所有預測特徵
   - `add_features_to_dataframe(df, group_by_col)` - 為訓練 DataFrame 批量添加特徵

---

## 📝 重構內容

### 已更新的檔案

| 檔案 | 變更內容 | 狀態 |
|------|---------|------|
| `src/ML_boxoffice/common/feature_engineering.py` | 新建共用模組 | ✅ 完成 |
| `src/ML_boxoffice/phase5_apply/M1_predict_new_movie.py` | 使用共用模組取代自訂邏輯 | ✅ 完成 |
| `src/ML_boxoffice/phase4_models/M1_predict_boxoffice.py` | 使用共用模組進行月份編碼 | ✅ 完成 |
| `src/ML_boxoffice/phase4_models/M2_predict_boxoffice.py` | 使用共用模組進行月份編碼 | ✅ 完成 |
| `src/ML_boxoffice/phase4_models/M3_predict_boxoffice.py` | 使用共用模組進行月份編碼 | ✅ 完成 |

### 程式碼範例

#### 重構前（M1_predict_new_movie.py）
```python
# 計算 sin/cos 特徵
if "release_month" in movie_data:
    movie_data["release_month_sin"] = np.sin(2 * np.pi * movie_data["release_month"] / 12)
    movie_data["release_month_cos"] = np.cos(2 * np.pi * movie_data["release_month"] / 12)

# 解析上映日期
release_date = self._parse_release_date(movie_info.get('release_date'))
release_year = release_date.year
release_month = release_date.month

# 計算首週相關資料（30+ 行程式碼）
...
```

#### 重構後（M1_predict_new_movie.py）
```python
from common.feature_engineering import BoxOfficeFeatureEngineer

# 使用共用模組建立完整特徵
features = BoxOfficeFeatureEngineer.build_prediction_features(
    week_data=week_data,
    movie_info=movie_info,
    target_week=target_week,
    use_predictions=(i > 0),
    predictions=predictions if i > 0 else None
)
```

---

## ✅ 測試驗證

### 測試檔案

1. **`test_feature_engineering.py`** - 測試共用模組的各項功能
   - ✅ 月份週期性編碼
   - ✅ 日期解析
   - ✅ 首週實力計算
   - ✅ Lag Features 計算
   - ✅ 完整特徵建立

2. **`test_prediction_integration.py`** - 測試預測功能整合
   - ✅ 預測器初始化
   - ✅ 多週預測功能
   - ✅ 預測結果合理性

### 測試結果

```
============================================================
[SUCCESS] All tests passed!
============================================================
[3/3] Prediction Results:
  --------------------------------------------------------
  Week         Boxoffice     Audience  Screens    Decline
  --------------------------------------------------------
  4            7,256,915       24,189      126    -23.6%
  5            5,451,198       18,170      113    -24.9%
  6            4,286,873       14,289      101    -21.4%
  --------------------------------------------------------
```

---

## 🎯 重構效益

### 1. **維護性提升**
- 特徵工程邏輯集中在單一模組
- 修改時只需更新一個檔案
- 減少程式碼重複（DRY 原則）

### 2. **一致性保證**
- 訓練和預測階段使用相同的特徵計算邏輯
- 避免因不同實作造成的特徵不一致問題
- 降低模型預測錯誤的風險

### 3. **可擴展性**
- 新增特徵時只需在共用模組中實作
- 所有使用者自動獲得新功能
- 易於支援更多模型（M2, M3, ...）

### 4. **可測試性**
- 特徵工程邏輯可獨立測試
- 易於驗證正確性
- 提升程式碼品質

---

## 📚 使用指南

### 在預測階段使用

```python
from common.feature_engineering import BoxOfficeFeatureEngineer

# 建立完整特徵
features = BoxOfficeFeatureEngineer.build_prediction_features(
    week_data=[
        {'week': 1, 'boxoffice': 12000000, 'audience': 40000, 'screens': 150},
        {'week': 2, 'boxoffice': 10200000, 'audience': 34000, 'screens': 140},
    ],
    movie_info={
        'name': '電影名稱',
        'release_date': '2024-11-08',
        'film_length': 120,
        'is_restricted': 0,
    },
    target_week=3
)
```

### 在訓練階段使用

```python
from common.feature_engineering import BoxOfficeFeatureEngineer

# 為 DataFrame 添加特徵
df = BoxOfficeFeatureEngineer.add_features_to_dataframe(df, group_by_col='gov_id')
```

---

## ⚠️ 注意事項

### 向後相容

為了保持向後相容，模組提供了獨立函數介面：

```python
# 類別方法（推薦）
BoxOfficeFeatureEngineer.encode_month_cyclical(month)

# 獨立函數（向後相容）
from common.feature_engineering import encode_month_cyclical
encode_month_cyclical(month)
```

### 未來開發建議

1. **新增特徵時**：
   - 在 `BoxOfficeFeatureEngineer` 類別中新增方法
   - 更新 `build_prediction_features()` 包含新特徵
   - 為新特徵撰寫單元測試

2. **修改現有特徵時**：
   - 只需修改共用模組
   - 執行測試腳本確認變更不會破壞功能
   - 考慮是否需要重新訓練模型

3. **支援新模型時**：
   - 直接使用現有的特徵工程方法
   - 必要時擴展共用模組而非重新實作

---

## 📊 程式碼統計

### 程式碼減少量

| 檔案 | 重構前 | 重構後 | 減少 |
|------|--------|--------|------|
| M1_predict_new_movie.py | 235 行 | 152 行 | -83 行 |
| M1_predict_boxoffice.py | 395 行 | 393 行 | -2 行 |
| M2_predict_boxoffice.py | 395 行 | 393 行 | -2 行 |
| M3_predict_boxoffice.py | 395 行 | 393 行 | -2 行 |
| **新增** feature_engineering.py | 0 行 | 434 行 | +434 行 |
| **總計** | 1,420 行 | 1,765 行 | +345 行 |

> 註：雖然總行數增加，但移除了約 89 行重複程式碼，並增加了完整的文件說明和錯誤處理。

---

## 🔄 未來改進方向

1. **擴展特徵工程功能**
   - 支援更多時間特徵（季節、假日等）
   - 支援類別特徵編碼（出版商、地區等）
   - 支援特徵標準化與正規化

2. **增強測試覆蓋率**
   - 為每個特徵計算方法撰寫單元測試
   - 增加邊界條件測試
   - 增加特徵一致性驗證測試

3. **效能優化**
   - 對批量處理進行向量化優化
   - 加入快取機制減少重複計算
   - 支援多執行緒處理

---

**重構完成日期**: 2025-11-13
**測試狀態**: ✅ 全部通過
**文件狀態**: ✅ 已完成
