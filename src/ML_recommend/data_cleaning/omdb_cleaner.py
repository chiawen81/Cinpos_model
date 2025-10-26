"""
OMDb 資料清洗模組
-------------------------------------------------
🎯 目標：
    將 data/raw/omdb/<year>/<week> 下的原始 JSON
    轉換為結構化 CSV（單支、週彙整、全域合併）。

📂 資料流：
    input  : data/raw/omdb/<year>/<week>/
    output :
        - data/processed/movieInfo_omdb/<year>/<week>/<gov_id>_<title_zh>_<imdb_id>.csv
        - data/processed/movieInfo_omdb/<year>/<week>/omdb_<周次>.csv
        - data/processed/movieInfo_omdb/combined/omdb_all.csv
"""

# -------------------------------------------------------
# 套件匯入
# -------------------------------------------------------
import os
import json
import pandas as pd
from datetime import datetime

# 共用模組
from common.path_utils import OMDB_RAW, MOVIEINFO_OMDB_PROCESSED
from common.file_utils import ensure_dir, save_csv, load_json, clean_filename
from common.date_utils import get_current_year_label, get_current_week_label


# -------------------------------------------------------
# 全域設定
# -------------------------------------------------------
YEAR_LABEL = get_current_year_label()
WEEK_LABEL = get_current_week_label()

RAW_DIR = os.path.join(OMDB_RAW, YEAR_LABEL, WEEK_LABEL)
PROCESSED_DIR = os.path.join(MOVIEINFO_OMDB_PROCESSED, YEAR_LABEL, WEEK_LABEL)
COMBINED_DIR = os.path.join(MOVIEINFO_OMDB_PROCESSED, "combined")

ensure_dir(PROCESSED_DIR)
ensure_dir(COMBINED_DIR)


# -------------------------------------------------------
# 輔助函式
# -------------------------------------------------------
def extract_ratings(data: dict):
    """拆解 Ratings 欄位成 imdb/tomatoes/metacritic 三欄"""
    imdb_rating = ""
    tomatoes_rating = ""
    metacritic_rating = ""

    ratings = data.get("Ratings", [])
    for r in ratings:
        src = r.get("Source", "")
        val = r.get("Value", "")
        if "Internet Movie Database" in src:
            imdb_rating = val
        elif "Rotten Tomatoes" in src:
            tomatoes_rating = val
        elif "Metacritic" in src:
            metacritic_rating = val

    return imdb_rating, tomatoes_rating, metacritic_rating


def flatten_omdb_json(data: dict) -> dict:
    """將單支 OMDb JSON 攤平成結構化字典"""
    note = data.get("crawl_note", {})

    imdb_rating, tomatoes_rating, metacritic_rating = extract_ratings(data)

    return {
        "gov_id": note.get("gov_id", ""),
        "gov_title_zh": note.get("gov_title_zh", ""),
        "gov_title_en": note.get("gov_title_en", ""),
        "imdb_id": data.get("imdbID", ""),
        "omdb_title_en": data.get("Title", ""),
        "year": data.get("Year", ""),
        "runtime": data.get("Runtime", ""),
        "genre": data.get("Genre", ""),
        "language": data.get("Language", ""),
        "country": data.get("Country", ""),
        "director": data.get("Director", ""),
        "writer": data.get("Writer", ""),
        "actors": data.get("Actors", ""),
        "plot": data.get("Plot", ""),
        "awards": data.get("Awards", ""),
        "poster": data.get("Poster", ""),
        "imdb_rating": imdb_rating,
        "tomatoes_rating": tomatoes_rating,
        "metacritic_rating": metacritic_rating,
        "source": note.get("source", "omdb"),
        "fetched_at": note.get("fetched_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    }


def combine_weekly_csv(output_dir: str, combined_dir: str, year_label: str, week_label: str):
    """將當週所有 CSV 合併成一支 weekly combined"""
    all_csv = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".csv")]
    if not all_csv:
        print("⚠️ 無可合併的 CSV。")
        return None

    dfs = [pd.read_csv(f, encoding="utf-8") for f in all_csv]
    combined_df = pd.concat(dfs, ignore_index=True)

    weekly_filename = f"omdb_combined_{week_label}.csv"
    weekly_path = os.path.join(output_dir, weekly_filename)
    save_csv(combined_df, output_dir, weekly_filename)
    print(f"📁 已產生週彙整：{weekly_path}")

    return combined_df


def update_all_combined(combined_dir: str, new_df: pd.DataFrame):
    """更新全域合併檔 (omdb_all_YYYY-MM-DD.csv)，自動排重"""
    today_label = datetime.now().strftime("%Y-%m-%d")
    all_filename = f"omdb_all_{today_label}.csv"
    all_path = os.path.join(combined_dir, all_filename)

    if os.path.exists(all_path):
        old_df = pd.read_csv(all_path, encoding="utf-8")
        merged = pd.concat([old_df, new_df], ignore_index=True)
        merged.drop_duplicates(subset=["imdb_id"], inplace=True)
    else:
        merged = new_df

    save_csv(merged, combined_dir, all_filename)
    print(f"📁 已更新全域合併：{all_path}（共 {len(merged)} 筆）")


# -------------------------------------------------------
# 主清洗流程
# -------------------------------------------------------
def clean_omdb_data():
    if not os.path.exists(RAW_DIR):
        print(f"⚠️ 找不到原始資料夾：{RAW_DIR}")
        return

    json_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".json")]
    if not json_files:
        print("⚠️ 無可清洗的 JSON 檔案。")
        return

    print(f"🚀 開始清洗 OMDb 資料，共 {len(json_files)} 部電影")

    processed_count = 0
    for file_name in json_files:
        file_path = os.path.join(RAW_DIR, file_name)
        data = load_json(file_path)
        if not data:
            print(f"⚠️ 無法讀取或內容空白：{file_name}")
            continue

        flat_data = flatten_omdb_json(data)
        safe_title = clean_filename(flat_data["gov_title_zh"] or "unknown")
        csv_name = f"{flat_data['gov_id']}_{safe_title}_{flat_data['imdb_id']}.csv"

        df = pd.DataFrame([flat_data])
        save_csv(df, PROCESSED_DIR, csv_name)
        processed_count += 1

    print(f"✅ 清洗完成，共處理 {processed_count} 筆資料。")

    # 合併當週資料
    weekly_df = combine_weekly_csv(PROCESSED_DIR, COMBINED_DIR, YEAR_LABEL, WEEK_LABEL)
    if weekly_df is not None:
        update_all_combined(COMBINED_DIR, weekly_df)

    print("🎉 OMDb 清洗流程完成！")


# -------------------------------------------------------
# 主程式執行區
# -------------------------------------------------------
if __name__ == "__main__":
    clean_omdb_data()
