import sys
from pathlib import Path

# 將 src 目錄加入 Python 路徑，以便能夠 import common 模組
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pandas as pd
import numpy as np
from common.file_utils import ensure_dir
from io import StringIO
from datetime import datetime
from common.path_utils import PHASE3_PREPARE_DIR, PHASE4_MODELS_DIR
from ML_boxoffice.common.feature_engineering import BoxOfficeFeatureEngineer

# ===================================================================
# 全域設定
# ===================================================================
# 時間戳記
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 建立輸出資料夾
output_model_dir = Path(PHASE4_MODELS_DIR) / "M3" / f"M3_{timestamp}"
output_prepare_dir = Path(PHASE4_MODELS_DIR) / "M3" / f"M3_{timestamp}" / "prepared_data"
log_file = output_model_dir / f"training_log_{timestamp}.txt"

# 建立輸出資料夾
ensure_dir(output_prepare_dir)
ensure_dir(output_model_dir)

# 使用的訓練資料集
input_data_path = Path(PHASE3_PREPARE_DIR) / "M3_train_dataset" / "features_market_2025-11-07.csv"

# ===================================================================
# 日誌系統設定
# ===================================================================
# 建立 log 緩衝區
log_buffer = StringIO()


# 建立自訂的 print 函數,同時輸出到終端機和 log
class Logger:
    def __init__(self, log_buffer):
        self.terminal = sys.stdout
        self.log = log_buffer

    def write(self, message):
        # 處理 Windows 終端機編碼問題
        try:
            self.terminal.write(message)
        except UnicodeEncodeError:
            # 移除無法編碼的字符
            clean_message = message.encode("ascii", "ignore").decode("ascii")
            self.terminal.write(clean_message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()


# 重定向 stdout
sys.stdout = Logger(log_buffer)

print("=" * 60)
print(f"🚀 模型訓練開始 (M3 - Decision Tree): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)


# ===================================================================
# 資料預處理
# ===================================================================
# === 1. 讀取資料 ===
df = pd.read_csv(input_data_path)


# === 2-1. 排除指定的電影 ===
# 排除清單路徑
exclude_config_path = "config/exclude_movies.csv"

try:
    exclude_df = pd.read_csv(exclude_config_path, comment="#")
    exclude_gov_ids = exclude_df["gov_id"].dropna().astype(int).tolist()

    if len(exclude_gov_ids) > 0:
        print(f"\n從 {exclude_config_path} 讀取排除清單:")
        print(f"  發現 {len(exclude_gov_ids)} 部需要排除的電影")
        print(f"  排除的 gov_id: {exclude_gov_ids}")

        # 檢查有多少筆資料會被排除
        exclude_count = df[df["gov_id"].isin(exclude_gov_ids)].shape[0]
        exclude_movie_count = df[df["gov_id"].isin(exclude_gov_ids)]["gov_id"].nunique()
        print(f"  將排除 {exclude_movie_count} 部電影，共 {exclude_count} 筆資料")

        # 執行排除
        df = df[~df["gov_id"].isin(exclude_gov_ids)].copy()
        print(f"  排除後剩餘資料筆數: {len(df)}")
    else:
        print(f"\n{exclude_config_path} 中沒有需要排除的電影")

except FileNotFoundError:
    print(f"\n警告: 找不到排除清單檔案 {exclude_config_path}，跳過排除步驟")
except Exception as e:
    print(f"\n警告: 讀取排除清單時發生錯誤: {e}，跳過排除步驟")


# === 2-2. 篩選資料 ===
# 只保留首輪資料
df = df[df["round_idx"] == 1].copy()
# 只保留有活躍週次的資料
df = df[df["current_week_active_idx"].notna()]
# 必須同時有 week_1 和 week_2 的資料,且都不為 0
df = df[
    (df["boxoffice_week_1"].notna())
    & (df["boxoffice_week_1"] > 0)
    & (df["boxoffice_week_2"].notna())
    & (df["boxoffice_week_2"] > 0)
]
print(f"基本篩選後資料筆數: {len(df)}")


# === 3. 月份週期性編碼 ===
# 使用共用特徵工程模組進行編碼
df = BoxOfficeFeatureEngineer.add_features_to_dataframe(df, group_by_col='gov_id')


# === 4. 刪除不需要的欄位 ===
# 定義要刪除的欄位
drop_columns = [
    # 資料洩漏
    "tickets",
    "theater_count",  # amount 要留到最後才刪
    # 不需要的時間資訊
    "official_release_date",
    "week_range",
    "current_week_real_idx",
    # 跨輪累積
    "boxoffice_cumsum",
    "boxoffice_round1_cumsum",
    "boxoffice_current_round_cumsum",  # ← 檢查這個
    "audience_cumsum",
    "audience_round1_cumsum",
    "audience_current_round_cumsum",  # ← 檢查這個
    "rounds_cumsum",
    # 問題欄位
    "ticket_price_avg_current",
    # 分類欄位 (時間有限先刪除)
    "region",
    "publisher",
    # 已編碼的原始欄位
    "release_month",
]

df = df.drop(columns=drop_columns)


# === 5. 檢查缺失值 ===
print("\n=== 缺失值檢查 ===")
print(df.isnull().sum()[df.isnull().sum() > 0])


# === 6. 存檔: 完整資料 (含 amount 和 gov_id) ===
df.to_csv(output_prepare_dir / "preprocessed_full.csv", index=False, encoding="utf-8-sig")
print(f"\n✅ 已存檔: {output_prepare_dir / 'preprocessed_full.csv'}")
print("📍資料數量小計:")
print(f"   欄位數: {len(df.columns)}")
print(f"   資料筆數: {len(df)}")


# === 7. 顯示最終欄位 ===
print("\n=== 📍最終欄位清單 ===")
for i, col in enumerate(df.columns, 1):
    print(f"{i:2d}. {col}")


# === 8. 存檔: 訓練用特徵 (移除 amount，保留 gov_id 用於分組) ===
feature_cols = [col for col in df.columns if col != "amount"]
df_features = df[feature_cols]
df_features.to_csv(
    output_prepare_dir / "preprocessed_features.csv", index=False, encoding="utf-8-sig"
)
print(f"\n✅ 已存檔: {output_prepare_dir / 'preprocessed_features.csv'}")


# === 9. 存檔: 目標變數 ===
df[["gov_id", "amount"]].to_csv(
    output_prepare_dir / "preprocessed_target.csv", index=False, encoding="utf-8-sig"
)
print(f"✅ 已存檔: {output_prepare_dir / 'preprocessed_target.csv'}")


# === 10. 統計摘要 ===
print("\n=== 📍資料摘要 ===")
print(df[["amount", "boxoffice_week_1", "current_week_active_idx"]].describe())


# ===================================================================
# 訓練模型
# ===================================================================
# === 11. 分離特徵與目標 ===
X = df.drop(columns=["amount"])
y = df["amount"]

print(f"\n特徵矩陣 X: {X.shape}")
print(f"目標變數 y: {y.shape}")

print("\n" + "=" * 50)
print("🔍 特徵與目標相關性 (Top 10)")
print("=" * 50)

correlation = pd.DataFrame(
    {
        "feature": X.drop(columns=["gov_id"]).columns,
        "correlation": X.drop(columns=["gov_id"]).corrwith(y),
    }
).sort_values("correlation", key=abs, ascending=False)

print(correlation.head(10).to_string(index=False))


# === 12. Group-based 切分資料集 ===
from sklearn.model_selection import GroupShuffleSplit

# 確保同一部電影的所有週次資料不會同時出現在訓練/測試集
splitter = GroupShuffleSplit(test_size=0.2, n_splits=1, random_state=42)
train_idx, test_idx = next(splitter.split(X, y, groups=X["gov_id"]))

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

print("\n📍 訓練集/測試集分割結果")
print(f"訓練集: {len(X_train)} 筆 ({len(X_train['gov_id'].unique())} 部電影)")
print(f"測試集: {len(X_test)} 筆 ({len(X_test['gov_id'].unique())} 部電影)")


# === 13. 移除 gov_id (只用於分組,不參與訓練) ===
X_train_model = X_train.drop(columns=["gov_id"])
X_test_model = X_test.drop(columns=["gov_id"])

print(f"\n模型訓練特徵數: {X_train_model.shape[1]}")


# === 14. 檢查缺失值 ===
print("\n" + "=" * 50)
print("🔍 訓練集缺失值檢查")
print("=" * 50)

missing_train = X_train_model.isnull().sum()
missing_train = missing_train[missing_train > 0].sort_values(ascending=False)

if len(missing_train) > 0:
    print("⚠️ 發現缺失值:")
    print(missing_train)
    print(f"\n總缺失筆數: {X_train_model.isnull().any(axis=1).sum()}/{len(X_train_model)}")
else:
    print("✅ 無缺失值")


# === 15. 訓練模型: Decision Tree Regressor ===
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

print("\n" + "=" * 50)
print("🟢 模型: Decision Tree Regressor")
print("=" * 50)

dt_model = DecisionTreeRegressor(
    max_depth=10,  # 樹的最大深度
    min_samples_split=20,  # 分裂節點所需最小樣本數
    min_samples_leaf=10,  # 葉節點所需最小樣本數
    random_state=42,
)

dt_model.fit(X_train_model, y_train)

y_pred_dt = dt_model.predict(X_test_model)

print(f"MAE:  {mean_absolute_error(y_test, y_pred_dt):,.0f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_dt)):,.0f}")
print(f"R²:   {r2_score(y_test, y_pred_dt):.4f}")


# ===================================================================
# 洞察模型分析結果
# ===================================================================
# === 16. 特徵重要性分析 ===
print("\n" + "=" * 50)
print("📊 Top 10 重要特徵 (Decision Tree)")
print("=" * 50)

feature_importance = pd.DataFrame(
    {"feature": X_train_model.columns, "importance": dt_model.feature_importances_}
).sort_values("importance", ascending=False)

print(feature_importance.head(10).to_string(index=False))

# 存檔特徵重要性
feature_importance.to_csv(
    output_model_dir / "feature_importance.csv", index=False, encoding="utf-8-sig"
)
print(f"\n✅ 特徵重要性已存檔: {output_model_dir / 'feature_importance.csv'}")


# === 17. 視覺化: 預測 vs 實際 ===
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]  # 中文字型
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(8, 6))

# Decision Tree
ax.scatter(y_test, y_pred_dt, alpha=0.5, s=10)
ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--", lw=2)
ax.set_xlabel("實際票房")
ax.set_ylabel("預測票房")
ax.set_title(f"Decision Tree (R²={r2_score(y_test, y_pred_dt):.3f})")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_model_dir / "prediction_comparison.png", dpi=150, bbox_inches="tight")
print(f"\n✅ 預測結果圖已存檔: {output_model_dir / 'prediction_comparison.png'}")
plt.show()


# === 18. 特徵相關性熱力圖 ===
print("\n" + "=" * 50)
print("🔥 特徵相關性熱力圖")
print("=" * 50)

# 計算相關性矩陣（排除 gov_id）
correlation_matrix = X_train_model.corr()

# 建立熱力圖
plt.figure(figsize=(20, 16))
sns.heatmap(
    correlation_matrix,
    annot=False,  # 特徵太多時不顯示數字
    cmap="coolwarm",
    center=0,
    square=True,
    linewidths=0.5,
    cbar_kws={"shrink": 0.8},
    vmin=-1,
    vmax=1,
)
plt.title("特徵相關性熱力圖", fontsize=16, pad=20)
plt.tight_layout()
plt.savefig(output_model_dir / "correlation_heatmap.png", dpi=150, bbox_inches="tight")
print(f"✅ 相關性熱力圖已存檔: {output_model_dir / 'correlation_heatmap.png'}")
plt.show()

# 儲存相關性矩陣為 CSV
correlation_matrix.to_csv(
    output_model_dir / "correlation_matrix.csv", encoding="utf-8-sig"
)
print(f"✅ 相關性矩陣已存檔: {output_model_dir / 'correlation_matrix.csv'}")

# 找出高度相關的特徵對（|r| > 0.8）
print("\n" + "=" * 50)
print("⚠️  高度相關的特徵對 (|r| > 0.8)")
print("=" * 50)

high_corr_pairs = []
for i in range(len(correlation_matrix.columns)):
    for j in range(i + 1, len(correlation_matrix.columns)):
        corr_value = correlation_matrix.iloc[i, j]
        if abs(corr_value) > 0.8:
            high_corr_pairs.append(
                {
                    "feature_1": correlation_matrix.columns[i],
                    "feature_2": correlation_matrix.columns[j],
                    "correlation": corr_value,
                }
            )

if len(high_corr_pairs) > 0:
    high_corr_df = pd.DataFrame(high_corr_pairs).sort_values(
        "correlation", key=abs, ascending=False
    )
    print(high_corr_df.to_string(index=False))
    high_corr_df.to_csv(
        output_model_dir / "high_correlation_pairs.csv", index=False, encoding="utf-8-sig"
    )
    print(f"\n✅ 高相關特徵對已存檔: {output_model_dir / 'high_correlation_pairs.csv'}")
else:
    print("✅ 沒有發現高度相關的特徵對")


# ===================================================================
# 儲存模型與分析結果
# ===================================================================
# === 19. 儲存模型 ===
import joblib

joblib.dump((dt_model, X_train_model.columns.tolist()), output_model_dir / "model_decision_tree.pkl")
print(f"\n✅ 模型已存檔:")
print(f"   - {output_model_dir / 'model_decision_tree.pkl'}")


# === 20. 儲存測試集預測結果 ===
results = pd.DataFrame(
    {
        "gov_id": X_test["gov_id"].values,
        "actual": y_test.values,
        "pred_dt": y_pred_dt,
        "error_dt": y_test.values - y_pred_dt,
    }
)

results.to_csv(output_model_dir / "test_predictions.csv", index=False, encoding="utf-8-sig")
print(f"✅ 測試集預測結果已存檔: {output_model_dir / 'test_predictions.csv'}")


# === 21. 紀錄本次執行過程log ===
print("\n" + "=" * 60)
print(f"✅ 訓練完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 寫入 log 檔案
sys.stdout = sys.stdout.terminal  # 恢復正常的 stdout
with open(log_file, "w", encoding="utf-8") as f:
    f.write(log_buffer.getvalue())

print(f"\n✅ 訓練紀錄已存檔: {log_file}")
print("\n🎉 訓練完成!")

# ===================================================================
#                                 END
# ===================================================================

# ===================================================================
# 補充說明
# ===================================================================
"""
## 📦 最終會產生的檔案
```
data/ML_boxoffice/phase4_models/M3/M3_YYYYMMDD_HHMMSS/
├── prepared_data/
│   ├── preprocessed_full.csv           # 完整預處理資料
│   ├── preprocessed_features.csv       # 特徵矩陣 (X)
│   └── preprocessed_target.csv         # 目標變數 (y)
├── training_log_YYYYMMDD_HHMMSS.txt    # 訓練日誌
├── feature_importance.csv              # 特徵重要性排名
├── prediction_comparison.png           # 預測 vs 實際散佈圖
├── correlation_heatmap.png             # 特徵相關性熱力圖
├── correlation_matrix.csv              # 相關性矩陣
├── high_correlation_pairs.csv          # 高相關特徵對（如有）
├── test_predictions.csv                # 測試集詳細預測結果
└── model_decision_tree.pkl             # 已訓練的 Decision Tree 模型
```

## 🔍 M3 模型說明
- **模型類型**: Decision Tree Regressor（決策樹回歸）
- **訓練資料**: features_market_2025-11-07.csv
- **模型參數**:
  - max_depth=10
  - min_samples_split=20
  - min_samples_leaf=10
- **資料處理**:
  - 排除指定電影
  - 只保留首輪資料
  - 月份週期性編碼
  - 移除資料洩漏欄位
- **評估指標**: MAE, RMSE, R²
"""
