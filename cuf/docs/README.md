# CSF-CUF Documentation

This directory contains the technical documentation for the CSF-CUF framework.

The documents are organized around two main topics:

1. how a structural problem interacts with the generic CUF solver;
2. how transverse CUF expansions can be implemented and extended.

The general design principle is to keep the **CUF solver core independent of the specific structural problem and of the selected transverse expansion**.

A typical analysis can be viewed as:

```text
CSF physical model
        |
        v
structural problem adapter
        |
        v
generic CUF solver
        |
        v
physical solution field
        |
        v
post-processing adapter
```

The transverse approximation used by the solver is independently selected through the CUF expansion plugin system.

---

## Documentation overview

### [`csf_problem.md`](csf_problem.md)

Describes the **input side of a CUF analysis**: how loads and boundary conditions are defined without modifying the generic solver.

The document explains the role of the structural problem adapter and the interfaces used to:

* query the current CSF section;
* project physical loads onto the CUF transverse basis;
* construct generalized longitudinal loads;
* access the CUF degree-of-freedom layout;
* define boundary conditions and constraint systems.

This is the main reference when implementing a new structural problem.

---

### [`csf_post.md`](csf_post.md)

Describes the **output and post-processing side of a CUF analysis**.

The post-processing adapter receives the already solved physical displacement field and can combine it with information obtained from the CSF physical model.

The document explains how to:

* query the current section geometry and material state;
* evaluate the solved physical displacement field through `u(x, y, z)`;
* use section-specific evaluators when available;
* sample the solution along the beam and across the section;
* perform problem-specific analytical or numerical comparisons;
* generate case-specific output without modifying the CUF solver.

Together,

```text
csf_problem.md
```

and

```text
csf_post.md
```

describe the two programmable boundaries around the generic CUF solver:

```text
problem.py
    |
    v
generic CUF solver
    |
    v
post.py
```

---

### [`how_to_create_transverse_expansion.md`](how_to_create_transverse_expansion.md)

General guide for implementing a **new transverse CUF expansion**.

It explains the plugin architecture and the common `CUFBasis` interface expected by the solver.

The guide covers:

* creation of a new expansion module;
* definition and stable ordering of the transverse functions;
* implementation of `value()` and transverse derivatives;
* use of `section_provider` and the continuous CSF model;
* expansion-specific YAML options;
* sectional quadrature requirements;
* longitudinal quadrature degree contributions;
* plugin registration;
* interaction with loads, constraints, and solution recovery;
* mathematical, numerical, and regression tests.

The guide uses a simple example expansion to show the complete procedure while keeping the CUF core unchanged.

This should be the starting point for anyone implementing a completely new CUF transverse approximation.

---

### [`scaled_lagrange_implementation_guide.md`](scaled_lagrange_implementation_guide.md)

Detailed implementation guide for the `scaled_lagrange` transverse expansion.

Unlike the general expansion guide, this document follows a concrete implementation already integrated into CSF-CUF.

It explains how the existing hierarchical Serendipity-Lagrange reference basis is mapped to the physical section and registered as the:

```yaml
cuf:
  basis: scaled_lagrange
```

expansion.

The guide covers:

* the existing Serendipity-Lagrange hierarchy;
* the stable hierarchical definition of the CUF index `tau`;
* scaling from reference to physical transverse coordinates;
* evaluation of basis functions and analytical derivatives;
* physical power-coefficient compilation;
* plugin construction and registration;
* quadrature requirements;
* YAML configuration;
* verification of the hierarchy and Kronecker properties;
* derivative tests;
* hierarchical prefix stability;
* validation over increasing CUF orders.

It can also be used as a practical reference implementation when developing other advanced transverse expansions.

---

## Recommended reading order

For understanding the general CSF-CUF architecture:

```text
1. csf_problem.md
2. csf_post.md
```

For developing a new transverse expansion:

```text
1. how_to_create_transverse_expansion.md
2. scaled_lagrange_implementation_guide.md
```

The first document explains the general extension mechanism, while the second shows how that mechanism is applied to a complete hierarchical expansion.

---

## Architectural separation

The documents in this directory follow the same fundamental separation of responsibilities:

```text
CSF
    physical geometry and material fields

Problem adapter
    loads and boundary conditions

CUF expansion plugin
    transverse approximation F_tau

CUF solver
    integration, assembly and algebraic solution

Post-processing adapter
    interpretation and validation of the physical solution
```

This separation allows new physical models, structural problems, transverse expansions, and post-processing procedures to be introduced without creating dedicated variants of the CUF solver.
