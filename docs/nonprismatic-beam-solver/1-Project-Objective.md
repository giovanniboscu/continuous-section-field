# 1. Project Objective

This project aims to develop a numerical solver based on the non-prismatic beam model introduced by **Giuseppe Balduzzi** and co-authors, with explicit recognition of the originality and importance of their formulation for tapered and non-prismatic members.

The immediate objective is **not** to replace or reinterpret the original theory, but to make it operational within a practical computational workflow. In particular, the project focuses on:

- implementing a solver consistent with the **Balduzzi beam formulation** for planar non-prismatic members;
- defining a clear separation between:
  - the **model input data** required by the formulation, and
  - the **numerical solver** that uses those data;
- adopting a fully **numerical perspective**, avoiding any requirement for closed-form geometric or constitutive expressions;
- preparing the ground for integration with **continuous geometric-sectional descriptions**, so that realistic non-prismatic members can be analyzed without reducing the problem to a few manually segmented idealized parts.

A second, more advanced objective is to explore the **generalization of the Balduzzi framework to non-rectangular and more general cross-sections**. This is recognized from the outset as a substantially harder step, likely deserving independent treatment. It is therefore considered a future development, separate from the first implementation of the original model.

The broader motivation is practical: many advanced beam formulations for non-prismatic members are mathematically sound, but their use in realistic applications is often limited by the absence of a programmable geometric pipeline capable of supplying the required data in a consistent form. This project is intended to address that gap incrementally.

Accordingly, the project is structured around three progressive goals:

1. **implement the original Balduzzi-based solver in numerical form;**
2. **formalize the reduced model data required to drive that solver;**
3. **investigate how the same framework may be extended to richer sectional geometries.**

This work is developed as an evolving technical effort and documented progressively in Markdown form on GitHub.


## Document flow and separation of concerns

A core design principle of this project is the strict separation between the **member description** and the **structural problem applied to that member**.

This separation is necessary both for implementation and for documentation clarity. It helps identify the target of each action, both for the developer and for any future reader of the repository.

The project is therefore organized around the following distinction:

### 1. Geometric / material model

This part describes the member itself, independently of any specific load case or support condition.

It includes, depending on the adopted formulation:

- geometric descriptors of the beam;
- material parameters and their possible variation along the axis;
- derived geometric or constitutive quantities required by the beam model.

This block answers the question:

> **What structural member is being modeled?**

### 2. Load / boundary-condition model

This part describes how the member is used in a specific structural problem.

It includes:

- distributed loads;
- concentrated actions, if present;
- boundary conditions at the beam ends;
- case-dependent problem definitions.

This block answers the question:

> **How is the member loaded and constrained?**

### 3. Reduced model input data

Only after the previous two parts are defined can the actual **model input data required by the formulation** be assembled.

These are not the full upstream descriptions, but their reduced representation in the form required by the beam model.

This block answers the question:

> **What data are actually required to drive the formulation?**

### 4. Solver

The solver is a separate layer.

Its role is only to solve the governing equations once the reduced model input data are available.

The solver must not depend on the origin of the geometry, on the upstream preprocessing pipeline, or on the format used to define the member and the load case.

This block answers the question:

> **How is the reduced model solved numerically?**

## Intended document flow

The documentation will follow the same logic.

The expected sequence of documents is:

1. **project scope and objectives**
2. **geometric / material model**
3. **load / boundary-condition model**
4. **reduced model input data**
5. **Balduzzi solver**
6. **numerical strategy and implementation notes**
7. **examples and progressive extensions**

This sequence is intended to make the development path explicit and readable.

It also keeps separate:

- the description of the structural member;
- the definition of the structural problem;
- the reduction of both into formulation-ready data;
- the numerical solution process itself.


# Main Reference

Balduzzi, G., Aminbaghai, M., Sacco, E., Füssl, J., Eberhardsteiner, J., & Auricchio, F. (2016). *Non-prismatic beams: A simple and effective Timoshenko-like model*. *International Journal of Solids and Structures*, 90, 236–250. https://doi.org/10.1016/j.ijsolstr.2016.02.017




