# CSF User Guide — Modeling and Sectional Analysis

Programmer-oriented documentation for building, validating, and integrating **Continuous Section Field (CSF)** models.

This README is the entry point. Detailed chapters will be added incrementally.

---

## What this guide is for

This guide explains how to:

- define CSF geometry and sections programmatically (via YAML-driven workflows),
- run sectional analyses consistently,
- handle `@wall` and `@cell` torsion paths correctly,
- integrate CSF outputs into downstream structural solvers.

---

## Intended audience

- Developers extending CSF internals
- Engineers scripting CSF workflows
- Users integrating CSF with external analysis pipelines

---

## Scope boundaries

CSF is a **geometric and sectional-property engine**.

CSF is **not** a global structural solver.  
It computes/exports section data; external solvers handle equilibrium and structural response.

---

## Modeling principles enforced by CSF

- Polygons must be **CCW** (positive signed area).
- Polygon closure is implicit (first vertex repetition is optional).
- Required attributes must be explicit (no silent defaults for missing mandatory data).
- `weight` is a **polygon-level** property.
- In geometric-composition mode, holes are modeled with dedicated polygons (`weight = 0`).
- `@wall` / `@cell` paths operate on explicitly tagged polygons as standalone entities.

---

## Current document status

This README is intentionally minimal.  
Detailed chapters will be added on command, including:

1. Geometry rules and data model  
2. Tags and semantics (`@wall`, `@cell`, `@t=`)  
3. Stations and interpolation  
4. Sectional properties API  
5. Torsion (`J_sv_wall`, `J_sv_cell`)  
6. Actions pipeline and diagnostics  
7. Validation and integration patterns

---

## Recommended folder structure

```text
docs/
  programmer-guide/
    README.md
    01_geometry_model.md
    02_tags_and_semantics.md
    03_stations_and_interpolation.md
    04_sectional_properties_api.md
    05_torsion_wall_and_cell.md
    06_actions_pipeline.md
    07_errors_and_diagnostics.md
    08_validation_and_benchmarks.md
    09_solver_integration.md
```

---

## Quick start (placeholder)

A full quick start will be provided in the next chapter.  
For now, use your existing `geometry.yaml` + `actions.yaml` workflow as baseline and keep inputs strictly validated upstream.

---

## License and contribution

Follow the repository’s root `LICENSE` and contribution workflow.  
When adding examples, prefer small, reproducible cases with explicit units and expected numeric checks.
