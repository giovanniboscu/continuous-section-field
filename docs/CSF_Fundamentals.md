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
