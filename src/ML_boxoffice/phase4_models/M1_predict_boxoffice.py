import pandas as pd
import numpy as np
import sys
from pathlib import Path
from io import StringIO
from datetime import datetime

# ===================================================================
# 日誌系統設定
# ===================================================================
# 建立 log 檔案路徑
output_model_dir = Path("data/ML_boxoffice/phase4_models/M1")
output_model_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = output_model_dir / f"training_log_{timestamp}.txt"

# 建立 log 緩衝區
log_buffer = StringIO()


# 建立自訂的 print 函數,同時輸出到終端機和 log
class Logger:
    def __init__(self, log_buffer):
        self.terminal = sys.stdout
        self.log = log_buffer

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()


# 重定向 stdout
sys.stdout = Logger(log_buffer)

print("=" * 60)
print(f"🚀 模型訓練開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)


# ===================================================================
# 資料預處理
# ===================================================================
# === 設定路徑 ===
output_prepare_dir = Path("data/ML_boxoffice/phase3_prepare/M1")
output_model_dir = Path("data/ML_boxoffice/phase4_models/M1")
output_prepare_dir.mkdir(parents=True, exist_ok=True)

# === 1. 讀取資料 ===
df = pd.read_csv(
    "data/ML_boxoffice/phase2_features/with_market/features_market_2025-11-07.csv"
)  # 替換成你的檔案路徑


# === 2. 篩選資料 ===
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
print(f"篩選後資料筆數: {len(df)}")


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
print(f"   欄位數: {len(df.columns)}")
print(f"   資料筆數: {len(df)}")


# === 7. 顯示最終欄位 ===
print("\n=== 最終欄位清單 ===")
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
print("\n=== 資料摘要 ===")
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

print(f"\n訓練集: {len(X_train)} 筆 ({len(X_train['gov_id'].unique())} 部電影)")
print(f"測試集: {len(X_test)} 筆 ({len(X_test['gov_id'].unique())} 部電影)")


# === 13. 移除 gov_id (只用於分組,不參與訓練) ===
X_train_model = X_train.drop(columns=["gov_id"])
X_test_model = X_test.drop(columns=["gov_id"])

print(f"\n模型訓練特徵數: {X_train_model.shape[1]}")


# === 13.5 檢查缺失值 ===
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


# === 14. 訓練基準模型: Linear Regression ===
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

print("\n" + "=" * 50)
print("🔵 模型 1: Linear Regression")
print("=" * 50)

lr_model = LinearRegression()
lr_model.fit(X_train_model, y_train)

y_pred_lr = lr_model.predict(X_test_model)

print(f"MAE:  {mean_absolute_error(y_test, y_pred_lr):,.0f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_lr)):,.0f}")
print(f"R²:   {r2_score(y_test, y_pred_lr):.4f}")


# === 15. 訓練進階模型: LightGBM ===
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

y_pred_lgb = lgb_model.predict(X_test_model)

print(f"MAE:  {mean_absolute_error(y_test, y_pred_lgb):,.0f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_lgb)):,.0f}")
print(f"R²:   {r2_score(y_test, y_pred_lgb):.4f}")


# ===================================================================
# 洞察模型分析結果
# ===================================================================
# === 16. 特徵重要性分析 ===
print("\n" + "=" * 50)
print("📊 Top 10 重要特徵 (LightGBM)")
print("=" * 50)

feature_importance = pd.DataFrame(
    {"feature": X_train_model.columns, "importance": lgb_model.feature_importances_}
).sort_values("importance", ascending=False)

print(feature_importance.head(10).to_string(index=False))

# 存檔特徵重要性
feature_importance.to_csv(
    output_model_dir / "feature_importance.csv", index=False, encoding="utf-8-sig"
)
print(f"\n✅ 特徵重要性已存檔: {output_model_dir / 'feature_importance.csv'}")


# === 17. 視覺化: 預測 vs 實際 ===
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]  # 中文字型
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Linear Regression
axes[0].scatter(y_test, y_pred_lr, alpha=0.5, s=10)
axes[0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--", lw=2)
axes[0].set_xlabel("實際票房")
axes[0].set_ylabel("預測票房")
axes[0].set_title(f"Linear Regression (R²={r2_score(y_test, y_pred_lr):.3f})")
axes[0].grid(True, alpha=0.3)

# LightGBM
axes[1].scatter(y_test, y_pred_lgb, alpha=0.5, s=10)
axes[1].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--", lw=2)
axes[1].set_xlabel("實際票房")
axes[1].set_ylabel("預測票房")
axes[1].set_title(f"LightGBM (R²={r2_score(y_test, y_pred_lgb):.3f})")
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_model_dir / "prediction_comparison.png", dpi=150, bbox_inches="tight")
print(f"✅ 預測結果圖已存檔: {output_model_dir / 'prediction_comparison.png'}")
plt.show()


# ===================================================================
# 儲存模型與分析結果
# ===================================================================
# === 18. 儲存模型 ===
import joblib

joblib.dump(lr_model, output_model_dir / "model_linear_regression.pkl")
joblib.dump(lgb_model, output_model_dir / "model_lightgbm.pkl")
print(f"\n✅ 模型已存檔:")
print(f"   - {output_model_dir / 'model_linear_regression.pkl'}")
print(f"   - {output_model_dir / 'model_lightgbm.pkl'}")


# === 19. 儲存測試集預測結果 ===
results = pd.DataFrame(
    {
        "gov_id": X_test["gov_id"].values,
        "actual": y_test.values,
        "pred_lr": y_pred_lr,
        "pred_lgb": y_pred_lgb,
        "error_lr": y_test.values - y_pred_lr,
        "error_lgb": y_test.values - y_pred_lgb,
    }
)

results.to_csv(output_model_dir / "test_predictions.csv", index=False, encoding="utf-8-sig")
print(f"✅ 測試集預測結果已存檔: {output_model_dir / 'test_predictions.csv'}")


# === 20. 紀錄本次執行過程log ===
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
data/ML_boxoffice/phase3_prepare/
├── preprocessed_full.csv           # 完整預處理資料
├── preprocessed_features.csv       # 特徵矩陣 (X)
├── preprocessed_target.csv         # 目標變數 (y)
├── feature_importance.csv          # 特徵重要性排名
├── prediction_comparison.png       # 預測 vs 實際散佈圖
├── test_predictions.csv            # 測試集詳細預測結果
├── model_linear_regression.pkl     # 已訓練的 LR 模型
└── model_lightgbm.pkl              # 已訓練的 LightGBM 模型
"""
