# 目前開發階段: 彙總模型訓練資料

## 待處理清單
1. 建立聚合檔 boxoffice_integrate.py、rating_integrate.py
  (1) 腳本位置src\ML_recommend\data_aggregated
  (2) 資料生成的位置data\integration
  (3) 生成內容: 單一電影的票房(或評分) 的逐周資料合成一個row，再把所有電影row合併成一隻綁案
  (4) 生成的檔案格式: boxoffice_agg_2025W43.csv


2. processed/boxoffice_permovie
  (1)資料夾結構改成跟movieInfo_gov一樣
    - 每個電影一隻檔案
    - 更新的時候直接覆蓋單一電影，再跑腳本生成combined檔
  (2) 腳本boxoffice_permovie.py要改


3. processed/omdb結構調整
  (1)資料夾改成
    - data/processed/movieInfo_omdb
       => 結構與更新方式比照movieInfo_gov
    - data/processed/rating_omdb
       => 結構與更新方式比照調整後的2.boxoffice_permovie
  (2) 腳本omdb_cleaner.py要改
 

4. 標記- 電影性質(第一次/重新/復刻上映)
  (1) 處理腳本: data_cleaning\boxoffice_permovie.py 
  (2) 生成在哪: data\processed\boxoffice_permovie下的單一電影


5. 電影長度film_length轉分鐘
  (1) 處理腳本: 同上 
  (2) 生成在哪: 同上


6. 生成movie_master_builder.py 
=> 欄位引用不變，另外新增電影性質、上映狀態
=> 資料源會改變成四周檔按omdb/gov的電影資訊、聚合後的票房資訊/評分資訊


## 暫不處理
