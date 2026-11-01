# Plot Results

This directory collects the graphical post-processing results generated for the CSF-CUF analysis of the tapered I-shaped beam.

The results are organized according to the type of representation:

1. **Longitudinal boundary results** - evolution of selected quantities along the beam axis.
2. **Transverse-section maps at `x = 500`** - reconstructed displacement, strain, and stress fields over the complete cross-section.
3. **Perimeter results at `x = 5`** - selected quantities reconstructed along the boundaries of individual CSF polygons.
4. **Complete perimeter analysis of `polygon_008` at `x = 500`** - all strain and stress components evaluated along the same polygon boundary.

Each result is displayed directly in this page.  
A direct link to the corresponding `.webp` file is also provided below each figure.

> **Note on FEM3D results**  
> The FEM3D curves shown here correspond to the raw, non-averaged element-wise results. No nodal smoothing or stress/strain averaging has been applied. Therefore, multiple traces may appear along the same geometric boundary when adjacent solid elements provide slightly different reconstructed values at shared locations. These differences are intentionally retained in order to preserve the original FEM3D output and avoid introducing additional post-processing into the comparison with the CSF-CUF solution.

---

# 1. Longitudinal boundary results

The following plots show the evolution of selected displacement, strain, and stress components along the longitudinal direction of the beam.

Each quantity is evaluated on the corresponding physical boundary portion identified in the figure name.

These plots provide a direct representation of the evolution of the solution along the beam axis and complement the transverse-section results shown later.

## `longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1`

### epsilon yy along boundary part01

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/epsilon_yy_along_boundary_part01.webp" alt="epsilon yy along boundary part01" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/epsilon_yy_along_boundary_part01.webp)

### gamma xy along boundary part02

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/gamma_xy_along_boundary_part02.webp" alt="gamma xy along boundary part02" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/gamma_xy_along_boundary_part02.webp)

### gamma yz along boundary part02

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/gamma_yz_along_boundary_part02.webp" alt="gamma yz along boundary part02" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/gamma_yz_along_boundary_part02.webp)

### sigma yy along boundary part03

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/sigma_yy_along_boundary_part03.webp" alt="sigma yy along boundary part03" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/sigma_yy_along_boundary_part03.webp)

### tau xy along boundary part04

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/tau_xy_along_boundary_part04.webp" alt="tau xy along boundary part04" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/tau_xy_along_boundary_part04.webp)

### tau yz along boundary part04

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/tau_yz_along_boundary_part04.webp" alt="tau yz along boundary part04" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/tau_yz_along_boundary_part04.webp)

### uy along boundary part05

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/uy_along_boundary_part05.webp" alt="uy along boundary part05" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/longitudinal/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/uy_along_boundary_part05.webp)

---

# 2. Transverse-section field maps at x = 500

The following plots show the reconstructed CSF-CUF fields over the complete physical cross-section at

**x = 500**.

The section is therefore kept fixed while the spatial variation of each mechanical quantity over the transverse domain is examined.

The complete set includes:

- displacement components `ux`, `uy`, `uz`;
- normal strains `epsilon_xx`, `epsilon_yy`, `epsilon_zz`;
- shear strains `gamma_xy`, `gamma_xz`, `gamma_yz`;
- normal stresses `sigma_xx`, `sigma_yy`, `sigma_zz`;
- shear stresses `tau_xy`, `tau_xz`, `tau_yz`;
- transverse shear-stress vector field.

## `maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500`

### Strain fields

| epsilon xx | epsilon yy |
|---|---|
| <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/epsilon_xx_transverse.webp" width="100%"> | <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/epsilon_yy_transverse.webp" width="100%"> |
| [Download epsilon_xx](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/epsilon_xx_transverse.webp) | [Download epsilon_yy](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/epsilon_yy_transverse.webp) |

| epsilon zz | gamma xy |
|---|---|
| <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/epsilon_zz_transverse.webp" width="100%"> | <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/gamma_xy_transverse.webp" width="100%"> |
| [Download epsilon_zz](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/epsilon_zz_transverse.webp) | [Download gamma_xy](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/gamma_xy_transverse.webp) |

| gamma xz | gamma yz |
|---|---|
| <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/gamma_xz_transverse.webp" width="100%"> | <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/gamma_yz_transverse.webp" width="100%"> |
| [Download gamma_xz](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/gamma_xz_transverse.webp) | [Download gamma_yz](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/gamma_yz_transverse.webp) |

### Stress fields

| shear stress vector | sigma xx |
|---|---|
| <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/shear_stress_vector_transverse.webp" width="100%"> | <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/sigma_xx_transverse.webp" width="100%"> |
| [Download shear vector](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/shear_stress_vector_transverse.webp) | [Download sigma_xx](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/sigma_xx_transverse.webp) |

| sigma yy | sigma zz |
|---|---|
| <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/sigma_yy_transverse.webp" width="100%"> | <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/sigma_zz_transverse.webp" width="100%"> |
| [Download sigma_yy](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/sigma_yy_transverse.webp) | [Download sigma_zz](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/sigma_zz_transverse.webp) |

| tau xy | tau xz |
|---|---|
| <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/tau_xy_transverse.webp" width="100%"> | <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/tau_xz_transverse.webp" width="100%"> |
| [Download tau_xy](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/tau_xy_transverse.webp) | [Download tau_xz](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/tau_xz_transverse.webp) |

### Displacement and remaining shear component

| tau yz | ux |
|---|---|
| <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/tau_yz_transverse.webp" width="100%"> | <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/ux_transverse.webp" width="100%"> |
| [Download tau_yz](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/tau_yz_transverse.webp) | [Download ux](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/ux_transverse.webp) |

| uy | uz |
|---|---|
| <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/uy_transverse.webp" width="100%"> | <img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/uz_transverse.webp" width="100%"> |
| [Download uy](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/uy_transverse.webp) | [Download uz](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/maps/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/uz_transverse.webp) |

---

# 3. Selected perimeter results at x = 5

The following figures show selected reconstructed quantities along the physical boundaries of individual CSF polygons at

**x = 5**.

This representation is complementary to the full transverse maps: instead of displaying the complete sectional field, the solution is sampled and plotted along a specific polygon boundary.

## Polygon 001 - gamma xz

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_001/gamma_xz_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_001/gamma_xz_along_perimeter.webp)

## Polygon 002 - epsilon zz

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_002/epsilon_zz_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_002/epsilon_zz_along_perimeter.webp)

## Polygon 003 - epsilon xx

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_003/epsilon_xx_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_003/epsilon_xx_along_perimeter.webp)

## Polygon 003 - tau xz

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_003/tau_xz_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_003/tau_xz_along_perimeter.webp)

## Polygon 004 - sigma zz

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_004/sigma_zz_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_004/sigma_zz_along_perimeter.webp)

## Polygon 005 - sigma xx

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_005/sigma_xx_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_005/sigma_xx_along_perimeter.webp)

## Polygon 006 - gamma xy

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_006/gamma_xy_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_006/gamma_xy_along_perimeter.webp)

## Polygon 007 - epsilon yy

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_007/epsilon_yy_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_007/epsilon_yy_along_perimeter.webp)

## Polygon 007 - tau yz

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_007/tau_yz_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_007/tau_yz_along_perimeter.webp)

## Polygon 008 - tau xy

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_008/tau_xy_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_008/tau_xy_along_perimeter.webp)

## Polygon 009 - sigma yy

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_009/sigma_yy_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_5/perimeter/boundary/polygon_009/sigma_yy_along_perimeter.webp)

---

# 4. Complete perimeter analysis of polygon 008 at x = 500

The following results keep both the longitudinal station and the CSF polygon fixed:

- longitudinal station: **x = 500**;
- sectional domain: **polygon_008**.

All available strain and stress components are then reconstructed along the same physical perimeter.

This representation makes it possible to compare the different mechanical quantities without changing either the cross-sectional station or the boundary being examined.

## 4.1 Strain components

The first six figures contain the three normal strains

`epsilon_xx`, `epsilon_yy`, `epsilon_zz`

and the three engineering shear strains

`gamma_xy`, `gamma_xz`, `gamma_yz`.

### epsilon xx

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/epsilon_xx_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/epsilon_xx_along_perimeter.webp)

### epsilon yy

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/epsilon_yy_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/epsilon_yy_along_perimeter.webp)

### epsilon zz

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/epsilon_zz_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/epsilon_zz_along_perimeter.webp)

### gamma xy

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/gamma_xy_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/gamma_xy_along_perimeter.webp)

### gamma xz

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/gamma_xz_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/gamma_xz_along_perimeter.webp)

### gamma yz

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/gamma_yz_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/gamma_yz_along_perimeter.webp)

## 4.2 Stress components

The following six figures contain the three normal stresses

`sigma_xx`, `sigma_yy`, `sigma_zz`

and the three shear stresses

`tau_xy`, `tau_xz`, `tau_yz`.

### sigma xx

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/sigma_xx_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/sigma_xx_along_perimeter.webp)

### sigma yy

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/sigma_yy_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/sigma_yy_along_perimeter.webp)

### sigma zz

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/sigma_zz_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/sigma_zz_along_perimeter.webp)

### tau xy

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/tau_xy_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/tau_xy_along_perimeter.webp)

### tau xz

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/tau_xz_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/tau_xz_along_perimeter.webp)

### tau yz

<img src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/tau_yz_along_perimeter.webp" width="100%">

[Download file](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/I-Shape_L/plot_results/perimeters/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1/transverse_x_500/perimeter/boundary/polygon_008/tau_yz_along_perimeter.webp)
