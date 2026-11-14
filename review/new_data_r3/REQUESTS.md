# Data requests to authors (draft emails for Ahmed to send; cloud session 5, 2026-11-04)

Send from the university address. Never promise redistribution. Ask for a written licence or permission line we can
quote in DATA.md. Log every reply in `CANDIDATES.md` §I (date, answer, licence).

Common signature:
> Ahmed Elreefy, graduation project #36 "Perception Pod" (supervisor Dr. Peter Makeen), Faculty of Engineering.

---
## R1. DriveIndia (TiHAN, IIT Hyderabad): unmarked speed-bump class
To: the TiHAN dataset contact listed on tihan.iith.ac.in (paper arXiv 2507.19912, IEEE 11423478)
Subject: Academic access request: DriveIndia dataset (unmarked / marked speed bump classes)

Dear DriveIndia team,

I am a final-year engineering student. My graduation project is a camera-based road-hazard warning pod. Our detector
struggles most with **unmarked speed bumps** in forward-facing dashcam video. Your paper describes "unmarked speed
bump", "marked speed bump", "rumble strips" and "zebra crossing" classes, which is exactly what we lack.

Could you grant academic, non-commercial access to the DriveIndia images and YOLO labels? Even the subset of images
that contain the two speed-bump classes would help. We will:
- use the data only for this non-commercial graduation project, with full citation;
- keep a copy only on the project laptop and never redistribute it;
- report results by drive or sequence, so frames of one drive never sit in both training and evaluation.

If there is a licence or form to sign, please send it. Thank you for your time.

---
## R2. Egyptian unmarked-bump videos (GitHub Mohamed20384/Speed-Bump-Detection-marked-unmarked)
To: the repository owner (GitHub profile e-mail, or an issue titled "Permission request: dataset use")
Subject: Permission to use your Egyptian speed-bump videos / labels in a graduation project

Dear Mohamed,

Your project on marked and unmarked speed bumps on Egyptian streets matches the hardest case of my graduation project
(a road-hazard warning pod tested in Egypt). Your repository has no licence, so I cannot use the material without
your permission.

May I:
1. use your input videos (bump1–6, bump_challenge) for research inside my project, and
2. if you still have them, receive the labelled frames you trained on?

I would keep everything private, cite your repository and name you in the report, and use the videos mainly as an
**Egyptian evaluation set** (never mixed into training) unless you prefer otherwise. A one-line reply such as "You
may use the data for your graduation project with attribution" is enough.

---
## R3. KFUPM / Al Khobar pothole + depth dataset (arXiv 2504.13648)
To: the corresponding author of arXiv 2504.13648
Subject: Request for the Saudi dashboard-camera pothole dataset (981 images)

Dear Dr. <name>,

I read your paper (arXiv 2504.13648) on pothole detection with depth estimation from dashboard-camera images in Saudi
Arabia. My graduation project builds a forward-view road-hazard detector for Egyptian roads, and public MENA dashcam
data is very scarce.

Would you share the 981 annotated 1920×1080 images (labels in any format) for non-commercial academic use? I will cite
the paper, not redistribute the data, and keep the leak and duplicate checks we apply to every source.

---
## R4. CMIRD authors (Kaggle ammanaveen/custom-multitask-indian-road-dataset-cmird; PubMed 42410140)
To: the Kaggle dataset owner / the paper's corresponding author
Subject: CMIRD detection class names (IDs 4 and 7)

Dear authors,

Thank you for publishing CMIRD (CC BY-NC-SA 4.0). The detection labels have 10 numeric classes but no class-name file.
From sample images we believe 0 auto-rickshaw, 1 bike, 2 bus, 3 car, 5 manhole, 6 person, 8 speed bump and
9 waterlogging. However, **IDs 4 and 7 both show cracks and potholes**. Could you confirm the official name of every
class ID, in particular 4 and 7?

---
## R5. HRP4K (Scientific Data 2026, doi 10.1038/s41597-026-07317-w): only if the laptop vet finds no public download
Subject: Access to HRP4K images and labels

Dear authors,

I would like to evaluate HRP4K for a non-commercial graduation project on forward-view pothole detection. Could you
point me to the download, its licence, and the region of capture? We also need to check it for overlap with RDD2022
and andrewmvd.

---
## R6. IRDD (Iraqi Road Damage Dataset, Zenodo 21167531): only needed if the cloud vet in CANDIDATES §I flags issues
CC BY 4.0, so no permission is needed. Ask only if video or sequence ids are missing (they decide the group split):
"Could you share the source video / drive id of each image, so that frames of one drive are never split across our
training and evaluation sets?"
