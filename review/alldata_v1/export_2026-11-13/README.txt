Export 2026-11-13 (claude.ai session, Stage 41a).
predictions_C_ALLVAL.csv: model C (runs/detect/v3b_C_11n_960_s0_r2) on ALLVAL (1,754 images), CPU ONNX re-implementation
  of yolo val (conf>=0.001, iou 0.7, max_det 300). Boxes in pixels of the ORIGINAL image (x1,y1,x2,y2). image = file name in
  review/alldata_v1/ds/images/val (<source>__<original name>). Use conf>=0.25 to see what the vehicle would see.
classes.txt / data_names.yaml: 0 pothole, 1 speed_bump.
sr_speed_bump_val_32.zip: all 32 sr val images that have a speed_bump label (C AP50 on them = 0.000) + their YOLO labels.
pothole_sample_val_25.zip: 5 random val images with pothole labels from each of r2, rsid, bucko, sr, egy_v2 (seed 0) + labels.
Labels are YOLO format (class cx cy w h, normalised). Val labels are unchanged originals.
