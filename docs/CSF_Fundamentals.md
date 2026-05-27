## CSF Building Blocks

CSF is defined through a small set of building blocks: reference sections, polygon pairs, axial/bending weights, shear/torsion weights, and optional longitudinal variation laws.

### 1. Geometry Building Blocks

Geometry starts from three basic elements, ordered from the smallest to the largest:

* **Vertex**: a point in the section plane, defined by its coordinates. Vertices are the smallest geometric units used to describe the boundary of a region.
* **Polygon**: a geometric region defined by an ordered set of vertices. The polygon is the main geometric component used to represent a part of the section.
* **Section**: a collection of one or more polygons at a given position along the member. A section represents the full cross-sectional geometry at that location.

These are the basic geometric elements from which the section model is built.

### 2. Material Building Blocks

Once geometry is defined, CSF defines sectional participation through two native weight fields:

**Axial/bending weight** `w_i(z)`: a scalar participation factor assigned to each corresponding polygon pair between `S0` and `S1`; along `z`, it scales the contribution of the interpolated polygon to area, axial, and bending-related section properties.

**Shear/torsion weight** `shear_w_i(z)`: a scalar participation factor assigned to each corresponding polygon pair between `S0` and `S1`; along `z`, it scales the contribution of the interpolated polygon to shear- and torsion-related section properties.

The two fields can be related or defined independently. `shear_w_i(z)` may be derived from `w_i(z)` through an isotropic relation, using the shortcut `iso(nu)`, where `nu` must be explicitly defined by the user. It may also be derived from `w_i(z)` through a custom user-defined law, or it may be specified as an independent field.

In this way, geometry defines where each region is, while `w_i(z)` and `shear_w_i(z)` define how much that region contributes to the corresponding classes of section properties.

### 3. Vertex Details

A vertex is defined in the section plane by its coordinates, usually `(x, y)`.

This means that each vertex belongs to a **2D local reference system** used to describe the cross-section. The longitudinal axis of the member is treated separately, so the vertex does not define the position along the member, only the position within the section plane.

In practical terms, a vertex tells CSF where one point of the polygon boundary is located inside the section geometry.

### 4. Polygon Details

A polygon is defined by an ordered sequence of vertices. Each vertex is connected to the next one, from vertex 0 to vertex n, and this ordering defines the polygon boundary region. CSF automatically connects the last vertex back to the first one to close the polygon. The resulting region must have a positive area. As a general guideline, this is usually obtained by listing the vertices counter-clockwise.

This is just an example of a polygon with an intermediate point along one side. To obtain a positive signed area, the vertices must be ordered in counter-clockwise (CCW) direction.

Area = 9

- `0 -> [2, 3]`
- `1 -> [2, 2]`
- `2 -> [5, 2]`
- `3 -> [5, 5]`
- `4 -> [2, 5]`


```text
  y
    ^
  5 ┤             4(2,5) ●─────────────────────────────● 3(5,5)
    │                    .                             │
    │                    .                             │
    │                    .                             │
  4 ┤                    .                             │             
    │                    .                             │
    │                    .                             │
    │                    .                             │
  3 ┤             0(2,3) ●                             │
    │                    |                             |
    │                    |                             |
    │                    |                             |
  2 ┤             1(2,2) ●─────────────────────────────● 2(5,2)
    │
    │
    │
  1 ┤
    │
    │
    │
  0 ┼────────────────────┬─────────────────────────────┬────────> x
     0         1         2         3         4         5

```

The user is free to define any polygonal shape through a single ordered vertex sequence, provided that the enclosed area is greater than zero. The figure below is an example of a valid polygon under this rule.

Example: The first part is traversed in counter-clockwise (CCW) direction up to point 5. From point 5 to point 6, the path continues into a second part, which is traversed in clockwise (CW) direction up to point 10. CSF automatically closes the polygon. An additional overlapping point may be introduced, but it is not required, because CSF automatically closes the polygon.

Area = 8

In this example, the outer area contributes +9, while the inner area contributes -1.

- `0 -> [2, 3]`
- `1 -> [2, 2]`
- `2 -> [5, 2]`
- `3 -> [5, 5]`
- `4 -> [2, 5]`  
- `5 -> [2, 3]`            
- `6 -> [3, 3]`  
- `7 -> [3, 4]`
- `8 -> [4, 4]`
- `9 -> [4, 3]` 
- `10 -> [3, 3]` 


```text
  y
    ^
  5 ┤             4(2,5) ●─────────────────────────────● 3(5,5)
    │                    │                             │
    │                    │                             │
    │                    │                   8(4,4)    │
  4 ┤                    │   7(3,4) ●────────●         │             
    │                    │          │        |         │
    │                    │          │        |         │
    │                    │   6(3,3) │        |         │
  3 ┤    5(2,3) - 0(2,3) ● ─────────●────────●         │
    │                    |   10(3,3)         9(4,3)    |
    │                    |                             |
    │                    |                             |
  2 ┤             1(2,2) ●─────────────────────────────● 2(5,2)
    │
    │
    │
  1 ┤
    │
    │
    │
  0 ┼────────────────────┬─────────────────────────────┬────────> x
     0         1         2         3         4         5
```

### 5. Section Details

A **section** is an ordered list of polygons.  
Each polygon in the list is associated with a unique name within its section and a numerical weight w (Axial/bending weight)

In CSF, two sections are defined:

- **S0**: the first ordered polygon list
- **S1**: the second ordered polygon list

Each section has a z-coordinate. The difference between the z-coordinates of S0 and S1 defines the element length.

The global element is formed as the union of the individual volumes generated between the corresponding polygons in sections `S0` and `S1`.

For example, a T-beam can be described schematically as follows:

```text
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
```

In this example, the element is formed as the union of the volume generated between the two flange polygons and the volume generated between the two web polygons.

> **Note**  
> Also in this YAML representation, the spatial connection order used to generate the element is determined by the ordered list of polygons in each section.

### 6. Polygon Classification Suffixes

In CSF, the polygon name can be extended with classification suffixes such as:

- `@cell`
- `@cell@t=?`
- `@wall`
- `@wall@t=?`

These suffixes are used by CSF to classify the polygon and to activate the corresponding calculation procedure.

More specifically:

- polygons classified with `@cell` are treated as closed-cell polygons
- polygons classified with `@wall` are treated as thin-wall polygons
- the optional suffix `@t=?` assigns the thickness value to that polygon

When one of these classifications is present, CSF applies the corresponding torsional contribution method described in the *De Saint-Venant Torsional Constant* section [De Saint-Venant Torsional Constant - Cell and Wall Contributions in CSF](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md)

This guide covers the geometric construction of tagged polygons in CSF. [CSF Polygon Geometry Guide: @cell and @wall](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSF_Polygon_Geometry_Guide.md)

**The classification suffix is not considered part of the polygon base name.**

The purpose of the 10-point polygon can now be made explicit.  
It is a single geometric representation of what would otherwise be described as two separate entities: an outer rectangle and an inner rectangle. By encoding both within one ordered polygon stream, CSF can treat them as one tagged geometric object.

---

This YAML example defines the same thin-walled closed-cell polygon in both reference sections,
`S0` and `S1`, at `z = 0.0` and `z = 10.0`.

The polygon is tagged as `@cell`, has weight `1.0`, and is described by a single ordered vertex sequence that contains both the outer and inner loops. The outer loop is a `3 x 3` rectangle written in counter-clockwise (CCW) order and explicitly closed by repeating the point `[2.0, 3.0]`. The inner loop is written in clockwise (CW) order, and is also explicitly closed by repeating the point `[2.1, 3.0]`. Using the same polygon name in `S0` and `S1` preserves the correspondence between the two sections and defines a prismatic thin-walled cell along the element length.

```
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        outer@cell:
          weight: 1.0
          # Thin-walled slit-cell example.
          # The outer loop is a 3x3 rectangle written in CCW order.
          # The repeated point [2.0, 3.0] explicitly closes the outer loop.
          # After that, the vertex stream continues with the inner loop.
          # The inner polygon is  kept very close to the outer boundary
          # so that the section represents a genuinely thin profile.
          # The inner loop is written in CW order.
          vertices:
            # Outer loop (CCW)
            - [2.0, 3.0]
            - [2.0, 2.0]
            - [5.0, 2.0]
            - [5.0, 5.0]
            - [2.0, 5.0]
            - [2.0, 3.0]

            # Inner loop (CW)
            - [2.1, 3.0]
            - [2.1, 4.9]
            - [4.9, 4.9]
            - [4.9, 2.1]
            - [2.1, 2.1]
            - [2.1, 3.0]
    S1:
      z: 10.0
      polygons:
        outer@cell:
          weight: 1.0
          # Same thin-walled cell at the end section.
          # Using the same polygon name keeps the correspondence between S0 and S1.
          vertices:
            # Outer loop (CCW)
            - [2.0, 3.0]
            - [2.0, 2.0]
            - [5.0, 2.0]
            - [5.0, 5.0]
            - [2.0, 5.0]
            - [2.0, 3.0]

            # Inner loop (CW)
            - [2.1, 3.0]
            - [2.1, 4.9]
            - [4.9, 4.9]
            - [4.9, 2.1]
            - [2.1, 2.1]
            - [2.1, 3.0]
```

---

This example shows a simplified open thin-walled `I`-section representation in which the polygons are explicitly classified with the `@wall` suffix, and the wall thickness is assigned directly in the polygon name through the `@t=` suffix.

In this model, three wall polygons are defined:

- `web@wall@t=0.41`
- `top_flange@wall@t=0.57`
- `bottom_flange@wall@t=0.57`

The `@wall` suffix tells CSF to treat these polygons as thin-wall components, while `@t=` provides the wall thickness to be used for the corresponding torsional contribution. This avoids relying on the automatic geometric estimate `t_est = 2A / P`, which is only an approximation and may underestimate the intended wall thickness when the strip is not extremely thin.

The example therefore represents a simplified three-wall `IPE100`-type section composed of one web and two flanges, with nominal thickness values assigned explicitly in the polygon names. In this way, the wall classification and the thickness used by CSF are both declared directly in the geometry definition.

```
# Explicit thickness override for thin-wall torsion (@wall):
#
# Why @t is needed
# ----------------
# The automatic thickness estimate uses:
#     t_est = 2A / P
# where A is polygon area and P is polygon perimeter.
#
# For a rectangular wall strip (length b, thickness t):
#     A = b*t
#     P = 2(b+t)
# so:
#     t_est = 2A/P = (b*t)/(b+t)
#
# This is NOT exactly t.
# It approaches t only in the very thin-strip limit (b >> t):
#     (b*t)/(b+t) ≈ t
# Otherwise it underestimates thickness, and this directly affects torsion.
#
# Impact on J_sv_wall
# -------------------
# In open thin-walled Saint-Venant torsion, each wall contribution scales with t^3
# (equivalently J_i ~ A*t^2/3 in the implemented form).
# Therefore, even a moderate thickness underestimation causes a large drop in J.
#
# IPE100 simplified model choice
# ------------------------------
# To keep the torsion model aligned with nominal section dimensions,
# we force thickness explicitly in polygon names:
#   - web thickness    tw = 4.1 mm  = 0.41 cm
#   - flange thickness tf = 5.7 mm  = 0.57 cm
#
# This removes ambiguity from geometry-based t estimation and makes J_sv_wall
# consistent with the intended open thin-walled analytical formulation for
# the simplified 3-wall IPE representation (web + 2 flanges).
#
# Note
# ----
# Remaining difference vs tabulated rolled IPE torsional constants is expected:
# this simplified model does not include full rolled-shape details (e.g. root
# fillets and local transitions), and tabulated values are based on the real profile.

web@wall@t=0.41:
top_flange@wall@t=0.57:
bottom_flange@wall@t=0.57:

CSF:
  sections:
    S0:
      z: 0.0   # cm
      polygons:
        web@wall@t=0.41:
          weight: 1.0
          vertices:
            - [-0.205, -4.430]
            - [ 0.205, -4.430]
            - [ 0.205,  4.430]
            - [-0.205,  4.430]

        top_flange@wall@t=0.57:
          weight: 1.0
          vertices:
            - [-2.750,  4.430]
            - [ 2.750,  4.430]
            - [ 2.750,  5.000]
            - [-2.750,  5.000]

        bottom_flange@wall@t=0.57:
          weight: 1.0
          vertices:
            - [-2.750, -5.000]
            - [ 2.750, -5.000]
            - [ 2.750, -4.430]
            - [-2.750, -4.430]

    S1:
      z: 5000.0   # cm (20 m)
      polygons:
        web@wall:
          weight: 1.0
          vertices:
            - [-0.205, -4.430]
            - [ 0.205, -4.430]
            - [ 0.205,  4.430]
            - [-0.205,  4.430]

        top_flange@wall:
          weight: 1.0
          vertices:
            - [-2.750,  4.430]
            - [ 2.750,  4.430]
            - [ 2.750,  5.000]
            - [-2.750,  5.000]

        bottom_flange@wall:
          weight: 1.0
          vertices:
            - [-2.750, -5.000]
            - [ 2.750, -5.000]
            - [ 2.750, -4.430]
            - [-2.750, -4.430]
```

> **Note on `@t=` suffix**  
> If the `@t=` thickness suffix is specified on only one of the two reference sections (`S0` or `S1`), CSF treats that thickness value as **constant along the entire element length**.

---

### 7. Weight Variation and Custom Laws

#### 7.1 Weight Variation Between `S0` and `S1`

Each polygon has a numerical weight `w` in `S0` and a numerical weight `w` in `S1`. For a given polygon, the weight may therefore change from a value `w0` in `S0` to a value `w1` in `S1`.

Since CSF linearly interpolates the intermediate geometry between `S0` and `S1`, the weight of that polygon is also interpolated between `w0` and `w1` at each intermediate section `z`. This means that, for the same polygon:

- at `S0`, the weight is `w0`
- at `S1`, the weight is `w1`
- at any intermediate section `z`, the weight is an interpolated value between `w0` and `w1`

The value `w_i(z) = 1` is the reference participation level. Values below or above `1` reduce or increase the effective contribution of the interpolated polygon relative to that reference. It is used to model longitudinal variation of sectional participation, such as material degradation, reinforcement contribution, staged activation, or equivalent stiffness weighting along the member axis. It affects the effective area, centroid, second moments of area, and related axial/bending sectional properties.

#### 7.2 Custom Weight Laws

The linear interpolation between `w0` and `w1` is the simplest way to describe the variation of `w` along the element. CSF also allows the user to define custom functions written in Python, associated with a specific polygon through the pair of corresponding polygon names in `S0` and `S1`:

- a polygon is first defined in `S0` with its name
- the corresponding polygon is then defined in `S1` with its name
- the custom weight function is associated with that polygon pair through the two names

The variation law is identified by the following syntax:

```text
<name_polygon_i_s0>,<name_polygon_i_s1>: <function of z>
```

For example:

```text
- 'flange,flange:1.0 - 0.28 * (1 - (z / 10.0)**2)'
```

In this example, the custom weight law is associated with the polygon named `flange` in `S0` and with the corresponding polygon named `flange` in `S1`.

For example, a polygon may have `w0 = 1.0` at `S0` and `w1 = 1.0` at `S1`, but a user-defined law can still impose a non-linear variation along the element:

```yaml
weight_laws:
  - "startsection,endsection: 1.0 - 0.4*(z/L)**2"
```

#### 7.3 Custom Shear Weight Laws

The shear/torsion weight `shear_w_i(z)` is associated with a corresponding polygon pair between `S0` and `S1` and defines the effective shear/torsion participation of the interpolated polygon at position `z`.

Unlike the axial/bending weight `w`, `shear_w` is not given by explicit polygon attributes in `S0` and `S1`. Its values, including the endpoint values at `S0` and `S1`, are computed from the applicable `shear_weight_laws`.

CSF supports the following cases:

- if `shear_weight_laws` is not defined, CSF uses the default relation:

  ```text
  shear_w_i(z) = w_i(z)
  ```

  This corresponds to the default isotropic relation with `nu = -0.5`.

- if an isotropic relation is required, the shortcut `iso(nu)` can be used, where `nu` must be explicitly defined by the user:

  ```yaml
  shear_weight_laws:
    - "iso(0.2)"
  ```

  When the law is written without polygon names, it is applied to all corresponding polygon pairs. A specific assignment can still be defined for a selected polygon pair by using the two polygon names:

  ```yaml
  shear_weight_laws:
    - "iso(0.2)"
    - "startsection,endsection: iso(0.3)"
  ```

- if a non-isotropic or custom relation is required, the user can define a Python expression. In this expression, `w` is the axial/bending weight already evaluated at the current section `z`:

  ```yaml
  shear_weight_laws:
    # non-isotropic function
    - "startsection,endsection: w - (1+0.4)*t/50"
  ```

In this way, CSF can describe two longitudinal participation fields: `w_i(z)` for area, axial, and bending-related properties, and `shear_w_i(z)` for shear- and torsion-related properties.

For more details, see [ContinuousSectionField (CSF) - Custom Weight Laws](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSFLongitudinally-varying-homogenization-user-guide.md).

#### 7.4 Examples

Example with an isotropic shear/torsion relation:

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
    - 'flange,flange:1.0 - 0.28 * (1 - (z / 10.0)**2)'

    # linear reduction for the web: from 1.0 at z=0 to 0.70 at z=10
    - 'web,web:1.0 - 0.30 * (z / 10.0)'

  shear_weight_laws:
    # isotropic shear/torsion relation with Poisson's ratio nu = 0.2
    - 'iso(0.2)'
```

Here, `w_i(z)` is first evaluated from `weight_laws`. Then `shear_w_i(z)` is derived from the isotropic relation:

```text
shear_w_i(z) = w_i(z) / (2 * (1 + nu))
```

For `nu = 0.2`:

```text
shear_w_i(z) = w_i(z) / 2.4
```

The same isotropic relation is applied to all corresponding polygon pairs.

The following example shows a non-isotropic shear/torsion weight law defined as a function of the axial/bending weight `w`. Here, `w` is first evaluated from `weight_laws` at the current section `z`. Then, `shear_weight_laws` uses that value to compute the corresponding shear/torsion participation `shear_w`.

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        startsection:
          weight: 1.0
          vertices:
            - [-0.4, -0.4]
            - [ 0.4, -0.4]
            - [ 0.4,  0.4]
            - [-0.4,  0.4]

    S1:
      z: 10.0
      polygons:
        endsection:
          weight: 1.0
          vertices:
            - [-0.2, -0.2]
            - [ 0.2, -0.2]
            - [ 0.2,  0.2]
            - [-0.2,  0.2]

  weight_laws:
    # axial/bending weight law w_i(z)
    - "startsection,endsection: 1.0 - 0.4*(z/L)**2"

  shear_weight_laws:
    # non-isotropic shear/torsion law as a function of the already evaluated w_i(z)
    - "startsection,endsection: 0.6*w"
```
