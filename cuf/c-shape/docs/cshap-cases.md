# Case - CUF approximation and numerical analysis

[← C-section benchmark](../readme.md) · [Model](cshape-model.md) · [Problem](cshape-problem.md)

## What does a case describe?

Once the physical [Model](cshape-model.md) and [Problem](cshape-problem.md) are fixed, a **case** defines **how the solution is approximated and computed**. The cases are held in [`cases/`](../cases/).

This is the layer to change when studying the effect of the CUF expansion, longitudinal discretization, integration or solver options without redefining the physical beam and its loading.

## The three independent choices

| Layer | Where it is defined | What it controls |
| --- | --- | --- |
| Physical model | [`models/`](../models/) | Geometry, sectional domains and material field |
| Physical problem | [`problems/`](../problems/) | Reference to the model, restraints and loading |
| Numerical case | [`cases/`](../cases/) | Transverse displacement expansion, longitudinal finite elements, numerical integration and solve/output settings |

## What a case selects

**1. Transverse approximation.** The case selects a separate Python implementation of the CUF transverse basis. For this 9-L9 benchmark, [`lagrangeL9_v4.py`](../expansions/lagrangeL9_v4.py) defines a nine-point Lagrange interpolation on each quadrilateral CSF domain, with isoparametric mapping from the reference square to the physical polygon. Adjacent polygons share coincident transverse interpolation nodes, ensuring displacement continuity along common boundaries.

**2. Longitudinal approximation.** The case specifies the one-dimensional finite-element approximation along the beam axis. Its element count and polynomial order concern the **axial** solution and must not be confused with the nine polygons in the section.

**3. Numerical controls.** Case-level options control quadrature, solution and requested output. Where supported, changing these settings changes the numerical experiment, not the physical boundary-value problem.

## Reading and reproducing a case

1. Open an actual YAML in [`cases/`](../cases/) and identify its reference to the chosen problem file.
2. Follow that reference to [`c_section_cantilever_point_9L9.yaml`](../problems/c_section_cantilever_point_9L9.yaml); this in turn refers to the [CSF model](../models/c_section_chapter9_5_3_9L9_csf.yaml).
3. Identify the transverse-basis implementation selected by the case, then note its order and domain layout.
4. Record the longitudinal element count and order, quadrature settings, solver configuration and requested outputs **exactly as written in that case**.
5. To make a controlled comparison, change one numerical choice at a time while keeping the same model and problem.

The chain is therefore:

```text
case YAML
  ├── problem YAML
  │     └── CSF model YAML → section geometry and material
  ├── transverse-basis Python implementation
  ├── longitudinal finite-element approximation
  └── integration / solver / output configuration
```

## What is specific to the 9-L9 example?

The label **9-L9** means that the section is divided into nine physical quadrilateral domains, each carrying a local nine-node Lagrange transverse approximation. It does **not** mean nine beam elements along the longitudinal direction.

The geometric partition is recorded in the [Model](cshape-model.md); the choice of L9 interpolation belongs here, in the Case. Keeping those definitions separate permits other transverse approximations to reuse the same geometry, provided they are compatible with its domains.

## Source of exact parameter values

The particular case filenames and their numerical parameter values must be read directly from the current [`cases/`](../cases/) YAMLs. They are intentionally **not invented or hard-coded in this page**: the case directory, rather than this guide, is the source of truth for the chosen expansion, finite-element order, Gauss integration and run options.

## References

- [Case directory](../cases/)
- [L9 transverse basis](../expansions/lagrangeL9_v4.py)
- [Physical problem](../problems/c_section_cantilever_point_9L9.yaml)
- [General CUF documentation](../../docs/)
