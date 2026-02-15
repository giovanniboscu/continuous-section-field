# CSF YAML Examples (No Python Coding Required)

1. **`write_opensees_geometry`**  
   Exports CSF section data along `z` into an OpenSees-ready Tcl geometry file, using sampled stations and reference material parameters (`E_ref`, `nu`).

2. **`degradation_laws_offshore`**  
   Collection of offshore-oriented degradation laws (e.g., splash-zone effects, corrosion-driven reductions) to model longitudinal property loss through `w(z)` and related CSF inputs.

3. **Torsion examples: `J_sv_cell` / `J_sv_wall`**  
   Practical examples showing how to compute Saint-Venant torsional constant in CSF for closed-cell behavior (`J_sv_cell`) and thin-wall/open-wall behavior (`J_sv_wall`), with tag-based polygon selection.

4. **Closed-Cell CHS with Splash-Zone Weight Law**  
   This example demonstrates a **reproducible CSF workflow** for a circular hollow steel member (CHS), combining closed-cell torsion and a splash-zone degradation law to evaluate section-property evolution along `z`.

5. **Simple rectangle example**  
   Minimal CSF case based on a rectangular section, intended for quick setup, validation, and first checks of area/inertia/torsion trends along the member length.


This directory contains **ready-to-run CSF examples** that require **no Python programming**.
Each example is defined by **two YAML files**:

- `geometry.yaml` — defines the cross-sections at the end stations (e.g., `S0`, `S1`) using explicit polygons.
- `actions.yaml` — defines what CSF should do (analysis, plots, exports) using `CSF_ACTIONS`.

The workflow is purely declarative: you edit YAML files and run the CSF actions runner.

---

## File Roles

### 1) `geometry.yaml`
Defines the geometry (and weights/material tags if used) at discrete stations along **z**.

Typical structure:

- `CSF.sections.S0` and `CSF.sections.S1` include:
  - `z`: station coordinate
  - `polygons`: one or more polygon definitions
    - `weight`: scalar weight for that polygon
    - `vertices`: polygon vertices in **CCW** order

Important:
- Polygon names and vertex counts must match between stations for consistent interpolation.
- Any required attributes must be explicitly provided (no silent defaults).

### 2) `actions.yaml`
Defines station sets and an ordered list of actions to execute.

Typical structure:

- `CSF_ACTIONS.stations`: named station sets (lists of absolute z coordinates)
- `CSF_ACTIONS.actions`: ordered list of actions (analysis, plots, exports, writers)

Some actions use explicit `stations`, while others sample internally and do **not** accept stations.

---

## How to Run

From this directory:

```bash
python CSFActions.py geometry.yaml actions.yaml
```

Outputs (plots, CSV/TXT reports, exported YAML, templates, etc.) are written to the paths listed under each action’s `output`.

---

## Example: Linearly Tapered Rectangle

A minimal example usually includes:

- `geometry.yaml`: rectangle at `S0` and `S1` (same polygon name, same vertex count)
- `actions.yaml`:
  - `section_full_analysis` at selected stations
  - `plot_section_2d` at stations
  - `plot_properties` along z (internal sampling)
  - `plot_volume_3d` (internal sampling)
  - `export_yaml` for the end sections

---

## Notes

- Keep all geometry vertices **CCW**.
- Use station sets to control where section-based actions evaluate properties.
- Writers (e.g., OpenSees/SAP2000) may have additional required parameters; see the action definitions in `CSFActions.py`.
