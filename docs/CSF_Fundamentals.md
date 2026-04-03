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

A polygon is defined by an ordered sequence of vertices.

This means that a polygon is not described only by the set of its points, but also by the order in which those points are connected. The vertex order defines the boundary and geometric meaning of the region, and for the polygon to be interpreted as a valid geometric region in CSF, its area must be positive.
