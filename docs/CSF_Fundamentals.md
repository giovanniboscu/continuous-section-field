## Building Blocks

In CSF, the model is built in a simple hierarchy.

### 1. Geometry Building Blocks

Geometry starts from three basic elements, ordered from the smallest to the largest:

* **Vertex**: a point in the section plane, defined by its coordinates. Vertices are the smallest geometric units used to describe the boundary of a region.
* **Polygon**: a geometric region defined by an ordered set of vertices. The polygon is the main geometric component used to represent a part of the section.
* **Section**: a collection of one or more polygons at a given position along the member. A section represents the full cross-sectional geometry at that location.

These are the basic geometric elements from which the section model is built.

### 2. Material Building Block

Once geometry is defined, CSF introduces one additional building block:

* **Weight**: a scalar factor assigned to a polygon to scale its contribution to the section properties. Each polygon can therefore contribute differently, even when the geometry is explicitly defined.

In this way, geometry defines **where** a region is, while weight defines **how much** that region contributes.
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
This is a more complex polygon defined by a single ordered vertex sequence. The first part is traversed in counter-clockwise (CCW) direction up to point 5. From point 5 to point 6, the path continues into a second part, which is traversed in clockwise (CW) direction up to point 10. CSF automatically closes the polygon. An additional overlapping point may be introduced, but it is not required, because CSF automatically closes the polygon.

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
Each polygon in the list is associated with a name and a numerical weight `w`.

In CSF, two sections are defined:

- **S0**: the first ordered polygon list
- **S1**: the second ordered polygon list

Each section has a z-coordinate. The difference between the z-coordinates of S0 and S1 defines the element length.

the element is formed as the union of the individual volumes generated between the corresponding polygons in sections `S0` and `S1`.

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

The polygon is tagged as `@cell`, has weight `1.0`, and is described by a single ordered vertex sequence that contains both the outer and inner loops. The outer loop is a `3 x 3` rectangle written in counter-clockwise (CCW) order and explicitly closed by repeating the point `[2.0, 3.0]`. The inner loop is written in clockwise (CW) order, offset inward by about `0.1`, and is also explicitly closed by repeating the point `[2.1, 3.0]`. Using the same polygon name in `S0` and `S1` preserves the correspondence between the two sections and defines a prismatic thin-walled cell along the element length.

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
          # The bridge is intentionally kept very close to the outer boundary
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

            # Inner loop (CW), offset inward by about 0.1
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


## 7. Material Building Block

### 7.1 Weight Variation Between `S0` and `S1`

From the section representation, it can be seen that each polygon has a numerical weight `w` in `S0` and a numerical weight `w` in `S1`.

For a given polygon, the weight may therefore change from a value `w0` in `S0` to a value `w1` in `S1`.

Since CSF linearly interpolates the intermediate geometry between `S0` and `S1`, the weight of that polygon is also interpolated between `w0` and `w1` at each intermediate section `z`.

This means that, for the same polygon:

- at `S0`, the weight is `w0`
- at `S1`, the weight is `w1`
- at any intermediate section `z`, the weight is an interpolated value between `w0` and `w1`


### 8. Custom Weight Functions

The linear interpolation between `w0` in `S0` and `w1` in `S1` is the simplest way to describe the variation of the polygon weight `w` between the two reference sections.

To represent a more flexible variation law for the property `w` of a given polygon from section `S0` to section `S1`, CSF also allows the user to define custom functions written in Python.

These functions are associated with a specific polygon through the pair of corresponding polygon names defined in `S0` and `S1`.

In other words, the association is not made by position in the list, but by the pair of polygon names that identify the same polygonal component in the two reference sections.

This means that:

- a polygon is first defined in `S0` with its name
- the corresponding polygon is then defined in `S1` with its name
- the custom weight function is associated with that polygon pair through the two names

In this way, CSF can apply a user-defined variation law to a specific polygon between `S0` and `S1`, instead of using only the default linear interpolation between `w0` and `w1`.
In this way, CSF describes not only the geometric transition between `S0` and `S1`, but also the transition of the polygon weight along the element.

For more details, see [ContinuousSectionField (CSF) - Custom Weight Laws](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSFLongitudinally-varying-homogenization-user-guide.md).
