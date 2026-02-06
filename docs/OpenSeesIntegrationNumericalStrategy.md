# CSF → OpenSees Integration and Numerical Strategy (`csfopenseescon`)

This document explains how **CSF (Continuous Section Field)** exports a continuously varying member and how that data is consumed to build a consistent **OpenSees `forceBeamColumn` model** (OpenSeesPy or OpenSees Tcl).

The focus is the **numerical integration strategy**: what is sampled, where it is sampled, and how those samples are mapped into OpenSees **without inventing extra sections**.

---

## 0) What CSF is (and what it is not)

CSF is **not** a finite element solver.  
CSF is a **geometric + constitutive engine** that provides a *continuous* description of a single non-prismatic member:

- ruled-surface interpolation of section geometry between end stations,
- continuous evaluation of sectional properties \(A(z), I(z), C(z)\),
- optional longitudinal material/weight laws \(w(z)\) (including void logic in the CSF model).

OpenSees performs the structural solution; CSF provides the **station-wise data** that OpenSees needs.

---

## 1) The central idea: continuous field → quadrature stations

OpenSees integrates section behavior numerically along the element axis, so a continuously varying member must be **sampled**.

CSF exports a set of **stations** along the axis:

- station coordinates: **Gauss–Lobatto points** (including both endpoints),
- at each station \(i\):
  - section properties are evaluated from the continuous field,
  - centroid offsets \((x_c, y_c)\) are stored.

This is **not** user-chosen “piecewise-prismatic stepping”. It is:

> **quadrature stationing** of a continuous stiffness field at Gauss–Lobatto abscissae (with endpoint sampling by construction).

---

## 2) The exported file: `geometry.tcl` is a DATA FILE

The CSF export `geometry.tcl` is intentionally a **data container**.

It is **not** a full OpenSees model to be run directly.  
A builder script reads it line-by-line and constructs nodes, constraints, elements, integration commands, loads, and BCs.

### 2.1 Required blocks in `geometry.tcl`

Typical export contains:

1) Header (human hints only)
```tcl
# Beam Span: 10.000000 (units follow your model)
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

For station \(i\) at position `CSF_Z_STATIONS[i]`, the exported line:

```tcl
section Elastic i  E  A  Iz  Iy  G  J  xc  yc
```

means:

- \(A, I_z, I_y, J\) are **evaluated at that station** by CSF (already including CSF weights according to the chosen export contract).
- \((x_c, y_c)\) are **centroid offsets** in the local section plane (used to build a centroid axis).
- The interpretation of \(E, G\) depends on the chosen export convention (next section).

**Note:** `xc yc` are **not** OpenSees syntax. They are extra fields intended for the builder.

---

## 3) Material conventions: `E=E_ref` vs `E=E_real`

OpenSees is unitless; “real” displacements require consistent stiffness units.

CSF supports two workflows.

### 3.1 Mode A — export physical moduli (direct stiffness)

- `geometry.tcl` stores the physical \(E(z)\) and \(G(z)\).
- The builder uses `MATERIAL_INPUT_MODE = "from_file"`.

Result: OpenSees uses \(E,G\) exactly as written in the file.

### 3.2 Mode B — export reference modulus and “modular properties”

In this contract:

- `geometry.tcl` stores a convenient constant \(E_\text{ref}\) (and compatible \(G_\text{ref}\)),
- the effects of weights / multi-material / void logic are embedded into the exported section properties \(\{A, I_z, I_y, J\}\).

A typical header states this explicitly, e.g.
```tcl
# CSF_EXPORT_MODE: E=E_ref ; A/I/J are station-wise CSF results (already weighted)
```

If you want “real” displacements, the builder should typically use:

- `MATERIAL_INPUT_MODE = "override"` and provide physical \(E_\text{real}\) (and \(G_\text{real}\)).

---

## 4) Variable centroid (“tilt”) handling

CSF can export centroid offsets that vary with \(z\): \((x_c(z), y_c(z))\).

OpenSees frame elements define their axis between element nodes. If you only define the two end nodes, you cannot represent a centroid axis that changes along the member.

### 4.1 Strategy used by the builder: reference axis + centroid axis

The builder creates two node chains:

1) **Reference axis nodes**  
A clean straight line used for BCs and loads.

2) **Centroid axis nodes**  
At each station:
$$
\mathbf{x}_\text{cen}(z_i) \;=\; \mathbf{x}_\text{ref}(z_i) + x_c(z_i)\,\mathbf{e}_1 + y_c(z_i)\,\mathbf{e}_2
$$

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

CSF exports **Gauss–Lobatto stations**. The OpenSees model must honor them **without inventing intermediate sections**.

### 5.1 Two valid mappings (depending on centroid behavior)

There are two consistent strategies, depending on whether \((x_c,y_c)\) are constant.

#### Strategy A — Single element with N-point Gauss–Lobatto (strict)

Allowed only if centroid offsets are constant along the member:
$$
x_c(z) = \text{const},\qquad y_c(z) = \text{const}.
$$

Then the builder can use:

- **one** `forceBeamColumn` element over the full span,
- `beamIntegration UserDefined` with:
  - \(N\) stations,
  - **Gauss–Lobatto locations** \(s_i\in[0,1]\),
  - **Gauss–Lobatto weights** \(w_i\).

Station matching requirement (strict): the exported `CSF_Z_STATIONS` must match the Lobatto abscissae mapped to \([0,1]\):
$$
s_i \;=\; \frac{z_i - z_0}{z_{N-1} - z_0}
$$

and the builder enforces:

$$
\max_i \left| s_i - s_i^{\text{Lobatto}} \right| < \varepsilon
$$


If it does not match, this strategy is rejected (no fallback weights).

#### Strategy B — Segmented elements with 2-point endpoint sampling (Lobatto-2)

Required when centroid offsets vary (tilt/curvature), because you need nodes at intermediate stations to represent the centroid axis.

- Build **one element per station-to-station segment** (\(N\) stations → \(N-1\) elements).
- For each segment \(i\to i+1\), assign:
  - section\(_i\) at \(s=0\),
  - section\(_{i+1}\) at \(s=1\),
  - weights \(w=\{0.5, 0.5\}\) (Lobatto-2 / endpoint trapezoid on that segment).

This uses only exported station sections and preserves the station-wise centroid axis.

### 5.2 What the builder actually does (“AUTO”)

The builder runs in `"auto"` mode by default:

- If \((x_c,y_c)\) are **constant** across all stations → **Strategy A** (single element, strict N-point Lobatto).
- If \((x_c,y_c)\) **vary** across stations → **Strategy B** (segmented, 2-point endpoint per segment).

This avoids the problematic case where a single element is used while the centroid axis is actually varying (which would silently discard geometry).

---

## 6) Torsion input \(J\)

In OpenSees `section Elastic`, the last scalar is the torsional constant used for torsional stiffness:
$$
GJ
$$
in the element formulation.

CSF exports a station-wise torsion scalar \(J\) in the section lines. The value may come from different CSF torsion paths (e.g. wall/cell/legacy), but **OpenSees only sees one scalar** per station.

The model uses that station-wise \(J\) to avoid torsional singularity and to represent torsional stiffness consistently with the chosen CSF torsion model.

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

- Ensure `CSF_Z_STATIONS` exists and its length equals the number of `section Elastic` lines.
- If you use `rigidLink`, use `constraints Transformation`.
- For strict member-level Lobatto:
  - `CSF_Z_STATIONS` must match Lobatto abscissae for \(N\) stations (within tolerance),
  - centroid offsets must be constant.
- Keep units consistent across geometry, forces, and \(E,G\).

---

## Quick reference (what is used in OpenSees)

- Element formulation: `forceBeamColumn`
- Variable centroid mapping: `rigidLink beam` (ref axis → centroid axis)
- Station placement: `CSF_Z_STATIONS` (Gauss–Lobatto)
- Integration:
  - **AUTO**: single-element strict Lobatto if no centroid variation; otherwise segmented endpoint Lobatto-2
- Constraints handler: `Transformation`
