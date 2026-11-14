"""Fill the official Project Outline template with the outline content (content.json)."""
import copy, json, os, re, sys
import docx
from docx.shared import Pt, Cm, Emu, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

TPL = '/home/claude/tpl/T.docx'
C = json.load(open('content.json'))
TASKS = json.load(open('gantt_tasks2.json'))
PAGES = json.load(open('tpages.json')) if os.path.exists('tpages.json') else {}
TITLE = 'AI-Powered Multi-Modal Perception System for Autonomous Micro-Mobility Environmental Awareness'

d = docx.Document(TPL)
body = d.element.body

# ---------------- cover: replace placeholder texts in the text boxes ----------------
def set_cover():
    xml_ts = body.iter(qn('w:t'))
    for t in list(xml_ts):
        s = t.text or ''
        if s == 'BEng/BSc/MSc':
            t.text = 'BEng (Hons) Mechatronics Engineering'
        elif s.strip() == '* Delete as appropriate' or s == '* Delete as appropriate':
            t.text = ''
        elif s == 'Name':
            t.text = 'Name: Ahmed Mohamed Elsayed Elreefy (23022692)'
        elif s == 'Supervisor':
            t.text = 'Supervisor: Dr. Peter Makeen'
        elif s in ('Delete this before submission:', 'Page limit: 10 pages ', 'excluding appendices'):
            t.text = ''
        elif s == 'Project Title':
            t.text = TITLE
        elif s in (' in', 'Arial Bold 21pt'):
            t.text = ''
        elif s == 'Date':
            t.text = '8 November 2026'
    # the "Delete as appropriate" may be split; clear any red run text containing it
    for t in body.iter(qn('w:t')):
        if t.text and 'Delete as appropriate' in t.text:
            t.text = ''
set_cover()

def fix_cover_title():
    for tb in body.iter(qn('w:txbxContent')):
        ps = list(tb.iter(qn('w:p')))
        for p in ps:
            txt = ''.join(t.text or '' for t in p.iter(qn('w:t')))
            szs = [e.get(qn('w:val')) for e in p.iter(qn('w:sz'))]
            if TITLE in txt:
                ppr = p.find(qn('w:pPr'))
                jc = OxmlElement('w:jc'); jc.set(qn('w:val'), 'left')
                spc = OxmlElement('w:spacing'); spc.set(qn('w:line'), '240'); spc.set(qn('w:lineRule'), 'auto'); spc.set(qn('w:after'), '120')
                ppr.insert(0, spc); ppr.append(jc)
                # keep order valid: spacing before ind, jc after ind
                ind = ppr.find(qn('w:ind'))
                if ind is not None:
                    ppr.remove(spc); ind.addprevious(spc); ppr.remove(jc); ind.addnext(jc)
            elif txt == '' and '42' in szs:
                tb.remove(p) if p.getparent() is tb else p.getparent().remove(p)
fix_cover_title()

# ---------------- remove template body from "INTRODUCTION" to the end ----------------
paras = list(body.iterchildren())
start = None
for i, el in enumerate(paras):
    if el.tag == qn('w:p') and ''.join(x.text or '' for x in el.iter(qn('w:t'))).strip() == 'INTRODUCTION':
        start = i; break
final_sectPr = paras[-1]
assert final_sectPr.tag == qn('w:sectPr')
for el in paras[start:-1]:
    body.remove(el)
# template appendix heading pPr (unnumbered Heading 1 with page break) for reuse
APP_PPR = '<w:pPr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:pStyle w:val="Heading1"/><w:pageBreakBefore/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr><w:ind w:left="357" w:hanging="357"/><w:jc w:val="left"/></w:pPr>'

# ---------------- helpers that append before the final sectPr ----------------
def _append(el):
    final_sectPr.addprevious(el)
    return el

def new_par(style=None):
    p = d.add_paragraph(style=style)  # appended at end (after sectPr? python-docx inserts before sectPr)
    return p

def runs_into(p, runs, size=None, base_bold=False):
    for rr in runs:
        txt = rr.get('t', '')
        if not txt:
            continue
        run = p.add_run(txt)
        if rr.get('bold') or base_bold:
            run.bold = True
        if rr.get('italics'):
            run.italic = True
        if size:
            run.font.size = Pt(size)
    return p

def para(runs, align=None, size=None, space_after=6, line=None, style=None):
    p = d.add_paragraph(style=style)
    runs_into(p, runs, size)
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    if line:
        pf.line_spacing = line
    if align is not None:
        pf.alignment = align
    return p

def bullet(runs):
    p = d.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.63); pf.first_line_indent = Cm(-0.4); pf.space_after = Pt(3)
    p.add_run('•\t')
    pf.tab_stops.add_tab_stop(Cm(0.63))
    runs_into(p, runs)
    return p

def heading(text, lvl):
    return d.add_paragraph(text, style=f'Heading {lvl}')

def app_heading(text, page_break=True):
    p = d.add_paragraph(text, style='Heading 1')
    ppr = p._p.get_or_add_pPr()
    from lxml import etree
    new = etree.fromstring(APP_PPR)
    if not page_break:
        new.remove(new.find(qn('w:pageBreakBefore')))
    p._p.remove(ppr); p._p.insert(0, new)
    return p

def caption(text):
    p = d.add_paragraph(style='Caption')
    p.add_run(text)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    return p

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), fill)
    tcPr.append(sh)

def table(rows, widths_dxa, size=8, center=False, total_dxa=8306):
    scale = min(1.0, total_dxa / sum(widths_dxa))
    widths = [int(w * scale) for w in widths_dxa]
    t = d.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = d.styles['Table Grid']
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, row in enumerate(rows):
        tr = t.rows[i]._tr
        trPr = tr.get_or_add_trPr()
        cs = OxmlElement('w:cantSplit'); trPr.append(cs)
        if i == 0:
            th = OxmlElement('w:tblHeader'); trPr.append(th)
        for j, c in enumerate(row):
            cell = t.cell(i, j)
            cell.width = Emu(widths[j] * 635)
            txt = c['t'] if isinstance(c, dict) else str(c)
            bold = (i == 0) or (isinstance(c, dict) and c.get('bold'))
            fill = 'D9E2F3' if i == 0 else (c.get('fill') if isinstance(c, dict) else None)
            if fill:
                shade(cell, fill)
            lines = txt.split('\n')
            p0 = cell.paragraphs[0]
            for k, line in enumerate(lines):
                p = p0 if k == 0 else cell.add_paragraph()
                pf = p.paragraph_format
                pf.space_after = Pt(0); pf.space_before = Pt(0); pf.line_spacing = 1.0
                pf.alignment = WD_ALIGN_PARAGRAPH.CENTER if (center and j > 0) else WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(line); r.font.size = Pt(size); r.bold = bool(bold)
    # grid widths
    grid = t._tbl.tblGrid
    for j, gc in enumerate(grid.findall(qn('w:gridCol'))):
        gc.set(qn('w:w'), str(widths[j]))
    d.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

def image(file, width_cm):
    p = d.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    p.add_run().add_picture('fig/' + file, width=Cm(width_cm))
    return p

def section_break(landscape=False, restart=None, fmt=None, title_pg=False):
    """End the current section at a new empty paragraph. Properties describe the section that ENDS here."""
    p = d.add_paragraph()
    sp = copy.deepcopy(final_sectPr)
    pg = sp.find(qn('w:pgSz')); mar = sp.find(qn('w:pgMar'))
    if landscape:
        pg.set(qn('w:w'), '16838'); pg.set(qn('w:h'), '11906'); pg.set(qn('w:orient'), 'landscape')
        mar.set(qn('w:left'), '1134'); mar.set(qn('w:right'), '1134'); mar.set(qn('w:top'), '1134'); mar.set(qn('w:bottom'), '1134')
    pn = sp.find(qn('w:pgNumType'))
    if pn is not None:
        sp.remove(pn)
    if restart is not None or fmt:
        pn = OxmlElement('w:pgNumType')
        if fmt: pn.set(qn('w:fmt'), fmt)
        if restart is not None: pn.set(qn('w:start'), str(restart))
        sp.find(qn('w:pgMar')).addnext(pn)
    tp = sp.find(qn('w:titlePg'))
    if tp is not None and not title_pg:
        sp.remove(tp)
    p._p.get_or_add_pPr().append(sp)
    return p

# ---------------- TOC page (after cover) ----------------
def toc_line(text, key, indent_cm=0.0, bold=False):
    p = d.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(indent_cm); pf.space_after = Pt(1); pf.line_spacing = 1.15
    pf.tab_stops.add_tab_stop(Cm(14.6), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    r = p.add_run(text); r.bold = bold; r.font.size = Pt(9.5)
    r2 = p.add_run('\t' + str(PAGES.get(key, '#'))); r2.bold = bold; r2.font.size = Pt(9.5)

# first, force a page break after the cover (keep template cover as is)
p = para([{'t': 'TABLE OF CONTENTS', 'bold': True}], size=13, space_after=8)
TOC = [('1. INTRODUCTION', 'h1', 0, True), ('1.1  Project Background and Justification', 'h11', 0.5, False),
       ('1.2  Project Aim and Objectives', 'h12', 0.5, False), ('1.3  Product Design Specification (PDS)', 'h13', 0.5, False),
       ('1.4  Methodology (VDI 2206)', 'h14', 0.5, False), ('1.5  Concept Generation and Selection', 'h15', 0.5, False),
       ('1.6  System Architecture and Circuit', 'h16', 0.5, False), ('1.7  Health, Safety and Ethics', 'h17', 0.5, False),
       ('1.8  Sustainability Analysis', 'h18', 0.5, False), ('2. SOURCES OF INFORMATION', 'h2', 0, True),
       ('3. RESOURCE ANALYSIS', 'h3', 0, True), ('4. PROJECT PLAN', 'h4', 0, True),
       ('4.1  Project Work Description and Progress to Date', 'h41', 0.5, False), ('4.2  Critical Path Analysis', 'h42', 0.5, False),
       ('4.3  Threats and Contingency Plan', 'h43', 0.5, False), ('5. REFERENCES', 'h5', 0, True),
       ('APPENDIX A: Gantt Chart', 'hA', 0, True), ('APPENDIX B: Project Resources Checklist', 'hB', 0, True),
       ('APPENDIX C: Project Risk, Ethics and Threat Assessment Checklist', 'hC', 0, True), ('APPENDIX D: Pod Wiring Diagram', 'hD', 0, True)]
for t_, k, ind, b in TOC:
    toc_line(t_, k, ind, b)
para([{'t': 'TABLE OF FIGURES', 'bold': True}], size=13, space_after=6).paragraph_format.space_before = Pt(10)
for i, f in enumerate(C['figs']):
    toc_line(f'Figure {i+1}: {f}', f'f{i+1}')
para([{'t': 'LIST OF TABLES', 'bold': True}], size=13, space_after=6).paragraph_format.space_before = Pt(10)
for i, f in enumerate(C['tabs']):
    toc_line(f'Table {i+1}: {f}', f't{i+1}')
section_break(fmt='lowerRoman', restart=0, title_pg=True)   # cover + contents section

# ---------------- body ----------------
IMG_W = {'vmodel.jpg': 13.0, 'architecture.jpg': 14.6, 'platform.jpg': 8.0}
def emit(items):
    for it in items:
        k = it['k']
        if k == 'h1':
            heading(it['t'], 1)
        elif k == 'h2':
            heading(it['t'], 2)
        elif k == 'p':
            para(it['runs'])
        elif k == 'bullet':
            bullet(it['runs'])
        elif k == 'tcap':
            c = caption(f"Table {it['n']}: {it['caption']}"); c.paragraph_format.keep_with_next = True
        elif k == 'table':
            table(it['rows'], it['widths'], size=7.5 if len(it['rows'][0]) >= 5 else 8, center=it['opt'].get('center', False))
        elif k == 'img':
            image(it['file'], IMG_W.get(it['file'], 14.0))
            caption(f"Figure {it['n']}: {it['caption']}")
        elif k == 'sp':
            pass

body_items = C['body']
# references: smaller, hanging indent, single spacing
ref_start = next(i for i, x in enumerate(body_items) if x['k'] == 'h1' and x['t'] == 'REFERENCES')
emit(body_items[:ref_start + 1])
for it in body_items[ref_start + 1:]:
    if it['k'] == 'p':
        p = para(it['runs'], size=9, space_after=4, line=1.0)
        p.paragraph_format.left_indent = Cm(0.7); p.paragraph_format.first_line_indent = Cm(-0.7)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
section_break(restart=1)  # chapters section (page 1 = Chapter 1)

# ---------------- Appendix A (landscape) ----------------
app_heading('APPENDIX A: Gantt Chart', page_break=False)
para([{'t': 'The Gantt chart was planned from the start of the project (5 Oct 2026) to the defence (May 2027). Grey = completed, orange = in progress, red = planned on the critical path, blue = planned not critical, hatched = buffer, diamonds = milestones and decision gates. Dependencies are finish-to-start unless marked SS (start-to-start).'}], size=9, space_after=4, line=1.0)
image('gantt.jpg', 20.0)
caption(f"Figure 4: {C['figs'][3]}")
caption(f'Table {[i for i,x in enumerate(C["tabs"]) if x.startswith("Gantt chart task list")][0]+1}: Gantt chart task list (each task ≤ 2 weeks; CP = on the critical path; SS = start-to-start)').paragraph_format.keep_with_next = True
rows = [['ID', 'Task', 'Duration', 'Start', 'Finish', 'Predecessors', 'Measurable outcome', 'CP', 'Status']]
for t in TASKS:
    if t[6] == 'head':
        rows.append([{'t': '', 'fill': 'EDEDED'}, {'t': t[1], 'bold': True, 'fill': 'EDEDED'}] + [{'t': '', 'fill': 'EDEDED'}] * 7)
        continue
    st = {'done': 'Done', 'prog': 'In progress', 'plan': 'Planned', 'buffer': 'Buffer', 'ms': 'Milestone'}[t[6]]
    rows.append([t[0], t[1], t[7], t[2], t[3], t[8], t[4] or '—', 'Yes' if t[5] else '', st])
table(rows, [550, 4450, 950, 800, 800, 1300, 3300, 550, 1000], size=7.5, total_dxa=14570)
section_break(landscape=True)

# ---------------- Appendices B, C, D (portrait) ----------------
def emit_app(items, first_heading):
    for it in items:
        if it['k'] == 'apph':
            app_heading(''.join(r['t'] for r in it['runs']))
        elif it['k'] == 'p':
            para(it['runs'], size=9, line=1.15)
        elif it['k'] == 'table':
            table(it['rows'], it['widths'], size=8)
        elif it['k'] == 'img':
            image(it['file'], 15.5)
            caption(f"Figure {it['n']}: {it['caption']}")
        elif it['k'] == 'tcap':
            caption(f"Table {it['n']}: {it['caption']}")
emit_app(C['appB'], True)
emit_app(C['appC'], True)
emit_app(C['appD'], True)

# final section: plain portrait, continue numbering
pn = final_sectPr.find(qn('w:pgNumType'))
if pn is not None: final_sectPr.remove(pn)
tp = final_sectPr.find(qn('w:titlePg'))
if tp is not None: final_sectPr.remove(tp)

# header text
for sec in d.sections:
    for hdr in (sec.header,):
        for t in hdr._element.iter(qn('w:t')):
            if t.text and 'MEng/BEng/BSc' in t.text:
                t.text = t.text.replace('*MEng/BEng/BSc', 'BEng').replace('MEng/BEng/BSc', 'BEng')
            elif t.text and t.text.strip() == '*':
                t.text = ''
# core properties
d.core_properties.author = 'Ahmed Elreefy'
d.core_properties.title = 'Project Outline – ' + TITLE
out = 'Elreefy_Ahmed_23022692_Project_Outline.docx'
os.makedirs('final', exist_ok=True)
d.save('final/' + out)
print('saved')
