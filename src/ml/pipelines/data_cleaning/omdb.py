"""
OMDb 清洗 + 評分資料整併模組
-------------------------------------------------
🎯 目標：
    讀取 data/raw/omdb/<year>/<week>/ 下的 JSON，
    同步清洗出兩份資料：
        (1) 電影完整資訊 → processed/movieInfo_omdb
        (2) 評分歷史資料 → processed/rating_omdb

📂 資料流：
    input  : data/raw/omdb/<year>/<week>/
    output :
        - data/processed/movieInfo_omdb/<gov_id>_<title_zh>_<imdb_id>.csv
        - data/processed/movieInfo_omdb/combined/movieInfo_omdb_full_<date>.csv
        - data/processed/rating_omdb/<gov_id>_<title_zh>_<imdb_id>.csv
"""

# -------------------------------------------------------
# 套件匯入
# -------------------------------------------------------
import os
import pandas as pd
from datetime import datetime

# 共用模組
from ml.common.path_utils import (
    OMDB_RAW,
    RATING_OMDB_PROCESSED,
    RATING_OMDB_PROCESSED,
)
from ml.common.file_utils import ensure_dir, load_json, save_csv, clean_filename
from ml.common.date_utils import get_year_label, get_week_label

# -------------------------------------------------------
# 全域設定
# -------------------------------------------------------
YEAR_LABEL = get_year_label()
WEEK_LABEL = get_week_label()

RAW_DIR = os.path.join(OMDB_RAW, YEAR_LABEL, WEEK_LABEL)
MOVIEINFO_DIR = RATING_OMDB_PROCESSED
MOVIEINFO_COMBINED_DIR = os.path.join(MOVIEINFO_DIR, "combined")
RATING_DIR = RATING_OMDB_PROCESSED

ensure_dir(MOVIEINFO_DIR)
ensure_dir(MOVIEINFO_COMBINED_DIR)
ensure_dir(RATING_DIR)


# -------------------------------------------------------
# 輔助函式
# -------------------------------------------------------
def extract_ratings(data: dict):
    """拆解 Ratings 欄位成 imdb/tomatoes/metacritic 三欄"""
    imdb_rating = ""
    tomatoes_rating = ""
    metacritic_rating = ""

    for r in data.get("Ratings", []):
        src, val = r.get("Source", ""), r.get("Value", "")
        if "Internet Movie Database" in src:
            imdb_rating = val
        elif "Rotten Tomatoes" in src:
            tomatoes_rating = val
        elif "Metacritic" in src:
            metacritic_rating = val

    return imdb_rating, tomatoes_rating, metacritic_rating


# ---------------- movieInfo_omdb ----------------
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


def combine_all_csv(processed_dir: str, combined_dir: str):
    """合併全部 processed/movieInfo_omdb 下的 CSV 成 movieInfo_omdb_full_<date>.csv"""
    all_csv = [
        os.path.join(processed_dir, f) for f in os.listdir(processed_dir) if f.endswith(".csv")
    ]
    if not all_csv:
        print("⚠️ 無可合併的 CSV 檔案。")
        return None

    dfs = [pd.read_csv(f, encoding="utf-8") for f in all_csv]
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.drop_duplicates(subset=["imdb_id"], inplace=True)

    today_label = datetime.now().strftime("%Y-%m-%d")
    filename = f"movieInfo_omdb_full_{today_label}.csv"
    save_csv(combined_df, combined_dir, filename)

    print(f"📁 已產生全域合併：{os.path.join(combined_dir, filename)}")
    print(f"　共 {len(combined_df)} 筆資料")
    return combined_df


# ---------------- rating_omdb ----------------
def build_rating_row(data: dict) -> dict:
    """從單支 OMDb JSON 提取評分資料"""
    note = data.get("crawl_note", {})
    imdb_rating, tomatoes_rating, metacritic_rating = extract_ratings(data)

    crawl_date = note.get("fetched_at", "")  # 爬蟲撈資料的時間
    update_at = datetime.now().strftime("%Y/%m/%d %H:%M")  # 寫入時間

    return {
        "gov_id": note.get("gov_id", ""),
        "imdb_id": note.get("imdb_id", ""),
        "week_label": note.get("week_label", ""),
        "crawl_date": crawl_date,
        "imdb_rating": imdb_rating,
        "tomatoes_rating": tomatoes_rating,
        "metacritic_rating": metacritic_rating,
        "source": note.get("source", "omdb"),
        "update_at": update_at,
        "gov_title_zh": note.get("gov_title_zh", ""),
    }


def update_movie_rating_csv(row: dict, output_dir: str):
    """若該電影已有歷史紀錄，則追加一行；若無則新建。"""
    gov_id = row["gov_id"]
    imdb_id = row["imdb_id"]
    safe_title = clean_filename(row.get("gov_title_zh", "unknown"))
    filename = f"{gov_id}_{safe_title}_{imdb_id}.csv"
    file_path = os.path.join(output_dir, filename)

    if os.path.exists(file_path):
        old_df = pd.read_csv(file_path, encoding="utf-8")
        merged_df = pd.concat([old_df, pd.DataFrame([row])], ignore_index=True)
    else:
        merged_df = pd.DataFrame([row])

    save_csv(merged_df, output_dir, filename)
    print(f"📄 已更新評分紀錄：{filename}（共 {len(merged_df)} 筆）")


# -------------------------------------------------------
# 主清洗流程
# -------------------------------------------------------
def clean_omdb_all():
    if not os.path.exists(RAW_DIR):
        print(f"⚠️ 找不到原始資料夾：{RAW_DIR}")
        return

    json_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".json")]
    if not json_files:
        print("⚠️ 無可清洗的 JSON 檔案。")
        return

    print(f"🚀 開始清洗 OMDb 資料，共 {len(json_files)} 部電影")

    count_movieinfo = 0
    count_rating = 0

    for file_name in json_files:
        file_path = os.path.join(RAW_DIR, file_name)
        data = load_json(file_path)
        if not data:
            print(f"⚠️ 無法讀取或內容空白：{file_name}")
            continue

        # --- 輸出 movieInfo_omdb ---
        flat_data = flatten_omdb_json(data)
        safe_title = clean_filename(flat_data["gov_title_zh"] or "unknown")
        movie_filename = f"{flat_data['gov_id']}_{safe_title}_{flat_data['imdb_id']}.csv"
        save_csv(pd.DataFrame([flat_data]), MOVIEINFO_DIR, movie_filename)
        count_movieinfo += 1

        # --- 輸出 rating_omdb ---
        rating_row = build_rating_row(data)
        update_movie_rating_csv(rating_row, RATING_DIR)
        count_rating += 1

    print(f"✅ 電影資料清洗完成，共 {count_movieinfo} 筆。")
    print(f"✅ 評分資料清洗完成，共 {count_rating} 筆。")

    # 整併全部 movieInfo_omdb
    combine_all_csv(MOVIEINFO_DIR, MOVIEINFO_COMBINED_DIR)
    print("🎉 OMDb 清洗與評分資料輸出完成！")


# -------------------------------------------------------
# 主程式執行區
# -------------------------------------------------------
if __name__ == "__main__":
    clean_omdb_all()
