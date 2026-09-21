# Introduction

<p align="center">
<img width="40%" alt="immagine" src="https://github.com/user-attachments/assets/1a1d297d-6d68-45ae-b538-7906a8b833f4" />
</p>
<p align="center">
<img width="40%" alt="immagine" src="https://github.com/user-attachments/assets/eecdab76-3a3b-48c2-a213-bacd8c07a1d8" />
</p>

This tutorial introduces the CSF-CUF framework through a complete structural example: a **non-prismatic T-section beam with variable material properties**.

From the initial section `S0` to the final section `S1`, both the geometry and the material distribution can vary continuously along the beam. In the example considered here, the upper flange and the web become smaller, while the material associated with the web also changes along the longitudinal direction.

No previous knowledge of CSF or CUF is required.

The framework is built around a simple separation of roles:

**CSF provides the physical description of the member; CUF provides the structural approximation built on that description.**

The transverse CUF expansion and the longitudinal approximation are selected independently. In the longitudinal direction, the finite-element discretization uses a configurable basis; when no basis is specified in the case YAML, the solver uses **Lagrange as the default longitudinal basis**. 


## CSF and CUF

**CSF (Continuous Section Field)** describes the physical member as a continuous geometrical and material field along the beam.

At any longitudinal position, CSF can provide the corresponding physical section, including its geometry and material state.

In this tutorial, the physical member is defined in:

```text
models/t_noprismatic_csf.yaml
```

through two physical polygons:

* `top_flange`;
* `web`.

The CSF model is independent of the particular structural approximation subsequently used to analyse it.

**CUF (Carrera Unified Formulation)** operates on this physical description.

It does not introduce a separate geometrical or material model. During the analysis, the CUF solver queries CSF for the physical section and material state required at each longitudinal position and constructs the displacement approximation over that physical member.

The displacement field is represented through two distinct approximations:

* a **transverse CUF expansion** over the cross-section;
* a **longitudinal finite-element approximation** along the beam axis.

The basic relationship between the two frameworks is therefore:

```text
CSF physical model
        ↓
CUF structural approximation
        ↓
displacement solution
```

In other words:

**CSF describes what the member is; CUF describes how its structural response is approximated.**

## Files involved in the tutorial

The same separation of responsibilities is reflected directly in the input files:

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
    ├── torsion_halfwave_legendre_N08.yaml
    └── torsion_halfwave_legendre_N25.yaml
```

These files belong to three main levels.

### Physical model

```text
models/t_noprismatic_csf.yaml
```

defines the geometry and material distribution of the member.

The auxiliary file

```text
models/action.yaml
```

is used to inspect the CSF model before the structural analysis.

### Structural problems

```text
problems/bending_halfwave.yaml
problems/torsion_halfwave.yaml
```

define the loads and boundary conditions applied to the same physical CSF model.

The physical geometry and material distribution are not repeated in these files: each problem refers to the existing CSF model.

### CUF analysis cases

```text
cases/bending_halfwave_legendre_N08.yaml
cases/torsion_halfwave_legendre_N08.yaml
cases/torsion_halfwave_legendre_N25.yaml
```

connect a structural problem to the CUF formulation and contain the numerical choices used for the corresponding analysis.

The overall organization can therefore be summarized as:

```text
CSF physical model
        +
structural problem
        +
CUF numerical settings
        ↓
complete structural analysis
```

This separation makes it possible to reuse the same physical member with different loading conditions, CUF expansions, approximation orders, or numerical settings without redefining the geometry and material model.

## Configuration-driven use

CSF-CUF is implemented in Python, but using the framework does not normally require writing Python code.

When the required building blocks already exist, the analysis is assembled through YAML configuration files: the physical model is defined once, a structural problem is associated with it, and a CUF case selects the numerical approximation used to solve that problem.

The package already provides several transverse CUF expansion families, including:

* `scaled_lagrange`
* `scaled_lagrange_q1`
* `scaled_legendre`
* `scaled_maclaurin`
* `scaled_maclaurin_tensor`

The examples in this tutorial use the existing `scaled_legendre` expansion.

The longitudinal approximation is handled independently through one-dimensional finite elements using Lagrange shape functions. The number of elements and their polynomial order are selected from the case YAML.

Python programming becomes necessary only when a new capability has to be introduced, for example a new structural problem, loading scheme, boundary condition, transverse expansion law, or CSF physical-model description.

The distinction is therefore intentional:

**YAML files configure and assemble an analysis; Python provides the reusable physical and numerical building blocks behind it.**

## Tutorial objective

The following sections develop the complete example step by step.

The objective is first to show how the existing CSF-CUF framework is used as a whole: starting from the physical CSF member, applying a structural problem, selecting a CUF approximation, solving the system, and inspecting the resulting physical displacement field.

Only after this workflow is clear is it necessary to consider more advanced topics such as implementing a custom structural problem or a new CUF transverse expansion.

The complete step-by-step tutorial is available here:

[`cuf/tutorials/variable_material_t_section/csf-cuf_template.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/csf-cuf_template.md)

