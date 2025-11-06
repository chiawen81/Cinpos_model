# -*- coding: utf-8 -*-
"""
市場特徵工程模組
---------------------------------------------------------------
模組目標：
    在 phase1 拉平資料的基礎上，加入市場環境相關特徵

新增欄位：
    - ticket_price_avg_current: 當週年度當輪次平均票價（元/張）
      （根據 week_range 起始日年份決定，而非上映年份）
    - release_year: 上映年份
    - release_month: 上映月份
    - region: 發行地區
    - publisher: 發行商
    - is_restricted: 是否限制級 (0/1)
    - film_length: 片長（分鐘）

處理邏輯：
    1. 從 official_release_date 提取年份和月份
    2. 將 rating 轉換為 is_restricted（限制級=1，其他=0）
    3. 計算平均票價：
       - 按 week_range 起始日年份 × round_type (首輪/非首輪) 分組
       - 計算 sum(amount) / sum(tickets)，四捨五入至整數
       - 每年會有 2 個平均票價（首輪/非首輪）
       - 每個 row 根據自己的 week_range 年份去對應票價
    4. 透過 gov_id 合併電影基本資訊
    5. 保留所有原有欄位

輸入：
    - phase1_flattened/boxoffice_timeseries_*.csv
    - processed/movieInfo_gov/combined/movieInfo_gov_full_*.csv

輸出：
    - phase2_features/with_market/features_market_*.csv
"""

import pandas as pd
from pathlib import Path
import sys
from datetime import date
import argparse
import re

# 加入共用模組路徑
sys.path.append(str(Path(__file__).parent.parent.parent))
from common.file_utils import ensure_dir, save_csv


def find_latest_file(directory, pattern):
    """
    在指定目錄下找符合 pattern 的最新檔案（根據檔名中的日期字串）

    Args:
        directory: 要搜尋的目錄 (Path 物件)
        pattern: 檔案名稱模式（例如: "boxoffice_timeseries_*.csv"）

    Returns:
        Path: 找到的最新檔案路徑，如果找不到則返回 None
    """
    if not directory.exists():
        print(f"錯誤: 目錄不存在 {directory}")
        return None

    # 找所有符合模式的檔案
    files = list(directory.glob(pattern))

    if not files:
        print(f"錯誤: 在 {directory} 中找不到符合 {pattern} 的檔案")
        return None

    # 從檔名中提取日期（格式: YYYY-MM-DD）
    date_pattern = r'(\d{4}-\d{2}-\d{2})'

    files_with_dates = []
    for file in files:
        match = re.search(date_pattern, file.name)
        if match:
            date_str = match.group(1)
            files_with_dates.append((file, date_str))

    if not files_with_dates:
        print(f"錯誤: 檔案名稱中找不到日期格式 (YYYY-MM-DD)")
        return None

    # 根據日期字串排序，取最新的
    files_with_dates.sort(key=lambda x: x[1], reverse=True)
    latest_file = files_with_dates[0][0]
    latest_date = files_with_dates[0][1]

    print(f"  找到最新檔案 (日期: {latest_date}): {latest_file.name}")
    return latest_file


def extract_date_features(df):
    """從 official_release_date 提取年份和月份"""
    df['official_release_date'] = pd.to_datetime(df['official_release_date'])
    df['release_year'] = df['official_release_date'].dt.year
    df['release_month'] = df['official_release_date'].dt.month
    return df


def convert_rating_to_restricted(rating):
    """
    將分級轉換為 is_restricted (限制級=1, 其他=0)

    Args:
        rating: 電影分級（如：限制級、輔12級、輔15級、普遍級、保護級）

    Returns:
        0: 非限制級
        1: 限制級
    """
    if pd.isna(rating):
        return 0
    return 1 if '限制級' in str(rating) else 0


def calculate_avg_ticket_price(df):
    """
    計算平均票價：按 week_range 起始日年份和輪次類型（首輪/非首輪）分組

    分組邏輯：
    - week_year: week_range 起始日的年份（例如 "2019-07-08~2019-07-14" -> 2019）
    - round_type: 首輪(round_idx==1) vs 非首輪(round_idx>=2)

    計算方式：
    - ticket_price = sum(amount) / sum(tickets)

    範例：
        2023 年首輪: 350 元/張
        2023 年非首輪: 150 元/張
        2024 年首輪: 360 元/張
        2024 年非首輪: 160 元/張

    重要：
        每個 row 的票價依據該 row 的 week_range 年份決定，
        而非電影的首輪上映年份，因此同一部電影在不同年份的 row
        會有不同的票價。

    Returns:
        原 DataFrame 加上 ticket_price_avg_current 欄位
    """
    # 從 week_range 提取起始日年份（格式: "2019-07-08~2019-07-14"）
    df['week_year'] = df['week_range'].str.split('~').str[0].str[:4].astype(int)

    # 建立輔助欄位：輪次類型（首輪/非首輪）
    df['round_type'] = df['round_idx'].apply(lambda x: '首輪' if x == 1 else '非首輪')

    # 過濾有效資料（票房>0 且觀眾數>0）
    valid_df = df[(df['amount'] > 0) & (df['tickets'] > 0)].copy()

    # 按 week_year 和輪次類型分組計算平均票價
    price_mapping = valid_df.groupby(['week_year', 'round_type']).agg({
        'amount': 'sum',
        'tickets': 'sum'
    }).reset_index()

    # 計算平均票價（元/人次 -> 元/張，四捨五入至整數）
    # amount 單位已經是元，不需要轉換
    price_mapping['ticket_price_avg'] = round(price_mapping['amount'] / price_mapping['tickets']).astype(int)

    # 只保留需要的欄位
    price_mapping = price_mapping[['week_year', 'round_type', 'ticket_price_avg']]

    print("\n計算出的平均票價：")
    for _, row in price_mapping.iterrows():
        print(f"  {int(row['week_year'])} 年 {row['round_type']}: {int(row['ticket_price_avg'])} 元/張")

    # Merge 回原始資料（根據每個 row 的 week_year 來對應票價）
    df = df.merge(price_mapping, on=['week_year', 'round_type'], how='left')
    df.rename(columns={'ticket_price_avg': 'ticket_price_avg_current'}, inplace=True)

    # 刪除輔助欄位
    df.drop(columns=['week_year', 'round_type'], inplace=True)

    return df


def add_movie_info(boxoffice_df, movie_info_path):
    """
    合併電影基本資訊

    Args:
        boxoffice_df: 票房時序資料
        movie_info_path: 電影基本資訊檔案路徑

    Returns:
        合併後的 DataFrame
    """
    # 讀取電影資訊
    movie_df = pd.read_csv(movie_info_path, encoding='utf-8-sig')

    print(f"  電影資訊檔: {len(movie_df)} 部電影")

    # 選取需要的欄位
    movie_cols = ['gov_id', 'region', 'rating', 'publisher', 'film_length']
    movie_df = movie_df[movie_cols]

    # 轉換 rating 為 is_restricted
    movie_df['is_restricted'] = movie_df['rating'].apply(convert_rating_to_restricted)
    movie_df.drop(columns=['rating'], inplace=True)

    # 合併（使用 left join 保留所有票房資料）
    result_df = boxoffice_df.merge(movie_df, on='gov_id', how='left')

    # 檢查是否有未匹配的電影
    unmatched = result_df[result_df['region'].isna()]['gov_id'].nunique()
    if unmatched > 0:
        print(f"  警告: {unmatched} 部電影無法找到對應的基本資訊")

    return result_df


def add_market_features(input_csv_path, movie_info_csv_path, output_csv_path):
    """
    主函數：加入市場特徵

    Args:
        input_csv_path: phase1 輸出的時序資料
        movie_info_csv_path: 電影基本資訊
        output_csv_path: 輸出路徑

    Returns:
        處理後的 DataFrame
    """
    print(f"\n{'='*60}")
    print("市場特徵工程 - Phase 2")
    print(f"{'='*60}\n")

    print("讀取票房時序資料...")
    print(f"  來源: {input_csv_path}")
    df = pd.read_csv(input_csv_path, encoding='utf-8-sig')
    print(f"  原始資料: {len(df)} rows, {len(df.columns)} columns")

    # 1. 提取日期特徵
    print("\n步驟 1/4: 提取 release_year, release_month...")
    df = extract_date_features(df)
    print(f"  年份範圍: {df['release_year'].min()}-{df['release_year'].max()}")

    # 2. 計算平均票價
    print("\n步驟 2/4: 計算平均票價 (按 week_range 年份+輪次類型分組)...")
    df = calculate_avg_ticket_price(df)

    # 3. 合併電影資訊
    print("\n步驟 3/4: 合併電影基本資訊...")
    print(f"  來源: {movie_info_csv_path}")
    df = add_movie_info(df, movie_info_csv_path)

    # 4. 檢查結果
    print("\n步驟 4/4: 檢查新增欄位...")
    new_cols = ['release_year', 'release_month', 'ticket_price_avg_current',
                'region', 'publisher', 'is_restricted', 'film_length']

    for col in new_cols:
        if col in df.columns:
            null_count = df[col].isna().sum()
            null_pct = (null_count / len(df)) * 100
            print(f"  - {col}: 已新增 (缺失值: {null_count} / {null_pct:.1f}%)")
        else:
            print(f"  - {col}: 錯誤 (欄位不存在)")

    # 5. 儲存結果
    print("\n儲存結果...")
    print(f"  目的地: {output_csv_path}")
    output_path = Path(output_csv_path)
    ensure_dir(str(output_path.parent))
    save_csv(df, str(output_path.parent), output_path.name)

    print(f"\n{'='*60}")
    print("完成！")
    print(f"{'='*60}")
    print(f"  輸出: {len(df)} rows, {len(df.columns)} columns")
    print(f"  新增: {len(new_cols)} 個市場特徵欄位")
    print(f"{'='*60}\n")

    return df


def main(input_file=None, movie_info_file=None):
    """
    執行腳本

    Args:
        input_file: 票房時序資料檔案路徑 (Path 物件或 None)
                   如果為 None，自動從 data/ML_boxoffice/phase1_flattened 找最新檔案
        movie_info_file: 電影資訊檔案路徑 (Path 物件或 None)
                        如果為 None，自動從 data/processed/movieInfo_gov/combined 找最新檔案
    """
    # 定義路徑
    project_root = Path(__file__).parent.parent.parent.parent

    # 如果沒有指定 input_file，自動找最新檔案
    if input_file is None:
        print("\n未指定 input_file，自動尋找最新的票房時序資料...")
        input_dir = project_root / "data/ML_boxoffice/phase1_flattened"
        input_file = find_latest_file(input_dir, "boxoffice_timeseries_*.csv")
        if input_file is None:
            return

    # 如果沒有指定 movie_info_file，自動找最新檔案
    if movie_info_file is None:
        print("\n未指定 movie_info_file，自動尋找最新的電影資訊...")
        movie_info_dir = project_root / "data/processed/movieInfo_gov/combined"
        movie_info_file = find_latest_file(movie_info_dir, "movieInfo_gov_full_*.csv")
        if movie_info_file is None:
            return

    # 輸出檔案（使用當下日期）
    date_str = date.today().strftime("%Y-%m-%d")
    output_file = project_root / f"data/ML_boxoffice/phase2_features/with_market/features_market_{date_str}.csv"

    # 檢查輸入檔案是否存在
    if not input_file.exists():
        print(f"錯誤: 找不到輸入檔案 {input_file}")
        return

    if not movie_info_file.exists():
        print(f"錯誤: 找不到電影資訊檔案 {movie_info_file}")
        return

    # 執行
    add_market_features(
        input_csv_path=str(input_file),
        movie_info_csv_path=str(movie_info_file),
        output_csv_path=str(output_file)
    )


if __name__ == "__main__":
    # 設定命令列參數
    parser = argparse.ArgumentParser(
        description='市場特徵工程 - Phase 2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=
"""使用範例：
  
  # 自動使用最新檔案（推薦）
  uv run src/ML_boxoffice/phase2_features/add_market_features.py

  # 指定單一檔案(以市場資訊為例) input_file
  uv run add_market_features.py --movie-info data/processed/movieInfo_gov/combined/movieInfo_gov_full_2025-11-06.csv

  # 指定兩個檔案
  uv run src/ML_boxoffice/phase2_features/add_market_features.py ^
  --input data/ML_boxoffice/phase1_flattened/boxoffice_timeseries_2025-11-06.csv ^
  --movie-info data/processed/movieInfo_gov/combined/movieInfo_gov_full_2025-11-06.csv
"""
    )

    parser.add_argument(
        '--input',
        type=str,
        help='票房時序資料檔案路徑（相對於專案根目錄）。若不指定，自動使用最新檔案。'
    )

    parser.add_argument(
        '--movie-info',
        type=str,
        help='電影資訊檔案路徑（相對於專案根目錄）。若不指定，自動使用最新檔案。'
    )

    args = parser.parse_args()

    # 處理檔案路徑
    project_root = Path(__file__).parent.parent.parent.parent

    input_file = None
    if args.input:
        input_file = project_root / args.input

    movie_info_file = None
    if args.movie_info:
        movie_info_file = project_root / args.movie_info

    # 執行
    main(input_file=input_file, movie_info_file=movie_info_file)
