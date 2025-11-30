"""
票房列表服務
處理電影票房列表的資料讀取、篩選、排序、分頁
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import math


class BoxOfficeListService:
    """票房列表服務類別"""

    def __init__(self):
        """初始化服務"""
        # 設定資料目錄路徑
        base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
        self.weekly_dir = base_dir / "data" / "raw" / "boxoffice_weekly"
        self.permovie_full_dir = base_dir / "data" / "raw" / "boxoffice_permovie" / "full"

        # 初始化預測服務（延遲載入）
        self.prediction_service = None

        # 快取
        self._cache = {}

    def _get_prediction_service(self):
        """延遲載入預測服務"""
        if self.prediction_service is None:
            from services.prediction_service import PredictionService
            self.prediction_service = PredictionService()
        return self.prediction_service

    def get_boxoffice_list(
        self,
        page: int = 1,
        page_size: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_tracked: Optional[bool] = None,
        warning_status: Optional[str] = None,
        release_status: Optional[str] = None,
        is_first_run: Optional[bool] = None,
        sort_by: str = "release_date",
        sort_order: str = "desc"
    ) -> Dict:
        """
        取得票房列表資料

        Args:
            page: 頁碼（從1開始）
            page_size: 每頁筆數
            start_date: 起始上映日期 (YYYY-MM-DD)
            end_date: 結束上映日期 (YYYY-MM-DD)
            is_tracked: 是否在追蹤清單
            warning_status: 預警狀態（正常/注意/嚴重）
            release_status: 上映狀態（即將上映/上映中/已下檔）
            is_first_run: 是否首輪
            sort_by: 排序欄位
            sort_order: 排序方向 (asc/desc)

        Returns:
            包含列表資料和分頁資訊的字典
        """
        # 取得最近的週票房資料
        movies_data = self._load_recent_movies_data()

        # 篩選資料
        filtered_movies = self._filter_movies(
            movies_data,
            start_date=start_date,
            end_date=end_date,
            is_tracked=is_tracked,
            warning_status=warning_status,
            release_status=release_status,
            is_first_run=is_first_run
        )

        # 排序
        sorted_movies = self._sort_movies(filtered_movies, sort_by, sort_order)

        # 分頁
        total_count = len(sorted_movies)
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_movies = sorted_movies[start_idx:end_idx]

        return {
            "success": True,
            "data": paged_movies,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages
            }
        }

    def _load_recent_movies_data(self) -> List[Dict]:
        """
        載入最近的電影資料（最近兩週的週票房資料）

        Returns:
            電影資料列表
        """
        # 取得最近一週的檔案
        recent_files = self._get_recent_weekly_files(count=1)

        if len(recent_files) < 1:
            return []

        current_week_file = recent_files[0]

        # 載入週票房資料
        current_week_data = self._load_json_file(current_week_file)

        if not current_week_data:
            return []

        # 處理當前週的電影資料
        movies = []
        if current_week_data.get('data', {}).get('dataItems'):
            for item in current_week_data['data']['dataItems']:
                movie_id = item.get('movieId')
                if not movie_id:
                    continue

                # 取得電影完整資料（從 full 目錄）
                movie_detail = self._load_movie_detail_from_full(movie_id)

                if not movie_detail:
                    continue

                # 計算各項資料
                movie_data = self._process_movie_data(item, movie_detail)

                if movie_data:
                    movies.append(movie_data)

        return movies

    def _get_recent_weekly_files(self, count: int = 1) -> List[Path]:
        """
        取得最近的週票房檔案

        Args:
            count: 要取得的檔案數量

        Returns:
            檔案路徑列表，按時間從新到舊排序
        """
        all_files = []

        # 遍歷所有年份目錄
        for year_dir in sorted(self.weekly_dir.iterdir(), reverse=True):
            if year_dir.is_dir():
                json_files = list(year_dir.glob("boxoffice_*.json"))
                all_files.extend(json_files)

        # 按檔案名稱排序
        all_files.sort(reverse=True)

        return all_files[:count]

    def _load_json_file(self, file_path: Path) -> Optional[Dict]:
        """
        載入JSON檔案

        Args:
            file_path: 檔案路徑

        Returns:
            JSON資料字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"讀取檔案失敗 {file_path}: {e}")
            return None

    def _load_movie_detail_from_full(self, movie_id: str) -> Optional[Dict]:
        """
        從 full 目錄載入電影完整資料

        Args:
            movie_id: 電影ID

        Returns:
            電影完整資料
        """
        # 尋找對應的電影檔案
        movie_files = list(self.permovie_full_dir.glob(f"{movie_id}_*.json"))

        if not movie_files:
            return None

        return self._load_json_file(movie_files[0])

    def _process_movie_data(
        self,
        current_item: Dict,
        movie_detail: Dict
    ) -> Optional[Dict]:
        """
        處理電影資料，計算各項指標

        Args:
            current_item: 當前週的電影資料（從 weekly 檔案）
            movie_detail: 電影完整資料（從 full 目錄）

        Returns:
            處理後的電影資料
        """
        movie_id = current_item.get('movieId')
        movie_name = current_item.get('name', '未知電影')
        release_date_str = current_item.get('releaseDate')

        # 解析上映日期
        try:
            release_date = datetime.strptime(release_date_str, '%Y-%m-%d') if release_date_str else None
        except:
            release_date = None

        # 取得上映天數（用於判斷上映狀態）
        day_count = current_item.get('dayCount') or 0

        # 從電影詳細資料中取得週次資料
        weeks_data = []
        if movie_detail and movie_detail.get('data', {}).get('weeks'):
            weeks_data = movie_detail['data']['weeks']

        # 確保有足夠的週次資料
        if len(weeks_data) < 1:
            # 資料不足，無法計算
            return None

        # 計算當前週次
        # weeks_data 包含的是已結束的週次資料
        # 例如：有 3 筆歷史資料表示第 1、2、3 週已結束，當前週次應該是第 4 週
        total_weeks_with_data = len(weeks_data)
        current_week = total_weeks_with_data + 1

        # === 1. 上週實際票房 ===
        # weeks_data[-1] 是最後一筆歷史資料（上週）
        last_week_actual = weeks_data[-1].get('amount') if len(weeks_data) >= 1 else None

        # === 2. 上週衰退率 ===
        # 直接使用原始資料中的 rate 欄位（已經計算好的衰退率）
        # weeks_data[-1]['rate'] 表示上週相對於上上週的變化率
        last_week_decline_rate = weeks_data[-1].get('rate') if len(weeks_data) >= 1 else None

        # === 3. 當週預測周票房 ===
        # 目標：使用所有歷史資料，預測當前週（第 N+1 週）
        # 例如：如果有 3 週歷史資料，使用第 1、2、3 週預測第 4 週
        current_week_predicted = self._predict_boxoffice_for_week(
            movie_id,
            movie_detail,
            weeks_data,
            target_week=total_weeks_with_data + 1  # 預測第 N+1 週（當週）
        )

        # === 4. 上週預測周票房 ===
        # 目標：使用上上週之前的資料，預測上週（第 N 週）
        # 例如：如果有 3 週歷史資料，使用第 1、2 週預測第 3 週
        last_week_predicted = self._predict_boxoffice_for_week(
            movie_id,
            movie_detail,
            weeks_data,
            target_week=total_weeks_with_data  # 預測第 N 週（上週）
        )

        # === 5. 計算預測差距% ===
        # 公式：(上週實際 - 上週預測) / 上週預測
        prediction_accuracy = None
        if last_week_predicted and last_week_predicted > 0 and last_week_actual:
            prediction_accuracy = (last_week_actual - last_week_predicted) / last_week_predicted

        # 判斷預警狀態
        warning_status = self._calculate_warning_status(
            last_week_decline_rate,
            current_week
        )

        # 判斷上映狀態
        release_status = self._calculate_release_status(release_date, day_count)

        # 判斷是否首輪
        is_first_run = True  # 目前資料無法判斷，預設為首輪

        # 取得電影分級
        rating = movie_detail.get('data', {}).get('rating', '未分級')

        return {
            'movie_id': movie_id,
            'movie_name': movie_name,
            'release_date': release_date_str,
            'current_week': current_week,
            'current_week_predicted': current_week_predicted,  # 元
            'last_week_predicted': last_week_predicted,  # 元
            'last_week_actual': last_week_actual,  # 元
            'last_week_decline_rate': last_week_decline_rate,  # 小數（如 -0.3 表示 -30%）
            'prediction_accuracy': prediction_accuracy,  # 小數
            'warning_status': warning_status,
            'release_status': release_status,
            'is_first_run': is_first_run,
            'is_tracked': False,  # 預設未追蹤，需要整合追蹤功能
            'rating': rating,
            'theater_count': current_item.get('theaterCount', 0),
            'total_amount': current_item.get('totalAmount', 0)
        }

    def _predict_boxoffice_for_week(
        self,
        movie_id: str,
        movie_detail: Dict,
        weeks_data: List[Dict],
        target_week: int
    ) -> Optional[float]:
        """
        使用預測模型預測指定週的票房

        Args:
            movie_id: 電影ID
            movie_detail: 電影完整資料
            weeks_data: 週次資料列表
            target_week: 目標週次（1-based，如第3週）

        Returns:
            預測票房（元），如果無法預測則返回 None
        """
        try:
            # 需要至少 2 週的歷史資料才能預測
            if target_week < 3:
                print(f"[預測] movie_id={movie_id}, target_week={target_week}: 週次不足 < 3")
                return None

            # 準備預測所需的資料
            # 使用到目標週的前一週為止的資料
            history_weeks = weeks_data[:target_week - 1]

            if len(history_weeks) < 2:
                print(f"[預測] movie_id={movie_id}, target_week={target_week}: 歷史資料不足 (history_weeks={len(history_weeks)})")
                return None

            # 構建週次資料（與預測頁的格式一致）
            week_data = []
            for i, week in enumerate(history_weeks, start=1):
                week_data.append({
                    'week': i,
                    'boxoffice': week.get('amount', 0),
                    'audience': week.get('tickets', 0),
                    'screens': week.get('theaterCount', 0)
                })

            # 構建電影資訊（與預測頁的格式一致）
            data = movie_detail.get('data', {})
            movie_info = {
                'gov_id': movie_id,
                'name': data.get('name', ''),
                'release_date': data.get('releaseDate', ''),
                'film_length': (data.get('filmLength', 0) or 0) / 60,  # 轉換為分鐘
                'is_restricted': 1 if data.get('rating', '').startswith('限制級') else 0,
                'open_week1_days': 7  # 預設7天
            }

            # 使用預測服務進行預測
            prediction_service = self._get_prediction_service()
            result = prediction_service.predict_new_movie(
                week_data=week_data,
                movie_info=movie_info,
                predict_weeks=1  # 只預測下一週
            )

            if result.get('success') and result.get('predictions'):
                # 返回預測的票房
                predicted_value = result['predictions'][0].get('boxoffice')
                print(f"[預測成功] movie_id={movie_id}, target_week={target_week}: {predicted_value}")
                return predicted_value
            else:
                error_msg = result.get('error', '未知錯誤')
                print(f"[預測失敗] movie_id={movie_id}, target_week={target_week}: {error_msg}")
                return None

        except Exception as e:
            print(f"[預測異常] movie_id={movie_id}, target_week={target_week}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _calculate_warning_status(
        self,
        decline_rate: Optional[float],
        current_week: int
    ) -> str:
        """
        計算預警狀態

        Args:
            decline_rate: 衰退率
            current_week: 當前週次

        Returns:
            預警狀態 (正常/注意/嚴重)
        """
        if decline_rate is None:
            return "正常"

        # 簡化的預警邏輯（未來可整合 decline_warning_service）
        # 第1-3週：衰退率超過50%為嚴重，超過30%為注意
        # 第4週以後：衰退率超過40%為嚴重，超過25%為注意

        if current_week <= 3:
            if decline_rate < -0.5:
                return "嚴重"
            elif decline_rate < -0.3:
                return "注意"
        else:
            if decline_rate < -0.4:
                return "嚴重"
            elif decline_rate < -0.25:
                return "注意"

        return "正常"

    def _calculate_release_status(
        self,
        release_date: Optional[datetime],
        day_count: int
    ) -> str:
        """
        計算上映狀態

        Args:
            release_date: 上映日期
            day_count: 上映天數

        Returns:
            上映狀態 (即將上映/上映中/已下檔)
        """
        if not release_date:
            return "上映中"

        today = datetime.now()

        # 即將上映：上映日期在未來
        if release_date > today:
            return "即將上映"

        # 已下檔：上映超過10週（70天）
        if day_count and day_count > 70:
            return "已下檔"

        return "上映中"

    def _filter_movies(
        self,
        movies: List[Dict],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_tracked: Optional[bool] = None,
        warning_status: Optional[str] = None,
        release_status: Optional[str] = None,
        is_first_run: Optional[bool] = None
    ) -> List[Dict]:
        """
        篩選電影資料

        Args:
            movies: 電影列表
            start_date: 起始上映日期
            end_date: 結束上映日期
            is_tracked: 是否在追蹤清單
            warning_status: 預警狀態
            release_status: 上映狀態
            is_first_run: 是否首輪

        Returns:
            篩選後的電影列表
        """
        filtered = movies

        # 篩選上映日期範圍
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                filtered = [
                    m for m in filtered
                    if m.get('release_date') and
                    datetime.strptime(m['release_date'], '%Y-%m-%d') >= start_dt
                ]
            except:
                pass

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                filtered = [
                    m for m in filtered
                    if m.get('release_date') and
                    datetime.strptime(m['release_date'], '%Y-%m-%d') <= end_dt
                ]
            except:
                pass

        # 篩選追蹤清單
        if is_tracked is not None:
            filtered = [m for m in filtered if m.get('is_tracked') == is_tracked]

        # 篩選預警狀態
        if warning_status:
            filtered = [m for m in filtered if m.get('warning_status') == warning_status]

        # 篩選上映狀態
        if release_status:
            filtered = [m for m in filtered if m.get('release_status') == release_status]

        # 篩選是否首輪
        if is_first_run is not None:
            filtered = [m for m in filtered if m.get('is_first_run') == is_first_run]

        return filtered

    def _sort_movies(
        self,
        movies: List[Dict],
        sort_by: str = "release_date",
        sort_order: str = "desc"
    ) -> List[Dict]:
        """
        排序電影列表

        Args:
            movies: 電影列表
            sort_by: 排序欄位
            sort_order: 排序方向 (asc/desc)

        Returns:
            排序後的電影列表
        """
        reverse = (sort_order.lower() == "desc")

        # 定義排序鍵
        sort_key_map = {
            "release_date": lambda m: m.get('release_date') or '',
            "current_week": lambda m: m.get('current_week') or 0,
            "movie_name": lambda m: m.get('movie_name') or '',
            "last_week_decline_rate": lambda m: m.get('last_week_decline_rate') or 0,
            "current_week_predicted": lambda m: m.get('current_week_predicted') or 0,
        }

        sort_key = sort_key_map.get(sort_by, sort_key_map["release_date"])

        try:
            return sorted(movies, key=sort_key, reverse=reverse)
        except:
            return movies
