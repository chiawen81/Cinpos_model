import pandas as pd
import numpy as np

# 讀取最新的預測結果和原始資料
# 使用「成功加入排除清單」版本（只排除2部問題電影）
pred = pd.read_csv('data/ML_boxoffice/phase4_models/M1_20251108_194054_成功加入排除清單/test_predictions.csv')
full_data = pd.read_csv('data/ML_boxoffice/phase3_prepare/M1_20251108_194054_成功加入排除清單/preprocessed_full.csv')

print("=" * 80)
print("分析離群值類型：大片 vs 爛片")
print("=" * 80)

# 計算絕對誤差並找出離群值
pred['abs_error_lgb'] = abs(pred['error_lgb'])
Q3 = pred['abs_error_lgb'].quantile(0.75)
IQR = Q3 - pred['abs_error_lgb'].quantile(0.25)
outlier_threshold = Q3 + 1.5 * IQR

outliers = pred[pred['abs_error_lgb'] > outlier_threshold]

print(f"\n找到 {len(outliers)} 個離群值樣本")
print(f"涉及 {outliers['gov_id'].nunique()} 部電影")
print(f"離群值 gov_id: {sorted(outliers['gov_id'].unique())}")

# 合併資料
merged = pred.merge(full_data, on='gov_id', how='left')
outlier_data = merged[merged['abs_error_lgb'] > outlier_threshold]

# 分類離群值：大片 vs 爛片
print("\n" + "-" * 80)
print("【分類 1】基於實際票房金額")
print("-" * 80)

# 定義大片閾值（使用全體資料的 75% 分位數）
big_movie_threshold = merged['actual'].quantile(0.75)
small_movie_threshold = merged['actual'].quantile(0.25)

print(f"大片定義：實際票房 > {big_movie_threshold:,.0f} (75% 分位數)")
print(f"小片定義：實際票房 < {small_movie_threshold:,.0f} (25% 分位數)")

big_outliers = outlier_data[outlier_data['actual'] > big_movie_threshold]
small_outliers = outlier_data[outlier_data['actual'] < small_movie_threshold]
mid_outliers = outlier_data[(outlier_data['actual'] >= small_movie_threshold) &
                            (outlier_data['actual'] <= big_movie_threshold)]

print(f"\n離群值分布:")
print(f"  大片離群值: {len(big_outliers)} 個樣本 ({len(big_outliers)/len(outlier_data)*100:.1f}%)")
print(f"  中等片離群值: {len(mid_outliers)} 個樣本 ({len(mid_outliers)/len(outlier_data)*100:.1f}%)")
print(f"  小片離群值: {len(small_outliers)} 個樣本 ({len(small_outliers)/len(outlier_data)*100:.1f}%)")

print("\n大片離群值詳情:")
if len(big_outliers) > 0:
    big_summary = big_outliers.groupby('gov_id').agg({
        'actual': ['count', 'mean', 'min', 'max'],
        'abs_error_lgb': 'mean'
    }).round(0)
    print(big_summary)
else:
    print("  無大片離群值")

print("\n小片離群值詳情:")
if len(small_outliers) > 0:
    small_summary = small_outliers.groupby('gov_id').agg({
        'actual': ['count', 'mean', 'min', 'max'],
        'abs_error_lgb': 'mean'
    }).round(0)
    print(small_summary)
else:
    print("  無小片離群值")

# 檢查資料筆數
print("\n" + "-" * 80)
print("【分析 2】檢查每部電影的資料筆數")
print("-" * 80)

# 統計每部電影的筆數
movie_counts = full_data.groupby('gov_id').size().reset_index(name='row_count')
print(f"\n資料筆數分布:")
print(movie_counts['row_count'].describe())

print(f"\n資料筆數統計:")
print(f"  < 3 筆: {(movie_counts['row_count'] < 3).sum()} 部電影")
print(f"  3-5 筆: {((movie_counts['row_count'] >= 3) & (movie_counts['row_count'] <= 5)).sum()} 部電影")
print(f"  6-10 筆: {((movie_counts['row_count'] >= 6) & (movie_counts['row_count'] <= 10)).sum()} 部電影")
print(f"  > 10 筆: {(movie_counts['row_count'] > 10).sum()} 部電影")

# 檢查離群值電影的資料筆數
outlier_gov_ids = outliers['gov_id'].unique()
outlier_movie_counts = movie_counts[movie_counts['gov_id'].isin(outlier_gov_ids)]

print(f"\n離群值電影的資料筆數:")
for idx, row in outlier_movie_counts.iterrows():
    gov_id = int(row['gov_id'])
    count = int(row['row_count'])
    avg_boxoffice = full_data[full_data['gov_id'] == gov_id]['amount'].mean()
    print(f"  gov_id={gov_id}: {count} 筆, 平均票房={avg_boxoffice:,.0f}")

# 評估方案2：移除資料筆數 < 3 的電影
print("\n" + "-" * 80)
print("【方案評估】移除資料筆數 < 3 的電影")
print("-" * 80)

few_data_movies = movie_counts[movie_counts['row_count'] < 3]['gov_id'].tolist()
if len(few_data_movies) > 0:
    print(f"\n將被移除的電影: {len(few_data_movies)} 部")
    print(f"gov_id: {few_data_movies}")

    few_data_rows = full_data[full_data['gov_id'].isin(few_data_movies)]
    print(f"將被移除的資料筆數: {len(few_data_rows)} 筆")

    # 檢查這些電影是否包含離群值
    few_data_outliers = outliers[outliers['gov_id'].isin(few_data_movies)]
    print(f"其中包含的離群值樣本: {len(few_data_outliers)} 個")
else:
    print("\n無資料筆數 < 3 的電影")

# 評估方案1：需要多少大片資料
print("\n" + "-" * 80)
print("【方案評估】導入更多大片資料")
print("-" * 80)

current_big_movies = full_data[full_data['amount'] > big_movie_threshold]['gov_id'].nunique()
current_total_movies = full_data['gov_id'].nunique()

print(f"\n當前資料集:")
print(f"  總電影數: {current_total_movies} 部")
print(f"  大片數量: {current_big_movies} 部 ({current_big_movies/current_total_movies*100:.1f}%)")
print(f"  大片定義: 票房 > {big_movie_threshold:,.0f}")

print(f"\n建議:")
print(f"  如果要改善對大片的預測，建議增加大片樣本至 {int(current_big_movies * 1.5)} 部以上")

print("\n" + "=" * 80)
