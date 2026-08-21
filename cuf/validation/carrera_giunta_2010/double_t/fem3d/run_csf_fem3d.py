from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from csf_fem3d import (
    bending_bottom_surface_nodal_loads,
    build_mesh,
    carrera_table9_style_row,
    carrera_table9_style_rows,
    carrera_table10_style_row,
    carrera_table10_style_rows,
    displacement_maxima,
    equilibrium_diagnostics,
    print_mesh_summary,
    print_table9_style,
    print_result_summary,
    print_table10_style,
    read_csf_field,
    solve_opensees,
    torsion_line_pair_nodal_loads,
    write_diagnostics,
    write_mesh_summary,
    write_summary,
)


def load_case(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("case YAML must contain a mapping")
    return data


def resolve_relative(base_file: Path, value: str) -> Path:
    return (base_file.parent / value).resolve()


def _operations_by_component(case: dict) -> dict:
    """Return the requested extrema operation for ux, uy and uz."""
    return {
        str(item["name"]): str(item["operation"])
        for item in case["outputs"]["maxima"]
    }


def _write_table9_txt(path: Path, rows: list[dict], case: dict) -> None:
    """Write one human-readable Table-9 report."""
    path.parent.mkdir(parents=True, exist_ok=True)

    global_row = rows[0]
    value_fields = global_row["value_fields"]
    operations = _operations_by_component(case)

    lines = []
    lines.append("TABLE 9 - FEM 3D")
    lines.append("================")
    lines.append("")
    lines.append("GLOBAL MAXIMUM DISPLACEMENTS - PAPER FORMAT")
    lines.append("-------------------------------------------")
    lines.append(
        f"{'model':<12}"
        f"{'10 u_x*':>16}"
        f"{'10^3 |u_y*|':>20}"
        f"{'10^2 u_z*':>16}"
    )
    lines.append(
        f"{global_row['model']:<12}"
        f"{global_row[value_fields[0]]:>16.6f}"
        f"{global_row[value_fields[1]]:>20.6f}"
        f"{global_row[value_fields[2]]:>16.6f}"
    )

    lines.append("")
    lines.append("LOCATIONS OF GLOBAL MAXIMA")
    lines.append("---------------------------")
    lines.append(
        f"{'component':<12}{'criterion':<12}{'x':>12}{'y':>12}{'z':>12}"
    )
    for component in ("ux", "uy", "uz"):
        lines.append(
            f"{component:<12}"
            f"{operations[component]:<12}"
            f"{global_row[component + '_x']:>12.3f}"
            f"{global_row[component + '_y']:>12.3f}"
            f"{global_row[component + '_z']:>12.3f}"
        )

    lines.append("")
    lines.append("COMMANDED SECTIONS")
    lines.append("------------------")
    if rows[1:]:
        lines.append(
            "x/L = " + ", ".join(
                f"{row['section_x_over_L']:.3f}" for row in rows[1:]
            )
        )
    else:
        lines.append("none")

    for row in rows[1:]:
        lines.append("")
        lines.append(
            f"SECTION x/L = {row['section_x_over_L']:.3f}   "
            f"x = {row['section_x']:.3f}"
        )
        lines.append("-" * 54)
        lines.append(
            f"{'component':<12}{'criterion':<12}{'scaled displacement':>20}"
            f"{'y':>12}{'z':>12}"
        )

        component_fields = {
            "ux": value_fields[0],
            "uy": value_fields[1],
            "uz": value_fields[2],
        }
        for component in ("ux", "uy", "uz"):
            field = component_fields[component]
            lines.append(
                f"{component:<12}"
                f"{operations[component]:<12}"
                f"{row[field]:>16.6f}"
                f"{row[component + '_y']:>12.3f}"
                f"{row[component + '_z']:>12.3f}"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_table10_txt(path: Path, rows: list[dict], case: dict) -> None:
    """Write one human-readable Table-10 report."""
    path.parent.mkdir(parents=True, exist_ok=True)

    global_row = rows[0]
    operations = _operations_by_component(case)

    value_fields = {
        "ux": "10_abs_ux_star",
        "uy": "10_abs_uy_star",
        "uz": "1e2_uz_star",
    }

    lines = []
    lines.append("TABLE 10 - FEM 3D")
    lines.append("=================")
    lines.append("")
    lines.append("GLOBAL MAXIMUM DISPLACEMENTS - PAPER FORMAT")
    lines.append("-------------------------------------------")
    lines.append(
        f"{'model':<12}"
        f"{'10 |u_x*|':>18}"
        f"{'10 |u_y*|':>18}"
        f"{'10^2 u_z*':>16}"
    )
    lines.append(
        f"{global_row['model']:<12}"
        f"{global_row[value_fields['ux']]:>18.6f}"
        f"{global_row[value_fields['uy']]:>18.6f}"
        f"{global_row[value_fields['uz']]:>16.6f}"
    )

    lines.append("")
    lines.append("LOCATIONS OF GLOBAL MAXIMA")
    lines.append("---------------------------")
    lines.append(
        f"{'component':<12}{'criterion':<12}{'x':>12}{'y':>12}{'z':>12}"
    )
    for component in ("ux", "uy", "uz"):
        lines.append(
            f"{component:<12}"
            f"{operations[component]:<12}"
            f"{global_row[component + '_x']:>12.3f}"
            f"{global_row[component + '_y']:>12.3f}"
            f"{global_row[component + '_z']:>12.3f}"
        )

    lines.append("")
    lines.append("COMMANDED SECTIONS")
    lines.append("------------------")
    if rows[1:]:
        lines.append(
            "x/L = " + ", ".join(
                f"{row['section_x_over_L']:.3f}" for row in rows[1:]
            )
        )
    else:
        lines.append("none")

    for row in rows[1:]:
        lines.append("")
        lines.append(
            f"SECTION x/L = {row['section_x_over_L']:.3f}   "
            f"x = {row['section_x']:.3f}"
        )
        lines.append("-" * 54)
        lines.append(
            f"{'component':<12}{'criterion':<12}{'scaled displacement':>20}"
            f"{'y':>12}{'z':>12}"
        )

        for component in ("ux", "uy", "uz"):
            field = value_fields[component]
            lines.append(
                f"{component:<12}"
                f"{operations[component]:<12}"
                f"{row[field]:>16.6f}"
                f"{row[component + '_y']:>12.3f}"
                f"{row[component + '_z']:>12.3f}"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a 3D OpenSees solid model directly from one CSF YAML model."
    )
    parser.add_argument("case_yaml", type=Path)
    parser.add_argument(
        "--mesh-only",
        action="store_true",
        help="Build and validate the CSF-driven 3D mesh without importing OpenSeesPy.",
    )
    args = parser.parse_args()

    case_path = args.case_yaml.resolve()
    case = load_case(case_path)

    model_path = resolve_relative(case_path, case["model"]["csf_yaml"])
    output_dir = resolve_relative(case_path, case["output"]["directory"])
    output_dir.mkdir(parents=True, exist_ok=True)

    field = read_csf_field(model_path)
    mesh = build_mesh(field, case["mesh"])

    print_mesh_summary(mesh)
    write_mesh_summary(output_dir / "mesh_summary.csv", mesh)

    problem = case["problem"]
    problem_type = str(problem["type"])
    if problem_type == "torsion_line_pair_halfwave":
        loads = torsion_line_pair_nodal_loads(mesh, problem, case["mesh"])
    elif problem_type == "bending_bottom_surface_halfwave":
        loads = bending_bottom_surface_nodal_loads(mesh, problem, case["mesh"])
    else:
        raise ValueError(f"unsupported problem.type={problem_type}")

    if args.mesh_only:
        print()
        print("MESH-ONLY CHECK: PASS")
        print(f"output: {output_dir / 'mesh_summary.csv'}")
        return

    result = solve_opensees(
        mesh,
        loads,
        case.get("analysis", {}),
    )

    rows = displacement_maxima(
        mesh,
        result["displacements"],
        case["outputs"]["maxima"],
    )
    diagnostics = equilibrium_diagnostics(
        mesh,
        loads,
        result["reactions"],
    )

    write_summary(output_dir / "summary.csv", rows)
    write_diagnostics(output_dir / "diagnostics.csv", diagnostics)

    report_cfg = case.get("report", {})
    report_type = report_cfg.get("type")
    report_row = None
    report_path = None

    if report_type == "carrera_table9_style":
        report_row = carrera_table9_style_rows(
            field,
            mesh,
            problem,
            rows,
            result["displacements"],
            case["outputs"]["maxima"],
            report_cfg.get("sections_x_over_L", []),
        )
        report_path = output_dir / "table9_style.txt"
        _write_table9_txt(report_path, report_row, case)
    elif report_type == "carrera_table10_style":
        report_row = carrera_table10_style_rows(
            field,
            mesh,
            problem,
            rows,
            result["displacements"],
            case["outputs"]["maxima"],
            report_cfg.get("sections_x_over_L", []),
        )
        report_path = output_dir / "table10_style.txt"
        _write_table10_txt(report_path, report_row, case)
    elif report_type is not None:
        raise ValueError(f"unsupported report.type={report_type}")

    print_result_summary(rows, diagnostics)
    if report_type == "carrera_table9_style":
        print_table9_style(report_row)
    elif report_type == "carrera_table10_style":
        print_table10_style(report_row)

    print()
    print("Results written to:")
    if report_path is not None:
        print(f"  {report_path}")
    print(f"  {output_dir / 'summary.csv'}")
    print(f"  {output_dir / 'diagnostics.csv'}")


if __name__ == "__main__":
    main()
