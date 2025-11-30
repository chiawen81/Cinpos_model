"""
OMDb 補爬爬蟲（針對 fix_omdb_mapping_temp.json）
-------------------------------------------------
🎯 目標：
    專門讀取「人工修正暫存表」中的清單，重新爬取指定電影的 OMDb 資料。

📂 資料流：
    input  : data/manual_fix/fix_omdb_mapping_temp.json
    output : data/raw/movieInfo_omdb/<year>/<week>/<gov_id>_<title_zh>_<imdb_id>.json
    error  : data/raw/movieInfo_omdb/error/error_<timestamp>.json

📦 輔助資料：
    - .env → OMDB_API_KEY
"""

# -------------------------------------------------------
# 套件匯入
# -------------------------------------------------------
import os
import json
import time
import requests
from datetime import datetime
from urllib.parse import quote
from dotenv import load_dotenv
from tqdm import tqdm

# 共用模組
from ml.common.path_utils import OMDB_RAW, MANUAL_FIX_DIR
from ml.common.file_utils import ensure_dir, save_json, clean_filename
from ml.common.date_utils import get_year_label, get_week_label


# -------------------------------------------------------
# 全域設定
# -------------------------------------------------------
load_dotenv()
API_KEY = os.getenv("OMDB_API_KEY")

YEAR_LABEL = get_year_label()
WEEK_LABEL = get_week_label()

FIX_MAPPING_TEMP = os.path.join(MANUAL_FIX_DIR, "fix_omdb_mapping_temp.json")

error_records = []
SLEEP_INTERVAL = 1.2

OUTPUT_DIR = os.path.join(OMDB_RAW, YEAR_LABEL, WEEK_LABEL)
ERROR_DIR = os.path.join(OMDB_RAW, "error")
ensure_dir(OUTPUT_DIR)
ensure_dir(ERROR_DIR)


# -------------------------------------------------------
# 工具函式
# -------------------------------------------------------
def save_error(error_type: str, reason: str, extra: dict = None):
    record = {
        "type": error_type,
        "reason": reason,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if extra:
        record.update(extra)
    error_records.append(record)


def fetch_omdb(api_param: str, by: str = "title") -> dict:
    """呼叫 OMDb API"""
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


# -------------------------------------------------------
# 主流程
# -------------------------------------------------------
def refetch_from_temp():
    """主函式：重爬人工暫存對照表中的電影"""
    if not API_KEY:
        raise ValueError("❌ 找不到 OMDB_API_KEY，請確認 .env 是否設定")

    if not os.path.exists(FIX_MAPPING_TEMP):
        print(f"⚠️ 找不到檔案：{FIX_MAPPING_TEMP}")
        return

    # 讀取暫存對照表
    with open(FIX_MAPPING_TEMP, "r", encoding="utf-8") as f:
        fix_list = json.load(f)

    if not fix_list:
        print(f"⚠️ 檔案為空：{FIX_MAPPING_TEMP}")
        return

    print(f"🎯 共 {len(fix_list)} 筆電影需重新爬取 OMDb 資料")
    print(f"📅 週期：{WEEK_LABEL}\n")

    success_count = 0

    for item in tqdm(fix_list, desc="OMDb Refetching", ncols=90):
        try:
            gov_id = str(item.get("gov_id") or "")
            imdb_id = str(item.get("imdb_id") or "").strip()
            gov_title_zh = clean_filename(str(item.get("gov_title_zh") or ""))
            gov_title_en = str(item.get("gov_title_en") or "").strip()

            # 排除無IMDb ID(IMDb 無此電影)
            if not imdb_id:
                save_error("skip_no_imdb_id", "無 IMDb ID（人工標記為無資料）", item)
                print(f"⚠️ 跳過：{gov_id} {gov_title_zh})，因 IMDb 無此電影")
                continue

            # 判斷用哪種方式查
            data = fetch_omdb(imdb_id, by="id")
            fetch_mode = "by_imdb_id_from_temp"

            if data.get("Response") == "True" and data.get("imdbID"):
                imdb_id = data["imdbID"]
                rating = data.get("imdbRating", "")
                votes = data.get("imdbVotes", "")

                print(
                    f"[成功] {gov_title_zh} ({gov_title_en}) - IMDb {rating} ({votes}) [{fetch_mode}]"
                )

                data["crawl_note"] = {
                    "gov_id": gov_id,
                    "gov_title_zh": gov_title_zh,
                    "gov_title_en": gov_title_en,
                    "imdb_id": imdb_id,
                    "source": "omdb",
                    "fetch_mode": fetch_mode,
                    "week_label": WEEK_LABEL,
                    "year_label": YEAR_LABEL,
                    "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                filename = f"{gov_id}_{gov_title_zh}_{imdb_id}.json"
                save_json(data, OUTPUT_DIR, filename)
                success_count += 1

            else:
                save_error("api_error", data.get("Error", "OMDb 回傳失敗"), item)
                print(f"[失敗] {gov_title_zh} ({gov_title_en}) - {data.get('Error', '未知錯誤')}")

        except Exception as e:
            save_error("exception", str(e), item)
            print(f"[例外] {item.get('title_zh')} - {e}")
            continue

        time.sleep(SLEEP_INTERVAL)

    # 統計結果
    print("\n==============================")
    print("🎉 補爬作業完成")
    print(f"✅ 成功：{success_count} 筆")
    print(f"❌ 失敗：{len(error_records)} 筆")
    print(f"📁 輸出資料夾：{OUTPUT_DIR}")
    print("==============================\n")

    # 錯誤輸出
    if error_records:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_json(error_records, ERROR_DIR, f"error_refetch_{timestamp}.json")
        print(f"⚠️ 已輸出錯誤紀錄 {len(error_records)} 筆 → error_refetch_{timestamp}.json")
    else:
        print("✅ 無異常紀錄")


# -------------------------------------------------------
# 主程式執行入口
# -------------------------------------------------------
if __name__ == "__main__":
    refetch_from_temp()
