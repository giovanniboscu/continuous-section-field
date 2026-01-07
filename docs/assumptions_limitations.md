# Assumptions and Limitations

This document summarizes the modeling assumptions, geometric scope, and known limitations of the **Continuous Section Field (CSF)** framework.

CSF is **not** a Finite Element Method (FEM) solver. It is a **geometric + constitutive engine for a single non-prismatic member**, providing sectional properties and stiffness/mass quantities to be used by beam-based solvers or external workflows.

---

## Modeling Assumptions

- **Slender-member (beam) idealization**  
  The member is treated as a 1D structural element whose behavior is represented through sectional resultants (e.g., \(EA\), \(EI\), \(GJ\)).

- **Linear elastic behavior**  
  Material response is assumed linear elastic. No cracking, yielding, plasticity, damage, or other nonlinear constitutive effects are modeled.

- **Small deformations (linear geometry)**  
  Geometric nonlinearities (large rotations/large displacements, P–Δ/P–δ, follower loads) are outside CSF’s scope.

- **Sectional properties drive response**  
  CSF computes cross-sectional properties and stiffness/mass quantities; global structural response requires an external solver (e.g., OpenSees/OpenSeesPy, OpenFAST input, custom beam solvers).

---

## Geometric Scope

CSF models members whose geometry is defined by **polygonal end sections** connected by **straight generator lines** (i.e., **ruled surfaces/ruled solids**).

- **End sections as polygons (polylines)**  
  Each cross-section is defined by one or more closed polylines (polygons). Polygons represent material regions; negative-weight polygons may represent voids/holes (algebraic subtraction).

- **Ruled-surface interpolation between extremes**  
  Corresponding vertices are mapped **vertex-to-vertex** between the start and end sections, producing straight generator lines in 3D.

- **Curved outlines via polygonal approximation**  
  Curved section boundaries (e.g., circular/curvilinear outlines) are approximated by increasing the number of polygon sides. Higher vertex counts improve geometric fidelity.

---

## Topological and Input Constraints

These constraints are essential for valid geometry and continuous mapping:

- **Consistent polyline topology between start and end**  
  The start and end sections must have:
  - the **same number of polylines/polygons**
  - matching **vertex ordering and correspondence** (vertex-to-vertex mapping)

- **No topological changes along the axis**  
  Changes such as splitting/merging regions, appearance/disappearance of holes, or any change in the number of polygons are not supported in a single CSF member field.

- **Non-self-intersecting, non-overlapping polygons**  
  Polylines must be simple (non-self-intersecting) and must not overlap in invalid ways. Geometric consistency is the user’s responsibility.

- **Orientation matters (CCW convention)**  
  Polygons must follow the orientation convention required by the implemented area/inertia algorithms (typically counter-clockwise for positive area). Inconsistent orientation can lead to incorrect results.

---

## Material Modeling Assumptions

- **Homogenization via weights**  
  Multi-material behavior is represented using polygon weights, typically defined as:
  \[
  w(z) = \frac{E(z)}{E_{\text{ref}}}
  \]
  where \(E(z)\) may vary along the member axis.

- **Longitudinal variation of stiffness is supported**  
  Each polygon may be assigned a longitudinal weight function \(w(z)\), including:
  - custom analytic functions
  - lookup-table based profiles (interpolated)

- **Across-section effects are “sectional”**  
  CSF captures the effect of non-uniform stiffness distribution across the section through weighted sectional integrals. However, complex phenomena that require a full 2D/3D stress solution may not be represented.

---

## Torsion and Shear (Important Notes)

- **Torsion constant for general sections**  
  The Saint-Venant torsion constant \(J\) is non-trivial for many shapes (especially open/thin-walled sections). If CSF uses an approximation for \(J\), treat results for thin-walled/open profiles as **preliminary** and validate against specialized methods when torsion is critical.

- **Multi-material torsion/shear coupling**  
  Advanced torsion/shear effects in multi-material or strongly non-uniform sections may require dedicated 2D analysis beyond the scope of a sectional homogenization approach.

- **Shear quantities (if computed)**  
  Shear stress-related quantities (e.g., \(Q\) via Jourawski-style assumptions) rely on classical beam theory assumptions and may be less reliable for thin-walled/open or highly non-uniform sections.

---

## Numerical Considerations

- **Geometry mapping is exact; integrals may be numerical**  
  While the geometric interpolation is defined by explicit mapping rules (ruled surfaces), many sectional quantities may be obtained via numerical integration (e.g., Gaussian quadrature over triangulated domains). Accuracy depends on integration settings and polygon resolution.

- **Polygon resolution controls fidelity for curved boundaries**  
  For curvilinear shapes approximated by polygons, accuracy improves with more sides/vertices. Users should verify convergence when high fidelity is required.

---

## Coupling to External Solvers

- **CSF provides properties; the solver computes response**  
  External solvers (OpenSees, OpenFAST, etc.) may internally require sampling/integration of the provided property fields. The analysis outcome will depend on the solver’s formulation and numerical settings (e.g., element type, integration scheme).

- **Exporter strategies can differ**  
  If an exporter samples properties at selected axial locations (e.g., element midpoints or integration points), that is a coupling choice. Users should ensure the chosen strategy matches their accuracy needs.

---

## Summary

CSF is designed for **linear elastic, slender-member modeling** where geometry and elastic properties vary along the axis and across the section. It is especially effective when a continuous property field is needed for rapid iteration, preprocessing, or solver coupling—within the geometric constraints of **ruled-surface members** and **consistent section topology**.
