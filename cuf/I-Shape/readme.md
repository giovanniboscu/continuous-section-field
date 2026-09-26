# I-Shape - Prismatic and Tapered Beam Comparison

## Purpose of this example

This example shows how the **CSF–CUF framework** separates the CUF computational core from the information defining a specific structural problem, such as the cross-section geometry, the longitudinal and transverse approximations, and the applied loads.

Two analyses are considered:

- a beam with a **prismatic I-shaped cross-section**;
- a beam with a **continuously tapered I-shaped cross-section**.

Between the two analyses, **only the cross-section geometry is changed**. The CUF formulation, the longitudinal and transverse approximations, the loads, and the remaining analysis settings are kept unchanged.

The cross-section is provided independently through the **Continuous Section Field (CSF)**. During the analysis, the CUF solver requests from CSF the section information required at each longitudinal position.

The results of both cases are then compared with independent three-dimensional finite-element models (FEM3D).

## Starting geometry

The reference geometry is the prismatic I-section considered in:

> E. Carrera and G. Giunta,  
> “Refined Beam Theories Based on a Unified Formulation”,  
> *International Journal of Applied Mechanics*, 2(1), 117–143, 2010.  
> DOI: [10.1142/S1758825110000500](https://doi.org/10.1142/S1758825110000500)

Starting from this section, two geometries are analysed:

- **Prismatic case:** the I-section remains constant along the beam.
- **Tapered case:** the clear web height decreases continuously from

$$
a = 100\ \mathrm{mm}
$$

to

$$
a = 20\ \mathrm{mm},
$$

corresponding to an **80% reduction**.

The flange width and flange thickness remain unchanged.

Only the prismatic section geometry is taken from the reference paper. The tapered geometry is generated from this section by continuously reducing the web height along the beam.

## Ingredients of the analysis

Each CSF–CUF analysis is defined by combining three independent components:

- the **model**, which describes the physical beam, including its length, cross-section geometry, and material data;
- the **problem**, which defines the applied loads and boundary conditions;
- the **case**, which specifies how the CUF formulation is approximated numerically, including the transverse expansion and the longitudinal finite-element approximation.

These components are not consecutive processing steps. They are separate descriptions of different aspects of the same structural analysis and are used together by the solver.

In the present comparison, the **problem formulation** and the **case settings** are kept unchanged. Only the **model geometry** is modified: one model contains the prismatic I-section, while the other contains the continuously tapered I-section.

Separate problem and case files are used for the two analyses only to keep the runs and their outputs clearly separated.

This separation makes it possible to compare the two geometries without changing the CUF formulation, the loading, the boundary conditions, or the numerical approximation.

### Model

The **model** describes the physical beam and is defined entirely in YAML; no Python code is required.

It contains the beam length and the CSF description of the cross-section: the geometry of the section at the reference stations, the polygons that compose it, and the material data associated with those regions.

From this information, CSF provides the physical cross-section at any longitudinal coordinate $x$.

In the present comparison, this is the only ingredient that changes:

- in the **prismatic model**, the initial and final I-sections are identical;
- in the **tapered model**, the final section is obtained by reducing the web height by 80%, and the intermediate sections are generated continuously between the two ends.

The two model definitions are:

- [Prismatic I-section model](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/models/carrera_i_shaped_prism.yaml)
- [Tapered I-section model](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/models/carrera_i_shaped_taper80.yaml)

### Problem

The **problem** describes how the beam is loaded and constrained.

It is implemented in Python and referenced through a YAML file. Once defined, the same problem implementation can be reused across different models and analysis cases without rewriting the loading and boundary-condition logic.

It defines:

- the applied loads;
- their spatial distribution;
- the boundary conditions.

The problem therefore answers the question: **what is done to the beam?**

It does not define the cross-section and it does not select the CUF approximation.

For the two geometries, the corresponding problem definitions are:

- [Prismatic problem](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/problems/prism_table9.yaml)
- [Tapered problem](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/problems/taper_table9.yaml)

The same loading and boundary-condition formulation is used in both analyses; separate problem files are retained only to keep the two runs and their outputs clearly separated.

### Case

The **case** brings together the previously defined model and problem, and specifies the numerical ingredients required for a complete CUF analysis.

It references the **transverse expansion** and the **longitudinal shape functions**, together with their associated orders, discretization parameters, numerical integration settings, and the remaining solver options.

Both the transverse expansion and the longitudinal shape functions are implemented in Python and, once defined, can be reused across different models, problems, and analysis cases.

In particular, the case specifies:

- the **transverse CUF basis** and its order;
- the **longitudinal finite-element approximation**;
- the longitudinal basis and polynomial order;
- the numerical integration settings.

The transverse and longitudinal approximations are independent choices. The transverse basis describes the displacement field over the cross-section, while the longitudinal finite-element basis describes its variation along the beam axis.

The case also identifies which **model** and which **problem** are to be combined for a given analysis.

The two case files used in this comparison are:

- [Prismatic case](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/cases/prism/lagrange_table9_N18_E1.yaml)
- [Tapered case](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/cases/taper/lagrange_table9_N18_E1.yaml)

The numerical approximation is kept unchanged between the two analyses. The same transverse CUF basis and order, the same longitudinal finite-element approximation, and the same numerical integration settings are used in both cases.

The only physical change introduced in the comparison is therefore the cross-section geometry provided by the model.

## Running the analyses

At this point, all ingredients required for the analyses have been defined: the physical model, the structural problem, and the CUF numerical case.

The two configurations are launched with:

```bash
csf-cuf cases/prism/lagrange_table9_N18_E1.yaml
csf-cuf cases/taper/lagrange_table9_N18_E1.yaml
```

The output location is defined directly in each case file through the `output` section. In this example, the results are written to the corresponding subdirectories of `output`.

## Independent FEM3D comparison

The same two geometries are also analysed using independent three-dimensional finite-element models.

The comparison therefore includes:

- prismatic CSF–CUF vs. prismatic FEM3D;
- tapered CSF–CUF vs. tapered FEM3D.

The comparison is performed along the beam at several points on the perimeter of the I-section.

For each selected point, the displacement predicted by CSF–CUF is plotted together with the corresponding FEM3D result.

The complete set of plots is available here:

[FEM3D - prismatic vs. tapered comparison plots](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape/fem3d/prism_vs_taper)

Details concerning the numerical settings, model construction, and full reproducibility of the calculations are provided separately.
