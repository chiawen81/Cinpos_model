"""
票房列表 API Blueprint
處理票房列表查詢的 API 端點
"""

from flask import Blueprint, jsonify, request
from ..services.boxoffice_list_service import BoxOfficeListService

# 建立 Blueprint
boxoffice_list_api_bp = Blueprint('boxoffice_list_api', __name__, url_prefix='/api/boxoffice')

# 初始化服務
boxoffice_list_service = BoxOfficeListService()


@boxoffice_list_api_bp.route('/list', methods=['GET'])
def get_boxoffice_list():
    """
    API: 取得電影票房列表

    Query Parameters:
        - page: 頁碼（從1開始，預設1）
        - page_size: 每頁筆數（預設10）
        - start_date: 起始上映日期 (YYYY-MM-DD)
        - end_date: 結束上映日期 (YYYY-MM-DD)
        - is_tracked: 是否在追蹤清單 (true/false)
        - warning_status: 預警狀態（正常/注意/嚴重）
        - release_status: 上映狀態（即將上映/上映中/已下檔）
        - is_first_run: 是否首輪 (true/false)
        - sort_by: 排序欄位（預設 release_date）
        - sort_order: 排序方向 (asc/desc，預設 desc)

    Returns:
        JSON 格式的列表資料，包含：
        - success: 是否成功
        - data: 電影列表資料
        - pagination: 分頁資訊
    """
    try:
        # 取得查詢參數
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        warning_status = request.args.get('warning_status')
        release_status = request.args.get('release_status')
        sort_by = request.args.get('sort_by', 'release_date')
        sort_order = request.args.get('sort_order', 'desc')

        # 處理布林值參數
        is_tracked = None
        if request.args.get('is_tracked'):
            is_tracked = request.args.get('is_tracked').lower() == 'true'

        is_first_run = None
        if request.args.get('is_first_run'):
            is_first_run = request.args.get('is_first_run').lower() == 'true'

        # 呼叫服務層
        result = boxoffice_list_service.get_boxoffice_list(
            page=page,
            page_size=page_size,
            start_date=start_date,
            end_date=end_date,
            is_tracked=is_tracked,
            warning_status=warning_status,
            release_status=release_status,
            is_first_run=is_first_run,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'取得票房列表失敗: {str(e)}'
        }), 500
