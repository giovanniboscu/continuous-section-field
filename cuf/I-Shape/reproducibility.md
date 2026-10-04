# CSF-CUF I-Shape Reproducibility

---
## Command summary
Prerequisite: Python 3 is required, together with the venv and pip modules.
Starting from a new system:

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

pip show csfpy
csf-cuf --help

export MPLBACKEND=Agg

cd cuf/I-Shape

csf-cuf cases/prism/lagrange_table9_N18_E1.yaml
csf-cuf cases/taper/lagrange_table9_N18_E1.yaml

cd fem3d

# Optional: regenerate the FEM3D reference solutions
./startfem_prism.sh
./startfem_tap.sh

# Generate the prismatic/tapered CSF-CUF vs FEM3D plots
./plot_prism_taper.sh
```

> For Windows installation and execution commands, see [Reproducibility on Windows](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/reproducibility_windows.md).

The FEM3D reference solutions already included in the repository are used, the two `startfem_*.sh` commands can be omitted.

---

# I-Shape - Prismatic vs. Tapered

This document provides a command-by-command guide to reproduce the **prismatic and tapered I-shaped beam comparison** contained in:

`cuf/I-Shape`

The two CSF-CUF analyses use the same loading and boundary-condition scheme. The prismatic case uses the reference I-shaped geometry, while the tapered case progressively reduces the clear web height by 80%.
The comparison with an independent three-dimensional finite-element model (FEM3D) can be reproduced as well. The FEM3D reference solutions are already included in the repository, so rerunning the 3D analyses is optional.

---
## 1. System prerequisites

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
```

---

## 2. Clone the repository

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
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

The installation registers the `csf-cuf` command.

Verify the installation:

```bash
pip show csfpy
csf-cuf --help
```

For a headless environment, `matplotlib` can be prevented from opening graphical windows with:

```bash
export MPLBACKEND=Agg
```

From this point onward, the virtual environment is assumed to remain active.

---
## 4. Move to the I-Shape example

From the repository root:

```bash
cd cuf/I-Shape
```

All subsequent commands in this document are executed from this directory unless explicitly stated otherwise.

---

## 5. Run the CSF-CUF analyses

### Prismatic I-shaped beam

As a reference, on a machine equipped with an AMD Ryzen 7 8745HS with Radeon 780M Graphics and 20 GB of RAM, each analysis requires approximately 10 minutes.

```bash
csf-cuf cases/prism/lagrange_table9_N18_E1.yaml
```

The results are written under:

```text
output/prism/lagrange/table9_N18_E1/
```

### Tapered I-shaped beam

```bash
csf-cuf cases/taper/lagrange_table9_N18_E1.yaml
```

The results are written under:

```text
output/taper/lagrange/table9_N18_E1/
```

The two analyses use the same problem definition and the same CUF approximation settings. The difference between them is the section geometry.

The prismatic model keeps the same I-shaped cross-section along the beam.
The tapered model starts from the same section and progressively reduces the clear web height from $a = 100\ \mathrm{mm}$ to $a = 20\ \mathrm{mm}$, corresponding to an 80% reduction.
>**Performance note.** The FEM model uses section and material data that
are pre-computed before the analysis. In CSF-CUF, instead, the solver
queries the continuous section field on demand during numerical
integration. This preserves the separation between the physical
description and the numerical solver, but introduces a significantly
higher computational cost. Therefore, execution times should not be
compared directly on the basis of the number of DOFs alone. Moreover,
the two approaches produce different forms of numerical output: while
the FEM solution is intrinsically associated with its spatial
discretization, CSF-CUF reconstructs the displacement field as the
continuous functions `u_x(x,y,z)`, `u_y(x,y,z)`, and `u_z(x,y,z)`. Once
the solution has been computed, these functions can be evaluated at
arbitrary points of the beam domain without introducing an additional
spatial interpolation of the computed solution.

---
## 6. FEM3D reference solutions

The independent FEM3D reference solutions used for the comparison are already included in the repository.

Therefore, this step can be skipped if the objective is only to reproduce the CSF-CUF/FEM3D comparison plots.

To regenerate the FEM3D solutions, move to:

```bash
cd fem3d
```

### Prismatic FEM3D model

```bash
./startfem_prism.sh
```

This generates:

```text
output/fem3d_prism.npz
```

### Tapered FEM3D model

```bash
./startfem_tap.sh
```

This generates:

```text
output/fem3d_taper.npz
```

After these commands, remain in the `fem3d` directory for the plotting step.

---
## 7. Gen plots
<img width="1037" height="589" alt="Screenshot 2026-10-04 at 17 42 19" src="https://github.com/user-attachments/assets/bbd090c3-34ab-491c-bdff-a8e77366b1e5" />

From:

```text
continuous-section-field/cuf/I-Shape/fem3d
```

run:

```bash
./plot_prism_taper.sh
```

The script compares:

- the prismatic CSF-CUF solution with the prismatic FEM3D solution;
- the tapered CSF-CUF solution with the tapered FEM3D solution.

It generates the displacement comparison plots for the vertices of the section polygons.

The plots are written to:

```text
prism_vs_taper/
```

The resulting directory contains the plots used in the I-Shape comparison documentation.

---
## 8. Using the precomputed FEM3D solutions

Because the FEM3D results are already stored in the repository, the shortest reproduction path is:

```bash
cd continuous-section-field/cuf/I-Shape

csf-cuf cases/prism/lagrange_table9_N18_E1.yaml
csf-cuf cases/taper/lagrange_table9_N18_E1.yaml

cd fem3d
./plot_prism_taper.sh
```

This reruns the two CSF-CUF analyses and generates the comparison plots using the FEM3D reference solutions already present in `fem3d/output/`.

ered FEM3D Comparison Plots

The following figures show the CSF-CUF/FEM3D displacement comparisons for all geometric vertices of the three I-section polygons.

## Top flange
### Vertex 0

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v0_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v0_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v0_uz.png" width="50%" />
</p>

### Vertex 1

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v1_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v1_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v1_uz.png" width="50%" />
</p>

### Vertex 2

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v2_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v2_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v2_uz.png" width="50%" />
</p>

### Vertex 3

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v3_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v3_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/top_flange_v3_uz.png" width="50%" />
</p>

## Web
### Vertex 0

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v0_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v0_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v0_uz.png" width="50%" />
</p>

### Vertex 1

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v1_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v1_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v1_uz.png" width="50%" />
</p>

### Vertex 2

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v2_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v2_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v2_uz.png" width="50%" />
</p>

### Vertex 3

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v3_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v3_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/web_v3_uz.png" width="50%" />
</p>

## Bottom flange
### Vertex 0

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v0_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v0_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v0_uz.png" width="50%" />
</p>

### Vertex 1

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v1_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v1_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v1_uz.png" width="50%" />
</p>

### Vertex 2

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v2_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v2_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v2_uz.png" width="50%" />
</p>

### Vertex 3

**$u_x$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v3_ux.png" width="50%" />
</p>

**$u_y$**

<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v3_uy.png" width="50%" />
</p>

**$u_z$**
<p align="center">
  <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape/fem3d/prism_vs_taper/bottom_flange_v3_uz.png" width="50%" />
</p>
