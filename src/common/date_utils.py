"""
日期處理
----------------------------------
"""

from datetime import datetime, timedelta, date
import re

# ========= 全域設定 =========
TODAY_DATETIME = datetime.today()


# -------------------------------
# 取得上週起訖日期
# -------------------------------
def get_last_week_range(reference_date: date | None = None):
    """
    目標：取得上週一到日的起訖日期
    參數：
        reference_date (date | None):
            - 可選，用來指定「參考日期」
            - 若未提供，預設使用今日日期
    回傳：
        dict: {
            "startDate": "YYYY-MM-DD",
            "endDate": "YYYY-MM-DD"
        }
    """
    today = reference_date or date.today()
    this_monday = today - timedelta(days=today.weekday())
    last_monday = this_monday - timedelta(weeks=1)
    last_sunday = last_monday + timedelta(days=6)

    week_range={
        "startDate": last_monday.strftime("%Y-%m-%d"),
        "endDate": last_sunday.strftime("%Y-%m-%d"),
    }

    print(f'''<查上週起訖>
          輸入的日期為: {reference_date} 
          該日期的上週起訖為：{week_range}''')
    return week_range



# -------------------------------
# 取得年份周次
# -------------------------------
from datetime import date

def get_year_label(input_date: date | None = None) -> str:
    """
    回傳像 2025 這樣的年標籤

    參數：
        input_date (date | None): 
            - 可選，用來指定要取得年份標籤的日期。
            - 若未傳入，預設使用今日日期。
            - 傳入格式範例：date(2025, 9, 30)

    回傳：
        str: 例如 "2025"
    """
    # 若未提供日期，使用今日
    target_date = input_date or date.today()

    # 取得 ISO 年份（注意：有些跨年週會屬於隔年的 ISO 年份）
    year, _, _ = target_date.isocalendar()

    label = f"{year}"
    print(f"傳入日期：{target_date} 所屬年份為：{label}")
    return label
"""測試範例
    get_current_year_label()
    # → 傳入日期：2025-10-29 所屬年份為：2025

    get_current_year_label(date(2025, 1, 1))
    # → 傳入日期：2025-01-01 所屬年份為：2025

    get_current_year_label(date(2024, 12, 30))
    # → 傳入日期：2024-12-30 所屬年份為：2025（因為 ISO 週制算進 2025 年）
"""


def get_week_label(input_date: date | None = None) -> str:
    """
    回傳像 2025W41 這樣的週次標籤
    
    參數：
        input_date (date | None): 
            - 可選，用來指定要取得週次標籤的日期。
            - 若未傳入，預設使用今日日期。
            - 傳入格式範例：date(2025, 9, 30)
    回傳：
        str: 例如 "2025W41"
    """
    # 若未提供日期，預設使用今日
    target_date = input_date or date.today()

    # 取得 ISO 週次
    year, week_num, _ = target_date.isocalendar()
    
    label = f"{year}W{week_num:02d}"
    print(f'''<周次標籤>
          輸入的日期為: {target_date} 
          該日期的所屬週次為：{label}''')
    
    return label
"""測試範例
    get_current_week_label()
    # → 傳入日期：2025-10-29 所屬週次為：2025W44

    get_current_week_label(date(2025, 9, 30))
    # → 傳入日期：2025-09-30 所屬週次為：2025W40
"""

# -------------------------------
# 取得一周的起訖日期
# -------------------------------
def format_week_date_range(date_range):
    """回傳像 "1008-1014" 這樣的日期"""
    date = f"{date_range['startDate'][-5:-3]}{date_range['startDate'][-2:]}-{date_range['endDate'][-5:-3]}{date_range['endDate'][-2:]}"
    print("date", date)
    return date


# -------------------------------
# 統一日期格式
# -------------------------------
def normalize_date(date_str: str) -> str | None:
    """
    將日期統一轉為 ISO 8601 格式（YYYY-MM-DD）。
    支援來源格式：
        - 2025/10/23
        - 2025-10-23
        - 2025/6/5 或 2025-6-5（自動補零）
    """
    if not date_str or not isinstance(date_str, str):
        return None

    # 移除多餘空白
    date_str = date_str.strip()

    # 將 / 轉為 -，確保一致
    date_str = date_str.replace("/", "-")

    # 若是簡短格式（例如 2025-6-5），自動補零
    parts = re.split(r"[-]", date_str)
    if len(parts) == 3:
        y, m, d = parts
        if len(m) == 1:
            m = f"0{m}"
        if len(d) == 1:
            d = f"0{d}"
        date_str = f"{y}-{m}-{d}"

    # 驗證格式正確性
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


# --------------------------------------------------------
# 時間相關
# --------------------------------------------------------
def create_timestamped() -> str:
    """建立自動時間戳，
    可用於檔案命名，例如：boxoffice_20251010.json"""
    now = datetime.now()
    return f"{now.strftime('%Y%m%d')}"
