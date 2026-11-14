import datetime as dt
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

D = lambda s: dt.date(2026 if s[3:] in ("Oct", "Nov", "Dec") else 2027,
                      ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].index(s[3:]) + 1, int(s[:2]))
# id, task, start, end, outcome, critical, status (done/prog/plan/buffer/ms)
T = [
 ("0","PHASE 1 – REQUIREMENTS AND RESEARCH",None,None,"",0,"head"),
 ("1.1","Allocation, brief, first meetings","05-Oct","11-Oct","Signed W3 logbook",0,"done"),
 ("1.2","Literature search and paper summaries","12-Oct","25-Oct","13 papers summarised",0,"done"),
 ("1.3","Datasets and repositories survey","19-Oct","25-Oct","Dataset list + licences",0,"done"),
 ("1.4","Component selection (decision matrices)","19-Oct","29-Oct","Items sheet (27 lines)",1,"done"),
 ("1.5","PDS, concepts, architecture","26-Oct","07-Nov","PDS + selected concept",1,"done"),
 ("1.6","Write Project Outline","26-Oct","08-Nov","Outline document",1,"prog"),
 ("M1","Project Outline submitted","08-Nov","08-Nov","Canvas submission",1,"ms"),
 ("0","PHASE 2 – AI DEVELOPMENT (started early)",None,None,"",0,"head"),
 ("2.1","Dataset audit, leak-free split, baseline","29-Oct","04-Nov","Test mAP50 baseline",0,"done"),
 ("2.2","Live pipeline (2 models + FSM) + tests","30-Oct","05-Nov","26 tests pass, latency",0,"done"),
 ("2.3","Multi-source dataset v3b + experiments","02-Nov","15-Nov","Val P/R/mAP50 per class",0,"prog"),
 ("2.4","Model selection on val + one test run","16-Nov","29-Nov","Frozen hazard model v2",0,"plan"),
 ("0","PHASE 3 – HARDWARE (MECHANICAL AND ELECTRICAL)",None,None,"",0,"head"),
 ("G1","Gate: vehicle + components confirmed","15-Nov","15-Nov","Lab car + PTO approval",1,"ms"),
 ("3.1","Order follow-up with PTO (before Xmas)","09-Nov","22-Nov","Parts received",1,"plan"),
 ("3.2","Sensor tower CAD (SolidWorks)","16-Nov","29-Nov","CAD + drawings",1,"plan"),
 ("3.3","Schematic, I/O list, power budget","16-Nov","29-Nov","Schematic + budget",0,"plan"),
 ("3.4","Simple FEA check of the mount (SolidWorks)","30-Nov","06-Dec","Max stress + deflection",0,"plan"),
 ("3.5","3D print + mount pod on the vehicle","30-Nov","13-Dec","Assembled pod",1,"plan"),
 ("3.6","Sensor drivers (TF-Luna, HC-SR04, IMU, OLED)","23-Nov","06-Dec","Live readings logged",1,"plan"),
 ("3.7","Vehicle interface (ESP32 + L298N, stop)","30-Nov","13-Dec","Remote drive + stop",1,"plan"),
 ("3.8","ESP32-CAM streaming + latency test","30-Nov","13-Dec","End-to-end latency (ms)",1,"plan"),
 ("3.9","Project week: pod test drives + IMU data","13-Dec","18-Dec","Labelled IMU/video logs",1,"plan"),
 ("B1","Christmas closure (buffer)","21-Dec","03-Jan","",0,"buffer"),
 ("0","PHASE 4 – PROGRESS REVIEW",None,None,"",0,"head"),
 ("4.1","Literature review chapter draft","04-Jan","17-Jan","Draft chapter",1,"plan"),
 ("4.2","Progress Review slides + updated Gantt","18-Jan","24-Jan","Slides + logbook",1,"plan"),
 ("M2","Progress Review submitted","24-Jan","24-Jan","Canvas submission",1,"ms"),
 ("0","PHASE 5 – FUSION, INTEGRATION AND MODELLING",None,None,"",0,"head"),
 ("5.1","IMU surface / bump classification","25-Jan","07-Feb","Accuracy + confusion matrix",1,"plan"),
 ("5.2","Sensor alignment + time stamps","08-Feb","21-Feb","Alignment check, synced logs",0,"plan"),
 ("5.3","Fusion + FSM with real sensors","15-Feb","28-Feb","Fused warnings working",1,"plan"),
 ("5.4","Hazard model on pod footage (fine-tune)","01-Mar","14-Mar","Pod-domain val results",0,"plan"),
 ("5.5","Simulink: latency vs stopping distance","01-Mar","07-Mar","Max safe speed",0,"plan"),
 ("5.6","Full integration (pod + vehicle + laptop)","08-Mar","21-Mar","End-to-end demo",1,"plan"),
 ("G2","Gate: integrated system working","21-Mar","21-Mar","Demo to supervisor",1,"ms"),
 ("0","PHASE 6 – TESTING AND REPORT",None,None,"",0,"head"),
 ("6.1","Benchmark tests (light, speed, angle)","22-Mar","04-Apr","Results vs PDS",1,"plan"),
 ("6.2","Fix issues + repeat tests","05-Apr","11-Apr","Updated results",0,"plan"),
 ("B2","Buffer","12-Apr","17-Apr","",0,"buffer"),
 ("6.3","Project week: final tests + demo video","18-Apr","22-Apr","Final results + video",1,"plan"),
 ("6.4","Report: methodology + results chapters","29-Mar","11-Apr","Chapters drafted",1,"plan"),
 ("6.5","Report: discussion, conclusion, PM/QM","12-Apr","25-Apr","Full draft",1,"plan"),
 ("6.6","Final edit, slides, poster, paper draft","19-Apr","02-May","Final documents",1,"plan"),
 ("M3","Report + slides submitted","04-May","04-May","Canvas submission",1,"ms"),
 ("M4","Project defence","04-May","13-May","Defence + demo",1,"plan"),
]
json.dump(T, open("gantt_tasks.json", "w"))

rows = list(reversed(T))
fig, ax = plt.subplots(figsize=(15.5, 10.2))
col = {"done": "#7f8c8d", "prog": "#f0a830", "plan": "#4a78b5", "buffer": "#cfcfcf"}
for i, (tid, name, s, e, out, crit, st) in enumerate(rows):
    if st == "head":
        ax.text(dt.date(2026, 10, 5), i, name, va="center", fontsize=7.6, fontweight="bold", color="#1f3864")
        continue
    sd, ed = D(s), D(e) + dt.timedelta(days=1)
    if st == "ms":
        ax.plot(sd, i, marker="D", ms=8, color="#c0392b" if crit else "#333", zorder=3)
    else:
        c = col[st]
        if st == "plan" and crit:
            c = "#c0392b"
        ax.barh(i, (ed - sd).days, left=sd, height=0.62, color=c, edgecolor="#333" if crit else "none", lw=0.6,
                hatch="//" if st == "buffer" else None)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([("" if r[6] == "head" else f"{r[0]}  {r[1]}") for r in rows], fontsize=7.4)
ax.set_xlim(dt.date(2026, 10, 5), dt.date(2027, 5, 16))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
plt.setp(ax.get_xticklabels(), rotation=60, fontsize=7)
ax.grid(axis="x", ls=":", alpha=0.6)
ax.axvline(dt.date(2026, 11, 8), color="#2e8b57", lw=1.4, ls="--")
ax.text(dt.date(2026, 11, 10), 9, "Today\n(8 Nov 2026)", color="#2e8b57", fontsize=8)
ax.set_ylim(-0.8, len(rows) - 0.2)
leg = [Patch(color="#7f8c8d", label="Completed"), Patch(color="#f0a830", label="In progress"),
       Patch(color="#c0392b", label="Planned – critical path"), Patch(color="#4a78b5", label="Planned – not critical"),
       Patch(facecolor="#cfcfcf", hatch="//", label="Buffer"),
       Line2D([], [], marker="D", color="#c0392b", ls="", label="Milestone / decision gate")]
ax.legend(handles=leg, loc="lower left", fontsize=7.5, ncol=3, frameon=True)
ax.set_title("Gantt chart v2 (updated 8 Nov 2026) – Project 36 Perception Pod", fontsize=11, fontweight="bold")
plt.tight_layout()
plt.savefig("fig/gantt.png", dpi=170)
print("ok", len(T))
