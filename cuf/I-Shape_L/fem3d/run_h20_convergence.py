#!/usr/bin/env python3
"""Reproducible H20 mesh-convergence series for I-Shape_L.

Runs the sibling H20 driver on a sequence of meshes, recording displacements,
relative changes, nodal load equilibrium, and independent strong residual metrics.
No H20 numerical results are hardcoded. Interrupted runs may resume.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
from h20_strong_residual import measure

QUICK=[
    ('T0',3,1,2,1,1,4),
    ('T1',6,1,2,1,2,4),
    ('T2',12,2,4,2,2,8),
    ('T3',24,2,4,2,2,8),
    ('T4',48,2,4,2,2,8),
    ('T6',72,2,4,2,2,8),
]
PRODUCTION=[
    ('P0',20,2,4,2,3,12),
    ('P1',40,3,6,3,4,20),
    ('P2',60,4,8,4,6,28),
]
FIELDS=('level','nx','ny_left','ny_web','ny_right','nz_flange','nz_web',
        'nodes','elements','min_uz_mm','rel_change_uz','rel_change_pct',
        'total_Fz_N','r_x_rms','r_y_rms','r_z_rms','r_norm_rms',
        'r_z_median_abs','seconds','status','npz')


def parse_level(s):
    p=s.split(':')
    if len(p)!=7:raise argparse.ArgumentTypeError('Expected NAME:nx:ny-left:ny-web:ny-right:nz-flange:nz-web')
    try:return (p[0],*(int(v) for v in p[1:]))
    except ValueError as exc:raise argparse.ArgumentTypeError(str(exc)) from exc


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('model',type=Path,help='original 3-polygon CSF YAML')
    ap.add_argument('--output-dir',type=Path,default=Path('fem3d/output/h20_convergence'))
    ap.add_argument('--profile',choices=('quick','production'),default='quick')
    ap.add_argument('--level',type=parse_level,action='append',
                    help='repeat NAME:nx:ny-left:ny-web:ny-right:nz-flange:nz-web')
    ap.add_argument('--amplitude',type=float,default=-1.)
    ap.add_argument('--mesh-only',action='store_true')
    ap.add_argument('--backend',choices=('opensees','scipy'),default='scipy')
    ap.add_argument('--force',action='store_true',help='redo previously solved levels')
    ap.add_argument('--max-elements',type=int,default=0,
                    help='elements sampled for interior strong residual, 0=all')
    ap.add_argument('--residual-gauss',type=int,default=1,choices=(1,2,3))
    ap.add_argument('--tol-pct',type=float,default=.1,
                    help='convergence target for min uz between consecutive levels')
    a=ap.parse_args()
    levels=a.level or (QUICK if a.profile=='quick' else PRODUCTION)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    records=[]
    prev_uz=None
    for level,nx,ny_left,ny_web,ny_right,nz_flange,nz_web in levels:
        dest=a.output_dir/f'{level}_h20.npz'
        cmd=[sys.executable,str(Path(__file__).with_name('run_bending_fem3d_h20.py')),
             str(a.model),str(dest),'--nx',str(nx),'--ny-left',str(ny_left),
             '--ny-web',str(ny_web),'--ny-right',str(ny_right),
             '--nz-flange',str(nz_flange),'--nz-web',str(nz_web),
             '--amplitude',str(a.amplitude),'--backend',a.backend]
        if a.mesh_only:cmd+=['--mesh-only']
        t=time.monotonic()
        must_run = a.force or not dest.exists()
        if dest.exists() and not a.mesh_only:
            with np.load(dest,allow_pickle=False) as prev:
                must_run = must_run or prev['displacement'].size == 0
        if must_run:
            print('Running',level,flush=True)
            with (a.output_dir/f'{level}.log').open('w',encoding='utf-8') as log:
                run=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=False)
            if run.returncode:
                raise RuntimeError(f'{level} failed (exit {run.returncode}); see {a.output_dir}/{level}.log')
        elapsed=time.monotonic()-t
        with np.load(dest,allow_pickle=False) as d:
            nodes=d['nodes'];elems=d['elements'];u=d['displacement']
            total=float(d['nodal_loads'][:,2].sum())
        if not u.size:
            uz=float('nan');change=float('nan');pct=float('nan');m=None
            status='MESH-ONLY'
        else:
            uz=float(u[:,2].min())
            change=(abs(uz-prev_uz)/max(abs(prev_uz),1e-16) if prev_uz is not None else float('nan'))
            pct=100*change
            m=measure(dest,max_elements=a.max_elements,gauss=a.residual_gauss)
            (a.output_dir/f'{level}_strong_residual.json').write_text(json.dumps(m,indent=2)+'\n')
            status=('STABLE_MIN_UZ' if np.isfinite(pct) and pct<=a.tol_pct else 'CHECK_REFINEMENT')
            prev_uz=uz
        record=dict(level=level,nx=nx,ny_left=ny_left,ny_web=ny_web,ny_right=ny_right,
                    nz_flange=nz_flange,nz_web=nz_web,nodes=len(nodes),elements=len(elems),
                    min_uz_mm=uz,rel_change_uz=change,rel_change_pct=pct,
                    total_Fz_N=total,
                    r_x_rms=m['metrics']['x']['rms'] if m else float('nan'),
                    r_y_rms=m['metrics']['y']['rms'] if m else float('nan'),
                    r_z_rms=m['metrics']['z']['rms'] if m else float('nan'),
                    r_norm_rms=m['metrics']['norm']['rms'] if m else float('nan'),
                    r_z_median_abs=m['metrics']['z']['median_abs'] if m else float('nan'),
                    seconds=elapsed,status=status,npz=str(dest))
        records.append(record)
        with (a.output_dir/'convergence.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(records)
        print(level,'elements',len(elems),'min uz',uz,'delta %',pct,
              'rz rms',record['r_z_rms'],'Fz',total,'status',status,flush=True)
    report=['# H20 convergence study','',
      'Same physical geometry, materials, supports and surface load across all mesh levels.',
      'H20 internal stress divergence estimated by physical-volume-weighted quadrature.',
      'Element interfaces and surface traction residual are NOT included in this diagnostic.',
      f'Interior residual subsample: max {a.max_elements} elements per mesh (0=all).','',
      '| Mesh | Elements | Nodes | min uz (mm) | Delta (%) | rms rx | rms ry | rms rz | rms norm | Status |',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in records:
        def fmt(v):return f'{v:.6g}' if np.isfinite(v) else '—'
        report.append(f"| {r['level']} | {r['elements']} | {r['nodes']} | {fmt(r['min_uz_mm'])} | {fmt(r['rel_change_pct'])} | {fmt(r['r_x_rms'])} | {fmt(r['r_y_rms'])} | {fmt(r['r_z_rms'])} | {fmt(r['r_norm_rms'])} | {r['status']} |")
    report+=['','A small change of a global displacement is a convergence indicator, not by itself a proof of local stress convergence.']
    (a.output_dir/'convergence.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print('Saved:',a.output_dir/'convergence.csv',a.output_dir/'convergence.md')

if __name__=='__main__':main()
