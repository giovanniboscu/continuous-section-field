#!/usr/bin/env python3
"""Shared validated orchestration for the independent CUF longitudinal studies v02.

Solver stage and CUF-FEM3D comparison stage use separate entrypoint scripts.
The comparator and the solver are never modified by this module.
"""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import zipfile
import numpy as np
import yaml

# Reference GCI selection and comparator summary readers are copied verbatim
# from the existing run_cuf_p_fem3d_comparison.py v01; do not change their
# numerical decisions or sampling fields.


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for piece in iter(lambda: f.read(1048576), b''):
            h.update(piece)
    return h.hexdigest()

def read_json(path):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError(f'Expected JSON object: {path}')
    return value

def finite(value, label):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f'{label} must be finite and nonnegative; got {value!r}')
    return float(value)

def selected_fem(result_file):
    """Only a genuine GCI v03.1 study selection; do not assert field convergence."""
    result_file = Path(result_file).resolve()
    data = read_json(result_file)
    if data.get('method') != 'gci' or data.get('status') != 'gci_selection_criterion_met' or data.get('gci_selection_criterion_met') is not True:
        raise ValueError('GCI selection criterion not satisfied in convergence_result.json')
    step, mesh = data.get('selected_step'), data.get('selected_mesh_divisions')
    if type(step) is not int or step < 1 or not isinstance(mesh, list) or len(mesh) != 3 or any(type(n) is not int or n < 1 for n in mesh):
        raise ValueError('Invalid selected GCI step or mesh divisions')
    if data.get('selected_mesh') != 'x'.join(map(str, mesh)):
        raise ValueError('GCI selected_mesh and divisions disagree')
    gci, tol = finite(data.get('selected_gci_pct'), 'selected GCI'), finite(data.get('tolerance_pct'), 'GCI tolerance')
    if gci > tol + 1e-12:
        raise ValueError('Selected GCI is above reported tolerance')
    rows = data.get('rows')
    if not isinstance(rows, list) or step > len(rows):
        raise ValueError('Selected GCI row absent')
    r = rows[step-1]
    if r.get('step') != step or [r.get(k) for k in ('nx','nu','nv')] != mesh or r.get('eligible_for_selection') is not True:
        raise ValueError('GCI selected row is inconsistent with selected mesh')
    if r.get('gci_pct') is None or not math.isclose(float(r['gci_pct']), gci, rel_tol=1e-10, abs_tol=1e-12):
        raise ValueError('GCI in selected row differs from reported GCI')
    fem = result_file.parent / f'step_{step:03d}' / 'solution.npz'
    if not fem.is_file():
        raise FileNotFoundError(f'Selected FEM3D checkpoint not found: {fem}')
    claimed = data.get('selected_npz')
    if not isinstance(claimed, str) or not claimed:
        raise ValueError('GCI report missing selected_npz')
    if Path(claimed).is_file() and not Path(claimed).samefile(fem):
        raise ValueError('selected_npz does not identify the selected GCI step')
    with np.load(fem, allow_pickle=False) as n:
        if ('status' not in n or str(n['status'].item()) != 'solved_opensees'
            or 'mesh_divisions' not in n or list(map(int,n['mesh_divisions'])) != mesh
            or 'case_name' not in n):
            raise ValueError('FEM3D checkpoint is not the selected solved mesh')
        case_name = str(n['case_name'].item())
        if 'elements' not in n or 'nodes' not in n or 'displacement' not in n:
            raise ValueError('FEM3D checkpoint lacks solved field arrays')
        if len(n['elements']) != data.get('selected_h8_elements'):
            raise ValueError('FEM3D element count differs from GCI report')
    manifest_file = result_file.parent / 'manifest.json'
    if not manifest_file.is_file():
        raise FileNotFoundError(f'GCI manifest missing: {manifest_file}')
    manifest = read_json(manifest_file)
    if manifest.get('method') != 'gci' or manifest.get('inputs',{}).get('case_name') != case_name:
        raise ValueError('GCI manifest and selected FEM case identity differ')
    if [manifest.get('nu'),manifest.get('nv')] != mesh[1:]:
        raise ValueError('GCI fixed transverse divisions conflict with selected mesh')
    return {'data':data, 'manifest':manifest, 'path':fem.resolve(),
            'sha256':sha(fem), 'case_name':case_name,
            'report_file':result_file, 'manifest_file':manifest_file}

def physical_case(gci, case_path):
    """Read physical *references* through official CSF APIs, not YAML parsing."""
    from csf.cuf.case import load_case
    from csf.cuf.problem.problem_api import load_problem
    case = load_case(case_path)
    problem = load_problem(case.problem_path)
    if case.name != gci['case_name']:
        raise ValueError('Original --base-case does not match the FEM3D checkpoint case_name')
    inputs = gci['manifest'].get('inputs',{}).get('files',{})
    paths = {'case':Path(case.path), 'problem':Path(problem.path),
             'csf_model':Path(problem.model_path)}
    for kind in ('load','constraint'):
        opts=problem.problem_options.get(kind)
        if isinstance(opts,dict) and 'adapter' in opts:
            name=str(opts['adapter'])
            if name.endswith('.py') or '/' in name or '\\' in name:
                x=Path(name)
                paths[kind+'_adapter'] = x if x.is_absolute() else Path(problem.path).parent/x
    for kind, path in paths.items():
        if not path.is_file() or inputs.get(kind,{}).get('sha256') != sha(path):
            raise ValueError(f'Physical input differs from GCI study: {kind}: {path}')
    return case

def metrics_from_summary(path, fem, fem_hash, cuf, base, sampling):
    d=read_json(path)
    inputs=d.get('inputs',{})
    if inputs.get('sha256_fem')!=fem_hash or inputs.get('sha256_cuf')!=sha(cuf):
        raise ValueError('Comparator checkpoint fingerprints mismatch')
    for key, expected in (('fem',fem),('cuf',cuf),('case',base)):
        if Path(inputs.get(key,'')).resolve()!=Path(expected).resolve():
            raise ValueError(f'Comparator used a different {key} input')
    modes=['centers','nodes'] if sampling=='both' else [sampling]
    if list(d.get('sampling',{}).get('modes',[]))!=modes:
        raise ValueError('Comparator sampling mode mismatch')
    mode='gauss2' if sampling=='gauss2' else 'centers'
    selected=d.get('results',{}).get(mode,{})
    weight=selected.get('physical_quadrature',{})
    percent=finite(weight.get('vector_weighted_relative_l2_percent'), 'volume-weighted L2 %')
    rms=finite(weight.get('vector_weighted_rmse_norm'),'weighted displacement RMS')
    volume=finite(weight.get('approximate_volume_native_cubed'),'FEM quadrature volume')
    count=selected.get('samples')
    if volume<=0 or type(count) is not int or count<=0:
        raise ValueError('Invalid FEM H8 sampling count/volume')
    out={'relative_l2_percent':percent,'weighted_rms':rms,'volume':volume,'samples':count}
    for component in ('ux','uy','uz'):
        x=weight.get('components',{}).get(component,{}).get('weighted_relative_l2_percent')
        out[component+'_relative_l2_percent']=None if x is None else finite(x,component+' relative L2')
    v=d.get('results',{}).get('nodes',{}).get('vector',{}).get('relative_l2_percent')
    out['node_relative_l2_percent'] = None if v is None else finite(v,'node relative L2')
    return out

def new_run(root):
    root.mkdir(parents=True,exist_ok=True)
    for n in range(1,100000):
        candidate=root/f'run_{n:04d}'
        try:
            candidate.mkdir(exist_ok=False)
            return candidate
        except FileExistsError:pass
    raise RuntimeError('No free run directory')


# Numerical definitions from the author's earlier p- and h-refinement plans.
BASE_NAME = 'i_shaped_taper80_lagrangeL9_v4_E10_web3_composite.yaml'
H_ELEMENTS = (2, 4, 6, 8, 10, 12, 16, 20)
P_ORDERS = tuple(range(2, 13))
VERSION = 'CSF-CUF independent longitudinal studies v02 (2026-11-20)'


def sequence(kind):
    if kind == 'p':
        return tuple((10, p) for p in P_ORDERS)
    if kind == 'h':
        return tuple((n, 12) for n in H_ELEMENTS)
    raise ValueError(f'Unsupported CUF study: {kind}')


def contained(path: Path, directory: Path, label: str) -> Path:
    p = Path(path).resolve()
    root = Path(directory).resolve()
    if not p.is_relative_to(root):
        raise ValueError(f'{label} leaves the I-Shape_cantilever project: {p} (root: {root})')
    return p


def json_save(path: Path, data: dict):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False,
                                    allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def fixed_signature(case):
    """All resolved physical and numerical controls except longitudinal h and p.

    Excludes case.name and output.directory, which are deliberately unique.
    Includes external basis options and adapter references to catch accidental
    changes beyond the designated longitudinal discretization.
    """
    return (
        str(case.problem_path.resolve()),
        str(case.problem_adapter_path),
        str(case.problem_load_adapter_path),
        str(case.problem_constraint_adapter_path),
        case.cuf.basis, case.cuf.order,
        json.dumps(case.cuf.basis_options, sort_keys=True, default=str),
        json.dumps(case.cuf.segments, sort_keys=True, default=str),
        case.longitudinal.method, case.longitudinal.basis,
        json.dumps(case.longitudinal.basis_options, sort_keys=True, default=str),
        case.longitudinal.gauss_order,
        case.longitudinal.material_polynomial_degree,
        case.section_integration.method, case.section_integration.gauss_order,
        case.solver.correctionMITC, case.solver.verifyMITCAssembly,
        case.solver.mitcDiagnostic,
        tuple(case.solver.equilibration.iteration_values),
        case.solver.equilibration.is_sweep,
        tuple(case.sampling.stations), case.sampling.displacement_samples,
        case.sampling.stress_grid, str(case.output_adapter_path),
    )


def expected_raw(base_dict: dict, kind: str, idx: int, elems: int, p_order: int):
    """Exact permitted transformation of the original YAML (no other changes)."""
    d = copy.deepcopy(base_dict)
    d['case']['name'] = f'csf_cuf_{kind}_v02_step_{idx:03d}'
    d['problem']['yaml'] = '../../problems/geometry_material_80pct_composite.yaml'
    d['longitudinal'].pop('element_boundaries', None)
    d['longitudinal']['elements'] = elems
    d['longitudinal']['order'] = p_order
    d['output']['directory'] = (
        f'../../output/cuf_convergence/{kind}_v02/step_{idx:03d}'
    )
    return d


def yaml_study_signature(raw: dict):
    """Compare only case configuration; avoid depending on an external base YAML."""
    if not isinstance(raw, dict):
        raise ValueError('Expected case YAML mapping')
    d = copy.deepcopy(raw)
    d.get('case', {}).pop('name', None)
    d.get('output', {}).pop('directory', None)
    d.get('longitudinal', {}).pop('elements', None)
    d.get('longitudinal', {}).pop('order', None)
    return d


def load_series(kind: str, project: Path, base_path: Path | None, cases_dir: Path):
    """Load independent study cases via the project case API, without a base YAML."""
    from csf.cuf.case import load_case
    project = project.resolve()
    if cases_dir.resolve() != project / 'cases' / f'convergence_{kind}_v02':
        raise ValueError('Study cases must be in project/cases/convergence_<kind>_v02')
    if not cases_dir.is_dir():
        raise FileNotFoundError(f'Missing study folder: {cases_dir}')
    specs = sequence(kind)
    files_expected = [f'step_{i:03d}.yaml' for i in range(1, len(specs)+1)]
    files_actual = sorted(f.name for f in cases_dir.glob('step_*.yaml'))
    if files_expected != files_actual:
        raise ValueError(f'Incorrect {kind}-series step files. Expected {files_expected}, got {files_actual}')
    items = []
    reference_signature = None
    reference_yaml_signature = None
    reference_problem = None
    for i, (elems, p_order) in enumerate(specs, 1):
        path = (cases_dir / f'step_{i:03d}.yaml').resolve()
        actual_raw = yaml.safe_load(path.read_text(encoding='utf-8'))
        current_yaml_signature = yaml_study_signature(actual_raw)
        if reference_yaml_signature is None:
            reference_yaml_signature = current_yaml_signature
        elif current_yaml_signature != reference_yaml_signature:
            raise ValueError(f'{path}: case settings differ beyond p/h and output labels')
        c = load_case(path)
        if not c.problem_path.is_file():
            raise FileNotFoundError(f'Missing CUF physical problem referenced by {path}: {c.problem_path}')
        current_signature = fixed_signature(c)
        if reference_signature is None:
            reference_signature = current_signature
            reference_problem = c.problem_path.resolve()
        elif current_signature != reference_signature:
            raise ValueError(f'{path}: physical or fixed numerical settings changed')
        if (c.cuf.basis, c.cuf.order) != ('lagrangeL9', 2):
            raise ValueError(f'{path}: expected fixed L9 transverse approximation')
        if (c.longitudinal.elements != elems or c.longitudinal.element_boundaries is not None
                or c.longitudinal.order != p_order or c.longitudinal.number_of_elements != elems):
            raise ValueError(f'{path}: incorrect CUF longitudinal discretization')
        if (not c.solver.equilibration.is_sweep or
                tuple(c.solver.equilibration.iteration_values) != (1,)):
            raise ValueError(f'{path}: expected a single eq1 sweep checkpoint')
        target = (project / 'output' / 'cuf_convergence' / f'{kind}_v02' /
                  f'step_{i:03d}').resolve()
        if c.output_dir.resolve() != target:
            raise ValueError(f'{path}: wrong output.directory {c.output_dir}; expected {target}')
        contained(c.output_dir, project / 'output', 'CUF checkpoint location')
        items.append({
            'step': i, 'elements': elems, 'order': p_order, 'case_name': c.name,
            'case_file': path, 'output_dir': target,
            'checkpoint': target/f'{c.name}_eq1.cuf.npz',
            'response': target/'response_eq1.txt',
        })
    if len({q['case_name'] for q in items}) != len(items):
        raise ValueError('Nonunique case names')
    if len({q['output_dir'] for q in items}) != len(items):
        raise ValueError('Nonunique output paths')
    # Optional base-case is only relevant to the later FEM3D comparison.
    # The CUF study itself never requires or loads it.
    if base_path is not None:
        base = load_case(base_path)
        if base.problem_path.resolve() != reference_problem:
            raise ValueError('FEM3D base case and CUF study refer to different physical problems')
    return items


def physical_input_hashes(base_path: Path | None, case_path: Path):
    """Fingerprint the actual step's references through official CSF APIs."""
    from csf.cuf.case import load_case
    from csf.cuf.problem.problem_api import load_problem
    c = load_case(case_path)
    p = load_problem(c.problem_path)
    filepaths = {'step_case': case_path, 'problem_yaml': Path(p.path),
                 'csf_model_yaml': Path(p.model_path)}
    for kind in ('load', 'constraint'):
        entry = p.problem_options.get(kind)
        if isinstance(entry, dict) and 'adapter' in entry:
            name = str(entry['adapter'])
            if name.endswith('.py') or '/' in name or '\\' in name:
                q = Path(name)
                filepaths[kind+'_adapter'] = q if q.is_absolute() else Path(p.path).parent / q
    return {key:{'path':str(Path(f).resolve()), 'sha256':sha(Path(f).resolve())}
            for key,f in filepaths.items()}

def valid_npz(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size <= 0 or not zipfile.is_zipfile(path):
        return False
    try:
        with zipfile.ZipFile(path) as zf:
            return bool(zf.namelist())
    except (OSError, zipfile.BadZipFile):
        return False


def checkpoint_valid(item: dict, inputs: dict):
    path = item['output_dir'] / 'step_manifest.json'
    ck, resp = item['checkpoint'], item['response']
    if not valid_npz(ck) or not resp.is_file() or not resp.stat().st_size or not path.is_file():
        return False
    try:
        doc = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    return (doc.get('version') == VERSION and doc.get('status') == 'completed'
            and doc.get('inputs') == inputs and doc.get('case_name') == item['case_name']
            and doc.get('elements') == item['elements'] and doc.get('order') == item['order']
            and doc.get('checkpoint_sha256') == sha(ck)
            and doc.get('response_sha256') == sha(resp))


def report_root(project: Path, path: Path) -> Path:
    if not path.is_absolute():
        path = project / path
    return contained(path, project / 'diagnostics', 'Study diagnostic report')


def run_series(kind: str, argv=None):
    ap = argparse.ArgumentParser(description=f'Execute CUF longitudinal {kind}-series, solver ONLY')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--skip-completed', action='store_true')
    ap.add_argument('--keep-going', action='store_true')
    ap.add_argument('--cases-dir', type=Path, default=Path(f'cases/convergence_{kind}_v02'))
    ap.add_argument('--reports-root', type=Path,
                    default=Path(f'diagnostics/cuf_{kind}_execution_v02'))
    a = ap.parse_args(argv)
    project = a.cases_dir.resolve().parent.parent
    try:
        items = load_series(kind, project, None, a.cases_dir.resolve())
        identities = [physical_input_hashes(None, it['case_file']) for it in items]
        root = report_root(project, a.reports_root)
    except (ImportError, OSError, TypeError, ValueError, KeyError) as exc:
        ap.error(str(exc))
    print(f'[CUF {kind} v02] project: {project}',flush=True)
    for it in items:
        print(f"  step {it['step']:03d} N={it['elements']:2d} p={it['order']:2d} => {it['output_dir']}",flush=True)
    if a.dry_run:
        print('[DRY RUN] all resolved files and output paths validated; nothing executed',flush=True)
        return 0
    folder = new_run(root)
    records = [{"step":it['step'],"elements":it['elements'],"order":it['order'],
                "case":str(it['case_file']),"output":str(it['output_dir']),
                "checkpoint":str(it['checkpoint']),"status":"pending",
                "solver_log":None,"reason":None}
               for it in items]
    def save_execution():
        json_save(folder/'execution_result.json',{
            'version':VERSION, 'type':kind, 'status':
            ('completed' if all(r['status'] in ('completed','skipped') for r in records)
             else 'in_progress'), 'records':records,
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'comparison_performed':False, 'fem3d_executed':False})
    save_execution()
    for it, inputs, record in zip(items, identities, records):
        output=it['output_dir']
        if a.skip_completed and checkpoint_valid(it, inputs):
            record['status']='skipped'
            print(f"[CUF {kind} v02] step {it['step']:03d}: SKIP, manifest and hashes verified",flush=True)
            save_execution()
            continue
        if output.exists() and any(output.iterdir()):
            record['status']='blocked'
            record['reason']='Nonempty output, unverified or not allowed to overwrite'
            print(f"[CUF {kind} v02] BLOCKED {output}: not overwriting",file=sys.stderr,flush=True)
            save_execution()
            if not a.keep_going:break
            continue
        # Do not create a series checkpoint before input validation succeeds.
        output.mkdir(parents=True, exist_ok=True)
        log=folder/f"step_{it['step']:03d}.log"
        record['solver_log']=str(log)
        cmd=[sys.executable,'-m','csf.cuf',str(it['case_file'])]
        print(f"[CUF {kind} v02] solve step {it['step']:03d}: N={it['elements']}, p={it['order']}",flush=True)
        try:
            with log.open('w',encoding='utf-8') as stream:
                stream.write('COMMAND: '+' '.join(cmd)+'\nCWD: '+str(project)+'\n\n')
                stream.flush()
                result=subprocess.run(cmd,cwd=project,stdout=stream,
                                      stderr=subprocess.STDOUT,check=False)
            if (result.returncode or not valid_npz(it['checkpoint'])
                    or not it['response'].is_file()
                    or not it['response'].stat().st_size):
                raise RuntimeError(f'Solver exit={result.returncode}, checkpoint/response missing or malformed')
            # Reject changing inputs while the numerical run is executing.
            if physical_input_hashes(None,it['case_file']) != inputs:
                raise RuntimeError('Physical or case inputs changed during solver execution')
            json_save(output/'step_manifest.json',{
                'version':VERSION, 'status':'completed', 'inputs':inputs,
                'case_name':it['case_name'], 'elements':it['elements'],
                'order':it['order'], 'checkpoint_sha256':sha(it['checkpoint']),
                'response_sha256':sha(it['response'])})
            record['status']='completed'
            print(f"[CUF {kind} v02] done step {it['step']:03d}",flush=True)
        except (OSError, RuntimeError, ImportError) as exc:
            record['status']='failed';record['reason']=str(exc)
            print(f"[CUF {kind} v02] FAILED step {it['step']:03d}: {exc}",file=sys.stderr,flush=True)
        save_execution()
        if record['status']=='failed' and not a.keep_going:break
    count=sum(r['status'] in ('completed','skipped') for r in records)
    print(f'[CUF {kind} v02] {count}/{len(items)} valid checkpoints; report: {folder}',flush=True)
    return 0 if count==len(items) else 1


def output_csv_and_md(kind: str, folder: Path, info: dict, rows: list[dict],
                      status: str, error: str | None = None):
    cols=('elements','order','case_name','cuf_checkpoint','relative_l2_percent',
          'weighted_rms','ux_relative_l2_percent','uy_relative_l2_percent',
          'uz_relative_l2_percent','node_relative_l2_percent','samples','volume',
          'comparison_summary','sha256_cuf')
    with (folder/f'comparison_{kind}_series.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)
    json_save(folder/f'comparison_{kind}_result.json',{
        'version':VERSION, 'study':kind, 'status':status,
        'metric':'volume_weighted_vector_relative_L2_percent',
        'fem_checkpoint':info['fem_checkpoint'],
        'fem_checkpoint_sha256':info['fem_checkpoint_sha256'],
        'sampling':info['sampling'], 'bins':info['bins'], 'results':rows,
        'failure':error})
    label='order p' if kind=='p' else 'elements N'
    axis='order' if kind=='p' else 'elements'
    lines=[f'# CUF {kind}-series comparison with the fixed, GCI-selected FEM3D', '',
           f'**Status:** {status} ({len(rows)}/{len(sequence(kind))} comparisons).',
           f'**FEM3D mesh:** {info["fem"]["selected_mesh"]}.',
           f'**FEM3D solution:** `{info["fem_checkpoint"]}`.',
           f'**Sampling:** {info["sampling"]}; **local x bins:** {info["bins"]}.',
           '**Metric:** unmodified volume-weighted vector relative L2 (%) ', '',
           f'| {label} | Relative L2 difference (%) |','|---:|---:|']
    lines += [f'| {r[axis]} | {r["relative_l2_percent"]:.9g} |' for r in rows]
    if status=='completed':
        lines += ['',f'![Same relative L2 comparison](cuf_vs_fem3d_relative_l2_by_{"order" if kind=="p" else "elements"}.png)']
        if (folder / 'cuf_fem3d_agreement_overview.png').is_file():
            lines += ['', '**Displacement agreement overview**', '',
                      '![CUF vs FEM3D displacement agreement](cuf_fem3d_agreement_overview.png)', '',
                      'The longitudinal displacement curves are volume-weighted bin means '
                      'at identical FEM H8 quadrature locations. The parity plot '
                      'shows paired samples and the exact-agreement diagonal.']
    # Every completed step has its own field-agreement figure. Include links
    # to existing figures without altering the numerical tables or JSON.
    step_figures = [
        (i, r) for i, r in enumerate(rows, start=1)
        if (folder / f'step_{i:03d}' / 'cuf_fem3d_agreement.png').is_file()
    ]
    if step_figures:
        lines += ['', '## Individual step displacement agreement', '',
                  'Each figure overlays CUF/FEM3D ux, uy, uz volume-weighted '
                  'longitudinal bin means and shows pointwise parity and local RMS.','',
                  '| Step | N | p | CUF-FEM3D figure |',
                  '|---:|---:|---:|---|']
        for i, r in step_figures:
            basename = f'step_{i:03d}/cuf_fem3d_agreement'
            lines.append(f'| {i:03d} | {r["elements"]} | {r["order"]} | '
                         f'[PNG]({basename}.png) |')
        # Embed each image directly in the series Markdown as well as linking it.
        lines += ['', '<!-- CUF-FEM3D-INLINE-STEPS:BEGIN -->', '',
                  '## Step-by-step displacement agreement figures', '',
                  'These figures display the paired CUF and FEM3D displacement fields. '
                  'Longitudinal curves are volume-weighted bin means, not a single material-line profile.', '']
        for i, r in step_figures:
            basename = f'step_{i:03d}/cuf_fem3d_agreement.png'
            lines += [f'### Step {i:03d} — N={r["elements"]}, p={r["order"]}', '',
                      f'![CUF vs FEM3D: step {i:03d}, N={r["elements"]}, p={r["order"]}]({basename})', '']
        lines.append('<!-- CUF-FEM3D-INLINE-STEPS:END -->')
    if error: lines+=['',f'**Failure:** {error}']
    lines+=['','The FEM3D checkpoint and the comparison method are unchanged. '
            'This plot measures CUF–FEM3D agreement; no independent CUF field convergence theorem is asserted.']
    (folder/f'comparison_{kind}_series.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def plot_series(kind: str, folder: Path, rows: list[dict]):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    key='order' if kind=='p' else 'elements'
    xx=[r[key] for r in rows]
    fig,ax=plt.subplots(figsize=(8.5,4.8))
    ax.plot(xx,[r['relative_l2_percent'] for r in rows],marker='o')
    ax.set_xticks(xx)
    ax.set(xlabel=('CUF longitudinal polynomial order p (N=10)' if kind=='p'
                   else 'CUF longitudinal elements N (p=12)'),
           ylabel='Volume-weighted relative L2 difference (%)',
           title='CUF displacements vs the fixed GCI-selected FEM3D field')
    ax.grid(alpha=.25);fig.tight_layout()
    fig.savefig(folder/f'cuf_vs_fem3d_relative_l2_by_{"order" if kind=="p" else "elements"}.png',dpi=200)
    plt.close(fig)


def verify_gci_physical_provenance(selected: dict, case_path: Path) -> dict:
    """Verify all study physical inputs against the selected GCI manifest.

    The case YAML itself intentionally differs in numerical h/p settings, so
    its SHA cannot match the original GCI case. Instead compare the *resolved*
    physical problem, CSF model and load/constraint source fingerprints using
    the official case/problem APIs. Reject missing and mismatched evidence.
    """
    resolved = physical_input_hashes(None, case_path)
    recorded = selected['manifest'].get('inputs', {}).get('files', {})
    if not isinstance(recorded, dict):
        raise ValueError('GCI manifest lacks recorded physical input hashes')
    mapping = {
        'problem_yaml': 'problem',
        'csf_model_yaml': 'csf_model',
        'load_adapter': 'load_adapter',
        'constraint_adapter': 'constraint_adapter',
    }
    for actual_key, gci_key in mapping.items():
        present_actual = actual_key in resolved
        present_gci = gci_key in recorded
        if present_actual != present_gci:
            raise ValueError(f'Physical input presence differs from GCI: {gci_key}')
        if not present_actual:
            if gci_key in ('problem', 'csf_model'):
                raise ValueError(f'GCI physical input missing: {gci_key}')
            continue
        recorded_item = recorded[gci_key]
        expected_hash = recorded_item.get('sha256') if isinstance(recorded_item, dict) else None
        if not isinstance(expected_hash, str) or resolved[actual_key]['sha256'] != expected_hash:
            raise ValueError(f'Physical input differs from GCI: {gci_key}')
    return resolved


def compare_series(kind: str, argv=None):
    """Compare saved CUF fields to an independently validated GCI FEM field.

    The series YAML files supply the CSF model: there is no extra base-case.
    The original numerical comparator is unchanged apart from an explicit,
    backward-compatible *name-label* override for its strict FEM case check.
    """
    ap = argparse.ArgumentParser(description=f'Compare solved CUF {kind} vs fixed FEM3D; no solver calls')
    ap.add_argument('--gci-result', required=True, type=Path,
                    help='Existing FEM3D GCI convergence_result.json')
    ap.add_argument('--cases-dir', type=Path,
                    default=Path(f'cases/convergence_{kind}_v02'),
                    help='Prepared CUF series cases (default: standard v02 directory)')
    ap.add_argument('--comparator', type=Path,
                    default=Path('tools/compare_cuf_fem_displacements.py'),
                    help='Existing displacement comparator (default: project tools/)')
    ap.add_argument('--sampling', choices=('both', 'centers', 'gauss2'), default='both')
    ap.add_argument('--bins', type=int, default=40)
    ap.add_argument('--output-root', type=Path,
                    default=Path(f'diagnostics/cuf_{kind}_fem3d_comparison_v02'))
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--detail-plots', action='store_true')
    args = ap.parse_args(argv)
    # Resolve all relative paths from this installed project, not the shell cwd.
    project = Path(__file__).resolve().parent.parent
    cases_dir = (args.cases_dir if args.cases_dir.is_absolute()
                 else project / args.cases_dir).resolve()
    comparator = (args.comparator if args.comparator.is_absolute()
                  else project / args.comparator).resolve()
    gci_file = (args.gci_result if args.gci_result.is_absolute()
                else project / args.gci_result).resolve()
    if args.bins < 1:
        ap.error('--bins must be >=1')
    try:
        if not comparator.is_file():
            raise FileNotFoundError(f'Comparator missing: {comparator}')
        # Reject an older comparator before starting the lengthy 8/11-step series.
        if '--fem-reference-case-name' not in comparator.read_text(encoding='utf-8'):
            raise ValueError('Comparator needs the accompanying backward-compatible name-label patch')
        items = load_series(kind, project, None, cases_dir)
        selected = selected_fem(gci_file)
        # Check physical provenance of every step, not just the first one.
        inputs = [physical_input_hashes(None, item['case_file']) for item in items]
        for item in items:
            verify_gci_physical_provenance(selected, item['case_file'])
        root = report_root(project, args.output_root)
        valid = [checkpoint_valid(item, h) for item, h in zip(items, inputs)]
    except (ImportError, OSError, TypeError, ValueError, KeyError) as exc:
        ap.error(str(exc))
    print(f'[COMPARE {kind} v02] FEM3D GCI selected: {selected["path"]}', flush=True)
    for item, ok in zip(items, valid):
        print(f'  step {item["step"]:03d} N={item["elements"]:2d} p={item["order"]:2d} '
              f'{"READY" if ok else "MISSING / NOT VERIFIED"} {item["checkpoint"]}', flush=True)
    if args.dry_run:
        print('[DRY RUN] no comparisons or solvers executed', flush=True)
        return 0 if all(valid) else 2
    if not all(valid):
        ap.error('CUF checkpoints missing/unverified; comparison cannot start')
    folder = new_run(root)
    metadata = {
        'version': VERSION, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'physical_identity_method': 'GCI physical input hashes against official CSF case/problem references',
        'fem': selected['data'], 'fem_checkpoint': str(selected['path']),
        'fem_checkpoint_sha256': selected['sha256'],
        'fem_recorded_case_name': selected['case_name'],
        'gci_result_path': str(selected['report_file']),
        'gci_result_sha256': sha(selected['report_file']),
        'gci_manifest_sha256': sha(selected['manifest_file']),
        'comparator': str(comparator), 'comparator_sha256': sha(comparator),
        'sampling': args.sampling, 'bins': args.bins,
        'entries': [
            {'step': item['step'], 'elements': item['elements'], 'order': item['order'],
             'case_path': str(item['case_file']), 'case_sha256': sha(item['case_file']),
             'physical_input_hashes': inputs[i],
             'checkpoint_sha256': sha(item['checkpoint'])}
            for i, item in enumerate(items)
        ],
    }
    json_save(folder / 'manifest.json', metadata)
    rows = []
    ref_size = None
    output_csv_and_md(kind, folder, metadata, rows, 'in_progress')
    try:
        for i, item in enumerate(items):
            current = metadata['entries'][i]
            if (sha(item['checkpoint']) != current['checkpoint_sha256']
                    or sha(item['case_file']) != current['case_sha256']
                    or physical_input_hashes(None, item['case_file']) != current['physical_input_hashes']
                    or sha(selected['path']) != selected['sha256']
                    or sha(comparator) != metadata['comparator_sha256']):
                raise RuntimeError('Study input or checkpoint changed during comparison')
            step = folder / f'step_{item["step"]:03d}'
            step.mkdir()
            command = [
                sys.executable, str(comparator),
                '--case', str(item['case_file']),
                '--cuf', str(item['checkpoint']),
                '--fem3d', str(selected['path']),
                '--fem-reference-case-name', selected['case_name'],
                '--sampling', args.sampling, '--bins', str(args.bins),
                '--no-profiles', '--output-dir', str(step),
            ]
            if not args.detail_plots:
                command.append('--no-plots')
            json_save(step / 'command.json', {'argv': command, 'cwd': str(project)})
            print(f'[COMPARE {kind} v02] step {item["step"]:03d}: '
                  f'N={item["elements"]}, p={item["order"]}', flush=True)
            with (step / 'comparator.log').open('w', encoding='utf-8') as log:
                proc = subprocess.run(command, cwd=project, stdout=log,
                                      stderr=subprocess.STDOUT, check=False)
            if proc.returncode:
                raise RuntimeError(f'Comparator failed; see {step / "comparator.log"}')
            summary = step / 'summary.json'
            if not summary.is_file():
                raise RuntimeError(f'Comparator summary missing: {summary}')
            measurements = metrics_from_summary(
                summary, selected['path'], selected['sha256'],
                item['checkpoint'], item['case_file'], args.sampling)
            identity = (measurements['samples'], measurements['volume'])
            if ref_size is None:
                ref_size = identity
            elif identity[0] != ref_size[0] or not math.isclose(
                    identity[1], ref_size[1], rel_tol=1e-12, abs_tol=1e-10):
                raise RuntimeError('FEM quadrature sample count/volume changed across CUF steps')
            row = {
                'elements': item['elements'], 'order': item['order'],
                'case_name': item['case_name'],
                'cuf_checkpoint': str(item['checkpoint']),
                'comparison_summary': str(summary),
                'sha256_cuf': sha(item['checkpoint']),
            }
            row.update(measurements)
            rows.append(row)
            output_csv_and_md(kind, folder, metadata, rows, 'in_progress')
            # Plot the step immediately: partial/completed runs have their own
            # field agreement figures without rerunning a solver/comparator.
            from plot_cuf_fem_agreement_v02 import create_step_agreement
            step_figure = create_step_agreement(folder, kind, len(rows))
            print(f'[COMPARE {kind} v02] step figure: {step_figure}', flush=True)
            output_csv_and_md(kind, folder, metadata, rows, 'in_progress')
        plot_series(kind, folder, rows)
        # Visualize actual FEM/CUF displacement agreement using the paired
        # sample NPZ saved by the unchanged comparator; no new field evaluation.
        from plot_cuf_fem_agreement_v02 import create_agreement_overview
        fig_path = create_agreement_overview(folder, kind)
        print(f'[COMPARE {kind} v02] agreement figure: {fig_path}', flush=True)
        output_csv_and_md(kind, folder, metadata, rows, 'completed')
        print(f'[COMPARE {kind} v02] COMPLETED: {folder}', flush=True)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        output_csv_and_md(kind, folder, metadata, rows, 'incomplete', str(exc))
        print(f'[COMPARE {kind} v02] INCOMPLETE: {exc}', file=sys.stderr, flush=True)
        return 1
