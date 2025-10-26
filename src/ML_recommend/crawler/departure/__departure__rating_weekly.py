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

# ———————————————————————————————————— 套件匯入 ————————————————————————————————————
import os
import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# 共用模組
from common.path_utils import RATING_WEEKLY_RAW, FIRSTRUN_PROCESSED, OMDB_PROCESSED
from common.file_utils import ensure_dir, save_json
from common.date_utils import get_current_week_label, create_timestamped


# ———————————————————————————————————— 全域設定 ————————————————————————————————————
load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
WEEK_LABEL = get_current_week_label()
OUTPUT_DIR = os.path.join(RATING_WEEKLY_RAW, WEEK_LABEL)
ERROR_DIR = os.path.join(RATING_WEEKLY_RAW, "error")
ensure_dir(OUTPUT_DIR)
ensure_dir(ERROR_DIR)


# ———————————————————————————————————— 工具函式 ————————————————————————————————————
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


def create_error_record(errors: list):
    """輸出錯誤紀錄"""
    if errors:
        fileName = f"error_{create_timestamped()}.json"

        for row in errors:
            print(f"  - {row['atmovies_title_zh']} (atmovies_id：{row['atmovies_id']})")
        save_json(errors, ERROR_DIR, fileName, "<錯誤紀錄>")


# ———————————————————————————————————— 主程式 ————————————————————————————————————
def fetch_weekly_ratings():
    print(f"🎬 開始撈取 IMDb / OMDb 評分資料（週次：{WEEK_LABEL}）")
    errors_record = []  # 異常資料

    # --------------------------------------------
    # Step 1：讀取當週首輪電影清單
    # --------------------------------------------
    first_run_path = os.path.join(FIRSTRUN_PROCESSED, WEEK_LABEL, f"firstRun_{WEEK_LABEL}.csv")
    ### 處理例外狀況1：無本周首輪電影清單
    if not os.path.exists(first_run_path):
        print(f"❌ 找不到首輪電影清單：{first_run_path}")
        return

    first_run_df = pd.read_csv(first_run_path, encoding="utf-8")
    print(f"📂 首輪電影筆數：{len(first_run_df)}")

    # --------------------------------------------
    # Step 2：讀取現有 OMDb 資料
    # --------------------------------------------
    omdb_files = [f for f in os.listdir(OMDB_PROCESSED) if f.endswith(".csv")]

    ### 處理例外狀況2：無movieInfo_omdb_*.csv
    if not omdb_files:
        print(f"❌ 找不到 OMDb 對照資料：{OMDB_PROCESSED}")
        return

    # 取得最新的 movieInfo_omdb_*.csv
    omdb_latest = max(omdb_files, key=lambda x: os.path.getmtime(os.path.join(OMDB_PROCESSED, x)))

    # 讀取最新的 CSV 檔成為 pandas.DataFrame
    omdb_path = os.path.join(OMDB_PROCESSED, omdb_latest)
    omdb_df = pd.read_csv(omdb_path, encoding="utf-8")
    print("====================================")
    print(f"🔍 使用 OMDb 對照資料：{omdb_latest}")
    print("====================================\n")

    # --------------------------------------------
    # Step 3：合併兩張資料表(本周首輪名單、omdb)
    # --------------------------------------------
    merged = first_run_df.merge(
        omdb_df[["gov_id", "atmovies_id", "imdb_id", "omdb_title_en"]],
        on="atmovies_id",
        how="left",
    )
    """NOTE:
        1. 鏈接欄位：用 atmovies_id 這個欄位做「左連接（left join）」：
        2. 左右表：
            - 左表是本週的首輪電影清單(first_run_df)
            - 右表是 OMDb 的完整資料(omdb_df)
        3. 挑出 omdb_df 中的相關欄位合併至 first_run_df：
            => omdb_df[["gov_id", "imdb_id",......]],
            => 鏈接欄位須包含在 omdb_df 中（atmovies_id）
    """

    # --------------------------------------------
    # Step 4：重新爬 OMDB 資料 (取得最新評分資料)
    # --------------------------------------------
    omdb_rating_data = []

    for _, row in merged.iterrows():
        imdb_id = row["imdb_id"] or ""
        atmovies_title_zh = row.get("atmovies_title_zh") or ""

        ##### 寫入錯誤訊息：無gov_id/imdb/omdb資料
        if not row["gov_id"] or pd.isna(row["gov_id"]):
            errors_record.append(
                {
                    "atmovies_id": row["atmovies_id"],
                    "atmovies_title_zh": row["atmovies_title_zh"],
                    "gov_id": "",
                    "imdb_id": "",
                    "errorType": "without gov_id/imdb/omdb data",
                    "errorMsg": "無資料(須看fix_omdb_mapping.json確認)",
                }
            )
            continue

        # 爬 OMDb 資料
        omdb_crawler_data = fetch_omdb_rating(imdb_id)

        ##### 寫入錯誤訊息：API錯誤
        if "Error" in omdb_crawler_data:
            print(f"❌ {atmovies_title_zh}- {omdb_crawler_data['error']}")
            errors_record.append(
                {
                    "atmovies_id": row["atmovies_id"],
                    "atmovies_title_zh": atmovies_title_zh,
                    "gov_id": row["gov_id"],
                    "imdb_id": imdb_id,
                    "errorType": "API response error",
                    "errorMsg": omdb_crawler_data["error"],
                }
            )
            continue

        # --------------------------------------------
        # Step 5：整理資料
        # --------------------------------------------
        # 本次執行資訊
        crawl_note = {
            "gov_id": row["gov_id"],
            "atmovies_id": row["atmovies_id"],
            "atmovies_title_zh": atmovies_title_zh,
            "imdb_id": imdb_id,
            "source": "omdb",
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 整理撈回的資料
        omdb_rating_data.append(
            {
                "title": omdb_crawler_data.get("Title"),
                "year": omdb_crawler_data.get("Year"),
                "imdb_id": omdb_crawler_data.get("imdbID"),
                "imdb_rating": omdb_crawler_data.get("imdbRating"),
                "imdb_votes": omdb_crawler_data.get("imdbVotes"),
                "metascore": omdb_crawler_data.get("Metascore"),
                "ratings": omdb_crawler_data.get("Ratings"),
                "crawl_note": crawl_note,
            }
        )
        print(f"✔️ 已取得資料：{atmovies_title_zh}")
        time.sleep(1)  # 避免 API 過載

    # --------------------------------------------
    # Step 6：輸出結果
    # --------------------------------------------
    fileName = f"rating_{WEEK_LABEL}.json"

    # 輸出成功資料
    save_json(omdb_rating_data, OUTPUT_DIR, fileName, "<成功資料>")
    print(
        f"""\n
🎉 IMDb 評分資料已完成
📂 首輪電影筆數：{len(first_run_df)}
📂 成功資料，共 {len(omdb_rating_data)} 筆
📂 異常資料，共 {len(errors_record)} 筆 """
    )

    # 輸出錯誤紀錄
    create_error_record(errors_record)


# ———————————————————————————————————— 主程式執行入口 ————————————————————————————————————
if __name__ == "__main__":
    fetch_weekly_ratings()
