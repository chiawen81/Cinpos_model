"""
政府公開資料：《全國電影票房統計資訊》爬蟲
------------------------------------------------
目標：
    以開眼電影網的首輪電影名單（存在 Cinpos_model/data）為基準，
    前往《全國電影票房統計資訊》查詢該電影的票房統計資料。

資料來源：
    1. 首輪電影名單：開眼電影網
                    （已存在於 data\processed\firstRunFilm_list）
    2. 政府電影票房統計：
        (1) 搜尋電影 ID：
            https://boxofficetw.tfai.org.tw/film/sf?keyword=<電影名>
        (2) 取得票房資料：
            https://boxofficetw.tfai.org.tw/film/gfd/<電影id>
"""

# ========= 套件匯入 =========
import os
import re
import time
import unicodedata
import requests
import pandas as pd
from urllib.parse import quote
from datetime import datetime
from rapidfuzz import fuzz
import math

# 共用模組
from common.path_utils import FIRSTRUN_PROCESSED, BOXOFFICE_PERMOVIE_RAW
from common.network_utils import get_default_headers
from common.file_utils import ensure_dir, save_json, clean_filename
from common.date_utils import get_current_week_label
from common.mapping_utils import load_manual_mapping, find_manual_mapping

# ========= 全域設定 =========
SEARCH_URL = "https://boxofficetw.tfai.org.tw/film/sf?keyword="
DETAIL_URL = "https://boxofficetw.tfai.org.tw/film/gfd/"
HEADERS = get_default_headers()
TIMEOUT = 10
SLEEP_INTERVAL = 1.2  # 避免連續請求過快被限制
manual_mappings = load_manual_mapping()


# ========= 輔助函式 =========
def normalize_title(title: str) -> str:
    """正規化電影名稱，提升模糊比對準確率"""
    if not title:
        return ""
    title = unicodedata.normalize("NFKC", title)
    title = re.sub(
        r"[：:、，,．。？！!？～～‐－—–‧·•『』「」()（）《》〈〉【】\[\]{}…\s]", "", title
    )
    return title.lower()


def simplify_keyword(keyword: str) -> str:
    """簡化搜尋關鍵詞：移除冒號、破折號後取前半段"""
    keyword = re.split(r"[：:－—–\-]", keyword)[0]
    return keyword.strip()


def compute_similarity(a: str, b: str) -> float:
    """字串相似度"""
    a_n, b_n = normalize_title(a), normalize_title(b)
    # 綜合三種演算法分數
    score_1 = fuzz.ratio(a_n, b_n)
    score_2 = fuzz.partial_ratio(a_n, b_n)
    score_3 = fuzz.token_sort_ratio(a, b)  # 保留原始空白比對
    return max(score_1, score_2, score_3) / 100


def compute_date_similarity(target_date: str, candidate_date: str) -> float:
    """根據上映日期相近程度給分（差距越大分數越低）"""
    try:
        d1 = datetime.strptime(target_date.replace("/", "-"), "%Y-%m-%d")
        d2 = datetime.strptime(candidate_date.replace("/", "-"), "%Y-%m-%d")
        delta_days = abs((d1 - d2).days)
        return max(0, 1 - delta_days / 365)  # 差1年 = 0分
    except Exception:
        return 0.5  # 無法比對時給中間值


def search_film_id(keyword: str, release_date: str = None) -> str | None:
    """根據電影名稱與上映日期，搜尋最相近的電影 ID"""

    def _fetch_results(kw: str):
        """發送搜尋請求並回傳結果列表"""
        try:
            res = requests.get(SEARCH_URL + quote(kw), headers=HEADERS, timeout=TIMEOUT)
            res.encoding = "utf-8"
            return res.json().get("data", {}).get("results", [])
        except Exception as e:
            print(f"❌ 查詢失敗：{kw} ({e})")
            return []

    # ---- 第一輪搜尋（原始標題）----
    results = _fetch_results(keyword)

    # ---- 第二輪搜尋（簡化關鍵字）----
    if not results:
        simple_kw = simplify_keyword(keyword)
        if simple_kw != keyword:
            print(f"⚙️ 降級搜尋：{keyword} → {simple_kw}")
            results = _fetch_results(simple_kw)

    if not results:
        print(f"❌ 查無結果：{keyword}")
        return None

    # ---- 模糊比對挑最像的 ----
    best_match, best_score = None, 0
    scores = []

    for r in results:
        name = r.get("name", "")
        norm_a = normalize_title(keyword)
        norm_b = normalize_title(name)

        # --- 1️⃣ 包含判定（強匹配）---
        if norm_a in norm_b or norm_b in norm_a:
            score = 1.0  # 完全包含視為滿分
        else:
            # --- 2️⃣ 模糊比對 ---
            score = fuzz.token_sort_ratio(keyword, name) / 100.0
            # --- 日期加權 ---
            if release_date and r.get("releaseDate"):
                date_score = compute_date_similarity(release_date, r["releaseDate"])
                score = 0.9 * score + 0.1 * date_score  # 日期佔 10%

        scores.append((r, score))

    # --- 3️⃣ 動態決策 ---
    scores.sort(key=lambda x: x[1], reverse=True)
    if not scores:
        print(f"❌ 無搜尋結果：{keyword}")
        return None

    best_match, best_score = scores[0]
    diff = best_score - scores[1][1] if len(scores) > 1 else best_score

    # 判定條件：高分或明顯領先
    if best_score >= 0.7 or diff >= 0.15:
        print(f"✅ {keyword} → {best_match['name']} (score={best_score:.2f})")
        return best_match["movieId"]
    else:
        print(f"⚠️ 無明確匹配：{keyword}（最高分 {best_score:.2f}）")
        print("候選：", [(r["name"], round(s, 2)) for r, s in scores[:3]])
        return None


# 抓票房資料
def fetch_boxoffice_data(film_id: str) -> dict | None:
    """根據電影 ID 抓取票房統計資料"""
    try:
        res = requests.get(DETAIL_URL + film_id, headers=HEADERS, timeout=TIMEOUT)
        res.encoding = "utf-8"
        data = res.json()
        return data
    except Exception as e:
        print(f"❌ 票房資料抓取失敗：ID={film_id} ({e})")
        return None


# 將未找到 ID 的電影資料儲存為 error_{week_label}.json
def save_missing_rows(missing_rows: list[dict], output_dir: str, week_label: str) -> None:
    """將未找到電影 ID 的資料儲存為 error_{week_label}.json"""
    if missing_rows:
        error_dir = os.path.join(output_dir, "error")
        ensure_dir(error_dir)

        fileName = f"error_{week_label}.json"
        save_json(missing_rows, error_dir, fileName)

        print(
            f"⚠️ 已儲存 {len(missing_rows)} 筆未找到電影 ID/票房資料：{os.path.join(error_dir, fileName)}"
        )


# 記錄錯誤類別
def mark_errorType(row: pd.Series, errorType: str) -> dict:
    row_dict = row.to_dict()
    clean_dict = {
        k: (None if (isinstance(v, float) and math.isnan(v)) else v) for k, v in row_dict.items()
    }
    clean_dict["errorType"] = errorType
    errMsg = "未找到電影 ID" if errorType == "notFoundID" else "未找到票房資料"
    print(f"⚠️ {errMsg}：{row.get('title_zh', '未知標題')}")
    return clean_dict


# ========= 主爬蟲邏輯 =========
### 取得政府公開的票房資料
def fetch_boxoffice_permovie() -> None:
    week_label = get_current_week_label()
    firstRunList_filePath = f"{FIRSTRUN_PROCESSED}\\{week_label}\\firstRun_{week_label}.csv"
    output_dir = os.path.join(BOXOFFICE_PERMOVIE_RAW, week_label)
    missing_rows: list[dict] = []  # 用來收集未找到電影 ID 的整列資料
    ensure_dir(output_dir)

    # 讀取首輪電影名單
    if not os.path.exists(firstRunList_filePath):
        print(f"⚠️ 找不到本週首輪電影清單：{firstRunList_filePath}")
        return

    df_movies = pd.read_csv(firstRunList_filePath)
    print(f"📋 共 {len(df_movies)} 部電影待處理\n")

    # 逐部整理電影資料
    for _, row in df_movies.iterrows():
        title = row["title_zh"]
        id=row["atmovies_id"]
        safe_title = clean_filename(title)
        release_date = row.get("release_date", "")
        print(f"🎬 處理中：{title},{id}")

        # Step 1️⃣：先檢查人工對照表
        mapping = find_manual_mapping(title, manual_mappings)
        if mapping:
            film_id = mapping.get("gov_id")
            print(f"🧭 使用人工對照：{title} → {mapping['gov_title_zh']} (ID={film_id})")
        else:
            # Step 2️⃣：正常搜尋
            film_id = search_film_id(title, release_date)

        # 將未找到ID的資料加入 missing_rows
        if not film_id:
            missing_rows.append(mark_errorType(row, "notFoundID"))
            continue

        # Step 3️⃣：抓票房資料
        data = fetch_boxoffice_data(film_id)
        # 將未找到ID的資料加入 missing_rows
        if not data:
            missing_rows.append(mark_errorType(row, "notFoundData"))
            continue

        # Step 3: 儲存 JSON（每部電影一檔）
        file_name = f"{film_id}_{safe_title}_{week_label}_{row["atmovies_id"]}.json"
        save_json(data, output_dir, file_name)

        print(f"✅ 已儲存：{file_name}")
        time.sleep(SLEEP_INTERVAL)

    # 將未找到 ID 的電影資料儲存為 error_{week_label}.json
    save_missing_rows(missing_rows, output_dir, week_label)

    print("\n🎉 政府票房資料爬取完成！")


# ========= 主程式執行區 =========
if __name__ == "__main__":
    fetch_boxoffice_permovie()
