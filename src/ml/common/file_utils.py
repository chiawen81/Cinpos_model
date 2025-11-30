"""
負責專案中的檔案存取與基本資料處理動作。
----------------------------------
✅ 設計原則：
1. 統一所有「存檔／讀檔」行為（JSON、CSV）。
2. 自動建立不存在的資料夾。
3. 可方便擴充未來雲端儲存或版本控制機制。
"""

import os
import json
import pandas as pd
from datetime import datetime
import re


# --------------------------------------------------------
# 檔案、資料夾相關
# --------------------------------------------------------
# 檢查資料夾是否存在
def ensure_dir(path: str) -> None:
    """確保資料夾存在，若不存在則自動建立。"""
    os.makedirs(path, exist_ok=True)


# 移除檔名中不合法字元
def clean_filename(name: str) -> str:
    """移除檔名中不合法字元"""
    return re.sub(r'[\\/*?:"<>|]', "_", name)


# --------------------------------------------------------
# 儲存與讀取 JSON
# --------------------------------------------------------
# 儲存 JSON 檔
def save_json(data: dict, dir_path: str, filename: str, topic: str = "") -> str:
    """儲存 JSON 檔，回傳實際儲存路徑。"""
    ensure_dir(dir_path)
    file_path = os.path.join(dir_path, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已儲存 JSON{topic}：{file_path}")
    except Exception as e:
        print(f"❌ 儲存 JSON 失敗：{file_path}\n{e}")
    return file_path


# 讀取 JSON 檔
def load_json(file_path: str) -> dict:
    """讀取 JSON 檔，若檔案不存在則回傳空字典。"""
    if not os.path.exists(file_path):
        print(f"⚠️ 找不到檔案：{file_path}")
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------
# 儲存與列出 CSV
# --------------------------------------------------------
def save_csv(df: pd.DataFrame, dir_path: str, filename: str) -> str:
    """儲存 DataFrame 成 CSV，回傳實際儲存路徑。"""
    ensure_dir(dir_path)
    file_path = os.path.join(dir_path, filename)
    try:
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        print(f"✅ 已儲存 CSV：{file_path}")
    except Exception as e:
        print(f"❌ 儲存 CSV 失敗：{file_path}\n{e}")
    return file_path


def list_files(dir_path: str, ext: str = "json") -> list:
    """列出指定資料夾內的特定副檔名檔案（預設 json）。"""
    if not os.path.exists(dir_path):
        return []
    return [f for f in os.listdir(dir_path) if f.endswith(f".{ext}")]


def get_latest_file(dir_path: str, ext: str = "json") -> str | None:
    """取得資料夾內最新的檔案（依修改時間排序）。"""
    if not os.path.exists(dir_path):
        return None
    files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith(f".{ext}")]
    return max(files, key=os.path.getmtime) if files else None


# --------------------------------------------------------
# 其他
# --------------------------------------------------------
