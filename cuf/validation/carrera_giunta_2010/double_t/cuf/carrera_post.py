# OPT-03 FIXED-X POST CACHE
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


# ============================================================================
# Generic use of the solved CUF field
# ============================================================================

_COMPONENT_INDEX = {"x": 0, "y": 1, "z": 2}


def _paper_displacement(u, x: float, y: float, z: float) -> np.ndarray:
    """
    Evaluate the solved CUF field and map solver components to the
    Carrera-Giunta paper components.

    Solver:
        x = member axis
        y,z = transverse coordinates

    Paper:
        u_x = -u_z,solver
        u_y =  u_y,solver
        u_z =  u_x,solver
    """
    solver_u = np.asarray(u(float(x), float(y), float(z)), dtype=float)

    if solver_u.shape != (3,):
        raise ValueError("u(x,y,z) must return a 3-component vector")

    return np.asarray(
        (
            -float(solver_u[2]),
            float(solver_u[1]),
            float(solver_u[0]),
        ),
        dtype=float,
    )


def _paper_displacement_fixed_x(u_at_x, y: float, z: float) -> np.ndarray:
    """
    Evaluate a solved CUF section field at fixed x and map solver components
    to the Carrera-Giunta paper components.
    """
    solver_u = np.asarray(u_at_x(float(y), float(z)), dtype=float)

    if solver_u.shape != (3,):
        raise ValueError("u_at_x(y,z) must return a 3-component vector")

    return np.asarray(
        (
            -float(solver_u[2]),
            float(solver_u[1]),
            float(solver_u[0]),
        ),
        dtype=float,
    )


def _inside_polygon(vertices, y: float, z: float) -> bool:
    pts = [(float(a), float(b)) for a, b in vertices]
    tol = 1.0e-10 * max(
        1.0,
        abs(y),
        abs(z),
        *(abs(value) for point in pts for value in point),
    )

    inside = False
    n = len(pts)

    for i in range(n):
        y0, z0 = pts[i]
        y1, z1 = pts[(i + 1) % n]

        dy = y1 - y0
        dz = z1 - z0
        seg2 = dy * dy + dz * dz

        if seg2 > 0.0:
            t = ((y - y0) * dy + (z - z0) * dz) / seg2
            if -tol <= t <= 1.0 + tol:
                yp = y0 + t * dy
                zp = z0 + t * dz
                if (y - yp) ** 2 + (z - zp) ** 2 <= tol ** 2:
                    return True

        if (z0 > z) != (z1 > z):
            y_cross = y0 + (z - z0) * (y1 - y0) / (z1 - z0)
            if y < y_cross:
                inside = not inside

    return inside


def _domain_bounds(domain):
    vertices = np.asarray(domain.vertices, dtype=float)
    if vertices.ndim != 2 or vertices.shape[1] != 2:
        raise ValueError("section domain vertices must have shape (n,2)")

    return (
        float(np.min(vertices[:, 0])),
        float(np.max(vertices[:, 0])),
        float(np.min(vertices[:, 1])),
        float(np.max(vertices[:, 1])),
    )


def _is_axis_aligned_rectangle(domain) -> bool:
    vertices = np.asarray(domain.vertices, dtype=float)
    y_min, y_max, z_min, z_max = _domain_bounds(domain)

    tol = 1.0e-10 * max(
        1.0,
        abs(y_min),
        abs(y_max),
        abs(z_min),
        abs(z_max),
    )

    for y, z in vertices:
        on_y = abs(float(y) - y_min) <= tol or abs(float(y) - y_max) <= tol
        on_z = abs(float(z) - z_min) <= tol or abs(float(z) - z_max) <= tol
        if not (on_y or on_z):
            return False

    corners = (
        (y_min, z_min),
        (y_min, z_max),
        (y_max, z_min),
        (y_max, z_max),
    )

    for corner_y, corner_z in corners:
        if not any(
            abs(float(y) - corner_y) <= tol and abs(float(z) - corner_z) <= tol
            for y, z in vertices
        ):
            return False

    return True


def _criterion_score(value: float, operation: str) -> float:
    if operation == "max_abs":
        return abs(float(value))
    if operation == "max":
        return float(value)
    if operation == "min":
        return -float(value)
    raise ValueError(f"unsupported extrema operation: {operation}")


def _reported_value(value: float, operation: str) -> float:
    if operation == "max_abs":
        return abs(float(value))
    if operation in ("max", "min"):
        return float(value)
    raise ValueError(f"unsupported extrema operation: {operation}")


def section_displacement_extremum(
    *,
    u,
    section_provider,
    x: float,
    component: str,
    operation: str,
    grid_n: int = 25,
    u_at_x=None,
):
    """
    Search one paper-coordinate displacement component on one CSF section.

    The post-processor knows only:
        - the callable solved field u(x,y,z);
        - the CSF section geometry.

    It does not inspect CUF DOFs, basis coefficients, FE nodes, or solver state.
    """
    if component not in _COMPONENT_INDEX:
        raise ValueError(f"unsupported component: {component}")

    component_index = _COMPONENT_INDEX[component]
    x = float(x)

    best = None

    if u_at_x is None and hasattr(u, "section_evaluator"):
        u_at_x = u.section_evaluator(x)

    if u_at_x is None:
        def signed_value(y, z):
            return float(
                _paper_displacement(
                    u,
                    x,
                    float(y),
                    float(z),
                )[component_index]
            )
    else:
        def signed_value(y, z):
            return float(
                _paper_displacement_fixed_x(
                    u_at_x,
                    float(y),
                    float(z),
                )[component_index]
            )

    for domain in section_provider.domains(x):
        y_min, y_max, z_min, z_max = _domain_bounds(domain)

        local_grid_n = max(9, int(grid_n))
        ys = np.linspace(y_min, y_max, local_grid_n)
        zs = np.linspace(z_min, z_max, local_grid_n)

        samples = []
        for y in ys:
            for z in zs:
                if not _inside_polygon(domain.vertices, float(y), float(z)):
                    continue
                value = signed_value(y, z)
                samples.append((value, float(y), float(z)))

        # Always include the polygon vertices.
        for y, z in np.asarray(domain.vertices, dtype=float):
            value = signed_value(y, z)
            samples.append((value, float(y), float(z)))

        if not samples:
            continue

        for value, y, z in samples:
            score = _criterion_score(value, operation)
            if best is None or score > best[0]:
                best = (score, value, y, z)

        # For the benchmark rectangular CSF domains, refine the continuous
        # solution directly inside the exact rectangle bounds.
        if _is_axis_aligned_rectangle(domain):
            if operation == "max_abs":
                signs = (+1.0, -1.0)
            elif operation == "max":
                signs = (+1.0,)
            elif operation == "min":
                signs = (-1.0,)
            else:
                raise ValueError(f"unsupported extrema operation: {operation}")

            for sign in signs:
                scored = np.asarray(
                    [sign * item[0] for item in samples],
                    dtype=float,
                )
                start_count = min(12, len(samples))
                start_indices = np.argpartition(
                    scored,
                    -start_count,
                )[-start_count:]

                for index in start_indices:
                    _, y0, z0 = samples[int(index)]

                    result = minimize(
                        lambda q: -sign * signed_value(q[0], q[1]),
                        x0=np.asarray((y0, z0), dtype=float),
                        method="L-BFGS-B",
                        bounds=((y_min, y_max), (z_min, z_max)),
                        options={
                            "ftol": 1.0e-14,
                            "gtol": 1.0e-11,
                            "maxiter": 300,
                        },
                    )

                    y_opt = float(result.x[0])
                    z_opt = float(result.x[1])
                    value_opt = signed_value(y_opt, z_opt)
                    score_opt = _criterion_score(value_opt, operation)

                    if best is None or score_opt > best[0]:
                        best = (score_opt, value_opt, y_opt, z_opt)

    if best is None:
        raise RuntimeError(f"no section points found at x={x}")

    _, signed, y, z = best

    return {
        "component": component,
        "operation": operation,
        "value": _reported_value(signed, operation),
        "signed_value": float(signed),
        "x": x,
        "y": float(y),
        "z": float(z),
    }


# ============================================================================
# Carrera-Giunta Table 9 / Table 10 report definitions
# ============================================================================

def _double_t_reference_data(model_bridge, x: float):
    """
    Read the Table-9/Table-10 reference dimensions and E from the CSF section.

    This is benchmark-report logic only. The CUF solver does not use it.
    """
    domains = tuple(model_bridge.section_provider.domains(float(x)))

    if len(domains) != 3:
        raise ValueError(
            "Carrera Table 9/10 reporting expects the benchmark double-T "
            "decomposition into three CSF rectangular domains"
        )

    records = []
    for domain_id, domain in enumerate(domains, start=1):
        if not _is_axis_aligned_rectangle(domain):
            raise ValueError(
                "Carrera Table 9/10 reporting expects rectangular CSF domains"
            )

        y_min, y_max, z_min, z_max = _domain_bounds(domain)
        records.append(
            {
                "domain_id": domain_id,
                "domain": domain,
                "y_min": y_min,
                "y_max": y_max,
                "z_min": z_min,
                "z_max": z_max,
                "width": y_max - y_min,
                "height": z_max - z_min,
                "z_center": 0.5 * (z_min + z_max),
            }
        )

    records.sort(key=lambda item: item["z_center"])
    bottom, web, top = records

    a = float(web["height"])
    b_bottom = float(bottom["width"])
    b_top = float(top["width"])

    tol_b = 1.0e-9 * max(1.0, abs(b_bottom), abs(b_top))
    if abs(b_bottom - b_top) > tol_b:
        raise ValueError(
            "Carrera Table 9/10 normalization requires equal flange widths "
            "at the reference section"
        )
    b = 0.5 * (b_bottom + b_top)

    E_values = [
        float(model_bridge.domain_state(float(x), item["domain_id"]).E)
        for item in records
    ]
    tol_E = 1.0e-9 * max(1.0, *(abs(value) for value in E_values))
    if max(E_values) - min(E_values) > tol_E:
        raise ValueError(
            "Carrera Table 9/10 normalization requires one reference E "
            "at the reference section"
        )
    E_ref = sum(E_values) / len(E_values)

    return {
        "a": a,
        "b": b,
        "E_ref": E_ref,
    }


def _report_spec(case, problem_definition, model_bridge, u):
    x0 = float(u.x_start)
    x1 = float(u.x_end)
    length = x1 - x0

    if length <= 0.0:
        raise ValueError("solution longitudinal domain must have positive length")

    ref = _double_t_reference_data(model_bridge, x0)
    a = ref["a"]
    b = ref["b"]
    E_ref = ref["E_ref"]

    amplitude = float(problem_definition.problem_options.get("amplitude", 1.0))
    if amplitude == 0.0:
        raise ValueError("paper-style normalization requires non-zero amplitude")

    l_over_a = length / a
    problem_type = str(problem_definition.problem_type)

    if problem_type in (
        "carrera_bending_halfwave",
        "carrera_bending_bottom_surface_halfwave",
    ):
        factor = (
            (math.pi ** 4) / 12.0
            * (a ** 3) / (length ** 4)
            * E_ref / amplitude
        )

        if math.isclose(l_over_a, 10.0, rel_tol=1.0e-9, abs_tol=1.0e-9):
            scales = {"ux": 10.0, "uy": 1.0e3, "uz": 1.0e2}
            headers = ("10 |u_x*|", "10^3 |u_y*|", "10^2 u_z*")
        elif math.isclose(l_over_a, 100.0, rel_tol=1.0e-9, abs_tol=1.0e-9):
            scales = {"ux": 10.0, "uy": 1.0e5, "uz": 1.0e3}
            headers = ("10 |u_x*|", "10^5 |u_y*|", "10^3 u_z*")
        else:
            raise ValueError(
                f"Table 9 display supports L/a=10 or 100, got {l_over_a:g}"
            )

        return {
            "table": 9,
            "title": "TABLE 9 — CSF-CUF",
            "factor": factor,
            "scales": scales,
            "headers": headers,
            "operations": {
                "ux": "max",
                "uy": "max_abs",
                "uz": "max",
            },
        }

    if problem_type == "carrera_torsion_halfwave":
        factor = (
            (math.pi ** 4) / 12.0
            * (a ** 3) * b / (length ** 4)
            * E_ref / amplitude
        )

        return {
            "table": 10,
            "title": "TABLE 10 — CSF-CUF",
            "factor": factor,
            "scales": {
                "ux": 10.0,
                "uy": 10.0,
                "uz": 1.0e2,
            },
            "headers": (
                "10 |u_x*|",
                "10 |u_y*|",
                "10^2 u_z*",
            ),
            "operations": {
                "ux": "max_abs",
                "uy": "max_abs",
                "uz": "max",
            },
        }

    raise ValueError(
        "paper-style displacement report is not defined for "
        f"problem.type={problem_type!r}"
    )


def _section_extrema(u, model_bridge, x: float, spec):
    rows = {}
    x = float(x)

    u_at_x = None
    if hasattr(u, "section_evaluator"):
        u_at_x = u.section_evaluator(x)

    for component in ("ux", "uy", "uz"):
        short = component[1:]
        row = section_displacement_extremum(
            u=u,
            section_provider=model_bridge.section_provider,
            x=x,
            component=short,
            operation=spec["operations"][component],
            u_at_x=u_at_x,
        )
        row["scaled_value"] = (
            spec["scales"][component]
            * spec["factor"]
            * float(row["value"])
        )
        rows[component] = row

    return rows


def _global_extrema(u, model_bridge, case, spec):
    sample_count = max(3, int(case.sampling.displacement_samples))
    xs = np.linspace(float(u.x_start), float(u.x_end), sample_count)

    global_rows = {component: None for component in ("ux", "uy", "uz")}

    for x in xs:
        section = _section_extrema(u, model_bridge, float(x), spec)

        for component, row in section.items():
            operation = spec["operations"][component]
            score = _criterion_score(row["signed_value"], operation)

            previous = global_rows[component]
            if previous is None:
                global_rows[component] = row
                continue

            previous_score = _criterion_score(
                previous["signed_value"],
                operation,
            )

            if score > previous_score:
                global_rows[component] = row

    return global_rows


def _format_report_text(*, u, model_bridge, case, spec):
    sections = tuple(float(value) for value in case.sampling.stations)
    if not sections:
        raise ValueError("sampling.stations must not be empty")

    for value in sections:
        if value < 0.0 or value > 1.0:
            raise ValueError("sampling.stations values must lie in [0,1]")

    global_rows = _global_extrema(u, model_bridge, case, spec)

    lines = []
    lines.append(spec["title"])
    lines.append("=" * len(spec["title"]))
    lines.append("")
    lines.append("GLOBAL MAXIMUM DISPLACEMENTS — PAPER FORMAT")
    lines.append("-------------------------------------------")
    lines.append(
        f"{'model':<12}"
        f"{spec['headers'][0]:>18}"
        f"{spec['headers'][1]:>20}"
        f"{spec['headers'][2]:>18}"
    )
    lines.append(
        f"{'CSF-CUF':<12}"
        f"{global_rows['ux']['scaled_value']:>18.6f}"
        f"{global_rows['uy']['scaled_value']:>20.6f}"
        f"{global_rows['uz']['scaled_value']:>18.6f}"
    )

    lines.append("")
    lines.append("LOCATIONS OF GLOBAL MAXIMA")
    lines.append("---------------------------")
    lines.append(
        f"{'component':<12}{'criterion':<14}"
        f"{'x':>12}{'y':>12}{'z':>12}"
    )

    for component in ("ux", "uy", "uz"):
        row = global_rows[component]
        lines.append(
            f"{component:<12}"
            f"{spec['operations'][component]:<14}"
            f"{row['x']:>12.3f}"
            f"{row['y']:>12.3f}"
            f"{row['z']:>12.3f}"
        )

    lines.append("")
    lines.append("COMMANDED SECTIONS")
    lines.append("------------------")
    lines.append(
        "x/L = " + ", ".join(f"{value:.3f}" for value in sections)
    )

    length = float(u.x_end - u.x_start)

    for fraction in sections:
        x = float(u.x_start + fraction * length)
        rows = _section_extrema(u, model_bridge, x, spec)

        lines.append("")
        lines.append(
            f"SECTION x/L = {fraction:.3f}   x = {x:.3f}"
        )
        lines.append("-" * 54)
        lines.append(
            f"{'component':<12}{'criterion':<14}"
            f"{'scaled displacement':>20}"
            f"{'y':>12}{'z':>12}"
        )

        for component in ("ux", "uy", "uz"):
            row = rows[component]
            lines.append(
                f"{component:<12}"
                f"{spec['operations'][component]:<14}"
                f"{row['scaled_value']:>20.6f}"
                f"{row['y']:>12.3f}"
                f"{row['z']:>12.3f}"
            )

    return "\n".join(lines) + "\n"


def write_outputs(u, model_bridge, case, problem_definition):
    """
    Post-process a solved CUF displacement field.

    Public dependency on the solver:
        u(x,y,z)

    No CUF DOFs, basis coefficients, FE mesh, recovery object, or algebraic
    solver state is inspected here.
    """
    if not callable(u):
        raise TypeError("u must be the callable solved displacement field")

    if not hasattr(u, "x_start") or not hasattr(u, "x_end"):
        raise TypeError("u must expose x_start and x_end")

    output_dir = Path(case.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    spec = _report_spec(case, problem_definition, model_bridge, u)
    text = _format_report_text(
        u=u,
        model_bridge=model_bridge,
        case=case,
        spec=spec,
    )

    path = output_dir / f"table{spec['table']}_style.txt"
    path.write_text(text, encoding="utf-8")

    return (path,)
