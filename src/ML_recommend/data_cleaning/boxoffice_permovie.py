"""
政府電影票房資料清洗
----------------------------------
目標：
    讀取每週爬下來的《全國電影票房統計資訊》原始 JSON
    清洗成：
        1. 電影基本資訊 → 存在 data/processed/movieInfo_gov
        2. 每部電影的週票房資料 → 存在 data/processed/boxoffice_permovie/<年份>/<週次>
"""

import os
import json
import pandas as pd
from datetime import datetime

# 共用模組
from common.path_utils import (
    BOXOFFICE_PERMOVIE_RAW,
    BOXOFFICE_PERMOVIE_PROCESSED,
    MOVIEINFO_GOV_PROCESSED,
)
from common.file_utils import ensure_dir, save_csv, clean_filename
from common.date_utils import get_current_week_label, get_current_year_label

# ========= 全域設定 =========
WEEK_LABEL = get_current_week_label()
YEAR_LABEL = get_current_year_label()


# ========= 輔助工具 =========
# 整理電影基本資訊
def parse_movie_info(movie_data: dict) -> dict:
    """整理電影基本資訊"""
    film_members = movie_data.get("filmMembers", [])
    directors = [m["name"] for m in film_members if m["typeName"] == "導演"]
    actors = [m["name"] for m in film_members if m["typeName"] == "演員"]

    # 轉換片長：秒 → 分鐘（整數）
    film_length = movie_data.get("filmLength", "")
    try:
        # 若為有效數值，四捨五入取整數分鐘
        film_length_min = round(float(film_length) / 60)
    except (ValueError, TypeError):
        film_length_min = ""

    return {
        "gov_id": movie_data.get("movieId", ""),
        "gov_title_zh": movie_data.get("name", ""),
        "gov_title_en": movie_data.get("originalName", ""),
        "region": movie_data.get("region", ""),
        "rating": movie_data.get("rating", ""),
        "release_date": movie_data.get("releaseDate", ""),
        "publisher": movie_data.get("publisher", ""),
        "film_length_min": film_length_min,  # 原資料單位為「秒」，現改為「分鐘」
        "director": "; ".join(directors),
        "actor_list": "; ".join(actors),
    }


# 將 weeks 區塊轉成 DataFrame
def flatten_weekly_boxoffice(movie_data: dict, gov_id: str) -> pd.DataFrame:
    """將 weeks 區塊轉成 DataFrame"""
    weeks = movie_data.get("weeks", [])
    if not weeks:
        return pd.DataFrame()

    df = pd.DataFrame(weeks)
    df.rename(
        columns={
            "date": "week_range",
            "amount": "amount",
            "tickets": "tickets",
            "totalAmount": "total_amount",
            "totalTickets": "total_tickets",
            "rate": "rate",
            "theaterCount": "theater_count",
        },
        inplace=True,
    )

    df["gov_id"] = gov_id
    df["fetch_date"] = datetime.now().strftime("%Y-%m-%d")

    return df[
        [
            "gov_id",
            "week_range",
            "amount",
            "tickets",
            "total_amount",
            "total_tickets",
            "rate",
            "theater_count",
            "fetch_date",
        ]
    ]


# ========= 主程式 =========
def clean_boxoffice_permovie():
    # --- 設定路徑 ---
    input_dir = os.path.join(BOXOFFICE_PERMOVIE_RAW, YEAR_LABEL, WEEK_LABEL)
    output_dir = os.path.join(BOXOFFICE_PERMOVIE_PROCESSED)
    ensure_dir(output_dir)
    ensure_dir(MOVIEINFO_GOV_PROCESSED)

    # --- 尋找當周資料夾 ---
    if not os.path.exists(input_dir):
        print(f"⚠️ 找不到資料夾：{input_dir}")
        return

    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    print(f"📂 準備清洗 {len(files)} 部電影資料\n")

    success_count = 0
    invalid_data_count = 0

    # 逐步清洗單一電影
    for file in files:
        file_path = os.path.join(input_dir, file)

        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        crawler_data = raw_data.get("data", {})
        if not crawler_data:
            print(f"⚠️ {file} 無有效內容")
            invalid_data_count += 1
            continue

        # Step 1️⃣：電影資訊
        processed_data_info = parse_movie_info(crawler_data)
        safe_title = clean_filename(processed_data_info["gov_title_zh"] or "unknown")

        df_info = pd.DataFrame([processed_data_info])
        info_filename = f"{processed_data_info['gov_id']}_{safe_title}.csv"
        save_csv(df_info, MOVIEINFO_GOV_PROCESSED, info_filename)

        # Step 2️⃣：整理週票房資料
        df_weeks = flatten_weekly_boxoffice(crawler_data, processed_data_info["gov_id"])
        if not df_weeks.empty:
            csv_filename = f"{processed_data_info['gov_id']}_{safe_title}.csv"
            save_csv(df_weeks, output_dir, csv_filename)
            print(f"✅ 已清洗：{csv_filename}")
            success_count += 1
        else:
            print(f"⚠️ 無週次資料：{file}")

    # ------------------------------------------------
    # 統計輸出
    # ------------------------------------------------
    print("\n==============================")
    print("🎉 《全國電影票房統計資訊》單一電影票房統計 已清洗完成")
    print(f"　週期：{WEEK_LABEL}")
    print(f"　年份：{YEAR_LABEL}")
    print(f"　總檔案數：{len(files)}")
    print(f"　成功清洗筆數：{success_count}")
    print(f"　異常筆數：{invalid_data_count}")
    print(f"📁 票房輸出資料夾：{output_dir}")
    print(f"📁 電影資訊輸出資料夾：{MOVIEINFO_GOV_PROCESSED}")
    print("==============================\n")


if __name__ == "__main__":
    clean_boxoffice_permovie()
