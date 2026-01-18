# How CSF Calculates Sections

## 1. Conceptual model

CSF represents a structural member through a **longitudinally parameterized model**, in which geometry, topology, and material attributes are defined as functions of the longitudinal coordinate `Z`.

Cross-sections are not stored as discrete geometric objects. Instead, they are **evaluated deterministically** from the model at any given `Z`.

---

## 2. Section definition

For each structural object, CSF requires:

- one initial section (`Z = Z_start`),
- one final section (`Z = Z_end`),
- an identical number of polygons in both sections,
- an identical number of ordered points for each corresponding polygon.

A one-to-one correspondence is therefore established:
- between polygons at the start and end sections,
- and between points within each corresponding polygon.

These correspondences are explicit and fixed for the entire length of the object.

---

## 3. Section evaluation at a given Z

Given a specific coordinate `Z`, CSF evaluates the section as follows:

1. For each polygon, the coordinates of every point are computed by interpolation between the corresponding points of the initial and final sections.
2. The interpolation is applied consistently to all points of the polygon, producing a new polygon at `Z`.
3. The process is repeated for all polygons associated with the object.

The collection of all evaluated polygons constitutes the complete cross-section at coordinate `Z`.

This procedure guarantees that the resulting section is uniquely defined, regardless of the geometric complexity or variation between the end sections.

---

## 4. Material and weighting evaluation

Material properties and weighting factors (e.g. elastic modulus ratios) are evaluated independently as functions of `Z`.

At a given `Z`, each evaluated polygon is associated with its corresponding material state, ensuring consistency between geometry and material definition along the member.

---

## 5. Determinism and non-ambiguity

The section evaluation process is deterministic under the following conditions:

- the number of polygons remains constant along the object;
- the number of points per polygon remains constant;
- polygon-to-polygon correspondence is preserved;
- point-to-point correspondence within each polygon is preserved.

If these conditions are satisfied, the section at any coordinate `Z` is uniquely determined and cannot be ambiguous.

---

## 6. Separation between definition and discretization

Discretization strategies (stations, integration points, solver-specific segmentation) do not alter the section definition.

They only determine **where** the model is evaluated along `Z`.

As a consequence:
- changing the discretization does not change the geometry or properties of the section,
- the same model can be sampled consistently for different solvers or levels of refinement.

---

## 7. Implications

This approach eliminates dependence on geometric slicing, curve ordering, orientation heuristics, or visual inspection.

Section consistency is enforced by construction, providing a reliable and reproducible basis for downstream structural analysis.
