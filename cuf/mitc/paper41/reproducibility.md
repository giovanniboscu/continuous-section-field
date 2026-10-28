# MITC Paper §4.1 - reproducibility

This guide reproduces the **six single-element L9 cantilever cases** from Carrera, de Miguel and Pagani (2017), §4.1, Table 1. It follows the command-first approach used by the project's bridge-like reproducibility guide. The full physical description and numerical comparisons are in [README.md](README.md).

**Command location:** run the following commands from the folder containing `cases/`, `models/`, `problems/`, `expansions/`, `output/`, and `run_paper41.sh` (normally `continuous-section-field/cuf/mitc/paper41/`). All relative paths below assume this folder.

## 1. What you need

- For verifying **archived results only**: Python 3 and NumPy. A solver is not needed.
- For **running new analyses**: the complete, compatible [CSF–CUF repository](https://github.com/giovanniboscu/continuous-section-field), installed in a Python environment, including the `csf-cuf` command and the `csf.cuf.adapters.problem.c_section_cantilever_point_load` and `csf.cuf.adapters.output.post` modules.
- For YAML inspection: PyYAML is optional; it is needed only if you want to parse YAML programmatically, not for the included NumPy recovery script.

Linux (Ubuntu/Debian) repository setup, from your working directory:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip

git clone --depth 1 https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -e .
python3 -m pip install numpy
pip install pypardiso
csf-cuf --help
```

If you already have a working solver environment, **reuse it**; do not reinstall it or overwrite existing results just to audit the published runs. On Windows use `python` instead of `python3` and activate the virtual environment with `venv\Scripts\activate.bat` in CMD.

Record the precise code revision when rerunning:

```bash
git rev-parse HEAD
python3 --version
python3 -m pip freeze > mitc_paper41_environment.txt
```

## 2. Put the benchmark files in place

The package has this structure:

```text
README.md
reproducibility.md
run_paper41.sh
recover_mitc_shear.py
paper41_shear_comparison.csv
models/mitc_paper41_square_csf.yaml
problems/mitc_paper41_point.yaml
expansions/lagrangeL9_v4.py
cases/mitc_paper41_L9_B{2,3,4}_{off,on}.yaml
output/mitc_paper41_L9_B*/response.txt
output/mitc_paper41_L9_B*/*.cuf.npz
logs/mitc_paper41_L9_B*.log
```

Extract or merge the folders into `cuf/mitc/paper41/` inside a checked-out, installed repository. You may instead use a separate benchmark directory if the installed solver resolves all paths consistently. **Do not copy** the case YAMLs alone: their `../models/`, `../problems/` and `../expansions/` references must resolve.

From the repository root:

```bash
cd cuf/mitc/paper41
```

Check that the inputs exist:

```bash
ls cases/mitc_paper41_L9_*.yaml
ls models/mitc_paper41_square_csf.yaml problems/mitc_paper41_point.yaml
ls expansions/lagrangeL9_v4.py
```

## 3. Understand the input files before running

The **CSF model** [`models/mitc_paper41_square_csf.yaml`](models/mitc_paper41_square_csf.yaml) describes the actual square sectional polygon and constitutive properties at longitudinal stations 0 and 1000 mm. CSF supplies the physical domains and material law for the section integrals, not a separate 3D mesh.

The **problem** [`problems/mitc_paper41_point.yaml`](problems/mitc_paper41_point.yaml) gives the clamp at x=0 and the `-100 N` tip force at `(1000,0,0)`. The named Python problem adapter in the case applies this physical condition as generalized CUF constraints and loads. It is part of the installed solver, not the YAML.

The **CUF case** (e.g. [`cases/mitc_paper41_L9_B3_on.yaml`](cases/mitc_paper41_L9_B3_on.yaml)) connects those physical inputs with the L9 section expansion and the longitudinal B3 element. The element list `[0,1]` denotes a single element in the normalized beam coordinate. `correctionMITC: true` enables the shear correction; `verifyMITCAssembly: true` requests an internal assembly diagnostic.

| File pair | Longitudinal nodes | Shear tying points | Approximation |
|---|---:|---:|---|
| B2 ON / OFF | 2 | 1 | Constant assumed shear (ON) |
| B3 ON / OFF | 3 | 2 | Linear assumed shear (ON) |
| B4 ON / OFF | 4 | 3 | Quadratic assumed shear (ON) |

## 4. Check the archived results - no solver run

To reproduce the shear comparison from the six supplied checkpoints:

```bash
python3 -m pip install numpy
python3 recover_mitc_shear.py --output output --csv paper41_shear_comparison_regenerated.csv
```

This reads each `output/mitc_paper41_L9_B*_*/...cuf.npz` and writes the stresses at the longitudinal nodes. Each row contains `raw_shear_MPa`, `mitc_shear_MPa`, the paper-scaled stress, the paper reference where available and their difference. For MITC ON, the correction is built from B2/B3/B4 tying points; for OFF, the direct displacement derivative is retained.

To compare the regenerated numbers with the archived CSV using the standard library:

```bash
python3 - <<'PY'
import csv
from pathlib import Path
old = list(csv.DictReader(Path('paper41_shear_comparison.csv').open()))
new = list(csv.DictReader(Path('paper41_shear_comparison_regenerated.csv').open()))
assert len(old) == len(new) == 18
for a, b in zip(old, new):
    assert a['case'] == b['case'] and a['node'] == b['node']
    assert abs(float(a['paper_table_units']) - float(b['paper_table_units'])) < 1e-8
print('PASS: 18 recovered shear samples match archived CSV')
PY
```

For displacement, open each `output/<case>/response.txt`, locate the row `x/L = 1.00`, `point = center`, and read the `uz` value (mm). Compare with [README.md, Section 6](README.md#6-tip-displacement-comparison-with-table-1). Do **not** take the maximum displacement somewhere else in the cross-section.

## 5. Rerun the six cases - solver required

```bash
bash run_paper41.sh
```

This executes B2, B3, B4, each OFF then ON, and stores command output in `logs/`. The solver writes `response.txt` and `.cuf.npz` to a separate `output/<case>/` directory per case.

To run just MITC B4:

```bash
csf-cuf cases/mitc_paper41_L9_B4_on.yaml
```

On Windows CMD, invoke single cases directly, for example:

```cmd
csf-cuf cases\mitc_paper41_L9_B4_on.yaml
```

The supplied `.sh` script needs Bash (Linux/macOS/WSL/Git Bash). **Rerunning may replace archived output**; copy it first if you want to preserve the supplied comparison.

## 6. Recover shear from newly generated checkpoints

```bash
python3 recover_mitc_shear.py --output output --csv paper41_shear_comparison.csv
```

The stress recovery evaluates the engineering shear strain `gamma_xz = du_z/dx + du_x/dz` at the section center. For ON it then interpolates this strain from the longitudinal tying points to each element node. The material shear modulus for this **isotropic** test is computed from the explicitly specified `E=75000 MPa` and `nu=0.33` as `G=E/[2(1+nu)]`. This relation is used only for the isotropic law specified in this particular benchmark; it is **not** a general assumption about CSF material carriers.

The paper uses longitudinal **y** and transverse **x,z**, whereas this solver uses longitudinal **x** and transverse **y,z**. Thus paper `sigma_yz` corresponds to the physical project `tau_xz` in the same loading configuration.

The paper table's stress column is the value of stress in Pa divided by `10^4`. Because the post-processor reports MPa internally, its scaled output is `stress_MPa × 100`.

## 7. Verify the numerical diagnostics

Check each `logs/mitc_paper41_L9_*.log` for the end of the solve, reported stiffness symmetry and residuals. For ON cases, locate `MITC assembly verify` entries. Those checks are **internal code consistency diagnostics** and should not be mistaken for an independent full-stiffness verification.

The comparison to the **published displacement and shear-stress samples** is a separate, stronger external numerical reference. It still covers only the prismatic isotropic L9 model used here.

## 8. Provenance and scope

Retain together for any newly generated result: repository commit, Python dependencies, all six case files, the CSF YAML, physical problem YAML, L9 expansion file, logs, response files, checkpoints, and post-processor command. The archived data supplied here do **not** establish the exact original repository commit; do not infer one.

This benchmark reproduces Table 1, §4.1 for B2/B3/B4 L9 and MITC ON/OFF. It is **not** the earlier long-beam B2 mesh-refinement series, and it does not verify general anisotropic cross-couplings, zero-energy modes, or arbitrary variable sections.
