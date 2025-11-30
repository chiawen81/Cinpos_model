###################################################
#  表頭相關設定(requests/headers/session/timeout)
###################################################


# -------------------------------
# 基本 Header 模板
# -------------------------------
def get_default_headers() -> dict:
    """模擬一般瀏覽器瀏覽行為"""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.google.com/",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
