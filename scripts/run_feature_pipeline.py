#!/usr/bin/env python3
"""
特徵工程自動化 Pipeline
====================

功能說明:
此腳本會依序執行以下步驟，並產生4個檔案：

  (1) 底稿：執行 flatten_timeseries.py
      └─ 輸出：data/ML_boxoffice/phase1_flattened/boxoffice_timeseries_<日期>.csv
      └─ 報告：data/ML_boxoffice/phase1_flattened/data_quality_report_<日期>.txt

  (2) 只要累計特徵：以(1)執行 add_cumsum_features.py
      └─ 輸出：data/ML_boxoffice/phase2_features/with_cumsum/features_cumsum_<日期>.csv

  (3) 只要市場特徵：以(1)執行 add_market_features.py
      └─ 輸出：data/ML_boxoffice/phase2_features/with_market/features_market_<日期>.csv

  (4) 全要：以(2)執行 add_market_features.py
      └─ 輸出：data/ML_boxoffice/phase2_features/full/features_full_<日期>.csv

使用方式:
    uv run scripts/run_feature_pipeline.py
    uv run scripts/run_feature_pipeline.py --dry-run  # 只顯示將執行的命令
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


class FeaturePipelineRunner:
    """特徵工程 Pipeline 執行器"""

    def __init__(self, dry_run=False):
        """
        初始化執行器

        Parameters:
        -----------
        dry_run : bool
            是否只顯示命令而不實際執行
        """
        self.dry_run = dry_run
        self.timestamp = datetime.now().strftime('%Y-%m-%d-%H%M')

        # 檔案路徑
        self.file1_flattened = None  # 將在執行後設定
        self.file2_cumsum = None
        self.file3_market = None
        self.file4_full = None

    def _execute_command(self, cmd, step_name):
        """執行命令"""
        print(f"\n{'='*70}")
        print(f"執行命令：{step_name}")
        print(f"{'='*70}")
        print(f"命令: {' '.join(cmd)}")

        if self.dry_run:
            print("\n[DRY-RUN] 僅顯示命令，不實際執行")
            return True

        print("\n執行中...")
        print("-" * 70)

        try:
            result = subprocess.run(cmd, check=True, capture_output=False, text=True)
            print("-" * 70)
            print(f"[OK] {step_name} 執行成功")
            return True
        except subprocess.CalledProcessError as e:
            print("-" * 70)
            print(f"[ERROR] {step_name} 執行失敗: {e}")
            return False

    def find_latest_file(self, directory, pattern):
        """找到最新生成的檔案"""
        dir_path = Path(directory)
        if not dir_path.exists():
            return None

        files = list(dir_path.glob(pattern))
        if not files:
            return None

        # 按修改時間排序，取最新的
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        return str(latest_file)

    def step1_flatten_timeseries(self):
        """步驟1：執行 flatten_timeseries.py 生成底稿 + 報告"""
        print("\n" + "="*70)
        print("步驟 1/4：生成票房時序底稿 + 資料品質報告")
        print("="*70)

        cmd = [
            "uv", "run",
            "src/ML_boxoffice/phase1_flatten/flatten_timeseries.py"
        ]

        success = self._execute_command(cmd, "生成時序底稿")

        if success and not self.dry_run:
            # 找到剛生成的檔案
            self.file1_flattened = self.find_latest_file(
                "data/ML_boxoffice/phase1_flattened",
                "boxoffice_timeseries_*.csv"
            )
            if self.file1_flattened:
                print(f"\n✓ 底稿檔案：{self.file1_flattened}")

                # 檢查報告是否生成
                report_file = self.file1_flattened.replace('.csv', '_report.txt')
                if Path(report_file).exists():
                    print(f"✓ 報告檔案：{report_file}")
            else:
                print("\n⚠ 警告：找不到生成的檔案")
                return False

        return success

    def step2_add_cumsum_features(self):
        """步驟2：以底稿(1)生成累計特徵檔案(2)"""
        print("\n" + "="*70)
        print("步驟 2/4：生成累計特徵檔案（只包含累計特徵）")
        print("="*70)

        if not self.dry_run and not self.file1_flattened:
            print("[ERROR] 找不到步驟1的輸出檔案")
            return False

        output_dir = Path("data/ML_boxoffice/phase2_features/with_cumsum")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"features_cumsum_{self.timestamp}.csv"

        cmd = [
            "uv", "run",
            "src/ML_boxoffice/phase2_features/add_cumsum_features.py"
        ]

        if not self.dry_run:
            cmd.extend([self.file1_flattened, str(output_file)])
        else:
            cmd.extend(["<步驟1輸出>", str(output_file)])

        success = self._execute_command(cmd, "生成累計特徵")

        if success and not self.dry_run:
            self.file2_cumsum = str(output_file)
            print(f"\n✓ 累計特徵檔案：{self.file2_cumsum}")

        return success

    def step3_add_market_features_only(self):
        """步驟3：以底稿(1)生成市場特徵檔案(3)"""
        print("\n" + "="*70)
        print("步驟 3/4：生成市場特徵檔案（只包含市場特徵）")
        print("="*70)

        if not self.dry_run and not self.file1_flattened:
            print("[ERROR] 找不到步驟1的輸出檔案")
            return False

        output_dir = Path("data/ML_boxoffice/phase2_features/with_market")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"features_market_{self.timestamp}.csv"

        cmd = [
            "uv", "run",
            "src/ML_boxoffice/phase2_features/add_market_features.py"
        ]

        if not self.dry_run:
            cmd.extend(["--input", self.file1_flattened])
        else:
            cmd.extend(["--input", "<步驟1輸出>"])

        cmd.extend(["--output", str(output_file)])

        success = self._execute_command(cmd, "生成市場特徵")

        if success and not self.dry_run:
            self.file3_market = str(output_file)
            print(f"\n✓ 市場特徵檔案：{self.file3_market}")

        return success

    def step4_add_market_to_cumsum(self):
        """步驟4：以累計特徵檔案(2)生成完整特徵檔案(4)"""
        print("\n" + "="*70)
        print("步驟 4/4：生成完整特徵檔案（累計 + 市場）")
        print("="*70)

        if not self.dry_run and not self.file2_cumsum:
            print("[ERROR] 找不到步驟2的輸出檔案")
            return False

        output_dir = Path("data/ML_boxoffice/phase2_features/full")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"features_full_{self.timestamp}.csv"

        cmd = [
            "uv", "run",
            "src/ML_boxoffice/phase2_features/add_market_features.py"
        ]

        if not self.dry_run:
            cmd.extend(["--input", self.file2_cumsum])
        else:
            cmd.extend(["--input", "<步驟2輸出>"])

        cmd.extend(["--output", str(output_file)])

        success = self._execute_command(cmd, "生成完整特徵")

        if success and not self.dry_run:
            self.file4_full = str(output_file)
            print(f"\n✓ 完整特徵檔案：{self.file4_full}")

        return success

    def run(self):
        """執行完整 pipeline"""
        print("\n" + "="*70)
        print("特徵工程自動化 Pipeline")
        print("="*70)
        print(f"執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if self.dry_run:
            print("\n[模式] DRY-RUN：只顯示將執行的命令，不會實際執行")

        print("\n將依序執行以下步驟：")
        print("  1. 生成時序底稿 + 資料品質報告")
        print("  2. 生成累計特徵檔案")
        print("  3. 生成市場特徵檔案")
        print("  4. 生成完整特徵檔案（累計+市場）")

        # 執行各個步驟
        steps = [
            ("步驟1", self.step1_flatten_timeseries),
            ("步驟2", self.step2_add_cumsum_features),
            ("步驟3", self.step3_add_market_features_only),
            ("步驟4", self.step4_add_market_to_cumsum),
        ]

        for step_name, step_func in steps:
            success = step_func()
            if not success and not self.dry_run:
                print(f"\n[ERROR] {step_name} 執行失敗，停止 pipeline")
                sys.exit(1)

        # 完成總結
        print("\n" + "="*70)
        print("Pipeline 執行完成！")
        print("="*70)
        print(f"完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if not self.dry_run:
            print("\n生成的檔案：")
            print(f"  (1) 底稿：{self.file1_flattened}")
            print(f"  (2) 累計特徵：{self.file2_cumsum}")
            print(f"  (3) 市場特徵：{self.file3_market}")
            print(f"  (4) 完整特徵：{self.file4_full}")


def main():
    """主程式"""
    dry_run = "--dry-run" in sys.argv

    try:
        runner = FeaturePipelineRunner(dry_run)
        runner.run()
    except Exception as e:
        print(f"\n錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
