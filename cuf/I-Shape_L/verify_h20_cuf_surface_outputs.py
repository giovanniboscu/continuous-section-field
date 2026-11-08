#!/usr/bin/env python3
"""Independent CSV/JSON consistency verifier for the H20-CUF surface audit.

Run: python3 verify_h20_cuf_surface_outputs.py diagnostics/h20_cuf_surfaces
Requires only Python standard library and numpy. Does not import the primary
surface comparison and never changes or repairs files.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import numpy as np


def load_csv(path):
    with path.open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))


def check_group(label, rows, columns, group):
    assert len(rows)==group['points'], (label,len(rows),group['points'])
    weights=np.array([float(r['area_mm2']) for r in rows])
    assert len(weights)>0 and (weights>0).all() and np.isfinite(weights).all(),label
    area=weights.sum()
    assert math.isclose(area,group['area_mm2'],rel_tol=1e-12,abs_tol=1e-7),label
    for name in columns:
        for comp in ('x','y','z','norm'):
            vals=np.array([float(r[name+'_'+comp]) for r in rows])
            v=float(np.sqrt(np.average(vals**2,weights=weights)))
            expected=group['values'][name][comp]['rms']
            assert math.isclose(v,expected,rel_tol=1e-11,abs_tol=1e-9), (label,name,comp,v,expected)
        components=np.array([[float(r[name+'_'+c]) for c in 'xyz'] for r in rows])
        mag=np.array([float(r[name+'_norm']) for r in rows])
        assert np.max(np.abs(np.linalg.norm(components,axis=1)-mag))<2e-8,(label,name)
    print(f'PASS {label}: {len(rows)} points, {area:.9g} mm2, RMS confirmed')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output_dir',type=Path)
    a=ap.parse_args()
    out=a.output_dir
    summary=json.loads((out/'summary.json').read_text(encoding='utf-8'))
    all_ext=load_csv(out/'external_surface_points.csv')
    inter=load_csv(out/'material_interface_points.csv')
    seam=load_csv(out/'cuf_domain_interface_points.csv')
    groups=summary['groups']
    for typ,cols in [('loaded_bottom',('fem_error','cuf_error')),
                     ('free_external',('fem_error','cuf_error')),
                     ('supported_end',('fem_traction','cuf_traction'))]:
        rr=[r for r in all_ext if r['kind']==typ]
        if rr:check_group(typ,rr,cols,groups[typ])
    check_group('material_interface',inter,('fem_jump','cuf_jump'),groups['material_interface'])
    check_group('cuf_domain_interfaces',seam,('cuf',),groups['cuf_domain_interfaces'])
    mesh_path=out/'h20_mesh_interface_points.csv'
    if mesh_path.exists() and mesh_path.stat().st_size:
        check_group('h20_mesh_interfaces',load_csv(mesh_path),('fem_jump',),groups['h20_mesh_interfaces'])
    sr=load_csv(out/'surface_sections.csv')
    category={'loaded_bottom':[r for r in all_ext if r['kind']=='loaded_bottom'],
              'free_external':[r for r in all_ext if r['kind']=='free_external'],
              'material_interface':inter,'cuf_domain_interfaces':seam}
    for name,rows in category.items():
        ss=[r for r in sr if r['group']==name]
        assert sum(int(r['points']) for r in ss)==len(rows),(name,'axial bins sum')
        assert len({int(r['section']) for r in ss})==len(ss),(name,'duplicated bins')
        assert math.isclose(sum(float(r['area_mm2']) for r in ss),sum(float(r['area_mm2']) for r in rows),rel_tol=1e-11),(name,'axial area')
    print('PASS: every point assigned exactly once to axial-bin summaries')
    # On this benchmark the loaded bottom surface is 66 mm wide and
    # its z-coordinate varies from -75 to -35 mm across 1000 mm.
    if summary['configuration']['max_faces']==0:
        L=1000.;width=66.;slope=40./1000.
        analytic_area=width*L*math.sqrt(1+slope*slope)
        actual=groups['loaded_bottom']['area_mm2']
        assert math.isclose(actual,analytic_area,rel_tol=1e-10,abs_tol=1e-6),(actual,analytic_area)
        amp=summary['configuration']['load_amplitude_mpa']
        exact_Fz=amp*analytic_area*(2/math.pi)
        quadrature_Fz=groups['loaded_bottom']['resultant_target_N'][2]
        assert math.isclose(quadrature_Fz,exact_Fz,rel_tol=1e-4),(quadrature_Fz,exact_Fz)
        print('PASS: loaded physical surface area and sinusoidal resultant independently verified')
    print('ALL TESTS PASS')

if __name__=='__main__':main()
