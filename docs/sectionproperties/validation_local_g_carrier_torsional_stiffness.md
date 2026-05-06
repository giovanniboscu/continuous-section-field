# Verification Note - Torsional Stiffness of Composite Cross-Sections
## G-Carrier Approach in `sectionproperties` - Independent FEM Verification

---

## 1. Background

The Python library `sectionproperties` computes the Saint-Venant torsional constant *J* by solving Prandtl's stress-function (warping) problem via finite elements. For composite sections, the library uses each material's Young's modulus *E*ᵢ as the local carrier, yielding a weighted quantity *EJ* rather than the torsionally relevant *GJ*.

The library provides a documented global correction:

$$GJ_\text{doc} = \frac{g_\text{eff}}{e_\text{eff}} \cdot EJ$$

This multiplier is a single scalar ratio computed from area-averaged effective moduli and does not account for the spatial distribution of *G*ᵢ across the section. For sections where the stiffer material is concentrated in a specific region, the approximation introduces a non-negligible error.

---

## 2. G-Carrier Approach

The warping (Prandtl) formulation is formally identical regardless of which local scalar field is used as the carrier. The torsionally correct procedure is:

1. Assign each material's shear modulus *G*ᵢ to the `E` field of the corresponding `Material` object in `sectionproperties`.
2. Run `calculate_frame_properties()` and retrieve `get_ej()`. Because the carrier is now *G*ᵢ, the result is the correct *GJ* of the composite section.
3. Poisson's ratio inputs retain their physical values; they affect only mesh generation and have no influence on the warping solution.

No external scaling or post-processing is required. The approach is exact within the finite-element discretisation error of the mesh.

---

## 3. Verification with scikit-fem

### 3.1 Reference Solver

An independent warping FEM was implemented with `scikit-fem` (`skfem`), a Python finite-element library with no dependency on `sectionproperties`. The problem is formulated in weak form as:

$$\int G_i \, \nabla\omega \cdot \nabla v \, dA = \int G_i \, \nabla v \cdot [y_c,\, -x_c] \, dA$$

where *ω* is the warping function, *v* is the test function, and *(xc, yc)* is the *G*-weighted centroid. The torsional stiffness is recovered as:

$$GJ = I_{pp,G} - \omega^\top f$$

with *I*pp,G the *G*-weighted polar second moment of area and *f* the assembled load vector.

The mesh is a structured triangular grid (240 × 640 elements) covering the full rectangular domain, with the local *G*ᵢ field assigned point-wise at each quadrature point.

### 3.2 Test Cases

Two rectangular cross-sections (B = 300 mm, D = 400 mm) are analysed. Both sections are composed of 60 % Material A and 40 % Material B by height (STEEL_FRAC = 0.4).

| Case | Layout |
|------|--------|
| **A** | Material B split equally between bottom and top layers (symmetric) |
| **B** | Material B concentrated entirely at the bottom (asymmetric) |

#### Material Properties

| Material | *E* [N/mm²] | *ν* [–] | *G* [N/mm²] |
|----------|------------|---------|------------|
| A (concrete-like) | 30 000 | 0.20 | 12 500 |
| B (steel-like)    | 200 000 | 0.30 | 76 923 |

---

## 4. Results

| Case | SP G-carrier *GJ* [N·mm²] | `skfem` *GJ* [N·mm²] | Difference [%] | SP doc *GJ* error [%] |
|------|--------------------------|----------------------|---------------|-----------------------|
| A    | 4.5983 × 10¹³            | 4.5978 × 10¹³        | −0.012        | −4.11                 |
| B    | 5.1046 × 10¹³            | 5.1042 × 10¹³        | −0.008        | −2.63                 |

The column **SP G-carrier** refers to the result obtained from `sectionproperties` with the G-carrier substitution described in Section 2. The column **`skfem` G-carrier** is the fully independent FEM result. The column **SP doc *GJ* error** quantifies the discrepancy between the library's documented global correction and the local G-carrier result, taken as reference.

---

## 5. Discussion

The G-carrier results from `sectionproperties` and `skfem` agree to within 0.012 % across both test cases. The residual difference is attributable solely to the difference in mesh refinement between the two solvers (triangular unstructured mesh in `sectionproperties` vs. structured 240 × 640 grid in `skfem`).

The documented global correction ($g_\text{eff}/e_\text{eff}$ scaling) introduces errors of −4.1 % and −2.6 % for cases A and B respectively. The error is larger for the symmetric case (A), where the two high-stiffness layers are spatially separated, amplifying the inadequacy of a single global scalar multiplier.

---

## 6. Conclusion

Substituting *G*ᵢ for *E*ᵢ in the `sectionproperties` material definition is a correct and sufficient procedure to compute *GJ* for composite cross-sections. The approach is verified against an independent `skfem` implementation of the warping problem, with agreement better than 0.02 % for both a symmetric and an asymmetric material layout. The library's documented global correction should not be used when an accurate spatial distribution of *GJ* is required.

---

*Verification performed with `sectionproperties` and `scikit-fem`. Reference script: `skitfem_comparison.py`.*
