"""
OMDb 評分資料清洗模組
-------------------------------------------------
🎯 目標：
    讀取 data/raw/omdb/<year>/<week>/ 下的 JSON，
    提取評分相關欄位（IMDb / Rotten / Metacritic），
    輸出逐部電影的歷史評分紀錄。

📂 資料流：
    input  : data/raw/omdb/<year>/<week>/
    output : data/processed/rating_omdb/<gov_id>_<title_zh>_<imdb_id>.csv
"""

# -------------------------------------------------------
# 套件匯入
# -------------------------------------------------------
import os
import pandas as pd
from datetime import datetime

# 共用模組
from common.path_utils import OMDB_RAW, RATING_OMDB_PROCESSED
from common.file_utils import ensure_dir, load_json, save_csv, clean_filename
from common.date_utils import get_current_year_label, get_current_week_label


# -------------------------------------------------------
# 全域設定
# -------------------------------------------------------
YEAR_LABEL = get_current_year_label()
WEEK_LABEL = get_current_week_label()

RAW_DIR = os.path.join(OMDB_RAW, YEAR_LABEL, WEEK_LABEL)
RATING_PROCESSED_DIR = RATING_OMDB_PROCESSED

ensure_dir(RATING_PROCESSED_DIR)


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


def build_rating_row(data: dict) -> dict:
    """從單支 OMDb JSON 提取評分資料"""
    note = data.get("crawl_note", {})
    imdb_rating, tomatoes_rating, metacritic_rating = extract_ratings(data)

    # --- 明確區分兩個時間來源 ---
    crawl_date = note.get("fetched_at", "")  # 爬蟲撈資料的時間
    update_at = datetime.now().strftime("%Y/%m/%d %H:%M")  # 清洗寫入時間

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
    }


def update_movie_rating_csv(row: dict, output_dir: str):
    """
    若該電影已有歷史紀錄，則追加一行；
    若無，則建立新檔案。
    """
    gov_id = row["gov_id"]
    imdb_id = row["imdb_id"]
    safe_title = clean_filename(row.get("gov_title_zh", ""))
    filename = f"{gov_id}_{safe_title}_{imdb_id}.csv"
    file_path = os.path.join(output_dir, filename)

    # 若檔案已存在，載入後追加
    if os.path.exists(file_path):
        old_df = pd.read_csv(file_path, encoding="utf-8")
        new_df = pd.DataFrame([row])
        merged_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        merged_df = pd.DataFrame([row])

    save_csv(merged_df, output_dir, filename)
    print(f"📄 已更新評分紀錄：{filename}（共 {len(merged_df)} 筆）")


# -------------------------------------------------------
# 主清洗流程
# -------------------------------------------------------
def clean_omdb_ratings():
    """主清洗流程"""
    if not os.path.exists(RAW_DIR):
        print(f"⚠️ 找不到原始資料夾：{RAW_DIR}")
        return

    json_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".json")]
    if not json_files:
        print("⚠️ 無可清洗的 JSON 檔案。")
        return

    print(f"🚀 開始清洗 OMDb 評分資料，共 {len(json_files)} 部電影")

    processed_count = 0
    for file_name in json_files:
        file_path = os.path.join(RAW_DIR, file_name)
        data = load_json(file_path)
        if not data:
            print(f"⚠️ 無法讀取或內容空白：{file_name}")
            continue

        note = data.get("crawl_note", {})
        row = build_rating_row(data)
        row["gov_title_zh"] = note.get("gov_title_zh", "")

        update_movie_rating_csv(row, RATING_PROCESSED_DIR)
        processed_count += 1

    print(f"✅ 清洗完成，共處理 {processed_count} 筆資料。")
    print("🎉 OMDb 評分清洗流程完成！")


# -------------------------------------------------------
# 主程式執行區
# -------------------------------------------------------
if __name__ == "__main__":
    clean_omdb_ratings()
