"""
日期處理
----------------------------------
"""

from datetime import datetime, timedelta


# -------------------------------
# 取得上週起訖日期
# -------------------------------
def get_last_week_range(reference_date: datetime = None):
    """
    目標：取得上週一到日的起訖日期
    回傳：
        {
            "startDate": "YYYY-MM-DD",
            "endDate":   "YYYY-MM-DD"
        }
    """
    if reference_date is None:
        today = datetime.today()
    else:
        today = reference_date

    # 計算這週的週一
    this_monday = today - timedelta(days=today.weekday())
    # 上週一
    last_monday = this_monday - timedelta(weeks=1)
    # 上週日
    last_sunday = last_monday + timedelta(days=6)

    return {
        "startDate": f"{last_monday.year}-{str(last_monday.month).zfill(2)}-{str(last_monday.day).zfill(2)}",
        "endDate": f"{last_sunday.year}-{str(last_sunday.month).zfill(2)}-{str(last_sunday.day).zfill(2)}",
    }


"""測試範例
    print(get_last_week_range(datetime(2025, 10, 8)))
    結果：{'startDate': '2025-09-29', 'endDate': '2025-10-05'}
"""


# -------------------------------
# 取得年份周次
# -------------------------------
def get_current_week_label():
    """回傳像 2025W41 這樣的週次標籤"""
    today = datetime.today()
    year, week_num, _ = today.isocalendar()
    print(f"{year}W{week_num}")
    return f"{year}W{week_num}"


# -------------------------------
# 取得一周的起訖日期
# -------------------------------
def format_week_date_range(date_range):
    """回傳像 "1008-1014" 這樣的日期"""
    date = f"{date_range['startDate'][-5:-3]}{date_range['startDate'][-2:]}-{date_range['endDate'][-5:-3]}{date_range['endDate'][-2:]}"
    print("date", date)
    return date
