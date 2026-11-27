#!/usr/bin/env python3
"""Diagnostic only: isolate axial/transverse Poisson constitutive couplings.

Run from any directory in a Python environment with csf-cuf installed.
No installed sources or original YAMLs are modified. Runs serially.

Variant A: intact physical CSF constitutive law.
Variant B: same local 6x6 matrix except C[xx,yy], C[yy,xx],
           C[xx,zz], C[zz,xx] are set to zero.
Voigt order: (xx,yy,zz,yz,xz,xy).
Variant B is a diagnostic artificial material, NOT isotropic elasticity.
"""
from __future__ import annotations
import argparse
import csv
import json
import tempfile
from pathlib import Path

import numpy as np
import yaml


def read_tip(path: Path) -> float:
    for line in path.read_text(encoding='utf-8').splitlines():
        a = line.split()
        if len(a) >= 8 and a[4] == 'center':
            try:
                if abs(float(a[0]) - 1) < 1e-9 and abs(float(a[2])) < 1e-8 and abs(float(a[3])) < 1e-8:
                    return float(a[7])
            except ValueError:
                pass
    raise RuntimeError(f'Tip center displacement missing: {path}')


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path.cwd(), help='b2_shear_locking directory')
    p.add_argument('--meshes', nargs='+', type=int, default=[8, 16], help='B2 longitudinal element counts')
    p.add_argument('--mode', choices=['both', 'baseline', 'decoupled'], default='both')
    args = p.parse_args()
    root = args.root.resolve()
    cases_dir = root / 'cases'
    outdir = root / 'poisson_coupling_probe'
    outdir.mkdir(exist_ok=True)
    from csf.cuf.core.material import MaterialConstitutive
    from csf.cuf.__main__ import run
    unmodified_matrix = MaterialConstitutive.matrix
    stats = {'samples': 0, 'max_removed': 0.0, 'min_eigenvalue': float('inf'), 'max_unchanged_error': 0.0}

    def decoupled_matrix(self, x, domain_id, y, z):
        C0 = np.asarray(unmodified_matrix(self, x, domain_id, y, z), dtype=float)
        C = C0.copy()
        for a, b in ((0, 1), (0, 2), (1, 0), (2, 0)):
            stats['max_removed'] = max(stats['max_removed'], abs(float(C[a, b])))
            C[a, b] = 0.0
        if not np.allclose(C, C.T, atol=1e-9, rtol=1e-12):
            raise RuntimeError('Diagnostic matrix lost symmetry')
        eig = float(np.linalg.eigvalsh(C).min())
        stats['min_eigenvalue'] = min(stats['min_eigenvalue'], eig)
        stats['samples'] += 1
        if eig <= 0:
            raise RuntimeError(f'Diagnostic matrix is not positive definite: lambda_min={eig}')
        keep = np.ones((6, 6), dtype=bool)
        for a, b in ((0,1),(0,2),(1,0),(2,0)):
            keep[a,b] = False
        stats['max_unchanged_error'] = max(stats['max_unchanged_error'], float(np.max(abs(C[keep] - C0[keep]))))
        return C

    rows=[]
    for n in args.meshes:
        source = cases_dir / f'mitc_locking_rect_B2_N{n:02d}_on.yaml'
        if not source.exists():
            raise FileNotFoundError(source)
        base = yaml.safe_load(source.read_text(encoding='utf-8'))
        for variant in (['baseline', 'decoupled'] if args.mode == 'both' else [args.mode]):
            case = dict(base)
            case['case'] = dict(base['case'])
            case['output'] = dict(base['output'])
            name = f'poisson_probe_B2_N{n:02d}_{variant}'
            case['case']['name'] = name
            # Relative paths refer to a temporary YAML stored in the original cases directory.
            case['output']['directory'] = f'../poisson_coupling_probe/{name}'
            tmp = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', prefix='.probe_', dir=cases_dir, encoding='utf-8', delete=False) as f:
                    tmp = Path(f.name)
                    yaml.safe_dump(case, f, sort_keys=False)
                MaterialConstitutive.matrix = decoupled_matrix if variant == 'decoupled' else unmodified_matrix
                print(f'\n=== {name} ===', flush=True)
                run(str(tmp))
                u = read_tip(outdir / name / 'response.txt')
                L = 5000.0; E = 75000.0; b = h = 100.0; Fz = -100.0
                eb = Fz * L**3 / (3*E*(b*h**3/12))
                row = {'N': n, 'variant': variant, 'uz_mm': u, 'eb_mm': eb, 'deficit_pct': 100 * (1 - abs(u/eb))}
                rows.append(row)
                print('RESULT:', row, flush=True)
            finally:
                MaterialConstitutive.matrix = unmodified_matrix
                if tmp is not None:
                    tmp.unlink(missing_ok=True)
    with (outdir / 'comparison.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['N', 'variant', 'uz_mm', 'eb_mm', 'deficit_pct'])
        w.writeheader(); w.writerows(rows)
    (outdir / 'matrix_diagnostic.json').write_text(json.dumps(stats, indent=2) + '\n', encoding='utf-8')
    print('\nWrote:', outdir / 'comparison.csv')
    print('Constitutive diagnostics:', stats)
    if args.mode == 'both':
        byn = {n: {r['variant']:r for r in rows if r['N']==n} for n in args.meshes}
        for n, d in byn.items():
            print(f"N={n}: additional effect of axial-transverse coupling = {d['baseline']['deficit_pct'] - d['decoupled']['deficit_pct']:.8f} percentage points")


if __name__ == '__main__':
    main()
