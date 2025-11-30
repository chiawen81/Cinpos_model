"""
統計資料服務
處理首頁統計卡片的資料邏輯
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class StatsService:
    """統計資料服務類別"""

    def __init__(self):
        """初始化服務"""
        # 設定資料目錄路徑
        self.data_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "data" / "raw" / "boxoffice_weekly"

    def get_recent_files(self, count: int = 3) -> List[Path]:
        """
        取得最近的週票房檔案

        Args:
            count: 要取得的檔案數量

        Returns:
            檔案路徑列表，按時間從新到舊排序
        """
        all_files = []

        # 遍歷所有年份目錄
        for year_dir in sorted(self.data_dir.iterdir(), reverse=True):
            if year_dir.is_dir():
                # 取得該年份的所有 JSON 檔案
                json_files = list(year_dir.glob("boxoffice_*.json"))
                all_files.extend(json_files)

        # 按檔案名稱排序（檔案名包含週次，所以可以直接排序）
        all_files.sort(reverse=True)

        return all_files[:count]

    def load_weekly_data(self, file_path: Path) -> Optional[Dict]:
        """
        載入週票房資料

        Args:
            file_path: JSON 檔案路徑

        Returns:
            週票房資料字典，如果讀取失敗則返回 None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"讀取檔案失敗 {file_path}: {e}")
            return None

    def get_recent_movies_stats(self) -> Dict:
        """
        取得近期上映電影統計

        Returns:
            統計資料字典，包含：
            - recent_count: 近期上映電影數量（1-4週內上映）
            - change_from_last_week: 較上週的變化數量
        """
        # 取得最近3個檔案（用於計算本週、上週、上上週）
        recent_files = self.get_recent_files(count=3)

        if len(recent_files) < 2:
            return {
                'recent_count': 0,
                'change_from_last_week': 0,
                'error': '資料檔案不足'
            }

        # 載入資料
        current_week_data = self.load_weekly_data(recent_files[0])  # 本週
        last_week_data = self.load_weekly_data(recent_files[1])     # 上週

        if not current_week_data or not last_week_data:
            return {
                'recent_count': 0,
                'change_from_last_week': 0,
                'error': '資料載入失敗'
            }

        # 計算本週的近期上映電影數量（1-4週內上映，也就是 dayCount <= 28）
        current_recent_count = self._count_recent_movies(
            current_week_data,
            max_days=28  # 4週 = 28天
        )

        # 計算上週的近期上映電影數量
        last_recent_count = self._count_recent_movies(
            last_week_data,
            max_days=28
        )

        # 計算變化
        change = current_recent_count - last_recent_count

        return {
            'recent_count': current_recent_count,
            'change_from_last_week': change,
            'last_week_count': last_recent_count
        }

    def _count_recent_movies(self, weekly_data: Dict, max_days: int = 28) -> int:
        """
        計算近期上映電影數量

        Args:
            weekly_data: 週票房資料
            max_days: 最大上映天數（預設28天=4週）

        Returns:
            符合條件的電影數量
        """
        if not weekly_data or 'data' not in weekly_data:
            return 0

        data_items = weekly_data['data'].get('dataItems', [])

        # 計算上映天數 <= max_days 的電影數量
        recent_movies = [
            movie for movie in data_items
            if movie.get('dayCount', 0) <= max_days
        ]

        return len(recent_movies)

    def get_warning_stats(self, tracked_movie_ids: list = None) -> Dict:
        """
        取得預警電影統計

        Args:
            tracked_movie_ids: 追蹤的電影 ID 列表

        Returns:
            統計資料字典，包含：
            - total_count: 總預警電影數量
            - attention_count: 注意狀態的電影數量
            - critical_count: 嚴重狀態的電影數量
        """
        # ⚠️ 臨時方案：從前端傳入追蹤的電影 ID 列表
        # 🔄 未來改進：從後端資料庫取得使用者的追蹤清單

        if not tracked_movie_ids or len(tracked_movie_ids) == 0:
            return {
                'total_count': 0,
                'attention_count': 0,
                'critical_count': 0
            }

        # 使用 boxoffice_list_service 取得電影資料
        from services.boxoffice_list_service import BoxOfficeListService
        boxoffice_service = BoxOfficeListService()

        # 取得所有電影資料
        all_movies = boxoffice_service._load_recent_movies_data()

        # 篩選出追蹤的電影
        tracked_movies = [
            movie for movie in all_movies
            if movie.get('movie_id') in tracked_movie_ids
        ]

        # 計算預警狀態
        attention_count = 0
        critical_count = 0

        for movie in tracked_movies:
            warning_status = movie.get('warning_status', '正常')
            if warning_status == '注意':
                attention_count += 1
            elif warning_status == '嚴重':
                critical_count += 1

        total_count = attention_count + critical_count

        return {
            'total_count': total_count,
            'attention_count': attention_count,
            'critical_count': critical_count
        }

    def get_all_stats(self, tracked_movie_ids: list = None) -> Dict:
        """
        取得首頁所有統計資料

        Args:
            tracked_movie_ids: 追蹤的電影 ID 列表

        Returns:
            包含所有統計資料的字典
        """
        recent_movies_stats = self.get_recent_movies_stats()

        # 取得預警電影統計
        # ⚠️ 臨時方案：從前端傳入追蹤的電影 ID 列表
        # 🔄 未來改進：從後端資料庫取得使用者的追蹤清單
        warning_stats = self.get_warning_stats(tracked_movie_ids)

        # 計算追蹤中電影數量
        # ⚠️ 臨時方案：從前端傳入的列表長度計算
        # 🔄 未來改進：從後端資料庫查詢使用者追蹤的電影數量
        tracked_count = len(tracked_movie_ids) if tracked_movie_ids else 0

        return {
            'recent_movies': recent_movies_stats,
            'tracked_movies': {
                'count': tracked_count
            },
            'warning_movies': warning_stats
        }
