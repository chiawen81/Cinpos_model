"""
驗證工具
說明: 提供資料驗證功能
"""

import re
from typing import Any, Optional, Tuple

def validate_gov_id(gov_id: str) -> Tuple[bool, Optional[str]]:
    """
    驗證政府代號格式
    
    Args:
        gov_id: 政府代號
        
    Returns:
        (是否有效, 錯誤訊息)
    """
    if not gov_id:
        return False, "政府代號不能為空"
    
    # 假設格式為 MOV 開頭加數字
    pattern = r'^MOV\d{3,}$'
    if not re.match(pattern, gov_id):
        return False, "政府代號格式無效"
    
    return True, None

def validate_week_number(week: Any) -> Tuple[bool, Optional[str]]:
    """
    驗證週次編號
    
    Args:
        week: 週次
        
    Returns:
        (是否有效, 錯誤訊息)
    """
    try:
        week_num = int(week)
        if week_num < 1:
            return False, "週次必須大於0"
        if week_num > 52:
            return False, "週次不能超過52"
        return True, None
    except (TypeError, ValueError):
        return False, "週次必須是數字"

def validate_export_format(format: str) -> Tuple[bool, Optional[str]]:
    """
    驗證匯出格式
    
    Args:
        format: 檔案格式
        
    Returns:
        (是否有效, 錯誤訊息)
    """
    allowed_formats = ['csv', 'excel', 'json', 'pdf']
    if format not in allowed_formats:
        return False, f"不支援的格式: {format}. 允許的格式: {', '.join(allowed_formats)}"
    return True, None

def sanitize_input(text: str) -> str:
    """
    清理使用者輸入
    
    Args:
        text: 輸入文字
        
    Returns:
        清理後的文字
    """
    if not text:
        return ''
    
    # 移除危險字元
    dangerous_chars = ['<', '>', '"', "'", '&', '\0']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    # 移除多餘空白
    text = ' '.join(text.split())
    
    return text.strip()
