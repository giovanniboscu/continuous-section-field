# Continuous Section Field (CSF)

The **Continuous Section Field (CSF)** framework provides a continuous description of non-prismatic and multi-material beam members by generating longitudinally varying cross-section properties without using piecewise-prismatic discretization.

CSF represents stiffness and mass properties as continuous fields derived directly from geometry and material layout.  
This makes it possible to model tapered beams, composite sections, and gradual changes in material participation along the beam axis in a consistent and mesh-independent way.

---

## Key Features

- Continuous cross-section properties along the beam axis
- Support for non-prismatic and multi-material sections
- Geometry defined by ruled surfaces between arbitrary end sections
- Section-level elastic homogenization
- Longitudinally varying homogenization factors
- Native Python library and file-based workflow
- Graphical inspection of geometry and properties
- Export to OpenSees for structural analysis

---

## Conceptual Overview

In CSF, a beam is described through:

1. A geometric definition of the beam axis and end sections  
2. A cross-section layout composed of multiple material sub-domains  
3. A continuous homogenization process that produces equivalent linear-elastic section properties along the beam axis  

The beam is not discretized into prismatic finite elements.  
Instead, cross-section properties are evaluated continuously as functions of the longitudinal coordinate.

---

## Cross-Section Homogenization

Each cross-section may include multiple material patches.  
For each patch, a reference elastic modulus is defined.

An elastic homogenization factor is associated with each patch.  
This factor scales the contribution of that patch to the equivalent section properties.

Multiple homogenization factors may coexist within the same cross-section, each acting on a different portion of the section.

---

## Longitudinal Variability

Homogenization factors may vary along the beam axis.

Their variation is:
- not required to be linear
- defined by the user
- independent for each material patch

They can be specified either through tabulated data or through analytical functions supported by the Python environment.

CSF evaluates these factors continuously along the beam axis and applies them locally, section by section, during all internal computations.

---

## Equivalent Section Properties

Using the homogenized material layout, CSF computes continuous sectional properties such as:

- Cross-section area
- Second moments of area
- Torsional constant
- Axial, bending, and torsional stiffness quantities

All properties can be visualized, exported as tables, or used as input for structural analysis.

---

## What CSF Is — and Is Not

### CSF is
- a continuous elastic homogenization framework
- a geometry-driven section property generator
- compatible with classical beam theory
- intended for linear structural analysis

### CSF is not
- a damage or cracking model
- a nonlinear material model
- a plasticity formulation
- a replacement for solid or shell finite element models

Homogenization factors describe elastic equivalence only and do not represent material degradation or state-dependent behavior.

---

## Workflow

CSF can be used in two complementary ways:

### File-Based Workflow
- Geometry definition file
- Output and processing definition file
- Automatic generation of section properties, plots, and solver-ready models

### Python API
- Full control over geometry and homogenization
- User-defined functions for longitudinal variation
- Advanced scripting and customization

---

## Structural Analysis Integration

CSF does not perform structural analysis directly.

Instead, it provides continuous section properties that can be mapped to standard beam-based finite element formulations, such as those used in OpenSees.

In this sense, CSF acts as a pre-processing and modeling layer.

---

## Documentation

Additional documentation is available in the `docs/` directory:

- `homogenization.md` — homogenization concepts and assumptions
- `geometry.md` — geometric modeling
- `opensees_export.md` — solver integration

---

## Status

CSF is under active development.  
The API and file formats may evolve as new features are introduced.
