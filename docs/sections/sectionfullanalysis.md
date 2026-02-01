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



# `compute_saint_venant_J` — Saint-Venant torsional constant for *solid* polygonal regions

This note specifies the intended behavior and mathematics for a function:

```python
def compute_saint_venant_J(polygons, *, grid_h, ...):
    ...
```

The function computes the Saint-Venant torsional constant **J** for a set of planar polygonal regions, each treated as a **solid** (filled) domain, and combines them with a per-polygon **weight**.

This document is written to match a “do what you’re told” contract:
- **No geometry validation** is performed (no convexity checks, no self-intersection checks, no repairs).
- **No biasing** (no `abs()` on signed quantities, no “fix orientation”, no automatic defaults for missing attributes).
- The algorithm acts **blindly** on the supplied polygons and weights.

---

## 1) Definitions and scope

Let the cross-section consist of **n** polygonal regions:

$$
\Omega = \{\Omega_1, \Omega_2, \dots, \Omega_n\}
$$

Each region $\Omega_i$ is the interior of a polygon described by a vertex list in the plane $(x,y)$, and has an associated **scalar weight** $w_i \in \mathbb{R}$.

### Output

The function returns a **weighted torsional constant**:

$$
J_\text{tot} = \sum_{i=1}^{n} w_i \, J_i
$$

where $J_i$ is the Saint-Venant torsional constant of the *solid* region $\Omega_i$.

### Interpretation of the weight

The meaning of $w_i$ is **external** to this function.

Common interpretation in CSF-style workflows:
- If $w_i = G_i / G_\text{ref}$ (or $E_i/E_\text{ref}$ under a chosen convention), then the returned
  $$J_\text{tot} = \sum (G_i/G_\text{ref})\,J_i$$
  can be used as a modular/weighted torsion measure so that
  $$G_\text{ref}\,J_\text{tot} = \sum G_i\,J_i$$

This function does **not** enforce physical constraints (e.g., it allows negative weights).

---

## 2) “Solid” means “filled domain”

Each polygon is treated as a filled region (a *solid cross-sectional domain*). There is:
- no recognition of holes,
- no nesting/subtraction,
- no @wall/@cell behavior,
- no topological union operation between polygons.

Therefore, if two polygons overlap, the overlap area is **counted twice** (once in each domain), because the contribution is computed per-domain and then summed. This is intentional under the “take what you find” contract.

---

## 3) Saint-Venant torsion via Prandtl stress function

For a solid simply-connected domain $\Omega_i$, define the **Prandtl stress function** $\psi_i(x,y)$ as the solution of the Poisson problem:

$$
\nabla^2 \psi_i = -2 \quad \text{in } \Omega_i
$$

with Dirichlet boundary condition:

$$
\psi_i = 0 \quad \text{on } \partial\Omega_i
$$

The Saint-Venant torsional constant is then:

$$
J_i = 2 \int_{\Omega_i} \psi_i \, dA
$$

### Equivalent energy identity (useful for checks)

Using Green’s identity (for sufficiently regular solutions):

$$
\int_{\Omega_i} \|\nabla \psi_i\|^2 \, dA = 2\int_{\Omega_i} \psi_i \, dA
$$

so one may also view:

$$
J_i = \int_{\Omega_i} \|\nabla \psi_i\|^2 \, dA
$$

(The implementation may compute $J_i$ using either expression; the primary definition in this spec is
$J_i = 2 \int \psi_i\, dA$.)

---

## 4) Discrete numerical method (Cartesian grid Poisson solve)

A robust, geometry-agnostic way to solve the Poisson problem on arbitrary polygons is a **masked Cartesian grid** method:

1. Build a bounding box around the polygon $\Omega_i$.
2. Create a uniform grid with spacing $h$:
   - grid nodes $(x_p, y_q)$
3. Classify nodes as **inside** or **outside** the polygon (point-in-polygon test).
4. Solve the discrete Poisson equation on the inside nodes, enforcing $\psi=0$ on boundary/outside.

### 4.1 Discrete Laplacian

For an interior grid node $(p,q)$ inside $\Omega_i$, approximate:

$$
\nabla^2 \psi(p,q) \approx \frac{\psi_{p+1,q}+\psi_{p-1,q}+\psi_{p,q+1}+\psi_{p,q-1}-4\psi_{p,q}}{h^2}
$$

Impose:

$$
\frac{\psi_{p+1,q}+\psi_{p-1,q}+\psi_{p,q+1}+\psi_{p,q-1}-4\psi_{p,q}}{h^2} = -2
$$

For neighbors outside the domain, use $\psi=0$ (Dirichlet condition). This yields a sparse linear system:

$$
A\,\mathbf{\psi}=\mathbf{b}
$$

### 4.2 Discrete torsional constant

Once $\psi$ is solved on the grid nodes classified inside:

$$
J_i \approx 2 \sum_{(p,q)\in \Omega_i} \psi_{p,q}\, h^2
$$

This is a midpoint-like quadrature on a uniform grid.

---

## 5) Combined weighted result

Given $J_i$ for each polygon:

$$
J_\text{tot} = \sum_{i=1}^{n} w_i\,J_i
$$

No post-processing is applied:
- no absolute value,
- no clipping,
- no normalization.

If the calling code wants physical constraints (e.g., $w_i\ge 0$), it must enforce them upstream.

---

## 6) Preconditions (expected upstream)

This function intentionally does **not** validate or repair input. For meaningful results, upstream validation should ensure:

- Each polygon has at least 3 vertices.
- Vertices define a non-degenerate region (non-zero area).
- Polygon is simple enough for point-in-polygon classification (no wild self-intersections).
- Each polygon provides a finite numeric weight $w_i$.

If these are violated, the method may:
- fail numerically (singular/ill-conditioned system),
- return meaningless values,
- or raise errors from the linear solver.

---

## 7) Accuracy and resolution guidance (practical)

Let $D$ be a characteristic dimension (e.g., the minimum bounding-box side length). Accuracy improves as $h$ decreases.

A pragmatic rule:
- Choose $h \approx D / N$ with $N$ in the range 80–250 for engineering-grade estimates,
  depending on aspect ratio and required accuracy.

The implementation may expose:
- a hard cap on the grid size,
- solver tolerances,
- a maximum iteration count (for iterative solvers).

---

## 8) Sanity-check reference values (optional)

These are useful for verifying the implementation.

### Solid square of side $a$

A common reference is:

$$
J_\square \approx 0.1406\,a^4
$$

### Solid rectangle $a \times b$ (with $a \ge b$)

Engineering references provide accurate series solutions; a frequently used approximation is:

$$
J \approx \frac{a\,b^3}{3}\left[1 - 0.63\frac{b}{a} + 0.052\left(\frac{b}{a}\right)^5\right]
$$

Use these as approximate targets for mesh convergence testing.

---

## 9) Non-goals (explicit)

This function does **not**:
- compute thin-walled torsion (Bredt–Batho) for open/closed walls,
- detect or process holes via nesting rules,
- merge adjacent polygons into a geometric union,
- fix orientation (CW/CCW),
- apply any “helpful” absolute values or sign corrections.

It is a pure “as supplied” solid-domain Saint-Venant torsion calculator with linear weighted summation.

---



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
