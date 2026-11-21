#!/usr/bin/env python3
"""Compare CUF recovered traction sigma*n with prescribed traction on loaded faces.

This audit DOES NOT integrate tractions over beam cross-sections. It integrates
only the exact exterior loaded surfaces selected by the supplied
vertical_face_tractions.py adapter.  The continuous CUF stress is reconstructed
by the supplied plot_strain_stress_boundary_v10.py's _evaluate_cuf_state().

Both sides use the SAME physical loaded face and orientation:
   F_sigma = integral_{Gamma_load} sigma_CUF * n dS
   F_load  = integral_{Gamma_load} t_prescribed dS
with t_prescribed = (0,0,p_z*abs(n_z)) (N/mm2). The moment about (x0,0,0)
is computed in addition. All values are N, N mm, and MPa for the supplied case.

A weak FE formulation does not guarantee pointwise satisfaction of Neumann
conditions by stress reconstructed as C*strain; residuals are diagnostic,
not automatically a sign of failed global force equilibrium.

Requirements are explicit: provided CUF case/problem/CSF model/load adapter,
CUF .cuf.npz and matching step_manifest.json, and supplied plotting script.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


def _load_module(path: Path, name: str):
    if not path.is_file():
        raise FileNotFoundError(f"Missing required module: {path}")
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load source file {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_check(checkpoint: Path, case, problem, load_path: Path):
    manifest_file = checkpoint.parent / "step_manifest.json"
    if not manifest_file.is_file():
        raise FileNotFoundError(f"Missing checkpoint provenance: {manifest_file}")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("status") != "completed":
        raise ValueError(f"Manifest status is not completed: {manifest_file}")
    files = {
        "step_case": case.path,
        "problem_yaml": case.problem_path,
        "csf_model_yaml": problem.model_path,
        "load_adapter": load_path,
    }
    for key, path in files.items():
        expected = manifest.get("inputs", {}).get(key, {}).get("sha256")
        if expected is None or _sha(Path(path)) != expected:
            raise ValueError(f"SHA-256 mismatch for {key}: {path}")
    if manifest.get("checkpoint_sha256") != _sha(checkpoint):
        raise ValueError(f"Checkpoint SHA-256 mismatch: {checkpoint}")
    if manifest.get("case_name") != case.name:
        raise ValueError("Checkpoint case name does not match manifest")
    return manifest_file


def _resolve_load_adapter(problem):
    raw = problem.problem_options.get("load")
    if not isinstance(raw, dict):
        raise ValueError("Expected a composite problem with problem.load")
    rel = raw.get("adapter")
    if not isinstance(rel, str) or Path(rel).suffix != ".py":
        raise ValueError("Expected problem.load.adapter to refer to a local Python file")
    return (Path(problem.path).parent / rel).resolve()


def _stress_matrix(voigt):
    # Contract of the supplied plotting script: xx,yy,zz,yz,xz,xy.
    xx, yy, zz, yz, xz, xy = map(float, voigt)
    return np.array([[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]])


def _as_numbers(a):
    return [float(v) for v in a]


def _result_dict(Fstress, Fload, Mstress, Mload, area, samples, point_sq, ref_sq):
    Fdiff = Fstress - Fload
    Mdiff = Mstress - Mload
    fref = float(np.linalg.norm(Fload))
    mref = float(np.linalg.norm(Mload))
    return {
        "F_stress_N": _as_numbers(Fstress),
        "F_load_N": _as_numbers(Fload),
        "F_difference_N": _as_numbers(Fdiff),
        "M_stress_about_x0_Nmm": _as_numbers(Mstress),
        "M_load_about_x0_Nmm": _as_numbers(Mload),
        "M_difference_Nmm": _as_numbers(Mdiff),
        "relative_force_resultant_percent": (100.0 * float(np.linalg.norm(Fdiff)) / fref if fref else None),
        "relative_moment_resultant_percent": (100.0 * float(np.linalg.norm(Mdiff)) / mref if mref else None),
        "relative_traction_L2_percent": (100.0 * float(np.sqrt(point_sq / ref_sq)) if ref_sq else None),
        "loaded_surface_area_mm2": float(area),
        "sample_count": int(samples),
    }


def _run(case_path: Path, npz_override: Path | None, stress_override: Path | None,
         axial_gauss: int | None, edge_gauss: int | None):
    root = case_path.parent.parent.parent.resolve()
    # Repository layout: cuf/I-Shape_cantilever and ../../src/csf.
    # The standalone test ZIP instead carries src/csf directly in its root.
    source_roots = (root / "src", root.parent.parent / "src")
    sources = [p for p in source_roots if (p / "csf").is_dir()]
    if sources:
        sys.path.insert(0, str(sources[0]))
    # Otherwise use the installed csf package; never reconstruct it locally.

    from csf.cuf.case import load_case
    from csf.cuf.problem.problem_api import load_problem, build_local_composite_problem
    from csf.cuf.csf_bridge import CSFCUFModelBridge
    from csf.cuf.solver.compiled_field import CompiledDisplacementField

    case = load_case(case_path)
    problem = load_problem(case.problem_path)
    if problem.problem_type != "composite":
        raise ValueError("Only the supplied composite load problem is supported")
    load_path = _resolve_load_adapter(problem)
    if load_path.name != "vertical_face_tractions.py":
        raise ValueError(f"Unsupported load adapter: {load_path}")
    load = build_local_composite_problem(problem).load_problem
    if type(load).__name__ != "VerticalFaceTractions":
        raise ValueError(f"Unexpected load class: {type(load)}")

    if npz_override is None:
        files = sorted(Path(case.output_dir).glob("*.cuf.npz"))
        if len(files) != 1:
            raise FileNotFoundError(f"Expected one *.cuf.npz in {case.output_dir}; found {len(files)}. Supply --npz")
        npz_path = files[0].resolve()
    else:
        npz_path = npz_override.resolve()
    manifest_path = _manifest_check(npz_path, case, problem, load_path)
    # Use the stress recovery module shipped with the CSF package.  It is
    # located at src/csf/cuf/tools/plot_strain_stress_boundary_v10.py, not at
    # the I-Shape_cantilever project root.  Keep --stress-script as an explicit
    # override when comparing against a specific separate source file.
    if stress_override is None:
        stress_tool = importlib.import_module("csf.cuf.tools.plot_strain_stress_boundary_v10")
        stress_path = Path(stress_tool.__file__).resolve()
    else:
        stress_path = stress_override.resolve()
        stress_tool = _load_module(stress_path, "_exact_supplied_stress_tool")
    for key in ("validate_checkpoint_domain_lookups", "_evaluate_cuf_state"):
        if not callable(getattr(stress_tool, key, None)):
            raise TypeError(f"The supplied stress script lacks {key}()")

    bridge = CSFCUFModelBridge.from_yaml(problem.model_path)
    field = CompiledDisplacementField.load(npz_path)
    x0, x1 = bridge.longitudinal_domain()
    if not np.allclose([x0, x1], [field.x_start, field.x_end], rtol=0, atol=1e-9):
        raise ValueError("CUF checkpoint and CSF model have different x domains")
    faces = load.physical_surface_tractions(section_provider=bridge.section_provider, x0=x0, x1=x1)
    if not faces:
        raise ValueError("No physically loaded exterior surfaces")

    # Only the axial FE partition is read from the NPZ; no physical geometry,
    # material law or loads are recovered from the checkpoint arrays.
    with np.load(npz_path, allow_pickle=False) as raw:
        starts = np.asarray(raw["element_x_starts"], dtype=float)
        ends = np.asarray(raw["element_x_ends"], dtype=float)
    if not (starts.ndim == ends.ndim == 1 and len(starts) > 0 and len(starts) == len(ends)
            and np.all(ends > starts) and np.allclose(starts[1:], ends[:-1], rtol=0, atol=1e-9)
            and abs(starts[0]-x0) < 1e-9 and abs(ends[-1]-x1) < 1e-9):
        raise ValueError("CUF checkpoint element intervals are not a contiguous mesh")

    qa = int(axial_gauss if axial_gauss is not None else load.axial_gauss)
    qt = int(edge_gauss if edge_gauss is not None else load.edge_gauss)
    if qa < 2 or qt < 2:
        raise ValueError("Use at least 2-point Gauss rules")
    xa, wa = np.polynomial.legendre.leggauss(qa)
    ta, wt = np.polynomial.legendre.leggauss(qt)
    provider = bridge.section_provider

    # Surface parametrization and outward oriented area vector are *identical*
    # to the face geometry rule of the supplied vertical_face_tractions.py:
    # V(x) is queried from CSF at each x, and vdot is obtained from CSF end
    # sections in the exact manner used by build_load_vector().
    speeds = {}
    for domain_id, edge, pz, side in faces:
        V0 = np.asarray(provider.domain(x0, domain_id).vertices, dtype=float)
        V1 = np.asarray(provider.domain(x1, domain_id).vertices, dtype=float)
        if V0.shape != (4, 2) or V1.shape != (4, 2):
            raise ValueError("The supplied load adapter supports only Q4 loaded polygon faces")
        speeds[domain_id] = (V1 - V0) / (x1 - x0)

    # Validate geometric domain identity at all FE-internal longitudinal Gauss points
    xs = [float(0.5*(a+b)+0.5*(b-a)*xi) for a,b in zip(starts, ends) for xi in xa]
    domain_lookup = stress_tool.validate_checkpoint_domain_lookups(field, bridge.field, xs)
    if any(v is None for v in domain_lookup.values()):
        raise ValueError("The supplied checkpoint lacks the required resolved domain identities")

    results = {}
    zero = lambda: np.zeros(3, dtype=float)
    for domain_id, edge, pz, side in faces:
        name = f"domain_{domain_id}_{side}_edge_{edge}"
        results[name] = {
            "domain_id": int(domain_id), "edge": int(edge), "side": str(side),
            "pressure_per_projected_area_MPa": float(pz),
            "Fstress": zero(), "Fload": zero(), "Mstress": zero(), "Mload": zero(),
            "area": 0., "samples": 0, "point_sq": 0., "ref_sq": 0.,
        }

    for a, b in zip(starts, ends):
        xm, xh = 0.5*(a+b), 0.5*(b-a)
        for ga, gw in zip(xa, wa):
            x = float(xm+xh*ga)
            jac_x = float(xh*gw)
            lookup = domain_lookup[x]
            for domain_id, edge, pz, side in faces:
                row = results[f"domain_{domain_id}_{side}_edge_{edge}"]
                V = np.asarray(provider.domain(x, domain_id).vertices, dtype=float)
                if V.shape != (4, 2) or not np.isfinite(V).all():
                    raise ValueError(f"Invalid loaded CSF polygon at x={x}, domain={domain_id}")
                j = (edge + 1) % 4
                pa, pb = V[edge], V[j]
                pt = 0.5*(pb-pa)
                v = speeds[domain_id]
                for t, w_edge in zip(ta, wt):
                    yz = 0.5*((1.0-t)*pa+(1.0+t)*pb)
                    px = 0.5*((1.0-t)*v[edge]+(1.0+t)*v[j])
                    # Same 'normal_area' formula, orientation, and projected-
                    # area sign as vertical_face_tractions.build_load_vector.
                    normal_area = np.array([
                        pt[0]*px[1]-pt[1]*px[0], pt[1], -pt[0]
                    ], dtype=float)
                    magnitude = float(np.linalg.norm(normal_area))
                    if not np.isfinite(magnitude) or magnitude <= 0:
                        raise ValueError("Degenerate loaded-face surface Jacobian")
                    _, _, sigma = stress_tool._evaluate_cuf_state(
                        field, bridge.constitutive_provider, lookup, domain_id,
                        x, float(yz[0]), float(yz[1])
                    )
                    dF_sigma = (_stress_matrix(sigma) @ normal_area) * jac_x * float(w_edge)
                    dF_load = np.array([0.0,0.0,float(pz)*abs(normal_area[2])]) * jac_x * float(w_edge)
                    arm = np.array([x-x0, float(yz[0]), float(yz[1])])
                    row["Fstress"] += dF_sigma
                    row["Fload"] += dF_load
                    row["Mstress"] += np.cross(arm, dF_sigma)
                    row["Mload"] += np.cross(arm, dF_load)
                    weight = jac_x * float(w_edge)
                    row["area"] += magnitude*weight
                    row["samples"] += 1
                    # A separate L2 traction measure avoids concealing
                    # pointwise mismatches due to cancellation of resultants.
                    delta_area = (_stress_matrix(sigma) @ normal_area -
                                  np.array([0.0,0.0,float(pz)*abs(normal_area[2])]))
                    row["point_sq"] += float(np.dot(delta_area,delta_area)/magnitude)*weight
                    row["ref_sq"] += float((pz*abs(normal_area[2]))**2/magnitude)*weight

    all_Fs, all_Fl, all_Ms, all_Ml = (zero(), zero(), zero(), zero())
    area_total, n_total, point_total, ref_total = 0.,0,0.,0.
    rows = []
    for key, record in results.items():
        all_Fs += record["Fstress"]
        all_Fl += record["Fload"]
        all_Ms += record["Mstress"]
        all_Ml += record["Mload"]
        area_total += record["area"]
        n_total += record["samples"]
        point_total += record["point_sq"]
        ref_total += record["ref_sq"]
        rows.append({
            "surface": key,
            "domain_id": record["domain_id"],
            "side": record["side"],
            "pressure_per_projected_area_MPa": record["pressure_per_projected_area_MPa"],
            **_result_dict(record["Fstress"], record["Fload"], record["Mstress"], record["Mload"],
                           record["area"], record["samples"], record["point_sq"], record["ref_sq"])
        })
    total = _result_dict(all_Fs, all_Fl, all_Ms, all_Ml,
                         area_total, n_total, point_total, ref_total)
    return {
        "case": str(case.name),
        "checkpoint": str(npz_path),
        "stress_source": str(stress_path),
        "model": str(problem.model_path),
        "load_adapter": str(load_path),
        "manifest": str(manifest_path),
        "input_sha256": {
            "checkpoint": _sha(npz_path), "case": _sha(case.path),
            "problem": _sha(case.problem_path), "model": _sha(problem.model_path),
            "adapter": _sha(load_path), "stress_script": _sha(stress_path),
        },
        "gauss": {"axial_per_cuf_element": qa, "edge": qt, "CUF_elements": len(starts)},
        "reference_origin_mm": [float(x0),0.0,0.0],
        "face_results": rows,
        "total": total,
        "notes": [
            "All stress tractions evaluated at the original exterior loaded CSF face; never at transverse sections or offsets.",
            "Face normal-area vector follows exactly vertical_face_tractions.py's geometry convention.",
            "Recovered stress is C@strain from the supplied plotting tool (mathematical domain side selected).",
            "Prescribed t=(0,0,p_z*abs(n_z)); p_z is per projected XY area, not per physical area.",
            "Traction boundary conditions are imposed weakly in CUF; strong surface traction equality is not guaranteed."
        ]
    }


def _save(data, path: Path):
    path.mkdir(parents=True, exist_ok=False)
    json_path = path / "loaded_surface_traction_audit.json"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    csv_path = path / "loaded_surface_traction_audit.csv"
    columns = ["surface","domain_id","side","pressure_per_projected_area_MPa"]
    for prefix in ("F_load_N", "F_stress_N", "F_difference_N", "M_load_about_x0_Nmm", "M_stress_about_x0_Nmm", "M_difference_Nmm"):
        columns.extend(f"{prefix}_{c}" for c in "xyz")
    columns += ["relative_force_resultant_percent","relative_moment_resultant_percent", "relative_traction_L2_percent","loaded_surface_area_mm2","sample_count"]
    def flatten(row):
        obj={k:row[k] for k in columns[:4]}
        keymap=[("F_load_N","F_load_N"),( "F_stress_N","F_stress_N"),("F_difference_N","F_difference_N"),
                ("M_load_about_x0_Nmm","M_load_about_x0_Nmm"),("M_stress_about_x0_Nmm","M_stress_about_x0_Nmm"),("M_difference_Nmm","M_difference_Nmm")]
        for p,k in keymap:
            for c,v in zip("xyz",row[k]):obj[f"{p}_{c}"]=v
        for k in columns[-5:]:obj[k]=row[k]
        return obj
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer=csv.DictWriter(fp,fieldnames=columns)
        writer.writeheader()
        for row in data["face_results"]:
            writer.writerow(flatten(row))
    total=data["total"]
    readme = (
        f"# CUF loaded-face traction audit: {data['case']}\n\n"
        "Checks surface-traction resultant integrated **on the originally loaded exterior faces**, "
        "not sectional forces on x=const cuts.\n\n"
        f"CUF field: `{data['checkpoint']}`  \n"
        f"Recovered stress source: `{data['stress_source']}`  \n"
        f"Quadrature: {data['gauss']['axial_per_cuf_element']} Gauss points per CUF FE, "
        f"{data['gauss']['edge']} across each loaded edge.\n\n"
        "| Component | Prescribed load | Recovered CUF stress | Difference |\n"
        "|---|---:|---:|---:|\n"
    )
    for group,label,unit in (("F","Force","N"),("M","Moment","N mm")):
        keys=(("F_load_N","F_stress_N","F_difference_N") if group=="F" else
              ("M_load_about_x0_Nmm","M_stress_about_x0_Nmm","M_difference_Nmm"))
        for idx,c in enumerate("xyz"):
            readme += (f"| {label} {c} ({unit}) | {total[keys[0]][idx]:.9g} | "
                       f"{total[keys[1]][idx]:.9g} | {total[keys[2]][idx]:.9g} |\n")
    readme += (
        f"\nForce resultant discrepancy / |F prescribed|: "
        f"{total['relative_force_resultant_percent']:.8g}%  \n"
        f"Local traction L2 discrepancy: {total['relative_traction_L2_percent']:.8g}%\n\n"
        "The local traction L2 discrepancy is **not** the same as the error in the total resultant. "
        "Surface traction recovered from a displacement-based CUF solution does not necessarily "
        "satisfy the natural boundary condition pointwise.\n\n"
        "See `loaded_surface_traction_audit.csv` for results on each loaded face "
        "and `loaded_surface_traction_audit.json` for full metadata and provenance.\n"
    )
    (path / "README.md").write_text(readme, encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case", required=True, type=Path, help="CUF YAML case from this project")
    p.add_argument("--npz", type=Path, help="Override CUF checkpoint file")
    p.add_argument("--stress-script", type=Path, help="plot_strain_stress_boundary_v10.py path")
    p.add_argument("--axial-gauss", type=int, help="Gauss points per longitudinal CUF element (default: load adapter)")
    p.add_argument("--edge-gauss", type=int, help="Gauss points across loaded face edge (default: load adapter)")
    p.add_argument("--output-dir", type=Path, help="Explicit new output directory; never overwritten")
    args = p.parse_args()
    case = args.case.resolve()
    if not case.is_file():
        p.error(f"Case not found: {case}")
    data = _run(case, args.npz, args.stress_script, args.axial_gauss, args.edge_gauss)
    if args.output_dir:
        out = args.output_dir.resolve()
        if out.exists():
            raise FileExistsError(f"Output exists; refusing to overwrite: {out}")
    else:
        root = case.parent.parent.parent
        base = root / "diagnostics/cuf_loaded_surface_traction" / data["case"]
        base.mkdir(parents=True, exist_ok=True)
        for index in range(1, 10000):
            out = base / f"run_{index:04d}"
            if not out.exists():
                break
        else:
            raise RuntimeError("No free output run number")
    _save(data, out)
    total=data["total"]
    print(f"[CUF loaded-surface traction] case: {data['case']}")
    print(f"  prescribed F[N]        {total['F_load_N']}")
    print(f"  CUF sigma*n F[N]       {total['F_stress_N']}")
    print(f"  difference F[N]        {total['F_difference_N']}")
    print(f"  resultant difference   {total['relative_force_resultant_percent']:.8g}%")
    print(f"  local traction L2      {total['relative_traction_L2_percent']:.8g}%")
    print(f"  results: {out}")

if __name__ == "__main__":
    main()
