"""
IMDb / OMDb 評分資料清洗
----------------------------------
目標：
    將 rating_weekly.py 爬取後的 JSON 清洗成可分析用的 CSV。
    同時輸出兩份版本：
        1. _cleaned：僅 IMDb 資料
        2. _full：包含 IMDb + Rotten Tomatoes + Metacritic

輸入：
    data/raw/rating_weekly/<當周>/rating_<當周>.json

輸出：
    data/processed/rating_weekly__<當周>_cleaned.csv
    data/processed/rating_weekly__<當周>_full.csv
"""

# ———————————————————————————————————— 套件匯入 ————————————————————————————————————
import os
import json
import pandas as pd
# 共用模組
from common.file_utils import save_csv
from common.date_utils import get_current_week_label
from common.path_utils import RATING_WEEKLY_PROCESSED


# ———————————————————————————————————— 展平輔助函式 ————————————————————————————————————
def extract_ratings(ratings_list):
    """從 ratings list 中提取 IMDb、Rotten、Metacritic 評分"""
    if not isinstance(ratings_list, list):
        return pd.Series([None, None, None])
    imdb, rotten, meta = None, None, None
    for r in ratings_list:
        src = r.get("Source", "").lower()
        val = r.get("Value")
        if "internet movie" in src:
            imdb = val
        elif "rotten" in src:
            rotten = val
        elif "metacritic" in src:
            meta = val
    return pd.Series([imdb, rotten, meta])


def extract_note(note_dict):
    """提取 crawl_note 中的 gov_id、atmovies_id、atmovies_title_zh"""
    if not isinstance(note_dict, dict):
        return pd.Series([None, None, None])
    return pd.Series([
        note_dict.get("gov_id"),
        note_dict.get("atmovies_id"),
        note_dict.get("atmovies_title_zh"),
    ])


# ———————————————————————————————————— 主要清洗函式 ————————————————————————————————————
def clean_rating_weekly(raw_folder: str, week_label: str):
    """清洗 IMDb / OMDb 評分資料"""
    raw_path = os.path.join(raw_folder, f"rating_{week_label}.json")
    print("raw_path", raw_path)
    if not os.path.exists(raw_path):
        print(f"⚠️ 找不到來源檔案：{raw_path}")
        return

    # 讀取 JSON
    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # ——— 展平 ratings 與 crawl_note ———
    df[["rating_imdb_src", "rating_rotten_src", "rating_meta_src"]] = df["ratings"].apply(extract_ratings)
    df[["gov_id", "atmovies_id", "atmovies_title_zh"]] = df["crawl_note"].apply(extract_note)

    # ——— 數值轉換 ———
    if "imdbRating" in df.columns:
        df["imdbRating"] = pd.to_numeric(df["imdbRating"], errors="coerce")
    if "imdbVotes" in df.columns:
        df["imdbVotes"] = (
            df["imdbVotes"].astype(str).str.replace(",", "").replace("N/A", None)
        )
        df["imdbVotes"] = pd.to_numeric(df["imdbVotes"], errors="coerce")

    # 去重
    if "imdb_id" in df.columns:
        df.drop_duplicates(subset=["imdb_id"], inplace=True)

    # ——— 統一欄位命名 ———
    df.rename(
        columns={
            "title": "omdb_title",
            "imdbRating": "imdb_rating",
            "imdbVotes": "imdb_votes",
            "rating_rotten_src": "tomatoes_rating",
            "rating_meta_src": "metacritic_rating",
        },
        inplace=True,
    )

    # ——— 指定欄位順序 ———
    col_order = [
        "imdb_id",
        "atmovies_title_zh",
        "omdb_title",
        "imdb_votes",
        "imdb_rating",
        "tomatoes_rating",
        "metacritic_rating",
        "atmovies_id",
        "gov_id",
    ]

    # 補齊缺欄位（避免部分缺失報錯）
    for col in col_order:
        if col not in df.columns:
            df[col] = None

    df = df[col_order]

    # ——— 輸出兩版本 ———
    cleaned_df = df[["imdb_id", "atmovies_title_zh", "omdb_title", "imdb_votes", "imdb_rating", "atmovies_id", "gov_id"]]
    cleaned_name = f"rating_weekly__{week_label}_cleaned.csv"
    full_name = f"rating_weekly__{week_label}_full.csv"

    save_csv(cleaned_df, RATING_WEEKLY_PROCESSED, cleaned_name)
    save_csv(df, RATING_WEEKLY_PROCESSED, full_name)

    print(f"✅ 已輸出兩份檔案：\n ├─ {cleaned_name}\n └─ {full_name}")


# ———————————————————————————————————— 主程式執行入口 ————————————————————————————————————
if __name__ == "__main__":
    week_label = get_current_week_label()
    raw_folder = f"data/raw/rating_weekly/{week_label}"
    clean_rating_weekly(raw_folder, week_label)
