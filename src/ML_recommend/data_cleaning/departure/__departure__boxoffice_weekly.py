"""
票房資料清理模組
功能：
1️⃣ 比對 raw/processed 資料夾，只轉換新的 JSON 檔
2️⃣ 清理欄位，統一成結構化 CSV
3️⃣ 儲存至 data/processed/boxoffice_weekly/
"""

from pathlib import Path
import pandas
import os
from common.file_utils import load_json, save_csv, ensure_dir
from common.path_utils import BOXOFFICE_RAW, BOXOFFICE_PROCESSED


def clean_new_boxoffice_json():
    """比對新檔案並將原始 JSON 轉為結構化 CSV"""

    # === 檢查/建立資料夾 ===
    ensure_dir(BOXOFFICE_RAW)
    ensure_dir(BOXOFFICE_PROCESSED)

    # === 取得現有檔案清單 ===
    raw_files = {f.stem for f in Path(BOXOFFICE_RAW).glob("*.json")}
    processed_files = {f.stem for f in Path(BOXOFFICE_PROCESSED).glob("*.csv")}

    # 找出「還沒轉換」的 JSON 檔
    new_files = sorted(list(raw_files - processed_files))

    if not new_files:
        print("✅ 沒有新檔案需要轉換。")
        return

    print(f"📦 發現 {len(new_files)} 個新檔案需要轉換：")
    for f in new_files:
        print(f" - {f}.json")

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

    # === 4️⃣ 開始轉換 ===
    for stem in new_files:
        json_path = os.path.join(BOXOFFICE_RAW, f"{stem}.json")
        csv_filename = f"{stem}.csv"

        try:
            data = load_json(json_path)
            records = data.get("data", {}).get("dataItems", [])

            if not records:
                print(f"⚠️ 找不到 dataItems，請確認 JSON 結構：{os.path.basename(json_path)}")
                continue

            df = pandas.DataFrame(records)

            # 保留需要的欄位（若有遺漏則自動略過）
            existing_cols = [c for c in keep_cols if c in df.columns]
            df = df[existing_cols]

            # 儲存 CSV
            save_csv(df, BOXOFFICE_PROCESSED, csv_filename)

        except Exception as e:
            print(f"❌ 轉換失敗 {os.path.basename(json_path)}：{e}")


if __name__ == "__main__":
    clean_new_boxoffice_json()
