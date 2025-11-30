#!/usr/bin/env python3
"""
資料刪減腳本
====================

功能說明:
- 根據指定條件刪減資料
- 支援欄位刪減、輪次刪減、無活躍編號的 row 刪減
- 支援從配置檔案讀取要剔除的電影清單
- 保持原始資料順序不變

使用方式:
    uv run filter_data.py <input_csv> [選項]

選項:
    --exclude-config <path>     電影剔除清單配置檔案路徑（可選，預設使用: config/exclude_movies.csv）
    --drop-columns <col1,col2>  要刪除的欄位清單（逗號分隔）
    --keep-rounds <1,2,3>       要保留的輪次（逗號分隔，預設保留全部）
    --drop-null-active-week     刪除無輪內活躍編號(current_week_active_idx為NaN)的row
    --output <path>             輸出檔案路徑（可選，預設自動生成）

範例:
    # 刪除特定欄位並只保留第1,2輪
    uv run filter_data.py input.csv --drop-columns "boxoffice_week_2,audience_week_2" --keep-rounds "1,2"

    # 刪除無活躍編號的row
    uv run filter_data.py input.csv --drop-null-active-week

    # 使用自訂配置檔案並刪除特定欄位
    uv run filter_data.py input.csv --exclude-config my_excludes.csv --drop-columns "col1,col2"
"""

import pandas as pd
import sys
import argparse
from pathlib import Path
from datetime import datetime
from ml.common.path_utils import PHASE2_FILTER_DIR


class DataFilter:
    """資料過濾器類別"""

    # 必須存在的欄位
    REQUIRED_FIELDS = [
        "gov_id",
        "official_release_date",
        "week_range",
        "round_idx",
        "current_week_real_idx",
        "current_week_active_idx",
        "gap_real_week_2to1",
        "gap_real_week_1tocurrent",
    ]

    # 至少保留一個的欄位
    MUST_KEEP_ONE = [
        "official_release_date",
        "week_range",
        "round_idx",
        "current_week_real_idx",
        "current_week_active_idx",
    ]

    # 不可刪除的欄位
    PROTECTED_FIELDS = ["gov_id"]

    def __init__(self, input_path, exclude_config_path=None):
        """
        初始化過濾器

        Parameters:
        -----------
        input_path : str
            輸入CSV檔案路徑
        exclude_config_path : str, optional
            電影剔除清單配置檔案路徑
        """
        self.input_path = Path(input_path)
        self.exclude_config_path = exclude_config_path
        self.df = None
        self.original_row_count = 0
        self.original_col_count = 0

    def load_data(self):
        """載入資料並進行安全檢查"""
        print(f"載入檔案: {self.input_path}")

        if not self.input_path.exists():
            raise FileNotFoundError(f"找不到輸入檔案: {self.input_path}")

        self.df = pd.read_csv(self.input_path)
        self.original_row_count = len(self.df)
        self.original_col_count = len(self.df.columns)

        print(f"  - 原始資料: {self.original_row_count} 列, {self.original_col_count} 欄")

        # 保存原始順序
        self.df["_original_order"] = range(len(self.df))

        # 安全檢查：檢查必須欄位
        self._check_required_fields()

    def _check_required_fields(self):
        """檢查必須存在的欄位"""
        missing_fields = [f for f in self.REQUIRED_FIELDS if f not in self.df.columns]

        if missing_fields:
            raise ValueError(
                f"資料缺少必要欄位，無法執行刪減操作！\n"
                f"缺少的欄位: {missing_fields}\n"
                f"實際欄位: {list(self.df.columns)}"
            )

        print("  [OK] 安全檢查通過：所有必要欄位皆存在")

    def exclude_movies(self):
        """從配置檔案讀取並剔除電影"""
        if not self.exclude_config_path:
            # 使用預設路徑
            default_config = Path("config/exclude_movies.csv")
            if default_config.exists():
                self.exclude_config_path = default_config
            else:
                print("  - 未指定電影剔除清單，跳過此步驟")
                return

        config_path = Path(self.exclude_config_path)

        if not config_path.exists():
            print(f"  [WARNING] 找不到配置檔案 {config_path}，跳過電影剔除")
            return

        print(f"\n讀取電影剔除清單: {config_path}")

        # 讀取配置檔案（跳過註解行）
        try:
            exclude_df = pd.read_csv(config_path, comment="#", skipinitialspace=True)

            if "gov_id" not in exclude_df.columns:
                print("  [WARNING] 配置檔案缺少 gov_id 欄位，跳過電影剔除")
                return

            exclude_ids = exclude_df["gov_id"].dropna().astype(int).tolist()

            if not exclude_ids:
                print("  - 配置檔案中沒有要剔除的電影")
                return

            # 剔除電影
            before_count = len(self.df)
            self.df = self.df[~self.df["gov_id"].isin(exclude_ids)]
            after_count = len(self.df)
            removed_count = before_count - after_count

            print(f"  - 剔除 {removed_count} 部電影，共 {removed_count} 筆資料")
            print(f"  - 剔除的電影 ID: {exclude_ids}")

        except Exception as e:
            print(f"  [WARNING] 讀取配置檔案時發生錯誤: {e}")
            print("  - 跳過電影剔除步驟")

    def drop_columns(self, columns_to_drop):
        """
        刪除指定欄位

        Parameters:
        -----------
        columns_to_drop : list
            要刪除的欄位清單
        """
        if not columns_to_drop:
            return

        print(f"\n刪除欄位: {columns_to_drop}")

        # 檢查是否嘗試刪除受保護的欄位
        protected_in_list = [col for col in columns_to_drop if col in self.PROTECTED_FIELDS]
        if protected_in_list:
            raise ValueError(f"不可刪除受保護的欄位: {protected_in_list}")

        # 檢查刪除後是否至少保留一個必要欄位
        remaining_must_keep = [
            col
            for col in self.MUST_KEEP_ONE
            if col in self.df.columns and col not in columns_to_drop
        ]

        if not remaining_must_keep:
            raise ValueError(
                f"必須至少保留以下欄位中的一個: {self.MUST_KEEP_ONE}\n" f"無法全部刪除！"
            )

        # 檢查欄位是否存在
        existing_cols = [col for col in columns_to_drop if col in self.df.columns]
        non_existing_cols = [col for col in columns_to_drop if col not in self.df.columns]

        if non_existing_cols:
            print(f"  [WARNING] 以下欄位不存在，將忽略: {non_existing_cols}")

        if existing_cols:
            self.df = self.df.drop(columns=existing_cols)
            print(f"  - 已刪除 {len(existing_cols)} 個欄位")

    def keep_rounds(self, rounds_to_keep):
        """
        只保留指定的輪次

        Parameters:
        -----------
        rounds_to_keep : list
            要保留的輪次清單
        """
        if not rounds_to_keep:
            return

        print(f"\n保留輪次: {rounds_to_keep}")

        before_count = len(self.df)
        self.df = self.df[self.df["round_idx"].isin(rounds_to_keep)]
        after_count = len(self.df)
        removed_count = before_count - after_count

        print(f"  - 刪除 {removed_count} 筆資料（非指定輪次）")
        print(f"  - 保留 {after_count} 筆資料")

    def drop_null_active_week(self):
        """刪除無輪內活躍編號(current_week_active_idx為NaN)的row"""
        print(f"\n刪除無輪內活躍編號的 row")

        before_count = len(self.df)
        self.df = self.df[self.df["current_week_active_idx"].notna()]
        after_count = len(self.df)
        removed_count = before_count - after_count

        print(f"  - 刪除 {removed_count} 筆資料（current_week_active_idx 為 NaN）")
        print(f"  - 保留 {after_count} 筆資料")

    def restore_order_and_save(self, output_path):
        """恢復原始順序並儲存"""
        print(f"\n準備儲存資料...")

        # 恢復原始順序
        self.df = self.df.sort_values("_original_order").reset_index(drop=True)

        # 刪除臨時欄位
        self.df = self.df.drop(columns=["_original_order"])

        # 確保輸出目錄存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 儲存
        self.df.to_csv(output_path, index=False, encoding="utf-8-sig")

        print(f"  - 最終資料: {len(self.df)} 列, {len(self.df.columns)} 欄")
        print(f"  - 儲存到: {output_path}")
        print(f"\n總計:")
        print(f"  - 刪除列數: {self.original_row_count - len(self.df)}")
        print(
            f"  - 刪除欄數: {self.original_col_count - len(self.df.columns) - 1}"
        )  # -1 是因為 _original_order


def generate_output_path(input_path):
    """
    生成輸出檔案路徑（帶時間戳記）

    Parameters:
    -----------
    input_path : Path
        輸入檔案路徑

    Returns:
    --------
    Path
        輸出檔案路徑
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(PHASE2_FILTER_DIR)
    output_filename = f"filtered_{input_path.stem}_{timestamp}.csv"
    return output_dir / output_filename


def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description="資料刪減腳本：支援欄位刪減、輪次刪減、電影剔除",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 刪除特定欄位並只保留第1,2輪
  uv run filter_data.py input.csv --drop-columns "boxoffice_week_2,audience_week_2" --keep-rounds "1,2"

  # 刪除無活躍編號的row
  uv run filter_data.py input.csv --drop-null-active-week

  # 使用自訂配置檔案
  uv run filter_data.py input.csv --exclude-config my_excludes.csv
        """,
    )

    parser.add_argument("input_csv", help="輸入CSV檔案路徑")
    parser.add_argument(
        "--exclude-config", help="電影剔除清單配置檔案路徑（預設: config/exclude_movies.csv）"
    )
    parser.add_argument(
        "--drop-columns", help='要刪除的欄位清單（逗號分隔），例如: "col1,col2,col3"'
    )
    parser.add_argument("--keep-rounds", help='要保留的輪次（逗號分隔），例如: "1,2"')
    parser.add_argument(
        "--drop-null-active-week",
        action="store_true",
        help="刪除無輪內活躍編號(current_week_active_idx為NaN)的row",
    )
    parser.add_argument("--output", help="輸出檔案路徑（可選，預設自動生成帶時間戳記的檔名）")

    args = parser.parse_args()

    print("=" * 60)
    print("資料刪減腳本")
    print("=" * 60)

    try:
        # 創建過濾器
        filter = DataFilter(args.input_csv, args.exclude_config)

        # 載入資料
        filter.load_data()

        # 步驟1: 剔除電影
        filter.exclude_movies()

        # 步驟2: 刪除欄位
        if args.drop_columns:
            columns = [col.strip() for col in args.drop_columns.split(",")]
            filter.drop_columns(columns)

        # 步驟3: 保留特定輪次
        if args.keep_rounds:
            rounds = [int(r.strip()) for r in args.keep_rounds.split(",")]
            filter.keep_rounds(rounds)

        # 步驟4: 刪除無活躍編號的row
        if args.drop_null_active_week:
            filter.drop_null_active_week()

        # 決定輸出路徑
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = generate_output_path(Path(args.input_csv))

        # 儲存結果
        filter.restore_order_and_save(output_path)

        print("\n" + "=" * 60)
        print("處理完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n錯誤: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
