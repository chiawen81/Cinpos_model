"""
批次修復Python檔案中的emoji編碼問題
將所有emoji替換為ASCII標籤
"""
import os
import re
from pathlib import Path

# emoji 對應表
EMOJI_REPLACEMENTS = {
    '\u2705': '[OK]',
    '\u274c': '[ERROR]',
    '\u26a0\ufe0f': '[WARNING]',
    '\u26a0': '[WARNING]',
    '\U0001f389': '[SUCCESS]',
    '\U0001f4e6': '[INFO]',
    '\U0001f4c1': '[INFO]',
    '\U0001f4c5': '[INFO]',  # 日曆
    '\u2728': '[INFO]',
    '\U0001f680': '[INFO]',
    '\U0001f3c6': '[SUCCESS]',  # 獎杯
    '\U0001f4ca': '[INFO]',  # 圖表
    '\U0001f4dd': '[INFO]',  # 備忘錄
    '\U0001f50d': '[INFO]',  # 放大鏡
    # 添加數字emoji (1️⃣ 等)
    '1\ufe0f\u20e3': '1.',
    '2\ufe0f\u20e3': '2.',
    '3\ufe0f\u20e3': '3.',
    '4\ufe0f\u20e3': '4.',
    '5\ufe0f\u20e3': '5.',
}

def fix_emoji_in_file(file_path):
    """修復單一檔案中的emoji"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 替換所有已知的emoji
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            content = content.replace(emoji, replacement)

        # 如果內容有變更，則寫回檔案
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] 修復: {file_path}")
            return True
        else:
            return False

    except Exception as e:
        print(f"[ERROR] 處理 {file_path} 時發生錯誤: {e}")
        return False

def main():
    """主程式"""
    # 要處理的目錄
    directories = [
        'src/fetch_common_data/crawler',
        'src/fetch_common_data/data_cleaning',
    ]

    fixed_count = 0

    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"[WARNING] 目錄不存在: {directory}")
            continue

        # 尋找所有Python檔案
        for py_file in dir_path.rglob('*.py'):
            # 跳過 __departure__ 資料夾
            if '__departure__' in str(py_file):
                continue

            if fix_emoji_in_file(py_file):
                fixed_count += 1

    print(f"\n[SUCCESS] 共修復 {fixed_count} 個檔案")

if __name__ == '__main__':
    main()
