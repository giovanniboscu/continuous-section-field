# CSF YAML Examples (No Coding Required)

This directory contains ready-to-run CSF examples designed to demonstrate
continuous-section modelling workflows without requiring custom programming.

The examples are based on YAML input files and cover several CSF capabilities,
including:

- continuously varying geometry along `z`;
- polygon-based section interpolation;
- independent weight and shear-weight laws;
- open-wall and closed-cell torsion workflows;
- degradation and corrosion-oriented modelling;
- section-property tracking along the member axis;
- thin-wall verification and regression cases;
- morphing and twisted geometries;
- offshore-oriented examples;
- external-solver-oriented exports;
- verification-oriented numerical workflows.

The purpose of this directory is to provide practical, reproducible reference
cases for using CSF in different modelling contexts.

---

## Example Categories

### 1. Basic Geometry and Property Tracking

These examples focus on simple section definitions and section-property
evolution along the member axis.

They are intended to check:

- area evolution;
- centroid motion;
- inertia variation;
- section interpolation;
- torsional trends.

---

### 2. Thin-Wall and Torsion Examples (`@wall` / `@cell`)

Several examples demonstrate the CSF Saint-Venant torsional indicators:

- `J_sv_wall` for open thin-walled layouts;
- `J_sv_cell` for closed-cell behavior.

The examples include:

- C-shaped sections;
- E/F/H/I/L/T layouts;
- rotated thin-wall geometries;
- multi-branch wall configurations;
- regression and verification cases.

Independent section analyses through `sectionproperties` are used in some cases
as reference comparisons for verification.

Some geometries intentionally exceed the selected tolerance in order to document
the practical limits of simplified thin-wall approximations.

---

### 3. Offshore and Degradation-Oriented Examples

Some examples demonstrate how CSF can model longitudinal property loss through:

- `weight_laws`;
- `shear_weight_laws`;
- corrosion-inspired reductions;
- splash-zone-type degradation patterns;
- offshore-oriented section variation.

These examples show how geometric variation and material participation can be
combined within the same continuous-section model.

---

### 4. Morphing and Twisted Geometries

Several examples demonstrate:

- continuous shape morphing;
- twisted members;
- variable towers;
- polygon interpolation between stations;
- ruled-volume generation.

These workflows are intended to illustrate geometric continuity and section
evolution along the member axis.

---

### 5. Export and External Solver Workflows

Some examples focus on interoperability and export pipelines, including:

- structural-solver-oriented geometry exports;
- Tcl geometry generation;
- exported YAML snapshots;
- template-oriented output files;
- verification-oriented reports.

These examples demonstrate how CSF geometries and section properties can be
transferred to external structural workflows.

---

## File Roles

### Geometry files

Geometry files define the section layout and polygon weights at discrete
stations along `z`.

They typically contain:

- section definitions such as `S0` and `S1`;
- polygon definitions;
- scalar weights;
- polygon tags such as `@wall` and `@cell`;
- explicit vertex lists in counter-clockwise order.

Polygon names and vertex counts should remain compatible between stations when
continuous interpolation is required.

---

### Action files

Action files define the analyses, plots, exports, and reports associated with a
case.

They may include:

- selected-station section analyses;
- section-property reports;
- 2D section plots;
- 3D volume plots;
- property evolution plots;
- geometry exports;
- solver-oriented writers;
- verification-oriented outputs.

---

## Execution Notes

Each example may contain its own workflow, auxiliary scripts, action files,
verification procedures, or solver-specific export steps.

Users should refer to the documentation and notes provided inside the
corresponding example directory for execution details and expected outputs.

---

## Philosophy

The examples are intentionally designed as declarative workflows rather than
programmatic extensions.

The objective is to allow:

- reproducible verification;
- geometry experimentation;
- continuous-section studies;
- torsional verification;
- degradation modelling;
- external solver integration;

using YAML-based inputs and case-specific documentation.
