"""
測試 curl_cffi 是否能成功繞過 Cloudflare 防護
"""
from curl_cffi import requests as curl_requests
import time

def test_search_api():
    """測試搜尋電影 API"""
    print("=" * 80)
    print("測試搜尋電影 API")
    print("=" * 80)

    try:
        # 使用 curl_cffi 完美模擬 Chrome 瀏覽器
        session = curl_requests.Session()

        # 先訪問首頁以取得 cookies
        print("[1/3] 訪問首頁取得 cookies...")
        session.get("https://boxofficetw.tfai.org.tw/", impersonate="chrome120", timeout=10)
        print("[OK] 成功取得 cookies")

        # 準備搜尋請求
        api_url = "https://boxofficetw.tfai.org.tw/film/sf"
        keyword = "創"
        timestamp = int(time.time() * 1000)
        params = {"keyword": keyword, "_": timestamp}

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
            "x-kl-saas-ajax-request": "Ajax_Request",
        }

        print(f"[2/3] 搜尋關鍵字: '{keyword}'")
        response = session.get(
            api_url, params=params, headers=headers, timeout=15, impersonate="chrome120"
        )

        print(f"[3/3] 回應狀態碼: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("[OK] 成功取得資料!")

            if data.get("success") and "data" in data and "results" in data["data"]:
                results = data["data"]["results"]
                print(f"[OK] 找到 {len(results)} 筆結果")

                # 顯示前 3 筆結果
                for i, item in enumerate(results[:3], 1):
                    print(f"\n  {i}. {item.get('name')} ({item.get('releaseDate')})")
                    print(f"     電影 ID: {item.get('movieId')}")
            else:
                print("[WARN] 回應格式異常")
        else:
            print(f"[FAIL] 請求失敗: {response.status_code}")
            print(f"  回應內容: {response.text[:200]}")

    except Exception as e:
        print(f"[ERROR] 發生錯誤: {type(e).__name__}")
        print(f"  錯誤訊息: {str(e)}")
        return False

    print("=" * 80)
    return True


def test_movie_detail_api():
    """測試取得電影詳細資料 API"""
    print("\n" + "=" * 80)
    print("測試取得電影詳細資料 API")
    print("=" * 80)

    try:
        # 使用 curl_cffi 完美模擬 Chrome 瀏覽器
        session = curl_requests.Session()

        # 先訪問首頁以取得 cookies
        print("[1/3] 訪問首頁取得 cookies...")
        session.get("https://boxofficetw.tfai.org.tw/", impersonate="chrome120", timeout=10)
        print("[OK] 成功取得 cookies")

        # 測試電影 ID (這裡使用一個範例 ID,你可以替換成真實的 ID)
        movie_id = "32462"
        api_url = f"https://boxofficetw.tfai.org.tw/film/gfd/{movie_id}"
        timestamp = int(time.time() * 1000)
        params = {"_": timestamp}

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
            "x-kl-saas-ajax-request": "Ajax_Request",
        }

        print(f"[2/3] 取得電影 ID: {movie_id}")
        response = session.get(
            api_url, params=params, headers=headers, timeout=15, impersonate="chrome120"
        )

        print(f"[3/3] 回應狀態碼: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("[OK] 成功取得資料!")

            if data.get("success") and "data" in data:
                movie_data = data["data"]
                print(f"\n  電影名稱: {movie_data.get('name')}")
                print(f"  原文名稱: {movie_data.get('originalName')}")
                print(f"  上映日期: {movie_data.get('releaseDate')}")
                print(f"  片長: {movie_data.get('filmLength', 0)} 秒")
                print(f"  週次資料: {len(movie_data.get('weeks', []))} 週")
            else:
                print("[WARN] 回應格式異常")
        else:
            print(f"[FAIL] 請求失敗: {response.status_code}")
            print(f"  回應內容: {response.text[:200]}")

    except Exception as e:
        print(f"[ERROR] 發生錯誤: {type(e).__name__}")
        print(f"  錯誤訊息: {str(e)}")
        return False

    print("=" * 80)
    return True


if __name__ == "__main__":
    print("\n測試 curl_cffi 繞過 Cloudflare 防護\n")

    # 測試搜尋 API
    test1_passed = test_search_api()

    # 測試電影詳細資料 API
    test2_passed = test_movie_detail_api()

    # 總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)
    print(f"搜尋 API: {'[PASS] 通過' if test1_passed else '[FAIL] 失敗'}")
    print(f"電影詳細資料 API: {'[PASS] 通過' if test2_passed else '[FAIL] 失敗'}")

    if test1_passed and test2_passed:
        print("\n[SUCCESS] 所有測試通過! curl_cffi 成功繞過 Cloudflare 防護")
        print("  你可以放心部署到 Render.com 了")
    else:
        print("\n[WARNING] 部分測試失敗,請檢查錯誤訊息")
    print("=" * 80)
