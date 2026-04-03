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
This is a more complex polygon defined by a single ordered vertex sequence. The first part is traversed in counter-clockwise (CCW) direction up to point 5. From point 5 to point 6, the path continues into a second part, which is traversed in clockwise (CW) direction up to point 9. CSF automatically closes the polygon

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
  3 ┤    5(2,3) - 0(2,3) ● ─────────●........●         │
    │                    |                   9(4,3)    |
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

he element is formed as the union of the individual volumes generated between the corresponding polygons in sections `S0` and `S1`.

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

