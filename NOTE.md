# 目前開發階段: 彙總模型訓練資料

## 待處理清單
1. 建立聚合檔 boxoffice_integrate.py、rating_integrate.py
  (1) 腳本位置src\ML_recommend\data_data_integration
  (2) 資料生成的位置data\aggregated
  (3) 生成內容: 單一電影的票房(或評分) 的逐周資料合成一個row，再把所有電影row合併成一隻綁案
  (4) 生成的檔案格式: boxoffice_agg_2025W43.csv


<已完成>
2. processed/boxoffice_permovie
  (1)資料夾結構改成跟movieInfo_gov一樣
    - 每個電影一隻檔案
    - 更新的時候直接覆蓋單一電影，再跑腳本生成combined檔
  (2) 腳本boxoffice_permovie.py要改


<已完成>
3. processed/omdb結構調整
  (1)資料夾改成
    - data/processed/movieInfo_omdb
       => 結構與更新方式比照movieInfo_gov
    - data/processed/rating_omdb
       => 結構與更新方式比照調整後的2.boxoffice_permovie
  (2) 腳本omdb_cleaner.py要改
 

<已完成>
5. 電影長度film_length轉分鐘
  (1) 處理腳本: data_cleaning\boxoffice_permovie.py 
  (2) 生成在哪: data\processed\boxoffice_permovie下的單一電影


6. 生成movie_master_builder.py 
=> 欄位引用不變，另外新增電影性質、上映狀態
=> 資料源會改變成四周檔按omdb/gov的電影資訊、聚合後的票房資訊/評分資訊


## 暫不處理



## 放棄處理
4. 標記- 電影性質(第一次/重新/復刻上映)
  (1) 處理腳本: data_cleaning\boxoffice_permovie.py 
  (2) 生成在哪: data\processed\boxoffice_permovie下的單一電影
"""
因為電影公開資料，發行日期只會顯示當下日期，因此無法判定復刻上映的情況
舉例來說
    1. 一一：這是2000初的電影，但現在發行日期是2025
    2. 樂來樂愛你：這是2016的電影，但政府公開資料分成獨立的三筆資料(三個都叫做"樂來樂愛你")
"""