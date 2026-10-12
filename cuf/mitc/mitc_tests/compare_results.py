#!/usr/bin/env python3
# Version: 2.0 - 2026-10-11
# Read only the tracked x/L=1.0, center, uz value in output/<case>/response.txt.
# Produces comparative TXT and CSV; no solver files are modified.
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

E = 75000.0  # MPa (N/mm^2)
L = 5000.0  # mm
B = 100.0  # mm
H = 100.0  # mm
FZ = -100.0  # N
IY = B * H**3 / 12.0  # mm^4
UZ_EB = FZ * L**3 / (3.0 * E * IY)  # mm: Euler-Bernoulli reference
COUNTS = (1, 2, 4, 8)


def read_tip_uz(response_path: Path) -> float | None:
    if not response_path.is_file():
        return None
    for line in response_path.read_text(encoding='utf-8').splitlines():
        fields = line.split()
        if len(fields) < 8 or fields[4] != 'center':
            continue
        try:
            x_over_L = float(fields[0])
            x_mm = float(fields[1])
            y_mm = float(fields[2])
            z_mm = float(fields[3])
            uz_mm = float(fields[7])
        except (ValueError, IndexError):
            continue
        if (abs(x_over_L - 1.0) < 1e-9
                and abs(x_mm - L) < 1e-6
                and abs(y_mm) < 1e-6
                and abs(z_mm) < 1e-6):
            return uz_mm
    raise ValueError(f'No x/L=1.0 center tip row in {response_path}')


def scalar_fmt(v: float | None, width: int = 13) -> str:
    return f'{v:{width}.8f}' if v is not None else 'MISSING'.rjust(width)


def main() -> int:
    base = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description='MITC B2 paired convergence report')
    parser.add_argument('--output-root', type=Path, default=base/'output')
    parser.add_argument('--report-dir', type=Path, default=base/'mitc_tests/reports')
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    report_dir = args.report_dir.resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    missing = []
    for ne in COUNTS:
        values = {}
        for mode in ('off', 'on'):
            name = f'mitc_locking_rect_B2_N{ne:02d}_{mode}'
            path = output_root/name/'response.txt'
            try:
                values[mode] = read_tip_uz(path)
            except ValueError as exc:
                print(f'ERROR: {exc}', file=sys.stderr)
                return 2
            if values[mode] is None:
                missing.append(str(path))

        off, on = values['off'], values['on']
        rows.append({
            'number_of_B2_elements': ne,
            'longitudinal_order': 1,
            'uz_off_mm': off,
            'uz_on_mm': on,
            'absolute_on_off_ratio': abs(on/off) if off not in (None, 0.0) and on is not None else None,
            'error_off_vs_EB_percent': abs((off-UZ_EB)/UZ_EB)*100.0 if off is not None else None,
            'error_on_vs_EB_percent': abs((on-UZ_EB)/UZ_EB)*100.0 if on is not None else None,
        })

    csv_path = report_dir/'mitc_B2_convergence.csv'
    with csv_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    report = [
        'MITC rectangular cantilever, longitudinal B2 convergence',
        '========================================================',
        f'Euler-Bernoulli reference u_z(L): {UZ_EB:.9f} mm',
        'All runs use E=75000 MPa, nu=0.33, L=5000 mm, 100 x 100 mm, Fz=-100 N.',
        'Displacement measured at x=5000,y=0,z=0 (response.txt: center, x/L=1).',
        '',
        'B2   u_z OFF [mm]  u_z ON [mm]   |ON/OFF|   EB err OFF %   EB err ON %',
    ]
    for row in rows:
        ratio = row['absolute_on_off_ratio']
        eroff = row['error_off_vs_EB_percent']
        eron = row['error_on_vs_EB_percent']
        report.append(
            f"{row['number_of_B2_elements']:2d} "
            f"{scalar_fmt(row['uz_off_mm'])} "
            f"{scalar_fmt(row['uz_on_mm'])} "
            f"{ratio:10.3f}" if ratio is not None else
            f"{row['number_of_B2_elements']:2d} "
            f"{scalar_fmt(row['uz_off_mm'])} "
            f"{scalar_fmt(row['uz_on_mm'])} "
            f"{'MISSING':>10}"
        )
        report[-1] += f" {eroff:14.4f}" if eroff is not None else f"{'MISSING':>15}"
        report[-1] += f" {eron:13.4f}" if eron is not None else f"{'MISSING':>14}"
    report.extend([
        '',
        'Note: Euler-Bernoulli is a slender-beam reference, not an exact CUF/3D solution.',
        'No numerical PASS criterion is imposed on displacement convergence.',
    ])
    if missing:
        report.append(f'Incomplete runs: {len(missing)} missing response.txt files.')
    report_path = report_dir/'mitc_B2_convergence.txt'
    report_path.write_text('\n'.join(report)+'\n', encoding='utf-8')
    print('\n'.join(report))
    print(f'\nReports: {csv_path}, {report_path}')
    if missing:
        print('Missing results:', file=sys.stderr)
        for name in missing:
            print(f'  {name}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
