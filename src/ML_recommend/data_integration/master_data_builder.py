# master_data_builder.py

import pandas as pd
import numpy as np
from datetime import datetime
from common.file_utils import ensure_dir

# -----------------------------------------------------
# 1️⃣ 全域設定
# -----------------------------------------------------
TODAY_LABEL = datetime.now().strftime("%Y-%m-%d")

MOVIEINFO_PATH = f"data/processed/movieInfo_gov/combined/movieInfo_gov_full_{TODAY_LABEL}.csv"
BOXOFFICE_PATH = f"data/aggregated/boxoffice/combined/boxoffice_latest_{TODAY_LABEL}.csv"

OUTPUT_MASTER = f"data/master/master_dataset_full_{TODAY_LABEL}.csv"
OUTPUT_M1 = f"data/model/before_train/M1/trainset_M1_{TODAY_LABEL}.csv"
OUTPUT_M2 = f"data/model/before_train/M2/trainset_M2_{TODAY_LABEL}.csv"
OUTPUT_M3 = f"data/model/before_train/M3/trainset_M3_{TODAY_LABEL}.csv"

for p in ["data/master", "data/model/before_train/M1", "data/model/before_train/M2", "data/model/before_train/M3"]:
    ensure_dir(p)

# -----------------------------------------------------
# 2️⃣ 主函式：建立 master dataset
# -----------------------------------------------------
def build_master_dataset():
    print("🚀 開始整合 movieInfo_gov 與 boxoffice_latest ...")

    # 讀取資料
    df_gov = pd.read_csv(MOVIEINFO_PATH)
    df_box = pd.read_csv(BOXOFFICE_PATH)

    # 核心整併
    df = pd.merge(df_box, df_gov, on="gov_id", how="left")

    # -------------------------------------------------
    # 3️⃣ 調整欄位名
    # -------------------------------------------------
    # 3-1. movie_class
    #      將電影分級欄位 rating 改名為 movie_class（避免與評分混淆）
    if "rating" in df.columns:
        df.rename(columns={"rating": "movie_class"}, inplace=True)

    # -------------------------------------------------
    # 4️⃣ 衍生計算欄位
    # -------------------------------------------------
    # 4-1. long_tail_strength
    df["long_tail_strength"] = (1 - df["decline_rate_mean"].abs()) * np.log(df["total_weeks"] + 1)

    # 4-2. retention_index（留存指數）
    df["retention_index"] = (
        (1 - df["decline_rate_mean"].abs()) + (df["active_weeks"] / df["total_weeks"])
    ) / 2

    # 4-3. same_class_amount_last_week
    #      按 region 群組，計算各區平均 avg_amount_per_week，作為市場對照
    df["same_class_amount_last_week"] = (
        df.groupby("region")["avg_amount_per_week"].transform("mean")
    )

    # 4-4. market_heat_level（票房熱度分級）
    #      依 total_amount 分位數分級 → A~E
    quantiles = df["total_amount"].quantile([0.2, 0.4, 0.6, 0.8]).to_dict()
    bins = [-np.inf, quantiles[0.2], quantiles[0.4], quantiles[0.6], quantiles[0.8], np.inf]
    labels = ["E", "D", "C", "B", "A"]
    df["market_heat_level"] = pd.cut(df["total_amount"], bins=bins, labels=labels)

    # -------------------------------------------------
    # 5️⃣ 儲存 master dataset
    # -------------------------------------------------
    df.to_csv(OUTPUT_MASTER, index=False, encoding="utf-8-sig")
    print(f"✅ 已輸出 master dataset：{OUTPUT_MASTER}")

    return df

# -----------------------------------------------------
# 6️⃣ 建立各模型訓練資料集
# -----------------------------------------------------
def build_trainset_M1(master_df: pd.DataFrame):
    features = [
        "gov_id", "title_zh", "total_amount", "avg_amount_per_week", "decline_rate_mean",
        "decline_rate_last", "peak_amount", "avg_theater_count", "peak_theater_count",
        "total_weeks", "momentum_score", "second_week_amount_growth_rate", "momentum_3w",
        "region", "movie_class", "film_length", "publisher", "same_class_amount_last_week"
    ]
    master_df[features].to_csv(OUTPUT_M1, index=False, encoding="utf-8-sig")
    print(f"✅ 已輸出 M1 訓練集：{OUTPUT_M1}")

def build_trainset_M2(master_df: pd.DataFrame):
    features = [
        "gov_id", "title_zh", "total_amount", "avg_amount_per_week", "decline_rate_mean",
        "is_long_tail", "release_days", "release_round", "previous_total_amount",
        "re_release_gap_days", "long_tail_strength", "region", "movie_class", "publisher"
    ]
    master_df[features].to_csv(OUTPUT_M2, index=False, encoding="utf-8-sig")
    print(f"✅ 已輸出 M2 訓練集：{OUTPUT_M2}")

def build_trainset_M3(master_df: pd.DataFrame):
    features = [
        "gov_id", "title_zh", "momentum_score", "momentum_3w", "second_week_amount_growth_rate",
        "retention_index", "decline_rate_mean", "active_weeks", "is_long_tail",
        "avg_theater_count", "peak_theater_count", "total_weeks",
        "total_amount", "avg_amount_per_week", "market_heat_level",
        "region", "movie_class"
    ]
    master_df[features].to_csv(OUTPUT_M3, index=False, encoding="utf-8-sig")
    print(f"✅ 已輸出 M3 訓練集：{OUTPUT_M3}")

# -----------------------------------------------------
# 7️⃣ 主程式執行區
# -----------------------------------------------------
if __name__ == "__main__":
    df_master = build_master_dataset()
    build_trainset_M1(df_master)
    build_trainset_M2(df_master)
    build_trainset_M3(df_master)
    print("🎉 全部 master 與模型訓練資料生成完成！")
