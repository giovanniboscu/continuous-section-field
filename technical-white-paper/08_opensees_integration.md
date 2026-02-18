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

## 2. What CSF Actually Exports

CSF exports a **list of stations** along the member.

Each station contains:
- Section properties: `A, Iy, Iz, J`
- Stiffness products (depending on mapping): `EA, EIy, EIz, GJ`
- Centroid offsets: `Cx(z), Cy(z)`

They are evaluated directly from the continuous ruled-surface geometry and weight laws.

---

## 3. Why Standard `beamIntegration Lobatto` May Not Be Enough

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

## 5. Station Placement: Gauss–Lobatto Rule

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

## 6. Element Construction Strategy

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

## 7. CSF Is *Not* Piecewise-Prismatic

### CSF + OpenSees model
- CSF defines a **continuous field**
- sampling locations are **prescribed by quadrature**
- no averaging, no guessing
- OpenSees performs **numerical quadrature of a known field**

The OpenSees elements are therefore **integration carriers**, not modeling approximations.

---

## 8. Centroid Axis and Eccentricity Preservation

Non-prismatic members often have:
- variable centroid position
- eccentric stiffness relative to a reference axis

CSF explicitly tracks:
```text
Cx(z), Cy(z)
```

## 9. Torsion model

`J_sv_wall` and `J_sv_cell` are thin-walled Saint-Venant torsion estimates for, respectively, **open** walls and **closed** cells (Bredt–Batho), while `J_sv` is the **general** Saint-Venant torsion estimate when thin-walled assumptions are not applicable.  
When exporting to OpenSees (which accepts a single `J`), a consistent practice is to select a `J_eff` (e.g., `max(J_sv_cell, J_sv_wall)` if any > 0, otherwise `J_sv`).


### OpenSees implementation
- create reference nodes along a straight axis
- create centroid nodes offset by `Cx, Cy`
- connect them using:

`rigidLink beam`

This produces:
- automatic moment–axial coupling
- correct geometric eccentricity
- no artificial offset forces

> **Note**  
> This requires `constraints Transformation` in OpenSees.
