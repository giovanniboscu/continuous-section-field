# CSF – Section Full Analysis Output

This document explains **all quantities reported by the CSF _Section Full Analysis_**.

It is intended as a **clear, engineering-oriented reference** for users who want to:
- understand what each value represents,
- know how it is computed in CSF,
- understand **the validity domain and limitations** of each quantity.

Whenever a quantity depends on **a specific modelling choice or policy** defined elsewhere (e.g. torsion selection rules), this is marked with **double asterisks `**`** and explicitly noted.

---

## General Notes

- All quantities are computed **purely from geometry and polygon weights**.
- No assumptions are made about profile families (I, H, box, tube, etc.).
- Polygon `weight` is treated as a **scalar field multiplier** (e.g. modular ratio, material factor).
- Negative weights are allowed and represent **subtractive domains**.

---

## 1. Area (A)

**Key:** `A`

**Definition**  
Total **net cross-sectional area**, including the effect of polygon weights.

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

## 7. Polar Moment (J)

**Key:** `J`

Polar second moment of area:

J = Ix + Iy

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
- Used only as a **fallback**.

---

## 15. First Moment of Area Q

**Key:** `Q_na`

First moment of area about the **neutral axis**.

Used in shear stress estimation:

Q = integral( y * dA ) about the neutral axis

---
## 16. Torsional Constant (Saint-Venant)

**Key:** `J_sv`

CSF reports `J_sv` using the legacy solid-torsion approximation with **α = 1** (as shown in CSF output reports).

---

## CSF solid torsion : `compute_saint_venant_J` (α·Jp, with α=1)

This routine **does not** solve Prandtl’s stress-function PDE (no mesh, no field solution).  
It derives torsion from **geometric section properties** and applies a scalar factor α.

### Core approximation

The polar second moment of area about the (weighted) centroid is:

$$
J_p = I_x + I_y
$$

For a circular solid section:

$$
J_{sv} = J_p
$$

For a general non-circular section:

$$
J_{sv} \neq J_p
$$

CSF uses the approximation:

$$
J_{sv} \approx \alpha\,J_p
$$

In CSF reports for this legacy path, **α = 1**, hence:

$$
J_{sv} \approx J_p
$$

### Multi-polygon weighting

For multiple polygons with weights $w_i$, CSF combines geometric integrals linearly:

$$
A = \sum_i w_i A_i
$$

Centroid from weighted first moments, and inertias:

$$
I_x = \sum_i w_i I_{x,i},\qquad I_y = \sum_i w_i I_{y,i}
$$

Then:

$$
J_p = I_x + I_y
$$

(all evaluated about the **weighted centroid**), and finally:

$$
J_{sv} \approx \alpha\,J_p
$$

---

## Limitations of this `J_sv`

Because this is an **α·Jp approximation**, it:

- does **not** classify the section as thin-walled / open / closed-cell;
- does **not** compute warping-related quantities (e.g., shear center, warping constant $C_w$);
- is **not** a general Saint-Venant torsion solver for multiply-connected shapes (holes): it may be accurate only in special cases.
---

## Under-the-hood geometry formulas 

The internal logic computes polygon area/centroid/inertias from standard signed shoelace integrals.

### Signed area (shoelace)
For vertices $(x_i, y_i)$, define:

$$
\text{cross}_i = x_i y_{i+1} - x_{i+1} y_i
$$

Then the signed area is:

$$
A = \frac{1}{2}\sum_i \text{cross}_i
$$

### Second moments about the origin
The standard (signed) formulas are:

$$
I_x = \frac{1}{12}\sum_i (y_i^2 + y_i y_{i+1} + y_{i+1}^2)\,\text{cross}_i
$$

$$
I_y = \frac{1}{12}\sum_i (x_i^2 + x_i x_{i+1} + x_{i+1}^2)\,\text{cross}_i
$$

$$
I_{xy} = \frac{1}{24}\sum_i (x_i y_{i+1} + 2x_i y_i + 2x_{i+1} y_{i+1} + x_{i+1} y_i)\,\text{cross}_i
$$

### Shift to the weighted centroid
Composite centroid $(\bar x, \bar y)$ is computed from weighted first moments.

The parallel-axis theorem shifts inertias from the origin to the composite centroid, e.g.:

$$
I_{x,c} = I_{x,o} - A\,\bar y^2,\qquad
I_{y,c} = I_{y,o} - A\,\bar x^2
$$

Then:

$$
J_p = I_{x,c} + I_{y,c}
$$

and:

$$
J_{sv} \approx \alpha\,J_p
$$


##  Practical checklist

This method is appropriate if:

1. You want a **fast approximation** based on section inertias.
2. Each polygon is a **single closed loop** (one boundary per polygon).
3. You accept that $\alpha$ is a **global calibration factor**, not shape recognition.
4. You do not need multiply-connected Saint-Venant torsion physics (holes) in this path.

---

## Scope limitations (by design)

- For thin-walled open sections use `@wall`.
- For thin-walled closed cells use `@cell`.
- For general solids where $J_{sv}$ must be computed accurately for arbitrary shapes, a dedicated Prandtl/Poisson solver is required (not this function).


## Torsion constant methods for tagged polygons (`@cell` / `@wall`)
**Key:** `J_sv_cell`   `J_sv_wall` 


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


### Input object

Both functions accept:

- `section`: a `Section` object providing `section.polygons`.

Each polygon is assumed to provide:

- `polygon.vertices`: ordered 2D vertices `(x, y)` (meters)
- `polygon.name`: string
- `polygon.weight`: scalar weight

### Tagging (polygon selection)

Only polygons whose **name** contains the relevant token are used:

- **Cell method:** name contains `@cell` or `@closed` (case-insensitive)
- **Wall method:** name contains `@wall` (case-insensitive)

All other polygons are **ignored** by these functions.

### Thickness token (`@t=<value>`)

A thickness override may be encoded in the polygon name as:

- `...@t=0.010`  (meters)

Parsing rules (both functions):

- Case-insensitive `@t=`
- Parsing stops at the first character that is not one of: `0–9 . + - e E`
- Thickness must be strictly positive (`t > 0`) or it is rejected

---

## 17. `compute_saint_venant_J_cell(section)`

**Key:** `J_sv_cell`  

## Purpose

Compute a **closed single-cell** torsional constant using a **Bredt–Batho** style formula
for a **thin-walled closed section** with (assumed) **constant thickness**.

This function only uses polygons tagged `@cell` or `@closed`.

If no `@cell` polygons are present, the current implementation returns `0`.


## Required parameters (user-specified)

### Thickness is required (current default)

For each `@cell` / `@closed` polygon, an explicit thickness **must** be provided:

- `@t=<value>`

## `@cell` Polygon Encoding Requirements

This note describes the **strict geometric and data-encoding conditions** required by the current CSF closed-cell torsion routine:

- `compute_saint_venant_J_cell(section)` (v2)
- Bredt–Batho **single-cell**, **thin-walled**, **constant thickness** (`@t=...`)
- A closed cell is represented as **two loops encoded inside one polygon** (the “slit” encoding).

The goal is to prevent silent wrong results by making the input representation unambiguous and mechanically consistent.

---
## Required naming and parameters

### Tag to activate the closed-cell path
The polygon **must** be tagged in its name:

- `@cell`  (preferred)
- or `@closed`

Example:

```yaml
poly@cell@t=0.5
```

### Thickness must be explicit
Thickness must be provided as:

- `@t=<positive float>`

Example:

- `poly@cell@t=0.5`

If `@t=` is missing (and strict mode is enabled), CSF should raise an error rather than guessing thickness.

---

## Required vertex encoding: **two closed loops in one `vertices` list**

A single `@cell` polygon encodes **two loops** concatenated into one `vertices` array.

### Exactly two loops
The routine expects **exactly two** closed loops:

- one outer boundary
- one inner boundary

(“Multiple holes” inside the same `@cell` polygon are **not** supported by this routine.)

---

##  Orientation conventions (your project standard)

For consistency with CSF conventions, use:

- **Outer loop:** counter-clockwise (**CCW**)
- **Inner loop:** clockwise (**CW**)

This is an **input convention**. The routine may internally normalize orientation for midline construction, but you should keep the encoding consistent to avoid confusion and reduce failure modes.

---
## Minimal YAML example 

```yaml
CSF:
  sections:
    S0:
      z: 0
      polygons:
        poly@cell@t=0.5:
          weight: 1
          vertices:
            # INNER loop (CW) - explicitly closed
            - [xi0, yi0]
            - [xi1, yi1]
            - [xi2, yi2]
            - [xi0, yi0]

            # OUTER loop (CCW) - explicitly closed
            - [xo0, yo0]
            - [xo1, yo1]
            - [xo2, yo2]
            - [xo0, yo0]
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
4. Outer and inner loops have the **same number of vertices** (excluding closure).
5. Outer encloses inner and has **larger area magnitude**.


---

## 18 `compute_saint_venant_J_wall

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

- `@wall`

---

## 3) Thickness definition per wall polygon

### 3.1 Explicit thickness (recommended)
Provide thickness in the polygon name:

- `@t=<positive float>`

Example:

- `web@wall@t=0.012`

This is the preferred mode because it avoids geometric guessing.

### Estimated thickness (fallback)
If `@t=` is not present, thickness is estimated as:

$$
t := \frac{2A}{P}
$$

where:

- $A$ is the polygon area (absolute)
- $P$ is the polygon perimeter.

**Important:** this estimate is only reliable when the polygon is a **thin strip** (high aspect ratio). For “bulky” polygons $2A/P$ behaves like a hydraulic-radius-type measure and is not a good wall thickness.

---

## Geometry requirements (non-obvious constraints)

The `@wall` routine does **not** reconstruct cells and does **not** support multi-loop encodings. It treats each `@wall` polygon as a single material patch.


### 4.2 Thin-strip (strip-like) shape (mandatory for validity)
Each `@wall` polygon must represent a **thin strip of material**, i.e. a wall patch whose midline length $b$ is much larger than thickness $t$.

Operationally:

- the polygon should look like an “offset” of a centerline with two short closing edges
- two long sides are roughly parallel
- the patch is not a “block” or a “compact” solid region.

If the patch is not strip-like, the formula $J_i \approx A t^2/3$ is not a valid model.

### Approximately constant thickness on the patch
A single `@wall` polygon represents **one constant thickness** (either explicit or estimated). If the physical thickness varies, split the wall into multiple polygons, each with its own `@t=`.

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

- Single loop, explicitly closed (repeat the first point).
- For more complex open sections, use multiple `@wall` polygons.

---

## 7) Practical checklist

A polygon is valid for `@wall` torsion (v2) if all items below are true:

1. Name includes `@wall`.
2. `vertices` define **one** closed loop (no concatenated loops).
3. The polygon represents a **thin strip** (midline length $b \gg t$).
4. Thickness is provided as `@t=...` (recommended), or the strip is thin enough that $t=2A/P$ is meaningful.
5. If thickness varies physically, the wall is split into multiple patches with separate polygons.

---

## 8) Scope limitations

By design, this routine:

- approximates **open** thin-walled torsion (no cell closure effects)
- assumes one constant thickness per patch
- does not compute warping constants
- is not intended for compact solids or general thick-walled regions.


---

## 19. Torsional Constant (Roark / Bredt)

**Key:** `J_s_vroark`

Closed-cell torsional constant based on Bredt–Batho / Roark thin-walled theory.

Plain-text formula:

J ≈ 4 * A_cell^2 * t / P

where:
- A_cell = area enclosed by the wall midline
- t = wall thickness
- P = cell perimeter

**Notes**
- Applicable **only to closed thin-walled cells**.
- Automatically ignored for open sections **

---

## 20. Roark Fidelity Index

**Key:** `J_s_vroark_fidelity`

Dimensionless reliability index in the range [0, 1].

Interpretation:

- > 0.6 : model applicable
- 0.3 – 0.6 : borderline validity
- < 0.3 : outside validity domain

**Notes**
- Used to gate the use of `J_s_vroark` **

---

## Final Remarks

- CSF deliberately exposes **multiple torsional indicators**.
- **Selection is policy-driven**, not profile-driven **
- This guarantees transparency, robustness, and solver independence.

# Interpreting `J_s_vroark_fidelity` and Reading the Plot in Practice

## Purpose

This page explains how to interpret `J_s_vroark_fidelity` in CSF and how to read the associated plot correctly, using non-prismatic sections (including T-like cases).

It is intentionally practical and documentation-oriented.

---

## What `J_s_vroark_fidelity` means

`J_s_vroark_fidelity` is a **method-internal consistency indicator** for the same equivalent-mapping pipeline used to compute `J_s_vroark`.

Use it to:

- compare reliability trends along `z` **within the same model and same method**,
- identify sections where the equivalent mapping is more/less stable.

Do **not** use it as:

- an absolute, geometry-independent physical accuracy metric.

---

## Why sharp points can appear without a discontinuity

For many variable sections, principal inertia `I2(z)` can show a sharp point (kink) when the governing branch changes (commonly near `Ix ≈ Iy`, especially when `Ixy ≈ 0`).

Important distinction:

- **Kink**: curve is continuous, slope changes abruptly.
- **Jump**: curve value itself is discontinuous.

A sharp visual point in the plot is not automatically a jump.

---

## How to read the fidelity plot correctly

When you look at `J_s_vroark_fidelity(z)`:

1. **Check continuity first**  
   If the curve is continuous and smooth except for mild corners, behavior is usually numerically consistent.

2. **Correlate with inertia branches**  
   Plot `Ix`, `Iy`, `I2` together.  
   If `Ix-Iy` crosses zero, `I2` may change branch and show a kink.

3. **Do not over-interpret local sharpness**  
   A narrow sharp point can be a branch-swap signature, not a solver failure.

4. **Read fidelity as a trend**  
   Focus on zones where fidelity degrades persistently over intervals, not on one single point.

---

## Suggested wording for reports

Use this wording in outputs/manuals:

> `J_s_vroark_fidelity` quantifies internal consistency of the equivalent-mapping approach used for `J_s_vroark` along the member axis.  
> It is intended for comparative trend reading within the same method, not as a universal physical accuracy guarantee for arbitrary section shapes.

---

## Plot-reading checklist (quick)

Before concluding there is a bug, verify:

- [ ] `I2` left/right test with shrinking `dz`  
- [ ] `Ix-Iy` sign around the same `z`  
- [ ] `Ixy` magnitude (near zero often implies branch behavior is easier to interpret)  
- [ ] no true jump in value, only slope change  
- [ ] fidelity interpreted as method-confidence trend, not absolute truth

---

## Recommended figure set in documentation

To make interpretation robust, include these plots together:

1. `Ix(z), Iy(z), I2(z)` (same figure)  
2. `Ix(z)-Iy(z)` (crossing visibility)  
3. `J_s_vroark(z)`  
4. `J_s_vroark_fidelity(z)`

This combination avoids misreading isolated curves.

---

## Final note

A sharp point in `I2` or in a related indicator may be a legitimate geometric-transition signature.  
The correct criterion is continuity testing, not visual smoothness alone.


For the formal torsional selection rules, see:

**README-P.md – CSF Torsional Constant Policy**
