# v7 - Sample moving CSF polygon vertices from generic compiled CUF fields.
# Usage (run with CSF installed):
# python plot_cuf_outputs_v7.py --csf-yaml MODEL.yaml --checkpoint RESULT.cuf.npz
# Or scan a series: --csf-yaml MODEL.yaml --cuf-output-root output
# Outputs: per-component figures and sampled_vertices[_eqN].npz in CUF axes.
# Optional FEM3D overlay: --fem3d PATH_TO_FULL_FIELD.fem.npz
# Keep fem3d_field.py beside this plotter or available on PYTHONPATH.
# Vertex IDs preserve zero-based CSF vertex indices.
# Default: merge coincident vertices; --vertices all retains every API vertex.

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from csf.io.csf_reader import CSFReader
from csf.io.csf_issues import CSFIssues
from csf.cuf.solver.compiled_field import CompiledDisplacementField


POINT_ORDER: tuple[str, ...] = ()
COMPONENTS = ("ux", "uy", "uz")

@dataclass(frozen=True)
class DiscoveredCase:
    response: Path
    directory_name: str
    label: str
    equilibration_iterations: int | None = None

    @property
    def key(self) -> str:
        return f"{self.directory_name}/{self.response.name}"

    @property
    def title(self) -> str:
        base = self.label.replace("_", " ")
        if self.equilibration_iterations is None:
            return base
        return f"{base} - equilibration={self.equilibration_iterations}"

    @property
    def cuf_label(self) -> str:
        order_match = re.search(r"(?:^|[_-])N(\d+)(?:$|[_-])", self.label, re.IGNORECASE)
        base = f"CUF N={int(order_match.group(1))}" if order_match else "CUF"
        if self.equilibration_iterations is None:
            return base
        return f"{base}, eq={self.equilibration_iterations}"

    @property
    def plot_suffix(self) -> str:
        if self.equilibration_iterations is None:
            return ""
        return f"_eq{self.equilibration_iterations}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sample compiled CUF fields at moving polygon vertices using CSF APIs."
        )
    )
    parser.add_argument(
        "--cuf-output-root",
        type=Path,
        default=Path("../output"),
        help="CUF output tree to scan recursively (default: ../output).",
    )
    parser.add_argument(
        "--fem3d",
        type=Path,
        default=None,
        help=(
            "Optional explicit FEM3D directory or full .fem.npz displacement field. "
            "The same reference is compared with every selected CUF checkpoint."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("plots_cuf"),
        help="Directory in which plot folders are written (default: plots_cuf).",
    )
    parser.add_argument(
        "--component",
        choices=("all", "ux", "uy", "uz"),
        default="all",
        help="Displacement component to plot (default: all).",
    )
    parser.add_argument(
        "--scale-mode",
        choices=("human", "local"),
        default="human",
        help=(
            "Y-axis policy. 'human' includes zero in each panel; 'local' zooms "
            "each panel independently. Default: human."
        ),
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also write a PDF copy of every figure.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=220,
        help="PNG resolution in dots per inch (default: 220).",
    )
    parser.add_argument("--csf-yaml", type=Path, required=True, help="CSF model YAML, read exactly once")
    parser.add_argument("--checkpoint", type=Path, help="One .cuf.npz instead of a recursive series scan")
    parser.add_argument("--samples", type=int, default=201, help="Longitudinal stations, including both ends (default: 201)")
    parser.add_argument("--vertices", choices=("unique", "all"), default="unique")
    return parser.parse_args()


def discover_cases(cuf_output_root: Path, checkpoint: Path | None = None) -> list[DiscoveredCase]:
    """Discover any compiled CUF checkpoint without interpreting the case name."""
    paths = [checkpoint.resolve()] if checkpoint else sorted(cuf_output_root.resolve().rglob("*.cuf.npz"))
    cases = []
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)

        stem = path.name.removesuffix(".cuf.npz")
        eq = re.search(r"_eq(\d+)$", stem, re.IGNORECASE)
        label = stem[:eq.start()] if eq else stem
        directory_name = label

        cases.append(DiscoveredCase(
            response=path.resolve(),
            directory_name=directory_name,
            label=label,
            equilibration_iterations=int(eq.group(1)) if eq else None,
        ))

    cases.sort(key=lambda c: (c.directory_name,
                              -1 if c.equilibration_iterations is None else c.equilibration_iterations,
                              c.response.name))
    if not cases:
        raise FileNotFoundError(f"No .cuf.npz checkpoints found below {cuf_output_root}")
    return cases


def unique_vertices(section):
    """Keep one API identity per physical point; record coincident aliases."""
    selectors, aliases = [], {}
    for pi, polygon in enumerate(section.polygons):
        for vi, vertex in enumerate(polygon.vertices):
            identity = (pi, vi)
            for previous in selectors:
                pp, pv = previous
                other = section.polygons[pp].vertices[pv]
                if np.allclose([vertex.x, vertex.y], [other.x, other.y], rtol=0, atol=1e-8):
                    aliases[previous].append(identity)
                    break
            else:
                selectors.append(identity)
                aliases[identity] = [identity]
    return selectors, aliases


def sample_geometry(field, samples: int, mode: str):
    """Ask CSF for each section once; retain homologous polygon/vertex indices."""
    start, end = float(field.s0.z), float(field.s1.z)
    if end <= start:
        raise ValueError("CSF longitudinal end must exceed its start")
    stations = np.linspace(start, end, samples)
    sections = [field.section(float(x)) for x in stations]
    first = sections[0]
    if mode == "unique":
        selectors, aliases = unique_vertices(first)
        if not selectors:
            raise ValueError("No section vertices found")
    else:
        selectors = [(pi, vi) for pi, polygon in enumerate(first.polygons) for vi in range(len(polygon.vertices))]
        aliases = {identity: [identity] for identity in selectors}
    ids = tuple(f"polygon_{pi+1}_vertex_{vi}" for pi, vi in selectors)
    geometry = []
    for x, section in zip(stations, sections):
        if len(section.polygons) != len(first.polygons) or any(
            len(p.vertices) != len(q.vertices) for p, q in zip(section.polygons, first.polygons)
        ):
            raise ValueError("Section topology changed: vertex identities cannot be followed")
        if mode == "unique":
            current, current_aliases = unique_vertices(section)
            if current != selectors or current_aliases != aliases:
                raise ValueError("Coincident vertex identities change along the beam; use --vertices all")
        for point, (pi, vi) in zip(ids, selectors):
            vertex = section.polygons[pi].vertices[vi]
            geometry.append({"x_over_L": float((x-start)/(end-start)),
                "point": point, "polygon_index": pi+1, "vertex_index": vi,
                "polygon_name": first.polygons[pi].name,
                "vertex_aliases": ";".join(f"polygon_{pp+1}_vertex_{pv}" for pp, pv in aliases[(pi, vi)]),
                "x": float(x), "y_mm": float(vertex.x), "z_mm": float(vertex.y)})
    print("Moving vertices (CSF polygon and vertex indices): " + ", ".join(ids))
    return ids, geometry, start, end


def evaluate_case(case, geometry, start, end):
    """Evaluate u_CUF(Z, X, Y); returned components remain (ux, uy, uz)."""
    field = CompiledDisplacementField.load(case.response)
    if not np.allclose([field.x_start, field.x_end], [start, end], rtol=0, atol=1e-8):
        raise ValueError(f"CUF/CSF longitudinal domain mismatch: {case.response}")
    rows = []
    for station in geometry:
        displacement = np.asarray(field(station["x"], station["y_mm"], station["z_mm"]), dtype=float)
        if displacement.shape != (3,) or not np.all(np.isfinite(displacement)):
            raise ValueError(f"Invalid displacement at {station}")
        row = dict(station)
        row.update({f"{c}_cuf_mm": float(v) for c, v in zip(COMPONENTS, displacement)})
        rows.append(row)
    return rows


def add_fem_reference(rows, field):
    """Evaluate the native H8 field at the exact moving CUF/CSF points."""
    for row in rows:
        components = field(row["x"], row["y_mm"], row["z_mm"])
        row.update({f"{c}_fem3d_mm": float(v) for c, v in zip(COMPONENTS, components)})


def _explicit_fem3d_file(path: Path | None) -> Path | None:
    if path is None:
        return None
    resolved = path.resolve()
    if resolved.is_dir():
        resolved = resolved / "fem3d_displacement.fem.npz"
    if not resolved.is_file():
        raise FileNotFoundError(f"FEM3D checkpoint not found: {resolved}")
    if not resolved.name.endswith(".npz"):
        raise ValueError("FEM3D comparison requires a full .fem.npz field")
    return resolved


def select_rows(rows: list[dict[str, float | str]], point: str):
    selected = [row for row in rows if row["point"] == point]
    return sorted(selected, key=lambda row: float(row["x_over_L"]))


def point_coordinate_label(rows: list[dict[str, float | str]]) -> str:
    first = rows[0]
    last = rows[-1]

    y0 = float(first["y_mm"])
    z0 = float(first["z_mm"])
    y1 = float(last["y_mm"])
    z1 = float(last["z_mm"])

    if np.allclose((y0, z0), (y1, z1), rtol=0.0, atol=1.0e-12):
        return f"y,z = ({y0:g}, {z0:g}) mm"

    return f"y,z: ({y0:g}, {z0:g}) -> ({y1:g}, {z1:g}) mm"


def local_limits(values: list[np.ndarray], pad_fraction: float = 0.08):
    """Per-panel zoom retained for diagnostics of small residual components."""
    merged = np.concatenate(values)
    finite = merged[np.isfinite(merged)]

    if finite.size == 0:
        return -1.0, 1.0

    lo = float(np.min(finite))
    hi = float(np.max(finite))

    if np.isclose(lo, hi):
        scale = max(abs(lo), 1.0e-6)
        pad = 0.05 * scale
    else:
        pad = pad_fraction * (hi - lo)

    return lo - pad, hi + pad


def human_limits(values: list[np.ndarray], pad_fraction: float = 0.08):
    """Build a common physical y-scale that includes zero and all supplied values."""
    if not values:
        return -1.0e-6, 1.0e-6

    merged = np.concatenate(values)
    finite = merged[np.isfinite(merged)]
    if finite.size == 0:
        return -1.0e-6, 1.0e-6

    lo = min(float(np.min(finite)), 0.0)
    hi = max(float(np.max(finite)), 0.0)

    if np.isclose(lo, 0.0) and np.isclose(hi, 0.0):
        return -1.0e-6, 1.0e-6

    span = hi - lo
    pad = pad_fraction * span if span > 0.0 else 0.0

    plot_lo = lo - pad if lo < 0.0 else 0.0
    plot_hi = hi + pad if hi > 0.0 else 0.0

    if np.isclose(plot_lo, plot_hi):
        scale = max(abs(plot_lo), abs(plot_hi), 1.0e-6)
        return -scale, scale

    return plot_lo, plot_hi


def plot_case_component(
    *,
    case: DiscoveredCase,
    rows: list[dict[str, float | str]],
    component: str,
    output_dir: Path,
    dpi: int,
    write_pdf: bool,
    scale_mode: str,
) -> list[Path]:
    fig, axes = plt.subplots(
        math.ceil(len(POINT_ORDER) / 2),
        2,
        figsize=(13.4, 3.4 * math.ceil(len(POINT_ORDER) / 2)),
        sharex=True,
        sharey=False,
        constrained_layout=True,
    )

    for unused_ax in axes.ravel()[len(POINT_ORDER):]:
        unused_ax.set_visible(False)

    for ax, point in zip(axes.ravel(), POINT_ORDER):
        selected = select_rows(rows, point)
        if not selected:
            ax.set_visible(False)
            continue

        x = np.array([float(row["x_over_L"]) for row in selected], dtype=float)
        has_fem = f"{component}_fem3d_mm" in selected[0]
        fem = np.array([float(row[f"{component}_fem3d_mm"]) for row in selected], dtype=float) if has_fem else np.array([])
        cuf = np.array(
            [float(row[f"{component}_cuf_mm"]) for row in selected],
            dtype=float,
        )

        if has_fem:
            ax.plot(x, fem, "o-", linewidth=1.45, markersize=1.8, color="0.20", label="FEM3D", zorder=3)
        ax.plot(
            x,
            cuf,
            "s--",
            linewidth=1.35,
            markersize=1.8,
            label=case.cuf_label,
            zorder=4,
        )

        if scale_mode == "human":
            # Scale each panel from the FEM3D + CUF values of the current case only.
            # Zero remains included through human_limits().
            ax.set_ylim(*human_limits([fem, cuf]))
        else:
            ax.set_ylim(*local_limits([fem, cuf]))

        ax.legend(loc="best", fontsize=8)
        ax.set_xlim(-0.025, 1.025)
        ax.set_xticks([0.0, 0.25, 0.50, 0.75, 1.0])
        ax.axhline(0.0, color="0.55", linewidth=0.7)
        ax.grid(True, alpha=0.25)
        ax.set_title(point.replace("_", " "), fontsize=13)
        ax.text(
            0.03,
            0.04,
            point_coordinate_label(selected),
            transform=ax.transAxes,
            fontsize=8.5,
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "alpha": 0.85,
                "edgecolor": "#cccccc",
            },
        )
        ax.ticklabel_format(
            style="sci",
            axis="y",
            scilimits=(-3, 4),
            useMathText=True,
        )

    scale_note = (
        "Per-panel physical y-scale (zero included)"
        if scale_mode == "human"
        else "Local per-panel zoom (diagnostic view)"
    )

    fig.suptitle(
        f"{case.title}\n"
        f"{component} along moving section vertices (CUF axes)\n"
        f"{scale_note}",
        fontsize=16,
    )
    fig.supxlabel("s = (x - x₀)/L", fontsize=14)
    fig.supylabel(f"{component} [mm]", fontsize=14)

    case_output_dir = output_dir / case.directory_name
    case_output_dir.mkdir(parents=True, exist_ok=True)

    output_base = case_output_dir / (
        f"displacement_{component}_along_beam{case.plot_suffix}"
    )
    outputs = [output_base.with_suffix(".png")]
    fig.savefig(outputs[0], dpi=dpi, bbox_inches="tight", pad_inches=0.10)

    if write_pdf:
        outputs.append(output_base.with_suffix(".pdf"))
        fig.savefig(outputs[-1], bbox_inches="tight", pad_inches=0.10)

    plt.close(fig)
    return outputs


def main() -> None:
    global POINT_ORDER
    args = parse_args()
    if args.samples < 2:
        raise ValueError("--samples must be at least 2")
    # This is the only YAML read. All geometry and bounds come from CSF objects.
    result = CSFReader().read_file(str(args.csf_yaml))
    if not result.ok or result.field is None:
        raise ValueError(CSFIssues.format_report(result.issues))
    POINT_ORDER, geometry, start, end = sample_geometry(result.field, args.samples, args.vertices)
    cases = discover_cases(args.cuf_output_root, args.checkpoint)
    fem_field = None
    fem_path = _explicit_fem3d_file(args.fem3d)
    if fem_path is not None:
        from fem3d_field import FEM3DDisplacementField
        fem_field = FEM3DDisplacementField.load(fem_path)
        if not np.allclose([fem_field.x_start, fem_field.x_end], [start, end], rtol=0, atol=1e-8):
            raise ValueError(f"FEM3D/CSF longitudinal domain mismatch: {fem_path}")
    components = COMPONENTS if args.component == "all" else (args.component,)
    for case in cases:
        rows = evaluate_case(case, geometry, start, end)
        if fem_field is not None:
            add_fem_reference(rows, fem_field)
        destination = args.output_dir / case.directory_name
        destination.mkdir(parents=True, exist_ok=True)
        samples_path = destination / f"sampled_vertices{case.plot_suffix}.npz"
        np.savez_compressed(samples_path, coordinate_system=np.array("CUF"),
                            **{key: np.asarray([row[key] for row in rows]) for key in rows[0]})
        for component in components:
            paths = plot_case_component(case=case, rows=rows, component=component,
                output_dir=args.output_dir, dpi=args.dpi, write_pdf=args.pdf, scale_mode=args.scale_mode)
            for path in paths:
                print(f"[ok] {path}")
        print(f"[ok] {samples_path}")


if __name__ == "__main__":
    main()
