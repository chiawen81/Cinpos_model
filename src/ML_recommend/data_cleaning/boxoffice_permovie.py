"""
政府電影票房資料清洗
----------------------------------
目標：
    讀取每週爬下來的《全國電影票房統計資訊》原始 JSON
    清洗成：
        1. 若僅一週資料 → 存電影資訊到 movieInfo_gov
        2. 每部電影的週票房資料 → 存在 processed/boxoffice_permovie/<週次>
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
from common.date_utils import get_current_week_label

# ========= 全域設定 =========
WEEK_LABEL = get_current_week_label()


# ========= 輔助工具 =========
# 整理電影基本資訊
def parse_movie_info(movie_data: dict, atmovies_id: str) -> dict:
    film_members = movie_data.get("filmMembers", [])
    directors = [m["name"] for m in film_members if m["typeName"] == "導演"]
    actors = [m["name"] for m in film_members if m["typeName"] == "演員"]

    return {
        "atmovies_id": atmovies_id,
        "gov_id": movie_data.get("movieId", ""),
        "gov_title_zh": movie_data.get("name", ""),
        "gov_title_en": movie_data.get("originalName", ""),
        "region": movie_data.get("region", ""),
        "rating": movie_data.get("rating", ""),
        "release_date": movie_data.get("releaseDate", ""),
        "publisher": movie_data.get("publisher", ""),
        "film_length": movie_data.get("filmLength", ""),
        "director": "; ".join(directors),
        "actor_list": "; ".join(actors),
    }


# 將 weeks 區塊轉成 DataFrame
def flatten_weekly_boxoffice(movie_data: dict, gov_id: str, atmovies_id: str) -> pd.DataFrame:
    weeks = movie_data.get("weeks", [])
    df = pd.DataFrame(weeks)
    if df.empty:
        return pd.DataFrame()

    # 統一欄位名稱與排序
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
    df["atmovies_id"] = atmovies_id
    df["week_label"] = get_current_week_label()
    df["fetch_date"] = datetime.now().strftime("%Y-%m-%d")

    return df[
        [
            "gov_id",
            "atmovies_id",
            "week_label",
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


# 抓出清洗後檔名不同的電影
def check_files_diff():
    """找出 raw 與 processed 中 ID 一樣但電影名稱不同的電影"""
    raw_dir = f"data/raw/boxoffice_permovie/{WEEK_LABEL}"
    clean_dir = f"data/processed/boxoffice_permovie/{WEEK_LABEL}"
    diff_count = 0

    # 取得 raw 與 processed 的檔名（不含副檔名）
    raw_files = {os.path.splitext(f)[0] for f in os.listdir(raw_dir) if f.endswith(".json")}
    processed_files = {os.path.splitext(f)[0] for f in os.listdir(clean_dir) if f.endswith(".csv")}

    for raw_file in raw_files:
        raw_id = raw_file.split("_")[0]
        raw_title = "_".join(raw_file.split("_")[1:-1])

        for processed_file in processed_files:
            processed_id = processed_file.split("_")[0]
            processed_title = "_".join(processed_file.split("_")[1:-1])

            if raw_id == processed_id and raw_title != processed_title:
                diff_count += 1
                print(
                    f"""⚠️  第{diff_count}筆：-------------------------------------------------
    原始資料(raw)：        {raw_file} 
    處理後資料(processed)：{processed_file}"""
                )

    print(f"\n 📊 <ID 一樣但電影名稱不同>的數量：{diff_count}")


# ========= 主程式 =========
def clean_boxoffice_permovie():
    input_dir = os.path.join(BOXOFFICE_PERMOVIE_RAW, WEEK_LABEL)
    output_dir = os.path.join(BOXOFFICE_PERMOVIE_PROCESSED, WEEK_LABEL)
    ensure_dir(output_dir)
    ensure_dir(MOVIEINFO_GOV_PROCESSED)

    if not os.path.exists(input_dir):
        print(f"⚠️ 找不到資料夾：{input_dir}")
        return

    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    print(f"📂 準備清洗 {len(files)} 部電影資料\n")

    for file in files:
        file_path = os.path.join(input_dir, file)
        atmovies_id = file_path.split("_")[-1].replace(".json", "")

        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        crawler_data = raw_data.get("data", {})
        if not crawler_data:
            print(f"⚠️ {file} 無有效內容")
            continue

        processed_data_info = parse_movie_info(crawler_data, atmovies_id)
        safe_title = clean_filename(processed_data_info["gov_title_zh"] or "unknown")

        # Step 1️⃣：若僅有一週或尚未有票房紀錄 → 存電影資訊
        weeks = crawler_data.get("weeks", [])
        if len(weeks) <= 1:
            # 此為新電影，需另存電影資訊
            df_info = pd.DataFrame([processed_data_info])
            info_filename = f"{processed_data_info['gov_id']}_{safe_title}_{processed_data_info['atmovies_id']}.csv"
            save_csv(df_info, MOVIEINFO_GOV_PROCESSED, info_filename)
            print(f"🆕 儲存新電影資訊：{info_filename}")

        # Step 2️⃣：整理 weeks 票房資料
        df_weeks = flatten_weekly_boxoffice(
            crawler_data, processed_data_info["gov_id"], atmovies_id
        )
        if not df_weeks.empty:
            csv_filename = f"{processed_data_info['gov_id']}_{safe_title}_{WEEK_LABEL}_{processed_data_info['atmovies_id']}.csv"
            save_csv(df_weeks, output_dir, csv_filename)
            print(f"✅ 已清洗：{csv_filename}")
        else:
            print(f"⚠️ 無週次資料：{file}")

    print("\n🎉 本週政府票房資料清洗完成！")


if __name__ == "__main__":
    # 清洗本週政府票房資料
    clean_boxoffice_permovie()

    # 抓出清洗後檔名不同的電影
    check_files_diff()
