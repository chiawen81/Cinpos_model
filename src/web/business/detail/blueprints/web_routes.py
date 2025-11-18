"""
前端頁面路由 Blueprint
處理所有返回 HTML 模板的路由
"""

from flask import Blueprint, render_template, jsonify
from services.movie_service import MovieService
from services.prediction_service import PredictionService
from utils.validators import validate_gov_id

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
    """電影列表頁面"""
    # 這裡應該從資料庫取得電影列表
    # 目前使用模擬資料
    movies = [
        {'gov_id': 'MOV001', 'title': '科技風暴', 'release_date': '2025-10-01'},
        {'gov_id': 'MOV002', 'title': '愛在深秋', 'release_date': '2025-09-15'},
    ]
    return render_template('movies_list.html', movies=movies)


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

    # 準備圖表資料
    chart_data = {
        'history': [record.to_dict() for record in history],
        'predictions': [pred.to_dict() for pred in predictions]
    }

    # 準備衰退率圖表資料
    decline_data = prepare_decline_chart_data(history)

    return render_template('movie_detail.html',
                         movie=movie,
                         history=history,
                         predictions=predictions,
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


# ============= 輔助函數 =============
def prepare_decline_chart_data(history):
    """
    準備衰退率圖表資料

    Args:
        history: 歷史票房記錄列表

    Returns:
        圖表資料字典
    """
    weeks = []
    decline_rates = []

    for i in range(1, len(history)):
        if history[i-1].boxoffice > 0:
            rate = (history[i].boxoffice - history[i-1].boxoffice) / history[i-1].boxoffice
            weeks.append(history[i].week)
            decline_rates.append(rate)

    avg_decline_rate = sum(decline_rates) / len(decline_rates) if decline_rates else 0

    return {
        'weeks': weeks,
        'decline_rates': decline_rates,
        'avg_decline_rate': avg_decline_rate
    }
