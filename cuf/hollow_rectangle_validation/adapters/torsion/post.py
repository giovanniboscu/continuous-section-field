# Version: CSF-CUF hollow-rectangle Bredt-Batho torsion post-processing v5 - 2026-08-27
from __future__ import annotations

import math
from pathlib import Path

import numpy as np


_PROBLEM_TYPE = "hollow_rectangle_torsion_side_surface_halfwave"


def _bounds(domain):
    vertices = np.asarray(domain.vertices, dtype=float)
    return {
        "y_min": float(vertices[:, 0].min()),
        "y_max": float(vertices[:, 0].max()),
        "z_min": float(vertices[:, 1].min()),
        "z_max": float(vertices[:, 1].max()),
    }


def _section_reference(model_bridge, x: float, poisson_ratio: float):
    records = []
    for fallback_id, domain in enumerate(model_bridge.section_provider.domains(float(x)), start=1):
        weightabs = getattr(domain, "weightabs", None)
        if weightabs is None:
            raise ValueError("section domains must expose CSF weightabs")
        record = _bounds(domain)
        record["weightabs"] = float(weightabs)
        record["domain_id"] = int(getattr(domain, "domain_id", fallback_id))
        records.append(record)
    active = [r for r in records if r["weightabs"] != 0.0]
    voids = [r for r in records if r["weightabs"] == 0.0]
    if len(active) != 1 or len(voids) != 1:
        raise ValueError("torsion baseline requires one rectangle and one void")
    outer, inner = active[0], voids[0]
    B = outer["y_max"] - outer["y_min"]
    H = outer["z_max"] - outer["z_min"]
    b = inner["y_max"] - inner["y_min"]
    h = inner["z_max"] - inner["z_min"]
    ty = 0.5 * (B - b)
    tz = 0.5 * (H - h)
    if not math.isclose(ty, tz, rel_tol=1.0e-10, abs_tol=1.0e-10):
        raise ValueError("v2 Bredt baseline requires uniform wall thickness")
    t = ty
    Bm, Hm = B - t, H - t
    area_m = Bm * Hm
    perimeter_m = 2.0 * (Bm + Hm)
    J_bredt = 4.0 * area_m ** 2 * t / perimeter_m
    state = model_bridge.domain_state(float(x), int(outer["domain_id"]))
    E = float(state.E)
    nu = float(poisson_ratio)
    if not math.isfinite(nu) or not (-1.0 < nu < 0.5):
        raise ValueError("poisson_ratio must lie in (-1, 0.5)")
    G = E / (2.0 * (1.0 + nu))
    return dict(B=B, H=H, b=b, h=h, t=t, area_m=area_m, J_bredt=J_bredt, E=E, nu=nu, G=G)


def _displacement(u, x, y, z):
    value = np.asarray(u(float(x), float(y), float(z)), dtype=float)
    if value.shape != (3,):
        raise ValueError("u(x,y,z) must return a 3-component vector")
    return value


def _theta_from_pair(u, x: float, radius: float) -> float:
    """Estimate twist from antisymmetric z displacement at y=+/-radius."""
    uz_plus = float(_displacement(u, x, +radius, 0.0)[2])
    uz_minus = float(_displacement(u, x, -radius, 0.0)[2])
    return (uz_plus - uz_minus) / (2.0 * radius)


def write_outputs(u, model_bridge, case, problem_definition):
    if str(problem_definition.problem_type) != _PROBLEM_TYPE:
        raise ValueError(f"unsupported problem.type: {problem_definition.problem_type!r}")
    x0, x1 = float(u.x_start), float(u.x_end)
    length = x1 - x0
    poisson_ratio = float(
        problem_definition.problem_options.get("poisson_ratio", 0.3)
    )
    reference = _section_reference(model_bridge, x0, poisson_ratio)
    end_reference = _section_reference(model_bridge, x1, poisson_ratio)
    for key in ("B", "H", "b", "h", "t", "J_bredt", "G"):
        if not math.isclose(reference[key], end_reference[key], rel_tol=1e-11, abs_tol=1e-11):
            raise ValueError("torsion baseline requires a prismatic beam")

    pressure = float(problem_definition.problem_options.get("amplitude", 1.0))
    torque_amplitude = pressure * reference["B"] * reference["H"]
    theta_max = torque_amplitude * length ** 2 / (
        math.pi ** 2 * reference["G"] * reference["J_bredt"]
    )
    radius = 0.5 * reference["B"]
    x_mid = 0.5 * (x0 + x1)
    theta_mid = _theta_from_pair(u, x_mid, radius)
    error_mid = abs(abs(theta_mid) - abs(theta_max)) / abs(theta_max) * 100.0

    lines = [
        "# Version: CSF-CUF hollow-rectangle torsion analytical report v5 - 2026-08-27",
        "HOLLOW RECTANGLE - SINUSOIDAL TORSION",
        "========================================",
        "",
        "GEOMETRY AND MATERIAL",
        "---------------------",
        f"outer B x H [mm]          = {reference['B']:.12g} x {reference['H']:.12g}",
        f"void  b x h [mm]          = {reference['b']:.12g} x {reference['h']:.12g}",
        f"uniform thickness t [mm]  = {reference['t']:.12g}",
        f"mean-line area A_m [mm^2] = {reference['area_m']:.12g}",
        f"Bredt J_t [mm^4]          = {reference['J_bredt']:.12g}",
        f"Young modulus E [MPa]     = {reference['E']:.12g}",
        f"Poisson ratio nu          = {reference['nu']:.12g}",
        f"shear modulus G [MPa]     = {reference['G']:.12g}",
        f"length L [mm]             = {length:.12g}",
        "",
        "LOAD",
        "----",
        f"side traction p0 [N/mm^2] = {pressure:.12e}",
        f"torque amplitude m0 [N]   = {torque_amplitude:.12e}",
        "m(x) = m0 sin(pi x/L); zero transverse resultant",
        "",
        "MIDSPAN TWIST",
        "-------------",
        f"CSF-CUF theta [rad]        = {theta_mid:.12e}",
        f"Bredt-Batho theta [rad]    = {theta_max:.12e}",
        f"relative magnitude error [%] = {error_mid:.12e}",
        "",
        "NOTE: Bredt-Batho is a thin-wall closed-section approximation.",
        "The CUF sequence must also be checked for internal convergence.",
        "",
        "STATIONS",
        "--------",
        f"{'x/L':>10} {'x [mm]':>16} {'CUF theta [rad]':>20} {'Bredt theta [rad]':>20} {'error [%]':>16}",
    ]
    for fraction in tuple(float(v) for v in case.sampling.stations):
        x = x0 + fraction * length
        numerical = _theta_from_pair(u, x, radius)
        exact = theta_max * math.sin(math.pi * fraction)
        error_text = "-" if abs(exact) < 1e-14 * max(1.0, abs(theta_max)) else f"{abs(abs(numerical)-abs(exact))/abs(exact)*100.0:.8e}"
        lines.append(f"{fraction:10.6f} {x:16.6f} {numerical:20.12e} {exact:20.12e} {error_text:>16}")

    output_dir = Path(case.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "hollow_rectangle_torsion_analytical.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return (path,)
