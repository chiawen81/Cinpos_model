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
ML_RECOMMEND_CUS_DATA_DIR = os.path.join(DATA_DIR, "ML_recommend")
ML_BOXOFFICE_CUS_DATA_DIR = os.path.join(DATA_DIR, "ML_boxoffice")

# -----------------------------
# 3. 各資料分類子資料夾
# -----------------------------
# ----------------- 共用 -----------------
# 票房資料（週次）
BOXOFFICE_RAW = os.path.join(RAW_DIR, "boxoffice_weekly")
BOXOFFICE_PROCESSED = os.path.join(PROCESSED_DIR, "boxoffice_weekly")

# 政府公開票房資料（單一電影）
BOXOFFICE_PERMOVIE_RAW = os.path.join(RAW_DIR, "boxoffice_permovie")
BOXOFFICE_PERMOVIE_PROCESSED = os.path.join(PROCESSED_DIR, "boxoffice_permovie")

# 政府公開電影資料（單一電影）
MOVIEINFO_GOV_PROCESSED = os.path.join(PROCESSED_DIR, "movieInfo_gov")
MOVIEINFO_GOV_COMBINED_PROCESSED = os.path.join(MOVIEINFO_GOV_PROCESSED, "combined")

# OMDb　電影資訊
OMDB_RAW = os.path.join(RAW_DIR, "omdb")
RATING_OMDB_PROCESSED = os.path.join(PROCESSED_DIR, "rating_omdb")

# ----------------- ML_recommend 專屬OUTPUT -----------------
MASTER_DIR = os.path.join(ML_BOXOFFICE_CUS_DATA_DIR, "master")

# 資料彙總- 資料庫主檔、模型訓練資料主檔
MASTER_FULL = os.path.join(MASTER_DIR, "full")  # 初步合併
MASTER_DB_READY = os.path.join(MASTER_DIR, "db_ready")  # API資料庫資料
MASTER_TRAIN_READY = os.path.join(MASTER_DIR, "train_ready")  # 訓練資料


# ----------------- ML_boxoffice 專屬OUTPUT-----------------




# -----------------------------
# 🧪 4. 測試執行 (僅限開發時)
# -----------------------------
if __name__ == "__main__":
    print("📂 RAW →", RAW_DIR)
    print("📂 PROCESSED →", PROCESSED_DIR)
    print("🎬 BOXOFFICE_RAW:", BOXOFFICE_RAW)
    print("🎬 BOXOFFICE_PERMOVIE_RAW:", BOXOFFICE_PERMOVIE_RAW)
    print("🏛️ GOV_PROCESSED:", MOVIEINFO_GOV_PROCESSED)
    print("🌐 OMDB_PROCESSED:", MOVIEINFO_OMDB_PROCESSED)
