"""
Analytical reference from CSF YAML without using CSF section APIs.

The script:
  - reads geometry directly from YAML;
  - reads weight_laws directly from YAML;
  - reconstructs:
        E(z)
        G(z)
        EI(z)
        GJ(z)
  - computes:
        Uy tip displacement
        Rz tip torsional rotation

No CSF section sampling APIs are used.
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import numpy as np
import yaml


DEFAULT_YAML = "NREL-5-MW.yaml"
N_REF = 2001
NU = 0.3


# Load case used for the structural response comparison.
# FY_TIP, MX_TIP, and WY_DIST contribute to the transverse tip displacement Uy.
# MZ_TIP contributes to the torsional tip rotation Rz.
# FZ_TIP is applied in the OpenSees model as axial load, but it is not used
# in the independent analytical reference because that check does not evaluate
# axial shortening or second-order geometric effects.

FY_TIP = 1.2e6   # Transverse concentrated tip force in global Y.
FZ_TIP = -5.0e6  # Axial tip force; excluded from Uy/Rz analytical checks.
MX_TIP = 8.0e6   # Concentrated bending moment about global X.
MZ_TIP = 3.0e6   # Concentrated torsional moment about global Z.
WY_DIST = 8.0e3  # Uniform transverse distributed load in global/local Y.


def simpson(y, x):
    if len(x) < 3:
        raise ValueError("Need at least 3 points.")

    if len(x) % 2 == 0:
        raise ValueError("Need odd number of points.")

    h = (x[-1] - x[0]) / (len(x) - 1)

    return h / 3.0 * (
        y[0]
        + y[-1]
        + 4.0 * np.sum(y[1:-1:2])
        + 2.0 * np.sum(y[2:-2:2])
    )


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def polygon_radii(vertices):
    radii = []

    for v in vertices:
        x = float(v[0])
        y = float(v[1])

        radii.append(math.sqrt(x * x + y * y))

    return min(radii), max(radii)


def compile_weight_expression(expr: str):
    expr = expr.strip()

    if ":" in expr:
        expr = expr.split(":", 1)[1].strip()

    expr = expr.replace("^", "**")

    allowed = {
        "np": np,
        "exp": np.exp,
        "sqrt": np.sqrt,
        "sin": np.sin,
        "cos": np.cos,
        "pi": np.pi,
    }

    def evaluator(z, L):
        return eval(
            expr,
            {"__builtins__": {}},
            {
                **allowed,
                "z": z,
                "L": L,
            },
        )

    return evaluator


def main():
    yaml_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_YAML

    yaml_stem = Path(yaml_file).stem
    output_dir = Path(f"openseeslab_output_{yaml_stem}")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "analytical_reference.txt"

    data = load_yaml(yaml_file)

    csf = data["CSF"]

    s0 = csf["sections"]["S0"]
    s1 = csf["sections"]["S1"]

    z0 = float(s0["z"])
    z1 = float(s1["z"])

    L = z1 - z0

    poly0 = next(iter(s0["polygons"].values()))
    poly1 = next(iter(s1["polygons"].values()))

    ri0, ro0 = polygon_radii(poly0["vertices"])
    ri1, ro1 = polygon_radii(poly1["vertices"])

    weight_expr = csf["weight_laws"][0]

    weight_fn = compile_weight_expression(weight_expr)

    z = np.linspace(0.0, L, N_REF)

    eta = z / L

    r_outer = ro0 + (ro1 - ro0) * eta
    r_inner = ri0 + (ri1 - ri0) * eta


    E = np.array(
        [float(weight_fn(zi, L)) for zi in z],
        dtype=float,
    )

    G = E / (2.0 * (1.0 + NU))

    I = math.pi / 4.0 * (r_outer**4 - r_inner**4)

    EI = E * I

    J = 0.5 * math.pi * (r_outer**4 - r_inner**4)

    GJ = G * J

    m_unit = L - z

    M_fy = FY_TIP * (L - z)
    M_wy = 0.5 * WY_DIST * (L - z) ** 2
    M_mx = MX_TIP * np.ones_like(z)

    uy_fy_component = simpson(M_fy * m_unit / EI, z)
    uy_wy_component = -simpson(M_wy * m_unit / EI, z)
    uy_mx_component = -simpson(M_mx * m_unit / EI, z)

    uy_reference = (
        uy_fy_component +
        uy_wy_component +
        uy_mx_component
    )

    rz_reference = MZ_TIP * simpson(1.0 / GJ, z)

    lines = []

    lines.append("")
    lines.append("AUTONOMOUS YAML ANALYTICAL REFERENCE")
    lines.append("=" * 78)

    lines.append(f"YAML file                  : {yaml_file}")
    lines.append(f"L                          : {L:.12e}")
    lines.append(f"N_REF                      : {N_REF}")

    lines.append("")
    lines.append("Geometry")
    lines.append("-" * 78)
    lines.append(f"R_OUTER_BASE               : {ro0:.12e}")
    lines.append(f"R_OUTER_TOP                : {ro1:.12e}")
    lines.append(f"R_INNER_BASE               : {ri0:.12e}")
    lines.append(f"R_INNER_TOP                : {ri1:.12e}")

    lines.append("")
    lines.append("Weight law")
    lines.append("-" * 78)
    lines.append(str(weight_expr))

    lines.append("")
    lines.append("REFERENCE RESULTS")
    lines.append("=" * 78)

    lines.append("")
    lines.append("CHECK 1 - TIP DISPLACEMENT Uy")
    lines.append("-" * 78)
    lines.append(f"Uy_force_component         : {uy_fy_component:.12e}")
    lines.append(f"Uy_uniform_component       : {uy_wy_component:.12e}")
    lines.append(f"Uy_tip_moment_component    : {uy_mx_component:.12e}")
    lines.append(f"Uy_reference               : {uy_reference:.12e}")

    lines.append("")
    lines.append("CHECK 2 - TIP TORSIONAL ROTATION Rz")
    lines.append("-" * 78)
    lines.append(f"Rz_reference               : {rz_reference:.12e} rad")

    output_text = "\n".join(lines)

    print(output_text)

    report_file.write_text(output_text + "\n", encoding="utf-8")

    print()
    print(f"Analytical reference report: {report_file}")


if __name__ == "__main__":
    main()
