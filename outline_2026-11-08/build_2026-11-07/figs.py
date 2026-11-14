import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def box(ax, x, y, w, h, text, fc, fs=8.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec="#333333", lw=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", wrap=True)

def arrow(ax, x1, y1, x2, y2, label="", lx=0, ly=0.12, both=False):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="<->" if both else "->",
                                 mutation_scale=11, lw=1.1, color="#333333"))
    if label:
        ax.text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, ha="center", fontsize=7, color="#333333",
                style="italic")

# ---------------- System architecture ----------------
fig, ax = plt.subplots(figsize=(10, 5.6))
ax.set_xlim(0, 10); ax.set_ylim(0, 5.6); ax.axis("off")

# Pod (on vehicle)
ax.add_patch(FancyBboxPatch((0.1, 0.15), 4.6, 5.2, boxstyle="round,pad=0.02", fc="#f4f7fb", ec="#5b7aa6", lw=1.2, ls="--"))
ax.text(2.4, 5.12, "PERCEPTION POD (on the vehicle)", ha="center", fontsize=9, fontweight="bold", color="#3b5b8a")
box(ax, 0.35, 3.85, 1.9, 0.95, "ESP32-CAM\nOV2640 camera\n(MJPEG over Wi-Fi)", "#dbe8f7")
box(ax, 0.35, 2.55, 1.9, 0.95, "TF-Luna LiDAR\n(front, 0.2–8 m)\n+ 2x HC-SR04", "#dbe8f7")
box(ax, 0.35, 1.25, 1.9, 0.95, "2x MPU6050 IMU\n(near the wheels,\nI2C 0x68 / 0x69)", "#dbe8f7")
box(ax, 2.6, 1.9, 1.85, 1.9, "ESP32 DevKit\n(sensor hub)\n• read sensors\n• timestamps\n• OLED + motor\n  stop override", "#fde9c9")
box(ax, 2.6, 0.35, 1.85, 0.85, "0.96\" OLED\nstate + distance", "#e6e6e6")
box(ax, 0.35, 0.35, 1.9, 0.7, "L298N driver →\n4 DC gear motors", "#e6e6e6")
arrow(ax, 2.25, 3.0, 2.6, 3.0)
arrow(ax, 2.25, 1.7, 2.6, 2.3)
arrow(ax, 3.52, 1.9, 3.52, 1.2)
arrow(ax, 2.6, 1.95, 2.25, 0.75)

# Laptop
ax.add_patch(FancyBboxPatch((5.4, 0.15), 4.45, 5.2, boxstyle="round,pad=0.02", fc="#f6faf3", ec="#5d9a4f", lw=1.2, ls="--"))
ax.text(7.62, 5.12, "EDGE PC (laptop, RTX GPU)", ha="center", fontsize=9, fontweight="bold", color="#3f7a33")
box(ax, 5.65, 3.85, 1.95, 0.95, "Hazard model\nYOLO11n\n(pothole, speed bump)", "#d9f0d9")
box(ax, 7.7, 3.85, 1.95, 0.95, "Object model\nYOLO11n (COCO)\n(person, car, bike…)", "#d9f0d9")
box(ax, 5.65, 2.45, 4.0, 1.0, "Fusion: detection box + range + IMU vibration\n→ distance to object, surface / hazard state", "#d9f0d9")
box(ax, 5.65, 1.15, 4.0, 0.95, "Decision FSM: SAFE / WARNING / STOP\n(hysteresis, fail-safe STOP if a sensor stops)", "#ffd9d9", bold=False)
box(ax, 5.65, 0.35, 4.0, 0.6, "Logging: frames, detections, latency (p50/p95/p99)", "#eeeeee", fs=8)
arrow(ax, 6.62, 3.85, 6.62, 3.45); arrow(ax, 8.67, 3.85, 8.67, 3.45)
arrow(ax, 7.65, 2.45, 7.65, 2.1)

# links
arrow(ax, 2.25, 4.32, 5.65, 4.32, "video frames (Wi-Fi)", ly=0.1)
arrow(ax, 4.45, 3.3, 5.65, 2.95, "range + IMU\n(Wi-Fi/UDP)", lx=0.0, ly=0.2)
arrow(ax, 5.65, 1.62, 4.45, 2.15, "STOP /\nWARNING", lx=0.0, ly=-0.42)
plt.tight_layout()
plt.savefig("fig/architecture.png", dpi=200)
plt.close()

# ---------------- VDI 2206 V-model ----------------
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.set_xlim(0, 9); ax.set_ylim(0, 3.6); ax.axis("off")
left = [("Requirements\n(PDS)", 0.2, 2.6), ("System design\n(concepts, architecture)", 1.0, 1.75)]
right = [("System integration\n(pod + vehicle)", 6.2, 1.75), ("Assurance of properties\n(tests vs PDS)", 7.0, 2.6)]
for t, x, y in left + right:
    box(ax, x, y, 1.8, 0.75, t, "#dbe8f7", fs=8)
box(ax, 2.95, 0.15, 3.1, 1.15, "Domain-specific design\nMechanical: sensor tower CAD, FEA, 3D print\nElectrical: wiring, power, ESP32 firmware\nSoftware / AI: dataset, YOLO, fusion, FSM", "#fde9c9", fs=7.8)
arrow(ax, 1.1, 2.6, 1.6, 2.5); arrow(ax, 1.9, 1.75, 3.1, 1.3)
arrow(ax, 5.9, 1.3, 7.1, 1.75); arrow(ax, 7.4, 2.5, 7.9, 2.6)
ax.annotate("", xy=(6.2, 2.12), xytext=(2.8, 2.12), arrowprops=dict(arrowstyle="<->", ls="--", color="#777"))
ax.text(4.5, 2.22, "verification against the design", ha="center", fontsize=7.5, color="#555")
ax.annotate("", xy=(7.0, 2.98), xytext=(2.0, 2.98), arrowprops=dict(arrowstyle="<->", ls="--", color="#777"))
ax.text(4.5, 3.08, "validation against the requirements (PDS)", ha="center", fontsize=7.5, color="#555")
ax.text(4.5, 3.45, "Modelling and analysis (latency vs stopping distance, sensor models) run alongside all stages",
        ha="center", fontsize=7.5, style="italic", color="#3b5b8a")
plt.tight_layout()
plt.savefig("fig/vmodel.png", dpi=200)
plt.close()
print("ok")
