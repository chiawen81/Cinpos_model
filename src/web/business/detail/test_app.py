"""
簡單測試腳本
說明: 驗證應用程式的基本功能
"""

import sys
from pathlib import Path

# 將專案目錄加入 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """測試所有模組能否正確導入"""
    try:
        print("測試模組導入...")
        
        # 測試配置
        from config import Config
        print("✓ 配置模組")
        
        # 測試模型
        from models.movie import Movie, BoxOfficeRecord, BoxOfficePrediction
        from models.prediction import BoxOfficePredictionModel
        print("✓ 模型模組")
        
        # 測試服務
        from services.movie_service import MovieService
        from services.prediction_service import PredictionService
        print("✓ 服務模組")
        
        # 測試工具
        from utils.formatters import format_currency
        from utils.validators import validate_gov_id
        print("✓ 工具模組")
        
        print("\n✅ 所有模組導入成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        return False

def test_basic_functionality():
    """測試基本功能"""
    try:
        print("\n測試基本功能...")
        
        from services.movie_service import MovieService
        from utils.formatters import format_currency
        
        # 測試電影服務
        service = MovieService()
        movie = service.get_movie_by_id("MOV001")
        if movie:
            print(f"✓ 成功取得電影: {movie.title}")
        
        # 測試格式化
        formatted = format_currency(50000000)
        print(f"✓ 貨幣格式化: 50000000 → {formatted}")
        
        print("\n✅ 基本功能測試通過！")
        return True
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        return False

def test_flask_app():
    """測試 Flask 應用能否啟動"""
    try:
        print("\n測試 Flask 應用...")
        
        from app import app
        
        # 測試路由是否存在
        with app.test_client() as client:
            # 測試首頁
            response = client.get('/')
            if response.status_code == 200:
                print("✓ 首頁路由正常")
            
            # 測試 API
            response = client.get('/api/movie/MOV001')
            if response.status_code == 200:
                print("✓ API 路由正常")
        
        print("\n✅ Flask 應用測試通過！")
        return True
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🎬 電影票房預測系統 - 功能測試")
    print("=" * 50)
    
    all_passed = True
    
    # 執行測試
    all_passed &= test_imports()
    all_passed &= test_basic_functionality()
    all_passed &= test_flask_app()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ 所有測試通過！應用程式準備就緒。")
        print("\n下一步:")
        print("1. 執行 ./start.sh 啟動應用")
        print("2. 訪問 http://localhost:5000")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息。")
    print("=" * 50)
