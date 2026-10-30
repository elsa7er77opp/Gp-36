"""
GP36 - Step 2: train YOLOv8 on the road-hazard dataset (pothole, speed_bump).

Transfer learning: start from YOLOv8n pre-trained on COCO (80 classes incl. person,
car, bicycle) and fine-tune it on our two new classes.

Usage (Linux / Windows / Google Colab):
    pip install ultralytics
    python train.py --data road_hazards/data.yaml --epochs 50 --imgsz 640
    (add --device 0 if an NVIDIA GPU is available)
"""
import argparse
from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="road_hazards/data.yaml")
    ap.add_argument("--model", default="yolov8n.pt", help="yolov8n.pt (fast) or yolov8s.pt (more accurate)")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--device", default="cpu", help="cpu or 0 for the first GPU")
    ap.add_argument("--name", default="gp36_road_hazards")
    args = ap.parse_args()

    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        name=args.name,
        patience=15,          # stop early if val mAP does not improve for 15 epochs
        seed=0,
        # augmentation suited to road images taken from a moving vehicle
        hsv_v=0.5,            # brightness changes (sun / shade)
        degrees=3.0,          # small camera tilt
        fliplr=0.5,           # left/right flip
        mosaic=1.0,
        close_mosaic=5,
        plots=True,
    )
    metrics = model.val(data=args.data, split="test", plots=True, name=args.name + "_test")
    print(f"TEST  mAP50 = {metrics.box.map50:.3f}   mAP50-95 = {metrics.box.map:.3f}")
    print(f"      precision = {metrics.box.mp:.3f}   recall = {metrics.box.mr:.3f}")


if __name__ == "__main__":
    main()
