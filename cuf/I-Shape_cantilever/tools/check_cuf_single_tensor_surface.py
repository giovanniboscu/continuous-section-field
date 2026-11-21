#!/usr/bin/env python3
"""One CUF stress-traction kernel, used on transverse cuts and the loaded face.

Stages (in this order for --stage all):
    sections : N, Ty, Tz, Mx, My, Mz at five x-cuts, from C@epsilon
    lower    : global resultant on the full inclined, physically loaded face

The same function stress_traction_increment() is called in both stages.
Only the *surface quadrature samples* change (CSF section or CSF boundary).

The current adapter is VerticalFaceTractions, with global Z traction specified
per XY-projected area. Non-Q4, non-affine and non-coplanar loaded faces are
rejected rather than silently invented or interpolated.

No solver, stress-recovery law, geometry/material YAML parsing, or checkpoint
updates take place here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class SurfaceSample:
    domain_id: int
    point: np.ndarray       # Global physical coordinates (x,y,z) in mm.
    d_area: np.ndarray      # Global OUTWARD oriented area, already weighted (mm2).
    pz: float | None = None # Only defined for externally loaded faces (N/mm2 projected).


def stress_tensor(voigt: np.ndarray) -> np.ndarray:
    """Exact supplied v10 stress contract: xx, yy, zz, yz, xz, xy."""
    a = np.asarray(voigt, dtype=float)
    if a.shape != (6,) or not np.isfinite(a).all():
        raise ValueError(f"Expected 6 finite Voigt components, got {a.shape}")
    xx, yy, zz, yz, xz, xy = a
    return np.array([[xx, xy, xz],
                     [xy, yy, yz],
                     [xz, yz, zz]], dtype=float)


def stress_traction_increment(voigt: np.ndarray, sample: SurfaceSample,
                              origin: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """THE ONLY stress-to-resultant formula used for every surface.

    dF = sigma(x,y,z) @ dS ; dM = (r-origin) cross dF.
    Here dS = n * (physical Jacobian) * (quadrature weights).
    """
    dF = stress_tensor(voigt) @ sample.d_area
    dM = np.cross(sample.point - origin, dF)
    return dF, dM


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prepare_source_path(root: Path) -> None:
    # Standalone test archive: project/src/csf; installed git repo:
    # continuous-section-field/src/csf, two levels above cuf/I-Shape_cantilever.
    for candidate in (root / 'src', root.parent.parent / 'src'):
        if (candidate / 'csf' / 'cuf').is_dir():
            sys.path.insert(0, str(candidate))
            return
    # Also supports an already installed csf package.


def _validate_manifest(case, problem, checkpoint: Path, adapter_file: Path) -> Path:
    manifest_path = checkpoint.parent / 'step_manifest.json'
    if not manifest_path.is_file():
        raise FileNotFoundError(f'Missing step manifest: {manifest_path}')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('status') != 'completed' or manifest.get('case_name') != case.name:
        raise ValueError(f'Incomplete or mismatching manifest: {manifest_path}')
    for label, source in {
        'step_case': case.path,
        'problem_yaml': case.problem_path,
        'csf_model_yaml': problem.model_path,
        'load_adapter': adapter_file,
    }.items():
        target = manifest.get('inputs', {}).get(label, {}).get('sha256')
        if not target or _sha256(Path(source)) != target:
            raise ValueError(f'{label} does not match the NPZ manifest: {source}')
    if _sha256(checkpoint) != manifest.get('checkpoint_sha256'):
        raise ValueError(f'CUF checkpoint does not match the manifest: {checkpoint}')
    return manifest_path


def _load_resources(case_path: Path, npz_override: Path | None):
    root = case_path.parent.parent.parent.resolve()
    _prepare_source_path(root)
    from csf.cuf.case import load_case
    from csf.cuf.problem.problem_api import load_problem, build_local_composite_problem
    from csf.cuf.csf_bridge import CSFCUFModelBridge
    from csf.cuf.solver.compiled_field import CompiledDisplacementField
    from csf.cuf.tools import plot_strain_stress_boundary_v10 as stress_v10

    case = load_case(case_path)
    problem = load_problem(case.problem_path)
    if problem.problem_type != 'composite':
        raise ValueError(f'Unsupported problem type: {problem.problem_type}')
    load_spec = problem.problem_options.get('load')
    if not isinstance(load_spec, dict) or not isinstance(load_spec.get('adapter'), str):
        raise ValueError('Missing problem.load.adapter')
    load_adapter = (problem.path.parent / load_spec['adapter']).resolve()
    if load_adapter.name != 'vertical_face_tractions.py' or not load_adapter.is_file():
        raise ValueError(f'Only the supplied vertical_face_tractions.py is supported: {load_adapter}')
    load = build_local_composite_problem(problem).load_problem
    if type(load).__name__ != 'VerticalFaceTractions':
        raise TypeError('Unexpected load adapter type; refusing to infer its load law')
    if npz_override is None:
        files = sorted(Path(case.output_dir).glob('*.cuf.npz'))
        if len(files) != 1:
            raise FileNotFoundError(f'Expected one CUF NPZ in {case.output_dir}, got {len(files)}')
        checkpoint = files[0].resolve()
    else:
        checkpoint = npz_override.resolve()
    manifest_path = _validate_manifest(case, problem, checkpoint, load_adapter)
    field = CompiledDisplacementField.load(checkpoint)
    bridge = CSFCUFModelBridge.from_yaml(problem.model_path)
    x0, x1 = map(float, bridge.longitudinal_domain())
    if not np.allclose([x0, x1], [field.x_start, field.x_end], atol=1e-9, rtol=0):
        raise ValueError('CSF/CUF longitudinal domains differ')
    faces = load.physical_surface_tractions(section_provider=bridge.section_provider,
                                             x0=x0, x1=x1)
    if not faces or any(side != 'lower' for _, _, _, side in faces):
        raise ValueError('This one-surface audit requires lower loaded faces only')
    with np.load(checkpoint, allow_pickle=False) as npz:
        starts = np.asarray(npz['element_x_starts'], dtype=float)
        ends = np.asarray(npz['element_x_ends'], dtype=float)
    if not (len(starts) > 0 and starts.shape == ends.shape and
            np.all(ends > starts) and
            np.isclose(starts[0], x0, atol=1e-9, rtol=0) and
            np.isclose(ends[-1], x1, atol=1e-9, rtol=0) and
            np.allclose(starts[1:], ends[:-1], atol=1e-9, rtol=0)):
        raise ValueError('Invalid CUF longitudinal element partition')
    return locals()


def _edges_affine_csf(section_provider, faces, x0: float, x1: float,
                      validation_xs: list[float]) -> dict[int, np.ndarray]:
    """x-derivatives from CSF public section evaluations, reject non-affine law."""
    speeds = {}
    for domain_id, edge, pz, side in faces:
        v0 = np.asarray(section_provider.domain(x0, domain_id).vertices, dtype=float)
        v1 = np.asarray(section_provider.domain(x1, domain_id).vertices, dtype=float)
        if v0.shape != (4, 2) or v1.shape != (4, 2):
            raise ValueError('This adapter supports Q4 CSF domain faces only')
        speed = (v1 - v0) / (x1 - x0)
        for x in validation_xs:
            actual = np.asarray(section_provider.domain(float(x), domain_id).vertices,
                                dtype=float)
            # This expression is a TEST of affineness, not a reconstruction of geometry:
            # integration coordinates always come from section_provider.domain(x).
            expected = v0 + (float(x)-x0) * speed
            if not np.allclose(actual, expected, rtol=0, atol=1e-8):
                raise ValueError('CSF surface is non-affine in x: current adapter lacks a valid derivative')
        speeds[domain_id] = speed
    return speeds


def transverse_section_samples(section_provider, x: float, gauss_order: int):
    """Physical planar x=constant section using the existing CSF quadrature."""
    from csf.cuf.numerics.integration import FixedGaussPolygonIntegrator
    integrator = FixedGaussPolygonIntegrator(int(gauss_order))
    for k in range(1, section_provider.number_of_domains(x)+1):
        domain = section_provider.domain(x=x, domain_id=k)
        ys, zs, weights = integrator.quadrature_points(domain)
        for y, z, weight in zip(ys, zs, weights):
            yield SurfaceSample(k,
                                np.array([x, float(y), float(z)], dtype=float),
                                np.array([float(weight), 0., 0.], dtype=float))


def loaded_surface_samples(section_provider, faces, intervals,
                           speeds: dict[int, np.ndarray],
                           n_gauss_x: int, n_gauss_edge: int):
    """The *entire* loaded physical surface; CSF-driven Q4 boundary geometry.

    Intervals only provide FE quadrature breakpoints, not geometric interpolation.
    The edge is taken at each x from the CSF section provider.  With the
    affine-in-x check above, the x-derivative follows the supplied adapter.
    """
    x_nodes, x_weights = np.polynomial.legendre.leggauss(int(n_gauss_x))
    t_nodes, t_weights = np.polynomial.legendre.leggauss(int(n_gauss_edge))
    for a, b in intervals:
        if b <= a:
            raise ValueError('Invalid loaded-surface x interval')
        mid, half = (a+b)/2, (b-a)/2
        for xi, w_x in zip(x_nodes, x_weights):
            x = float(mid + half*xi)
            for domain_id, edge, pz, side in faces:
                vertices = np.asarray(section_provider.domain(x=x, domain_id=domain_id).vertices,
                                      dtype=float)
                if vertices.shape != (4, 2):
                    raise ValueError('Loaded CSF domain is not Q4')
                next_edge = (int(edge)+1)%4
                pa, pb = vertices[int(edge)], vertices[next_edge]
                tangent_edge = (pb-pa)/2
                vdot = speeds[int(domain_id)]
                for t, w_edge in zip(t_nodes, t_weights):
                    yz = (1-float(t))/2*pa + (1+float(t))/2*pb
                    yz_x = (1-float(t))/2*vdot[int(edge)] + (1+float(t))/2*vdot[next_edge]
                    tangent_t = np.array([0.0, *tangent_edge], dtype=float)
                    tangent_x = np.array([1.0, *yz_x], dtype=float)
                    oriented_dA = (np.cross(tangent_t, tangent_x) *
                                   half * float(w_x) * float(w_edge))
                    if not np.isfinite(oriented_dA).all() or np.linalg.norm(oriented_dA) <= 0:
                        raise ValueError('Invalid oriented surface-area vector')
                    if side == 'lower' and oriented_dA[2] >= 0:
                        raise ValueError('Loaded lower face has wrong external normal orientation')
                    yield SurfaceSample(int(domain_id),
                                        np.array([x, float(yz[0]), float(yz[1])]),
                                        oriented_dA, float(pz))


def integrate_stress(samples, field, bridge, stress_v10, domain_lookups,
                     origin: np.ndarray):
    forces = np.zeros(3)
    moments = np.zeros(3)
    area = 0.
    nsamples = 0
    normal_force = 0.
    sample_normal_ref = None
    sample_point_ref = None
    for sample in samples:
        x, y, z = map(float, sample.point)
        lookup = domain_lookups[x]
        _, _, sigma = stress_v10._evaluate_cuf_state(
            field, bridge.constitutive_provider, lookup, sample.domain_id,
            x, y, z)
        dF, dM = stress_traction_increment(sigma, sample, origin)
        forces += dF
        moments += dM
        dA = float(np.linalg.norm(sample.d_area))
        area += dA
        nsamples += 1
        if sample.pz is not None:
            unit = sample.d_area/dA
            if sample_normal_ref is None:
                sample_normal_ref = unit
                sample_point_ref = sample.point
            elif (np.linalg.norm(unit-sample_normal_ref) > 1e-9 or
                  abs(float(np.dot(sample_normal_ref, sample.point-sample_point_ref))) > 1e-7):
                raise ValueError('Loaded faces are not one coplanar physical surface')
            normal_force += float(np.dot(dF, unit))
    return {'F': forces, 'M': moments, 'area': area, 'samples': nsamples,
            'F_normal': normal_force,
            'n': sample_normal_ref}


def integrate_prescribed_load(samples, origin: np.ndarray,
                              require_coplanar: bool = False):
    F = np.zeros(3)
    M = np.zeros(3)
    Fnormal = 0.
    area = 0.
    count = 0
    normal_ref = None
    point_ref = None
    for sample in samples:
        if sample.pz is None:
            raise ValueError('Load integral requires loaded-surface samples')
        # Exact contract of supplied adapter: global-Z traction per
        # XY-projected area.  dA[2] includes the projected area and quadrature.
        dF = np.array([0., 0., sample.pz * abs(float(sample.d_area[2]))])
        dM = np.cross(sample.point-origin, dF)
        F += dF
        M += dM
        da = float(np.linalg.norm(sample.d_area))
        area += da
        count += 1
        if require_coplanar:
            n = sample.d_area/da
            if normal_ref is None:
                normal_ref, point_ref = n, sample.point
            elif (np.linalg.norm(n-normal_ref) > 1e-9 or
                  abs(float(np.dot(normal_ref, sample.point-point_ref))) > 1e-7):
                raise ValueError('Prescribed loaded faces are not coplanar')
            Fnormal += float(np.dot(dF,n))
    return {'F': F, 'M': M, 'area': area, 'samples': count,
            'F_normal': Fnormal, 'n': normal_ref}


def _write_report(data: dict, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir/'result.json').write_text(json.dumps(data, indent=2, allow_nan=False)+'\n',
                                          encoding='utf-8')
    if data['section_cuts']:
        with (output_dir/'sections.csv').open('w', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=data['section_cuts'][0].keys())
            writer.writeheader()
            writer.writerows(data['section_cuts'])
    readme = ['# CUF traction audit — single stress integration kernel', '',
              'Same formula on cross sections and loaded face: `dF = sigma @ dS`, '
              '`dM = (r-O) x dF`.  The stress is reconstructed through '
              '`csf.cuf.tools.plot_strain_stress_boundary_v10._evaluate_cuf_state()`.',
              '', '## Sections: N, T and M', '',
              '| x/L | N [N] | Tz [N] | Tz load [N] | My [N mm] | My load [N mm] |',
              '|---:|---:|---:|---:|---:|---:|']
    for row in data['section_cuts']:
        readme.append('| '+ ' | '.join([
            f'{row["x_L"]:.3f}', f'{row["N_N"]:.8g}',
            f'{row["Tz_N"]:.8g}', f'{row["Tz_load_N"]:.8g}',
            f'{row["My_Nmm"]:.8g}', f'{row["My_load_Nmm"]:.8g}'])+' |')
    if data['lower']:
        lo = data['lower']
        readme += ['', '## Entire loaded lower surface', '',
                   f'Physical area: {lo["area_mm2"]:.9f} mm2; '
                   f'unit normal: {lo["normal"]}.',
                   f'Prescribed normal force: {lo["Fnormal_load_N"]:.8f} N.',
                   f'CUF stress normal force: {lo["Fnormal_sigma_N"]:.8f} N.',
                   f'Difference: {lo["Fnormal_delta_N"]:.8f} N.',
                   f'Prescribed vertical force: {lo["Fz_load_N"]:.8f} N.',
                   f'CUF stress vertical force: {lo["Fz_sigma_N"]:.8f} N.',
                   '', 'Normal load is the projection of the GLOBAL-Z '
                   'prescribed load, not an independent normal pressure.']
    readme += ['', 'This is a recovery/integration diagnostic. The CSV and '
               'JSON preserve all six force/moment components.']
    (output_dir/'README.md').write_text('\n'.join(readme)+'\n', encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case', required=True, type=Path)
    ap.add_argument('--npz', type=Path, help='Optional CUF NPZ override')
    ap.add_argument('--stage', choices=['all', 'sections', 'lower'], default='all',
                    help='Default: compute sections FIRST, then lower surface')
    ap.add_argument('--cuts', default='0,0.125,0.375,0.625,0.875',
                    help='Normalized section locations x/L')
    ap.add_argument('--section-gauss', type=int, help='Default: case section quadrature')
    ap.add_argument('--axial-gauss', type=int, help='Default: original load adapter')
    ap.add_argument('--edge-gauss', type=int, help='Default: original load adapter')
    ap.add_argument('--output-root', type=Path, help='Optional diagnostics directory')
    args = ap.parse_args()

    if args.section_gauss is not None and args.section_gauss < 2:
        raise ValueError('Section quadrature order must be >= 2')
    if args.axial_gauss is not None and args.axial_gauss < 2:
        raise ValueError('Axial quadrature order must be >= 2')
    if args.edge_gauss is not None and args.edge_gauss < 2:
        raise ValueError('Edge quadrature order must be >= 2')

    context = _load_resources(args.case.resolve(), args.npz)
    case = context['case']
    bridge = context['bridge']
    field = context['field']
    stress_v10 = context['stress_v10']
    load = context['load']
    checkpoint = context['checkpoint']
    x0, x1 = context['x0'], context['x1']
    faces = context['faces']
    starts, ends = context['starts'], context['ends']
    provider = bridge.section_provider

    section_gauss = int(args.section_gauss or case.section_integration.gauss_order)
    nx = int(args.axial_gauss or load.axial_gauss)
    nt = int(args.edge_gauss or load.edge_gauss)
    cuts = sorted(float(t) for t in args.cuts.split(','))
    if not cuts or len(set(cuts)) != len(cuts) or any(not (0<=f<1) for f in cuts):
        raise ValueError('--cuts must be distinct finite positions 0<=x/L<1')
    cut_positions = [x0+(x1-x0)*f for f in cuts] if args.stage in ('all','sections') else []
    fe_intervals = list(zip(starts,ends))
    xs_quadrature = np.polynomial.legendre.leggauss(nx)[0]
    surface_xs = [float((a+b)/2+(b-a)/2*q) for a,b in fe_intervals for q in xs_quadrature]
    stations = cut_positions + (surface_xs if args.stage in ('all','lower') else [])
    # The same CSF API supplies exact physical cross-section and face points.
    lookups = stress_v10.validate_checkpoint_domain_lookups(field,bridge.field,stations)
    if any(v is None for v in lookups.values()):
        raise ValueError('Cannot reconcile physical CSF domains and CUF checkpoint')

    speeds = _edges_affine_csf(provider,faces,x0,x1,
                              [x0+(x1-x0)*f for f in (0.25,0.5,0.75)] + surface_xs)

    result = {'case': case.name, 'checkpoint': str(checkpoint),
              'checkpoint_sha256': _sha256(checkpoint),
              'csf_model': str(context['problem'].model_path),
              'load_adapter': str(context['load_adapter']),
              'stress_module': str(Path(stress_v10.__file__).resolve()),
              'manifest': str(context['manifest_path']),
              'method': {'stress_kernel': 'stress_traction_increment: dF=sigma@dA, dM=cross(r-origin,dF)',
                         'voigt': ['xx','yy','zz','yz','xz','xy'],
                         'section_gauss': section_gauss,'surface_axial_gauss':nx,
                         'surface_edge_gauss':nt,
                         'section_orientation': '+ex',
                         'loaded_surface_orientation':'CSF Q4 physical lower exterior normal'},
              'section_cuts': [], 'lower': None}
    if args.stage in ('all','sections'):
        print(f'[1/2] Section resultants from the SHARED stress kernel: {case.name}',flush=True)
        for fraction,x in zip(cuts,cut_positions):
            O = np.array([x,0.,0.])
            Fs = integrate_stress(transverse_section_samples(provider,x,section_gauss),
                                  field,bridge,stress_v10,lookups,O)
            # Prescribed load on RIGHT portion of the beam. Load integration
            # uses the same CSF faces, not the CUF stress field.
            load_samples = loaded_surface_samples(provider,faces,[(x,x1)],speeds,nx,nt)
            L = integrate_prescribed_load(load_samples,O)
            row={'x_L':float(fraction), 'x_mm':float(x),
                 'section_area_mm2':float(Fs['area']),
                 'N_N':float(Fs['F'][0]),'Ty_N':float(Fs['F'][1]),
                 'Tz_N':float(Fs['F'][2]),
                 'Mx_Nmm':float(Fs['M'][0]), 'My_Nmm':float(Fs['M'][1]),
                 'Mz_Nmm':float(Fs['M'][2]),
                 'Tz_load_N':float(L['F'][2]),
                 'My_load_Nmm':float(L['M'][1]),
                 'dTz_N':float(Fs['F'][2]-L['F'][2]),
                 'dMy_Nmm':float(Fs['M'][1]-L['M'][1]),
                 'section_samples':int(Fs['samples'])}
            result['section_cuts'].append(row)
            print(f"  x/L={fraction:.3f} N={row['N_N']:.6g} N "
                  f"Tz={row['Tz_N']:.6f} N (load {row['Tz_load_N']:.6f}) "
                  f"My={row['My_Nmm']:.4f} Nmm (load {row['My_load_Nmm']:.4f})",flush=True)
    if args.stage in ('all','lower'):
        print('[2/2] Global loaded lower surface from the SAME stress kernel',flush=True)
        O = np.array([x0,0.,0.])
        # We traverse the contiguous FE intervals only as quadrature partitions;
        # physically the sum is ONE entire loaded surface.
        samples = loaded_surface_samples(provider,faces,fe_intervals,speeds,nx,nt)
        S = integrate_stress(samples,field,bridge,stress_v10,lookups,O)
        L = integrate_prescribed_load(
            loaded_surface_samples(provider,faces,fe_intervals,speeds,nx,nt),O,
            require_coplanar=True)
        result['lower']={'normal':S['n'].tolist(),
                         'area_mm2':S['area'],'samples':S['samples'],
                         'F_sigma_N':S['F'].tolist(), 'F_load_N':L['F'].tolist(),
                         'M_sigma_Nmm':S['M'].tolist(), 'M_load_Nmm':L['M'].tolist(),
                         'Fnormal_sigma_N':S['F_normal'],
                         'Fnormal_load_N':L['F_normal'],
                         'Fnormal_delta_N':S['F_normal']-L['F_normal'],
                         'Fz_sigma_N':S['F'][2], 'Fz_load_N':L['F'][2]}
        print(f"  Loaded physical area: {S['area']:.8f} mm2; normal {S['n']}",flush=True)
        print(f"  Normal from load: {L['F_normal']:.8f} N; "
              f"normal from sigma: {S['F_normal']:.8f} N",flush=True)
        print(f"  Vertical from load: {L['F'][2]:.8f} N; "
              f"vertical from sigma: {S['F'][2]:.8f} N",flush=True)

    outroot = (args.output_root.resolve() if args.output_root else
               (args.case.resolve().parent.parent.parent/'diagnostics'/
                'cuf_single_tensor_traction'/case.name))
    outroot.mkdir(parents=True,exist_ok=True)
    for idx in range(1,10000):
        out = outroot/f'run_{idx:04d}'
        if not out.exists():
            _write_report(result,out)
            break
    else:
        raise RuntimeError('No free run name under output root')
    print(f'[report] {out}',flush=True)
    return 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'[ERROR] {exc}',file=sys.stderr)
        raise SystemExit(2) from exc
