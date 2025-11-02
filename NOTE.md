# 目前開發階段: 彙總模型訓練資料
## 1103 to do list
1. 完成 7-8 調整欄位(boxoffice_integrate.py)
   => ChatGPT: https://chatgpt.com/g/g-p-68b005c1aeb881919915454a65419b81/c/6907854c-fbc4-8321-bd21-ee506731bbad
2. 完成 6 生成movie_master_builder.py => 產生full+三支模型訓練資料
   => ChatGPT: https://chatgpt.com/g/g-p-68b005c1aeb881919915454a65419b81/c/6907653f-ec7c-8323-a451-d7804640985e
3. 訓練 M3 推薦模型、評估、調教
4. 訓練 M1 票房模型、評估、調教
 (先跳過M2 再上映，之後再補)


## ------------------------------------ 待處理清單 ------------------------------------
6. 生成movie_master_builder.py 
=> 欄位引用不變，另外新增電影性質、上映狀態
=> 資料源會改變成四周檔按omdb/gov的電影資訊、聚合後的票房資訊/評分資訊

7. 修改boxoffice_integrate.py
  新增以下欄位
  (1) momentum_3w
      近三週 second_week_amount_growth_rate 的平均值

  (2) same_class_amount_last_week	
      mean(total_amount ÷ total_weeks) for all films with same region（若無逐週資料，則取整體平均週票房作為近似）
      ps. 若只有最新輪，無法取得「上週」	同樣可用「同區域電影平均週票房」作近似

  (3) market_heat_level	
      依 total_amount 或 avg_amount_per_week 的分位數切級（如 Q3 = 高熱、Q2 = 中熱）

8. 要調整欄位
  (1) 棄用same_class_amount_last_week =>現在全部都是0
  (2) market_heat_level	改成
    - 上映中: 用當周票房去比
    - 下檔: 用該輪總票房去比



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