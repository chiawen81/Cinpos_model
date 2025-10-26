"""
統一管理專案中的資料夾與檔案路徑。
----------------------------------
✅ 功能與設計原則：
1. 無論從哪個位置執行（VSCode、Jupyter、終端機），皆可自動定位專案根目錄。
2. 所有子資料夾路徑集中管理，方便共用、重構或搬移專案時維護。
3. 搭配 file_utils.ensure_dir() 可自動建立不存在的資料夾。
"""

import os


# -----------------------------
# 1. 專案根目錄定位
# -----------------------------
def find_project_root(marker_files=("pyproject.toml", ".git")) -> str:
    """
    目標：找到根目錄
    方法：當前位置往上尋找，找到 pyproject.toml 或 .git，就以該層當作專案根目錄
    """
    path = os.path.abspath(os.path.dirname(__file__))
    while path != os.path.dirname(path):  # 防止無限迴圈
        if any(os.path.exists(os.path.join(path, m)) for m in marker_files):
            return path
        path = os.path.dirname(path)
    raise FileNotFoundError("❌ 無法找到專案根目錄（請確認有 pyproject.toml 或 .git）")


# -----------------------------
# 2. 主資料夾路徑
# -----------------------------
PROJECT_ROOT = find_project_root()
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
MANUAL_FIX_DIR = os.path.join(DATA_DIR, "manual_fix")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# -----------------------------
# 3. 各資料分類子資料夾
# -----------------------------
# 票房資料
BOXOFFICE_RAW = os.path.join(RAW_DIR, "boxoffice_weekly")
BOXOFFICE_PROCESSED = os.path.join(PROCESSED_DIR, "boxoffice_weekly")

# 單一電影票房資料
BOXOFFICE_PERMOVIE_RAW = os.path.join(RAW_DIR, "boxoffice_permovie")
BOXOFFICE_PERMOVIE_PROCESSED = os.path.join(PROCESSED_DIR, "boxoffice_permovie")
MOVIEINFO_GOV_PROCESSED = os.path.join(PROCESSED_DIR, "movieInfo_gov")
MOVIEINFO_GOV_COMBINED_PROCESSED = os.path.join(MOVIEINFO_GOV_PROCESSED, "combined")  # 彙總單一電影

# 開眼電影網 - 首輪電影名單
FIRSTRUN_RAW = os.path.join(RAW_DIR, "firstRunFilm_list")
FIRSTRUN_PROCESSED = os.path.join(PROCESSED_DIR, "firstRunFilm_list")

# OMDb電影資訊
OMDB_RAW = os.path.join(RAW_DIR, "movieInfo_omdb")
OMDB_PROCESSED = os.path.join(PROCESSED_DIR, "movieInfo_omdb")

# <準備棄用>
MOVIEINFO_OMDB_RAW = os.path.join(RAW_DIR, "movieInfo_omdb")
MOVIEINFO_OMDB_PROCESSED = os.path.join(PROCESSED_DIR, "movieInfo_omdb")


# 評分相關資料
RATING_WEEKLY_RAW = os.path.join(RAW_DIR, "rating_weekly")
RATING_WEEKLY_PROCESSED = os.path.join(PROCESSED_DIR, "rating_weekly")

# 資料彙總- 資料庫主檔、模型訓練資料主檔
MOVIE_MASTER_PROCESSED = os.path.join(PROCESSED_DIR, "movie_master")
MOVIE_MASTER_MERGE = os.path.join(MOVIE_MASTER_PROCESSED, "merge")  # 初步合併
MOVIE_MASTER_DATABASE_READY = os.path.join(
    MOVIE_MASTER_PROCESSED, "database_ready"
)  # API資料庫資料
MOVIE_MASTER_TRAIN_READY = os.path.join(MOVIE_MASTER_PROCESSED, "train_ready")  # 訓練資料
MOVIE_MASTER_PROCESSED_ALL_FILE = os.path.join(
    MOVIE_MASTER_TRAIN_READY, "movie_master_train_full.csv"
)  # 訓練資料歷史檔案


# -----------------------------
# 🧪 4. 測試執行 (僅限開發時)
# -----------------------------
if __name__ == "__main__":
    print("專案根目錄：", PROJECT_ROOT)
    print("原始資料資料夾：", RAW_DIR)
    print("處理後資料資料夾：", PROCESSED_DIR)
