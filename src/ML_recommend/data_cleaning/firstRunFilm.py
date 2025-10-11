"""
開眼電影網：首輪上映電影資料清洗
----------------------------------
任務：整理已爬取的 JSON 檔，轉換為結構化 CSV。
來源：data/raw/firstRunFilm_list/<週次>/firstRun_<週次>.json
輸出：data/processed/firstRunFilm_list/<週次>/firstRun_<週次>.csv
"""

# ========= 套件匯入 =========
import pandas as pd
import os

# 共用模組
from common.date_utils import get_current_week_label
from common.file_utils import load_json, save_csv
from common.path_utils import FIRSTRUN_RAW, FIRSTRUN_PROCESSED
from common.mapping_utils import find_by_atmovies_title  # ✅ 新增引用人工對照表函式
from common.date_utils import normalize_date


# ========= 清洗邏輯 =========
def clean_first_run_data():
    week_label = get_current_week_label()
    json_filename = f"firstRun_{week_label}.json"
    json_path = os.path.join(FIRSTRUN_RAW, json_filename)

    print(f"📂 載入原始資料：{json_path}")
    data = load_json(json_path)

    if not data:
        print("⚠️ 沒有讀到任何資料，請確認 JSON 是否存在或內容是否正確。")
        return

    # 建立 DataFrame
    df = pd.DataFrame(
        data, columns=["title_zh", "atmovies_id", "release_date", "screen_count", "source_url"]
    )

    # 清理欄位
    df = df.dropna(subset=["title_zh"])  # 移除沒有標題的列
    df["release_date"] = df["release_date"].apply(normalize_date)  # 格式日期統一
    df = df.sort_values(by="release_date", ascending=True)

    # ========= 關鍵部分：比對人工對照表 =========
    corrected_titles = []
    for idx, row in df.iterrows():
        title = row["title_zh"]
        mapped = find_by_atmovies_title(title)

        if mapped:
            gov_title = mapped.get("gov_title_zh")
            print(f"🧩 對照表命中：{title} → {gov_title}")
            df.at[idx, "title_zh"] = gov_title
            corrected_titles.append(title)
        else:
            corrected_titles.append(None)

    # 新增一欄紀錄是否來自人工修正（方便後續分析）
    df["mapping_type"] = ["fixed" if t else "auto" for t in corrected_titles]

    # 儲存結果
    csv_filename = f"firstRun_{week_label}.csv"
    output_dir = os.path.join(FIRSTRUN_PROCESSED, week_label)
    save_csv(df, output_dir, csv_filename)

    print(f"✅ 清洗完成並輸出：{output_dir}/{csv_filename}")
    print(f"📊 本次共修正 {df['mapping_type'].eq('fixed').sum()} 筆電影名稱。")


# ========= 主程式執行區 =========
if __name__ == "__main__":
    clean_first_run_data()
