# CSF → OpenSees Integration and Numerical Strategy 

This document explains how **CSF (Continuous Section Field)** exports a continuously varying member and how that data is consumed to build a consistent **OpenSees `forceBeamColumn` model** (OpenSeesPy or OpenSees Tcl).

The focus is the **numerical integration strategy**: what is sampled, where it is sampled, and how those samples are mapped into OpenSees **without inventing extra sections**.


---

## 1) The central idea: continuous field → quadrature stations

OpenSees integrates section behavior numerically along the element axis, so a continuously varying member must be **sampled**.

CSF exports a set of **stations** along the axis.

In the current OpenSees export (`write_opensees_geometry()`), station coordinates are **Gauss–Lobatto points** (including both endpoints).  
At each station `i`:
- section properties are evaluated from the continuous field,
- centroid offsets `(xc, yc)` are stored.

This is **not** user-chosen “piecewise-prismatic stepping”. It is:

> **quadrature stationing** of a continuous stiffness field at Gauss–Lobatto abscissae (with endpoint sampling by construction).

---

## 2) The exported file: `geometry.tcl` is a DATA FILE

The CSF export `geometry.tcl` is intentionally a **data container**.

It is **not** a full OpenSees model to be run directly.  
A builder script reads it line-by-line and constructs nodes, constraints, elements, integration commands, loads, and BCs.

### 2.1 Typical blocks in `geometry.tcl`

Typical export contains:

1) Header (human hints only)
```tcl
# Beam Length: 10.000000 (units follow your model)
# Stations: 10
# NOTE: This file is meant to be PARSED AS DATA (do NOT source it as Tcl).
```

2) Station coordinates (**machine-readable**, strongly recommended)
```tcl
# CSF_Z_STATIONS: z0 z1 ... zN-1
```

3) A minimal transformation orientation (builder reuses it)
```tcl
geomTransf Linear 1 vx vy vz
```

4) One **section line per station** with appended centroid offsets (CSF-only fields)
```tcl
section Elastic <tag> <E> <A> <Iz> <Iy> <G> <J> <xc> <yc>
```

5) Optional informational nodes (ignored by robust builders)
```tcl
node 1 x0 y0 z0
node 2 x1 y1 z1
```

### 2.2 Meaning of the exported `section Elastic` line

For station `i` at position `CSF_Z_STATIONS[i]`, the exported line:

```tcl
section Elastic i  E  A  Iz  Iy  G  J  xc  yc
```

means:

- `A, Iz, Iy, J` are **evaluated at that station** by CSF (already including CSF weights according to the chosen export contract).
- `(xc, yc)` are **centroid offsets** in the local section plane (used to build a centroid axis).
- The interpretation of `E, G` depends on the chosen export convention (next section).

**Note:** `xc yc` are **not** OpenSees syntax. They are extra fields intended for the builder.

---

## 3) Material conventions: `E=E_ref` vs `E=E_real`

OpenSees is unitless; “real” displacements require consistent stiffness units.

CSF supports two workflows.

### 3.1 Mode A — export physical moduli (direct stiffness)

- `geometry.tcl` stores the physical `E(z)` and `G(z)`.
- The builder uses `MATERIAL_INPUT_MODE = "from_file"`.

Result: OpenSees uses `E, G` exactly as written in the file.

### 3.2 Mode B — export reference modulus and “modular properties”

In this contract:

- `geometry.tcl` stores a convenient constant `E_ref` (and compatible `G_ref`),
- the effects of weights / multi-material / void logic are embedded into the exported section properties `{A, Iz, Iy, J}`.

A typical header states this explicitly, e.g.
```tcl
# CSF_EXPORT_MODE: E=E_ref ; A/I/J are station-wise CSF results (already weighted)
```

If you want “real” displacements, the builder should typically use:

- `MATERIAL_INPUT_MODE = "override"` and provide physical `E_real` (and `G_real`).

---

## 4) Variable centroid (“tilt”) handling

CSF can export centroid offsets that vary with `z`: `(xc(z), yc(z))`.

OpenSees frame elements define their axis between element nodes. If you only define the two end nodes, you cannot represent a centroid axis that changes along the member.

### 4.1 Strategy used by the builder: reference axis + centroid axis

The builder creates two node chains:

1) **Reference axis nodes**  
A clean straight line used for BCs and loads.

2) **Centroid axis nodes**  
At each station:
```text
x_cen(z_i) = x_ref(z_i) + xc(z_i)*e1 + yc(z_i)*e2
```

3) **Rigid kinematic bridge**
Each station connects:
```tcl
rigidLink beam $refNode_i $cenNode_i
```

This lets you apply BCs/loads on a clean axis while stiffness “lives” on the centroid axis.

### 4.2 OpenSees constraints handler requirement

`rigidLink` creates multi-point constraints, therefore the model must use:
```tcl
constraints Transformation
```
(not `Plain`).

---

## 5) Integration method in OpenSees (core)

CSF exports stations. The OpenSees model should honor them **without inventing intermediate sections**.

### 5.1 Two valid mappings (depending on centroid behavior)

There are two consistent strategies, depending on whether `(xc, yc)` are constant.

#### Strategy A — Single element with N-point Gauss–Lobatto (strict)

Allowed only if centroid offsets are constant along the member:
```text
xc(z) = const,   yc(z) = const
```

Then the builder can use:

- **one** `forceBeamColumn` element over the full span,
- `beamIntegration UserDefined` with:
  - `N` stations,
  - **Gauss–Lobatto locations** `s_i` in `[0,1]`,
  - **Gauss–Lobatto weights** `w_i`.

Station matching requirement (strict): the exported `CSF_Z_STATIONS` must match the Lobatto abscissae mapped to `[0,1]`:
```text
s_i = (z_i - z_0) / (z_{N-1} - z_0)
max_i | s_i - s_i^Lobatto | < eps
```

If it does not match, this strategy is rejected (no fallback weights).

#### Strategy B — Segmented elements with 2-point endpoint sampling (Lobatto-2)

Required when centroid offsets vary (tilt/curvature), because you need nodes at intermediate stations to represent the centroid axis.

- Build **one element per station-to-station segment** (`N` stations → `N-1` elements).
- For each segment `i -> i+1`, assign:
  - `section_i` at `s=0`,
  - `section_{i+1}` at `s=1`,
  - weights `w={0.5, 0.5}` (Lobatto-2 / endpoint trapezoid on that segment).

This uses only exported station sections and preserves the station-wise centroid axis.

### 5.2 “Example builder behavior (‘AUTO’)”


A builder may run in `"auto"` mode by default:

- If `(xc, yc)` are **constant** across all stations → **Strategy A** (single element, strict N-point Lobatto).
- If `(xc, yc)` **vary** across stations → **Strategy B** (segmented, 2-point endpoint per segment).

This avoids the problematic case where a single element is used while the centroid axis is actually varying (which would silently discard geometry).

---

## 6) Torsion input `J`

In OpenSees `section Elastic`, torsional stiffness is represented by `G * J` (a single scalar per section).

CSF exports **one torsion constant per station** into the `J` slot of each line:

```tcl
section Elastic <tag> <E> <A> <Iz> <Iy> <G> <J> <Cx> <Cy>  # torsion=<selected_key>
```

### What `J` means in the CSF export

CSF may compute multiple torsion candidates at each station (different modeling paths), for example:
- `J_sv_cell` : closed thin-walled cell (Bredt–Batho / midline)
- `J_sv_wall` : open thin-walled wall
- `J_sv`      : general Saint-Venant torsion estimate (fallback)

OpenSees cannot store multiple torsion models in `section Elastic`, so **the exporter must select exactly one value** per station.

### Export selection policy (current)

Per station:

1) If any thin-walled torsion candidate is available, export:

- `J_eff = max(J_sv_cell, J_sv_wall)`

and record the selected key as:

- `# torsion=J_sv_cell` or `# torsion=J_sv_wall`

2) If both thin-walled candidates are missing or non-positive, export:

- `J_eff = J_sv`

and record:

- `# torsion=J_sv`

3) If no torsion candidate is available, the export fails fast (`ERROR`).

This keeps the file self-describing: the `J` value is always accompanied by the exact CSF key used to produce it.

---

## 7) End-to-end workflow

1) Generate `geometry.tcl` from CSF including:
- `# CSF_Z_STATIONS: ...`
- `section Elastic ... J xc yc` for each station.

2) Run the builder (OpenSeesPy or Tcl builder):
- choose `MATERIAL_INPUT_MODE` according to your export contract,
- keep `INTEGRATION_MODE="auto"` unless you want to force a strategy.

---

## 8) Practical checklist

- If you want strict station placement, ensure `CSF_Z_STATIONS` exists and its length equals the number of `section Elastic` lines.
- If you use `rigidLink`, use `constraints Transformation`.
- For strict member-level Lobatto:
  - `CSF_Z_STATIONS` must match Lobatto abscissae for `N` stations (within tolerance),
  - centroid offsets must be constant.
- Keep units consistent across geometry, forces, and `E, G`.

---

## Quick reference (what is used in OpenSees)

- Element formulation: `forceBeamColumn`
- Variable centroid mapping: `rigidLink beam` (ref axis → centroid axis)
- Station placement: `CSF_Z_STATIONS` (Gauss–Lobatto) when provided
- Integration:
  - **AUTO**: single-element strict Lobatto if no centroid variation; otherwise segmented endpoint Lobatto-2
- Constraints handler: `Transformation`
  
# geometry file description

## `geometry.tcl` (CSF export) — detailed, block-by-block explanation

This file is **not meant to be sourced** as a complete OpenSees model.  
It is a **CSF data file**: it contains *station-by-station section properties* plus the **centroid offsets** needed by external builders to reconstruct a centroid axis.

The file is created by:

```python
write_opensees_geometry(section_field, n_points=10, filename=geometryfile)
```

Example (excerpt):

```tcl
# OpenSees Geometry DATA File - Generated by CSF
# Beam Span: 10.000000 (units follow your model)
# Stations: 10
# NOTE: This file is meant to be PARSED AS DATA (do NOT source it as Tcl).
# NOTE: Section lines append 'Cx Cy' as CSF-only fields (not OpenSees syntax).
#
# CSF_EXPORT_MODE: E=E_ref ; A/I/J are station-wise CSF results (already weighted)
# CSF_TORSION_SELECTION: J_eff = max(J_sv_cell, J_sv_wall) if any >0 else J_sv if >0 else ERROR
#
# CSF_Z_STATIONS: 0 ... 10

# Informational nodes (best-fit line through centroid offsets)
node 1 ...
node 2 ...

geomTransf Linear 1 1 0 0

section Elastic 1 ...  # torsion=J_sv
...
section Elastic 10 ... # torsion=J_sv
```

---

## 1) Header block (human hints + export contract)

```tcl
# OpenSees Geometry DATA File - Generated by CSF
# Beam Span: 10.000000 (units follow your model)
# Stations: 10
# NOTE: This file is meant to be PARSED AS DATA (do NOT source it as Tcl).
# NOTE: Section lines append 'Cx Cy' as CSF-only fields (not OpenSees syntax).
#
# CSF_EXPORT_MODE: E=E_ref ; A/I/J are station-wise CSF results (already weighted)
# CSF_TORSION_SELECTION: J_eff = max(J_sv_cell, J_sv_wall) if any >0 else J_sv if >0 else ERROR
```

- Pure comments (`# ...`).
- They communicate:
  - the beam span `L`,
  - the number of stations `N`,
  - that the file must be **parsed**, not **sourced**,
  - the **export contract** used by CSF, including the torsion selection policy.

**Critical clarification:**  
The `section Elastic ...` lines include **two extra fields at the far right**:
- `Cx Cy` = centroid offsets at that station, **CSF-only**, not OpenSees syntax.  
An external builder must parse them explicitly if eccentricity preservation is required.

---

## 2) CSF station coordinates block (for exact station placement)

```tcl
# CSF_Z_STATIONS: z0 z1 ... zN-1
```

- Comment, but **machine-readable** for an external builder.
- This is the list of **exact z-coordinates** of the exported stations.

If the export uses Gauss–Lobatto stationing, then (conceptually):

```text
z0 = 0
zN-1 = L
(interior stations are non-uniform and clustered near the ends)
```

**Why it matters:**  
Station locking makes the export deterministic. Recomputing stations differently changes the model.

---

## 3) Informational nodes (optional; not used for precision)

```tcl
node 1 x0 y0 z0
node 2 x1 y1 z1
```

These nodes are optional and **informational**:
- they may encode a reference axis or legacy data,
- they are kept for human readability or older scripts.

A robust builder should not rely on these lines to reconstruct station placement.  
Instead it should use:
- `CSF_Z_STATIONS` for station positions, and
- per-station `Cx Cy` for a centroid axis (if eccentricity preservation is required).

---

## 4) Local orientation (`geomTransf`)

```tcl
geomTransf Linear 1 vx vy vz
```

- Defines the geometric transformation tag `1`.
- `vx vy vz` is the “vecxz” vector used to orient local axes about the member axis.
- A builder can reuse this orientation to keep bending directions consistent.

---

## 5) Section station lines (the core data)

General format:

```tcl
section Elastic <secTag> <E> <A> <Iz> <Iy> <G> <J> <Cx> <Cy>  # torsion=<selected_key>
```

### Field meaning (exact)

- `section Elastic`  
  OpenSees elastic section definition.

- `<secTag>`  
  Unique section id for this station (typically `1..N`).

- `<E>`, `<G>`  
  Moduli written by the exporter. Their meaning depends on the export contract:
  - physical moduli (direct stiffness), or
  - reference moduli `E_ref, G_ref` (with modular properties).

- `<A>`  
  Area at station (units: `L^2`). In CSF export mode it may already be weighted/modular.

- `<Iz>`, `<Iy>`  
  Second moments at station (units: `L^4`), possibly already weighted/modular.

- `<J>`  
  Torsion constant used by OpenSees (torsional stiffness `G*J`).  
  In CSF export, this `J` slot receives a **single selected torsion constant** per station according to the header policy:
  - prefer thin-walled candidates via `max(J_sv_cell, J_sv_wall)` when available,
  - else fallback to `J_sv`,
  - else `ERROR`.
  The selected CSF key is written in the trailing comment `# torsion=<selected_key>`.

- `<Cx> <Cy>` (**CSF-only extension fields**)  
  Centroid offsets at the station (units: `L`).  
  These are appended at the far right and are **not** OpenSees syntax.  
  They are intended for a builder to place centroid-axis nodes.

### Interpretation

Each station line is a snapshot at `z_i`:
- stiffness properties sampled at `z_i`,
- centroid offsets sampled at `z_i`,
- one torsion constant selected for OpenSees.

The member can be described by the list:

```text
{ z_i, A_i, Iz_i, Iy_i, J_i, Cx_i, Cy_i }
```

---

## 6) Template-only OpenSees commands (commented out)

```tcl
# TEMPLATE ONLY ...
# beamIntegration ...
# element forceBeamColumn ...
```

- These are comments for humans only.
- A robust builder typically does not rely on these lines, because the builder must decide how to map:
  - the exported station set, and
  - the station-wise sections,
to the final OpenSees element/integration commands.

---

## 7) What an external builder typically does with this file (minimal contract)

A robust CSF → OpenSees builder typically:

1) If strict station placement is required: read `CSF_Z_STATIONS`  
   - enforce `N = (# stations) = (# section lines)`.

2) Read each `section Elastic ...` line  
   - extract `E, A, Iz, Iy, G, J` **and** the extra fields `Cx Cy`
   - optionally read `# torsion=<selected_key>` for traceability.

3) If eccentricity preservation is required: build
   - a **reference axis** (clean line for BCs/loads),
   - a **centroid axis** using `Cx Cy` at the exported stations,
   - a kinematic bridge (e.g. `rigidLink beam`) from reference to centroid nodes.

4) Choose an integration mapping, for example:
   - single element with `N`-point Gauss–Lobatto (only if `Cx,Cy` are constant and stations match Lobatto), or
   - segmented elements with 2-point endpoint sampling (if `Cx,Cy` vary and intermediate nodes are needed).
  
 OpenSees Geometry DATA File - Generated by CSF

 ```
# Beam Span: 10.000000 (units follow your model)
# Stations: 10
# NOTE: This file is meant to be PARSED AS DATA (do NOT source it as Tcl).
# NOTE: Section lines append 'Cx Cy' as CSF-only fields (not OpenSees syntax).
#
# CSF_EXPORT_MODE: E=E_ref ; A/I/J are station-wise CSF results (already weighted)
# CSF_TORSION_SELECTION: J_eff = max(J_sv_cell, J_sv_wall) if any >0 else J_sv if >0 else ERROR

# CSF_Z_STATIONS: 0 0.402330459168 1.30613067447 2.61037525095 4.17360521167 5.82639478833 7.38962474905 8.69386932553 9.59766954083 10

# Informational nodes (best-fit line through centroid offsets)
node 1 0 1.35332593178e-17 0
node 2 0 0.25 10

geomTransf Linear 1 1 0 0

section Elastic 1 1.000000e+00 3.600000e-01 4.320000e-02 2.700000e-03 5.000000e-01 4.590000e-02 0.000000e+00 0.000000e+00  # torsion=J_sv
section Elastic 2 1.000000e+00 3.539650e-01 4.106363e-02 2.654738e-03 5.000000e-01 4.371837e-02 0.000000e+00 1.005826e-02  # torsion=J_sv
section Elastic 3 1.000000e+00 3.404080e-01 3.652378e-02 2.553060e-03 5.000000e-01 3.907684e-02 0.000000e+00 3.265327e-02  # torsion=J_sv
section Elastic 4 1.000000e+00 3.208444e-01 3.058155e-02 2.406333e-03 5.000000e-01 3.298788e-02 0.000000e+00 6.525938e-02  # torsion=J_sv
section Elastic 5 1.000000e+00 2.973959e-01 2.435462e-02 2.230469e-03 5.000000e-01 2.658508e-02 0.000000e+00 1.043401e-01  # torsion=J_sv
section Elastic 6 1.000000e+00 2.726041e-01 1.875743e-02 2.044531e-03 5.000000e-01 2.080196e-02 0.000000e+00 1.456599e-01  # torsion=J_sv
section Elastic 7 1.000000e+00 2.491556e-01 1.432149e-02 1.868667e-03 5.000000e-01 1.619016e-02 0.000000e+00 1.847406e-01  # torsion=J_sv
section Elastic 8 1.000000e+00 2.295920e-01 1.120589e-02 1.721940e-03 5.000000e-01 1.292783e-02 0.000000e+00 2.173467e-01  # torsion=J_sv
section Elastic 9 1.000000e+00 2.160350e-01 9.335731e-03 1.620262e-03 5.000000e-01 1.095599e-02 0.000000e+00 2.399417e-01  # torsion=J_sv
section Elastic 10 1.000000e+00 2.100000e-01 8.575000e-03 1.575000e-03 5.000000e-01 1.015000e-02 0.000000e+00 2.500000e-01  # torsion=J_sv

```

