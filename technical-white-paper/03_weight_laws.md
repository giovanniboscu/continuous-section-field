# Weight Laws and Sectional Homogenization

## Purpose of Weight Laws

In CSF, geometric definition and physical properties are intentionally decoupled.

Geometry defines *where material exists*.  
**Weight laws** define *how that geometry contributes to sectional properties*.

The weight mechanism provides a general and explicit way to introduce:
- material heterogeneity,
- stiffness variation along the member,
- staged or degraded properties,
- embedded components and voids,

without altering the underlying geometric description.

---

## Definition of Weight

Each polygonal region of a section is associated with a scalar weight field
`w_k(z)` where k denotes the polygon index


defined along the longitudinal coordinate`z`.

During sectional property assembly, this scalar multiplies the geometric contribution
of the corresponding polygon.

Formally, a generic sectional quantity \( Q(z) \) is evaluated as:
`Q(z) = sum_k [ w_k(z) * Q_k(z) ]`

where `Q_k(z)` is the purely geometric contribution of polygon ` k `.

The term *weight* is deliberately generic.  
It does not enforce a specific physical interpretation.

---

## Physical Interpretation

The physical meaning of  `w(z)` is entirely **user-defined**, but must remain
**internally consistent** throughout the workflow.

Typical interpretations include:
- ratio of Young’s modulus with respect to a reference material,
- absolute Young’s modulus,
- density multiplier for mass evaluation,
- any scalar field that scales with area integrals.

CSF does not infer or enforce units.  
All consistency checks are the responsibility of the user.

---

## Two Common Modeling Conventions

### Convention A — Dimensionless Homogenization Factor (Recommended)

In this convention, the weight is defined as:
`w(z) = E(z) / E_ref`

where `E_ref` is a chosen reference modulus.

`A*(z) = sum_k [ w_k(z) * A_k(z) ]`
`I*(z) = sum_k [ w_k(z) * I_k(z) ]`

`E_ref * A*(z)`
`E_ref * I*(z)`


This convention:
- preserves numerical stability,
- keeps geometric quantities dimensionally clean,
- integrates naturally with beam solvers such as OpenSees.

---

### Convention B — Weight as a Physical Property

Alternatively, the weight may represent a physical quantity directly, such as:
`
w(z) = E(z)
`

In this case, the resulting integrals already carry stiffness dimensions:

`∫_A E(z) dA`

This approach is valid, but requires careful documentation and consistent handling
during solver export.

---

## Voids and Zero-Weight Regions

A **void** is modeled by assigning:
`
w(z) = 0
`

A zero-weight polygon contributes nothing to sectional integrals.

When a zero-weight polygon is geometrically contained within a solid polygon,
CSF interprets the overlap as a **true void**, not as superposed material.

No negative values are required to model holes in standard use.

---

## Polygon Containment and Effective Contribution

All polygon weights are specified as **absolute values**.

CSF internally evaluates containment relationships and computes effective
contributions automatically.

For example, when a stiff inclusion is embedded in a softer matrix,
the effective contribution is derived from the absolute properties of each region,
without requiring the user to subtract the surrounding material explicitly.

This design avoids error-prone manual bookkeeping.

---

## Default Longitudinal Behavior

If no custom law is specified, CSF applies a **linear interpolation** of weights
between reference sections.

Let:
- `w_0`: weight at `z = z_0`
- `w_1`: weight at `z = z_1`
The default law is:

$$
w(z) = w_0 + \frac{z - z_0}{z_1 - z_0}\,(w_1 - w_0)
$$

---

## Custom Weight Laws

CSF allows the user to override the default interpolation by specifying
**custom longitudinal laws**.

A custom law is defined as a mathematical expression evaluated at runtime,
with access to:

- the longitudinal coordinate \( z \),
- start and end weights \( w_0, w_1 \),
- member length \( L \),
- standard mathematical functions,
- selected geometric measures.

This enables non-linear, piecewise, or data-driven variation of properties.

example:

`w(z) = 1.0 - 0.40 * exp(-((z-5.0)^2) / (2*2.0^2))`

This is a Gaussian-shaped reduction centered at `z=5.0`, subtracted from a baseline value of `1.0`.

Interpretation:
- far from `z=5.0`: `exp(...) -> 0`, so `w(z) -> 1.0`
- at `z=5.0`: `exp(0)=1`, so `w(5)=1.0-0.40=0.60` (minimum value)
- `2.0` is the spread parameter (`sigma`): larger `sigma` gives a wider dip, smaller `sigma` gives a narrower dip.


```
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        solid_rect_start:
          weight: 1.0
          vertices:
            - [-2.0, -1.0]
            - [ 2.0, -1.0]
            - [ 2.0,  1.0]
            - [-2.0,  1.0]

    S1:
      z: 10.0
      polygons:
        solid_rect_end:
          weight: 1.0
          vertices:
            - [-2.0, -1.0]
            - [ 2.0, -1.0]
            - [ 2.0,  1.0]
            - [-2.0,  1.0]

weight_laws:
    - 'solid_rect_start,solid_rect_end: 1.0 - 0.40*np.exp(-((z-5.0)**2)/(2*(2.0**2)))'
```


---

## Available Variables and Functions

Custom laws may reference the following quantities:

- `z` — current longitudinal coordinate,
- `w0`, `w1` — weights at the start and end sections,
- `L` — total member length,
- `d(i,j)` — distance between vertices \( i \) and \( j \) at current \( z \),
- `d0(i,j)`, `d1(i,j)` — corresponding distances at start and end,
- `E_lookup(file)` — interpolated values from ext_

