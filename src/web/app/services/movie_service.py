"""
電影資料服務

從 data/raw/boxoffice_permovie/full 載入真實票房資料
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models.movie import BoxOfficeRecord, Movie
from ..utils.box_office_utils import (
    calculate_decline_rate,
    calculate_first_week_daily_avg,
    parse_date_range,
    parse_release_date,
)


class MovieService:
    """電影資料服務：負責讀取電影資訊和票房歷史記錄"""

    def __init__(self, data_path: Optional[Path] = None):
        """
        初始化服務

        Args:
            data_path: 資料目錄路徑（預設：data/raw/boxoffice_permovie/full）
        """
        base_dir = Path(__file__).resolve().parents[5]
        self.data_path = data_path or base_dir / "data" / "raw" / "boxoffice_permovie" / "full"

        # 快取：避免重複讀取檔案
        self.movies_cache: Dict[str, Movie] = {}
        self.boxoffice_cache: Dict[str, List[BoxOfficeRecord]] = {}
        self.raw_cache: Dict[str, Dict] = {}
        self.movie_file_index: Optional[Dict[str, Path]] = None

        if self.data_path.exists():
            self.load_data()

    def load_data(self) -> None:
        """建立電影 ID 到檔案路徑的索引，加速查詢"""
        self.movie_file_index = {}
        for file_path in self.data_path.glob("*.json"):
            # 從檔名提取電影 ID（例如："13460_仲夏魘.json" -> "13460"）
            movie_id = file_path.name.split("_", 1)[0]
            self.movie_file_index[movie_id] = file_path

    def get_movie_by_id(self, gov_id: str) -> Optional[Movie]:
        """
        根據政府代號取得電影資訊

        Args:
            gov_id: 政府電影代號（例如："13460"）

        Returns:
            電影物件，如果找不到則返回 None
        """
        gov_id = str(gov_id)

        # 檢查快取
        if gov_id in self.movies_cache:
            return self.movies_cache[gov_id]

        # 載入原始資料
        data = self._load_movie_payload(gov_id)
        if not data:
            return None

        # 解析並建立電影物件
        release_date = parse_release_date(data.get("releaseDate"))
        movie = Movie(
            gov_id=gov_id,
            title=data.get("name", ""),
            duration=self._parse_duration_minutes(data.get("filmLength")),
            director=self._extract_director(data.get("filmMembers", [])),
            actors=self._extract_actors(data.get("filmMembers", [])),
            country=data.get("region", "") or "",
            release_date=release_date or datetime.now(),
            distributor=data.get("publisher"),
            rating=data.get("rating"),
            genre=self._extract_genres(data),
        )

        # 存入快取
        self.movies_cache[gov_id] = movie
        return movie

    def get_movie_raw_data(self, gov_id: str) -> Optional[Dict]:
        """
        取得電影的原始 JSON 資料

        Args:
            gov_id: 政府電影代號

        Returns:
            原始資料字典，如果找不到則返回 None
        """
        return self._load_movie_payload(str(gov_id))

    def get_boxoffice_history(self, gov_id: str) -> List[BoxOfficeRecord]:
        """
        取得電影的歷史票房記錄

        Args:
            gov_id: 政府電影代號

        Returns:
            票房記錄列表，按週次排序
            每筆記錄會動態附加 decline_rate 屬性（衰退率）
        """
        gov_id = str(gov_id)

        # 檢查快取
        if gov_id in self.boxoffice_cache:
            return self.boxoffice_cache[gov_id]

        # 載入原始資料
        data = self._load_movie_payload(gov_id)
        if not data:
            return []

        # 取得週次資料（優先使用 weeks，其次 weekends）
        weeks_data = data.get("weeks") or data.get("weekends") or []
        history: List[BoxOfficeRecord] = []

        for item in weeks_data:
            amount = item.get("amount")
            tickets = item.get("tickets")

            # 跳過沒有票房和觀影人次的記錄
            if amount is None and tickets is None:
                continue

            # 建立票房記錄
            record = BoxOfficeRecord(
                gov_id=gov_id,
                week=len(history) + 1,  # 週次從 1 開始編號
                boxoffice=float(amount or 0),
                audience=int(tickets or 0),
                screens=int(item.get("theaterCount") or 0),
                date=self._parse_week_start(item.get("date")),
            )

            # 計算衰退率（使用共用工具函數）
            if history and history[-1].boxoffice > 0:
                decline_rate = calculate_decline_rate(record.boxoffice, history[-1].boxoffice)
            else:
                decline_rate = None

            # 動態附加衰退率屬性
            setattr(record, "decline_rate", decline_rate)
            history.append(record)

        # 存入快取
        self.boxoffice_cache[gov_id] = history
        return history

    def get_current_week_data(self, gov_id: str) -> Dict:
        """
        準備預測模型所需的當前週資料

        Args:
            gov_id: 政府電影代號

        Returns:
            包含最新週次、前兩週票房、開片資訊等的字典
            如果資料不足（少於 2 週），返回空字典
        """
        history = self.get_boxoffice_history(gov_id)
        movie = self.get_movie_by_id(gov_id)
        raw_data = self._load_movie_payload(gov_id)

        # 至少需要 2 週資料才能進行預測
        if len(history) < 2:
            return {}

        # 取得最新兩週和開片兩週的記錄
        latest_week = history[-1]
        previous_week = history[-2]
        open_week1 = history[0] if history else None
        open_week2 = history[1] if len(history) > 1 else None

        # 計算第一週日均票房和放映天數
        open_week1_daily_avg = 0
        open_week1_days = 7
        if open_week1 and raw_data:
            # 取得第一週的日期範圍和上映日期
            weeks_data = raw_data.get("weeks") or raw_data.get("weekends") or []
            first_week_date_range = weeks_data[0].get("date") if weeks_data else None
            release_date = raw_data.get("releaseDate")

            # 使用共用工具函數計算
            from utils.box_office_utils import calculate_first_week_days
            open_week1_days = calculate_first_week_days(first_week_date_range, release_date)
            open_week1_daily_avg = calculate_first_week_daily_avg(
                open_week1.boxoffice,
                first_week_date_range,
                release_date
            )

        return {
            "gov_id": str(gov_id),
            "current_week": latest_week.week,
            # 模型訓練時的欄位
            "round_idx": 1,  # 輪次索引（預設為1）
            "gap_real_week_2to1": 1,  # week_2 到 week_1 的週數間隔
            "gap_real_week_1tocurrent": 1,  # week_1 到當前週的週數間隔
            # 最新兩週的票房資料
            "boxoffice_week_1": latest_week.boxoffice,
            "boxoffice_week_2": previous_week.boxoffice,
            "audience_week_1": latest_week.audience,
            "audience_week_2": previous_week.audience,
            "screens_week_1": latest_week.screens,
            "screens_week_2": previous_week.screens,
            # 開片資訊
            "open_week1_days": open_week1_days,
            "open_week1_boxoffice": open_week1.boxoffice if open_week1 else 0,
            "open_week1_boxoffice_daily_avg": open_week1_daily_avg,
            "open_week2_boxoffice": open_week2.boxoffice if open_week2 else 0,
            # 電影屬性
            "film_length": movie.duration if movie else 120,
            "release_year": movie.release_date.year if movie else 2025,
            "release_month": movie.release_date.month if movie else 1,
            "is_restricted": 1 if movie and movie.rating and "限" in movie.rating else 0,
        }

    def calculate_statistics(self, gov_id: str) -> Dict:
        """
        計算電影的統計資訊

        Args:
            gov_id: 政府電影代號

        Returns:
            統計資訊字典，包含：
            - 累計票房、觀影人次
            - 平均衰退率
            - 最高週票房
            - 本週各項衰退率
        """
        history = self.get_boxoffice_history(gov_id)
        if not history:
            return {}

        # 累計數據
        total_boxoffice = sum(record.boxoffice for record in history)
        total_audience = sum(record.audience for record in history)

        # 計算平均衰退率
        decline_rates: List[float] = []
        for current, previous in zip(history[1:], history[:-1]):
            rate = calculate_decline_rate(current.boxoffice, previous.boxoffice)
            if rate is not None:
                decline_rates.append(rate)

        avg_decline_rate = sum(decline_rates) / len(decline_rates) if decline_rates else 0

        # 找出票房最高的週次
        peak_week_record = max(history, key=lambda record: record.boxoffice)

        # 計算本週各項衰退率
        current_decline_rate = 0.0
        audience_decline_rate = 0.0
        screens_decline_rate = 0.0

        if len(history) >= 2:
            latest = history[-1]
            previous = history[-2]

            # 票房衰退率
            rate = calculate_decline_rate(latest.boxoffice, previous.boxoffice)
            current_decline_rate = rate if rate is not None else 0.0

            # 觀影人次衰退率
            rate = calculate_decline_rate(latest.audience, previous.audience)
            audience_decline_rate = rate if rate is not None else 0.0

            # 廳數衰退率
            rate = calculate_decline_rate(latest.screens, previous.screens)
            screens_decline_rate = rate if rate is not None else 0.0

        return {
            # 累計數據（當輪）
            "total_boxoffice": total_boxoffice,
            "total_audience": total_audience,
            # 跨輪累計（模擬值：當輪 * 1.25）
            "cross_round_total_boxoffice": total_boxoffice * 1.25,
            "cross_round_total_audience": int(total_audience * 1.25),
            # 衰退率統計
            "avg_decline_rate": avg_decline_rate,
            "current_decline_rate": current_decline_rate,
            "audience_decline_rate": audience_decline_rate,
            "screens_decline_rate": screens_decline_rate,
            # 最高週資訊
            "peak_week": peak_week_record.week,
            "peak_boxoffice": peak_week_record.boxoffice,
            # 上映週數
            "weeks_released": len(history),
        }

    def prepare_decline_chart_data(self, history: List[BoxOfficeRecord]) -> Dict:
        """
        準備衰退率分析圖表所需的資料

        Args:
            history: 票房歷史記錄列表

        Returns:
            包含週次、衰退率陣列和平均衰退率的字典
        """
        weeks: List[int] = []
        decline_rates: List[float] = []

        # 提取每週的衰退率（跳過 None 值）
        for record in history:
            decline_rate = getattr(record, "decline_rate", None)
            if decline_rate is None:
                continue
            weeks.append(record.week)
            decline_rates.append(decline_rate)

        # 計算平均衰退率
        avg_decline_rate = sum(decline_rates) / len(decline_rates) if decline_rates else 0

        return {
            "weeks": weeks,
            "decline_rates": decline_rates,
            "avg_decline_rate": avg_decline_rate,
        }

    def _load_movie_payload(self, gov_id: str) -> Optional[Dict]:
        """
        載入電影的原始 JSON 資料（內部方法）

        Args:
            gov_id: 政府電影代號

        Returns:
            JSON 的 data 欄位內容，如果載入失敗則返回 None
        """
        gov_id = str(gov_id)

        # 檢查快取
        if gov_id in self.raw_cache:
            return self.raw_cache[gov_id]

        # 取得檔案路徑
        file_path = self._get_movie_file_path(gov_id)
        if not file_path:
            return None

        # 讀取並解析 JSON
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        # 提取 data 欄位
        data = payload.get("data")
        if not data:
            return None

        # 存入快取
        self.raw_cache[gov_id] = data
        return data

    def _get_movie_file_path(self, gov_id: str) -> Optional[Path]:
        """
        取得電影資料檔案的路徑（內部方法）

        Args:
            gov_id: 政府電影代號

        Returns:
            檔案路徑，如果找不到則返回 None
        """
        movie_id = str(gov_id)

        # 確保索引已建立
        if self.movie_file_index is None:
            self.load_data()

        # 從索引中查找
        if self.movie_file_index and movie_id in self.movie_file_index:
            return self.movie_file_index[movie_id]

        # 直接搜尋檔案（作為備用方案）
        matches = list(self.data_path.glob(f"{movie_id}_*.json"))
        if matches:
            # 更新索引
            if self.movie_file_index is not None:
                self.movie_file_index[movie_id] = matches[0]
            return matches[0]

        return None

    @staticmethod
    def _parse_duration_minutes(film_length: Optional[float]) -> int:
        """
        解析片長（從秒轉換為分鐘）

        Args:
            film_length: 片長（秒）

        Returns:
            片長（分鐘），如果解析失敗則返回 0
        """
        if film_length in (None, "", 0):
            return 0
        try:
            # 原始資料儲存的是秒數，需要轉換為分鐘
            return max(int(float(film_length) / 60), 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_week_start(date_range: Optional[str]) -> Optional[datetime]:
        """
        從日期範圍中提取起始日期

        Args:
            date_range: 日期範圍（格式："2025-01-01~2025-01-07"）

        Returns:
            起始日期，如果解析失敗則返回 None
        """
        if not date_range:
            return None

        # 提取 "~" 之前的部分
        start_date = str(date_range).split("~", 1)[0]

        try:
            return datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            return None

    @staticmethod
    def _extract_director(members: List[Dict]) -> str:
        """
        從電影成員列表中提取導演名稱

        Args:
            members: 電影成員列表（來自 filmMembers 欄位）

        Returns:
            導演名稱，如果找不到則返回空字串
        """
        for member in members or []:
            type_name = member.get("typeName") or ""
            if "導演" in type_name:
                return member.get("name") or member.get("originalName") or ""
        return ""

    @staticmethod
    def _extract_actors(members: List[Dict]) -> List[str]:
        """
        從電影成員列表中提取演員名稱

        Args:
            members: 電影成員列表（來自 filmMembers 欄位）

        Returns:
            演員名稱列表
            如果沒有標記為演員的成員，則返回前 5 位成員作為備用
        """
        actors: List[str] = []

        # 提取標記為演員的成員
        for member in members or []:
            type_name = member.get("typeName") or ""
            if any(keyword in type_name for keyword in ("演員", "主演")):
                name = member.get("name") or member.get("originalName")
                if name:
                    actors.append(name)

        if actors:
            return actors

        # 備用方案：如果沒有角色標記，返回前幾位成員
        for member in members or []:
            name = member.get("name")
            if name:
                actors.append(name)
            if len(actors) >= 5:
                break

        return actors

    @staticmethod
    def _extract_genres(data: Dict) -> Optional[List[str]]:
        """
        提取電影類型

        Args:
            data: 電影原始資料

        Returns:
            類型列表，如果沒有則返回 None
        """
        # 嘗試從 classes 或 filmClasses 取得類型
        genres = data.get("classes") or data.get("filmClasses")
        if not genres:
            return None

        # 處理列表格式
        if isinstance(genres, list):
            return [str(item) for item in genres if item]

        # 處理字串格式（可能用逗號或頓號分隔）
        if isinstance(genres, str):
            parts = [part.strip() for part in genres.replace("、", ",").split(",")]
            return [part for part in parts if part]

        return None
