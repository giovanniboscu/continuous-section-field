# CSF-CUF Framework

This repository provides a framework for building and running models based on the Carrera Unified Formulation (CUF).

It is not a theoretical treatment, but a parametric and reusable implementation. The model is described through YAML files defining geometry, materials, loads, boundary conditions, and the expansion law; the framework then automatically builds and executes the corresponding CUF model.

The solver core is independent of the cross-section geometry. Geometric and constitutive information is supplied by an external provider based on CSF, which the solver queries during model construction. This keeps the problem description separate from the computational algorithm and allows the same solver core to operate on different configurations.

The repository includes two complete workflows:

- a **prismatic model**, used to reproduce the reference benchmark cases;
- a **variable-section model**, showing how the same architecture can be applied to beams whose geometry and materials evolve along the longitudinal axis.

This guide describes the project organization, the data flow, and the available examples. Theoretical details are introduced only where needed and are referred to the dedicated documentation.
