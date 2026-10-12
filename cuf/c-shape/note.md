# C-section benchmark – CSF–CUF with polygon-wise L9 expansion

## Reference problem

This example revisits the open C-section beam described by **E. Carrera and M. Petrolo**, *Refined beam elements with only displacement variables and plate/shell capabilities*, Section 4.3.

The objective is to reproduce the C-section geometry and the **nine-domain L9 transverse layout** within the CSF–CUF framework. The section is represented by nine adjacent quadrilateral polygons: five along the upper flange, one along the web, and three along the lower flange.

The main section dimensions follow the reference proportions: height \(h=1000\,\mathrm{mm}\), thickness \(t=100\,\mathrm{mm}\), upper-flange width \(b_2=1000\,\mathrm{mm}\), and lower-flange width \(b_1=500\,\mathrm{mm}\). The prismatic beam length is \(L=20000\,\mathrm{mm}\). The isotropic material has \(E=75000\,\mathrm{MPa}\) and \(\nu=0.33\).

The beam is cantilevered, with a transverse concentrated force of −1 N applied at the free end.

> The paper specifies the L9 subdivision graphically, but not the internal partition coordinates. The subdivisions used here are reconstructed from the published figure rather than taken from tabulated values.

## CSF section and transverse expansion

The **physical sectional description** is provided by CSF. Each polygon identifies one local domain for the transverse CUF expansion; its vertices and material properties belong to the CSF model, not to the expansion law.

![C-section geometry](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/img/Figure_3.png)

*Figure 1 – C-section geometry and reference partition.*

The transverse approximation is supplied by the independent [`lagrangeL9_v4.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/expansions/lagrangeL9_v4.py) module. It defines a **nine-point Lagrange interpolation on each quadrilateral CSF polygon**, using an isoparametric mapping from the reference square to the physical domain.

The local functions are quadratic in each natural coordinate. Shared interpolation points on neighbouring polygons provide displacement continuity across their common edges.

Thus, the CSF geometry and the transverse approximation remain separate descriptions: the former provides the physical domains, while the latter defines how the displacement field is approximated over those domains.

## Reproducible input files

The example is configured through three plain-text YAML files:

1. **Model** – the CSF section geometry and material distribution: [`c_section_chapter9_5_3_9L9_csf.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/models/c_section_chapter9_5_3_9L9_csf.yaml).
2. **Problem** – the cantilever boundary conditions and concentrated loading: [`c_section_cantilever_point_9L9.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/problems/c_section_cantilever_point_9L9.yaml).
3. **Case** – the transverse expansion, longitudinal finite elements, integration and solver settings: [`c_section_table_9_13_lagrangeL9_E10.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/cases/c_section_table_9_13_lagrangeL9_E10.yaml).

The case uses ten longitudinal elements of order 12. These are numerical choices for this analysis, not fixed characteristics of CSF–CUF.

The geometry, material, structural problem and approximation choices can be changed independently without modifying the CUF solver core.

## Displacement comparison with FEM3D

The CUF solver constructs a displacement field evaluable at arbitrary physical points along the beam and across its section.

The following figures compare the CSF–CUF displacement components with the FEM3D reference along the longitudinal trajectories of selected CSF polygon vertices.

![Longitudinal displacement ux](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/ux_along_boundary_part01.png)

*Figure 2 – Longitudinal displacement \(u_x\).*

![Transverse displacement uy](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/uy_along_boundary_part01.png)

*Figure 3 – Transverse displacement \(u_y\).*

![Transverse displacement uz](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/uz_along_boundary_part01.png)

*Figure 4 – Transverse displacement \(u_z\).*

The displacement comparison provides a first assessment of the global structural response. Stress convergence, however, requires separate examination because stresses depend on derivatives of the displacement approximation.

## Strain comparison with FEM3D

The strain components are obtained directly from the displacement gradients.

![Normal strain epsilon xx](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/epsilon_xx_along_boundary_part01.png)

*Figure 5 – Longitudinal normal strain \(\varepsilon_{xx}\).*

![Shear strain gamma xy](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/gamma_xy_along_boundary_part01.png)

*Figure 6 – Shear strain \(\gamma_{xy}\).*

The strain comparison helps distinguish differences in the underlying displacement derivatives from those associated with stress recovery.

## Stress comparison with FEM3D

The FEM3D stress values are calculated from the displacement gradients of individual H8 elements using the CSF constitutive law.

At element boundaries, **the original element-side values are retained without averaging across adjacent elements**. Several FEM3D values may therefore appear at the same longitudinal position.

The CSF–CUF stresses are instead obtained directly from the derivatives of the continuous displacement representation and the constitutive law, without averaging or smoothing.

![Normal stress sigma xx](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/sigma_xx_along_boundary_part01.png)

*Figure 7 – Longitudinal normal stress \(\sigma_{xx}\).*

![Shear stress tau xy](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/tau_xy_along_boundary_part01.png)

*Figure 8 – Shear stress \(\tau_{xy}\).*

![Shear stress tau xz](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/tau_xz_along_boundary_part01.png)

*Figure 9 – Shear stress \(\tau_{xz}\).*

![Shear stress tau yz](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/tau_yz_along_boundary_part01.png)

*Figure 10 – Shear stress \(\tau_{yz}\).*

For the shear stress component \(\tau_{xy}\), the CSF–CUF curves generally follow the **central trend of the FEM3D stress distribution**, particularly away from the beam ends, despite the scatter of individual FEM3D element-side values.

This does not imply that CSF–CUF computes an average of FEM3D stresses. The two fields are obtained independently, and the observed correspondence concerns their overall behaviour rather than pointwise agreement between individual element-side values.

Differences near the beam ends remain more pronounced and require separate consideration, particularly in the presence of concentrated loading and boundary constraints.

## Closing perspective

This example illustrates the central design choice of CSF–CUF: **the physical beam is defined independently of the functions chosen to approximate its displacement**.

The CUF formulation remains unchanged, while geometry, material, transverse expansions and longitudinal approximation remain interchangeable components.

The purpose is not a special-purpose implementation for one C-section, but a reusable framework for constructing and examining CUF models.

**Repository:** [C-section example](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/c-shape)

**Additional results:** [Strain and stress boundary comparisons](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/c-shape/strain_stress_boundary)
