"""
合併政府電影資訊資料
----------------------------------
目標：
    合併 data/processed/movieInfo_gov/ 資料夾下所有電影 CSV 檔。
    統一輸出一份彙整檔 movieInfo_gov_combined_<日期>.csv

輸入：
    data/processed/movieInfo_gov/*.csv

輸出：
    data/processed/movieInfo_gov_combined/movieInfo_gov_combined_<日期>.csv
"""

import os
import pandas as pd
from datetime import datetime
from common.file_utils import save_csv  # 若你的 save_csv 能接受資料夾 + 檔名

# -------------------------------------------------------
# 主程式
# -------------------------------------------------------
def merge_movieInfo_gov(input_folder: str, output_folder: str):
    all_data = []
    files = [f for f in os.listdir(input_folder) if f.endswith(".csv")]

    if not files:
        print("⚠️ 找不到任何 CSV 檔案，請確認資料夾路徑是否正確。")
        return

    print(f"📦 準備合併 {len(files)} 支電影資料...")

    for file in files:
        file_path = os.path.join(input_folder, file)
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
            df["source_file"] = file  # 保留原始檔名供追蹤
            all_data.append(df)
        except Exception as e:
            print(f"⚠️ 無法讀取檔案：{file}，原因：{e}")

    if not all_data:
        print("⚠️ 無資料可合併。")
        return

    merged_df = pd.concat(all_data, ignore_index=True)

    # 統一欄位順序
    col_order = [
        "gov_id",
        "atmovies_id",
        "gov_title_zh",
        "gov_title_en",
        "region",
        "rating",
        "release_date",
        "publisher",
        "film_length",
        "director",
        "actor_list",
        "source_file",
    ]

    for col in col_order:
        if col not in merged_df.columns:
            merged_df[col] = None

    merged_df = merged_df[col_order]

    # 建立輸出資料夾（若不存在）
    os.makedirs(output_folder, exist_ok=True)

    # 輸出檔案
    today = datetime.now().strftime("%Y-%m-%d")
    output_name = f"movieInfo_gov_combined_{today}.csv"
    save_csv(merged_df, output_folder, output_name)

    print(f"✅ 合併完成，共 {len(merged_df)} 筆資料。")
    print(f"📁 輸出檔案：{os.path.join(output_folder, output_name)}")


# -------------------------------------------------------
# 主程式執行入口
# -------------------------------------------------------
if __name__ == "__main__":
    input_folder = "data/processed/movieInfo_gov"
    output_folder = "data/processed/movieInfo_gov_combined"
    merge_movieInfo_gov(input_folder, output_folder)
