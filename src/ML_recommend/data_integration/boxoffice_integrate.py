"""
票房資料聚合模組（支援多輪上映 + 容忍小間斷）
-------------------------------------------------
🎯 目標：
    將 data/processed/boxoffice_permovie 下的逐週票房資料，
    聚合成兩層結果：
        (1) 分輪聚合檔（每一輪上映一筆）
          - 只保留「連續有票房」的活躍週期
          - 中間連續無票房（或金額不變）的週期視為「下檔」
          - 依每次活躍期產生 1 row（release_round）
        (2) 最新輪整併檔（每部電影僅保留最新一輪）

📂 資料流：
    input  : data/processed/boxoffice_permovie/*.csv
    output :
        - data/aggregated/boxoffice/rounds/boxoffice_rounds_<日期時間>.csv
        - data/aggregated/boxoffice/combined/boxoffice_latest_<日期時間>.csv
"""

# -------------------------------------------------------
# 套件匯入
# -------------------------------------------------------
import os
import pandas as pd
from datetime import datetime

# 共用模組
from common.path_utils import BOXOFFICE_PERMOVIE_PROCESSED
from common.file_utils import ensure_dir

# -------------------------------------------------------
# 全域設定
# -------------------------------------------------------
NOW_LABEL = datetime.now().strftime("%Y-%m-%d")
INPUT_DIR = BOXOFFICE_PERMOVIE_PROCESSED
OUTPUT_ROUND_DIR = os.path.join("data", "aggregated", "boxoffice", "rounds")
OUTPUT_COMBINED_DIR = os.path.join("data", "aggregated", "boxoffice", "combined")

ensure_dir(OUTPUT_ROUND_DIR)
ensure_dir(OUTPUT_COMBINED_DIR)

# 允許票房中斷的最大週數（可調參數）
MAX_GAP_WEEKS = 2  # 不超過 2 週無票房仍算同一輪


# -------------------------------------------------------
# 工具函式
# -------------------------------------------------------
def parse_week_range(week_range: str):
    """解析週期字串（例：'2025-03-10~2025-03-16'）→ (start_date, end_date)"""
    try:
        start_str, end_str = week_range.split("~")
        start = datetime.strptime(start_str, "%Y-%m-%d")
        end = datetime.strptime(end_str, "%Y-%m-%d")
        return start, end
    except Exception:
        return None, None


def get_latest_status(release_end: str, max_gap_weeks: int = 2) -> str:
    """
    根據最近一輪上映結束週期，判斷是否仍在上映中。
    規則：
        - 若距今天數 <= max_gap_weeks * 7 → 上映中
        - 否則 → 下檔
    """
    try:
        release_end_dt = datetime.strptime(release_end, "%Y-%m-%d")
        gap_days = (datetime.now() - release_end_dt).days
        return "上映中" if gap_days <= max_gap_weeks * 7 else "下檔"
    except Exception:
        return "下檔"


# -------------------------------------------------------
# 輪次偵測（容忍小間斷）
# -------------------------------------------------------
def detect_release_rounds(df: pd.DataFrame):
    """
    根據週票房資料偵測上映輪次（以「連續有票房」作為活躍期）
    規則：
      - 當周有票房 (amount > 0) → 則計入活躍週(active_weeks)的周次統計
      - 若連續超過 MAX_GAP_WEEKS 週無票房 → 視為正式下檔 (目前暫定為2周)
      - 之後再出現票房 → 新一輪上映
    """
    df = df.copy().sort_values("week_range")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    rounds = []
    current_round = []
    inactive_streak_weeks = 0

    for _, row in df.iterrows():
        amount = row["amount"]

        if amount > 0:
            inactive_streak_weeks = 0
            current_round.append(row)
        else:
            inactive_streak_weeks += 1
            # 若中斷超過容忍週數 → 視為結束一輪
            if inactive_streak_weeks > MAX_GAP_WEEKS and current_round:
                rounds.append(pd.DataFrame(current_round))
                current_round = []
                inactive_streak_weeks = 0

    if current_round:
        rounds.append(pd.DataFrame(current_round))

    return rounds


# -------------------------------------------------------
# 單輪聚合統計
# -------------------------------------------------------
def aggregate_single_round(
    df: pd.DataFrame, gov_id: str, title_zh: str, release_round: int, release_initial_date: str
):
    """將單一輪上映週資料聚合為一筆統計摘要"""
    df = df.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["tickets"] = pd.to_numeric(df["tickets"], errors="coerce").fillna(0)
    df["theater_count"] = pd.to_numeric(df["theater_count"], errors="coerce").fillna(0)
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce").fillna(0)

    # === 時間資訊 ===
    active_weeks = (df["amount"] > 0).sum()  # 實際有票房的週數
    first_week = df["week_range"].iloc[0]
    last_week = df["week_range"].iloc[-1]
    start, _ = parse_week_range(first_week)
    _, end = parse_week_range(last_week)
    release_days = (end - start).days + 1 if start and end else ""
    total_weeks = int(round(release_days / 7))

    # === 統計指標 ===
    total_amount = df["amount"].sum()
    total_tickets = df["tickets"].sum()
    avg_amount_per_week = round(total_amount / active_weeks, 2)
    avg_tickets_per_week = round(total_tickets / active_weeks, 2)

    # === 峰值指標 ===
    peak_idx = df["amount"].idxmax()
    peak_amount = df.loc[peak_idx, "amount"]
    peak_amount_week = df.loc[peak_idx, "week_range"]
    peak_theater_count = df["theater_count"].max()
    avg_theater_count = round(df["theater_count"].mean(), 2)

    # --- 首週→次週成長率 ---
    amount_growth_rate = ""
    if len(df) >= 2 and df["amount"].iloc[0] > 0:
        amount_growth_rate = round(
            (df["amount"].iloc[1] - df["amount"].iloc[0]) / df["amount"].iloc[0], 3
        )

    decline_rate_mean = round(df["rate"].mean(), 3) if len(df) > 1 else ""
    decline_rate_last = round(df["rate"].iloc[-1], 3) if len(df) > 1 else ""
    is_long_tail = total_weeks > 10

    return {
        # === 基本資料 ===
        "gov_id": gov_id,  # 政府電影代碼（唯一識別符）
        "title_zh": title_zh,  # 中文片名，用於識別與其他資料源對照
        "release_round": release_round,  # 上映輪次（第幾次上映，首輪=1、再映=2...）
        "is_re_release": release_round > 1,  # 是否為再上映（布林值）
        # === 時間資訊 ===
        "release_start": start.strftime("%Y-%m-%d"),  # 本輪上映起始日期（週期起始日）
        "release_end": end.strftime("%Y-%m-%d"),  # 本輪上映結束日期（週期結束日）
        "release_days": release_days,  # 本輪上映天數（首尾日相減 +1）
        "total_weeks": total_weeks,  # 本輪涵蓋的週數（含中斷週）
        "active_weeks": active_weeks,  # 實際有票房的週數（活躍週數）
        # === 統計指標 ===
        "total_amount": total_amount,  # 本輪票房總金額（累積 amount）
        "total_tickets": total_tickets,  # 本輪觀影總人次（累積 tickets）
        "avg_amount_per_week": avg_amount_per_week,  # 平均每週票房（total_amount ÷ active_weeks）
        "avg_tickets_per_week": avg_tickets_per_week,  # 平均每週觀影人次（total_tickets ÷ active_weeks）
        # === 峰值指標 ===
        "peak_amount": peak_amount,  # 單週最高票房金額
        "peak_amount_week": peak_amount_week,  # 票房最高週的週期（例：2025-03-24~2025-03-30）
        "peak_theater_count": peak_theater_count,  # 單週上映戲院數峰值
        "avg_theater_count": avg_theater_count,  # 平均上映戲院數（整輪週期平均）
        # === 動態變化 ===
        "amount_growth_rate": amount_growth_rate,  # 首週→次週票房成長率 ((week2-week1)/week1)
        "decline_rate_mean": decline_rate_mean,  # 平均下降率（所有週 rate 平均）
        "decline_rate_last": decline_rate_last,  # 最末週下降率（最後一週 rate）
        # === 標記 ===
        "is_long_tail": is_long_tail,  # 是否為長尾電影（上映週數 > 10）
        "status": "下檔",  # 上映狀態：預設下檔（稍後由最新輪更新為「上映中」）
        "release_initial_date": release_initial_date,  # 該電影首輪起始日期（跨輪參考指標）
        # === 系統欄位 ===
        "update_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 資料生成時間戳
    }
    """NOTE: 這裡都是每一活躍週期(round)的指標，跨週期的指標會在生成最新輪整併檔(latest)時加入"""


# -------------------------------------------------------
# 主整合流程
# -------------------------------------------------------
def integrate_boxoffice():
    print("🚀 開始進行票房聚合（多輪上映 + 容忍小間斷）...")
    # 取得所有單一電影票房的"檔案名稱"
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
    all_rounds = []

    # 遍歷 csv
    for file in files:
        file_path = os.path.join(INPUT_DIR, file)
        df = pd.read_csv(file_path)
        if df.empty:
            continue

        gov_id = str(df["gov_id"].iloc[0])
        title_zh = file.split("_", 1)[1].replace(".csv", "")  # 從檔名取得中文
        rounds = detect_release_rounds(df)  # 確認第幾次上映

        if not rounds:
            continue

        # 取最早上映日期（首輪首週）
        release_initial_date = ""
        if rounds and not rounds[0].empty:
            start, _ = parse_week_range(rounds[0]["week_range"].iloc[0])
            release_initial_date = start.strftime("%Y-%m-%d") if start else ""

        for idx, r_df in enumerate(rounds, start=1):
            agg = aggregate_single_round(r_df, gov_id, title_zh, idx, release_initial_date)
            all_rounds.append(agg)

    # ----------------------
    # 生成分輪聚合檔
    # ----------------------
    df_rounds = pd.DataFrame(all_rounds)

    # 確認有資料
    if df_rounds.empty:
        print("⚠️ 無有效電影資料可聚合，程式結束。")
        return

    output_round_path = os.path.join(OUTPUT_ROUND_DIR, f"boxoffice_rounds_{NOW_LABEL}.csv")
    df_rounds.to_csv(output_round_path, index=False, encoding="utf-8-sig")
    print(f"✅ 分輪聚合完成，共 {len(df_rounds)} 筆")
    print(f"📁 已輸出：{output_round_path}")

    # ----------------------
    # 生成最新輪整併檔
    # ----------------------
    latest_records = []
    for gov_id, group in df_rounds.groupby("gov_id"):
        group = group.sort_values("release_round")
        latest = group.iloc[-1].to_dict()

        # --- 處理歷史統計資料 ---
        if len(group) > 1:
            # 同一電影有多輪上映時
            prev = group.iloc[:-1]

            # === 歷史統計欄位 ===
            latest["previous_round_count"] = len(prev)  # 前輪次數量（例：第2輪上映則此欄為1）
            latest["previous_total_amount"] = prev[
                "total_amount"
            ].sum()  # 前輪累積票房（所有前輪 total_amount 加總）

            # 上一輪下檔與本輪開映之間的間隔天數
            prev_end = pd.to_datetime(prev["release_end"].iloc[-1])  # 上一輪結束日期
            curr_start = pd.to_datetime(latest["release_start"])  # 本輪開始日期
            latest["re_release_gap_days"] = (curr_start - prev_end).days  # 本輪與前一輪的間隔天數

            # 前一輪的平均票房表現（反映前期市場反應）
            latest["previous_avg_amount"] = round(prev["avg_amount_per_week"].mean(), 2)
        else:
            # 第一次上映
            latest["previous_round_count"] = 0
            latest["previous_total_amount"] = 0
            latest["re_release_gap_days"] = 0
            latest["previous_avg_amount"] = 0

        # --- 狀態判斷（僅針對最新輪）---
        latest["status"] = get_latest_status(
            latest.get("release_end", ""), max_gap_weeks=MAX_GAP_WEEKS
        )
        latest_records.append(latest)

    df_latest = pd.DataFrame(latest_records)
    output_latest_path = os.path.join(OUTPUT_COMBINED_DIR, f"boxoffice_latest_{NOW_LABEL}.csv")
    df_latest.to_csv(output_latest_path, index=False, encoding="utf-8-sig")

    # ----------------------
    # 統計結果
    # ----------------------
    print(f"✅ 最新輪整併完成，共 {len(df_latest)} 筆電影資料")
    print(f"📁 已輸出：{output_latest_path}")
    print("🎉 全部票房聚合流程完成！")


# -------------------------------------------------------
# 主程式執行區
# -------------------------------------------------------
if __name__ == "__main__":
    integrate_boxoffice()
