"""
IMDb / OMDb 評分資料爬取
----------------------------------
目標：
    撈取當週首輪電影的 IMDb / OMDb 評分資料

步驟：
    step1. 讀取當週《首輪電影名單》
    step2. 承上，根據 atmovies_id 找出對應 imdb_id
    step3. 呼叫 OMDb API，取得 imdbRating、imdbVotes、Metascore、Ratings 等評分資料

爬蟲目標API：
   https://www.omdbapi.com/?apikey=<OMDB_API_KEY>6&i=<IMDB_ID>&plot=full

輸入來源：
    - 取得當周首輪電影：data/processed/firstRunFilm_list/<當周>/firstRun_<當周>.csv
    - 取得每部電影對應的imdb ID：data/processed/movieInfo_omdb/movieInfo_omdb_<上次執行日期>.csv

輸出：
    - 成功資料：data/raw/rating_weekly/<當週>/rating_<當週>.json
    - 錯誤紀錄：data/raw/rating_weekly/error/error_<timestamp>.json
"""
# -------------------------------------------------------
# 套件匯入
# -------------------------------------------------------
import os
import json
import time
import requests
import pandas as pd
from datetime import datetime

# 共用模組
from common.path_utils import RATING_WEEKLY_RAW, FIRSTRUN_PROCESSED, MOVIEINFO_OMDb_PROCESSED
from common.file_utils import ensure_dir
from common.date_utils import get_current_week_label


# -------------------------------------------------------
# 全域設定
# -------------------------------------------------------
OMDB_API_KEY = os.getenv("OMDB_API_KEY") or "<YOUR_API_KEY>"
WEEK_LABEL = get_current_week_label()
OUTPUT_DIR = os.path.join(RATING_WEEKLY_RAW, WEEK_LABEL)
ERROR_DIR = os.path.join(RATING_WEEKLY_RAW, "error")
ensure_dir(OUTPUT_DIR)
ensure_dir(ERROR_DIR)


# -------------------------------------------------------
# 工具函式(檢查可抽共用)
# -------------------------------------------------------
def fetch_omdb_rating(imdb_id: str) -> dict:
    """打 OMDb API，取得電影評分資料"""
    url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}&plot=full"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("Response") == "False":
            return {"error": data.get("Error", "Movie not found")}
        return data
    except Exception as e:
        return {"error": str(e)}


def save_json(data: list, path: str):
    """存成 JSON 檔"""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_error(errors: list):
    """輸出錯誤紀錄"""
    if not errors:
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    err_path = os.path.join(ERROR_DIR, f"error_{ts}.json")
    save_json(errors, err_path)
    print(f"⚠️ 已輸出錯誤紀錄：{err_path}")


# ========= 主程式 =========
def fetch_weekly_ratings():
    print(f"🎬 開始撈取 IMDb / OMDb 評分資料（週次：{WEEK_LABEL}）")

    # Step 1️⃣：讀取當週首輪電影清單
    first_run_path = os.path.join(FIRSTRUN_PROCESSED, WEEK_LABEL, f"firstRun_{WEEK_LABEL}.csv")
    if not os.path.exists(first_run_path):
        print(f"❌ 找不到首輪電影清單：{first_run_path}")
        return

    first_run_df = pd.read_csv(first_run_path, encoding="utf-8")
    print(f"📂 首輪電影筆數：{len(first_run_df)}")

    # Step 2️⃣：讀取 OMDb 資料（用於對照 imdb_id）
    omdb_files = [f for f in os.listdir(MOVIEINFO_OMDb_PROCESSED) if f.endswith(".csv")]
    if not omdb_files:
        print(f"❌ 找不到 OMDb 對照資料：{MOVIEINFO_OMDb_PROCESSED}")
        return

    omdb_latest = max(omdb_files, key=lambda x: os.path.getmtime(os.path.join(MOVIEINFO_OMDb_PROCESSED, x)))
    omdb_path = os.path.join(MOVIEINFO_OMDb_PROCESSED, omdb_latest)
    omdb_df = pd.read_csv(omdb_path, encoding="utf-8")
    print(omdb_df)
    print("====================================\n")
    print(f"🔍 使用 OMDb 對照資料：{omdb_latest}")
    print("====================================\n")
    print(first_run_df)

    # 合併 imdb_id
    merged = first_run_df.merge(
        omdb_df[["gov_title_zh", "atmovies_id", "imdb_id"]],
        on="atmovies_id",
        how="left"
    )

    missing = merged[merged["imdb_id"].isna()]
    if not missing.empty:
        print(f"⚠️ 找不到 IMDb ID 的電影：{len(missing)} 筆")
        print("====================================")
        print(merged)
        for _, row in missing.iterrows():
            print(f"  - {row['atmovies_title_zh']} ({row['atmovies_id']})")

    # Step 3️⃣：撈取 IMDb 評分資料
    results = []
    errors = []

    for _, row in merged.iterrows():
        atmovies_id = row["atmovies_id"]
        imdb_id = row["imdb_id"]
        gov_title_zh = row.get("gov_title_zh", "")
        atmovies_title_zh = row.get("atmovies_title_zh", "")

        if not imdb_id or imdb_id == "N/A":
            errors.append({
                "atmovies_id": atmovies_id,
                "atmovies_title_zh": atmovies_title_zh,
                "error": "無 IMDb ID 對應"
            })
            continue

        data = fetch_omdb_rating(imdb_id)
        if "error" in data:
            errors.append({
                "atmovies_id": atmovies_id,
                "imdb_id": imdb_id,
                "gov_title_zh": gov_title_zh,
                "error": data["error"]
            })
            continue

        result = {
            "atmovies_id": atmovies_id,
            "gov_title_zh": gov_title_zh,
            "title": data.get("Title"),
            "year": data.get("Year"),
            "imdb_id": data.get("imdbID"),
            "imdb_rating": data.get("imdbRating"),
            "imdb_votes": data.get("imdbVotes"),
            "metascore": data.get("Metascore"),
            "ratings": data.get("Ratings"),
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        results.append(result)
        print(f"✅ {atmovies_title_zh} ({imdb_id}) - IMDb {result['imdb_rating']}")
        time.sleep(1)  # 避免 API 過載

    # Step 4️⃣：輸出結果
    output_path = os.path.join(OUTPUT_DIR, f"rating_{WEEK_LABEL}.json")
    save_json(results, output_path)
    print(f"\n🎉 IMDb 評分資料已完成，共 {len(results)} 筆\n👉 儲存位置：{output_path}")

    # Step 5️⃣：輸出錯誤紀錄
    log_error(errors)


if __name__ == "__main__":
    fetch_weekly_ratings()