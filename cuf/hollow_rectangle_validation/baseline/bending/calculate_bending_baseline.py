#!/usr/bin/env python3
# Version: hollow-rectangle standalone Euler-Bernoulli baseline v5 - 2026-08-27
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


STATIONS = (0.0, 0.25, 0.5, 0.75, 1.0)


def calculate(*, B, H, b, h, length, E, pressure):
    area = B * H - b * h
    inertia_y = (B * H**3 - b * h**3) / 12.0
    line_load = pressure * B
    maximum = -(line_load * length**4) / (math.pi**4 * E * inertia_y)
    rows = []
    for fraction in STATIONS:
        rows.append(
            {
                "x_over_L": fraction,
                "x_mm": fraction * length,
                "uz_eb_mm": maximum * math.sin(math.pi * fraction),
            }
        )
    return {
        "area": area,
        "inertia_y": inertia_y,
        "line_load": line_load,
        "maximum": maximum,
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description="Euler-Bernoulli hollow-rectangle baseline")
    parser.add_argument("--B", type=float, default=100.0)
    parser.add_argument("--H", type=float, default=100.0)
    parser.add_argument("--b", type=float, default=80.0)
    parser.add_argument("--h", type=float, default=80.0)
    parser.add_argument("--length", type=float, default=10000.0)
    parser.add_argument("--E", type=float, default=71700.0)
    parser.add_argument("--pressure", type=float, default=1.0e-5)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "output")
    args = parser.parse_args()
    if not (args.B > args.b > 0.0 and args.H > args.h > 0.0):
        parser.error("outer dimensions must be larger than positive void dimensions")
    if args.length <= 0.0 or args.E <= 0.0:
        parser.error("length and E must be positive")

    result = calculate(
        B=args.B, H=args.H, b=args.b, h=args.h,
        length=args.length, E=args.E, pressure=args.pressure,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    txt = args.output_dir / "bending_baseline.txt"
    csv_path = args.output_dir / "bending_baseline.csv"
    lines = [
        "# Version: hollow-rectangle Euler-Bernoulli baseline report v5 - 2026-08-27",
        "HOLLOW RECTANGLE - BENDING BASELINE",
        "===================================",
        f"outer B x H [mm]          = {args.B:.12g} x {args.H:.12g}",
        f"void  b x h [mm]          = {args.b:.12g} x {args.h:.12g}",
        f"net area [mm^2]           = {result['area']:.12g}",
        f"I_y [mm^4]                = {result['inertia_y']:.12g}",
        f"length L [mm]             = {args.length:.12g}",
        f"Young modulus E [MPa]     = {args.E:.12g}",
        f"pressure p0 [N/mm^2]      = {args.pressure:.12e}",
        f"line load q0 [N/mm]       = {result['line_load']:.12e}",
        f"midspan u_z [mm]          = {result['maximum']:.12e}",
        "",
        f"{'x/L':>10} {'x [mm]':>16} {'EB u_z [mm]':>20}",
    ]
    lines.extend(
        f"{r['x_over_L']:10.6f} {r['x_mm']:16.6f} {r['uz_eb_mm']:20.12e}"
        for r in result["rows"]
    )
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("x_over_L", "x_mm", "uz_eb_mm"))
        writer.writeheader()
        writer.writerows(result["rows"])
    print(txt)
    print(csv_path)


if __name__ == "__main__":
    main()
