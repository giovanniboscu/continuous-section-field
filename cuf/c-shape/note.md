# C-section cantilever - a CSF–CUF example

*A compact illustration of the separation between the physical section and the CUF approximation.*

## The structural problem

The example considers a cantilever beam with an unsymmetric C-shaped cross-section, based on the Carrera–Petrolo C-section benchmark (Chapter 9, Table 9.13). The beam is 20,000 mm long, with a 1,000 mm section height, 100 mm wall thickness, and unequal flange widths of 1,000 and 500 mm. The material is isotropic, with Young's modulus 75,000 MPa and Poisson's ratio 0.33. A transverse concentrated load of −1 N is applied at the free end. Length, force and stress are expressed in mm, N and MPa.

![C-section reference illustration](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/img/Figure_3.png)

*Reference figure included with the example; consult the original publication for the benchmark convention.*

## What CSF–CUF changes

In the Carrera Unified Formulation (CUF), the displacement field is represented through transverse expansion functions and longitudinal approximations. CSF–CUF preserves this separation while introducing the **Continuous Section Field (CSF)** as an independent description of the physical cross-section, including geometry and material properties.

The physical section is evaluated numerically, without deriving and symbolically integrating new sectional expressions for each geometry. Changing the section does not require rewriting the CUF formulation or the transverse expansion law. The same architecture can accommodate different sections, materials and approximation choices.

A **CSF polygon** identifies a local physical domain. Its vertices and material properties belong to the CSF model, **not** to the transverse expansion law. In this example, nine quadrilateral CSF polygons describe the section partition used by the nine-domain Lagrange approximation. The partition follows the topology of the published figure; the internal split coordinates are reconstructed from that figure rather than taken from a numerical table.

The transverse approximation is supplied by a **separate Python module**, implementing the nine-node Lagrange interpolation over each quadrilateral domain. Shared interpolation points connect neighbouring domains. The longitudinal approximation is independently defined by finite elements.

## Three files, three responsibilities

The analysis is assembled from three human-readable YAML files, with links to the corresponding sources:

1. **Model - what is the beam?** [CSF geometry and material](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/models/c_section_chapter9_5_3_9L9_csf.yaml). This describes the section polygons, their coordinates and physical properties.
2. **Problem - how is the beam loaded and constrained?** [Cantilever and point load](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/problems/c_section_cantilever_point_9L9.yaml). It refers to the model and specifies the structural problem.
3. **Case - how is the solution approximated and computed?** [Analysis case](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/cases/c_section_table_9_13_lagrangeL9_E10.yaml). It refers to the problem and selects the [external transverse expansion](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/expansions/lagrangeL9_v4.py), longitudinal finite elements, numerical integration and solver options.

The case uses ten longitudinal elements of order 12 and a nine-point requested sectional Gauss rule. These are **choices for this analysis**, not fixed features of CSF–CUF. The geometry, structural problem and numerical approximation can be varied independently.

## Reading the results

The solver constructs a displacement field that can be evaluated at arbitrary physical points along the beam and across the section. Strains and stresses are obtained from the derivatives of that approximation. The latter deserve particular care: agreement in displacement does not, by itself, establish local convergence of every stress component, especially near a concentrated force or at boundaries.

The repository includes a FEM3D reference and boundary plots of displacement, strain and stress. These plots are useful not only for comparison but also for inspecting the spatial regularity of the reconstructed fields. The figures below are representative examples; the full gallery remains available online.

![Longitudinal displacement along the boundary](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/ux_along_boundary_part01.png)

*Representative displacement comparison along one boundary segment.*

![Normal stress along the boundary](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/sigma_xx_along_boundary_part01.png)

*Representative stress comparison: local behaviour should be interpreted in light of the approximation and load singularity.*

![Shear stress along the boundary](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/tau_xy_along_boundary_part01.png)

*Representative shear-stress comparison.*

[Browse all 75 boundary plots](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/strain_stress_boundary/README.md) · [Example directory](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/c-shape) · [CSF–CUF documentation](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/README.md) · [YAML reference](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/yaml_reference/readme.md)

## Closing perspective

This example illustrates the central design choice of CSF–CUF: **the physical beam is defined independently of the functions chosen to approximate its displacement**. The CUF formulation remains unchanged, while geometry, material, transverse expansions and longitudinal approximation remain interchangeable components. The purpose is not a special-purpose implementation for one C-section, but a reusable way of constructing and examining CUF models.
