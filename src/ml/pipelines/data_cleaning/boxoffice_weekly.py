"""
票房資料清理模組（支援年度子資料夾）
------------------------------------------------
功能：
1️⃣ 比對 raw 和 processed 資料夾，只轉換新的 JSON 檔
2️⃣ 清理欄位，統一成結構化 CSV
3️⃣ 儲存至 data/processed/boxoffice_weekly/<年份>/
"""

from pathlib import Path
import pandas
import os
from ml.common.file_utils import load_json, save_csv, ensure_dir
from ml.common.path_utils import BOXOFFICE_RAW, BOXOFFICE_PROCESSED


def clean_new_boxoffice_json():
    """比對新檔案並將原始 JSON 轉為結構化 CSV（依年份輸出）"""

    # === 檢查/建立資料夾 ===
    ensure_dir(BOXOFFICE_RAW)
    ensure_dir(BOXOFFICE_PROCESSED)

    # === 取得現有檔案清單 ===
    # 遞迴尋找所有年份資料夾底下的 JSON
    raw_files = list(Path(BOXOFFICE_RAW).rglob("*.json"))

    if not raw_files:
        print("⚠️ 找不到任何原始 JSON 檔案。")
        return

    total_files = len(raw_files)
    success_count = 0
    skip_count = 0
    fail_count = 0

    print(f"📦 發現 {total_files} 個待檢查 JSON 檔案。\n")

    # === 保留的欄位 ===
    keep_cols = [
        "movieId",
        "rank",
        "name",
        "releaseDate",
        "publisher",
        "dayCount",
        "theaterCount",
        "amount",
        "tickets",
        "marketShare",
        "totalDayCount",
        "totalAmount",
        "totalTickets",
    ]
    """NOTE:目前預設全數保留
    """

    # === 開始逐一轉換 ===
    for json_path in raw_files:
        try:
            year_folder = json_path.parent.name  # 例如 "2025"
            stem = json_path.stem  # 例如 "boxoffice_2025W43_1013-1019"

            # === 設定輸出資料夾與檔案路徑 ===
            output_year_dir = os.path.join(BOXOFFICE_PROCESSED, year_folder)
            ensure_dir(output_year_dir)

            csv_path = os.path.join(output_year_dir, f"{stem}.csv")

            # 若 processed 已存在同名 CSV → 略過
            if os.path.exists(csv_path):
                skip_count += 1
                continue

            data = load_json(str(json_path))
            records = data.get("data", {}).get("dataItems", [])

            if not records:
                print(f"⚠️ 找不到 dataItems：{os.path.basename(json_path)}")
                fail_count += 1
                continue

            df = pandas.DataFrame(records)

            # 保留需要的欄位（若有遺漏則自動略過）
            existing_cols = [c for c in keep_cols if c in df.columns]
            df = df[existing_cols]

            # === 儲存 CSV ===
            save_csv(df, output_year_dir, f"{stem}.csv")
            success_count += 1

        except Exception as e:
            print(f"❌ 轉換失敗 {os.path.basename(json_path)}：{e}")
            fail_count += 1

    # ------------------------------------------------
    # 統計輸出
    # ------------------------------------------------
    print("\n==============================")
    print("🎉 《全國電影票房統計資訊》周票房資料 已清理完成")
    print(f"　raw總檔案數：{total_files}")
    print(f"　本次成功轉換：{success_count}")
    print(f"　本次轉換失敗：{fail_count}")
    print(f"　略過（已存在）：{skip_count}")
    print(f"📁 輸出資料夾：{BOXOFFICE_PROCESSED}")
    print("==============================\n")


if __name__ == "__main__":
    clean_new_boxoffice_json()
