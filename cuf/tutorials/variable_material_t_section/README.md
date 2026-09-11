# Introduction

This tutorial introduces the CSF-CUF framework through a complete structural example.

The structure considered throughout the tutorial is a **non-prismatic T-section beam with variable material properties**.

The beam extends from the initial section `S0` to the final section `S1`. Along this direction, the geometry of the T-section progressively changes: both the upper flange and the web become smaller. At the same time, the material assigned to the web varies along the beam, while the material of the upper flange remains unchanged.

The example therefore contains, in a single model, the two features that CSF-CUF is designed to handle directly:

* a cross-section whose **geometry changes along the beam**;
* a material whose **properties change along the beam**.

The objective of the tutorial is to start from this physical T-shaped member and progressively build the corresponding CUF structural analysis.

No previous knowledge of CUF is required.

## What are CSF and CUF doing in this example?

The beam is described using two complementary parts of the framework.

**CSF (Continuous Section Field)** describes the physical member.

For the T-section used in this tutorial, CSF provides:

* the geometry of the upper flange;
* the geometry of the web;
* the way both parts change from `S0` to `S1`;
* the material associated with each part of the section;
* the variation of the material properties along the member.

At any position along the beam, CSF can therefore provide the actual physical T-section that exists at that location.

**CUF (Carrera Unified Formulation)** uses this physical description to construct the structural approximation and solve for the displacement field.

CUF does not contain its own copy of the T-section geometry. During the analysis, it obtains the current geometry and material directly from the CSF model.

For this tutorial, the basic workflow is therefore

**variable T-section CSF model → CUF structural model → displacement solution**

This separation is important.

The geometry and material variation belong to the CSF model, while CUF determines how the displacement field of that physical member is represented and solved.

## What must be chosen for the T-section analysis?

To perform the analysis developed in this tutorial, four main ingredients are required:

1. a **CSF model**, describing the geometry and material of the non-prismatic T-section;
2. a **structural problem**, describing how the T-section beam is constrained and loaded;
3. a **CUF transverse expansion**, describing how the displacement field is represented over each T-shaped cross-section;
4. a **longitudinal discretization**, describing how the solution is represented along the beam axis.

These four ingredients have different roles.

### 1. CSF physical model

The first ingredient is the beam itself.

In this tutorial it is defined by

`models/t_noprismatic_csf.yaml`

The cross-section contains two physical polygons:

* `top_flange`, representing the upper flange;
* `web`, representing the vertical web.

The dimensions of both polygons vary continuously from the initial section `S0` to the final section `S1`, producing the non-prismatic T-shaped member used throughout the tutorial.

The material field is also defined by the same CSF model. The upper flange keeps the same material properties along the beam, while the material assigned to the web varies longitudinally.

The geometry and material are therefore defined once in CSF and are subsequently reused by the structural problems and CUF cases.

### 2. Structural problem

Once the physical T-section has been defined, we must specify what happens to it structurally.

The structural problem defines:

* the applied load;
* where that load acts on the physical member;
* how the load varies along the beam;
* the boundary conditions.

This tutorial considers both **bending** and **torsion**.

For bending, a surface traction is applied to a physical surface associated with the `web` polygon.

For torsion, opposite loads act along trajectories obtained directly from the changing CSF geometry.

In both cases, the structural problem operates on the same non-prismatic T-section defined by the CSF model.

### 3. CUF transverse expansion

The structural solution must describe displacement not only along the beam but also across the T-shaped cross-section.

CUF represents this transverse variation using a set of mathematical functions called a **transverse expansion**.

For example, the bending case developed in this tutorial uses the `scaled_legendre` expansion.

The important distinction is that the CUF expansion does not define the shape of the T-section.

The **physical T geometry comes from CSF**.

The **CUF expansion provides the mathematical approximation used over that geometry**.

The order of the expansion determines the richness of the transverse displacement approximation and can be changed without modifying the CSF model.

### 4. Longitudinal discretization

The displacement field also varies from `S0` to `S1` along the beam axis.

This longitudinal variation is represented separately using finite elements.

The longitudinal discretization specifies:

* the number of longitudinal elements;
* the polynomial order used inside those elements.

The two approximations therefore have distinct roles:

* the **CUF transverse expansion** represents the displacement variation over the T-section;
* the **longitudinal finite-element discretization** represents the displacement variation along the beam.

They can be selected independently.

## Structural problems currently available

The T-section examples in this tutorial use predefined structural-problem adapters supplied with the CSF-CUF framework.

At present, the package includes several predefined static problems. Each one combines a particular loading pattern with the boundary conditions required for that problem.

The currently available implementations include:

* **surface half-wave loading** - a load applied to a selected physical surface of the member, whose intensity varies sinusoidally along the beam axis;
* **uniform surface loading** - a load applied to a selected physical surface with constant longitudinal intensity;
* **torsional half-wave loading** - a torsional loading whose intensity varies sinusoidally along the beam axis;
* **uniform torsional loading** - the corresponding torsional loading with constant longitudinal intensity;
* a predefined **bending/torsion half-wave problem** used for the original CUF validation cases.

In this tutorial, the T-section is analysed using the half-wave surface-loading problem for bending and the half-wave torsional problem for torsion.

These ready-to-use problems are implemented in the current problem-adapter library.

They are supplied for convenience and do not define the limits of the formulation. Additional loading conditions, boundary conditions, and complete structural problems can be introduced through the same adapter architecture.

## CUF transverse expansions currently available

The displacement field over the T-section can also be represented using different families of transverse functions.

The package currently provides:

* `scaled_lagrange`
* `scaled_lagrange_q1`
* `scaled_legendre`
* `scaled_maclaurin`
* `scaled_maclaurin_tensor`

The examples developed below use an existing expansion, so no CUF expansion needs to be programmed in order to follow the tutorial.

These are the expansion families presently distributed with the solver. Additional expansion laws can be implemented and added without rewriting the CUF core.

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
