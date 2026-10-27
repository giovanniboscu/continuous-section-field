# CSF-CUF C-Shape Reproducibility

This document provides a command-by-command guide to reproduce the C-section benchmark described in:

`cuf/c-shape/readme.md`

The example revisits the open C-section beam discussed by E. Carrera and M. Petrolo in *Refined beam elements with only displacement variables and plate/shell capabilities*. The CSF geometry is partitioned into nine quadrilateral domains, each associated with an L9 transverse expansion. The independent FEM3D reference uses three-dimensional H8 (`stdBrick`) elements in OpenSees.

The commands below start from the repository root. After Section 4, they are executed from `cuf/c-shape` unless otherwise indicated. Linux/macOS examples use `python3`; on Windows, use `python` (or `py -3`) as appropriate.

---

## 1. System prerequisites

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
```

On Windows, install Python 3 and Git, make sure they are on `PATH`, and use Command Prompt (CMD) or PowerShell. Linux package-manager instructions do not apply to Windows.

---

## 2. Clone the repository

```bash
git clone --depth 1 https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
```

---

## 3. Virtual environment and package installation

```bash
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -e .
pip install pypardiso
```

The installation registers the `csf-cuf` command. Verify it with:

```bash
pip show csfpy
csf-cuf --help
```

On Windows (CMD), create and activate the environment with:

```cmd
python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .
```

`pypardiso` is an optional solver dependency: install it only where supported and required by the selected solver configuration. Check the case's solver settings on your platform.

For a headless environment (Linux/macOS):

```bash
export MPLBACKEND=Agg
```

To regenerate the FEM3D solution (optional), install OpenSeesPy:

```bash
pip install openseespy
```

In Windows CMD, use `set MPLBACKEND=Agg` for headless plotting. The virtual environment is assumed to remain active in the following steps.

---

## 4. Move to the C-Shape example

From the repository root:

```bash
cd cuf/c-shape
```

All remaining commands are executed from this directory.

The benchmark configuration is split into independent inputs:

- **CSF model:** `models/c_section_chapter9_5_3_9L9_csf.yaml` (geometry and material).
- **Problem:** `problems/c_section_cantilever_point_9L9.yaml` (loading and boundary conditions).
- **Case:** `cases/c_section_table_9_13_lagrangeL9_E10.yaml` (CUF settings and output).
- **Transverse expansion:** `expansions/lagrangeL9_v4.py` (L9 basis loaded by the case).

The reference case uses ten longitudinal finite elements of order 12; `E10` is the case identifier and should not be interpreted as an expansion order.

---

## 5. Run the CSF-CUF analysis

```bash
csf-cuf cases/c_section_table_9_13_lagrangeL9_E10.yaml
```

The case configures a polygon-wise L9 expansion, with shared transverse degrees of freedom at coincident interpolation points, and saves the solver results under:

```text
output/c_section_table_9_13_lagrangeL9_v4_E10/
```

The checkpoint used by the comparison tools is:

```text
output/c_section_table_9_13_lagrangeL9_v4_E10/c_section_table_9_13_lagrangeL9_v4_E10_eq1.cuf.npz
```

The file corresponds to the first equilibration iteration; the YAML also requests subsequent iterations. Use the matching checkpoint if comparing another iteration.

---

## 6. FEM3D reference solution (optional regeneration)

The FEM3D baseline can be generated using the provided shell script (where available):

```bash
./fem3dbaseline.sh
```

Alternatively, run the underlying command **from `cuf/c-shape`**. These exact model, problem, and mesh parameters define the baseline used here:

```bash
python3 fem3d/run_c_section_table_9_13_fem3d.py \
  models/c_section_chapter9_5_3_csf.yaml \
  problems/c_section_table_9_13.yaml \
  fem3d/c_section_table_9_13_a.npz \
  --nx 200 \
  --ny-top-free 18 \
  --ny-bottom-free 18 \
  --ny-web 10 \
  --nz-flange 10 \
  --nz-web 18
```

**Windows (Command Prompt):** run the same command on one line (no Bash `\` continuations):

```cmd
python fem3d/run_c_section_table_9_13_fem3d.py models/c_section_chapter9_5_3_csf.yaml problems/c_section_table_9_13.yaml fem3d/c_section_table_9_13_a.npz --nx 200 --ny-top-free 18 --ny-bottom-free 18 --ny-web 10 --nz-flange 10 --nz-web 18
```

The generated FEM3D file is:

```text
fem3d/c_section_table_9_13_a.npz
```

**Model distinction:** the CSF-CUF case uses `models/c_section_chapter9_5_3_9L9_csf.yaml`, while the FEM3D baseline invocation above deliberately uses `models/c_section_chapter9_5_3_csf.yaml` and `problems/c_section_table_9_13.yaml`. Do not substitute the CUF inputs into the FEM3D command.

Regenerating this fine FEM3D mesh can require significant memory and execution time. If the reference `.npz` is available, this step may be skipped.

---

## 7. Generate CSF-CUF/FEM3D comparison plots

Use the shell launcher if available in the example directory:

```bash
./plots_comparison.sh
```

Or execute the explicit plotting command from `cuf/c-shape`:

```bash
python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml models/c_section_chapter9_5_3_9L9_csf.yaml \
  --checkpoint output/c_section_table_9_13_lagrangeL9_v4_E10/c_section_table_9_13_lagrangeL9_v4_E10_eq1.cuf.npz \
  --fem3d fem3d/c_section_table_9_13_a.npz \
  --fem-stress-from-csf
```

**Windows (Command Prompt):**

```cmd
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 --csf-yaml models/c_section_chapter9_5_3_9L9_csf.yaml --checkpoint output/c_section_table_9_13_lagrangeL9_v4_E10/c_section_table_9_13_lagrangeL9_v4_E10_eq1.cuf.npz --fem3d fem3d/c_section_table_9_13_a.npz --fem-stress-from-csf
```

On Windows the direct commands replace Bash `.sh` launchers; a standard CMD installation does not run `.sh` files natively. The command also works in PowerShell as a single line.

The plotting tool reads the selected CUF checkpoint and the independent FEM3D displacement results. With `--fem-stress-from-csf`, FEM stresses are evaluated from FEM3D displacement derivatives and the CSF constitutive law; they are not derived by averaging CUF stresses. Element-side FEM values are retained without averaging across adjacent elements.

For supported plotting options and any configurable output directory, run:

```bash
python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 --help
```

The reproducible comparison figures are described in [`readme.md`](readme.md) and the [`strain_stress_boundary/`](strain_stress_boundary/) results directory.

---

## 8. Shortest reproduction path

With the repository installed and the FEM3D `.npz` already available, run from `cuf/c-shape`:

```bash
csf-cuf cases/c_section_table_9_13_lagrangeL9_E10.yaml
./plots_comparison.sh
```

Or replace `./plots_comparison.sh` with the explicit plotting command in Section 7. To regenerate the FEM3D reference first, run `./fem3dbaseline.sh` or the exact FEM3D command in Section 6.

On Windows (CMD), after installation and `cd cuf\c-shape`, use these direct commands:

```cmd
csf-cuf cases/c_section_table_9_13_lagrangeL9_E10.yaml
python fem3d/run_c_section_table_9_13_fem3d.py models/c_section_chapter9_5_3_csf.yaml problems/c_section_table_9_13.yaml fem3d/c_section_table_9_13_a.npz --nx 200 --ny-top-free 18 --ny-bottom-free 18 --ny-web 10 --nz-flange 10 --nz-web 18
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 --csf-yaml models/c_section_chapter9_5_3_9L9_csf.yaml --checkpoint output/c_section_table_9_13_lagrangeL9_v4_E10/c_section_table_9_13_lagrangeL9_v4_E10_eq1.cuf.npz --fem3d fem3d/c_section_table_9_13_a.npz --fem-stress-from-csf
```

The middle command is optional if `fem3d/c_section_table_9_13_a.npz` is already available.

---

## Command summary (Linux/macOS)

From a fresh Ubuntu/Debian system:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git

git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
pip install pypardiso
pip install openseespy  # only for FEM3D regeneration

export MPLBACKEND=Agg
cd cuf/c-shape

# CSF-CUF
csf-cuf cases/c_section_table_9_13_lagrangeL9_E10.yaml

# Optional: regenerate FEM3D baseline (or use the command from Section 6)
./fem3dbaseline.sh

# Generate comparison plots (or use the command from Section 7)
./plots_comparison.sh
```

**Shell script location:** the launcher examples above assume `fem3dbaseline.sh` and `plots_comparison.sh` are in `cuf/c-shape`. If they are elsewhere in your checkout, invoke them by their actual paths or use the explicit commands above. All documented direct commands have their working directory fixed to `cuf/c-shape`.
