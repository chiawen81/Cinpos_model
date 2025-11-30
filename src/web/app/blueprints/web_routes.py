"""
前端頁面路由 Blueprint
處理所有返回 HTML 模板的路由
"""

from flask import Blueprint, render_template, jsonify
from ..services.movie_service import MovieService
from ..services.prediction_service import PredictionService
from ..utils.validators import validate_gov_id

# 建立 Blueprint
web_bp = Blueprint('web', __name__)

# 初始化服務
movie_service = MovieService()
prediction_service = PredictionService()


@web_bp.route('/')
def index():
    """首頁 - 總覽儀表板"""
    return render_template('index.html')


@web_bp.route('/movies')
def movies_list():
    """
    電影列表頁面

    注意：此頁面目前未啟用
    實際的電影列表在首頁（/）中透過 API 載入
    """
    # TODO: 如果需要獨立的電影列表頁面，從資料庫或檔案系統取得電影列表
    return render_template('movies_list.html', movies=[])


@web_bp.route('/movie/<gov_id>')
def movie_detail(gov_id):
    """
    單部電影詳細頁面

    Args:
        gov_id: 政府代號
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    # 取得電影資料
    movie = movie_service.get_movie_by_id(gov_id)
    if not movie:
        return render_template('404.html', message='電影不存在'), 404

    # 取得歷史票房資料
    history = movie_service.get_boxoffice_history(gov_id)

    # 取得預測資料
    predictions = prediction_service.predict_movie_boxoffice(gov_id, weeks=3)

    # 取得統計資料
    statistics = movie_service.calculate_statistics(gov_id)

    # 取得預警資訊
    warning = prediction_service.check_decline_warning(gov_id)

    # 為每個預測加入預警資訊（用於表格顯示）
    predictions_with_warnings = []
    if len(history) >= 2:
        # 使用統一的開片實力計算方法
        week_1_boxoffice = history[0].boxoffice
        week_2_boxoffice = history[1].boxoffice if len(history) > 1 else week_1_boxoffice
        opening_strength = prediction_service.calculate_opening_strength(
            week_1_boxoffice,
            week_2_boxoffice
        )

        # 為每個預測加入預警
        warning_service = prediction_service.warning_service
        for pred in predictions:
            pred_dict = pred.to_dict()
            warning_info = warning_service.check_decline_warning(
                opening_strength=opening_strength,
                current_week=pred.week,
                predicted_decline_rate=pred.decline_rate,
            )
            pred_dict['warning'] = warning_info
            predictions_with_warnings.append(pred_dict)
    else:
        predictions_with_warnings = [pred.to_dict() for pred in predictions]

    # 準備圖表資料
    chart_data = {
        'history': [record.to_dict() for record in history],
        'predictions': [pred.to_dict() for pred in predictions]
    }

    # 準備衰退率圖表資料
    decline_data = movie_service.prepare_decline_chart_data(history)

    return render_template('movie_detail.html',
                         movie=movie,
                         history=history,
                         predictions=predictions_with_warnings,
                         statistics=statistics,
                         warning=warning,
                         chart_data=chart_data,
                         decline_data=decline_data)


@web_bp.route('/predictions')
def predictions():
    """預測分析頁面"""
    return render_template('predictions.html')


@web_bp.route('/predict-new')
def predict_new():
    """新電影預測頁面"""
    return render_template('predict.html')


@web_bp.route('/reports')
def reports():
    """報表中心頁面"""
    return render_template('reports.html')
