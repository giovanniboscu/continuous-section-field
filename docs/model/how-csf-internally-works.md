# How CSF Internally Works

## Deterministic section evaluation along Z

In CSF, the geometry of a section at a given coordinate `Z` is obtained by **direct evaluation**, not by geometric intersection or reconstruction.

For each object, the model defines:
- an initial section and a final section,
- the same number of polygons in both sections,
- and, for each polygon, the same number of ordered points.

Given a value of `Z`, the coordinates of each point are computed by interpolating between the corresponding points of the initial and final sections.  
This operation is applied consistently to **all points of a polygon**, producing a new polygon at that `Z`.  
Repeating the process for all polygons yields a complete and unambiguous section at `Z`, even if its shape differs significantly from the end sections.

At the same coordinate `Z`, material properties or weighting factors `w(Z)` are evaluated independently and associated with the corresponding polygons or objects.

---

## Required conditions for non-ambiguity

This deterministic behavior relies on explicit structural conditions:

- the number of polygons is constant between start and end sections;
- the number of points per polygon is constant;
- point-to-point correspondence is preserved;
- polygon-to-polygon correspondence between start and end sections is explicitly defined.

Under these conditions, the section at any `Z` is uniquely defined and cannot be ambiguous.

---

## Key consequence

Because the section is obtained by evaluating a well-defined mapping rather than by slicing geometry, the result does not depend on discretization strategy, visual inspection, or ordering heuristics.

For any `Z`, **one and only one section exists**, fully determined by the model.
