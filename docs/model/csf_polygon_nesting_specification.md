# CSF - Polygon Nesting and Effective Weight Model

This document specifies the behaviour of the containment resolution algorithm in CSF:
how polygons are classified, how effective weights are derived, and what happens in edge cases.
This is a technical reference for contributors, reviewers, and users who need to understand
what the engine does internally.

---

## 1. The Problem: Why Nesting Matters

In CSF, each polygon carries an **absolute weight** `W(z)` - a user-defined scalar field
(e.g. elastic modulus, density) that scales the polygon's area contribution to section properties.

When a polygon is fully contained inside another polygon (nesting), simply summing all
contributions would count the overlapping region twice. CSF resolves this automatically
by computing an **effective weight** for each polygon.

The rule is:

```
W_eff_child(z) = W_abs_child(z) − W_abs_parent(z)
```

where `W_abs_parent(z)` is the absolute weight of the **immediate container** (direct parent)
of the polygon in the containment hierarchy.

Root polygons (no container) have `W_eff = W_abs`.

---

## 2. Containment Hierarchy

CSF resolves, for each polygon, its **immediate container** - the smallest polygon that
fully contains it.

- Only the **direct parent** is considered, not ancestors higher in the hierarchy.
- The hierarchy can be arbitrarily deep (polygon inside polygon inside polygon).
- Containment is evaluated at each integration point along `z`.

### Example: Embedded Steel Bar in Concrete

```
Polygon         W_abs       Container       W_eff
────────────────────────────────────────────────
Concrete        30 000      none (root)     30 000
Steel bar       210 000     Concrete        180 000   (= 210 000 − 30 000)
```

The user declares only the absolute material property of each polygon.
The effective contribution is derived automatically.

---

## 3. Voids and Holes

A void is a polygon declared with `weight = 0.0`.

CSF treats it as a hole: the void's effective contribution is:

```
W_eff_void(z) = 0.0 − W_abs_parent(z) = −W_abs_parent(z)
```

This subtracts the parent material from the region of the hole, regardless of how
`W_parent(z)` varies along `z`. The user does not need to replicate the parent's law
with a negative sign - CSF handles it automatically.

> **This is the key advantage of the nesting model**: a void in a region with a
> spatially varying material weight (e.g. a corroded zone, a graded section) is correctly
> handled without any user-side knowledge of the parent's law.

### Example: Circular Void in a Tapered Pier

```yaml
weight_laws:
  - 'concrete,concrete: 30000 * np.exp(-0.05 * z)'   # degradation along z
  # No law needed for the void - CSF uses the parent's law automatically
```

```
At z = 10:  W_parent = 30000 * exp(-0.5) ≈ 18 197
            W_eff_void = 0 − 18 197 = −18 197   ✓ correct subtraction
```

---

## 4. Edge Case: Annular Polygon with an Island

Consider a **donut-shaped polygon** (annular section, e.g. hollow concrete ring)
with an **isolated polygon** (island) located inside the hole - not touching the
donut material, floating in the void.

```
┌─────────────────────────┐
│        Concrete         │
│   ┌─────────────┐       │
│   │    Hole     │  ●    │  ← Island (steel insert)
│   └─────────────┘       │
└─────────────────────────┘
```

**Question:** what is the containment parent of the island?

A naive point-in-polygon test would classify the island as being *inside the donut*,
because it lies inside its outer boundary. This is **topologically wrong** - the island
is inside the hole, not inside the material.

**CSF's answer:** the island inherits the **same parent as the donut**.

The algorithm distinguishes "inside the material" from "inside the hole of the material"
by resolving the full polygon topology, not just the bounding boundary.

```
Polygon         W_abs       Container           W_eff
──────────────────────────────────────────────────────────
Donut outer     30 000      none (root)         30 000
Donut hole      0           Donut outer         −30 000
Island          210 000     none (root)         210 000   ← same level as donut
```

> **Consequence:** if the parent of the donut is not `root` but another polygon,
> the island's parent follows accordingly - it is always the immediate container
> of the donut, not the donut itself.

---

## 5. Edge Case: Partial Overlap Between Polygons

Partial overlap - two polygons sharing a region without one fully containing the other -
is not a supported modelling pattern. CSF cannot infer intent from geometry alone,
and the result would be physically ambiguous.

**CSF's behaviour:** CSF issues a **WARNING** when two polygons are detected as
**perfectly overlapping** (identical geometry). Partial overlaps are not automatically
detected - they are the user's responsibility.

The user is expected to verify section topology using **CSF's graphical output** before
running any analysis. Visual inspection of the rendered section is the primary tool
for catching unintended overlaps.

```
⚠️  WARNING: Polygons 'web' and 'flange' are perfectly overlapping.
    Verify your section geometry.
```

> Partial overlaps that go undetected will produce incorrect section properties
> without any error or warning. Always inspect the graphical output.

---

## 6. Summary Table

| Configuration | How CSF resolves it | User action required |
|---|---|---|
| Full containment (nesting) | Automatic: `W_eff = W_abs − W_parent` | None |
| Void / hole | Automatic: `W_eff = 0 − W_parent(z)` | Declare `weight = 0.0` |
| Island inside a hole | Assigned to parent of annular polygon | None |
| Perfect overlap | WARNING issued | Verify geometry |
| Partial overlap | Not detected - user responsibility | Inspect graphical output |
| Root polygon (no container) | `W_eff = W_abs` | None |

---

## 7. Code Examples

### 7.1 Reinforced Concrete Section (Python API)

```python
from csf import Polygon, Pt, Section, ContinuousSectionField

E_concrete = 30_000  # MPa
E_steel    = 210_000

# Concrete outer rectangle
concrete = Polygon(
    vertices=(Pt(-0.25, -0.5), Pt(0.25, -0.5),
              Pt(0.25,  0.5), Pt(-0.25,  0.5)),
    weight=E_concrete,
    name="concrete",
)

# Steel bar - fully inside concrete; no need to subtract concrete manually
bar = Polygon(
    vertices=(Pt(-0.02, -0.02), Pt(0.02, -0.02),
              Pt(0.02,  0.02), Pt(-0.02,  0.02)),
    weight=E_steel,
    name="steel_bar",
)

s0 = Section(polygons=(concrete, bar), z=0.0)
s1 = Section(polygons=(concrete, bar), z=10.0)

sf = ContinuousSectionField(section0=s0, section1=s1)

# Optional: apply a degradation law to concrete only
sf.set_weight_laws([
    "concrete,concrete : E_concrete * np.exp(-0.03 * z)",
])
# The steel bar's effective weight will automatically account
# for the varying concrete weight at each z.
```

### 7.2 Void with Spatially Varying Parent (YAML)

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        concrete:
          weight: 30000.0
          vertices:
            - [-0.5, -0.5]
            - [ 0.5, -0.5]
            - [ 0.5,  0.5]
            - [-0.5,  0.5]
        hole:
          weight: 0.0          # void - no law needed
          vertices:
            - [-0.1, -0.1]
            - [ 0.1, -0.1]
            - [ 0.1,  0.1]
            - [-0.1,  0.1]

    S1:
      z: 15.0
      polygons:
        concrete:
          weight: 30000.0
          vertices:
            - [-0.5, -0.5]
            - [ 0.5, -0.5]
            - [ 0.5,  0.5]
            - [-0.5,  0.5]
        hole:
          weight: 0.0
          vertices:
            - [-0.1, -0.1]
            - [ 0.1, -0.1]
            - [ 0.1,  0.1]
            - [-0.1,  0.1]

  weight_laws:
    - 'concrete,concrete: 30000 * (1 - 0.4 * np.exp(-((z - 5.0)**2) / (2 * (2.0**2))))'
    # hole follows parent automatically - no entry needed
```

---

## 8. Design Rationale

The nesting model was chosen to place the algorithmic complexity inside CSF rather than
on the user. The alternative - requiring explicit declaration of holes and subtractive
contributions, as in tools like `sectionproperties` - is correct but forces the user to
replicate the parent's weight law with the opposite sign.

This becomes unmanageable when the parent law is spatially varying (corrosion profile,
graded material, experimental data via `E_lookup`). A void would require the user to
track and mirror a law they did not write.

CSF absorbs this complexity internally. The cost is a non-trivial containment algorithm;
the benefit is a model where the user thinks in terms of absolute material properties,
not net contributions.

---

## 9. Known Limitations

- Only the **immediate parent** is used for effective weight calculation.
  Grand-parent contributions are not propagated directly - they are captured through
  the chain of effective weights at each level.
- Partial overlaps are handled by creation-order priority and flagged as warnings.
  They are not considered a supported modelling pattern.
- Containment is resolved geometrically at each `z` station. For heavily tapered
  sections where containment relationships change along `z`, behaviour should be
  verified explicitly.
