# Pipeline 配置系統使用說明

## 簡介

為了避免每次執行腳本都要打一長串命令，我們建立了一個配置檔案系統。您只需要：

1. **編輯配置檔案** → 填寫參數
2. **一鍵執行** → 自動執行所有腳本

## 檔案位置

- **配置檔案**: `config/pipeline_config.yaml`
- **執行器腳本**: `scripts/run_pipeline.py`

## 快速開始

### 1. 編輯配置檔案

打開 `config/pipeline_config.yaml`，設定您要執行的腳本參數：

```yaml
filter_data:
  enabled: true  # 啟用此腳本
  input_file: "data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv"

  drop_columns:
    - "theater_count"
    - "rounds_cumsum"

  keep_rounds:
    - 1

  drop_null_active_week: true
```

### 2. 執行 Pipeline

```bash
# 實際執行
uv run scripts/run_pipeline.py config/pipeline_config.yaml

# 或先用 dry-run 模式檢查（只顯示命令，不實際執行）
uv run scripts/run_pipeline.py config/pipeline_config.yaml --dry-run
```

就這樣！系統會自動執行所有啟用的腳本。

## 配置檔案說明

### 基本結構

```yaml
script_name:
  enabled: true/false  # 是否執行此腳本
  # ... 各腳本的參數 ...
```

### 支援的腳本

#### 1. 累積特徵生成 (add_cumsum_features)

```yaml
add_cumsum_features:
  enabled: true
  input_file: "data/ML_boxoffice/phase1_flattened/boxoffice_timeseries_2025-11-06.csv"
  output_file: "data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv"
  description: "生成累積特徵（截至上週）"
```

**參數說明:**
- `enabled`: 是否執行此腳本
- `input_file`: 輸入 CSV 檔案路徑
- `output_file`: 輸出 CSV 檔案路徑
- `description`: 腳本說明（可選）

#### 2. 資料過濾 (filter_data)

```yaml
filter_data:
  enabled: true
  input_file: "data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv"
  output_file: ""  # 留空則自動生成帶時間戳記的檔名

  exclude_config: "config/exclude_movies.csv"  # 電影剔除清單

  drop_columns:  # 要刪除的欄位
    - "theater_count"
    - "rounds_cumsum"

  keep_rounds:  # 要保留的輪次
    - 1
    # - 2

  drop_null_active_week: true  # 是否刪除無活躍編號的 row

  description: "過濾資料"
```

**參數說明:**
- `enabled`: 是否執行此腳本
- `input_file`: 輸入 CSV 檔案路徑
- `output_file`: 輸出 CSV 檔案路徑（留空則自動生成）
- `exclude_config`: 電影剔除清單路徑
- `drop_columns`: 要刪除的欄位列表
- `keep_rounds`: 要保留的輪次列表（留空則保留全部）
- `drop_null_active_week`: 是否刪除無活躍編號的 row
- `description`: 腳本說明（可選）

## 使用範例

### 範例 1：只保留第 1 輪，刪除特定欄位

編輯 `config/pipeline_config.yaml`:

```yaml
filter_data:
  enabled: true
  input_file: "data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv"

  drop_columns:
    - "theater_count"
    - "rounds_cumsum"
    - "boxoffice_week_2"
    - "audience_week_2"

  keep_rounds:
    - 1

  drop_null_active_week: true
```

執行：
```bash
uv run scripts/run_pipeline.py config/pipeline_config.yaml
```

### 範例 2：保留第 1, 2 輪，刪除特定欄位

```yaml
filter_data:
  enabled: true
  input_file: "data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv"

  drop_columns:
    - "theater_count"

  keep_rounds:
    - 1
    - 2

  drop_null_active_week: false
```

### 範例 3：先生成累積特徵，再過濾資料

```yaml
add_cumsum_features:
  enabled: true
  input_file: "data/ML_boxoffice/phase1_flattened/boxoffice_timeseries_2025-11-06.csv"
  output_file: "data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv"

filter_data:
  enabled: true
  input_file: "data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv"

  drop_columns:
    - "theater_count"

  keep_rounds:
    - 1

  drop_null_active_week: true
```

系統會按順序執行兩個腳本。

### 範例 4：只執行特定腳本

如果只想執行某個腳本，將其他腳本的 `enabled` 設為 `false`:

```yaml
add_cumsum_features:
  enabled: false  # 不執行

filter_data:
  enabled: true   # 只執行這個
  # ...
```

## Dry-Run 模式

在實際執行前，建議先用 dry-run 模式檢查：

```bash
uv run scripts/run_pipeline.py config/pipeline_config.yaml --dry-run
```

這會顯示將要執行的命令，但不會實際執行。輸出範例：

```
要執行的命令:
  uv run src/ML_boxoffice/phase2_features/filter_data.py data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv --exclude-config config/exclude_movies.csv --drop-columns theater_count,rounds_cumsum --keep-rounds 1 --drop-null-active-week

  [DRY-RUN] 僅顯示命令，不實際執行
```

確認命令正確後，再移除 `--dry-run` 實際執行。

## 配置檔案註解

YAML 支援註解，使用 `#` 開頭：

```yaml
filter_data:
  enabled: true

  drop_columns:
    - "theater_count"
    # - "rounds_cumsum"  # 暫時不刪除這個欄位

  keep_rounds:
    - 1
    - 2  # 也保留第 2 輪
```

## 常見問題

### Q1: 如何查看配置檔案的完整範例？

A: 查看 `config/pipeline_config.yaml`，裡面有完整的範例和註解。

### Q2: 如何只執行某個腳本？

A: 將其他腳本的 `enabled` 設為 `false`，只將要執行的腳本設為 `true`。

### Q3: 可以一次執行多個腳本嗎？

A: 可以！將多個腳本的 `enabled` 都設為 `true`，系統會依序執行。

### Q4: 輸出檔案放在哪裡？

A:
- 如果在配置中指定了 `output_file`，則存到指定位置
- 如果 `output_file` 留空，則自動生成帶時間戳記的檔名

### Q5: 如何確認參數設定正確？

A: 先用 `--dry-run` 模式執行，檢查輸出的命令是否正確。

### Q6: 配置檔案可以有多個嗎？

A: 可以！您可以建立多個配置檔案，例如：
```bash
# 使用不同的配置檔案
uv run scripts/run_pipeline.py config/pipeline_config_test.yaml
uv run scripts/run_pipeline.py config/pipeline_config_prod.yaml
```

### Q7: 如果參數留空會怎樣？

A:
- `drop_columns` 留空 → 不刪除任何欄位
- `keep_rounds` 留空 → 保留所有輪次
- `output_file` 留空 → 自動生成檔名

### Q8: 修改配置後需要重新啟動什麼嗎？

A: 不需要！每次執行都會重新讀取配置檔案。

## 優點

相比於打長長的命令列，使用配置檔案系統有以下優點：

✅ **清晰易讀** - 所有參數一目了然
✅ **不易出錯** - 不用擔心打錯命令
✅ **可重複使用** - 保存配置，下次直接用
✅ **易於修改** - 修改參數很方便
✅ **統一管理** - 所有腳本的參數集中管理
✅ **支援註解** - 可以寫註解說明每個參數的用途

## 進階技巧

### 建立不同情境的配置檔案

您可以針對不同情境建立多個配置檔案：

```
config/
├── pipeline_config.yaml          # 預設配置
├── pipeline_config_round1.yaml   # 只處理第1輪
├── pipeline_config_round12.yaml  # 處理第1,2輪
└── pipeline_config_test.yaml     # 測試用配置
```

使用時指定配置檔案：

```bash
uv run scripts/run_pipeline.py config/pipeline_config_round1.yaml
```

### 使用版本控制

建議將配置檔案加入 Git 版本控制，這樣可以：
- 追蹤配置的變更歷史
- 與團隊成員分享配置
- 在不同環境使用不同配置

## 未來擴充

未來如果有新的腳本，只需要：

1. 在 `config/pipeline_config.yaml` 加入新腳本的配置區塊
2. 在 `scripts/run_pipeline.py` 加入對應的執行函數

就可以用同樣的方式管理新腳本的參數了！

## 總結

使用配置系統後，原本這樣的命令：

```bash
uv run src\ML_boxoffice\phase2_features\filter_data.py data\ML_boxoffice\phase2_features\with_cumsum\features_cumsum_2025-11-06.csv --exclude-config config\exclude_movies.csv --drop-columns "theater_count,rounds_cumsum" --keep-rounds "1" --drop-null-active-week
```

只需要：

```bash
uv run scripts/run_pipeline.py config/pipeline_config.yaml
```

簡潔多了！🎉
