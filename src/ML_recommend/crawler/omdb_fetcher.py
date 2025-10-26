"""
OMDb 整合爬蟲（Info + Rating）
-------------------------------------------------
🎯 目標：
    以政府《單部電影票房原始資料》為輸入，
    撈取 OMDb 的電影資訊與 IMDb 評分，並整合為單一 JSON。

📂 資料流：
    input  : data/raw/boxoffice_permovie/<year>/<week>/
    output : data/raw/omdb/<year>/<week>/<gov_id>_<title_zh>_<imdb_id>.json
    error  : data/raw/omdb/error/error_<timestamp>.json

📦 輔助資料：
    - .env → OMDB_API_KEY
    - data/manual_fix/fix_omdb_mapping.json （人工對照表）
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
from common.path_utils import (
    BOXOFFICE_PERMOVIE_RAW,
    OMDB_RAW,
    MANUAL_FIX_DIR,
)
from common.file_utils import ensure_dir, save_json, clean_filename, load_json
from common.date_utils import get_current_year_label, get_current_week_label


# -------------------------------------------------------
# 全域設定
# -------------------------------------------------------
load_dotenv()
API_KEY = os.getenv("OMDB_API_KEY")

YEAR_LABEL = get_current_year_label()
WEEK_LABEL = get_current_week_label()

FIX_MAPPING_FILE = os.path.join(MANUAL_FIX_DIR, "fix_omdb_mapping.json")
manual_mapping = (
    json.load(open(FIX_MAPPING_FILE, "r", encoding="utf-8"))
    if os.path.exists(FIX_MAPPING_FILE)
    else []
)

error_records = []  # 儲存略過與異常資料
SLEEP_INTERVAL = 1.2

# 資料夾目錄
INPUT_DIR = os.path.join(BOXOFFICE_PERMOVIE_RAW, YEAR_LABEL, WEEK_LABEL)
OUTPUT_DIR = os.path.join(OMDB_RAW, YEAR_LABEL, WEEK_LABEL)
ERROR_DIR = os.path.join(OMDB_RAW, "error")
# 確定資料夾存在
ensure_dir(OUTPUT_DIR)
ensure_dir(ERROR_DIR)


# -------------------------------------------------------
# 工具函式
# -------------------------------------------------------
def save_error(error_type: str, reason: str, extra: dict = None):
    """統一記錄錯誤訊息"""
    record = {
        "type": error_type,
        "reason": reason,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if extra:
        record.update(extra)
    error_records.append(record)


def find_manual_imdb_id(gov_id: str) -> dict:
    """從人工對照表中尋找 IMDb ID"""
    for item in manual_mapping:
        if str(item.get("gov_id")) == str(gov_id):
            return {"imdb_id": item.get("imdb_id"), "is_matched": True}
    return {"imdb_id": "", "is_matched": False}


def fetch_omdb(api_param: str, by: str = "title") -> dict:
    """呼叫 OMDb API（可用 title 或 id 查詢）"""
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
def crawl_omdb_for_week():
    """主函式：以本週票房電影為基準撈取 OMDb 資料"""
    if not API_KEY:
        raise ValueError("❌ 找不到 OMDB_API_KEY，請確認 .env 是否設定")

    if not os.path.exists(INPUT_DIR):
        print(f"⚠️ 找不到本週票房原始資料夾：{INPUT_DIR}")
        return

    json_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".json")]
    if not json_files:
        print(f"⚠️ 沒有可用的 JSON 檔案：{INPUT_DIR}")
        return

    print(f"🎬 發現 {len(json_files)} 部電影待爬取 OMDb 資料")
    print(f"📅 週期：{WEEK_LABEL}\n")

    success_count = 0

    # 2️⃣ 逐一處理電影
    for file_name in tqdm(json_files, desc="OMDb Fetching", ncols=90):
        file_path = os.path.join(INPUT_DIR, file_name)

        try:
            raw_json = load_json(file_path)
            movie_data = raw_json.get("data", {})
            # -------------------------------------------------
            # 前置檢查
            # -------------------------------------------------
            # 確認 data/raw/boxoffice_permovie/<year>/<week> 有資料
            if not movie_data:
                save_error("empty_json", "無有效內容", {"file": file_name})
                print(f"⚠️ 無有效內容：{file_name}")
                continue

            gov_id = str(movie_data.get("movieId") or "")
            gov_title_zh = clean_filename(str(movie_data.get("name") or ""))
            gov_title_en = str(movie_data.get("originalName") or "").strip()
            gov_file_info = {
                "gov_id": gov_id,
                "gov_title_zh": gov_title_zh,
                "gov_title_en": gov_title_en,
            }

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
                fetch_mode = "by_imdb_id_from_manual_fix"
            else:
                if mapping["is_matched"] == True:
                    save_error(
                        "omdb查不到資料(已記錄在人工對照表)", "OMDb 查不到資料", gov_file_info
                    )
                    continue
                else:
                    # 第一次爬取：以英文片名查詢
                    data = fetch_omdb(gov_title_en, by="title")
                    fetch_mode = "by_title_from_gov"

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

                print(
                    f"[成功] {gov_title_zh} ({gov_title_en}) - IMDb {rating} ({votes}) [{fetch_mode}]"
                )

                # 加上爬取資訊區塊
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

                # 儲存檔案
                file_name_out = f"{gov_id}_{gov_title_zh}_{imdb_id}.json"
                save_json(data, OUTPUT_DIR, file_name_out)
                success_count += 1

            else:
                save_error("api_error", data.get("Error", "OMDb 回傳失敗"), gov_file_info)
                print(f"[失敗] {gov_title_zh} ({gov_title_en}) - {data.get('Error', '未知錯誤')}")

        except Exception as e:
            save_error("exception", str(e), {"file": file_name})
            print(f"[例外] {file_name} - {e}")
            continue

        time.sleep(SLEEP_INTERVAL)

    # 4️⃣ 統計輸出
    print("\n==============================")
    print("🎉 本週 OMDb 資料抓取完成")
    print(f"📅 週期：{WEEK_LABEL}")
    print(f"✅ 成功：{success_count} 筆")
    print(f"❌ 失敗：{len(error_records)} 筆")
    print(f"📁 輸出資料夾：{OUTPUT_DIR}")
    print("==============================\n")

    # 5️⃣ 輸出錯誤紀錄
    if error_records:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_json(error_records, ERROR_DIR, f"error_{timestamp}.json")
        print(f"⚠️ 已輸出錯誤紀錄 {len(error_records)} 筆 → error_{timestamp}.json")
    else:
        print("✅ 無異常紀錄")


# -------------------------------------------------------
# 主程式執行入口
# -------------------------------------------------------
if __name__ == "__main__":
    crawl_omdb_for_week()
