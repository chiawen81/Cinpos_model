"""
Flask 主應用程式
說明: 提供電影票房預測網站的主要路由和API端點
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime
import io

# 自訂模組
from config import Config
from services.movie_service import MovieService
from services.prediction_service import PredictionService
from utils.formatters import (
    format_currency,
    format_number,
    format_percentage,
    format_date,
    get_decline_color,
)
from utils.validators import validate_gov_id, validate_export_format

# 初始化 Flask 應用
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# 初始化服務
movie_service = MovieService()
prediction_service = PredictionService()


# ============= 自訂過濾器 =============
@app.template_filter("format_currency")
def format_currency_filter(value):
    """格式化貨幣的模板過濾器"""
    return format_currency(value)


@app.template_filter("format_number")
def format_number_filter(value):
    """格式化數字的模板過濾器"""
    return format_number(value)


@app.template_filter("format_percentage")
def format_percentage_filter(value):
    """格式化百分比的模板過濾器"""
    return format_percentage(value)


@app.template_filter("decline_color")
def decline_color_filter(value):
    """根據衰退率返回顏色的模板過濾器"""
    return get_decline_color(value)


# ============= 頁面路由 =============
@app.route("/")
def index():
    """首頁 - 總覽儀表板"""
    return render_template("index.html")


@app.route("/movies")
def movies_list():
    """電影列表頁面"""
    # 這裡應該從資料庫取得電影列表
    # 目前使用模擬資料
    movies = [
        {"gov_id": "MOV001", "title": "科技風暴", "release_date": "2025-10-01"},
        {"gov_id": "MOV002", "title": "愛在深秋", "release_date": "2025-09-15"},
    ]
    return render_template("movies_list.html", movies=movies)


@app.route("/movie/<gov_id>")
def movie_detail(gov_id):
    """
    單部電影詳細頁面

    Args:
        gov_id: 政府代號
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    # 取得電影資料
    movie = movie_service.get_movie_by_id(gov_id)
    if not movie:
        return render_template("404.html", message="電影不存在"), 404

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
        "history": [record.to_dict() for record in history],
        "predictions": [pred.to_dict() for pred in predictions],
    }

    # 準備衰退率圖表資料
    decline_data = prepare_decline_chart_data(history)

    return render_template(
        "movie_detail.html",
        movie=movie,
        history=history,
        predictions=predictions,
        statistics=statistics,
        warning=warning,
        chart_data=chart_data,
        decline_data=decline_data,
    )


@app.route("/predictions")
def predictions():
    """預測分析頁面"""
    return render_template("predictions.html")


@app.route("/predict-new")
def predict_new():
    """新電影預測頁面"""
    return render_template("predict_new.html")


@app.route("/reports")
def reports():
    """報表中心頁面"""
    return render_template("reports.html")


# ============= API 路由 =============
@app.route("/api/movie/<gov_id>")
def api_movie_detail(gov_id):
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
        return jsonify({"error": error_msg}), 400

    # 取得完整資料
    data = prediction_service.generate_combined_data(gov_id)

    return jsonify(data)


@app.route("/api/movie/<gov_id>/predict")
def api_predict(gov_id):
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
        return jsonify({"error": error_msg}), 400

    # 取得預測週數參數
    weeks = request.args.get("weeks", 3, type=int)
    weeks = min(max(weeks, 1), 12)  # 限制在1-12週之間

    # 進行預測
    predictions = prediction_service.predict_movie_boxoffice(gov_id, weeks)

    # 轉換為 JSON 格式
    result = {
        "gov_id": gov_id,
        "weeks": weeks,
        "predictions": [pred.to_dict() for pred in predictions],
    }

    return jsonify(result)


@app.route("/api/movie/<gov_id>/latest")
def api_latest_data(gov_id):
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
        return jsonify({"error": error_msg}), 400

    # 取得最新資料
    current_data = movie_service.get_current_week_data(gov_id)

    return jsonify(current_data)


@app.route("/api/export/<gov_id>")
def api_export(gov_id):
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
        return jsonify({"error": error_msg}), 400

    # 取得格式參數
    export_format = request.args.get("format", "csv")

    # 驗證格式
    is_valid, error_msg = validate_export_format(export_format)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    try:
        # 產生報表
        file_content, filename = prediction_service.export_report(gov_id, export_format)

        # 設定 MIME 類型
        if export_format == "excel":
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            mimetype = "text/csv"

        # 返回檔案
        return send_file(
            io.BytesIO(file_content), mimetype=mimetype, as_attachment=True, download_name=filename
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/warning/<gov_id>")
def api_warning(gov_id):
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
        return jsonify({"error": error_msg}), 400

    # 取得預警資訊
    warning = prediction_service.check_decline_warning(gov_id)

    return jsonify(warning)


@app.route("/api/search-movie", methods=["GET"])
def api_search_movie():
    """
    API: 搜尋電影（代理公開 API）

    Query Parameters:
        keyword: 搜尋關鍵字

    Returns:
        JSON 格式的搜尋結果
    """
    from curl_cffi import requests as curl_requests

    try:
        keyword = request.args.get("keyword", "").strip()

        if not keyword:
            return jsonify({"error": "請輸入搜尋關鍵字"}), 400

        # 使用 curl_cffi 完美模擬 Chrome 瀏覽器
        session = curl_requests.Session()

        # 先訪問首頁以取得 cookies
        session.get("https://boxofficetw.tfai.org.tw/", impersonate="chrome120", timeout=10)

        api_url = "https://boxofficetw.tfai.org.tw/film/sf"

        # 添加時間戳參數防止快取
        import time

        timestamp = int(time.time() * 1000)
        params = {"keyword": keyword, "_": timestamp}

        # 完整的瀏覽器 headers（參考實際瀏覽器請求）
        headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://boxofficetw.tfai.org.tw/search/32462",
            "Content-Type": "application/json",
            "sec-ch-ua": '"Chromium";v="120", "Google Chrome";v="120", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-kl-saas-ajax-request": "Ajax_Request",  # 關鍵 header
        }

        # Debug 日誌
        print("=" * 80)
        print("[DEBUG] 搜尋電影 API 請求資訊 (使用 curl_cffi):")
        print(f"[DEBUG] 請求 URL: {api_url}")
        print(f"[DEBUG] 請求參數: {params}")
        print(f"[DEBUG] Headers:")
        for key, value in headers.items():
            print(f"  {key}: {value}")
        print("=" * 80)

        # 使用 impersonate="chrome120" 模擬 Chrome 瀏覽器的 TLS 指紋
        response = session.get(
            api_url, params=params, headers=headers, timeout=15, impersonate="chrome120"
        )

        print(f"[DEBUG] 回應狀態碼: {response.status_code}")
        print(f"[DEBUG] 回應 Headers: {dict(response.headers)}")

        response.raise_for_status()

        # 解析回應
        data = response.json()
        print(f"[DEBUG] 回應成功，資料長度: {len(str(data))}")
        print("=" * 80)

        # 檢查回應格式（API 回應格式為 {data: {results: [...]}, success: true}）
        if data.get("success") and "data" in data and "results" in data["data"]:
            api_results = data["data"]["results"]
            results = []
            for item in api_results:
                results.append(
                    {
                        "movieId": item.get("movieId"),
                        "name": item.get("name"),
                        "originalName": item.get("originalName", ""),
                        "releaseDate": item.get("releaseDate"),
                        "duration": item.get("duration"),
                        "rating": item.get("rating", ""),
                        "film_length": item.get("duration", 120),
                        "is_restricted": 1 if item.get("rating") == "限制級" else 0,
                    }
                )
            return jsonify({"success": True, "results": results})
        else:
            return jsonify({"success": True, "results": []})

    except Exception as e:
        error_msg = str(e)

        # Debug 錯誤資訊
        print("=" * 80)
        print("[ERROR] 搜尋電影 API 發生錯誤:")
        print(f"[ERROR] 錯誤類型: {type(e).__name__}")
        print(f"[ERROR] 錯誤訊息: {error_msg}")

        # 如果是 HTTP 錯誤，顯示更多資訊
        if hasattr(e, "response") and e.response is not None:
            print(f"[ERROR] 回應狀態碼: {e.response.status_code}")
            print(f"[ERROR] 回應內容: {e.response.text[:500]}")  # 只顯示前 500 字元
            print(f"[ERROR] 回應 Headers: {dict(e.response.headers)}")

        import traceback

        print(f"[ERROR] 完整錯誤堆疊:")
        traceback.print_exc()
        print("=" * 80)

        if "timeout" in error_msg.lower():
            return jsonify({"success": False, "error": "API 請求逾時，請稍後再試"}), 504
        else:
            return jsonify({"success": False, "error": f"搜尋失敗: {error_msg}"}), 500


@app.route("/api/movie-detail/<movie_id>", methods=["GET"])
def api_movie_detail_by_id(movie_id):
    """
    API: 取得電影詳細資料（代理公開 API）

    Args:
        movie_id: 電影 ID

    Returns:
        JSON 格式的電影詳細資料
    """
    from curl_cffi import requests as curl_requests

    try:
        if not movie_id:
            return jsonify({"error": "電影 ID 不可為空"}), 400

        # 使用 curl_cffi 完美模擬 Chrome 瀏覽器
        session = curl_requests.Session()

        # 先訪問首頁以取得 cookies
        session.get("https://boxofficetw.tfai.org.tw/", impersonate="chrome120", timeout=10)

        api_url = f"https://boxofficetw.tfai.org.tw/film/gfd/{movie_id}"

        # 添加時間戳參數防止快取
        import time

        timestamp = int(time.time() * 1000)
        params = {"_": timestamp}

        # 完整的瀏覽器 headers（參考實際瀏覽器請求）
        headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://boxofficetw.tfai.org.tw/search/32462",
            "Content-Type": "application/json",
            "sec-ch-ua": '"Chromium";v="120", "Google Chrome";v="120", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-kl-saas-ajax-request": "Ajax_Request",  # 關鍵 header
        }

        # Debug 日誌
        print("=" * 80)
        print("[DEBUG] 取得電影詳細資料 API 請求資訊 (使用 curl_cffi):")
        print(f"[DEBUG] 請求 URL: {api_url}")
        print(f"[DEBUG] 請求參數: {params}")
        print(f"[DEBUG] Headers:")
        for key, value in headers.items():
            print(f"  {key}: {value}")
        print("=" * 80)

        # 使用 impersonate="chrome120" 模擬 Chrome 瀏覽器的 TLS 指紋
        response = session.get(
            api_url, params=params, headers=headers, timeout=15, impersonate="chrome120"
        )

        print(f"[DEBUG] 回應狀態碼: {response.status_code}")
        print(f"[DEBUG] 回應 Headers: {dict(response.headers)}")

        response.raise_for_status()

        # 解析回應
        data = response.json()
        print(f"[DEBUG] 回應成功，資料長度: {len(str(data))}")
        print("=" * 80)

        # 檢查回應格式
        if data.get("success") and "data" in data:
            movie_data = data["data"]

            # 整理回傳資料
            result = {
                "movieId": movie_data.get("movieId"),
                "name": movie_data.get("name"),
                "originalName": movie_data.get("originalName", ""),
                "releaseDate": movie_data.get("releaseDate"),
                "rating": movie_data.get("rating", ""),
                "filmLength": movie_data.get("filmLength", 0),  # 單位：秒
                "weeks": movie_data.get("weeks", []),
            }

            return jsonify({"success": True, "data": result})
        else:
            return jsonify({"success": False, "error": "無法取得電影資料"}), 404

    except Exception as e:
        error_msg = str(e)

        # Debug 錯誤資訊
        print("=" * 80)
        print("[ERROR] 取得電影詳細資料 API 發生錯誤:")
        print(f"[ERROR] 錯誤類型: {type(e).__name__}")
        print(f"[ERROR] 錯誤訊息: {error_msg}")

        # 如果是 HTTP 錯誤，顯示更多資訊
        if hasattr(e, "response") and e.response is not None:
            print(f"[ERROR] 回應狀態碼: {e.response.status_code}")
            print(f"[ERROR] 回應內容: {e.response.text[:500]}")  # 只顯示前 500 字元
            print(f"[ERROR] 回應 Headers: {dict(e.response.headers)}")

        import traceback

        print(f"[ERROR] 完整錯誤堆疊:")
        traceback.print_exc()
        print("=" * 80)

        if "timeout" in error_msg.lower():
            return jsonify({"success": False, "error": "API 請求逾時，請稍後再試"}), 504
        else:
            return jsonify({"success": False, "error": f"取得電影資料失敗: {error_msg}"}), 500


@app.route("/api/predict-new", methods=["POST"])
def api_predict_new():
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
            return jsonify({"error": "缺少請求資料"}), 400

        # 驗證必要欄位
        if "week_data" not in data:
            return jsonify({"error": "缺少 week_data 欄位"}), 400

        if "movie_info" not in data:
            return jsonify({"error": "缺少 movie_info 欄位"}), 400

        week_data = data["week_data"]
        movie_info = data["movie_info"]
        predict_weeks = data.get("predict_weeks", 3)

        # 驗證週次資料
        if not isinstance(week_data, list) or len(week_data) < 2:
            return jsonify({"error": "至少需要 2 週的歷史資料"}), 400

        # 驗證每週資料是否包含必要欄位
        for week in week_data:
            if not all(key in week for key in ["week", "boxoffice"]):
                return jsonify({"error": "每週資料必須包含 week 和 boxoffice"}), 400

        # 進行預測
        result = prediction_service.predict_new_movie(
            week_data=week_data, movie_info=movie_info, predict_weeks=predict_weeks
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e), "message": "預測失敗，請稍後再試"}), 500


@app.route("/api/predict-new/export", methods=["POST"])
def api_predict_new_export():
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
            return jsonify({"error": "缺少請求資料"}), 400

        # 驗證必要欄位
        if "prediction_result" not in data:
            return jsonify({"error": "缺少 prediction_result 欄位"}), 400

        prediction_result = data["prediction_result"]
        export_format = data.get("format", "csv")

        # 驗證格式
        if export_format not in ["csv", "excel"]:
            return jsonify({"error": "格式必須是 csv 或 excel"}), 400

        # 產生報表
        file_content, filename = prediction_service.export_new_movie_report(
            prediction_result=prediction_result, format=export_format
        )

        # 設定 MIME 類型
        if export_format == "excel":
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            mimetype = "text/csv"

        # 返回檔案
        return send_file(
            io.BytesIO(file_content), mimetype=mimetype, as_attachment=True, download_name=filename
        )

    except Exception as e:
        return jsonify({"error": str(e), "message": "匯出失敗，請稍後再試"}), 500


@app.route("/api/predict-new/download-preprocessed", methods=["POST"])
def api_download_preprocessed_data():
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
            return jsonify({"error": "缺少請求資料"}), 400

        # 驗證必要欄位
        if "week_data" not in data or "movie_info" not in data:
            return jsonify({"error": "缺少 week_data 或 movie_info 欄位"}), 400

        week_data = data["week_data"]
        movie_info = data["movie_info"]

        # 驗證資料
        if not isinstance(week_data, list) or len(week_data) < 3:
            return jsonify({"error": "至少需要 3 週的資料（生成預處理資料需要從第 3 週開始）"}), 400

        # 產生預處理資料
        file_content, filename = prediction_service.export_preprocessed_data(
            week_data=week_data, movie_info=movie_info
        )

        # 返回檔案
        return send_file(
            io.BytesIO(file_content),
            mimetype="text/csv",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        print(f"下載預處理資料錯誤: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"下載失敗: {str(e)}"}), 500


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
        if history[i - 1].boxoffice > 0:
            rate = (history[i].boxoffice - history[i - 1].boxoffice) / history[i - 1].boxoffice
            weeks.append(history[i].week)
            decline_rates.append(rate)

    avg_decline_rate = sum(decline_rates) / len(decline_rates) if decline_rates else 0

    return {"weeks": weeks, "decline_rates": decline_rates, "avg_decline_rate": avg_decline_rate}


# ============= 錯誤處理 =============
@app.errorhandler(404)
def page_not_found(e):
    """404 錯誤處理"""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    """500 錯誤處理"""
    return render_template("500.html"), 500


# ============= 主程式入口 =============
if __name__ == "__main__":
    # 確保必要目錄存在
    Path("data").mkdir(exist_ok=True)
    Path("saved_models").mkdir(exist_ok=True)
    Path("exports").mkdir(exist_ok=True)

    # 啟動應用
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
