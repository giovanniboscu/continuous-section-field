# Introduction

The CSF-CUF module is a structural solver based on the **Carrera Unified Formulation (CUF)**.

Its purpose is to analyse a beam-like three-dimensional body starting from a physical description of its cross-section.

The cross-section is provided by **CSF (Continuous Section Field)**. CSF describes:

* the shape of the section;
* how that shape may change along the beam;
* the material occupying the section;
* how the material properties may vary from point to point.

The CUF solver does not contain a particular section geometry or a particular material distribution. Instead, it receives this information from the CSF model and uses it to construct the structural analysis.

In simple terms, the workflow is

**CSF model → CUF structural model → solution**

This means that the same CUF solver can be used, for example, with a rectangular section, a T section, a hollow section, a non-prismatic section, or a section made of spatially varying material, without introducing a new solver for each geometry.

## What must be chosen for a CUF analysis?

To perform an analysis, four main ingredients are required:

1. a **CSF model**, describing the geometry and material;
2. a **structural problem**, describing how the member is constrained and loaded;
3. a **CUF transverse expansion**, describing how the displacement field is represented over the cross-section;
4. a **longitudinal discretization**, describing how the solution varies along the beam axis.

The framework already provides a number of ready-to-use structural problems and CUF expansions. These are supplied for convenience: they are not intended to define the limits of the formulation. New problems, loading conditions, and expansion laws can be added to the same architecture.

## Structural problems currently available

At present, the package includes several predefined static problems. Each one combines a particular loading pattern with the boundary conditions required for that problem.

The currently available implementations include:

* **surface half-wave loading** — a load applied to a selected physical surface of the member, whose intensity varies sinusoidally along the beam axis;
* **uniform surface loading** — a load applied to a selected physical surface with constant longitudinal intensity;
* **torsional half-wave loading** — a torsional loading whose intensity varies sinusoidally along the beam axis;
* **uniform torsional loading** — the corresponding torsional loading with constant longitudinal intensity;
* a predefined **bending/torsion half-wave problem** used for the original CUF validation cases.

These ready-to-use problems are implemented in the current problem-adapter library.

## CUF transverse expansions currently available

The displacement field over the cross-section can be represented using different families of transverse functions.

The package currently provides:

* `scaled_lagrange`
* `scaled_lagrange_q1`
* `scaled_legendre`
* `scaled_maclaurin`
* `scaled_maclaurin_tensor`

These are the expansion families presently distributed with the solver. Additional expansion laws can be implemented and added without rewriting the CUF core.

## Tutorial example

In the following example, no new structural problem and no new CUF expansion will be implemented.

Instead, the tutorial will use the components already available in the framework to analyse a **non-prismatic T-shaped section with spatially varying material properties**.

The geometry and material distribution will be described by CSF. The structural problem will use the existing **surface half-wave loading**, and the CUF approximation will use the existing **scaled Lagrange expansion**.

The objective is therefore first to show how an existing CSF physical model is used directly by the CUF solver, before discussing how custom problems or custom expansion laws can be introduced.
