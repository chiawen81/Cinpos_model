# 修正版：src/ML_trend/round_and_week_processor.py

import pandas as pd
import numpy as np
from pathlib import Path
import glob


def process_rounds_and_weeks():
    """
    步驟1：處理輪次定義、真實週次、活躍週次 + 近期趨勢
    """

    print("🚀 開始處理輪次與週次...")

    # === 1. 讀取所有電影的週資料 ===
    boxoffice_dir = Path("data/processed/boxoffice_permovie")
    all_files = list(boxoffice_dir.glob("*.csv"))

    print(f"📁 找到 {len(all_files)} 部電影")

    all_data = []
    for file in all_files:
        try:
            df = pd.read_csv(file)
            df["gov_id"] = file.stem.split("_")[0]
            all_data.append(df)
        except Exception as e:
            print(f"⚠️ 跳過 {file.name}: {e}")

    df_all = pd.concat(all_data, ignore_index=True)
    print(f"✅ 載入完成：{len(df_all):,} 筆週資料")

    # === 2. 基本清理與排序 ===
    df_all["amount"] = pd.to_numeric(df_all["amount"], errors="coerce").fillna(0)
    df_all["tickets"] = pd.to_numeric(df_all["tickets"], errors="coerce").fillna(0)
    df_all["theater_count"] = pd.to_numeric(df_all["theater_count"], errors="coerce").fillna(0)
    df_all = df_all.sort_values(["gov_id", "week_range"]).reset_index(drop=True)

    print(f"📊 清理後：{len(df_all):,} 筆")

    # === 3. 定義輪次 ===
    print("\n🔄 定義輪次...")

    result_list = []

    for gov_id in df_all["gov_id"].unique():
        movie_df = df_all[df_all["gov_id"] == gov_id].copy().reset_index(drop=True)

        # 保存原始索引（用於計算跳週）
        movie_df["original_real_idx"] = range(1, len(movie_df) + 1)

        # 計算連續零週次
        movie_df["is_zero"] = (movie_df["amount"] == 0).astype(int)

        zero_streak = 0
        zero_streaks = []
        for is_zero in movie_df["is_zero"]:
            if is_zero:
                zero_streak += 1
            else:
                zero_streak = 0
            zero_streaks.append(zero_streak)

        movie_df["zero_streak"] = zero_streaks

        # 輪次結束判斷（連續3週=0）
        movie_df["round_end"] = (movie_df["zero_streak"] >= 3).astype(int)
        movie_df["round_end_shifted"] = movie_df["round_end"].shift(1).fillna(0)

        # 輪次編號
        round_idx = 1
        round_indices = []
        for i, row in movie_df.iterrows():
            round_indices.append(round_idx)
            if row["round_end_shifted"] == 1:
                round_idx += 1

        movie_df["round_idx"] = round_indices

        # === 4. 計算真實週次（當輪內連續編號）===
        movie_df["current_week_real_idx"] = movie_df.groupby("round_idx").cumcount() + 1

        # === 5. 過濾：輪次真實週次 < 3 的整輪刪除 ===
        round_weeks = movie_df.groupby("round_idx")["current_week_real_idx"].max()
        valid_rounds = round_weeks[round_weeks >= 3].index.tolist()

        movie_df = movie_df[movie_df["round_idx"].isin(valid_rounds)].copy()

        if len(movie_df) == 0:
            continue

        # === 6. 刪除票房=0的row ===
        movie_df = movie_df[movie_df["amount"] > 0].copy()

        if len(movie_df) == 0:
            continue

        # === 7. 重新編號輪次（刪除後可能有空號）===
        round_mapping = {
            old: new for new, old in enumerate(sorted(movie_df["round_idx"].unique()), 1)
        }
        movie_df["round_idx"] = movie_df["round_idx"].map(round_mapping)

        # === 8. 重新計算活躍週次（去除0後重編）===
        movie_df["current_week_active_idx"] = movie_df.groupby("round_idx").cumcount() + 1

        # === 9. 計算累計輪次 ===
        movie_df["rounds_cumsum"] = movie_df["round_idx"]

        # === 10. 計算跳週數 ===
        movie_df["prev1_real_idx"] = movie_df.groupby("round_idx")["original_real_idx"].shift(1)
        movie_df["prev2_real_idx"] = movie_df.groupby("round_idx")["original_real_idx"].shift(2)

        movie_df["gap_real_week_1tocurrent"] = (
            (movie_df["original_real_idx"] - movie_df["prev1_real_idx"] - 1).fillna(0).astype(int)
        )
        movie_df["gap_real_week_2to1"] = (
            (movie_df["prev1_real_idx"] - movie_df["prev2_real_idx"] - 1).fillna(0).astype(int)
        )

        movie_df.loc[movie_df["current_week_active_idx"] == 1, "gap_real_week_1tocurrent"] = 0
        movie_df.loc[movie_df["current_week_active_idx"] == 1, "gap_real_week_2to1"] = 0
        movie_df.loc[movie_df["current_week_active_idx"] == 2, "gap_real_week_2to1"] = 0

        # === 11. 【新增】近期趨勢 Lag Features ===
        # 按輪次分組，取前1週和前2週的資料
        movie_df["boxoffice_week_1"] = movie_df.groupby("round_idx")["amount"].shift(1)
        movie_df["boxoffice_week_2"] = movie_df.groupby("round_idx")["amount"].shift(2)

        movie_df["audience_week_1"] = movie_df.groupby("round_idx")["tickets"].shift(1)
        movie_df["audience_week_2"] = movie_df.groupby("round_idx")["tickets"].shift(2)

        movie_df["screens_week_1"] = movie_df.groupby("round_idx")["theater_count"].shift(1)
        movie_df["screens_week_2"] = movie_df.groupby("round_idx")["theater_count"].shift(2)

        result_list.append(movie_df)

    if len(result_list) == 0:
        print("⚠️ 沒有符合條件的資料！")
        return pd.DataFrame()

    # === 12. 合併所有電影 ===
    result = pd.concat(result_list, ignore_index=True)

    # === 13. 選擇欄位 ===
    key_columns = [
        # 基本資訊
        "gov_id",
        "official_release_date",
        "week_range",
        # 輪次與週次
        "round_idx",
        "rounds_cumsum",
        "current_week_real_idx",
        "current_week_active_idx",
        "gap_real_week_2to1",
        "gap_real_week_1tocurrent",
        # 近期趨勢（活躍週）
        "boxoffice_week_2",
        "boxoffice_week_1",
        "audience_week_2",
        "audience_week_1",
        "screens_week_2",
        "screens_week_1",
        # 當週資料（目標變數）
        "amount",
        "tickets",
        "theater_count",
    ]

    result = result[key_columns].copy()

    # === 14. 儲存 ===
    output_path = Path("data/model/step1_rounds_weeks_trends.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, encoding="utf-8-sig")

    # === 15. 統計報告 ===
    print("\n" + "=" * 70)
    print("✅ 步驟1完成：輪次、週次 + 近期趨勢")
    print("=" * 70)
    print(f"📄 檔案位置：{output_path}")
    print(f"📊 總樣本數：{len(result):,}")
    print(f"🎬 電影數量：{result['gov_id'].nunique()}")
    print(f"🔄 總輪次數：{result.groupby('gov_id')['round_idx'].max().sum():.0f}")

    # 統計每部電影的輪次數
    rounds_per_movie = result.groupby("gov_id")["round_idx"].max()
    print(f"\n📈 輪次分布：")
    print(f"   ├─ 單輪電影：{(rounds_per_movie == 1).sum()} 部")
    print(f"   ├─ 雙輪電影：{(rounds_per_movie == 2).sum()} 部")
    print(f"   └─ 三輪以上：{(rounds_per_movie >= 3).sum()} 部")

    # 活躍週次分布
    active_weeks = result.groupby(["gov_id", "round_idx"])["current_week_active_idx"].max()
    print(f"\n📊 活躍週次分布（每輪）：")
    print(f"   ├─ 最小：{active_weeks.min():.0f} 週")
    print(f"   ├─ 平均：{active_weeks.mean():.1f} 週")
    print(f"   ├─ 中位數：{active_weeks.median():.0f} 週")
    print(f"   └─ 最大：{active_weeks.max():.0f} 週")

    # 跳週情況
    gaps = result["gap_real_week_1tocurrent"]
    print(f"\n🔀 跳週情況（week-1 到 current）：")
    print(f"   ├─ 無跳週（=0）：{(gaps == 0).sum()} 次 ({(gaps == 0).sum()/len(gaps)*100:.1f}%)")
    print(f"   ├─ 跳1週（=1）：{(gaps == 1).sum()} 次 ({(gaps == 1).sum()/len(gaps)*100:.1f}%)")
    print(f"   ├─ 跳2週（=2）：{(gaps == 2).sum()} 次 ({(gaps == 2).sum()/len(gaps)*100:.1f}%)")
    print(f"   └─ 跳3週以上：{(gaps > 2).sum()} 次 ({(gaps > 2).sum()/len(gaps)*100:.1f}%)")

    # === 16. Lag Features 有效性 ===
    print(f"\n📊 近期趨勢欄位有效性：")
    print(
        f"   ├─ boxoffice_week_1 有值：{result['boxoffice_week_1'].notna().sum():,} ({result['boxoffice_week_1'].notna().sum()/len(result)*100:.1f}%)"
    )
    print(
        f"   ├─ boxoffice_week_2 有值：{result['boxoffice_week_2'].notna().sum():,} ({result['boxoffice_week_2'].notna().sum()/len(result)*100:.1f}%)"
    )
    print(
        f"   └─ 同時有 week_1 & week_2：{(result['boxoffice_week_1'].notna() & result['boxoffice_week_2'].notna()).sum():,}"
    )

    print("\n📋 資料預覽（含近期趨勢）：")
    preview_cols = [
        "gov_id",
        "week_range",
        "round_idx",
        "current_week_active_idx",
        "boxoffice_week_2",
        "boxoffice_week_1",
        "amount",
        "audience_week_2",
        "audience_week_1",
        "tickets",
    ]
    print(result[preview_cols].head(15).to_string(index=False))

    # === 17. 驗證範例 ===
    print("\n" + "=" * 70)
    print("🔍 驗證範例（檢查近期趨勢是否正確）")
    print("=" * 70)

    # 選一部有多輪的電影
    multi_round_movies = result.groupby("gov_id")["round_idx"].max()
    multi_round_movies = multi_round_movies[multi_round_movies > 1].index

    if len(multi_round_movies) > 0:
        sample_movie = multi_round_movies[0]
        sample_df = result[result["gov_id"] == sample_movie].copy()

        print(f"\n範例電影：{sample_movie}")
        display_cols = [
            "week_range",
            "round_idx",
            "current_week_active_idx",
            "boxoffice_week_2",
            "boxoffice_week_1",
            "amount",
        ]
        print(sample_df[display_cols].to_string(index=False))

    return result


if __name__ == "__main__":
    df = process_rounds_and_weeks()
