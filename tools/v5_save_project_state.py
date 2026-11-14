"""Persist a resumable, honest project state and candidate YOLO labels; never mark candidates clean."""
import csv,json,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/v5';P=R/'pretrain';E=R/'expansion13000'
release=json.loads((P/'SOURCE_RELEASE_REPORT.json').read_text());resolution=json.loads((P/'RESOLUTION_AUDIT.json').read_text());leak=json.loads((R/'no_leak_gate/REVIEWED_REPORT.json').read_text())
assert release['dataset']==resolution['dataset']==leak['dataset']
candidates=[r for r in map(json.loads,(E/'rdd_candidates/candidate_ledger.jsonl').read_text().splitlines())]
visual=[r for r in map(json.loads,(E/'rdd_visual_review_decisions.jsonl').read_text().splitlines())]
staged=[]
for manifest_path in sorted(E.glob('reviewed_additions*/manifest.csv')):staged.extend(csv.DictReader(manifest_path.open()))
for manifest_path in sorted(E.glob('reviewed_upstream*/manifest.csv')):staged.extend(csv.DictReader(manifest_path.open()))
dest=E/'rdd_candidates/proposed_labels';dest.mkdir(exist_ok=True)
for r in candidates:
 if 'proposed_boxes' not in r:continue
 lines=[]
 for c,x,y,X,Y in r['proposed_boxes']:
  assert c in [0,1] and 0<=x<X<=1 and 0<=y<Y<=1
  lines.append(f'{int(c)} {(x+X)/2:.6f} {(y+Y)/2:.6f} {X-x:.6f} {Y-y:.6f}\n')
 p=dest/f"c{r['candidate']:04}.txt";tmp=p.with_suffix('.tmp');tmp.write_text(''.join(lines));tmp.replace(p)
(E/'rdd_candidates/README.md').write_text('# Candidate additions — NOT approved training data\n\n2,420 unused RDD Japan/India train candidates. Images cNNNN.jpg are standardized to 960x720 with the existing std_dataset_v2.py crop/pad and box transform. proposed_labels/cNNNN.txt contains mapped source labels in YOLO format: class 0 pothole, class 1 speed_bump. These source labels are proposals, NOT visually confirmed labels. Contact sheets show boxes and candidate IDs.\n\nDo not train on this directory. Source labels include cracks, filled repairs and unpaved shoulders mislabelled as potholes. Every admitted image needs exhaustive visual annotation, final box inspection, current-train dedup and held-out checks. Current pending status is recorded in candidate_ledger.jsonl. Original labels were not changed.\n')
dedupfile=E/'DEDUP_REPORT.json'
dedup=json.loads(dedupfile.read_text()) if dedupfile.exists() else {'status':'running_or_pending','tool':'tools/v5_expansion_dedup.py'}
state=dict(updated_utc=datetime.now(timezone.utc).isoformat(),workspace=str(ROOT),current_dataset=release['dataset'],resolution=[960,720],current_images=resolution['total_images'],current_splits=release['splits'],current_content_fingerprint=release['content_fingerprint'],resolution_pass=resolution['pass'],current_release_integrity=release['integrity'],leakage_review=leak,unresolved_existing_labels=release['unresolved_images'],target_train_images=13000,current_train_images=release['splits']['train']['images'],additional_train_images_needed=2438,addition_candidates=len(candidates),candidate_yolo_labels=len(list(dest.glob('*.txt'))),addition_images_visually_screened=len(visual),addition_images_staged=len(staged),addition_boxes_staged=sum(int(r['boxes']) for r in staged),addition_images_merged_into_training=0,expansion_dedup=dedup,training_started=False,test_inference_performed=False,train_ready=False)
state['next_steps']=['Adjudicate 149 existing provisional images using adequate source evidence; do not silently promote confidence.','Continue candidate visual review after C0042; C0010, C0015, C0021, C0024 and other held images require individual recheck.','Adjudicate current-reference and within-candidate perceptual matches, then complete video/scene-family grouping.','Only merge fully reviewed, unique additions into a NEW version; retain all existing images and freeze validation/test. Need 2,438 admitted additions for 13,000 train images.','Recheck every output image is 960x720 and every YOLO label is aligned, in bounds and class-correct; verify full hashes and split paths.','Train from clean pretrained YOLO11n at imgsz960, batch8, seed0, epochs70, patience20, workers2, close_mosaic10 as baseline; select checkpoints on validation. Do not invoke old train.py which automatically evaluates test.']
state['addition_staged_pending_images']=sum(r['status']=='visual_reviewed_pending_full_dedup' for r in staged)
state['addition_staged_rejected_duplicate_images']=sum(r['status']=='rejected_same_scene_duplicate' for r in staged)
state['addition_reviewed_negative_images']=sum(r['status']=='visual_reviewed_negative_dedup_screen_pass' for r in staged)
state['addition_reviewed_pothole_images']=sum(r['status']=='visual_reviewed_pothole_dedup_screen_pass' for r in staged)
u=E/'upstream_candidates/PREPARATION_REPORT.json'
if u.exists():
 state['upstream_preparation']=json.loads(u.read_text())
 state['upstream_visual_screened_images']=len((E/'upstream_visual_review_decisions.jsonl').read_text().splitlines()) if (E/'upstream_visual_review_decisions.jsonl').exists() else 0
 check=E/'upstream_checks/DEDUP_REPORT.json'
 state['upstream_dedup']=json.loads(check.read_text()) if check.exists() else {'status':'running_or_pending'}
 exact=E/'upstream_checks/EXACT_HASH_REPORT.json'
 if exact.exists():state['upstream_exact_hash_audit']=json.loads(exact.read_text())
 structural=E/'upstream_checks/STRUCTURAL_AUDIT.json'
 if structural.exists():state['upstream_structural_audit']=json.loads(structural.read_text())
cross_pool=E/'CROSS_POOL_REPORT.json'
if cross_pool.exists():state['new_candidate_cross_pool_audit']=json.loads(cross_pool.read_text())
next_candidate=max(r['candidate'] for r in visual)+1
state['next_steps'][1]=f'Continue candidate visual review at C{next_candidate:04}; individually recheck held images recorded in visual ledger.'
draft=ROOT/'road_hazards_v5_clear_subset_draft_20261112'
if (draft/'release_info.json').exists():
 state['optional_clear_subset_draft']=json.loads((draft/'release_info.json').read_text())
 state['training_scope_choice']='awaiting_user_choice_between_clear_only_now_provisional_full_now_or_finish_13000_first'
policy_path=R/'training/TRAINING_POLICY.json'
if policy_path.exists():
 state['training_policy']=json.loads(policy_path.read_text())
 state['training_scope_choice']=state['training_policy']['mode']
(R/'PROJECT_STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
text=f'''# حالة Stage 40 — اقرأ الملف ده عند استكمال الشغل

آخر تحديث UTC: {state['updated_utc']}

## النسخة الحالية

`{Path(release['dataset']).name}` نسخة مراجعة محفوظة وليست إصدار تدريب نهائي.

- train: 10,562 صورة، validation: 830، test: 323؛ الإجمالي 11,715.
- كل الصور فُحصت: **960×720**. فحص البصمات وفك الصور والليبلز نجح.
- الفئات: `0 pothole` و`1 speed_bump`. ملفات YOLO تستخدم `class x_center y_center width height` بإحداثيات نسبية.
- التحويل المعتمد: `tools/std_dataset_v2.py`، قص 4:3 يحفظ كل البوكسات، أو letterbox عند الحاجة، مع إعداد تصحيح تمدد `sb15=1.7778`. الصور الإضافية تتبع نفس التحويل.
- مراجعة الأصول ونسخ upstream الأعلى دقة صححت قرارات سابقة. يوجد **149 صورة بليبلز غير محسومة**؛ لم تُحذف ولم تُعلن سليمة بالتخمين.
- بصمة المحتوى: `{release['content_fingerprint']}`.

## منع التسرب

`review/v5/no_leak_gate/REVIEWED_REPORT.json` يحفظ آخر نتيجة. فُحصت الصورة الموحّدة والأصلية مع 8 تحويلات قلب/دوران، وقورنت بيانات التدريب بالـvalidation/test والمراجع المحمية. فُحصت البصمات الأصلية والنهائية والجروبات وأسماء الفيديو الصريحة.

ظهر تشابهان تقريبيان؛ روجعا بصريًا وهما مشهدان مختلفان عن صورة الـvalidation، والتشابه تسببت فيه هوامش letterbox الرمادية. **صفر حالات تسرب مؤكدة وصفر تشابهات معلقة من هذا الفحص**. ده لا يثبت استحالة وجود مشاهد مشتركة لا تكشفها البصمات أو أسماء الملفات العامة. لم تُجرَ تنبؤات على test ولم تتغير صوره أو ليبلزه.

## الصور الجديدة والبوكسات

الهدف: **13,000 صورة train**؛ نحتاج 2,438 إضافة مقبولة، وليس مجرد زيادة أسماء الملفات.

- جُهز 2,420 مرشحًا محليًا غير مستخدم من RDD Japan/India، بمقاس 960×720.
- `review/v5/expansion13000/rdd_candidates/cNNNN.jpg`: الصور الموحّدة.
- `review/v5/expansion13000/rdd_candidates/proposed_labels/cNNNN.txt`: بوكسات المصدر بعد تحويل الإحداثيات، **مرشّحة وغير معتمدة بصريًا**.
- `review/v5/expansion13000/rdd_candidates/sheet_NNNN.jpg`: صور المعاينة بالبوكسات.
- فُحص أول **{len(visual)} مرشحًا**؛ `rdd_visual_review_decisions.jsonl` يسجل القرار وسبب رفض الترقيعات والشروخ والمناطق غير الواضحة.
- أول **4 صور و5 بوكسات** راجعتها محفوظة في `review/v5/expansion13000/reviewed_additions/`؛ `images/` للصور، `labels/` للـYOLO، و`annotated/` لمعاينات البوكسات. **C0039 مرفوضة** بعد تأكيد أنها نفس مشهد وصورة ضرر موجودة بالفعل في train من زاوية مجاورة؛ ملفاتها محفوظة كدليل. الثلاثة الباقية لها 4 بوكسات وما زالت معلقة لفحص جروبات المشاهد. **لم تُدمج أي إضافة في train**؛ اقرأ status داخل manifest.
- الدفعة الثانية `reviewed_additions_batch2/`: ثلاث صور negative مراجَعة فرديًا (C0005 وC0078 وC0109)، اتشالت بوكسات المصدر الخاطئة من الليبل النهائي لأنها شروخ/ترقيعات/دهان وليست الهدفين. ملفات YOLO الفارغة مقصودة. لم تظهر لها مطابقات مع المراجع الحالية أو المحمية أو المرشحين الآخرين في الفحص. المصدر الأولي محفوظ بدون تعديل، ولم تُدمج بعد في train.
- الدفعة الثالثة `reviewed_additions_batch3/`: صورتان لحفر مراجَعتان فرديًا (C0123 وC0151)، ببوكسين YOLO فعليين ومعاينات. حُذف بوكس التكسير المجاور لغطاء المرافق في C0151، مع حفظ الليبل الأولي والتاريخ. لا توجد لهما مطابقات في الفحص الحالي. لم تُدمجا في train.
- المصدر الأعلى دقة: `upstream_candidates/` فيه 2,623 فريمًا موحّدًا 960×720 من 131 فيديو، بعد استبعاد 442 فريمًا مستخدمًا و961 فريمًا من فيديوهات محمية. المصدر نفسه upstream لـBPO وليس بلدًا مستقلًا. فيه 430 ليبل مصدر موجب و2,193 ليبل مصدر فارغ؛ الفراغ لا يثبت أن الصورة negative لأن المصدر لا يوسم المطبات. 3 حالات بها بوكس مصدر أدق من بكسل ومعلّمة لإعادة وسم كاملة قبل أي قبول. فُحص أول {state.get('upstream_visual_screened_images',0)} فريمًا مبدئيًا. `upstream_checks/` يحفظ فحص البصمات: صفر مطابقات byte-for-byte، وصفر مطابقات مرشّحة مع المراجع المحمية، و33 صورة مرشّحة شبيهة بتدريب حالي، و331 زوجًا شبيهًا داخل المرشحين؛ المطابقات التقريبية تحتاج حسمًا بصريًا.
- `reviewed_upstream_batch1/`: صورتان negative راجعتها فرديًا (U0022 وU0033) بعد حسم الظلال والمخلفات من الأصل. ليبلز YOLO فارغة مقصودة، ومعاينات وأدلة محفوظة. U0010 وU0016 مرفوضتان بسبب غموض الشريط العرضي/الترقيع الرملي. لم تُدمج أي إضافة في train.
- `CROSS_POOL_REPORT.json`: فحص RDD المرشح مقابل upstream المرشح، بالأصل والصورة الموحّدة و8 تحويلات؛ صفر مطابقات مرشّحة عند الحدود المستخدمة. الفحص البنيوي لكل الـ2,623 صورة upstream نجح للدقة وفك الصور وهندسة الليبلز؛ الحالات الثلاث دون البكسل ما زالت ممنوعة قبل إعادة وسمها. هذه الفحوص لا تعني اعتماد الليبلز بصريًا.
- فحص التكرار على كل المرشحين: `tools/v5_expansion_dedup.py`؛ تقريره `DEDUP_REPORT.json` ومقارناته CSV. الحالة الحالية محفوظة في `review/v5/PROJECT_STATE.json`.

## الاستكمال

1. اقرأ `review/v5/PROJECT_STATE.json` ونتيجة منع التسرب والتكرار؛ راجع أي مطابقات جديدة بصريًا.
2. استكمل مراجعة المرشحين من C{next_candidate:04}. لا تعتبر بوكسات المصدر ground truth. راجع الصور المعلقة المذكورة في سجل القرارات.
3. احسم الـ149 حالة القديمة بدليل كافٍ؛ الملف `review/v5/pretrain/unresolved_review.csv` يحتوي الصور والأسباب. لا ترفع الثقة آليًا.
4. لا تضف نفس فريم BPO من d7k بنسختي 4K و640، ولا توزع نفس الفيديو بين splits. Czech/BD87 والمراجع المحمية تظل خارج التدريب.
5. ابنِ نسخة جديدة بعد قبول الإضافات. لا تعدل نسخ الداتا السابقة أو hardlinks مباشرة؛ اكتب الليبلز الجديدة بـatomic replace.
6. أعد فحص الدقة والبوكسات والبصمات والتسرب على النسخة النهائية. لا تبدأ تدريبًا على مجلد المرشحين.

## التدريب

**التدريب لم يبدأ.** البوكسات المعلقة والإضافات لم تنتهِ، والهدف 13,000 train لم يتحقق بعد. لا يوجد وعد بنتيجة أو داتا خالية 100% من الأخطاء.

بعد الجاهزية: أول تجربة YOLO11n pretrained بإعدادات baseline الموجودة: imgsz960، batch8، epochs70، patience20، workers2، seed0، deterministic=True، close_mosaic10. قياس mAP50 وmAP50-95 لكل فئة واختيار النموذج بالـvalidation. لا تستخدم `train.py` القديم لأنه يقيم test تلقائيًا، ولا تشغّل bat يشير لنسخة تصحيح قديمة.

تم تجهيز مسودة اختيارية `road_hazards_v5_clear_subset_draft_20261112`: train 10,413، validation 830، test 323. اجتازت فحص البصمات والدقة وفك الصور. تستبعد الـ149 المعلقة من **هذه المسودة فقط**، مع إبقائها كلها في النسخة الكاملة. ليست النسخة المختارة للتدريب.

**اختيار أحمد الصريح: انتظار اكتمال 13,000 صورة train مراجَعة.** السياسة محفوظة في `review/v5/training/TRAINING_POLICY.json`. لا تبدأ بالـ10,413 ولا بالـ10,562 المؤقتة. كمّل مراجعة الداتا والبوكسات والتكرار، وحافظ على إيقاف التدريب حتى الجاهزية. سكربت التدريب يمنع البدء على الإصدارات الحالية بموجب هذا الاختيار.

سكربت التدريب الجاهز: `tools/v5_train_selected.py`. يتطلب قرار سياسة الداتا في `review/v5/training/DATA_CHOICE.json`، يعيد فحص المحتوى والتسرب، ويستخدم YAML للتدريب والـvalidation فقط بدون مفتاح test. إعداداته baseline ولم يبدأ بعد. لا تكتب ملف اختيار نيابة عن المستخدم قبل إجابته.

الحالة الآلية: `review/v5/PROJECT_STATE.json`. هذا الملف لا يغير الداتا ولا يشغّل تدريبًا.
'''
(ROOT/'START_HERE_STAGE40.md').write_text(text,encoding='utf-8')
with (R/'PROGRESS.md').open('a',encoding='utf-8') as f:f.write(f"\n\n## Saved resumable state {state['updated_utc']}\nSee START_HERE_STAGE40.md and review/v5/PROJECT_STATE.json. Current train 10562; provisional existing labels 149; proposed addition labels {state['candidate_yolo_labels']}; visual screens {len(visual)}; staged review records {len(staged)}, including 1 rejected same-scene duplicate and {state['addition_reviewed_negative_images']} reviewed hard negatives; merged 0. Current release leakage candidates 2, both visually rejected as different scenes. Training not started; policy: {state.get('training_scope_choice','unselected')}.\n")
print(json.dumps({k:state[k] for k in ['current_dataset','current_train_images','unresolved_existing_labels','candidate_yolo_labels','addition_images_visually_screened','addition_images_staged','training_started']},indent=2))
