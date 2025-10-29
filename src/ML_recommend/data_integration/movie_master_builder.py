"""
🎬 movie_master_builder.py
------------------------------------------------------------
🎯 任務：
    將政府電影資料（movieInfo_gov_full）
    與票房聚合資料（boxoffice_latest）
    整合為「Movie Master Dataset」。

📂 輸出至data\master：
      - full資料夾：最完整版本（含所有欄位，用於人工檢查與備份）
      - db_ready資料夾：精簡版本（用於資料庫上傳）
      - train_ready資料夾：訓練版本（僅保留模型訓練所需欄位，處理空值與數值化）

🔑 執行方式：
      (1) uv run <本檔案路徑> --target all      (預設)
          => 共產生 3 份csv, 同時重建 full + 衍生版本
      (2) uv run <本檔案路徑> --target full
          => 共產生 1 份csv, 僅生成 full	movie_master_full.csv
      (3) uv run <本檔案路徑> --target derivative
          => 共產生 2 份csv, 從既有 full 衍生 db_ready、train_ready
"""

# ------------------------------------------------------------
# 套件匯入
# ------------------------------------------------------------
import os
import argparse
import pandas as pd
from datetime import datetime

# 若你有共用工具可以引用以下
# from common.file_utils import ensure_folder_exists, save_csv


# ------------------------------------------------------------
# 檔案路徑設定
# ------------------------------------------------------------
GOV_PATH = "data/processed/movieInfo_gov/combined/movieInfo_gov_full_2025-10-29.csv"
BOX_PATH = "data/aggregated/boxoffice/combined/boxoffice_latest_2025-10-29.csv"

MASTER_FOLDER = "data/master"
OUTPUT_FULL = os.path.join(MASTER_FOLDER, "full/movie_master_full.csv")
OUTPUT_DB = os.path.join(MASTER_FOLDER, "db_ready/movie_master_db_ready.csv")
OUTPUT_TRAIN = os.path.join(MASTER_FOLDER, "train_ready/movie_master_train_ready.csv")


# ------------------------------------------------------------
# 工具函數
# ------------------------------------------------------------
def ensure_folder_exists(path: str):
    """確保資料夾存在"""
    os.makedirs(path, exist_ok=True)


def save_csv(df: pd.DataFrame, output_path: str):
    """將 DataFrame 輸出為 CSV"""
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"📁 已輸出檔案：{output_path}")


# ------------------------------------------------------------
# Step 1. 整合資料 (Full 版)
# ------------------------------------------------------------
def merge_datasets(df_gov: pd.DataFrame, df_box: pd.DataFrame) -> pd.DataFrame:
    """
    以 gov_id 為主鍵合併政府資料與票房資料。
    """
    print("🔗 進行資料合併中...")
    df_merged = pd.merge(df_gov, df_box, on="gov_id", how="left", suffixes=("_gov", "_box"))

    # 移除重複欄位（例如 official_release_date_box）
    drop_cols = [
        col for col in df_merged.columns if col.endswith("_box") and "official_release_date" in col
    ]
    if drop_cols:
        df_merged = df_merged.drop(columns=drop_cols)

    print(f"✅ 合併完成，共 {len(df_merged)} 筆資料。")
    return df_merged


# ------------------------------------------------------------
# Step 2. 建立 db_ready 版本
# ------------------------------------------------------------
def make_db_ready(df: pd.DataFrame) -> pd.DataFrame:
    """
    精簡欄位、統一命名風格，作為資料庫上傳版本。
    """
    print("🧩 生成 db_ready 版本...")

    cols = [
        "gov_id",
        "gov_title_zh",
        "gov_title_en",
        "region",
        "rating_class",
        "official_release_date",
        "publisher",
        "film_length",
        "release_round",
        "release_start",
        "release_end",
        "release_days",
        "total_weeks",
        "total_amount",
        "total_tickets",
        "peak_amount",
        "is_long_tail",
        "status",
        "update_at",
    ]

    # 有些欄位可能在 gov 或 boxoffice 尚未出現，需先確認存在
    existing_cols = [c for c in cols if c in df.columns]
    db_df = df[existing_cols].copy()

    print(f"✅ db_ready 欄位數：{len(existing_cols)}，筆數：{len(db_df)}")
    return db_df


# ------------------------------------------------------------
# Step 3. 建立 train_ready 版本
# ------------------------------------------------------------
def make_train_ready(df: pd.DataFrame) -> pd.DataFrame:
    """
    建立訓練用版本：
        - 選取模型訓練所需欄位
        - 補齊空值（以 0 取代）
        - 保留主要數值與分類特徵
    """
    print("🤖 生成 train_ready 版本...")

    train_cols = [
        "gov_id",
        "region",
        "rating_class",
        "film_length",
        "release_round",
        "is_re_release",
        "release_days",
        "total_weeks",
        "avg_amount_per_week",
        "peak_amount",
        "amount_growth_rate",
        "decline_rate_mean",
        "previous_round_count",
        "previous_total_amount",
        "total_amount",  # 🎯 預測目標 y 值
    ]

    existing_cols = [c for c in train_cols if c in df.columns]
    train_df = df[existing_cols].copy()
    train_df = train_df.fillna(0)

    print(f"✅ train_ready 欄位數：{len(existing_cols)}，筆數：{len(train_df)}")
    return train_df


# ------------------------------------------------------------
# Step 4. 執行主流程
# ------------------------------------------------------------
def main(target: str):
    """
    主控制流程，依照 --target 參數執行不同任務。
    """
    print(f"\n🚀 開始執行 movie_master_builder.py（模式：{target}）\n")

    if target in ["full", "all"]:
        # 載入來源資料
        df_gov = pd.read_csv(GOV_PATH)
        df_box = pd.read_csv(BOX_PATH)
        print(f"📄 政府電影資料：{len(df_gov)} 筆")
        print(f"📄 聚合票房資料：{len(df_box)} 筆")

        # 欄位命名統一
        df_gov = df_gov.rename(columns={"rating": "rating_class"})
        df_box = df_box.rename(columns={"rating": "rating_class"})

        # 合併資料
        df_full = merge_datasets(df_gov, df_box)

        # 輸出 full 版本
        ensure_folder_exists(os.path.dirname(OUTPUT_FULL))
        save_csv(df_full, OUTPUT_FULL)
    else:
        # 若只執行 derivative 模式，直接從現有 full 版本讀取
        print("📂 從既有 full 版本讀取資料...")
        df_full = pd.read_csv(OUTPUT_FULL)

    # 生成 db_ready 與 train_ready
    if target in ["derivative", "all"]:
        ensure_folder_exists(os.path.dirname(OUTPUT_DB))
        ensure_folder_exists(os.path.dirname(OUTPUT_TRAIN))

        db_df = make_db_ready(df_full)
        save_csv(db_df, OUTPUT_DB)

        train_df = make_train_ready(df_full)
        save_csv(train_df, OUTPUT_TRAIN)

    print("\n🎉 全部處理完成！\n")


# ------------------------------------------------------------
# Step 5. 參數解析（Command-line）
# ------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Movie Master Builder - 整合電影主資料集")
    parser.add_argument(
        "--target",
        type=str,
        choices=["full", "derivative", "all"],
        default="all",
        help="指定要執行的任務類型：full / derivative / all",
    )
    args = parser.parse_args()
    main(args.target)
