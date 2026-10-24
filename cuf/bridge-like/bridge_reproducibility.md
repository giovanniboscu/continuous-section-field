# CSF-CUF Bridge Benchmark Reproducibility

This document provides a command-by-command procedure to reproduce the **bridge-section bending and torsion benchmarks** using scaled Lagrange transverse expansions. It follows the organization of the C-shape reproducibility guide, adapted to the cases, solution checkpoints, equilibration studies, and plots provided for this benchmark.

All commands are shown relative to the benchmark directory that contains `cases/`, `models/`, `output/`, and `plot_traverse.sh`. The commands should be run from that directory after installing the repository. In the steps below, `cuf/<bridge-benchmark-directory>` is a placeholder, **not a literal repository path**: use the actual directory containing these inputs.

---

## 1. System prerequisites

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
```

On Windows, install Python 3 and Git and ensure that they are available on `PATH`. Bash `.sh` launchers require a Bash-compatible environment (for example, WSL or Git Bash); otherwise use the explicit Python commands below.

---

## 2. Clone the repository

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
```

For strict reproducibility, record the checkout revision:

```bash
git rev-parse HEAD
```

---

## 3. Virtual environment and package installation

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

If required by the solver selected in the YAML cases, and supported on the platform:

```bash
python3 -m pip install pypardiso
```

Verify installation:

```bash
csf-cuf --help
```

Windows (CMD):

```cmd
python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .
csf-cuf --help
```

For headless plotting on Linux/macOS, optionally set:

```bash
export MPLBACKEND=Agg
```

No independent FEM3D regeneration is specified in this guide: the `FEM10` suffix is part of the supplied case names and should not be taken, by itself, as an instruction to run a separate FEM3D analysis.

---

## 4. Move to the benchmark directory

From the repository root, navigate to **the directory containing**:

```text
cases/
models/bridge_geometry.yaml
plot_traverse.sh
```

All subsequent commands assume this directory as the current working directory. In particular, `cases/...`, `models/...`, and `output/...` are resolved relative to it.

The benchmark configuration separates:

- **CSF geometry/material model:** `models/bridge_geometry.yaml` (used in the plotting commands).
- **CUF cases:** YAML files in `cases/`, defining the load problem, longitudinal discretization, transverse expansion order, solver settings, and output configuration as specified by each file.
- **Results:** one `output/<case-name>/` directory per run.
- **Post-processing:** `plot_traverse.sh` or `csf.cuf.tools.plot_strain_stress_boundary_v10`.

### Available convergence series

**Bending:**

```text
cases/bending_scaled_lagrange_N04_FEM10.yaml
cases/bending_scaled_lagrange_N10_FEM10.yaml
cases/bending_scaled_lagrange_N11_FEM10.yaml
cases/bending_scaled_lagrange_N12_FEM10.yaml
cases/bending_scaled_lagrange_N13_FEM10.yaml
cases/bending_scaled_lagrange_N14_FEM10.yaml
cases/bending_scaled_lagrange_N15_FEM10.yaml
```

**Torsion:**

```text
cases/torsion_scaled_lagrange_N10_FEM10.yaml
cases/torsion_scaled_lagrange_N11_FEM10.yaml
cases/torsion_scaled_lagrange_N12_FEM10.yaml
cases/torsion_scaled_lagrange_N13_FEM10.yaml
cases/torsion_scaled_lagrange_N14_FEM10.yaml
cases/torsion_scaled_lagrange_N15_FEM10.yaml
```

Here `N04` through `N15` label the transverse expansion order/family variant in the supplied case series. Verify the precise expansion definition in each YAML. The series allows an **order-convergence study**, while the multiple `eq` outputs within a single run allow an **equilibration-sensitivity/stability study**. These are different checks and should not be conflated.

---

## 5. Run the CSF-CUF analyses

Run the highest-order torsion and bending examples:

```bash
csf-cuf cases/torsion_scaled_lagrange_N15_FEM10.yaml
csf-cuf cases/bending_scaled_lagrange_N15_FEM10.yaml
```

To reproduce the full bending series (Linux/macOS Bash):

```bash
for n in 04 10 11 12 13 14 15; do
  csf-cuf "cases/bending_scaled_lagrange_N${n}_FEM10.yaml"
done
```

To reproduce the full torsion series:

```bash
for n in 10 11 12 13 14 15; do
  csf-cuf "cases/torsion_scaled_lagrange_N${n}_FEM10.yaml"
done
```

On Windows CMD, invoke each case individually, using the same `csf-cuf cases/...yaml` syntax. All cases should be run from the benchmark directory.

---

## 6. Generated solution files and equilibration repeats

For the highest-order bending case, an example output tree is:

```text
output/
└── bending_scaled_lagrange_N15/
    ├── carrera_bridge_bending_scaled_lagrange_N15_eq1.cuf.npz
    ├── carrera_bridge_bending_scaled_lagrange_N15_eq2.cuf.npz
    ├── carrera_bridge_bending_scaled_lagrange_N15_eq3.cuf.npz
    ├── carrera_bridge_bending_scaled_lagrange_N15_eq4.cuf.npz
    ├── carrera_bridge_bending_scaled_lagrange_N15_eq5.cuf.npz
    ├── response_eq1.txt
    ├── response_eq2.txt
    ├── response_eq3.txt
    ├── response_eq4.txt
    └── response_eq5.txt
```

The lower-order bending run has the same basic structure, for example:

```text
output/bending_scaled_lagrange_N04/
    carrera_bridge_bending_scaled_lagrange_N04_eq1.cuf.npz
    ...
    carrera_bridge_bending_scaled_lagrange_N04_eq5.cuf.npz
    response_eq1.txt
    ...
    response_eq5.txt
```

- **`.cuf.npz` checkpoints** contain the detailed numerical solution for each equilibration (`eq1` to `eq5`) and are the inputs to the visualization tool.
- **`response_eq*.txt` files** contain the corresponding text response reports.
- The five equilibrations are repeated **within a given case** to assess sensitivity to the equilibration procedure. They are not five different transverse expansion orders.

The directory and file structure shown is representative of the supplied bending runs; other files or output options may also be present. Torsion runs should be inspected for their actual checkpoint names instead of assuming the bending prefix.

---

## 7. Check convergence and numerical stability

Perform **two independent comparisons**.

### 7.1 Convergence with transverse expansion order

For bending, compare `N04`, `N10`, `N11`, `N12`, `N13`, `N14`, and `N15`. For torsion, compare `N10` through `N15`. At corresponding physical sampling locations, track for example:

- displacements and rotations/response quantities where available;
- strain and stress components, especially near section boundaries;
- changes in field distributions when increasing the expansion order.

Keep the same load case, geometry, longitudinal discretization, evaluation locations, and selected equilibration index when comparing orders, subject to the actual YAML settings. Compare **physical fields**, rather than raw coefficient vectors, since basis size and conditioning can change with `N`.

### 7.2 Sensitivity across the five equilibrations

For a fixed case (for example, bending `N15`), compare `eq1` through `eq5` using its checkpoints and response reports. Check:

- finiteness of reported values (`NaN`/`Inf` detection);
- consistency of displacements and their gradients at identical points;
- sensitivity of strains and stresses, including near corners and free boundaries;
- consistency of global response quantities among the five equilibrations.

Small differences in physical fields across `eq1`–`eq5` support **empirical insensitivity to the tested equilibrations**, but do not by themselves establish the condition number of the assembled stiffness matrix or prove stability for every mesh/order. Matrix conditioning, residual norms, and backward-error checks require additional solver diagnostics if available.

For quantitative comparisons, report the points and components used, the reference scale, and the numerical definition of the absolute/relative error; do not infer convergence solely from visual overlap.

---

## 8. Generate displacement and stress plots

If the provided launcher is available, invoke it from the benchmark directory:

```bash
bash plot_traverse.sh
```

Alternatively, plot an N15 bending checkpoint directly.

**Transverse maps at `x = 20`:**

```bash
python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml models/bridge_geometry.yaml \
  --checkpoint output/bending_scaled_lagrange_N15/carrera_bridge_bending_scaled_lagrange_N15_eq1.cuf.npz \
  --transverse-x 20 \
  --transverse-grid 120 \
  --transverse-vector-grid 50
```

**Default longitudinal boundary/vertex plots:**

```bash
python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml models/bridge_geometry.yaml \
  --checkpoint output/bending_scaled_lagrange_N15/carrera_bridge_bending_scaled_lagrange_N15_eq1.cuf.npz
```

The plots show **displacement and stress quantities along the beam at selected section vertices/boundary locations**, and, with the transverse options, **maps of displacement and stress over the section at `x = 20`**. The exact plot set, component naming, and output directory depend on the installed version of the visualization script.

To plot `eq2` through `eq5`, change the `eq1` suffix in `--checkpoint`. To plot another order, update both the directory and checkpoint filename consistently.

Windows CMD, transverse map (single line):

```cmd
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 --csf-yaml models/bridge_geometry.yaml --checkpoint output/bending_scaled_lagrange_N15/carrera_bridge_bending_scaled_lagrange_N15_eq1.cuf.npz --transverse-x 20 --transverse-grid 120 --transverse-vector-grid 50
```

Windows CMD, default plots:

```cmd
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 --csf-yaml models/bridge_geometry.yaml --checkpoint output/bending_scaled_lagrange_N15/carrera_bridge_bending_scaled_lagrange_N15_eq1.cuf.npz
```

For the exact supported flags and plot-output configuration:

```bash
python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 --help
```

---

## 9. Shortest reproduction path

With the repository installed and from the benchmark directory:

```bash
# Highest-order benchmarks
csf-cuf cases/torsion_scaled_lagrange_N15_FEM10.yaml
csf-cuf cases/bending_scaled_lagrange_N15_FEM10.yaml

# Plots through the supplied launcher
bash plot_traverse.sh
```

Or replace the launcher with either/both explicit plotting commands in Section 8. To study order convergence, execute the additional cases listed in Section 4; to study equilibration sensitivity, compare the five `eq` checkpoints of the **same** case.

---

## 10. Reproducibility record

For each reported figure or table, retain:

1. Git commit (`git rev-parse HEAD`) and Python/package environment (`python3 --version`, `python3 -m pip freeze`).
2. Exact case YAML and geometry/material model used.
3. Analysis type (bending or torsion), expansion order `N`, and equilibration index `eq1`–`eq5`.
4. Exact checkpoint/response file paths, physical evaluation coordinates, and plotted field components.
5. Plotting command (including `--transverse-x` and grid settings, if present).
6. Definition of the comparison metric and reference solution when stating convergence or numerical stability.

**Scope:** This guide documents the provided CSF-CUF benchmark runs and their self-consistency/convergence checks. It does not claim an independent FEM3D comparison or a formal matrix-conditioning analysis without the corresponding reference solutions and diagnostics.
