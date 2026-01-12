# csf_openseespy_builder.py

## What it is
`csf_openseespy_builder.py` is a **single-file OpenSeesPy “checker/builder”** that reads a CSF-exported `geometry.tcl` **as a data file** (it does **not** `source` it), builds an OpenSees model that matches the CSF station sampling, and runs a **simple cantilever verification** (fixed at the base, tip force in global Y).

Its primary purpose is to:
- reproduce the CSF discretization **exactly at the exported stations** (via `# CSF_Z_STATIONS`),
- keep CSF’s **centroid eccentricity** concept (`xc`, `yc`) through a **reference axis + centroid axis** topology,
- provide a **fast sanity check** of stiffness/displacement consistency between CSF-exported properties and OpenSees.

---

## Inputs and file contract
The script expects a CSF-style `geometry.tcl` containing (at minimum):

1. **Station coordinates (mandatory for strict mode)**
   ```tcl
   # CSF_Z_STATIONS: z0 z1 z2 ... zN-1
   ```
   - The script uses these coordinates to place stations precisely.
   - The length of this list must match the number of `section Elastic ...` lines.

2. **Station sections (mandatory)**
   ```tcl
   section Elastic tag E A Iz Iy G J [xc yc]
   ```
   - One section per station.
   - `xc`, `yc` (centroid offsets) are optional but strongly recommended if you want eccentricity/tilt tracking.

3. **Orientation vector (optional but recommended)**
   ```tcl
   geomTransf Linear 1 vx vy vz
   ```
   - Used to define a stable local basis so that `(xc, yc)` offsets can be mapped consistently.

4. **Beam length header (optional)**
   ```tcl
   # Beam Length: 10.000 m | Int. Points: 10
   ```
   - Used only as a fallback if `CSF_Z_STATIONS` is missing.

If `CSF_Z_STATIONS` is missing, the script can optionally generate fallback station coordinates (Gauss–Lobatto or uniform) depending on the configuration flags.

---

## Model topology (how it represents CSF)
The script uses **two parallel axes of nodes** at each station:

- **Reference axis (REF)**: straight member axis; used for applying boundary conditions and loads.
- **Centroid axis (CEN)**: the “real” axis where beam elements are created.

For each station `i`:
- A REF node is created at `(0,0,z_i)` (or along the chosen reference axis).
- A CEN node is created at:
  
  \[\mathbf{x}_{CEN,i} = \mathbf{x}_{REF,i} + x_{c,i}\,\mathbf{e}_1 + y_{c,i}\,\mathbf{e}_2\]

The kinematic link is enforced via:
```python
ops.rigidLink("beam", refTag, cenTag)
```

Because rigid links introduce multi-point constraints, the script uses:
```python
ops.constraints("Transformation")
```

---

## Material input handling (E/G)
The script supports two modes:

### 1) `MATERIAL_INPUT_MODE = "from_file"`
- Uses `E` and `G` exactly as stored in each `section Elastic` line.
- Suitable when `geometry.tcl` already contains **physical** moduli (possibly varying with `z`).

### 2) `MATERIAL_INPUT_MODE = "override"`
- Ignores `E` and `G` in the file and forces constant `E_OVERRIDE` and `G_OVERRIDE` (or computed from `NU_OVERRIDE`).
- This is useful when CSF exports **modular/weighted section properties** and you want the physical stiffness via a single reference modulus.

**Important limitation:** you must avoid *double counting stiffness*. If CSF already “baked” material variation into the exported section properties (A/I/J weighted), then applying varying `E(z)` again is usually wrong.

---

## Integration strategy (key behavior)
The script’s job is to connect CSF station data to OpenSees beam integration. Since you required “**use only section tags from geometry.tcl**” (no interpolation), the integration strategy is constrained.

It supports three modes:

### A) `INTEGRATION_MODE = "auto"`
- If **tilt is NOT detected** (centroid offsets constant): use **member-level** integration (single element + N points).
- If **tilt IS detected** (centroid offsets vary): use **segmented** integration (many elements + endpoint integration per segment).

### B) `INTEGRATION_MODE = "member_lobatto"`
- Force **one single forceBeamColumn element** over the entire member.
- Use **N integration points**, where `N = number of stations`, and section tags are exactly those from `geometry.tcl`.

Weights/locations:
- The script compares normalized station coordinates `s_i = (z_i - z0)/(zL - z0)` with theoretical Gauss–Lobatto nodes.
- If they match (within tolerance), it uses **Gauss–Lobatto weights**.
- Otherwise, it uses **trapezoid-rule weights** on the provided station abscissae as a robust fallback.

### C) `INTEGRATION_MODE = "segment_endpoints"`
- Build one element per segment `(station i -> i+1)`.
- Use **2-point endpoint sampling** per element:
  - section `i` at `loc=0`
  - section `i+1` at `loc=1`
  - weights `(0.5, 0.5)`

This is a valid “station-collocation” approach and works well when your goal is to force OpenSees to sample the stiffness exactly at the stations.

---

## What “tilt detected” means
In practice, “tilt” means: **the centroid axis is not a straight line parallel to the reference axis**.

The script flags tilt when centroid offsets vary beyond a tolerance:
- `xc(z)` not constant, or
- `yc(z)` not constant.

A typical reason is having a nonzero `yc` at some station(s), e.g. last station `yc = -0.020`.

**Why tilt matters:** a single element cannot represent a centroid axis that changes station-by-station unless you discretize the geometry (i.e., create intermediate nodes). That’s why `auto` switches away from member-level integration when tilt is detected.

---

## Analysis performed
The script runs a minimal static analysis:
- fix all DOFs at base REF node
- apply a point load `FY_TIP` at tip REF node (global Y)
- solve one load step using a linear algorithm

It prints the absolute tip displacement (scaled for display).

---

## Limitations and “gotchas” (important)

### 1) File-only sections => no internal interpolation
The script **does not create new sections** between stations.
- In **segmented mode**, each element span contains only endpoint stations, so 2-point integration is natural.
- If you demand “true Lobatto with internal points inside each segment”, you would need sections at those internal points (or interpolation), which is intentionally not done.

### 2) Member-level (single element) requires near-constant centroid offsets
If `xc,yc` vary, a single element cannot represent the changing centroid axis.
- You can force it (`member_lobatto`) but then centroid variation is effectively ignored (or simplified to endpoints).

### 3) Nonuniform station spacing
If `CSF_Z_STATIONS` are not exact Gauss–Lobatto nodes, using Lobatto weights is not strictly correct.
- The script detects this and uses trapezoid weights as a fallback.

### 4) Only linear-elastic sections
The script reads `section Elastic ...` only.
- It does not build fiber sections, plasticity, shear nonlinearities, etc.

### 5) Rigid links require Transformation constraints
If you change constraint handling to `Plain`, the model may fail or behave incorrectly.

### 6) Torsion handling depends on what the file provides
If `J` in the file is a placeholder or inconsistent, torsional effects are not trustworthy.

### 7) This is a “checker”, not a full analysis pipeline
- Single load case.
- Single static step.
- Minimal solver setup.

---

## Practical guidance
- If you want **maximum fidelity to CSF station sampling** for a straight centroid axis: use `member_lobatto`.
- If you have a varying centroid axis (tilt): use `auto` (it will segment automatically) or force `segment_endpoints`.
- Always keep `CSF_Z_STATIONS` aligned with the number of `section Elastic` lines.
