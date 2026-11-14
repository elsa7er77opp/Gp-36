# Candidate additions — NOT approved training data

2,420 unused RDD Japan/India train candidates. Images cNNNN.jpg are standardized to 960x720 with the existing std_dataset_v2.py crop/pad and box transform. proposed_labels/cNNNN.txt contains mapped source labels in YOLO format: class 0 pothole, class 1 speed_bump. These source labels are proposals, NOT visually confirmed labels. Contact sheets show boxes and candidate IDs.

Do not train on this directory. Source labels include cracks, filled repairs and unpaved shoulders mislabelled as potholes. Every admitted image needs exhaustive visual annotation, final box inspection, current-train dedup and held-out checks. Current pending status is recorded in candidate_ledger.jsonl. Original labels were not changed.
