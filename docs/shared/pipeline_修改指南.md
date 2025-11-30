# Pipeline 系統修改指南

## 目的

本文件提供 Pipeline 系統的修改檢查清單，確保當新增或修改腳本時，所有相關檔案都能保持同步和一致性。

## 適用情境

以下情況需要參考本指南：

1. 新增一個腳本到 Pipeline 系統
2. 修改現有腳本的參數介面
3. 更新腳本的預設行為
4. 修改 Pipeline 執行邏輯

---

## 新增腳本到 Pipeline 系統的完整檢查清單

當您要將一個新的腳本加入到 Pipeline 系統時，請依序完成以下步驟：

### 步驟 1：分析目標腳本

**檔案位置：** `src/ML_boxoffice/phase2_features/<腳本名稱>.py`

需要確認的資訊：

- [ ] 腳本接受哪些命令列參數？
- [ ] 哪些參數是必填的？哪些是選填的？
- [ ] 參數的格式是什麼？（位置參數 vs 標誌參數）
- [ ] 腳本的預設行為是什麼？（例如：自動找最新檔案）
- [ ] 輸入檔案的預設路徑？
- [ ] 輸出檔案的預設路徑？

**範例分析：**
```python
# add_market_features.py 的參數介面
# - 使用 argparse
# - --input: 輸入檔案（選填，預設自動找 phase1_flattened 最新檔）
# - --movie-info: 電影資訊檔案（選填，預設自動找 combined 最新檔）
# - --output: 輸出檔案（選填，預設輸出到 with_market）
```

---

### 步驟 2：更新 `config/pipeline_config.yaml`

**檔案位置：** `config/pipeline_config.yaml`

需要新增的內容：

- [ ] 在適當位置新增腳本配置區塊
- [ ] 加入分隔線註解
- [ ] 設定 `enabled: false`（預設停用）
- [ ] 列出所有參數及其說明
- [ ] 對每個參數加上註解說明其用途
- [ ] 說明留空時的預設行為
- [ ] 加入 `description` 欄位說明腳本功能
- [ ] **重要：在最上方加入執行命令，並標記 `複製指令!!!`**

**範例：**
```yaml
# ============================================================
# ML 票房預測 Pipeline 配置檔案
# ============================================================
# 用途：統一管理所有腳本的參數，避免打長長的命令列
# 使用方式：
#   1. 在下方填寫要執行的腳本及其參數
#   2. 執行：uv run scripts/run_pipeline.py config/pipeline_config.yaml      <<<<<<<< 複製指令!!!
# ============================================================

# ------------------------------------------------------------
# 市場特徵生成腳本 (add_market_features.py)
# ------------------------------------------------------------
add_market_features:
  enabled: false  # 是否執行此腳本
  # 欲新增<市場特徵欄位>的 csv
  input_file: ""   # 留空會自動從 data/ML_boxoffice/phase1_flattened 找日期最新的檔案
  # 電影資訊檔案
  movie_info_file: ""  # 留空會自動從 data/processed/movieInfo_gov/combined 找日期最新的檔案
  # 輸出位置
  output_file: ""  # 留空會自動輸出到 data/ML_boxoffice/phase2_features/with_market（檔名含當日日期）
  description: "生成市場特徵（票價、年份、月份、地區、發行商、分級、片長）- 會自動找最新的 phase1 檔案"
```

**檢查要點：**
- [ ] 參數名稱與腳本實際參數一致
- [ ] 註解清楚說明預設行為
- [ ] 配置區塊位置合理（通常按照執行順序排列）

---

### 步驟 3：更新 `scripts/run_pipeline.py`

**檔案位置：** `scripts/run_pipeline.py`

需要修改的地方有 **三處**：

#### 3.1 新增執行器函數

在現有的執行器函數後面新增一個專門的執行器函數。

- [ ] 函數名稱格式：`run_<腳本名稱>(self, config)`
- [ ] 加入 docstring
- [ ] 顯示分隔線和標題
- [ ] 檢查 `enabled` 狀態
- [ ] 顯示所有配置參數（包含預設行為說明）
- [ ] 構建命令列表
- [ ] 根據參數值條件性加入標誌
- [ ] 呼叫 `self._execute_command(cmd)`

**範例：**
```python
def run_add_market_features(self, config):
    """執行市場特徵生成腳本"""
    print("\n" + "-" * 70)
    print("[n/n] 執行市場特徵生成腳本")
    print("-" * 70)

    if not config.get("enabled", False):
        print("  [SKIP] 此腳本已停用（enabled: false）")
        return

    # 顯示配置
    print(f"\n配置:")
    if config.get("input_file"):
        print(f"  - 輸入檔案: {config.get('input_file')}")
    else:
        print(f"  - 輸入檔案: (自動使用最新檔案)")

    if config.get("movie_info_file"):
        print(f"  - 電影資訊檔案: {config.get('movie_info_file')}")
    else:
        print(f"  - 電影資訊檔案: (自動使用最新檔案)")

    if config.get("output_file"):
        print(f"  - 輸出檔案: {config.get('output_file')}")
    else:
        print(f"  - 輸出檔案: (自動生成)")

    print(f"  - 說明: {config.get('description', '無')}")

    # 構建命令
    cmd = [
        "uv",
        "run",
        "src/ML_boxoffice/phase2_features/add_market_features.py",
    ]

    # 添加可選參數
    if config.get("input_file"):
        cmd.extend(["--input", config["input_file"]])

    if config.get("movie_info_file"):
        cmd.extend(["--movie-info", config["movie_info_file"]])

    if config.get("output_file"):
        cmd.extend(["--output", config["output_file"]])

    self._execute_command(cmd)
```

**檢查要點：**
- [ ] 命令路徑正確（`src/ML_boxoffice/phase2_features/<腳本名>.py`）
- [ ] 參數標誌與腳本的 argparse 定義一致
- [ ] 選填參數使用 `if config.get(...)` 條件判斷
- [ ] 顯示訊息清楚說明預設行為

#### 3.2 更新 `run()` 方法中的啟用腳本偵測

在 `run()` 方法中找到「計算要執行的腳本數量」區塊，新增一行偵測邏輯。

- [ ] 位置：在 `enabled_scripts = []` 初始化後
- [ ] 格式：`if self.config.get("<腳本名>", {}).get("enabled"): enabled_scripts.append("<腳本名>")`
- [ ] 順序：按照腳本執行順序排列

**範例：**
```python
# 計算要執行的腳本數量
enabled_scripts = []
if self.config.get("add_cumsum_features", {}).get("enabled"):
    enabled_scripts.append("add_cumsum_features")
if self.config.get("add_market_features", {}).get("enabled"):  # 新增這行
    enabled_scripts.append("add_market_features")
if self.config.get("filter_data", {}).get("enabled"):
    enabled_scripts.append("filter_data")
```

**檢查要點：**
- [ ] 腳本名稱與配置檔案中的 key 一致
- [ ] 插入位置合理（通常按執行順序）

#### 3.3 更新 `run()` 方法中的執行區塊

在 `run()` 方法中找到「執行各個腳本」區塊，新增執行呼叫。

- [ ] 位置：在現有腳本執行區塊之間適當位置
- [ ] 格式：`if "<腳本名>" in enabled_scripts: self.run_<腳本名>(self.config["<腳本名>"])`
- [ ] 順序：與偵測區塊順序一致

**範例：**
```python
# 執行各個腳本
if "add_cumsum_features" in enabled_scripts:
    self.run_add_cumsum_features(self.config["add_cumsum_features"])

if "add_market_features" in enabled_scripts:  # 新增這行
    self.run_add_market_features(self.config["add_market_features"])

if "filter_data" in enabled_scripts:
    self.run_filter_data(self.config["filter_data"])
```

**檢查要點：**
- [ ] 函數名稱與步驟 3.1 定義的函數一致
- [ ] 配置 key 與 YAML 檔案一致

---

### 步驟 4：測試

完成上述修改後，務必進行測試。

#### 4.1 Dry-Run 測試（必做）

使用 dry-run 模式確認命令生成正確。

```bash
uv run scripts/run_pipeline.py config/pipeline_config.yaml --dry-run
```

**測試案例 1：使用預設值（留空）**

在 `pipeline_config.yaml` 中：
```yaml
add_market_features:
  enabled: true
  input_file: ""
  movie_info_file: ""
  output_file: ""
```

預期輸出：
```
要執行的命令:
  uv run src/ML_boxoffice/phase2_features/add_market_features.py
```

- [ ] 命令不包含任何參數標誌
- [ ] 顯示訊息說明使用自動最新檔案

**測試案例 2：指定所有參數**

在 `pipeline_config.yaml` 中：
```yaml
add_market_features:
  enabled: true
  input_file: "data/test_input.csv"
  movie_info_file: "data/test_movie.csv"
  output_file: "data/test_output.csv"
```

預期輸出：
```
要執行的命令:
  uv run src/ML_boxoffice/phase2_features/add_market_features.py --input data/test_input.csv --movie-info data/test_movie.csv --output data/test_output.csv
```

- [ ] 所有參數標誌正確加入
- [ ] 參數值正確對應

**測試案例 3：混合使用**

測試部分留空、部分指定的情況，確保邏輯正確。

#### 4.2 實際執行測試（選做）

如果有測試資料，可以實際執行確認腳本能正常運作。

```bash
uv run scripts/run_pipeline.py config/pipeline_config.yaml
```

- [ ] 腳本成功執行
- [ ] 輸出檔案產生在預期位置
- [ ] 檔案內容正確

---

### 步驟 5：更新文件（選做但建議）

如果該腳本需要使用者了解，建議更新使用說明文件。

**檔案位置：** `docs/shared/pipeline_配置使用說明.md`

需要新增的內容：

- [ ] 在「支援的腳本」區塊新增一個章節
- [ ] 說明參數用途
- [ ] 說明預設行為
- [ ] 提供使用範例

---

## 一致性檢查清單總結

每次修改 Pipeline 系統時，請確認以下三個檔案保持同步：

### `config/pipeline_config.yaml`
- [ ] 腳本配置區塊存在
- [ ] 所有參數都有列出
- [ ] 參數註解清楚說明預設行為
- [ ] `description` 說明腳本功能

### `scripts/run_pipeline.py`
- [ ] 執行器函數 `run_<腳本名>()` 已定義
- [ ] 命令路徑正確
- [ ] 參數標誌與腳本 argparse 一致
- [ ] `enabled_scripts` 偵測邏輯已加入
- [ ] 執行區塊呼叫已加入

### 目標腳本 `src/.../腳本名.py`
- [ ] 參數介面穩定（argparse 定義）
- [ ] 支援選填參數
- [ ] 有合理的預設行為

---

## 常見錯誤

### 錯誤 1：參數標誌不一致

**症狀：** Pipeline 執行時找不到參數或參數無效

**原因：** `run_pipeline.py` 中的參數標誌與腳本的 argparse 定義不一致

**範例：**
```python
# 錯誤：腳本使用 --movie-info，但 pipeline 使用 --movie_info
cmd.extend(["--movie_info", config["movie_info_file"]])  # ❌

# 正確：
cmd.extend(["--movie-info", config["movie_info_file"]])  # ✅
```

**解決方法：** 檢查腳本的 argparse 定義，確保標誌名稱完全一致

---

### 錯誤 2：必填參數未提供

**症狀：** 腳本執行時報錯缺少必要參數

**原因：** 配置檔案中參數留空，但腳本要求必填

**解決方法：**
- 方案 1：在配置檔案中提供必填參數
- 方案 2：修改腳本讓參數變為選填，加入預設行為

---

### 錯誤 3：忘記更新 enabled_scripts 偵測

**症狀：** 配置檔案中 `enabled: true`，但腳本不執行

**原因：** 忘記在 `run()` 方法中加入偵測邏輯

**解決方法：** 在 `run()` 方法的「計算要執行的腳本數量」區塊加入偵測

---

### 錯誤 4：執行順序錯誤

**症狀：** 後面的腳本需要前面腳本的輸出，但執行順序不對

**原因：** `enabled_scripts` 偵測順序或執行區塊順序錯誤

**解決方法：** 調整順序，確保依賴的腳本先執行

---

## 腳本參數介面最佳實踐

為了讓腳本更容易整合到 Pipeline 系統，建議遵循以下規範：

### 1. 使用 argparse 而非位置參數

**建議：**
```python
parser = argparse.ArgumentParser()
parser.add_argument("--input", type=str, help="輸入檔案")
parser.add_argument("--output", type=str, help="輸出檔案")
```

**不建議：**
```python
input_file = sys.argv[1]
output_file = sys.argv[2]
```

**原因：** argparse 更清晰，參數順序不重要

---

### 2. 所有參數都設為選填

**建議：**
```python
parser.add_argument("--input", type=str, default="", help="輸入檔案（留空則自動找最新）")
```

**不建議：**
```python
parser.add_argument("--input", type=str, required=True, help="輸入檔案")
```

**原因：** 選填參數更靈活，可以加入自動找檔案等預設行為

---

### 3. 加入 `find_latest_file()` 自動找檔案功能

**範例：**
```python
def find_latest_file(directory, pattern="*.csv"):
    """從指定目錄找出日期戳記最新的檔案"""
    dir_path = Path(directory)
    if not dir_path.exists():
        return None
    files = list(dir_path.glob(pattern))
    if not files:
        return None
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return latest_file
```

**使用：**
```python
if not args.input:
    input_path = find_latest_file("data/ML_boxoffice/phase1_flattened")
else:
    input_path = Path(args.input)
```

---

### 4. 輸出檔案自動生成日期戳記

**範例：**
```python
if not args.output:
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = Path(f"data/output/result_{today}.csv")
else:
    output_path = Path(args.output)
```

---

## 總結

修改 Pipeline 系統時，記住三個核心原則：

1. **同步性**：`pipeline_config.yaml`、`run_pipeline.py`、目標腳本三者參數介面必須一致
2. **測試性**：務必使用 dry-run 模式測試命令生成
3. **靈活性**：參數設為選填，提供合理的預設行為

遵循本指南的檢查清單，可以確保 Pipeline 系統的修改正確且一致。
