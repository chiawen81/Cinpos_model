import joblib
import pandas as pd
from pathlib import Path
import numpy as np

# === 載入模型 ===
model_path = Path(
    "data\ML_boxoffice\phase4_models\M1\M1_20251110_015910\model_linear_regression.pkl"
)
model, feature_names = joblib.load(model_path)

print(f"✅ 已載入模型: {model_path}")

# === 輸入要預測的資料 ===
print("\n請輸入電影資訊:")
new_movie = {
    "round_idx": 1,
    "current_week_active_idx": int(input("要預測第幾週: ")),
    "boxoffice_week_1": float(input("上週票房: ")),
    "boxoffice_week_2": float(input("兩週前票房: ")),
    "audience_week_1": float(input("上週觀影人數: ")),
    "audience_week_2": float(input("兩週前觀影人數: ")),
    "screens_week_1": int(input("上週院線數: ")),
    "screens_week_2": int(input("兩週前院線數: ")),
    "open_week1_boxoffice": float(input("首週票房: ")),
    "open_week1_boxoffice_daily_avg": float(input("首週日均票房: ")),
    "film_length": int(input("片長(分鐘): ")),
    "is_restricted": int(input("是否限制級(0/1): ")),
    "gap_real_week_2to1": 0,
    "gap_real_week_1tocurrent": 0,
    "open_week1_days": float(input("首周放映天數: ")),
    "open_week2_boxoffice": float(input("上映第二周的票房: ")),
    "release_year": float(input("上映年份: ")),
    "release_month": float(input("上映月份: ")),
}

new_movie["release_month_sin"] = np.sin(2 * np.pi * new_movie["release_month"] / 12)
new_movie["release_month_cos"] = np.cos(2 * np.pi * new_movie["release_month"] / 12)

# === 預測 ===
X_new = pd.DataFrame([new_movie])

# 使用模型內建的欄位順序 feature_order
X_new = X_new[feature_names]

# 預測
prediction = model.predict(X_new)[0]

print(f"\n🎬 預測結果:")
print(f"第 {new_movie['current_week_active_idx']} 週票房: {prediction:,.0f} 元")
