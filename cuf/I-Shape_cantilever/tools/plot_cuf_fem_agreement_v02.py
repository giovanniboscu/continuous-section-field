#!/usr/bin/env python3
"""Generate CUF-FEM3D displacement agreement figures from existing comparator data.

Plotting-only: reads the already paired displacement NPZ saved by the unchanged
numerical comparator. Never evaluates CSF geometry/materials, FEM elements, or
CUF basis functions; never runs a solver or a comparison.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import numpy as np


STUDIES = ('p', 'h')
EXPECTED_STEPS = {'p': 11, 'h': 8}
PLOT_NAME = 'cuf_fem3d_agreement_overview.png'
STEP_PLOT_NAME = 'cuf_fem3d_agreement.png'


def _read_json(path: Path) -> dict:
    val = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(val, dict):
        raise ValueError(f'Not a JSON object: {path}')
    return val


def _ensure_completed_run(folder: Path, study: str) -> dict:
    """Reject incomplete runs: plotting 4/8 images is not a complete h report."""
    report = folder / f'comparison_{study}_result.json'
    aggregate = _read_json(report)
    rows = aggregate.get('results', [])
    expected = EXPECTED_STEPS[study]
    completed = (aggregate.get('study') == study
                 and aggregate.get('status') == 'completed'
                 and isinstance(rows, list) and len(rows) == expected)
    if not completed:
        count = len(rows) if isinstance(rows, list) else 'invalid'
        raise ValueError(f'Comparison run is not complete: {folder} '
                         f'(status={aggregate.get("status")!r}, '
                         f'comparisons={count}/{expected}). '
                         'Figures can be generated for all steps only from a completed '
                         'comparison run.')
    return aggregate


def _series_run(project: Path, study: str) -> Path:
    """Select the newest COMPLETED run rather than a newer partial rerun."""
    root = project / f'diagnostics/cuf_{study}_fem3d_comparison_v02'
    if not root.is_dir():
        raise FileNotFoundError(f'Comparison output directory not found: {root}')
    examined = []
    for folder in sorted(root.glob('run_*'), reverse=True):
        summary = folder / f'comparison_{study}_result.json'
        if not summary.is_file():
            continue
        report = _read_json(summary)
        rows = report.get('results', [])
        count = len(rows) if isinstance(rows, list) else 'invalid'
        examined.append(f'{folder.name}: status={report.get("status")}, '
                        f'comparisons={count}/{EXPECTED_STEPS[study]}')
        if (report.get('status') == 'completed'
            and report.get('study') == study
            and isinstance(rows, list)
            and len(rows) == EXPECTED_STEPS[study]):
            return folder
    raise FileNotFoundError('No completed comparison run found in '
                            f'{root}. Checked: ' + '; '.join(examined))


def _load_pairs(folder: Path, kind: str, row: dict, step_index: int,
                sampling: str, expected_fem_hash: str):
    step = folder / f'step_{step_index:03d}'
    report_file = step / 'summary.json'
    report = _read_json(report_file)
    if report.get('inputs', {}).get('sha256_fem') != expected_fem_hash:
        raise ValueError(f'FEM checkpoint hash differs from series reference: {report_file}')
    mode = 'gauss2' if sampling == 'gauss2' else 'centers'
    data_file = step / f'comparison_{mode}.npz'
    if not data_file.is_file():
        raise FileNotFoundError(f'Paired displacement samples missing: {data_file}')
    with np.load(data_file, allow_pickle=False) as n:
        required = ('x_y_z', 'u_fem', 'u_cuf', 'physical_volume_quadrature_weight')
        absent = [k for k in required if k not in n]
        if absent:
            raise ValueError(f'Missing {absent} in {data_file}')
        xyz = np.asarray(n['x_y_z'], dtype=float)
        fem = np.asarray(n['u_fem'], dtype=float)
        cuf = np.asarray(n['u_cuf'], dtype=float)
        weight = np.asarray(n['physical_volume_quadrature_weight'], dtype=float)
    if (xyz.ndim != 2 or xyz.shape[1] != 3 or fem.shape != xyz.shape
        or cuf.shape != xyz.shape or weight.shape != (len(xyz),)
        or not len(xyz)):
        raise ValueError(f'Invalid paired arrays: {data_file}')
    if (not np.all(np.isfinite(xyz)) or not np.all(np.isfinite(fem))
        or not np.all(np.isfinite(cuf)) or not np.all(np.isfinite(weight))
        or np.any(weight <= 0)):
        raise ValueError(f'Non-finite data or nonpositive quadrature weights: {data_file}')
    err_sq = np.sum((cuf-fem)**2, axis=1)
    fem_sq = np.sum(fem**2, axis=1)
    denom = float(np.dot(weight, fem_sq))
    if denom <= 0:
        raise ValueError('The FEM displacement norm is zero; relative L2 is undefined')
    independent_check = 100.0 * math.sqrt(float(np.dot(weight, err_sq)) / denom)
    reported = float(row['relative_l2_percent'])
    if not math.isclose(independent_check, reported, rel_tol=2e-7, abs_tol=1e-6):
        raise ValueError(f'Paired samples and recorded L2 disagree: '
                         f'{independent_check:.12g} vs {reported:.12g}')
    csf_domain = report.get('physical_domain', {})
    x0, x1 = float(csf_domain['x0']), float(csf_domain['x1'])
    if not math.isfinite(x0) or not math.isfinite(x1) or x0 >= x1:
        raise ValueError('Invalid saved CSF longitudinal domain')
    if np.min(xyz[:,0]) < x0-1e-7 or np.max(xyz[:,0]) > x1+1e-7:
        raise ValueError('Sample points outside saved CSF longitudinal domain')
    return xyz, fem, cuf, weight, x0, x1, mode


def _bin_pairs(xyz, fem, cuf, weight, x0, x1, bins):
    t = np.clip((xyz[:, 0]-x0)/(x1-x0), 0, 1)
    ibin = np.minimum(np.floor(t*bins).astype(int), bins-1)
    sw = np.bincount(ibin, weights=weight, minlength=bins)
    active = sw > 0
    if not np.any(active):
        raise ValueError('No longitudinal bins contain sample points')
    centers = (np.arange(bins)+.5)/bins
    mean_fem = np.full((bins, 3), np.nan)
    mean_cuf = np.full((bins, 3), np.nan)
    for k in range(3):
        sf = np.bincount(ibin, weights=weight*fem[:,k], minlength=bins)
        sc = np.bincount(ibin, weights=weight*cuf[:,k], minlength=bins)
        mean_fem[active,k] = sf[active]/sw[active]
        mean_cuf[active,k] = sc[active]/sw[active]
    err2 = np.sum((cuf-fem)**2,axis=1)
    se = np.bincount(ibin, weights=weight*err2, minlength=bins)
    rmse = np.full(bins, np.nan)
    rmse[active] = np.sqrt(se[active]/sw[active])
    return centers[active], mean_fem[active], mean_cuf[active], rmse[active]


def create_step_agreement(folder: Path, study: str, step_index: int, aggregate: dict | None = None) -> Path:
    """Plot a single CUF/FEM displacement comparison from saved paired samples.

    No solution reconstruction or interpolation of CSF physical fields occurs here.
    ``step_index`` is 1-based and corresponds to ``step_NNN``.
    """
    if study not in STUDIES:
        raise ValueError(f'Unknown study: {study}')
    folder = Path(folder).resolve()
    if aggregate is None:
        aggregate = _read_json(folder / f'comparison_{study}_result.json')
    rows = aggregate.get('results', [])
    if (aggregate.get('study') != study
        or aggregate.get('metric') != 'volume_weighted_vector_relative_L2_percent'
        or not isinstance(rows, list) or not 1 <= step_index <= len(rows)):
        raise ValueError(f'Invalid series or step {step_index}')
    row = rows[step_index - 1]
    sampling = aggregate.get('sampling')
    xyz, fem, cuf, w, x0, x1, mode = _load_pairs(
        folder, study, row, step_index, sampling,
        aggregate['fem_checkpoint_sha256'])
    bins = aggregate.get('bins', 40)
    if not isinstance(bins, int) or not 1 <= bins <= 500:
        raise ValueError('Invalid longitudinal bin count')
    bx, mf, mc, rmse = _bin_pairs(xyz, fem, cuf, w, x0, x1, bins)

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axs = plt.subplots(2, 3, figsize=(13.7, 8.1), constrained_layout=True)
    N, order = int(row['elements']), int(row['order'])
    discrepancy = float(row['relative_l2_percent'])
    fig.suptitle(f'CUF vs FEM3D | {study}-study, step {step_index:03d} | '
                 f'N={N}, p={order} | L2 difference = {discrepancy:.6g}%',
                 fontsize=16, weight='bold')

    for k, ax in enumerate(axs[0]):
        component = ('ux', 'uy', 'uz')[k]
        ax.plot(bx, mf[:, k], linewidth=2.1, label='FEM3D')
        ax.plot(bx, mc[:, k], '--', linewidth=1.7, label='CUF')
        ax.set(xlabel='Longitudinal coordinate x/L',
               ylabel=f'{component} (native units)',
               title=f'{component}: volume-weighted bin means')
        ax.grid(alpha=.24)
        ax.legend(loc='best', fontsize=9)

    # Show the largest FEM displacement component by its squared weighted norm.
    # Choice does NOT depend on which component agrees best with CUF.
    component_energy = np.einsum('i,ij->j', w, fem**2)
    component = int(np.argmax(component_energy))
    cname = ('ux', 'uy', 'uz')[component]
    stride = max(1, math.ceil(len(w) / 6000))
    xdata = fem[::stride, component]
    ydata = cuf[::stride, component]
    ax = axs[1, 0]
    limits = np.r_[xdata, ydata]
    min_value, max_value = float(limits.min()), float(limits.max())
    width = max_value - min_value
    if width < 1e-14:
        width = max(abs(max_value), 1.) * 1e-3
    low, high = min_value - .04 * width, max_value + .04 * width
    ax.scatter(xdata, ydata, s=5, alpha=.23, rasterized=True,
               label=f'Paired points (every {stride}th)')
    ax.plot([low, high], [low, high], '--', color='#333333',
            linewidth=1.4, label='Perfect agreement')
    ax.set(xlim=(low, high), ylim=(low, high),
           xlabel=f'FEM3D {cname} (native units)',
           ylabel=f'CUF {cname} (native units)',
           title=f'Pointwise parity: dominant FEM component ({cname})')
    ax.set_aspect('equal', adjustable='box')
    ax.legend(loc='best', fontsize=8)
    ax.grid(alpha=.22)

    ax = axs[1, 1]
    ax.plot(bx, rmse, linewidth=2)
    ax.fill_between(bx, 0, rmse, alpha=.12)
    ax.set(xlabel='Longitudinal coordinate x/L',
           ylabel='RMS ||U_CUF - U_FEM|| (native units)',
           title='Local vector discrepancy along the member')
    ax.grid(alpha=.24)

    ax = axs[1, 2]
    ax.axis('off')
    metadata = [
        f'CUF discretization: N = {N}, p = {order}',
        f'Volume-weighted relative vector L2: {discrepancy:.6g} %',
        f'Paired FEM quadrature points: {len(w):,}',
        f'FEM quadrature volume: {float(w.sum()):.7g} (native units)^3',
        f'Quadrature samples: {mode}',
        f'Longitudinal bins: {bins}',
        '',
        'SAME PHYSICAL POINTS FOR CUF AND FEM3D',
        'Profiles: volume-weighted means per x/L bin',
        'NOT pointwise paths or single-section values.',
        'Parity: pointwise comparison (visual subsample).',
        'Local RMS: absolute displacement-difference norm.',
    ]
    ax.text(.04, .95, '\n'.join(metadata), va='top', ha='left',
            transform=ax.transAxes, fontsize=10.5, linespacing=1.55,
            family='monospace')

    step_dir = folder / f'step_{step_index:03d}'
    out = step_dir / STEP_PLOT_NAME
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # Add a discoverable figure link to the existing comparator's step report.
    report_md = step_dir / 'summary.md'
    if report_md.is_file():
        report = report_md.read_text(encoding='utf-8')
        if STEP_PLOT_NAME not in report:
            report += ('\n\n## CUF-FEM3D displacement agreement at this step\n\n'
                       f'![CUF vs FEM3D: N={N}, p={order}]({STEP_PLOT_NAME})\n\n'
                       'The three longitudinal curves are volume-weighted bin '
                       'means of paired FEM quadrature samples; they are not '
                       'individual material-line profiles. The parity plot shows '
                       'pointwise agreement. This figure is generated from '
                       'already-saved comparison data.\n')
            report_md.write_text(report, encoding='utf-8')
    return out


def create_all_step_agreements(folder: Path, study: str) -> list[Path]:
    """Create the step figures for all completed comparisons in a p/h run."""
    aggregate = _read_json(Path(folder) / f'comparison_{study}_result.json')
    rows = aggregate.get('results', [])
    if not isinstance(rows, list) or not rows:
        raise ValueError('No completed comparison steps available')
    return [create_step_agreement(folder, study, i, aggregate)
            for i in range(1, len(rows) + 1)]


def _add_report_links(folder: Path, study: str, plotted: list[Path], overview: Path) -> None:
    """Show each existing step PNG inline, not only as a table hyperlink.

    Idempotent: rerunning --report-only updates the dedicated inline section
    without changing results or repeatedly appending copies of the figures.
    """
    report_md = folder / f'comparison_{study}_series.md'
    if not report_md.is_file():
        raise FileNotFoundError(f'Comparison Markdown report missing: {report_md}')
    original = report_md.read_text(encoding='utf-8')
    content = original
    if PLOT_NAME not in content and overview.is_file():
        content += ('\n## CUF-FEM3D displacement agreement overview\n\n'
                    f'![CUF and FEM3D agreement]({PLOT_NAME})\n')

    aggregate = _read_json(folder / f'comparison_{study}_result.json')
    rows = aggregate['results']
    heading = '## Individual step displacement agreement'
    if heading not in content:
        content += (f'\n{heading}\n\n'
                    '| Step | N | p | Figure |\n'
                    '|---:|---:|---:|---|\n')
        for i, figure in enumerate(plotted, start=1):
            row = rows[i-1]
            rel = figure.relative_to(folder).as_posix()
            content += (f'| {i:03d} | {row["elements"]} | {row["order"]} | '
                        f'[PNG]({rel}) |\n')

    start_marker = '<!-- CUF-FEM3D-INLINE-STEPS:BEGIN -->'
    end_marker = '<!-- CUF-FEM3D-INLINE-STEPS:END -->'
    pieces = [start_marker, '', '## Step-by-step displacement agreement figures', '',
              'These figures display the paired CUF and FEM3D displacement fields. '
              'Longitudinal curves are volume-weighted bin means, not a single material-line profile.', '']
    for i, figure in enumerate(plotted, start=1):
        row = rows[i-1]
        rel = figure.relative_to(folder).as_posix()
        pieces.extend((f'### Step {i:03d} — N={row["elements"]}, p={row["order"]}', '',
                       f'![CUF vs FEM3D: step {i:03d}, N={row["elements"]}, '
                       f'p={row["order"]}]({rel})', ''))
    pieces.append(end_marker)
    inline_block = '\n'.join(pieces)
    if start_marker in content:
        if end_marker not in content:
            raise ValueError(f'Incomplete embedded-figure markers: {report_md}')
        begin = content.index(start_marker)
        finish = content.index(end_marker, begin) + len(end_marker)
        content = content[:begin] + inline_block + content[finish:]
    else:
        content = content.rstrip() + '\n\n' + inline_block + '\n'

    if content != original:
        report_md.write_text(content, encoding='utf-8')

def create_agreement_overview(folder: Path, study: str) -> Path:
    """One reproducible figure for L2 trend + actual CUF/FEM field agreement."""
    if study not in STUDIES:
        raise ValueError(f'Unknown study: {study}')
    folder = Path(folder).resolve()
    aggregate = _read_json(folder / f'comparison_{study}_result.json')
    rows = aggregate.get('results', [])
    if aggregate.get('study') != study or not isinstance(rows, list) or not rows:
        raise ValueError('No valid results in series report')
    if aggregate.get('metric') != 'volume_weighted_vector_relative_L2_percent':
        raise ValueError('Unexpected series comparison metric')
    latest = rows[-1]
    sampling = aggregate['sampling']
    xyz, fem, cuf, w, x0, x1, mode = _load_pairs(
        folder, study, latest, len(rows), sampling, aggregate['fem_checkpoint_sha256'])
    bins = aggregate.get('bins', 40)
    if not isinstance(bins, int) or not 1 <= bins <= 500:
        raise ValueError('Invalid longitudinal bin count')
    bx, mf, mc, rmse = _bin_pairs(xyz, fem, cuf, w, x0, x1, bins)

    # All plotted points below were evaluated previously by the numerical
    # comparator at identical physical FEM coordinates. No new interpolation.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    key = 'order' if study == 'p' else 'elements'
    xx = np.asarray([int(r[key]) for r in rows], dtype=int)
    ll = np.asarray([float(r['relative_l2_percent']) for r in rows], dtype=float)
    if not np.all(np.isfinite(ll)):
        raise ValueError('Non-finite series L2 values')
    last_title = f'N={latest["elements"]}, p={latest["order"]}'
    fig, axs = plt.subplots(3, 2, figsize=(14.5, 12.1), constrained_layout=True)
    fig.suptitle(f'CUF - FEM3D displacement agreement | {study}-study | {last_title}',
                 fontsize=17, weight='bold')
    ax = axs[0,0]
    ax.plot(xx, ll, marker='o', linewidth=2, markersize=6)
    ax.set_xlabel('CUF polynomial order p (N=10)' if study=='p'
                  else 'CUF longitudinal elements N (p=12)')
    ax.set_ylabel('Volume-weighted vector L2 difference (%)')
    ax.set_title('Global discrepancy across the study')
    ax.set_xticks(xx)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
    ax.grid(alpha=.24)
    ax.annotate(f'{ll[-1]:.4g}%', (xx[-1], ll[-1]), xytext=(-12, 10),
                textcoords='offset points', ha='right', fontsize=10)

    # The visually dominant component is selected by FEM volume-weighted
    # squared displacement, not by choosing the smallest CUF/FEM error.
    energy = np.einsum('i,ij->j', w, fem**2)
    c = int(np.argmax(energy))
    cname = ('ux','uy','uz')[c]
    ax = axs[0,1]
    stride = max(1, math.ceil(len(w)/6000))
    xs, ys = fem[::stride,c], cuf[::stride,c]
    extent = np.r_[xs,ys]
    amin, amax = float(np.min(extent)), float(np.max(extent))
    span = amax-amin
    if span < 1e-14:
        span = max(abs(amax),1.)*1e-3
    amin -= .045*span; amax += .045*span
    ax.scatter(xs, ys, s=5, alpha=.23, rasterized=True,
               label=f'Paired FEM samples (1/{stride} shown)')
    ax.plot([amin,amax],[amin,amax], '--', color='#333333', linewidth=1.4,
            label='Exact agreement')
    ax.set(xlim=(amin,amax), ylim=(amin,amax),
           xlabel=f'FEM3D {cname} (native units)',
           ylabel=f'CUF {cname} (native units)',
           title=f'Pointwise agreement: largest FEM component ({cname})')
    ax.set_aspect('equal', adjustable='box')
    ax.grid(alpha=.2); ax.legend(loc='best', fontsize=8)

    for k, slot in enumerate((axs[1,0], axs[1,1], axs[2,0])):
        label=('ux','uy','uz')[k]
        slot.plot(bx, mf[:,k], linewidth=2, label='FEM3D')
        slot.plot(bx, mc[:,k], '--', linewidth=1.7, label='CUF')
        slot.set(xlabel='Normalized longitudinal position x/L',
                 ylabel=f'{label} (native units)',
                 title=f'{label}: volume-weighted bin mean')
        slot.grid(alpha=.22)
        slot.legend(loc='best', fontsize=9)

    ax = axs[2,1]
    ax.plot(bx, rmse, linewidth=1.9)
    ax.fill_between(bx, 0, rmse, alpha=.12)
    ax.set(xlabel='Normalized longitudinal position x/L',
           ylabel='RMS of ||U_CUF - U_FEM|| (native units)',
           title='Local vector discrepancy along the member')
    ax.grid(alpha=.22)

    status = aggregate.get('status', 'unknown')
    fig.supxlabel(f'Identical FEM H8 quadrature points ({mode}); {len(w):,} samples. '
                  f'The three profiles are weighted bin means, not pointwise paths. '
                  f'Series status: {status}.', fontsize=9)
    out = folder / PLOT_NAME
    fig.savefig(out, dpi=190, bbox_inches='tight')
    fig.savefig(out.with_suffix('.svg'), bbox_inches='tight')
    plt.close(fig)
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', choices=STUDIES, default='p',
                        help='CUF longitudinal study (default: p)')
    parser.add_argument('--run-dir', type=Path, default=None,
                        help='Specific comparison run; default: latest run for --study')
    parser.add_argument('--report-only', action='store_true',
                        help='Embed existing step PNGs in Markdown; no plots recomputed')
    args = parser.parse_args(argv)
    project = Path(__file__).resolve().parent.parent
    folder = (args.run_dir if args.run_dir.is_absolute() else project/args.run_dir).resolve() \
             if args.run_dir is not None else _series_run(project, args.study)
    try:
        _ensure_completed_run(folder, args.study)
        print(f'[AGREEMENT {args.study}] using completed run: {folder}', flush=True)
        if args.report_only:
            rows = _read_json(folder / f'comparison_{args.study}_result.json').get('results', [])
            plotted = [folder / f'step_{i:03d}' / STEP_PLOT_NAME
                       for i in range(1, len(rows)+1)]
            missing = [path for path in plotted if not path.is_file()]
            if missing:
                raise FileNotFoundError(f'Missing {len(missing)} step figures; '
                                        f'run without --report-only to generate them: {missing[0]}')
            overview = folder / PLOT_NAME
        else:
            plotted = create_all_step_agreements(folder, args.study)
            overview = create_agreement_overview(folder, args.study)
        _add_report_links(folder, args.study, plotted, overview)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(f'[AGREEMENT {args.study}] step figures: {len(plotted)}/{len(plotted)}', flush=True)
    if overview.is_file():
        print(f'[AGREEMENT {args.study}] overview: {overview}', flush=True)
    print(f'[AGREEMENT {args.study}] individual plots: '
          f'{folder}/step_NNN/{STEP_PLOT_NAME}', flush=True)
    print(f'[AGREEMENT {args.study}] Markdown with inline images: '
          f'{folder}/comparison_{args.study}_series.md', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
