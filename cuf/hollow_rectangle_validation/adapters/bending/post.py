# Version: CSF-CUF hollow-rectangle Euler-Bernoulli post-processing v5 - 2026-08-27
from __future__ import annotations

import math
from pathlib import Path

import numpy as np


_PROBLEM_TYPE = "hollow_rectangle_bending_bottom_surface_halfwave"


def _domain_bounds(domain):
    vertices = np.asarray(domain.vertices, dtype=float)
    if vertices.ndim != 2 or vertices.shape[1] != 2:
        raise ValueError("section domain vertices must have shape (n,2)")

    y_min = float(np.min(vertices[:, 0]))
    y_max = float(np.max(vertices[:, 0]))
    z_min = float(np.min(vertices[:, 1]))
    z_max = float(np.max(vertices[:, 1]))
    tol = 1.0e-10 * max(
        1.0,
        abs(y_min),
        abs(y_max),
        abs(z_min),
        abs(z_max),
    )

    corners = (
        (y_min, z_min),
        (y_max, z_min),
        (y_max, z_max),
        (y_min, z_max),
    )
    for corner_y, corner_z in corners:
        if not any(
            abs(float(y) - corner_y) <= tol
            and abs(float(z) - corner_z) <= tol
            for y, z in vertices
        ):
            raise ValueError("analytical validation requires rectangular domains")

    return {
        "y_min": y_min,
        "y_max": y_max,
        "z_min": z_min,
        "z_max": z_max,
        "width": y_max - y_min,
        "height": z_max - z_min,
        "y_center": 0.5 * (y_min + y_max),
        "z_center": 0.5 * (z_min + z_max),
    }


def _section_reference(model_bridge, x: float):
    domains = tuple(model_bridge.section_provider.domains(float(x)))
    if len(domains) != 2:
        raise ValueError(
            "hollow-rectangle validation expects exactly two CSF domains"
        )

    records = []
    for fallback_id, domain in enumerate(domains, start=1):
        weightabs = getattr(domain, "weightabs", None)
        if weightabs is None:
            raise ValueError("section domains must expose CSF weightabs")

        domain_id = getattr(domain, "domain_id", None)
        if domain_id is None:
            domain_id = fallback_id

        record = _domain_bounds(domain)
        record.update(
            {
                "domain_id": int(domain_id),
                "weightabs": float(weightabs),
            }
        )
        records.append(record)

    active = [record for record in records if record["weightabs"] != 0.0]
    voids = [record for record in records if record["weightabs"] == 0.0]
    if len(active) != 1 or len(voids) != 1:
        raise ValueError(
            "hollow-rectangle validation requires one material domain and one void"
        )

    outer = active[0]
    inner = voids[0]
    scale = max(
        1.0,
        outer["width"],
        outer["height"],
    )
    tol = 1.0e-10 * scale

    if not (
        inner["y_min"] > outer["y_min"] + tol
        and inner["y_max"] < outer["y_max"] - tol
        and inner["z_min"] > outer["z_min"] + tol
        and inner["z_max"] < outer["z_max"] - tol
    ):
        raise ValueError("the void must lie strictly inside the outer rectangle")

    if not (
        math.isclose(
            inner["y_center"],
            outer["y_center"],
            rel_tol=0.0,
            abs_tol=tol,
        )
        and math.isclose(
            inner["z_center"],
            outer["z_center"],
            rel_tol=0.0,
            abs_tol=tol,
        )
    ):
        raise ValueError("the analytical validation requires a concentric void")

    material_state = model_bridge.domain_state(
        float(x),
        int(outer["domain_id"]),
    )
    E = float(material_state.E)
    if not math.isfinite(E) or E <= 0.0:
        raise ValueError("the material Young modulus must be positive")

    B = outer["width"]
    H = outer["height"]
    b = inner["width"]
    h = inner["height"]
    area = B * H - b * h
    inertia_y = (B * H ** 3 - b * h ** 3) / 12.0

    return {
        "outer": outer,
        "inner": inner,
        "B": B,
        "H": H,
        "b": b,
        "h": h,
        "area": area,
        "inertia_y": inertia_y,
        "E": E,
    }


def _require_prismatic(reference_start, reference_end):
    for key in ("B", "H", "b", "h", "area", "inertia_y", "E"):
        left = float(reference_start[key])
        right = float(reference_end[key])
        if not math.isclose(left, right, rel_tol=1.0e-11, abs_tol=1.0e-11):
            raise ValueError("Euler-Bernoulli comparison requires a prismatic beam")


def _solver_uz(u, x: float, y: float, z: float) -> float:
    value = np.asarray(u(float(x), float(y), float(z)), dtype=float)
    if value.shape != (3,):
        raise ValueError("u(x,y,z) must return a 3-component vector")
    return float(value[2])


def _exact_uz(*, fraction: float, maximum: float) -> float:
    return float(maximum * math.sin(math.pi * float(fraction)))


def write_outputs(u, model_bridge, case, problem_definition):
    """Compare the solved bottom-wall displacement with Euler-Bernoulli."""
    if not callable(u):
        raise TypeError("u must be the callable solved displacement field")
    if not hasattr(u, "x_start") or not hasattr(u, "x_end"):
        raise TypeError("u must expose x_start and x_end")
    if str(problem_definition.problem_type) != _PROBLEM_TYPE:
        raise ValueError(
            f"unsupported problem.type: {problem_definition.problem_type!r}"
        )

    x0 = float(u.x_start)
    x1 = float(u.x_end)
    length = x1 - x0
    if length <= 0.0:
        raise ValueError("solution longitudinal domain must have positive length")

    reference = _section_reference(model_bridge, x0)
    reference_end = _section_reference(model_bridge, x1)
    _require_prismatic(reference, reference_end)

    pressure = float(
        problem_definition.problem_options.get("amplitude", 1.0)
    )
    if not math.isfinite(pressure) or pressure == 0.0:
        raise ValueError("surface-pressure amplitude must be finite and non-zero")

    line_load = pressure * reference["B"]
    maximum_exact = -(
        line_load
        * length ** 4
        / (math.pi ** 4 * reference["E"] * reference["inertia_y"])
    )

    y_sample = float(reference["outer"]["y_center"])
    z_sample = float(reference["outer"]["z_min"])
    x_mid = 0.5 * (x0 + x1)
    numerical_mid = _solver_uz(u, x_mid, y_sample, z_sample)
    relative_mid = (
        abs(abs(numerical_mid) - abs(maximum_exact))
        / abs(maximum_exact)
        * 100.0
    )

    lines = [
        "# Version: CSF-CUF hollow-rectangle analytical report v1 - 2026-08-27",
        "HOLLOW RECTANGLE - SINUSOIDAL BENDING",
        "=======================================",
        "",
        "GEOMETRY AND MATERIAL",
        "---------------------",
        f"outer B x H [mm]          = {reference['B']:.12g} x {reference['H']:.12g}",
        f"void  b x h [mm]          = {reference['b']:.12g} x {reference['h']:.12g}",
        f"net area [mm^2]           = {reference['area']:.12g}",
        f"I_y [mm^4]                = {reference['inertia_y']:.12g}",
        f"length L [mm]             = {length:.12g}",
        f"Young modulus E [MPa]     = {reference['E']:.12g}",
        "",
        "LOAD",
        "----",
        f"surface pressure p0 [N/mm^2] = {pressure:.12e}",
        f"line-load amplitude q0 [N/mm] = {line_load:.12e}",
        "q(x) = q0 sin(pi x/L), acting in solver -z",
        "",
        "MIDSPAN BOTTOM-WALL DISPLACEMENT",
        "--------------------------------",
        f"sample point (x,y,z) [mm] = ({x_mid:.12g}, {y_sample:.12g}, {z_sample:.12g})",
        f"CSF-CUF u_z [mm]           = {numerical_mid:.12e}",
        f"Euler-Bernoulli u_z [mm]   = {maximum_exact:.12e}",
        f"relative magnitude error [%] = {relative_mid:.12e}",
        "",
        "STATIONS",
        "--------",
        f"{'x/L':>10} {'x [mm]':>16} {'CUF u_z [mm]':>20} {'EB u_z [mm]':>20} {'error [%]':>16}",
    ]

    for fraction in tuple(float(v) for v in case.sampling.stations):
        if fraction < 0.0 or fraction > 1.0:
            raise ValueError("sampling.stations values must lie in [0,1]")

        x = x0 + fraction * length
        numerical = _solver_uz(u, x, y_sample, z_sample)
        exact = _exact_uz(fraction=fraction, maximum=maximum_exact)

        if abs(exact) <= 1.0e-14 * max(1.0, abs(maximum_exact)):
            error_text = "-"
        else:
            error = abs(abs(numerical) - abs(exact)) / abs(exact) * 100.0
            error_text = f"{error:.8e}"

        lines.append(
            f"{fraction:10.6f} {x:16.6f} {numerical:20.12e} "
            f"{exact:20.12e} {error_text:>16}"
        )

    output_dir = Path(case.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "hollow_rectangle_analytical.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return (path,)
