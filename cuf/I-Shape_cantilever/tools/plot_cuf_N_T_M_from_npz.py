#!/usr/bin/env python3
"""Plot CUF vs prescribed N, Tz and My by EVALUATING THE CUF NPZ.

Stress is reconstructed through
csf.cuf.tools.plot_strain_stress_boundary_v10._evaluate_cuf_state(),
called by check_cuf_single_tensor_surface.integrate_stress().

The existing CSF section quadrature and VerticalFaceTractions adapter are used.
No solver, no CSV input, no reconstruction of CSF geometry/material YAML.

Run from cuf/I-Shape_cantilever:
  python tools/plot_cuf_N_T_M_from_npz.py --case cases/convergence_h_v02/step_008.yaml
  python tools/plot_cuf_N_T_M_from_npz.py --case cases/convergence_h_v02/step_008.yaml --cuts 0,0.125,0.375,0.625,0.875
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

try:
    from check_cuf_single_tensor_surface import (
        _load_resources, _edges_affine_csf, _sha256,
        transverse_section_samples, loaded_surface_samples,
        integrate_stress, integrate_prescribed_load,
    )
except ImportError as exc:
    raise SystemExit(
        "Missing tools/check_cuf_single_tensor_surface.py. "
        "Install the existing single-tensor CUF audit first."
    ) from exc


def _positions(raw: str | None, count: int) -> np.ndarray:
    if raw is None:
        if not 2 <= count <= 201:
            raise ValueError("--points must be between 2 and 201")
        # Do not evaluate exactly at the free end; keep strictly x/L < 1.
        fractions = np.linspace(0.0, 1.0, count + 1)[:-1]
    else:
        fractions = np.array([float(value) for value in raw.split(",")], dtype=float)
    if (len(fractions) < 2 or not np.isfinite(fractions).all()
            or np.any(fractions < 0) or np.any(fractions >= 1)
            or np.any(np.diff(fractions) <= 0)):
        raise ValueError("Cuts must be ordered, distinct, finite x/L values within [0,1)")
    return fractions


def _one_plot(rows: list[dict], value: str, reference: str,
              title: str, unit: str, path: Path) -> None:
    x = np.array([row['x_L'] for row in rows])
    numerical = np.array([row[value] for row in rows])
    expected = np.array([row[reference] for row in rows])
    fig, (ax, ad) = plt.subplots(2, 1, figsize=(9.2, 6.3), sharex=True,
                                  gridspec_kw={'height_ratios': [3, 1.3]},
                                  constrained_layout=True)
    ax.plot(x, expected, '-', lw=1.8, label='Theoretical load resultant')
    ax.plot(x, numerical, 'o', ms=3.7, markerfacecolor='none',
            label='CUF stress-integrated resultant')
    ax.set_title(title)
    ax.set_ylabel(unit)
    ax.grid(True, alpha=0.27)
    ax.legend()
    ad.plot(x, numerical - expected, 'o-', lw=1.2, ms=3)
    ad.axhline(0, color='0.5', lw=1, ls='--')
    ad.set_xlabel('Longitudinal position x/L')
    ad.set_ylabel('CUF - theoretical\n' + unit)
    ad.grid(True, alpha=0.27)
    fig.savefig(path, dpi=175)
    plt.close(fig)


def _summary(rows: list[dict], path: Path) -> None:
    x = np.array([row['x_L'] for row in rows])
    layout = [('N_N', 'N_load_N', 'N [N]'),
              ('Tz_N', 'Tz_load_N', 'Tz [N]'),
              ('My_Nmm', 'My_load_Nmm', 'My [N mm]')]
    fig, axes = plt.subplots(3, 2, figsize=(12.6, 10.1), sharex='col',
                             gridspec_kw={'width_ratios': [2, 1]},
                             constrained_layout=True)
    fig.suptitle('CUF vs theoretical loads | Stress resultants from NPZ')
    for j, (value, reference, unit) in enumerate(layout):
        actual = np.array([row[value] for row in rows])
        expected = np.array([row[reference] for row in rows])
        a, b = axes[j]
        a.plot(x, expected, '-', lw=1.8, label='Theoretical (applied loads)')
        a.plot(x, actual, 'o', markersize=3.5, markerfacecolor='none', label='CUF')
        a.set_ylabel(unit)
        a.grid(True, alpha=0.27)
        if j == 0:
            a.legend()
        b.plot(x, actual-expected, 'o-', markersize=3, lw=1.1)
        b.axhline(0, ls='--', lw=1, color='0.5')
        b.set_ylabel('CUF - theoretical')
        b.grid(True, alpha=0.27)
    axes[-1, 0].set_xlabel('x/L')
    axes[-1, 1].set_xlabel('x/L')
    fig.savefig(path, dpi=175)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case', type=Path, required=True, help='Existing CUF case YAML')
    ap.add_argument('--points', type=int, default=20,
                    help='Number of longitudinal cuts, default 20 in [0,0.95]')
    ap.add_argument('--cuts', help='Optional comma-separated explicit positions x/L')
    args = ap.parse_args()

    fractions = _positions(args.cuts, args.points)
    ctx = _load_resources(args.case.resolve(), None)
    case, field, bridge = ctx['case'], ctx['field'], ctx['bridge']
    stress_v10 = ctx['stress_v10']
    load = ctx['load']
    provider = bridge.section_provider
    x0, x1 = ctx['x0'], ctx['x1']
    xs = [float(x0 + (x1-x0) * fraction) for fraction in fractions]
    section_order = int(case.section_integration.gauss_order)
    nx, ne = int(load.axial_gauss), int(load.edge_gauss)

    # v10 resolves the correct CSF polygon identity for each CUF domain at each x.
    lookup_by_x = stress_v10.validate_checkpoint_domain_lookups(field, bridge.field, xs)
    if any(lookup_by_x[float(x)] is None for x in xs):
        raise ValueError('CSF domains do not match the CUF checkpoint')

    # Expected external force and moment are calculated via the EXISTING
    # adapter and CSF section provider, not from the CUF stress solution.
    speeds = _edges_affine_csf(provider, ctx['faces'], x0, x1,
                              xs + [x0 + 0.25*(x1-x0), x0+0.5*(x1-x0), x0+0.75*(x1-x0)])
    rows = []
    print(f'[CUF stress API] {case.name}; cuts={len(xs)}; Gauss={section_order}', flush=True)
    print(f'[CUF stress API] {Path(stress_v10.__file__).resolve()}', flush=True)
    for idx, (fraction, x) in enumerate(zip(fractions, xs), 1):
        origin = np.array([x, 0., 0.], dtype=float)
        stress = integrate_stress(
            transverse_section_samples(provider, x, section_order),
            field, bridge, stress_v10, lookup_by_x, origin)
        prescribed = integrate_prescribed_load(
            loaded_surface_samples(provider, ctx['faces'], [(x, x1)], speeds, nx, ne),
            origin)
        row = {
            'x_L': float(fraction), 'x_mm': x,
            'N_N': float(stress['F'][0]),
            'N_load_N': float(prescribed['F'][0]),
            'Tz_N': float(stress['F'][2]),
            'Tz_load_N': float(prescribed['F'][2]),
            'My_Nmm': float(stress['M'][1]),
            'My_load_Nmm': float(prescribed['M'][1]),
            'dN_N': float(stress['F'][0]-prescribed['F'][0]),
            'dTz_N': float(stress['F'][2]-prescribed['F'][2]),
            'dMy_Nmm': float(stress['M'][1]-prescribed['M'][1]),
        }
        rows.append(row)
        print(f'[{idx:02d}/{len(xs):02d}] x/L={fraction:.4f} ' 
              f'N={row["N_N"]:.6g} ' 
              f'Tz={row["Tz_N"]:.6f} (theory {row["Tz_load_N"]:.6f}) ' 
              f'My={row["My_Nmm"]:.4f} (theory {row["My_load_Nmm"]:.4f})',
              flush=True)

    # Directory identifies the case AND checkpoint hash: regenerated graphs do
    # not create pointless numbered runs, different solutions cannot overwrite.
    checkpoint = Path(ctx['checkpoint']).resolve()
    hash_value = _sha256(checkpoint)
    project = args.case.resolve().parent.parent.parent
    out = project / 'diagnostics' / 'cuf_N_T_M_from_npz' / case.name / hash_value[:12]
    out.mkdir(parents=True, exist_ok=True)

    with (out/'section_resultants.csv').open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out/'provenance.json').write_text(json.dumps({
        'case': case.name,
        'checkpoint': str(checkpoint),
        'checkpoint_sha256': hash_value,
        'stress_module': str(Path(stress_v10.__file__).resolve()),
        'method': 'v10._evaluate_cuf_state -> sigma @ (CSF quadrature weight * +e_x)',
        'section_gauss_order': section_order,
        'number_of_cuts': len(xs),
        'load_adapter': str(ctx['load_adapter']),
        'reference': 'physical loads integrated over x_cut..x1 with the same CSF provider',
    }, indent=2)+'\n', encoding='utf-8')

    _one_plot(rows, 'N_N', 'N_load_N', 'Axial force N: CUF vs theoretical',
              'N [N]', out/'comparison_axial_force_N.png')
    _one_plot(rows, 'Tz_N', 'Tz_load_N', 'Shear force Tz: CUF vs theoretical',
              'Tz [N]', out/'comparison_shear_force_Tz.png')
    _one_plot(rows, 'My_Nmm', 'My_load_Nmm', 'Bending moment My: CUF vs theoretical',
              'My [N mm]', out/'comparison_bending_moment_My.png')
    _summary(rows, out/'comparison_N_Tz_My_overview.png')
    print(f'[DONE] 4 PNG, CSV and provenance: {out}', flush=True)


if __name__ == '__main__':
    main()
