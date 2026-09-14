# Introduction

This tutorial introduces the CSF-CUF framework through a complete structural example: a **non-prismatic T-section beam with variable material properties**.

The beam extends from the initial section `S0` to the final section `S1`. Along this direction, both the geometry and the material distribution may change continuously.

In the example considered here:

* the upper flange and the web progressively become smaller;
* the material assigned to the web varies along the beam;
* the material of the upper flange remains unchanged.

The example therefore combines two features that the framework is specifically designed to handle:

* **geometry varying along the beam**;
* **material properties varying along the beam**.

No previous knowledge of CSF or CUF is required.

The central idea of the framework is simple:

**CSF describes the physical member, while CUF describes how its structural response is approximated.**

## CSF: the physical model

**CSF (Continuous Section Field)** provides the physical description of the beam.

For the present T-section, it defines:

* the geometry of the upper flange and web;
* how their dimensions change from `S0` to `S1`;
* the material associated with each part of the section;
* how those material properties vary along the member.

At any position along the beam, CSF can therefore provide the actual cross-section and material properties existing at that location.

In this tutorial, the physical member is defined in

`models/t_noprismatic_csf.yaml`

and contains two physical polygons:

* `top_flange`;
* `web`.

The geometry and material are defined once in CSF and are then reused throughout the structural analysis.

## CUF: the structural approximation

**CUF (Carrera Unified Formulation)** uses the physical information supplied by CSF to construct and solve the structural model.

CUF does not redefine the beam geometry.

Instead, during the analysis it obtains the current geometry and material directly from the CSF model and uses them to evaluate the structural equations.

Its role is to define how the displacement field is represented:

* over the cross-section;
* along the beam axis.

The overall logic is therefore

**CSF physical model → CUF approximation → structural solution**

or, more directly:

* **CSF answers: what beam exists here?**
* **CUF answers: how do we approximate its displacement field?**

## The structural problem

Geometry and material alone do not define an analysis.

The beam must also be given:

* boundary conditions;
* applied loads;
* the physical regions on which those loads act;
* the longitudinal variation of the loads.

These ingredients form the **structural problem**.

This tutorial considers two problems:

* **bending**;
* **torsion**.

For bending, a surface traction acts on a physical surface associated with the `web` polygon.

For torsion, opposite loads act along trajectories obtained from the changing CSF geometry.

Both problems operate on the same CSF beam.

Only the structural loading conditions change.

The current framework already provides predefined problem adapters for several static loading cases, including:

* surface half-wave loading;
* uniform surface loading;
* torsional half-wave loading;
* uniform torsional loading;
* the predefined bending/torsion half-wave problem used for the original CUF validation cases.

The examples in this tutorial use the half-wave surface-loading problem for bending and the half-wave torsional problem for torsion.

These predefined problems are provided for convenience. Additional loads, boundary conditions, and complete structural problems can be introduced through the same adapter architecture.

## The CUF transverse expansion

A beam model must represent displacement not only along the beam axis, but also over the cross-section.

CUF represents this transverse variation through a **transverse expansion**.

The expansion is a set of mathematical functions used to approximate the displacement field over the physical cross-section supplied by CSF.

This distinction is fundamental:

* **CSF defines the physical shape of the T-section;**
* **the CUF expansion defines the mathematical approximation over that shape.**

Changing the CUF expansion therefore does not change the geometry of the beam.

It changes only the way the displacement field is represented.

The order of the expansion controls the richness of this transverse approximation.

The package currently provides several expansion families:

* `scaled_lagrange`
* `scaled_lagrange_q1`
* `scaled_legendre`
* `scaled_maclaurin`
* `scaled_maclaurin_tensor`

The examples in this tutorial use existing expansions, in particular `scaled_legendre`.

No new transverse expansion needs to be programmed in order to follow the tutorial.

Additional expansion laws can nevertheless be implemented and added without modifying the CUF core.

## The longitudinal approximation

The displacement field also varies from `S0` to `S1`.

This variation is represented independently using a longitudinal finite-element discretization.

The longitudinal approximation specifies:

* the number of elements along the beam;
* the polynomial order used inside those elements.

The complete CUF approximation therefore contains two separate directions:

* a **transverse expansion**, describing variation over the cross-section;
* a **longitudinal finite-element approximation**, describing variation along the beam.

These two approximations are independent and can be selected separately.

## The four ingredients of a CSF-CUF analysis

A complete analysis can therefore be viewed as the combination of four building blocks:

1. **CSF physical model**
   geometry and material of the beam;

2. **structural problem**
   loads and boundary conditions;

3. **CUF transverse expansion**
   approximation of the displacement field over the cross-section;

4. **longitudinal discretization**
   approximation of the displacement field along the beam.

For the example developed in this tutorial, these ingredients combine as

**non-prismatic variable-material T-section

* bending or torsion problem
* CUF transverse expansion
* longitudinal finite elements
  → displacement solution**

The following sections show how these building blocks are organized in practice.



## How the tutorial is organized

The analysis is built progressively.

The input files are separated according to the role they play:

```text
.
├── models
│   ├── t_noprismatic_csf.yaml
│   └── action.yaml
├── problems
│   ├── bending_halfwave.yaml
│   └── torsion_halfwave.yaml
└── cases
    ├── bending_halfwave_legendre_N08.yaml
    └── torsion_halfwave_legendre_N08.yaml
```

The tutorial follows the same physical sequence in which the analysis is constructed.

First, the **T-section itself** is defined and inspected with CSF.

Then, the **loads and boundary conditions** are applied to that physical model.

Finally, the **CUF numerical approximation** is selected and the structural problem is solved.

The complete sequence is therefore:

1. **build and inspect the non-prismatic, variable-material T-section;**
2. **define the bending and torsion structural problems;**
3. **define the CUF cases;**
4. **select the transverse expansion and its order;**
5. **define the longitudinal approximation and numerical integration;**
6. **run the CUF analyses;**
7. **inspect the solver diagnostics and output;**
8. **evaluate the continuous displacement field at physical points of the T-section.**

The purpose is to learn the framework by following one physical member from its CSF definition to its final structural response.

Only after this complete workflow is clear is it necessary to consider more advanced topics such as defining a custom structural problem or implementing a new CUF transverse expansion.


## 7. First complete example

The recommended way to learn the framework is not to start by writing a new CUF expansion or a new structural problem.

Instead, begin with an existing CSF model and the building blocks already provided by the package.

The step-by-step tutorial is available here:

[`cuf/tutorials/variable_material_t_section/csf-cuf_template.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/csf-cuf_template.md)

The tutorial uses a non-prismatic, variable-material T-section.

It progressively shows how to:

1. define and inspect the physical model with CSF;
2. define the loading and boundary conditions;
3. assemble these ingredients in a CUF case;
4. select a transverse expansion;
5. define the longitudinal discretization and numerical integration;
6. run the solver;
7. inspect the solver diagnostics;
8. evaluate the resulting displacement field.

The objective of the tutorial is therefore to first learn **how to use the existing CSF-CUF framework**.

Only after this workflow is clear is it necessary to consider more advanced topics such as implementing a custom structural problem or a new transverse expansion law.
