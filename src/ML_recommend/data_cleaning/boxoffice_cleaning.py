"""
票房資料清理模組
功能：
1️⃣ 比對 raw/processed 資料夾，只轉換新的 JSON 檔
2️⃣ 清理欄位，統一成結構化 CSV
3️⃣ 儲存至 data/processed/boxoffice_weekly/
"""

from pathlib import Path
import pandas as pd
import json
import os


def clean_new_boxoffice_json():
    # === 資料夾設定 ===
    RAW_DIR = Path("data/raw/boxoffice_weekly")
    PROCESSED_DIR = Path("data/processed/boxoffice_weekly")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # === 取得現有檔案清單 ===
    raw_files = {f.stem for f in RAW_DIR.glob("*.json")}
    processed_files = {f.stem for f in PROCESSED_DIR.glob("*.csv")}

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
    '''NOTE:目前預設全數保留
    '''

    # === 開始處理 ===
    for stem in new_files:
        json_path = RAW_DIR / f"{stem}.json"
        csv_path = PROCESSED_DIR / f"{stem}.csv"

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                # ✅ 正確的路徑：data → dataItems
                records = data.get("data", {}).get("dataItems", [])

                if not records:
                    print(f"⚠️ 找不到 dataItems，請確認 JSON 結構：{json_path.name}")
                    continue

                df = pd.DataFrame(records)

                # 保留需要的欄位
                existing_cols = [c for c in keep_cols if c in df.columns]
                df = df[existing_cols]

                # 儲存 CSV
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                print(f"✅ 已轉換：{csv_path.name}")

        except Exception as e:
            print(f"❌ 轉換失敗 {json_path.name}：{e}")

    print("🎉 全部新檔案轉換完成！")


if __name__ == "__main__":
    clean_new_boxoffice_json()
