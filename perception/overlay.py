"""Drawing helpers for the live view. Labels are drawn inside the box, so they never cover other objects."""
import cv2

COLORS = {"hazard": (0, 140, 255), "coco": (255, 200, 0)}
STATE_COLORS = {"SAFE": (0, 170, 0), "WARNING": (0, 200, 255), "STOP": (0, 0, 230)}


def draw(frame, dets, state, reasons, corridor_x, info=""):
    h, w = frame.shape[:2]
    for x in corridor_x:
        cv2.line(frame, (int(x * w), int(0.4 * h)), (int(x * w), h), (180, 180, 180), 1)
    for d in dets:
        x1, y1, x2, y2 = (int(v) for v in d.xyxy)
        c = COLORS.get(d.ns, (255, 255, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), c, 2)
        cv2.putText(frame, f"{d.label} {d.conf:.2f}", (x1 + 3, y1 + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1,
                    cv2.LINE_AA)
    cv2.rectangle(frame, (0, 0), (w, 34), STATE_COLORS[state], -1)
    cv2.putText(frame, f"{state}  {info}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    if reasons:
        cv2.putText(frame, reasons[0][:80], (8, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.55, STATE_COLORS[state], 2,
                    cv2.LINE_AA)
    return frame
