'''
目標：一次性取得半年的電影票房資料
資料來源：《全國電影票房統計資訊》https://boxofficetw.tfai.org.tw/
'''

# src/movie_recommendation/crawler/boxoffice_init.py

import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# === 參數設定 ===
RAW_PATH = "data/raw/boxoffice/"
BASE_URL = "https://boxoffice.tfi.org.tw/api/export"  # 政府票房統計API（影視局）
# ↑ 若之後網站不同，可改成實際提供下載的 CSV URL

# 建立資料夾
os.makedirs(RAW_PATH, exist_ok=True)

def fetch_boxoffice_by_week(start_date: str, end_date: str) -> pd.DataFrame:
    """
    從 API 抓取指定週期的票房資料，並轉成 DataFrame。
    """
    payload = {
        "start": start_date,
        "end": end_date,
        "mode": "week",
    }
    try:
        response = requests.get(BASE_URL, params=payload)
        response.raise_for_status()
        df = pd.read_csv(pd.compat.StringIO(response.text))
        return df
    except Exception as e:
        print(f"⚠️ 無法取得 {start_date} ~ {end_date} 的票房資料: {e}")
        return pd.DataFrame()

def fetch_past_half_year():
    today = datetime.today()
    for i in range(26, -1, -1):  # 往前 26 週（半年）
        end_date = today - timedelta(weeks=i*1)
        start_date = end_date - timedelta(days=6)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        print(f"📦 下載週期: {start_str} ~ {end_str}")

        df = fetch_boxoffice_by_week(start_str, end_str)
        if not df.empty:
            week_label = f"{end_date.strftime('%Y')}W{end_date.strftime('%U')}"
            df.to_csv(f"{RAW_PATH}/boxoffice_{week_label}.csv", index=False)

if __name__ == "__main__":
    fetch_past_half_year()
    print("✅ 半年票房資料下載完成！")
