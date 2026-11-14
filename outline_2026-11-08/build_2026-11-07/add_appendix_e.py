"""Add Appendix E (data sources and licences) to the 7 Nov outline, point section 1.7 to it, and add the TOC /
list-of-tables lines. Input: final_2026-11-07b/src_copy.docx (copy of the 7 Nov file). Output:
final_2026-11-07b/Elreefy_Ahmed_23022692_Project_Outline.docx. Licences: configs/sources.yaml,
supervisor_2026-11-08/DATA.md, review/new_data_r3/CANDIDATES.md, Roboflow README files."""
import copy, sys, docx
from docx.shared import Emu
from docx.oxml.ns import qn

SRC = 'final_2026-11-07b/src_copy.docx'
OUT = 'final_2026-11-07b/Elreefy_Ahmed_23022692_Project_Outline.docx'
PG = sys.argv[1] if len(sys.argv) > 1 else '19'
d = docx.Document(SRC)
P = d.paragraphs

def set_text(par, text):
    runs = par.runs
    runs[0].text = text
    for r in runs[1:]:
        r._element.getparent().remove(r._element)

# 1) section 1.7 sentence
p91 = [p for p in P if p.text.startswith('Ethics. The project does not involve')][0]
r = p91.runs[1]
old = 'and every source is credited.'
assert old in r.text, r.text
r.text = r.text.replace(old, 'and every data source with its licence is listed in Appendix E.')

# 2) TOC + list of tables lines
tocD = [p for p in P if p.text.startswith('APPENDIX D: Pod Wiring Diagram\t')][0]
new = copy.deepcopy(tocD._p); tocD._p.addnext(new)
np_ = docx.text.paragraph.Paragraph(new, tocD._parent)
set_text(np_, f'APPENDIX E: Data Sources and Licences\t{PG}')
lt11 = [p for p in P if p.text.startswith('Table 11: Components to be used')][0]
new = copy.deepcopy(lt11._p); lt11._p.addnext(new)
np_ = docx.text.paragraph.Paragraph(new, lt11._parent)
set_text(np_, f'Table 12: Data sources used in the project and their licences\t{PG}')

# 3) Appendix E at the end (before sectPr)
P = d.paragraphs
hD = [p for p in P if p.style.name == 'Heading 1' and p.text.startswith('APPENDIX D')][0]
txtD = P[P.index(hD) + 1] if False else [p for p in P if p.text.startswith('The diagram uses net labels')][0]
capT11 = [p for p in P if p.style.name == 'Caption' and p.text.startswith('Table 11:')][0]
body = d.element.body
sectPr = body.find(qn('w:sectPr'))

def add_par(src, text):
    e = copy.deepcopy(src._p)
    sectPr.addprevious(e)
    par = docx.text.paragraph.Paragraph(e, body)
    set_text(par, text)
    return par

add_par(hD, 'APPENDIX E: Data Sources and Licences')
add_par(txtD, 'All road-hazard images used to train and test the hazard model come from public datasets. Each source is '
        'listed below with its provider and licence, and the same attribution will be given in the final report. Every '
        'source was checked for duplicates of the test images before use, and its own validation or test images were '
        'split by drive or location. No images of people were collected by the project.')
add_par(capT11, 'Table 12: Data sources used in the project and their licences')

rows = [
    ['Dataset (provider)', 'Region', 'Use in this project', 'Licence'],
    ['Humps, Bumps & Potholes v8, Roboflow Universe (detection-system)', 'Mixed (incl. an Egyptian drive)', 'Main train / validation / test set', 'CC BY 4.0'],
    ['Speed-Bump Detection v15, Roboflow Universe (speed-bump-detection)', 'Indonesia', 'Training', 'CC BY 4.0'],
    ['learnai-potholes-detection, GitHub (biodatlab)', 'Not stated', 'Main train / validation / test set', 'Not stated in the repository (to be confirmed)'],
    ['RDD2022 (Arya et al., 2022), Figshare', 'Japan, India; Czech Republic', 'Training (Japan, India); external test (Czech)', 'CC BY-SA 4.0'],
    ['Road Surface Irregularities Dataset (RSID), Zenodo 18789662', 'Lithuania', 'Training; unseen-country validation', 'CC BY 4.0'],
    ['Potholes dataset with YOLO annotations, Figshare 21214400', 'Slovakia', 'Training; unseen-country validation', 'CC BY 4.0'],
    ['speedregulator-road-hazards-and-speed-bumps, Kaggle (bensemanemohamedreda)', 'Mixed', 'Training', 'CC BY-SA 4.0'],
    ['SpeedBumps-Detection, GitHub (dm-druid)', 'China', 'Training', 'MIT'],
    ['Deteksi Polisi Tidur, Roboflow Universe (sca5a-kelompok-5)', 'Indonesia', 'Training; validation', 'CC BY 4.0'],
    ['REDUCTOR, Roboflow Universe (rompe)', 'Latin America', 'Training; validation', 'CC BY 4.0'],
    ['Speed Breaker Detection, Roboflow Universe (speedbreakerdatalabelling)', 'India', 'Training; validation', 'CC BY 4.0'],
    ['Road Hazard Detection 6, Roboflow Universe (thesis-grzdh)', 'India', 'Training', 'CC BY 4.0'],
    ['total, Roboflow Universe (ensam)', 'South Asia', 'Training', 'CC BY 4.0'],
    ['RDD, Roboflow Universe (road-damage-detection)', 'Egypt', 'Training; validation', 'CC BY 4.0'],
    ['BHARATPothole, Roboflow Universe (rahul-tripathi)', 'India', 'Training', 'CC BY 4.0'],
    ['BD_speedbreaker v2, Roboflow Universe (cse400)', 'Bangladesh', 'External test only (87 images)', 'CC BY 4.0'],
    ['COCO 2017, through the Ultralytics YOLO11n pretrained model', 'Worldwide', 'People and vehicle detection (not retrained)', 'COCO annotations CC BY 4.0; YOLO11n AGPL-3.0'],
]
src_tbl = d.tables[14]  # hazard table in Appendix C (same look)
tbl = copy.deepcopy(src_tbl._tbl)
sectPr.addprevious(tbl)
T = docx.table.Table(tbl, body)
# keep header + one body row as templates, 4 columns: drop the 5th column
for row in list(T.rows)[2:]:
    tbl.remove(row._tr)
def drop_last_col(tr):
    tcs = tr.findall(qn('w:tc')); tr.remove(tcs[-1])
for tr in tbl.findall(qn('w:tr')):
    drop_last_col(tr)
grid = tbl.find(qn('w:tblGrid')); gcs = grid.findall(qn('w:gridCol')); grid.remove(gcs[-1])
widths = [4300, 1500, 2100, 1600]  # twips, sum 9500
for gc, w in zip(grid.findall(qn('w:gridCol')), widths):
    gc.set(qn('w:w'), str(w))
tmpl = copy.deepcopy(tbl.findall(qn('w:tr'))[1])
tbl.remove(tbl.findall(qn('w:tr'))[1])
for _ in rows[1:]:
    tbl.append(copy.deepcopy(tmpl))
T = docx.table.Table(tbl, body)
for ri, (row, vals) in enumerate(zip(T.rows, rows)):
    for ci, (cell, v) in enumerate(zip(row.cells, vals)):
        tcPr = cell._tc.find(qn('w:tcPr'))
        tcW = tcPr.find(qn('w:tcW')) if tcPr is not None else None
        if tcW is not None:
            tcW.set(qn('w:w'), str(widths[ci])); tcW.set(qn('w:type'), 'dxa')
        par = cell.paragraphs[0]
        for extra in cell.paragraphs[1:]:
            extra._p.getparent().remove(extra._p)
        if par.runs:
            set_text(par, v)
        else:
            par.add_run(v)
tw = tbl.find(qn('w:tblPr')).find(qn('w:tblW'))
if tw is not None:
    tw.set(qn('w:w'), str(sum(widths))); tw.set(qn('w:type'), 'dxa')
d.save(OUT)
print('saved', OUT)
