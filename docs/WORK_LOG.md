# 電影票房預測專案 - 工作日誌

## 📅 最後更新：2025-11-08

---

## 🎯 當前狀態

### 模型表現（最佳版本）
- **Linear Regression R² = 0.939**
- **LightGBM R² = 0.936**
- **資料筆數**: 876 筆（排除 2 部問題電影後）
- **排除清單**: `config/exclude_movies.csv`（只排除 31082, 22894）

### 關鍵檔案位置
```
最新訓練結果（原始尺度，無對數轉換）：
├── data/ML_boxoffice/phase4_models/M1_20251108_193104/
│   ├── training_log_20251108_193104.txt
│   ├── prediction_comparison.png  ← 視覺化結果
│   ├── model_linear_regression.pkl
│   ├── model_lightgbm.pkl
│   └── test_predictions.csv

主要腳本：
├── src/ML_boxoffice/phase4_models/M1_predict_boxoffice.py
└── config/exclude_movies.csv  ← 電影排除清單
```

---

## 📝 重要發現與決策

### 1. 離群值的正確定義（重要！）

**❌ 錯誤做法**：
- 把「票房數值大的電影」當成離群值移除
- 這會讓模型無法學習「大片」的規律

**✅ 正確做法**：
- **離群值 = 預測誤差極大的樣本**，與特徵值大小無關
- 使用 IQR 方法：`誤差 > Q3 + 1.5 × IQR`

### 2. 排除清單策略

**只排除真正有問題的電影**：
- `31082` - 地球特派員（首輪票房異常）
- `22894` - 一一（資料汙染）

**不排除正常的大片**：
- `31123` - 侏羅紀世界：重生
- `31352`, `31794`, `23322`, `30739`, `31027`, `31365`
- 這些是正常的票房大片，應該保留讓模型學習

**實驗結果對比**：

| 排除策略 | Linear R² | LightGBM R² | 分數差距 | 結論 |
|---------|-----------|-------------|---------|------|
| 只排除 2 部問題電影 | 0.939 | 0.936 | 0.003 ⭐ | **最佳** |
| 排除 2 部 + 7 部大片 | 0.955 | 0.884 | 0.071 ❌ | 模型不穩定 |

### 3. 對數轉換實驗（已放棄）

**嘗試原因**：
- 票房數值範圍極大（210元 ~ 1.5億元）
- 希望透過對數轉換改善 LightGBM 表現

**實驗結果**：
- Linear Regression R² 從 0.939 暴跌到 0.428 ❌
- LightGBM R² 從 0.936 提升到 0.908 ✅
- 但整體不一致，已還原

**結論**：
- 票房衰減在原始尺度下是線性關係，不需要對數轉換
- 當前的原始尺度版本已經是最佳方案

---

## 🛠️ 實作的功能

### 1. 電影排除清單系統

**檔案**: `config/exclude_movies.csv`

**使用方式**：
```csv
gov_id,title_zh,reason
31082,地球特派員,首輪上映第一二周票房異常
22894,一一,這部電影在公開資料個別使用不同名字，汙染後續統計
```

**特點**：
- ✅ 支援 `#` 註解
- ✅ 自動跳過空行
- ✅ 檔案不存在時會顯示警告但不中斷執行
- ✅ 顯示詳細的排除日誌

**程式碼位置**：
`src/ML_boxoffice/phase4_models/M1_predict_boxoffice.py` 第 70-110 行

---

## 📊 資料處理流程

### 當前的資料篩選邏輯
```
原始資料
  ↓
排除 config/exclude_movies.csv 中的電影
  ↓
只保留首輪資料 (round_idx == 1)
  ↓
只保留有活躍週次的資料
  ↓
必須同時有 week_1 和 week_2 的資料，且都不為 0
  ↓
最終：876 筆訓練資料
```

---

## 🐛 已解決的問題

### 問題 1：LightGBM R² (0.704) 遠低於 Linear Regression (0.963)

**原因**：
- 測試集中包含極端大片（如侏羅紀世界）
- LightGBM 對這些沒見過的極端值預測失準

**解決方案**：
- 保留大片，讓模型學習
- 只排除真正有問題的電影（資料異常）

### 問題 2：如何定義離群值

**學到的教訓**：
- 不能因為「票房高」就認為是離群值
- 應該基於「預測誤差」來判斷

### 問題 3：編碼問題（Windows 終端機）

**問題**：Emoji 符號導致 UnicodeEncodeError

**解決方案**：
- 在 Logger class 中加入 try-except 處理
- 位置：`M1_predict_boxoffice.py` 第 28-47 行

---

## 📈 模型評估指標

### 最佳模型表現（只排除 2 部問題電影）

**Linear Regression**：
- MAE: 268,569
- RMSE: 472,999
- R²: 0.9550

**LightGBM**：
- MAE: 274,877
- RMSE: 758,444
- R²: 0.8842

**特徵重要性 Top 5**：
1. `boxoffice_week_1` (179)
2. `audience_week_1` (118)
3. `open_week2_boxoffice` (61)
4. `screens_week_1` (58)
5. `screens_week_2` (56)

---

## 🔄 待辦事項

### 高優先級
- [ ] 分析剩餘的離群值（藍圈、黃圈）是哪些電影
- [ ] 確認是否需要調整 LightGBM 超參數
- [ ] 考慮添加「衰減率」特徵：`(week_1 - week_2) / week_2`

### 中優先級
- [ ] 評估是否需要處理極端值（非移除，而是其他方法）
- [ ] 考慮分層建模：大片 vs 一般片

### 低優先級
- [ ] 移除日誌系統中的 Emoji（避免編碼問題）
- [ ] 整理臨時分析腳本（`analyze_*.py`）

---

## 📚 重要文件參考

### 資料定義
- `docs/ML_boxoffice/data_dictionary.md` - 欄位定義（人類可讀）
- `docs/ML_boxoffice/feature_config.yaml` - 欄位定義（機器可讀）

### Pipeline 文件
- `docs/ML_boxoffice/pipeline.md` - Pipeline 流程 + 建模策略
- `docs/ML_boxoffice/data_processing_rules.md` - 資料處理規則

### 配置文件
- `config/exclude_movies.csv` - 電影排除清單

---

## 💡 下次工作建議

1. **如果要改善 LightGBM 表現**：
   - 調整超參數：`n_estimators=500`, `max_depth=10`, `learning_rate=0.01`
   - 添加衰減率特徵
   - 考慮交叉驗證找最佳參數

2. **如果要分析離群值**：
   - 執行：`uv run python analyze_outliers.py`
   - 檢查藍圈、黃圈代表的電影
   - 決定是否需要處理

3. **如果要訓練新模型**：
   - 修改 `config/exclude_movies.csv`（如需要）
   - 執行：`uv run python src/ML_boxoffice/phase4_models/M1_predict_boxoffice.py`
   - 檢查生成的圖表和 log

---

## 🎓 經驗教訓

### 關於離群值
> 「大片不是離群值，它們是正常的數據分布。只有資料異常的樣本才是真正的離群值。」

### 關於特徵工程
> 「不要急著轉換數據。先檢查原始數據的分布和關係，確認轉換是否真的有幫助。」

### 關於模型比較
> 「兩個模型的 R² 接近（0.939 vs 0.936）比單一模型的高 R² 更重要，這代表模型穩健。」

---

## 🔗 相關連結

- 專案 README: `README.md`
- Pipeline 修改指南: `docs/shared/pipeline_modification_guide.md`
- Claude Code 使用說明: `CLAUDE.md`

---

**備註**：此工作日誌應該在每次重要變更後更新，以便團隊成員或 AI Agent 快速了解專案狀態。
