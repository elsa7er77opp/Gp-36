"""Thin wrapper around an Ultralytics model that returns namespaced detections.

Ultralytics is imported inside the constructor so the rest of the package (and
its tests) can be used on a machine without it.
"""
import time

from .types import NAMESPACES, Detection


class NamespacedDetector:
    def __init__(self, weights, ns, imgsz=640, conf=0.25, iou=0.5, classes=None,
                 expect_names=None, device=None, half=False):
        if ns not in NAMESPACES:
            raise ValueError(f"unknown namespace {ns!r}")
        from ultralytics import YOLO

        self.model = YOLO(str(weights))
        self.ns = ns
        self.names = {int(k): str(v) for k, v in self.model.names.items()}
        if expect_names is not None:
            expected = {int(k): str(v) for k, v in dict(expect_names).items()}
            if self.names != expected:
                raise ValueError(f"{weights}: class names {self.names} do not match expected {expected}")
        self.class_ids = None
        if classes:
            inv = {v: k for k, v in self.names.items()}
            missing = [c for c in classes if c not in inv]
            if missing:
                raise ValueError(f"{weights}: classes not in model: {missing}")
            self.class_ids = sorted(inv[c] for c in classes)
        self.imgsz, self.conf, self.iou = imgsz, conf, iou
        self.device, self.half = device, half

    def predict(self, frame):
        """Run on one BGR frame. Returns (detections, milliseconds incl. pre/post-processing)."""
        t0 = time.perf_counter()
        r = self.model.predict(frame, imgsz=self.imgsz, conf=self.conf, iou=self.iou, classes=self.class_ids,
                               device=self.device, half=self.half, verbose=False)[0]
        b = r.boxes
        xyxy = b.xyxy.cpu().numpy() if len(b) else []
        cls = b.cls.cpu().numpy().astype(int) if len(b) else []
        conf = b.conf.cpu().numpy() if len(b) else []
        ms = (time.perf_counter() - t0) * 1000.0
        h, w = frame.shape[:2]
        dets = [Detection(self.ns, int(c), self.names[int(c)], float(p), tuple(float(v) for v in box), (w, h))
                for box, c, p in zip(xyxy, cls, conf)]
        return dets, ms
