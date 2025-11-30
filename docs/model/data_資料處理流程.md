# ML_boxoffice - 電影票房預測 Pipeline

## 📌 專案概述

### 目標
預測電影「當週票房」與「當週觀眾數」，協助電影發行商和戲院進行排片決策。

### 核心預測任務
```
輸入: 
- 前兩週的票房、人數、院線數
- 累積表現（截至上週）
- 開片實力（首輪數據）
- 市場資訊（年份、發行商、票價等）

輸出:
- 當週票房（amount）
- 當週觀眾數（tickets）
```

### 資料規模
- **電影數量**: 約 500 部
- **時間跨度**: 2020-2025 年
- **平均週數**: 每部電影 6 週資料
- **訓練樣本**: 約 1500-2000 筆（每部電影產生多筆樣本）

---

## 🔄 Pipeline 流程

### Phase 1: Flatten Timeseries（拉平時序）
**目標**: 將逐週票房資料拉平為時間序列格式，完成輪次定義與基礎特徵

**腳本**: `src/ML_boxoffice/phase1_flatten/flatten_timeseries.py`

**輸入**:
- `data/processed/boxoffice_permovie/*.csv` - 清洗後的逐週票房
- `data/processed/movieInfo_gov/combined/movieInfo_gov_full_*.csv` - 電影基本資訊

**輸出**:
- `data/ML_boxoffice/phase1_flattened/boxoffice_timeseries_YYYY-MM-DD.csv`

**處理內容**:
1. 過濾正式上映日之前的週次
2. 定義輪次（連續3週票房=0視為結束）
3. 計算真實週次 & 活躍週次
4. 建立 lag features（前1週、前2週）
5. 計算開片實力（首週票房等）

**詳細邏輯**: 見腳本內的註解

---

### Phase 2: Feature Engineering（特徵工程）
**目標**: 在拉平資料基礎上加入進階特徵

**腳本**:
- `src/ML_boxoffice/phase2_features/add_pr_features.py` - PR特徵
- `src/ML_boxoffice/phase2_features/add_cumulative_features.py` - 累積特徵
- `src/ML_boxoffice/phase2_features/add_market_features.py` - 市場特徵

**輸入**: `phase1_flattened/boxoffice_timeseries_*.csv`

**輸出**:
- `data/ML_boxoffice/phase2_features/with_pr/features_pr_*.csv` ← 原有欄位 + PR特徵
- `data/ML_boxoffice/phase2_features/with_cumulative/features_cumulative_*.csv` ← 原有欄位 + 累積特徵
- `data/ML_boxoffice/phase2_features/with_market/features_market_*.csv` ← 原有欄位 + 市場特徵
- `data/ML_boxoffice/phase2_features/full/features_full_*.csv` ← 整合所有特徵

**特徵類型**:
- **PR特徵**: Percentile Rank（按年份×輪次分組）
- **累積特徵**: 截至上週的累積票房、累積觀眾等
- **市場特徵**: 平均票價、季節性、競爭環境等

---

### Phase 3: Prepare Training Data（訓練準備）
**目標**: 組合最終訓練資料，針對不同模型選擇特徵

**腳本**: `src/ML_boxoffice/phase3_prepare/build_training_data.py`

**輸入**: `phase2_features/full/features_full_*.csv`

**輸出**:
- `data/ML_boxoffice/phase3_train_ready/M1_predict_boxoffice/training_M1_*.csv`
- `data/ML_boxoffice/phase3_train_ready/M2_predict_audience/training_M2_*.csv`

**處理內容**:
1. 選擇特徵（依配置檔）
2. 切分訓練/驗證/測試集（時間切分）
3. 處理缺失值
4. 輸出 feature_list.txt（記錄使用的特徵）

---

### Phase 4: Train Models（模型訓練）
**目標**: 訓練票房預測模型

**腳本**:
- `src/ML_boxoffice/phase4_models/train_boxoffice_model.py` - 票房預測
- `src/ML_boxoffice/phase4_models/train_audience_model.py` - 觀眾數預測

**輸入**: `phase3_train_ready/M*/training_M*_*.csv`

**輸出**:
- `data/ML_boxoffice/phase4_model/M1_predict_boxoffice/model_*.pkl`
- `data/ML_boxoffice/phase4_model/M1_predict_boxoffice/predictions_*.csv`
- `data/ML_boxoffice/phase4_model/M1_predict_boxoffice/evaluation_*.json`

**模型配置**:
- **M1_predict_boxoffice**: 預測目標=票房（amount）
- **M2_predict_audience**: 預測目標=觀眾數（tickets）

---

## 🎯 建模策略

### Baseline 模型
- **演算法**: XGBoost / LightGBM
- **特徵**: 全部特徵（base + pr + cumulative + market）
- **評估**: 時間切分（2020-2023 訓練，2024 驗證，2025 測試）

### 優化方向
1. **特徵工程**: 交互特徵、衰減速度
2. **分輪次建模**: 首輪 vs 次輪分別建模
3. **超參數調整**: Optuna / GridSearch

### 部署策略
1. **滾動預測**: 用預測值預測更遠的週次
2. **監控**: 追蹤預測誤差
3. **更新**: 定期納入新資料重訓練

---

## 📊 成功標準

### 預測準確度
- 首輪 MAPE < 25%
- 次輪 MAPE < 35%
- 整體 RMSE < 350 萬

### 業務價值
- 協助排片決策
- 提前識別黑馬/爆雷片
- 優化宣傳資源配置

---

## 🔗 相關文件

- [欄位定義](data_資料欄位定義.md) - 所有特徵欄位的詳細說明
- [資料處理規則](data_資料處理規則.md) - 輪次定義、週次編號等規則
- [特徵配置](ml_特徵配置.yaml) - 機器可讀的特徵定義
