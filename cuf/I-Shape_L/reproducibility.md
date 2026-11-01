# DRAFT

# CSF-CUF I-Shape_L Reproducibility

This document provides a command-by-command guide to reproduce the I-shaped tapered-section analysis and the corresponding FEM3D/CSF-CUF comparison workflow contained in:

```text
cuf/I-Shape_L
```

The workflow includes:

- execution of the CSF-CUF tapered I-section case;
- generation of the independent FEM3D reference solution;
- generation of the comparison plots;
- evaluation of the multi-section strong-equilibrium diagnostic.

The commands below start from the repository root. After the installation prerequisites, all analysis commands are executed from:

```text
continuous-section-field/cuf/I-Shape_L
```

Linux/macOS examples use `python3`; on Windows, use `python` or `py -3` as appropriate.

---

## 1. System prerequisites

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
```

On Windows, install Python 3 and Git, make sure they are available on `PATH`, and use Command Prompt or PowerShell.

Linux package-manager instructions do not apply to Windows.

---

## 2. Clone the repository

```bash
git clone --depth 1 https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
```

---

## 3. Virtual environment and package installation

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the project:

```bash
pip install --upgrade pip
pip install -e .
```



```bash
pip install pypardiso
```

The installation registers the `csf-cuf` command.

Verify the installation with:

```bash
pip show csfpy
csf-cuf --help
```

For headless Linux environments:

```bash
export MPLBACKEND=Agg
```

### Windows

From Command Prompt:

```cmd
python -m venv venv
venv\Scripts\activate.bat

python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install openseespy
```

Install `pypardiso` only where supported and required by the selected solver configuration.

For headless plotting in Windows CMD:

```cmd
set MPLBACKEND=Agg
```

The virtual environment is assumed to remain active in the following steps.

---

## 4. Move to the I-Shape_L example

From the repository root:

```bash
cd cuf/I-Shape_L
```

Verify the current working directory if necessary:

```bash
pwd
```

The expected directory is:

```text
continuous-section-field/cuf/I-Shape_L
```

All commands in the following sections are executed relative to this directory unless explicitly stated otherwise.

---

## 5. Run the CSF-CUF tapered I-section analysis

From:

```text
continuous-section-field/cuf/I-Shape_L
```

execute:

```bash
csf-cuf cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml
```

This is the CSF-CUF analysis used by the subsequent comparison and strong-equilibrium post-processing workflow.

The case defines the tapered I-shaped configuration and uses the L9 transverse expansion associated with this benchmark.

The generated CSF-CUF solution is subsequently read by the plotting and equilibrium-analysis scripts described below.

---

## 6. Generate the FEM3D reference solution

The FEM3D model is contained in the `fem3d` subdirectory.

Starting from:

```text
continuous-section-field/cuf/I-Shape_L
```

move into the FEM3D directory:

```bash
cd fem3d
```

Under Linux, generate the FEM3D reference solution with:

```bash
./startfem_tap.sh
```

The script generates the independent three-dimensional FEM reference solution required by the subsequent comparison tools.

After the FEM3D analysis has completed, return to the main `I-Shape_L` directory:

```bash
cd ..
```

Optionally verify the current directory:

```bash
pwd
```

The expected location is again:

```text
continuous-section-field/cuf/I-Shape_L
```

### Important working-directory requirement

`startfem_tap.sh` is executed from:

```text
continuous-section-field/cuf/I-Shape_L/fem3d
```

whereas the post-processing launchers described below are executed from:

```text
continuous-section-field/cuf/I-Shape_L
```

Keeping these working directories unchanged avoids ambiguity in relative file paths used by the scripts.

---

## 7. Generate all comparison plots

Once both the CSF-CUF and FEM3D solutions are available, remain in:

```text
continuous-section-field/cuf/I-Shape_L
```

and execute:

```bash
./generate_all_plots.sh
```

This launcher generates the plots associated with the I-shaped tapered benchmark using the previously computed CSF-CUF and FEM3D results.

The script should therefore be executed only after the required solution files have been generated or are already present.

---

## 8. Run the multi-section strong-equilibrium diagnostic

Still from:

```text
continuous-section-field/cuf/I-Shape_L
```

execute:

```bash
./equilibrium_multisection_components.sh
```

This launcher evaluates the strong-equilibrium diagnostic over multiple beam sections.

The diagnostic compares the FEM3D H8 and CSF-CUF L9 solutions at corresponding physical sampling locations and evaluates the three components of the stress-divergence residual:

```math
(\nabla\cdot\sigma)_x
=
\frac{\partial \sigma_{xx}}{\partial x}
+
\frac{\partial \tau_{xy}}{\partial y}
+
\frac{\partial \tau_{xz}}{\partial z}
```

```math
(\nabla\cdot\sigma)_y
=
\frac{\partial \tau_{xy}}{\partial x}
+
\frac{\partial \sigma_{yy}}{\partial y}
+
\frac{\partial \tau_{yz}}{\partial z}
```

and

```math
(\nabla\cdot\sigma)_z
=
\frac{\partial \tau_{xz}}{\partial x}
+
\frac{\partial \tau_{yz}}{\partial y}
+
\frac{\partial \sigma_{zz}}{\partial z}
```

The corresponding total residual norm is

```math
\|\nabla\cdot\sigma\|
=
\sqrt{
(\nabla\cdot\sigma)_x^2
+
(\nabla\cdot\sigma)_y^2
+
(\nabla\cdot\sigma)_z^2
}
```

The resulting comparison is an element/domain-interior strong-equilibrium diagnostic.

It is a local post-processing measure and should not be interpreted as a proof of global strong-form equilibrium.

---

## 9. Complete reproduction sequence

After completing the installation prerequisites, the complete Linux workflow is:

```bash
cd continuous-section-field/cuf/I-Shape_L

# 1. CSF-CUF analysis
csf-cuf cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml

# 2. FEM3D reference
cd fem3d
./startfem_tap.sh

# 3. Return to I-Shape_L
cd ..
pwd

# 4. Generate CSF-CUF/FEM3D comparison plots
./generate_all_plots.sh

# 5. Run the multi-section strong-equilibrium diagnostic
./equilibrium_multisection_components.sh
```

After:

```bash
cd ..
pwd
```

the working directory must be:

```text
continuous-section-field/cuf/I-Shape_L
```

before executing the final two scripts.

---

## 10. Shortest reproduction path

If the repository and Python environment are already configured, execute:

```bash
cd continuous-section-field/cuf/I-Shape_L

csf-cuf cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml

cd fem3d
./startfem_tap.sh
cd ..

./generate_all_plots.sh
./equilibrium_multisection_components.sh
```

If the FEM3D reference solution has already been generated and the required files are still available, the FEM3D step may be skipped:

```bash
cd continuous-section-field/cuf/I-Shape_L

csf-cuf cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml

./generate_all_plots.sh
./equilibrium_multisection_components.sh
```

---

## Command summary - Linux

From a fresh Ubuntu/Debian installation:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git

git clone --depth 1 https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -e .
pip install pypardiso
pip install openseespy

export MPLBACKEND=Agg

cd cuf/I-Shape_L

# CSF-CUF
csf-cuf cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml

# FEM3D
cd fem3d
./startfem_tap.sh

# Return to I-Shape_L
cd ..

# Comparison plots
./generate_all_plots.sh

# Strong-equilibrium comparison
./equilibrium_multisection_components.sh
```

The execution order is:

```text
CSF-CUF
   |
   v
FEM3D
   |
   v
comparison plots
   |
   v
multi-section strong-equilibrium diagnostic
```

Both numerical solutions must therefore exist before running the final comparison and equilibrium-analysis stages.
