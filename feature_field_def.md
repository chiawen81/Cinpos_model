# ==================== 基本資訊 ==================== V
movie_id
round_idx                          # 當週輪次
rounds_cumsum                      # 已知累計輪次


# ==================== 當週時間資訊 ==================== V
current_week_real_idx              # 當輪當週真實週次（輪內連續編號）
current_week_active_idx            # 當輪當週活躍週次（去除0後重編）
gap_real_week_2to1                 # week-2→week-1 跳週數
gap_real_week_1tocurrent           # week-1→當週 跳週數


# ==================== 近期趨勢(皆為活躍周) ==================== V 缺3 (PR*3)
boxoffice_week_2                   # 兩周前票房
boxoffice_week_1                   # 上周票房
boxoffice_week_1_PR                # 上周票房 PR
audience_week_2		   	   # 兩周前觀影人數
audience_week_1		  	   # 上週觀影人數
audience_week_1_PR		   # 上週觀影人數 PR
screens_week_2			   # 兩周前院線數
screens_week_1			   # 上周院線數
screens_week_1_PR		   # 上周院線數 PR


# ==================== 累積資訊(截至上週) ====================
boxoffice_cumsum        	   # 跨輪累積票房（截至上週，不含當週）
boxoffice_round1_cumsum  	   # 首輪累積票房（截至上週，不含當週）
boxoffice_current_round_cumsum     # 當輪累積票房（截至上週，不含當週）
audience_cumsum         	   # 跨輪累積觀影人次（截至上週，不含當週）
audience_round1_cumsum		   # 首輪累積觀影人次（截至上週，不含當週）
audience_current_round_cumsum      # 當輪累積觀影人次（截至上週，不含當週）


# ==================== 開片實力（首輪）==================== V 缺2 (PR、avg)
open_week1_days			   # 首輪第1週天數
open_week1_boxoffice		   # 首輪第1週票房
open_week1_boxoffice_daily_avg	   # 首輪第1週日均票房
open_week1_boxoffice_daily_avg_PR  # 首輪第1週日均 PR(按年分組)
open_week2_boxoffice		   # 首輪第2週票房


# ==================== 市場資訊 ====================
ticket_price_avg_current	   # 發行年的平均票價(分首輪 / 非首輪兩種票價)
release_year		   	   # 上映年份			
release_month			   # 上映月份
region				   # 發行地區 
file_length                        # 片長(分鐘)
is_restricted			   # 是否為限制級
publisher 			   # 發片商


# ==================== 目標變數 ====================
target_week_boxoffice		  # 當週票房(預測目標)



2. 未來再考慮納入
 - 首輪佔比: round1_cumsum_ratio = 
	     boxoffice_round1_total / boxoffice_all_rounds_cumsum
 - 當輪佔比: current_round_cumsum_ratio = 
             boxoffice_current_round_cumsum / boxoffice_all_rounds_cumsum
 - 首週日均PR open_week1_boxoffice_daily_avg_PR
   => 要分組比較(按年分)