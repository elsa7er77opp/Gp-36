"""Update Table 6 (AI row), Table 7 and the two results paragraphs of the
5 Nov outline with the final C / WBF results (test used once, ledger uses 6-9).
Input: ../Elreefy_Ahmed_23022692_Project_Outline.docx (not modified).
Output: out/Elreefy_Ahmed_23022692_Project_Outline.docx
Numbers: review/metrics_r3/{val_r2_final,test_r2_final,test_bd87_final,partval_bucko_C,partval_rsid_C}/report.md"""
import copy, os, docx

SRC = '../Elreefy_Ahmed_23022692_Project_Outline.docx'
d = docx.Document(SRC)

def set_runs(par, parts):
    """parts = [(text, bold)]; reuse the first run's formatting."""
    base = par.runs[0]
    for r in par.runs[1:]:
        r._element.getparent().remove(r._element)
    base.text = parts[0][0]; base.bold = parts[0][1]
    prev = base
    for txt, b in parts[1:]:
        new = copy.deepcopy(base._element)
        prev._element.addnext(new)
        run = docx.text.run.Run(new, par)
        run.text = txt; run.bold = b
        prev = run

def set_cell(cell, parts):
    if isinstance(parts, str): parts = [(parts, False)]
    set_runs(cell.paragraphs[0], parts)

# ---- Table 6, AI accuracy row ----
t6 = d.tables[5]
row = [r for r in t6.rows if r.cells[0].text.startswith('Improve model accuracy')][0]
set_cell(row.cells[2], 'New sources in D1, D2, then C (10,562 training images): large gains on unseen countries; C and WBF chosen on validation and tested once (Table 7); model frozen by 29 Nov')

# ---- Table 7 ----
t7 = d.tables[6]
assert t7.rows[0].cells[0].text.startswith('Model (data')
set_cell(t7.rows[0].cells[5], [('Test, used once (pothole / bump; 323–324 img)', True)])
B = True
rows = [
    ['v1 (v3a_r1)', '0.628', '0.710', '0.399', '0.028', [('0.660 / 0.354', False)]],
    ['Run A (cleaned labels, v3a_r2)', '0.605', '0.725', '0.422', '0.036', [('0.631 / 0.294', False)]],
    ['D1 (+ RSID, Bučko, RDD2022)', '0.596', '0.710', '0.571', '0.670', [('not tested', False)]],
    ['D2 (+ Malaysia/Indonesia data)', '0.615', '0.683', '0.617', '0.630', [('not tested', False)]],
    ['C (all sources, 10,562 img)', '0.639', '0.703', [('0.636', B)], [('0.680', B)], [('0.711', B), (' / 0.320', False)]],
    ['WBF (C + v1, two models)', [('0.676', B)], [('0.752', B)], 'not measured', 'not measured', [('0.698 / ', False), ('0.463', B)]],
]
# 5 data rows exist; add one more by copying the last one
tr_last = t7.rows[-1]._tr
tr_last.addnext(copy.deepcopy(tr_last))
assert len(t7.rows) == 7
for r, vals in zip(t7.rows[1:], rows):
    for c, v in zip(r.cells, vals):
        set_cell(c, v)

# ---- paragraphs ----
P = d.paragraphs
p1 = [p for p in P if p.text.startswith('Table 7 summarises')][0]
p2 = [p for p in P if p.text.startswith('The supervisor target of 0.90')][0]
set_runs(p1, [('Table 7 summarises the leak-free results (YOLO11n, image size 960). On the main validation set the single models are close (0.60–0.64 AP50 for potholes, 0.68–0.73 for speed bumps; seed-to-seed difference about ±0.01–0.02). The clear gain from new public sources is on countries never used in training: Lithuanian speed bumps rose from 0.028 (v1) to 0.680 (C) and Slovak potholes from 0.399 to 0.636. Model C (all sources) and the weighted boxes fusion (WBF) of C and v1 were chosen on validation and tested once each. On the test set, C raised potholes from 0.631 (Run A) to 0.711 and WBF raised speed bumps from 0.294 to 0.463; on 87 external speed-bump images (Bangladesh), C reached 0.731 (Run A 0.367).', None)])
set_runs(p2, [('The supervisor target of 0.90 per-class mAP50 has not been reached. Two per-class metrics defined before testing pass 0.90 with C: pothole image-level accuracy on the test set (0.938; its 152 images without potholes contain speed bumps) and speed-bump precision at 50 % recall on the Bangladesh set (0.936). The main weakness is near, unmarked Egyptian bumps: C finds 25 % of the near test bumps (WBF 39 %), as public data has few of them. WBF needs two models and its speed is not yet measured, so C or WBF is chosen at gate G1b (29 Nov).', None)])

os.makedirs('out', exist_ok=True)
d.save('out/Elreefy_Ahmed_23022692_Project_Outline.docx')
print('saved')
