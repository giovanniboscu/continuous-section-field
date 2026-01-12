# write_opensees_builder_tcl.py

## What it is
`write_opensees_builder_tcl.py` is a **Python generator** that writes a **standalone OpenSees Tcl script** (typically `csf_member_builder.tcl`).

The generated Tcl script:
- reads `geometry.tcl` as a **data file** (opened and parsed line-by-line; it is **not sourced**),
- extracts CSF stations, section properties, centroid offsets, and optional orientation,
- builds a 3D beam model with **reference axis + centroid axis** linked by **rigidLink beam**,
- creates `forceBeamColumn` elements and a user-defined beam integration rule,
- runs a simple cantilever test and prints tip displacement.

This tool exists to reproduce CSF station stiffness sampling in “pure OpenSees Tcl” without requiring external Python dependencies.

---

## Inputs and file contract
The generated Tcl expects a CSF-style `geometry.tcl` containing:

1. **Exact station coordinates (strongly required)**
   ```tcl
   # CSF_Z_STATIONS: z0 z1 ... zN-1
   ```
   - Used to place nodes exactly at CSF stations.
   - Must contain `N` values.

2. **Station sections (required)**
   ```tcl
   section Elastic tag E A Iz Iy G J [xc yc]
   ```
   - Must appear exactly `N` times.
   - Optional `(xc,yc)` offsets are supported.

3. **Orientation vector (optional)**
   ```tcl
   geomTransf Linear 1 vx vy vz
   ```
   - If present, it is reused; otherwise a default is used.

4. **Beam length header (optional)**
   - Used only if `CSF_Z_STATIONS` is missing (but strict mode prefers the station list).

---

## How the generated Tcl works

### 1) Parsing stage (no `source`)
The Tcl script opens `geometry.tcl` and parses:
- beam length from commented header (optional)
- the `CSF_Z_STATIONS` list (required for strict placement)
- `geomTransf Linear` orientation vector (optional)
- all `section Elastic ...` lines (required)

It stores station-aligned arrays:
- `zStations`, `secTags`, `secA`, `secIz`, `secIy`, `secJ`, `secXc`, `secYc`, and optionally `secE`, `secG`.

### 2) Model topology
The Tcl script creates two node lines per station:
- REF node at `(0,0,z)`
- CEN node at `(xc,yc,z)`

Then couples them:
```tcl
rigidLink beam $refNode $cenNode
```

Elements are created on the centroid axis:
```tcl
element forceBeamColumn $eleTag $cen_i $cen_{i+1} $transfTag $intTag
```

### 3) Material handling (E/G)
The Tcl supports:
- `MATERIAL_MODE = override` → uses constant `E_REF` and `G_REF` for all sections
- `MATERIAL_MODE = from_file` → uses `E` and `G` read from each `section Elastic` line

In both cases, `A`, `Iz`, `Iy`, `J` are taken from the file.

---

## Beam integration behavior
The generated Tcl uses `beamIntegration UserDefined`.

### What “Gauss–Lobatto” means here
- The script can define Gauss–Lobatto **locations and weights on [0,1]** for `N_INT_PTS` in `{2,3,4,5}`.
- However, you required that **section tags must come from `geometry.tcl`** (no interpolation, no synthetic sections).

Therefore, for each element segment `(station i -> station i+1)`, the Tcl:
1. computes Lobatto locations `locs` and weights `wts`,
2. maps each Lobatto location inside the segment to a **station section tag** taken from `secTags`.

In the “file-only sections” variant, this mapping is effectively a **quantization** step:
- internal Lobatto points may be assigned the same station tag as an endpoint if no other station exists inside the segment.

This is a fundamental limitation when you discretize by station-to-station elements and forbid interpolation.

---

## Cantilever verification
The Tcl script then:
- fixes the base REF node (all 6 DOFs)
- applies a tip force `FY_TIP` at the tip REF node (global Y)
- runs one static step
- prints the absolute tip displacement (scaled by `DISP_SCALE` for display)

---

## Limitations and usage constraints (high priority)

### 1) “True member-level Lobatto” is not produced by default
Because the Tcl builder creates **one element per segment**, you cannot obtain a true N-point Lobatto integration over the **entire member** unless you:
- create a **single element** over the full length, and
- pass all station sections as integration points of that single element.

The segment-based strategy is excellent for sampling endpoint stiffness exactly, but it is not the same as global Lobatto integration.

### 2) Internal Lobatto points may collapse to endpoints
With station-to-station elements, there are no additional file-defined sections inside each span.
Therefore:
- if `N_INT_PTS > 2`, internal points often map to the same section tag as endpoints.
- this reduces the effective integration order back toward endpoint sampling.

### 3) Centroid offsets and “tilt”
If `xc,yc` vary, the centroid axis is geometrically non-straight.
The Tcl builder represents this using station nodes and rigid links (good), but:
- using a **single element** would not reproduce station-wise centroid curvature.

### 4) Only `section Elastic` is supported
No fiber sections, no nonlinear materials, no distributed plasticity definitions beyond elastic beam-column.

### 5) Rigid links impose MPC constraints
Models with rigidLink require:
- `constraints Transformation`
(or an equivalent MPC-capable constraint handler). Changing it can break the solution.

### 6) Station list mismatch is a hard error
If the number of `CSF_Z_STATIONS` entries does not match the number of `section Elastic` lines, the builder aborts.

### 7) Torsion handling depends on file quality
If `J` is a placeholder or inconsistent across stations, torsional response is not reliable.

---

## When to use it
Use `write_opensees_builder_tcl.py` when you want:
- a **portable** OpenSees Tcl script to reproduce CSF station stiffness sampling,
- a quick “FE vs theory” or “FE vs OpenSeesPy” check,
- a workflow that does not depend on OpenSeesPy.

---

## Recommended practices
- Always export `# CSF_Z_STATIONS` from CSF.
- Keep section tags unique and ordered.
- Decide upfront whether your CSF export is “modular/weighted properties” (use `override`) or “physical E(z),G(z)” (use `from_file`).
- If you need true global Lobatto integration with station sections, prefer a **single element** formulation (and accept the centroid-axis limitation if tilt exists).
