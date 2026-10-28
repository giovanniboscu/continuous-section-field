# CSF–CUF MITC rectangular cantilever - reproducibility

This guide reproduces the **longitudinal B2 mesh-refinement test** of a rectangular cantilever, comparing **MITC OFF** and **MITC ON**. It follows the command-by-command approach of the [bridge-like benchmark guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/bridge-like/bridge_reproducibility.md), adapted to the files and calculations of this MITC example.

The companion [README.md](README.md) explains the physical problem, the numerical results, and their interpretation. This page explains **which files are used, how to run them, and how to check the result**.

**Working directory:** all commands after installation are run from the directory containing `cases/`, `models/`, `problems/`, `expansions/`, and `mitc_tests/` (normally `continuous-section-field/cuf/mitc/b2_shear_locking`). Do not run them from the repository root.

## 1. What is being reproduced?

The physical object is a cantilever of length `L = 5000 mm`, with a constant `100 × 100 mm` rectangular section. It is fixed at `x = 0` and loaded by `F_z = -100 N` at `(x,y,z) = (5000,0,0)`. The CSF material data specify `E = 75000 MPa` and an isotropic shear law with `nu = 0.33`. Lengths are in **mm**, forces in **N**, stresses and moduli in **MPa**.

Each analysis evaluates the free-end vertical displacement `u_z` at `(5000,0,0)`. Seven uniform longitudinal meshes are tested (`1, 2, 4, 8, 16, 32, 64` **B2 elements**), each with MITC disabled and enabled: **14 runs** in total.

The comparison reference is the Euler–Bernoulli cantilever deflection:

```text
I = 100 * 100^3 / 12 = 8333333.333 mm^4
u_EB = F_z * L^3 / (3 * E * I) = -6.666666667 mm
```

This is a slender-beam reference, **not an exact 3D/CUF solution**. A small difference from Euler–Bernoulli supports the locking assessment but is not by itself proof of complete MITC validity.

## 2. Requirements and installation

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
```

Clone and install the **complete** CSF–CUF solver from the [project repository](https://github.com/giovanniboscu/continuous-section-field):

```bash
git clone --depth 1 https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -e .
python3 -m pip install PyYAML
pip install pypardiso
csf-cuf --help
```

The benchmark also requires the version of the repository implementing the problem adapter `csf.cuf.adapters.problem.c_section_cantilever_point_load`, the output adapter `csf.cuf.adapters.output.post`, and the MITC solver switches shown below. **A Git commit was not recorded for the original archived runs**: the same numerical results on another installation therefore require a compatible solver revision, not just these input files. Record the revision used for any new run (Section 10).

On Windows, create/activate a Python virtual environment with `python -m venv venv` and `venv\Scripts\activate.bat`, and use `python` for Python commands. The `.sh` launchers require a Bash environment (e.g. WSL or Git Bash); the individual `csf-cuf` commands also work in Windows CMD.

## 3. Benchmark directory and file roles

Place the benchmark directory at `cuf/mitc/b2_shear_locking/` within the working repository; retain the paths below. From the repository root:

```bash
cd cuf/mitc/b2_shear_locking
```

```text
README.md                           explanation and results
reproducibility.md                  this procedure
models/mitc_locking_rect_conv_csf.yaml
problems/mitc_locking_rect_conv_point.yaml
expansions/lagrangeL9_v4.py        transverse CUF basis
cases/mitc_locking_rect_B2_N*_*.yaml
mitc_tests/run_all_B2.sh           B2 = 1, 2, 4, 8 (ON/OFF)
mitc_tests/run_extended_B2.sh      B2 = 16, 32, 64 (ON/OFF)
mitc_tests/extend_B2.py            creates the three larger-mesh cases
mitc_tests/audit.py                audits archived cases, responses and logs
mitc_tests/compare_extended.py     computes the convergence table
mitc_tests/plot_B2.py              generates the convergence figure
mitc_tests/logs/                  solver logs
mitc_tests/reports/               numerical tables and audit
output/mitc_locking_rect_B2_N*_*/response.txt
output/mitc_locking_rect_B2_N*_*/  solution checkpoints (.cuf.npz)
```

A **YAML** file is human-readable configuration data. It does not execute the analysis by itself. A `.cuf.npz` file is a saved numerical solution; `response.txt` contains physical response samples from which the reported tip displacement is extracted.

### 3.1 CSF: the physical section and material

[`models/mitc_locking_rect_conv_csf.yaml`](models/mitc_locking_rect_conv_csf.yaml) defines two section stations: `S0` at the beam start and `S1` at the beam end. Both use the same four transverse polygon vertices, from `(-50,-50)` to `(50,50)` mm. Their equality describes a **prismatic** section. The polygon `weight: 75000` carries the elastic-modulus value, while `shear_weight_laws: ['iso(0.33)']` specifies the shear constitutive law used in this example.

CSF gives the physical section and constitutive data. The polygon is **not** a longitudinal B2 finite element. The CSF station coordinate named `z` in this file corresponds to the longitudinal beam coordinate `x` in the CUF problem; the polygon vertex pairs are transverse `(y,z)` coordinates.

### 3.2 Physical load, clamp and Python adapter

[`problems/mitc_locking_rect_conv_point.yaml`](problems/mitc_locking_rect_conv_point.yaml) refers to the CSF model and specifies a point force of `-100 N` at the free-end center. The cantilever adapter applies the clamp at `x = 0` and maps the prescribed force and constraints into the generalized CUF system.

The case file identifies that implementation through:

```yaml
problem:
  yaml: ../problems/mitc_locking_rect_conv_point.yaml
  adapter: csf.cuf.adapters.problem.c_section_cantilever_point_load
```

The YAML states **what** physical problem is requested; the named Python adapter implements **how** the force and constraints enter the discrete equations. For the exact algebraic construction, inspect that adapter in the solver revision being used. This benchmark does not include a separate FEM3D run.

### 3.3 CUF expansion, longitudinal B2 elements and MITC

For example, [`cases/mitc_locking_rect_B2_N64_on.yaml`](cases/mitc_locking_rect_B2_N64_on.yaml) combines the problem, numerical approximation and solver settings:

```yaml
cuf:
  basis: ../expansions/lagrangeL9_v4.py
  order: 2
longitudinal:
  method: finite_element
  basis: lagrange
  order: 1
solver:
  correctionMITC: true
  verifyMITCAssembly: true
```

The **transverse** expansion is the custom L9 implementation (`lagrangeL9_v4.py`). Its `cuf.order: 2` is not the number of longitudinal elements. The **longitudinal** interpolation has `order: 1`: two nodes per element, abbreviated **B2**. The `element_boundaries` array subdivides the normalized longitudinal interval `[0,1]` into the stated number of uniform elements. In these cases the sectional Gauss order is 9 and the longitudinal Gauss order is 15.

`correctionMITC` activates the MITC treatment of selected strain terms. `verifyMITCAssembly` enables an internal assembly diagnostic. For a given mesh count, the paired OFF/ON configurations have the same physical model, load, expansion, mesh and quadrature; the switches, output name, and case name differ. The output adapter is `csf.cuf.adapters.output.post`.

## 4. Verify the archived results without running the solver

In the benchmark directory, with the Python environment active:

```bash
python3 mitc_tests/audit.py
python3 mitc_tests/compare_extended.py
```

- `audit.py` checks the 14 YAML configurations, references to other input files, physical data, tip sampling, solver completion markers, symmetry logs and MITC diagnostics. Its own report is written to `mitc_tests/reports/audit.json`.
- `compare_extended.py` reads the 14 `response.txt` files and writes `mitc_tests/reports/mitc_B2_extended.csv`. It does **not** run the solver.

On the archived results supplied for this benchmark the audit reported **PASS for 14 cases**. Passing the audit means the **archived records agree with the implemented checks**, not that the solver has independently been verified against another finite-element formulation.

## 5. Re-run the numerical cases (solver required)

For **one quick case** (64 elements, MITC ON):

```bash
csf-cuf cases/mitc_locking_rect_B2_N64_on.yaml
```

For the **complete paired convergence series**, Linux/macOS or Bash:

```bash
bash mitc_tests/run_all_B2.sh
bash mitc_tests/run_extended_B2.sh
```

The first launcher runs **B2 = 1, 2, 4, 8** with MITC OFF/ON; the second generates the **B2 = 16, 32, 64** YAML files from the smaller-mesh template, then runs both modes. Runs are sequential, and log files go to `mitc_tests/logs/`. The solver writes `response.txt` and checkpoints beneath `output/<case-name>/`.

A Windows CMD individual run has the form:

```cmd
csf-cuf cases\mitc_locking_rect_B2_N64_on.yaml
```

**Do not rerun the solver simply to check the delivered archive**: Section 4 already does that. Re-running can replace the saved output, which may vary with the solver revision and numerical dependencies. If running a fresh series, preserve the original files first.

## 6. Rebuild tables and plots

After all 14 `response.txt` files exist:

```bash
python3 mitc_tests/compare_extended.py
python3 mitc_tests/plot_B2.py
```

Read the generated table at `mitc_tests/reports/mitc_B2_extended.csv` and the figure at `mitc_tests/reports/mitc_B2_convergence.png`. The plotting script needs Matplotlib; install it with `python3 -m pip install matplotlib` if necessary. For a headless Linux environment, `MPLBACKEND=Agg python3 mitc_tests/plot_B2.py` can be used.

The displacement sample is the row in `response.txt` for `center` at `x/L=1`, `x=5000`, `y=0`, `z=0`. Each `ON` and `OFF` number must refer to **that same physical point**.

The table gives the difference from the Euler–Bernoulli value as:

```text
error_vs_EB_pct = 100 * abs(u_z - u_EB) / abs(u_EB)
```

For three meshes with element counts `N/4`, `N/2` and `N` (uniform halving of element size), the observed difference ratio is:

```text
p_delta = log2(abs((u_(N/4) - u_(N/2)) / (u_(N/2) - u_N)))
```

`p_delta` measures **successive solution differences** and does not assume that Euler–Bernoulli is exact. It may be interpreted as a convergence order only after the asymptotic regime is reached.

## 7. Expected numerical checkpoints

The supplied archived output gives these free-end displacements (mm):

| B2 elements | MITC OFF | MITC ON |
| ---: | ---: | ---: |
| 1 | -0.00708710 | -4.46440963 |
| 2 | -0.02823923 | -5.32304167 |
| 4 | -0.11144445 | -6.04742888 |
| 8 | -0.42380388 | -6.36966283 |
| 16 | -1.42006314 | -6.52174394 |
| 32 | -3.45574606 | -6.59488122 |
| 64 | -5.39772621 | -6.62980268 |

For `N=64`, MITC ON differs from Euler–Bernoulli by about **0.553%** and MITC OFF by about **19.03%**. Across the finest three-mesh groups, the ON refinement indicator is near **1.06–1.08**. These results are evidence of **marked locking reduction in this benchmark**, not a validation for all geometries and loading conditions.

## 8. Understand the solver diagnostics

Consult the corresponding file in `mitc_tests/logs/`. Useful markers include:

```text
[verification] global stiffness symmetry
[MITC assembly verify]
[3/4] solve complete
[kkt-solution-diagnostic]
```

The global symmetry report checks the assembled global stiffness matrix, using the relative metric and tolerance printed by that solver version. The MITC assembly diagnostic in the supplied ON logs reports **pair `(1,1)`**, once per B2 element: this is an **internal block-level comparison**, not a check of every CUF pair or proof of the complete formulation. The KKT residual concerns numerical solution of the constrained algebraic system; a small residual does not establish the absence of shear locking.

The archived records have 127 MITC pair checks in total across the ON series (`1+2+4+8+16+32+64`), all reported as PASS. No independent MITC patch test, full-pair audit, reaction/energy balance or 3D reference is claimed here.

## 9. Typical problems

- **`csf-cuf: command not found`** - activate the environment and verify `csf-cuf --help` from the installed project.
- **Missing adapter/module** - check that the installed repository revision includes `c_section_cantilever_point_load`, `csf.cuf.adapters.output.post`, and the MITC options. A CUF-only source snapshot is not a full CSF installation.
- **Missing expansion or referenced YAML** - check the directory tree in Section 3 and run from the benchmark directory, not from `mitc_tests/` or the project root.
- **Different floating-point results** - record the solver commit, Python version, installed packages and chosen linear solver. Compare physical displacements with a stated tolerance rather than expecting bitwise identity across environments.

## 10. Record the environment and provenance

For a new independent reproduction, retain the exact source revision and environment together with the YAML, logs, results, and analysis commands. From the **repository root**:

```bash
git rev-parse HEAD
python3 --version
python3 -m pip freeze > mitc_environment_freeze.txt
```

Also record the launch commands, the output paths and the point `(5000,0,0)` used for the comparison. The original archived solver commit is not identified by these files; record the Git revision for any independent reproduction.

**Scope of this guide:** a complete, auditable MITC B2 convergence benchmark using the installed CSF–CUF solver. It demonstrates the numerical effect of enabling MITC for the specified rectangular cantilever. Independent verification of the general MITC formulation would require additional tests.
