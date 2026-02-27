#!/usr/bin/env python3
"""
make_csf_blade_yaml.py

Generate a CSF-compatible geometry.yaml:

CSF:
  sections:
    S0:
      z: ...
      polygons:
        - name: ...
          weight: ...
          vertices:
            - [x, y]
    S1:
      ...

Twist is provided via CLI flags:
  --s0-twist <deg>  --s1-twist <deg>

and applied inside transform_airfoil() as a 2D CCW rotation.
"""

from __future__ import annotations

import argparse
import math
import os
from typing import List, Tuple

import numpy as np

Pt = Tuple[float, float]


def read_xy_file(path: str) -> List[Pt]:
    pts: List[Pt] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            s = s.replace(",", " ")
            parts = [p for p in s.split() if p]
            if len(parts) < 2:
                continue
            try:
                x = float(parts[0])
                y = float(parts[1])
            except ValueError:
                # Skip non-numeric header lines (e.g., "Cylinder1 ...")
                continue
            pts.append((x, y))
    if len(pts) < 3:
        raise ValueError(f"Too few numeric points read from {path}: {len(pts)}")
    return pts


def polygon_signed_area(pts: List[Pt]) -> float:
    a = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return 0.5 * a


def ensure_ccw(pts: List[Pt]) -> List[Pt]:
    return pts if polygon_signed_area(pts) > 0 else list(reversed(pts))


def transform_airfoil(
    pts_norm: List[Pt],
    chord: float,
    twist_deg: float,
    pitch_axis_xc: float,
) -> List[Pt]:
    """
    pts_norm: (x/c, y/c)
    chord: meters
    pitch_axis_xc: rotation axis location as x/c (e.g. 0.25)
    twist_deg: degrees, CCW positive in (x,y)
    """
    # 1) Scale to chord
    pts = [(x * chord, y * chord) for (x, y) in pts_norm]

    # 2) Shift so rotation happens about pitch axis x = pitch_axis_xc * chord
    x0 = pitch_axis_xc * chord
    pts = [(x - x0, y) for (x, y) in pts]

    # 3) Apply twist rotation (THIS IS WHERE TWIST IS USED)
    th = math.radians(twist_deg)
    c = math.cos(th)
    s = math.sin(th)
    pts = [(c * x - s * y, s * x + c * y) for (x, y) in pts]

    return pts


def best_cyclic_shift(P0: np.ndarray, P1: np.ndarray) -> int:
    """
    Returns k that minimizes sum_i ||P0[i] - P1[(i+k) mod N]||^2.
    Use np.roll(P1, -k) to align P1 to P0.
    """
    if P0.shape != P1.shape or P0.ndim != 2 or P0.shape[1] != 2:
        raise ValueError("P0 and P1 must be (N,2) arrays with the same shape.")
    N = P0.shape[0]
    best_k = 0
    best_val = float("inf")
    for k in range(N):
        P1k = np.roll(P1, -k, axis=0)
        val = float(np.sum((P0 - P1k) ** 2))
        if val < best_val:
            best_val = val
            best_k = k
    return best_k


def fmt_vertices_yaml(pts: List[Pt], indent: int = 12, ndigits: int = 10) -> str:
    sp = " " * indent
    return "\n".join(f"{sp}- [{x:.{ndigits}g}, {y:.{ndigits}g}]" for x, y in pts)


def write_csf_yaml(
    out_path: str,
    s0_z: float,
    s1_z: float,
    s0_pts: List[Pt],
    s1_pts: List[Pt],
    polygon_base: str,
    weight: float,
) -> None:
    lines: List[str] = []
    lines.append("CSF:")
    lines.append("  sections:")
    lines.append("    S0:")
    lines.append(f"      z: {s0_z}")
    lines.append("      polygons:")
    lines.append(f"        - name: \"{polygon_base}_S0\"")
    lines.append(f"          weight: {weight}")
    lines.append("          vertices:")
    lines.append(fmt_vertices_yaml(s0_pts, indent=12))
    lines.append("    S1:")
    lines.append(f"      z: {s1_z}")
    lines.append("      polygons:")
    lines.append(f"        - name: \"{polygon_base}_S1\"")
    lines.append(f"          weight: {weight}")
    lines.append("          vertices:")
    lines.append(fmt_vertices_yaml(s1_pts, indent=12))
    lines.append("")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate CSF geometry.yaml (CSF/sections/S0,S1) from two airfoil coord files."
    )
    ap.add_argument("--airfoil-s0", required=True, help="S0 airfoil coords file (x/c y/c).")
    ap.add_argument("--airfoil-s1", required=True, help="S1 airfoil coords file (x/c y/c).")
    ap.add_argument("--out", default="geometry.yaml", help="Output YAML path.")

    ap.add_argument("--s0-z", type=float, default=0.0)
    ap.add_argument("--s1-z", type=float, default=61.5)

    ap.add_argument("--s0-chord", type=float, required=True)
    ap.add_argument("--s1-chord", type=float, required=True)

    # ---- TWIST INPUTS (degrees) ----
    ap.add_argument("--s0-twist", type=float, required=True, help="S0 twist [deg] (applied to vertices).")
    ap.add_argument("--s1-twist", type=float, required=True, help="S1 twist [deg] (applied to vertices).")

    ap.add_argument("--pitch-axis-xc", type=float, default=0.25)

    ap.add_argument("--polygon-base", default="blade_shell")
    ap.add_argument("--weight", type=float, default=1.0)

    ap.add_argument("--force-ccw", action="store_true")
    ap.add_argument("--align-cyclic", action="store_true",
                    help="Re-index S1 by best cyclic shift to match S0.")

    args = ap.parse_args()

    pts0_norm = read_xy_file(args.airfoil_s0)
    pts1_norm = read_xy_file(args.airfoil_s1)

    # ---- APPLY TWIST HERE (transform_airfoil uses args.s0_twist / args.s1_twist) ----
    pts0 = transform_airfoil(pts0_norm, args.s0_chord, args.s0_twist, args.pitch_axis_xc)
    pts1 = transform_airfoil(pts1_norm, args.s1_chord, args.s1_twist, args.pitch_axis_xc)

    if args.force_ccw:
        pts0 = ensure_ccw(pts0)
        pts1 = ensure_ccw(pts1)

    if len(pts0) != len(pts1):
        raise ValueError(
            f"Point count mismatch: S0 has {len(pts0)} points, S1 has {len(pts1)} points."
        )

    if args.align_cyclic:
        P0 = np.asarray(pts0, dtype=float)
        P1 = np.asarray(pts1, dtype=float)
        k = best_cyclic_shift(P0, P1)
        pts1 = [tuple(p) for p in np.roll(P1, -k, axis=0)]

    write_csf_yaml(
        out_path=args.out,
        s0_z=args.s0_z,
        s1_z=args.s1_z,
        s0_pts=pts0,
        s1_pts=pts1,
        polygon_base=args.polygon_base,
        weight=args.weight,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

