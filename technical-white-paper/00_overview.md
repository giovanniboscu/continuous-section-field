# Continuous Section Field (CSF) — Overview

## Purpose of the Library

**Continuous Section Field (CSF)** is a geometric–mechanical preprocessing engine for the analysis of **non-prismatic** and **non-homogeneous** beam-like structural members.

CSF is designed to address a specific and well-defined gap in current structural engineering workflows:  
the **explicit, continuous, and reproducible definition of cross-section geometry and properties along the member axis**, independent of the numerical solver used for global analysis.

CSF does **not** aim to introduce new mechanical theories.  

---

## What CSF Is — and What It Is Not

### CSF *is*:
- A **continuous geometric and sectional model** for a single structural member.
- A **pre-processor** that computes section properties and stiffness/mass fields along the longitudinal coordinate \( z \).
- A tool for **non-prismatic**, **tapered**, **multi-material**, and **multi-cell** cross-sections.
- A bridge between **explicit geometry definition** and **beam-based structural solvers** (e.g. OpenSees).

### CSF *is not*:
- A finite element solver.
- A global structural analysis program.
- A nonlinear constitutive or damage model.
- A black-box profile generator.

CSF deliberately separates **geometric description**, **sectional homogenization**, and **solver execution**.

---

## Conceptual Model

CSF represents a structural member as a **continuous field along the longitudinal axis** \( z \), defined by two coupled but independent descriptions:

1. **Continuous Geometry**  
   The cross-section is defined explicitly by the user as a set of **polygonal regions** at a limited number of reference stations (start and end).  
   Intermediate sections are generated through **ruled-surface interpolation**, ensuring a smooth and deterministic geometric evolution.

2. **Continuous Property Laws**  
   Each polygonal region may carry a user-defined **longitudinal scalar field** \( w(z) \), used to scale sectional contributions.  
   This mechanism enables the representation of:
   - multi-material sections,
   - stiffness or thickness variation,
   - degradation or staging effects,
   - voids and cut-outs through explicit zero-weight regions.

From these two descriptions, CSF evaluates **section properties and derived fields** such as:

`A(z), C_x(z), C_y(z), I_x(z), I_y(z), J(z), EA(z), EI(z), GJ(z)`
---

## Motivation and Methodological Positioning

Standard practice approximates non-prismatic members as prismatic segments. The result depends on arbitrary choices: segment count, sampling points, averaging rules.
CSF defines the member as a continuous field. The solver samples this field; it does not invent piecewise-constant substitutes.
Discretization remains at the solver level. Arbitrariness is removed from the section definition.

---

## Transparency and Reproducibility

A core design principle of CSF is **explicitness**.

- All geometries are defined by coordinates.
- All assumptions are declared in text-based input files.
- No predefined section templates are used.
- No hidden defaults are introduced during computation.

For this reason, CSF workflows can be expressed entirely using **plain-text YAML files**, enabling:
- version control,
- peer review,
- documentation-driven modeling,
- long-term reproducibility.

Alternatively, CSF can be used through its Python APIs, providing greater flexibility for programmable and automated workflows

---

## Document Structure

The CSF documentation is organized as a sequence of focused technical notes:

- **Concepts and scope**
- **Geometric model**
- **Weight laws and homogenization**
- **Section property evaluation**
- **Numerical engine**
- **Validation benchmarks**
- **Solver integration**
- **YAML workflows**
- **Methodological FAQ**

Each document is self-contained and can be read independently, while collectively forming a complete technical reference.

---

## Intended Audience

CSF is written for:
- structural engineers,
- researchers,
- advanced practitioners,

who are comfortable with:
- beam theory,
- sectional properties,
- numerical integration concepts,

and who require **control, transparency, and reproducibility** in the modeling of non-prismatic structural members.

