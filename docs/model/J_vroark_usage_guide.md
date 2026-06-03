# Roark-based torsional indicator - engineering note

## Purpose

The Roark-based torsional indicator provides a fast engineering read-out for compact, approximately rectangular cross-sections. It is intended as a diagnostic quantity, not as a general Saint-Venant torsional solution.

The method maps the sampled section to an equivalent solid rectangle and evaluates a Roark-type torsional approximation on that rectangle. The result is reported together with a fidelity indicator that qualifies whether the rectangular mapping is meaningful for the sampled geometry.

The two reported quantities are:

```text
J_s_vroark
J_s_vroark_fidelity
```

`J_s_vroark` is the Roark-equivalent torsional read-out.
`J_s_vroark_fidelity` indicates whether the sampled section is sufficiently compact and rectangle-like for that read-out to be used.

They must be interpreted together.

---

## Construction of `J_s_vroark`

The method does not solve the Saint-Venant torsion problem on the actual cross-section.

Instead, it constructs an equivalent solid rectangle from two geometric ingredients:

1. the net occupied geometric area of the sampled section;
2. the aspect ratio of the minimum-area geometric bounding box.

The minimum-area bounding box is computed from the sampled polygon geometry only. Polygon weights and shear weights do not affect the bounding-box orientation or aspect ratio.

The net geometric area is computed by subtracting direct inner polygons from their parent polygons. Polygons with zero shear participation are excluded from the torsional indicator.

The equivalent rectangle is then built as follows:

```text
equivalent rectangle aspect ratio = geometric bounding-box aspect ratio
equivalent rectangle area         = A_geom_net
```

where `A_geom_net` is the net occupied geometric area used by the torsional indicator.

A Roark-type torsional approximation for a solid rectangle is evaluated on this equivalent rectangle.

The result is then multiplied by a global shear-weight factor:

```text
w_total = A_shear_weighted / A_geom_net
```

where:

```text
A_geom_net
```

is the net occupied geometric area, and

```text
A_shear_weighted
```

is the same net occupied area weighted by the polygon shear weights.

The final reported quantity is therefore:

```text
J_s_vroark = w_total * J_roark_equivalent_rectangle
```

This scalar shear-weight correction accounts only for the global amount of shear-participating area. It does not solve the torsional warping problem associated with non-uniform shear participation across the section.

---

## Fidelity indicator

`J_s_vroark_fidelity` answers one specific question:

```text
Is the sampled section sufficiently close to a compact filled rectangle for the Roark-equivalent read-out to be meaningful?
```

It is not an error estimate for the Saint-Venant torsional constant. It is an admissibility indicator for the equivalent-rectangle approximation.

The fidelity is based on three checks.

---

### 1. Geometric fill ratio

The base fidelity compares the net occupied geometric area with the area of the minimum-area geometric bounding box.

A compact filled rectangle gives a value close to one. A sparse, thin-walled, flange-web, or void-rich section gives a lower value because only part of its enclosing rectangle is actually occupied by material.

This check is purely geometric. It is based on the filledness of the sampled shape inside its minimum-area bounding box.

---

### 2. Isoperimetric veto

Near-circular outer geometries are not treated as Roark-compatible rectangular sections.

If the outer polygon is sufficiently close to circular according to the isoperimetric ratio, both the Roark-equivalent value and the fidelity are set to zero.

This prevents circular or near-circular sections from being reported through a rectangular Roark approximation.

---

### 3. Shear-weight dispersion penalty

The global multiplier `w_total` is a scalar correction based on the total shear-weighted area. It cannot fully represent the nonlinear effect of strongly non-uniform shear participation across the section.

For this reason, the fidelity is reduced when the positive polygon shear weights vary significantly across the sampled section.

Uniform or nearly uniform shear weights produce no significant penalty. Strongly dispersed shear weights reduce the final fidelity. The final value is clamped between zero and one.

---

## Interpretation

`J_s_vroark` should not be interpreted without checking `J_s_vroark_fidelity`.

A practical reading is:

* fidelity close to `1.0`: the section is compact and rectangle-like; the Roark-equivalent value can be used as a reasonable engineering estimate;
* fidelity between `0.7` and `0.9`: borderline case; the value may still be useful, but visible approximation error should be expected;
* fidelity below `0.7`: the section is not sufficiently rectangle-like; `J_s_vroark` should be discarded.

A conservative automated rule is:

```text
if J_s_vroark_fidelity < 0.7:
    discard J_s_vroark
```

---

## Scope

The Roark-based torsional indicator is intended for compact solid rectangular or near-rectangular cross-sections, possibly with mild shear-weight non-uniformity.

It should not be used as the primary torsion estimator for:

* T sections;
* H or I sections;
* channel sections;
* thin-walled sections;
* hollow or void-rich sections;
* near-circular sections;
* sections with strong shear-weight non-uniformity.

For closed thin-walled cells, open thin walls, or general sections requiring warping-based torsion, a dedicated torsional method should be used instead. In CSF this means using the appropriate cell, wall, or external finite-element torsion workflow where applicable.

Accordingly, `J_s_vroark` is a fast equivalent torsional diagnostic, while `J_s_vroark_fidelity` indicates whether that diagnostic is admissible for the sampled section.
