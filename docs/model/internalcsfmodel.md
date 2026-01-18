# Implementation Notes (CSF): From Mathematical Model to Code

This document connects the **formal mathematical formulation of CSF**
to its **actual implementation choices** in the codebase.
It clarifies where each theoretical concept appears in code,
why certain design decisions were made, and how numerical robustness is enforced.

---

## 1. Single evaluation entry point

### Mathematical model

The section at coordinate z is defined as:

S(z) = { (Pₒ,ₖ(z), wₒ,ₖ(z)) }

where each polygon Pₒ,ₖ(z) is obtained by deterministic vertex interpolation
and each weight wₒ,ₖ(z) is evaluated independently.

### Implementation

In CSF this is realized by a **single public evaluation method**:

```python
section(z: float)
```

This method is the *only* place where section geometry is computed.
All downstream quantities (areas, centroids, inertias, exports)
are derived exclusively from the output of this function.

**Consequence:**  
Discretization (stations, integration points, solver segments)
never modifies the model — it only queries it.

---

## 2. Deterministic vertex interpolation

### Mathematical model

For each vertex:

pₒ,ₖ,ⱼ(z) = (1 − t) · pᶦₒ,ₖ,ⱼ + t · pᶠₒ,ₖ,ⱼ  
with t = z / L

### Implementation

In code, this is implemented directly during polygon construction inside `section(z)`.
Vertices are interpolated **point-by-point**, using fixed index correspondence.
No geometric slicing or intersection is involved.

This guarantees:
- one-to-one vertex correspondence,
- no dependence on curve ordering heuristics,
- reproducible geometry for identical inputs.

---

## 3. Polygon construction and orientation enforcement

### Mathematical model

All polygons are required to have:
- counter-clockwise (CCW) vertex order,
- non-negative geometric area.

Negative areas are not used to model holes.

### Implementation

The `Polygon` constructor performs:

- area computation via the shoelace formula;
- validation that the area is strictly positive;
- rejection of CW or degenerate polygons via exception.

This enforces the invariant:

A(P(z)) > 0   for all evaluated polygons.

---

## 4. Self-intersection detection as a warning condition

### Mathematical model

A polygon exhibits self-intersection if two non-adjacent edges intersect.

This condition does **not** invalidate the section,
but generates a warning.

### Implementation

Inside `section(z)`, every evaluated polygon is checked via:

```python
if polygon_has_self_intersections(poly):
    warnings.warn(..., RuntimeWarning)
```

The predicate:
- tests all non-adjacent edge pairs;
- uses orientation-based segment intersection tests;
- includes proper crossings, touching, and collinear overlap;
- applies a geometry-scaled tolerance `EPS_L`.

The section remains valid and usable after the warning.

---

## 5. Global geometric scale and tolerances

### Mathematical model

All numerical predicates depend on a characteristic length scale S.

### Implementation

During construction of `ContinuousSectionField`:

- a global bounding box is computed from all endpoint polygons;
- the characteristic scale is defined as:

S = max(dx, dy, L, 1)

From this scale, CSF defines:

- `EPS_L`  — linear geometry tolerance;
- `EPS_A`  — area / degeneracy tolerance (∝ S²);
- `EPS_K`  — numerical tolerance for matrix operations.

This ensures robustness across different unit systems and model sizes.

---

## 6. Weights and transformed quantities

### Mathematical model

Transformed section quantities are defined as:

Q_tr(z) = Σₒ Σₖ wₒ,ₖ(z) · Q(Pₒ,ₖ(z))

where Q is linear in area.

### Implementation

In code:

- each polygon carries an associated weight;
- all section properties are computed by linear accumulation;
- negative weights represent subtractive contributions (holes, material replacement).

No boolean geometry is performed.

This mirrors classical transformed-section theory exactly.

---

## 7. Holes and material replacement

### Mathematical model

Holes are modeled via negative weights, not negative geometry.

### Implementation

A polygon representing a void:
- has valid CCW geometry;
- carries a negative weight (e.g. w = −1).

Material replacement (e.g. steel in concrete) is implemented as:

w_eff = w_material − w_base

avoiding double counting while preserving linearity.

---

## 8. Separation of responsibilities

CSF enforces a strict separation:

- **Geometry**: deterministic, index-based, interpolation-driven;
- **Validity**: checked (warnings) but not enforced;
- **Semantics**: entirely user-defined via polygon grouping and weights.

This separation is intentional and central to the CSF design.

---

## 9. Debugging and visualization

Although the model is purely analytical,
CSF optionally generates 3D swept volumes for inspection.

This allows users to:
- visually identify twist or self-intersections;
- correlate warnings with spatial anomalies;
- validate complex models without modifying the core algorithm.

---

## 10. Design summary

- One evaluation function: `section(z)`.
- Deterministic geometry from endpoint correspondence.
- No slicing, no ordering heuristics.
- Validation via warnings, not silent failure.
- Linear, weight-based formulation of section properties.

This concludes the mapping between the CSF mathematical model
and its concrete implementation.
