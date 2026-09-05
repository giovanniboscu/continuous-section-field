# Version: CUF post matched torsion sampling
# Scope:
# This post-processor is independent of the CUF transverse expansion and evaluates
# the public displacement field u(x,y,z) directly at physical points obtained from
# the current CSF section.
#
# The sampling convention (center, plus, minus, bottom_mid) is intended for centered
# sections for which the origin and the minimum-z boundary have the expected geometric
# meaning. It is suitable, for example, for rectangular, T and I/double-T sections,
# including sections whose geometry varies along x. It is not intended as a universal
# sampling rule for arbitrary translated, disconnected or highly irregular sections.
from __future__ import annotations
from pathlib import Path
import math
import numpy as np


def _bounds(section_provider, x: float):
    vertices = []
    for domain in section_provider.domains(float(x)):
        for y, z in domain.vertices:
            vertices.append((float(y), float(z)))
    if not vertices:
        raise ValueError(f"empty section at x={x}")

    ys = [y for y, _ in vertices]
    zs = [z for _, z in vertices]
    ymin, ymax = min(ys), max(ys)
    zmin, zmax = min(zs), max(zs)

    scale = max(1.0, abs(zmin), abs(zmax))
    tol = 1.0e-10 * scale
    bottom_vertices = [
        (y, z) for y, z in vertices
        if math.isclose(z, zmin, rel_tol=0.0, abs_tol=tol)
    ]
    if not bottom_vertices:
        raise ValueError(f"no section vertex found on minimum-z boundary at x={x}")

    bottom_right_y = max(bottom_vertices, key=lambda point: point[0])[0]
    return ymin, ymax, zmin, zmax, bottom_right_y


def write_outputs(u, model_bridge, case, problem_definition):
    x0, x1 = float(u.x_start), float(u.x_end)
    L = x1 - x0
    out = Path(case.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "response.txt"

    lines = [
        "CSF-CUF RESPONSE",
        "======================",
        f"problem.type = {problem_definition.problem_type}",
        "",
        "STATION RESPONSES",
        "-----------------",
        "x/L       x [mm]             y [mm]               z [mm]               point         ux [mm]             uy [mm]             uz [mm]",
    ]
    for ratio in tuple(float(v) for v in case.sampling.stations):
        x = x0 + ratio * L
        ymin, ymax, zmin, zmax, bottom_right_y = _bounds(model_bridge.section_provider, x)
        points = (
            ("center", 0.0, 0.0),
            ("plus", ymin, zmax),
            ("minus", bottom_right_y, zmin),
            ("bottom_mid", 0.0, zmin),
        )
        for name, y, z in points:
            vec = np.asarray(u(x, y, z), dtype=float)
            lines.append(
                f"{ratio:5.2f}     {x:18.12e}  {y:18.12e}  {z:18.12e}  {name:12s}  {vec[0]:18.12e}  {vec[1]:18.12e}  {vec[2]:18.12e}"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written: {path}")
    return (path,)
