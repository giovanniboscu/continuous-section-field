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


## 3. Visualization
CSF includes a dedicated `Visualizer` class:
* **2D Plots**: Weighted sections, centroids, and principal axes.
* **3D Rendering**: Wireframe of the ruled solid to visualize the vertex trajectories and ensure topological consistency.
