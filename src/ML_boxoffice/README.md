# ML_boxoffice Pipeline 配置

project_name: "ML_boxoffice"
description: "週票房與觀眾數預測"

# 資料路徑
data_paths:
  raw: "data/raw"
  processed: "data/processed"
  phase1_output: "data/ML_boxoffice/phase1_flattened"
  phase2_output: "data/ML_boxoffice/phase2_features"
  phase3_output: "data/ML_boxoffice/phase3_train_ready"
  phase4_output: "data/ML_boxoffice/phase4_model"

# Pipeline 階段
phases:
  phase1:
    name: "flatten_timeseries"
    script: "src/ML_boxoffice/phase1_flatten/flatten_timeseries.py"
    input:
      - "data/processed/boxoffice_permovie/*.csv"
      - "data/processed/movieInfo_gov/combined/*.csv"
    output: "data/ML_boxoffice/phase1_flattened/boxoffice_timeseries_{date}.csv"
  
  phase2:
    name: "feature_engineering"
    scripts:
      - "src/ML_boxoffice/phase2_features/add_pr_features.py"
      - "src/ML_boxoffice/phase2_features/add_cumulative_features.py"
    base_input: "phase1_output"
  
  phase3:
    name: "prepare_training"
    script: "src/ML_boxoffice/phase3_prepare/build_training_data.py"
  
  phase4:
    name: "train_models"
    models:
      - M1_predict_boxoffice
      - M2_predict_audience

# 模型配置
models:
  M1_predict_boxoffice:
    target: "amount"
    features: ["base", "pr", "cumulative"]
  
  M2_predict_audience:
    target: "tickets"
    features: ["base", "pr", "cumulative"]