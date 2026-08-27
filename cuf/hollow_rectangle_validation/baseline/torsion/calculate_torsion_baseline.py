#!/usr/bin/env python3
# Version: hollow-rectangle standalone Bredt-Batho baseline v5 - 2026-08-27
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


STATIONS = (0.0, 0.25, 0.5, 0.75, 1.0)


def calculate(*, B, H, b, h, length, E, poisson_ratio, pressure):
    ty = 0.5 * (B - b)
    tz = 0.5 * (H - h)
    if not math.isclose(ty, tz, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("Bredt v5 baseline requires uniform wall thickness")
    thickness = ty
    Bm, Hm = B - thickness, H - thickness
    area_m = Bm * Hm
    perimeter_m = 2.0 * (Bm + Hm)
    J_bredt = 4.0 * area_m**2 * thickness / perimeter_m
    G = E / (2.0 * (1.0 + poisson_ratio))
    torque_amplitude = pressure * B * H
    theta_max = torque_amplitude * length**2 / (math.pi**2 * G * J_bredt)
    rows = []
    for fraction in STATIONS:
        theta = theta_max * math.sin(math.pi * fraction)
        rows.append(
            {
                "x_over_L": fraction,
                "x_mm": fraction * length,
                "theta_bredt_rad": theta,
                "uz_at_y_plus_B_over_2_mm": 0.5 * B * theta,
            }
        )
    return {
        "thickness": thickness,
        "area_m": area_m,
        "J_bredt": J_bredt,
        "G": G,
        "torque_amplitude": torque_amplitude,
        "theta_max": theta_max,
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description="Bredt-Batho hollow-rectangle baseline")
    parser.add_argument("--B", type=float, default=100.0)
    parser.add_argument("--H", type=float, default=100.0)
    parser.add_argument("--b", type=float, default=80.0)
    parser.add_argument("--h", type=float, default=80.0)
    parser.add_argument("--length", type=float, default=10000.0)
    parser.add_argument("--E", type=float, default=71700.0)
    parser.add_argument("--poisson-ratio", type=float, default=0.3)
    parser.add_argument("--pressure", type=float, default=1.0e-5)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "output")
    args = parser.parse_args()
    if not (args.B > args.b > 0.0 and args.H > args.h > 0.0):
        parser.error("outer dimensions must be larger than positive void dimensions")
    if args.length <= 0.0 or args.E <= 0.0:
        parser.error("length and E must be positive")
    if not (-1.0 < args.poisson_ratio < 0.5):
        parser.error("poisson ratio must lie in (-1, 0.5)")

    try:
        result = calculate(
            B=args.B, H=args.H, b=args.b, h=args.h, length=args.length,
            E=args.E, poisson_ratio=args.poisson_ratio, pressure=args.pressure,
        )
    except ValueError as error:
        parser.error(str(error))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    txt = args.output_dir / "torsion_baseline.txt"
    csv_path = args.output_dir / "torsion_baseline.csv"
    lines = [
        "# Version: hollow-rectangle Bredt-Batho baseline report v5 - 2026-08-27",
        "HOLLOW RECTANGLE - TORSION BASELINE",
        "===================================",
        f"outer B x H [mm]          = {args.B:.12g} x {args.H:.12g}",
        f"void  b x h [mm]          = {args.b:.12g} x {args.h:.12g}",
        f"uniform thickness t [mm]  = {result['thickness']:.12g}",
        f"mean-line area A_m [mm^2] = {result['area_m']:.12g}",
        f"Bredt J_t [mm^4]          = {result['J_bredt']:.12g}",
        f"Young modulus E [MPa]     = {args.E:.12g}",
        f"Poisson ratio nu          = {args.poisson_ratio:.12g}",
        f"shear modulus G [MPa]     = {result['G']:.12g}",
        f"torque amplitude m0 [N]   = {result['torque_amplitude']:.12e}",
        f"midspan theta [rad]       = {result['theta_max']:.12e}",
        "NOTE: Bredt-Batho is a thin-wall closed-section approximation.",
        "",
        f"{'x/L':>10} {'x [mm]':>16} {'theta [rad]':>20} {'u_z(y=B/2) [mm]':>22}",
    ]
    lines.extend(
        f"{r['x_over_L']:10.6f} {r['x_mm']:16.6f} {r['theta_bredt_rad']:20.12e} {r['uz_at_y_plus_B_over_2_mm']:22.12e}"
        for r in result["rows"]
    )
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    fields = ("x_over_L", "x_mm", "theta_bredt_rad", "uz_at_y_plus_B_over_2_mm")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["rows"])
    print(txt)
    print(csv_path)


if __name__ == "__main__":
    main()
