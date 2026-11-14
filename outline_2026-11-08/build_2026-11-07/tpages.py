import subprocess, json, re
pdf = 'final/Elreefy_Ahmed_23022692_Project_Outline.pdf'
n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
txt = [subprocess.run(['pdftotext', '-f', str(i), '-l', str(i), '-layout', pdf, '-'], capture_output=True, text=True).stdout for i in range(1, n + 1)]
toc = next(i for i, t in enumerate(txt) if 'TABLE OF CONTENTS' in t)
keys = {'h1': r'^\s*1\.\s+INTRODUCTION', 'h11': r'^\s*1\.1\s+Project Background', 'h12': r'^\s*1\.2\s+Project Aim', 'h13': r'^\s*1\.3\s+Product Design',
        'h14': r'^\s*1\.4\s+Methodology', 'h15': r'^\s*1\.5\s+Concept', 'h16': r'^\s*1\.6\s+System Architecture', 'h17': r'^\s*1\.7\s+Health',
        'h18': r'^\s*1\.8\s+Sustainability', 'h2': r'^\s*2\.\s+SOURCES', 'h3': r'^\s*3\.\s+RESOURCE', 'h4': r'^\s*4\.\s+PROJECT PLAN', 'h41': r'^\s*4\.1\s+Project Work',
        'h42': r'^\s*4\.2\s+Critical', 'h43': r'^\s*4\.3\s+Threats', 'h5': r'^\s*5\.\s+REFERENCES', 'hA': r'APPENDIX A: Gantt', 'hB': r'APPENDIX B: Project',
        'hC': r'APPENDIX\s+C:', 'hD': r'APPENDIX D: Pod'}
for i in range(1, 10): keys[f'f{i}'] = rf'Figure {i}:'
for i in range(1, 12): keys[f't{i}'] = rf'Table {i}:'
phys = {}
for k, pat in keys.items():
    for p in range(toc + 1, n):
        if re.search(pat, txt[p], re.M): phys[k] = p + 1; break
off = phys['h1'] - 1
out = {k: v - off for k, v in phys.items()}
json.dump(out, open('tpages.json', 'w'))
print(out); print('chapters 1-4 pages:', out['h1'], '->', out['h5'] - (0 if txt[phys['h5']-1].strip().startswith('') else 0), 'refs page', out['h5'], 'total physical', n)
