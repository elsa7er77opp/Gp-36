"""Inventory distinct upstream frame candidates, excluding protected BPO videos and existing frames.

No image is admitted or relabelled; same-frame 640/4K exports are never counted twice.
"""
import csv,json,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'review/v5/expansion13000';CAT=ROOT/'review/v5/pretrain/upstream_catalog.json'
def canonical(name):
 s=Path(name).stem;s=re.sub(r'(?:_jpg)?\.rf\.[0-9a-f]+$','',s);return re.sub(r'_jpg$','',s)
def video(key):return key.rsplit('_frame_',1)[0] if '_frame_' in key else None
base=list(csv.DictReader((ROOT/'road_hazards_v5_all/manifest.csv').open()))
part=list(csv.DictReader((ROOT/'parts_r3/bpo/manifest.csv').open()))
used={canonical(r['orig_image']) for r in base};held_videos={video(canonical(r['orig_image'])) for r in part if r['split']!='train'};held_videos.discard(None)
train_videos={video(canonical(r['orig_image'])) for r in base if r['source']=='bpo' and r['split']=='train'};train_videos.discard(None)
catalog=json.loads(CAT.read_text());rows=[];rejected=Counter()
for key,item in catalog.items():
 v=video(key);p=Path(item['path']);w,h=item['size']
 if not v:rejected['no_explicit_video_id']+=1;continue
 if v in held_videos:rejected['protected_bpo_video']+=1;continue
 if key in used:rejected['already_used_frame_identity']+=1;continue
 if w*h<=960*720:rejected['no_higher_resolution_copy']+=1;continue
 label=p.parent.parent/'labels'/(p.stem+'.txt')
 if not label.exists():rejected['missing_source_label']+=1;continue
 rows.append(dict(frame_id=key,video_id=v,original=str(p),original_label=str(label),width=w,height=h,source_family='bpo_upstream',video_previously_in_training=v in train_videos,status='pending_full_guard_hashes_dedup_and_visual_review'))
with (E/'upstream_candidates_inventory.csv').open('w',newline='') as f:
 fields=list(rows[0]) if rows else ['frame_id','status'];wr=csv.DictWriter(f,fieldnames=fields);wr.writeheader();wr.writerows(rows)
summary=dict(catalog_unique_frames=len(catalog),high_resolution_unused_candidate_frames=len(rows),candidate_video_ids=len({r['video_id'] for r in rows}),frames_from_new_video_ids=sum(not r['video_previously_in_training'] for r in rows),protected_bpo_video_ids=len(held_videos),current_bpo_train_video_ids=len(train_videos),current_and_protected_video_overlap=sorted(train_videos&held_videos),rejected=dict(rejected),accepted_images=0,limitations='Inventory only. BPO upstream is the same dataset family, not independent geography. Do not include same canonical frame twice. Every candidate still needs source/standardized eight-transform checks against current and protected data, within-candidate dedup, visual relabeling and final 960x720 geometry. Original export splits are image-level and not adopted. Keep these videos train-only, outside all protected BPO videos.')
(E/'UPSTREAM_INVENTORY_REPORT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
