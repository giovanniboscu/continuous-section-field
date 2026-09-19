#!/usr/bin/env python3
"""Build a mixed CSF-CUF compiled displacement from compatible eq solutions.

Example
-------
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq1 --uy eq1 --uz eq2

The script combines complete CUF coefficient fields component-wise, e.g.
ux <- eq1, uy <- eq1, uz <- eq2.  It does not interpolate sampled curves.
All source files must describe the same compiled displacement space.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np

COMPONENTS: Tuple[str, str, str] = ("ux", "uy", "uz")
REQUIRED_KEYS: Tuple[str, ...] = (
    "format_version",
    "metadata_json",
    "element_x_starts",
    "element_x_ends",
    "element_coefficients",
    "longitudinal_shape_coefficients",
    "transverse_power_coefficients",
)
METADATA_COMPATIBILITY_KEYS: Tuple[str, ...] = (
    "basis_class",
    "basis_name",
    "basis_order",
    "basis_size",
    "case_name",
    "components",
    "format",
    "format_version",
)


def _parse_eq(value: str) -> int:
    """Accept 0, 1, ... or eq0, eq1, ... and return the integer level."""
    text = str(value).strip().lower()
    match = re.fullmatch(r"(?:eq)?(\d+)", text)
    if not match:
        raise argparse.ArgumentTypeError(
            f"invalid equilibration level {value!r}; use e.g. 0, 1, eq0, eq1"
        )
    return int(match.group(1))


def _source_tag(sources: Mapping[str, int]) -> str:
    return "_".join(f"{component}eq{sources[component]}" for component in COMPONENTS)


def _candidate_bases(input_dir: Path, eq: int) -> set[str]:
    suffix = f"_eq{eq}.cuf.npz"
    bases: set[str] = set()
    for path in input_dir.glob(f"*{suffix}"):
        name = path.name
        bases.add(name[: -len(suffix)])
    return bases


def _resolve_case_base(input_dir: Path, sources: Mapping[str, int], requested: str | None) -> str:
    if requested:
        return requested

    unique_eq = sorted(set(sources.values()))
    intersections: set[str] | None = None
    details: List[str] = []
    for eq in unique_eq:
        bases = _candidate_bases(input_dir, eq)
        details.append(f"eq{eq}: {sorted(bases) if bases else 'none'}")
        intersections = bases if intersections is None else intersections & bases

    if not intersections:
        raise FileNotFoundError(
            "could not infer a common case base for the requested sources. "
            + "; ".join(details)
        )
    if len(intersections) > 1:
        raise RuntimeError(
            "multiple compatible case bases were found: "
            + ", ".join(sorted(intersections))
            + ". Use --case-base to select one."
        )
    return next(iter(intersections))


def _load_npz(path: Path) -> np.lib.npyio.NpzFile:
    if not path.is_file():
        raise FileNotFoundError(path)
    npz = np.load(path, allow_pickle=True)
    missing = [key for key in REQUIRED_KEYS if key not in npz.files]
    if missing:
        npz.close()
        raise ValueError(f"{path}: missing required keys: {', '.join(missing)}")
    return npz


def _metadata(npz: np.lib.npyio.NpzFile, path: Path) -> dict:
    try:
        raw = npz["metadata_json"].item()
        meta = json.loads(str(raw))
    except Exception as exc:
        raise ValueError(f"{path}: invalid metadata_json: {exc}") from exc
    if not isinstance(meta, dict):
        raise ValueError(f"{path}: metadata_json must decode to an object")
    return meta


def _same_array(a: np.ndarray, b: np.ndarray) -> bool:
    # These arrays define the compiled approximation space.  We require exact
    # identity rather than a tolerance-based geometric approximation.
    return a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a, b)


def _check_compatibility(
    loaded: Mapping[int, np.lib.npyio.NpzFile],
    paths: Mapping[int, Path],
) -> dict:
    eq_levels = sorted(loaded)
    ref_eq = eq_levels[0]
    ref = loaded[ref_eq]
    ref_path = paths[ref_eq]
    ref_meta = _metadata(ref, ref_path)

    coeff_shape = ref["element_coefficients"].shape
    if not coeff_shape or coeff_shape[-1] != len(COMPONENTS):
        raise ValueError(
            f"{ref_path}: expected element_coefficients[..., 3], got {coeff_shape}"
        )

    ref_components = ref_meta.get("components")
    if ref_components is not None and list(ref_components) != list(COMPONENTS):
        raise ValueError(
            f"{ref_path}: expected metadata components {list(COMPONENTS)}, got {ref_components}"
        )

    array_keys = (
        "element_x_starts",
        "element_x_ends",
        "longitudinal_shape_coefficients",
        "transverse_power_coefficients",
    )

    problems: List[str] = []
    for eq in eq_levels[1:]:
        cur = loaded[eq]
        cur_path = paths[eq]
        cur_meta = _metadata(cur, cur_path)

        if cur["element_coefficients"].shape != coeff_shape:
            problems.append(
                f"eq{eq}: element_coefficients shape {cur['element_coefficients'].shape} "
                f"!= {coeff_shape}"
            )

        if not _same_array(ref["format_version"], cur["format_version"]):
            problems.append(f"eq{eq}: format_version differs")

        for key in array_keys:
            if not _same_array(ref[key], cur[key]):
                problems.append(f"eq{eq}: {key} differs")

        for key in METADATA_COMPATIBILITY_KEYS:
            if ref_meta.get(key) != cur_meta.get(key):
                problems.append(
                    f"eq{eq}: metadata {key!r} differs: "
                    f"{cur_meta.get(key)!r} != {ref_meta.get(key)!r}"
                )

    if problems:
        raise ValueError(
            "source solutions are not compatible and cannot be mixed:\n  - "
            + "\n  - ".join(problems)
        )

    return ref_meta


def _build_mixed_coefficients(
    loaded: Mapping[int, np.lib.npyio.NpzFile],
    sources: Mapping[str, int],
) -> np.ndarray:
    ref = loaded[next(iter(sorted(loaded)))]
    mixed = np.empty_like(ref["element_coefficients"])
    for component_index, component in enumerate(COMPONENTS):
        eq = sources[component]
        mixed[..., component_index] = loaded[eq]["element_coefficients"][..., component_index]
    return mixed


def _write_mixed_npz(
    output_path: Path,
    ref: np.lib.npyio.NpzFile,
    ref_meta: dict,
    mixed_coefficients: np.ndarray,
    sources: Mapping[str, int],
    force: bool,
) -> None:
    if output_path.exists() and not force:
        raise FileExistsError(f"{output_path} already exists; use --force to replace it")

    meta = dict(ref_meta)
    meta.pop("equilibration_iterations", None)
    base_case_name = str(ref_meta.get("case_name", output_path.stem))
    tag = _source_tag(sources)
    meta["case_name"] = f"{base_case_name}_mix_{tag}"
    meta["component_sources"] = {component: f"eq{sources[component]}" for component in COMPONENTS}
    meta["mixed_equilibration"] = True

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        format_version=ref["format_version"],
        metadata_json=np.array(json.dumps(meta, separators=(",", ":"))),
        element_x_starts=ref["element_x_starts"],
        element_x_ends=ref["element_x_ends"],
        element_coefficients=mixed_coefficients,
        longitudinal_shape_coefficients=ref["longitudinal_shape_coefficients"],
        transverse_power_coefficients=ref["transverse_power_coefficients"],
    )


def _make_evaluator(npz: np.lib.npyio.NpzFile):
    coefficients = npz["element_coefficients"]
    longitudinal = npz["longitudinal_shape_coefficients"]
    transverse = npz["transverse_power_coefficients"]
    starts = npz["element_x_starts"]
    ends = npz["element_x_ends"]

    def evaluate_point(x: float, y: float, z: float) -> np.ndarray:
        if x == ends[-1]:
            element = len(starts) - 1
        else:
            element = int(np.searchsorted(ends, x, side="right"))
        element = max(0, min(element, len(starts) - 1))

        length = ends[element] - starts[element]
        if length == 0:
            raise ZeroDivisionError(f"element {element} has zero longitudinal length")
        xi = 2.0 * (x - starts[element]) / length - 1.0

        n_values = np.array(
            [np.polynomial.polynomial.polyval(xi, row) for row in longitudinal]
        )
        y_powers = np.array([y**i for i in range(transverse.shape[1])])
        z_powers = np.array([z**j for j in range(transverse.shape[2])])
        f_values = np.einsum("tij,i,j->t", transverse, y_powers, z_powers)
        return np.einsum(
            "n,nTc,T->c", n_values, coefficients[element], f_values
        )

    return evaluate_point


def _read_station_rows(template: Path) -> List[Tuple[float, float, float, float, str]]:
    rows: List[Tuple[float, float, float, float, str]] = []
    in_table = False
    saw_data = False

    with template.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not in_table:
                if line.lstrip().startswith("x/L") and "point" in line:
                    in_table = True
                continue

            if not line.strip():
                if saw_data:
                    break
                continue
            if line.lstrip().startswith("-"):
                continue

            parts = line.split()
            if len(parts) < 5:
                if saw_data:
                    break
                continue
            try:
                x_over_l = float(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
            except ValueError:
                if saw_data:
                    break
                continue

            point = parts[4]
            rows.append((x_over_l, x, y, z, point))
            saw_data = True

    if not rows:
        raise ValueError(f"{template}: no STATION RESPONSES rows found")
    return rows


def _write_response(
    output_path: Path,
    mixed_npz_path: Path,
    template_path: Path,
    sources: Mapping[str, int],
    force: bool,
) -> int:
    if output_path.exists() and not force:
        raise FileExistsError(f"{output_path} already exists; use --force to replace it")

    station_rows = _read_station_rows(template_path)
    with np.load(mixed_npz_path, allow_pickle=True) as mixed:
        evaluate = _make_evaluator(mixed)
        values = [evaluate(x, y, z) for _, x, y, z, _ in station_rows]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("CSF-CUF MIXED RESPONSE\n")
        handle.write("======================\n")
        handle.write(
            "component sources: "
            + ", ".join(f"{c}=eq{sources[c]}" for c in COMPONENTS)
            + "\n\n"
        )
        handle.write("STATION RESPONSES\n")
        handle.write("-----------------\n")
        handle.write(
            "x/L       x [mm]             y [mm]               z [mm]               "
            "point         ux [mm]             uy [mm]             uz [mm]\n"
        )
        for row, displacement in zip(station_rows, values):
            x_over_l, x, y, z, point = row
            handle.write(
                f"{x_over_l:5.2f}     {x: .12e}  {y: .12e}  {z: .12e}  "
                f"{point:<12s}  {displacement[0]: .12e}  "
                f"{displacement[1]: .12e}  {displacement[2]: .12e}\n"
            )
    return len(station_rows)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build one mixed CSF-CUF .cuf.npz by taking ux, uy and uz from "
            "different equilibration solutions of the same case."
        )
    )
    parser.add_argument("--input-dir", required=True, type=Path, help="directory containing *_eqN.cuf.npz files")
    parser.add_argument("--ux", required=True, type=_parse_eq, help="source for ux, e.g. eq1 or 1")
    parser.add_argument("--uy", required=True, type=_parse_eq, help="source for uy, e.g. eq1 or 1")
    parser.add_argument("--uz", required=True, type=_parse_eq, help="source for uz, e.g. eq2 or 2")
    parser.add_argument(
        "--case-base",
        help=(
            "file base before _eqN.cuf.npz; normally inferred automatically. "
            "Use this when input-dir contains multiple matching cases."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="output directory; default: input-dir",
    )
    parser.add_argument(
        "--response-template",
        type=Path,
        help=(
            "response file whose STATION RESPONSES coordinates are reused. "
            "If omitted, input-dir/response.txt is used when present."
        ),
    )
    parser.add_argument(
        "--no-response",
        action="store_true",
        help="do not generate response_mix_*.txt even if a template is available",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace existing mixed output files",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    input_dir = args.input_dir.resolve()
    if not input_dir.is_dir():
        raise NotADirectoryError(input_dir)
    output_dir = (args.output_dir or input_dir).resolve()

    sources: Dict[str, int] = {"ux": args.ux, "uy": args.uy, "uz": args.uz}
    case_base = _resolve_case_base(input_dir, sources, args.case_base)

    unique_eq = sorted(set(sources.values()))
    paths: Dict[int, Path] = {
        eq: input_dir / f"{case_base}_eq{eq}.cuf.npz" for eq in unique_eq
    }
    loaded: Dict[int, np.lib.npyio.NpzFile] = {}

    try:
        for eq, path in paths.items():
            loaded[eq] = _load_npz(path)

        ref_meta = _check_compatibility(loaded, paths)
        mixed_coefficients = _build_mixed_coefficients(loaded, sources)

        tag = _source_tag(sources)
        mixed_npz_path = output_dir / f"{case_base}_mix_{tag}.cuf.npz"
        ref_eq = unique_eq[0]
        _write_mixed_npz(
            mixed_npz_path,
            loaded[ref_eq],
            ref_meta,
            mixed_coefficients,
            sources,
            args.force,
        )

        response_path: Path | None = None
        station_count: int | None = None
        if not args.no_response:
            template = args.response_template
            if template is None:
                automatic = input_dir / "response.txt"
                if automatic.is_file():
                    template = automatic
            if template is not None:
                template = template.resolve()
                if not template.is_file():
                    raise FileNotFoundError(template)
                response_path = output_dir / f"response_mix_{tag}.txt"
                station_count = _write_response(
                    response_path,
                    mixed_npz_path,
                    template,
                    sources,
                    args.force,
                )

        print("Compatibility checks: PASS")
        print(f"case base: {case_base}")
        print(
            "component sources: "
            + ", ".join(f"{c}=eq{sources[c]}" for c in COMPONENTS)
        )
        for eq in unique_eq:
            print(f"source eq{eq}: {paths[eq]}")
        print(f"mixed npz: {mixed_npz_path}")
        if response_path is not None:
            print(f"mixed response: {response_path} ({station_count} stations)")
        elif not args.no_response:
            print("mixed response: not generated (no response template found)")
        return 0

    finally:
        for npz in loaded.values():
            npz.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
