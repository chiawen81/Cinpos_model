"""
票房資料時序拉平模組（輪次定義 + 週次編碼 + 基礎特徵）
---------------------------------------------------------------
🎯 模組目標：
    將 data/processed/boxoffice_permovie 下的逐週票房資料，
    拉平為時間序列格式（每 row = 一週），並完成輪次定義、週次編碼、
    基礎特徵工程，作為後續特徵工程與模型訓練的基礎。

📦 輸出內容：
    時序資料檔（每部電影每週一筆資料）
    - 包含輪次編號、真實週次、活躍週次
    - 包含 lag features（前1週、前2週的票房/觀眾/院線數）
    - 包含開片實力指標（首週票房、日均票房等）

🧩 本次拉平的主要資料轉換邏輯：

    1. 正式上映日過濾：
        - 僅保留週次結束日 >= 官方上映日 (official_release_date) 的資料
        - 避免試映場或宣傳場影響統計

    2. 輪次定義（容忍中斷）：
        - 連續 3 週票房 = 0 視為輪次結束
        - 輪次內允許最多連續 2 週票房 = 0（這些週次保留但不計入活躍週次）
        - 不屬於任何輪次的 row（連續第 3 週以上票房 = 0）→ 刪除

    3. 輪次成立條件：
        - 真實週次（含輪內票房 = 0 的週次）≥ 3 週
        - 活躍週次（僅計票房 > 0 的週次）≥ 3 週
        - 輪次最後一週必須有票房（末尾連續票房 = 0 的週次會被移除）

    4. 週次編號：
        - 真實週次 (current_week_real_idx): 輪內連續編號（含票房 = 0）
        - 活躍週次 (current_week_active_idx): 僅對票房 > 0 的週次編號
        - 跳週數 (gap_real_week_*): 基於活躍週次計算，跳過的真實週次數量

    5. Lag Features（近期趨勢）：
        - 基於活躍週次計算前 1 週、前 2 週的票房/觀眾/院線數
        - 用於捕捉票房趨勢與變化模式

    6. 開片實力（首輪固定值）：
        - 首輪第 1 週上映天數、票房、日均票房
        - 首輪第 2 週票房
        - 每部電影的所有 row 都是相同值（反映市場接受度）

    7. 資料過濾順序（重要！）：
        Step 1: 過濾上映日之前的週次
        Step 2: 定義輪次（標記哪些 row 屬於哪一輪）
        Step 3: 刪除不屬於任何輪次的 row
        Step 4: 過濾真實週次 < 3 的輪次
        Step 5: 移除每輪末尾票房 = 0 的週次
        Step 6: 過濾活躍週次 < 3 的輪次
        Step 7: 重新編號輪次為連續的 1, 2, 3...

📂 輸入位置：
    - data/processed/boxoffice_permovie/*.csv

📂 輸出位置：
    - data/ML_boxoffice/phase1_flattened/boxoffice_timeseries_<日期>.csv

📊 輸出欄位結構：
    基本資訊:
        - gov_id, official_release_date, week_range

    輪次與週次:
        - round_idx, rounds_cumsum
        - current_week_real_idx, current_week_active_idx
        - gap_real_week_2to1, gap_real_week_1tocurrent

    近期趨勢（Lag Features）:
        - boxoffice_week_2, boxoffice_week_1
        - audience_week_2, audience_week_1
        - screens_week_2, screens_week_1

    開片實力（首輪）:
        - open_week1_days, open_week1_boxoffice
        - open_week1_boxoffice_daily_avg, open_week2_boxoffice

    當週資料（目標變數）:
        - amount, tickets, theater_count

🔗 下游模組：
    - phase2_features/add_pr_features.py: 加入 PR 特徵
    - phase2_features/add_cumulative_features.py: 加入累積特徵
    - phase3_prepare/build_training_data.py: 組合最終訓練資料
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# 加入共用模組路徑
sys.path.append(str(Path(__file__).parent.parent.parent))
from ml.common.file_utils import ensure_dir, save_csv


def generate_data_quality_report(df, output_path):
    """
    生成資料品質報告

    報告內容：
    1. 前三周票房為0的資料數、電影數（列出電影編號）
    2. 各特徵欄位的離群值
    3. 缺失值比例

    Parameters:
        df: 處理後的時序資料
        output_path: 報告輸出路徑
    """
    report_lines = []
    report_lines.append("="*70)
    report_lines.append("資料品質報告")
    report_lines.append("="*70)
    report_lines.append(f"生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"總樣本數：{len(df):,}")
    report_lines.append(f"電影數量：{df['gov_id'].nunique()}")
    report_lines.append("")

    # === 1. 前三周票房為0的資料 ===
    report_lines.append("="*70)
    report_lines.append("1. 前三周票房為0的資料")
    report_lines.append("="*70)

    # 找出每部電影每一輪的前三週
    early_weeks_zero = []
    early_weeks_zero_movies = set()

    for gov_id in df['gov_id'].unique():
        movie_df = df[df['gov_id'] == gov_id]
        for round_idx in movie_df['round_idx'].unique():
            round_df = movie_df[movie_df['round_idx'] == round_idx].copy()
            round_df = round_df.sort_values('current_week_real_idx')

            # 取前三週（根據 real_idx）
            first_three = round_df[round_df['current_week_real_idx'] <= 3]
            zero_weeks = first_three[first_three['amount'] == 0]

            if len(zero_weeks) > 0:
                early_weeks_zero.extend(zero_weeks.index.tolist())
                early_weeks_zero_movies.add(gov_id)

    report_lines.append(f"前三周票房為0的資料筆數：{len(early_weeks_zero)} 筆")
    report_lines.append(f"涉及電影數量：{len(early_weeks_zero_movies)} 部")

    if early_weeks_zero_movies:
        report_lines.append("\n涉及的電影編號：")
        movie_list = sorted(list(early_weeks_zero_movies))
        # 每行顯示5個電影ID
        for i in range(0, len(movie_list), 5):
            line_movies = movie_list[i:i+5]
            report_lines.append("  " + ", ".join(line_movies))
    else:
        report_lines.append("  (無)")

    report_lines.append("")

    # === 2. 各特徵欄位的離群值 ===
    report_lines.append("="*70)
    report_lines.append("2. 各特徵欄位的離群值分析（使用 IQR 方法）")
    report_lines.append("="*70)

    # 選擇數值型欄位進行離群值分析
    numeric_features = [
        'amount', 'tickets', 'theater_count',
        'boxoffice_week_1', 'boxoffice_week_2',
        'audience_week_1', 'audience_week_2',
        'screens_week_1', 'screens_week_2',
        'open_week1_days', 'open_week1_boxoffice',
        'open_week1_boxoffice_daily_avg', 'open_week2_boxoffice',
        'gap_real_week_1tocurrent', 'gap_real_week_2to1'
    ]

    # 過濾出實際存在的欄位
    numeric_features = [col for col in numeric_features if col in df.columns]

    report_lines.append(f"分析欄位數：{len(numeric_features)} 個\n")

    for col in numeric_features:
        # 移除 NaN 值
        col_data = df[col].dropna()

        if len(col_data) == 0:
            report_lines.append(f"{col}:")
            report_lines.append(f"  無有效資料")
            report_lines.append("")
            continue

        # 計算 IQR
        Q1 = col_data.quantile(0.25)
        Q3 = col_data.quantile(0.75)
        IQR = Q3 - Q1

        # 定義離群值範圍
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        # 找出離群值
        outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
        outlier_count = len(outliers)
        outlier_pct = (outlier_count / len(col_data)) * 100 if len(col_data) > 0 else 0

        report_lines.append(f"{col}:")
        report_lines.append(f"  樣本數: {len(col_data):,}")
        report_lines.append(f"  Q1: {Q1:,.2f}")
        report_lines.append(f"  Q3: {Q3:,.2f}")
        report_lines.append(f"  IQR: {IQR:,.2f}")
        report_lines.append(f"  離群值範圍: < {lower_bound:,.2f} 或 > {upper_bound:,.2f}")
        report_lines.append(f"  離群值數量: {outlier_count:,} ({outlier_pct:.2f}%)")

        if outlier_count > 0:
            report_lines.append(f"  離群值統計:")
            report_lines.append(f"    - 最小值: {outliers.min():,.2f}")
            report_lines.append(f"    - 最大值: {outliers.max():,.2f}")
            report_lines.append(f"    - 平均值: {outliers.mean():,.2f}")

        report_lines.append("")

    # === 3. 缺失值比例 ===
    report_lines.append("="*70)
    report_lines.append("3. 缺失值分析")
    report_lines.append("="*70)

    missing_stats = []
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_pct = (missing_count / len(df)) * 100
        if missing_count > 0:
            missing_stats.append((col, missing_count, missing_pct))

    if missing_stats:
        # 按缺失值比例排序
        missing_stats.sort(key=lambda x: x[2], reverse=True)

        report_lines.append(f"有缺失值的欄位數：{len(missing_stats)} 個\n")

        for col, count, pct in missing_stats:
            report_lines.append(f"{col}:")
            report_lines.append(f"  缺失值數量: {count:,} ({pct:.2f}%)")
            report_lines.append("")
    else:
        report_lines.append("所有欄位都沒有缺失值 ✓")
        report_lines.append("")

    # === 儲存報告 ===
    report_lines.append("="*70)
    report_lines.append("報告結束")
    report_lines.append("="*70)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"\n📄 資料品質報告已生成：{output_path}")


def flatten_timeseries():
    """
    主要處理函數：拉平時序資料並完成輪次定義與基礎特徵工程

    Returns:
        pd.DataFrame: 處理後的時序資料
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

    # === 3. 【Step 1】過濾：只保留正式上映日之後的週次 ===
    print("\n🔍 Step 1: 過濾正式上映日之前的資料...")

    filtered_list = []
    filtered_count = 0

    for gov_id in df_all["gov_id"].unique():
        movie_df = df_all[df_all["gov_id"] == gov_id].copy()

        if len(movie_df) == 0:
            continue

        # 解析上映日期
        try:
            release_date_str = movie_df.iloc[0]["official_release_date"]

            # 嘗試多種日期格式
            release_date = None
            for fmt in ["%Y/%m/%d", "%Y-%m-%d"]:
                try:
                    release_date = datetime.strptime(release_date_str, fmt)
                    break
                except:
                    continue

            if release_date is None:
                print(f"⚠️ 電影 {gov_id} 日期格式無法解析: {release_date_str}")
                continue

            # 過濾：只保留週次區間的結束日 >= 上映日的資料
            valid_rows = []
            for idx, row in movie_df.iterrows():
                week_range = row["week_range"]
                try:
                    # 取週次區間的結束日
                    week_end_str = week_range.split("~")[1]
                    week_end = datetime.strptime(week_end_str, "%Y-%m-%d")

                    # 如果週次結束日 >= 上映日，保留
                    if week_end >= release_date:
                        valid_rows.append(row)
                except Exception as e:
                    continue

            if len(valid_rows) > 0:
                filtered_movie_df = pd.DataFrame(valid_rows)
                filtered_list.append(filtered_movie_df)
                filtered_count += len(movie_df) - len(filtered_movie_df)
            else:
                filtered_count += len(movie_df)

        except Exception as e:
            print(f"⚠️ 電影 {gov_id} 處理失敗: {e}")
            continue

    if len(filtered_list) == 0:
        print("⚠️ 沒有符合條件的資料！")
        return pd.DataFrame()

    df_all = pd.concat(filtered_list, ignore_index=True)
    df_all = df_all.sort_values(["gov_id", "week_range"]).reset_index(drop=True)

    print(f"✅ 過濾完成：剔除 {filtered_count:,} 筆試映場資料")
    print(f"📊 剩餘：{len(df_all):,} 筆")

    # === 4. 【Step 2-4】定義輪次並過濾 ===
    print("\n🔄 Step 2-4: 定義輪次並過濾...")

    result_list = []

    for gov_id in df_all["gov_id"].unique():
        movie_df = df_all[df_all["gov_id"] == gov_id].copy().reset_index(drop=True)

        # 保存原始索引（用於計算跳週）
        movie_df["original_real_idx"] = range(1, len(movie_df) + 1)

        # === Step 2: 定義輪次 ===
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

        # 輪次編號 + 標記是否屬於輪次
        round_idx = 1
        round_indices = []
        in_round = []

        for i in range(len(movie_df)):
            row = movie_df.iloc[i]

            # 如果是連續第3週（含）以上沒票房 → 不屬於任何輪次
            if row["zero_streak"] >= 3:
                round_indices.append(-1)
                in_round.append(False)
            else:
                # 屬於當前輪次
                round_indices.append(round_idx)
                in_round.append(True)

            # 檢查是否該切換到新輪次
            # 條件：下一row會是連續第3週=0
            if i + 1 < len(movie_df):
                next_row = movie_df.iloc[i + 1]
                if next_row["zero_streak"] >= 3:
                    round_idx += 1

        movie_df["round_idx"] = round_indices
        movie_df["in_round"] = in_round

        # === Step 3: 過濾不在輪次內的row ===
        movie_df = movie_df[movie_df["in_round"]].copy()

        if len(movie_df) == 0:
            continue

        # === Step 4: 過濾真實週次 < 3 的整輪刪除 ===
        movie_df["temp_real_idx"] = movie_df.groupby("round_idx").cumcount() + 1
        real_weeks_per_round = movie_df.groupby("round_idx")["temp_real_idx"].max()
        valid_rounds = real_weeks_per_round[real_weeks_per_round >= 3].index.tolist()

        movie_df = movie_df[movie_df["round_idx"].isin(valid_rounds)].copy()

        if len(movie_df) == 0:
            continue

        # === 【新增】Step 4.5: 移除每輪末尾的0票房週次 ===
        print(f"  處理電影 {gov_id}：移除末尾0票房週次...")

        rows_to_keep = []
        for round_num in movie_df["round_idx"].unique():
            round_data = movie_df[movie_df["round_idx"] == round_num].copy()

            # 從最後一筆往前找，移除末尾連續的0票房row
            last_nonzero_idx = None
            for i in range(len(round_data) - 1, -1, -1):
                if round_data.iloc[i]["amount"] > 0:
                    last_nonzero_idx = i
                    break

            # 保留到最後一個有票房的週次
            if last_nonzero_idx is not None:
                rows_to_keep.append(round_data.iloc[: last_nonzero_idx + 1])

        if len(rows_to_keep) == 0:
            continue

        movie_df = pd.concat(rows_to_keep, ignore_index=True)

        if len(movie_df) == 0:
            continue

        # === 【新增】Step 4.6: 過濾活躍週次 < 3 的整輪刪除 ===
        print(f"  處理電影 {gov_id}：過濾活躍週次<3的輪次...")

        active_weeks_per_round = movie_df[movie_df["amount"] > 0].groupby("round_idx").size()
        valid_rounds = active_weeks_per_round[active_weeks_per_round >= 3].index.tolist()

        movie_df = movie_df[movie_df["round_idx"].isin(valid_rounds)].copy()

        if len(movie_df) == 0:
            continue

        # === 【新增】Step 4.7: 重新編號輪次 ===
        round_mapping = {
            old: new for new, old in enumerate(sorted(movie_df["round_idx"].unique()), 1)
        }
        movie_df["round_idx"] = movie_df["round_idx"].map(round_mapping)

        # === Step 5: 計算真實週次 ===
        movie_df["current_week_real_idx"] = movie_df.groupby("round_idx").cumcount() + 1

        # === Step 6: 計算活躍週次（僅對票房>0的row編號）===
        # 先標記哪些row有票房
        movie_df["has_boxoffice"] = (movie_df["amount"] > 0).astype(int)

        # 對每個輪次單獨計算活躍週次
        active_indices = []
        for round_num in movie_df["round_idx"].unique():
            round_mask = movie_df["round_idx"] == round_num
            round_data = movie_df[round_mask].copy()

            active_idx = 0
            for idx, row in round_data.iterrows():
                if row["has_boxoffice"] == 1:
                    active_idx += 1
                    active_indices.append(active_idx)
                else:
                    active_indices.append(np.nan)  # 票房=0的row不編號

        movie_df["current_week_active_idx"] = active_indices

        # === Step 5: 計算累計輪次 ===
        movie_df["rounds_cumsum"] = movie_df["round_idx"]

        # === Step 7: 計算跳週數（基於活躍週次）===
        movie_df["prev1_real_idx"] = np.nan
        movie_df["prev2_real_idx"] = np.nan
        movie_df["gap_real_week_1tocurrent"] = 0
        movie_df["gap_real_week_2to1"] = 0

        for round_num in movie_df["round_idx"].unique():
            round_mask = movie_df["round_idx"] == round_num
            round_data = movie_df[round_mask].copy()

            # 只處理有票房的row
            active_rows = round_data[round_data["has_boxoffice"] == 1].copy()

            if len(active_rows) >= 2:
                # 取得原始索引
                active_indices_list = active_rows.index.tolist()

                for i, idx in enumerate(active_indices_list):
                    if i >= 1:
                        # 前1週（活躍週）
                        prev1_idx = active_indices_list[i - 1]
                        movie_df.loc[idx, "prev1_real_idx"] = movie_df.loc[
                            prev1_idx, "original_real_idx"
                        ]

                        # 計算跳週數
                        gap = (
                            movie_df.loc[idx, "original_real_idx"]
                            - movie_df.loc[idx, "prev1_real_idx"]
                            - 1
                        )
                        movie_df.loc[idx, "gap_real_week_1tocurrent"] = int(gap)

                    if i >= 2:
                        # 前2週（活躍週）
                        prev2_idx = active_indices_list[i - 2]
                        movie_df.loc[idx, "prev2_real_idx"] = movie_df.loc[
                            prev2_idx, "original_real_idx"
                        ]

                        # 計算跳週數
                        gap = (
                            movie_df.loc[idx, "prev1_real_idx"]
                            - movie_df.loc[idx, "prev2_real_idx"]
                            - 1
                        )
                        movie_df.loc[idx, "gap_real_week_2to1"] = int(gap)

        # === 近期趨勢 Lag Features（基於活躍週次）===
        # 只對有票房的row計算lag
        movie_df["boxoffice_week_1"] = np.nan
        movie_df["boxoffice_week_2"] = np.nan
        movie_df["audience_week_1"] = np.nan
        movie_df["audience_week_2"] = np.nan
        movie_df["screens_week_1"] = np.nan
        movie_df["screens_week_2"] = np.nan

        for round_num in movie_df["round_idx"].unique():
            round_mask = movie_df["round_idx"] == round_num
            active_mask = round_mask & (movie_df["has_boxoffice"] == 1)

            # 對活躍週次做shift
            movie_df.loc[active_mask, "boxoffice_week_1"] = movie_df.loc[
                active_mask, "amount"
            ].shift(1)
            movie_df.loc[active_mask, "boxoffice_week_2"] = movie_df.loc[
                active_mask, "amount"
            ].shift(2)
            movie_df.loc[active_mask, "audience_week_1"] = movie_df.loc[
                active_mask, "tickets"
            ].shift(1)
            movie_df.loc[active_mask, "audience_week_2"] = movie_df.loc[
                active_mask, "tickets"
            ].shift(2)
            movie_df.loc[active_mask, "screens_week_1"] = movie_df.loc[
                active_mask, "theater_count"
            ].shift(1)
            movie_df.loc[active_mask, "screens_week_2"] = movie_df.loc[
                active_mask, "theater_count"
            ].shift(2)

        # === 開片實力（首輪）===
        first_round = movie_df[movie_df["round_idx"] == 1].copy()

        if len(first_round) > 0:
            # 找到首輪第1週（有票房的那一週）
            first_round_active = first_round[first_round["has_boxoffice"] == 1].copy()

            if len(first_round_active) > 0:
                first_week = first_round_active.iloc[0]

                # 解析日期
                try:
                    release_date_str = first_week["official_release_date"]
                    for fmt in ["%Y/%m/%d", "%Y-%m-%d"]:
                        try:
                            release_date = datetime.strptime(release_date_str, fmt)
                            break
                        except:
                            continue

                    week_range = first_week["week_range"]
                    week_end_str = week_range.split("~")[1]
                    week_end = datetime.strptime(week_end_str, "%Y-%m-%d")

                    open_week1_days = (week_end - release_date).days + 1
                    open_week1_days = max(1, min(7, open_week1_days))

                except Exception as e:
                    print(f"⚠️ 電影 {gov_id} 日期解析失敗: {e}")
                    open_week1_days = 7

                open_week1_boxoffice = first_week["amount"]
                open_week1_boxoffice_daily_avg = (
                    open_week1_boxoffice / open_week1_days if open_week1_days > 0 else 0
                )

                # 首輪第2週票房
                if len(first_round_active) >= 2:
                    open_week2_boxoffice = first_round_active.iloc[1]["amount"]
                else:
                    open_week2_boxoffice = np.nan

                movie_df["open_week1_days"] = open_week1_days
                movie_df["open_week1_boxoffice"] = open_week1_boxoffice
                movie_df["open_week1_boxoffice_daily_avg"] = open_week1_boxoffice_daily_avg
                movie_df["open_week2_boxoffice"] = open_week2_boxoffice
            else:
                movie_df["open_week1_days"] = np.nan
                movie_df["open_week1_boxoffice"] = np.nan
                movie_df["open_week1_boxoffice_daily_avg"] = np.nan
                movie_df["open_week2_boxoffice"] = np.nan
        else:
            movie_df["open_week1_days"] = np.nan
            movie_df["open_week1_boxoffice"] = np.nan
            movie_df["open_week1_boxoffice_daily_avg"] = np.nan
            movie_df["open_week2_boxoffice"] = np.nan

        result_list.append(movie_df)

    if len(result_list) == 0:
        print("⚠️ 沒有符合條件的資料！")
        return pd.DataFrame()

    # === 合併所有電影 ===
    result = pd.concat(result_list, ignore_index=True)

    # === 選擇欄位 ===
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

    # === 儲存與輸出 ===
    output_path = Path("data/ML_boxoffice/phase1_flattened")
    ensure_dir(output_path)
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_file = output_path / f"boxoffice_timeseries_{date_str}.csv"
    result.to_csv(output_file, index=False, encoding="utf-8-sig")

    # === 統計報告 ===
    print("\n" + "=" * 70)
    print("✅ 完成！輪次定義 + 週次計算 + 近期趨勢 + 開片實力")
    print("=" * 70)
    print(f"📄 檔案位置：{output_path}")
    print(f"📊 總樣本數：{len(result):,}")
    print(f"🎬 電影數量：{result['gov_id'].nunique()}")
    print(f"🔄 總輪次數：{result.groupby('gov_id')['round_idx'].max().sum():.0f}")

    # 統計輪次分布
    rounds_per_movie = result.groupby("gov_id")["round_idx"].max()
    print(f"\n📈 輪次分布：")
    print(f"   ├─ 單輪電影：{(rounds_per_movie == 1).sum()} 部")
    print(f"   ├─ 雙輪電影：{(rounds_per_movie == 2).sum()} 部")
    print(f"   └─ 三輪以上：{(rounds_per_movie >= 3).sum()} 部")

    # 統計有票房 vs 無票房的row
    has_boxoffice = (result["amount"] > 0).sum()
    no_boxoffice = (result["amount"] == 0).sum()
    print(f"\n📊 票房分布：")
    print(f"   ├─ 有票房的週次：{has_boxoffice:,} ({has_boxoffice/len(result)*100:.1f}%)")
    print(f"   └─ 無票房但保留（輪內中斷）：{no_boxoffice:,} ({no_boxoffice/len(result)*100:.1f}%)")

    # 驗證：每輪最後一週是否都有票房
    print(f"\n🔍 驗證：檢查每輪最後一週是否都有票房...")
    last_week_per_round = result.groupby(["gov_id", "round_idx"]).tail(1)
    last_week_zero = (last_week_per_round["amount"] == 0).sum()
    print(
        f"   └─ 最後一週票房=0的輪次：{last_week_zero} 個 {'✅' if last_week_zero == 0 else '❌'}"
    )

    # 驗證：每輪活躍週次是否都>=3
    print(f"\n🔍 驗證：檢查每輪活躍週次是否都>=3...")
    active_weeks_per_round = result[result["amount"] > 0].groupby(["gov_id", "round_idx"]).size()
    rounds_less_than_3 = (active_weeks_per_round < 3).sum()
    print(
        f"   └─ 活躍週次<3的輪次：{rounds_less_than_3} 個 {'✅' if rounds_less_than_3 == 0 else '❌'}"
    )

    # 開片實力統計
    print(f"\n🎬 開片實力統計：")
    open_days = result.groupby("gov_id")["open_week1_days"].first()
    print(f"   ├─ 平均上映天數：{open_days.mean():.1f} 天")

    open_bo = result.groupby("gov_id")["open_week1_boxoffice"].first()
    print(f"   ├─ 首週票房中位數：{open_bo.median():,.0f} 元")
    print(f"   └─ 首週票房平均：{open_bo.mean():,.0f} 元")

    print("\n📋 資料預覽：")
    preview_cols = [
        "gov_id",
        "week_range",
        "round_idx",
        "current_week_real_idx",
        "current_week_active_idx",
        "amount",
    ]
    print(result[preview_cols].head(20).to_string(index=False))

    # === 生成資料品質報告 ===
    report_file = output_path / f"boxoffice_timeseries_{date_str}_report.txt"
    generate_data_quality_report(result, report_file)

    return result


if __name__ == "__main__":
    df = flatten_timeseries()
