# 08_opensees_integration.md

# OpenSees Integration

This document explains **how CSF outputs are consumed by OpenSees**, and - more importantly - **why the chosen integration strategy is mathematically consistent with a continuous stiffness field**.

---

## 1. Role Separation: CSF vs OpenSees

It is essential to separate responsibilities:

### CSF
- Defines a **continuous geometric and stiffness field** along the member axis `z`
- Computes section properties **exactly at prescribed locations**
- Controls *where* and *how* properties are sampled
- Outputs **solver-ready station data**

### OpenSees
- Solves the **structural equilibrium problem**
- Integrates section response along elements
- Does **not** know how the section properties were generated

CSF is therefore a **pre-processor with mathematical authority over section definition**.  
OpenSees is a **numerical integrator and solver**.

---

## 2. Why Standard `beamIntegration Lobatto` May Not Be Enough

In OpenSees, the standard integration:

- `beamIntegration Lobatto ...`

defines the **integration rule** (number and location of points, and weights), but it does not provide an explicit, user-authored list of:
- **which section tag** is used at each integration point
- **where** (local coordinate `xi`) each section is placed
- **which integration weights** are associated to each point

When you need a strict one-to-one, fully explicit mapping between:
- exported CSF stations
- OpenSees integration points

the only OpenSees mechanism that can encode `(sectionTag, xi, weight)` explicitly is:

- `beamIntegration UserDefined ...`

> **Current CSF export status**  
> The current `write_opensees_geometry()` export samples stations at Gauss–Lobatto locations and writes the corresponding `section Elastic ...` definitions.  
> It does **not** export `UserDefined` integration data (xi/weights), and it does **not** emit element definitions.  
> The station coordinates can be written as a comment line (e.g. `# CSF_Z_STATIONS: ...`) for traceability by external builders.

---

## 3. Station Placement: Gauss–Lobatto Rule

CSF places stations using the **Gauss–Lobatto quadrature rule**.

Key properties:
- Endpoints **are included**
- Optimal accuracy for smooth fields
- Exact sampling at:
  - member start
  - member end

This guarantees:
- boundary conditions applied at **true physical ends**
- no artificial extrapolation at supports or tips

---

## 4. Element Construction Strategy

### What is implemented today (export side)

`write_opensees_geometry()` currently:
- generates **Gauss–Lobatto stations** for a chosen `n_points`
- writes one `section Elastic <tag> ...` per station
- optionally writes station coordinates in a comment line for traceability (for example `# CSF_Z_STATIONS: ...`)

It does **not** currently:
- build OpenSees `element` commands
- write `beamIntegration UserDefined ...` (xi/weights)

### Optional robust strategy (solver-side)

If you want an unambiguous station-to-integration mapping in the OpenSees model, a robust approach is:

#### Chain of Elements Between Stations

For stations (conceptually):
```text
z0, z1, z2, ..., zn
```

Create:
- one OpenSees element between each consecutive pair

For element `i -> i+1`:
- local coordinate `0` → station `i`
- local coordinate `1` → station `i+1`

Example integration definition (two-point symmetric rule):

```
beamIntegration UserDefined <tag> <sec_i> 0.0 0.5 <sec_{i+1}> 1.0 0.5
```

This ensures:
- stiffness sampled **exactly at stations used by CSF**
- no invented intermediate section
- symmetric integration weights

---

## 5. CSF Is *Not* Piecewise-Prismatic

### CSF + OpenSees model
- CSF defines a **continuous field**
- sampling locations are **prescribed by quadrature**
- no averaging, no guessing
- OpenSees performs **numerical quadrature of a known field**

The OpenSees elements are therefore **integration carriers**, not modeling approximations.

---


# CSF -- Torsion Model for Export

## 6. Available Torsion Quantities

CSF may compute the following Saint-Venant torsion estimates:

-   **J_sv_wall**\
    Thin-walled Saint-Venant torsion constant for **open walls**.

-   **J_sv_cell**\
    Thin-walled Saint-Venant torsion constant for **closed cells**\
    (Bredt--Batho formulation).

-   **J_sv**\
    General Saint-Venant torsion constant when thin-walled assumptions
    are not applicable.

------------------------------------------------------------------------

## 6.1 Export Philosophy

External solvers such as OpenSees require a **single torsional constant
`J`**.

For export purposes:

-   Only thin-walled torsion contributions are considered.
-   The general `J_sv` value is **not** used as fallback.
-   If no valid thin-walled contribution exists, torsion is exported as
    zero and a warning is issued.

This ensures deterministic and explicit behavior.

------------------------------------------------------------------------

## 6.2 Effective Torsional Constant

Let:

-   `cell_ok` → `J_sv_cell > 0`
-   `wall_ok` → `J_sv_wall > 0`

Then:

### Case A -- At least one valid thin-walled contribution

If either closed-cell or open-wall torsion is valid:

    J_eff = J_sv_cell (if valid) + J_sv_wall (if valid)

The export metadata records which contribution was used:

-   `J_sv_cell`
-   `J_sv_wall`
-   `J_sv_cell + J_sv_wall`

### Case B -- No valid thin-walled contribution

If neither contribution is valid:

    J_eff = 0

A warning is emitted stating that no Saint-Venant thin-walled torsion
contribution is available for export.

No automatic substitution with `J_sv` occurs.

------------------------------------------------------------------------

## 6.3 Rationale

The export model reflects the CSF philosophy:

-   Thin-walled open walls and closed cells represent distinct physical
    torsion mechanisms.
-   Their Saint-Venant contributions are additive when both are present.
-   Ambiguous fallback External solvers such as OpenSees require a **single torsional constant
`J`**.

For export purposes:

-   Only thin-walled torsion contributions are considered.
-   The general `J_sv` value is **not** used as fallback.
-   If no valid thin-walled contribution exists, torsion is exported as
    zero and a warning is issued.

This ensures deterministic and explicit behavior.

------------------------------------------------------------------------

## 6.4 Effective Torsional Constant

Let:

-   `cell_ok` → `J_sv_cell > 0`
-   `wall_ok` → `J_sv_wall > 0`

Then:

### Case A -- At least one valid thin-walled contribution

If either closed-cell or open-wall torsion is valid:

    J_eff = J_sv_cell (if valid) + J_sv_wall (if valid)

The export metadata records which contribution was used:

-   `J_sv_cell`
-   `J_sv_wall`
-   `J_sv_cell + J_sv_wall`

### Case B -- No valid thin-walled contribution

If neither contribution is valid:

    J_eff = 0

A warning is emitted stating that no Saint-Venant thin-walled torsion
contribution is available for export.

No automatic substitution with `J_sv` occurs.

------------------------------------------------------------------------

## 6.5 Rationale

The export model reflects the CSF philosophy:

-   Thin-walled open walls and closed cells represent distinct physical
    torsion mechanisms.
-   Their Saint-Venant contributions are additive when both are present.
-   Ambiguous fallback rules are avoided.
-   No silent defaults are introduced.

The exported torsional constant is therefore:

-   Explicit
-   Traceable
-   Deterministic

------------------------------------------------------------------------

## 6.6 Eccentricity Handling (Centroid Offsets)

If section centroid offsets `(Cx, Cy)` are present:

-   A reference node is created on the straight axis.
-   A centroid node is created at `(Cx, Cy)`.
-   A rigid beam link connects them.

This guarantees:

-   Correct geometric eccentricity
-   Proper axial--bending coupling
-   No artificial offset forces

In OpenSees this requires:

    constraints Transformation

rules are avoided.
-   No silent defaults are introduced.

The exported torsional constant is therefore:

-   Explicit
-   Traceable
-   Deterministic

------------------------------------------------------------------------

## 6.7 Eccentricity Handling (Centroid Offsets)

If section centroid offsets `(Cx, Cy)` are present:

-   A reference node is created on the straight axis.
-   A centroid node is created at `(Cx, Cy)`.
-   A rigid beam link connects them.

This guarantees:

-   Correct geometric eccentricity
-   Proper axial--bending coupling
-   No artificial offset forces

In OpenSees this requires:

    constraints Transformation

------------------------------------------------------------------------

## Summary

-   Export uses only `J_sv_cell` and `J_sv_wall`
-   Contributions are additive if both valid
-   No fallback to `J_sv`
-   Zero torsion is exported when no valid thin-walled mechanism exists
-   Behavior is deterministic and explicitly documented
