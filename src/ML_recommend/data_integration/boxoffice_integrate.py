"""
票房資料聚合模組（支援多輪上映）
-------------------------------------------------
🎯 目標：
    將 data/processed/boxoffice_permovie 下的逐週票房資料，
    聚合成兩層結果：
        (1) 分輪聚合檔（每一輪上映一筆）
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
NOW_LABEL = datetime.now().strftime("%Y%m%d_%H%M")
# NOW_LABEL =datetime.now().strftime("%Y-%m-%d")
INPUT_DIR = BOXOFFICE_PERMOVIE_PROCESSED
OUTPUT_ROUND_DIR = os.path.join("data", "aggregated", "boxoffice", "rounds")
OUTPUT_COMBINED_DIR = os.path.join("data", "aggregated", "boxoffice", "combined")

ensure_dir(OUTPUT_ROUND_DIR)
ensure_dir(OUTPUT_COMBINED_DIR)


# -------------------------------------------------------
# 輔助函式
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


def detect_release_rounds(df: pd.DataFrame):
    """
    根據週票房資料偵測上映輪次（以「連續有票房」作為活躍期）
    規則：
      - 若連續三週以上票房 amount 為空或 total_amount 無變化，即視為下檔
      - 每次重新出現票房即視為新一輪上映
    """
    df = df.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")

    rounds = []
    current_round = []
    inactive_weeks = 0

    last_total = None
    for _, row in df.iterrows():
        amt, total = row["amount"], row["total_amount"]

        # 無票房 or 累積未變 → 靜止期
        if pd.isna(amt) or amt == 0 or (last_total is not None and total == last_total):
            inactive_weeks += 1
        else:
            inactive_weeks = 0

        # 若連續靜止超過3週 → 新一輪上映
        if inactive_weeks > 3 and current_round:
            rounds.append(current_round)
            current_round = []
            inactive_weeks = 0

        current_round.append(row)
        last_total = total

    if current_round:
        rounds.append(current_round)

    return [pd.DataFrame(r) for r in rounds]


def aggregate_single_round(
    df: pd.DataFrame, gov_id: str, title_zh: str, release_round: int, release_initial_date: str
):
    """將單一輪上映週資料聚合為一筆統計摘要"""
    df = df.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["tickets"] = pd.to_numeric(df["tickets"], errors="coerce").fillna(0)
    df["theater_count"] = pd.to_numeric(df["theater_count"], errors="coerce").fillna(0)
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce").fillna(0)

    total_weeks = len(df)
    first_week = df["week_range"].iloc[0]
    last_week = df["week_range"].iloc[-1]

    start, _ = parse_week_range(first_week)
    _, end = parse_week_range(last_week)
    release_days = (end - start).days + 1 if start and end else ""

    total_amount = df["amount"].sum()
    total_tickets = df["tickets"].sum()
    avg_amount_per_week = round(total_amount / total_weeks, 2)
    avg_tickets_per_week = round(total_tickets / total_weeks, 2)

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
    status = "下檔" if df["amount"].iloc[-1] == 0 else "上映中"

    return {
        "gov_id": gov_id,
        "title_zh": title_zh,
        "release_round": release_round,
        "release_start": start.strftime("%Y-%m-%d") if start else "",
        "release_end": end.strftime("%Y-%m-%d") if end else "",
        "release_days": release_days,
        "total_weeks": total_weeks,
        "total_amount": total_amount,
        "total_tickets": total_tickets,
        "avg_amount_per_week": avg_amount_per_week,
        "avg_tickets_per_week": avg_tickets_per_week,
        "peak_amount": peak_amount,
        "peak_amount_week": peak_amount_week,
        "peak_theater_count": peak_theater_count,
        "avg_theater_count": avg_theater_count,
        "amount_growth_rate": amount_growth_rate,
        "decline_rate_mean": decline_rate_mean,
        "decline_rate_last": decline_rate_last,
        "is_long_tail": is_long_tail,
        "status": status,
        "is_re_release": release_round > 1,
        "release_initial_date": release_initial_date,
        "update_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# -------------------------------------------------------
# 主整合流程
# -------------------------------------------------------
def integrate_boxoffice():
    print("🚀 開始進行票房聚合（多輪上映版本）...")
    # 取得單一電影票房資料夾下所有的"檔案名稱"
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

        # --- 計算最初上映日期 ---
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

        # 處理歷史統計資料
        if len(group) > 1:
            # 過去已有上映紀錄
            prev = group.iloc[:-1]
            latest["previous_round_count"] = len(prev)
            latest["previous_total_amount"] = prev["total_amount"].sum()
            prev_end = pd.to_datetime(prev["release_end"].iloc[-1])
            curr_start = pd.to_datetime(latest["release_start"])
            latest["re_release_gap_days"] = (curr_start - prev_end).days
            latest["previous_avg_amount"] = round(prev["avg_amount_per_week"].mean(), 2)
        else:
            # 第一次上映
            latest["previous_round_count"] = 0
            latest["previous_total_amount"] = 0
            latest["re_release_gap_days"] = 0
            latest["previous_avg_amount"] = 0

        latest_records.append(latest)

    df_latest = pd.DataFrame(latest_records)
    output_latest_path = os.path.join(OUTPUT_COMBINED_DIR, f"boxoffice_latest_{NOW_LABEL}.csv")
    df_latest.to_csv(output_latest_path, index=False, encoding="utf-8-sig")

    # ----------------------
    # 統計本次清洗結果
    # ----------------------
    print(f"✅ 最新輪整併完成，共 {len(df_latest)} 筆電影資料")
    print(f"📁 已輸出：{output_latest_path}")
    print("🎉 全部票房聚合流程完成！")


# -------------------------------------------------------
# 主程式執行區
# -------------------------------------------------------
if __name__ == "__main__":
    integrate_boxoffice()
