#!/usr/bin/env python3
"""Compare CSF-CUF and native OpenSees FEM3D sectional N, Tz and My.

This script REUSES the existing CSF API based CUF integration kernel and the
native-stress FEM3D ``plot_fem3d_N_T_M_from_npz.py`` (v03) postprocessor.
Neither a solver nor a new physical geometry/material interpolation is used.

Run from cuf/I-Shape_cantilever:

    python tools/compare_cuf_fem3d_N_T_M.py \
      --cuf-case cases/convergence_h_v02/step_005.yaml \
      --fem-case cases/convergence_h_v02/step_008.yaml \
      --fem-npz fem3d/native_stress_reference/solution.npz \
      --points 20

To reuse an existing FEM3D `center` result and skip native-stress recovery:

    python tools/compare_cuf_fem3d_N_T_M.py \
      --cuf-case cases/convergence_h_v02/step_005.yaml \
      --fem-case cases/convergence_h_v02/step_008.yaml \
      --fem-csv path/to/center/section_resultants.csv

Both methods are evaluated at exactly the same FEM3D center-section x values.
This is a SECTIONAL RESULTANT comparison, not a convergence assessment and not
an evaluation of tractions on external beam surfaces.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


FIELDS = ('N', 'Tz', 'My')
UNITS = {'N': 'N', 'Tz': 'N', 'My': 'N mm'}
REF_FIELDS = {'N': 'N_load_N', 'Tz': 'Tz_load_N', 'My': 'My_load_Nmm'}
VALUE_FIELDS = {'N': 'N_N', 'Tz': 'Tz_N', 'My': 'My_Nmm'}


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    required = {'x_L', 'x_mm', 'gauss_plane', *VALUE_FIELDS.values(), *REF_FIELDS.values()}
    if len(rows) < 2:
        raise ValueError(f'Expected at least two FEM3D center sections: {path}')
    if not required.issubset(rows[0]):
        raise ValueError(f'Invalid FEM3D v03 CSV {path}; missing {sorted(required-set(rows[0]))}')
    last = -math.inf
    for row in rows:
        if row['gauss_plane'] != 'center':
            raise ValueError('Only native FEM3D center recovery is permitted for this comparison')
        for key in ('x_L', 'x_mm', *VALUE_FIELDS.values(), *REF_FIELDS.values()):
            value = float(row[key])
            if not math.isfinite(value):
                raise ValueError(f'Non-finite FEM3D value: {key} at x={row["x_mm"]}')
        x = float(row['x_mm'])
        if x <= last:
            raise ValueError('FEM3D center-section coordinates must be strictly increasing')
        last = x
    return rows


def _read_native_provenance(fem_csv: Path, fem_case_name: str, fem_npz: Path | None) -> dict:
    path = fem_csv.parent / 'provenance.json'
    if not path.is_file():
        raise FileNotFoundError(f'FEM3D native v03 provenance missing beside CSV: {path}')
    p = json.loads(path.read_text(encoding='utf-8'))
    if p.get('sampling') != 'center':
        raise ValueError('FEM3D provenance must explicitly state sampling=center')
    if p.get('case') != fem_case_name:
        raise ValueError(f'FEM3D report was made for {p.get("case")!r}, not {fem_case_name!r}')
    if 'Native OpenSees' not in p.get('method', ''):
        raise ValueError('FEM3D report is not the native OpenSees Gauss-stress recovery')
    if fem_npz is not None and p.get('sha256') != _hash(fem_npz):
        raise ValueError('FEM3D CSV does not correspond to the selected NPZ (SHA-256 mismatch)')
    return p


def _get_case_identity(path: Path):
    # Public APIs: no raw physical model YAML parsing.
    from csf.cuf.case import load_case
    from csf.cuf.problem.problem_api import load_problem
    case = load_case(path)
    definition = load_problem(case.problem_path)
    return case, definition


def _reference_close(value: float, independent: float, label: str, x: float):
    # Independent calculation through the CUF load adapter and FEM3D CSF API.
    tol = max(1e-5, 1e-9 * max(abs(value), abs(independent)))
    if abs(value-independent) > tol:
        raise ValueError(f'FEM and CUF theoretical {label} differ at x={x:.8f} mm: '
                         f'{value:.12g} vs {independent:.12g}. '
                         'Check the load adapter, physical model and coordinates.')


def _plot_one(rows: list[dict], symbol: str, out: Path) -> None:
    x = np.array([r['x_L'] for r in rows])
    theory = np.array([r[f'{symbol}_theoretical'] for r in rows])
    cuf = np.array([r[f'{symbol}_CUF'] for r in rows])
    fem = np.array([r[f'{symbol}_FEM3D'] for r in rows])
    fig, (ax, ae) = plt.subplots(2, 1, figsize=(10, 7), sharex=True,
                                gridspec_kw={'height_ratios': [2.7, 1.3]},
                                constrained_layout=True)
    ax.plot(x, theory, '-', lw=2.0, label='Prescribed-load resultant')
    ax.plot(x, cuf, 'o', ms=4.2, mfc='none', label='CSF-CUF (N=10, p=12)')
    ax.plot(x, fem, 'x', ms=4.2, label='FEM3D (native OpenSees, center P0)')
    ax.set_title(f'{symbol}: CSF-CUF vs FEM3D vs prescribed loads')
    ax.set_ylabel(f'{symbol} [{UNITS[symbol]}]')
    ax.grid(alpha=.27)
    ax.legend()
    ae.plot(x, cuf-theory, 'o-', ms=3.5, label='CSF-CUF - theoretical')
    ae.plot(x, fem-theory, 'x-', ms=3.5, label='FEM3D - theoretical')
    ae.axhline(0, color='0.5', ls='--', lw=.9)
    ae.set_ylabel(f'Residual [{UNITS[symbol]}]')
    ae.set_xlabel('Longitudinal position x/L')
    ae.grid(alpha=.27)
    ae.legend(fontsize=8)
    fig.savefig(out / f'comparison_{symbol}.png', dpi=180)
    plt.close(fig)


def _plot_overview(rows: list[dict], out: Path) -> None:
    x = np.array([r['x_L'] for r in rows])
    fig, axes = plt.subplots(3, 2, figsize=(14, 10.5), sharex='col',
                             gridspec_kw={'width_ratios': [2.1, 1]},
                             constrained_layout=True)
    fig.suptitle('CSF-CUF and FEM3D | Sectional resultants at identical physical cuts')
    for j, symbol in enumerate(FIELDS):
        theory = np.array([r[f'{symbol}_theoretical'] for r in rows])
        cuf = np.array([r[f'{symbol}_CUF'] for r in rows])
        fem = np.array([r[f'{symbol}_FEM3D'] for r in rows])
        ax, ae = axes[j]
        ax.plot(x, theory, '-', lw=1.8, label='Theoretical')
        ax.plot(x, cuf, 'o', ms=3.0, mfc='none', label='CSF-CUF')
        ax.plot(x, fem, 'x', ms=3.5, label='FEM3D center P0')
        ax.set_ylabel(f'{symbol} [{UNITS[symbol]}]')
        ax.grid(alpha=.27)
        if j == 0:
            ax.legend(fontsize=8)
        ae.plot(x, cuf-theory, 'o-', ms=2.8, label='CUF - theory')
        ae.plot(x, fem-theory, 'x-', ms=3.0, label='FEM - theory')
        ae.axhline(0, ls='--', lw=.8, color='0.5')
        ae.set_ylabel(f'Residual [{UNITS[symbol]}]')
        ae.grid(alpha=.27)
    axes[-1, 0].set_xlabel('x/L')
    axes[-1, 1].set_xlabel('x/L')
    fig.savefig(out/'comparison_N_Tz_My_overview.png', dpi=180)
    plt.close(fig)


def _summary(rows: list[dict]) -> dict:
    result = {}
    for symbol in FIELDS:
        t = np.array([r[f'{symbol}_theoretical'] for r in rows])
        c = np.array([r[f'{symbol}_CUF'] for r in rows])
        f = np.array([r[f'{symbol}_FEM3D'] for r in rows])
        # Whole-curve normalization (avoids artificial blow-up near free end).
        scale = float(np.max(np.abs(t)))
        entry = {'reference_max_abs': scale,
                 'max_abs_CUF_minus_theory': float(np.max(np.abs(c-t))),
                 'max_abs_FEM_minus_theory': float(np.max(np.abs(f-t))),
                 'max_abs_CUF_minus_FEM': float(np.max(np.abs(c-f)))}
        if scale > 0:
            entry.update(max_abs_CUF_minus_theory_pct_of_reference=100*entry['max_abs_CUF_minus_theory']/scale,
                         max_abs_FEM_minus_theory_pct_of_reference=100*entry['max_abs_FEM_minus_theory']/scale,
                         max_abs_CUF_minus_FEM_pct_of_reference=100*entry['max_abs_CUF_minus_FEM']/scale)
        # Axial resultant reference N=0: report absolute N, never a relative percentage.
        result[symbol] = entry
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cuf-case', type=Path, default=Path('cases/convergence_h_v02/step_005.yaml'),
                    help='CUF solution selected independently: h-series N=10, p=12')
    ap.add_argument('--fem-case', type=Path, default=Path('cases/convergence_h_v02/step_008.yaml'),
                    help='FEM driver case which generated the native-stress NPZ')
    ap.add_argument('--fem-npz', type=Path, default=None,
                    help='Native OpenSees solution NPZ (default: fem3d/native_stress_reference/solution.npz)')
    ap.add_argument('--fem-csv', type=Path, default=None,
                    help='Reuse an existing v03 native-stress CENTER CSV + adjacent provenance.json')
    ap.add_argument('--fem-script', type=Path, default=Path('tools/plot_fem3d_N_T_M_from_npz.py'),
                    help='Existing native OpenSees FEM3D v03 postprocessor')
    ap.add_argument('--points', type=int, default=20,
                    help='Number of requested FEM3D center cuts (default 20, x/L=0..0.95 snapped to centers)')
    ap.add_argument('--output-dir', type=Path, default=None,
                    help='Output directory; default diagnostics/cuf_fem3d_N_T_M/<checkpoint hashes>')
    args = ap.parse_args()
    if not 2 <= args.points <= 200:
        ap.error('--points must be 2..200')

    cuf_case = args.cuf_case.resolve()
    fem_case = args.fem_case.resolve()
    for p in (cuf_case, fem_case):
        if not p.is_file():
            raise FileNotFoundError(p)
    project = cuf_case.parent.parent.parent
    if fem_case.parent.parent.parent != project:
        raise ValueError('CUF and FEM case files must belong to the same project root')
    for candidate in (project.parent.parent/'src', project/'src'):
        if (candidate/'csf'/'cuf').is_dir():
            sys.path.insert(0, str(candidate))
            break

    # Public case/problem APIs validate physical identity independent of case name.
    c_case, c_def = _get_case_identity(cuf_case)
    f_case, f_def = _get_case_identity(fem_case)
    if (Path(c_case.problem_path).resolve() != Path(f_case.problem_path).resolve()
            or Path(c_def.model_path).resolve() != Path(f_def.model_path).resolve()):
        raise ValueError('CUF/FEM cases do not reference the same physical problem and CSF model')

    # Read CUF using the previously verified public-API based stress kernel.
    try:
        from check_cuf_single_tensor_surface import (
            _load_resources, transverse_section_samples, integrate_stress,
            loaded_surface_samples, integrate_prescribed_load, _edges_affine_csf,
        )
    except ImportError as exc:
        raise RuntimeError('Missing tools/check_cuf_single_tensor_surface.py; '
                           'install the existing CUF stress audit first') from exc
    ctx = _load_resources(cuf_case, None)
    checkpoint = Path(ctx['checkpoint']).resolve()
    cuf_sha = _hash(checkpoint)

    default_npz = Path('fem3d/native_stress_reference/solution.npz')
    fem_npz = (args.fem_npz if args.fem_npz is not None else default_npz).resolve()
    if not args.fem_csv and not fem_npz.is_file():
        raise FileNotFoundError(f'Native FEM3D checkpoint not found: {fem_npz}')
    check_npz = fem_npz if fem_npz.is_file() else None
    if args.fem_npz is not None and check_npz is None:
        raise FileNotFoundError(fem_npz)
    fem_sha = _hash(check_npz) if check_npz else None

    # Input identity determines deterministic output: no accidental mixing or overwrites.
    if args.fem_csv:
        fem_csv = args.fem_csv.resolve()
        fem_provenance = _read_native_provenance(fem_csv, f_case.name,
                                                  check_npz if args.fem_npz is not None else None)
        fem_sha = fem_provenance.get('sha256')
        if not isinstance(fem_sha, str) or len(fem_sha) != 64:
            raise ValueError('FEM3D provenance must contain the native checkpoint SHA-256')
    else:
        fem_csv = None
    request_tag = hashlib.sha256(f'{cuf_sha}:{fem_sha}:{args.points}:center'.encode()).hexdigest()[:12]
    output = (args.output_dir.resolve() if args.output_dir else
              project/'diagnostics'/'cuf_fem3d_N_T_M'/request_tag)
    output.mkdir(parents=True, exist_ok=True)

    if fem_csv is None:
        native_script = args.fem_script.resolve()
        if not native_script.is_file():
            raise FileNotFoundError(f'Native FEM3D v03 script is missing: {native_script}')
        fem_out = output/'fem3d_native_center'
        command = [sys.executable, str(native_script), '--case', str(fem_case),
                   '--fem-npz', str(fem_npz), '--sampling', 'center',
                   '--points', str(args.points), '--output-dir', str(fem_out)]
        print('[RUN] Existing FEM3D native-stress center postprocessor:', flush=True)
        print('      '+' '.join(command), flush=True)
        subprocess.run(command, cwd=project, check=True)
        fem_csv = fem_out/'section_resultants.csv'
        fem_provenance = _read_native_provenance(fem_csv, f_case.name, fem_npz)

    fem_rows = _load_csv(fem_csv)
    x0, x1 = float(ctx['x0']), float(ctx['x1'])
    if any(not x0 < float(row['x_mm']) < x1 for row in fem_rows):
        raise ValueError('A FEM3D section is outside the CSF longitudinal interval')
    if any(abs((float(row['x_mm'])-x0)/(x1-x0)-float(row['x_L'])) > 1e-10
           for row in fem_rows):
        raise ValueError('FEM3D normalized x positions differ from the physical CSF interval')
    xs = [float(row['x_mm']) for row in fem_rows]

    bridge = ctx['bridge']
    field = ctx['field']
    stress_v10 = ctx['stress_v10']
    csf = bridge.section_provider
    lookups = stress_v10.validate_checkpoint_domain_lookups(field, bridge.field, xs)
    if any(lookups[float(x)] is None for x in xs):
        raise ValueError('CSF polygon-to-CUF domain lookup does not match the CUF checkpoint')
    section_order = int(c_case.section_integration.gauss_order)
    load = ctx['load']
    # CSF API is queried at every integration coordinate. The affine test does
    # NOT synthesize or interpolate geometry: it validates this adapter's scope.
    speeds = _edges_affine_csf(csf, ctx['faces'], x0, x1,
                              xs + [x0+.25*(x1-x0), x0+.5*(x1-x0), x0+.75*(x1-x0)])

    comparison = []
    for i, (x, fem) in enumerate(zip(xs, fem_rows), 1):
        origin = np.array([x, 0., 0.], dtype=float)
        cuf = integrate_stress(transverse_section_samples(csf, x, section_order),
                               field, bridge, stress_v10, lookups, origin)
        external = integrate_prescribed_load(
            loaded_surface_samples(csf, ctx['faces'], [(x, x1)], speeds,
                                   int(load.axial_gauss), int(load.edge_gauss)), origin)
        cuf_f = {'N': float(cuf['F'][0]), 'Tz': float(cuf['F'][2]),
                 'My': float(cuf['M'][1])}
        ref = {'N': float(external['F'][0]), 'Tz': float(external['F'][2]),
               'My': float(external['M'][1])}
        for sym in FIELDS:
            _reference_close(ref[sym], float(fem[REF_FIELDS[sym]]), sym, x)
        values = {'x_mm': x, 'x_L': (x-x0)/(x1-x0),
                  'FEM3D_layer_0based': fem.get('h8_layer_0based', ''),
                  'FEM3D_recovery': 'center (8-Gauss mean, transverse P0)'}
        for sym in FIELDS:
            values[f'{sym}_theoretical'] = ref[sym]
            values[f'{sym}_CUF'] = cuf_f[sym]
            values[f'{sym}_FEM3D'] = float(fem[VALUE_FIELDS[sym]])
            values[f'{sym}_CUF_minus_theory'] = cuf_f[sym]-ref[sym]
            values[f'{sym}_FEM_minus_theory'] = float(fem[VALUE_FIELDS[sym]])-ref[sym]
            values[f'{sym}_CUF_minus_FEM'] = cuf_f[sym]-float(fem[VALUE_FIELDS[sym]])
        comparison.append(values)
        print(f'[{i:02d}/{len(xs):02d}] x={x:9.3f} mm | '
              f'Tz: theory={ref["Tz"]: .5f}, CUF={cuf_f["Tz"]: .5f}, '
              f'FEM={values["Tz_FEM3D"]: .5f} N | '
              f'My: theory={ref["My"]: .5f}, CUF={cuf_f["My"]: .5f}, '
              f'FEM={values["My_FEM3D"]: .5f} Nmm', flush=True)

    with (output/'section_resultants_comparison.csv').open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(comparison[0]))
        writer.writeheader()
        writer.writerows(comparison)
    for sym in FIELDS:
        _plot_one(comparison, sym, output)
    _plot_overview(comparison, output)

    stats = _summary(comparison)
    provenance = {
        'CUF_case': c_case.name,
        'CUF_case_path': str(cuf_case),
        'CUF_checkpoint': str(checkpoint),
        'CUF_checkpoint_sha256': cuf_sha,
        'FEM3D_case': f_case.name,
        'FEM3D_checkpoint': str(fem_npz) if check_npz else fem_provenance.get('checkpoint'),
        'FEM3D_checkpoint_sha256': fem_sha,
        'FEM3D_report': str(fem_csv),
        'FEM3D_sampling': 'center',
        'FEM3D_method': 'Native OpenSees 8-Gauss arithmetic mean, P0 per H8 cell, CSF section quadrature',
        'CUF_stress_method': 'Existing plot_strain_stress_boundary_v10._evaluate_cuf_state via shared section kernel',
        'physical_model': str(c_def.model_path),
        'physical_problem': str(c_case.problem_path),
        'comparison_stations_x_mm': xs,
        'section_integration_gauss_order': section_order,
        'reference_load': 'CUF existing VerticalFaceTractions adapter (integrated via CSF); independent FEM3D load references checked',
        'purpose': 'comparison only; not used to decide convergence',
        'limitations': [
            'The selected CUF configuration was chosen from an independent CUF convergence study.',
            'The selected FEM3D mesh was chosen from an independent FEM3D GCI study.',
            'FEM3D center recovery is a postprocessed average, not a native midpoint stress.',
            'FEM3D transverse P0 stress recovery does not preserve all within-cell variation.',
            'No exterior-surface traction verification is performed.',
            'N_theoretical=0; absolute N errors are reported, not relative percentage errors.',
        ],
        'summary': stats,
    }
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n', encoding='utf-8')

    report = [
        '# Sectional resultants: CSF-CUF vs FEM3D', '',
        '## Method', '',
        'CUF: 10 longitudinal elements, polynomial degree p=12, fixed transverse L9; '
        'stress evaluated by the existing `plot_strain_stress_boundary_v10` API and integrated '
        'over CSF physical sections. FEM3D: native OpenSees `stdBrick` Gauss stresses, '
        'eight-point arithmetic mean per element followed by transverse P0 recovery '
        'and CSF sectional quadrature. All results are compared at identical physical x sections.', '',
        '## Input provenance', '',
        f'- CUF case: `{cuf_case}`',
        f'- CUF checkpoint SHA-256: `{cuf_sha}`',
        f'- FEM3D case: `{fem_case}`',
        f'- FEM3D native-stress SHA-256: `{fem_sha}`',
        f'- Number of matched sections: {len(xs)}',
        '', '## Maximum absolute deviations on the sampled sections', '',
        '| Action | CUF − theory | FEM3D − theory | CUF − FEM3D | Unit |',
        '|:---|---:|---:|---:|:---|',
    ]
    for sym in FIELDS:
        s = stats[sym]
        report.append(f'| {sym} | {s["max_abs_CUF_minus_theory"]:.8g} | '
                      f'{s["max_abs_FEM_minus_theory"]:.8g} | '
                      f'{s["max_abs_CUF_minus_FEM"]:.8g} | {UNITS[sym]} |')
    report += ['', 'The values above are maxima over the listed sample positions, '
               '**not** an error estimate or convergence criterion. '
               'For N, the theoretical value is zero; relative N error is undefined.',
               '', '## Figures', '',
               '![N comparison](comparison_N.png)', '',
               '![Tz comparison](comparison_Tz.png)', '',
               '![My comparison](comparison_My.png)', '',
               '![Overview](comparison_N_Tz_My_overview.png)', '',
               '## Interpretation limitation', '',
               'Native FEM3D `center` is an **eight-Gauss-value mean per element**, '
               'not a directly evaluated center-point stress. '
               'The method does not address traction equilibrium on outer surfaces. '
               'Neither the inter-method displacement difference nor the sectional action '
               'comparison is used to establish convergence.', '']
    (output/'comparison_report.md').write_text('\n'.join(report), encoding='utf-8')
    print(f'[DONE] matched sections={len(xs)}; CSV + 4 PNG + Markdown + JSON: {output}', flush=True)


if __name__ == '__main__':
    main()
