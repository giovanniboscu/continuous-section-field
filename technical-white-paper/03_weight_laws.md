# Weight Laws and Sectional Homogenization

> **Prerequisites**
> This document assumes familiarity with the basic concepts of linear structural elasticity:
> Young's modulus E, shear modulus G, and the isotropic relation G = E / (2(1+ν)).
> Readers without this background are referred to a standard structural mechanics textbook before proceeding.

## Purpose of Weight Laws

In CSF, geometric definition and physical properties are intentionally decoupled.

Geometry defines *where material exists*.  
**Weight laws** define *how that geometry contributes to sectional properties*.

CSF defines two separate participation fields:

- `w_i(z)` - the **axial/bending weight**, which scales the contribution of each polygon to area, centroid, and bending-related properties.
- `shear_w_i(z)` - the **shear/torsion weight**, which scales the contribution of each polygon to shear- and torsion-related properties.

Both fields are defined through longitudinal laws and can vary independently along the member.

Together, they provide a general and explicit way to introduce:
- material heterogeneity,
- stiffness variation along the member,
- staged or degraded properties,
- embedded components and voids,
- non-isotropic axial/shear participation,

without altering the underlying geometric description.

---

## Definition of Weight

Each polygonal region of a section is associated with a scalar weight field
`w_k(z)` where `k` denotes the polygon index, defined along the longitudinal coordinate `z`.

During sectional property assembly, this scalar multiplies the geometric contribution
of the corresponding polygon.

Formally, a generic sectional quantity `Q(z)` is evaluated as:

```
Q(z) = sum_k [ w_k(z) * Q_k(z) ]
```

where `Q_k(z)` is the purely geometric contribution of polygon `k`.

The term *weight* is deliberately generic.  
It does not enforce a specific physical interpretation.

---

## Definition of Shear Weight

Each polygonal region is also associated with a scalar shear/torsion weight field
`shear_w_k(z)`, defined along the same longitudinal coordinate `z`.

During sectional property assembly, this scalar multiplies the geometric contribution
of the corresponding polygon to shear- and torsion-related quantities.

Formally, a generic shear/torsion quantity `Q_sv(z)` is evaluated as:

```
Q_sv(z) = sum_k [ shear_w_k(z) * Q_k(z) ]
```

where `Q_k(z)` is the purely geometric contribution of polygon `k`.

Unlike `w_k(z)`, the shear weight is **not assigned as a polygon attribute** in `S0`
and `S1`. Its values at every section `z` are always computed from the applicable
`shear_weight_laws`.

The term *shear weight* is deliberately generic.  
It does not enforce a specific physical interpretation.

---

## Physical Interpretation

The physical meaning of `w(z)` is entirely **user-defined**, but must remain
**internally consistent** throughout the workflow.

Typical interpretations include:
- ratio of Young's modulus with respect to a reference material,
- absolute Young's modulus,
- density multiplier for mass evaluation,
- any scalar field that scales with area integrals.

CSF does not infer or enforce units.  
All consistency checks are the responsibility of the user.

---

## Two Common Modeling Conventions

### Convention A - Dimensionless Homogenization Factor (Recommended)

In this convention, the weight is defined as:

```
w(z) = E(z) / E_ref
```

where `E_ref` is a chosen reference modulus.

```
A*(z) = sum_k [ w_k(z) * A_k(z) ]
I*(z) = sum_k [ w_k(z) * I_k(z) ]
```

The effective stiffness quantities become `E_ref * A*(z)` and `E_ref * I*(z)`.

This convention:
- preserves numerical stability,
- keeps geometric quantities dimensionally clean,
- integrates naturally with beam solvers such as OpenSees.

---

### Convention B - Weight as a Physical Property

Alternatively, the weight may represent a physical quantity directly, such as:

```
w(z) = E(z)
```

In this case, the resulting integrals already carry stiffness dimensions:

```
∫_A E(z) dA
```

This approach is valid, but requires careful documentation and consistent handling
during solver export.

---

## Voids and Zero-Weight Regions

A **void** is modeled by assigning:

```
w(z) = 0
```

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

```
w(z) = w_0 + (z - z_0) / (z_1 - z_0) * (w_1 - w_0)
```

---

## Custom Weight Laws

CSF allows the user to override the default interpolation by specifying
**custom longitudinal laws**.

A custom law is defined as a mathematical expression evaluated at runtime,
with access to:

- the longitudinal coordinate `z`,
- start and end weights `w_0`, `w_1`,
- member length `L`,
- standard mathematical functions,
- selected geometric measures.

This enables non-linear, piecewise, or data-driven variation of properties.

**Example - Gaussian-shaped reduction:**

```
w(z) = 1.0 - 0.40 * exp(-((z - 5.0)^2) / (2 * 2.0^2))
```

Interpretation:
- far from `z = 5.0`: `exp(...) → 0`, so `w(z) → 1.0`
- at `z = 5.0`: `exp(0) = 1`, so `w(5) = 0.60` (minimum value)
- `2.0` is the spread parameter (`sigma`): larger `sigma` gives a wider dip.

```yaml
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

| Variable | Meaning |
| :--- | :--- |
| `z` | Current longitudinal coordinate |
| `w0`, `w1` | Weights at the start and end sections |
| `L` | Total member length |
| `t` | Normalized coordinate in `[0, 1]` |
| `d(i,j)` | Distance between vertices `i` and `j` at current `z` |
| `d0(i,j)`, `d1(i,j)` | Corresponding distances at start and end |
| `E_lookup(file)` | Interpolated value from external file (keyed on `z`) |
| `T_lookup(file)` | Interpolated value from external file (keyed on `t`) |
| `np` | NumPy namespace |

---

## Shear/Torsion Weight

### Definition

In addition to the axial/bending weight `w_i(z)`, CSF defines a separate scalar
participation field for shear- and torsion-related section properties:

```
shear_w_i(z)
```

where `i` identifies a corresponding polygon pair between `S0` and `S1`.

`shear_w_i(z)` multiplies the geometric contribution of each interpolated polygon
to quantities such as shear area and Saint-Venant torsional constant.

### Key difference from `w_i(z)`

Unlike the axial/bending weight, `shear_w_i(z)` is **not assigned as a polygon
attribute** in `S0` and `S1`. Its values - including the endpoint values at `S0`
and `S1` - are always computed from the applicable `shear_weight_laws`.

---

## Shear Weight Laws

### Default behavior

If `shear_weight_laws` is not defined, CSF applies the default relation:

```
shear_w_i(z) = w_i(z)
```

This corresponds to the isotropic relation with `nu = -0.5`.

---

### Isotropic shortcut - `iso(nu)`

When an isotropic relation between axial/bending and shear/torsion participation
is required, the shortcut `iso(nu)` can be used:

```yaml
shear_weight_laws:
  - 'iso(0.2)'
```

This evaluates as:

```
shear_w_i(z) = w_i(z) / (2 * (1 + nu))
```

For `nu = 0.2`:

```
shear_w_i(z) = w_i(z) / 2.4
```

When written without polygon names, the law is applied to **all** corresponding
polygon pairs. A specific assignment can still be defined for a selected pair:

```yaml
shear_weight_laws:
  - 'iso(0.2)'
  - 'startsection,endsection: iso(0.3)'
```

---

### Custom shear weight law

A non-isotropic or fully custom relation can be specified as a Python expression.

Inside a custom shear weight expression, the variable **`w` is the axial/bending
weight already evaluated at the same section `z`**:

```yaml
shear_weight_laws:
  - 'startsection,endsection: 0.6*w'
```

This means the shear/torsion participation is derived from the current value of
the axial/bending participation, without requiring an additional independent
definition.

---

### Syntax

The same polygon-pair syntax used for `weight_laws` applies:

```
<name_polygon_i_s0>,<name_polygon_i_s1>: <expression>
```

A global law (no polygon names) is applied to all pairs:

```yaml
shear_weight_laws:
  - 'iso(0.2)'
```

A pair-specific law overrides the global one for that pair:

```yaml
shear_weight_laws:
  - 'iso(0.2)'
  - 'flange,flange: 0.5*w'
```

---

### Available variables in shear weight expressions

| Variable | Meaning |
| :--- | :--- |
| `w` | Axial/bending weight `w_i(z)` already evaluated at current `z` |
| `z` | Current longitudinal coordinate |
| `w0`, `w1` | Weights at the start and end sections |
| `L` | Total member length |
| `t` | Normalized coordinate in `[0, 1]` |
| `d(i,j)` | Distance between vertices `i` and `j` at current `z` |
| `d0(i,j)`, `d1(i,j)` | Corresponding distances at start and end |
| `E_lookup(file)` | Interpolated value from external file (keyed on `z`) |
| `T_lookup(file)` | Interpolated value from external file (keyed on `t`) |
| `np` | NumPy namespace |

---

### Full example - combined weight and shear weight laws

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        flange:
          weight: 1.0
          vertices:
            - [-1.0, -0.2]
            - [ 1.0, -0.2]
            - [ 1.0,  0.2]
            - [-1.0,  0.2]
        web:
          weight: 1.0
          vertices:
            - [-0.2, -1.0]
            - [ 0.2, -1.0]
            - [ 0.2, -0.2]
            - [-0.2, -0.2]

    S1:
      z: 10.0
      polygons:
        flange:
          weight: 1.0
          vertices:
            - [-1.0, -0.2]
            - [ 1.0, -0.2]
            - [ 1.0,  0.2]
            - [-1.0,  0.2]
        web:
          weight: 1.0
          vertices:
            - [-0.2, -2.5]
            - [ 0.2, -2.5]
            - [ 0.2, -0.2]
            - [-0.2, -0.2]

  weight_laws:
    # parabolic increase: 72% at base (z=0), full section at top (z=10)
    - 'flange,flange: 1.0 - 0.28 * (1 - (z / 10.0)**2)'
    # linear reduction for the web: from 1.0 at z=0 to 0.70 at z=10
    - 'web,web: 1.0 - 0.30 * (z / 10.0)'

  shear_weight_laws:
    # isotropic shear/torsion relation with Poisson's ratio nu = 0.2
    # applied to all polygon pairs
    - 'iso(0.2)'
```

Here, `w_i(z)` is first evaluated from `weight_laws`. Then `shear_w_i(z)` is
derived from the isotropic relation `w_i(z) / 2.4` and applied to both pairs.

---

### Non-isotropic example

```yaml
  weight_laws:
    - 'startsection,endsection: 1.0 - 0.4*(z/L)**2'

  shear_weight_laws:
    # shear/torsion participation as a fraction of the axial/bending participation
    - 'startsection,endsection: 0.6*w'
```

In this case, `w` inside the shear law is the value of `1.0 - 0.4*(z/L)**2`
already evaluated at the current `z`.

By defining `w_i(z)` and `shear_w_i(z)` separately, CSF can represent a
non-isotropic equivalent 1D sectional participation model, where axial/bending
and shear/torsion behavior follow independent longitudinal laws.
