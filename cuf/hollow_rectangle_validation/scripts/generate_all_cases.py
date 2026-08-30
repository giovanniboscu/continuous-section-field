#!/usr/bin/env python3
# Version: CSF-CUF hollow-rectangle complete case generator v5 - 2026-08-27
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
N_MIN = 1
N_MAX = 20


def render(*, analysis: str, basis: str, basis_dir: str, order: int) -> str:
    problem = (
        "hollow_rectangle_bending_halfwave.yaml"
        if analysis == "bending"
        else "hollow_rectangle_torsion_halfwave.yaml"
    )
    return f"""# Version: CSF-CUF hollow-rectangle complete validation case v5 - 2026-08-27
case:
  name: cuf_{basis}_hollow_rectangle_{analysis}_N{order:02d}

problem:
  yaml: ../../../problems/{analysis}/{problem}
  adapter: ../../../adapters/{analysis}/problem.py

cuf:
  basis: {basis}
  order: {order}

longitudinal:
  method: finite_element
  elements: 1
  order: 6

section_integration:
  method: fixed_gauss_polygon
  gauss_order: 6

sampling:
  stations: [0.00, 0.25, 0.50, 0.75, 1.00]
  displacement_samples: 201
  stress_grid: 31

output:
  adapter: ../../../adapters/{analysis}/post.py
  directory: ../../../output/{analysis}/{basis_dir}/N{order:02d}
"""


def main():
    for analysis in ("bending", "torsion"):
        for basis, basis_dir in (
            ("scaled_legendre", "legendre"),
            ("scaled_maclaurin", "maclaurin"),
        ):
            directory = ROOT / "cases" / analysis / basis_dir
            directory.mkdir(parents=True, exist_ok=True)
            for order in range(N_MIN, N_MAX + 1):
                path = directory / f"{basis_dir}_hollow_{analysis}_N{order:02d}.yaml"
                path.write_text(
                    render(
                        analysis=analysis,
                        basis=basis,
                        basis_dir=basis_dir,
                        order=order,
                    ),
                    encoding="utf-8",
                )


if __name__ == "__main__":
    main()
