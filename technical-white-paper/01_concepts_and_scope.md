# Concepts and Scope

## Problem Statement

In structural engineering practice, beam-like members are commonly analyzed under the assumption of **prismatic geometry** and **uniform sectional properties**.  
When a member is non-prismatic, the prevailing workaround consists in subdividing it into a sequence of prismatic elements, each assigned constant properties obtained by averaging or sampling.

While this approach is computationally convenient, it introduces several conceptual limitations:
- the solution depends on the number of subdivisions,
- sectional properties depend on arbitrary sampling locations,
- geometric continuity is replaced by stepwise approximations,
- the modeling choices are often implicit and difficult to reproduce.

These limitations become particularly evident for members with:
- continuous tapering,
- varying thickness or stiffness,
- multi-material layouts,
- internal voids or multi-cell geometries.

CSF is designed to address this specific modeling gap.

---

## Core Concept: The Continuous Section Field

The fundamental idea behind CSF is to treat a structural member as a **continuous section field** rather than as a sequence of prismatic segments.

Formally, the member is described by:
- a longitudinal coordinate \( z \in [0, L] \),
- a cross-section \( \Omega(z) \) that varies continuously with \( z \),
- a set of scalar fields \( w_k(z) \) associated with subdomains of the section.

All sectional quantities are derived from these continuous descriptions, not from discretized substitutes.

---

## Separation of Responsibilities

CSF enforces a strict separation between three modeling layers:

1. **Geometry definition**  
   The user defines the cross-section explicitly using polygonal regions at reference stations.

2. **Sectional homogenization**  
   Physical properties are introduced through user-defined scalar fields \( w(z) \), applied per polygon.

3. **Structural solution**  
   The global equilibrium problem is delegated to an external solver.

This separation ensures that CSF remains:
- solver-agnostic,
- transparent,
- limited in scope.

---

## Geometric Scope

CSF models a single structural member whose geometry satisfies the following assumptions:

- The member is beam-like, with a dominant longitudinal axis.
- Cross-sections are defined in planes normal to the axis.
- Section geometry is represented by **closed polygonal regions**.
- Corresponding polygons between reference sections are connected through **ruled surfaces**.
- The topology of the section is consistent between reference stations.

Curved outlines are represented through polygonal approximation.  
The geometric accuracy depends on the number of polygon vertices supplied by the user.

---

## Constitutive Scope

CSF operates within the framework of **linear elasticity** and **sectional homogenization**.

- Material nonlinearity is not modeled.
- Cracking, yielding, damage, and hysteresis are outside the scope.
- All physical effects are introduced through scalar weighting fields applied to geometry.

The interpretation of the scalar field \( w(z) \) is left to the user and must remain consistent throughout the workflow.

---

## Continuous vs. Piecewise-Prismatic Modeling

CSF does not eliminate discretization at the solver level.  
However, it eliminates **arbitrary discretization at the modeling level**.

The key distinction is the following:

- In piecewise-prismatic modeling, the user chooses how to discretize the member and how to assign constant properties.
- In CSF, the user defines a continuous field once, and the solver samples it according to a prescribed numerical rule.

Refinement in CSF corresponds to improving the numerical quadrature of the *same continuous field*, not to redefining the model.

---

## Reproducibility and Determinism

Given the same inputs:
- geometry definition,
- weight laws,
- numerical integration scheme,

CSF produces identical results, independent of:
- platform,
- solver,
- user discretization preferences.

This determinism is a deliberate design choice aimed at reproducible engineering workflows.

---

## Intended Use and Limitations

CSF is intended for:
- preprocessing,
- validation,
- export of sectional data,
- educational and research applications.

It is **not** intended to replace:
- finite element solvers,
- commercial section libraries,
- nonlinear material models.

When sectional properties are constant or trivial, CSF offers no advantage over simpler tools.

---

## Summary

CSF provides a formal and explicit way to define non-prismatic structural members as continuous entities.

Its contribution is methodological rather than theoretical:
- it clarifies assumptions,
- removes hidden modeling choices,
- and makes sectional variation an explicit, inspectable part of the engineering model.

The following documents describe the geometric model, weighting logic, numerical engine, and validation examples in detail.

