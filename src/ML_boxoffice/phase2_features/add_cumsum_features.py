#!/usr/bin/env python3
"""
累積特徵生成腳本 v2 (適配實際資料格式)
====================

功能說明:
- 接收包含實際票房資料的 CSV 檔案
- 保留所有原有欄位
- 新增 6 個累積特徵欄位（截至上週，不含當週）

實際欄位對應:
- gov_id → movie_id (電影唯一識別)
- round_idx → round (輪次)
- current_week_active_idx → week_in_round (當輪週次)
- amount → boxoffice (本週票房)
- tickets → audience (本週觀影人數)

累積欄位說明:
1. boxoffice_cumsum: 跨輪累積票房（首輪全部 + 當輪截至上週）
2. boxoffice_round1_cumsum: 首輪累積票房
3. boxoffice_current_round_cumsum: 當輪累積票房
4. audience_cumsum: 跨輪累積觀影人數
5. audience_round1_cumsum: 首輪累積觀影人數
6. audience_current_round_cumsum: 當輪累積觀影人數

使用方式:
    # 自動使用最新的檔案
    uv run src/ML_boxoffice/phase2_features/add_cumsum_features.py

    # 或指定特定檔案
    uv run src/ML_boxoffice/phase2_features/add_cumsum_features.py data\ML_boxoffice\phase1_flattened\boxoffice_timeseries_2025-11-06.csv

    # 或指定輸入和輸出
    uv run src/ML_boxoffice/phase2_features/add_cumsum_features.py ^ data\ML_boxoffice\phase1_flattened\boxoffice_timeseries_2025-11-06.csv ^ data\ML_boxoffice\phase2_features\with_cumsum\features_cumsum_2025-11-07.csv
"""

import pandas as pd
import sys
from pathlib import Path
import glob
from datetime import datetime


def calculate_cumsum_features(df):
    """
    計算累積特徵（截至上週，不含當週）

    Parameters:
    -----------
    df : pd.DataFrame
        輸入資料框，必須包含以下欄位:
        - gov_id: 電影ID
        - round_idx: 輪次(1=首輪, 2=次輪)
        - current_week_active_idx: 當輪週次
        - amount: 本週票房
        - tickets: 本週觀影人數

    Returns:
    --------
    pd.DataFrame
        包含原有欄位 + 6個新增累積欄位
    """

    # 檢查必要欄位
    required_cols = ["gov_id", "round_idx", "current_week_active_idx", "amount", "tickets"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"缺少必要欄位: {missing_cols}\n實際欄位: {list(df.columns)}")

    # 複製資料框避免修改原始資料
    result_df = df.copy()

    # 保留原始順序索引
    result_df["_original_order"] = range(len(result_df))

    # 確保資料按照 gov_id, round_idx, current_week_active_idx 排序（用於計算）
    result_df = result_df.sort_values(
        ["gov_id", "round_idx", "current_week_active_idx"]
    ).reset_index(drop=True)

    # 初始化新欄位
    cumsum_cols = [
        "boxoffice_cumsum",
        "boxoffice_round1_cumsum",
        "boxoffice_current_round_cumsum",
        "audience_cumsum",
        "audience_round1_cumsum",
        "audience_current_round_cumsum",
    ]

    for col in cumsum_cols:
        result_df[col] = 0.0

    # 按電影分組計算
    for gov_id, movie_group in result_df.groupby("gov_id"):
        movie_indices = movie_group.index

        # 計算每一輪的總計（用於跨輪累積）
        round_totals_boxoffice = {}
        round_totals_audience = {}
        for round_idx in sorted(movie_group["round_idx"].unique()):
            round_data = movie_group[movie_group["round_idx"] == round_idx]
            round_totals_boxoffice[round_idx] = round_data["amount"].sum()
            round_totals_audience[round_idx] = round_data["tickets"].sum()

        # 逐列計算累積值
        for idx in movie_indices:
            current_round = result_df.loc[idx, "round_idx"]
            current_week = result_df.loc[idx, "current_week_active_idx"]
            current_order = result_df.loc[idx, "_original_order"]

            # 取得當前電影、當前輪次、當前週次之前的所有資料
            # 如果 current_week 是 NaN（amount=0 的情況），使用原始順序來判斷「之前」
            if pd.isna(current_week):
                previous_data = movie_group[
                    (movie_group["round_idx"] == current_round)
                    & (movie_group["_original_order"] < current_order)
                ]
            else:
                previous_data = movie_group[
                    (movie_group["round_idx"] == current_round)
                    & (movie_group["current_week_active_idx"] < current_week)
                ]

            # === 計算當輪累積（截至上週） ===
            current_round_boxoffice_cumsum = previous_data["amount"].sum()
            current_round_audience_cumsum = previous_data["tickets"].sum()

            result_df.loc[idx, "boxoffice_current_round_cumsum"] = current_round_boxoffice_cumsum
            result_df.loc[idx, "audience_current_round_cumsum"] = current_round_audience_cumsum

            # === 計算首輪累積 ===
            if current_round == 1:
                # 首輪進行中: 累積到上週
                result_df.loc[idx, "boxoffice_round1_cumsum"] = current_round_boxoffice_cumsum
                result_df.loc[idx, "audience_round1_cumsum"] = current_round_audience_cumsum
            else:
                # 首輪已結束: 使用首輪總計（固定值）
                result_df.loc[idx, "boxoffice_round1_cumsum"] = round_totals_boxoffice.get(1, 0)
                result_df.loc[idx, "audience_round1_cumsum"] = round_totals_audience.get(1, 0)

            # === 計算跨輪累積 ===
            # 累積所有之前輪次的總計 + 當輪截至上週
            previous_rounds_boxoffice = sum(
                round_totals_boxoffice[r] for r in round_totals_boxoffice if r < current_round
            )
            previous_rounds_audience = sum(
                round_totals_audience[r] for r in round_totals_audience if r < current_round
            )
            result_df.loc[idx, "boxoffice_cumsum"] = (
                previous_rounds_boxoffice + current_round_boxoffice_cumsum
            )
            result_df.loc[idx, "audience_cumsum"] = (
                previous_rounds_audience + current_round_audience_cumsum
            )

    # 轉換整數欄位
    integer_cols = ["audience_cumsum", "audience_round1_cumsum", "audience_current_round_cumsum"]
    for col in integer_cols:
        result_df[col] = result_df[col].astype(int)

    # 恢復原始順序
    result_df = result_df.sort_values("_original_order").reset_index(drop=True)
    # 刪除臨時欄位
    result_df = result_df.drop(columns=["_original_order"])

    return result_df


def find_latest_file(directory, pattern="boxoffice_timeseries_*.csv"):
    """
    從指定目錄找出日期戳記最新的檔案

    Parameters:
    -----------
    directory : str or Path
        要搜尋的目錄
    pattern : str
        檔案名稱模式

    Returns:
    --------
    Path or None
        最新的檔案路徑，找不到則返回 None
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return None

    # 找出所有符合模式的檔案
    files = list(dir_path.glob(pattern))

    if not files:
        return None

    # 按修改時間排序，取最新的
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return latest_file


def main():
    """主程式"""

    # 解析命令列參數
    if len(sys.argv) < 2:
        # 沒有提供參數，自動找最新檔案
        print("未指定輸入檔案，自動搜尋最新檔案...")
        default_input_dir = Path("data/ML_boxoffice/phase1_flattened")
        input_path = find_latest_file(default_input_dir)

        if input_path is None:
            print(f"錯誤: 找不到輸入檔案於 {default_input_dir}")
            print("\n使用方式:")
            print("  # 自動使用最新的檔案")
            print("  uv run src/ML_boxoffice/phase2_features/add_cumsum_features.py")
            print("\n  # 或指定特定檔案")
            print(
                "  uv run src/ML_boxoffice/phase2_features/add_cumsum_features.py <input_csv> [output_csv]"
            )
            sys.exit(1)

        print(f"  -> 找到最新檔案: {input_path.name}")
    else:
        input_path = Path(sys.argv[1])

    # 決定輸出路徑
    if len(sys.argv) >= 3:
        # 有指定輸出路徑
        output_path = Path(sys.argv[2])
    else:
        # 預設: 輸出到 data/ML_boxoffice/phase2_features/with_cumsum
        default_output_dir = Path("data/ML_boxoffice/phase2_features/with_cumsum")

        # 從輸入檔名提取日期戳記
        # 假設檔名格式為: boxoffice_timeseries_YYYY-MM-DD.csv
        stem = input_path.stem
        if "boxoffice_timeseries_" in stem:
            date_part = stem.replace("boxoffice_timeseries_", "")
            output_filename = f"features_cumsum_{date_part}.csv"
        else:
            # 如果檔名格式不符，使用原檔名加後綴
            output_filename = f"{stem}_with_cumsum.csv"

        output_path = default_output_dir / output_filename

    # 檢查輸入檔案
    if not input_path.exists():
        print(f"錯誤: 找不到輸入檔案 {input_path}")
        sys.exit(1)

    print(f"讀取檔案: {input_path}")

    try:
        # 讀取 CSV
        df = pd.read_csv(input_path)
        print(f"  - 原始資料: {len(df)} 列, {len(df.columns)} 欄")
        print(f"  - 原始欄位數: {len(df.columns)}")

        # 顯示關鍵欄位資訊
        key_cols = ["gov_id", "round_idx", "current_week_active_idx", "amount", "tickets"]
        available_key_cols = [col for col in key_cols if col in df.columns]
        if available_key_cols:
            print(f"  - 關鍵欄位: {available_key_cols}")

        # 計算累積特徵
        print("\n計算累積特徵...")
        result_df = calculate_cumsum_features(df)
        print(f"  - 新增 6 個累積欄位")
        print(f"  - 輸出資料: {len(result_df)} 列, {len(result_df.columns)} 欄")

        # 確保輸出目錄存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 儲存結果
        result_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n[OK] 成功儲存到: {output_path}")

        # 顯示新增的欄位範例
        new_cols = [
            "boxoffice_cumsum",
            "boxoffice_round1_cumsum",
            "boxoffice_current_round_cumsum",
            "audience_cumsum",
            "audience_round1_cumsum",
            "audience_current_round_cumsum",
        ]
        display_cols = ["gov_id", "round_idx", "current_week_active_idx"] + new_cols
        print("\n新增欄位範例 (前 5 列):")
        print(result_df[display_cols].head(5).to_string())

        # 統計資訊
        print("\n累積欄位統計:")
        stats_df = result_df[new_cols].describe()
        print(stats_df.to_string())

        # 檢查是否有次輪資料
        if (result_df["round_idx"] > 1).any():
            print("\n[OK] 檢測到次輪資料，跨輪累積已正確計算")
            round2_sample = result_df[result_df["round_idx"] == 2].head(2)
            if len(round2_sample) > 0:
                print("\n次輪範例 (前 2 列):")
                print(round2_sample[display_cols].to_string())

    except Exception as e:
        print(f"\n錯誤: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
