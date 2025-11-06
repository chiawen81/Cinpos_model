import pandas as pd
import numpy as np

drop_columns = [
    # 資料洩漏
    "amount",
    "tickets",
    "theater_count",
    # 不需要的時間資訊
    "official_release_date",
    "week_range",
    "current_week_real_idx",  # 有 active_idx 就夠了
    # 跨輪累積 (預測首輪時不需要)
    "boxoffice_cumsum",
    "audience_cumsum",
    "boxoffice_round1_cumsum",
    "audience_round1_cumsum",
    "rounds_cumsum",
    # 問題欄位
    "ticket_price_avg_current",
    # 分類欄位 (時間有限先刪除)
    "region",
    "publisher",
]

# 1. 讀取資料
df = pd.read_csv("data\ML_boxoffice\phase2_features\with_market\features_market_2025-11-07.csv")

# 2. 篩選首輪 + 活躍週次
df = df[df["round_idx"] == 1].copy()
df = df[df["current_week_active_idx"].notna()]

# 3. 刪除前兩週都無票房的 row
df = df[(df["boxoffice_week_1"] > 0) | (df["boxoffice_week_2"] > 0)]

# 4. 月份週期性編碼
df["release_month_sin"] = np.sin(2 * np.pi * df["release_month"] / 12)
df["release_month_cos"] = np.cos(2 * np.pi * df["release_month"] / 12)

# 5. 刪除不需要的欄位
df = df.drop(columns=drop_columns + ["release_month"])

# 6. 檢查缺失值
print(df.isnull().sum())

# 7. 分離特徵與目標 (保留 gov_id 用於分組)
target = "amount"  # 注意: 需要先從原始資料取出 amount 再刪除
y = df[target]
X = df.drop(columns=[target])

# 8. Group-based 切分 (確保同一部電影的資料不會同時出現在訓練/測試集)
from sklearn.model_selection import GroupShuffleSplit

splitter = GroupShuffleSplit(test_size=0.2, n_splits=1, random_state=42)
train_idx, test_idx = next(splitter.split(X, y, groups=X["gov_id"]))

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

# 9. 訓練時移除 gov_id (只用於分組，不參與模型訓練)
X_train_model = X_train.drop(columns=["gov_id"])
X_test_model = X_test.drop(columns=["gov_id"])

# 10. 訓練模型
import lightgbm as lgb

model = lgb.LGBMRegressor(random_state=42)
model.fit(X_train_model, y_train)

# 11. 評估
from sklearn.metrics import mean_absolute_error, r2_score

y_pred = model.predict(X_test_model)
print(f"MAE: {mean_absolute_error(y_test, y_pred)}")
print(f"R²: {r2_score(y_test, y_pred)}")
