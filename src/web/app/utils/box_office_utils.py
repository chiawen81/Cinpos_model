"""
票房計算相關的共用工具函數
提供衰退率、開片實力、日期計算等核心邏輯
"""

from datetime import datetime
from typing import Optional, Tuple


def calculate_decline_rate(
    current_value: float,
    previous_value: float
) -> Optional[float]:
    """
    計算衰退率（變化率）

    公式：(本期數值 - 上期數值) / 上期數值

    Args:
        current_value: 本期數值（例如：本週票房）
        previous_value: 上期數值（例如：上週票房）

    Returns:
        衰退率（小數形式，例如：-0.3 表示衰退 30%）
        如果上期數值為 0 或無效，返回 None

    Examples:
        >>> calculate_decline_rate(7000000, 10000000)
        -0.3  # 衰退 30%

        >>> calculate_decline_rate(12000000, 10000000)
        0.2  # 成長 20%
    """
    if previous_value is None or previous_value <= 0:
        return None

    return (current_value - previous_value) / previous_value


def calculate_opening_strength(
    week_1_boxoffice: float,
    week_2_boxoffice: float,
    week_1_days: int = 7
) -> float:
    """
    計算開片實力（前兩週日均票房的平均值）

    公式：(第一週日均票房 + 第二週日均票房) / 2
         = (第一週票房 / 第一週天數 + 第二週票房 / 7) / 2

    Args:
        week_1_boxoffice: 第一週票房
        week_2_boxoffice: 第二週票房
        week_1_days: 第一週放映天數（預設 7 天）

    Returns:
        開片實力數值（日均票房）

    Examples:
        >>> calculate_opening_strength(14000000, 10000000, 7)
        1714285.71  # (14000000/7 + 10000000/7) / 2
    """
    week_1_daily_avg = week_1_boxoffice / week_1_days
    week_2_daily_avg = week_2_boxoffice / 7  # 第二週固定 7 天

    return (week_1_daily_avg + week_2_daily_avg) / 2


def parse_date_range(date_range: Optional[str]) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    解析日期範圍字串

    Args:
        date_range: 日期範圍字串（格式："2025-01-01~2025-01-07"）

    Returns:
        (起始日期, 結束日期) 的元組
        如果解析失敗，返回 (None, None)

    Examples:
        >>> parse_date_range("2025-01-01~2025-01-07")
        (datetime(2025, 1, 1), datetime(2025, 1, 7))
    """
    if not date_range:
        return None, None

    try:
        parts = str(date_range).split("~")
        if len(parts) != 2:
            return None, None

        start_date = datetime.strptime(parts[0].strip(), "%Y-%m-%d")
        end_date = datetime.strptime(parts[1].strip(), "%Y-%m-%d")

        return start_date, end_date
    except (ValueError, AttributeError):
        return None, None


def parse_release_date(release_date: Optional[str]) -> Optional[datetime]:
    """
    解析上映日期字串

    Args:
        release_date: 上映日期字串（格式："2025-01-01"）

    Returns:
        上映日期的 datetime 物件
        如果解析失敗，返回 None

    Examples:
        >>> parse_release_date("2025-01-01")
        datetime(2025, 1, 1)
    """
    if not release_date:
        return None

    try:
        return datetime.strptime(release_date, "%Y-%m-%d")
    except ValueError:
        return None


def calculate_first_week_days(
    first_week_date_range: Optional[str],
    release_date: Optional[str]
) -> int:
    """
    計算第一週的實際放映天數

    計算邏輯：
    1. 解析第一週的日期範圍（例如："2025-01-01~2025-01-07"）
    2. 解析上映日期（例如："2025-01-03"）
    3. 計算天數：(第一週結束日 - 上映日) + 1

    Args:
        first_week_date_range: 第一週日期範圍（格式："2025-01-01~2025-01-07"）
        release_date: 上映日期（格式："2025-01-03"）

    Returns:
        第一週放映天數（最少 1 天，最多 7 天）
        如果計算失敗，返回預設值 7 天

    Examples:
        >>> calculate_first_week_days("2025-01-01~2025-01-07", "2025-01-03")
        5  # 1/3, 1/4, 1/5, 1/6, 1/7 共 5 天

        >>> calculate_first_week_days("2025-01-01~2025-01-07", "2025-01-01")
        7  # 整週 7 天
    """
    # 解析日期
    start_date, end_date = parse_date_range(first_week_date_range)
    release_dt = parse_release_date(release_date)

    # 如果解析失敗，返回預設值 7 天
    if not end_date or not release_dt:
        return 7

    # 計算天數：(結束日 - 上映日) + 1
    days = (end_date - release_dt).days + 1

    # 確保天數在合理範圍內（1-7 天）
    if days < 1:
        return 1
    elif days > 7:
        return 7

    return days


def calculate_first_week_daily_avg(
    first_week_boxoffice: float,
    first_week_date_range: Optional[str],
    release_date: Optional[str]
) -> float:
    """
    計算第一週日均票房

    公式：第一週票房 / 第一週實際放映天數

    Args:
        first_week_boxoffice: 第一週票房
        first_week_date_range: 第一週日期範圍（格式："2025-01-01~2025-01-07"）
        release_date: 上映日期（格式："2025-01-03"）

    Returns:
        第一週日均票房
        如果票房為 0，返回 0

    Examples:
        >>> calculate_first_week_daily_avg(14000000, "2025-01-01~2025-01-07", "2025-01-03")
        2800000.0  # 14000000 / 5
    """
    if first_week_boxoffice <= 0:
        return 0

    days = calculate_first_week_days(first_week_date_range, release_date)
    return first_week_boxoffice / days
