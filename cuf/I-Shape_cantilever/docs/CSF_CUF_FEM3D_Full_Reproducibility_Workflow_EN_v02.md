# CSF-CUF / FEM3D I-shaped cantilever: complete manual reproducibility workflow

**Purpose.** Reproduce the seven stages of the final CSF-CUF benchmark on a clean working directory, using the project's existing solvers and postprocessors. All commands below are run **from the case directory** (`cuf/I-Shape_cantilever` or the equivalent clean copy). Activate the repository's Python environment first.

**Scientific scope.** The transverse CUF L9 approximation is fixed. CUF convergence is assessed independently from consecutive CUF displacement solutions under longitudinal h- and p-refinement. FEM3D selects its longitudinal H8 mesh through its separate three-grid GCI study, at fixed transverse divisions. Sectional force/moment verification and CUF-FEM3D displacement-field comparisons are **post-selection validation results, not criteria used to select either model**. No exterior-surface traction/stress comparison is included.

## 0. Prerequisites and preflight

- Use a clean copy of the I-shaped case inside the installed `continuous-section-field` repository, with the CSF package/import path available.
- Required directories include `cases/convergence_h_v02/`, `cases/convergence_p_v02/`, `models/`, `problems/`, `adapters/`, `tools/`, and `fem3d/`.
- `tools/converge_opensees_csf.py` must be copied from the recovered `tools_2remove/converge_opensees_csf.py`, if it has not already been restored.
- `fem3d/run_opensees_csf_native_stresses_v02.py` must be present. It records native `stdBrick` Gauss stresses, as well as nodal support reactions.
- The current `tools/plot_fem3d_N_T_M_from_npz.py` must be the **native-stress v03 version**, supporting `--sampling center`.
- `tools/compare_cuf_fem3d_N_T_M.py` requires `tools/check_cuf_single_tensor_surface.py`, `tools/plot_fem3d_N_T_M_from_npz.py`, and the existing CSF/CUF code.
- For stage 7, `tools/run_cuf_h_fem3d_comparison_v02.py`, `tools/run_cuf_p_fem3d_comparison_v02.py`, `tools/_cuf_series_common_v02.py`, `tools/compare_cuf_fem_displacements.py`, and `tools/plot_cuf_fem_agreement_v02.py` must be available.
- Python packages must include the CSF package, OpenSeesPy, NumPy and Matplotlib (plus the existing case and adapter dependencies).

Check the environment and commands:

```bash
python -c "import csf, numpy, matplotlib; import openseespy.opensees; print('Environment OK')"
test -f tools/converge_opensees_csf.py && echo 'GCI orchestrator OK'
test -f fem3d/run_opensees_csf_native_stresses_v02.py && echo 'Native-stress FEM3D driver OK'
python tools/run_cuf_h_study_v02.py --dry-run
python tools/run_cuf_p_study_v02.py --dry-run
python tools/converge_opensees_csf.py --help
test -f tools/run_cuf_h_fem3d_comparison_v02.py
test -f tools/run_cuf_p_fem3d_comparison_v02.py
```

The dry runs validate the CUF study configurations; they do not solve the model. Do not proceed if a required command or input is missing.

## 1. Solve the CSF-CUF cases (longitudinal h and p series)

The transverse L9 basis and physical CSF model remain unchanged.

**h series:** 8 solutions with longitudinal element counts `N = 2, 4, 6, 8, 10, 12, 16, 20`; `p = 12` fixed:

```bash
python tools/run_cuf_h_study_v02.py
```

**p series:** 11 solutions with polynomial orders `p = 2, 3, ..., 12`; `N = 10` fixed:

```bash
python tools/run_cuf_p_study_v02.py
```

These scripts write checkpoint/response/manifest records to case-defined paths under `output/cuf_convergence/` and execution reports under `diagnostics/`. They do not use FEM3D. To resume an interrupted run **without overwriting verified completed outputs**, use `--skip-completed` on the relevant command; do not use this option to conceal invalid or incomplete checkpoints.

## 2. Check independent CSF-CUF longitudinal convergence

```bash
python tools/check_cuf_longitudinal_convergence.py \
  --input output/cuf_convergence \
  --cases cases \
  --tolerance-pct 0.5
```

The program verifies 19 checkpoint/response pairs against their saved SHA-256 provenance and computes consecutive **CUF-to-CUF** changes of the vertical displacement at the fixed physical point `P = (1000, -33, 35) mm`. The study rule requires **two consecutive relative changes no greater than 0.5%**, applied separately to h and p series. It is a **displacement stabilization criterion**, not an estimate of convergence of the entire stress field.

Previously observed first passing configurations (reference values, to be checked on the new run):

| Study | First two-increment pass | Tip displacement u_z(P) |
|---|---|---:|
| h, p=12 fixed | N=6 | -80.41228804958 mm |
| p, N=10 fixed | p=4 | -80.34557893389 mm |

For the final sectional-action comparison, use the already solved **common configuration `N = 10, p = 12`** at `cases/convergence_h_v02/step_005.yaml`, rather than combining independently selected `N=6` and `p=4` into an uncomputed case. The h and p series both contain that common configuration.

Output: `diagnostics/cuf_longitudinal_convergence/<dataset-hash>/` with `h_series.csv`, `p_series.csv`, `convergence_h.png`, `convergence_p.png`, the Markdown report, and `provenance.json`.

## 3. Solve FEM3D and perform its independent GCI study

Use the recovered GCI orchestrator with the **native-stress OpenSees driver**:

```bash
python tools/converge_opensees_csf.py \
  cases/convergence_h_v02/step_008.yaml \
  --driver fem3d/run_opensees_csf_native_stresses_v02.py \
  --method gci \
  --nx 20 40 60 80 100 125 \
  --nu 6 --nv 6 \
  --point 1000 -33 35 \
  --tolerance-pct 0.5 \
  --run-all \
  --output-root fem3d/convergence_gci
```

This generates **a new uniquely numbered** `fem3d/convergence_gci/run_NNNN/` directory and a `convergence_result.json`. The GCI is computed from three FEM3D mesh levels based on the displacement `u_z(P)`; transverse H8 subdivisions per CSF domain are fixed at `nu=6`, `nv=6`. The 0.5% threshold is study-specific. The Richardson/GCI estimate **assumes** asymptotic behavior; the script does not independently verify that regime and does not certify stress-field convergence.

The prior study selected `80 x 6 x 6` (25,920 H8 elements) with GCI `0.477699%`; **do not hard-code this result** for the clean replication.

### Select the FEM3D checkpoint from this run

Use the **actual new run directory printed by the GCI program**. For example, if it reports `run_0001`, set:

```bash
GCI_RUN=fem3d/convergence_gci/run_0001
```

Do not automatically assume the new run number is `0001` if the directory is not empty.

Then extract and validate the selected checkpoint, using the actual fields in `convergence_result.json`:

```bash
FEM_NPZ=$(python - "$GCI_RUN" <<'PY'
import json
import sys
from pathlib import Path
import numpy as np

run = Path(sys.argv[1]).resolve()
d = json.loads((run / 'convergence_result.json').read_text(encoding='utf-8'))
if d.get('method') != 'gci' or d.get('gci_selection_criterion_met') is not True:
    raise SystemExit('The GCI study did not select an eligible mesh.')
step = d.get('selected_step')
if type(step) is not int or step < 1:
    raise SystemExit('Invalid selected_step in GCI result.')
checkpoint = run / f'step_{step:03d}' / 'solution.npz'
if not checkpoint.is_file():
    raise SystemExit(f'Missing selected checkpoint: {checkpoint}')
with np.load(checkpoint, allow_pickle=False) as f:
    if 'gauss_stress' not in f:
        raise SystemExit('Selected checkpoint lacks native OpenSees gauss_stress.')
    if not np.isfinite(f['gauss_stress']).all():
        raise SystemExit('Nonfinite native OpenSees Gauss stresses.')
    if 'mesh_divisions' not in f or list(map(int, f['mesh_divisions'])) != d.get('selected_mesh_divisions'):
        raise SystemExit('Selected checkpoint and GCI mesh do not agree.')
print(checkpoint)
PY
)

echo "Selected native-stress FEM3D checkpoint: $FEM_NPZ"
```

The saved native stresses are the eight six-component OpenSees Gauss stresses per H8 element. Save the original `convergence_result.json`, `manifest.json` and selected NPZ, including their checksums, as the FEM3D study evidence.

## 4. Recover the CSF-CUF sectional actions N, Tz, and My

Use the `N=10`, `p=12` CUF configuration:

```bash
python tools/plot_cuf_N_T_M_from_npz.py \
  --case cases/convergence_h_v02/step_005.yaml \
  --points 20
```

CUF displacements are read from the solved checkpoint; strain and stress are evaluated through the project's existing `plot_strain_stress_boundary_v10` machinery, with physical cross-sectional quadrature provided by CSF. This is a **separate CUF sectional-resultant verification** against the prescribed load resultants.

Output root: `diagnostics/cuf_N_T_M_from_npz/` (PNG figures, sectional CSV, provenance JSON).

## 5. Recover FEM3D sectional actions N, Tz, and My

Use **native OpenSees Gauss stresses** from the GCI-selected checkpoint; do not reconstruct them from nodal displacements. Use the specified `center` recovery:

```bash
python tools/plot_fem3d_N_T_M_from_npz.py \
  --case cases/convergence_h_v02/step_008.yaml \
  --fem-npz "$FEM_NPZ" \
  --sampling center \
  --points 20
```

At each H8 element, `center` takes the **arithmetic mean of its eight native Gauss stress tensors**. The result is a piecewise-constant transverse recovery integrated over CSF physical section quadrature; it is **not** a native OpenSees stress evaluated at the exact center. The script also reports support reaction balance where available.

Output root: `diagnostics/fem3d_N_T_M_native/` (PNG figures, sectional CSV, `support_balance.json`, provenance JSON).

## 6. Compare independently selected CUF and FEM3D N, Tz, and My

```bash
python tools/compare_cuf_fem3d_N_T_M.py \
  --cuf-case cases/convergence_h_v02/step_005.yaml \
  --fem-case cases/convergence_h_v02/step_008.yaml \
  --fem-npz "$FEM_NPZ" \
  --points 20
```

This program runs the FEM3D `center` postprocessor and evaluates CUF on **the same actual FEM3D center-section coordinates**. It compares `N`, `Tz`, and `My` against each other and against the independently integrated applied-load resultants. This does **not** use CUF-FEM3D displacement differences to determine CUF convergence.

Output root: `diagnostics/cuf_fem3d_N_T_M/<checkpoint-hash-key>/` with:

- `section_resultants_comparison.csv`
- `comparison_N.png`, `comparison_Tz.png`, `comparison_My.png`, `comparison_N_Tz_My_overview.png`
- `comparison_report.md`, `provenance.json`
- `fem3d_native_center/` (internal FEM3D run of the same stress-recovery method)

## 7. Compare CSF-CUF and FEM3D displacement fields (existing postprocessors)

**This is a separate post-selection validation, not a CUF or FEM3D convergence test.** Reuse the `GCI_RUN` directory from stage 3 and its already selected FEM3D displacement checkpoint. The existing v02 comparison orchestrators process the **completed CUF h-series (8 configurations)** and **p-series (11 configurations)** against exactly the **same FEM3D checkpoint**. Neither orchestrator calls the CUF or OpenSees solver.

The scripts validate the saved CUF checkpoint/response manifests and their SHA-256 fingerprints, the GCI selection record, and the physical model's CSF problem/model/adapter fingerprints. They invoke the existing `tools/compare_cuf_fem_displacements.py` for each CUF configuration.

**CUF h-series versus selected FEM3D (fixed p = 12):**

```bash
python tools/run_cuf_h_fem3d_comparison_v02.py \
  --gci-result "$GCI_RUN/convergence_result.json" \
  --comparator tools/compare_cuf_fem_displacements.py \
  --sampling both \
  --bins 40
```

**CUF p-series versus selected FEM3D (fixed N = 10):**

```bash
python tools/run_cuf_p_fem3d_comparison_v02.py \
  --gci-result "$GCI_RUN/convergence_result.json" \
  --comparator tools/compare_cuf_fem_displacements.py \
  --sampling both \
  --bins 40
```

Both commands can be pre-validated without starting any comparisons by appending `--dry-run`.

**Sampling and metric.** `--sampling both` performs displacement comparisons at FEM3D element centers and nodes. The consolidated series metric is the existing **volume-weighted relative vector L2 displacement difference (%) at element-center samples**, not the point displacement `u_z(P)` used for the independent convergence studies. `--bins 40` is used only for longitudinal breakdowns and visualizations; it does not modify either numerical model or the global L2 metric.

**Outputs.** Each command creates a new numbered directory under:

```text
diagnostics/cuf_h_fem3d_comparison_v02/run_NNNN/
diagnostics/cuf_p_fem3d_comparison_v02/run_NNNN/
```

Each directory contains `manifest.json`, `comparison_h_series.csv` or `comparison_p_series.csv`, the corresponding Markdown report and results JSON, the relative-L2-versus-N or versus-p plot, `cuf_fem3d_agreement_overview.png`, and `step_NNN/` comparison reports and displacement-agreement plots for each completed CUF configuration. Retain the records for the common `N=10, p=12` CUF configuration; it appears in both series and should be numerically consistent.

**Interpretation.** These results measure the *agreement between two independently selected numerical approximations*. They do not turn a CUF-FEM3D difference into a CUF convergence criterion, demonstrate uniqueness of the exact solution, or establish convergence of the stress field. Stress/traction comparisons remain outside the displacement-validation step.

## Acceptance and archiving checklist

| Stage | Required evidence |
|---|---|
| 1. CUF solutions | 8 h-series and 11 p-series solved NPZs, responses and manifests |
| 2. CUF convergence | Independent h/p successive-displacement changes, CSVs, plots, and report |
| 3. FEM3D GCI | New run manifest, `convergence_result.json`, eligible selected step, NPZ with native `gauss_stress` |
| 4. CUF actions | N/Tz/My sectional CSV, figures, and provenance |
| 5. FEM3D actions | Native-stress `center` sectional CSV, figures, support balance and provenance |
| 6. Sectional-resultant comparison | Shared-coordinate N/Tz/My CSV, overview plots, report and input hashes |
| 7. Displacement-field comparison | Completed h/p-series relative-L2 CSV/JSON/Markdown reports, agreement plots, and GCI/CUF input hashes |

**Report limitations explicitly in the paper.** CUF h/p stabilization is evaluated on one displacement observable; FEM3D GCI is a displacement-based estimate at fixed transverse resolution; neither alone certifies the full stress field. The `center` FEM3D resultants use an averaging/recovery procedure different from direct CUF stress evaluation. The stage-7 CUF-FEM3D displacement discrepancy quantifies agreement **after** independent model selection; it is not a convergence acceptance criterion. No surface-traction reconstruction results are included in this workflow.
