## Coordinate systems and displacement components

The displacement components reported in this example retain the notation of Carrera and Giunta (2010): **u<sub>z</sub> denotes the longitudinal displacement**.

### CSF and CUF coordinate systems

CSF describes the cross-section in the (X, Y) plane, with Z along the beam axis. The CSF–CUF solver uses x along the beam axis and (y, z) within the cross-section.

| Physical direction | CSF coordinate | CUF solver coordinate |
| --- | --- | --- |
| Longitudinal | Z | x |
| First transverse direction | X | y |
| Second transverse direction | Y | z |

The coordinate correspondence is therefore **x = Z, y = X, z = Y**.

### Displacement components in the comparison plots

The same transformation is applied to both CUF and FEM3D displacement results to express them in the paper convention:

| Component in the plots (paper notation) | Component in the solver | CSF direction |
| --- | --- | --- |
| u<sub>x</sub> | −u<sub>z</sub> | −Y |
| u<sub>y</sub> | u<sub>y</sub> | +X |
| u<sub>z</sub> | u<sub>x</sub> | +Z (longitudinal) |

Thus, the longitudinal displacement is labelled **u<sub>z</sub> in the plots** and **u<sub>x</sub> in the solver**.

### Point coordinates and plot abscissa

Point coordinates in plot titles and CSV coordinate columns remain in the **CSF reference system (X, Y, Z)**.

The plot abscissa **x/L** uses the solver's longitudinal coordinate and is equivalent to **Z/L** in CSF, where L is the beam length.

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
