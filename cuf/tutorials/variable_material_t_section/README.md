
# Introduction

<p align="center">
<img width="40%" alt="immagine" src="https://github.com/user-attachments/assets/1a1d297d-6d68-45ae-b538-7906a8b833f4" />
</p>
<p align="center">
<img  width="40%"  alt="immagine" src="https://github.com/user-attachments/assets/eecdab76-3a3b-48c2-a213-bacd8c07a1d8" />
</p>


This tutorial introduces the CSF-CUF framework through a complete structural example: a **non-prismatic T-section beam with variable material properties**.

From the initial section `S0` to the final section `S1`, both the geometry and the material distribution may change continuously. In this example, the upper flange and web become smaller, while the material assigned to the web also varies along the beam.

No previous knowledge of CSF or CUF is required.

The central idea is:

**CSF describes the physical member; CUF describes how its structural response is approximated.**

## CSF and CUF

**CSF (Continuous Section Field)** defines the physical beam:

* cross-section geometry;
* its variation along the beam;
* material distribution;
* variation of material properties.

At any longitudinal position, CSF provides the actual section and material existing there.

In this tutorial, the beam is defined in

`models/t_noprismatic_csf.yaml`

and contains two physical polygons:

* `top_flange`;
* `web`.

**CUF (Carrera Unified Formulation)** uses this physical description to construct the structural approximation and solve for the displacement field.

CUF does not redefine the geometry. It queries CSF during the analysis and approximates displacement:

* over the cross-section;
* along the beam axis.

The basic logic is therefore:

**CSF physical model → CUF approximation → structural solution**

## Main ingredients of the analysis

A complete CSF-CUF analysis combines four elements.

### 1. Physical model

The CSF model defines geometry and material once and makes them available to all structural analyses.

### 2. Structural problem

The structural problem defines:

* loads;
* where they act;
* their variation along the beam;
* boundary conditions.

This tutorial considers **bending** and **torsion**.

For bending, a surface traction acts on a physical surface associated with the `web`.

For torsion, opposite loads act along trajectories obtained from the changing CSF geometry.

The framework already provides predefined adapters for half-wave and uniform surface and torsional loading, as well as the original bending/torsion validation problem. Additional problems can be introduced through the same adapter architecture.

### 3. CUF transverse expansion

The displacement field over the cross-section is represented through a **transverse expansion**.

The distinction is important:

* **CSF defines the physical shape;**
* **CUF defines the displacement approximation over that shape.**

The package currently provides:

* `scaled_lagrange`
* `scaled_lagrange_q1`
* `scaled_legendre`
* `scaled_maclaurin`
* `scaled_maclaurin_tensor`

The examples in this tutorial use existing expansions, so no new CUF expansion needs to be programmed.

### 4. Longitudinal discretization

Variation along the beam is represented separately using finite elements.

The longitudinal discretization is defined in the YAML input and specifies:

* the number of finite elements along the beam;
* the polynomial order inside each element.

The current implementation uses **one-dimensional Lagrange shape functions** for the longitudinal finite-element approximation. The interpolation family is therefore fixed by the solver, while the number of elements and the polynomial order are configurable from YAML.

The resulting displacement approximation combines two distinct ingredients:

* a **transverse CUF expansion** over the cross-section;
* a **longitudinal finite-element approximation** along the beam axis.

These two approximations are independent. The transverse CUF expansion determines how the displacement field is represented over the section, while the longitudinal discretization determines how its variation along the beam is approximated.

The complete analysis can therefore be viewed as the combination of four distinct components:

**CSF physical model

* structural problem
* transverse CUF expansion
* longitudinal finite-element discretization
  → displacement solution**

The **CSF physical model** provides the geometrical and material description of the beam. It is defined through a YAML configuration file containing, among other information, the coordinates of the polygons describing the cross-section and the corresponding material definitions, including their possible variation along the beam.

For example, the non-prismatic T-section used in this tutorial is defined by:

[`t_noprismatic_csf.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/models/t_noprismatic_csf.yaml)

This CSF model is supplied to the CUF solver, which queries the geometrical and material state required during the analysis.

### Python implementation and ready-made building blocks

Using the framework does not normally require writing Python code.

When the predefined building blocks already provided by the package are sufficient, an analysis can be assembled through YAML configuration files alone. These building blocks include:

* CSF geometrical and material models;
* structural problems;
* boundary conditions;
* loading schemes;
* transverse CUF expansion laws;
* longitudinal finite-element discretizations.

The user therefore defines the physical model and selects and combines the required structural and numerical components without having to implement the underlying formulation.

Python programming is only required when introducing a capability that is not already available in the framework, such as a new structural problem, loading scheme, boundary condition, transverse expansion law, or a new type of physical-model description.

### 5. CSF-CUF is implemented in Python. 

However, using the framework does not normally require writing Python code.

When the predefined building blocks already provided by the package are sufficient - including physical models, structural problems, boundary conditions, loads, and CUF expansion laws - an analysis can be assembled through the configuration files alone. In this case, the user selects and combines the required components without developing new numerical code.

Python programming is only needed when introducing a new capability that is not already available, such as a new structural problem, loading scheme, boundary condition, or transverse expansion law.


### 6. How the tutorial is organized

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
