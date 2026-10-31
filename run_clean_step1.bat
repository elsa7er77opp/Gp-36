@echo off
cd /d %~dp0
echo === perception tests
venv\Scripts\python -m unittest discover -s tests -t tests -p "test_perception.py"
echo === predict val (inference only, no training, no data change)
venv\Scripts\yolo predict model=runs\detect\v3a_r1_11n_960_s0\weights\best.pt source=road_hazards_v3a_r1\images\val imgsz=960 conf=0.05 iou=0.6 save=False save_txt=True save_conf=True project=runs\clean name=pred_val_r1 verbose=False
echo === predict train
venv\Scripts\yolo predict model=runs\detect\v3a_r1_11n_960_s0\weights\best.pt source=road_hazards_v3a_r1\images\train imgsz=960 conf=0.05 iou=0.6 save=False save_txt=True save_conf=True project=runs\clean name=pred_train_r1 verbose=False
echo === DONE
