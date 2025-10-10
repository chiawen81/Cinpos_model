"""
目標：取得當周電影院的票房資料，每周爬一次
資料來源：《全國電影票房統計資訊》https://boxofficetw.tfai.org.tw/
"""

import os
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from common.date_utils import get_last_week_range, get_current_week_label, format_week_date_range
from common.path_utils import BOXOFFICE_RAW
from common.file_utils import save_json


# 全國電影票房統計API- 每周電影票房
BASE_URL = "https://boxofficetw.tfai.org.tw/stat/qsl"


##### 取得<每周電影票房>票房 #####
def fetch_boxoffice_json(date_str: str = None):
    """
    從官方 API 下載指定週的票房資料(JSON) 並存檔
    """

    # 設定查詢日期
    date_range = get_last_week_range(date_str)

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
    fileName_week = get_current_week_label()
    fileName_date = format_week_date_range(date_range)
    filename = f"boxoffice_{fileName_week}_{fileName_date}.json"

    # 儲存成原始 JSON
    save_json(data, BOXOFFICE_RAW, filename)

    print(f"已儲存原始資料：{BOXOFFICE_RAW}")


# 主程式
if __name__ == "__main__":
    fetch_boxoffice_json()
"""NOTE:
     Python 會在執行檔案時自動設定內建變數 __name__。
     若此檔案是被「直接執行」，__name__ 會等於 "__main__"；
     若此檔案是被「其他檔案 import」，__name__ 會等於模組名稱。
     因此這段判斷可避免：當此檔案被匯入時就自動執行主程式(fetch_boxoffice_json())
"""
