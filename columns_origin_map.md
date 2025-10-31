# 🎬 Columns Origin Map  
> 對照各欄位的 **功能說明**、**資料來源** 與 **產出方式**

---

## 🧩 一、票房預測報表（`boxoffice_forecast_*.csv`）

| 欄位名稱 | 說明 | 欄位資料來源 |
|-----------|------|----------------|
| `gov_id`, `title_zh` | 電影識別資訊 | 📙 聚合資料 `gov_id`, `title_zh` |
| `release_round` | 上映輪次 | 📙 聚合資料 `release_round` |
| `week_range` | 當前週期 | 📗 原始資料 `week_range` |
| `amount` | 上週實際票房 | 📗 原始資料 `amount` |
| `expected_amount_per_week` | 應收票房（統計預期） | 📙 聚合 `avg_amount_per_week` + 📘 電影資訊 (`region`, `rating`) 分群統計 |
| `performance_gap` | (實收 – 應收) / 應收 | 🧮 推算（by 統計） |
| `forecast_week1_amount` ~ `forecast_week3_amount` | 預測接下來三週票房 | ⚙️ 模型預測（以聚合＋電影資訊特徵訓練） |
| `forecast_week1_decline` ~ `forecast_week3_decline` | 對應衰退率預測 | ⚙️ 模型預測（by 票房預測模型） |
| `forecast_ci_lower`, `forecast_ci_upper` | 預測信心區間 | ⚙️ 模型（Prophet 類型模型自帶） |
| `forecast_week1_tickets` ~ `forecast_week3_tickets` | 預測觀影人數 | 🧮 推算（by 預測票房 ÷ 平均票價） |
| `momentum_3w` | 三週票房動能平均 | 📗 原始資料 `amount` → 移動平均 |
| `momentum_status` | 動能狀態（上升／下滑） | 🧮 推算（by momentum_3w vs 同類平均） |
| `update_at` | 報表生成時間 | 系統生成 timestamp |

---

## 📣 二、宣傳與場次建議報表（`promotion_alerts_*.csv`）

| 欄位名稱 | 說明 | 欄位資料來源 |
|-----------|------|----------------|
| `gov_id`, `title_zh` | 電影識別 | 📙 聚合資料 |
| `amount`, `expected_amount_per_week`, `performance_gap` | 當週表現基礎 | 📗 原始資料 + 📙 聚合 + 🧮 推算 |
| `decline_gap`, `momentum_gap` | 偵測異常衰退或動能不足 | 📗 原始 `rate` + 📙 聚合 `decline_rate_mean` + 🧮 統計比較 |
| `promotion_urgency_score` | 綜合指數（>0.8 代表需加宣傳） | 🧮 推算（by performance_gap、decline_gap、momentum_gap 加權） |
| `promotion_suggestion` | 文本建議（加強宣傳／表現穩定） | 🧮 推算（rule-based 規則） |
| `forecast_week1_amount`, `forecast_week1_decline` | 預測短期走勢 | ⚙️ 模型預測（票房預測模型） |
| `avg_amount_per_theater` | 平均每廳票房 | 📙 聚合 (`total_amount`, `avg_theater_count`) 統計計算 |
| `recommended_screen_count_week1` | 建議下週場次 | 🧮 推算（by 預測票房 ÷ 平均每廳票房） |
| `recommended_screen_delta` | 與目前院數差距 | 🧮 推算（by recommended_screen_count – 現行院數） |
| `update_at` | 報表生成時間 | 系統生成 timestamp |

---

## 🔁 三、再上映潛力報表（`re_release_suggestion_*.csv`）

| 欄位名稱 | 說明 | 欄位資料來源 |
|-----------|------|----------------|
| `gov_id`, `title_zh` | 電影識別 | 📙 聚合資料 |
| `release_round`, `total_amount`, `decline_rate_mean`, `is_long_tail` | 本輪票房表現基礎 | 📙 聚合資料 |
| `re_release_gap_weeks` | 上輪至本輪間隔週數 | 🧮 推算（by 聚合 `release_end`, `release_start`） |
| `long_tail_strength` | 長尾強度指標 | 🧮 推算（by 聚合 `decline_rate_mean`, `active_weeks`, `total_weeks`） |
| `expected_re_release_amount` | 模型預測再上映票房 | ⚙️ 模型預測（以聚合 + 電影資訊 特徵訓練） |
| `expected_re_release_tickets` | 模型預測再上映觀影人數 | ⚙️ 模型輸出（同上或票價推算） |
| `re_release_roi_pred` | 預估再映投報率 | 🧮 推算（by expected_re_release_amount ÷ previous_total_amount） |
| `re_release_suggestion` | 文本建議（建議再映／不建議） | 🧮 推算（rule-based by ROI 與長尾強度） |
| `update_at` | 報表生成時間 | 系統生成 timestamp |

---

## 📘 四、資料來源類別總覽

| 類型 | 說明 | 常見欄位來源 |
|------|------|----------------|
| 📗 **原始資料（逐週票房）** | 每週實際票房、成長率等時間序列 | `amount`, `rate`, `week_range`, `theater_count` |
| 📙 **聚合資料（逐片票房總表）** | 每部電影的整體週期統計 | `total_amount`, `avg_amount_per_week`, `decline_rate_mean`, `is_long_tail` |
| 📘 **電影資訊（靜態屬性）** | 類型、區域、分級、片長、發行商等 | `region`, `rating`, `publisher`, `film_length_min` |
| ⚙️ **模型預測（ML 輸出）** | 預測未來票房、衰退、再映 ROI | `forecast_*`, `expected_re_release_*` |
| 🧮 **推算欄位（衍生與決策）** | 根據統計或模型結果用公式／規則生成 | `performance_gap`, `promotion_score`, `recommended_screen_count`, `ROI` |

---

✅ **建議保存路徑：**  
`/docs/columns_origin_map.md`

此文件將協助你在開發 ETL、模型訓練與報表生成階段快速查欄位來源與依賴關係。
