#!/usr/bin/env python3
"""Postprocess available extended meshes; computes observed order without EB as exact truth."""
from pathlib import Path
import csv,math,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from compare_results import read_tip_uz,UZ_EB
root=Path(__file__).resolve().parent.parent
counts=[1,2,4,8,16,32,64]
rows=[]
for mode in ('off','on'):
 values={}
 for n in counts:
  file=root/'output'/f'mitc_locking_rect_B2_N{n:02d}_{mode}'/'response.txt'
  value=read_tip_uz(file)
  if value is not None:values[n]=value
 for n in counts:
  if n not in values:continue
  v=values[n];d1=values.get(n//2);d2=values.get(n//4)
  p=math.log2(abs((d2-d1)/(d1-v))) if d1 is not None and d2 is not None and v!=d1 and d2!=d1 else None
  rows.append({'mode':mode,'elements':n,'tip_uz_mm':v,'error_vs_EB_pct':abs((v-UZ_EB)/UZ_EB)*100,'delta_to_coarser_mm':v-d1 if d1 is not None else None,'observed_p':p})
dst=root/'mitc_tests'/'reports'/'mitc_B2_extended.csv';dst.parent.mkdir(parents=True,exist_ok=True)
with dst.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['mode','elements','tip_uz_mm','error_vs_EB_pct','delta_to_coarser_mm','observed_p']);w.writeheader();w.writerows(rows)
for r in rows:print(r)
print('Wrote',dst)
