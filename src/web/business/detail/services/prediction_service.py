"""
預測服務
說明: 整合預測模型與資料服務，提供完整的預測功能
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
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
                week=pred['week'],
                predicted_boxoffice=pred['predicted_boxoffice'],
                confidence_lower=pred['confidence_lower'],
                confidence_upper=pred['confidence_upper'],
                decline_rate=pred['decline_rate']
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
        avg_decline_rate = stats.get('avg_decline_rate', 0)
        
        # 取得預測
        predictions = self.predict_movie_boxoffice(gov_id, weeks=1)
        
        if not predictions:
            return {
                'has_warning': False,
                'message': '無法計算預警資訊'
            }
        
        next_week_decline = predictions[0].decline_rate
        
        # 檢查是否低於平均或門檻
        threshold = self.config.DECLINE_RATE_THRESHOLD
        
        warning_info = {
            'has_warning': False,
            'next_week_decline': next_week_decline,
            'avg_decline_rate': avg_decline_rate,
            'threshold': threshold,
            'message': ''
        }
        
        if next_week_decline < threshold:
            warning_info['has_warning'] = True
            warning_info['message'] = f'預測下週票房衰退率 {next_week_decline:.1%}，超過門檻 {threshold:.0%}'
        elif next_week_decline < avg_decline_rate * 1.5:  # 比平均衰退快50%
            warning_info['has_warning'] = True
            warning_info['message'] = f'預測下週票房衰退速度異常，比平均快 {abs(next_week_decline/avg_decline_rate - 1):.0%}'
        
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
            'gov_id': gov_id,
            'history': [
                {
                    'week': record.week,
                    'boxoffice': record.boxoffice,
                    'audience': record.audience,
                    'screens': record.screens,
                    'date': record.date.isoformat() if record.date else None,
                    'type': 'actual'
                }
                for record in history
            ],
            'predictions': [
                {
                    'week': pred.week,
                    'boxoffice': pred.predicted_boxoffice,
                    'confidence_lower': pred.confidence_lower,
                    'confidence_upper': pred.confidence_upper,
                    'decline_rate': pred.decline_rate,
                    'type': 'predicted'
                }
                for pred in predictions
            ]
        }
        
        # 加入統計資訊
        stats = self.movie_service.calculate_statistics(gov_id)
        combined_data['statistics'] = stats
        
        # 加入預警資訊
        warning = self.check_decline_warning(gov_id)
        combined_data['warning'] = warning
        
        return combined_data
    
    def export_report(self, gov_id: str, format: str = 'csv') -> Tuple[bytes, str]:
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
        for item in data['history']:
            rows.append({
                '週次': f"第{item['week']}週",
                '類型': '實際',
                '票房': item['boxoffice'],
                '觀影人數': item['audience'],
                '廳數': item['screens'],
                '信心區間下界': '',
                '信心區間上界': '',
                '衰退率': ''
            })
        
        # 加入預測資料
        for item in data['predictions']:
            rows.append({
                '週次': f"第{item['week']}週",
                '類型': '預測',
                '票房': item['boxoffice'],
                '觀影人數': '',
                '廳數': '',
                '信心區間下界': item['confidence_lower'],
                '信心區間上界': item['confidence_upper'],
                '衰退率': f"{item['decline_rate']:.1%}"
            })
        
        df = pd.DataFrame(rows)
        
        # 根據格式匯出
        buffer = io.BytesIO()
        
        if format == 'excel':
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='票房預測', index=False)
                
                # 加入統計資訊表
                stats_df = pd.DataFrame([data['statistics']])
                stats_df.to_excel(writer, sheet_name='統計資訊', index=False)
            
            filename = f"boxoffice_prediction_{gov_id}.xlsx"
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:  # CSV
            df.to_csv(buffer, index=False, encoding='utf-8-sig')
            filename = f"boxoffice_prediction_{gov_id}.csv"
            content_type = 'text/csv'
        
        buffer.seek(0)
        return buffer.read(), filename
