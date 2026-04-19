# Roark-based torsional indicator in CSF

## Overview

`compute_saint_venant_Jv2(poly_input, verbose=False)` returns two quantities:

- `J_s_vroark`
- `J_s_vroark_fidelity`

These two outputs must be read separately.

### `J_s_vroark`

`J_s_vroark` is a **geometric Roark-like torsional indicator** obtained by mapping the current section to an equivalent solid rectangle and then applying the standard Roark rectangle formula.

It is **not** an exact Saint-Venant torsional constant.
It is a low-cost geometric indicator that is meaningful only when the section is still sufficiently rectangle-like.

### `J_s_vroark_fidelity`

`J_s_vroark_fidelity` is a **geometric reliability indicator**.
Its role is not to compute torsion directly, but to tell whether the rectangular Roark mapping remains geometrically credible.

---

## Current Roark-based formulation

The current logic is:

1. Build the geometric reference section from the raw polygons.
2. Compute a Roark reference value `J_ref` on the geometric section only.
3. Compute the homogenized weighted area:

   `A_weighted = sum_i(weight_i * A_i)`

4. Apply the global area correction:

   `w_roark = A_weighted / A_geom`

   `J_s_vroark = w_roark * J_ref`

This formulation has one important advantage:

- it preserves the correct linear scaling with `weight` in compact rectangular cases
- it preserves invariance under equivalent geometric splits of the same rectangle

This is why it works well for:

- single compact rectangles
- uniformly weighted compact rectangles
- split rectangles that still reconstruct the same global filled rectangle

---

## Why this is only "Roark-like"

The method is called **Roark-like** because the Roark part is real, but it is not applied to the real section directly.

The actual sequence is:

1. take the full raw geometric section
2. replace it with an equivalent solid rectangle
3. apply the Roark solid-rectangle torsion formula to that equivalent rectangle
4. scale the result globally by `A_weighted / A_geom`

So the method is genuinely Roark-based in its core:

- it uses the standard Roark rectangle formula
- it keeps the idea of a low-cost closed-form rectangular surrogate
- it derives the torsional indicator from a rectangle defined by geometric equivalence

But it is **not** Roark on the real section, because:

- the real section is generally not a solid rectangle
- the rectangle is only an equivalent surrogate built from `A_geom` and `i_min_geom`
- the polygon weights do not enter that equivalent geometry directly
- the weights are introduced only afterward through the global factor `A_weighted / A_geom`

This distinction is exactly why the method works on true rectangle-like sections and fails on shapes that are no longer credible rectangular surrogates.

In other words:

- the **Roark formula itself** is the same rectangle formula
- the **section to which it is applied** is not the real section, but an equivalent one

That is the precise meaning of **Roark-like** in this context.

---

## What problem appears

The problem is not visible on true rectangle-like cases.
It appears when the geometry is no longer a filled rectangle, even if the Roark mapping remains formally computable.

Typical problematic families are:

- `T`
- `H`
- `I`
- any arrangement of boxes leaving empty space inside the minimum bounding rectangle
- any remote polygon with very small weight that still deforms the global rectangle used by Roark

In these cases, the equivalent-rectangle mapping can still produce a number, but that number is no longer trustworthy.

---

## Why this happens

The current `J_s_vroark` uses:

- the **full geometric reference section** to define `J_ref`
- only a **global linear area scaling** to account for weights

This is acceptable for compact rectangle-like sections, but it becomes problematic for shapes such as `T`, `H`, or `I`.

### Example of the failure mode

A remote box with very small weight can still enlarge or distort the geometric reference rectangle used by Roark.
Then:

- `J_ref` becomes large because the reference rectangle becomes large
- the final scaling `A_weighted / A_geom` is only a weak global correction
- the final `J_s_vroark` remains strongly overestimated

This is a structural limitation of the method.
It is not a numerical bug.

---

## Why this should not be "fixed" inside `J_s_vroark`

A stronger correction than `A_weighted / A_geom` would need to answer this question:

> how much does each polygon contribute torsionally to the global equivalent rectangle?

That quantity is not available from pure area information alone.
A rigorous answer would depend on more than:

- area
- position
- shape
- connectivity

At that point the method would stop being a simple geometric Roark indicator and would move toward a richer torsion model.
That is outside the intended scope here.

Therefore, the correct decision is:

- keep `J_s_vroark` as a simple geometric Roark-like indicator
- do **not** try to repair it with ad hoc pseudo-physical corrections
- make the limitation explicit through `J_s_vroark_fidelity`

---

## The role of fidelity

The fidelity must answer this question:

> is this geometry still sufficiently rectangle-like for a Roark rectangle mapping to be meaningful?

So fidelity is not a torsion value.
It is a validity check for the simplified Roark interpretation.

---

## Base fidelity already in use

The base fidelity is built from a weighted bounding box:

- `weight` is **not** used here
- `weightabs` is used only to contract polygon bounds toward the global geometric centroid
- the base fidelity is then:

  `fidelity_base = A_weighted / A_box_eff`

where `A_box_eff` is the area of the weighted effective bounding box.

This works well for:

- compact squares
- compact rectangles
- equivalent rectangular splits
- mildly perturbed near-rectangular cases

So the base fidelity is useful and should not be discarded.

---

## What the base fidelity misses

The base fidelity alone can remain too high when the geometry is not actually a filled rectangle.

This is exactly what happens in cases such as:

- `T`
- `H`
- `I`
- rectangle-like stacks with one remote box enlarged or shifted

In these cases the section may still have a weighted box that looks compact enough, while the actual raw geometry leaves empty regions inside its minimum container.

That is the key point:

- the base fidelity measures **compactness of a weighted box**
- but it does **not** guarantee **full rectangular fill of the raw geometry**

---

## Geometric rectangularity veto

To solve this, an additional pure-geometry check is introduced.

### Principle

Ignore weights completely.
Take the raw polygons and build their minimum global container.
Then compare:

- `A_cont` = area of the minimum global container
- `A_geom` = total geometric area of the raw polygons

In the considered CSF workflow, overlap is not expected, so `A_geom` is the geometric occupied area.

Define:

- `gap_area  = A_cont - A_geom`
- `gap_ratio = gap_area / A_cont`

### Interpretation

- `gap_ratio = 0` means the geometry fully fills its minimum container
- `gap_ratio > 0` means the geometry leaves voids inside that container

If voids exist, the section is not a true filled rectangle-like domain.
Therefore a Roark rectangle interpretation is not reliable.

---

## Final fidelity logic

The final logic is:

1. Compute `fidelity_base` from the weighted box.
2. If `fidelity_base` is not high, keep it as is.
3. If `fidelity_base` is suspiciously high, perform a rectangular-fill veto using the raw geometry.

Operationally:

- suspicious zone: `fidelity_base > 0.9`
- tolerated geometric gap: `gap_ratio <= 0.10`
- if `gap_ratio > 0.10`, then set:

  `J_s_vroark_fidelity = 0`

This means:

- the Roark value may still be formally computable
- but it is explicitly flagged as not trustworthy for that geometry

---

## Why this is the right compromise

This approach keeps the method honest.

It does **not** pretend that a Roark rectangle approximation can represent shapes that are clearly not filled rectangles.
At the same time, it does **not** destroy the good behavior on compact rectangular cases.

So the split is clean:

### `J_s_vroark`

A cheap geometric Roark-like indicator.
Useful only for genuinely rectangle-like sections.

### `J_s_vroark_fidelity`

A geometric validity indicator.
It must collapse when the raw geometry no longer fills a rectangle-like domain.

---

## Practical conclusion

The practical conclusion is simple:

- `J_s_vroark` should be interpreted only for **true rectangle-like geometries**
- `T`, `H`, `I`, and other void-creating arrangements are outside its reliable scope
- for those cases, the correct behavior is **not** to invent stronger Roark corrections
- the correct behavior is to keep the Roark number separate and let the fidelity drop to zero

In short:

> `J_s_vroark` serves real rectangle-like domains.
> `J_s_vroark_fidelity` must explicitly reject geometries that do not fill their own rectangular container.

---

## Minimal implementation idea

The additional helper is conceptually:

```python

def _container_gap_metrics(polys: Any, a_geom_total: float) -> Tuple[float, float, float]:
    """
    Returns (gap_area, gap_ratio, a_cont), where:
    - gap_area  = A_cont - A_geom
    - gap_ratio = gap_area / A_cont
    - a_cont    = minimum global container area
    """
```

And the final veto logic is:

```python
if fid > 0.9 and gap_ratio > 0.10:
    fid = 0.0
```

This keeps the modification local, geometric, and fully separated from the Roark calculation itself.
