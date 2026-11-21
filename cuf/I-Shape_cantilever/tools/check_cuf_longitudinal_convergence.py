#!/usr/bin/env python3
"""Independent CSF-CUF longitudinal h/p stabilization from solved CUF outputs.

The script NEVER solves the problem or uses FEM3D. It consumes CUF's existing
response_eq1.txt and checkpoint NPZ files, verifies their step-manifest hashes,
and compares successive CUF displacements at the same physical probe.

Geometry, materials and constitutive data are not reconstructed or interpolated.
The optional case input is read *only* to verify numerical configuration and
provenance: it is not used to evaluate any CSF physical quantity.

Example (from cuf/I-Shape_cantilever):
  python tools/check_cuf_longitudinal_convergence.py \\
      --input output/cuf_convergence --cases cases --tolerance-pct 0.5

Example (on the archived inputs):
  python tools/check_cuf_longitudinal_convergence.py \\
      --input cuf_convergence.zip --cases 'cases(1).zip' --tolerance-pct 0.5
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


SERIES = {"h_v02": "convergence_h_v02", "p_v02": "convergence_p_v02"}
SOURCE_ENTRY = re.compile(r"(?:^|/)(h_v02|p_v02)/(step_(\d+))/step_manifest\.json$")
NEEDED_INPUTS = ("csf_model_yaml", "problem_yaml", "load_adapter", "constraint_adapter")


class Source:
    """Read archive entries or directory files without extracting user inputs."""

    def __init__(self, path: Path):
        self.path = path.resolve()
        self.zip = zipfile.ZipFile(self.path) if self.path.is_file() and zipfile.is_zipfile(self.path) else None
        if self.zip is None and not self.path.is_dir():
            raise FileNotFoundError(f"Input does not exist or is not a ZIP/directory: {self.path}")
        if self.zip:
            self.names = sorted(n for n in self.zip.namelist() if not n.endswith("/"))
        else:
            self.names = sorted(str(x.relative_to(self.path)).replace("\\", "/")
                                for x in self.path.rglob("*") if x.is_file())
        self.name_set = set(self.names)

    def read(self, name: str) -> bytes:
        if name not in self.name_set:
            raise FileNotFoundError(f"Missing input {name} inside {self.path}")
        return self.zip.read(name) if self.zip else (self.path / name).read_bytes()

    def find_suffix(self, suffix: str) -> str:
        hits = [n for n in self.names if n == suffix or n.endswith("/" + suffix)]
        if len(hits) != 1:
            raise ValueError(f"Expected one '{suffix}' in {self.path}; found {len(hits)}")
        return hits[0]

    def close(self) -> None:
        if self.zip:
            self.zip.close()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_probe(response: str, point: tuple[float, float, float]) -> dict[str, float]:
    """Read a *reported* CUF displacement; do not reconstruct its geometry."""
    matches = []
    for line in response.splitlines():
        parts = line.split()
        if len(parts) != 8:
            continue
        try:
            fraction, x, y, z = (float(v) for v in parts[:4])
            ux, uy, uz = (float(v) for v in parts[5:8])
        except ValueError:
            continue
        if not np.all(np.isfinite([fraction, x, y, z, ux, uy, uz])):
            raise ValueError(f"Nonfinite response entry: {line}")
        if all(abs(given - requested) <= 1e-6 for given, requested in zip((x, y, z), point)):
            matches.append({"x_L": fraction, "x_mm": x, "y_mm": y, "z_mm": z,
                            "point_name": parts[4], "ux_mm": ux, "uy_mm": uy, "uz_mm": uz})
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one CUF station response at {point}; got {len(matches)}")
    return matches[0]


def verify_checkpoint(blob: bytes, count: int, order: int, name: str) -> None:
    """Validate saved CUF solution structure (without evaluating the field)."""
    with np.load(io.BytesIO(blob), allow_pickle=False) as npz:
        required = ("element_x_starts", "element_x_ends", "solved_nodal_domain_natural_coefficients")
        missing = [key for key in required if key not in npz]
        if missing:
            raise ValueError(f"Checkpoint {name} is missing {missing}")
        begins = np.asarray(npz["element_x_starts"], dtype=float)
        ends = np.asarray(npz["element_x_ends"], dtype=float)
        solved = npz["solved_nodal_domain_natural_coefficients"]
        if begins.shape != (count,) or ends.shape != (count,):
            raise ValueError(f"Checkpoint {name}: longitudinal element count mismatch")
        if solved.ndim < 2 or solved.shape[0] != count or solved.shape[1] != order + 1:
            raise ValueError(f"Checkpoint {name}: saved solution order/element count mismatch")
        if not (np.isfinite(begins).all() and np.isfinite(ends).all()
                and np.all(ends > begins) and np.allclose(begins[1:], ends[:-1], atol=1e-8, rtol=0)):
            raise ValueError(f"Checkpoint {name}: invalid longitudinal element bounds")


def verify_numerical_case(case: dict[str, Any], count: int, order: int, name: str) -> dict[str, Any]:
    cuf = case.get("cuf", {})
    longi = case.get("longitudinal", {})
    sect = case.get("section_integration", {})
    basis = str(cuf.get("basis", ""))
    if basis != "lagrangeL9" or int(cuf.get("order", -1)) != 2:
        raise ValueError(f"{name}: transverse basis/order is not the fixed quadratic lagrangeL9")
    if (str(longi.get("basis", "")) != "lagrange" or
            int(longi.get("elements", -1)) != count or int(longi.get("order", -1)) != order):
        raise ValueError(f"{name}: case longitudinal elements/order differ from manifest")
    return {"transverse_basis": basis, "transverse_order": 2,
            "transverse_options": cuf.get("basis_options", {}),
            "longitudinal_basis": longi.get("basis"),
            "longitudinal_gauss_order": longi.get("gauss_order"),
            "section_method": sect.get("method"),
            "section_gauss_order": sect.get("gauss_order"),
            "mitc_correction": case.get("solver", {}).get("correctionMITC")}


@dataclass
class Record:
    series: str
    step: int
    n: int
    p: int
    case: str
    response: dict[str, float]
    checkpoint_sha: str
    response_sha: str
    input_shas: dict[str, str]
    step_case_sha: str
    numeric_settings: dict[str, Any] | None
    delta_pct: float | None = None
    passes_pair: bool = False


def collect(source: Source, case_source: Source | None, point: tuple[float, float, float]) -> list[Record]:
    try:
        import yaml  # YAML used only for case *numerical* configuration, not CSF physics.
    except ImportError:
        if case_source is not None:
            raise RuntimeError("PyYAML is required to validate the provided case configurations")
        yaml = None

    seen: dict[str, list[tuple[int, str]]] = {k: [] for k in SERIES}
    for name in source.names:
        match = SOURCE_ENTRY.search(name)
        if match:
            series, _, step = match.groups()
            seen[series].append((int(step), name))
    records: list[Record] = []
    for series in SERIES:
        steps = sorted(seen[series])
        if len(steps) < 3:
            raise ValueError(f"{series}: need at least three solved CUF steps; got {len(steps)}")
        if [s for s, _ in steps] != list(range(1, len(steps)+1)):
            raise ValueError(f"{series}: step IDs are missing or duplicated")
        for step, manifest_name in steps:
            manifest_blob = source.read(manifest_name)
            man = json.loads(manifest_blob)
            if man.get("status") != "completed":
                raise ValueError(f"{manifest_name}: study not marked completed")
            prefix = manifest_name.removesuffix("step_manifest.json")
            resp_name = prefix + "response_eq1.txt"
            response_blob = source.read(resp_name)
            if sha(response_blob) != man.get("response_sha256"):
                raise ValueError(f"{resp_name}: SHA-256 does not match manifest")
            checkpoints = [n for n in source.names if n.startswith(prefix) and n.endswith(".npz")]
            if len(checkpoints) != 1:
                raise ValueError(f"{prefix}: expected one solved checkpoint NPZ; got {len(checkpoints)}")
            checkpoint_blob = source.read(checkpoints[0])
            if sha(checkpoint_blob) != man.get("checkpoint_sha256"):
                raise ValueError(f"{checkpoints[0]}: SHA-256 does not match manifest")
            n, p = int(man["elements"]), int(man["order"])
            verify_checkpoint(checkpoint_blob, n, p, checkpoints[0])
            probe = parse_probe(response_blob.decode("utf-8"), point)
            hashes = {key: str(man["inputs"][key]["sha256"]) for key in NEEDED_INPUTS}
            step_case_sha = str(man["inputs"]["step_case"]["sha256"])
            settings = None
            if case_source is not None:
                case_name = case_source.find_suffix(f"{SERIES[series]}/step_{step:03d}.yaml")
                case_blob = case_source.read(case_name)
                if sha(case_blob) != step_case_sha:
                    raise ValueError(f"{case_name}: numerical case SHA-256 does not match manifest")
                config = yaml.safe_load(case_blob)
                settings = verify_numerical_case(config, n, p, case_name)
                if config.get("case", {}).get("name") != man.get("case_name"):
                    raise ValueError(f"{case_name}: case identifier differs from manifest")
            records.append(Record(series=series, step=step, n=n, p=p, case=str(man["case_name"]),
                                  response=probe, checkpoint_sha=str(man["checkpoint_sha256"]),
                                  response_sha=str(man["response_sha256"]), input_shas=hashes,
                                  step_case_sha=step_case_sha, numeric_settings=settings))
    for key in NEEDED_INPUTS:
        if len({r.input_shas[key] for r in records}) != 1:
            raise ValueError(f"Input provenance differs among runs: {key}")
    if case_source is not None:
        checked = [r.numeric_settings for r in records]
        if len({json.dumps(s, sort_keys=True) for s in checked}) != 1:
            raise ValueError("Numerical settings other than longitudinal N/p changed among runs")
    h = [r for r in records if r.series == "h_v02"]
    p = [r for r in records if r.series == "p_v02"]
    if len({r.p for r in h}) != 1 or len({r.n for r in p}) != 1:
        raise ValueError("Not an independent h- and p-study: fixed parameters vary")
    if not all(b.n > a.n for a, b in zip(h, h[1:])):
        raise ValueError("h-series longitudinal element counts are not strictly increasing")
    if not all(b.p > a.p for a, b in zip(p, p[1:])):
        raise ValueError("p-series longitudinal orders are not strictly increasing")
    for r in records:
        seq = h if r.series == "h_v02" else p
        if r.step == 1:
            continue
        before = seq[r.step - 2].response["uz_mm"]
        current = r.response["uz_mm"]
        if current == 0.0:
            raise ValueError(f"Zero denominator for relative change at {r.case}")
        r.delta_pct = 100.0 * abs(current - before) / abs(current)
    common = {(r.n, r.p): r for r in h}
    for r in p:
        match = common.get((r.n, r.p))
        if match is not None and not math.isclose(match.response["uz_mm"], r.response["uz_mm"], abs_tol=1e-9):
            raise ValueError(f"Shared h/p setting ({r.n},{r.p}) has inconsistent displacement")
    return records


def first_stable(rows: list[Record], threshold: float) -> Record | None:
    for index in range(2, len(rows)):
        a, b = rows[index-1], rows[index]
        if a.delta_pct is not None and b.delta_pct is not None and a.delta_pct <= threshold and b.delta_pct <= threshold:
            return b
    return None


def csv_output(rows: list[Record], path: Path, threshold: float) -> None:
    columns = ["step", "N", "p", "case", "uz_P_mm", "delta_pct", "two_successive_below_threshold",
               "ux_P_mm", "uy_P_mm", "x_L", "x_mm", "y_mm", "z_mm", "checkpoint_sha256"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for index, rec in enumerate(rows):
            yes = (index >= 2 and rows[index-1].delta_pct is not None and rec.delta_pct is not None
                   and rows[index-1].delta_pct <= threshold and rec.delta_pct <= threshold)
            rec.passes_pair = bool(yes)
            writer.writerow({"step": rec.step, "N": rec.n, "p": rec.p, "case": rec.case,
                             "uz_P_mm": f'{rec.response["uz_mm"]:.12g}',
                             "delta_pct": "" if rec.delta_pct is None else f"{rec.delta_pct:.12g}",
                             "two_successive_below_threshold": "yes" if yes else "no",
                             "ux_P_mm": f'{rec.response["ux_mm"]:.12g}',
                             "uy_P_mm": f'{rec.response["uy_mm"]:.12g}',
                             "x_L": rec.response["x_L"], "x_mm": rec.response["x_mm"],
                             "y_mm": rec.response["y_mm"], "z_mm": rec.response["z_mm"],
                             "checkpoint_sha256": rec.checkpoint_sha})


def plot_study(rows: list[Record], param: str, threshold: float, path: Path) -> None:
    axis_values = [r.n if param == "h" else r.p for r in rows]
    q = [r.response["uz_mm"] for r in rows]
    delta = [float("nan") if r.delta_pct is None else r.delta_pct for r in rows]
    fig, axes = plt.subplots(2, 1, figsize=(9.2, 7.2), constrained_layout=True)
    x_label = "Longitudinal elements N" if param == "h" else "Longitudinal polynomial degree p"
    axes[0].plot(axis_values, q, "o-", lw=1.5)
    axes[0].set_ylabel(r"$u_z(P)$ [mm]")
    axes[0].set_xlabel(x_label)
    axes[0].set_title(f"Independent CSF-CUF longitudinal {param}-study (transverse L9 fixed)")
    axes[0].grid(alpha=0.25)
    axes[1].plot(axis_values, delta, "o-", lw=1.5, label="Successive relative change")
    axes[1].axhline(threshold, ls="--", lw=1.2, label=f"Study threshold ({threshold:g}%)")
    axes[1].set_yscale("log")
    axes[1].set_ylabel(r"$\delta_k$ [%]")
    axes[1].set_xlabel(x_label)
    axes[1].grid(alpha=0.25)
    axes[1].legend(loc="best")
    fig.savefig(path, dpi=180)
    plt.close(fig)


def markdown_report(h: list[Record], p: list[Record], point: tuple[float, float, float],
                    threshold: float, common: list[tuple[int, int]], source: Source,
                    checked_cases: bool) -> str:
    hfirst, pfirst = first_stable(h, threshold), first_stable(p, threshold)
    s = ["# CSF-CUF independent longitudinal convergence", "",
         "## Numerical study and physical model", "",
         "The transverse **L9** kinematic basis is fixed. Only the longitudinal finite-element",
         "discretization is varied, in two distinct numerical studies:", "",
         f"- **h-study:** N = {', '.join(str(r.n) for r in h)}, with p = {h[0].p} fixed.",
         f"- **p-study:** p = {', '.join(str(r.p) for r in p)}, with N = {p[0].n} fixed.", "",
         f"The monitored physical location is P = ({point[0]:g}, {point[1]:g}, {point[2]:g}) mm.",
         "The ordinate is the **CUF displacement** u_z(P), in mm.",
         "The values are read from the existing CUF station-response files; no new solve is run.",
         "No FEM3D output enters the convergence criterion.", "",
         "## Selection rule", "",
         "For successive solutions k-1 and k in the **same** series, define", "",
         r"$$\delta_k = 100\,\frac{|u_z^{(k)}(P)-u_z^{(k-1)}(P)|}{|u_z^{(k)}(P)|}\quad[\%].$$", "",
         f"The first configuration for which **two successive increments** satisfy "
         f"delta <= {threshold:g}% is flagged as *stabilized* under this study-specific rule.",
         "The displacement denominator is checked to be nonzero. This is a successive-change",
         "criterion, **not** a Grid Convergence Index (GCI) or a full-field error estimate.", "",
         "## h-study (longitudinal N-refinement)", "",
         "| N | p | u_z(P) [mm] | Successive change [%] | Two-increment rule |",
         "|---:|---:|---:|---:|:---:|"]
    for r in h:
        s.append(f'| {r.n} | {r.p} | {r.response["uz_mm"]:.11f} | '
                 f'{"--" if r.delta_pct is None else f"{r.delta_pct:.9f}"} | '
                 f'{"yes" if r.passes_pair else "no"} |')
    s += ["", f"First passing h-study setting: **{f'N={hfirst.n}, p={hfirst.p}' if hfirst else 'none'}**.",
          "", "![h convergence](convergence_h.png)", "", "## p-study (longitudinal order-refinement)", "",
          "| N | p | u_z(P) [mm] | Successive change [%] | Two-increment rule |",
          "|---:|---:|---:|---:|:---:|"]
    for r in p:
        s.append(f'| {r.n} | {r.p} | {r.response["uz_mm"]:.11f} | '
                 f'{"--" if r.delta_pct is None else f"{r.delta_pct:.9f}"} | '
                 f'{"yes" if r.passes_pair else "no"} |')
    s += ["", f"First passing p-study setting: **{f'N={pfirst.n}, p={pfirst.p}' if pfirst else 'none'}**.",
          "", "![p convergence](convergence_p.png)", "", "## Consistency and interpretation", "",
          "- The CSF model, problem, load adapter and constraint adapter SHA-256 hashes agree across both series.",
          "- The response and checkpoint SHA-256 hashes match their archived step manifests."]
    if checked_cases:
        s += ["- The 19 numerical case configurations were also checked against the step manifests.",
              "  They all use quadratic transverse `lagrangeL9`, with invariant numerical settings other than longitudinal N/p."]
    else:
        s += ["- Numerical case YAML files were not supplied; transverse L9 is identified from the study specification",
              "  but was not independently cross-checked against each YAML. Supply `--cases` to enforce that check."]
    if common:
        for n, order in common:
            r = next(r for r in h if (r.n, r.p) == (n, order))
            s += [f"- Shared solved configuration: **N={n}, p={order}**, "
                  f"u_z(P)={r.response['uz_mm']:.11f} mm (matching across h- and p-studies)."]
    s += ["", "These are **two separate one-dimensional refinement paths**. In particular, an",
          "uncomputed combination of the individual first-passing N and p values must not",
          "be described as a converged computed solution. A shared, explicitly solved",
          "configuration can be used for subsequent comparison of sectional resultants.", "",
          "## Limitations", "",
          "- The reported threshold demonstrates stabilization of this displacement probe only.",
          "- It does not establish convergence of the full displacement field or of N(x), T_z(x), M_y(x).",
          "- No CUF-FEM3D displacement differences are used as convergence evidence.",
          "- No external surface traction or surface stress-equilibrium study is performed.",
          "- Geometry and materials are neither read from physical YAML nor re-interpolated:",
          "  these are already-computed CUF displacement outputs.", "",
          "## Provenance", "",
          f"- Source of CUF solutions: `{source.path}`.",
          "- Full per-step checkpoint hashes: `h_series.csv`, `p_series.csv`.",
          "- Full input hashes and selection records: `provenance.json`.", ""]
    return "\n".join(s)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, required=True,
                        help="Existing cuf_convergence directory or its ZIP archive")
    parser.add_argument("--cases", type=Path,
                        help="Optional project cases directory or cases ZIP, used only to check L9/N/p settings")
    parser.add_argument("--output-root", type=Path, default=Path("diagnostics/cuf_longitudinal_convergence"),
                        help="Parent output directory; hashed subdirectory avoids mixing studies")
    parser.add_argument("--tolerance-pct", type=float, default=0.5,
                        help="Study-specific successive-change threshold in percent (default 0.5)")
    parser.add_argument("--point", type=float, nargs=3, metavar=("X", "Y", "Z"),
                        default=(1000., -33., 35.), help="Fixed physical CUF response point in mm")
    args = parser.parse_args()
    if not (np.isfinite(args.tolerance_pct) and 0.0 < args.tolerance_pct < 100.0):
        parser.error("--tolerance-pct must lie in (0,100)")
    point = tuple(float(x) for x in args.point)
    source = Source(args.input)
    cases = Source(args.cases) if args.cases is not None else None
    try:
        records = collect(source, cases, point)
        h = [r for r in records if r.series == "h_v02"]
        p = [r for r in records if r.series == "p_v02"]
        provenance_key = json.dumps({"checkpoint_hashes": [r.checkpoint_sha for r in records],
                                     "response_hashes": [r.response_sha for r in records],
                                     "point": point, "threshold_pct": args.tolerance_pct}, sort_keys=True)
        fingerprint = sha(provenance_key.encode())[:12]
        out = args.output_root.resolve() / fingerprint
        out.mkdir(parents=True, exist_ok=True)
        csv_output(h, out / "h_series.csv", args.tolerance_pct)
        csv_output(p, out / "p_series.csv", args.tolerance_pct)
        plot_study(h, "h", args.tolerance_pct, out / "convergence_h.png")
        plot_study(p, "p", args.tolerance_pct, out / "convergence_p.png")
        common = sorted(set((r.n, r.p) for r in h) & set((r.n, r.p) for r in p))
        (out / "CSF_CUF_longitudinal_convergence.md").write_text(
            markdown_report(h, p, point, args.tolerance_pct, common, source, cases is not None),
            encoding="utf-8")
        provenance = {"source": str(source.path), "cases_source": str(cases.path) if cases else None,
                      "threshold_pct": args.tolerance_pct, "physical_probe_mm": list(point),
                      "checkpoint_count": len(records),
                      "physical_input_sha256": {key: records[0].input_shas[key] for key in NEEDED_INPUTS},
                      "first_stable_h": ({"N": first_stable(h, args.tolerance_pct).n,
                                          "p": first_stable(h, args.tolerance_pct).p}
                                         if first_stable(h, args.tolerance_pct) else None),
                      "first_stable_p": ({"N": first_stable(p, args.tolerance_pct).n,
                                          "p": first_stable(p, args.tolerance_pct).p}
                                         if first_stable(p, args.tolerance_pct) else None),
                      "common_solved_configurations": [{"N": n, "p": order} for n, order in common],
                      "checkpoints": [{"study": r.series, "step": r.step, "N": r.n, "p": r.p,
                                       "case_name": r.case, "checkpoint_sha256": r.checkpoint_sha,
                                       "response_sha256": r.response_sha, "case_sha256": r.step_case_sha}
                                      for r in records],
                      "selection_method": "two successive CUF displacement changes below threshold; no GCI"}
        (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        print(f"[CSF-CUF] validated {len(records)} completed checkpoint/response pairs with SHA-256")
        print(f"[CSF-CUF] physical input provenance consistent across both studies")
        print(f"[CSF-CUF] numerical case validation: {'yes' if cases else 'not requested'}")
        for label, rows in (("h", h), ("p", p)):
            first = first_stable(rows, args.tolerance_pct)
            print(f"[{label}] {len(rows)} CUF solutions; first two-increment pass: "
                  + (f"N={first.n}, p={first.p}, uz(P)={first.response['uz_mm']:.11f} mm" if first else "NONE"))
        print(f"[CSF-CUF] shared solved configurations: {common}")
        print(f"[DONE] {out}")
    finally:
        source.close()
        if cases is not None:
            cases.close()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, FileNotFoundError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(2)
