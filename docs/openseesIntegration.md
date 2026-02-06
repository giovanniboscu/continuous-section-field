## OpenSees Integration

CSF bridges continuous geometric modeling and structural analysis by exporting **station-wise section data** and building a consistent OpenSees beam model.

### 1. Force-Based Formulation

CSF uses the `forceBeamColumn` element (force-based beam-column).  
This formulation is well-suited to members with longitudinally varying stiffness because it performs **numerical integration of section response** along the element axis.

**Important:** a “single element” representation is valid only when the **centroid offsets are constant** along the member. If centroid offsets vary, intermediate nodes are required (see §4).

### 2. Longitudinal Sampling (Gauss–Lobatto)

The longitudinal variation is handled by exporting a deterministic set of stations:

- **Point distribution:** section properties are sampled at **Gauss–Lobatto stations** (endpoints included), exported explicitly as:
  - `# CSF_Z_STATIONS: z0 z1 ... zN-1`
- **Property mapping:** each station is assigned one `section Elastic` record (unique tag).  
  The OpenSees builder maps these station sections into the element integration using `beamIntegration UserDefined`:
  - **Member-level strict Lobatto (N points):** only if exported stations match Lobatto abscissae and centroid offsets are constant.
  - **Segmented (N−1 elements, 2-point endpoints):** used when centroid offsets vary, to avoid inventing intermediate sections.

This ensures the OpenSees model uses **only exported sections**, with no interpolation.

### 3. Torsional Rigidity (J)

A torsional constant `J` is required for 3D frame stability (torsional stiffness `GJ`) to prevent singular stiffness matrices.

- **Current behavior:** CSF exports a station-wise torsion scalar `J` selected from available CSF torsion results (e.g. wall/cell/legacy depending on availability).
- **Scope:** the value provides numerical stability and a consistent torsional stiffness input; its physical fidelity depends on the torsion model used (wall/cell/legacy) and the section topology.

### 4. Centroidal Axis Alignment

If the section varies asymmetrically, the centroid \((x_c(z), y_c(z))\) may vary along the member.

- **Data source:** `xc yc` are exported per station as **CSF-only fields** appended to each `section Elastic` line.
- **Modeling strategy:** the builder constructs:
  - a **reference axis** (for BCs/loads),
  - a **centroid axis** (station nodes placed using `xc yc`),
  - a station-wise kinematic bridge (e.g. `rigidLink beam`) between the two axes.

**Note:** a simple linear regression using only end nodes is informational/legacy; it is not sufficient when \((x_c,y_c)\) varies nonlinearly.

---

### Implementation Overview

- **Language:** Python (`openseespy`) or Tcl builder.
- **Element type:** `forceBeamColumn`.
- **Stations:** `CSF_Z_STATIONS` (Gauss–Lobatto if chosen).
- **Integration mapping:** `beamIntegration UserDefined`
  - member-level strict Lobatto (N points) or segmented endpoint sampling (2 points/segment).
- **Geometry:** topology-agnostic (any number of stations; no invented sections).
