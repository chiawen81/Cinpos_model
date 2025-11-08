import pandas as pd
import numpy as np
import sys
from common.file_utils import ensure_dir
from pathlib import Path
from io import StringIO
from datetime import datetime
from common.path_utils import PHASE3_PREPARE_DIR, PHASE4_MODELS_DIR

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
print(f"🚀 模型訓練開始 (M3 - 排除大片測試): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)


# ===================================================================
# 資料預處理
# ===================================================================
# === 1. 讀取資料 ===
df = pd.read_csv(
    "data/ML_boxoffice/phase2_features/with_market/features_market_2025-11-07.csv"
)  # 替換成你的檔案路徑


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
df["release_month_sin"] = np.sin(2 * np.pi * df["release_month"] / 12)
df["release_month_cos"] = np.cos(2 * np.pi * df["release_month"] / 12)


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

print("\n📍 訓練集/測試集分割結果 (原始)")
print(f"訓練集: {len(X_train)} 筆 ({len(X_train['gov_id'].unique())} 部電影)")
print(f"測試集: {len(X_test)} 筆 ({len(X_test['gov_id'].unique())} 部電影)")


# === 13. [M3 特色] 在測試集中排除大片 ===
print("\n" + "=" * 60)
print("🎬 [M3 特色] 測試集排除大片樣本")
print("=" * 60)

# ===================================================================
# 過濾設定（可彈性調整）
# ===================================================================

# 1️⃣ 選擇過濾基準欄位
FILTER_COLUMN = "amount"  # 選項: "amount", "boxoffice_week_1", "boxoffice_week_2" 等

# 2️⃣ 選擇百分位數閾值（排除「高於」此百分位數的樣本）
#    例如: 85 表示排除前 15% (保留後85%)
#          90 表示排除前 10% (保留後90%)
#          95 表示排除前 5%  (保留後95%)
PERCENTILE_THRESHOLD = 95

# 3️⃣ 是否刪除整部電影（True: 刪除整部電影的所有週次，False: 只刪除符合條件的樣本）
EXCLUDE_WHOLE_MOVIE = True

# 4️⃣ 或使用絕對閾值（取消註解以使用，會覆蓋百分位數設定）
# ABSOLUTE_THRESHOLD = 10_000_000  # 排除 > 1000萬的樣本
# FILTER_COLUMN = "amount"

# ===================================================================

# 計算過濾基準值
if FILTER_COLUMN == "amount":
    filter_values = y_test
else:
    filter_values = X_test[FILTER_COLUMN]

# 判斷使用百分位數還是絕對值
if "ABSOLUTE_THRESHOLD" in locals():
    threshold = ABSOLUTE_THRESHOLD
    threshold_method = f"絕對值 > {threshold:,.0f}"
else:
    threshold = np.percentile(filter_values, PERCENTILE_THRESHOLD)
    threshold_method = f"第 {PERCENTILE_THRESHOLD} 百分位數 (排除前 {100-PERCENTILE_THRESHOLD}%)"

print(f"\n過濾設定:")
print(f"  基準欄位: {FILTER_COLUMN}")
print(f"  閾值: {threshold:,.0f} ({threshold_method})")
print(f"  刪除整部電影: {'是' if EXCLUDE_WHOLE_MOVIE else '否（僅刪除單筆樣本）'}")

# 找出要排除的樣本
blockbuster_mask = filter_values > threshold

if EXCLUDE_WHOLE_MOVIE:
    # 找出所有要排除的電影 gov_id
    blockbuster_gov_ids = X_test.loc[blockbuster_mask, "gov_id"].unique()
    # 將整部電影的所有樣本標記為要排除
    blockbuster_mask_full = X_test["gov_id"].isin(blockbuster_gov_ids)
    blockbuster_count = blockbuster_mask_full.sum()

    print(f"\n測試集中要排除的電影:")
    print(f"  電影數: {len(blockbuster_gov_ids)} 部")
    print(f"  樣本數: {blockbuster_count} 筆（包含該電影的所有週次）")
    print(f"  gov_id: {sorted(blockbuster_gov_ids.tolist())}")

    # 使用完整的遮罩
    final_mask = ~blockbuster_mask_full
    excluded_gov_ids = blockbuster_gov_ids  # 用於後續儲存
else:
    blockbuster_count = blockbuster_mask.sum()
    blockbuster_gov_ids = X_test.loc[blockbuster_mask, "gov_id"].unique()

    print(f"\n測試集中要排除的樣本:")
    print(f"  樣本數: {blockbuster_count} 筆")
    print(f"  涉及電影: {len(blockbuster_gov_ids)} 部")
    print(f"  gov_id: {sorted(blockbuster_gov_ids.tolist())}")

    final_mask = ~blockbuster_mask
    excluded_gov_ids = blockbuster_gov_ids  # 用於後續儲存

# 過濾測試集
X_test_filtered = X_test[final_mask].copy()
y_test_filtered = y_test[final_mask].copy()

print(f"\n過濾後的測試集:")
print(
    f"  樣本數: {len(X_test_filtered)} 筆 (原始: {len(X_test)}, 減少 {len(X_test) - len(X_test_filtered)} 筆)"
)
print(
    f"  電影數: {len(X_test_filtered['gov_id'].unique())} 部 (原始: {len(X_test['gov_id'].unique())})"
)
print(f"  保留比例: {len(X_test_filtered)/len(X_test)*100:.1f}%")

# ⚠️ 檢查測試集是否太小
if len(X_test_filtered) < 30:
    print(f"\n⚠️ 警告: 測試集樣本數過少 ({len(X_test_filtered)} 筆)，模型評估可能不穩定！")
    print(f"   建議: 調整 PERCENTILE_THRESHOLD 或設定 EXCLUDE_WHOLE_MOVIE = False")
elif len(X_test_filtered) < len(X_test) * 0.3:
    print(f"\n⚠️ 注意: 測試集已減少超過 70%，請留意評估結果的代表性")

# 檢查過濾後的資料分布
print(f"\n過濾後的 {FILTER_COLUMN} 分布:")
if FILTER_COLUMN == "amount":
    print(f"  最小值: {y_test_filtered.min():,.0f}")
    print(f"  最大值: {y_test_filtered.max():,.0f}")
    print(f"  平均值: {y_test_filtered.mean():,.0f}")
    print(f"  中位數: {y_test_filtered.median():,.0f}")
else:
    print(f"  最小值: {X_test_filtered[FILTER_COLUMN].min():,.0f}")
    print(f"  最大值: {X_test_filtered[FILTER_COLUMN].max():,.0f}")
    print(f"  平均值: {X_test_filtered[FILTER_COLUMN].mean():,.0f}")

# 同時保留原始測試集用於對比
X_test_original = X_test.copy()
y_test_original = y_test.copy()


# === 14. 移除 gov_id (只用於分組,不參與訓練) ===
X_train_model = X_train.drop(columns=["gov_id"])
X_test_model_filtered = X_test_filtered.drop(columns=["gov_id"])

print(f"\n模型訓練特徵數: {X_train_model.shape[1]}")


# === 15. 檢查缺失值 ===
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


# === 16. 訓練模型 1: Linear Regression ===
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

print("\n" + "=" * 50)
print("🔵 模型 1: Linear Regression")
print("=" * 50)

lr_model = LinearRegression()
lr_model.fit(X_train_model, y_train)

y_pred_lr = lr_model.predict(X_test_model_filtered)

print(f"MAE:  {mean_absolute_error(y_test_filtered, y_pred_lr):,.0f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test_filtered, y_pred_lr)):,.0f}")
print(f"R²:   {r2_score(y_test_filtered, y_pred_lr):.4f}")


# === 17. 訓練模型 2: LightGBM ===
import lightgbm as lgb

print("\n" + "=" * 50)
print("🟢 模型 2: LightGBM")
print("=" * 50)

lgb_model = lgb.LGBMRegressor(
    n_estimators=100,
    learning_rate=0.05,
    max_depth=5,
    random_state=42,
    verbose=-1,  # 關閉訓練過程輸出
)

lgb_model.fit(X_train_model, y_train)

y_pred_lgb = lgb_model.predict(X_test_model_filtered)

print(f"MAE:  {mean_absolute_error(y_test_filtered, y_pred_lgb):,.0f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test_filtered, y_pred_lgb)):,.0f}")
print(f"R²:   {r2_score(y_test_filtered, y_pred_lgb):.4f}")


# === 18. 訓練模型 3: Decision Tree Regressor ===
from sklearn.tree import DecisionTreeRegressor

print("\n" + "=" * 50)
print("🟡 模型 3: Decision Tree Regressor")
print("=" * 50)

dt_model = DecisionTreeRegressor(
    max_depth=10,
    min_samples_split=20,
    min_samples_leaf=10,
    random_state=42,
)

dt_model.fit(X_train_model, y_train)

y_pred_dt = dt_model.predict(X_test_model_filtered)

print(f"MAE:  {mean_absolute_error(y_test_filtered, y_pred_dt):,.0f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test_filtered, y_pred_dt)):,.0f}")
print(f"R²:   {r2_score(y_test_filtered, y_pred_dt):.4f}")


# ===================================================================
# 洞察模型分析結果
# ===================================================================
# === 19. 特徵重要性分析 ===
print("\n" + "=" * 50)
print("📊 Top 10 重要特徵 (LightGBM)")
print("=" * 50)

feature_importance_lgb = pd.DataFrame(
    {"feature": X_train_model.columns, "importance": lgb_model.feature_importances_}
).sort_values("importance", ascending=False)

print(feature_importance_lgb.head(10).to_string(index=False))

# 存檔特徵重要性
feature_importance_lgb.to_csv(
    output_model_dir / "feature_importance_lgb.csv", index=False, encoding="utf-8-sig"
)
print(f"\n✅ LightGBM特徵重要性已存檔: {output_model_dir / 'feature_importance_lgb.csv'}")

print("\n" + "=" * 50)
print("📊 Top 10 重要特徵 (Decision Tree)")
print("=" * 50)

feature_importance_dt = pd.DataFrame(
    {"feature": X_train_model.columns, "importance": dt_model.feature_importances_}
).sort_values("importance", ascending=False)

print(feature_importance_dt.head(10).to_string(index=False))

feature_importance_dt.to_csv(
    output_model_dir / "feature_importance_dt.csv", index=False, encoding="utf-8-sig"
)
print(f"\n✅ Decision Tree特徵重要性已存檔: {output_model_dir / 'feature_importance_dt.csv'}")


# === 20. 視覺化: 預測 vs 實際 (三模型比較) ===
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]  # 中文字型
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Linear Regression
axes[0].scatter(y_test_filtered, y_pred_lr, alpha=0.5, s=10)
axes[0].plot(
    [y_test_filtered.min(), y_test_filtered.max()],
    [y_test_filtered.min(), y_test_filtered.max()],
    "r--",
    lw=2,
)
axes[0].set_xlabel("實際票房")
axes[0].set_ylabel("預測票房")
axes[0].set_title(f"Linear Regression (R²={r2_score(y_test_filtered, y_pred_lr):.3f})")
axes[0].grid(True, alpha=0.3)

# LightGBM
axes[1].scatter(y_test_filtered, y_pred_lgb, alpha=0.5, s=10, color="green")
axes[1].plot(
    [y_test_filtered.min(), y_test_filtered.max()],
    [y_test_filtered.min(), y_test_filtered.max()],
    "r--",
    lw=2,
)
axes[1].set_xlabel("實際票房")
axes[1].set_ylabel("預測票房")
axes[1].set_title(f"LightGBM (R²={r2_score(y_test_filtered, y_pred_lgb):.3f})")
axes[1].grid(True, alpha=0.3)

# Decision Tree
axes[2].scatter(y_test_filtered, y_pred_dt, alpha=0.5, s=10, color="orange")
axes[2].plot(
    [y_test_filtered.min(), y_test_filtered.max()],
    [y_test_filtered.min(), y_test_filtered.max()],
    "r--",
    lw=2,
)
axes[2].set_xlabel("實際票房")
axes[2].set_ylabel("預測票房")
axes[2].set_title(f"Decision Tree (R²={r2_score(y_test_filtered, y_pred_dt):.3f})")
axes[2].grid(True, alpha=0.3)

plt.suptitle(f"M3 模型比較 (排除票房前 {100-PERCENTILE_THRESHOLD}% 大片)", fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(output_model_dir / "prediction_comparison.png", dpi=150, bbox_inches="tight")
print(f"\n✅ 預測結果圖已存檔: {output_model_dir / 'prediction_comparison.png'}")
plt.show()


# ===================================================================
# 儲存模型與分析結果
# ===================================================================
# === 21. 儲存模型 ===
import joblib

joblib.dump(lr_model, output_model_dir / "model_linear_regression.pkl")
joblib.dump(lgb_model, output_model_dir / "model_lightgbm.pkl")
joblib.dump(dt_model, output_model_dir / "model_decision_tree.pkl")
print(f"\n✅ 模型已存檔:")
print(f"   - {output_model_dir / 'model_linear_regression.pkl'}")
print(f"   - {output_model_dir / 'model_lightgbm.pkl'}")
print(f"   - {output_model_dir / 'model_decision_tree.pkl'}")


# === 22. 儲存測試集預測結果 ===
results = pd.DataFrame(
    {
        "gov_id": X_test_filtered["gov_id"].values,
        "actual": y_test_filtered.values,
        "pred_lr": y_pred_lr,
        "pred_lgb": y_pred_lgb,
        "pred_dt": y_pred_dt,
        "error_lr": y_test_filtered.values - y_pred_lr,
        "error_lgb": y_test_filtered.values - y_pred_lgb,
        "error_dt": y_test_filtered.values - y_pred_dt,
    }
)

results.to_csv(output_model_dir / "test_predictions.csv", index=False, encoding="utf-8-sig")
print(f"✅ 測試集預測結果已存檔: {output_model_dir / 'test_predictions.csv'}")

# 同時儲存被排除的大片資訊
if blockbuster_count > 0:
    # 儲存被排除的樣本資訊
    excluded_mask = X_test_original["gov_id"].isin(excluded_gov_ids)
    blockbuster_info = pd.DataFrame(
        {
            "gov_id": X_test_original.loc[excluded_mask, "gov_id"].values,
            "actual_amount": y_test_original[excluded_mask].values,
        }
    )

    # 按 gov_id 分組統計
    excluded_summary = (
        blockbuster_info.groupby("gov_id")
        .agg({"actual_amount": ["count", "sum", "mean", "max"]})
        .reset_index()
    )
    excluded_summary.columns = ["gov_id", "樣本數", "總票房", "平均票房", "最大票房"]

    blockbuster_info.to_csv(
        output_model_dir / "excluded_samples.csv", index=False, encoding="utf-8-sig"
    )
    excluded_summary.to_csv(
        output_model_dir / "excluded_movies_summary.csv", index=False, encoding="utf-8-sig"
    )
    print(f"✅ 被排除的樣本已存檔: {output_model_dir / 'excluded_samples.csv'}")
    print(f"✅ 被排除的電影統計已存檔: {output_model_dir / 'excluded_movies_summary.csv'}")


# === 23. 模型表現總結 ===
print("\n" + "=" * 60)
print("📊 M3 模型表現總結 (排除大片後)")
print("=" * 60)

summary = pd.DataFrame(
    {
        "模型": ["Linear Regression", "LightGBM", "Decision Tree"],
        "MAE": [
            mean_absolute_error(y_test_filtered, y_pred_lr),
            mean_absolute_error(y_test_filtered, y_pred_lgb),
            mean_absolute_error(y_test_filtered, y_pred_dt),
        ],
        "RMSE": [
            np.sqrt(mean_squared_error(y_test_filtered, y_pred_lr)),
            np.sqrt(mean_squared_error(y_test_filtered, y_pred_lgb)),
            np.sqrt(mean_squared_error(y_test_filtered, y_pred_dt)),
        ],
        "R²": [
            r2_score(y_test_filtered, y_pred_lr),
            r2_score(y_test_filtered, y_pred_lgb),
            r2_score(y_test_filtered, y_pred_dt),
        ],
    }
)

print(summary.to_string(index=False))
summary.to_csv(output_model_dir / "model_summary.csv", index=False, encoding="utf-8-sig")
print(f"\n✅ 模型總結已存檔: {output_model_dir / 'model_summary.csv'}")


# === 24. 紀錄本次執行過程log ===
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
## 📦 M3 最終會產生的檔案
```
data/ML_boxoffice/phase3_prepare/M3_YYYYMMDD_HHMMSS/
├── preprocessed_full.csv           # 完整預處理資料
├── preprocessed_features.csv       # 特徵矩陣 (X)
└── preprocessed_target.csv         # 目標變數 (y)

data/ML_boxoffice/phase4_models/M3_YYYYMMDD_HHMMSS/
├── training_log_YYYYMMDD_HHMMSS.txt  # 訓練日誌
├── feature_importance_lgb.csv      # LightGBM 特徵重要性
├── feature_importance_dt.csv       # Decision Tree 特徵重要性
├── prediction_comparison.png       # 三模型比較圖 (1x3)
├── test_predictions.csv            # 測試集詳細預測結果
├── excluded_blockbusters.csv       # 被排除的大片清單
├── model_summary.csv               # 三模型表現總結
├── model_linear_regression.pkl     # 已訓練的 LR 模型
├── model_lightgbm.pkl              # 已訓練的 LightGBM 模型
└── model_decision_tree.pkl         # 已訓練的 DT 模型
```

## 🎯 M3 的特色
1. **訓練集不變**：使用與 M1/M2 相同的訓練資料
2. **測試集彈性過濾**：可自訂過濾條件
3. **三模型比較**：Linear Regression、LightGBM、Decision Tree
4. **離群值分析**：觀察排除大片後，離群值是否消失

## 🔧 彈性過濾控制

### 1️⃣ 選擇過濾基準欄位
```python
FILTER_COLUMN = "amount"  # 可選: "amount", "boxoffice_week_1", "boxoffice_week_2" 等
```

### 2️⃣ 選擇百分位數閾值（排除「高於」此百分位數的樣本）
```python
PERCENTILE_THRESHOLD = 90  # 排除前 10% (保留後90%)
PERCENTILE_THRESHOLD = 85  # 排除前 15% (保留後85%)
PERCENTILE_THRESHOLD = 95  # 排除前 5%  (保留後95%)
```

### 3️⃣ 是否刪除整部電影
```python
EXCLUDE_WHOLE_MOVIE = True   # 刪除整部電影的所有週次
EXCLUDE_WHOLE_MOVIE = False  # 只刪除符合條件的單筆樣本
```

### 4️⃣ 或使用絕對閾值
```python
ABSOLUTE_THRESHOLD = 10_000_000  # 排除 > 1000萬的樣本（取消註解以使用）
```

## ⚠️ 安全機制
- 自動檢測測試集樣本數，過少時會發出警告
- 顯示詳細的過濾前後統計資訊
- 儲存被排除電影的詳細資訊
"""
