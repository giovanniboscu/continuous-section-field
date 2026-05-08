---
title: 'CSF: Continuous Section Fields for Non-Prismatic and Axially Graded Structural Members'
tags:
  - Python
  - structural engineering
  - cross-section properties
  - non-prismatic members
  - finite element preprocessing
  - wind turbines
authors:
  - name: Giovanni Boscu
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: Independent Researcher, Sardinia, Italy
    index: 1
date: 2026-05-08
bibliography: paper.bib
---

# Summary

Continuous Section Field (CSF) is an open-source Python package for constructing and analysing continuous cross-section fields in structural members whose geometry and sectional participation vary along the longitudinal axis. Its main purpose is to turn a member-level geometric description into station-wise section properties that can be used in beam, tower, bridge, and finite element workflows.

The central idea of CSF is to treat the cross-section not as a single isolated object, but as a field defined along `z`. A user defines polygonal cross-sections at reference stations, usually `S0` and `S1`; CSF then interpolates corresponding polygon vertices to generate intermediate sections and evaluates properties such as area, centroid, second moments of area, principal inertias, section moduli, torsional constants, and stiffness-weighted quantities at any station.

The change of paradigm is the explicit separation between geometry and sectional participation. Geometry defines where each polygonal region is located along the member. Two independent longitudinal participation fields define how much each region contributes: the axial/bending field `w_i(z)` and the shear/torsion field `shear_w_i(z)`. These fields can represent stiffness ratios, degraded regions, reinforcement, voids, density-like quantities, or other user-defined sectional contributions. They may be interpolated from endpoint values, derived from an isotropic relation, or specified through custom laws that depend on the longitudinal coordinate and on geometric quantities.

CSF can be used through a Python API or through a file-based YAML workflow. The YAML workflow separates the definition of the continuous member from the requested computations, plots, and exports, allowing the same geometry to be reused in reproducible analysis pipelines. The package also provides interoperability tools for OpenSees [@mckenna2011opensees], SAP2000, and `sectionproperties` [@vandenbergh2023sectionproperties].

# Statement of need

Many engineering research problems involve members whose cross-section changes along their length: tapered wind turbine towers, haunched bridge girders, variable-depth beams, repaired or degraded members, hybrid material sections, and staged or homogenized structural models. In these cases, the required input for downstream solvers is not one section, but a field of section properties such as `A(z)`, `EI_x(z)`, `EI_y(z)`, and `GJ(z)`.

Most cross-section analysis tools are section-first. They provide accurate properties for a section at a given station, but the user remains responsible for creating all intermediate sections, preserving topological consistency, applying material or degradation laws, sampling the member, and exporting the results to a solver. This creates repeated custom scripting and increases the risk that geometry variation, material participation, and solver stations are handled inconsistently.

CSF is designed for researchers and engineers who need a reproducible way to define, sample, inspect, and export continuous sectional models. Its target users include structural engineering researchers, wind turbine modelers, bridge and tower analysts, and developers who need section-property fields as inputs to beam-level or aeroelastic simulations. The software is especially useful when a sectional model must combine geometric taper, multi-region composition, longitudinal stiffness variation, and solver-specific tabular output.

The key need addressed by CSF is therefore not another single-section calculator. It is a field-level modelling layer that makes the longitudinal evolution of a section a first-class object. This allows a structural member to be represented by coupled but independently controlled fields: geometry, axial/bending participation, and shear/torsion participation.

# State of the field

Several open-source tools address important parts of cross-section analysis. `sectionproperties` provides finite-element-based analysis of arbitrary cross-sections, including warping-based torsion [@vandenbergh2023sectionproperties]. `cross-section` provides sectional property calculations for individual profiles [@de2022cross]. OpenFAST and BeamDyn consume distributed structural properties for wind turbine analysis, but the user must supply the corresponding sectional tables [@jonkman2021openfast; @wang2016beamdyn]. OpenSees is a general finite element framework in which beam-column formulations require section definitions or section properties at element integration points [@mckenna2011opensees].

CSF occupies a different layer in this ecosystem. It represents the member as a continuous sectional field, samples it at requested stations, and exports solver-ready data. This makes it complementary to single-section tools rather than a replacement for them. Through the `csf_sp` bridge, CSF can send any station of the continuous field to `sectionproperties` for finite-element section analysis. Through the reverse `sp_csf` bridge, parametric sections from `sectionproperties` can be converted into CSF YAML geometries and then treated as evolving members.

The build-versus-contribute justification follows from this modelling level. Extending a single-section analysis package would not by itself provide a field representation with polygon-pair interpolation, independent longitudinal participation laws, nested composition, YAML action workflows, and solver export. CSF provides these capabilities as a dedicated pre-processing layer for continuous sectional models.

# Software design

CSF is built around a compact data model: vertices define polygonal regions, polygons form sections, and ordered section pairs define a continuous member. Corresponding polygon vertices are interpolated along the longitudinal coordinate, producing a deterministic intermediate section at any requested `z`. Section properties are then computed from the generated station section.

The main architectural choice is to keep geometry and participation separate. A polygon has an evolving shape, while its axial/bending contribution and shear/torsion contribution are controlled by `w_i(z)` and `shear_w_i(z)`. This avoids forcing all sectional effects through a single scalar. For example, a region may follow one participation law for axial and bending terms and another for torsion-related quantities. The `iso(nu)` shortcut links the two fields through an isotropic relation when appropriate, while explicit laws allow more general models.

A second design choice is to keep the same model available through two interfaces. The Python API supports scripted construction, testing, parameter studies, and integration in larger programs. The YAML action workflow supports reproducible file-based runs in which one file defines the continuous member and another file defines computations, plots, inspections, and exports. This division makes CSF usable both as a library and as a command-line research tool.

The torsion workflow is stratified. CSF includes analytical paths for thin-walled closed cells and open wall components, a Roark-type approximation with a fidelity indicator for general sections, and an optional finite-element route through `sectionproperties`. This provides fast built-in estimates while preserving access to higher-fidelity warping analysis when required.

# Research impact statement

CSF is currently a single-author open-source project. Its research significance
does not rely on an established external user community, but on the reproducible
modelling workflow it provides for structural members whose sectional properties
vary along the longitudinal axis.

The software has been developed and tested through reference research workflows
in which continuous section-property fields are generated from evolving
polygonal geometry and longitudinal participation laws. These workflows include
non-prismatic beam and tower models, solver-oriented station sampling, OpenSees
export, OpenFAST/BModes-oriented tower-property generation, and comparisons with
analytical or finite-element section-property calculations.

CSF contributes a reusable modelling abstraction rather than a one-off analysis
script: a member is represented as a continuous field composed of geometry,
axial/bending participation `w_i(z)`, and shear/torsion participation
`shear_w_i(z)`. This makes it possible to generate consistent tabular inputs for
downstream beam, tower, and aeroelastic solvers from a single declarative
section model.

Near-term scholarly significance is supported by the reproducible reference
materials distributed with the package: documented YAML workflows, Python API
examples, validation cases, solver export examples, and interoperability with
the established `sectionproperties` ecosystem. These materials allow other
researchers to install the package, inspect the model assumptions, reproduce the
reported section-property fields, and adapt the workflow to tapered, graded,
composite, repaired, or otherwise spatially varying beam-like members.
structural-analysis tools.

# AI usage disclosure

OpenAI ChatGPT was used to assist with documentation drafting, paper wording,
code-development support, code review and editing of explanatory
material. AI assistance was used for drafting, refactoring suggestions,
copy-editing, and technical phrasing, but not for making the core scientific,
architectural, validation, or design decisions.

All AI-assisted text, code suggestions, and technical content were reviewed,
edited, tested, validated, and approved by the author. The author remains fully
responsible for the software implementation, manuscript content, validation
results, licensing, originality, and scientific claims.

# Acknowledgements

The author thanks the developers of `sectionproperties` [@vandenbergh2023sectionproperties] for providing the open finite-element section-analysis backend used by the CSF integration workflow.

# References
