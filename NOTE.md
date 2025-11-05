# 目前開發階段: 彙總模型訓練資料
## 1103 to do list
2. 完成 6 生成movie_master_builder.py => 產生full+三支模型訓練資料
   => ChatGPT: https://chatgpt.com/g/g-p-68b005c1aeb881919915454a65419b81/c/6907653f-ec7c-8323-a451-d7804640985e
   => 檢查生成出來的報表
   => 優化註解
3. 倒歷史資料、刪除離群值
4. 訓練 M3 推薦模型、評估、調教
5. 訓練 M1 票房模型、評估、調教
 (先跳過M2 再上映，之後再補)

re_release_gap_days 上映間隔
file_length 片長
is_long_tail=> 改成只要任一輪超過10周

待確認作法：
  - 多輪電影只留最後一輪可能無法反映狀況=> ex:阿凡達的第一周數據比第三周更有代表性
  - 動能欄位=> 只給上映中的電影
  - 回顧欄位=> 只給下映的電影
  - 特殊案例:發現發行日期寫錯 造成 second_week_ampunt_growth_rate 異常 
  - 刪除離群值=> 怎麼定義?

decline_rate_mean"逐周類型的欄位，中間有inactive的周次怎麼算?
momentum_3w:同上+確認第一輪以後的第一個衰退值
avg_ticket_price=> 計算有誤，阿凡達的平均票價只有93元XD
previous_avg_amount => 計算有誤，阿凡達的上輪平均值報高
重複欄位=> gov_title_zh	gov_title_en、official_release_date_y、source_file






## ------------------------------------ 待處理清單 ------------------------------------
6. 生成 master_data_builder.py
=> 欄位引用不變，另外新增電影性質、上映狀態
=> 資料源會改變成四周檔按omdb/gov的電影資訊、聚合後的票房資訊/評分資訊

9. 在 master_data_builder.py 新增以下欄位
  (2) same_class_amount_last_week	
      mean(total_amount ÷ total_weeks) for all films with same region（若無逐週資料，則取整體平均週票房作為近似）
      ps. 若只有最新輪，無法取得「上週」	同樣可用「同區域電影平均週票房」作近似

  (3) market_heat_level	
      依 total_amount 或 avg_amount_per_week 的分位數切級（如 Q3 = 高熱、Q2 = 中熱）
      market_heat_level	改成
        - 上映中: 用當周票房去比
        - 下檔: 用該輪總票房去比

  1. 比較的影片數過少，則省略market_heat_level
  2. 砍掉所有失去意義的動態指標
  3. 需要逐周計算的欄位，如果中間遇到空白怎麼處理?

## ------------------------------------ 暫不處理 ------------------------------------
1. 建立聚合檔 rating_integrate.py
  (1) 腳本位置src\ML_recommend\data_data_integration
  (2) 資料生成的位置data\aggregated
  (3) 生成內容: 單一電影的票評分的逐周資料合成一個row，再把所有電影row合併成一隻綁案
  (4) 生成的檔案格式: boxoffice_agg_2025W43.csv

7. 爬歷史資料
   因應直接拿 gov_title_en 去打 omdb API 錯誤太多
=> 改先從imdb拿到imdb_id，再去omdb拿資料
=> 新生成檔案:人工對照表gov_title_en、gov_title_zh、gov_id、imdb_id
(---未完成pipeline企劃---)

9. 想新增的欄位
  (1) momentum_current_3w
      => 此為動態欄位，只以最近三周來統計票房動能(momentum_3w是逐周票房動能的平均)
      => 修改腳本: boxoffice_integrate.py
  (2) peak_week_index
      => 該輪中，票房最好的周次
      => 修改腳本: boxoffice_integrate.py
  (3) 上週成績(amount/ticket/rate)
      => 修改腳本: 要出報表的時候再併即可
      
10. 未來再考慮納入的特徵欄位
 - 首輪佔比: round1_cumsum_ratio = 
	     boxoffice_round1_total / boxoffice_all_rounds_cumsum
 - 當輪佔比: current_round_cumsum_ratio = 
             boxoffice_current_round_cumsum / boxoffice_all_rounds_cumsum
 - 首週日均PR open_week1_boxoffice_daily_avg_PR
   => 要分組比較(按年分) 


## ------------------------------------ 放棄處理 ------------------------------------
4. 標記- 電影性質(第一次/重新/復刻上映)
  (1) 處理腳本: data_cleaning\boxoffice_permovie.py 
  (2) 生成在哪: data\processed\boxoffice_permovie下的單一電影
"""
因為電影公開資料，發行日期只會顯示當下日期，因此無法判定復刻上映的情況
舉例來說
    1. 一一：這是2000初的電影，但現在發行日期是2025
    2. 樂來樂愛你：這是2016的電影，但政府公開資料分成獨立的三筆資料(三個都叫做"樂來樂愛你")
"""

99. 訓練 M2 <再上映>模型、評估、調教


## ------------------------------------ 拉齊週期 ------------------------------------

<該輪即時資訊>
是否上映中(若否，以下為空值)-----------
當周上映周次(總周次/活躍周次)、上映天數
當周上映輪次(第一round/第2round....)
當周狀況：票房、觀影人次、衰退率、市場熱度(market_level)=> 可以改成PR
該輪加總：票房、觀影人次
 - 衰退率：平均衰退率、第二周衰退率、第三周衰退率
 - 巔峰：周次、當周票房、當周衰退率、當周觀影人次


<同生命週期- 首輪>
上映周次(總上映周次/有票房的周次)
首輪前 3周：票房加總、逐周平均票房衰退率、觀影人次  => 除以活躍周次，若都沒票房則剔除該部電影
首輪前 6周：票房加總、逐周平均票房衰退率、觀影人次  => 除以活躍周次，若都沒票房則為0
首輪前 9周：票房加總、逐周平均票房衰退率、觀影人次  => 除以活躍周次，若都沒票房則為0
首輪前12周：票房加總、逐周平均票房衰退率、觀影人次  => 除以活躍周次，若都沒票房則為0
首輪加總：票房、觀影人次
 - 衰退率：平均衰退率、第二周衰退率、第三周衰退率
 - 巔峰：周次、當周票房、當周衰退率、當周觀影人次


<歷史資訊>
上映總輪次(總周次/活躍周次)
歷史累計票房
歷史累計觀影人次


<再上映> 只有多輪電影才有
是否是再上映電影(若否，以下為空值)-----------
上一輪的周次(總周次/活躍周次)
上一輪的票房
上一輪的觀影人次
上一輪的間隔天數
重映的 輪次加總
重映的 上映周次(總周次/活躍周次)
重映的 累計票房
重映的 累計觀影人次
首輪與次輪的間隔天數