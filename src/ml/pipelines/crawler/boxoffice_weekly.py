"""
目標：取得當周電影院的票房資料，每周爬一次
資料來源：《全國電影票房統計資訊》https://boxofficetw.tfai.org.tw/
"""

import os
import argparse
import cloudscraper
import time
from ml.common.date_utils import (
    get_last_week_range,
    get_week_label,
    format_week_date_range,
    get_year_label,
)
from ml.common.path_utils import BOXOFFICE_RAW
from ml.common.file_utils import save_json
from datetime import datetime, date


# 全國電影票房統計API- 每周電影票房
BASE_URL = "https://boxofficetw.tfai.org.tw/stat/qsl"


##### 取得<每周電影票房>票房 #####
def fetch_boxoffice_json(reference_date: date | None = None):
    """
    從官方 API 下載指定週的票房資料(JSON) 並存檔
    """

    # 設定查詢日期
    last_week_date_range = get_last_week_range(reference_date)
    target_date=datetime.strptime(last_week_date_range["startDate"], "%Y-%m-%d").date()
    WEEK_LABEL = get_week_label(target_date)
    YEAR_LABEL = get_year_label(target_date)

    # 整理API參數
    params = {
        "mode": "Week",
        "start": last_week_date_range["startDate"],
        "ascending": "false",
        "orderedColumn": "ReleaseDate",
        "page": 0,
        "size": "",  # 留空以抓全部
        "region": "all",
    }

    # 使用 cloudscraper 來繞過 Cloudflare 保護
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    print("正在取得票房資料...")

    # 取得每周資料
    response = scraper.get(BASE_URL, params=params, timeout=30)
    response.encoding = "utf-8"

    # 檢查回應是否為 JSON
    try:
        data = response.json()
    except Exception as e:
        print(f"\n[ERROR] API 回應不是有效的 JSON")
        print(f"狀態碼: {response.status_code}")
        print(f"回應內容前 500 字元:\n{response.text[:500]}")
        if "cloudflare" in response.text.lower():
            print("\n[WARNING] 請求被 Cloudflare 阻擋，請稍後再試或檢查網路連線")
        raise
    # print("data",data)

    # 設定儲存的檔名
    file_folder = os.path.join(BOXOFFICE_RAW, YEAR_LABEL)
    fileName_date = format_week_date_range(last_week_date_range)
    filename = f"boxoffice_{WEEK_LABEL}_{fileName_date}.json"

    # 儲存成原始 JSON
    save_json(data, file_folder, filename)

    # ------------------------------------------------
    # 統計輸出
    # ------------------------------------------------
    print("\n==============================")
    print("🎉 本週票房資料 已抓取完成")
    print("\n==============================")


# 主程式
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抓取每周電影票房資料")
    parser.add_argument(
        "--date",
        type=str,
        help="指定參考日期（格式：YYYY-MM-DD），預設為當天",
    )

    args = parser.parse_args()

    # 解析日期參數
    reference_date = None
    if args.date:
        try:
            reference_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("❌ 日期格式錯誤，請使用 YYYY-MM-DD 格式")
            exit(1)

    fetch_boxoffice_json(reference_date)

"""NOTE:
     Python 會在執行檔案時自動設定內建變數 __name__。
     若此檔案是被「直接執行」，__name__ 會等於 "__main__"；
     若此檔案是被「其他檔案 import」，__name__ 會等於模組名稱。
     因此這段判斷可避免：當此檔案被匯入時就自動執行主程式(fetch_boxoffice_json())
"""
