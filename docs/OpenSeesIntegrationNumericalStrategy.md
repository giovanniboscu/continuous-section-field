# CSF → OpenSees Integration and Numerical Strategy (csfopenseescon)

This document explains **how CSF (Continuous Section Field)** exports a continuously varying member and how that data is consumed to build a correct **OpenSees force-based beam model** (OpenSeesPy *or* OpenSees binary).

The focus is on the **numerical integration strategy**: what is sampled, where it is sampled, and how those samples are mapped into OpenSees without ambiguity.

---

## 0) What CSF is (and what it is not)

CSF is **not** a finite element solver.  
CSF is a **geometric + constitutive engine** that produces a *continuous* description of a single non-prismatic member:

- ruled-surface interpolation of section geometry between the two ends,
- continuous evaluation of sectional properties (A(z), I(z), centroid C(z), etc.),
- optional longitudinal material/weight laws (w(z)) including void logic.

OpenSees performs the structural solution; CSF provides the **station data** to feed OpenSees.

---

## 1) The central idea: continuous field → quadrature sampling

A continuously varying member cannot be represented in OpenSees without sampling, because OpenSees integrates section behavior numerically.

CSF therefore exports a set of **integration stations** along the axis:

- Station coordinates: **Gauss–Lobatto points** (includes the end points).
- At each station *i*:
  - the section properties are evaluated from the continuous field,
  - the centroid offset (xc, yc) is stored (variable eccentricity / “tilt”).

This is **not** the classic “piecewise-prismatic” modeling where the user arbitrarily subdivides the beam into constant segments to approximate taper.
Instead it is:

> **Quadrature sampling of a continuous stiffness field** at mathematically chosen points (Gauss–Lobatto), with exact endpoint sampling.

---

## 2) The exported file: `geometry.tcl` is a DATA FILE

The CSF export called `geometry.tcl` is intentionally a **data container**.

It is **not** a complete OpenSees model to run by itself.

A builder script (OpenSeesPy or Tcl builder) reads it line-by-line and constructs:
- nodes,
- constraints/links,
- elements,
- integration commands,
- loads and boundary conditions.

### 2.1 Required blocks in `geometry.tcl`

Typical CSF export contains:

1) Header (human hints):
```tcl
# Beam Length: 10.000 m | Int. Points: 10
# CSF_EXPORT_MODE: E=E_ref ; A/I are CSF-weighted (modular) properties
```

2) Station coordinates (machine-readable, **mandatory**):
```tcl
# CSF_Z_STATIONS: 0.000000 0.402330 ... 10.000000
```

3) A minimal `geomTransf` orientation (builder reuses it):
```tcl
geomTransf Linear 1 1 0 0
```

4) One **section line per station** with optional centroid offsets:
```tcl
section Elastic <tag> <E> <A> <Iz> <Iy> <G> <J> <xc> <yc>
```

5) Optional “template” lines (commented) for humans:
```tcl
# TEMPLATE ONLY ...
# beamIntegration Lobatto ...
# element forceBeamColumn ...
```

### 2.2 What the section line represents

For station *i* at position `zStations[i]`, the exported line:

```tcl
section Elastic i  E  A  Iz  Iy  G  J  xc  yc
```

means:

- **A, Iz, Iy, J** are the section properties evaluated at that station.
- **xc, yc** are the measured centroid offsets (local neutral axis shift).
- **E and G interpretation depends on the export mode** (see next section).

---

## 3) Material conventions: `E=E_ref` vs `E=E_real`

OpenSees is unitless; it will produce “real” displacements only if **your stiffness scale is consistent** with your unit system.

CSF supports two valid workflows:

### 3.1 Mode A — export REAL moduli (direct physical stiffness)
- You export **E(z)** (and thus G(z)) in consistent physical units.
- The OpenSees builder should use `material_mode = from_file`.

Result: OpenSees uses E/G exactly as written.

### 3.2 Mode B — export a reference modulus, embed material effects in “modular properties”
This is your documented approach:

```tcl
# CSF_EXPORT_MODE: E=E_ref ; A/I are CSF-weighted (modular) properties
```

Meaning:
- CSF writes a convenient constant `E_ref` into the file,
- the effects of weights / multi-material / void logic are already embedded in:
  - A, Iz, Iy, etc. (modular/weighted section properties).

In this case, the OpenSees builder must decide:

- If you want **physically correct displacements in your unit system**, you must use:
  - `material_mode = override` and provide `E_real` (and G_real).
- If you are doing a **normalized analysis**, you can keep `E_ref` as a unit scale.

**Recommendation (practical):**
- Keep the geometry export stable (`E_ref`).
- Let the builder script carry the physical unit decision (`override E/G`).

This is why the builder exposes:
- `MATERIAL_MODE = "override" | "from_file"`
- `E_REF`, `G_REF`, and optionally `nu` to compute G.

---

## 4) Centroid shift / variable eccentricity (“tilt”) handling

A critical CSF feature is the station-by-station centroid drift (e.g. `yc(z)` changing).

OpenSees frame elements define an element axis between nodes.  
If you only define two end nodes, you lose the local centroid drift.

### 4.1 The CSF strategy used here

The builder creates two node chains:

1) **Reference axis nodes**  
A straight, theoretical line (commonly x=y=0) used for:
- boundary conditions,
- loads,
- “external interface” of the member.

2) **Centroid axis nodes**  
At each station:
- node is placed at `reference + (xc, yc)`.

3) **Rigid kinematic bridge**
Each station connects:
- `reference node i` → `centroid node i` via:
  - `rigidLink beam ref_i cen_i`

This ensures:
- loads and boundary conditions can be applied to a clean reference axis,
- the beam stiffness “lives” on the physical centroid axis,
- the model captures the **real eccentricity** that varies along the member.

**Important OpenSees note:**  
`rigidLink` creates multi-point constraints, so you must use:

```tcl
constraints Transformation
```

(not `Plain`).

---

## 5) The integration method in OpenSees (the core point)

### 5.1 Why Gauss–Lobatto stations
CSF uses **Gauss–Lobatto** stations because they include the endpoints:

- station 1 is exactly at z=0,
- station N is exactly at z=L.

That matters because:
- support reactions and end rotations depend heavily on end stiffness sampling,
- the tip displacement is sensitive to the end stiffness distribution.

### 5.2 How stations become OpenSees integration

OpenSees’ `forceBeamColumn` integrates section flexibility along the element.  
However, the standard integration commands typically assume a single section (or a limited mapping).

CSF requires **multiple distinct sections** along a single member.

There are two robust and transparent ways to do this:

#### Option 1 (recommended, and used in your builder): **Segmented member with endpoint sampling**
- Build **one element per station segment** (N stations → N−1 elements).
- For segment i between station i and i+1:
  - assign the two station sections to the segment endpoints
  - integrate with `beamIntegration UserDefined` using 2 points:

Conceptually:
- section_i at loc=0
- section_{i+1} at loc=1
- weights 0.5 and 0.5 (simple endpoint sampling)

This is **not** “manual piecewise meshing” by the user:
- stations are fixed by Gauss–Lobatto,
- sections are CSF-evaluated from the continuous field,
- the discretization is systematic and deterministic.

#### Option 2: Single element with many sections (only if the solver supports it cleanly)
In pure OpenSees Tcl, this is typically not as clean as Option 1, because
the standard Lobatto command is usually not used to map a full list of distinct sections in the way CSF needs.

If you need “one element only”, you must ensure the integration command actually supports the full section list as intended.
In practice, Option 1 is clearer, more portable, and easier to validate.

---

## 6) Torsion (J) and numerical stability

3D frame elements require a torsional stiffness to avoid singular matrices.

CSF exports a torsional constant `J`:
- may be computed by an approximation designed for stability,
- especially important for open/thin-walled sections.

Interpretation:
- For solid/compact shapes: usually acceptable as engineering torsion stiffness.
- For thin-walled open shapes: treat as a **stability placeholder** unless you provide a dedicated torsion model.

---

## 7) What a new user should do (end-to-end workflow)

### Step 1 — Build your CSF member and export `geometry.tcl`
Run CSF and generate the file containing:
- `CSF_Z_STATIONS`,
- `section Elastic ... xc yc` lines.

### Step 2 — Choose your solver path

#### Path A: OpenSeesPy (Python)
- Use the provided OpenSeesPy example builder.
- Choose:
  - `override E/G` if your export is `E_ref`,
  - `from_file` if your export uses real E/G.

#### Path B: OpenSees binary (command line)
- Generate `csf_member_builder.tcl` (or adapt the example).
- Run with your OpenSees installation, e.g.:
```bash
OpenSees csf_member_builder.tcl
```

(With conda, for example:)
```bash
conda run -n opensees OpenSees csf_member_builder.tcl
```

---

## 8) “Isn’t this piecewise?” — the correct technical response

A classic piecewise-prismatic model is:
- user-chosen subdivision count,
- user-chosen sampling positions,
- constant properties per sub-element.

CSF + OpenSees (this workflow) is:
- **continuous geometry and stiffness** computed from ruled-surface interpolation,
- **Gauss–Lobatto stationing** (fixed quadrature points, includes endpoints),
- **station-by-station sections** exported deterministically,
- OpenSees integrates the flexibility field through a force-based formulation.

So the correct statement is:

> OpenSees still uses numerical integration (it must), but CSF controls the sampling using Gauss–Lobatto points and continuous-field evaluation. It is quadrature sampling of a continuous stiffness field, not an arbitrary stepped approximation.

---

## 9) Practical checklist (common pitfalls)

-  Always export `# CSF_Z_STATIONS: ...` and ensure its length equals the number of section lines.
-  If you use `rigidLink`, use `constraints Transformation`.
-  If `E` in `geometry.tcl` is a reference modulus (`E_ref`), set `override E/G` in the builder when you want real displacements.
-  Keep your unit system consistent across:
  - geometry units,
  - forces,
  - E/G,
  - inertias.

---

## Quick reference (what is used in OpenSees)

- Element formulation: `forceBeamColumn`
- Kinematic bridge for variable centroid: `rigidLink beam`
- Station placement: `CSF_Z_STATIONS` (Gauss–Lobatto points)
- Integration mapping strategy (recommended): **N−1 elements**, each with **2-point UserDefined** endpoint sampling
- Constraints handler: `Transformation` (required by rigid links)
---
---
---
## OpenSees Integration & Numerical Strategy

The CSF library bridges the gap between continuous geometric modeling and structural analysis by generating optimized OpenSees models.

### 1. Force-Based Formulation

The library uses the `forceBeamColumn` element (Non-linear Beam-Column). This approach is superior for tapered members because it integrates the **section flexibility** along the element. Unlike standard elements, it can capture the exact deformation of a variable-section beam using a single element, avoiding the need to manually break the beam into many small segments.

### 2. Longitudinal Sampling (Gauss-Lobatto)

The internal variation of the cross-section is handled through a strategic sampling process:

* **Point Distribution:** Section properties are sampled using the **Gauss-Lobatto rule**. This ensures that the beam ends (nodes) are included in the calculation, which is critical for accurate support reactions and tip displacement.
* **Property Mapping:** Every sampling point is assigned a unique `section Elastic` tag. These tags are then linked via the `beamIntegration` command, mapping the continuous geometric transition onto the element's numerical scheme.

### 3. Torsional Rigidity () - Beta Status

The torsional constant () is required for numerical stability in 3D FEA models to prevent singular matrices.

* **Current Implementation:** The library uses a semi-empirical approximation based on the area and polar moment of inertia.
* **Scope:** This method provides reliable numerical convergence for solid, compact sections.
* **Note:** For thin-walled or complex open profiles, this value should be considered a preliminary estimate for stability purposes.

### 4. Centroidal Axis Alignment

When the section height or shape varies asymmetrically, the neutral axis might shift.

* **Alignment Logic:** CSF tracks the centroid () of every sampled section and uses a linear regression to align the OpenSees nodes.
* **Purpose:** This ensures the element's longitudinal axis follows the physical center of the beam, minimizing unintended coupling between axial and bending forces.

---

### Quick Implementation Details

* **Module:** `openseespy`
* **Element Type:** `forceBeamColumn`
* **Integration Scheme:** `beamIntegration Lobatto`
* **Flexibility:** Topology-agnostic (automatically adapts to any number of integration points).

