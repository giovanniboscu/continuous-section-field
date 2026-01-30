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




# `compute_saint_venant_J(section)` — Generic approximate torsion constant (always calculated)

This document specifies a **generic, always-computable** approximation for the torsion constant `J` returned by
`compute_saint_venant_J(section)`.

The purpose is **not** to provide a universally valid Saint-Venant solution, but to provide a **single, coherent**
model that:

- can be applied to **any** polygonal section (open, closed, mixed),
- is **always** computable (no special-case branching by topology),
- makes all modeling assumptions **explicit**, so the **user** can judge applicability.

> If you need a method that explicitly models thin-walled **closed cells** or **open walls**, use the specialized routines
> `compute_saint_venant_J_cell(...)` and `compute_saint_venant_J_wall(...)`.

---

## What this method is (and is not)

### What it is
A **thin-walled strip model** applied to each polygon independently and summed:

- each polygon is treated as an equivalent thin strip with thickness `t`,
- torsion constant is computed using the standard open-strip expression,
- the final `J` is the sum of all polygon contributions (optionally weight-scaled).

### What it is not
- **Not** a general Saint-Venant torsion solver (no Prandtl stress function, no warping solution).
- **Not** a topology-aware method (does not identify cells, multi-cells, or coupling between cells).
- **Not** a verification routine (does not validate the thin-wall condition).

This is an **engineering approximation** designed to be **well-defined for any input**.

---

## Inputs and metadata

### Input
- `section`: a `Section` object providing a list of polygons `section.polygons`.

Each polygon is assumed to provide:
- `vertices`: ordered 2D points `(x, y)` in **meters**
- `name`: string
- `weight`: scalar (dimensionless)

### Optional thickness override
Thickness can be specified per polygon via a token in the polygon name:

- `@t=<value>` where `<value>` is thickness in **meters**, e.g. `@t=0.010`

If `@t=` is absent, thickness is estimated automatically (see below).

---

## Output

- A scalar torsion constant `J` in **m⁴**.
- Intended to be used in torsional stiffness as `G · J`.

---

## Declared modeling assumptions

This method assumes:

1. **Thin-wall / strip behavior**
   - Each polygon can be represented by an equivalent thin strip.

2. **Independent contributions**
   - The global torsion constant is the sum of polygon contributions.
   - No multi-cell coupling or compatibility constraints are enforced.

3. **No warping solution**
   - Warping is not solved. The result is a Saint-Venant-like *estimate* under thin-wall assumptions.

4. **User responsibility**
   - The method will return a value even outside validity; the user must assess acceptability.

---

## Geometry primitives

For each polygon with vertices $(x_i, y_i)$, define:

### Signed area (shoelace)

$$
A_{\text{signed}}=\frac{1}{2}\sum_{i=0}^{N-1}\left(x_i y_{i+1}-x_{i+1}y_i\right)
$$

Area magnitude:

$$
A = \left|A_{\text{signed}}\right|
$$

### Perimeter

$$
P=\sum_{i=0}^{N-1}\left\|\mathbf{x}_{i+1}-\mathbf{x}_i\right\|
$$

with $\mathbf{x}_i=(x_i,y_i)$ and wrap-around indexing $i+1 \to 0$.

---

## Thickness definition (always defined)

For each polygon $i$, define thickness $t_i$ as:

$$
t_i=
\begin{cases}
t_{\text{user}} & \text{if a valid }@t=\text{ token is present} \\
\displaystyle \frac{2A_i}{P_i} & \text{otherwise}
\end{cases}
$$

Requirements:
- $t_i > 0$. If $t_i \le 0$, the contribution is invalid (implementation should emit an error or set contribution to zero).

Notes:
- $t_{\text{eq}} = 2A/P$ is a purely geometric proxy. It **does not** validate thin-wall behavior.

---

## Core torsion model (thin strip)

### Strip torsion constant
For an open thin strip of thickness $t$ and midline length $b$, the standard approximation is:

$$
J \approx \int \frac{t(s)^3}{3}\,ds
\quad\Rightarrow\quad
J \approx \frac{b\,t^3}{3}\quad(\text{constant }t)
$$

### Eliminating explicit midline length
Using the thin-wall identity $A \approx b\,t$, set:

$$
b \approx \frac{A}{t}
$$

Substitute into the strip expression:

$$
J_i \approx \frac{(A_i/t_i)\,t_i^3}{3}=\frac{A_i\,t_i^2}{3}
$$

Therefore the per-polygon contribution is:

$$
\boxed{J_i=\frac{A_i\,t_i^2}{3}}
$$

This formula is **always computable** as long as $A_i$ and $t_i$ are defined.

---

## Weight scaling

In many workflows, `weight` represents an effective stiffness scaling (e.g., normalized modulus ratio).
Torsional stiffness should not become negative; therefore a conservative convention is:

$$
J_{\text{total}}=\sum_i \left|w_i\right|\,J_i
$$

If your modeling intent requires signed contributions, this must be stated explicitly and implemented as a different routine.

---

## Full algorithm (reference specification)

Given `section.polygons`:

For each polygon $i$:

1. Compute $A_i$ (area magnitude) and $P_i$ (perimeter).
2. Determine thickness $t_i$:
   - from `@t=<value>` if present and valid, else
   - $$t_i = \frac{2A_i}{P_i}$$
3. Compute geometric torsion contribution:
   $$J_i = \frac{A_i\,t_i^2}{3}$$
4. Apply weight scaling:
   $$J_i \leftarrow |w_i|\,J_i$$
5. Accumulate:
   $$J \leftarrow J + J_i$$

Return $J$.

**Edge cases (recommended handling):**
- If $A_i = 0$ or $P_i = 0$: set $J_i = 0$ and emit a warning.
- If $t_i \le 0$: error or $J_i = 0$ with warning (choose one policy and document it).

---

## Interpretation and limitations

### When this method is reasonable
- Dominant behavior is **thin-walled** and **strip-like**.
- You want a **single fallback** that never fails and is consistent across geometries.
- You accept that closed-cell effects are not explicitly enforced.

### When this method is not appropriate
- Thick sections (solid rectangles, circles) where thin-wall assumptions break.
- Multi-cell closed sections where cell coupling matters.
- Cases where warping restraint is significant and must be captured.

### Relationship to specialized methods
- **Closed thin-walled cells:** Bredt–Batho is typically more appropriate:

$$
J=\frac{4A_m^2}{\int \frac{ds}{t}}
$$

Use `compute_saint_venant_J_cell(...)`.

- **Open thin-walled walls:** strip model is appropriate and can be applied per wall:

$$
J \approx \int \frac{t^3}{3}\,ds
$$

Use `compute_saint_venant_J_wall(...)`.

This generic routine intentionally **does not** branch by topology: it applies the strip model everywhere.

---

## Quick sanity check: square box (order-of-magnitude)

For a thin-walled square box (side $0.4$ m, thickness $t$), the closed-cell Bredt–Batho estimate scales like:

$$
J_{\text{cell}} \sim (0.4-t)^3\,t
$$

The generic strip model will generally produce a value of the same **order of magnitude** but may differ systematically
because it does not enforce closed-cell compatibility. This is expected and should be documented in validation notes.

---

## Summary

`compute_saint_venant_J(section)` (generic spec) is:

- **Always defined**
- **Single-model**
- **Explicit assumptions**
- **User-judged validity**

It returns:

$$
\boxed{
J = \sum_i |w_i|\,\frac{A_i\,t_i^2}{3}
}
$$

with

$$
t_i=
\begin{cases}
t_{\text{user}} & \text{if }@t=\text{ provided} \\
\displaystyle \frac{2A_i}{P_i} & \text{otherwise}
\end{cases}
$$






























**Notes**
- Valid primarily for **open thin-walled sections**.
- Used as the **reference torsional constant** when no closed cell is detected.

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
