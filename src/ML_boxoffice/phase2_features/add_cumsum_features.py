#!/usr/bin/env python3
"""
累積特徵生成腳本 v2 (適配實際資料格式)
====================

功能說明:
- 接收包含實際票房資料的 CSV 檔案
- 保留所有原有欄位
- 新增 6 個累積特徵欄位（截至上週，不含當週）

實際欄位對應:
- gov_id → movie_id (電影唯一識別)
- round_idx → round (輪次)
- current_week_active_idx → week_in_round (當輪週次)
- amount → boxoffice (本週票房)
- tickets → audience (本週觀影人數)

累積欄位說明:
1. boxoffice_cumsum: 跨輪累積票房（首輪全部 + 當輪截至上週）
2. boxoffice_round1_cumsum: 首輪累積票房
3. boxoffice_current_round_cumsum: 當輪累積票房
4. audience_cumsum: 跨輪累積觀影人數
5. audience_round1_cumsum: 首輪累積觀影人數
6. audience_current_round_cumsum: 當輪累積觀影人數

使用方式:
    python add_cumsum_features_v2.py input.csv output.csv
    python add_cumsum_features_v2.py input.csv  # 預設輸出到 input_with_cumsum.csv
"""

import pandas as pd
import sys
from pathlib import Path


def calculate_cumsum_features(df):
    """
    計算累積特徵（截至上週，不含當週）
    
    Parameters:
    -----------
    df : pd.DataFrame
        輸入資料框，必須包含以下欄位:
        - gov_id: 電影ID
        - round_idx: 輪次(1=首輪, 2=次輪)
        - current_week_active_idx: 當輪週次
        - amount: 本週票房
        - tickets: 本週觀影人數
    
    Returns:
    --------
    pd.DataFrame
        包含原有欄位 + 6個新增累積欄位
    """
    
    # 檢查必要欄位
    required_cols = ['gov_id', 'round_idx', 'current_week_active_idx', 'amount', 'tickets']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"缺少必要欄位: {missing_cols}\n實際欄位: {list(df.columns)}")
    
    # 複製資料框避免修改原始資料
    result_df = df.copy()
    
    # 確保資料按照 gov_id, round_idx, current_week_active_idx 排序
    result_df = result_df.sort_values(
        ['gov_id', 'round_idx', 'current_week_active_idx']
    ).reset_index(drop=True)
    
    # 初始化新欄位
    cumsum_cols = [
        'boxoffice_cumsum',
        'boxoffice_round1_cumsum', 
        'boxoffice_current_round_cumsum',
        'audience_cumsum',
        'audience_round1_cumsum',
        'audience_current_round_cumsum'
    ]
    
    for col in cumsum_cols:
        result_df[col] = 0.0
    
    # 按電影分組計算
    for gov_id, movie_group in result_df.groupby('gov_id'):
        movie_indices = movie_group.index
        
        # 分離首輪和當輪資料
        round1_data = movie_group[movie_group['round_idx'] == 1].copy()
        
        # 計算首輪總票房和總觀影人數（用於次輪的跨輪累積）
        round1_total_boxoffice = round1_data['amount'].sum() if len(round1_data) > 0 else 0
        round1_total_audience = round1_data['tickets'].sum() if len(round1_data) > 0 else 0
        
        # 逐列計算累積值
        for idx in movie_indices:
            current_round = result_df.loc[idx, 'round_idx']
            current_week = result_df.loc[idx, 'current_week_active_idx']
            
            # 取得當前電影、當前輪次、當前週次之前的所有資料
            previous_data = movie_group[
                ((movie_group['round_idx'] == current_round) & 
                 (movie_group['current_week_active_idx'] < current_week))
            ]
            
            # === 計算當輪累積（截至上週） ===
            current_round_boxoffice_cumsum = previous_data['amount'].sum()
            current_round_audience_cumsum = previous_data['tickets'].sum()
            
            result_df.loc[idx, 'boxoffice_current_round_cumsum'] = current_round_boxoffice_cumsum
            result_df.loc[idx, 'audience_current_round_cumsum'] = current_round_audience_cumsum
            
            # === 計算首輪累積 ===
            if current_round == 1:
                # 首輪進行中: 累積到上週
                result_df.loc[idx, 'boxoffice_round1_cumsum'] = current_round_boxoffice_cumsum
                result_df.loc[idx, 'audience_round1_cumsum'] = current_round_audience_cumsum
            else:
                # 首輪已結束: 使用首輪總計（固定值）
                result_df.loc[idx, 'boxoffice_round1_cumsum'] = round1_total_boxoffice
                result_df.loc[idx, 'audience_round1_cumsum'] = round1_total_audience
            
            # === 計算跨輪累積 ===
            if current_round == 1:
                # 首輪: 跨輪累積 = 當輪累積
                result_df.loc[idx, 'boxoffice_cumsum'] = current_round_boxoffice_cumsum
                result_df.loc[idx, 'audience_cumsum'] = current_round_audience_cumsum
            else:
                # 次輪: 跨輪累積 = 首輪總計 + 當輪累積
                result_df.loc[idx, 'boxoffice_cumsum'] = round1_total_boxoffice + current_round_boxoffice_cumsum
                result_df.loc[idx, 'audience_cumsum'] = round1_total_audience + current_round_audience_cumsum
    
    # 轉換整數欄位
    integer_cols = ['audience_cumsum', 'audience_round1_cumsum', 'audience_current_round_cumsum']
    for col in integer_cols:
        result_df[col] = result_df[col].astype(int)
    
    return result_df


def main():
    """主程式"""
    
    # 解析命令列參數
    if len(sys.argv) < 2:
        print("使用方式: uv run add_cumsum_features_v2.py <input_csv> [output_csv]")
        print("""範例: 
        uv run src/ML_boxoffice/phase2_features/add_cumsum_features.py data\ML_boxoffice\phase1_flattened\boxoffice_timeseries_2025-11-06.csv data\ML_boxoffice\phase2_features\with_cumsum\features_cumsum_2025-11-06.csv
        """)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    
    # 決定輸出路徑
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        # 預設: 在檔名加上 _with_cumsum
        output_path = input_path.parent / f"{input_path.stem}_with_cumsum{input_path.suffix}"
    
    # 檢查輸入檔案
    if not input_path.exists():
        print(f"錯誤: 找不到輸入檔案 {input_path}")
        sys.exit(1)
    
    print(f"讀取檔案: {input_path}")
    
    try:
        # 讀取 CSV
        df = pd.read_csv(input_path)
        print(f"  - 原始資料: {len(df)} 列, {len(df.columns)} 欄")
        print(f"  - 原始欄位數: {len(df.columns)}")
        
        # 顯示關鍵欄位資訊
        key_cols = ['gov_id', 'round_idx', 'current_week_active_idx', 'amount', 'tickets']
        available_key_cols = [col for col in key_cols if col in df.columns]
        if available_key_cols:
            print(f"  - 關鍵欄位: {available_key_cols}")
        
        # 計算累積特徵
        print("\n計算累積特徵...")
        result_df = calculate_cumsum_features(df)
        print(f"  - 新增 6 個累積欄位")
        print(f"  - 輸出資料: {len(result_df)} 列, {len(result_df.columns)} 欄")
        
        # 確保輸出目錄存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 儲存結果
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n✓ 成功儲存到: {output_path}")
        
        # 顯示新增的欄位範例
        new_cols = [
            'boxoffice_cumsum', 'boxoffice_round1_cumsum', 'boxoffice_current_round_cumsum',
            'audience_cumsum', 'audience_round1_cumsum', 'audience_current_round_cumsum'
        ]
        display_cols = ['gov_id', 'round_idx', 'current_week_active_idx'] + new_cols
        print("\n新增欄位範例 (前 5 列):")
        print(result_df[display_cols].head(5).to_string())
        
        # 統計資訊
        print("\n累積欄位統計:")
        stats_df = result_df[new_cols].describe()
        print(stats_df.to_string())
        
        # 檢查是否有次輪資料
        if (result_df['round_idx'] > 1).any():
            print("\n✓ 檢測到次輪資料，跨輪累積已正確計算")
            round2_sample = result_df[result_df['round_idx'] == 2].head(2)
            if len(round2_sample) > 0:
                print("\n次輪範例 (前 2 列):")
                print(round2_sample[display_cols].to_string())
        
    except Exception as e:
        print(f"\n錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()