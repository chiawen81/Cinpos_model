# 修正版：src/ML_trend/round_and_week_processor.py

import pandas as pd
import numpy as np
from pathlib import Path
import glob
from datetime import datetime, timedelta


def process_rounds_and_weeks():
    """
    步驟1：處理輪次定義、真實週次、活躍週次 + 近期趨勢 + 開片實力
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

        # === 11. 近期趨勢 Lag Features ===
        movie_df["boxoffice_week_1"] = movie_df.groupby("round_idx")["amount"].shift(1)
        movie_df["boxoffice_week_2"] = movie_df.groupby("round_idx")["amount"].shift(2)

        movie_df["audience_week_1"] = movie_df.groupby("round_idx")["tickets"].shift(1)
        movie_df["audience_week_2"] = movie_df.groupby("round_idx")["tickets"].shift(2)

        movie_df["screens_week_1"] = movie_df.groupby("round_idx")["theater_count"].shift(1)
        movie_df["screens_week_2"] = movie_df.groupby("round_idx")["theater_count"].shift(2)

        # === 12. 【新增】開片實力（首輪）===
        # 只計算首輪（round_idx == 1）的資料
        first_round = movie_df[movie_df["round_idx"] == 1].copy()

        if len(first_round) > 0:
            # 12.1 首輪第1週資料
            first_week = first_round.iloc[0]

            # 解析日期
            try:
                # 上映日期
                release_date_str = first_week["official_release_date"]
                # 嘗試多種日期格式
                for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y/%m/%d"]:
                    try:
                        release_date = datetime.strptime(release_date_str, fmt)
                        break
                    except:
                        continue

                # 首週區間
                week_range = first_week["week_range"]
                week_end_str = week_range.split("~")[1]  # 取結束日期
                week_end = datetime.strptime(week_end_str, "%Y-%m-%d")

                # 計算首週上映天數（從上映日到該週結束）
                open_week1_days = (week_end - release_date).days + 1

                # 確保天數在合理範圍 (1-7天)
                open_week1_days = max(1, min(7, open_week1_days))

            except Exception as e:
                print(f"⚠️ 電影 {gov_id} 日期解析失敗: {e}")
                open_week1_days = 7  # 預設7天

            # 12.2 首週票房
            open_week1_boxoffice = first_week["amount"]

            # 12.3 首週日均票房
            open_week1_boxoffice_daily_avg = (
                open_week1_boxoffice / open_week1_days if open_week1_days > 0 else 0
            )

            # 12.4 首輪第2週票房（如果有的話）
            if len(first_round) >= 2:
                open_week2_boxoffice = first_round.iloc[1]["amount"]
            else:
                open_week2_boxoffice = np.nan

            # 對整部電影的所有row填入這些固定值
            movie_df["open_week1_days"] = open_week1_days
            movie_df["open_week1_boxoffice"] = open_week1_boxoffice
            movie_df["open_week1_boxoffice_daily_avg"] = open_week1_boxoffice_daily_avg
            movie_df["open_week2_boxoffice"] = open_week2_boxoffice
        else:
            # 如果沒有首輪資料，填入NaN
            movie_df["open_week1_days"] = np.nan
            movie_df["open_week1_boxoffice"] = np.nan
            movie_df["open_week1_boxoffice_daily_avg"] = np.nan
            movie_df["open_week2_boxoffice"] = np.nan

        result_list.append(movie_df)

    if len(result_list) == 0:
        print("⚠️ 沒有符合條件的資料！")
        return pd.DataFrame()

    # === 13. 合併所有電影 ===
    result = pd.concat(result_list, ignore_index=True)

    # === 14. 選擇欄位 ===
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
        # 開片實力（首輪）
        "open_week1_days",
        "open_week1_boxoffice",
        "open_week1_boxoffice_daily_avg",
        "open_week2_boxoffice",
        # 當週資料（目標變數）
        "amount",
        "tickets",
        "theater_count",
    ]

    result = result[key_columns].copy()

    # === 15. 儲存 ===
    output_path = Path("data/model/step1_rounds_weeks_trends_opening.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, encoding="utf-8-sig")

    # === 16. 統計報告 ===
    print("\n" + "=" * 70)
    print("✅ 步驟1完成：輪次、週次 + 近期趨勢 + 開片實力")
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

    # 開片實力統計
    print(f"\n🎬 開片實力統計（首輪第1週）：")
    open_days = result.groupby("gov_id")["open_week1_days"].first()
    print(f"   ├─ 平均上映天數：{open_days.mean():.1f} 天")
    print(f"   ├─ 上映天數分布：")
    for days in sorted(open_days.unique()):
        count = (open_days == days).sum()
        print(f"   │  ├─ {days}天：{count} 部 ({count/len(open_days)*100:.1f}%)")

    open_bo = result.groupby("gov_id")["open_week1_boxoffice"].first()
    print(f"   ├─ 首週票房中位數：{open_bo.median():,.0f} 元")
    print(f"   └─ 首週票房平均：{open_bo.mean():,.0f} 元")

    open_daily = result.groupby("gov_id")["open_week1_boxoffice_daily_avg"].first()
    print(f"\n💰 日均票房統計：")
    print(f"   ├─ 中位數：{open_daily.median():,.0f} 元/天")
    print(f"   └─ 平均：{open_daily.mean():,.0f} 元/天")

    # Lag Features 有效性
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

    print("\n📋 資料預覽（含開片實力）：")
    preview_cols = [
        "gov_id",
        "week_range",
        "round_idx",
        "current_week_active_idx",
        "open_week1_days",
        "open_week1_boxoffice",
        "open_week1_boxoffice_daily_avg",
        "boxoffice_week_1",
        "amount",
    ]
    print(result[preview_cols].head(15).to_string(index=False))

    # === 17. 驗證範例 ===
    print("\n" + "=" * 70)
    print("🔍 驗證範例：13460（檢查開片實力）")
    print("=" * 70)

    sample_df = result[result["gov_id"] == "13460"].head(5)
    if len(sample_df) > 0:
        display_cols = [
            "official_release_date",
            "week_range",
            "round_idx",
            "open_week1_days",
            "open_week1_boxoffice",
            "open_week1_boxoffice_daily_avg",
            "open_week2_boxoffice",
        ]
        print(sample_df[display_cols].to_string(index=False))

    return result


if __name__ == "__main__":
    df = process_rounds_and_weeks()
