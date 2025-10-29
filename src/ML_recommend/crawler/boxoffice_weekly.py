"""
目標：取得當周電影院的票房資料，每周爬一次
資料來源：《全國電影票房統計資訊》https://boxofficetw.tfai.org.tw/
"""

import os
import requests
from common.date_utils import (
    get_last_week_range,
    get_current_week_label,
    format_week_date_range,
    get_current_year_label,
)
from common.path_utils import BOXOFFICE_RAW
from common.file_utils import save_json
from datetime import datetime,date


# 全國電影票房統計API- 每周電影票房
BASE_URL = "https://boxofficetw.tfai.org.tw/stat/qsl"


##### 取得<每周電影票房>票房 #####
def fetch_boxoffice_json(reference_date: date | datetime | None = None):
    """
    從官方 API 下載指定週的票房資料(JSON) 並存檔
    """

    # 設定查詢日期
    date_range = get_last_week_range(reference_date)

    # 整理API參數
    params = {
        "mode": "Week",
        "start": date_range["startDate"],
        "ascending": "false",
        "orderedColumn": "ReleaseDate",
        "page": 0,
        "size": "",  # 留空以抓全部
        "region": "all",
    }

    # 取得每周資料
    response = requests.get(BASE_URL, params=params)
    response.encoding = "utf-8"
    data = response.json()
    # print("data",data)

    # 設定儲存的檔名
    year_label = get_current_year_label()
    week_label = get_current_week_label(datetime.strptime(date_range["startDate"], "%Y-%m-%d").date())
    file_folder = os.path.join(BOXOFFICE_RAW, year_label)
    fileName_date = format_week_date_range(date_range)
    filename = f"boxoffice_{week_label}_{fileName_date}.json"

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
    fetch_boxoffice_json(date(2025, 10, 9))
"""NOTE:
     Python 會在執行檔案時自動設定內建變數 __name__。
     若此檔案是被「直接執行」，__name__ 會等於 "__main__"；
     若此檔案是被「其他檔案 import」，__name__ 會等於模組名稱。
     因此這段判斷可避免：當此檔案被匯入時就自動執行主程式(fetch_boxoffice_json())
"""
