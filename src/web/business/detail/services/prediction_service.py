"""
預測服務
說明: 整合預測模型與資料服務，提供完整的預測功能
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys

# 加入 ML_boxoffice 路徑以便匯入預測模組
# Path: services/prediction_service.py -> services/ -> detail/ -> business/ -> web/ -> src/
src_root = Path(__file__).parent.parent.parent.parent.parent
ml_path = src_root / "ML_boxoffice" / "phase5_apply"
if not ml_path.exists():
    raise ImportError(f"ML module path not found: {ml_path}")
sys.path.insert(0, str(ml_path))

from M1_predict_new_movie import M1NewMoviePredictor
from models.prediction import BoxOfficePredictionModel, AudiencePredictionModel
from models.movie import BoxOfficePrediction
from services.movie_service import MovieService
from config import Config


class PredictionService:
    """預測服務類別"""

    def __init__(self, model_path: Optional[Path] = None):
        """
        初始化預測服務

        Args:
            model_path: 模型檔案路徑
        """
        self.boxoffice_model = BoxOfficePredictionModel(model_path)
        self.audience_model = AudiencePredictionModel(model_path)
        self.movie_service = MovieService()
        self.config = Config()

        # 初始化新電影預測器（使用延遲載入模式，避免啟動時載入模型失敗）
        self.new_movie_predictor = M1NewMoviePredictor(model_path, lazy_load=True)

    def predict_movie_boxoffice(self, gov_id: str, weeks: int = 3) -> List[BoxOfficePrediction]:
        """
        預測電影未來票房

        Args:
            gov_id: 政府代號
            weeks: 預測週數

        Returns:
            預測結果列表
        """
        # 取得當前資料
        current_data = self.movie_service.get_current_week_data(gov_id)

        if not current_data:
            return []

        # 進行預測
        predictions_raw = self.boxoffice_model.predict_multi_week(current_data, weeks)

        # 轉換為 BoxOfficePrediction 物件
        predictions = []
        for pred in predictions_raw:
            prediction = BoxOfficePrediction(
                gov_id=gov_id,
                week=pred["week"],
                predicted_boxoffice=pred["predicted_boxoffice"],
                confidence_lower=pred["confidence_lower"],
                confidence_upper=pred["confidence_upper"],
                decline_rate=pred["decline_rate"],
            )
            predictions.append(prediction)

        return predictions

    def check_decline_warning(self, gov_id: str) -> Dict:
        """
        檢查票房衰退預警

        Args:
            gov_id: 政府代號

        Returns:
            預警資訊字典
        """
        # 取得歷史統計
        stats = self.movie_service.calculate_statistics(gov_id)
        avg_decline_rate = stats.get("avg_decline_rate", 0)

        # 取得預測
        predictions = self.predict_movie_boxoffice(gov_id, weeks=1)

        if not predictions:
            return {"has_warning": False, "message": "無法計算預警資訊"}

        next_week_decline = predictions[0].decline_rate

        # 檢查是否低於平均或門檻
        threshold = self.config.DECLINE_RATE_THRESHOLD

        warning_info = {
            "has_warning": False,
            "next_week_decline": next_week_decline,
            "avg_decline_rate": avg_decline_rate,
            "threshold": threshold,
            "message": "",
        }

        if next_week_decline < threshold:
            warning_info["has_warning"] = True
            warning_info["message"] = (
                f"預測下週票房衰退率 {next_week_decline:.1%}，超過門檻 {threshold:.0%}"
            )
        elif next_week_decline < avg_decline_rate * 1.5:  # 比平均衰退快50%
            warning_info["has_warning"] = True
            warning_info["message"] = (
                f"預測下週票房衰退速度異常，比平均快 {abs(next_week_decline/avg_decline_rate - 1):.0%}"
            )

        return warning_info

    def generate_combined_data(self, gov_id: str) -> Dict:
        """
        產生整合的歷史與預測資料

        Args:
            gov_id: 政府代號

        Returns:
            包含歷史與預測的完整資料
        """
        # 取得歷史資料
        history = self.movie_service.get_boxoffice_history(gov_id)

        # 取得預測資料
        predictions = self.predict_movie_boxoffice(gov_id, weeks=self.config.PREDICTION_WEEKS)

        # 整合資料
        combined_data = {
            "gov_id": gov_id,
            "history": [
                {
                    "week": record.week,
                    "boxoffice": record.boxoffice,
                    "audience": record.audience,
                    "screens": record.screens,
                    "date": record.date.isoformat() if record.date else None,
                    "type": "actual",
                }
                for record in history
            ],
            "predictions": [
                {
                    "week": pred.week,
                    "boxoffice": pred.predicted_boxoffice,
                    "confidence_lower": pred.confidence_lower,
                    "confidence_upper": pred.confidence_upper,
                    "decline_rate": pred.decline_rate,
                    "type": "predicted",
                }
                for pred in predictions
            ],
        }

        # 加入統計資訊
        stats = self.movie_service.calculate_statistics(gov_id)
        combined_data["statistics"] = stats

        # 加入預警資訊
        warning = self.check_decline_warning(gov_id)
        combined_data["warning"] = warning

        return combined_data

    def predict_new_movie(
        self, week_data: List[Dict], movie_info: Dict, predict_weeks: int = 3
    ) -> Dict:
        """
        預測新電影未來票房

        Args:
            week_data: 已知的週次資料列表 [{week: 1, boxoffice: xxx, audience: xxx, screens: xxx}, ...]
            movie_info: 電影基本資訊 {name, release_date, film_length, is_restricted, ...}
            predict_weeks: 要預測的週數（預設3週）

        Returns:
            包含歷史資料、預測結果、統計資訊的字典
        """
        try:
            # 進行預測
            predictions = self.new_movie_predictor.predict_multi_weeks(
                week_data=week_data, movie_info=movie_info, predict_weeks=predict_weeks
            )

            # 計算統計資訊
            total_actual_boxoffice = sum(w["boxoffice"] for w in week_data)
            total_predicted_boxoffice = sum(p["predicted_boxoffice"] for p in predictions)
            avg_decline_rate = (
                sum(p["decline_rate"] for p in predictions) / len(predictions) if predictions else 0
            )

            # 檢查異常警示
            warnings = []
            for pred in predictions:
                if pred["decline_rate"] < -0.5:  # 衰退超過 50%
                    warnings.append(
                        {
                            "week": pred["week"],
                            "type": "high_decline",
                            "message": f"第 {pred['week']} 週預測衰退率過高 ({pred['decline_rate']:.1%})",
                        }
                    )
                elif pred["predicted_boxoffice"] < 1000000:  # 票房低於 100 萬
                    warnings.append(
                        {
                            "week": pred["week"],
                            "type": "low_boxoffice",
                            "message": f"第 {pred['week']} 週預測票房過低 ({pred['predicted_boxoffice']:,.0f} 元)",
                        }
                    )

            # 組合結果
            result = {
                "success": True,
                "movie_info": movie_info,
                "history": [
                    {
                        "week": w["week"],
                        "boxoffice": w["boxoffice"],
                        "audience": w.get("audience", 0),
                        "screens": w.get("screens", 0),
                        "type": "actual",
                    }
                    for w in week_data
                ],
                "predictions": [
                    {
                        "week": p["week"],
                        "boxoffice": p["predicted_boxoffice"],
                        "audience": p["predicted_audience"],
                        "screens": p["predicted_screens"],
                        "decline_rate": p["decline_rate"],
                        "type": "predicted",
                    }
                    for p in predictions
                ],
                "statistics": {
                    "total_actual_boxoffice": total_actual_boxoffice,
                    "total_predicted_boxoffice": total_predicted_boxoffice,
                    "total_boxoffice": total_actual_boxoffice + total_predicted_boxoffice,
                    "avg_decline_rate": avg_decline_rate,
                    "weeks_count": len(week_data) + len(predictions),
                },
                "warnings": warnings,
            }

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "預測失敗，請檢查輸入資料是否正確",
            }

    def export_new_movie_report(
        self, prediction_result: Dict, format: str = "csv"
    ) -> Tuple[bytes, str]:
        """
        匯出新電影預測報表

        Args:
            prediction_result: predict_new_movie 的返回結果
            format: 檔案格式 ('csv' 或 'excel')

        Returns:
            (檔案內容, 檔案名稱)
        """
        import io
        import pandas as pd
        from datetime import datetime

        # 準備 DataFrame
        rows = []

        # 加入歷史資料
        for item in prediction_result["history"]:
            rows.append(
                {
                    "週次": f"第{item['week']}週",
                    "類型": "實際",
                    "票房": f"{item['boxoffice']:,.0f}",
                    "觀影人數": f"{item['audience']:,}" if item["audience"] else "-",
                    "廳數": f"{item['screens']}" if item["screens"] else "-",
                    "衰退率": "-",
                }
            )

        # 加入預測資料
        for item in prediction_result["predictions"]:
            rows.append(
                {
                    "週次": f"第{item['week']}週",
                    "類型": "預測",
                    "票房": f"{item['boxoffice']:,.0f}",
                    "觀影人數": f"{item['audience']:,}",
                    "廳數": f"{item['screens']}",
                    "衰退率": f"{item['decline_rate']:.1%}",
                }
            )

        df = pd.DataFrame(rows)

        # 根據格式匯出
        buffer = io.BytesIO()
        movie_name = prediction_result["movie_info"].get("name", "new_movie")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "excel":
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="票房預測", index=False)

                # 加入統計資訊表
                stats = prediction_result["statistics"]
                stats_df = pd.DataFrame(
                    [
                        {
                            "總實際票房": f"{stats['total_actual_boxoffice']:,.0f}",
                            "總預測票房": f"{stats['total_predicted_boxoffice']:,.0f}",
                            "累計總票房": f"{stats['total_boxoffice']:,.0f}",
                            "平均衰退率": f"{stats['avg_decline_rate']:.1%}",
                            "週數": stats["weeks_count"],
                        }
                    ]
                )
                stats_df.to_excel(writer, sheet_name="統計資訊", index=False)

                # 加入警示資訊
                if prediction_result["warnings"]:
                    warnings_df = pd.DataFrame(
                        [
                            {
                                "週次": f"第{w['week']}週",
                                "警示類型": w["type"],
                                "警示訊息": w["message"],
                            }
                            for w in prediction_result["warnings"]
                        ]
                    )
                    warnings_df.to_excel(writer, sheet_name="警示資訊", index=False)

            filename = f"{movie_name}_prediction_{timestamp}.xlsx"
        else:  # CSV
            df.to_csv(buffer, index=False, encoding="utf-8-sig")
            filename = f"{movie_name}_prediction_{timestamp}.csv"

        buffer.seek(0)
        return buffer.read(), filename

    def export_report(self, gov_id: str, format: str = "csv") -> Tuple[bytes, str]:
        """
        匯出報表

        Args:
            gov_id: 政府代號
            format: 檔案格式 ('csv' 或 'excel')

        Returns:
            (檔案內容, 檔案名稱)
        """
        import io
        import pandas as pd

        # 取得完整資料
        data = self.generate_combined_data(gov_id)

        # 準備 DataFrame
        rows = []

        # 加入歷史資料
        for item in data["history"]:
            rows.append(
                {
                    "週次": f"第{item['week']}週",
                    "類型": "實際",
                    "票房": item["boxoffice"],
                    "觀影人數": item["audience"],
                    "廳數": item["screens"],
                    "信心區間下界": "",
                    "信心區間上界": "",
                    "衰退率": "",
                }
            )

        # 加入預測資料
        for item in data["predictions"]:
            rows.append(
                {
                    "週次": f"第{item['week']}週",
                    "類型": "預測",
                    "票房": item["boxoffice"],
                    "觀影人數": "",
                    "廳數": "",
                    "信心區間下界": item["confidence_lower"],
                    "信心區間上界": item["confidence_upper"],
                    "衰退率": f"{item['decline_rate']:.1%}",
                }
            )

        df = pd.DataFrame(rows)

        # 根據格式匯出
        buffer = io.BytesIO()

        if format == "excel":
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="票房預測", index=False)

                # 加入統計資訊表
                stats_df = pd.DataFrame([data["statistics"]])
                stats_df.to_excel(writer, sheet_name="統計資訊", index=False)

            filename = f"boxoffice_prediction_{gov_id}.xlsx"
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:  # CSV
            df.to_csv(buffer, index=False, encoding="utf-8-sig")
            filename = f"boxoffice_prediction_{gov_id}.csv"
            content_type = "text/csv"

        buffer.seek(0)
        return buffer.read(), filename

    def export_preprocessed_data(
        self, week_data: List[Dict], movie_info: Dict
    ) -> Tuple[bytes, str]:
        """
        匯出經過特徵工程處理後的資料（用於驗證與訓練資料一致性）

        Args:
            week_data: 已知的週次資料列表
            movie_info: 電影基本資訊

        Returns:
            (CSV 檔案內容, 檔案名稱)
        """
        import io
        import pandas as pd
        from datetime import datetime
        import sys
        from pathlib import Path

        # 加入共用模組路徑
        src_root = Path(__file__).parent.parent.parent.parent.parent
        sys.path.insert(0, str(src_root / "ML_boxoffice"))

        from common.feature_engineering import BoxOfficeFeatureEngineer

        # 排序週次資料
        week_data = sorted(week_data, key=lambda x: x.get('week', 0))

        # 解析上映日期
        release_date = BoxOfficeFeatureEngineer.parse_release_date(movie_info.get('release_date'))

        # 計算首週實力指標
        opening_strength = BoxOfficeFeatureEngineer.calculate_opening_strength(week_data, release_date)

        # 為每一週生成完整特徵（從第 3 週開始，因為需要 week_1 和 week_2）
        rows = []

        for i in range(2, len(week_data)):  # 從第 3 週開始（index=2）
            target_week = week_data[i]['week']

            # 使用共用模組建立完整特徵
            features = BoxOfficeFeatureEngineer.build_prediction_features(
                week_data=week_data[:i],  # 只使用到當前週之前的資料
                movie_info=movie_info,
                target_week=target_week,
                use_predictions=False,
                predictions=None
            )

            # 組合成與 preprocessed_full.csv 相同格式的資料
            row = {
                'gov_id': movie_info.get('gov_id', 'web_input'),
                'round_idx': features.get('round_idx', 1),
                'current_week_active_idx': features.get('current_week_active_idx'),
                'gap_real_week_2to1': features.get('gap_real_week_2to1', 0),
                'gap_real_week_1tocurrent': features.get('gap_real_week_1tocurrent', 0),
                'boxoffice_week_2': features.get('boxoffice_week_2'),
                'boxoffice_week_1': features.get('boxoffice_week_1'),
                'audience_week_2': features.get('audience_week_2'),
                'audience_week_1': features.get('audience_week_1'),
                'screens_week_2': features.get('screens_week_2'),
                'screens_week_1': features.get('screens_week_1'),
                'open_week1_days': features.get('open_week1_days'),
                'open_week1_boxoffice': features.get('open_week1_boxoffice'),
                'open_week1_boxoffice_daily_avg': features.get('open_week1_boxoffice_daily_avg'),
                'open_week2_boxoffice': features.get('open_week2_boxoffice'),
                'amount': week_data[i].get('boxoffice', 0),  # 目標變數（當週實際票房）
                'release_year': features.get('release_year'),
                'film_length': features.get('film_length'),
                'is_restricted': features.get('is_restricted'),
                'release_month_sin': features.get('release_month_sin'),
                'release_month_cos': features.get('release_month_cos'),
            }

            rows.append(row)

        # 建立 DataFrame
        df = pd.DataFrame(rows)

        # 確保欄位順序與 preprocessed_full.csv 一致
        column_order = [
            'gov_id',
            'round_idx',
            'current_week_active_idx',
            'gap_real_week_2to1',
            'gap_real_week_1tocurrent',
            'boxoffice_week_2',
            'boxoffice_week_1',
            'audience_week_2',
            'audience_week_1',
            'screens_week_2',
            'screens_week_1',
            'open_week1_days',
            'open_week1_boxoffice',
            'open_week1_boxoffice_daily_avg',
            'open_week2_boxoffice',
            'amount',
            'release_year',
            'film_length',
            'is_restricted',
            'release_month_sin',
            'release_month_cos',
        ]

        df = df[column_order]

        # 匯出為 CSV
        buffer = io.BytesIO()
        df.to_csv(buffer, index=False, encoding='utf-8-sig')

        # 生成檔案名稱
        movie_name = movie_info.get('name', 'unknown_movie')
        # 清理檔名中的特殊字元，保留中文、英文、數字、底線、連字號
        import re
        safe_movie_name = re.sub(r'[^\w\s\-\u4e00-\u9fff]', '', movie_name)  # 保留中文字符
        safe_movie_name = safe_movie_name.replace(' ', '_')  # 空格替換為底線
        filename = f"cinpos_preprocessed_{safe_movie_name}.csv"

        buffer.seek(0)
        return buffer.read(), filename
