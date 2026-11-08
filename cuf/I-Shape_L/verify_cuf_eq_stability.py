"""Verify CSF-CUF eq1..eq5 checkpoint stability for cuf/I-Shape_L.

The test compares both (a) the complete saved displacement coefficients in
*.cuf.npz and (b) the displacement samples in response_eqN.txt. It does NOT
solve the structural problem, test mesh convergence, or verify stress equilibrium.

Run from cuf/I-Shape_L:
    python3 verify_cuf_eq_stability.py

Default output:
    diagnostics/cuf_eq_stability/summary.md
    diagnostics/cuf_eq_stability/summary.csv

Requirement: numpy. No other project-specific modules are required.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from pathlib import Path

import numpy as np

DEFAULT_RESULTS = Path(
    'output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3'
)
DEFAULT_REPORT = Path('diagnostics/cuf_eq_stability')
FIELD_KEYS = (
    'element_coefficients',
    'solved_nodal_domain_natural_coefficients',
    'solved_nodal_domain_power_coefficients',
)
COMPONENTS = ('ux', 'uy', 'uz')


class VerificationError(Exception):
    pass


def parse_response(path: Path) -> tuple[str, dict]:
    """Read station rows identified by (x/L, point), retaining coordinates."""
    problem = None
    stations = {}
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        s = line.strip()
        if s.startswith('problem.type') and '=' in s:
            problem = s.split('=', 1)[1].strip()
            continue
        fields = s.split()
        if len(fields) != 8:
            continue
        try:
            xi, x, y, z = map(float, fields[:4])
            ux, uy, uz = map(float, fields[5:8])
        except ValueError:
            continue
        if not all(math.isfinite(v) for v in (xi, x, y, z, ux, uy, uz)):
            raise VerificationError(f'Non-finite response value: {path}:{number}')
        point = fields[4]
        key = (xi, point)
        if key in stations:
            raise VerificationError(f'Duplicate point {key}: {path}:{number}')
        stations[key] = (np.asarray([xi, x, y, z]),
                         np.asarray([ux, uy, uz]))
    if not stations:
        raise VerificationError(f'No station responses found in {path}')
    if problem is None:
        raise VerificationError(f'No problem.type found in {path}')
    return problem, stations


def read_npz(path: Path) -> dict:
    try:
        with np.load(path, allow_pickle=False) as archive:
            data = {name: archive[name].copy() for name in archive.files}
    except Exception as exc:
        raise VerificationError(f'Cannot read {path}: {exc}') from exc
    if not data:
        raise VerificationError(f'Empty NPZ archive: {path}')
    for name, arr in data.items():
        # A checkpoint can legitimately store an empty optional coefficient array.
        # Other arrays (e.g. strings containing configuration data) are metadata.
        if arr.dtype.hasobject:
            raise VerificationError(f'Object array not supported for {name!r}: {path}')
        if np.issubdtype(arr.dtype, np.number) and not np.all(np.isfinite(arr)):
            raise VerificationError(f'Non-finite array {name!r}: {path}')
    return data


def response_vectors(reference: tuple, candidate: tuple) -> tuple:
    problem0, data0 = reference
    problem1, data1 = candidate
    if problem0 != problem1:
        raise VerificationError(f'Problem type differs: {problem0!r} vs {problem1!r}')
    if data0.keys() != data1.keys():
        missing = set(data0) - set(data1)
        extra = set(data1) - set(data0)
        raise VerificationError(f'Sampling points differ; missing={missing}, added={extra}')
    keys = sorted(data0)
    for key in keys:
        coords0, _ = data0[key]
        coords1, _ = data1[key]
        if not np.allclose(coords0, coords1, atol=1e-10, rtol=0):
            raise VerificationError(f'Sampling coordinates differ at {key}')
    a = np.asarray([data0[key][1] for key in keys], dtype=float)
    b = np.asarray([data1[key][1] for key in keys], dtype=float)
    return a, b, len(keys)


def fields_for_comparison(ref: dict, cur: dict) -> list:
    if ref.keys() != cur.keys():
        missing = set(ref) - set(cur)
        extra = set(cur) - set(ref)
        raise VerificationError(f'Checkpoint keys differ; missing={missing}, added={extra}')
    for key in sorted(ref):
        if ref[key].shape != cur[key].shape:
            raise VerificationError(f'Checkpoint shape differs in {key}: '
                                    f'{ref[key].shape} vs {cur[key].shape}')
        if ref[key].dtype != cur[key].dtype:
            raise VerificationError(f'Checkpoint dtype differs in {key}: '
                                    f'{ref[key].dtype} vs {cur[key].dtype}')
        if key not in FIELD_KEYS and not np.array_equal(ref[key], cur[key]):
            raise VerificationError(f'Checkpoint configuration/geometry differs in {key}')
    # Optional coefficient arrays can be present but empty. Their shapes have
    # already been checked; an empty pair has no values to compare.
    return [name for name in FIELD_KEYS if name in ref and ref[name].size > 0]


def metrics(a: np.ndarray, b: np.ndarray, rtol: float, atol: float) -> dict:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape:
        raise VerificationError(f'Array shape mismatch: {a.shape} vs {b.shape}')
    if a.size == 0:
        raise VerificationError('Empty array cannot be compared')
    delta = b - a
    max_abs = float(np.max(np.abs(delta)))
    rms = float(np.sqrt(np.mean(np.square(delta))))
    # One global scale per field/component; no near-zero pointwise division.
    scale = max(float(np.max(np.abs(a))), float(np.max(np.abs(b))))
    threshold = atol + rtol * scale
    return dict(count=int(a.size), scale=scale, max_abs=max_abs, rms=rms,
                relative_max=(max_abs / scale if scale > 0 else 0.0),
                threshold=threshold, passed=(max_abs <= threshold))


def validate_checkpoint_names(directory: Path, indices: list[int], logs_only: bool):
    responses, checkpoints = {}, {}
    for index in indices:
        path = directory / f'response_eq{index}.txt'
        if not path.is_file():
            raise VerificationError(f'Missing response: {path}')
        responses[index] = path
        if not logs_only:
            matches = list(directory.glob(f'*_eq{index}.cuf.npz'))
            # Restrict to an exact eqN suffix to avoid accidental eq10 matches.
            matches = [p for p in matches if re.search(rf'_eq{index}\.cuf\.npz$', p.name)]
            if len(matches) != 1:
                raise VerificationError(
                    f'Expected one eq{index} .cuf.npz, found {len(matches)} in {directory}; '
                    f'use --logs-only to assess samples without whole-field verification'
                )
            checkpoints[index] = matches[0]
    return responses, checkpoints


def produce_rows(indices: list[int], responses: dict, checkpoints: dict,
                 rtol: float, atol: float, logs_only: bool) -> list:
    log_data = {i: parse_response(responses[i]) for i in indices}
    npz_data = {} if logs_only else {i: read_npz(checkpoints[i]) for i in indices}
    baseline = indices[0]
    # All checkpoints compared to eq1; also compare each neighboring pair.
    pairs = [(baseline, i, 'vs_reference') for i in indices[1:]]
    pairs += [(indices[i-1], indices[i], 'consecutive')
              for i in range(1, len(indices))]
    rows = []
    for left, right, kind in pairs:
        a, b, point_count = response_vectors(log_data[left], log_data[right])
        for j, component in enumerate(COMPONENTS):
            row = dict(pair=f'eq{left} -> eq{right}', kind=kind,
                       source='response', field=component, points=point_count)
            row.update(metrics(a[:, j], b[:, j], rtol, atol))
            rows.append(row)
        # Also compare the full sampled displacement vectors.
        row = dict(pair=f'eq{left} -> eq{right}', kind=kind,
                   source='response', field='u_xyz', points=point_count)
        row.update(metrics(a, b, rtol, atol))
        rows.append(row)
        if not logs_only:
            fields = fields_for_comparison(npz_data[left], npz_data[right])
            for field in fields:
                row = dict(pair=f'eq{left} -> eq{right}', kind=kind,
                           source='checkpoint', field=field, points='all coefficients')
                row.update(metrics(npz_data[left][field], npz_data[right][field],
                                   rtol, atol))
                rows.append(row)
    return rows


def write_reports(output_dir: Path, rows: list, source_dir: Path,
                  indices: list[int], rtol: float, atol: float,
                  logs_only: bool) -> tuple[Path, Path, bool]:
    output_dir.mkdir(parents=True, exist_ok=True)
    success = all(row['passed'] for row in rows)
    csv_path = output_dir / 'summary.csv'
    columns = ['pair', 'kind', 'source', 'field', 'points', 'count',
               'scale', 'max_abs', 'rms', 'relative_max', 'threshold', 'passed']
    with csv_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    def fnum(n):
        return f'{n:.6e}'

    checkpoint_fields = sorted({r['field'] for r in rows if r['source'] == 'checkpoint'})
    if logs_only:
        scope = 'sampled displacements only (--logs-only)'
    elif checkpoint_fields:
        scope = 'sampled displacements and the available saved coefficient arrays'
    else:
        scope = 'sampled displacements only (no nonempty supported coefficient arrays in the NPZ files)'
    text = [
        '# CSF-CUF equilibration-checkpoint stability', '',
        f'**Result:** {"PASS" if success else "FAIL"}', '',
        f'**Scope:** {scope}.', '',
        f'**Compared coefficient fields:** {", ".join(f"`{k}`" for k in checkpoint_fields) if checkpoint_fields else "none"}.', '',
        f'**Input directory:** `{source_dir.as_posix()}`', '',
        f'**Checkpoints:** {", ".join(f"eq{i}" for i in indices)}', '',
        f'**Criterion:** `max|b-a| <= {atol:.3e} + {rtol:.3e} * max(max|a|, max|b|)`.',
        'The scale is calculated per response component or coefficient array, not pointwise.',
        'The absolute tolerance is expressed in the native units of the compared data',
        '(mm for displacements and physical displacement coefficients).', '',
        '## Comparison with eq1', '',
        '| Checkpoint | Report u max diff (mm) | DOF coefficient max diff | '
        'Reconstructed-field coefficient max diff | Result |',
        '|---|---:|---:|---:|---|',
    ]
    for i in indices[1:]:
        part = [r for r in rows if r['pair'] == f'eq{indices[0]} -> eq{i}'
                and r['kind'] == 'vs_reference']
        disp = next(r for r in part if r['source']=='response' and r['field']=='u_xyz')
        dof = next((r for r in part if r['source']=='checkpoint' and
                    r['field']=='element_coefficients'), None)
        reconstructed = [r for r in part if r['source']=='checkpoint' and
                         r['field'].startswith('solved_nodal_domain_')]
        recon = max([r['max_abs'] for r in reconstructed], default=None)
        overall = all(r['passed'] for r in part)
        text.append('| eq{idx} | {report} | {dof} | {recon} | {result} |'.format(
            idx=i,
            report=fnum(disp['max_abs']),
            dof=fnum(dof['max_abs']) if dof else 'not evaluated',
            recon=fnum(recon) if recon is not None else 'not present',
            result='PASS' if overall else 'FAIL'
        ))

    text += ['', '## Detailed checks', '',
             '| Pair | Mode | Data | Max abs diff | RMS diff | Relative max | Allowed | PASS |',
             '|---|---|---|---:|---:|---:|---:|---|']
    for r in rows:
        text.append('| {pair} | {kind} | `{field}` ({source}) | {ma} | {rms} | {rel} | {tol} | {ok} |'.format(
            pair=r['pair'], kind=r['kind'], field=r['field'], source=r['source'],
            ma=fnum(r['max_abs']), rms=fnum(r['rms']),
            rel=fnum(r['relative_max']), tol=fnum(r['threshold']),
            ok='PASS' if r['passed'] else 'FAIL'))
    text += [
        '', '## Interpretation', '',
        'PASS indicates that the compared displacement data meet the selected tolerance',
        'over eq1..eq5. The compared coefficient fields, when present, are listed above.', '',
    ]
    md_path = output_dir / 'summary.md'
    md_path.write_text('\n'.join(text), encoding='utf-8')
    return md_path, csv_path, success


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dir', type=Path, default=DEFAULT_RESULTS,
                        help='Folder containing response_eq*.txt and *_eq*.cuf.npz')
    parser.add_argument('--out', type=Path, default=DEFAULT_REPORT,
                        help='Output directory for summary.md and summary.csv')
    parser.add_argument('--iterations', type=int, nargs='+', default=[1,2,3,4,5],
                        help='Checkpoint numbers (default 1 2 3 4 5)')
    parser.add_argument('--rtol', type=float, default=1e-8,
                        help='Relative max-difference tolerance (default 1e-8)')
    parser.add_argument('--atol', type=float, default=1e-9,
                        help='Absolute max-difference tolerance (default 1e-9)')
    parser.add_argument('--logs-only', action='store_true',
                        help='Compare only response_eq*.txt; do NOT claim whole-field stability')
    args = parser.parse_args(argv)
    try:
        indices = args.iterations
        if len(indices) < 2 or len(set(indices)) != len(indices) or any(i < 1 for i in indices):
            raise VerificationError('--iterations needs at least two unique positive indices')
        if indices != sorted(indices):
            raise VerificationError('--iterations must be increasing')
        if not all(math.isfinite(t) and t >= 0 for t in (args.rtol, args.atol)):
            raise VerificationError('Tolerances must be finite and nonnegative')
        if not args.dir.is_dir():
            raise VerificationError(f'Directory not found: {args.dir}')
        responses, checkpoints = validate_checkpoint_names(args.dir, indices, args.logs_only)
        rows = produce_rows(indices, responses, checkpoints, args.rtol, args.atol, args.logs_only)
        md_path, csv_path, success = write_reports(args.out, rows, args.dir, indices,
                                                    args.rtol, args.atol, args.logs_only)
    except (VerificationError, OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print(f'Verification: {"PASS" if success else "FAIL"}')
    checkpoint_fields = sorted({r['field'] for r in rows if r['source'] == 'checkpoint'})
    print(f'Compared saved coefficient fields: {", ".join(checkpoint_fields) if checkpoint_fields else "none"}')
    print('Scope: response samples' + (' + available checkpoint coefficients' if checkpoint_fields else ' only'))
    for i in indices[1:]:
        part = [r for r in rows if r['pair'] == f'eq{indices[0]} -> eq{i}'
                and r['kind'] == 'vs_reference']
        sample = next(r for r in part if r['source']=='response' and r['field']=='u_xyz')
        coeff = next((r for r in part if r['source']=='checkpoint' and
                      r['field']=='element_coefficients'), None)
        print(f'eq{indices[0]} -> eq{i}: max(sample u)={sample["max_abs"]:.6e} mm; '
              + (f'max(DOF coeff)={coeff["max_abs"]:.6e}; ' if coeff else '')
              + ('PASS' if all(r['passed'] for r in part) else 'FAIL'))
    print(f'Markdown: {md_path}')
    print(f'CSV:      {csv_path}')
    return 0 if success else 2


if __name__ == '__main__':
    sys.exit(main())
