"""GP36 live perception.

Hazard YOLO11n (baseline v1) and COCO YOLO11n run on the same frame. Their
detections go into one list with namespaced labels (hazard:*, coco:*), and a
small state machine turns that list into SAFE / WARNING / STOP.
"""
