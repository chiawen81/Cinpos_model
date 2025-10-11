"""
開眼電影網：首輪上映電影清單爬蟲
----------------------------------
目標：取得開眼電影網的「首輪上映中」電影清單
更新頻率：每周一次
資料來源：https://www.atmovies.com.tw/movie/now
"""

# ========= 套件匯入 =========
import re
import requests
from bs4 import BeautifulSoup

# 共用模組
from common.date_utils import get_current_week_label
from common.network_utils import get_default_headers
from common.file_utils import save_json
from common.path_utils import FIRSTRUN_RAW

# ========= 全域設定 =========
BASE_URL = "https://www.atmovies.com.tw"  # 開眼電影網網址
TARGET_URL = f"{BASE_URL}/movie/now/"  # 開眼電影網的首輪電影頁面路徑
HEADERS = get_default_headers()


# ========= 輔助函式 =========
# 整理單筆電影資料
def format_crawler_data(li):
    # 取得中文片名
    title_tag = li.find("a")
    title = title_tag.text.strip() if title_tag else None

    # 取得開眼電影編號
    href = title_tag["href"] if title_tag else ""
    movie_id_match = re.search(r"/movie/([a-z0-9]+)/", href)
    movie_id = movie_id_match.group(1) if movie_id_match else None

    # 取得上映日期 & 片長 & 廳數
    runtime_span = li.find("span", class_="runtime")
    date_match = re.search(r"(\d{4}/\d{1,2}/\d{1,2})", runtime_span.text)
    theater_match = re.search(r"\((\d+)廳\)", runtime_span.text)

    release_date = date_match.group(1) if date_match else None
    theater_count = int(theater_match.group(1)) if theater_match else None

    return {
        "atmovies_id": movie_id,
        "title_zh": title,
        "release_date": release_date,
        "screen_count": theater_count,
        "source_url": f"{BASE_URL}/movie/{movie_id}/",
    }


# ========= 主爬蟲邏輯 =========
### 抓取開眼電影網「首輪上映中」清單
def fetch_first_run_movies():
    print("📡 正在抓取開眼電影網首輪電影清單...")
    res = requests.get(TARGET_URL, headers=HEADERS, timeout=10)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")
    film_list = soup.find(attrs={"class": "filmListPA"})
    movies = []

    # 檢查有找到資料
    if not film_list:
        print("❌ 找不到電影清單區塊 (filmListPA)")
        return []

    # 整理爬蟲資料
    for li in film_list.find_all("li", recursive=False):
        managed_data = format_crawler_data(li)
        movies.append(managed_data)

    print(f"✅ 共抓取到 {len(movies)} 部電影")
    return movies


# ========= 儲存邏輯 =========
# 儲存原始 JSON 檔
def save_raw_json(movies):
    week_label = get_current_week_label()
    json_filename = f"firstRun_{week_label}.json"
    save_json(movies, FIRSTRUN_RAW, json_filename)
    print(f"💾 已儲存 JSON：data/raw/firstRunFilm_list/{json_filename}")


# ========= 主程式執行區 =========
if __name__ == "__main__":
    # 取得電影資料
    movies = fetch_first_run_movies()

    # 儲存資料
    if movies:
        save_raw_json(movies)
        print("🎉 開眼電影網首輪清單爬取完成！")
