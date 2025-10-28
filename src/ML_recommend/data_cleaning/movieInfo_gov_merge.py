"""
合併政府電影資訊資料
----------------------------------
目標：
    合併 data/processed/movieInfo_gov/ 資料夾下所有電影 CSV 檔。
    統一輸出一份彙整檔 movieInfo_gov_combined_<日期>.csv

輸入：
    data/processed/movieInfo_gov/*.csv

輸出：
    data/processed/movieInfo_gov/combined/movieInfo_gov_combined_<日期>.csv
"""

import os
import pandas as pd
from datetime import datetime
from common.file_utils import save_csv  # 若你的 save_csv 能接受資料夾 + 檔名
from common.path_utils import MOVIEINFO_GOV_PROCESSED, MOVIEINFO_GOV_COMBINED_PROCESSED


# -------------------------------------------------------
# 主程式
# -------------------------------------------------------
def merge_movieInfo_gov():
    all_data = []
    gov_processed_files = [f for f in os.listdir(MOVIEINFO_GOV_PROCESSED) if f.endswith(".csv")]

    if not gov_processed_files:
        print("⚠️ 找不到任何 CSV 檔案，請確認資料夾路徑是否正確。")
        return

    print(f"📦 準備合併 {len(gov_processed_files)} 支電影資料...")

    success_count = 0
    fail_files = []

    for file in gov_processed_files:
        file_path = os.path.join(MOVIEINFO_GOV_PROCESSED, file)
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
            df["source_file"] = file  # 保留原始檔名供追蹤
            all_data.append(df)
            success_count += len(df)
        except Exception as e:
            fail_files.append(file)
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

    # 建立輸出資料夾
    os.makedirs(MOVIEINFO_GOV_COMBINED_PROCESSED, exist_ok=True)

    # 輸出檔案
    today = datetime.now().strftime("%Y-%m-%d")
    output_name = f"movieInfo_gov_full_{today}.csv"
    save_csv(merged_df, MOVIEINFO_GOV_COMBINED_PROCESSED, output_name)

    # 統計輸出
    print("\n✅ 合併完成")
    print(f"　├─ processed/movieInfo_gov 檔案總數：{len(gov_processed_files)} 支")
    print(f"　├─ 合併成功筆數：{success_count} 筆")
    print(f"　└─ 讀取失敗檔案：{len(fail_files)} 支")

    if fail_files:
        print("　⚠️ 以下檔案未成功讀取：")
        for f in fail_files:
            print(f"　　- {f}")

    print(f"\n📁 已輸出檔案：{os.path.join(MOVIEINFO_GOV_COMBINED_PROCESSED, output_name)}")


# -------------------------------------------------------
# 主程式執行入口
# -------------------------------------------------------
if __name__ == "__main__":
    merge_movieInfo_gov()
