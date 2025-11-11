#!/usr/bin/env python3
"""
票房資料批次處理腳本
====================

功能說明:
- 指定時間範圍和頻率，批次執行票房資料的爬取與清洗流程
- 按照固定順序執行 5 個步驟：
  1. 爬取單周電影票房
  2. 清洗單周票房資料
  3. 爬取單部電影累計票房
  4. 清洗單部電影票房資料
  5. 合併電影資訊

使用方式:
    # 基本用法：指定起始日期、結束日期、間隔天數
    uv run scripts/run_boxoffice_batch.py --start 2025-09-01 --end 2025-09-29 --interval 7

    # 使用 dry-run 模式預覽將執行的日期和命令
    uv run scripts/run_boxoffice_batch.py --start 2025-09-01 --end 2025-09-29 --interval 7 --dry-run

    # 發生錯誤時繼續執行（預設遇到錯誤會停止）
    uv run scripts/run_boxoffice_batch.py --start 2025-09-01 --end 2025-09-29 --interval 7 --continue-on-error

範例:
    撈取 2025-09-01 到 2025-09-29，每 7 天一次：
    uv run scripts/run_boxoffice_batch.py --start 2025-09-01 --end 2025-09-29 --interval 7

    執行日期為：2025-09-01, 2025-09-08, 2025-09-15, 2025-09-22, 2025-09-29
"""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta, date
from pathlib import Path


class BoxOfficeBatchRunner:
    """票房資料批次處理執行器"""

    def __init__(self, start_date, end_date, interval_days, dry_run=False, continue_on_error=False):
        """
        初始化批次執行器

        Parameters:
        -----------
        start_date : date
            起始日期
        end_date : date
            結束日期
        interval_days : int
            間隔天數
        dry_run : bool
            是否只顯示將執行的命令而不實際執行
        continue_on_error : bool
            是否在遇到錯誤時繼續執行
        """
        self.start_date = start_date
        self.end_date = end_date
        self.interval_days = interval_days
        self.dry_run = dry_run
        self.continue_on_error = continue_on_error

        # 統計資訊
        self.total_dates = 0
        self.success_dates = 0
        self.failed_dates = []

    def calculate_dates(self):
        """計算所有要執行的日期"""
        dates = []
        current = self.start_date

        while current <= self.end_date:
            dates.append(current)
            current += timedelta(days=self.interval_days)

        return dates

    def run_command(self, command, step_name):
        """
        執行命令

        Parameters:
        -----------
        command : list
            要執行的命令（列表形式）
        step_name : str
            步驟名稱（用於顯示）

        Returns:
        --------
        bool : 是否執行成功
        """
        cmd_str = " ".join(command)
        print(f"\n  命令: {cmd_str}")

        if self.dry_run:
            print("  [DRY-RUN] 略過實際執行")
            return True

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=False,  # 顯示即時輸出
                text=True
            )
            print(f"  ✅ {step_name} 執行成功")
            return True

        except subprocess.CalledProcessError as e:
            print(f"  ❌ {step_name} 執行失敗")
            print(f"  錯誤訊息: {e}")
            return False

    def run_single_date(self, target_date):
        """
        執行單一日期的完整流程

        Parameters:
        -----------
        target_date : date
            目標日期

        Returns:
        --------
        bool : 是否全部步驟都執行成功
        """
        date_str = target_date.strftime("%Y-%m-%d")

        print("\n" + "=" * 70)
        print(f"開始處理日期: {date_str}")
        print("=" * 70)

        # 定義 5 個步驟
        steps = [
            {
                "name": "Step 1: 爬取單周電影票房",
                "command": ["uv", "run", "src/fetch_common_data/crawler/boxoffice_weekly.py", "--date", date_str]
            },
            {
                "name": "Step 2: 清洗單周票房資料",
                "command": ["uv", "run", "src/fetch_common_data/data_cleaning/boxoffice_weekly.py"]
            },
            {
                "name": "Step 3: 爬取單部電影累計票房",
                "command": ["uv", "run", "src/fetch_common_data/crawler/boxoffice_permovie.py", "--date", date_str]
            },
            {
                "name": "Step 4: 清洗單部電影票房資料",
                "command": ["uv", "run", "src/fetch_common_data/data_cleaning/boxoffice_permovie.py", "--date", date_str]
            },
            {
                "name": "Step 5: 合併電影資訊",
                "command": ["uv", "run", "src/fetch_common_data/data_cleaning/movieInfo_gov_merge.py"]
            }
        ]

        # 逐步執行
        all_success = True
        for i, step in enumerate(steps, 1):
            print(f"\n{'-' * 70}")
            print(f"[{i}/5] {step['name']}")
            print(f"{'-' * 70}")

            success = self.run_command(step["command"], step["name"])

            if not success:
                all_success = False
                if not self.continue_on_error:
                    print(f"\n⚠️ 步驟執行失敗，停止處理日期 {date_str}")
                    return False
                else:
                    print(f"\n⚠️ 步驟執行失敗，但繼續執行下一步驟（--continue-on-error）")

        return all_success

    def run(self):
        """執行批次處理"""
        print("=" * 70)
        print("票房資料批次處理腳本")
        print("=" * 70)

        # 計算要執行的日期
        dates = self.calculate_dates()
        self.total_dates = len(dates)

        print(f"\n設定:")
        print(f"  起始日期: {self.start_date}")
        print(f"  結束日期: {self.end_date}")
        print(f"  間隔天數: {self.interval_days} 天")
        print(f"  總執行次數: {self.total_dates} 次")
        print(f"  Dry-run 模式: {'是' if self.dry_run else '否'}")
        print(f"  遇錯繼續: {'是' if self.continue_on_error else '否'}")

        print(f"\n將執行的日期:")
        for i, d in enumerate(dates, 1):
            print(f"  {i}. {d.strftime('%Y-%m-%d')}")

        if self.dry_run:
            print("\n[DRY-RUN] 以下為預覽模式，不會實際執行命令")

        # 開始執行
        print("\n" + "=" * 70)
        print("開始執行批次處理")
        print("=" * 70)

        for date_obj in dates:
            success = self.run_single_date(date_obj)

            if success:
                self.success_dates += 1
            else:
                self.failed_dates.append(date_obj.strftime("%Y-%m-%d"))

                if not self.continue_on_error:
                    print("\n" + "=" * 70)
                    print("批次處理中斷（遇到錯誤）")
                    print("=" * 70)
                    self.print_summary()
                    return False

        # 顯示執行結果摘要
        print("\n" + "=" * 70)
        print("批次處理完成")
        print("=" * 70)
        self.print_summary()

        return len(self.failed_dates) == 0

    def print_summary(self):
        """顯示執行結果摘要"""
        print(f"\n執行摘要:")
        print(f"  總執行次數: {self.total_dates}")
        print(f"  成功次數: {self.success_dates}")
        print(f"  失敗次數: {len(self.failed_dates)}")

        if self.failed_dates:
            print(f"\n失敗的日期:")
            for failed_date in self.failed_dates:
                print(f"  - {failed_date}")


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(
        description="票房資料批次處理腳本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 撈取 2025-09-01 到 2025-09-29，每 7 天一次
  uv run scripts/run_boxoffice_batch.py --start 2025-09-01 --end 2025-09-29 --interval 7

  # 預覽模式（不實際執行）
  uv run scripts/run_boxoffice_batch.py --start 2025-09-01 --end 2025-09-29 --interval 7 --dry-run

  # 遇到錯誤時繼續執行
  uv run scripts/run_boxoffice_batch.py --start 2025-09-01 --end 2025-09-29 --interval 7 --continue-on-error
        """
    )

    parser.add_argument(
        "--start",
        type=str,
        required=True,
        help="起始日期（格式：YYYY-MM-DD）"
    )

    parser.add_argument(
        "--end",
        type=str,
        required=True,
        help="結束日期（格式：YYYY-MM-DD）"
    )

    parser.add_argument(
        "--interval",
        type=int,
        required=True,
        help="間隔天數（例如：7 表示每 7 天執行一次）"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="預覽模式：只顯示將執行的命令，不實際執行"
    )

    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="遇到錯誤時繼續執行（預設遇到錯誤會停止）"
    )

    args = parser.parse_args()

    # 解析日期
    try:
        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end, "%Y-%m-%d").date()
    except ValueError as e:
        print(f"❌ 日期格式錯誤: {e}")
        print("請使用 YYYY-MM-DD 格式，例如：2025-09-01")
        sys.exit(1)

    # 驗證日期範圍
    if start_date > end_date:
        print("❌ 起始日期不能晚於結束日期")
        sys.exit(1)

    # 驗證間隔天數
    if args.interval <= 0:
        print("❌ 間隔天數必須大於 0")
        sys.exit(1)

    # 執行批次處理
    runner = BoxOfficeBatchRunner(
        start_date=start_date,
        end_date=end_date,
        interval_days=args.interval,
        dry_run=args.dry_run,
        continue_on_error=args.continue_on_error
    )

    success = runner.run()

    # 根據執行結果設定 exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
