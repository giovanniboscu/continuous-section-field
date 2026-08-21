from __future__ import annotations

import argparse
import csv
from pathlib import Path

import yaml


def read_key_value_csv(path: Path) -> dict[str, float]:
    values: dict[str, float] = {}
    with path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            values[str(row["quantity"])] = float(row["value"])
    return values


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check numerical diagnostics produced by run_csf_fem3d.py."
    )
    parser.add_argument("case_yaml", type=Path)
    args = parser.parse_args()

    case_path = args.case_yaml.resolve()
    with case_path.open("r", encoding="utf-8") as f:
        case = yaml.safe_load(f)

    output_dir = (case_path.parent / case["output"]["directory"]).resolve()
    diagnostics = read_key_value_csv(output_dir / "diagnostics.csv")

    tolerance = float(case.get("checks", {}).get("equilibrium_tolerance", 1.0e-8))

    force_ok = diagnostics["force_residual"] <= tolerance
    moment_ok = diagnostics["moment_residual"] <= tolerance

    print("FEM3D check")
    print("===========")
    print(f"force residual : {diagnostics['force_residual']:.3e}")
    print(f"moment residual: {diagnostics['moment_residual']:.3e}")
    print(f"tolerance      : {tolerance:.3e}")
    print()
    print("CHECK: PASS" if force_ok and moment_ok else "CHECK: FAIL")

    raise SystemExit(0 if force_ok and moment_ok else 1)


if __name__ == "__main__":
    main()
