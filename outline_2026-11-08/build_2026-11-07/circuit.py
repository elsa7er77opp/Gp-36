"""Pod wiring diagram drawn with net labels (pins with the same net name are connected)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

fig, ax = plt.subplots(figsize=(13.6, 10.6))
ax.set_xlim(0, 13.6); ax.set_ylim(0, 10.6); ax.axis("off")
C = {"5V": "#c0392b", "3V3": "#d35400", "GND": "#222222", "VBAT": "#b9770e", "I2C": "#2e8b57",
     "UART": "#1f5fa8", "US": "#1f5fa8", "MOT": "#555555", "ADC": "#7d3c98", "ENC": "#7d3c98"}

def net_color(n):
    for k, v in [("GND", C["GND"]), ("+5V", C["5V"]), ("+3V3", C["3V3"]), ("VBAT", C["VBAT"]), ("SDA", C["I2C"]),
                 ("SCL", C["I2C"]), ("TF_", C["UART"]), ("US", C["US"]), ("M_", C["MOT"]), ("ADC", C["ADC"]), ("ENC", C["ENC"])]:
        if k in n:
            return v
    return "#333"

def label(x, y, net, side):
    col = net_color(net)
    w = 0.09 * len(net) + 0.18
    if side == "right":
        ax.plot([x, x + 0.25], [y, y], color=col, lw=1.3)
        ax.add_patch(FancyBboxPatch((x + 0.25, y - 0.1), w, 0.2, boxstyle="larrow,pad=0.0", fc="white", ec=col, lw=1))
        ax.text(x + 0.3 + w / 2, y, net, fontsize=6.6, color=col, va="center", ha="center", fontweight="bold")
    else:
        ax.plot([x - 0.25, x], [y, y], color=col, lw=1.3)
        ax.add_patch(FancyBboxPatch((x - 0.25 - w, y - 0.1), w, 0.2, boxstyle="rarrow,pad=0.0", fc="white", ec=col, lw=1))
        ax.text(x - 0.3 - w / 2, y, net, fontsize=6.6, color=col, va="center", ha="center", fontweight="bold")

def module(x, y, w, title, pins, side, fc, note=None):
    """pins: list of (pin_name, net). side: where the stubs go."""
    h = 0.27 * len(pins) + 0.1
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec="#222", lw=1.2))
    ax.text(x + w / 2, y + h + 0.06, title, ha="center", va="bottom", fontsize=7.8, fontweight="bold")
    for i, (p, net) in enumerate(pins):
        py = y + h - 0.05 - (i + 0.5) * 0.27
        if side == "right":
            ax.text(x + w - 0.06, py, p, fontsize=6.8, va="center", ha="right"); label(x + w, py, net, "right")
        else:
            ax.text(x + 0.06, py, p, fontsize=6.8, va="center", ha="left"); label(x, py, net, "left")
    if note:
        ax.text(x + w / 2, y - 0.06, note, fontsize=6.1, ha="center", va="top", style="italic", color="#444")

# ---------------- ESP32 DevKit ----------------
EL = [("VIN", "+5V"), ("GND", "GND"), ("3V3", "+3V3_OUT"), ("GPIO21", "SDA"), ("GPIO22", "SCL"),
      ("GPIO16 (RX2)", "TF_TX"), ("GPIO17 (TX2)", "TF_RX"), ("GPIO36 (VP, ADC)", "ADC_VBAT"),
      ("GPIO34 (in)", "ENC_L"), ("GPIO35 (in)", "ENC_R")]
ER = [("GPIO4", "US1_TRIG"), ("GPIO18", "US1_ECHO_3V3"), ("GPIO19", "US2_TRIG"), ("GPIO23", "US2_ECHO_3V3"),
      ("GPIO25 (PWM)", "M_ENA"), ("GPIO26", "M_IN1"), ("GPIO27", "M_IN2"), ("GPIO14", "M_IN3"),
      ("GPIO13", "M_IN4"), ("GPIO33 (PWM)", "M_ENB")]
ex, ey, ew = 5.5, 4.0, 2.3
eh = 0.36 * len(EL) + 0.1
ax.add_patch(Rectangle((ex, ey), ew, eh, fc="#fff3e0", ec="#222", lw=1.6))
ax.text(ex + ew / 2, ey + eh + 0.07, "ESP32 DevKit V1 (ESP32-WROOM-32)", ha="center", va="bottom", fontsize=8.8, fontweight="bold")
for i, ((pl, nl), (pr, nr)) in enumerate(zip(EL, ER)):
    py = ey + eh - 0.05 - (i + 0.5) * 0.36
    ax.text(ex + 0.06, py, pl, fontsize=6.9, va="center"); label(ex, py, nl, "left")
    ax.text(ex + ew - 0.06, py, pr, fontsize=6.9, va="center", ha="right"); label(ex + ew, py, nr, "right")

# ---------------- Left column: I2C + LiDAR + camera ----------------
module(0.6, 9.45, 1.55, "ESP32-CAM (OV2640)", [("5V", "+5V"), ("GND", "GND")], "right", "#e8f4ff")
module(0.6, 6.05, 1.55, "MPU6050 #1 – left (0x68)", [("VCC", "+3V3_OUT"), ("GND", "GND"), ("SDA", "SDA"), ("SCL", "SCL"), ("AD0", "GND")], "right", "#eef8ee")
module(0.6, 4.15, 1.55, "MPU6050 #2 – right (0x69)", [("VCC", "+3V3_OUT"), ("GND", "GND"), ("SDA", "SDA"), ("SCL", "SCL"), ("AD0", "+3V3_OUT")], "right", "#eef8ee")
module(0.6, 7.85, 1.55, "OLED SSD1306 (0x3C)", [("VCC", "+3V3_OUT"), ("GND", "GND"), ("SDA", "SDA"), ("SCL", "SCL")], "right", "#eef8ee")
module(0.6, 2.4, 1.55, "TF-Luna LiDAR (UART)", [("5V", "+5V"), ("GND", "GND"), ("TXD", "TF_TX"), ("RXD", "TF_RX")], "right", "#e8f4ff",
       note="115200 baud, 3.3 V TTL I/O")

# ---------------- Right column: ultrasonic, motor driver, encoders ----------------
module(10.95, 9.0, 1.45, "HC-SR04 #1 front-left", [("VCC", "+5V"), ("TRIG", "US1_TRIG"), ("ECHO", "US1_ECHO_5V"), ("GND", "GND")], "left", "#e8f4ff")
module(10.95, 7.4, 1.45, "HC-SR04 #2 front-right", [("VCC", "+5V"), ("TRIG", "US2_TRIG"), ("ECHO", "US2_ECHO_5V"), ("GND", "GND")], "left", "#e8f4ff")
module(10.95, 3.2, 1.45, "L298N motor driver", [("12V in", "VBAT_SW"), ("GND", "GND"), ("ENA", "M_ENA"), ("IN1", "M_IN1"), ("IN2", "M_IN2"),
       ("IN3", "M_IN3"), ("IN4", "M_IN4"), ("ENB", "M_ENB")], "left", "#fdf2e9",
       note="5V-EN jumper ON (on-board regulator)\nOUT1/2 → left motor pair, OUT3/4 → right pair")
module(10.95, 0.75, 1.45, "2x LM393 encoders", [("VCC", "+3V3_OUT"), ("DO left", "ENC_L"), ("DO right", "ENC_R"), ("GND", "GND")], "left", "#e8f4ff")

# echo dividers (drawn as small sub-circuits)
def divider(x, y, inp, out):
    ax.text(x, y, f"{inp} → 1 kΩ (series) → {out} → 2 kΩ → GND", fontsize=6.8, color=C["US"])
divider(5.0, 9.6, "US1_ECHO_5V", "US1_ECHO_3V3")
divider(5.0, 9.25, "US2_ECHO_5V", "US2_ECHO_3V3")
ax.text(7.3, 9.1, "echo level shift: 5 V × 2k/(1k+2k) = 3.3 V", fontsize=6.3, color=C["US"], ha="center", va="top", style="italic")

# ---------------- Power tree (bottom) ----------------
py = 0.55
def pbox(x, w, t, fc="#fdecea"):
    ax.add_patch(Rectangle((x, py - 0.3), w, 0.6, fc=fc, ec="#222")); ax.text(x + w / 2, py, t, ha="center", va="center", fontsize=6.8)
pbox(2.7, 1.25, "2S 18650 pack\n7.4 V (6.0–8.4 V)")
pbox(4.2, 0.95, "2S BMS\n8.4 V / 5 A")
pbox(5.4, 0.8, "ON/OFF\n(main switch)")
pbox(6.45, 1.15, "LM2596 buck\nset to 5.0 V, 3 A")
for a, b in [(3.95, 4.2), (5.15, 5.4), (6.2, 6.45)]:
    ax.plot([a, b], [py, py], color=C["VBAT"], lw=1.6)
label(7.6, py, "+5V", "right")
ax.plot([6.32, 6.32], [py + 0.3, py + 0.55], color=C["VBAT"], lw=1.4)
label(6.32, py + 0.55, "VBAT_SW", "right")
ax.text(2.7, py + 0.72, "Battery sense: VBAT_SW → 10 kΩ → ADC_VBAT → 4.7 kΩ → GND   (8.4 V × 4.7/14.7 = 2.69 V)", fontsize=6.8, color=C["ADC"])
ax.text(2.7, py - 0.42, "All GND nets are one common ground (battery −, buck −, ESP32, sensors, L298N).", fontsize=6.4, style="italic")

ax.text(0.6, 2.02, "Notes: the ESP32-CAM sends video to the laptop over Wi-Fi (MJPEG), with a 1000 µF/16 V capacitor across its 5V–GND.\nI2C bus (SDA/SCL): 4.7 kΩ pull-ups are already on the GY-521 (MPU6050) boards.", fontsize=6.6, style="italic", va="top")
ax.text(0.1, 10.45, "Pod wiring diagram – Project 36 (net labels: pins with the same name are connected)", fontsize=10.5, fontweight="bold")
ax.text(5.5 + 1.15, 3.8, "Not used: strapping pins GPIO0, 2, 5, 12, 15\nGPIO34/35/36 are input-only", fontsize=6.3, ha="center", va="top", style="italic")
plt.savefig("fig/circuit.png", dpi=190, bbox_inches="tight")
print("ok")
