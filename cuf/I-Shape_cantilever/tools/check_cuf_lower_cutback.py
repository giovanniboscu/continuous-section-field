#!/usr/bin/env python3
"""Progressive clamped-end exclusion for the loaded lower surface of a CUF case.

For each cutoff c measured from the clamp, integrate exactly the remaining
physical loaded surface x in [x0+c,x1], using the SHARED stress traction kernel
in tools/check_cuf_single_tensor_surface.py. The integration is divided only
at CUF element boundaries and the requested cutoffs for exact integration
limits. It does not omit Gaussian samples or interpolate the CSF geometry.

The primary comparison is the normal-force resultant. Vertical-force results
are included as a useful cross-check because the adapter prescribes a GLOBAL-Z
load per projected XY area (not a pressure normal to the tilted surface).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from check_cuf_single_tensor_surface import (
    _load_resources,
    _edges_affine_csf,
    loaded_surface_samples,
    integrate_stress,
    integrate_prescribed_load,
)


def _cutoffs(spec: str, length: float) -> list[float]:
    try:
        values = [float(s.strip()) for s in spec.split(',')]
    except ValueError as exc:
        raise ValueError('--exclude-mm must contain comma-separated numbers') from exc
    if not values or not np.all(np.isfinite(values)):
        raise ValueError('--exclude-mm must contain finite numbers')
    if any(v < 0. or v >= length for v in values):
        raise ValueError(f'Exclusions must be >= 0 and < beam length {length:.6g} mm')
    values = sorted(values)
    if not np.isclose(values[0], 0., rtol=0, atol=1e-12):
        values.insert(0,0.)  # Always report the entire surface as reference.
    if any(b-a < 1e-10 for a,b in zip(values,values[1:])):
        raise ValueError('Duplicate or indistinguishable cutoff positions')
    return values


def _partition(starts, ends, cut_x, x0, x1):
    points = [float(x0), float(x1)]
    points.extend(map(float,starts))
    points.extend(map(float,ends))
    points.extend(map(float,cut_x))
    points.sort()
    distinct=[]
    for x in points:
        if not distinct or x-distinct[-1] > 1e-9:
            distinct.append(x)
    if abs(distinct[0]-x0)>1e-9 or abs(distinct[-1]-x1)>1e-9:
        raise ValueError('Partition extends outside CSF longitudinal domain')
    return list(zip(distinct[:-1],distinct[1:]))


def _dump_plot(rows, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    x = np.array([r['excluded_mm'] for r in rows])
    normal = np.array([r['normal_relative_difference_percent'] for r in rows])
    vertical = np.array([r['vertical_relative_difference_percent'] for r in rows])
    fig, ax = plt.subplots(figsize=(8.2,4.9))
    ax.plot(x, normal, 'o-', label='Normal resultant |CUF - load| / |load|')
    ax.plot(x, vertical, 's--', label='Vertical resultant |CUF - load| / |load|')
    ax.set(xlabel='Excluded distance from clamp [mm]',ylabel='Difference over remaining loaded surface [%]',
           title='CUF vs prescribed load: progressive exclusion of clamped-end zone')
    ax.grid(alpha=.25)
    ax.legend(loc='best')
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run(args):
    context = _load_resources(args.case.resolve(), args.npz)
    case = context['case']
    field = context['field']
    bridge = context['bridge']
    stress_v10 = context['stress_v10']
    load = context['load']
    x0, x1 = context['x0'], context['x1']
    starts, ends = context['starts'],context['ends']
    faces = context['faces']
    provider = bridge.section_provider
    length = x1-x0
    distances = _cutoffs(args.exclude_mm, length)
    cuts = [float(x0+d) for d in distances]
    nx = int(load.axial_gauss if args.axial_gauss is None else args.axial_gauss)
    nt = int(load.edge_gauss if args.edge_gauss is None else args.edge_gauss)
    if nx<2 or nt<2: raise ValueError('Gauss orders must be at least 2')
    intervals = _partition(starts,ends,cuts,x0,x1)
    nodes = np.polynomial.legendre.leggauss(nx)[0]
    stations = [float((a+b)/2 + (b-a)*q/2) for a,b in intervals for q in nodes]
    lookups = stress_v10.validate_checkpoint_domain_lookups(field,bridge.field,stations)
    if any(lookups.get(x) is None for x in stations):
        raise ValueError('Cannot match CUF NPZ and physical CSF domains')
    speeds = _edges_affine_csf(provider,faces,x0,x1,
             [x0+f*length for f in (0.25,0.5,0.75)]+stations)
    origin = np.array([x0,0.,0.])
    segments=[]
    for i,interval in enumerate(intervals,1):
        samples = loaded_surface_samples(provider,faces,[interval],speeds,nx,nt)
        stresses = integrate_stress(samples,field,bridge,stress_v10,lookups,origin)
        loads = integrate_prescribed_load(
            loaded_surface_samples(provider,faces,[interval],speeds,nx,nt),origin,
            require_coplanar=True)
        if not np.allclose(stresses['n'],loads['n'],rtol=0,atol=1e-10):
            raise ValueError('Normal orientation mismatch in segment')
        segments.append({'a':interval[0], 'b':interval[1], 'sigma':stresses, 'load':loads})
        print(f'  integration segment {i:02d}/{len(intervals):02d}: x={interval[0]:.6g}..{interval[1]:.6g}',flush=True)

    rows=[]
    for distance,cut in zip(distances,cuts):
        chunks=[seg for seg in segments if seg['a']>=cut-1e-9]
        if not chunks: raise ValueError('No remaining surface beyond cutoff')
        fload_norm=sum(s['load']['F_normal'] for s in chunks)
        fsigma_norm=sum(s['sigma']['F_normal'] for s in chunks)
        fload_z=sum(s['load']['F'][2] for s in chunks)
        fsigma_z=sum(s['sigma']['F'][2] for s in chunks)
        row={
            'excluded_mm':float(distance),
            'remaining_length_mm':float(x1-cut),
            'remaining_area_mm2':float(sum(s['sigma']['area'] for s in chunks)),
            'samples':int(sum(s['sigma']['samples'] for s in chunks)),
            'Fnormal_load_N':float(fload_norm),
            'Fnormal_sigma_N':float(fsigma_norm),
            'normal_difference_N':float(fsigma_norm-fload_norm),
            'normal_relative_difference_percent':float(100*abs(fsigma_norm-fload_norm)/abs(fload_norm)),
            'Fz_load_N':float(fload_z),
            'Fz_sigma_N':float(fsigma_z),
            'vertical_difference_N':float(fsigma_z-fload_z),
            'vertical_relative_difference_percent':float(100*abs(fsigma_z-fload_z)/abs(fload_z)),
            'Fx_sigma_N':float(sum(s['sigma']['F'][0] for s in chunks)),
        }
        rows.append(row)

    outroot = args.output_root or (args.case.resolve().parent.parent.parent/'diagnostics'/
                                   'cuf_loaded_surface_cutback'/case.name)
    outroot=outroot.resolve()
    outroot.mkdir(parents=True,exist_ok=True)
    for n in range(1,10000):
        out=outroot/f'run_{n:04d}'
        try:
            out.mkdir()
            break
        except FileExistsError:
            pass
    else: raise RuntimeError('No available output run number')
    with (out/'cutback.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    result={'case':case.name,'checkpoint':str(context['checkpoint']),
            'checkpoint_sha256':hashlib.sha256(context['checkpoint'].read_bytes()).hexdigest(),
            'model':str(context['problem'].model_path),
            'stress_module':str(Path(stress_v10.__file__).resolve()),
            'method':'Same stress_traction_increment and CSF loaded_surface_samples as single-tensor script; exact x cut by splitting CUF quadrature intervals',
            'normal_is_projection_of_global_vertical_load':True,
            'gauss_x':nx,'gauss_edge':nt,'cuts':rows}
    (out/'cutback.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    try:
        _dump_plot(rows,out/'cutback.png')
        plot_message='cutback.png'
    except ImportError:
        plot_message='(matplotlib unavailable: no PNG; CSV/JSON still written)'
    report=['# Progressive exclusion of lower loaded surface','',
            f'Case: `{case.name}`. No CUF or FEM solve; no local equilibration claims.','',
            'The integration uses the same stress tensor and physically oriented CSF surface quadrature as the previous script.',
            'Each cutoff excludes the initial length from the **clamp**; both load and stress are integrated over the **same remaining surface**.',
            '', '| Excluded [mm] | Normal load [N] | Normal CUF [N] | Relative difference [%] |',
            '|---:|---:|---:|---:|']
    for r in rows:
        report.append(f"| {r['excluded_mm']:g} | {r['Fnormal_load_N']:.6f} | {r['Fnormal_sigma_N']:.6f} | {r['normal_relative_difference_percent']:.6f} |")
    report.extend(['','The original load is vertical per projected XY area. The normal component is its projection on the inclined surface.',
                   'The plotted percentages use the remaining load resultant in the denominator, not the original full-surface load.','',
                   '![Difference vs excluded length](cutback.png)' if plot_message=='cutback.png' else plot_message])
    (out/'README.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print('\nExcluded [mm] | Fnormal(load) [N] | Fnormal(CUF) [N] | Error normal [%] | Error vertical [%]',flush=True)
    for r in rows:
        print(f"{r['excluded_mm']:12.3f} | {r['Fnormal_load_N']:17.5f} | {r['Fnormal_sigma_N']:17.5f} | "
              f"{r['normal_relative_difference_percent']:16.6f} | {r['vertical_relative_difference_percent']:18.6f}",flush=True)
    print(f'\n[report] {out}',flush=True)
    print(f'[plot] {plot_message}',flush=True)
    return out,rows


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case',required=True,type=Path)
    ap.add_argument('--npz',type=Path,help='Optional checkpoint override')
    ap.add_argument('--exclude-mm',default='0,10,25,50,75,100,150,200,300',
                    help='Comma-separated distances excluded from clamp [mm]. Default: 0,10,25,50,75,100,150,200,300')
    ap.add_argument('--axial-gauss',type=int,default=None,help='Default: load adapter')
    ap.add_argument('--edge-gauss',type=int,default=None,help='Default: load adapter')
    ap.add_argument('--output-root',type=Path)
    args=ap.parse_args()
    run(args)

if __name__=='__main__':
    main()
