# Introduction

This guide does not assume previous knowledge of the Carrera Unified Formulation (CUF).

The starting point is a simple structural problem: we have a long three-dimensional body, such as a beam, and we want to determine how it deforms when loads and constraints are applied.

A beam has one main direction, called the **longitudinal direction**. In the CSF-CUF framework this direction is identified by the coordinate \(x\).

If the beam is cut at a particular value of \(x\), the shape visible on the cut is its **cross-section**.

For example, a beam may have a rectangular, T-shaped, I-shaped, hollow, or more general cross-section.

The cross-section does not need to remain the same along the beam. Its dimensions may change with \(x\), and the material may also change from one point to another.

The CSF-CUF framework separates these two aspects of the problem:

* **CSF describes the physical beam**: its cross-sectional geometry and material;
* **CUF describes how that beam deforms**.

This separation is the basic idea behind the framework.

## 1. What does CSF describe?

**CSF** means **Continuous Section Field**.

Its role is to provide the physical cross-section of the beam at any longitudinal position \(x\).

At a requested position, CSF can provide information such as:

* the shape of the cross-section;
* the physical regions that form the section;
* the material associated with those regions;
* the variation of the geometry along the beam;
* the variation of the material properties.

For a prismatic beam, the same section is returned at every position.

For a non-prismatic beam, the section returned by CSF changes with \(x\).

Therefore CSF can be thought of as the part of the model that answers the question:

> **What physical cross-section and material exist here?**

## 2. What does CUF do?

Once the physical beam is known, the structural problem is to determine its displacement.

A point of the beam can move in the three spatial directions. The displacement field therefore contains three components.

The CUF solver provides an approximation of this displacement field over the complete three-dimensional beam.

The key idea of the **Carrera Unified Formulation** is that the variation of displacement over the cross-section is represented using a chosen set of mathematical functions.

These functions form the **transverse expansion**.

The word *transverse* simply refers to the directions inside the cross-section, as opposed to the longitudinal direction \(x\).

Increasing or changing the transverse expansion changes how much detail the model can represent inside the cross-section.

The behaviour along the beam axis is treated separately through a **longitudinal finite-element discretization**.

CUF therefore answers a different question from CSF:

> **How can the displacement field of this physical beam be represented and solved?**

## 3. How CSF and CUF work together

During the structural analysis, CUF needs information about the cross-section at different positions along the beam.

Instead of containing that geometry itself, CUF asks CSF for the physical section at the required longitudinal position.

The basic interaction is therefore:

**longitudinal position \(x\)**
↓
**CSF provides the current section and material**
↓
**CUF uses that information in the structural equations**
↓
**the solver computes the displacement field**

In compact form:

**CSF physical model → CUF approximation → structural solution**

This separation is important.

The CUF solver does not need a different implementation for a rectangular section, a T-section, an I-section, or a section whose dimensions change along the beam.

The geometry and material belong to the CSF model.

The structural approximation belongs to CUF.

## 4. What does a user need to define?

A complete CSF-CUF analysis combines four main pieces of information.

### 4.1 The physical model

The **CSF model** describes the geometry and material of the beam.

It answers questions such as:

* What is the cross-section?
* Does the section change along the beam?
* Which material occupies each part of the section?
* Do the material properties vary?

### 4.2 Loads and constraints

The **structural problem** describes how the beam interacts with its surroundings.

It specifies:

* where the beam is constrained;
* which displacement components are constrained;
* where loads are applied;
* how those loads vary along the beam.

For example, a model may contain a surface load producing bending or a loading producing torsion.

### 4.3 The transverse approximation

CUF must decide how the displacement field is represented inside each cross-section.

This is done through a **transverse expansion**.

The expansion is a set of mathematical functions defined over the cross-section.

Different expansion families provide different ways of approximating the same physical displacement field.

The framework currently provides:

* `scaled_lagrange`
* `scaled_lagrange_q1`
* `scaled_legendre`
* `scaled_maclaurin`
* `scaled_maclaurin_tensor`

A user does not need to implement a new expansion in order to run the examples. One of the existing families can simply be selected in the case configuration.

### 4.4 The longitudinal discretization

The displacement also varies from one end of the beam to the other.

This variation along \(x\) is represented using longitudinal finite elements.

The longitudinal discretization specifies how the beam axis is divided and which interpolation order is used along it.

The transverse expansion and the longitudinal discretization therefore have different roles:

* the **transverse expansion** describes variation inside the cross-section;
* the **longitudinal discretization** describes variation along the beam.

## 5. What is already provided?

To make a first analysis possible without writing Python code, the package already contains problem adapters and transverse-expansion plugins.

The currently available static problem implementations include:

* **surface half-wave loading**, where a load is applied to a selected physical surface and varies sinusoidally along the beam;
* **uniform surface loading**, where the surface load has constant longitudinal intensity;
* **torsional half-wave loading**, where the torsional loading varies sinusoidally along the beam;
* **uniform torsional loading**, where the corresponding torsional loading is constant along the beam;
* a predefined **bending/torsion half-wave problem** used by the CUF validation cases.

These implementations are ready-to-use building blocks.

They do not define the limits of the formulation. New structural problems and new transverse expansions can be added through the same adapter/plugin architecture.

## 6. What happens when a case is run?

From the user's point of view, a CSF-CUF analysis can be understood as the following sequence.

First, a CSF model defines the physical beam.

Then, a CUF case selects:

1. that CSF model;
2. the structural problem;
3. the transverse expansion;
4. the longitudinal discretization;
5. the numerical and solver settings required for the analysis.

When the case is executed, the solver assembles and solves the structural equations.

The resulting solution represents a continuous displacement approximation that can then be evaluated at physical points of the beam.

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
