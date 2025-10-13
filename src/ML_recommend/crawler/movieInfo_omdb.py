"""
目標：利用英文片名撈取OMDB的電影資料
----------------------------------
用途：
    以政府公開資料中的英文片名，查詢 OMDb API 取得電影資料。
    儲存於 data/raw/movieInfo_omdb 下的 JSON 檔。

資料來源：
    http://www.omdbapi.com/?apikey=<>&i=<IMDb參數&t=<>&plot=full

輸入來源：
    data/processed/movieInfo_gov 內的 JSON 檔。

輸出：
    data/raw/movieInfo_omdb/<gov_id>_<中文名>_<英文名>.json
"""

# -------------------------------------------------------
# 套件匯入
# -------------------------------------------------------
import os
import json
import time
import logging
import requests
import pandas as pd
from tqdm import tqdm
from urllib.parse import quote
from dotenv import load_dotenv
from datetime import datetime

# 共用模組
from common.file_utils import clean_filename, save_json, ensure_dir
from common.path_utils import (
    MANUAL_FIX_DIR,
    MOVIEINFO_GOV_PROCESSED,
    MOVIEINFO_OMDb_RAW,
    LOG_DIR,
)

# -------------------------------------------------------
# 全域設定
# -------------------------------------------------------
load_dotenv()
API_KEY = os.getenv("OMDB_API_KEY")
LOG_PATH = os.path.join(LOG_DIR, "omdb.log")
FIX_MAPPING_FILE = os.path.join(MANUAL_FIX_DIR, "fix_omdb_mapping.json")
manual_mapping = []
error_records = []  # 儲存略過與異常資料

if os.path.exists(FIX_MAPPING_FILE):
    with open(FIX_MAPPING_FILE, "r", encoding="utf-8") as f:
        manual_mapping = json.load(f)

# 建立 logger
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)
ensure_dir(MOVIEINFO_OMDb_RAW)


# -------------------------------------------------------
# 工具函式
# -------------------------------------------------------
def find_manual_imdb_id(gov_id):
    """從人工 mapping 尋找對應 IMDb ID"""
    for item in manual_mapping:
        if str(item.get("gov_id")) == str(gov_id):
            return item.get("imdb_id")
    return None


def fetch_omdb_data(title_en: str) -> dict:
    """以英文片名查詢 OMDb API"""
    url = f"https://www.omdbapi.com/?apikey={API_KEY}&t={quote(title_en)}&plot=full"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ API 請求失敗：{title_en} | {e}")
        return {"Response": "False", "Error": str(e)}


def fetch_omdb_data_by_imdb_id(imdb_id: str) -> dict:
    """以 IMDb ID 查詢 OMDb API"""
    url = f"https://www.omdbapi.com/?apikey={API_KEY}&i={imdb_id}&plot=full"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ 以 IMDb ID 查詢失敗：{imdb_id} | {e}")
        return {"Response": "False", "Error": str(e)}


# -------------------------------------------------------
# 主流程
# -------------------------------------------------------
def crawl_omdb():
    """主函式：遍歷政府電影資料，呼叫 OMDb API 並儲存結果"""
    if not API_KEY:
        raise ValueError("❌ 無法取得 OMDB_API_KEY，請確認 .env 檔是否設定。")

    gov_files = [f for f in os.listdir(MOVIEINFO_GOV_PROCESSED) if f.endswith(".csv")]
    if not gov_files:
        print(f"⚠️ 找不到 movieInfo_gov 資料：{MOVIEINFO_GOV_PROCESSED}")
        return

    print(f"🚀 開始爬取 OMDb 資料，共 {len(gov_files)} 部電影")

    for file_name in tqdm(gov_files, desc="OMDb Fetching", ncols=90):
        gov_path = os.path.join(MOVIEINFO_GOV_PROCESSED, file_name)
        atmovies_id = gov_path.split("_")[-1].replace(".csv", "")

        try:
            df = pd.read_csv(gov_path)
            # 檢查 data\processed\movieInfo_gov 下的 csv 有資料
            if df.empty:
                    msg = f"[略過] 空 CSV：{file_name}"
                    print(msg)
                    logging.warning(msg)
                    error_records.append({
                        "type": "empty_csv",
                        "file": file_name,
                        "reason": "空 CSV",
                        "gov_id": None,
                        "gov_title_zh": None,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
                    continue

            row = df.iloc[0]
            gov_id = str(row.get("gov_id") or "")
            gov_title_zh = clean_filename(str(row.get("gov_title_zh", "未知")))
            gov_title_en = str(row.get("gov_title_en") or "").strip()

            # 篩掉已爬取過的電影
            existing_files = os.listdir(MOVIEINFO_OMDb_RAW)
            already_exists = any(f.startswith(f"{gov_id}_") for f in existing_files)
            if already_exists:
                logging.info(f"[略過] 已存在檔案：{gov_id} {gov_title_zh} ({gov_title_en})")
                continue
            
            # 不爬無英文片名的電影
            if not gov_title_en:
                msg = f"[略過] 無英文片名：{gov_id} {gov_title_zh}"
                print(msg)
                logging.warning(msg)
                error_records.append({
                    "type": "missing_en_title",
                    "gov_id": gov_id,
                    "gov_title_zh": gov_title_zh,
                    "reason": "無英文片名",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                continue

            # ------------------ 開始爬取資料 ------------------
            # 優先使用人工 IMDb ID
            imdb_id = find_manual_imdb_id(gov_id)
            if imdb_id:
                data = fetch_omdb_data_by_imdb_id(imdb_id)
            else:
                data = fetch_omdb_data(gov_title_en)

            # 若仍查不到，嘗試補救
            if data.get("Response") == "False" and not imdb_id:
                imdb_id = find_manual_imdb_id(gov_id)
                if imdb_id:
                    data = fetch_omdb_data_by_imdb_id(imdb_id)

            # 若有成功找到 IMDb ID，就更新
            imdb_id = data.get("imdbID") or imdb_id or "no_imdb"

            # 🔸 加上爬取資訊區塊
            data["crawl_note"] = {
                "gov_id": gov_id,
                "atmovies_id": atmovies_id,
                "gov_title_zh": gov_title_zh,
                "gov_title_en": gov_title_en,
                "imdb_id": imdb_id,
                "source": "omdb",
                "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 🔸 儲存檔案
            filename = f"{gov_id}_{gov_title_zh}_{imdb_id}.json"
            save_json(data, MOVIEINFO_OMDb_RAW, filename)
            time.sleep(1.2)

            if data.get("Response") == "True":
                rating = data.get("imdbRating", "N/A")
                votes = data.get("imdbVotes", "N/A")
                logging.info(f"[成功] {gov_id} {gov_title_zh} ({gov_title_en}) IMDb: {rating} ({votes})")
            else:
                error_msg = data.get("Error", "未知錯誤")
                logging.warning(f"[查無資料] {gov_id} {gov_title_zh} ({gov_title_en}) | {error_msg}")

        except Exception as e:
            logging.error(f"[例外] {file_name} 發生錯誤：{e}")
            continue

    print("✅ OMDb 資料抓取完成，已儲存於 data/raw/movieInfo_omdb/")


# -------------------------------------------------------
# 執行區
# -------------------------------------------------------
if __name__ == "__main__":
    crawl_omdb()

    # === 結尾：輸出異常紀錄 ===
    if error_records:
        error_dir = os.path.join(MOVIEINFO_OMDb_RAW, "error")
        ensure_dir(error_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        error_file = os.path.join(error_dir, f"error_{timestamp}.json")
        save_json(error_records, error_dir, f"error_{timestamp}.json")
        print(f"⚠️ 已輸出 {len(error_records)} 筆異常記錄至：{error_file}")
    else:
        print("✅ 無異常記錄")
