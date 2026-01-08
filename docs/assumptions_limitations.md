# Assumptions and Limitations

This document summarizes the modeling assumptions, geometric scope, and known limitations of the **Continuous Section Field (CSF)** framework.

CSF is **not** a Finite Element Method (FEM) solver. It is a **geometric + constitutive engine for a single non-prismatic member**, providing sectional properties and stiffness/mass quantities to be used by beam-based solvers or external workflows.

---

## Modeling Assumptions

- **Slender-member (beam) idealization**  
  The member is treated as a 1D member model with 2D cross-sectional integration structural element whose behavior is represented through sectional resultants (e.g., \(EA\), \(EI\), \(GJ\)).

- **Linear elastic behavior**  
  Material response is assumed linear elastic. No cracking, yielding, plasticity, or other nonlinear constitutive effects are modeled.

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

## Torsion and Shear (Critical Engineering Warnings)

- **Approximation for Saint-Venant Torsion (K/Jsv)** The current implementation of the Torsional Constant ($K$) follows a simplified "sum-of-thin-parts" approach ($K \approx \sum \frac{1}{3}bt^3$). This leads to specific engineering implications:
  - **Overestimation in Thick Sections:** For solid/stout sections (e.g., rectangles where $b/h < 10$), the algorithm may overestimate torsional stiffness by **5% to 10%** due to the lack of warping correction factors (e.g., Roark’s coefficients).
  - **Intersections (The "Bulb" Effect):** The model treats the section as a collection of independent polygons. It does not account for the additional stiffness provided by material intersections (bulbs) in shapes like L, T, or I beams.
  - **Pathological Geometries:** Torsional results for self-intersecting or highly concave polygons are numerically unstable and physically meaningless.



- **Thin-Walled vs. Solid Sections** CSF is optimized for thin-walled open profiles where the sum-of-parts approximation is standard. For solid, high-precision mechanical components, results must be considered **preliminary** and should be validated against 2D FEM or BEM solvers.

- **Shear Center and Warping Constant ($Cw$)** Advanced torsional properties such as the warping constant ($C_w$) and the exact coordinates of the shear center are currently outside the primary geometric engine's scope.

---

## Numerical Stability and Pathological Cases

The "Stress-Test" protocols (Green’s Theorem validation) have identified the following behaviors:

- **Numerical Precision (Inertia):** Sectional properties ($A, I_x, I_y$) are computed with high fidelity (absolute errors near $10^{-14}$ for standard polygons), matching state-of-the-art commercial solvers.
- **Degenerate Polygons:** - **Collinear vertices:** May trigger area-zero warnings or numerical instability.
    - **Self-Intersections:** Will trigger `RuntimeWarning`. The resulting inertia might be calculated correctly via the Shoelace formula (signed area), but torsional constants will diverge.
- **Floating Point Limits:** Large coordinate offsets (e.g., $> 10^{10}$) may lead to precision loss in secondary properties ($I_{xy}$, $K$).

---

## Numerical Considerations

- **Geometry mapping is exact; integrals may be numerical**  
  While the geometric interpolation is defined by explicit mapping rules (ruled surfaces), many sectional quantities may be obtained via numerical integration. Accuracy depends on integration settings and polygon resolution.

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
