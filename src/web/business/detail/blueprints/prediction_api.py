"""
預測 API Blueprint
處理所有票房預測相關的 API 端點（自己開發的模型服務）
"""

from flask import Blueprint, request, jsonify, send_file
import io

from services.movie_service import MovieService
from services.prediction_service import PredictionService
from utils.validators import validate_gov_id, validate_export_format

# 建立 Blueprint
prediction_api_bp = Blueprint('prediction_api', __name__, url_prefix='/api')

# 初始化服務
movie_service = MovieService()
prediction_service = PredictionService()


@prediction_api_bp.route('/movie/<gov_id>')
def movie_detail(gov_id):
    """
    API: 取得電影詳細資料

    Args:
        gov_id: 政府代號

    Returns:
        JSON 格式的電影資料
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    # 取得完整資料
    data = prediction_service.generate_combined_data(gov_id)

    return jsonify(data)


@prediction_api_bp.route('/movie/<gov_id>/key-metrics')
def movie_key_metrics(gov_id):
    """
    API: 關鍵指標卡片資料
    """
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    statistics = movie_service.calculate_statistics(gov_id)
    if not statistics:
        return jsonify({'success': False, 'error': '找不到電影票房資料'}), 404

    warning = prediction_service.check_decline_warning(gov_id)

    return jsonify({
        'success': True,
        'data': {
            'statistics': statistics,
            'warning': warning
        }
    })


@prediction_api_bp.route('/movie/<gov_id>/basic-info')
def movie_basic_info(gov_id):
    """
    API: 電影基本資訊
    """
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    movie = movie_service.get_movie_by_id(gov_id)
    raw_data = movie_service.get_movie_raw_data(gov_id)

    if not movie or not raw_data:
        return jsonify({'success': False, 'error': '找不到電影資料'}), 404

    movie_dict = movie.to_dict()
    movie_dict.update({
        'movie_id': str(gov_id),
        'original_name': raw_data.get('originalName', ''),
        'region': raw_data.get('region', ''),
        'release_date': raw_data.get('releaseDate') or movie_dict.get('release_date'),
        'publisher': raw_data.get('publisher'),
        'film_length_seconds': raw_data.get('filmLength'),
        'film_members': raw_data.get('filmMembers', []),
        'amount_in_this_week': raw_data.get('amountInThisWeek'),
        'total_amount': raw_data.get('totalAmount'),
    })

    return jsonify({'success': True, 'data': movie_dict})


@prediction_api_bp.route('/movie/<gov_id>/trend')
def movie_trend(gov_id):
    """
    API: 票房趨勢與未來預測
    """
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    history = movie_service.get_boxoffice_history(gov_id)
    if not history:
        return jsonify({'success': False, 'error': '找不到票房歷史資料'}), 404

    weeks_to_predict = getattr(prediction_service.config, 'PREDICTION_WEEKS', 3)
    predictions = prediction_service.predict_movie_boxoffice(gov_id, weeks=weeks_to_predict)

    history_payload = []
    for record in history:
        record_dict = record.to_dict()
        record_dict['decline_rate'] = getattr(record, 'decline_rate', None)
        history_payload.append(record_dict)

    predictions_chart = [pred.to_dict() for pred in predictions]
    predictions_with_warnings = []

    if len(history) >= 2:
        week_1_boxoffice = history[0].boxoffice
        week_2_boxoffice = history[1].boxoffice if len(history) > 1 else history[0].boxoffice
        opening_strength = prediction_service.calculate_opening_strength(
            week_1_boxoffice,
            week_2_boxoffice
        )

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

    chart_data = {
        'history': history_payload,
        'predictions': predictions_chart
    }

    warning_summary = prediction_service.check_decline_warning(gov_id)

    return jsonify({
        'success': True,
        'data': {
            'history': history_payload,
            'predictions': predictions_with_warnings,
            'chart': chart_data,
            'warning': warning_summary
        }
    })


@prediction_api_bp.route('/movie/<gov_id>/decline-analysis')
def movie_decline_analysis(gov_id):
    """
    API: 週衰退率分析
    """
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    history = movie_service.get_boxoffice_history(gov_id)
    if not history:
        return jsonify({'success': False, 'error': '找不到票房歷史資料'}), 404

    decline_data = movie_service.prepare_decline_chart_data(history)
    return jsonify({'success': True, 'data': decline_data})


@prediction_api_bp.route('/movie/<gov_id>/predict')
def predict(gov_id):
    """
    API: 預測電影票房

    Args:
        gov_id: 政府代號

    Query Parameters:
        weeks: 預測週數（預設3週）

    Returns:
        JSON 格式的預測結果
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    # 取得預測週數參數
    weeks = request.args.get('weeks', 3, type=int)
    weeks = min(max(weeks, 1), 12)  # 限制在1-12週之間

    # 進行預測
    predictions = prediction_service.predict_movie_boxoffice(gov_id, weeks)

    # 轉換為 JSON 格式
    result = {
        'gov_id': gov_id,
        'weeks': weeks,
        'predictions': [pred.to_dict() for pred in predictions]
    }

    return jsonify(result)


@prediction_api_bp.route('/movie/<gov_id>/latest')
def latest_data(gov_id):
    """
    API: 取得最新資料（用於即時更新）

    Args:
        gov_id: 政府代號

    Returns:
        JSON 格式的最新資料
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    # 取得最新資料
    current_data = movie_service.get_current_week_data(gov_id)

    return jsonify(current_data)


@prediction_api_bp.route('/export/<gov_id>')
def export(gov_id):
    """
    API: 匯出報表

    Args:
        gov_id: 政府代號

    Query Parameters:
        format: 檔案格式 (csv, excel)

    Returns:
        檔案下載
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    # 取得格式參數
    export_format = request.args.get('format', 'csv')

    # 驗證格式
    is_valid, error_msg = validate_export_format(export_format)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    try:
        # 產生報表
        file_content, filename = prediction_service.export_report(gov_id, export_format)

        # 設定 MIME 類型
        if export_format == 'excel':
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            mimetype = 'text/csv'

        # 返回檔案
        return send_file(
            io.BytesIO(file_content),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@prediction_api_bp.route('/warning/<gov_id>')
def warning(gov_id):
    """
    API: 取得預警資訊

    Args:
        gov_id: 政府代號

    Returns:
        JSON 格式的預警資訊
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    # 取得預警資訊
    warning_data = prediction_service.check_decline_warning(gov_id)

    return jsonify(warning_data)


@prediction_api_bp.route('/predict-new', methods=['POST'])
def predict_new():
    """
    API: 預測新電影票房

    Request Body:
        {
            "week_data": [
                {"week": 1, "boxoffice": 12000000, "audience": 40000, "screens": 150},
                {"week": 2, "boxoffice": 10200000, "audience": 34000, "screens": 140}
            ],
            "movie_info": {
                "name": "電影名稱",
                "release_date": "2025-01-01",
                "film_length": 120,
                "is_restricted": 0
            },
            "predict_weeks": 3
        }

    Returns:
        JSON 格式的預測結果
    """
    try:
        # 取得請求資料
        data = request.get_json()

        if not data:
            return jsonify({'error': '缺少請求資料'}), 400

        # 驗證必要欄位
        if 'week_data' not in data:
            return jsonify({'error': '缺少 week_data 欄位'}), 400

        if 'movie_info' not in data:
            return jsonify({'error': '缺少 movie_info 欄位'}), 400

        week_data = data['week_data']
        movie_info = data['movie_info']
        predict_weeks = data.get('predict_weeks', 3)

        # 驗證週次資料
        if not isinstance(week_data, list) or len(week_data) < 2:
            return jsonify({'error': '至少需要 2 週的歷史資料'}), 400

        # 驗證每週資料是否包含必要欄位
        for week in week_data:
            if not all(key in week for key in ['week', 'boxoffice']):
                return jsonify({'error': '每週資料必須包含 week 和 boxoffice'}), 400

        # 進行預測
        result = prediction_service.predict_new_movie(
            week_data=week_data,
            movie_info=movie_info,
            predict_weeks=predict_weeks
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '預測失敗，請稍後再試'
        }), 500


@prediction_api_bp.route('/predict-new/export', methods=['POST'])
def predict_new_export():
    """
    API: 匯出新電影預測報表

    Request Body:
        {
            "prediction_result": {...},  # predict_new_movie 的返回結果
            "format": "csv" or "excel"
        }

    Returns:
        檔案下載
    """
    try:
        # 取得請求資料
        data = request.get_json()

        if not data:
            return jsonify({'error': '缺少請求資料'}), 400

        # 驗證必要欄位
        if 'prediction_result' not in data:
            return jsonify({'error': '缺少 prediction_result 欄位'}), 400

        prediction_result = data['prediction_result']
        export_format = data.get('format', 'csv')

        # 驗證格式
        if export_format not in ['csv', 'excel']:
            return jsonify({'error': '格式必須是 csv 或 excel'}), 400

        # 產生報表
        file_content, filename = prediction_service.export_new_movie_report(
            prediction_result=prediction_result,
            format=export_format
        )

        # 設定 MIME 類型
        if export_format == 'excel':
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            mimetype = 'text/csv'

        # 返回檔案
        return send_file(
            io.BytesIO(file_content),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': '匯出失敗，請稍後再試'
        }), 500


@prediction_api_bp.route('/predict-new/download-preprocessed', methods=['POST'])
def download_preprocessed_data():
    """
    API: 下載預處理後的資料（用於驗證與訓練資料一致性）

    Request Body:
        {
            "week_data": [{week: 1, boxoffice: xxx, ...}, ...],
            "movie_info": {name: xxx, release_date: xxx, ...}
        }

    Returns:
        CSV 檔案下載
    """
    try:
        # 取得請求資料
        data = request.get_json()

        if not data:
            return jsonify({'error': '缺少請求資料'}), 400

        # 驗證必要欄位
        if 'week_data' not in data or 'movie_info' not in data:
            return jsonify({'error': '缺少 week_data 或 movie_info 欄位'}), 400

        week_data = data['week_data']
        movie_info = data['movie_info']

        # 驗證資料
        if not isinstance(week_data, list) or len(week_data) < 3:
            return jsonify({'error': '至少需要 3 週的資料（生成預處理資料需要從第 3 週開始）'}), 400

        # 產生預處理資料
        file_content, filename = prediction_service.export_preprocessed_data(
            week_data=week_data,
            movie_info=movie_info
        )

        # 返回檔案
        return send_file(
            io.BytesIO(file_content),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"下載預處理資料錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'下載失敗: {str(e)}'}), 500
