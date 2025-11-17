"""
政府公開資料：《全國電影票房統計資訊》爬蟲
------------------------------------------------
目標：
    以《全國電影票房統計資訊》每周電影票房的名單為基準
    （存在 data/processed/boxoffice_weekly/boxoffice_<週期>_<日期範圍>.csv），
    逐一查詢該電影的「累計票房統計資料」。

資料來源：
    1. 每周電影票房（已清理完的CSV）
       data/processed/boxoffice_weekly/boxoffice_<週期>_<日期範圍>.csv
       欄位重點：movieId, name

    2. 政府電影票房統計詳細頁
       https://boxofficetw.tfai.org.tw/film/gfd/<電影id>
"""

# ========= 套件匯入 =========
import os
import argparse
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import date, datetime

# 共用模組
from common.path_utils import (
    BOXOFFICE_PERMOVIE_RAW,
    BOXOFFICE_PERMOVIE_FULL,
    BOXOFFICE_PROCESSED,
)
from common.network_utils import get_default_headers
from common.file_utils import ensure_dir, save_json, clean_filename
from common.date_utils import get_week_label, get_year_label, get_last_week_range


# ========= 全域設定 =========
SEARCH_URL = "https://boxofficetw.tfai.org.tw/film/sf?keyword="
DETAIL_URL = "https://boxofficetw.tfai.org.tw/film/gfd/"
HEADERS = get_default_headers()
TIMEOUT = 10
SLEEP_INTERVAL = 1.2  # 避免連續請求過快被限制


# ========= 輔助函式 =========
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


# ========= 主爬蟲邏輯 =========
def fetch_boxoffice_permovie_from_weekly(reference_date: date | None = None) -> None:
    """
    以每週票房名單為基準，逐一抓取單部電影的票房統計資料。
    """

    # 設定查詢日期
    last_week_date_range = get_last_week_range(reference_date)
    target_date=datetime.strptime(last_week_date_range["startDate"], "%Y-%m-%d").date()
    WEEK_LABEL = get_week_label(target_date)
    YEAR_LABEL = get_year_label(target_date)

    print(f"📅 本次執行週期(最近一周)：{WEEK_LABEL}")

    # --- 前置 ---
    ready_crawler_num = 0  # 預計要撈取的電影數
    success_crawler_num = 0  # 成功撈取的電影數

    # ------------------------------------------------
    # 取得電影名單與id
    # ------------------------------------------------
    boxoffice_weekly_dir = os.path.join(BOXOFFICE_PROCESSED, YEAR_LABEL)

    # 🔍 遞迴搜尋該年份底下符合週期名稱的 CSV 檔案
    matches = list(Path(boxoffice_weekly_dir).rglob(f"boxoffice_{WEEK_LABEL}_*.csv"))

    if not matches:
        print(f"⚠️ 找不到最近一週的週票房資料：{boxoffice_weekly_dir}")
        return

    boxoffice_this_week_filePath = str(matches[0])

    print("-------------------------------")
    print(f"本周票房檔案：{boxoffice_this_week_filePath}")

    # 讀取檔案
    df_weekly = pd.read_csv(boxoffice_this_week_filePath)

    if "movieId" not in df_weekly.columns:
        print("❌ 檔案缺少必要欄位 'movieId'")
        return

    ready_crawler_num = len(df_weekly)
    print(f"📊 共 {ready_crawler_num} 部電影待查詢票房詳細資料\n")

    # ------------------------------------------------
    # 取得輸出資料夾路徑
    # ------------------------------------------------
    output_dir = os.path.join(BOXOFFICE_PERMOVIE_RAW, YEAR_LABEL, WEEK_LABEL)
    ensure_dir(output_dir)

    # 建立 full 資料夾（用於存放最新的完整資料，不含週次標籤）
    ensure_dir(BOXOFFICE_PERMOVIE_FULL)

    # ------------------------------------------------
    # 開始逐部電影抓取
    # ------------------------------------------------
    for _, row in df_weekly.iterrows():
        movie_id = str(row["movieId"]).strip()
        movie_name = row.get("name", "")
        clean_movie_name = clean_filename(movie_name)

        if not movie_id or movie_id == "nan":
            print(f"⚠️ 無有效 movieId，略過：{movie_name}")
            continue

        # 抓取單部電影資料
        crawler_data = fetch_boxoffice_data(movie_id)

        # 加入最新爬取日期
        if crawler_data:
            crawler_data["last_crawled_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. 儲存到週次資料夾（含週次標籤）
        file_name_with_week = f"{movie_id}_{clean_movie_name}_{WEEK_LABEL}.json"
        save_json(crawler_data, output_dir, file_name_with_week)

        # 2. 額外儲存到 full 資料夾（不含週次標籤，會自動覆蓋舊資料）
        file_name_full = f"{movie_id}_{clean_movie_name}.json"
        save_json(crawler_data, BOXOFFICE_PERMOVIE_FULL, file_name_full)

        print(f"✅ 已儲存：{file_name_with_week} (週次) & {file_name_full} (full)")
        success_crawler_num += 1

        time.sleep(SLEEP_INTERVAL)

    # ------------------------------------------------
    # 統計輸出
    # ------------------------------------------------
    print("\n==============================")
    print("🎉 單一電影票房累計資料 已抓取完成")
    print(f"　週期：{WEEK_LABEL}")
    print(f"　預計撈取電影數量：{ready_crawler_num}")
    print(f"　成功撈取電影數量：{success_crawler_num}")
    print(f"　未成功撈取：{ready_crawler_num - success_crawler_num}")
    print(f"📁 輸出資料夾：{output_dir}")
    print("==============================\n")


# ========= 主程式執行區 =========
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抓取單部電影的累計票房資料")
    parser.add_argument(
        "--date",
        type=str,
        help="指定參考日期（格式：YYYY-MM-DD），預設為當天",
    )

    args = parser.parse_args()

    # 解析日期參數
    reference_date = None
    if args.date:
        try:
            reference_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("❌ 日期格式錯誤，請使用 YYYY-MM-DD 格式")
            exit(1)

    fetch_boxoffice_permovie_from_weekly(reference_date)
