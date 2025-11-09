"""
格式化工具
說明: 提供數字、日期等格式化功能
"""

from typing import Union, Optional
from datetime import datetime

def format_currency(amount: Union[int, float], currency: str = 'NT$') -> str:
    """
    格式化貨幣金額
    
    Args:
        amount: 金額
        currency: 貨幣符號
        
    Returns:
        格式化的貨幣字串
    """
    if amount >= 100000000:  # 億
        return f"{currency}{amount/100000000:.1f}億"
    elif amount >= 10000:  # 萬
        return f"{currency}{amount/10000:.1f}萬"
    else:
        return f"{currency}{amount:,.0f}"

def format_number(num: Union[int, float]) -> str:
    """
    格式化數字（加千分位）
    
    Args:
        num: 數字
        
    Returns:
        格式化的數字字串
    """
    if isinstance(num, float):
        return f"{num:,.2f}"
    return f"{num:,}"

def format_percentage(value: float, decimal_places: int = 1) -> str:
    """
    格式化百分比
    
    Args:
        value: 數值（小數形式）
        decimal_places: 小數位數
        
    Returns:
        格式化的百分比字串
    """
    return f"{value * 100:.{decimal_places}f}%"

def format_date(date: datetime, format: str = '%Y/%m/%d') -> str:
    """
    格式化日期
    
    Args:
        date: 日期時間物件
        format: 格式字串
        
    Returns:
        格式化的日期字串
    """
    if not date:
        return ''
    return date.strftime(format)

def format_week_label(week: int) -> str:
    """
    格式化週次標籤
    
    Args:
        week: 週次編號
        
    Returns:
        週次標籤字串
    """
    return f"第{week}週"

def get_decline_color(decline_rate: float) -> str:
    """
    根據衰退率返回對應的顏色
    
    Args:
        decline_rate: 衰退率
        
    Returns:
        CSS 顏色值
    """
    if decline_rate < -0.5:  # 衰退超過50%
        return '#FF4444'  # 紅色
    elif decline_rate < -0.3:  # 衰退30-50%
        return '#FFA500'  # 橘色
    elif decline_rate < -0.1:  # 衰退10-30%
        return '#FFDD00'  # 黃色
    else:
        return '#51CF66'  # 綠色

def get_trend_icon(value: float) -> str:
    """
    根據數值返回趨勢圖標
    
    Args:
        value: 變化值
        
    Returns:
        HTML 圖標
    """
    if value > 0:
        return '📈'  # 上升
    elif value < 0:
        return '📉'  # 下降
    else:
        return '➡️'  # 持平
