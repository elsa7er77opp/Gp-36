const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, BorderStyle, Header, Footer, PageNumber, PageBreak, LevelFormat, TabStopType,
  TabStopPosition, PageOrientation, VerticalAlign,
} = require('docx');

const FONT = 'Arial';
const SZ = 20; // 10 pt
const pages = fs.existsSync('pages.json') ? JSON.parse(fs.readFileSync('pages.json')) : {};
const sizes = JSON.parse(fs.readFileSync('sizes.json'));

// ---------- helpers ----------
const r = (t, o = {}) => new TextRun({ text: t, font: FONT, size: SZ, ...o });
const P = (runs, o = {}) => new Paragraph({ spacing: { after: 100, line: 264 }, alignment: AlignmentType.JUSTIFIED, ...o,
  children: (Array.isArray(runs) ? runs : [runs]).map(x => typeof x === 'string' ? r(x) : x) });
// rich text: **bold** segments
const T = (s, o = {}) => P(s.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map(x => x.startsWith('**') ? r(x.slice(2, -2), { bold: true }) : r(x)), o);
const B = (s, lvl = 0) => new Paragraph({ numbering: { reference: 'bul', level: lvl }, spacing: { after: 50, line: 252 },
  children: s.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map(x => x.startsWith('**') ? r(x.slice(2, -2), { bold: true }) : r(x)) });
const H1 = (n, t) => new Paragraph({ spacing: { before: 240, after: 120 }, keepNext: true,
  children: [new TextRun({ text: `${n}\t${t}`, font: FONT, size: 26, bold: true })], tabStops: [{ type: TabStopType.LEFT, position: 567 }] });
const H2 = (n, t) => new Paragraph({ spacing: { before: 160, after: 80 }, keepNext: true,
  children: [new TextRun({ text: `${n}\t${t}`, font: FONT, size: 22, bold: true })], tabStops: [{ type: TabStopType.LEFT, position: 567 }] });
let figN = 0, tabN = 0;
const figs = [], tabs = [];
function IMG(file, widthPx, caption) {
  const [w, h] = sizes[file];
  const height = Math.round(h * widthPx / w);
  figN += 1; figs.push(`Figure ${figN}: ${caption}`);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 40 }, keepNext: true,
      children: [new ImageRun({ type: 'jpg', data: fs.readFileSync('fig/' + file), transformation: { width: widthPx, height } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 140 },
      children: [r(`Figure ${figN}: ${caption}`, { italics: true, size: 18 })] }),
  ];
}
function TCAP(caption) {
  tabN += 1; tabs.push(`Table ${tabN}: ${caption}`);
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100, after: 60 }, keepNext: true,
    children: [r(`Table ${tabN}: ${caption}`, { italics: true, size: 18 })] });
}
const bd = { style: BorderStyle.SINGLE, size: 4, color: '808080' };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
function TABLE(rows, widths, opt = {}) {
  const fs_ = opt.size || 16;
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((row, i) => new TableRow({ tableHeader: i === 0, cantSplit: true, children: row.map((c, j) => {
      const txt = typeof c === 'object' ? c.t : String(c);
      const fill = i === 0 ? 'D9E2F3' : (typeof c === 'object' && c.fill) ? c.fill : undefined;
      return new TableCell({ borders, width: { size: widths[j], type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
        shading: fill ? { fill, type: ShadingType.CLEAR, color: 'auto' } : undefined,
        margins: { top: 30, bottom: 30, left: 70, right: 70 },
        children: txt.split('\n').map(line => new Paragraph({ spacing: { after: 0, line: 230 },
          alignment: (opt.center && j > 0) ? AlignmentType.CENTER : AlignmentType.LEFT,
          children: [r(line, { size: fs_, bold: i === 0 || (typeof c === 'object' && c.bold) })] })) });
    }) })),
  });
}
const sp = (n = 60) => new Paragraph({ spacing: { after: n }, children: [] });
const pg = (k) => (pages[k] !== undefined ? String(pages[k]) : '#');
const tocLine = (text, key, indent = 0, bold = false) => new Paragraph({ spacing: { after: 30 }, indent: { left: indent },
  tabStops: [{ type: TabStopType.RIGHT, position: 9600, leader: 'dot' }],
  children: [r(text, { bold }), r('\t' + pg(key), { bold })] });

// ---------- content ----------
const W = 9638; // content width (A4, 2 cm margins)

const title = [
  new Paragraph({ spacing: { before: 600, after: 120 }, alignment: AlignmentType.CENTER, children: [r('PROJECT OUTLINE', { size: 32, bold: true })] }),
  new Paragraph({ spacing: { after: 600 }, alignment: AlignmentType.CENTER, children: [r('BEng (Hons) Mechatronics Engineering', { size: 24 })] }),
  new Paragraph({ spacing: { after: 600 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: 'AI-Powered Multi-Modal Perception System for Autonomous Micro-Mobility Environmental Awareness', font: 'Arial', size: 42, bold: true })] }),
  new Paragraph({ spacing: { after: 80 }, alignment: AlignmentType.CENTER, children: [r('Graduation Project 36', { size: 24 })] }),
  sp(500),
  TABLE([
    ['Name', 'Ahmed Mohamed Elsayed Elreefy'],
    ['Student ID (UH)', '23022692'],
    ['SRN (GAF)', '202301376'],
    ['Supervisor', 'Dr. Peter Makeen'],
    ['Module', '6FTC2038 BEng Individual Project'],
    ['Date', '8 November 2026'],
  ].map((x, i) => i === 0 ? [{ t: x[0], fill: 'FFFFFF', bold: true }, { t: x[1], fill: 'FFFFFF' }] : [{ t: x[0], bold: true }, x[1]]), [2800, 5000], { size: 22 }),
  new Paragraph({ children: [new PageBreak()] }),
];

const toc = () => [
  new Paragraph({ spacing: { after: 160 }, children: [r('TABLE OF CONTENTS', { size: 26, bold: true })] }),
  tocLine('1   INTRODUCTION', 'h1', 0, true),
  tocLine('1.1   Project Background and Justification', 'h11', 300),
  tocLine('1.2   Project Aim and Objectives', 'h12', 300),
  tocLine('1.3   Product Design Specification (PDS)', 'h13', 300),
  tocLine('1.4   Methodology (VDI 2206)', 'h14', 300),
  tocLine('1.5   Concept Generation and Selection', 'h15', 300),
  tocLine('1.6   System Architecture and Circuit', 'h16', 300),
  tocLine('1.7   Health, Safety and Ethics', 'h17', 300),
  tocLine('1.8   Sustainability Analysis', 'h18', 300),
  tocLine('2   SOURCES OF INFORMATION', 'h2', 0, true),
  tocLine('3   RESOURCE ANALYSIS', 'h3', 0, true),
  tocLine('4   PROJECT PLAN', 'h4', 0, true),
  tocLine('4.1   Project Work Description and Progress to Date', 'h41', 300),
  tocLine('4.2   Critical Path Analysis', 'h42', 300),
  tocLine('4.3   Threats and Contingency Plan', 'h43', 300),
  tocLine('5   REFERENCES', 'h5', 0, true),
  tocLine('APPENDIX A: Gantt Chart', 'hA', 0, true),
  tocLine('APPENDIX B: Project Resources Checklist', 'hB', 0, true),
  tocLine('APPENDIX C: Project Risk, Ethics and Threat Assessment Checklist', 'hC', 0, true),
  tocLine('APPENDIX D: Pod Wiring Diagram', 'hD', 0, true),
  sp(200),
  new Paragraph({ spacing: { after: 120 }, children: [r('TABLE OF FIGURES', { size: 26, bold: true })] }),
  ...FIGLIST.map((f, i) => tocLine(f, 'f' + (i + 1), 0)),
  sp(120),
  new Paragraph({ spacing: { after: 120 }, children: [r('LIST OF TABLES', { size: 26, bold: true })] }),
  ...TABLIST.map((f, i) => tocLine(f, 't' + (i + 1), 0)),
  new Paragraph({ children: [new PageBreak()] }),
];

const body = [];
const add = (...x) => body.push(...x.flat());

// ===== 1 INTRODUCTION =====
add(H1('1', 'INTRODUCTION'));
add(H2('1.1', 'Project Background and Justification'));
add(T('Electric micro-mobility vehicles such as e-scooters, small delivery robots and personal mobility pods are now common in many cities, and they share the road with pedestrians, cars and a road surface that is not always in good condition. A small vehicle is much more affected by potholes and speed bumps than a car, and its rider or its control system has very little time to react. Most low-cost safety systems use a single sensor. An ultrasonic sensor alone cannot tell a soft bush from a solid wall, and a camera alone can fail in poor lighting or when the lens is blocked, so the brief of this project asks for a module that combines several sensors.'));
add(T('A review of perception for intelligent two-wheelers by Hassanin et al. (2025) found fewer than ten e-scooter detection studies in three years, small datasets, and weak performance at night, and it named multi-modal fusion as a future direction. Existing systems that do work are expensive: Zheng et al. (2025) used an Intel RealSense depth camera on an e-scooter, and Barua and Hitosugi (2025) used thermal and stereo cameras on an NVIDIA Jetson AGX Orin. On the other hand, the low-cost ESP32-CAM and ultrasonic system of Aniobi (2024) had a delay of about 715 ms, which is too slow for a moving vehicle. There is therefore a gap for a **low-cost, modular perception pod** that can detect obstacles and road hazards, measure their distance and give a clear safety decision in real time.'));
add(T('The expected benefits are a cheap and re-usable "perception pod" that can be mounted on different small vehicles, a documented and leak-free dataset and model for potholes and speed bumps, and measured results (accuracy, latency and distance error) that can be compared with the literature. The work also supports the safety of micro-mobility users in local conditions, where unmarked speed bumps and potholes are very common.'));

add(H2('1.2', 'Project Aim and Objectives'));
add(T('**Aim:** To design, build and evaluate a low-cost multi-modal perception pod (camera, LiDAR and ultrasonic range sensors, and IMU) for a small micro-mobility vehicle that detects obstacles and road hazards (pedestrians, vehicles, potholes and speed bumps), estimates their distance and outputs SAFE / WARNING / STOP decisions in real time.'));
add(T('**Objectives** (each one is linked to the PDS in Table 1 and to the Gantt chart in Appendix A):'));
add(B('**O1** – Produce a Product Design Specification, generate and select a system concept and define the system architecture (by 8 Nov 2026; Table 1).'));
add(B('**O2** – Build a labelled, leak-free road hazard dataset (potholes and speed bumps) from public sources and train a YOLO detector, reporting precision, recall, mAP50 and accuracy for each class separately (model frozen by 29 Nov 2026, fine-tuned on pod footage by 14 Mar 2027; R1–R3).'));
add(B('**O3** – Design (SolidWorks), check with a simple static FEA and 3D-print a sensor tower that holds the ESP32-CAM, TF-Luna LiDAR, two HC-SR04 sensors, two MPU6050 IMUs and an OLED, and mount it on the lab vehicle (by 13 Dec 2026; R11, R15).'));
add(B('**O4** – Implement the sensor firmware and the Wi-Fi link to the laptop, and measure the end-to-end latency from camera frame to decision (by 13 Dec 2026; R5, R6, R8).'));
add(B('**O5** – Develop the fusion algorithm and the SAFE / WARNING / STOP state machine using detections, range and IMU vibration, including an IMU-based surface and bump classifier (by 7 Mar 2027; R7, R9).'));
add(B('**O6** – Integrate and validate the whole system against the PDS under different lighting, speeds (0.3–1 m/s) and approach angles, and report PR curves, confusion matrices and latency tables (by 22 Apr 2027; R4, R10, R12).'));

add(H2('1.3', 'Product Design Specification (PDS)'));
add(T('Table 1 lists the main requirements. D = demand (must be met), W = wish. Each requirement has a test, so it can be verified in the "assurance of properties" stage of the V-model.'));
add(TCAP('Product Design Specification'));
add(TABLE([
  ['ID', 'Requirement', 'Target value', 'D/W', 'Verification test'],
  ['R1', 'Hazard and object classes', 'Pothole, speed bump; person, bicycle, car, motorcycle, bus, truck, dog', 'D', 'Model output check'],
  ['R2', 'Hazard detection accuracy (per class, leak-free test set)', 'P, R, mAP50 and accuracy reported per class (D); mAP50 ≥ 0.70 (W); 0.90 supervisor target (W)', 'D/W', 'One evaluation per final model; P, R, mAP50, accuracy per class'],
  ['R3', 'Speed-bump recall at the chosen threshold', '≥ 0.80', 'W', 'Validation set, threshold chosen on val only'],
  ['R4', 'Distance measurement error (0.2–3 m)', '≤ ±6 cm (TF-Luna datasheet accuracy)', 'D', 'Tape-measure test at 0.5, 1, 2, 3 m'],
  ['R5', 'End-to-end latency (frame to decision)', '≤ 300 ms (D); ≤ 150 ms (W), p95', 'D/W', 'Time-stamped logs, 1,000 frames'],
  ['R6', 'Processing rate', '≥ 5 frames per second (D); ≥ 10 (W)', 'D/W', 'Logged FPS during driving'],
  ['R7', 'Decision thresholds', 'STOP < 0.5 m, WARNING < 2.0 m in the path', 'D', 'Bench test with a box at set distances'],
  ['R8', 'Fail-safe', 'STOP within 1 s if any stream or sensor stops', 'D', 'Unplug / Wi-Fi off test'],
  ['R9', 'IMU surface / bump classification', '≥ 85 % accuracy (bump, pothole, smooth)', 'W', 'Labelled drives, confusion matrix'],
  ['R10', 'Operating conditions', 'Day, dusk and indoor light; speed up to 1 m/s', 'D', 'Test matrix: light × speed × angle'],
  ['R11', 'Mass and size of the pod', '≤ 1 kg; fits a 20 × 12 cm deck', 'D', 'Scale and measurement'],
  ['R12', 'Battery life', '≥ 30 min from a 2S 2600 mAh pack', 'D', 'Continuous run test'],
  ['R13', 'Cost of components', '≤ 5,400 EGP (component sheet)', 'D', 'Items sheet total'],
  ['R14', 'Outputs', 'OLED: state, nearest object, distance; Wi-Fi telemetry log', 'D', 'Inspection'],
  ['R15', 'Safety and data', 'Main power switch; Class 1 laser; no identifiable people stored', 'D', 'Inspection, data audit'],
], [640, 2380, 2810, 650, 3158]));
add(sp(80));

add(H2('1.4', 'Methodology (VDI 2206)'));
add(T('The project follows the VDI 2206 V-model for mechatronic systems (VDI, 2021), which was also used in the Integrated Engineering Systems Design module. The left side of the V goes from requirements to system design and then to domain-specific design (mechanical, electrical and software/AI). The right side integrates the domains and checks the result against the design and the PDS (Figure 1). Modelling and analysis, such as a latency versus stopping-distance model in Simulink and an FEA of the mount, run beside these stages.'));
add(...IMG('vmodel.jpg', 520, 'VDI 2206 V-model as applied to the perception pod'));
add(T('For the AI part, a strict evaluation method is used: the data is split by video or recording group, so frames from one drive never appear in both training and test; near-duplicate images are removed with image hashing (also under flips and rotations); the model and thresholds are chosen on the validation set only; and the test set is used once per final model. Precision, recall, mAP50 and accuracy are always reported per class. This method was adopted after an audit showed that the first test mAP50 of 0.69 was inflated (42 test images were identical to training images and 100 were near-duplicates), so those numbers were withdrawn. The corrected results are in Section 4.1 (Table 7).'));

add(H2('1.5', 'Concept Generation and Selection'));
add(T('A morphological chart (Table 2) was used to list solution options for each main function. Four concepts were then built from different combinations.'));
add(TCAP('Morphological chart (selected options of Concept A in bold)'));
add(TABLE([
  ['Function', 'Option 1', 'Option 2', 'Option 3', 'Option 4'],
  ['Capture image', { t: 'ESP32-CAM (Wi-Fi)', bold: true }, 'Pi Camera 3', 'USB webcam', 'RGB-D camera (RealSense)'],
  ['Measure range', { t: 'TF-Luna LiDAR + 2× HC-SR04', bold: true }, 'HC-SR04 only', 'VL53L1X ToF', 'Stereo / depth camera'],
  ['Sense vibration', { t: '2× MPU6050', bold: true }, 'MPU9250', 'BNO055', 'None'],
  ['Run the AI model', { t: 'Laptop GPU via Wi-Fi', bold: true }, 'Raspberry Pi 5 + AI HAT+', 'Jetson Orin Nano', 'ESP32 only (TinyML)'],
  ['Fuse the data', { t: 'Decision-level rules + FSM', bold: true }, 'Feature-level fusion', 'Learned fusion network', '—'],
  ['Show the output', { t: 'OLED + Wi-Fi telemetry', bold: true }, 'Buzzer and LEDs', 'Phone app', '—'],
], [1700, 2050, 1960, 1960, 1968]));
add(T('**Concept A – low-cost offload:** ESP32-CAM, TF-Luna and ultrasonic sensors, MPU6050, AI on the laptop over Wi-Fi. **Concept B – all on board:** Pi Camera 3, TF-Luna, MPU6050 and a Raspberry Pi 5 with an AI HAT+. **Concept C – depth camera:** RealSense D435i (RGB-D and IMU) on a Jetson Orin Nano, similar to Zheng et al. (2025). **Concept D – ESP32 only:** ESP32-CAM running a tiny model, with HC-SR04 and MPU6050.'));
add(T('The concepts were scored from 1 to 5 against weighted criteria taken from the PDS (Table 3). The weights follow the importance of each requirement: accuracy and latency come from R2 and R5, cost from R13, and the risk of late or unavailable parts from the critical path. Each component inside the selected concept was also chosen with its own reference-based decision matrix (camera, range sensor, IMU, processing, motor driver, platform and regulator).'));
add(TCAP('Weighted evaluation of the four concepts (score 1–5)'));
add(TABLE([
  ['Criterion (PDS link)', 'Weight', 'A – Offload', 'B – On board', 'C – Depth cam', 'D – ESP32 only'],
  ['Detection accuracy (R2)', '25 %', '5', '4', '5', '1'],
  ['Latency (R5, R6)', '20 %', '4', '4', '5', '2'],
  ['Cost within budget (R13)', '20 %', '5', '1', '1', '5'],
  ['Parts availability / development risk', '15 %', '4', '3', '2', '2'],
  ['Independent of external PC', '10 %', '2', '5', '5', '5'],
  ['Power and mass (R11, R12)', '10 %', '4', '3', '2', '5'],
  [{ t: 'Weighted total', bold: true }, '100 %', { t: '4.25', bold: true, fill: 'E2EFDA' }, '3.25', '3.45', '2.95'],
], [3100, 900, 1400, 1400, 1400, 1438], { center: true }));
add(T('**Concept A was selected.** It gives the best accuracy and speed for the lowest cost, because the laptop GPU can run full YOLO models (the full pipeline with both models was measured at 35.8 ms per frame (median) on the laptop, about 28 frames per second). Its weakness is the dependence on Wi-Fi and an external PC, so latency is a demand in the PDS and the fail-safe STOP (R8) covers a lost link. Concept B is kept as the upgrade path if on-board processing is needed later.'));

add(H2('1.6', 'System Architecture and Circuit'));
add(T('Figure 2 shows the selected architecture. The ESP32-CAM streams video to the laptop, where two YOLO11n models run on the same frame: a hazard model trained in this project and a pretrained COCO model for people and vehicles. The ESP32 DevKit is the sensor hub on the vehicle: it reads the TF-Luna (UART), the two HC-SR04 sensors and the two MPU6050 IMUs and OLED (I2C), sends the readings to the laptop, and can stop the motors through the L298N driver when a STOP flag arrives or the link is lost. Fusion is done at decision level, which is the lightest method for low-cost hardware (Yeong et al., 2021): the detection box gives the class and direction, the range sensor gives the distance, and the IMU confirms bumps and rough surfaces. The full pin-level wiring with the power supply is given in Appendix D.'));
add(...IMG('architecture.jpg', 600, 'System architecture of the perception pod and the edge PC'));
add(T('The vehicle is a four-wheel-drive two-deck acrylic robot car from the university lab (Figure 3), requested from the lab engineer. It has DC gear motors with accessible wires and enough deck space for the sensor tower, so it meets the platform requirements of the component sheet.'));
add(...IMG('platform.jpg', 330, 'Four-wheel-drive lab robot car to be used as the test vehicle'));

add(H2('1.7', 'Health, Safety and Ethics'));
add(T('**Health and safety.** The main hazards and controls are: (1) Li-ion 18650 cells – a 2S BMS protects against over-charge, over-discharge and short circuit; charging only with the 8.4 V charger and under supervision. (2) Moving vehicle – speed limited to about 1 m/s, a main power switch and a software STOP, tests only in the lab or a closed area of the campus, never on public roads. (3) Soldering and 3D printing – done in the lab with ventilation, heat-resistant mat and lead-free solder. (4) TF-Luna LiDAR – a Class 1 eye-safe laser product (IEC 60825-1), the sensor is still not looked into at close range. (5) Electrical – all voltages are below 9 V. A risk assessment of these hazards is given in Appendix C.'));
add(T('**Ethics.** The project does not involve measurements on human subjects or questionnaires (Appendix C, Q8–Q10 are "No"). People and vehicles are detected with a pretrained COCO model, so images of people are not collected for training. Road hazard images come from public datasets with open licences (for example CC BY 4.0), and every source is credited. If the pod camera records people on campus during tests, faces and number plates will be blurred before storage, the data will be kept only on a password-protected laptop and its backup, and no identifiable images will be published. If recording of people becomes necessary, Ethics Committee approval will be requested first.'));
add(T('**Legal requirements.** Images in which people can be identified are personal data under the UK Data Protection Act 2018 (UK GDPR) and the Egyptian Personal Data Protection Law No. 151 of 2020 (Egypt, 2020), so they are blurred, kept private and deleted at the end of the project. Dataset licences are followed (e.g. CC BY 4.0 attribution), the LiDAR is classified under IEC 60825-1, and e-waste goes through the university route.'));

add(H2('1.8', 'Sustainability Analysis'));
add(B('**Re-use of hardware:** the vehicle is borrowed from the lab and the pod is modular, so it can be moved to another vehicle after the project; no new chassis is bought.'));
add(B('**Low-power electronics:** the ESP32 boards use much less energy than a single-board computer, and the existing laptop is used for AI instead of buying new hardware.'));
add(B('**Materials:** the sensor tower is printed in PLA with low infill and few supports; failed prints and off-cuts are recycled through the lab where possible.'));
add(B('**Batteries and e-waste:** rechargeable cells with a BMS extend battery life; damaged cells and electronics will be disposed of through the university e-waste route.'));
add(B('**Computing energy:** public datasets are re-used instead of long data-collection drives, and training runs are planned in advance and compared on the validation set, so the GPU is not used for random experiments.'));
add(B('**Social:** the result can improve the safety of micro-mobility users and pedestrians at low cost.'));

// ===== 2 SOURCES =====
add(H1('2', 'SOURCES OF INFORMATION'));
add(T('The following sources have been identified for the literature review of the final report. Thirteen papers have already been read and summarised.'));
add(B('**Sensor fusion and autonomous vehicles:** Yeong et al. (2021) review of sensors and fusion levels; Favelli, Xie and Tonoli (2024) camera–LiDAR distance estimation; Alai and Rajamani (2024) low-cost camera and 2-D LiDAR fusion for micro-mobility; Barua and Hitosugi (2025) multi-modal fusion with braking decisions.'));
add(B('**Micro-mobility perception:** Hassanin et al. (2025) review of intelligent two-wheelers; Zheng et al. (2025) e-scooter obstacle detection; Akhavi Zadegan, Vivet and Hadachi (2024) DELTA multi-sensor e-scooter; Strässer et al. (2024) ultrasonic collision-avoidance filter; Jang, Kim and Lim (2023) ESP32-based e-scooter monitoring.'));
add(B('**Low-cost hardware and edge AI:** Aniobi (2024) ESP32-CAM with ultrasonic and YOLOv8; Alqahtani, Cheema and Toosi (2024) benchmark of detectors on edge devices; Jocher and Qiu (2024) Ultralytics YOLO11.'));
add(B('**Road hazards and surface classification:** Liang et al. (2025) SBP-YOLO for speed bumps and potholes; Peralta-López et al. (2023) speed bump and pothole detection with a ZED camera; Arce-Saenz, Izquierdo-Reyes and Bustamante-Bello (2025) IMU road surface classification with MPU6050; Wang et al. (2023) camera and vibration fusion for terrain.'));
add(B('**Datasets:** RDD2022 road damage dataset (Arya et al., 2022), Roboflow Universe and Kaggle speed-bump and pothole datasets, and the Egyptian EGY_PDD dataset (access not yet obtained).'));
add(B('**Standards and guidance:** VDI 2206 (VDI, 2021); IEC 60825-1 laser safety (IEC, 2014); the University project handbook (University of Hertfordshire, 2026).'));

// ===== 3 RESOURCES =====
add(H1('3', 'RESOURCE ANALYSIS'));
add(T('The resources were agreed with the supervisor and entered in the Project Resources Checklist (Appendix B). The component request sheet was submitted to the PTO on 29 October 2026 and contains 27 lines with a total of **5,362 EGP** (Table 4; full list in Appendix B), which is close to the nominal budget of £75 per project in the handbook (about 5,350 EGP at the October 2026 exchange rate). The vehicle comes from the lab at no cost.'));
add(TCAP('Summary of the component request (full list in Appendix B)'));
add(TABLE([
  ['Group', 'Main items', 'Cost (EGP)'],
  ['Camera and processing', 'ESP32-CAM + programmer, ESP32 DevKit V1, spare ESP32-CAM', '1,330'],
  ['Range and motion sensors', 'TF-Luna LiDAR, 3× HC-SR04 (1 spare), 3× MPU6050 (1 spare), 2× LM393 encoders', '2,815'],
  ['Output and actuation', '0.96" OLED, L298N motor driver', '235'],
  ['Power', '2× 18650 cells, holder with switch, 2S BMS, 8.4 V charger, LM2596 buck', '701'],
  ['Wiring and mounting', 'Jumpers, perfboard, capacitors, resistors, terminals, breadboard, standoffs, cable', '281'],
  ['Vehicle', '4WD robot car from the university lab', '0'],
  [{ t: 'Total', bold: true }, '27 lines', { t: '5,362', bold: true }],
], [2300, 5938, 1400]));
add(T('**Other resources:** a laptop with an NVIDIA RTX GPU (training and running the models); software – Python, PyTorch, Ultralytics YOLO, OpenCV, Arduino IDE / ESP-IDF, SolidWorks (including its FEA tool), MATLAB/Simulink and Microsoft Excel; lab facilities – 3D printer, soldering station, bench power supply and multimeter; people – the supervisor, the lab engineer (vehicle) and the PTO (orders). Public datasets are used for training, and the pod itself will record test footage on campus.'));

// ===== 4 PLAN =====
add(H1('4', 'PROJECT PLAN'));
add(H2('4.1', 'Project Work Description and Progress to Date'));
add(T('The project covers the whole perception pod, not only the AI model: the mechanical design of the sensor tower, the electronics and firmware, the AI and fusion software, the connection to the vehicle, and the testing against the PDS. The work is divided into six phases that follow the V-model: requirements and research, AI development, hardware (mechanical and electrical), progress review, fusion and integration, and testing and reporting. Table 5 describes the work to be done in each part of the project, what each part produces and how it will be checked. The detailed Gantt chart is in Appendix A.'));
add(TCAP('Work plan for the whole project (task numbers refer to the Gantt chart in Appendix A)'));
add(TABLE([
  ['Part of the project', 'Work to be done', 'Output and how it is checked', 'When (Gantt tasks)'],
  ['1. Requirements and research', 'Read the literature, write the PDS, generate and select the concept, and choose each component with a decision matrix.', 'PDS, selected concept, items sheet and this outline.', { t: 'Oct – 8 Nov (1.1–1.6), done', fill: 'E2EFDA' }],
  ['2. AI hazard detection', 'Build a leak-free pothole and speed-bump dataset from public sources, train YOLO11n, choose the model on validation only and test it once, then fine-tune it on video recorded by the pod.', 'Precision, recall, mAP50 and accuracy for each class; frozen model by 29 Nov; results on pod footage by 14 Mar.', { t: 'Oct – Mar (2.1–2.4, 5.4), in progress', fill: 'FCE4D6' }],
  ['3. Mechanical design', 'Design the sensor tower in SolidWorks so that the camera, LiDAR and ultrasonic sensors face forward at fixed heights and angles, check it with a simple static FEA in SolidWorks, 3D print it and mount it on the lab car.', 'CAD model and drawings, FEA stress and deflection, assembled pod on the vehicle.', '16 Nov – 13 Dec (3.2, 3.4, 3.5)'],
  ['4. Electrical design', 'Draw the schematic and I/O list, calculate the power budget, and wire the 2S battery, BMS, 5 V buck converter, ESP32 and sensors, with level shifting for the ultrasonic echo pins (Appendix D).', 'Schematic and power budget; every supply rail and signal checked with a multimeter before power-up.', '16 – 29 Nov (3.3)'],
  ['5. Firmware and communication', 'Write the ESP32 drivers for the TF-Luna, HC-SR04, MPU6050 and OLED; stream the ESP32-CAM video to the laptop over Wi-Fi; drive the motors through the L298N with an emergency stop on STOP or on link loss.', 'Live sensor readings logged; remote drive and stop working; end-to-end latency measured in ms.', '23 Nov – 13 Dec (3.6–3.8)'],
  ['6. Sensor fusion and decision', 'Record labelled IMU and video data in project week, train the IMU bump and surface classifier, check where the LiDAR and ultrasonic beams point in the camera image, time-stamp all readings, and combine detection, distance and IMU in the SAFE / WARNING / STOP state machine.', 'IMU accuracy and confusion matrix; alignment check; correct warnings with the real sensors.', '13 Dec – 28 Feb (3.9, 5.1–5.3)'],
  ['7. Modelling', 'Build a Simulink model of detection latency against stopping distance to find the maximum safe speed of the vehicle.', 'Maximum safe speed for the measured latency.', '1 – 7 Mar (5.5)'],
  ['8. Integration and testing', 'Join the pod, vehicle and laptop, then test the system under different lighting, speeds (0.3–1 m/s) and approach angles, fix problems and repeat.', 'End-to-end demo (gate G2, 21 Mar); results against each PDS requirement; demo video.', '8 Mar – 22 Apr (5.6, 6.1–6.3)'],
  ['9. Management and reporting', 'Keep weekly logbooks and supervisor meetings, update the Gantt chart, and write the Progress Review, final report, slides, poster and paper draft.', 'Progress Review (24 Jan), final report (4 May), defence (May).', 'Whole year (4.1–4.2, 6.4–6.6)'],
], [1750, 3700, 2650, 1538]));
add(sp(60));
add(T('Table 6 compares the first plan (Gantt v1, October) with the real progress on 8 November.'));
add(TCAP('Progress against the first Gantt chart (v1) on 8 November 2026'));
add(TABLE([
  ['Gantt v1 task', 'Status', 'What was done / what changed'],
  ['Literature and market research (Oct)', { t: 'Done', fill: 'E2EFDA' }, '13 papers summarised; datasets and repositories collected'],
  ['PDS, concepts, selection, architecture', { t: 'Done', fill: 'E2EFDA' }, 'Decision matrices for 7 components; PDS and concept selection in this outline'],
  ['Component order through PTO', { t: 'Done (early)', fill: 'E2EFDA' }, 'Items sheet submitted 29 Oct (27 lines, 5,362 EGP)'],
  ['Platform (RC car from the lab)', { t: 'Changed', fill: 'FFF2CC' }, 'A 4WD two-deck lab robot car will be used; request sent to the lab engineer'],
  ['AI: dataset, training, fusion logic (planned Jan–Mar)', { t: 'Ahead of plan', fill: 'E2EFDA' }, 'Leak-free dataset, two rounds of label cleaning and several controlled training runs (Table 7); live pipeline with two models and the SAFE/WARNING/STOP state machine, 26 unit tests passing, about 36 ms per frame on the laptop'],
  ['Dataset collection in project week (Dec)', { t: 'Changed', fill: 'FFF2CC' }, 'Supervisor advised a wider search of existing data (e.g. Kaggle) instead of collecting a large dataset; the pod will record test drives only'],
  ['Improve model accuracy (Jan–Feb)', { t: 'In progress', fill: 'FCE4D6' }, 'New public sources added (models D1, D2): large gains on unseen countries (Table 7); v3b_C with 10,562 training images is being trained; final model chosen on validation by 29 Nov'],
  ['Sensor tower CAD, electronics, firmware', { t: 'Not started', fill: 'F2F2F2' }, 'Starts 16 Nov after the vehicle and components are confirmed (gate G1)'],
], [2900, 1300, 5438]));
add(sp(60));
add(T('Table 7 summarises the leak-free results (YOLO11n, image size 960). On the main validation set all models are close (about 0.60–0.63 AP50 for potholes and 0.68–0.73 for speed bumps; the difference between training seeds is about ±0.01–0.02). The clear gain is on countries never used in training: after new public sources were added (D1, D2), Lithuanian speed bumps rose from 0.028 to 0.670 and Slovak potholes from 0.399 to 0.617. Only v1 and Run A have been tested, once each; Run A reached 0.631 for potholes but only 0.294 for speed bumps, because the test bumps come from two drives with unmarked bumps that the early training data did not cover.'));
add(TCAP('Hazard model results so far (AP50 per class; val = validation set, never used for testing)'));
add(TABLE([
  ['Model (data version)', 'Pothole – val (830 img)', 'Bump – val (830 img)', 'Pothole – unseen country (Slovakia)', 'Bump – unseen country (Lithuania)', 'Test, used once (pothole / bump)'],
  ['v1 (v3a_r1)', '0.628', '0.710', '0.399', '0.028', '0.660 / 0.354 (324 img)'],
  ['Run A (cleaned labels, v3a_r2)', '0.605', '0.725', '0.422', '0.036', '0.631 / 0.294 (323 img)'],
  ['D1 (+ RSID, Bučko, RDD2022 data)', '0.596', '0.710', '0.571', { t: '0.670', bold: true }, 'not tested yet'],
  ['D2 (D1 + Malaysia/Indonesia data)', '0.615', '0.683', { t: '0.617', bold: true }, '0.630', 'not tested yet'],
  ['v3b_C (10,562 train images, bump boxes doubled)', 'training', 'training', 'training', 'training', 'after selection on val'],
], [2700, 1250, 1250, 1450, 1450, 1538], { center: true }));
add(T('The supervisor target of 0.90 has not been reached yet. The closest agreed metric is the precision of speed-bump warnings at 50 % recall (0.904 for D2 and 0.950 for Run A on validation), which still has to be confirmed on the test set. Per-class mAP50 is well below 0.90 and recall is the main weakness. The gap comes from data diversity (unmarked Egyptian bumps, far and small potholes), not from training length, so the next step is more independent data, model selection on validation and one test.'));
add(sp(60));
add(T('**Next steps (to 13 Dec):** confirm the vehicle and the parts (G1), finish the model experiments and freeze the hazard model using the validation set only, design and print the sensor tower, write the sensor firmware, connect the vehicle to the ESP32 and the L298N, and measure the end-to-end latency over Wi-Fi. The project week in December is used for test drives with the complete pod.'));

add(H2('4.2', 'Critical Path Analysis'));
add(T('The critical path (red in Appendix A) is: Outline → vehicle and parts confirmed (G1) → sensor tower CAD → 3D print and mounting → sensor drivers and vehicle interface → ESP32-CAM streaming → test drives → IMU classification → fusion with real sensors → full integration (G2) → benchmark tests → report. The AI tasks were moved earlier and are now off the critical path, which gives extra float. Table 8 lists the key decision gates and milestones.'));
add(TCAP('Decision gates and milestones'));
add(TABLE([
  ['ID', 'Date', 'Gate / milestone', 'Decision or measurable outcome'],
  ['M1', '8 Nov 2026', 'Project Outline submitted', 'Outline on Canvas'],
  ['G1', '15 Nov 2026', 'Vehicle and components confirmed', 'Lab car received; PTO order approved, otherwise switch to the 4WD kit (400 EGP)'],
  ['G1b', '29 Nov 2026', 'Hazard model frozen', 'Best model chosen on validation; tested once; P, R, mAP50, accuracy per class'],
  ['G1c', '13 Dec 2026', 'Pod assembled and streaming', 'All sensors read on the laptop; latency measured against R5'],
  ['M2', '24 Jan 2027', 'Progress Review submitted', 'Literature review, slides, updated Gantt, logbook'],
  ['G2', '21 Mar 2027', 'Integrated system working', 'End-to-end demo: STOP and WARNING on real obstacles'],
  ['M3', '4 May 2027', 'Report and slides submitted', 'Canvas submission'],
  ['M4', '4–13 May 2027', 'Project defence', 'Presentation and live demo'],
], [650, 1300, 2700, 4988]));

add(H2('4.3', 'Threats and Contingency Plan'));
add(TCAP('Main threats to the plan'));
add(TABLE([
  ['Threat', 'L', 'I', 'Mitigation / contingency'],
  ['Lab vehicle not available or not suitable', 'M', 'H', 'Back-up: 4WD two-layer kit (400 EGP) is already in the items sheet as the alternative'],
  ['Late delivery of parts (TF-Luna stock is limited)', 'M', 'H', 'Order before Christmas; HC-SR04 sensors cover range finding; alternative vendors listed'],
  ['Hazard model does not reach the accuracy target', 'H', 'M', 'Wider data search, per-class thresholds on validation, larger model if latency allows; report the honest result'],
  ['Wi-Fi delay too high for real time', 'M', 'H', 'Lower resolution/JPEG quality, phone hotspot close to the car, on-board STOP from range sensors only'],
  ['Hardware damage (ESP32-CAM, IMU)', 'L', 'M', 'Spares ordered (ESP32-CAM, HC-SR04, MPU6050)'],
  ['Laptop or data loss', 'L', 'H', 'Git repository and weekly backup to cloud and external drive'],
  ['Exams and other modules in January', 'H', 'M', 'Christmas buffer (B1) and April buffer (B2); hardware finished before Christmas'],
], [3300, 400, 400, 5538]));
add(T('L = likelihood, I = impact (L/M/H). **Monitoring and control.** Progress is checked at the weekly supervisor meeting and recorded, with the hours spent, in the logbook (about 300 h in total and 120–150 h by the Progress Review, as in the handbook). The Gantt chart is updated every two weeks with the actual dates; if a critical-path task slips by more than one week, its contingency (Table 9) or the next buffer is used and the change is logged.'));

// ===== 5 REFERENCES =====
add(H1('5', 'REFERENCES'));
const refs = [
  'Akhavi Zadegan, A., Vivet, D. and Hadachi, A. (2024) \'DELTA: integrating multimodal sensing with micromobility for enhanced sidewalk and pedestrian route understanding\', Sensors, 24(12), p. 3863.',
  'Alai, H. and Rajamani, R. (2024) \'Low-cost camera and 2-D LIDAR fusion for target vehicle corner detection and tracking: applications to micromobility devices\', Mechanical Systems and Signal Processing, 206, p. 110891.',
  'Alqahtani, D.K., Cheema, A. and Toosi, A.N. (2024) \'Benchmarking deep learning models for object detection on edge computing devices\', arXiv preprint, arXiv:2409.16808.',
  'Aniobi, A. (2024) \'Sensor fusion for real-time object detection and spatial positioning in unmanned vehicles using YOLOv8 and ESP32-Cam\', Preprints.org, 202411.0611 (not peer-reviewed).',
  'Arce-Saenz, L.A., Izquierdo-Reyes, J. and Bustamante-Bello, R. (2025) \'Exploring single-head and multi-head CNN and LSTM-based models for road surface classification using on-board vehicle multi-IMU data\', Scientific Reports, 15, p. 24595.',
  'Arya, D., Maeda, H., Ghosh, S.K., Toshniwal, D. and Sekimoto, Y. (2022) \'RDD2022: a multi-national image dataset for automatic road damage detection\', arXiv preprint, arXiv:2209.08538.',
  'Barua, N. and Hitosugi, M. (2025) \'Advanced multi-modal sensor fusion system for detecting falling humans: quantitative evaluation for enhanced vehicle safety\', Vehicles, 7(4), p. 149.',
  'Data Protection Act 2018, c. 12. Available at: https://www.legislation.gov.uk/ukpga/2018/12 (Accessed: 5 November 2026).',
  'Egypt (2020) Law No. 151 of 2020 on the Protection of Personal Data. Cairo: Official Gazette of the Arab Republic of Egypt.',
  'Favelli, S., Xie, M. and Tonoli, A. (2024) \'Sensor fusion method for object detection and distance estimation in assisted driving applications\', Sensors, 24(24), p. 7895.',
  'Hassanin, M., Abu Alsheikh, M., Kuhn, C.C.N., Herath, D., Hoang, D.T. and Radwan, I. (2025) \'Towards autonomous riding: a review of perception, planning, and control in intelligent two-wheelers\', arXiv preprint, arXiv:2507.11852.',
  'IEC (2014) IEC 60825-1:2014 Safety of laser products – Part 1: Equipment classification and requirements. Geneva: International Electrotechnical Commission.',
  'Jang, W.-J., Kim, D.-H. and Lim, S.-H. (2023) \'An AI safety monitoring system for electric scooters based on the number of riders and road types\', Sensors, 23(22), p. 9181.',
  'Jocher, G. and Qiu, J. (2024) Ultralytics YOLO11. Available at: https://github.com/ultralytics/ultralytics (Accessed: 5 November 2026).',
  'Liang, C., Fu, J., Yu, M. and Luo, L. (2025) \'SBP-YOLO: a lightweight real-time model for detecting speed bumps and potholes toward intelligent vehicle suspension systems\', arXiv preprint, arXiv:2508.01339.',
  'Peralta-López, J.-E. et al. (2023) \'Speed bump and pothole detection using deep neural network with images captured through ZED camera\', Applied Sciences, 13(14), p. 8349.',
  'Strässer, R., Seidel, M., Brändle, F., Meister, D., Soloperto, R., Hambach Ferrer, D. and Allgöwer, F. (2024) \'Collision avoidance safety filter for an autonomous e-scooter using ultrasonic sensors\', IFAC-PapersOnLine (17th IFAC Symposium on Control in Transportation Systems). doi:10.1016/j.ifacol.2024.07.313.',
  'University of Hertfordshire (2026) Undergraduate Project Handbook 2026–27, BEng Individual Project. School of Engineering and Computer Science.',
  'VDI (2021) VDI/VDE 2206: Development of mechatronic and cyber-physical systems. Berlin: Beuth Verlag.',
  'Wang, H., Lu, E., Zhao, X. and Xue, J. (2023) \'Vibration and image texture data fusion-based terrain classification using WKNN for tracked robots\', World Electric Vehicle Journal, 14(8), p. 214.',
  'Yeong, D.J., Velasco-Hernandez, G., Barry, J. and Walsh, J. (2021) \'Sensor and sensor fusion technology in autonomous vehicles: a review\', Sensors, 21(6), p. 2140.',
  'Zheng, Z., Hosseini, A., Chen, D., Shoghli, O. and Heydarian, A. (2025) \'Real-time roadway obstacle detection for electric scooters using deep learning and multi-sensor fusion\', arXiv preprint, arXiv:2504.03171.',
];
refs.forEach(x => add(new Paragraph({ spacing: { after: 70, line: 240 }, indent: { left: 400, hanging: 400 }, children: [r(x, { size: 18 })] })));

// ===== APPENDICES =====
const tasks = JSON.parse(fs.readFileSync('gantt_tasks.json'));
const appA = [
  new Paragraph({ children: [r('APPENDIX A: Gantt Chart', { size: 26, bold: true })], spacing: { after: 120 } }),
  ...IMG('gantt.jpg', 870, 'Gantt chart v2 – completed, in-progress and planned tasks, critical path and gates'),
];
const ganttRows = [['ID', 'Task', 'Start', 'End', 'Measurable outcome', 'CP', 'Status']];
tasks.forEach(t => {
  if (t[6] === 'head') { ganttRows.push([{ t: '', fill: 'EDEDED' }, { t: t[1], bold: true, fill: 'EDEDED' }, { t: '', fill: 'EDEDED' }, { t: '', fill: 'EDEDED' }, { t: '', fill: 'EDEDED' }, { t: '', fill: 'EDEDED' }, { t: '', fill: 'EDEDED' }]); return; }
  const st = { done: 'Done', prog: 'In progress', plan: 'Planned', buffer: 'Buffer', ms: 'Milestone' }[t[6]];
  ganttRows.push([t[0], t[1], t[2], t[3], t[4] || '—', t[5] ? 'Yes' : '', st]);
});
appA.push(TCAP('Gantt chart task list (each task ≤ 2 weeks; CP = on the critical path)'));
appA.push(TABLE(ganttRows, [600, 5300, 950, 950, 3900, 500, 1300], { size: 15 }));

const yn = (y) => y ? '☒ Yes   ☐ No' : '☐ Yes   ☒ No';
const appB = [
  new Paragraph({ pageBreakBefore: true, children: [r('APPENDIX B: Project Resources Checklist', { size: 26, bold: true })], spacing: { after: 120 } }),
  TABLE([["Student's Name:", 'Ahmed Mohamed Elsayed Elreefy'], ['SRN:', '202301376 (UH ID 23022692)'],
    ['Project Title:', 'AI-Powered Multi-Modal Perception System for Autonomous Micro-Mobility Environmental Awareness'],
    ["Supervisor's Name:", 'Dr. Peter Makeen'], ['Date:', '8 November 2026']].map((x, i) => i === 0 ? [{ t: x[0], bold: true, fill: 'FFFFFF' }, { t: x[1], fill: 'FFFFFF' }] : [{ t: x[0], bold: true }, x[1]]), [2600, 7038], { size: 18 }),
  sp(100),
  TABLE([
    ['No', 'Question', 'Answer and details'],
    ['1', 'Will materials or components be ordered?', yn(1) + '\nItems sheet submitted to the PTO on 29 Oct 2026 (27 lines, 5,362 EGP).'],
    ['2', 'Will you be designing a PCB or drawing which will require manufacture?', yn(1) + '\nSensor tower drawing for 3D printing (PLA). Electronics on perfboard, no PCB manufacture.'],
    ['3', 'Will PCB or drawing assemblies already designed and manufactured within the School be required?', yn(1) + '\nThe 4WD robot car from the university lab.'],
    ['4', 'Will a PC be required for work other than for report writing?', yn(1) + '\nLaptop with NVIDIA GPU for model training, live inference and data logging.'],
    ['5', 'Special hardware installed/attached?', yn(1) + '\nUSB-serial programmers (CH340 on ESP32-CAM-MB, CP2102 on the ESP32 DevKit); Wi-Fi access point or phone hotspot.'],
    ['6', 'Will you require specific software, other than word processing?', yn(1) + '\nPython, PyTorch, Ultralytics YOLO, OpenCV, Arduino IDE / ESP-IDF, SolidWorks, MATLAB/Simulink.'],
    ['7', 'Will your project require technical staff to make items requiring workshop facilities?', yn(1) + '\n3D printing of the sensor tower, and possibly drilling mounting holes in the acrylic deck.'],
    ['8', 'Workshop activities required', 'Drilling (mounting holes); Other: 3D printing'],
    ['9', 'Are there other resources required, not covered above?', yn(1) + '\nA closed indoor or campus area for driving tests, and lab bench power supply and multimeter.'],
  ], [500, 4100, 5038], { size: 17 }),
  sp(100),
  TCAP('Components to be used in the pod (items sheet submitted to the PTO on 29 Oct 2026)'),
  TABLE([
    ['No', 'Component', 'Qty', 'Use in the pod', 'Cost (EGP)'],
    ["1", "ESP32-CAM AI-Thinker (OV2640)", "1", "Captures road images and streams them to the laptop over Wi-Fi", "450"],
    ["2", "ESP32-CAM-MB programmer (CH340)", "1", "Uploads code to the ESP32-CAM", "80"],
    ["3", "ESP32 DevKit V1 (ESP32-WROOM-32)", "1", "Sensor hub on the vehicle: LiDAR, ultrasonic, IMU, OLED, motor driver", "350"],
    ["4", "TF-Luna ToF LiDAR (0.2–8 m, UART)", "1", "Main range sensor: distance to the detected obstacle", "2,250"],
    ["5", "HC-SR04 ultrasonic sensor", "2", "Front-left and front-right range, wider coverage", "80"],
    ["6", "MPU6050 GY-521 IMU", "2", "Vibration for bump and surface classification (left and right)", "230"],
    ["7", "0.96\" OLED SSD1306 (I2C)", "1", "Shows state, nearest object, distance and surface", "160"],
    ["8", "L298N motor driver", "1", "Drives the vehicle motors and the STOP command", "75"],
    ["9", "Robot car from the university lab", "1", "Test vehicle (4WD kit, 400 EGP, as alternative)", "0"],
    ["10", "18650 Li-ion cell 3.7 V 2600 mAh", "2", "2S battery pack (7.4 V)", "398"],
    ["11", "2×18650 holder with ON/OFF switch", "1", "Battery holder and main power switch", "18"],
    ["12", "2S BMS 8.4 V 5 A", "1", "Over-charge, over-discharge and short-circuit protection", "40"],
    ["13", "2S charger 8.4 V 2 A", "1", "Charging the battery pack", "185"],
    ["14", "LM2596 buck converter (set to 5 V)", "1", "5 V supply for the ESP32 boards and sensors", "60"],
    ["15–16", "Jumper wires M/F and M/M (40 each)", "2", "Connections between modules", "70"],
    ["17", "Perfboard 7×9 cm + pin headers", "1", "Permanent wiring of the pod electronics", "60"],
    ["18", "Capacitor 1000 µF / 16 V", "2", "Stabilises the ESP32-CAM 5 V supply", "10"],
    ["19", "Resistor kit (1k, 2k, 4.7k, 10k)", "1", "Echo dividers (5 V → 3.3 V) and battery voltage sensing", "20"],
    ["20", "Micro-USB data cable", "1", "Programming the ESP32 boards", "30"],
    ["21", "Screw terminal 2-pin", "4", "Battery, 5 V and motor connections", "20"],
    ["22", "Mini breadboard 400 points", "1", "Testing each sensor before soldering", "35"],
    ["23", "M3 nylon standoffs 12 mm (10 pcs)", "3", "Mounting the boards on the vehicle and tower", "36"],
    ["24", "LM393 speed sensor (wheel encoder)", "2", "Wheel speed, to link vehicle speed with stopping distance", "100"],
    ["25–27", "Spares: ESP32-CAM, HC-SR04, MPU6050", "3", "Replacement if a part is damaged", "605"],
    [{ t: '', bold: true }, { t: 'Total (27 lines)', bold: true }, '', '', { t: '5,362', bold: true }],
  ], [720, 3080, 650, 4188, 1000], { size: 16 }),
  P([r('Other items are taken from the lab and are not in the sheet: PLA filament and 3D printing, M3 screws and nuts, hook-up wire, soldering tools, bench power supply and multimeter.', { size: 18 })]),
];

const appC = [
  new Paragraph({ pageBreakBefore: true, children: [r('APPENDIX C: Project Risk, Ethics and Threat Assessment Checklist', { size: 26, bold: true })], spacing: { after: 120 } }),
  TABLE([
    ['No', 'Question', 'Answer and details'],
    ['1', 'Use or contact with: voltages above 30 V; high currents at low voltage; rotating machines; high temperatures; hazardous fluids or gases', '☒ Yes   ☐ No\nNo voltage above 9 V. High current possible from Li-ion cells (short circuit); small DC gear motors and wheels (rotating); soldering iron and 3D-printer nozzle (high temperature). No hazardous fluids or gases.'],
    ['2', 'Attaching electrodes to yourself or someone else?', yn(0)],
    ['3', 'If 2 is Yes, has a risk assessment been carried out?', 'N/A'],
    ['4', 'If 2 or 3 is Yes, is the risk acceptable?', 'N/A'],
    ['5', "Substances classified as 'Hazardous to Health'?", yn(0) + '\nLead-free solder used with ventilation.'],
    ['6', 'Flammable substances?', yn(0) + '\nNo cleaning solvents or paint planned.'],
    ['7', 'Other aspects which might impose a danger to yourself or others?', '☒ Yes   ☐ No\nMoving vehicle during tests; Class 1 LiDAR laser; Li-ion battery charging.'],
    [{ t: '', fill: 'EDEDED' }, { t: 'Ethical issues', bold: true, fill: 'EDEDED' }, { t: '', fill: 'EDEDED' }],
    ['8', 'Measurements on human subjects or their behaviour?', yn(0) + '\nPeople are detected with a pretrained model only; no data about people is collected.'],
    ['9', 'Asking human subjects questions of a personal nature?', yn(0)],
    ['10', 'Could any aspect cause distress to human subjects?', yn(0) + '\nAny accidental images of people on campus are blurred and not published.'],
  ], [500, 4100, 5038], { size: 17 }),
  sp(80),
  P([r('Questions 1 and 7 are "Yes", so the hazards are assessed in the table below with their controls.', { size: 18 })]),
  TABLE([
    ['Hazard', 'Who', 'Risk (L × S)', 'Controls', 'Residual'],
    ['Li-ion cell short circuit, fire while charging', 'Student, lab users', 'M × H', '2S BMS, insulated holder and switch, 8.4 V CC/CV charger, charge only when present, fire-proof bag, inspect cells', 'Low'],
    ['Vehicle collision with people or objects', 'Student, bystanders', 'M × M', 'Speed ≤ 1 m/s, closed test area, main switch, software STOP and fail-safe STOP, test with boxes', 'Low'],
    ['Burns from soldering iron / printer nozzle', 'Student', 'M × L', 'Stand and mat, switch off after use, lab rules', 'Low'],
    ['Laser exposure (TF-Luna)', 'Student, bystanders', 'L × L', 'Class 1 eye-safe product; do not look into the emitter', 'Very low'],
    ['Cuts or pinching from wheels and tools', 'Student', 'L × L', 'Wheels lifted off the ground during bench tests; correct tools', 'Very low'],
  ], [2200, 1300, 1050, 3988, 1100], { size: 16 }),
];

const appD = [
  new Paragraph({ pageBreakBefore: true, children: [r('APPENDIX D: Pod Wiring Diagram', { size: 26, bold: true })], spacing: { after: 120 } }),
  P('The diagram uses net labels: pins with the same label are connected. The ESP32 DevKit is supplied with 5 V from the LM2596 buck converter, and the I2C devices and encoders use its 3.3 V output. The HC-SR04 echo outputs (5 V) are reduced to 3.3 V with 1 kΩ / 2 kΩ dividers, and the battery voltage is measured on GPIO36 through a 10 kΩ / 4.7 kΩ divider. Strapping pins are not used. The pin map will be confirmed on the bench before soldering (Gantt task 3.3).'),
  ...IMG('circuit.jpg', 640, 'Pod wiring diagram: ESP32 DevKit sensor hub, sensors, motor driver and power supply'),
];

// figure / table lists are known only after building body; build twice
global.FIGLIST = figs; global.TABLIST = tabs;

const header = new Header({ children: [new Paragraph({ tabStops: [{ type: TabStopType.RIGHT, position: 9638 }],
  border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: '808080', space: 2 } },
  children: [r('School of Engineering and Computer Science', { size: 16 }), r('\tBEng Project Outline – Elreefy, A. (23022692)', { size: 16 })] })] });
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [r('Page ', { size: 16 }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16 })] })] });

const margins = { top: 1134, bottom: 1134, left: 1134, right: 1134 };
const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: SZ } } } },
  numbering: { config: [{ reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 250 } } } }] }] },
  sections: [
    { properties: { page: { margin: margins } }, children: title },
    { properties: { page: { margin: margins } }, headers: { default: header }, footers: { default: footer }, children: [...toc(), ...body] },
    { properties: { page: { margin: margins, size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE } } }, headers: { default: header }, footers: { default: footer }, children: appA },
    { properties: { page: { margin: margins } }, headers: { default: header }, footers: { default: footer }, children: [...appB, ...appC, ...appD] },
  ],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync('Elreefy_Ahmed_23022692_Project_Outline.docx', b); console.log('written', figs.length, tabs.length); });
