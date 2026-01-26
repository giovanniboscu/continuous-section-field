# 🛠 ContinuousSectionField (CSF) — Custom Weight Laws & Effective Weights (User Guide)

This guide explains how CSF evaluates the scalar field **`weight`** (also written as **W(z)**) along a member, and how **nested polygons** (materials, voids, inserts) are handled **automatically** using a *smallest-container* rule.

It also documents how **custom weight laws** override the default interpolation, and clarifies a critical past mistake: **a void is not always `-1`**.

---

## 1) What are we talking about?

CSF models a member by interpolating polygonal cross-sections along the axis *z*.
Each polygon represents a region of the section (material, void, reinforcement, liner, etc.).

Every polygon carries a scalar **`weight` = W(z)**. At each station *z*, CSF uses the weights to compute **weighted section integrals** (area, inertia, centroid, …).

---

## 2) What is `weight` (W)?

In CSF, `weight` is a **scalar field attached to each polygon**. CSF uses it as a multiplier inside area integrals:

```math
A^*(z) = \sum_i w_i(z)\,A_i(z), \qquad
I^*(z) = \sum_i w_i(z)\,I_i(z)
```

### Two common conventions

You can use either convention; CSF is unit-system agnostic as long as you stay consistent.

**Convention A — Ratio (dimensionless)**  
```math
w = E/E_{ref}
```
- Choose a reference modulus \(E_{ref}\).
- Softer materials: \(0 < w < 1\); stiffer: \(w > 1\).

**Convention B — Physical units (e.g., Young’s modulus)**  
```math
w = E
```
- Use real numbers (MPa, Pa, …).
- Then integrals become stiffness-like quantities (e.g., \(\int E\,dA\)).

---

## 3) The key point: polygons can be nested (overlap)

A typical composite section contains nested regions:

- concrete (outer shell)
- steel liner or reinforcement (inside concrete)
- voids (holes / inner cavity)

In these cases, polygons overlap **by design**. If you simply summed *absolute* weights of all polygons that cover a point, you would **double count**.

CSF therefore uses an **effective weight** (delta-weight) computed automatically.

---

## 4) Automatic “smallest-container” rule (no guesses, no heuristics)

For each polygon \(P_i\) CSF finds its **parent polygon** \(P_{parent}\):

- The parent is the **smallest** polygon (by area) that **geometrically contains** \(P_i\).
- Containment is evaluated on the internal reference topology (typically `S0`).
- If no container exists, the polygon has **no parent**.

This is intentionally simple:

> **CSF only cares about geometric containment (smallest container).  
> It does not “interpret” materials, holes, or meanings.**

---

## 5) Effective weight definition (the “delta”)

Let \(w_i(z)\) be the **absolute** weight of polygon \(i\) at station \(z\), computed either by:
- default interpolation, or
- a custom law.

Then CSF defines an **effective weight**:

```math
w^{eff}_i(z) =
\begin{cases}
w_i(z) - w_{parent}(z) & \text{if polygon } i \text{ has a parent} \\
w_i(z) & \text{if polygon } i \text{ has no parent}
\end{cases}
```

### Why this works (important)

At a point located inside a nested region, the total contribution becomes:

- parent contributes \(w_{parent}\)
- child contributes \(w_i - w_{parent}\)

So the sum is:
```math
w_{parent} + (w_i - w_{parent}) = w_i
```

Meaning: the “most specific” region wins, **without double counting**.

---

## 6) Correct void logic 

A void must remove the stiffness (or property) of the material it is cutting.

With **effective weights**, you should define a void polygon with the **absolute target weight of the void** (usually 0), and CSF will compute the correct subtraction automatically.

### ✅ Correct rule
- If the void means “no material”, then **absolute weight** of the void region is:
```math
w_{void} = 0
```
- CSF computes:
```math
w^{eff}_{void} = 0 - w_{parent}
```

---

## 7) Default behavior: linear interpolation

If no custom law is provided for a polygon, CSF interpolates its absolute weight between start and end:

```math
w(z) = w_0 + (w_1 - w_0)\,\frac{z}{L}
```

- \(w_0\): weight at `S0`
- \(w_1\): weight at `S1`
- \(L\): member length

After this, CSF applies the **same effective-weight rule** (delta vs parent) described above.

---

## 8) Custom weight laws: identical procedure (absolute first, delta after)

A custom law **replaces the default interpolation** for that polygon, producing **absolute** \(w_i(z)\).

Then **the effective weight is computed exactly the same way**:

1) evaluate \(w_i(z)\) (custom law or default interpolation)  
2) find the parent (smallest container)  
3) compute \(w^{eff}_i(z) = w_i(z) - w_{parent}(z)\) (if parent exists)

> The delta step is never skipped: it is applied to *whatever* values exist at station \(z\).

---

## 9) Polygon identification and mapping (naming and order)

CSF connects polygons from `S0` to `S1` by **creation order** (index alignment):
- the first polygon in `S0` matches the first in `S1`, etc.

Names are strongly recommended for readability and for authoring laws.

---

## 10) Examples (multiple, explicit)

### Example A — Single material with a hole (rectangle + inner void)

**Goal:** a plate with a rectangular hole.  
Use absolute weights:
- plate material: `w = 1`
- void: `w = 0`

CSF will compute the void delta automatically as `0 - 1 = -1`.

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        solid:
          weight: 1.0
          vertices:
            - [-0.2, -0.2]
            - [ 0.2, -0.2]
            - [ 0.2,  0.2]
            - [-0.2,  0.2]
        hole:
          weight: 0.0
          vertices:
            - [-0.1, -0.05]
            - [ 0.1, -0.05]
            - [ 0.1,  0.05]
            - [-0.1,  0.05]
    S1:
      z: 10.0
      polygons:
        solid:
          weight: 1.0
          vertices:
            - [-0.2, -0.2]
            - [ 0.2, -0.2]
            - [ 0.2,  0.2]
            - [-0.2,  0.2]
        hole:
          weight: 0.0
          vertices:
            - [-0.1, -0.05]
            - [ 0.1, -0.05]
            - [ 0.1,  0.05]
            - [-0.1,  0.05]
```

**Effective weights at any z**
- `solid`: parent=None → \(w^{eff}=1\)
- `hole`: parent=solid → \(w^{eff}=0-1=-1\)

---

### Example B — Material substitution (steel insert inside concrete)

**Goal:** concrete region is the baseline, steel polygon upgrades the stiffness inside its footprint.

Let’s use Convention A (ratio), with concrete as reference:
- concrete: \(w=1\)
- steel: \(w=7\)  (example ratio)

Define absolute weights:
- `concrete`: 1
- `steel`: 7

CSF produces:
- `steel_eff = 7 - 1 = 6`
So inside steel: total is \(1 + 6 = 7\).

---

### Example C — Concentric circles (tower: concrete shell + steel liner + inner void)

This mirrors a common tower concept (concrete body + steel liner + hollow core).
Use absolute target weights:
- concrete shell: \(w_{conc} = 1\)
- steel liner: \(w_{steel} = 7\)
- inner void: \(w_{void} = 0\)

At station \(z\):
- concrete has no parent → \(w^{eff}=1\)
- steel parent is concrete → \(w^{eff}=7-1=6\)
- void parent is steel (smallest container) → \(w^{eff}=0-7=-7\)

So the core is truly empty.

**Important:** You do NOT need to manually set `-1` or `-7` for the void.
You set the void absolute weight to `0`, and CSF does the subtraction.

---

### Example D — Your three-polygon test (pol1 contains pol2 and pol3)

Given:
- `pol1` is outer (parent=None)
- `pol2` and `pol3` are inside `pol1` (parent=pol1)

If you set absolute weights:
- `pol1 = 11`
- `pol2 = 11` (same material as parent → it should “disappear” as delta)
- `pol3 = 3`  (different material)

Then:
- \(w^{eff}_{pol1} = 11\)
- \(w^{eff}_{pol2} = 11 - 11 = 0\)
- \(w^{eff}_{pol3} = 3 - 11 = -8\)

This matches the debug output you observed.

---

## 11) Custom law syntax (overview)

Custom laws override the default interpolation for a polygon.

**Format**
```text
"StartPolygonName, EndPolygonName : <Python expression>"
```

Example:
```python
section_field.set_weight_laws([
    "concrete,concrete : w0",                 # constant
    "steel,steel : w0 + (w1-w0)*(z/L)**2",    # quadratic
    "hole,hole : 0.0",                        # always void
])
```

**Variables typically available**
- `z`, `L`
- `w0`, `w1`
- `np` (NumPy)

After the law is evaluated, CSF still applies:
```math
w^{eff}_i(z) = w_i(z) - w_{parent}(z)
```

---

## 12) Common pitfalls (quick)

1) **Writing voids as negative absolute weights**
   - If CSF is computing effective weights, define void absolute weight as `0`.
   - Do not write `-1` unless you are explicitly bypassing the delta approach.

2) **Indexing mistakes in `weight_laws`**
   - Prefer naming-based laws.
   - If using index-based storage, ensure the indexing convention matches the implementation.

3) **Parent not found**
   - The “parent” is purely geometric containment.
   - If a polygon is not entirely inside another (touching/outside), it has no parent.

4) **Topology changes along z**
   - Parent detection assumes containment relations remain valid along the field.
   - If containment changes with z, you must base containment on the interpolated polygon, not only `S0`.

---

## 13) One-line summary (what CSF guarantees)

At each station \(z\), CSF ensures that nested regions behave correctly by:

- evaluating **absolute** \(w_i(z)\) (custom or default),
- finding the **smallest containing parent** polygon,
- converting to **effective** weights using:
```math
w^{eff}_i(z) = w_i(z) - w_{parent}(z)
```
- so the final field equals the intended absolute weight inside each region, without double counting.
# 🛠 ContinuousSectionField (CSF) — Custom Weight Laws & Effective Weights (User Guide)

This guide explains how CSF evaluates the scalar field **`weight`** (also written as **W(z)**) along a member, and how **nested polygons** (materials, rings, liners, holes, inserts) are handled **automatically** using a *smallest-container* rule.

The key idea is simple:

> You assign an **absolute target weight** to each polygon (including holes as **0**).  
> CSF automatically derives the **effective (delta) weights** needed for correct weighted section integrals.

---

## 1) What are we talking about?

CSF models a member by interpolating polygonal cross-sections along the axis *z*.
Each polygon represents a region of the section: a material domain, a liner, a reinforcement zone, a ring, or a void.

Every polygon carries a scalar **`weight` = W(z)**. At each station *z*, CSF uses the weights to compute **weighted section integrals** (area, inertia, centroid, …) that represent an equivalent homogenized section.

---

## 2) What is `weight` (W)?

In CSF, `weight` is a **scalar field attached to each polygon**. CSF uses it as a multiplier inside area integrals:

```math
A^*(z) = \sum_i w^{eff}_i(z)\,A_i(z), \qquad
I^*(z) = \sum_i w^{eff}_i(z)\,I_i(z)
```

> Note: the integrals use **effective weights** \(w^{eff}\) (explained below), not necessarily the raw values you write in YAML.

### Two common conventions

You can use either convention; CSF is unit-system agnostic as long as you stay consistent.

**Convention A — Ratio (dimensionless)**  
```math
w = E/E_{ref}
```
- Choose a reference modulus \(E_{ref}\).
- Softer materials: \(0 < w < 1\); stiffer: \(w > 1\).

**Convention B — Physical units (e.g., Young’s modulus)**  
```math
w = E
```
- Use real numbers (MPa, Pa, …).
- Then integrals become stiffness-like quantities (e.g., \(\int E\,dA\)).

---

## 3) Overlap is normal: think “onion layers”

Composite sections are typically defined as **nested polygons** (overlapping regions):

- an outer concrete ring
- an inner steel liner ring
- another inner concrete region (e.g., grout or a different concrete grade)
- a final inner void (the hollow core)

This is the “onion” model: each polygon is a layer inside the previous one.

If you simply summed raw weights in overlapped regions you would **double count**.  
CSF solves this by converting your absolute weights into **delta weights** automatically.

---

## 4) Automatic mapping: the smallest-container rule

For each polygon \(P_i\) CSF finds its **parent polygon** \(P_{parent}\):

- The parent is the **smallest** polygon (by area) that **geometrically contains** \(P_i\).
- Containment is evaluated on the internal reference topology (typically `S0`).
- If no container exists, the polygon has **no parent**.

This is intentionally minimal:

> CSF uses only geometry: **containment and “smallest container”**.  
> You do not need to declare “this is a hole”, “this is steel”, “this is concrete”, etc.

---

## 5) You provide absolute weights — CSF builds effective weights

### 5.1 Absolute weights (what you write)

For each polygon, you define an **absolute target weight** \(w_i(z)\):

- by default: linear interpolation between `S0` and `S1`
- or by a custom law (Section 9)

This value represents “what the region should be” in that polygon footprint.

### 5.2 Effective weights (what CSF integrates)

CSF converts absolute weights into **effective weights** (delta weights) as:

```math
w^{eff}_i(z) =
\begin{cases}
w_i(z) - w_{parent}(z) & \text{if polygon } i \text{ has a parent} \\
w_i(z) & \text{if polygon } i \text{ has no parent}
\end{cases}
```

### 5.3 Why this works

At a point inside a nested region:

- parent contributes \(w_{parent}\)
- child contributes \(w_i - w_{parent}\)

So the sum becomes:
```math
w_{parent} + (w_i - w_{parent}) = w_i
```

Meaning:
- you get the intended **absolute** field \(w_i\),
- without double counting,
- with a purely geometric rule.

---

## 6) Holes and voids: set `weight = 0` (CSF does the subtraction)

A void means “no material” (or “no contribution”) in that region.  
Therefore, its absolute weight is naturally:

```math
w_{void}(z) = 0
```

If the void polygon sits inside a material polygon with absolute weight \(w_{parent}\), CSF automatically computes:

```math
w^{eff}_{void}(z) = 0 - w_{parent}(z)
```

So **you do not need to compute negative values yourself**.  
You simply write `weight: 0` for the hole/void polygon.

> In the equivalent integrals you will often see **negative contributions** for void polygons.  
> This is expected: it is the correct delta needed to remove the parent material contribution in that region.

---

## 7) Default behavior: linear interpolation (when no custom law exists)

If no custom law is provided for a polygon, CSF interpolates its **absolute** weight between start and end:

```math
w(z) = w_0 + (w_1 - w_0)\,\frac{z}{L}
```

Then CSF applies the **same delta rule** to obtain \(w^{eff}\).

---

## 8) Polygon identification and mapping (naming and order)

CSF connects polygons from `S0` to `S1` by **creation order** (index alignment):
- the first polygon in `S0` matches the first in `S1`, etc.

Names are strongly recommended for clarity and for authoring laws.

---

## 9) Custom weight laws: same procedure at station z

A custom law **replaces the default interpolation** for that polygon, producing the **absolute** value \(w_i(z)\).

Then CSF applies the *same* parent/child delta logic:

1) evaluate absolute \(w_i(z)\) (custom law or default)  
2) find parent by smallest-container  
3) compute effective \(w^{eff}_i(z)\)

> The delta step is always applied. Custom laws do not change the nesting logic.

---

## 10) Examples (multiple, explicit)

### Example A — Single material with a hole (rectangle + inner void)

Absolute weights:
- solid material: `w = 1`
- void: `w = 0`

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        solid:
          weight: 1.0
          vertices:
            - [-0.2, -0.2]
            - [ 0.2, -0.2]
            - [ 0.2,  0.2]
            - [-0.2,  0.2]
        hole:
          weight: 0.0
          vertices:
            - [-0.1, -0.05]
            - [ 0.1, -0.05]
            - [ 0.1,  0.05]
            - [-0.1,  0.05]
    S1:
      z: 10.0
      polygons:
        solid:
          weight: 1.0
          vertices:
            - [-0.2, -0.2]
            - [ 0.2, -0.2]
            - [ 0.2,  0.2]
            - [-0.2,  0.2]
        hole:
          weight: 0.0
          vertices:
            - [-0.1, -0.05]
            - [ 0.1, -0.05]
            - [ 0.1,  0.05]
            - [-0.1,  0.05]
```

Effective weights at any z:
- `solid`: parent=None → \(w^{eff}=1\)
- `hole`: parent=solid → \(w^{eff}=0-1=-1\)

You never typed a negative number for the hole; CSF computed it.

---

### Example B — Material substitution (steel insert inside concrete)

Use Convention A (ratio), concrete as reference:
- concrete: \(w=1\)
- steel: \(w=7\)  (example ratio)

Absolute:
- `concrete = 1`
- `steel = 7`

Effective:
- `steel_eff = 7 - 1 = 6`

Inside steel footprint: \(1 + 6 = 7\).

---

### Example C — Concentric circles (tower-style “onion” section)

This is a common tower concept:

1) outer concrete ring  
2) inner steel ring (liner / reinforcement ring)  
3) inner concrete ring (another grade or grout)  
4) final inner void (hollow core)

Think “onion layers”: each one sits inside the previous one.

#### Target absolute weights (example)
- outer concrete: \(w_{c1} = 1\)
- steel ring: \(w_s = 7\)
- inner concrete: \(w_{c2} = 1\) (could differ if needed)
- void: \(w_v = 0\)

Then CSF computes effective deltas:
- outer concrete (no parent): \(w^{eff}=1\)
- steel (parent is outer concrete): \(w^{eff}=7-1=6\)
- inner concrete (parent is steel): \(w^{eff}=1-7=-6\)
- void (parent is inner concrete): \(w^{eff}=0-1=-1\)

Interpretation:
- between outer concrete and steel ring → stiffness is 7
- between steel and inner concrete → stiffness returns to 1
- inside the core → 0

You only described “what each region should be” (absolute weights).  
CSF derived all needed negative deltas automatically.

---

### Example D — Your three-polygon test (pol1 contains pol2 and pol3)

Given containment:
- `pol1` is outer (parent=None)
- `pol2` and `pol3` are inside `pol1` (parent=pol1)

If absolute weights are:
- `pol1 = 11`
- `pol2 = 11`
- `pol3 = 3`

Then:
- \(w^{eff}_{pol1} = 11\)
- \(w^{eff}_{pol2} = 11 - 11 = 0\)
- \(w^{eff}_{pol3} = 3 - 11 = -8\)

---

## 11) Custom law syntax (overview)

Custom laws override the default interpolation for a polygon.

**Format**
```text
"StartPolygonName, EndPolygonName : <Python expression>"
```

Example:
```python
section_field.set_weight_laws([
    "outer_concrete,outer_concrete : w0",
    "steel_ring,steel_ring : w0 + (w1-w0)*(z/L)**2",
    "inner_concrete,inner_concrete : w0",
    "void,void : 0.0",
])
```

After the law is evaluated, CSF still computes:
```math
w^{eff}_i(z) = w_i(z) - w_{parent}(z)
```

---

## 12) Common pitfalls (quick)

1) **Trying to manually compute subtraction**
   - Do not “pre-subtract” weights in YAML.
   - Write absolute weights (including void as 0). CSF computes deltas.

2) **Parent not found**
   - Parent detection is purely geometric containment.
   - If a polygon is not entirely inside another, it has no parent.

3) **Topology changes along z**
   - Parent detection assumes containment relations remain valid along the field.
   - If containment changes with z, parent detection must be based on interpolated geometry.

---

## 13) One-line summary

At each station \(z\), CSF ensures that nested regions behave correctly by:

- evaluating **absolute** \(w_i(z)\) (custom or default),
- finding the **smallest containing parent** polygon,
- converting to **effective** weights with:
```math
w^{eff}_i(z) = w_i(z) - w_{parent}(z)
```

This yields the intended field inside each region **without double counting**, and automatically produces negative delta contributions where necessary (e.g., holes).
