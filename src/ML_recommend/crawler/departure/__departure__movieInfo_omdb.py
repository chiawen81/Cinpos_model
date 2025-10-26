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
import requests
import pandas as pd
from tqdm import tqdm
from urllib.parse import quote
from dotenv import load_dotenv
from datetime import datetime

# 共用模組
from common.file_utils import clean_filename, save_json, ensure_dir  # ✅ 已存在共用邏輯
from common.path_utils import MANUAL_FIX_DIR, MOVIEINFO_GOV_PROCESSED, OMDB_RAW, LOG_DIR


# -------------------------------------------------------
# 全域設定
# -------------------------------------------------------
load_dotenv()
API_KEY = os.getenv("OMDB_API_KEY")
LOG_PATH = os.path.join(LOG_DIR, "omdb.log")
FIX_MAPPING_FILE = os.path.join(MANUAL_FIX_DIR, "fix_omdb_mapping.json")
manual_mapping = (
    json.load(open(FIX_MAPPING_FILE, "r", encoding="utf-8"))
    if os.path.exists(FIX_MAPPING_FILE)
    else []
)
error_records = []  # 儲存略過與異常資料

# 確定目錄存在
ensure_dir(OMDB_RAW)


# -------------------------------------------------------
# 工具函式
# -------------------------------------------------------
def save_error(error_type: str, reason: str, extra: dict = None):
    """統一記錄錯誤與寫入 error_records"""
    record = {
        "type": error_type,
        "reason": reason,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if extra:
        record.update(extra)
    error_records.append(record)


def find_manual_imdb_id(gov_id: str) -> dict:
    """從人工 mapping 尋找對應 IMDb ID"""
    for item in manual_mapping:
        if str(item.get("gov_id")) == str(gov_id):
            return {"imdb_id": item.get("imdb_id"), "is_matched": True}
    return {"imdb_id": "", "is_matched": False}


def fetch_omdb(api_param: str, by: str = "title") -> dict:
    """統一封裝 OMDb API 請求邏輯"""
    if by == "title":
        url = f"https://www.omdbapi.com/?apikey={API_KEY}&t={quote(api_param)}&plot=full"
    else:
        url = f"https://www.omdbapi.com/?apikey={API_KEY}&i={api_param}&plot=full"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"Response": "False", "Error": str(e)}


def should_skip_existing(gov_id: str, folder: str) -> bool:
    """檢查電影是否已爬取過"""
    return any(f.startswith(f"{gov_id}_") for f in os.listdir(folder))


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
            # -------------------------------------------------
            # 前置檢查
            # -------------------------------------------------
            # 檢查 data\processed\movieInfo_gov 下的 csv 有資料
            if df.empty:
                save_error("empty_csv", f"空 CSV：{file_name}", {"error_file": file_name})
                continue

            row = df.iloc[0]
            gov_id = str(row.get("gov_id") or "")
            gov_title_zh = clean_filename(str(row.get("gov_title_zh")))
            gov_title_en = str(row.get("gov_title_en") or "").strip()
            gov_file_info = {
                "gov_id": gov_id,
                "gov_title_zh": gov_title_zh,
                "gov_title_en": gov_title_en,
            }

            # 檢查是否已存在
            if should_skip_existing(gov_id, OMDB_RAW):
                print(f"[略過] 已存在檔案：{gov_id} {gov_title_zh} ({gov_title_en})")
                continue

            # 不爬無英文片名的電影
            if not gov_title_en:
                save_error(
                    "missing_en_title",
                    "無英文片名",
                    gov_file_info,
                )
                continue

            # -------------------------------------------------
            # 開始爬取資料
            # -------------------------------------------------
            # 優先用人工 mapping
            mapping = find_manual_imdb_id(gov_id)
            imdb_id = mapping["imdb_id"]

            if imdb_id:
                # 第二次爬取：已加入至人工對照表，直接用 IMDb ID 查
                data = fetch_omdb(imdb_id, by="id")
            else:
                if mapping["is_matched"] == True:
                    save_error(
                        "omdb查不到資料(已記錄在人工對照表)", "OMDb 查不到資料", gov_file_info
                    )
                    continue
                else:
                    # 第一次爬取：以英文片名查詢
                    data = fetch_omdb(gov_title_en, by="title")

                    if data.get("Response") == "False":
                        save_error("Movie not found", "OMDb 查不到資料", gov_file_info)
                        continue

            # -------------------------------------------------
            # 儲存成功結果
            # -------------------------------------------------
            if data.get("Response") == "True" and data.get("imdbID"):
                imdb_id = data["imdbID"]
                rating = data.get("imdbRating", "")
                votes = data.get("imdbVotes", "")
                print(f"[成功] {gov_id} {gov_title_zh} ({gov_title_en}) IMDb: {rating} ({votes})")

                # 加上爬取資訊區塊
                data["crawl_note"] = {
                    "gov_id": gov_id,
                    "atmovies_id": atmovies_id,
                    "gov_title_zh": gov_title_zh,
                    "gov_title_en": gov_title_en,
                    "imdb_id": imdb_id,
                    "source": "omdb",
                    "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                # 儲存檔案
                filename = f"{gov_id}_{gov_title_zh}_{imdb_id}.json"
                save_json(data, OMDB_RAW, filename)
                time.sleep(1.2)

            else:
                save_error(
                    "未知錯誤",
                    data.get("Error", "未知錯誤"),
                    gov_file_info,
                )

        except Exception as e:
            save_error(
                "例外錯誤",
                str(e),
                gov_file_info,
            )
            continue

    print("✅ OMDb 資料抓取完成，已儲存於 data/raw/movieInfo_omdb/")


# -------------------------------------------------------
# 執行區
# -------------------------------------------------------
if __name__ == "__main__":
    crawl_omdb()

    # === 結尾：輸出異常紀錄 ===
    if error_records:
        error_dir = os.path.join(OMDB_RAW, "error")
        ensure_dir(error_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_json(error_records, error_dir, f"error_{timestamp}.json")
        print(f"⚠️ 已輸出 {len(error_records)} 筆異常記錄至 error_{timestamp}.json")
    else:
        print("✅ 無異常記錄")
