'''
目標：取得當周電影院的票房資料，每周爬一次
資料來源：《全國電影票房統計資訊》https://boxofficetw.tfai.org.tw/
'''

# src/movie_recommendation/crawler/boxoffice_weekly.py

import os
import requests
import pandas as pd
from datetime import datetime, timedelta

RAW_PATH = "data/raw/boxoffice/"
BASE_URL = "https://boxoffice.tfi.org.tw/api/export"

os.makedirs(RAW_PATH, exist_ok=True)

def fetch_current_week_boxoffice():
    today = datetime.today()
    start_date = (today - timedelta(days=today.weekday()))  # 本週一
    end_date = start_date + timedelta(days=6)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"📦 正在下載: {start_str} ~ {end_str}")

    try:
        response = requests.get(BASE_URL, params={"start": start_str, "end": end_str, "mode": "week"})
        response.raise_for_status()
        df = pd.read_csv(pd.compat.StringIO(response.text))
        week_label = f"{end_date.strftime('%Y')}W{end_date.strftime('%U')}"
        df.to_csv(f"{RAW_PATH}/boxoffice_{week_label}.csv", index=False)
        print(f"✅ 已儲存至 boxoffice_{week_label}.csv")
    except Exception as e:
        print(f"⚠️ 本週票房資料下載失敗: {e}")

if __name__ == "__main__":
    fetch_current_week_boxoffice()

