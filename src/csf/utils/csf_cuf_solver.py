"""
Initial CSF-CUF solver / verification driver.

Current verification chain:
1. read the CSF YAML with the native CSFReader;
2. obtain ContinuousSectionField;
3. query section geometry through CSFSectionProvider;
4. verify the constitutive provider;
5. verify the prismatic Carrera-Giunta rectangle at x=0, L/2, L.

This file is intended to evolve into the CUF solver that will later query
the bridge for C, J, and K quantities.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from csf.io.csf_issues import CSFIssues
from csf.io.csf_reader import CSFReader
from csf.utils.csf_cuf import (
    CSFSectionProvider,
    IsotropicEGConstitutive,
)


CARRERA_GIUNTA_E_MPA = 71700.0
CARRERA_GIUNTA_NU = 0.30
CARRERA_GIUNTA_A_MM = 100.0
CARRERA_GIUNTA_B_MM = 1.0
CARRERA_GIUNTA_L_MM = 10000.0


@dataclass(frozen=True)
class ConstitutiveVerificationResult:
    E: float
    nu: float
    G: float
    C11: float
    C12: float
    C44: float
    expected_C11: float
    expected_C12: float
    expected_C44: float
    passed: bool


@dataclass(frozen=True)
class SectionVerificationResult:
    number_of_domains: int
    vertices: tuple[tuple[float, float], ...]
    constant_along_x: bool
    passed: bool


def isotropic_reference_coefficients(
    E: float,
    nu: float,
) -> tuple[float, float, float]:
    denominator = (1.0 + nu) * (1.0 - 2.0 * nu)

    C11 = E * (1.0 - nu) / denominator
    C12 = E * nu / denominator
    C44 = E / (2.0 * (1.0 + nu))

    return C11, C12, C44


def carrera_giunta_E_field(
    x: float,
    domain_id,
    y: float,
    z: float,
) -> float:
    return CARRERA_GIUNTA_E_MPA


def carrera_giunta_G_field(
    x: float,
    domain_id,
    y: float,
    z: float,
) -> float:
    return CARRERA_GIUNTA_E_MPA / (
        2.0 * (1.0 + CARRERA_GIUNTA_NU)
    )


def load_csf_field(yaml_path: str | Path):
    result = CSFReader().read_file(str(yaml_path))

    if not result.ok:
        raise RuntimeError(CSFIssues.format_report(result.issues))

    if result.field is None:
        raise RuntimeError(
            "CSFReader completed without errors but returned no field"
        )

    return result.field


def run_constitutive_verification(
    *,
    rtol: float = 1.0e-12,
    atol: float = 1.0e-12,
    verbose: bool = True,
) -> ConstitutiveVerificationResult:
    E = CARRERA_GIUNTA_E_MPA
    nu = CARRERA_GIUNTA_NU
    G = E / (2.0 * (1.0 + nu))

    constitutive = IsotropicEGConstitutive(
        E_field=carrera_giunta_E_field,
        G_field=carrera_giunta_G_field,
    )

    x = 0.0
    y = 0.0
    z = 0.0
    domain_id = 1

    C = constitutive.matrix(
        x=x,
        domain_id=domain_id,
        y=y,
        z=z,
    )

    C11 = constitutive.coefficient(
        x=x,
        domain_id=domain_id,
        m=1,
        n=1,
        y=y,
        z=z,
    )

    C12 = constitutive.coefficient(
        x=x,
        domain_id=domain_id,
        m=1,
        n=2,
        y=y,
        z=z,
    )

    C44 = constitutive.coefficient(
        x=x,
        domain_id=domain_id,
        m=4,
        n=4,
        y=y,
        z=z,
    )

    expected_C11, expected_C12, expected_C44 = (
        isotropic_reference_coefficients(E=E, nu=nu)
    )

    expected_matrix = np.array(
        [
            [expected_C11, expected_C12, expected_C12, 0.0, 0.0, 0.0],
            [expected_C12, expected_C11, expected_C12, 0.0, 0.0, 0.0],
            [expected_C12, expected_C12, expected_C11, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, expected_C44, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, expected_C44, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, expected_C44],
        ],
        dtype=float,
    )

    shape_ok = C.shape == (6, 6)
    symmetry_ok = np.allclose(C, C.T, rtol=rtol, atol=atol)
    matrix_ok = np.allclose(C, expected_matrix, rtol=rtol, atol=atol)

    coefficient_ok = all(
        (
            math.isclose(C11, expected_C11, rel_tol=rtol, abs_tol=atol),
            math.isclose(C12, expected_C12, rel_tol=rtol, abs_tol=atol),
            math.isclose(C44, expected_C44, rel_tol=rtol, abs_tol=atol),
        )
    )

    passed = shape_ok and symmetry_ok and matrix_ok and coefficient_ok

    result = ConstitutiveVerificationResult(
        E=E,
        nu=nu,
        G=G,
        C11=C11,
        C12=C12,
        C44=C44,
        expected_C11=expected_C11,
        expected_C12=expected_C12,
        expected_C44=expected_C44,
        passed=passed,
    )

    if verbose:
        print()
        print("CSF-CUF constitutive verification")
        print("=" * 36)
        print(f"E   = {result.E:.12f} MPa")
        print(f"nu  = {result.nu:.12f}")
        print(f"G   = {result.G:.12f} MPa")
        print()
        print("Coefficient      bridge              reference")
        print("-" * 51)
        print(
            f"C11       {result.C11:18.12f}  "
            f"{result.expected_C11:18.12f}"
        )
        print(
            f"C12       {result.C12:18.12f}  "
            f"{result.expected_C12:18.12f}"
        )
        print(
            f"C44       {result.C44:18.12f}  "
            f"{result.expected_C44:18.12f}"
        )
        print()
        print("RESULT: PASS" if result.passed else "RESULT: FAIL")

    return result


def run_section_verification(
    yaml_path: str | Path,
    *,
    verbose: bool = True,
) -> SectionVerificationResult:
    field = load_csf_field(yaml_path)
    provider = CSFSectionProvider(field)

    x_stations = (
        0.0,
        CARRERA_GIUNTA_L_MM / 2.0,
        CARRERA_GIUNTA_L_MM,
    )

    domains = tuple(
        provider.domain(x=x, domain_id=1)
        for x in x_stations
    )

    expected_vertices = (
        (-50.0, -0.5),
        (50.0, -0.5),
        (50.0, 0.5),
        (-50.0, 0.5),
    )

    number_of_domains_ok = all(
        provider.number_of_domains(x) == 1
        for x in x_stations
    )

    vertices_ok = all(
        domain.vertices == expected_vertices
        for domain in domains
    )

    constant_along_x = all(
        domain.vertices == domains[0].vertices
        for domain in domains
    )

    passed = number_of_domains_ok and vertices_ok and constant_along_x

    result = SectionVerificationResult(
        number_of_domains=provider.number_of_domains(0.0),
        vertices=domains[0].vertices,
        constant_along_x=constant_along_x,
        passed=passed,
    )

    if verbose:
        print()
        print("CSF-CUF YAML section verification")
        print("=" * 33)
        print(f"N_Omega = {result.number_of_domains}")
        print("vertices:")
        for vertex in result.vertices:
            print(f"  {vertex}")
        print(f"constant along x = {result.constant_along_x}")
        print()
        print("RESULT: PASS" if result.passed else "RESULT: FAIL")

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "yaml_path",
        type=Path,
        help="CSF YAML file for the Carrera-Giunta rectangle",
    )
    args = parser.parse_args()

    constitutive_result = run_constitutive_verification()
    section_result = run_section_verification(args.yaml_path)

    passed = constitutive_result.passed and section_result.passed

    print()
    print("CSF-CUF current verification status")
    print("=" * 35)
    print("OVERALL RESULT: PASS" if passed else "OVERALL RESULT: FAIL")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
