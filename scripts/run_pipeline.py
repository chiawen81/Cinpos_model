#!/usr/bin/env python3
"""
Pipeline 執行器
====================

功能說明:
- 讀取 YAML 配置檔案
- 根據配置自動執行對應的腳本
- 支援多個腳本的參數管理

使用方式:
    uv run scripts/run_pipeline.py config/pipeline_config.yaml
    uv run scripts/run_pipeline.py config/pipeline_config.yaml --dry-run  # 只顯示將執行的命令，不實際執行
"""

import yaml
import subprocess
import sys
from pathlib import Path
from datetime import datetime


class PipelineRunner:
    """Pipeline 執行器類別"""

    def __init__(self, config_path, dry_run=False):
        """
        初始化執行器

        Parameters:
        -----------
        config_path : str
            配置檔案路徑
        dry_run : bool
            是否只顯示命令而不實際執行
        """
        self.config_path = Path(config_path)
        self.dry_run = dry_run
        self.config = None

    def load_config(self):
        """載入配置檔案"""
        print("=" * 70)
        print("Pipeline 執行器")
        print("=" * 70)
        print(f"\n載入配置檔案: {self.config_path}")

        if not self.config_path.exists():
            raise FileNotFoundError(f"找不到配置檔案: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        print(f"  [OK] 配置檔案載入成功")

    def run_add_cumsum_features(self, config):
        """執行累積特徵生成腳本"""
        print("\n" + "-" * 70)
        print("[1/n] 執行累積特徵生成腳本")
        print("-" * 70)

        if not config.get("enabled", False):
            print("  [SKIP] 此腳本已停用（enabled: false）")
            return

        # 顯示配置
        print(f"\n配置:")
        print(f"  - 輸入檔案: {config.get('input_file')}")
        print(f"  - 輸出檔案: {config.get('output_file')}")
        print(f"  - 說明: {config.get('description', '無')}")

        # 構建命令
        cmd = [
            "uv",
            "run",
            "src/ML_boxoffice/phase2_features/add_cumsum_features.py",
            config["input_file"],
            config["output_file"],
        ]

        self._execute_command(cmd)

    def run_filter_data(self, config):
        """執行資料過濾腳本"""
        print("\n" + "-" * 70)
        print("[n/n] 執行資料過濾腳本")
        print("-" * 70)

        if not config.get("enabled", False):
            print("  [SKIP] 此腳本已停用（enabled: false）")
            return

        # 顯示配置
        print(f"\n配置:")
        print(f"  - 輸入檔案: {config.get('input_file')}")
        if config.get("output_file"):
            print(f"  - 輸出檔案: {config.get('output_file')}")
        else:
            print(f"  - 輸出檔案: (自動生成)")

        if config.get("exclude_config"):
            print(f"  - 電影剔除配置: {config.get('exclude_config')}")

        if config.get("drop_columns"):
            print(f"  - 刪除欄位: {', '.join(config.get('drop_columns', []))}")

        if config.get("keep_rounds"):
            print(f"  - 保留輪次: {', '.join(map(str, config.get('keep_rounds', [])))}")

        if config.get("drop_null_active_week"):
            print(f"  - 刪除無活躍編號: 是")

        print(f"  - 說明: {config.get('description', '無')}")

        # 構建命令
        cmd = [
            "uv",
            "run",
            "src/ML_boxoffice/phase2_features/filter_data.py",
            config["input_file"],
        ]

        # 添加可選參數
        if config.get("exclude_config"):
            cmd.extend(["--exclude-config", config["exclude_config"]])

        if config.get("drop_columns"):
            columns = ",".join(config["drop_columns"])
            cmd.extend(["--drop-columns", columns])

        if config.get("keep_rounds"):
            rounds = ",".join(map(str, config["keep_rounds"]))
            cmd.extend(["--keep-rounds", rounds])

        if config.get("drop_null_active_week", False):
            cmd.append("--drop-null-active-week")

        if config.get("output_file"):
            cmd.extend(["--output", config["output_file"]])

        self._execute_command(cmd)

    def _execute_command(self, cmd):
        """執行命令"""
        print(f"\n要執行的命令:")
        print(f"  {' '.join(cmd)}")

        if self.dry_run:
            print("\n  [DRY-RUN] 僅顯示命令，不實際執行")
            return

        print("\n執行中...")
        print("-" * 70)

        try:
            result = subprocess.run(cmd, check=True, capture_output=False, text=True)
            print("-" * 70)
            print("  [OK] 執行成功")
        except subprocess.CalledProcessError as e:
            print("-" * 70)
            print(f"  [ERROR] 執行失敗: {e}")
            sys.exit(1)

    def run(self):
        """執行 pipeline"""
        self.load_config()

        print("\n" + "=" * 70)
        print("開始執行 Pipeline")
        print("=" * 70)

        if self.dry_run:
            print("\n[模式] DRY-RUN：只顯示將執行的命令，不會實際執行")

        # 計算要執行的腳本數量
        enabled_scripts = []
        if self.config.get("add_cumsum_features", {}).get("enabled"):
            enabled_scripts.append("add_cumsum_features")
        if self.config.get("filter_data", {}).get("enabled"):
            enabled_scripts.append("filter_data")

        if not enabled_scripts:
            print("\n[WARNING] 沒有啟用任何腳本（所有腳本的 enabled 都是 false）")
            print("請編輯配置檔案並將要執行的腳本設為 enabled: true")
            return

        print(f"\n將執行 {len(enabled_scripts)} 個腳本:")
        for i, script in enumerate(enabled_scripts, 1):
            print(f"  {i}. {script}")

        # 執行各個腳本
        if "add_cumsum_features" in enabled_scripts:
            self.run_add_cumsum_features(self.config["add_cumsum_features"])

        if "filter_data" in enabled_scripts:
            self.run_filter_data(self.config["filter_data"])

        # 完成
        print("\n" + "=" * 70)
        print("Pipeline 執行完成！")
        print("=" * 70)
        print(f"\n完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("使用方式:")
        print("  uv run scripts/run_pipeline.py config/pipeline_config.yaml")
        print("  uv run scripts/run_pipeline.py config/pipeline_config.yaml --dry-run")
        sys.exit(1)

    config_path = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    try:
        runner = PipelineRunner(config_path, dry_run)
        runner.run()
    except Exception as e:
        print(f"\n錯誤: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
