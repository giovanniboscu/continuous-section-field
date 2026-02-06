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



## CSF Solid Torsion (Approx.): `compute_saint_venant_J` with `alpha` parameter

This note documents the scope, assumptions, and input requirements for the **current CSF “solid torsion” approximation**:

- `compute_saint_venant_J(section, alpha=..., eps_a=...)`

It matches the implementation that **does not solve a PDE on a grid**. Instead, it derives torsion from **pure geometric section properties**.

Math is written for **GitHub Markdown** using `$$...$$` blocks.

---

## 1) What this routine is (and is not)

This function returns an **approximate Saint-Venant torsional constant** for a *Section-like* object with multiple weighted polygons.

It is **not** a Prandtl stress-function (Poisson) solver. There is no meshing and no iterative field solution.

Instead, it starts from the **polar second moment of area** and applies a user-controlled correction factor `alpha`.

---

## 2) Core approximation

The polar second moment of area about the (weighted) centroid is:

$$
J_p = I_x + I_y
$$

For a circular solid section, the Saint-Venant torsion constant equals the polar moment:

$$
J_{sv} = J_p
$$

For **non-circular** solids, in general:

$$
J_{sv} \neq J_p
$$

This CSF routine approximates Saint-Venant torsion by scaling the polar moment:

$$
J_{sv} \approx \alpha\,J_p
$$

where:

- `alpha` is a **user-chosen reduction factor** that “maps” $J_p$ to an estimate of $J_{sv}$.

### 2.1 Interpretation of `alpha`

- $\alpha=1$ corresponds to the **circular** case (exact).
- Values $\alpha<1$ reflect that many non-circular shapes have **lower** Saint-Venant torsion constant than $J_p$.

The common default `alpha = 0.8436` matches the **square** ratio (engineering reference):

$$
\alpha_{square} \approx \frac{J_{sv}}{J_p} \approx 0.8436
$$

Use this default only if you accept that it is a **global approximation**.

---

## 3) Weighted multi-polygon combination

The routine is “weighted” across polygons.

Geometric integrals (area, centroid, inertias) are combined by linear weights $w_i$:

- weighted area: $A = \sum_i w_i A_i$
- weighted centroid: computed from weighted first moments
- weighted inertias: $I_x = \sum_i w_i I_{x,i}$, $I_y = \sum_i w_i I_{y,i}$

Then:

$$
J_p = I_x + I_y\quad\text{(about the weighted centroid)}
$$

and finally:
### 4.2 What the legacy `J_sv` cannot infer

`J_sv` is an **α·Jp approximation**, therefore it:

- does not classify the section as thin-walled / open / closed-cell;
- does not compute warping-related quantities (e.g., shear center, warping constant `Cw`);
- is not a general Saint-Venant torsion solver for multiply-connected shapes (holes): it may be accurate only in special cases.
$$
J_{sv} \approx \alpha\,J_p
$$

**Important:** this is an algebraic homogenization approach. It is not “automatic shape recognition” and it is not a union/difference geometry engine.

---

## 4) Geometry requirements (non-obvious constraints)

### What this method cannot infer
Because this is a $\alpha\,J_p$ approximation:

- it cannot detect whether a shape is thin-walled, open, closed-cell, etc.
- it does not compute warping-related quantities (e.g., $C_w$, shear center)
- it does not handle multiply-connected torsion physics (holes) in the Saint-Venant sense.

---

## 5) Under-the-hood geometry formulas (for `J_p`)

The helper logic computes polygon area/centroid/inertias from standard signed shoelace integrals.

### 5.1 Signed area (shoelace)
For vertices $(x_i, y_i)$, define:

$$
\text{cross}_i = x_i y_{i+1} - x_{i+1} y_i
$$

Then the signed area is:

$$
A = \frac{1}{2}\sum_i \text{cross}_i
$$

### 5.2 Second moments about the origin
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

### 5.3 Shift to the weighted centroid
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

---

## 6) Minimal YAML examples

### 6.1 Solid square (where `alpha≈0.8436` is meaningful)

```yaml
CSF:
  sections:
    S0:
      z: 0
      polygons:
        square_solid:
          weight: 1
          vertices:
            - [0.0, 0.0]
            - [1.0, 0.0]
            - [1.0, 1.0]
            - [0.0, 1.0]
            - [0.0, 0.0]
```

If you call:

```python
J = compute_saint_venant_J(section, alpha=0.8436)
```

you are explicitly choosing the “square-like” scaling $J_{sv}\approx 0.8436\,J_p$.

### 6.2 Solid circle (use `alpha=1`)

For a circle of radius $R$, the exact value is:

$$
J_{sv} = J_p = \frac{\pi}{2}R^4
$$

So set:

- `alpha = 1.0`

and discretize the circle as a single solid polygon.

---

## 7) Practical checklist

This method is appropriate if:

1. You want a **fast approximation** based on section inertias.
2. Each polygon is a **single closed loop** (one boundary per polygon).
3. You accept that $\alpha$ is a **global calibration factor**, not shape recognition.
4. You do not need multiply-connected Saint-Venant torsion physics (holes) in this path.

---

## 8) Scope limitations (by design)

- Accuracy depends on how representative the chosen $\alpha$ is for the actual shape family.
- For thin-walled open sections use `@wall`.
- For thin-walled closed cells use `@cell`.
- For general solids where $J_{sv}$ must be computed accurately for arbitrary shapes, a dedicated Prandtl/Poisson solver is required (not this function).



# Torsion constant methods for tagged polygons (`@cell` / `@wall`)

This note documents the *implemented* methods used by:

- `compute_saint_venant_J_cell(section)`
- `compute_saint_venant_J_wall(section)`

These routines do **not** solve the general Saint-Venant torsion boundary-value problem (Prandtl stress function / warping).
They compute **model-based** torsion constants under thin-walled assumptions, restricted to **user-selected polygons**.

Throughout, the returned quantity is a torsional constant `J_sv` in **m⁴**, intended to be used in a torsional stiffness `G · J_sv`.

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

### Weight usage

For torsional stiffness, negative stiffness is not physically meaningful.
Implemented convention:

\[
J_{\text{effective}} \;=\; \sum_i \left|w_i\right|\; J_i
\]

where `w_i` is the polygon weight and `J_i` the geometric torsion constant of that polygon entity.

---

# A) `compute_saint_venant_J_cell(section)`

## Purpose

Compute a **closed single-cell** torsional constant using a **Bredt–Batho** style formula
for a **thin-walled closed section** with (assumed) **constant thickness**.

This function only uses polygons tagged `@cell` or `@closed`.

If no such polygons are present, the current implementation returns `0`.

## Required parameters (user-specified)

### Thickness is required (current default)

For each `@cell` / `@closed` polygon, an explicit thickness **must** be provided:

- `@t=<value>`

If thickness is missing, the function raises an error (strict mode).

> Note: there is a legacy fallback path in the code (estimate thickness as `t = 2A/P`),
> but it is disabled by default (`REQUIRE_EXPLICIT_T = True`).

## Geometry encoding required by the implementation

A `@cell` polygon must encode **two loops** (outer boundary and inner boundary) in a **single vertex list**
using repeated vertices as delimiters (a “slit-cell” encoding):

- The **outer loop** starts at the first vertex and ends when that first vertex appears again.
- Immediately after that, the **inner loop** starts and ends when its first vertex appears again.

Schematically:

```
outer:  v0, v1, ... , v_{n-1}, v0,
inner:  u0, u1, ... , u_{m-1}, u0
```

Additional requirements enforced:

- Both loops must have at least 3 vertices.
- Outer and inner loops must have the **same number of vertices**:
  \[
  n = m
  \]
  (this is required to build a pointwise midline by vertex averaging).

## Method (step-by-step)

For each selected `@cell` polygon:

### Step 1 — Parse inputs

- Read polygon weight `w`
- Parse thickness `t` from `@t=...`
- Build the raw XY list from vertices (dropping only an explicit closure *at the very end*, if present)

### Step 2 — Split outer and inner loops

Identify the first repeated vertex to delimit the outer loop, and similarly for the inner loop.

### Step 3 — Area consistency checks

Compute signed polygon areas by the standard shoelace formula:

\[
A = \frac{1}{2}\sum_{i=0}^{N-1} \left(x_i y_{i+1} - x_{i+1} y_i\right)
\]

The routine computes:

- \(A_{\text{outer}} = |A(\text{outer loop})|\)
- \(A_{\text{inner}} = |A(\text{inner loop})|\)
- Wall area:
  \[
  A_{\text{wall}} = A_{\text{outer}} - A_{\text{inner}}
  \]

It then checks that \(A_{\text{wall}}\) is positive and consistent with the area returned by
`polygon_area_centroid(p)` (within a strict tolerance).

### Step 4 — Build a midline polygon

The midline is built by averaging corresponding vertices of the outer loop
and the **reversed** inner loop (to align orientation and indices):

\[
\mathbf{x}^{(m)}_k = \frac{1}{2}\left(\mathbf{x}^{(\text{outer})}_k + \mathbf{x}^{(\text{inner,ccw})}_k\right)
\]

This yields a midline polygon with:

- enclosed area \(A_m\)
- perimeter (midline length) \(b_m\)

# CSF `@cell` Polygon Encoding Requirements (v2)

This note describes the **strict geometric and data-encoding conditions** required by the current CSF closed-cell torsion routine:

- `compute_saint_venant_J_cell(section)` (v2)
- Bredt–Batho **single-cell**, **thin-walled**, **constant thickness** (`@t=...`)
- A closed cell is represented as **two loops encoded inside one polygon** (the “slit” encoding).

The goal is to prevent silent wrong results by making the input representation unambiguous and mechanically consistent.

---

## 1) What the algorithm assumes (conceptually)

A valid “cell polygon” represents a **tubular region** (a wall) bounded by:

- an **outer** closed contour (external boundary)
- an **inner** closed contour (hole boundary)

and it approximates the wall as **thin-walled** with **constant thickness** `t`.

The routine computes a *midline* (median contour) and applies the Bredt–Batho formula (constant thickness form):

$$
J \approx \frac{4A_m^2\,t}{b_m}
$$

where:

- $A_m$ is the area enclosed by the **midline**
- $b_m$ is the perimeter of the **midline**
- $t$ is the (constant) wall thickness from the polygon name tag `@t=...`

**Important:** in v2 the midline is built by **pairing vertices point-by-point** between outer and inner loops. Therefore, the data encoding must provide a consistent correspondence.

---

## 2) Required naming and parameters

### 2.1 Tag to activate the closed-cell path
The polygon **must** be tagged in its name:

- `@cell`  (preferred)
- or `@closed`

Example:

```yaml
poly@cell@t=0.5
```

### 2.2 Thickness must be explicit
Thickness must be provided as:

- `@t=<positive float>`

Example:

- `poly@cell@t=0.5`

If `@t=` is missing (and strict mode is enabled), CSF should raise an error rather than guessing thickness.

---

## 3) Required vertex encoding: **two closed loops in one `vertices` list**

A single `@cell` polygon encodes **two loops** concatenated into one `vertices` array.

### 3.1 Loop closure rule (mandatory)
Each loop must be explicitly closed by repeating its first vertex at the end of that loop.

So the pattern is:

1. Loop #1: `p0, p1, ..., pN-1, p0`
2. Loop #2: `q0, q1, ..., qN-1, q0`

### 3.2 Exactly two loops
The routine expects **exactly two** closed loops:

- one outer boundary
- one inner boundary

(“Multiple holes” inside the same `@cell` polygon are **not** supported by this routine.)

---

## 4) Orientation conventions (your project standard)

For consistency with CSF conventions, use:

- **Outer loop:** counter-clockwise (**CCW**)
- **Inner loop:** clockwise (**CW**)

This is an **input convention**. The routine may internally normalize orientation for midline construction, but you should keep the encoding consistent to avoid confusion and reduce failure modes.

---

## 5) Outer vs inner identification

Even if the two loops are provided in either order, the algorithm must be able to determine:

- which loop is **outer** (larger enclosed area)
- which loop is **inner** (smaller enclosed area)

Therefore, a valid cell must satisfy:

$$
|A_{outer}| > |A_{inner}|
$$

where areas are measured by the signed shoelace integral.

---

## 6) Discrete correspondence constraints 


### 6.1 Same vertex count (mandatory)
Outer and inner loops must have the **same number of distinct vertices** (excluding the repeated closure point).

If:

- outer has $N$ points
- inner has $M$ points

then you must have:

$$
N = M
$$

### 6.2 Phase alignment (mandatory)
The loops must have consistent “starting point” alignment so that:

- outer vertex `i` corresponds to inner vertex `i` along the contour progression.

If one loop is rotated (same shape, same points, different start index), the point-by-point pairing will be wrong and the computed midline may become distorted (or even degenerate).

### 6.3 Offset-like relationship (strongly recommended)
The method is intended for thin-walled cells where inner and outer boundaries are approximately “parallel” (inner is roughly an offset of outer).

In practice:

- the segment joining `outer[i]` and `inner[i]` should represent the local thickness direction.

This does **not** require a perfect geometric offset, but it requires the two loops to be sampled in a consistent way.

---

## 7) Consistency check on areas

A robust implementation often checks that the polygon’s net area matches the wall area implied by the two loops:

$$
A_{wall} = |A_{outer}| - |A_{inner}|
$$

and compares it to the area computed from the full polygon representation (as CSF integrates it).

If these do not match within tolerance, it usually means:

- the loop split failed (bad closure)
- outer/inner were swapped and not corrected
- the encoding is not representing a true wall region

This check prevents returning a numerically plausible but physically wrong $J$.

---

## 8) Minimal YAML example (template)

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

## 9) Practical checklist

A `@cell` polygon is valid for v2 if all items below are true:

1. Name includes `@cell` (or `@closed`).
2. Name includes `@t=<t>` with $t > 0$.
3. `weight` is present and not near zero.
4. `vertices` contains **two** loops.
5. Each loop is **explicitly closed** by repeating its first point.
6. Outer and inner loops have the **same number of vertices** (excluding closure).
7. Loops are **phase-aligned** (index-to-index correspondence).
8. Outer encloses inner and has **larger area magnitude**.
9. (Recommended) Outer is CCW, inner is CW.

---

## 10) Scope limitations (by design)

This routine is intentionally limited to keep it explicit and predictable:

- **Single-cell** only.
- **Constant thickness** only (`@t=`), not $t(s)$.
- Midline built by **pointwise averaging**, so correspondence constraints apply.

If you need general closed-cell torsion for arbitrary wall thickness or non-corresponding boundaries, the algorithm must change (e.g., arc-length parametrization, $\oint ds/t(s)$ integration, multi-cell system).
  

### Step 5 — Closed thin-walled torsion (Bredt–Batho)

For a closed thin-walled section of constant thickness \(t\), the implemented formula is:

\[
J_{\text{geom}} = \frac{4 A_m^2}{\displaystyle \int \frac{ds}{t}}
\quad\Longrightarrow\quad
J_{\text{geom}} = \frac{4 A_m^2}{b_m/t} = 4A_m^2\,\frac{t}{b_m}
\]

So the contribution of one `@cell` polygon is:

\[
J_i = 4A_m^2\frac{t}{b_m}
\]

### Step 6 — Weight scaling and accumulation

\[
J_{\text{total}} = \sum_i |w_i|\,J_i
\]

## Output

- Returns `max(J_total, 0)` as a float.

## Assumptions and limitations

- **Single-cell** per polygon entity (no multi-cell coupling).
- **Constant thickness** per polygon entity (one `t` per cell polygon).
- Requires **matched discretization** between outer and inner loops (same vertex count).
- Warping and non-uniform thickness effects are **not** modeled.
- Only considers **tagged polygons**; untagged geometry is ignored.

---

# B) `compute_saint_venant_J_wall(section)`

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

## Method (step-by-step)

For each selected `@wall` polygon:

### Step 1 — Compute geometric measures

- Area magnitude:
  \[
  A = \left|\;A_{\text{signed}}\;\right|
  \]
  using `polygon_area_centroid(p)[0]`.

- Perimeter \(P\) computed from the vertex polyline length.

### Step 2 — Thickness selection

- If `@t=<value>` is present: use that value.
- Otherwise estimate an equivalent thickness from geometry:

\[
t_{\text{eq}} = \frac{2A}{P}
\]

This rule is intentionally shape-agnostic (no profile recognition and no validation).

### Step 3 — Open thin-walled torsion constant

A standard thin-walled open-section approximation is:

\[
J \approx \int \frac{t(s)^3}{3}\,ds
\]

For a single wall strip with constant thickness \(t\) and midline length \(b\):

\[
J_i \approx \frac{b\,t^3}{3}
\]

The implementation avoids explicit midline reconstruction by using the thin-wall identity:

\[
A \approx b\,t \quad\Longrightarrow\quad b \approx \frac{A}{t}
\]

Substituting into the strip formula gives:

\[
J_i \approx \frac{(A/t)\,t^3}{3} = \frac{A\,t^2}{3}
\]

So the implemented per-polygon contribution is:

\[
J_i = \frac{A\,t^2}{3}
\]

### Step 4 — Weight scaling and accumulation

\[
J_{\text{total}} = \sum_i |w_i|\,J_i
\]

## Output

- Returns `J_total` as a float.

## Assumptions and limitations

- Intended for **open thin-walled** components represented as wall polygons.
- Thickness may be **user-specified** (`@t=`) or **estimated** (`t = 2A/P`).
- Using `t = 2A/P` is a geometric proxy; it does **not** verify thin-wall validity.
- Warping and shear deformation effects are **not** modeled.
- Only considers **tagged polygons**; untagged geometry is ignored.

---

## Practical guidance

- Use `@cell ... @t=` when you have a **closed thin-walled** single-cell representation and you can provide a reliable wall thickness.
- Use `@wall` for **open thin-walled** components (webs, flanges, plates) where strip-type torsion is appropriate.
- If you need general torsion constants outside thin-walled assumptions, these routines are not sufficient (a Prandtl/warping solver is required).


# CSF `@wall` Polygon Geometry Requirements

This note documents the **geometric/data-encoding requirements** assumed by the current CSF open-wall torsion routine:

- `compute_saint_venant_J_wall(section)`
- open thin-walled approximation over polygons tagged with `@wall`
- thickness per wall polygon is either explicit (`@t=...`) or estimated.

The purpose is to make the input representation **explicit** and to avoid silent misuse (e.g., using `@wall` for “bulky” solids or multi-loop slit encodings).

---

## 1) What this `@wall` routine computes

For each polygon tagged `@wall`, the routine approximates the **Saint-Venant torsional constant** of an **open thin-walled strip**.

The classical thin-walled open-section formula is:

$$
J \approx \int \frac{t(s)^3}{3}\,ds
$$

If the thickness is constant on the strip, $t(s)=t$, and if $b = \int ds$ is the strip length along the midline, then:

$$
J \approx \frac{b\,t^3}{3}
$$

In this implementation the midline length $b$ is not computed explicitly. Instead it uses the thin-strip area approximation $A \approx b\,t$ to get:

$$
J_i \approx \frac{A\,t^2}{3}
$$

and sums contributions (scaled by non-negative stiffness weight):

$$
J_{total} = \sum_i |w_i|\,J_i
$$

---

## 2) Selection rule

A polygon is handled by the `@wall` path if its name contains (case-insensitive):

- `@wall`

If no polygon contains `@wall`, the routine returns the **legacy** torsion value (outside the scope of this note).

---

## 3) Thickness definition per wall polygon

### 3.1 Explicit thickness (recommended)
Provide thickness in the polygon name:

- `@t=<positive float>`

Example:

- `web@wall@t=0.012`

This is the preferred mode because it avoids geometric guessing.

### 3.2 Estimated thickness (fallback)
If `@t=` is not present, thickness is estimated as:

$$
t := \frac{2A}{P}
$$

where:

- $A$ is the polygon area (absolute)
- $P$ is the polygon perimeter.

**Important:** this estimate is only reliable when the polygon is a **thin strip** (high aspect ratio). For “bulky” polygons $2A/P$ behaves like a hydraulic-radius-type measure and is not a good wall thickness.

---

## 4) Geometry requirements (non-obvious constraints)

The `@wall` routine does **not** reconstruct cells and does **not** support multi-loop encodings. It treats each `@wall` polygon as a single material patch.

### 4.1 Single-loop boundary (mandatory)
`vertices` must represent **one single closed loop**.

- Do **not** concatenate multiple loops in one `vertices` list.
- Do **not** use slit-style “outer+inner” loop encodings inside a `@wall` polygon.

Reason: the perimeter is computed by wrapping the vertex list with `(i+1) % n`, which assumes a single loop.

### 4.2 Thin-strip (strip-like) shape (mandatory for validity)
Each `@wall` polygon must represent a **thin strip of material**, i.e. a wall patch whose midline length $b$ is much larger than thickness $t$.

Operationally:

- the polygon should look like an “offset” of a centerline with two short closing edges
- two long sides are roughly parallel
- the patch is not a “block” or a “compact” solid region.

If the patch is not strip-like, the formula $J_i \approx A t^2/3$ is not a valid model.

### 4.3 Approximately constant thickness on the patch
A single `@wall` polygon represents **one constant thickness** (either explicit or estimated). If the physical thickness varies, split the wall into multiple polygons, each with its own `@t=`.

### 4.4 Prefer explicit thickness for complex shapes
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

## 17. Torsional Constant (Roark / Bredt)

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

## 18. Roark Fidelity Index

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

For the formal torsional selection rules, see:

**README-P.md – CSF Torsional Constant Policy**
