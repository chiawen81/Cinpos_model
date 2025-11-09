# uv run data\ML_rating\train_Model_Rating\crawler_gov_to_imdb_merge_final.py
# ==========================================================
import pandas as pd
import requests
import time
from pathlib import Path

# ==========================================================
# 🔧 基本設定
# ==========================================================
OMDB_API_KEY = "749f9108"   # ← 這裡放你在 https://www.omdbapi.com/apikey.aspx 的金鑰
OMDB_URL = "https://www.omdbapi.com/"
INPUT_FILE = r"data\ML_rating\movieInfo_gov_full_2025-11-06.csv"
OUTPUT_FILE = r"data\ML_rating\gov_imdb_full_merge.csv"
CACHE_FILE = r"data\ML_rating\gov_imdb_cache.csv"

# ==========================================================
# 🧠 輔助函數
# ==========================================================
def fetch_imdb_info(title, year=None):
    """透過 OMDb 取得 imdb_id 與 imdb_rating"""
    if not title or pd.isna(title):
        return None, None

    params = {
        "apikey": OMDB_API_KEY,
        "t": title.strip(),
        "type": "movie"
    }
    if year:
        params["y"] = str(year)

    try:
        r = requests.get(OMDB_URL, params=params, timeout=10)
        data = r.json()
        if data.get("Response") == "True":
            return data.get("imdbID"), data.get("imdbRating")
    except Exception as e:
        print(f"⚠️  查詢失敗: {title} ({year}) → {e}")

    return None, None


# ==========================================================
# 📥 Step 1. 載入電影清單
# ==========================================================
df = pd.read_csv(INPUT_FILE, dtype=str)
print(f"📄 已載入 {len(df)} 筆電影資料")

# ==========================================================
# 💾 Step 2. 載入快取（避免重查）
# ==========================================================
cache = {}
if Path(CACHE_FILE).exists():
    df_cache = pd.read_csv(CACHE_FILE, dtype=str)
    cache = {str(r["gov_id"]): (r["imdb_id"], r["imdb_rating"]) for _, r in df_cache.iterrows()}
    print(f"💾 已載入快取 {len(cache)} 筆 IMDb 對應資料")

# ==========================================================
# 🔄 Step 3. 逐筆查詢 IMDb
# ==========================================================
records = []
for i, row in df.iterrows():
    gov_id = str(row["gov_id"]).strip()
    zh = row.get("gov_title_zh")
    en = row.get("gov_title_en")
    year = None

    imdb_id, imdb_rating = cache.get(gov_id, (None, None))

    if not imdb_id:
        # 優先以英文片名查詢
        if en:
            imdb_id, imdb_rating = fetch_imdb_info(en, year)
        # 若英文查不到，則用中文查詢
        if not imdb_id and zh:
            imdb_id, imdb_rating = fetch_imdb_info(zh, year)

        cache[gov_id] = (imdb_id, imdb_rating)
        print(f"{i+1}/{len(df)} ✅ {gov_id} | {zh or en} → {imdb_id} ({imdb_rating})")
        time.sleep(0.6)  # 延遲避免被封鎖
    else:
        print(f"{i+1}/{len(df)} ⚡ 快取命中: {gov_id} → {imdb_id} ({imdb_rating})")

    # 建立合併紀錄
    record = row.to_dict()
    record["imdb_id"] = imdb_id
    record["imdb_rating"] = imdb_rating
    records.append(record)

    # 每 20 筆暫存一次
    if (i + 1) % 20 == 0:
        pd.DataFrame(records).to_csv(CACHE_FILE, index=False, encoding="utf-8-sig")
        print(f"💾 暫存快取中... ({i+1} 筆)")

# ==========================================================
# 📊 Step 4. 匯出最終合併檔
# ==========================================================
df_result = pd.DataFrame(records)
df_result.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print("\n✅ 完成整合！已輸出檔案：", OUTPUT_FILE)
print("📁 欄位包含：gov_id, gov_title_zh, gov_title_en, imdb_id, imdb_rating")
