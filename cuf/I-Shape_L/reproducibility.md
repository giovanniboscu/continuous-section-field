
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

The partial set of generated comparison plots can be viewed directly here:

[View all generated plots](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/plot_results/README.md)


---

## 8. Run the multi-section equilibrium diagnostic

Still from:

```text
continuous-section-field/cuf/I-Shape_L
```

execute:

```bash
./equilibrium_multisection_components.sh
```

on windows
```bash
python compare_fem3d_cuf_strong_equilibrium.py `
  --fem fem3d/output/fem3d_taper.npz `
  --cuf output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz `
  --csf models/carrera_i_shaped_taper80_l9_web3.yaml `
  --sections 40 `
  --xmin 0.01 `
  --xmax 0.99 `
  --output-dir diagnostics/equilibrium_multisection_components

```



This launcher evaluates the equilibrium quantities over multiple beam sections and generates the data required for the FEM3D/CSF-CUF equilibrium comparison.

The diagnostic evaluates the three components of the stress-divergence residual:

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
\frac{\partial \sigma_{zz}}{\partial z}.
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
}.
```

---

## 9. Compare FEM3D and CSF-CUF equilibrium results

After the multi-section data have been generated, remain in:

```text
continuous-section-field/cuf/I-Shape_L
```

and execute:

```bash
python3 compare_fem3d_cuf_strong_equilibrium.py
```

On Windows:

```cmd
python compare_fem3d_cuf_strong_equilibrium.py
```

The script reads the FEM3D and CSF-CUF equilibrium data generated by the previous analysis and produces the direct comparison between the two formulations.

The comparison includes:

- the first equilibrium residual, `div_x`;
- the second equilibrium residual, `div_y`;
- the third equilibrium residual, `div_z`;
- the total residual norm, `div_norm`;
- the evolution of the residuals along the selected beam sections;
- the FEM3D/CUF residual ratios.

This is the script used to obtain the quantitative FEM3D/CSF-CUF equilibrium comparison reported for the tapered I-shaped benchmark.

For the FEM3D mesh-convergence study and the reference mesh adopted in the subsequent comparisons, see:

[FEM3D mesh-convergence criterion](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/FEM3Dmesh-convergence-criterion.md)

---

## 10. Complete reproduction sequence

After completing the installation prerequisites, the complete Linux workflow is:

```bash
cd continuous-section-field/cuf/I-Shape_L

# 1. CSF-CUF analysis
csf-cuf cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml

# 2. FEM3D reference solution
cd fem3d
./startfem_tap.sh

# 3. Return to I-Shape_L
cd ..

# 4. Generate CSF-CUF/FEM3D comparison plots
./generate_all_plots.sh

# 5. Generate multi-section equilibrium data
./equilibrium_multisection_components.sh

# 6. Compare FEM3D and CSF-CUF equilibrium results
python3 compare_fem3d_cuf_strong_equilibrium.py
```

The execution sequence is therefore:

```text
CSF-CUF analysis
       |
       v
FEM3D reference solution
       |
       v
comparison plots
       |
       v
multi-section equilibrium data
       |
       v
FEM3D / CSF-CUF equilibrium comparison
```

---

## 11. Shortest reproduction path

If the repository and Python environment are already configured:

```bash
cd continuous-section-field/cuf/I-Shape_L

csf-cuf cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml

cd fem3d
./startfem_tap.sh
cd ..

./generate_all_plots.sh
./equilibrium_multisection_components.sh
python3 compare_fem3d_cuf_strong_equilibrium.py
```

If the FEM3D reference solution is already available:

```bash
cd continuous-section-field/cuf/I-Shape_L

csf-cuf cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml

./generate_all_plots.sh
./equilibrium_multisection_components.sh
python3 compare_fem3d_cuf_strong_equilibrium.py
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
cd ..

# Comparison plots
./generate_all_plots.sh

# Multi-section equilibrium data
./equilibrium_multisection_components.sh

# FEM3D / CSF-CUF equilibrium comparison
python3 compare_fem3d_cuf_strong_equilibrium.py
```

The complete analysis chain is:

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
multi-section equilibrium data
   |
   v
FEM3D / CSF-CUF equilibrium comparison
```
