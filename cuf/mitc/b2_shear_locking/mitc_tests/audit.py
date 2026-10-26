#!/usr/bin/env python3
"""Offline, reproducible audit of archived MITC B2 cases, outputs and logs."""
import csv, json, math, re, sys
from pathlib import Path
try:
 import yaml
except ImportError:
 sys.exit('PyYAML is required: python -m pip install PyYAML')
ROOT=Path(__file__).resolve().parent.parent
COUNTS=(1,2,4,8,16,32,64)
EB=-100*5000**3/(3*75000*(100*100**3/12))
issues=[]; rows=[]; by_mode={}
def check(ok,description):
 if not ok: issues.append(description)
def read_tip(path):
 matches=[]
 for line in path.read_text().splitlines():
  f=line.split()
  if len(f)>=8 and f[4]=='center':
   try: xs,x,y,z,uz=map(float,(f[0],f[1],f[2],f[3],f[7]))
   except ValueError: continue
   if all(abs(a-b)<tol for a,b,tol in [(xs,1,1e-9),(x,5000,1e-6),(y,0,1e-6),(z,0,1e-6)]): matches.append(uz)
 check(len(matches)==1,f'{path}: expected exactly one tip-center sample, found {len(matches)}')
 return matches[0] if matches else float('nan')
# Input physics control: configurations must differ only in MITC flags, case name, and output destination
for n in COUNTS:
 configs={}
 for mode in ('off','on'):
  name=f'mitc_locking_rect_B2_N{n:02d}_{mode}'
  cp=ROOT/'cases'/f'{name}.yaml'; case=yaml.safe_load(cp.read_text())
  configs[mode]=case
  bound=case['longitudinal']['element_boundaries']
  check(len(bound)==n+1 and all(abs(v-i/n)<1e-12 for i,v in enumerate(bound)),f'{name}: element boundaries not uniform {n}')
  check(case['longitudinal']['order']==1,f'{name}: not longitudinal B2')
  check(case['solver']['correctionMITC']==(mode=='on'),f'{name}: MITC flag wrong')
  check(case['solver']['verifyMITCAssembly']==(mode=='on'),f'{name}: verify flag wrong')
  check(case['cuf']['order']==2,f'{name}: transverse expansion unexpected')
  for section,fn in [('problem','yaml'),('cuf','basis'),('output','directory')]:
   if section=='cuf' or section=='output': ref=case[section][fn]
   else: ref=case[section][fn]
   if isinstance(ref,str) and ref.startswith('../'):
    check((cp.parent/ref).resolve().exists(),f'{name}: missing referenced file: {ref}')
  op=ROOT/'output'/name/'response.txt'; log=ROOT/'mitc_tests'/'logs'/f'{name}.log'
  check(op.exists(),f'{name}: response missing');check(log.exists(),f'{name}: log missing')
  if not op.exists() or not log.exists():continue
  uz=read_tip(op); content=log.read_text()
  check('[3/4] solve complete' in content,f'{name}: no solver completion marker')
  m=re.search(r'global stiffness symmetry: relative=([0-9.eE+-]+).*?rtol=([0-9.eE+-]+)',content)
  check(m is not None,f'{name}: no stiffness symmetry diagnostic')
  rel=float(m.group(1)) if m else None; tol=float(m.group(2)) if m else None
  if m:check(rel<=tol,f'{name}: stiffness symmetry failed')
  diagnostics=re.findall(r'\[MITC assembly verify\].*',content)
  if mode=='on':
   check(len(diagnostics)==n,f'{name}: expected {n} MITC verification lines, got {len(diagnostics)}')
   check(all('pair=(1,1)' in x and 'status=PASS' in x for x in diagnostics),f'{name}: MITC verification status or pair mismatch')
  else:check(len(diagnostics)==0,f'{name}: OFF contains MITC verification lines')
  check(re.search(r'CUF point load\] physical force \(N\): \(0, 0, -100\)',content) is not None,f'{name}: unexpected reported load')
  rows.append(dict(name=name,n=n,mode=mode,uz_mm=uz,error_vs_EB_pct=abs((uz-EB)/EB)*100,symmetry_rel=rel,mitc_checks=len(diagnostics)))
  by_mode[(n,mode)]=uz
 a,b=configs['off'],configs['on']
 for c in (a,b):
  c['case']['name']='X';c['output']['directory']='X';c['solver'].pop('correctionMITC',None);c['solver'].pop('verifyMITCAssembly',None)
 check(a==b,f'N{n:02d}: OFF/ON inputs differ beyond name, output and MITC flags')
# verify shared physical model and problem, not just case pointers
model=yaml.safe_load((ROOT/'models/mitc_locking_rect_conv_csf.yaml').read_text())
problem=yaml.safe_load((ROOT/'problems/mitc_locking_rect_conv_point.yaml').read_text())
check(problem['problem']['force']['amplitude']==-100.,'Fz not -100 N')
check([problem['problem']['force'][k] for k in ('x','y','z')]==[5000.,0.,0.],'force location mismatch')
sects=model['CSF']['sections'];check(set(sects)=={'S0','S1'},'unexpected CSF stations')
for s,z in [('S0',0),('S1',5000)]:
 check(sects[s]['z']==z,f'{s}: wrong location')
 check(sects[s]['polygons'][0]['weight']==75000,f'{s}: wrong E carrier')
 check(sects[s]['polygons'][0]['vertices']==[[-50.,-50.],[50.,-50.],[50.,50.],[-50.,50.]],f'{s}: wrong rectangle')
check(model['CSF']['shear_weight_laws']==['iso(0.33)'],'unexpected shear constitutive law')
for mode in ('off','on'):
 vals=[by_mode.get((n,mode)) for n in COUNTS]
 check(all(v is not None and math.isfinite(v) for v in vals),f'{mode}: missing/nonfinite displacement')
 if all(v is not None and math.isfinite(v) for v in vals):
  check(all(v<0 for v in vals),f'{mode}: unexpected displacement sign')
  check(all(abs(vals[i+1])>abs(vals[i]) for i in range(len(vals)-1)),f'{mode}: magnitude not increasing with refinement')
for n in COUNTS:
 if (n,'on') in by_mode and (n,'off') in by_mode:
  check(abs(by_mode[n,'on']-EB)<abs(by_mode[n,'off']-EB),f'N{n:02d}: ON not closer to EB')
report={'reference_EB_mm':EB,'scope':'Archived-output audit, not an independent solver rerun or proof of MITC correctness','status':'PASS' if not issues else 'FAIL','issues':issues,'runs':rows}
path=ROOT/'mitc_tests'/'reports'/'audit.json';path.parent.mkdir(exist_ok=True,parents=True);path.write_text(json.dumps(report,indent=2)+'\n')
print('Archived MITC B2 audit:',report['status'])
for r in rows:print(f"  {r['name']:<34} uz={r['uz_mm']:+.9f} mm  symmetry={r['symmetry_rel']}  MITC checks={r['mitc_checks']}")
for msg in issues:print('FAIL:',msg,file=sys.stderr)
print('Report:',path)
sys.exit(bool(issues))
