"""
mapping_utils.py
----------------------------------
人工修正對照表工具
----------------------------------
用途：
    統一管理跨資料來源的電影名稱與 ID 對照關係
    (政府票房資料 / 開眼電影網 / IMDb / OMDb)
檔案位置：
    data/MANUAL_FIX_DIR/fix_gov_mapping.json
"""

import os
import json
from typing import Optional
from common.path_utils import MANUAL_FIX_DIR


# ==============================
# 基本設定
# ==============================
FIX_MAPPING_FILE = os.path.join(MANUAL_FIX_DIR, "fix_gov_mapping.json")


# ==============================
# 基本操作函式
# ==============================
def ensure_mapping_dir():
    os.makedirs(MANUAL_FIX_DIR, exist_ok=True)


def load_manual_mapping() -> list[dict]:
    """讀取人工修正對照表（回傳陣列形式）"""
    ensure_mapping_dir()
    if not os.path.exists(FIX_MAPPING_FILE):
        return {}
    with open(FIX_MAPPING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_manual_mapping_as_dict() -> dict:
    """載入後轉成以 gov_id 為 key 的 dict 結構，方便查找"""
    data = load_manual_mapping()
    return {item.get("gov_id"): item for item in data if item.get("gov_id")}


def save_manual_mapping(data: list[dict]):
    """儲存人工修正對照表（陣列形式）"""
    ensure_mapping_dir()
    with open(FIX_MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 已更新人工修正對照表：{FIX_MAPPING_FILE}")


def find_manual_mapping(title_zh: str, mappings: list[dict]) -> dict | None:
    """
    根據開眼中文片名查找人工對照資料。
    精確比對 atmovies_title_zh。
    """
    for item in mappings:
        if item.get("atmovies_title_zh") == title_zh:
            return item
    return None


# ==============================
# 查找函式
# ==============================
def find_by_atmovies_title(title_zh: str) -> Optional[dict]:
    """以開眼電影中文名稱查找對應紀錄"""
    data = load_manual_mapping()
    for item in data:
        if item.get("atmovies_title_zh") == title_zh:
            return item
    return None


def find_by_gov_id(gov_id: str) -> Optional[dict]:
    """以政府電影 ID 查找紀錄"""
    mapping_dict = load_manual_mapping_as_dict()
    return mapping_dict.get(gov_id)


# ==============================
# 新增 / 更新資料
# ==============================
def upsert_mapping(record: dict):
    """
    新增或更新一筆電影對照資料。
    record 應包含：
        gov_id, gov_title_zh, atmovies_id, atmovies_title_zh,
        imdb_id, imdb_en, omdb_id, omdb_en, match_level, note
    """
    data = load_manual_mapping()
    existing = next((item for item in data if item.get("gov_id") == record.get("gov_id")), None)

    if existing:
        existing.update(record)
        print(f"🔁 更新對照資料：{record.get('gov_title_zh')}")
    else:
        data.append(record)
        print(f"➕ 新增對照資料：{record.get('gov_title_zh')}")

    save_manual_mapping(data)
