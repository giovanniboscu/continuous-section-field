# CSF – Section Full Analysis Output

This document explains **all quantities reported by the CSF _Section Full Analysis_**.

It is intended as a **clear, engineering-oriented reference** for users who want to:
- understand what each value represents,
- know how it is computed in CSF,
- understand **the validity domain and limitations** of each quantity.

Whenever a quantity depends on **a specific modelling choice or policy** defined elsewhere (e.g. torsion selection rules), this is marked with **double asterisks `**`** and explicitly noted.

[CSF sectionproperties mapping table](#csf-sectionproperties-mapping-table)


---

## General Notes

- All quantities are computed **purely from geometry and polygon weights**.
- No assumptions are made about profile families (I, H, box, tube, etc.).
- Polygon `weight` is treated as a **scalar field multiplier** (e.g. modular ratio, material factor).

---

## 1. Area (A)

**Key:** `A`

**Definition**  
Total **cross-sectional area**, including the effect of polygon weights.

Plain-text formula:

A = sum( w_i * A_i )

where:
- A_i = signed area of polygon i
- w_i = polygon weight

**Notes**
- Can be reduced or increased by weighted sub-domains.
- Must be non-zero for a valid section.

---

## 2. Centroid Cx

**Key:** `Cx`

Horizontal coordinate of the **geometric centroid**.

Plain-text formula:

Cx = sum( w_i * A_i * x_i ) / sum( w_i * A_i )

---

## 3. Centroid Cy

**Key:** `Cy`

Vertical coordinate of the **geometric centroid**.

Plain-text formula:

Cy = sum( w_i * A_i * y_i ) / sum( w_i * A_i )

---

## 4. Inertia Ix

**Key:** `Ix`

Second moment of area about the **centroidal X-axis**.

Computed using Green’s theorem with parallel-axis correction.

---

## 5. Inertia Iy

**Key:** `Iy`

Second moment of area about the **centroidal Y-axis**.

---

## 6. Inertia Ixy

**Key:** `Ixy`

Product of inertia about centroidal axes.

**Notes**
- Zero value indicates symmetry with respect to X or Y axes.

---

## 7. Polar Moment (Ip)

**Key:** `Ip`

Polar second moment of area:

Ip = Ix + Iy

**Notes**
- Purely geometric.
- **Not** a torsional stiffness for non-circular sections.

---

## 8. Principal Inertia I1

**Key:** `I1`

Major principal second moment of area.

---

## 9. Principal Inertia I2

**Key:** `I2`

Minor principal second moment of area.

---

## 10. Radius of Gyration rx

**Key:** `rx`

Plain-text formula:

rx = sqrt( Ix / A )

Represents the distribution of area relative to the X-axis.

---

## 11. Radius of Gyration ry

**Key:** `ry`

Plain-text formula:

ry = sqrt( Iy / A )

---

## 12. Elastic Section Modulus Wx

**Key:** `Wx`

Elastic section modulus for bending about the **X-axis**.

Plain-text formula:

Wx = Ix / c_y,max

where c_y,max is the maximum distance from the centroid to the extreme fibers.

---

## 13. Elastic Section Modulus Wy

**Key:** `Wy`

Elastic section modulus for bending about the **Y-axis**.

Plain-text formula:

Wy = Iy / c_x,max

---

## 14. Torsional Rigidity K

**Key:** `K_torsion`

Semi-empirical torsional stiffness approximation.

Plain-text formula:

K ≈ A^4 / (40 * Ip)

where Ip = Ix + Iy.

**Notes**
- Always defined.
- Low physical fidelity.

---

## 15. First Moment of Area `Q_na`

**Key:** `Q_na`

First moment of area of the **portion of the section located on one side of the neutral axis** (used in shear stress evaluation).

Let the neutral axis be the centroidal axis `y = 0`. Then:

`Q_na(z) = Σ_i w_i(z) * ∫_{A_i(y > 0)} y dA`

where the integral is taken over the sub-area above the neutral axis  
(the lower portion may equivalently be used in absolute value).

Note:

- Over the **entire section**, `∫_A y dA = 0` for centroidal axes.
- `Q_na` is therefore computed over a **partial area**, not the full section.

Typical use in shear stress estimation:

`tau = V * Q / (I * b)`

where `Q` is the first moment of the sub-area cut by the neutral axis,
evaluated consistently with the same weighted section model.

---
## 16 - 17 Torsion constant methods for tagged polygons (`@cell` / `@wall`)

[Saint-Venant Torsional Constant - CSF Summation Assumptions ](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md)

**Key:** `J_sv_cell`   `J_sv_wall` 

### Thin-walled torsion tags: `@cell` and `@wall`

In CSF, `@cell` and `@wall` are **tags applied to polygon names**.\
They classify specific polygons for dedicated thin-walled torsion
calculations.

-   `@cell` → polygon is treated as a **closed thin-walled cell**
-   `@wall` → polygon is treated as an **open thin-walled wall**

These tags are **not geometric operations**: they do not modify the
shape.\
They only define which polygons are included in the corresponding
torsional path.

Polygons without these tags are **ignored** in `J_sv` computations.

------------------------------------------------------------------------

### Behavior

`J_sv` (both `@cell` and `@wall`) is computed exclusively from the
tagged polygons:

-   only their **midline geometry** and **thickness** are used
-   each tagged polygon is treated as an **independent entity**
-   **no interaction** with other polygons (including
    nesting/composition)

Any additional polygons or inclusions (e.g. rebars, inner shapes):

-   do **not** modify the wall path
-   do **not** contribute to `J_sv`
-   may still contribute to homogenized/global properties (`A`, `Ix`,
    `Iy`, ...)

------------------------------------------------------------------------

### Example

``` yaml
polygons:
  - name: outer_shell@cell
    points: [...]
    t: 0.30

  - name: inner_void
    points: [...]
    w: 0.0

  - name: rebar_row_1
    points: [...]
    w: 7.85

  - name: rebar_row_2
    points: [...]
    w: 7.85
```

Interpretation:

-   `outer_shell@cell` → used to compute `J_sv_cell`
-   `inner_void` → ignored in `J_sv_cell` (even if inside)
-   `rebar_row_*` → ignored in `J_sv_cell`, but included in `A`, `Ix`,
    `Iy`

---

### Key point

`@cell` / `@wall` define **which polygons enter the torsional model**,\
not how the global geometry is composed.


### Torsional contribution of `@cell` and `@wall` polygons

The torsional stiffness is computed as the sum of the contributions of all polygons participating in the torsion path.

This note documents the *implemented* methods used by:

- `compute_saint_venant_J_cell(section)`
- `compute_saint_venant_J_wall(section)`

These routines do **not** solve the general Saint-Venant torsion boundary-value problem (Prandtl stress function / warping).
They compute **model-based** torsion constants under thin-walled assumptions, restricted to **user-selected polygons**.

> **Note:** `@t=` can be defined with different values at `S0` and `S1`.  
> Intermediate sections use **linear interpolation** of `t` along `z`.


![softwarex_props](https://github.com/user-attachments/assets/c4b03d5c-544c-4d18-9821-e05facd651b7)


---

## Common inputs and conventions

### Tagging (polygon selection)

Only polygons whose **name** contains the relevant token are used:

- **Cell method:** name contains `@cell` or `@closed` (case-insensitive)
- **Wall method:** name contains `@wall` (case-insensitive)

All other polygons are **ignored** by these functions.

### Thickness token (`@t=<value>`)

A thickness may be encoded in the polygon name as:

- `...@t=0.010`  (meters)

Parsing rules (both functions):

- Case-insensitive `@t=`
- Parsing stops at the first character that is not one of: `0–9 . + - e E`
- Thickness must be strictly positive (`t > 0`) or it is rejected

---

## Thickness 
### Required parameters (user-specified)



### Important: Thickness Rule for `@cell` and @wall Polygons

The thickness parameter `t` follows the rules below.

### 1. `@cell` without `t`

If no thickness is provided, it is **deduced from geometry**:

`t = 2A / P`

where:

-   `A` = polygonal cell area
-   `P` = total cell perimeter (outer + inner boundaries)

This rule assumes a **thin‑walled closed cell with uniform thickness**.


###  Variation along the member axis

###  `t` provided in both sections

If thickness is specified in **both** sections (`S0` and `S1`), it is **linearly interpolated** along the member axis:

`t(z) = t0 + (t1 - t0) * (z - z0) / (z1 - z0)`

where

- `t0`, `t1` are the thickness values at sections `S0` and `S1`
- `z0`, `z1` are the corresponding axial coordinates

### `t` provided in only one section

If thickness is specified in **only one section**, it is assumed **constant** along the member:

`t(z) = t_provided`

---

### Summary

| Case | Behavior |
|-----|-----|
| `t` not provided in S0 and S1 | `t(z) = 2A(z) / P(z)` |
| `t` provided in both sections | linear interpolation |
| `t` provided in only one section | constant thickness |







## 16. `compute_saint_venant_J_cell(section)`

**Key:** `J_sv_cell`  

## Purpose

Compute a **closed single-cell** torsional constant using a **Bredt–Batho** style formula
for a **thin-walled closed section** with (assumed) **constant thickness**.

This function only uses polygons tagged `@cell` or `@closed`.

If no `@cell` polygons are present, the current implementation returns `0`.

## `@cell` Polygon Encoding Requirements

This note describes the **strict geometric and data-encoding conditions** required by the current CSF closed-cell torsion routine:

- `compute_saint_venant_J_cell(section)`
- Bredt–Batho **single-cell**, **thin-walled**, **constant thickness** (`@t=...`)
- A closed cell is represented as **two loops encoded inside one polygon** (the “slit” encoding).

---
## Required naming and parameters

### Tag to activate the closed-cell path
The polygon **must** be tagged in its name:

- `@cell`  (preferred)

Example:

```yaml
poly@cell@t=0.5
```

---

## Required vertex encoding: **two closed loops in one `vertices` list**

A single `@cell` polygon encodes **two loops** concatenated into one `vertices` array.

### Exactly two loops
The routine expects **exactly two** closed loops:

- one outer boundary
- one inner boundary

(“Multiple holes” inside the same `@cell` polygon are **not** supported by this routine.)

---

##  Orientation conventions

For consistency with CSF conventions, use:

- **Outer loop:** counter-clockwise (**CCW**)
- **Inner loop:** clockwise (**CW**)

This is an **input convention**. The routine may internally normalize orientation for midline construction, but you should keep the encoding consistent to avoid confusion and reduce failure modes.

---
## Minimal YAML examples

```yaml

CSF:
  sections:
    S0:
      z: 0.000000
      polygons:
        box1@cell: #or  box1@cell@t=1
          weight: 1.000000
          vertices:
            # OUTER loop (CCW)
            - [0.0, 0.0]
            - [10.0, 0.0]
            - [10.0, 6.0]
            - [0.0, 6.0]
            - [0.0, 0.0]
            # bridge to inner start
            - [1.0, 1.0]
            # INNER loop (CW)
            - [1.0, 5.0]
            - [9.0, 5.0]
            - [9.0, 1.0]
            - [1.0, 1.0]

    S1:
      z: 10.000000
      polygons:
        box1@cell:#or  box1@cell@t=1
          weight: 1.000000
          vertices:
            # OUTER loop (CCW)
            - [0.0, 0.0]
            - [10.0, 0.0]
            - [10.0, 6.0]
            - [0.0, 6.0]
            - [0.0, 0.0]
            # bridge to inner start
            - [1.0, 1.0]
            # INNER loop (CW)
            - [1.0, 5.0]
            - [9.0, 5.0]
            - [9.0, 1.0]
            - [1.0, 1.0]


```



Notes:

- The example follows the input orientation convention: inner CW, outer CCW.
- Use the same encoding for `S1` and any other station.

---

## Practical guidance

Use `@cell ... @t=` when you have a **closed thin-walled** single-cell representation and you can provide a reliable wall thickness.

##  Practical checklist

A `@cell` polygon is valid for v2 if all items below are true:


1. Name includes `@cell` (or `@closed`).
2. Name includes `@t=<t>` with $t > 0$.
3. `vertices` contains **two** loops.
4. Outer encloses inner and has **larger area magnitude**.

---

## 17 compute_saint_venant_J_wall
**Key:** `J_sv_wall`

## Purpose

Compute a torsional constant for **open thin-walled** components, using polygons tagged `@wall`.

This is an **open-section thin-walled approximation** applied per selected polygon,
with an optional thickness override.

If no `@wall` polygons are present, the current implementation returns `0`.

## Parameters: optional vs required

### Required

- `section` with at least one polygon tagged `@wall`

### Optional (per wall polygon)

- `@t=<value>` thickness override (meters)

If `@t=` is absent, thickness is estimated from geometry (see below).


## Assumptions and limitations

- Intended for **open thin-walled** components represented as wall polygons.
- Thickness may be **user-specified** (`@t=`) or **estimated** (`t = 2A/P`).
- Using `t = 2A/P` is a geometric proxy; it does **not** verify thin-wall validity.
- Warping and shear deformation effects are **not** modeled.
- Only considers **tagged polygons**; untagged geometry is ignored.

---

## Practical guidance

- Use `@wall` for **open thin-walled** components (webs, flanges, plates) where strip-type torsion is appropriate.
- If you need general torsion constants outside thin-walled assumptions, these routines are not sufficient (a Prandtl/warping solver is required).


## Selection rule

A polygon is handled by the `@wall` path if its name contains (case-insensitive):

---

## Geometry requirements (non-obvious constraints)

The `@wall` routine does **not** reconstruct cells and does **not** support multi-loop encodings. It treats each `@wall` polygon as a single material patch.


### 4.2 Thin-strip (strip-like) shape (mandatory for validity)

Each `@wall` polygon must represent a **thin strip of material**, i.e. a wall patch whose midline length $b$ is much larger than thickness $t$.
This polygon is assumed to represent a thin rectangular wall patch (“rettangoloid” in 2D), i.e. a polygon that is well-approximated by a rectangle with:

two long edges (wall midline direction),

two short edges (thickness direction),

thickness t much smaller than the long dimension.


Operationally:

- the polygon should look like an “offset” of a centerline with two short closing edges
- two long sides are roughly parallel
- the patch is not a “block” or a “compact” solid region.

If the patch is not strip-like, the formula $J_i \approx A t^2/3$ is not a valid model.

### Prefer explicit thickness for complex shapes

If the strip has:
- noticeable curvature
- non-rectangular ends
- varying width
- local fillets/indentations

then always use `@t=`. The fallback $t=2A/P$ is only a rough estimate and may drift.

---

## 5) Recommended modeling pattern

Model an open thin-walled section as a **set of separate wall patches**, one polygon per patch:

- web plates
- flange plates
- stiffener plates

Each patch can have its own `weight` and its own `@t=`.

---

## 6) Minimal YAML example

The following example models one thin rectangular strip of length $b=1.0\,m$ and thickness $t=0.02\,m$.

Analytical (thin strip):

$$
J \approx \frac{b\,t^3}{3} = \frac{1.0\cdot 0.02^3}{3} = 2.666\times 10^{-6}\,m^4
$$

With $A=b\,t=0.02$, the code uses:

$$
J \approx \frac{A\,t^2}{3} = \frac{0.02\cdot 0.02^2}{3} = 2.666\times 10^{-6}\,m^4
$$

```yaml
CSF:
  sections:
    S0:
      z: 0
      polygons:
        strip@wall@t=0.02:
          weight: 1
          vertices:
            # A thin strip (single loop): 1.0 x 0.02
            - [0.00, 0.00]
            - [1.00, 0.00]
            - [1.00, 0.02]
            - [0.00, 0.02]
            - [0.00, 0.00]
```

Notes:

- For more complex open sections, use multiple `@wall` polygons.

---

## Practical checklist

A polygon is valid for `@wall` torsion (v2) if all items below are true:

1. Name includes `@wall`.
2. `vertices` define **one** closed loop (no concatenated loops).
3. The polygon represents a **thin strip** (midline length $b \gg t$).
4. Thickness is provided as `@t=...` (recommended), or the strip is thin enough that $t=2A/P$ is meaningful.
5. If thickness varies physically, the wall is split into multiple patches with separate polygons.

---

## Scope limitations

By design, this routine:

- approximates **open** thin-walled torsion (no cell closure effects)
- assumes one constant thickness per patch
- does not compute warping constants
- shape must be rectanguloid
- is not intended for compact solids or general thick-walled regions.

---
**
## 18. Torsional Constant (Roark – Equivalent Rectangle)

**Key:** `J_s_vroark`

General-purpose torsional constant estimate obtained by mapping the composite section to an **equivalent solid rectangle** (from effective area and principal inertias) and applying **Roark's torsion formula for a solid rectangle**.

Notes:
- Tag-free: independent of `@cell/@wall`.
- Not a thin-walled closed-cell (Bredt–Batho) formulation; closed/open thin-walled 
  torsion is handled by the dedicated `@cell/@wall` paths.
- The equivalent-rectangle mapping is a heuristic procedure internal to CSF. 
  Only the final torsion formula is from Roark; no literature reference exists 
  for the mapping step itself.
- Intended for compact solid sections (e.g. solid piles, filled profiles) where 
  `@cell/@wall` tagging is not applicable. Check `J_s_vroark_fidelity` before use: 
  reliable only when fidelity >= 0.6.

---

## 19. Roark Fidelity Index

**Key:** `J_s_vroark_fidelity`

Internal consistency index for the equivalent-rectangle mapping pipeline used to compute `J_s_vroark`. Intended as a trend/reliability indicator within the same method, not as an absolute physical accuracy metric.

**Range:** `[0, 1]`

Interpretation (recommended gating):
- `>= 0.6` : applicable
- `0.3 – 0.6` : borderline validity
- `< 0.3` : outside validity domain

---

## What `J_s_vroark_fidelity` means

`J_s_vroark_fidelity` is a **method-internal consistency indicator** for the same equivalent-mapping pipeline used to compute `J_s_vroark`.

Use it to:
- compare reliability trends along `z` **within the same model and same method**,
- identify zones where the equivalent mapping is more/less stable.

Do **not** use it as:
- an absolute, geometry-independent physical accuracy metric.

---

## Why sharp points can appear without a discontinuity

For many variable sections, any quantity derived from a branch selection (e.g., principal inertia I2(z) or the mapped I_min(z) used by the equivalent-rectangle pipeline) can show a sharp point (kink) when the governing branch changes (commonly near `Ix ≈ Iy`, especially when `Ixy ≈ 0`).

Important distinction:
- **Kink**: curve is continuous, slope changes abruptly.
- **Jump**: curve value itself is discontinuous.

A sharp visual point is not automatically a jump.

---

## How to read the fidelity plot correctly

When you look at `J_s_vroark_fidelity(z)`:

1. **Check continuity first**  
   If the curve is continuous and smooth except for mild corners, behavior is usually numerically consistent.

2. **Correlate with inertia branches**  
   Plot `Ix`, `Iy`, `I2` together.  
   If `Ix - Iy` crosses zero, `I2` may change branch and show a kink.

3. **Do not over-interpret local sharpness**  
   A narrow sharp point can be a branch-swap signature, not a solver failure.

4. **Read fidelity as a trend**  
   Focus on zones where fidelity degrades persistently over intervals, not on one single point.

---

## Suggested wording for reports

> `J_s_vroark_fidelity` quantifies internal consistency of the equivalent-mapping approach used for `J_s_vroark` along the member axis.  
> It is intended for comparative trend reading within the same method, not as a universal physical accuracy guarantee for arbitrary section shapes.

---

## Plot-reading checklist (quick)

Before concluding there is a bug, verify:
- [ ] `I2` left/right test with shrinking `dz`
- [ ] `Ix - Iy` sign around the same `z`
- [ ] `Ixy` magnitude (near zero often implies branch behavior is easier to interpret)
- [ ] no true jump in value, only slope change
- [ ] fidelity interpreted as method-confidence trend, not absolute truth

---

## Recommended figure set in documentation

To make interpretation robust, include these plots together:
1. `Ix(z), Iy(z), I2(z)` (same figure)
2. `Ix(z) - Iy(z)` (crossing visibility)
3. `J_s_vroark(z)`
4. `J_s_vroark_fidelity(z)`

---
## CSF sectionproperties mapping table

| CSF | SP field | Type | Notes |
|---|---|---|---|
| `A` | `e.a` | homogenized | do **not** map to `area` |
| `Cx` | `cx` | centroid | geometric centroid coordinate |
| `Cy` | `cy` | centroid | geometric centroid coordinate |
| `Ix` | `e.ixx_c` | homogenized | centroidal second moment |
| `Iy` | `e.iyy_c` | homogenized | centroidal second moment |
| `Ixy` | `e.ixy_c` | homogenized | centroidal product of inertia |
| `Ip` | `e.ixx_c + e.iyy_c` | derived homogenized | this is **not** `e.j` |
| `I1` | `e.i11_c` | homogenized | principal second moment |
| `I2` | `e.i22_c` | homogenized | principal second moment |
| `rx` | `rx` | homogenized-derived | consistent with `sqrt(e.ixx_c / e.a)` |
| `ry` | `ry` | homogenized-derived |  consistent with `sqrt(e.iyy_c / e.a)` |
| `Wx` | `e.zxx+`, `e.zxx-` | homogenized | CSF computes `Wx = Ix / c_y,max`, so it corresponds to the controlling modulus, i.e. `min(e.zxx+, e.zxx-)` |
| `Wy` | `e.zyy+`, `e.zyy-` | homogenized | CSF computes `Wy = Iy / c_x,max`, so it corresponds to the controlling modulus, i.e. `min(e.zyy+, e.zyy-)` |
| `J_sv_cell/wall` | `e.j` | torsion cell/wall polygon |  [De Saint-Venant Torsional Constant](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md) |
| `Q_na` | — | CSF-only |First Moment of Area |

This combination avoids misreading isolated curves.**

---
