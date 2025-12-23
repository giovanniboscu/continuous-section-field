# Continuous Section Field (CSF)

**CSF** is a Python library for the geometric and mechanical modeling of **single non-prismatic structural members** (slender beams with variable cross-sections).

> [!IMPORTANT]
> **Not a FEM Solver**: This library is **not** a Finite Element Method (FEM) software. It is a geometric and constitutive "engine" designed to model the continuous variation of a single member. It provides the stiffness matrices and sectional properties required for structural analysis, acting as a high-accuracy pre-processor or a kernel for beam theory applications.

---

## 1. Theoretical Framework: Overcoming Discretization Dependence
The common practice of modeling non-prismatic members as a concatenation of equivalent prismatic elements (**piecewise-prismatic approach**) introduces a non-neutral methodological choice. The numerical solution varies with the number of subdivisions and the location of sampling points.

**CSF** treats the single member as a **continuous manifold** using **ruled surfaces**. By defining the member’s geometry through explicit analytical functions (linear interpolation of vertices), the library ensures that:
* The structural response is an intrinsic property of the geometry.
* Physical properties (Area, Inertia) are defined at every infinitesimal coordinate $z$.
* Arbitrariness is confined exclusively to the solver level, ensuring reproducibility.

---

## 2. Key Features

### Ruled Surface Geometry (Vertex Mapping)
The library generates the 3D volume by connecting a "Start" polygon ($z_0$) and an "End" polygon ($z_1$).

* **Linear Interpolation**: Each vertex of the cross-section is described as a linear function of the longitudinal coordinate.
* **Continuous Transition**: This mapping creates ruled surfaces that define a smooth variation of the section, making vertex coordinates polynomial functions of known degree.

### The Role of Polygons: Homogenization & Voids
Polygons in CSF are the fundamental units for both geometry and mechanics:
* **Multi-material sections**: Each polygon carries a `weight` attribute ($n = E_i / E_{ref}$). This allows the modeling of composite sections (e.g., steel-reinforced timber) by calculating the **Elastic Centroid**.
* **Hole Modeling (Algebraic Voids)**: By assigning a **weight of -1.0**, a polygon acts as a hole. The library automatically subtracts its area and inertia from the total, allowing for effortless modeling of hollow tubes or cellular beams without complex boolean operations.

### Advanced Property Digestor
For any point $z$ along the axis, the library calculates:
* **Sectional Stiffness Matrix ($3 \times 3$)**: Rigorous coupling of axial and flexural stiffness ($EA, EI_x, EI_y, EI_{xy}$) via Gaussian Quadrature over triangulated domains.
* **Shear Analysis (Jourawski)**: Calculation of the **Partial Statical Moment ($Q$)** using a polygon clipping algorithm, enabling shear stress analysis on variable sections.
* **Volumetric Analysis**: Exact material volume calculation via integration of the area function $A(z)$.
---

## 3. Comprehensive Mechanical Property Digest

The library performs a multi-pass integration to extract every relevant structural parameter. All values are calculated at any coordinate $z$ and account for homogenization (weights) and voids (negative weights).

### A. Geometric & Mass Properties (Zeroth & First Moments)
These define the "quantity" and "position" of the section.
* **Weighted Area ($A$):** The homogenized net area $\sum A_i \cdot w_i$.
* **Elastic Centroid ($C_x, C_y$):** The center of stiffness relative to the global origin.
* **Total Volume ($V$):** The 3D integral of the area function $A(z)$ along the longitudinal axis.
* **Section Perimeter ($P$):** Total length of all polygon boundaries, used for surface-related calculations.

### B. Stiffness & Inertia (Second Moments)
Calculated relative to the **Centroidal Axes** via the Parallel Axis Theorem.
* **Centroidal Moments of Inertia ($I_{xx}, I_{yy}$):** Resistance to bending about horizontal and vertical axes.
* **Product of Inertia ($I_{xy}$):** Measure of sectional asymmetry; essential for unsymmetrical bending.
* **Polar Moment of Area ($J$):** Resistance to torsional deformation, calculated as $I_{xx} + I_{yy}$.
* **Sectional Stiffness Matrix ($[K]$):** A $3 \times 3$ constitutive matrix relating generalized strains ($\epsilon, \kappa_x, \kappa_y$) to internal actions ($N, M_x, M_y$).



### C. Derived & Principal Properties
Calculated via Mohr's Circle analysis for structural stability and orientation.
* **Principal Moments of Inertia ($I_1, I_2$):** The maximum and minimum possible second moments of area.
* **Principal Rotation Angle ($\theta$):** The inclination of the principal axes relative to the global system.
* **Radii of Gyration ($r_x, r_y$):** Measure of efficiency for buckling analysis, defined as $\sqrt{I/A}$.

### D. Strength & Shear Analysis
Properties used for stress verification at specific fibers.
* **Elastic Section Moduli ($W_x, W_y$):** Calculated using the extreme fiber distances ($y_{max}, y_{min}$) to find the maximum bending stress $\sigma = M/W$.
* **Extreme Fiber Distances:** The maximum distances from the neutral axis to the outer vertices of the polygons.
* **Partial Statical Moment ($Q$):** Calculated for the portion above a cut $y_{cut}$ using the **Sutherland-Hodgman clipping algorithm**; required for Jourawski shear stress ($\tau = VQ/It$).

---
## 6. Model Validation: Circular Hollow Section
<br>
<img width="513" height="675" alt="cilinder_withcheck" src="https://github.com/user-attachments/assets/6ea0c8e5-4cc9-4d9a-8773-c9318cbe9ddb" />

To verify the accuracy of the numerical engine, a validation test was performed using a **non-tapered hollow cylinder** (Steel Pipe). This allows for a direct comparison between the library's results (based on weighted polygons) and exact analytical formulas.

The test script `cilinder_withcheck.py` models a tower with a diameter of 4.935m and a thickness of 23mm using a 128-sided polygon. The results demonstrate that the polygonal approximation converges to the analytical solution with exceptional precision.

### Extended Validation Report
The following table reports the full output of the validation script, comparing **Theoretical (Analytical)** values with the **Numerical** results generated by the library.

| Structural Property | Sym | Theoretical | Numerical | Error % | Unit |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Net material cross-section** | A | 3.54924572e-01 | 3.54782053e-01 | 0.0402% | m^2 |
| **Horizontal center of mass** | Cx | 0.00000000e+00 | 8.24051633e-15 | 8.24e-15 (abs) | m |
| **Vertical center of mass** | Cy | 0.00000000e+00 | 1.30616095e-14 | 1.31e-14 (abs) | m |
| **Axial stiffness** | EA | 7.45341600e+10 | 7.45042311e+10 | 0.0402% | N |
| **Bending stiffness about X** | EIxx | 2.24797570e+11 | 2.24617080e+11 | 0.0803% | N*m^2 |
| **Bending stiffness about Y** | EIyy | 2.24797570e+11 | 2.24617080e+11 | 0.0803% | N*m^2 |
| **Symmetry check (Ixy)** | Ixy | 0.00000000e+00 | 4.83640905e-15 | 4.84e-15 (abs) | m^4 |
| **Torsional stiffness constant** | J | 2.14092924e+00 | 2.13921029e+00 | 0.0803% | m^4 |
| **Torsional stiffness (GJ)** | GJ | 1.72987083e+11 | 1.72848191e+11 | 0.0803% | N*m^2 |
| **Maximum bending stiffness** | EI_max | 2.24797570e+11 | 2.24617080e+11 | 0.0803% | N*m^2 |
| **Minimum bending stiffness** | EI_min | 2.24797570e+11 | 2.24617080e+11 | 0.0803% | N*m^2 |
| **Principal axis rotation** | Alpha | 0.00000000e+00 | 0.00000000e+00 | 0.0000% (Iso) | deg |
| **Buckling radius about X** | rx | 1.73667329e+00 | 1.73632461e+00 | 0.0201% | m |
| **Buckling radius about Y** | ry | 1.73667329e+00 | 1.73632461e+00 | 0.0201% | m |
| **First moment of area (Shear)** | Q | 2.77471084e-01 | 2.77303971e-01 | 0.0602% | m^3 |
| **Elastic Section Modulus** | W | 4.33825580e-01 | 4.33477262e-01 | 0.0803% | m^3 |
| **Mass per unit length** | m_lin | 2.78615789e+03 | 2.78503911e+03 | 0.0402% | kg/m |

### Global Mass & Volume Summary
* **Total Calculated Tower Volume:** 31.078908 m³
* **Total Calculated Tower Mass:** 243.969426 t
* **Analytical vs Numerical Mass Error:** **0.0402%**
  
## 7. Advanced Validation: NREL 5-MW Reference Wind Turbine Tower

<img width="424" height="630" alt="5-MW" src="https://github.com/user-attachments/assets/73fe46a0-b778-489c-9f49-980ea3d0a20e" />


To demonstrate the library's performance on complex, real-world structural members, a full-scale model of the **NREL 5-MW Reference Wind Turbine Tower** was implemented. The geometry and material properties strictly follow the technical report *"Definition of a 5-MW Reference Wind Turbine for Offshore System Development"* (NREL/TP-500-38060).

The following tables provide a side-by-side comparison between the **Numerical results generated by CSF** and the **Official NREL Reference Data (Table 6-1)**.

### CSF Numerical Results (Generated Model)
| Elevation [m] | HtFract | TMassDen [kg/m] | TwFAStif [N·m²] | TwSSStif [N·m²] | TwGJStif [N·m²] | TwEAStif [N] | TwFAIner [kg·m] | TwSSIner [kg·m] |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0.00 | 0.000 | 4306.07 | 4.7440e+11 | 4.7440e+11 | 3.6506e+11 | 1.0639e+11 | 1.92e+04 | 1.92e+04 |
| 8.76 | 0.100 | 4030.04 | 4.1300e+11 | 4.1300e+11 | 3.1781e+11 | 9.9566e+10 | 1.67e+04 | 1.67e+04 |
| 17.52 | 0.200 | 3763.07 | 3.5775e+11 | 3.5775e+11 | 2.7530e+11 | 9.2970e+10 | 1.45e+04 | 1.45e+04 |
| 26.28 | 0.300 | 3505.17 | 3.0823e+11 | 3.0823e+11 | 2.3719e+11 | 8.6598e+10 | 1.25e+04 | 1.25e+04 |
| 35.04 | 0.400 | 3256.33 | 2.6403e+11 | 2.6403e+11 | 2.0318e+11 | 8.0450e+10 | 1.07e+04 | 1.07e+04 |
| 43.80 | 0.500 | 3016.56 | 2.2475e+11 | 2.2475e+11 | 1.7295e+11 | 7.4527e+10 | 9.10e+03 | 9.10e+03 |
| 52.56 | 0.600 | 2785.85 | 1.9002e+11 | 1.9002e+11 | 1.4622e+11 | 6.8827e+10 | 7.69e+03 | 7.69e+03 |
| 61.32 | 0.700 | 2564.21 | 1.5946e+11 | 1.5946e+11 | 1.2271e+11 | 6.3351e+10 | 6.45e+03 | 6.45e+03 |
| 70.08 | 0.800 | 2351.63 | 1.3274e+11 | 1.3274e+11 | 1.0215e+11 | 5.8099e+10 | 5.37e+03 | 5.37e+03 |
| 78.84 | 0.900 | 2148.12 | 1.0951e+11 | 1.0951e+11 | 8.4274e+10 | 5.3071e+10 | 4.43e+03 | 4.43e+03 |
| 87.60 | 1.000 | 1953.67 | 8.9470e+10 | 8.9470e+10 | 6.8849e+10 | 4.8267e+10 | 3.62e+03 | 3.62e+03 |

&nbsp;

### Official NREL 5-MW Tower Data (Reference Table 6-1)
| Elevation [m] | HtFract | TMassDen [kg/m] | TwFAStif [N·m²] | TwSSStif [N·m²] | TwGJStif [N·m²] | TwEAStif [N] | TwFAIner [kg·m] | TwSSIner [kg·m] |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0.00 | 0.000 | 4306.0 | 4.744e+11 | 4.744e+11 | 3.651e+11 | 1.064e+11 | 1.92e+04 | 1.92e+04 |
| 8.76 | 0.100 | 4030.0 | 4.130e+11 | 4.130e+11 | 3.178e+11 | 9.957e+10 | 1.67e+04 | 1.67e+04 |
| 17.52 | 0.200 | 3763.1 | 3.578e+11 | 3.578e+11 | 2.753e+11 | 9.298e+10 | 1.44e+04 | 1.44e+04 |
| 26.28 | 0.300 | 3505.2 | 3.082e+11 | 3.082e+11 | 2.372e+11 | 8.661e+10 | 1.24e+04 | 1.24e+04 |
| 35.04 | 0.400 | 3256.3 | 2.640e+11 | 2.640e+11 | 2.032e+11 | 8.046e+10 | 1.07e+04 | 1.07e+04 |
| 43.80 | 0.500 | 3016.6 | 2.248e+11 | 2.248e+11 | 1.730e+11 | 7.453e+10 | 9.08e+03 | 9.08e+03 |
| 52.56 | 0.600 | 2785.8 | 1.900e+11 | 1.900e+11 | 1.462e+11 | 6.883e+10 | 7.67e+03 | 7.67e+03 |
| 61.32 | 0.700 | 2564.2 | 1.595e+11 | 1.595e+11 | 1.227e+11 | 6.335e+10 | 6.44e+03 | 6.44e+03 |
| 70.08 | 0.800 | 2351.6 | 1.327e+11 | 1.327e+11 | 1.021e+11 | 5.810e+10 | 5.36e+03 | 5.36e+03 |
| 78.84 | 0.900 | 2148.1 | 1.095e+11 | 1.095e+11 | 8.427e+10 | 5.307e+10 | 4.42e+03 | 4.42e+03 |
| 87.60 | 1.000 | 1953.7 | 8.947e+10 | 8.947e+10 | 6.885e+10 | 4.827e+10 | 3.61e+03 | 3.61e+03 |


### Scientific Observation
The alignment between the CSF results and the NREL data is nearly perfect. Small discrepancies (e.g., in mass or inertia) are due to the fact that NREL data is often rounded for publication, while CSF maintains double-precision accuracy throughout its internal integration of the ruled surface. This comparison confirms the library's ability to accurately handle **continuously varying tapered sections** in high-stakes engineering applications.

## 8. References & Official Documentation

This project was developed and validated using the following official engineering standards and technical references:

### Wind Energy Reference Models
* **NREL 5-MW Reference Wind Turbine**: The tower validation is based on the official technical report:
  > *Jonkman, J., Butterfield, S., Musial, W., and Scott, G., "Definition of a 5-MW Reference Wind Turbine for Offshore System Development," NREL Technical Report NREL/TP-500-38060, February 2009.*
  * [**Download Official PDF (NREL)**](https://www.nrel.gov/docs/fy09osti/38060.pdf)
  * [**Project Page at NREL.gov**](https://www.nrel.gov/wind/data-models.html)

### Key Structural Concepts
* **Ruled Surfaces in Architecture/Engineering**: The geometric engine uses linear interpolation between sections, a principle used in hyperbolic cooling towers and tapered bridge piers.
* **Sutherland-Hodgman Algorithm**: Used for the exact calculation of the Statical Moment ($Q$) via polygon clipping.
  * [Reference on Computer Graphics and Geometric Modeling](https://en.wikipedia.org/wiki/Sutherland%E2%80%93Hodgman_algorithm)

### How to Cite this Library
If you use **CSF** in your research, academic work, or professional projects, please cite it as follows:

##  Documentation & Code Comments

The library is designed with a **"self-documenting code"** approach. For developers and engineers who wish to dive deeper into the mathematical implementations or extend the library's functionality:

* **Well-Commented Source**: The main file `section_field.py` is extensively documented with internal comments, docstrings, and explicit assumptions.
* **Inline Instructions**: Every core function (from the Sutherland-Hodgman clipping to the Gaussian quadrature integrals) includes a description of its input parameters and expected physical units.
* **Developer Friendly**: You can find detailed explanations of the vertex-mapping logic and the stiffness matrix assembly directly above the respective function definitions.


### How to Cite
If you use **CSF** in your research, academic work, or professional projects, please cite it as follows:

> Boscu, G. (2025). **Continuous Section Field (CSF)**: A geometric and mechanical engine for non-prismatic structural members. Available at: https://github.com/giovanniboscu/
