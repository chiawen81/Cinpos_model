# 資料刪減腳本使用說明

## 檔案位置

- **主腳本**: `src/ML_boxoffice/phase2_features/filter_data.py`
- **電影剔除配置**: `config/exclude_movies.csv`
- **輸出目錄**: `data/ML_boxoffice/phase2_features/`

## 功能說明

此腳本提供以下資料刪減功能：

1. **欄位刪減**: 刪除指定的欄位
2. **輪次過濾**: 只保留指定的輪次
3. **活躍週次過濾**: 刪除無輪內活躍編號(current_week_active_idx為NaN)的row
4. **電影剔除**: 從配置檔案讀取並剔除指定的電影

## 使用方式

### 基本語法

```bash
uv run src/ML_boxoffice/phase2_features/filter_data.py <input_csv> [選項]
```

### 可用選項

| 選項 | 說明 | 範例 |
|------|------|------|
| `--exclude-config <path>` | 電影剔除清單配置檔案路徑 | `--exclude-config config/exclude_movies.csv` |
| `--drop-columns <cols>` | 要刪除的欄位（逗號分隔） | `--drop-columns "col1,col2,col3"` |
| `--keep-rounds <rounds>` | 要保留的輪次（逗號分隔） | `--keep-rounds "1,2"` |
| `--drop-null-active-week` | 刪除無活躍編號的row | `--drop-null-active-week` |
| `--output <path>` | 輸出檔案路徑（可選） | `--output output.csv` |

## 使用範例

### 1. 只保留第1輪且刪除無活躍編號的row

```bash
uv run src/ML_boxoffice/phase2_features/filter_data.py \
  data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv \
  --keep-rounds "1" \
  --drop-null-active-week
```

### 2. 刪除特定欄位

```bash
uv run src/ML_boxoffice/phase2_features/filter_data.py \
  data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv \
  --drop-columns "boxoffice_week_2,audience_week_2,screens_week_2"
```

### 3. 保留第1,2輪並刪除特定欄位

```bash
uv run src/ML_boxoffice/phase2_features/filter_data.py \
  data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv \
  --keep-rounds "1,2" \
  --drop-columns "boxoffice_week_2,audience_week_2"
```

### 4. 使用電影剔除清單

```bash
# 先編輯 config/exclude_movies.csv 加入要剔除的電影ID
# 然後執行：
uv run src/ML_boxoffice/phase2_features/filter_data.py \
  data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv \
  --keep-rounds "1"
```

### 5. 指定輸出檔案路徑

```bash
uv run src/ML_boxoffice/phase2_features/filter_data.py \
  input.csv \
  --keep-rounds "1" \
  --output data/ML_boxoffice/phase2_features/my_filtered_data.csv
```

## 電影剔除清單配置

### 配置檔案格式

配置檔案位於 `config/exclude_movies.csv`，格式如下：

```csv
gov_id,reason
# 這是電影剔除清單配置檔案
# 格式：gov_id,reason
8873,票房資料異常
8878,重複資料
9161,測試資料
```

### 使用方式

1. 編輯 `config/exclude_movies.csv`
2. 在檔案中加入要剔除的電影 `gov_id` 和原因
3. 執行腳本時會自動讀取此配置檔案

### 注意事項

- 使用 `#` 開頭的行會被視為註解
- `reason` 欄位僅供參考，不影響剔除功能
- 如果不想使用預設配置檔案，可以用 `--exclude-config` 指定其他檔案

## 安全限制

### 不可刪除的欄位

- `gov_id`: 永遠不可刪除

### 至少保留一個的欄位

以下欄位必須至少保留一個：
- `official_release_date`
- `week_range`
- `round_idx`
- `current_week_real_idx`
- `current_week_active_idx`

### 必須存在的欄位檢查

執行前會檢查以下欄位是否存在：
- `gov_id`
- `official_release_date`
- `week_range`
- `round_idx`
- `current_week_real_idx`
- `current_week_active_idx`
- `gap_real_week_2to1`
- `gap_real_week_1tocurrent`

如果缺少任何必要欄位，腳本將拒絕執行。

## 輸出說明

### 檔名格式

如果未指定輸出路徑，檔名將自動生成：

```
filtered_<原檔名>_<時間戳記>.csv
```

例如：`filtered_features_cumsum_2025-11-06_20251106_230957.csv`

### 輸出位置

所有輸出檔案統一存放在：`data/ML_boxoffice/phase2_features/`

### 時間戳記格式

- 格式: `YYYYMMDD_HHMMSS`
- 範例: `20251106_230957` (2025年11月6日 23:09:57)

## 執行順序

腳本會按照以下順序執行刪減操作：

1. **載入資料** → 安全檢查（檢查必要欄位）
2. **電影剔除** → 從配置檔案讀取並剔除指定電影
3. **欄位刪減** → 刪除指定欄位
4. **輪次過濾** → 只保留指定輪次
5. **活躍週次過濾** → 刪除無活躍編號的row
6. **恢復順序並儲存** → 維持原始順序並輸出

## 注意事項

### 資料順序

- ✅ 保證維持原始資料的 row 順序
- ✅ 不會因為刪減操作而改變 row 的相對位置

### 配置檔案

- 預設會嘗試讀取 `config/exclude_movies.csv`
- 如果檔案不存在，會跳過電影剔除步驟（不會報錯）
- 可以使用 `--exclude-config` 指定其他配置檔案

### 錯誤處理

- 嘗試刪除受保護欄位 → 拒絕執行並報錯
- 嘗試刪除所有必要欄位 → 拒絕執行並報錯
- 缺少必要欄位 → 拒絕執行並報錯
- 指定不存在的欄位 → 顯示警告但繼續執行

## 常見問題

### Q: 如何查看有哪些欄位可以刪除？

A: 可以先用 `head` 或其他工具查看 CSV 標題行：

```bash
head -1 data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_2025-11-06.csv
```

### Q: 可以同時使用多個過濾條件嗎？

A: 可以！所有選項都可以組合使用：

```bash
uv run src/ML_boxoffice/phase2_features/filter_data.py input.csv \
  --drop-columns "col1,col2" \
  --keep-rounds "1,2" \
  --drop-null-active-week
```

### Q: 如何確認刪減結果？

A: 腳本執行後會顯示詳細統計：
- 刪除的列數
- 刪除的欄數
- 最終資料大小

### Q: 刪減後的檔案放在哪裡？

A: 預設放在 `data/ML_boxoffice/phase2_features/`，檔名會帶有時間戳記。

### Q: 可以覆蓋原始檔案嗎？

A: 不建議。但如果需要，可以使用 `--output` 指定原始檔案路徑（請先備份）。

## 測試驗證

腳本已通過以下測試：

✅ 欄位刪除功能
✅ 輪次過濾功能
✅ 活躍週次過濾功能
✅ 電影剔除功能
✅ 原始順序保持
✅ 安全檢查機制
✅ 時間戳記生成
