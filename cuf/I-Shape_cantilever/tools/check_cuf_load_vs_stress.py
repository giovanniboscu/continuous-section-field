#!/usr/bin/env python3
"""Audit physical load resultants against CUF stress resultants at beam cuts.

Uses only public CSF/CUF model providers and the supplied
plot_strain_stress_boundary_v10.py stress recovery helper. The former
provides physical geometry and quadrature; the latter computes sigma=C@eps.
Does not solve, modify checkpoints, or infer loading from displacement.

For the *right* portion of the beam [x_cut, x1]:
    integral_{section(x_cut)} sigma . e_x dA
        ?= integral_{loaded surfaces, x>=x_cut} t dS
and similarly for moments about (x_cut,0,0).

Only the provided vertical_face_tractions adapter is supported: an unsupported
load adapter must raise rather than be silently approximated.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


def _load_module(path: Path, name: str):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Missing required source: {path}")
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _check_manifest(directory, case, model_path, load_path, checkpoint):
    path = directory / 'step_manifest.json'
    if not path.is_file():
        raise FileNotFoundError(f"Checkpoint provenance manifest is missing: {path}")
    record = json.loads(path.read_text(encoding='utf-8'))
    if record.get('status') != 'completed':
        raise ValueError(f"Checkpoint manifest not completed: {path}")
    checks = {
        'step_case': case.path,
        'problem_yaml': case.problem_path,
        'csf_model_yaml': model_path,
        'load_adapter': load_path,
    }
    for label, file in checks.items():
        expected = record.get('inputs', {}).get(label, {}).get('sha256')
        if not expected or _sha(file) != expected:
            raise ValueError(f"Provenance mismatch for {label} at {file}")
    if record.get('checkpoint_sha256') != _sha(checkpoint):
        raise ValueError(f"Checkpoint SHA-256 mismatch: {checkpoint}")
    if record.get('case_name') != case.name:
        raise ValueError("Manifest and CUF case names differ")
    return path


def _resolve_load_path(problem):
    raw = problem.problem_options.get('load')
    if not isinstance(raw, dict):
        raise ValueError("Expected a single local composite problem.load mapping")
    ref = raw.get('adapter')
    if not isinstance(ref, str) or Path(ref).suffix != '.py':
        raise ValueError("This audit requires a load adapter specified by a .py file")
    return (problem.path.parent / ref).resolve()


def _load_resultants(load, provider, loaded_faces, lower_x, upper_x, origin_x):
    """Integrate the exact projected-area law of vertical_face_tractions v03.

    Query the physical CSF polygon *at each x Gauss point*, rather than
    constructing, interpolating, or assuming sections independently.
    The only edge parameterization is the Q4 straight boundary segment, as
    in the load adapter's build_load_vector().
    """
    resultant = np.zeros(3)
    moment = np.zeros(3)
    if not upper_x > lower_x:
        return resultant, moment
    gx, wx = np.polynomial.legendre.leggauss(load.axial_gauss)
    gt, wt = np.polynomial.legendre.leggauss(load.edge_gauss)
    xmid = (lower_x + upper_x) / 2.0
    xhalf = (upper_x - lower_x) / 2.0
    for xi, wi in zip(gx, wx):
        x = xmid + xhalf * float(xi)
        dx = xhalf * float(wi)
        for domain_id, edge, pz, side in loaded_faces:
            domain = provider.domain(x=x, domain_id=domain_id)
            vertices = np.asarray(domain.vertices, dtype=float)
            if vertices.shape != (4, 2):
                raise ValueError("The original load adapter requires Q4 physical faces")
            j = (int(edge) + 1) % 4
            a, b = vertices[int(edge)], vertices[j]
            tangent = 0.5 * (b - a)
            # For t = (0,0,pz*|n_z|), the projected area measure is
            # |n_z| dS = |dy/dt| dx dt (per load adapter implementation).
            weighted_fz = float(pz) * abs(float(tangent[0])) * dx
            for t, w in zip(gt, wt):
                yz = 0.5 * ((1.0-float(t))*a + (1.0+float(t))*b)
                dF = np.array([0.0, 0.0, weighted_fz * float(w)])
                resultant += dF
                moment += np.cross([x-origin_x, float(yz[0]), float(yz[1])], dF)
    return resultant, moment


def _stress_resultants(stress_tool, field, bridge, x, order):
    """Recover C@eps through the user's plotting tool and integrate by CUF rule."""
    from csf.cuf.numerics.integration import FixedGaussPolygonIntegrator
    quadrature = FixedGaussPolygonIntegrator(int(order))
    lookup = stress_tool.validate_checkpoint_domain_lookups(
        field, bridge.field, [x]
    )[float(x)]
    if lookup is None:
        raise ValueError("Expected v5 checkpoint with validated CSF domain identities")
    forces = np.zeros(3)
    moments = np.zeros(3)
    area = 0.0
    evaluations = 0
    for domain_id in range(1, bridge.section_provider.number_of_domains(x) + 1):
        domain = bridge.section_provider.domain(x, domain_id)
        ys, zs, ws = quadrature.quadrature_points(domain)
        for y, z, w in zip(ys, zs, ws):
            _, _, sigma = stress_tool._evaluate_cuf_state(
                field, bridge.constitutive_provider, lookup, domain_id,
                float(x), float(y), float(z)
            )
            # Voigt: (xx,yy,zz,yz,xz,xy). Traction on +ex section.
            dF = np.array([sigma[0], sigma[5], sigma[4]], dtype=float)*float(w)
            forces += dF
            moments += np.cross([0.0, float(y), float(z)], dF)
            area += float(w)
            evaluations += 1
    return forces, moments, area, evaluations


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case', type=Path, required=True, help='CUF case YAML')
    ap.add_argument('--npz', type=Path, help='CUF checkpoint (otherwise discover unique one in output dir)')
    ap.add_argument('--stress-script', type=Path, help='Path of supplied plot_strain_stress_boundary_v10.py')
    ap.add_argument('--cuts', default='0,0.125,0.375,0.625,0.875',
                    help='Comma-separated section locations x/L; default includes clamp section')
    ap.add_argument('--section-gauss', type=int,
                    help='Sectional Gauss order (default = case.section_integration.gauss_order)')
    ap.add_argument('--output-dir', type=Path,
                    help='Output directory; default diagnostics/cuf_load_vs_stress/<case-name>')
    args=ap.parse_args()
    case_path=args.case.resolve()
    project = case_path.parent.parent.parent.resolve() # project/cases/convergence_h_v02/step_008.yaml
    sys.path.insert(0, str(project / 'src'))
    from csf.cuf.case import load_case
    from csf.cuf.problem.problem_api import load_problem, build_local_composite_problem
    from csf.cuf.csf_bridge import CSFCUFModelBridge
    from csf.cuf.solver.compiled_field import CompiledDisplacementField
    case = load_case(case_path)
    problem=load_problem(case.problem_path)
    if problem.problem_type != 'composite':
        raise ValueError('Unsupported problem: this audit handles the supplied composite vertical-face load')
    load_path=_resolve_load_path(problem)
    if load_path.name != 'vertical_face_tractions.py':
        raise ValueError(f'Unsupported load adapter for this audit: {load_path.name}')
    if args.npz is None:
        candidates = sorted(case.output_dir.glob('*.cuf.npz'))
        if len(candidates) != 1:
            raise ValueError(f'Expected exactly one CUF NPZ in {case.output_dir}; got {len(candidates)}; supply --npz')
        checkpoint=candidates[0].resolve()
    else:
        checkpoint=args.npz.resolve()
    manifest=_check_manifest(checkpoint.parent,case,problem.model_path,load_path,checkpoint)
    stress_path=(args.stress_script.resolve() if args.stress_script is not None else project/'plot_strain_stress_boundary_v10.py')
    stress_tool=_load_module(stress_path,'_supplied_cuf_stress_tool')
    for method in ('validate_checkpoint_domain_lookups', '_evaluate_cuf_state'):
        if not callable(getattr(stress_tool, method, None)):
            raise TypeError(f'Supplied stress script does not expose required {method}()')
    bridge=CSFCUFModelBridge.from_yaml(problem.model_path)
    field=CompiledDisplacementField.load(checkpoint)
    x0,x1=map(float,bridge.longitudinal_domain())
    domain_at_cuf=(float(field.x_start),float(field.x_end))
    if not np.allclose([x0,x1],domain_at_cuf,rtol=0,atol=1e-10*max(abs(x0),abs(x1),1)):
        raise ValueError('CSF longitudinal interval differs from CUF checkpoint')
    composite=build_local_composite_problem(problem)
    load=composite.load_problem
    # Refuse a different load law, rather than fabricating a replacement.
    if load.__class__.__name__ != 'VerticalFaceTractions':
        raise TypeError(f'Unsupported load contract: {type(load)!r}')
    faces=load.physical_surface_tractions(section_provider=bridge.section_provider,x0=x0,x1=x1)
    if not faces:
        raise ValueError('No prescribed loaded faces found')
    order=int(args.section_gauss or case.section_integration.gauss_order)
    if order<2:
        raise ValueError('Section quadrature order must be >= 2')
    try:
        fractions=[float(s) for s in args.cuts.split(',')]
    except ValueError as exc:
        raise ValueError('--cuts must be comma-separated numeric fractions') from exc
    if not fractions or any(not np.isfinite(t) or t<0.0 or t>=1.0 for t in fractions):
        raise ValueError('Cuts must be finite normalized fractions in [0,1)')
    if len(set(fractions))!=len(fractions):
        raise ValueError('Duplicate cut station')
    fractions=sorted(fractions)

    # Independently integrate the original physical load adapter law.
    total_F,total_M=_load_resultants(load,bridge.section_provider,faces,x0,x1,x0)
    Fscale=float(np.linalg.norm(total_F))
    Mscale=float(np.linalg.norm(total_M))
    if not Fscale>0:
        raise ValueError('Global applied resultant is zero; choose explicit scales for this study')
    rows=[]
    print(f'[CUF load/stress audit] case: {case.name}')
    print(f'  checkpoint: {checkpoint}')
    print(f'  stress source: {stress_path}')
    print(f'  sectional Gauss: {order}; loaded faces: {len(faces)}')
    print(f'  prescribed full F[N]={total_F}; M_about_x0[Nmm]={total_M}')
    print('    x/L    Fz_load[N]      Fz_stress[N]    dFz[N]       My_load[Nmm]     My_stress[Nmm]     dMy[Nmm]   |dF|/|Ftot|[%]')
    for fraction in fractions:
        x=x0+fraction*(x1-x0)
        Fext,Mext=_load_resultants(load,bridge.section_provider,faces,x,x1,x)
        Fs,Ms,area,nevals=_stress_resultants(stress_tool,field,bridge,x,order)
        dF=Fs-Fext
        dM=Ms-Mext
        row={'x_over_L':fraction,'x':x,'section_area_mm2':area,'section_samples':nevals}
        for group,values in [('applied_F_N',Fext),('stress_F_N',Fs),('difference_F_N',dF),
                             ('applied_M_Nmm',Mext),('stress_M_Nmm',Ms),('difference_M_Nmm',dM)]:
            for key,value in zip('xyz',values):
                row[f'{group}_{key}']=float(value)
        row['difference_force_over_full_force_percent']=float(100*np.linalg.norm(dF)/Fscale)
        row['difference_moment_over_full_moment_percent']=(float(100*np.linalg.norm(dM)/Mscale) if Mscale>0 else None)
        rows.append(row)
        print(f'   {fraction:5.3f}  {Fext[2]:14.6f} {Fs[2]:14.6f} {dF[2]:11.5f} {Mext[1]:16.3f} {Ms[1]:16.3f} {dM[1]:11.3f}  {row["difference_force_over_full_force_percent"]:10.4e}')

    if args.output_dir is not None:
        out = args.output_dir.resolve()
        if out.exists() and any(out.iterdir()):
            raise FileExistsError(f'Refusing to overwrite existing output: {out}')
        out.mkdir(parents=True,exist_ok=True)
    else:
        base=project/'diagnostics/cuf_load_vs_stress'/case.name
        base.mkdir(parents=True,exist_ok=True)
        for i in range(1,10000):
            out=base/f'run_{i:04d}'
            try:
                out.mkdir(exist_ok=False)
                break
            except FileExistsError:
                continue
        else:
            raise RuntimeError(f'No available run number under {base}')
    csv_file=out/'section_load_vs_stress.csv'
    with csv_file.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    result={
        'definition': 'right-segment external loading vs CUF section +ex stress traction',
        'frame': 'global (x,y,z); moment origin per cut (x_cut,0,0)',
        'units': {'force':'N','moment':'Nmm','coordinate':'mm','stress':'MPa'},
        'input':{'case':str(case.path),'case_sha256':_sha(case.path),
                 'checkpoint':str(checkpoint),'checkpoint_sha256':_sha(checkpoint),
                 'csf_model':str(problem.model_path),'csf_model_sha256':_sha(problem.model_path),
                 'load_adapter':str(load_path),'load_adapter_sha256':_sha(load_path),
                 'stress_script':str(stress_path),'stress_script_sha256':_sha(stress_path),
                 'manifest':str(manifest)},
        'method':{'section_gauss_order':order,'load_axial_gauss':load.axial_gauss,
                  'load_edge_gauss':load.edge_gauss,'boundary_stress_recovery':'_evaluate_cuf_state (C@strain)',
                  'section_quadrature':'FixedGaussPolygonIntegrator.quadrature_points over CSF domains'},
        'total_applied_F_N':total_F.tolist(),
        'total_applied_M_about_x0_Nmm':total_M.tolist(),
        'cuts':rows,
        'interpretation':'Postprocessed strong-form sectional stress-resultant diagnostic. Not the discrete CUF KKT reaction residual, nor a proof of exact boundary traction equilibrium.'
    }
    (out/'section_load_vs_stress.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    md=['# CUF load-versus-stress resultant audit', '',
        f'Case: `{case.name}`. Cross-section Gauss order: **{order}**.',
        f'Checkpoint: `{checkpoint.name}`.',
        'All forces in N; moments in N mm; x is physical CSF longitudinal coordinate.', '',
        'Total prescribed load, about the fixed-section center O=(x0,0,0):',
        f'- F = ({total_F[0]:.9g}, {total_F[1]:.9g}, {total_F[2]:.9g}) N',
        f'- M = ({total_M[0]:.9g}, {total_M[1]:.9g}, {total_M[2]:.9g}) N mm', '',
        'At each cut x, the applied load is integrated over the **right-hand** span [x,x1].',
        'The CUF resultant is integrated over the cut using t = sigma e_x.',
        'Moment origin is (x,0,0). Positive values have the same global Cartesian convention.', '',
        '| x/L | Applied Fz [N] | CUF stress Fz [N] | dFz [N] | Applied My [Nmm] | CUF stress My [Nmm] | dMy [Nmm] | ||dF||/||F_total|| [%] |',
        '|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        md.append('| '+ ' | '.join((
            f'{row["x_over_L"]:.3f}',
            f'{row["applied_F_N_z"]:.9g}',
            f'{row["stress_F_N_z"]:.9g}',
            f'{row["difference_F_N_z"]:.9g}',
            f'{row["applied_M_Nmm_y"]:.9g}',
            f'{row["stress_M_Nmm_y"]:.9g}',
            f'{row["difference_M_Nmm_y"]:.9g}',
            f'{row["difference_force_over_full_force_percent"]:.6g}',
        )) + ' |')
    md += ['', '**Complete six-component audit:** `section_load_vs_stress.csv` and `.json`.', '',
           'This verifies *section-integrated recovered stresses* versus the original physical load.',
           'It is **not** a check of discrete CUF support reactions or a pointwise traction-equilibrium proof.',
           'At x=x0, the clamped-end stress field may show an end effect.', '']
    (out/'README.md').write_text('\n'.join(md),encoding='utf-8')
    print(f'  report: {out}')
    return 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'[CUF load/stress audit] ERROR: {exc}',file=sys.stderr)
        raise SystemExit(2) from exc
