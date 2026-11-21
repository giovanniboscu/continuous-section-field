
# Version: FEM3D longitudinal h-convergence, optional ASME V&V 10.1 7.2 GCI, v03.1
"""FEM3D longitudinal convergence of the existing CSF-driven OpenSees H8 model.

Methods (selected with --method):
  gci      Three-grid Richardson / Grid Convergence Index. Estimates observed
           longitudinal convergence order p from three solutions; computes
           the fine-grid GCI with F_s=1.25. See ASME V&V 10.1-2012(R2022), 7.2.
  relative Original v02 consecutive-mesh percent change in u_z(P).

Both evaluate the same u_z at one fixed physical point P for every mesh, and
vary only nx while fixing transverse nu and nv. The GCI is an estimated
numerical uncertainty for the FIXED transverse discretization, valid only
under the asymptotic-power-law assumption. Thresholds are user-selected.

No material or physical-geometry interpolation is implemented. The existing
OpenSees/CSF driver handles the physical model via CSF APIs. In this script,
standard H8 shape functions reconstruct only the solved FEM displacement.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback

import numpy as np

VERSION = "CSF-CUF FEM3D longitudinal GCI v03.1 - 2026-11-20"
LEGACY_VERSION = "CSF-CUF FEM3D longitudinal GCI v03 - 2026-11-20"
H8_SIGNS = np.asarray([
    (-1, -1, -1), (+1, -1, -1), (+1, +1, -1), (-1, +1, -1),
    (-1, -1, +1), (+1, -1, +1), (+1, +1, +1), (-1, +1, +1),
], dtype=float)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                    allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def finite_float(value, name: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise ValueError(f"{name} must be finite")
    return x


def parse_nx(values) -> list[int]:
    result = [int(v) for v in values]
    if len(result) < 2 or any(n < 1 for n in result):
        raise ValueError("--nx requires at least two positive values")
    if any(a >= b for a, b in zip(result, result[1:])):
        raise ValueError("--nx must be strictly increasing, without duplicates")
    return result


def model_provenance(case_path: Path, driver_path: Path) -> dict:
    """Use existing case/problem APIs for references; never parse physical YAML."""
    from csf.cuf.case import load_case
    from csf.cuf.problem.problem_api import load_problem

    case = load_case(case_path)
    problem = load_problem(case.problem_path)
    if problem.problem_type != "composite":
        raise ValueError("The existing OpenSees driver requires a composite local problem")
    paths = {
        "case": Path(case.path).resolve(),
        "problem": Path(problem.path).resolve(),
        "csf_model": Path(problem.model_path).resolve(),
        "fem_driver": driver_path.resolve(),
    }
    for role in ("load", "constraint"):
        options = problem.problem_options.get(role)
        if isinstance(options, dict) and "adapter" in options:
            reference = str(options["adapter"])
            if reference.endswith(".py") or "/" in reference or "\\" in reference:
                path = Path(reference)
                if not path.is_absolute():
                    path = Path(problem.path).parent / path
                paths[f"{role}_adapter"] = path.resolve()
    for role, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing {role}: {path}")
    return {
        "case_name": str(case.name),
        "files": {role: {"path": str(path), "sha256": sha256(path)}
                  for role, path in paths.items()},
    }


def h8_shape(q: np.ndarray) -> np.ndarray:
    """OpenSees stdBrick H8 shape functions in local node ordering."""
    return np.prod(1.0 + H8_SIGNS * np.asarray(q, dtype=float), axis=1) / 8.0


def h8_derivatives(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    d = np.empty((8, 3), dtype=float)
    for axis in range(3):
        a, b = [j for j in range(3) if j != axis]
        d[:, axis] = (H8_SIGNS[:, axis] / 8.0
                      * (1 + H8_SIGNS[:, a] * q[a])
                      * (1 + H8_SIGNS[:, b] * q[b]))
    return d


def invert_h8(xyz: np.ndarray, point: np.ndarray,
              physical_tol: float, natural_tol: float = 1e-8):
    """Find natural coordinates of a physical P in an H8; return None if outside.

    The FEM isoparametric map x(q)=sum N_a(q) x_a is part of FEM field
    evaluation. This is not an interpolation of CSF geometry or material laws.
    """
    q = np.zeros(3, dtype=float)
    for _ in range(35):
        N = h8_shape(q)
        residual = point - N @ xyz
        if float(np.max(np.abs(residual))) <= physical_tol:
            if np.any(np.abs(q) > 1.0 + natural_tol):
                return None
            if np.any(np.abs(q) > 1.0):
                q = np.clip(q, -1.0, 1.0)
                if float(np.max(np.abs(point - h8_shape(q) @ xyz))) > physical_tol:
                    return None
            return q
        jac = xyz.T @ h8_derivatives(q)
        try:
            dq = np.linalg.solve(jac, residual)
        except np.linalg.LinAlgError:
            return None
        if not np.isfinite(dq).all():
            return None
        q += dq
        if np.any(np.abs(q) > 4.0):
            return None
    return None


def fem_displacement_at_point(nodes: np.ndarray, elements: np.ndarray,
                              disp: np.ndarray, point: np.ndarray) -> dict:
    """Return displacement at the exact physical point, or fail if not found.

    Prefer an existing FEM node. Otherwise invert the standard H8 map and
    interpolate FEM displacements on the solved mesh. Shared-interface values
    must be continuous to within a numeric tolerance.
    """
    scale = max(1.0, float(np.max(np.ptp(nodes, axis=0))),
                float(np.max(np.abs(point))))
    physical_tol = 1e-10 * scale
    coincident = np.flatnonzero(np.max(np.abs(nodes - point), axis=1) <= physical_tol)
    if coincident.size:
        vectors = disp[coincident]
        if np.max(np.abs(vectors - vectors[0])) > 1e-8 * max(1.0, np.max(np.abs(vectors))):
            raise ValueError("Coincident FEM nodes have inconsistent displacements at P")
        return {
            "u": vectors[0].tolist(), "sampling": "fem_node",
            "node_id_0based": int(coincident[0]),
            "element_id_0based": None, "natural_coordinates": None,
            "candidate_count": int(len(coincident)),
        }

    # Bounding-box filter is purely a search on the saved FE mesh nodes.
    xyz = nodes[elements]
    lower = np.min(xyz, axis=1)
    upper = np.max(xyz, axis=1)
    eligible = np.flatnonzero(
        np.all(point >= lower - physical_tol, axis=1)
        & np.all(point <= upper + physical_tol, axis=1)
    )
    matches = []
    for eid in eligible:
        q = invert_h8(xyz[eid], point, physical_tol)
        if q is not None:
            u = h8_shape(q) @ disp[elements[eid]]
            matches.append((int(eid), q, u))
    if not matches:
        raise ValueError(
            f"P={point.tolist()} is not located in the solved H8 mesh. "
            "Choose one physical point belonging to every mesh of the study."
        )
    reference = matches[0][2]
    tolerance = 1e-8 * max(1.0, float(np.max(np.abs(reference))))
    if any(float(np.max(np.abs(entry[2] - reference))) > tolerance
           for entry in matches[1:]):
        raise ValueError("Noncontinuous FEM displacement at P on an element interface")
    eid, q, u = matches[0]
    return {
        "u": u.tolist(), "sampling": "h8_isoparametric",
        "node_id_0based": None, "element_id_0based": eid,
        "natural_coordinates": q.tolist(), "candidate_count": len(matches),
    }


def analyze_solution(npz_path: Path, mesh: tuple[int, int, int],
                     point: np.ndarray, expected_case: str) -> dict:
    with np.load(npz_path, allow_pickle=False) as data:
        required = {"status", "mesh_divisions", "nodes", "elements", "displacement", "x0", "x1"}
        missing = sorted(required - set(data.files))
        if missing:
            raise ValueError(f"Not a solved OpenSees H8 NPZ; missing fields: {missing}")
        status = str(np.asarray(data["status"]).item())
        if status != "solved_opensees":
            raise ValueError(f"FEM NPZ must have status='solved_opensees', got {status!r}")
        saved_mesh = tuple(int(v) for v in data["mesh_divisions"])
        if saved_mesh != mesh:
            raise ValueError(f"NPZ mesh {saved_mesh} is not the requested mesh {mesh}")
        if "case_name" in data.files:
            actual_case = str(np.asarray(data["case_name"]).item())
            if actual_case != expected_case:
                raise ValueError(f"Saved NPZ case {actual_case!r} differs from {expected_case!r}")
        nodes = np.asarray(data["nodes"], dtype=float)
        elements = np.asarray(data["elements"])
        u = np.asarray(data["displacement"], dtype=float)
        x0 = finite_float(np.asarray(data["x0"]).item(), "NPZ x0")
        x1 = finite_float(np.asarray(data["x1"]).item(), "NPZ x1")
        nregions = (len(np.asarray(data["element_region_names"]))
                    if "element_region_names" in data.files else None)
        end0 = (np.asarray(data["end0_nodes"], dtype=np.int64)
                if "end0_nodes" in data.files else None)
    if nodes.ndim != 2 or nodes.shape[1] != 3 or not len(nodes):
        raise ValueError("Invalid FEM nodes array")
    if (elements.ndim != 2 or elements.shape[1] != 8
            or not len(elements) or not np.issubdtype(elements.dtype, np.integer)
            or np.min(elements) < 0 or np.max(elements) >= len(nodes)):
        raise ValueError("Invalid H8 element connectivity")
    if u.shape != nodes.shape or not np.isfinite(nodes).all() or not np.isfinite(u).all():
        raise ValueError("Invalid FEM displacement/coordinate arrays")
    if np.any(np.diff(np.sort(elements, axis=1), axis=1) == 0):
        raise ValueError("Repeated local node in H8 element")
    if not x1 > x0:
        raise ValueError("Invalid longitudinal domain")
    if point[0] < x0 - 1e-8 or point[0] > x1 + 1e-8:
        raise ValueError(f"P longitudinal coordinate lies outside [{x0}, {x1}]")
    if end0 is not None and end0.size:
        if (np.min(end0) < 0 or np.max(end0) >= len(nodes)):
            raise ValueError("Invalid end0 node IDs")
        if not np.allclose(u[end0], 0.0, atol=1e-7, rtol=0):
            raise ValueError("Nonzero displacement on supposedly fixed end0 FEM nodes")
    sample = fem_displacement_at_point(nodes, elements, u, point)
    return {
        "mesh": list(mesh), "nx": mesh[0], "nu": mesh[1], "nv": mesh[2],
        "h8_elements": int(len(elements)), "nodes": int(len(nodes)),
        "csf_domain_count_in_npz": nregions,
        "x0": x0, "x1": x1,
        "point": point.tolist(),
        "point_ux": float(sample["u"][0]),
        "point_uy": float(sample["u"][1]),
        "point_uz": float(sample["u"][2]),
        "point_evaluation": {key: value for key, value in sample.items() if key != "u"},
        "npz": str(npz_path.resolve()), "npz_sha256": sha256(npz_path),
    }


def delta_pct(current: float, previous: float) -> float:
    """Relative change divided by |current|. No artificial scale near zero."""
    if current == 0.0:
        raise ValueError("u_z(P) is zero in current mesh; relative criterion undefined")
    return 100.0 * abs(current - previous) / abs(current)


def _log_expm1(value: float) -> float:
    """Numerically stable logarithm of exp(value)-1, for value>0."""
    if value > 50.0:
        return value + math.log1p(-math.exp(-value))
    return math.log(math.expm1(value))


def gci_three_grid(h1: float, w1: float, h2: float, w2: float,
                   h3: float, w3: float, safety_factor: float = 1.25,
                   min_ratio: float = 1.3) -> dict:
    """ASME V&V 10.1 section 7.2, 3-grid Richardson GCI for one scalar QoI.

    h1 < h2 < h3 (fine, medium, coarse); h=L/nx; w_i=u_z(P).
    Fits w(h)=w_inf+A*h**p, with p>0 and a monotonic three-grid sequence.
    Unequal mesh ratios are supported by scalar bisection, not by assuming
    r21 == r32. No theoretical p is invented and no p is forced for failures.

    A valid three-point fit is NOT an independent proof of asymptotic behavior.
    Ratios <= min_ratio are reported but disallowed for automatic selection.
    """
    if h1 <= 0.0 or h2 <= 0.0 or h3 <= 0.0:
        raise ValueError("Mesh sizes must be strictly positive")
    r21 = h2/h1
    r32 = h3/h2
    result = {
        'r21': r21, 'r32': r32, 'p_observed': None,
        'richardson_extrapolated': None, 'gci_pct': None,
        'gci_band_lower': None, 'gci_band_upper': None,
        'valid_estimate': False, 'recommended_ratios_met': bool(r21>min_ratio and r32>min_ratio),
        'reason': None,
    }
    if not (0 < h1 < h2 < h3) or not all(math.isfinite(v) for v in (h1,h2,h3,w1,w2,w3)):
        result['reason'] = 'invalid mesh lengths or non-finite solution'
        return result
    d21 = w2 - w1
    d32 = w3 - w2
    if w1 == 0:
        result['reason'] = 'fine-mesh uz(P)=0: relative GCI undefined'
        return result
    if d21 == 0.0 or d32 == 0.0:
        result['reason'] = 'zero consecutive difference: observed order indeterminate'
        return result
    if d21*d32 <= 0.0:
        result['reason'] = 'oscillatory or non-monotonic sequence: positive-order Richardson fit unavailable'
        return result
    a=math.log(r21)
    b=math.log(r32)
    target=math.log(abs(d32/d21))
    # As p -> 0+, (h3^p-h2^p)/(h2^p-h1^p) -> log(r32)/log(r21).
    floor=math.log(b/a)
    if target <= floor + 1e-12:
        result['reason'] = 'no positive observed convergence order from these three solutions'
        return result
    def log_ratio(p: float) -> float:
        return p*a + _log_expm1(p*b) - _log_expm1(p*a)
    low, high=1e-12, 32.0
    if log_ratio(high) < target:
        result['reason'] = 'observed order exceeds supported numerical range (p>32)'
        return result
    for _ in range(180):
        mid=(low+high)*0.5
        if log_ratio(mid) < target:
            low=mid
        else:
            high=mid
    p=0.5*(low+high)
    denominator=math.expm1(p*a)
    if not math.isfinite(denominator) or denominator <= 0.0:
        result['reason']='invalid Richardson extrapolation denominator'
        return result
    correction=(w1-w2)/denominator
    w_ex=w1+correction
    gci_pct=100.0*safety_factor*abs(correction)/abs(w1)
    halfwidth=abs(w1)*gci_pct/100.0
    if not all(math.isfinite(v) for v in (p,w_ex,gci_pct,halfwidth)):
        result['reason']='non-finite Richardson/GCI output'
        return result
    result.update({
        'p_observed':p, 'richardson_extrapolated':w_ex,
        'gci_pct':gci_pct, 'gci_band_lower':w1-halfwidth,
        'gci_band_upper':w1+halfwidth,
        'valid_estimate':True,
        'reason': (None if result['recommended_ratios_met']
                   else f'refinement ratios do not exceed the STUDY-SPECIFIED minimum {min_ratio:g}; ASME recommends > 1.3'),
    })
    return result



def plan_gci_triplets(nx_values: list[int], min_ratio: float,
                      explicit: list[list[int]] | None = None) -> dict[str, list[int]]:
    """Plan every GCI triplet BEFORE the displacement results are available.

    The three-grid equations are ASME V&V 10.1 section 7.2. Triplet planning
    is a documented SOFTWARE choice, not part of the standard's equations.
    It is based exclusively on the user-supplied mesh schedule and the
    recommended refinement ratio, never on the computed displacements.

    Default: for each fine nx, choose the nearest intermediate nx and then
    the nearest coarse nx whose ratios both exceed min_ratio. If none exist,
    use the last three previous resolution levels and mark ratio warnings.
    Explicit: --gci-triple COARSE MEDIUM FINE, repeatable; only those fine
    meshes are assessed. Never retroactively pick a favorable triplet.
    """
    available = set(nx_values)
    triplets: dict[str, list[int]] = {}
    if explicit:
        for triple in explicit:
            if len(triple) != 3:
                raise ValueError("Every --gci-triple needs COARSE MEDIUM FINE")
            c, m, f = (int(x) for x in triple)
            if not (c < m < f) or not all(x in available for x in (c, m, f)):
                raise ValueError(f"GCI triplet {triple} must be increasing and appear in --nx")
            if str(f) in triplets:
                raise ValueError(f"Multiple predefined GCI triplets for fine nx={f}")
            triplets[str(f)] = [c, m, f]
        return triplets
    for fi in range(2, len(nx_values)):
        f = nx_values[fi]
        eligible = []
        for mi in range(1, fi):
            m = nx_values[mi]
            if f/m <= min_ratio:
                continue
            for ci in range(mi):
                c = nx_values[ci]
                if m/c > min_ratio:
                    eligible.append((m, c))
        if eligible:
            m, c = max(eligible)  # closest admissible medium, then coarse
            triplets[str(f)] = [c, m, f]
        else:
            triplets[str(f)] = nx_values[fi-2:fi+1]
    return triplets


def collect_rows(run_dir: Path, nx_values: list[int], nu: int, nv: int,
                 tol_pct: float, point: list[float], method: str = 'relative',
                 safety_factor: float = 1.25, min_ratio: float = 1.3,
                 gci_triplets: dict[str, list[int]] | None = None):
    rows=[]
    selected=None
    reference_domain=None
    if method not in ('relative','gci'):
        raise ValueError(f'Unknown convergence method: {method}')
    if method == 'gci' and gci_triplets is None:
        gci_triplets = plan_gci_triplets(nx_values, min_ratio)
    for step_number,nx in enumerate(nx_values,1):
        metrics_file=run_dir / f'step_{step_number:03d}' / 'metrics.json'
        if not metrics_file.is_file():
            break
        data=json.loads(metrics_file.read_text(encoding='utf-8'))
        if data['mesh'] != [nx,nu,nv] or data['point'] != point:
            raise ValueError(f'Step {step_number} does not match immutable manifest')
        domain=(float(data['x0']),float(data['x1']))
        if reference_domain is None:
            reference_domain=domain
        elif not np.allclose(domain, reference_domain, rtol=0.0, atol=1e-8):
            raise ValueError('Longitudinal physical domain changed during convergence')
        h=(domain[1]-domain[0])/nx
        previous=rows[-1] if rows else None
        if previous:
            try:
                delta=delta_pct(float(data['point_uz']),float(previous['uz_P']))
            except ValueError:
                if method == 'relative':
                    raise
                delta=None  # GCI itself reports a zero-fine-value failure
        else:
            delta=None
        gci=None
        gci_triplet=None
        if method == 'gci' and gci_triplets:
            gci_triplet=gci_triplets.get(str(nx))
            if gci_triplet is not None:
                if gci_triplet[2] != nx:
                    raise ValueError(f'GCI triplet ending at wrong fine nx: {gci_triplet}')
                available={int(r['nx']):r for r in rows}
                if gci_triplet[0] not in available or gci_triplet[1] not in available:
                    raise ValueError(f'GCI triplet {gci_triplet} needs missing coarse meshes')
                coarse=available[gci_triplet[0]]
                medium=available[gci_triplet[1]]
                gci=gci_three_grid(h,float(data['point_uz']),
                                   medium['h'],float(medium['uz_P']),
                                   coarse['h'],float(coarse['uz_P']),
                                   safety_factor=safety_factor,min_ratio=min_ratio)
        if method == 'relative':
            threshold_met = (None if delta is None else delta <= tol_pct)
            eligible = threshold_met
        else:
            # None means NOT EVALUABLE, which is scientifically distinct from
            # False (a valid GCI estimate greater than the numerical threshold).
            threshold_met = (None if gci is None or not gci['valid_estimate']
                             else bool(gci['gci_pct'] <= tol_pct))
            # Numeric GCI threshold and the study's optional refinement-ratio
            # selection gate are intentionally two DIFFERENT predicates.
            eligible = (None if threshold_met is None else
                        bool(threshold_met and gci['recommended_ratios_met']))
        if selected is None and eligible is True:
            selected=step_number
        entry={
            'step':step_number,'nx':nx,'nu':nu,'nv':nv,'h':h,
            'h8_elements':data['h8_elements'],'nodes':data['nodes'],
            'ux_P':data['point_ux'],'uy_P':data['point_uy'],
            'uz_P':data['point_uz'],'delta_uz_pct':delta,
            'meets_tolerance':threshold_met,
            'eligible_for_selection':eligible,
            'gci_valid_estimate':(None if method != 'gci' or gci is None
                                  else bool(gci['valid_estimate'])),
            'evaluation':data['point_evaluation']['sampling'],
            'npz':data['npz'],
            'gci_triplet_nx': gci_triplet,
            'r21':None,'r32':None,'p_observed':None,
            'richardson_extrapolated':None,'gci_pct':None,
            'gci_band_lower':None,'gci_band_upper':None,
            'recommended_ratios_met':None,'study_minimum_ratios_met':None,'gci_note':None,
        }
        if gci is not None:
            for key in ('r21','r32','p_observed','richardson_extrapolated',
                        'gci_pct','gci_band_lower','gci_band_upper','recommended_ratios_met'):
                entry[key]=gci[key]
            entry['study_minimum_ratios_met']=gci['recommended_ratios_met']
            entry['gci_note']=gci['reason']
        rows.append(entry)
    return rows,selected


def selected_info(rows: list[dict], selected: int | None) -> dict | None:
    if selected is None:
        return None
    r=rows[selected-1]
    return {
        'step':int(r['step']),'mesh':f'{r["nx"]}x{r["nu"]}x{r["nv"]}',
        'nx':int(r['nx']),'nu':int(r['nu']),'nv':int(r['nv']),
        'h8_elements':int(r['h8_elements']),'nodes':int(r['nodes']),
        'uz_P':float(r['uz_P']),'delta_uz_pct':r['delta_uz_pct'],
        'gci_pct':r['gci_pct'],'p_observed':r['p_observed'],
        'richardson_extrapolated':r['richardson_extrapolated'],
        'gci_triplet_nx':r.get('gci_triplet_nx'),
        'gci_threshold_met':r.get('meets_tolerance'),
        'eligible_for_selection':r.get('eligible_for_selection'),
        'npz':str(r['npz']),
    }


def study_status(method: str, selected: int | None, *, complete: bool, failed: bool = False) -> str:
    """Report *decisions*, never an unverified GCI convergence claim."""
    if failed:
        return 'failed'
    if not complete:
        return 'in_progress'
    if method == 'gci':
        return ('gci_selection_criterion_met' if selected is not None
                else 'gci_selection_criterion_not_met')
    if method == 'relative':
        return ('relative_change_criterion_met' if selected is not None
                else 'relative_change_criterion_not_met')
    raise ValueError(f'Unknown method {method!r}')


def write_reports(run_dir: Path, manifest: dict, rows: list[dict],
                  selected: int | None, status: str,
                  failure: str | None = None, plots: bool = True) -> None:
    method=manifest.get('method','relative')
    if method == 'gci' and status not in {
            'in_progress', 'failed', 'gci_selection_criterion_met',
            'gci_selection_criterion_not_met'}:
        raise ValueError('GCI status must describe selection, not proven convergence')
    if method == 'relative' and status not in {
            'in_progress','failed','relative_change_criterion_met',
            'relative_change_criterion_not_met'}:
        raise ValueError('Relative-change status must not claim proven convergence')
    if status in ('gci_selection_criterion_met','relative_change_criterion_met') and selected is None:
        raise ValueError('Selection-met final status requires a selected step')
    if status in ('gci_selection_criterion_not_met','relative_change_criterion_not_met') and selected is not None:
        raise ValueError('Selection-not-met final status cannot have a selected step')
    columns=('step','nx','nu','nv','h','h8_elements','nodes','ux_P','uy_P','uz_P',
             'delta_uz_pct','gci_triplet_nx','r21','r32','p_observed','richardson_extrapolated',
             'gci_pct','gci_band_lower','gci_band_upper','recommended_ratios_met',
             'study_minimum_ratios_met','gci_valid_estimate','gci_note','meets_tolerance',
             'eligible_for_selection','evaluation','npz')
    with (run_dir/'convergence.csv').open('w',encoding='utf-8',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=columns)
        writer.writeheader();writer.writerows(rows)
    # No final reference mesh is published while running or after a failure;
    # step-level candidates remain visible in the saved row diagnostics.
    complete = status not in ('in_progress', 'failed')
    chosen=selected_info(rows,selected) if complete else None
    valid_gci_rows = [r for r in rows if r.get('gci_valid_estimate') is True]
    result={
        'version':VERSION,'method':method,'status':status,
        # Neither a GCI threshold nor a two-mesh change threshold proves convergence.
        'gci_acceptance_threshold_met':(
            (any(r['meets_tolerance'] is True for r in valid_gci_rows)
             if valid_gci_rows else None) if method=='gci' else None),
        'gci_threshold_met_any_valid_triplet':(
            (any(r['meets_tolerance'] is True for r in valid_gci_rows)
             if valid_gci_rows else None) if method=='gci' else None),
        'gci_selection_criterion_met':(
            (selected is not None if complete else None) if method=='gci' else None),
        'converged':None,
        'asymptotic_regime_status':('not_assessed' if method=='gci' else None),
        'study_manifest_version':manifest.get('version'),
        'selection_rule':('STUDY-SPECIFIC: first eligible three-grid estimate with '
                          'GCI <= the user tolerance, positive observed order, '
                          'and BOTH ratios above the chosen minimum' if method=='gci' else
                          'first consecutive pair with relative change <= tolerance'),
        'asymptotic_regime_independently_verified':None,
        'method_reference':('ASME V&V 10.1-2012 (R2022), Section 7.2, '
                            'equations (4), (6), (8), (10)' if method=='gci' else None),
        'asymptotic_limitation':('The three-grid estimate is CONDITIONAL on the asymptotic '
                                  'power-law assumption, which this program does NOT verify. '
                                  'No convergence of the entire FEM3D field and no certified '
                                  'bound on the exact 3D error are claimed.'
                                  if method=='gci' else None),
        'point_xyz':manifest['point_xyz'], 'point_units':'native FEM coordinate units',
        'component':'uz','tolerance_pct':manifest['tolerance_pct'],
        'safety_factor':manifest.get('safety_factor') if method=='gci' else None,
        'min_refinement_ratio':manifest.get('min_refinement_ratio') if method=='gci' else None,
        'transverse_divisions_per_csf_domain':{'nu':manifest['nu'],'nv':manifest['nv']},
        'selected_step':(chosen['step'] if chosen else None),'selected_mesh':chosen['mesh'] if chosen else None,
        'selected_mesh_interpretation':('candidate chosen by STUDY-SPECIFIC GCI selection rule; '
                                        'asymptotic regime NOT assessed' if chosen and method=='gci' else
                                        'chosen by non-GCI relative-change rule; no convergence proof' if chosen else None),
        'selected_mesh_divisions':([chosen[k] for k in ('nx','nu','nv')] if chosen else None),
        'selected_h8_elements':chosen['h8_elements'] if chosen else None,
        'selected_nodes':chosen['nodes'] if chosen else None,
        'selected_uz_P':chosen['uz_P'] if chosen else None,
        'selected_delta_pct':chosen['delta_uz_pct'] if chosen else None,
        'selected_gci_pct':chosen['gci_pct'] if chosen else None,
        'selected_p_observed':chosen['p_observed'] if chosen else None,
        'selected_triplet_nx':chosen['gci_triplet_nx'] if chosen else None,
        'selected_richardson_extrapolated':chosen['richardson_extrapolated'] if chosen else None,
        'selected_npz':chosen['npz'] if chosen else None,
        'step_count':len(rows),'planned_step_count':len(manifest['nx']),
        'rows':rows,'manifest':str((run_dir/'manifest.json').resolve()),'failure':failure,
        'gci_triplets_planned':manifest.get('gci_triplets') if method == 'gci' else None,
    }
    write_json(run_dir/'convergence_result.json',result)
    p=manifest['point_xyz']
    lines=[
        '# FEM3D longitudinal discretization study: '+method, '',
        f'Status: **{status}**','',
        f'Point P (CUF/OpenSees x,y,z): **({p[0]:g}, {p[1]:g}, {p[2]:g})**',
        f'Fixed transverse divisions per CSF domain: **nu={manifest["nu"]}, nv={manifest["nv"]}**',
        f'Method: **{method}**, acceptance threshold: **{manifest["tolerance_pct"]:g}%**',
    ]
    if method=='gci':
        lines += [f'F_s={manifest["safety_factor"]:g}; STUDY minimum r > {manifest["min_refinement_ratio"]:g}; ASME recommends r > 1.3.',
                  'Use three mesh levels to infer a positive observed order p. '
                  'The fine-grid GCI is F_s * |(w1-w2)/w1| / (r21^p-1).',
                  'Reference: ASME V&V 10.1-2012 (R2022), Section 7.2, Eqs. (4),(6),(8),(10).',
                  'Acceptance by GCI is conditional on the Richardson asymptotic-power-law assumption. '
                  'Three-point fitting alone cannot establish this assumption.',
                  'GCI triplets were chosen from nx before reading any displacement; '
                  'these are listed in the gci_triplet_nx column.',
                  '**ASYMPTOTIC REGIME: NOT ASSESSED.** A positive fitted p, GCI < threshold '
                  'or an automatic selection DOES NOT by itself prove convergence.',
                  'The ratio check is a STUDY selection rule; ASME recommends r > 1.3 '
                  'but does not impose it as a universal mandatory acceptance condition.']
    else:
        lines += ['Consecutive relative change: 100 |uz_k(P)-uz_(k-1)(P)|/|uz_k(P)|.']
    lines += ['', '| Step | Mesh nx x nu x nv | H8 | h | uz(P) | delta (%) | p_obs | GCI (%) | Below threshold | Eligible for selection |',
              '|---:|---|---:|---:|---:|---:|---:|---:|---|---|']
    def fmt(x):
        return '-' if x is None else f'{x:.8g}'
    def yesno(x):
        return 'n/a' if x is None else ('yes' if x else 'no')
    for r in rows:
        lines.append(f'| {r["step"]} | {r["nx"]}x{r["nu"]}x{r["nv"]} | '
                     f'{r["h8_elements"]} | {r["h"]:.8g} | {r["uz_P"]:.12g} | '
                     f'{fmt(r["delta_uz_pct"])} | {fmt(r["p_observed"])} | '
                     f'{fmt(r["gci_pct"])} | {yesno(r["meets_tolerance"])} | '
                     f'{yesno(r["eligible_for_selection"])} |')
    if method=='gci':
        lines += ['', '## Richardson diagnostics', '',
                  '| Step | nx triplet coarse/medium/fine | r21 | r32 | extrapolated uz | GCI band lower | GCI band upper | note |',
                  '|---:|---|---:|---:|---:|---:|---:|---|']
        for r in rows:
            lines.append(f'| {r["step"]} | {r["gci_triplet_nx"] or "-"} | {fmt(r["r21"])} | {fmt(r["r32"])} | '
                         f'{fmt(r["richardson_extrapolated"])} | {fmt(r["gci_band_lower"])} | '
                         f'{fmt(r["gci_band_upper"])} | {r["gci_note"] or "-"} |')
    lines.append('')
    if chosen:
        label = ('SELECTED BY STUDY GCI RULE (asymptotic regime NOT assessed)'
                 if method == 'gci' else 'SELECTED MESH')
        lines += [f'**{label}: {chosen["mesh"]}** '
                  f'({chosen["h8_elements"]} H8, {chosen["nodes"]} nodes).',
                  f'Chosen uz(P): `{chosen["uz_P"]:.12g}`.',
                  (f'GCI: `{chosen["gci_pct"]:.8g}%`, observed p: `{chosen["p_observed"]:.8g}`.'
                   if method=='gci' else f'Relative delta: `{chosen["delta_uz_pct"]:.8g}%`.'),
                  f'Checkpoint: `{chosen["npz"]}`.']
    else:
        lines.append('**SELECTED MESH: none** (study selection rule not met in completed sequence).')
    if failure:
        lines.append(f'\nError: `{failure}`')
    lines += ['', 'The transverse mesh is fixed. This is only a longitudinal '
              'discretization-sensitivity analysis for the monitored FEM3D point displacement; '
              'in GCI mode the discretization-uncertainty ESTIMATE is conditional on the '
              'unverified asymptotic assumption. No stress, energy, transverse-mesh or '
              'complete-field convergence is asserted. The script does not assess the asymptotic regime.']
    (run_dir/'convergence.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if not (plots and rows):
        return
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('[FEM convergence] matplotlib not available; CSV/JSON/MD saved',flush=True)
        return
    x=[r['nx'] for r in rows]
    fig,ax=plt.subplots(figsize=(8,4.5))
    ax.plot(x,[r['uz_P'] for r in rows],'o-',linewidth=1.5)
    if chosen:
        ax.axvline(chosen['nx'],linestyle='--',color='gray',label='study-rule nx')
        ax.legend()
    ax.set(xlabel='Longitudinal H8 divisions nx',ylabel='uz(P) [native length units]',
           title='FEM3D longitudinal mesh sensitivity: point displacement')
    ax.grid(alpha=0.3);fig.tight_layout()
    fig.savefig(run_dir/'uz_point_convergence.png',dpi=180)
    plt.close(fig)
    key='gci_pct' if method=='gci' else 'delta_uz_pct'
    plotted=[r for r in rows if r[key] is not None]
    if plotted:
        fig,ax=plt.subplots(figsize=(8,4.5))
        ax.plot([r['nx'] for r in plotted],[r[key] for r in plotted],'o-')
        ax.axhline(manifest['tolerance_pct'],linestyle='--',color='gray',
                   label=f'threshold {manifest["tolerance_pct"]:g}%')
        if chosen:
            ax.axvline(chosen['nx'],linestyle=':',color='gray',label='study-rule nx')
        ax.set(xlabel='Longitudinal H8 divisions nx',
               ylabel=('GCI [%]' if method=='gci' else 'Relative change [%]'),
               title=('Three-grid GCI (conditional asymptotic estimate)' if method=='gci' else 'Consecutive change'))
        ax.grid(alpha=0.3);ax.legend();fig.tight_layout()
        fig.savefig(run_dir/('gci_convergence.png' if method=='gci' else 'relative_changes.png'),dpi=180)
        plt.close(fig)
    if method=='gci':
        fitted=[r for r in rows if r['p_observed'] is not None]
        if fitted:
            fig,ax=plt.subplots(figsize=(8,4.5))
            ax.plot([r['nx'] for r in fitted],[r['p_observed'] for r in fitted],'o-')
            ax.set(xlabel='Longitudinal H8 divisions nx',ylabel='Observed order p',
                   title='Three-grid observed longitudinal convergence order')
            ax.grid(alpha=0.3);fig.tight_layout()
            fig.savefig(run_dir/'observed_order.png',dpi=180)
            plt.close(fig)

def parse_reuse(entries: list[str], nx_values: list[int], nu: int, nv: int) -> dict:
    result = {}
    for item in entries:
        key, equals, filename = item.partition("=")
        if not equals or not filename:
            raise ValueError("--reuse-npz requires NX=FILE.npz (or NXxNUxNV=FILE.npz)")
        if re.fullmatch(r"\d+", key):
            mesh = (int(key), nu, nv)
        else:
            match = re.fullmatch(r"(\d+)[xX](\d+)[xX](\d+)", key)
            if not match:
                raise ValueError(f"Unrecognized --reuse-npz mesh: {key!r}")
            mesh = tuple(int(n) for n in match.groups())
        if mesh[0] not in nx_values or mesh[1:] != (nu, nv):
            raise ValueError(f"Reused NPZ {mesh} does not fit fixed-transverse schedule")
        label = str(mesh[0])
        if label in result:
            raise ValueError(f"Repeated --reuse-npz for nx={mesh[0]}")
        path = Path(filename).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        result[label] = {"path": str(path), "sha256": sha256(path)}
    return result


def allocate_run(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(1, 100000):
        path = root / f"run_{i:04d}"
        try:
            path.mkdir(exist_ok=False)
            return path
        except FileExistsError:
            continue
    raise RuntimeError("Could not allocate a unique run directory")


def print_selected(rows: list[dict], selected: int | None, method: str = 'gci') -> None:
    info=selected_info(rows,selected)
    if info is None:
        print('[FEM convergence] SELECTED MESH: NONE',flush=True)
        return
    label = ('SELECTED BY STUDY GCI RULE (asymptotic NOT assessed)'
             if method=='gci' else 'SELECTED MESH')
    print(f'[FEM convergence] {label}: {info["mesh"]} '
          f'({info["h8_elements"]} H8, {info["nodes"]} nodes)',flush=True)
    if method=='gci':
        print(f'[FEM convergence] selected uz(P)={info["uz_P"]:.12g}, '
              f'GCI={info["gci_pct"]:.8g}%, observed p={info["p_observed"]:.8g}, '
              f'triplet={info["gci_triplet_nx"]}',flush=True)
    else:
        print(f'[FEM convergence] selected uz(P)={info["uz_P"]:.12g}, '
              f'delta={info["delta_uz_pct"]:.8g}%',flush=True)
    print(f'[FEM convergence] selected NPZ: {info["npz"]}',flush=True)

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("case", type=Path, help="Original CSF-CUF case YAML")
    p.add_argument("--driver", type=Path, default=None,
                   help="Existing CSF-based OpenSees H8 driver (use explicit path for reproducibility)")
    p.add_argument("--nx", nargs="+", type=int, required=False,
                   help="Strictly increasing longitudinal divisions, e.g. --nx 20 40 60 80 100 125")
    p.add_argument("--nu", type=int, help="Fixed transverse H8 subdivisions per CSF domain")
    p.add_argument("--nv", type=int, help="Fixed transverse H8 subdivisions per CSF domain")
    p.add_argument("--point", nargs=3, type=float, metavar=("X", "Y", "Z"),
                   help="Exactly one fixed physical P in OpenSees/CUF coordinates (native units)")
    p.add_argument("--method", choices=("gci", "relative"), default=None,
                   help="gci: 3-grid ASME/Richardson (default); relative: v02 2-grid variation")
    p.add_argument("--tolerance-pct", type=float, default=None,
                   help="Acceptance threshold in percent (GCI or relative), default 0.5")
    p.add_argument("--gci-triple", type=int, nargs=3, action="append",
                   metavar=("COARSE","MEDIUM","FINE"),
                   help="Explicit PREDECLARED GCI triplet of nx, repeatable; defaults to mesh-only planning")
    p.add_argument("--safety-factor", type=float, default=None,
                   help="Three-grid GCI safety factor F_s; default 1.25")
    p.add_argument("--min-refinement-ratio", type=float, default=None,
                   help="Conservative run-selection rule: require both h-ratios greater than this; ASME recommends > 1.3")
    p.add_argument("--output-root", type=Path,
                   default=Path("fem3d/convergence_longitudinal"),
                   help="New uniquely numbered run directory; never overwrites older studies")
    p.add_argument("--resume", type=Path,
                   help="Continue a v03 study with immutable method and criteria")
    p.add_argument("--run-all", action="store_true",
                   help="Solve every listed nx even if the study-specific selection criterion is met earlier")
    p.add_argument("--reuse-npz", action="append", default=[], metavar="NX=FILE.npz",
                   help="Copy and validate a pre-existing solved FEM NPZ; exact nx/nu/nv must match")
    p.add_argument("--no-plots", action="store_true")
    a = p.parse_args(argv)

    case = a.case.expanduser().resolve()
    if not case.is_file():
        p.error(f'Case YAML not found: {case}')
    if a.driver is not None:
        driver = a.driver.expanduser().resolve()
        candidates = [driver]
    else:
        candidates = [Path(__file__).with_name('run_opensees_csf.py').resolve(),
                      (case.parent.parent / 'fem3d' / 'run_opensees_csf.py').resolve()]
        driver = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    if not driver.is_file():
        p.error('OpenSees driver not found; tried: ' + ', '.join(map(str, candidates))
                + '. Supply --driver explicitly.')
    provenance = model_provenance(case, driver)

    if a.resume:
        run_dir = a.resume.expanduser().resolve()
        manifest_file = run_dir / "manifest.json"
        if not manifest_file.is_file():
            p.error(f"Missing v03 manifest: {run_dir}")
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        if manifest.get("version") not in (VERSION, LEGACY_VERSION):
            p.error('Unsupported convergence manifest version; do not mix different study definitions.')
        if manifest.get("inputs") != provenance:
            p.error("Resume rejected: case/problem/model/adapter/driver fingerprints changed")
        nx_values = manifest["nx"]
        nu, nv = manifest["nu"], manifest["nv"]
        point = np.asarray(manifest["point_xyz"], dtype=float)
        tol = manifest["tolerance_pct"]
        method = manifest["method"]
        safety_factor = manifest["safety_factor"]
        min_ratio = manifest["min_refinement_ratio"]
        gci_triplets = manifest.get("gci_triplets", {})
        if a.gci_triple:
            if plan_gci_triplets(nx_values,min_ratio,a.gci_triple) != gci_triplets:
                p.error("GCI triplets differ from saved study")
        if a.method is not None and a.method != method:
            p.error("--method differs from saved study")
        if a.safety_factor is not None and a.safety_factor != safety_factor:
            p.error("--safety-factor differs from saved study")
        if a.min_refinement_ratio is not None and a.min_refinement_ratio != min_ratio:
            p.error("--min-refinement-ratio differs from saved study")
        if a.nx is not None and parse_nx(a.nx) != nx_values:
            p.error("--nx differs from the saved study")
        if a.nu is not None and a.nu != nu or a.nv is not None and a.nv != nv:
            p.error("Transverse subdivisions differ from the saved study")
        if a.point is not None and list(a.point) != point.tolist():
            p.error("Physical point P differs from the saved study")
        if a.tolerance_pct is not None and a.tolerance_pct != tol:
            p.error("Tolerance differs from the saved study")
        if a.reuse_npz and parse_reuse(a.reuse_npz, nx_values, nu, nv) != manifest["reused_npz"]:
            p.error("Reused-NPZ inputs differ from the saved study")
        if a.run_all and not manifest["run_all"]:
            p.error("--run-all cannot be enabled on resume if the study stopped early")
        run_all = manifest["run_all"]
        print(f"[FEM h-convergence] resume: {run_dir}", flush=True)
    else:
        if a.nx is None or a.nu is None or a.nv is None or a.point is None:
            p.error("New study requires --nx, --nu, --nv and --point X Y Z")
        nx_values = parse_nx(a.nx)
        method = a.method or 'gci'
        if method == 'gci' and len(nx_values) < 3:
            p.error("Three-grid GCI requires at least 3 longitudinal meshes")
        safety_factor = finite_float(1.25 if a.safety_factor is None else a.safety_factor,
                                     "safety-factor")
        min_ratio = finite_float(1.3 if a.min_refinement_ratio is None else a.min_refinement_ratio,
                                 "min-refinement-ratio")
        if safety_factor <= 0 or min_ratio <= 1:
            p.error("GCI safety factor must be positive and minimum ratio must exceed 1")
        nu, nv = int(a.nu), int(a.nv)
        if min(nu, nv) < 1:
            p.error("Fixed transverse divisions --nu and --nv must be positive")
        point = np.asarray([finite_float(v, "point coordinate") for v in a.point], dtype=float)
        tol = finite_float(0.5 if a.tolerance_pct is None else a.tolerance_pct, "tolerance-pct")
        if tol <= 0:
            p.error("Tolerance must be positive")
        run_all = bool(a.run_all)
        reused = parse_reuse(a.reuse_npz, nx_values, nu, nv)
        gci_triplets = (plan_gci_triplets(nx_values,min_ratio,a.gci_triple)
                        if method == 'gci' else {})
        run_dir = allocate_run(a.output_root.expanduser().resolve())
        manifest = {
            "version": VERSION, "created_utc": datetime.now(timezone.utc).isoformat(),
            "inputs": provenance, "nx": nx_values, "nu": nu, "nv": nv,
            "point_xyz": point.tolist(), "tolerance_pct": tol,
            "method": method, "safety_factor": safety_factor,
            "gci_triplets":gci_triplets,
            "min_refinement_ratio": min_ratio,
            "selection_rule": ("first eligible 3-grid Richardson GCI" if method == "gci" else
                               "first consecutive pair meeting pointwise uz tolerance"),
            "run_all": run_all, "reused_npz": reused,
            "python_executable": sys.executable,
        }
        write_json(run_dir / "manifest.json", manifest)
        print(f"[FEM h-convergence] new study: {run_dir}", flush=True)
        if method=='gci':
            print('[FEM h-convergence] method: ASME V&V 10.1-2012 (R2022), Section 7.2, three-grid GCI', flush=True)
        if method == 'gci':
            print(f"[FEM h-convergence] predetermined GCI triples: {gci_triplets}",flush=True)

    rows, selected = collect_rows(run_dir, nx_values, nu, nv, tol, point.tolist(),
                                  method=method, safety_factor=safety_factor, min_ratio=min_ratio,
                                  gci_triplets=gci_triplets)
    if selected is not None and not run_all:
        status = study_status(method, selected, complete=True)
        write_reports(run_dir, manifest, rows, selected, status, plots=not a.no_plots)
        print(f'[FEM h-convergence] resumed study: {status}', flush=True)
        print_selected(rows, selected, method=method)
        return 0
    if len(rows) == len(nx_values):
        status = study_status(method, selected, complete=True)
        write_reports(run_dir, manifest, rows, selected, status, plots=not a.no_plots)
        print(f"[FEM h-convergence] all steps already completed: {status}", flush=True)
        print_selected(rows, selected, method=method)
        return 0 if selected is not None else 2

    try:
        for index, nx in enumerate(nx_values, 1):
            step = run_dir / f"step_{index:03d}"
            step.mkdir(exist_ok=True)
            npz = step / "solution.npz"
            meta_file = step / "metrics.json"
            mesh = (nx, nu, nv)
            if meta_file.exists():
                if not npz.is_file():
                    raise RuntimeError(f"Missing solved checkpoint for completed step: {npz}")
                verified = json.loads(meta_file.read_text(encoding="utf-8"))
                if verified.get("npz_sha256") != sha256(npz):
                    raise RuntimeError(f"Previously validated NPZ was modified: {npz}")
            else:
                if not npz.exists():
                    saved = manifest["reused_npz"].get(str(nx))
                    if saved:
                        src = Path(saved["path"])
                        if not src.is_file() or sha256(src) != saved["sha256"]:
                            raise RuntimeError(f"Reused solved NPZ changed or disappeared: {src}")
                        if src.resolve() == npz.resolve():
                            raise ValueError("Cannot use a run step as its own --reuse-npz source")
                        shutil.copy2(src, npz)
                        print(f"[FEM h-convergence] step {index}: reused solved NPZ {src}", flush=True)
                    else:
                        cmd = [sys.executable, str(driver), str(case), str(npz),
                               "--nx", str(nx), "--nu", str(nu), "--nv", str(nv)]
                        log = step / "solver.log"
                        attempt = 2
                        while log.exists():
                            log = step / f"solver_attempt_{attempt:03d}.log"
                            attempt += 1
                        print(f"[FEM h-convergence] step {index}/{len(nx_values)}: "
                              f"mesh={nx}x{nu}x{nv}; log={log}", flush=True)
                        with log.open("w", encoding="utf-8") as out:
                            out.write("COMMAND: " + " ".join(cmd) + "\n\n")
                            out.flush()
                            result = subprocess.run(cmd, stdout=out,
                                                    stderr=subprocess.STDOUT, check=False)
                        if result.returncode != 0:
                            tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-18:]
                            raise RuntimeError(f"OpenSees solver failed: {log}\n" + "\n".join(tail))
                        if not npz.exists():
                            raise RuntimeError(f"Solver did not produce checkpoint: {npz}")
                else:
                    print(f"[FEM h-convergence] step {index}: validating existing NPZ", flush=True)
                metrics = analyze_solution(npz, mesh, point, provenance["case_name"])
                write_json(meta_file, metrics)
            rows, selected = collect_rows(run_dir, nx_values, nu, nv, tol, point.tolist(),
                                  method=method, safety_factor=safety_factor, min_ratio=min_ratio,
                                  gci_triplets=gci_triplets)
            write_reports(run_dir, manifest, rows, selected,
                          study_status(method, selected, complete=False),
                          plots=not a.no_plots)
            current = rows[-1]
            delta = ("initial" if current["delta_uz_pct"] is None
                     else f'delta={current["delta_uz_pct"]:.8g}%')
            if method == 'gci':
                gci = current['gci_pct']
                description = ((f'GCI={gci:.8g}%, p={current["p_observed"]:.7g}; '
                                f'below_threshold={current["meets_tolerance"]}, '
                                f'selection_eligible={current["eligible_for_selection"]}') if gci is not None
                               else (current['gci_note'] or 'needs three meshes'))
            else:
                description = delta
            print(f'[FEM convergence] step {index}: mesh={nx}x{nu}x{nv}; '
                  f'uz(P)={current["uz_P"]:.12g}; {description}', flush=True)
            if selected is not None and not run_all:
                break
        status = study_status(method, selected, complete=True)
        write_reports(run_dir, manifest, rows, selected, status, plots=not a.no_plots)
        label = (status.upper() + ' (asymptotic regime NOT assessed)'
                 if method == 'gci' else status.upper())
        print(f"[FEM h-convergence] {label}; report={run_dir / 'convergence_result.json'}",
              flush=True)
        print_selected(rows, selected, method=method)
        return 0 if selected is not None else 2
    except Exception as exc:
        print(f"[FEM h-convergence] ERROR: {exc}", file=sys.stderr, flush=True)
        traceback.print_exc()
        rows, selected = collect_rows(run_dir, nx_values, nu, nv, tol, point.tolist(),
                                  method=method, safety_factor=safety_factor, min_ratio=min_ratio,
                                  gci_triplets=gci_triplets)
        write_reports(run_dir, manifest, rows, selected, "failed",
                      failure=str(exc), plots=not a.no_plots)
        return 1


if __name__ == "__main__":
    sys.exit(main())
