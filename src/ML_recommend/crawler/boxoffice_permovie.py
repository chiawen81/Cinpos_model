"""
政府公開資料：《全國電影票房統計資訊》爬蟲
------------------------------------------------
目標：
    以開眼電影網的首輪電影名單（存在 Cinpos_model/data）為基準，
    前往《全國電影票房統計資訊》查詢該電影的票房統計資料。

資料來源：
    1. 首輪電影名單：開眼電影網
                   （已存在於 data\processed\firstRunFilm_list）
    2. 政府電影票房統計：
        (1) 搜尋電影 ID：
            https://boxofficetw.tfai.org.tw/film/sf?keyword=<電影名>
        (2) 取得票房資料：
            https://boxofficetw.tfai.org.tw/film/gfd/<電影id>
"""

# ========= 套件匯入 =========
import os
import re
import time
import json
import requests
import pandas as pd
from urllib.parse import quote

# 共用模組
from common.path_utils import FIRSTRUN_PROCESSED, BOXOFFICE_PERMOVIE_RAW
from common.network_utils import get_default_headers
from common.file_utils import ensure_dir, save_json
from common.date_utils import get_current_week_label


# ========= 全域設定 =========
SEARCH_URL = "https://boxofficetw.tfai.org.tw/film/sf?keyword="
DETAIL_URL = "https://boxofficetw.tfai.org.tw/film/gfd/"
HEADERS = get_default_headers()
TIMEOUT = 10
SLEEP_INTERVAL = 1.2  # 避免連續請求過快被限制


# ========= 輔助函式 =========
# 抓電影 ID
def search_film_id(keyword: str) -> str | None:
    """根據電影名稱查詢政府資料庫中的電影 ID"""
    try:
        res = requests.get(SEARCH_URL + quote(keyword), headers=HEADERS, timeout=TIMEOUT)
        res.encoding = "utf-8"
        data = res.json()
        print(f"🔍 查詢結果(資料)：{data}")

        try:
            film_id = data["data"]["results"][0]["movieId"]
            print(f"🔍 查詢結果(電影ID)：{film_id}")
            return film_id
        except (KeyError, TypeError, IndexError):
            return None

    except Exception as e:
        print(f"❌ 查詢ID失敗：{keyword} ({e})")
        return None


# 抓票房資料
def fetch_boxoffice_data(film_id: str) -> dict | None:
    """根據電影 ID 抓取票房統計資料"""
    try:
        res = requests.get(DETAIL_URL + film_id, headers=HEADERS, timeout=TIMEOUT)
        res.encoding = "utf-8"
        data = res.json()
        return data
    except Exception as e:
        print(f"❌ 票房資料抓取失敗：ID={film_id} ({e})")
        return None


# 儲存 CSV
def sanitize_filename(name: str) -> str:
    """移除檔名中不合法的字元"""
    return re.sub(r'[\\/*?:"<>|]', "_", name)


# 將未找到 ID 的電影資料儲存為 error_{week_label}.json
def save_missing_rows(missing_rows: list[dict], output_dir: str, week_label: str) -> None:
    """將未找到電影 ID 的資料儲存為 error_{week_label}.json"""
    if missing_rows:
        fileName = f"error_{week_label}.json"
        save_json(missing_rows, output_dir, fileName)
        filePath = os.path.join(output_dir, fileName)
        print(f"⚠️ 已儲存 {len(missing_rows)} 筆未找到電影 ID/票房資料：{filePath}")


# 記錄錯誤類別
def mark_errorType(row: pd.Series, errorType: str) -> dict:
    row_dict = row.to_dict()
    row_dict["errorType"] = errorType
    print(f"⚠️ 未找到電影 ID：{row['title_zh']}")
    return row_dict


# ========= 主爬蟲邏輯 =========
### 取得政府公開的票房資料
def fetch_boxoffice_permovie() -> None:
    week_label = get_current_week_label()
    firstRunList_filePath = f"{FIRSTRUN_PROCESSED}\\{week_label}\\firstRun_{week_label}.csv"
    output_dir = os.path.join(BOXOFFICE_PERMOVIE_RAW, week_label)
    missing_rows: list[dict] = []  # 用來收集未找到電影 ID 的整列資料
    ensure_dir(output_dir)

    # 讀取首輪電影名單
    if not os.path.exists(firstRunList_filePath):
        print(f"⚠️ 找不到本週首輪電影清單：{firstRunList_filePath}")
        return

    df_movies = pd.read_csv(firstRunList_filePath)
    print(f"📋 共 {len(df_movies)} 部電影待處理\n")

    # 逐部整理電影資料
    for _, row in df_movies.iterrows():
        title = row["title_zh"]
        safe_title = sanitize_filename(title)
        print(f"🎬 處理中：{title}")

        # Step 1: 查電影 ID
        film_id = search_film_id(title)
        # 將未找到ID的資料加入 missing_rows
        if not film_id:
            missing_rows.append(mark_errorType(row, "notFoundID"))
            continue

        # Step 2: 抓票房資料
        data = fetch_boxoffice_data(film_id)
        # 將未找到ID的資料加入 missing_rows
        if not data:
            missing_rows.append(mark_errorType(row, "notFoundData"))
            continue

        # Step 3: 儲存 JSON（每部電影一檔）
        file_name = f"{film_id}_{safe_title}_{week_label}.json"
        save_json(data, output_dir, file_name)

        print(f"✅ 已儲存：{file_name}")
        time.sleep(SLEEP_INTERVAL)

    # 將未找到 ID 的電影資料儲存為 error_{week_label}.json
    save_missing_rows(missing_rows, output_dir, week_label)

    print("\n🎉 政府票房資料爬取完成！")


# ========= 主程式執行區 =========
if __name__ == "__main__":
    fetch_boxoffice_permovie()
