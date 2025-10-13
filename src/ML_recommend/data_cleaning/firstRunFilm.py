"""
開眼電影網：首輪上映電影資料清洗
----------------------------------
任務：
    整理已爬取的 JSON 檔，轉換為結構化 CSV。
來源：
    data/raw/firstRunFilm_list/<週次>/firstRun_<週次>.json
輸出：
    data/processed/firstRunFilm_list/<週次>/firstRun_<週次>.csv
清洗任務：
    - 統一日期格式
"""

# ========= 套件匯入 =========
import pandas as pd
import os

# 共用模組
from common.date_utils import get_current_week_label, normalize_date
from common.file_utils import load_json, save_csv
from common.path_utils import FIRSTRUN_RAW, FIRSTRUN_PROCESSED


# ========= 清洗邏輯 =========
def clean_first_run_data():
    # 取得當前週次標籤與路徑
    week_label = get_current_week_label()
    json_filename = f"firstRun_{week_label}.json"
    json_path = os.path.join(FIRSTRUN_RAW, json_filename)

    print(f"📂 載入原始資料：{json_path}")
    data = load_json(json_path)

    if not data:
        print("⚠️ 沒有讀到任何資料，請確認 JSON 是否存在或內容是否正確。")
        return

    # === 建立 DataFrame ===
    df = pd.DataFrame(
        data, columns=["title_zh", "atmovies_id", "release_date", "screen_count", "source_url"]
    )

    # === 清理資料 ===
    df = df.dropna(subset=["title_zh"])  # 移除無片名資料列，確保欄位完整性
    df["release_date"] = df["release_date"].apply(normalize_date)  # 統一日期格式（YYYY-MM-DD）
    df = df.drop_duplicates(subset=["title_zh", "release_date"], keep="first")  # 去除重複電影資料
    df = df.sort_values(by="release_date", ascending=True)  # 按上映日期排序
    df = df[["title_zh", "atmovies_id", "release_date", "screen_count", "source_url"]]  # 欄位排序統一

    # === 輸出結果 ===
    csv_filename = f"firstRun_{week_label}.csv"
    output_dir = os.path.join(FIRSTRUN_PROCESSED, week_label)
    save_csv(df, output_dir, csv_filename)

    print(f"✅ 清洗完成並輸出：{output_dir}/{csv_filename}")


# ========= 主程式執行區 =========
if __name__ == "__main__":
    clean_first_run_data()
