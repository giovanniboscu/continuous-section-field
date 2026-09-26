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

In the present comparison, the **problem** and the **case** are kept unchanged. Only the **model geometry** is modified: one model contains the prismatic I-section, while the other contains the continuously tapered I-section.

This separation makes it possible to compare the two geometries without changing the CUF formulation, the loading, the boundary conditions, or the numerical approximation.

## Ingredients of the analysis

Each analysis is obtained by combining three independent descriptions: the **model**, the **problem**, and the **case**.

### Model

The **model** describes the physical beam.

It contains the beam length and the CSF description of the cross-section: the geometry of the section at the reference stations, the polygons that compose it, and the material data associated with those regions.

From this information, CSF provides the physical cross-section at any longitudinal coordinate $x$.

In the present comparison, this is the only ingredient that changes:

- in the **prismatic model**, the initial and final I-sections are identical;
- in the **tapered model**, the final section is obtained by reducing the web height by 80%, and the intermediate sections are generated continuously between the two ends.

The model is defined in a dedicated YAML file and is independent of the CUF approximation used to solve the problem.

### Problem

The **problem** describes how the beam is loaded and constrained.

It defines:

- the applied loads;
- their spatial distribution;
- the boundary conditions.

The problem therefore answers the question: **what is done to the beam?**

It does not define the cross-section and it does not select the CUF approximation.

In this comparison, the same problem definition is used for both the prismatic and tapered models, so the loads and boundary conditions are unchanged.

### Case

The **case** defines how the structural problem is approximated and solved with CUF.

It specifies, among other numerical settings:

- the **transverse CUF basis** and its order;
- the **longitudinal finite-element approximation**;
- the longitudinal basis and polynomial order;
- the numerical integration settings.

The transverse and longitudinal approximations are independent choices. The transverse basis describes the displacement field over the cross-section, while the longitudinal finite-element basis describes its variation along the beam axis.

The case also identifies which **model** and which **problem** are to be combined for a given analysis.

For the comparison presented here, the same case is used for both geometries. Therefore, the CUF expansion, the longitudinal approximation, the loads, the boundary conditions, and the numerical settings remain unchanged; only the model geometry is replaced.



## CSF–CUF representation

In the prismatic case, CSF returns the same cross-section at every longitudinal position.

In the tapered case, the section changes continuously with the longitudinal coordinate $x$, from the initial I-section to the final reduced section.

The CUF solver itself is unchanged between the two analyses.

The corresponding CSF–CUF cases are available here:

[CSF–CUF I-Shape cases](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape)

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
