## Building Blocks

In CSF, the model is built in a simple hierarchy.

### 1. Geometry Building Blocks

Geometry starts from three basic elements, ordered from the smallest to the largest:

- **Vertex**: a point in the section plane.
- **Polygon**: a geometric region defined by an ordered set of vertices.
- **Section**: a collection of one or more polygons at a given position along the member.

These are the basic geometric elements from which the section model is built.

### 2. Material Building Block

Once geometry is defined, CSF introduces one additional building block:

- **Weight**: a scalar factor assigned to a polygon to scale its contribution to the section properties.

In this way, geometry defines **where** a region is, while weight defines **how much** that region contributes.
