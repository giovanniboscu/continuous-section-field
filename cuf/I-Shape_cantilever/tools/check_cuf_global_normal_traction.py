#!/usr/bin/env python3
"""Integrate the NORMAL traction on the entire loaded lower CSF surface.

This checks one scalar global resultant, not section forces, not local
volumetric equilibrium, and not the vertical resultant. The surface is
integrated over its existing CSF polygon patches only to select the correct
CUF material domain, and over its CUF x elements for quadrature. No physical
load or stress is reconstructed from case YAML or NPZ numerical arrays.

Stress recovery: csf.cuf.tools.plot_strain_stress_boundary_v10._evaluate_cuf_state
Geometry: public CSF section_provider.domain(x, domain_id)
Loaded faces: problem load adapter .physical_surface_tractions(...)

The v03 load adapter specifies GLOBAL-Z traction per XY-PROJECTED area:
  t_load = (0, 0, p_z * abs(n_z)) per physical area.
It is NOT a pressure acting in the normal direction.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def stress_tensor(s):
    # Exact v10 Voigt order: [xx, yy, zz, yz, xz, xy].
    xx, yy, zz, yz, xz, xy = np.asarray(s, dtype=float)
    return np.array([[xx, xy, xz],
                     [xy, yy, yz],
                     [xz, yz, zz]], dtype=float)


def run(case_file: Path, npz_file: Path | None, nx: int | None, nt: int | None):
    from csf.cuf.case import load_case
    from csf.cuf.problem.problem_api import load_problem, build_local_composite_problem
    from csf.cuf.csf_bridge import CSFCUFModelBridge
    from csf.cuf.solver.compiled_field import CompiledDisplacementField
    from csf.cuf.tools import plot_strain_stress_boundary_v10 as v10

    case = load_case(case_file)
    problem = load_problem(case.problem_path)
    bridge = CSFCUFModelBridge.from_yaml(problem.model_path)
    load = build_local_composite_problem(problem).load_problem
    if type(load).__name__ != "VerticalFaceTractions":
        raise ValueError("This script requires the supplied VerticalFaceTractions load adapter")

    x0, x1 = map(float, bridge.longitudinal_domain())
    faces = load.physical_surface_tractions(section_provider=bridge.section_provider,
                                            x0=x0, x1=x1)
    if not faces or any(side != "lower" for _, _, _, side in faces):
        raise ValueError("Expected ONLY the lower, externally loaded CSF faces")

    if npz_file is None:
        matches = sorted(Path(case.output_dir).glob("*.cuf.npz"))
        if len(matches) != 1:
            raise FileNotFoundError(f"Expected one CUF NPZ in {case.output_dir}, found {len(matches)}")
        npz_file = matches[0]
    field = CompiledDisplacementField.load(npz_file)
    if not np.allclose([field.x_start, field.x_end], [x0, x1], atol=1e-9, rtol=0):
        raise ValueError("CSF model length and CUF NPZ length differ")
    with np.load(npz_file, allow_pickle=False) as arrays:
        starts = np.asarray(arrays["element_x_starts"], dtype=float)
        ends = np.asarray(arrays["element_x_ends"], dtype=float)
    if not (len(starts) and starts.shape == ends.shape and
            np.all(ends > starts) and
            np.isclose(starts[0], x0, rtol=0, atol=1e-9) and
            np.isclose(ends[-1], x1, rtol=0, atol=1e-9) and
            np.allclose(starts[1:], ends[:-1], rtol=0, atol=1e-9)):
        raise ValueError("Unexpected or non-contiguous longitudinal CUF mesh")

    nx = int(load.axial_gauss if nx is None else nx)
    nt = int(load.edge_gauss if nt is None else nt)
    if nx < 2 or nt < 2:
        raise ValueError("Quadrature orders must be >= 2")
    xi, wi = np.polynomial.legendre.leggauss(nx)
    tau, wt = np.polynomial.legendre.leggauss(nt)
    provider = bridge.section_provider

    # The supplied adapter treats end-section vertex paths as affine in x.
    # Positions ALWAYS come from the public CSF provider, not from the YAML.
    speeds = {}
    for k, edge, pz, side in faces:
        V0 = np.asarray(provider.domain(x0, k).vertices, dtype=float)
        V1 = np.asarray(provider.domain(x1, k).vertices, dtype=float)
        if V0.shape != (4, 2) or V1.shape != (4, 2):
            raise ValueError("The supplied adapter requires Q4 CSF polygon faces")
        speeds[k] = (V1-V0)/(x1-x0)
        # Do not assume the end-point derivative is valid for a nonlinear CSF law.
        for fraction in (0.25, 0.5, 0.75):
            x_check = x0 + fraction*(x1-x0)
            actual = np.asarray(provider.domain(x_check, k).vertices, dtype=float)
            expected = V0 + fraction*(V1-V0)
            if not np.allclose(actual, expected, rtol=0, atol=1e-8):
                raise ValueError("Non-affine face geometry: no valid x derivative available here")

    stations = [float((a+b)/2+(b-a)/2*q)
                for a, b in zip(starts, ends) for q in xi]
    lookups = v10.validate_checkpoint_domain_lookups(field, bridge.field, stations)

    reference_normal = None
    reference_point = None
    area = 0.0
    Fnormal_stress = 0.0
    Fnormal_prescribed = 0.0
    Fvertical_stress = 0.0
    Fvertical_prescribed = 0.0
    sample_count = 0
    for a, b in zip(starts, ends):
        half = (b-a)/2
        mid = (a+b)/2
        for q, w_x in zip(xi, wi):
            x = float(mid + half*q)
            for domain_id, edge, pz, side in faces:
                vertices = np.asarray(provider.domain(x, domain_id).vertices,
                                      dtype=float)
                end_edge = (edge+1)%4
                va, vb = vertices[edge], vertices[end_edge]
                # Surface parameterization r(x,t)=(x, y(x,t), z(x,t)).
                tangent_t_yz = (vb-va)/2
                velocity = speeds[domain_id]
                for t, w_t in zip(tau, wt):
                    yz = (1-t)/2*va + (1+t)/2*vb
                    velocity_x_yz = (1-t)/2*velocity[edge] + (1+t)/2*velocity[end_edge]
                    tangent_t = np.array([0.0, *tangent_t_yz])
                    tangent_x = np.array([1.0, *velocity_x_yz])
                    # Exact oriented surface Jacobian: outward n * dA/(dx dt)
                    nA = np.cross(tangent_t, tangent_x)
                    J = float(np.linalg.norm(nA))
                    if not J > 0 or not np.isfinite(J):
                        raise ValueError("Degenerate loaded CSF surface patch")
                    n = nA/J
                    point = np.array([x, yz[0], yz[1]], dtype=float)
                    if reference_normal is None:
                        reference_normal = n
                        reference_point = point
                    elif (not np.allclose(n, reference_normal, atol=1e-9, rtol=0) or
                          abs(float(np.dot(reference_normal, point-reference_point))) > 1e-7):
                        raise ValueError("Selected loaded faces do NOT form one common plane")

                    _, _, sigma = v10._evaluate_cuf_state(
                        field, bridge.constitutive_provider, lookups[x],
                        domain_id, x, float(yz[0]), float(yz[1]))
                    t_cuf = stress_tensor(sigma) @ n
                    # Exact user adapter contract: signed global-Z load per
                    # projected XY area, converted to traction per physical area.
                    t_load = np.array([0., 0., pz*abs(float(n[2]))])
                    dA = J * half*float(w_x)*float(w_t)
                    Fnormal_stress += float(np.dot(t_cuf, n))*dA
                    Fnormal_prescribed += float(np.dot(t_load, n))*dA
                    Fvertical_stress += float(t_cuf[2])*dA
                    Fvertical_prescribed += float(t_load[2])*dA
                    area += dA
                    sample_count += 1

    delta = Fnormal_stress-Fnormal_prescribed
    print("\n[CUF] Global normal traction on the ENTIRE lower loaded surface")
    print(f"  Case                  : {case.name}")
    print(f"  Checkpoint            : {npz_file}")
    print(f"  Loaded CSF faces      : {len(faces)} (one coplanar physical surface)")
    print(f"  Quadrature            : {nx} x-points/CUF FE, {nt} points/CSF edge")
    print(f"  Samples               : {sample_count}")
    print(f"  Outward unit normal   : {reference_normal}")
    print(f"  Surface area [mm2]    : {area:.9f}")
    print(f"  Normal from load [N]  : {Fnormal_prescribed:.9f}")
    print(f"  Normal from sigma [N] : {Fnormal_stress:.9f}")
    print(f"  Normal difference [N] : {delta:.9f}")
    print(f"  Relative difference   : {100*abs(delta)/abs(Fnormal_prescribed):.6f}%")
    print(f"  Vertical from load [N]: {Fvertical_prescribed:.9f} (reference only)")
    print(f"  Vertical from sigma[N]: {Fvertical_stress:.9f} (reference only)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--npz", type=Path, default=None,
                        help="Optional CUF NPZ override; default from case.output_dir")
    parser.add_argument("--axial-gauss", type=int, default=None,
                        help="Default from load adapter")
    parser.add_argument("--edge-gauss", type=int, default=None,
                        help="Default from load adapter")
    args = parser.parse_args()
    run(args.case.resolve(), args.npz.resolve() if args.npz else None,
        args.axial_gauss, args.edge_gauss)


if __name__ == "__main__":
    main()
