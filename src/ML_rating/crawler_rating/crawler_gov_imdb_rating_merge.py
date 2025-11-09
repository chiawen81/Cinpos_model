# uv run data\ML_rating\train_Model_Rating\crawler_gov_imdb_rating_merge.py
# ==========================================================
import pandas as pd
import requests
import time
import re
from pathlib import Path

# ============================================================
# 🔧 設定區
# ============================================================
OMDB_API_KEY = "你的API_KEY"   # ← 改成你在 https://www.omdbapi.com/apikey.aspx 申請的金鑰
OMDB_URL = "https://www.omdbapi.com/"

INPUT_FILE = "data\ML_rating\movieInfo_gov_full_2025-11-06.csv"
OUTPUT_FILE = "gov_imdb_full_merge.csv"
CACHE_FILE = "gov_imdb_cache.csv"  # 防止重複查詢，可重啟續跑

# ============================================================
# 🧩 輔助函式：搜尋 IMDb 資料
# ============================================================
def fetch_imdb_info(title, year=None):
    """根據電影標題查詢 IMDb ID + 評分"""
    if not title or pd.isna(title):
        return None, None
    params = {"apikey": OMDB_API_KEY, "t": title.strip(), "type": "movie"}
    if year:
        params["y"] = str(year)
    try:
        resp = requests.get(OMDB_URL, params=params, timeout=10)
        data = resp.json()
        if data.get("Response") == "True":
            return data.get("imdbID"), data.get("imdbRating")
    except Exception as e:
        print(f"⚠️ 查詢失敗：{title} ({year}) → {e}")
    return None, None

# ============================================================
# 📥 Step 1. 讀取政府電影資料
# ============================================================
df = pd.read_csv(INPUT_FILE, dtype=str)
print(f"📄 載入 {len(df)} 筆電影資料")

# 自動偵測中文/英文片名欄位
title_cols = [c for c in df.columns if re.search("片名|title", c, re.IGNORECASE)]
title_zh_col = title_cols[0] if len(title_cols) > 0 else None
title_en_col = title_cols[1] if len(title_cols) > 1 else None
year_col = next((c for c in df.columns if re.search("年份|year", c, re.IGNORECASE)), None)

print("🎬 偵測片名欄位：", title_cols)
print("📅 偵測年份欄位：", year_col)

# ============================================================
# 💾 Step 2. 若有快取檔，先載入避免重查
# ============================================================
cache = {}
if Path(CACHE_FILE).exists():
    df_cache = pd.read_csv(CACHE_FILE, dtype=str)
    cache = {str(r["gov_id"]): (r["imdb_id"], r["imdb_rating"]) for _, r in df_cache.iterrows()}
    print(f"💾 載入快取 {len(cache)} 筆")

# ============================================================
# 🔄 Step 3. 逐筆查詢 IMDb
# ============================================================
records = []
for i, row in df.iterrows():
    gov_id = str(row.get("gov_id", "")).strip()
    zh = row.get(title_zh_col)
    en = row.get(title_en_col)
    year = row.get(year_col)

    if gov_id in cache:
        imdb_id, imdb_rating = cache[gov_id]
        print(f"{i+1}/{len(df)} ⚡ 快取命中: {gov_id} → {imdb_id} ({imdb_rating})")
    else:
        imdb_id, imdb_rating = None, None

        # 先用英文片名查詢
        if en:
            imdb_id, imdb_rating = fetch_imdb_info(en, year)
        # 若失敗再用中文片名查詢
        if not imdb_id and zh:
            imdb_id, imdb_rating = fetch_imdb_info(zh, year)

        cache[gov_id] = (imdb_id, imdb_rating)
        print(f"{i+1}/{len(df)} ✅ {gov_id} | {zh or en} → {imdb_id} ({imdb_rating})")
        time.sleep(0.6)

    records.append({
        "gov_id": gov_id,
        "title_zh": zh,
        "title_en": en,
        "imdb_id": imdb_id,
        "imdb_rating": imdb_rating
    })

    # 每 20 筆暫存快取
    if (i+1) % 20 == 0:
        pd.DataFrame(records).to_csv(CACHE_FILE, index=False, encoding="utf-8-sig")
        print(f"💾 暫存至 {CACHE_FILE}")

# ============================================================
# 📊 Step 4. 匯出最終整合結果
# ============================================================
df_result = pd.DataFrame(records)
df_result.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print("\n✅ 全部完成！已匯出：", OUTPUT_FILE)
print("📁 含欄位：gov_id, title_zh, title_en, imdb_id, imdb_rating")
