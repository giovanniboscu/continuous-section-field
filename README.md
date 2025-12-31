**[Key Features](#key-features)** • **[Setup Environment (Linux & Windows)](#setup-environment-linux--windows)** • **[Practical Example](#8-practical-example-continuously-tapered-t-beam)** • **[Model Validation (Cylinder)](#5-model-validation-circular-hollow-section)** • **[NREL 5-MW Validation](#6-advanced-validation-nrel-5-mw-reference-wind-turbine-tower)**

# Continuous Section Field (CSF) Python Tool for Analyzing Tapered Generic Structural Members
Continuous Section Field (CSF) is a Python library for the continuous modeling of non-prismatic structural members.
It computes sectional and stiffness properties without resorting to piecewise-prismatic discretization.
## An Analytical Engine for Non-Prismatic Structural Members
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18063427.svg)](https://doi.org/10.5281/zenodo.18063427)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Math](https://img.shields.io/badge/Engine-Analytical_Mechanics-red.svg)
![Integration](https://img.shields.io/badge/Integration-Gaussian_Quadrature-green.svg)
![License](https://img.shields.io/github/license/giovanniboscu/continuous-section-field)
![Repo Size](https://img.shields.io/github/repo-size/giovanniboscu/continuous-section-field)



**CSF** is a Python library for the geometric and mechanical modeling of **single non-prismatic structural members** (slender beams with variable cross-sections). Here below the CSF model of  NREL 5-MW Tower 


<img width="423" height="609" alt="NREL-5-MW" src="https://github.com/user-attachments/assets/712ec7c1-3b7c-4a99-aa7d-791dbbc6eb53" />


[See full NREL 5‑MW validation ](#6-advanced-validation-nrel-5-mw-reference-wind-turbine-tower)

### **Arbitrary Cross-Section Support**
Unlike traditional structural tools limited to predefined geometric templates, this library treats the cross-section as a **fully generic topological entity**.
Python tool for accurate, continuous calculation of cross-section properties for complex non-prismatic members (tapered beams, wind turbine towers, piles, variable columns, FGM materials).

> [!IMPORTANT]
> **Not a FEM Solver**: This library is **not** a Finite Element Method (FEM) software. It is a geometric and constitutive "engine" designed to model the continuous variation of a single member. It provides the stiffness matrices and sectional properties required for structural analysis, acting as a high-accuracy pre-processor or a kernel for beam theory applications.
---
## Key Features

- **Algebraic Polygon Logic**: Sections defined as collections of 2D vertices with weights. Handles any shape — from standard profiles to fully custom architectural sections.
- **Curvature Handling**: Discrete segments with arbitrary vertex count → approximate curved surfaces (e.g., circular towers) to any desired precision.
- **No Predefined Templates**: No restricted "Circle" or "Rectangle" classes — any geometry describable by coordinates is supported (A, I, J, Q, etc.).
- **Topological Freedom**:
  - Hollow sections (e.g., NREL tapered shell)
  - Multi-cellular shapes with internal stiffeners
  - Composite/multi-material sections via modular ratio weights
- Version 2: fully arbitrary `w(z)` per polygon  
  → non-linear thickness, modulus, or reinforcement variation  
  → access to `w₀`, `w₁`, current/initial/end distances `d(i,j)`, `di(i,j)`, `de(i,j)`, and all `math` functions
- Algebraic void handling (`w < 0`)
- Beta OpenSees export (midpoint integration)
- Lightweight, no GUI, no built-in FEM: pure Python for custom scripts or integration with PyNite/OpenSeesPy
---
## 🛠 Installation & Quick Start

To use the **CSF** engine, it is recommended to use a virtual environment to keep dependencies isolated.
###  Setup Environment linux & windows
```bash
LINUX
# Clone the repository
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in editable mode
pip install -e .
python3 example/nrel_5mw_tower.py 
python3 example/cilinder_withcheck.py
python3 example/csf_rotated_validation_benchmark.py

WINDOWS

# Clone the repository
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

# Create and activate virtual environment
python3 -m venv venv
.\venv\Scripts\activate

# Install in editable mode
pip install -e .
python3 example\nrel_5mw_tower.py 
python3 example\cilinder_withcheck.py
python3 example\csf_rotated_validation_benchmark.py
python3 .\example\tsection_opensees.py
```
---
 **[Practical Example](#8-practical-example-continuously-tapered-t-beam)** 
---
## Theoretical Framework: Overcoming Discretization Dependence
The common practice of modeling non-prismatic members as a concatenation of equivalent prismatic elements (**piecewise-prismatic approach**) introduces a non-neutral methodological choice. The numerical solution varies with the number of subdivisions and the location of sampling points.

## **CSF** treats the single member as a **continuous manifold** using **ruled surfaces**.

## 1. Reference System

Sections are modeled as ruled surfaces linearly interpolated between two arbitrary end sections

Two section planes are defined:

- start section at \( z = 0 \)
- end section at \( z = L \)

Both sections are defined in the **same local $x$ – $y$ coordinate system**.

- The two section planes are **parallel and not rotated** with respect to each other.
- The beam axis is aligned with the **\( z \)-axis**, normal to the section planes.

All section geometries must be provided in this local reference system.

## 2. Section Geometry

### 2.1 Polylines

A section is defined by a **set of closed polylines**.

- Each polyline represents a **material region**.
- All polylines must be:
  - non self-intersecting
  - oriented **counter-clockwise (CCW)**
  - Polylines are closed implicitly; do not repeat the first vertex at the end of the list.


### Notes and Limitations

- Polylines must not self-intersect or overlap.
- Topological changes along the beam are not supported.
- Advanced material effects (e.g. torsion with multiple materials) may require
  two-dimensional numerical analysis.
- Geometric consistency is the responsibility of the user.

### 2.2 Polyline Weight (Material Coefficient)

Each polyline is assigned a **scalar weight** \( w \), defined as:

$$
w = \frac{E}{E_{\text{ref}}}
$$

where:

 $E$ is the Young’s modulus of the region
- $E_{\text{ref}}$ is the reference Young’s modulus

Typical values:

- $w = +1$: reference material  
- $0 < w < 1$: softer material  
- $w > 1$: stiffer material  
- $w = -1$: void (geometric hole)

All polylines use the same orientation; material addition or removal is controlled
exclusively by the sign of **$w$**

## 2.3 Extreme Sections

Two sections must be provided:

- one at $z = 0$
- one at $z = L$

Both sections must contain:

- the **same number of polylines**
- the **same polyline IDs**
- the **same weights \( w \)**

This ensures **geometric and material continuity** along the beam axis.

### The Role of Polygons: Homogenization & Voids
Polygons in CSF are the fundamental units for both geometry and mechanics:
* **Multi-material sections**: Each polygon carries a `weight` attribute ($n = E_i / E_{ref}$). This allows the modeling of composite sections (e.g., steel-reinforced timber) by calculating the **Elastic Centroid**.
* **Hole Modeling (Algebraic Voids)**: By assigning a **weight of -1.0**, a polygon acts as a hole. The library automatically subtracts its area and inertia from the total, allowing for effortless modeling of hollow tubes or cellular beams without complex boolean operations.

## 2.4 Geometric Interpolation

- Corresponding polylines at $z = 0$ and $z = L$ are interpolated along the beam axis.
- Interpolation is performed **point-wise between matching vertices**.

### Ruled Surfaces and Vertex Interpolation

The 3D volume is generated by connecting a **Start** section at $z_{start}$ and an **End** section at $z_{end}$ using **ruled surfaces**.

For each vertex $P_i$, the generator line is defined as:

$$
P_i(z) = P_{i,start} + \frac{z - z_{start}}{z_{end} - z_{start}} \cdot (P_{i,end} - P_{i,start})
$$

**Geometric results**:
- **Linear Interpolation**: Each vertex of the cross-section is described as a linear function of the longitudinal coordinate.
- **Ruled Surfaces**: This mapping creates ruled surfaces that define a smooth variation of the section, making vertex coordinates polynomial functions of known degree.
- **Continuous taper**: smooth transition between different shapes (e.g. tapered T-beams, conical tubes)
- **Continuous properties**: $A(z)$, $I(z)$, $EA(z)$, $EI(z)$, $GJ(z)$ defined analytically along the entire axis

## 2.5 Section Properties

Section properties (area, inertia) are computed from geometry as:

$$
\text{Property}(z) = \sum_k w_k \, \text{Property}_k(z)
$$

- Geometry is the primary input.
- Section properties are automatically derived.

## 3. Sectional Analysis Engine

The library is designed for the analysis of non-prismatic and non-homogeneous members,
with section properties varying continuously along the longitudinal axis.

## Technical Methodology & Integration Schemes

The engine employs a **multi-pass analysis** combined with **Gaussian integration schemes** to extract structural parameters with high numerical fidelity. Specifically engineered for **tapered and non-homogeneous members**, it is ideal for applications where sectional properties vary continuously along the longitudinal axis (e.g., wind turbine towers, bridge girders, or aerospace components).

####  Multi-Pass Analysis Workflow
To ensure accuracy, the library processes geometry in distinct logical stages:
* **Geometric Pass**: Uses the **Shoelace algorithm** (Surveyor's formula) to determine net area and first moments, applying **Steiner’s Parallel Axis Theorem** to translate results to the centroid.
* **Principal Axis Pass**: Performs eigen-decomposition of the inertia tensor (Mohr's Circle logic) to identify principal moments ($I_1, I_2$) and the rotation angle ($\theta$).

####  Gaussian Integration Schemes (Numerical Quadrature)
For complex constitutive properties, the library moves beyond simple boundary integration:
* **Stiffness Matrix Calculation**: To compute the exact sectional stiffness matrix $[K]$, the engine performs **Gaussian quadrature** on triangulated sub-domains. 
* **Sub-domain Triangulation**: Each polygon is decomposed into triangles where integration points and weights are applied, allowing the model to handle variations in Elastic Moduli ($E$) across the section.

####  Continuous Longitudinal Mapping
Unlike traditional frame analysis software that treats members as prismatic, this library treats the member as a **Continuous Section Field**:
* **Dynamic Computation**: Every property is calculated "on-the-fly" at any longitudinal coordinate $z$ via linear vertex-mapping.
* **Homogenization & Voids**: Full support for material homogenization through **positive weights** and internal voids or cut-outs through **negative weights**.

#### The CSF library natively provides

Primary & Centroidal Properties
| ID | Parameter | Symbol | Technical Description |
| :--- | :--- | :---: | :--- |
| 1 | **Area** | $A$ | Total net cross-sectional area |
| 2 | **Centroid Cx** | $C_x$ | Horizontal coordinate of the geometric centroid |
| 3 | **Centroid Cy** | $C_y$ | Vertical coordinate of the geometric centroid |
| 4 | **Inertia Ix** | $I_x$ | Second moment of area about centroidal X-axis |
| 5 | **Inertia Iy** | $I_y$ | Second moment of area about centroidal Y-axis |
| 6 | **Inertia Ixy** | $I_{xy}$ | Product of inertia (Zero indicates symmetry) |
| 7 | **Polar Moment** | $J$ | Polar moment of area ($I_x + I_y$) |



Derived Geometric Properties
| ID | Parameter | Symbol | Technical Description |
| :--- | :--- | :---: | :--- |
| 8 | **Principal I1** | $I_1$ | Maximum Principal Moment of Area |
| 9 | **Principal I2** | $I_2$ | Minimum Principal Moment of Area |
| 10 | **Radius rx** | $r_x$ | Radius of gyration about X: $\sqrt{I_x/A}$ |
| 11 | **Radius ry** | $r_y$ | Radius of gyration about Y: $\sqrt{I_y/A}$ |

Structural Analysis (Strength & Rigidity)
| ID | Parameter | Symbol | Technical Description |
| :--- | :--- | :---: | :--- |
| 12 | **Elastic Modulus Wx** | $W_x$ | Section modulus for bending about X ($I_x / y_{max}$) |
| 13 | **Elastic Modulus Wy** | $W_y$ | Section modulus for bending about Y ($I_y / x_{max}$) |
| 14 | **Torsional Rigidity** | $K$ | Torsional Rigidity (K) The Saint-Venant torsional constant ($J$) is notoriously complex for non-circular sections. In this Beta version:</br> Core Engine: Implements a semi-empirical approximation ($J \approx A^4 / 40I_p$). </br> Purpose: This estimation is designed to provide numerical stability for 3D Finite Element models (e.g., OpenSees) where a null torsional stiffness would lead to singular matrices.</br> Accuracy: While reliable for solid, compact sections, it is a simplified model. For thin-walled or open profiles, users should treat this value as a preliminary estimate|


Shear & Verification Data
| ID | Parameter | Symbol | Technical Description |
| :--- | :--- | :---: | :--- |
| 15 | **Poly 0 Ix (Origin)** | $I_{x0}$ | Polygon 0 inertia relative to global origin |
| 16 | **Poly 0 Q_local** | $Q_{p0}$ | Statical moment of Poly 0 relative to centroid |
| 17 | **Section Q_na** | $Q_{na}$ | Total Statical Moment at Neutral Axis (for $\tau$ shear) |
| 18 | **Stiffness Shape** | Matrix | Dimensionality of the Sectional Stiffness Matrix $[K]$ |

---

## 4. OpenSees Analysis Integration (BETA)

> ** Beta Phase Notice**: This module is in active development. While geometric and stiffness calculations are verified for tapered beam configurations, users should validate results for complex thin-walled or open sections.

This library bridges the gap between complex geometric modeling and structural simulation by providing a high-level API for **OpenSees** model generation.

### Automated FEM Discretization
* **Midpoint Integration**: Sectional properties are automatically sampled at the center of each finite element to accurately capture non-prismatic (tapering) effects.
* **Full Model Generation**: The exporter generates complete `.tcl` environments, including nodal coordinates, element connectivity, and basic analysis patterns.

### Advanced Property Digestor
For any point $z$ along the axis, the library computes:
* **Sectional Stiffness Matrix**: Rigorous derivation of $EA, EI_x, EI_y, EI_{xy}$ using Gaussian Quadrature over triangulated domains.
* **Torsional Estimation**: Implements a robust semi-empirical approximation for the torsional constant ($J \approx A^4 / 40I_p$) to ensure numerical stability in 3D analysis for solid sections.
* **Shear Analysis (Jourawski)**: Calculates the **Statical Moment ($Q$)** via a custom polygon clipping algorithm, enabling shear stress evaluation on variable cross-sections.
---

## 5. Model Validation: Circular Hollow Section
examples/cilinder_withcheck.py

<img width="520" height="509" alt="circeltest" src="https://github.com/user-attachments/assets/b3384be1-0a35-4654-b39b-aae614703ad0" />

To verify the accuracy of the numerical engine, a validation test was performed using a **non-tapered hollow cylinder** (Steel Pipe). This allows for a direct comparison between the library's results (based on weighted polygons) and exact analytical formulas.

The test script `cilinder_withcheck.py` models a tower with a diameter of 4.935m and a thickness of 23mm using a 512-sided polygon. The results demonstrate that the polygonal approximation converges to the analytical solution with exceptional precision.

### Extended Validation Report
The following table reports the full output of the validation script, comparing **Theoretical (Analytical)** values with the **Numerical** results generated by the library.

| Structural Property                  | Sym    | Theoretical        | Numerical          | Error             | Unit |
|-------------------------------------|--------|--------------------|--------------------|-------------------|------|
| Net material cross-section          | A      | 3.54924572e-01     | 3.54915663e-01     | 0.0025%           | m²   |
| Horizontal center of mass           | Cx     | 0.00000000e+00     | 5.44816314e-15     | 5.45e-15 (abs)    | m    |
| Vertical center of mass             | Cy     | 0.00000000e+00     | -4.12383916e-14    | 4.12e-14 (abs)    | m    |
| Axial stiffness                     | EA     | 7.45341600e+10     | 7.45322893e+10     | 0.0025%           | N    |
| Bending stiffness about X           | EIxx   | 2.24797570e+11     | 2.24786286e+11     | 0.0050%           | N·m² |
| Bending stiffness about Y           | EIyy   | 2.24797570e+11     | 2.24786286e+11     | 0.0050%           | N·m² |
| Symmetry check (Ixy)                | Ixy    | 0.00000000e+00     | 3.45889405e-15     | 3.46e-15 (abs)    | m⁴   |
| Torsional stiffness constant        | J      | 2.14092924e+00     | 2.14082177e+00     | 0.0050%           | m⁴   |
| Torsional stiffness (GJ)            | GJ     | 1.72987083e+11     | 1.72978399e+11     | 0.0050%           | N·m² |
| Maximum bending stiffness           | EI_max | 2.24797570e+11     | 2.24786286e+11     | 0.0050%           | N·m² |
| Minimum bending stiffness           | EI_min | 2.24797570e+11     | 2.24786286e+11     | 0.0050%           | N·m² |
| Principal axis rotation             | Alpha  | 0.00000000e+00     | 0.00000000e+00     | 0.0000% (Iso)     | deg  |
| Buckling radius about X             | rx     | 1.73667329e+00     | 1.73665150e+00     | 0.0013%           | m    |
| Buckling radius about Y             | ry     | 1.73667329e+00     | 1.73665150e+00     | 0.0013%           | m    |
| First moment of area (Shear)        | Q      | 2.77471084e-01     | 2.77460637e-01     | 0.0038%           | m³   |
| Elastic Section Modulus             | W      | 4.33825580e-01     | 4.33803803e-01     | 0.0050%           | m³   |
| Mass per unit length                | m_lin  | 2.78615789e+03     | 2.78608796e+03     | 0.0025%           | kg/m |

**Total Calculated Tower Volume:** 31.041 m³  
**Total Calculated Tower Mass:**   243.676 t  

| Description          | Theoretical | Numerical | Error   | Unit |
|----------------------|-------------|-----------|---------|------|
| Total Tower Mass     | 244.067     | 244.061   | 0.0025% | t    |

  
## 6. Advanced Validation: NREL 5-MW Reference Wind Turbine Tower
Official research portal of the National Renewable Energy Laboratory providing authoritative wind energy data, reference turbine models, technical reports, and validated simulation tools. It serves as a primary source for benchmark wind turbine definitions, including the NREL 5-MW reference model.

## 512-sided polygons

<img width="423" height="609" alt="NREL-5-MW" src="https://github.com/user-attachments/assets/712ec7c1-3b7c-4a99-aa7d-791dbbc6eb53" />

**CSF** computes continuous sectional properties along the tower height \(z\) - \(A(z)\), \(EI(z)\), \(GJ(z)\), etc. - compatible with OpenFAST ElastoDyn/SubDyn distributed property requirements and validated against NREL 5‑MW reference data.


example/nrel_5mw_tower.py is to demonstrate the library's performance on complex, real-world structural members, a full-scale model of the **NREL 5-MW Reference Wind Turbine Tower** was implemented. The geometry and material properties strictly follow the technical report *"Definition of a 5-MW Reference Wind Turbine for Offshore System Development"* (NREL/TP-500-38060).

The following tables provide a side-by-side comparison between the **Numerical results generated by CSF** and the **Official NREL Reference Data (Table 6-1) pdf official doc**.

Density = 8.500 kg/m3
### CSF Numerical Results (Generated Model)

| Elevation [m] | HtFract | TMassDen [kg/m] | TwFAStif [N·m²] | TwSSStif [N·m²] | TwGJStif [N·m²] | TwEAStif [N] | TwFAIner [kg·m] | TwSSIner [kg·m] |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0.00 | 0.000 | 5590.73 | 6.1431e+11 | 6.1431e+11 | 4.7273e+11 | 1.3812e+11 | 2.49e+04 | 2.49e+04 |
| 8.76 | 0.100 | 5232.30 | 5.3479e+11 | 5.3479e+11 | 4.1154e+11 | 1.2927e+11 | 2.16e+04 | 2.16e+04 |
| 17.52 | 0.200 | 4885.64 | 4.6324e+11 | 4.6324e+11 | 3.5648e+11 | 1.2070e+11 | 1.88e+04 | 1.88e+04 |
| 26.28 | 0.300 | 4550.76 | 3.9911e+11 | 3.9911e+11 | 3.0713e+11 | 1.1243e+11 | 1.62e+04 | 1.62e+04 |
| 35.04 | 0.400 | 4227.65 | 3.4187e+11 | 3.4187e+11 | 2.6307e+11 | 1.0445e+11 | 1.38e+04 | 1.38e+04 |
| 43.80 | 0.500 | 3916.31 | 2.9100e+11 | 2.9100e+11 | 2.2393e+11 | 9.6756e+10 | 1.18e+04 | 1.18e+04 |
| 52.56 | 0.600 | 3616.74 | 2.4601e+11 | 2.4601e+11 | 1.8931e+11 | 8.9355e+10 | 9.96e+03 | 9.96e+03 |
| 61.32 | 0.700 | 3328.95 | 2.0645e+11 | 2.0645e+11 | 1.5887e+11 | 8.2245e+10 | 8.36e+03 | 8.36e+03 |
| 70.08 | 0.800 | 3052.93 | 1.7184e+11 | 1.7184e+11 | 1.3224e+11 | 7.5425e+10 | 6.96e+03 | 6.96e+03 |
| 78.84 | 0.900 | 2788.68 | 1.4177e+11 | 1.4177e+11 | 1.0909e+11 | 6.8897e+10 | 5.74e+03 | 5.74e+03 |
| 87.60 | 1.000 | 2536.21 | 1.1581e+11 | 1.1581e+11 | 8.9122e+10 | 6.2659e+10 | 4.69e+03 | 4.69e+03 |


**Total Calculated Tower Volume:** 40.8634 m³  
**Total Calculated Tower Mass:**   347.339 t  
&nbsp;

### Official NREL 5-MW Tower Data (Reference Table 6-1) pag. 15 [**Download Official PDF (NREL)**](https://www.nrel.gov/docs/fy09osti/38060.pdf)

| Elevation [m] | HtFract | TMassDen [kg/m] | TwFAStif [N·m²] | TwSSStif [N·m²] | TwGJStif [N·m²] | TwEAStif [N] | TwFAIner [kg·m] | TwSSIner [kg·m] |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0.00 | 0.000 | 5590.9 | 6.143e+11 | 6.143e+11 | 4.728e+11 | 1.381e+11 | 2.49e+04 | 2.49e+04 |
| 8.76 | 0.100 | 5232.4 | 5.348e+11 | 5.348e+11 | 4.116e+11 | 1.293e+11 | 2.16e+04 | 2.16e+04 |
| 17.52 | 0.200 | 4885.8 | 4.633e+11 | 4.633e+11 | 3.565e+11 | 1.207e+11 | 1.88e+04 | 1.88e+04 |
| 26.28 | 0.300 | 4550.9 | 3.991e+11 | 3.991e+11 | 3.071e+11 | 1.124e+11 | 1.62e+04 | 1.62e+04 |
| 35.04 | 0.400 | 4227.8 | 3.419e+11 | 3.419e+11 | 2.631e+11 | 1.044e+11 | 1.38e+04 | 1.38e+04 |
| 43.80 | 0.500 | 3916.4 | 2.910e+11 | 2.9100e+11 | 2.239e+11 | 9.676e+10 | 1.18e+04 | 1.18e+04 |
| 52.56 | 0.600 | 3616.8 | 2.460e+11 | 2.460e+11 | 1.893e+11 | 8.936e+10 | 9.96e+03 | 9.96e+03 |
| 61.32 | 0.700 | 3329.0 | 2.065e+11 | 2.065e+11 | 1.589e+11 | 8.225e+10 | 8.36e+03 | 8.36e+03 |
| 70.08 | 0.800 | 3053.0 | 1.718e+11 | 1.718e+11 | 1.322e+11 | 7.543e+10 | 6.96e+03 | 6.96e+03 |
| 78.84 | 0.900 | 2788.8 | 1.418e+11 | 1.418e+11 | 1.091e+11 | 6.890e+10 | 5.74e+03 | 5.74e+03 |
| 87.60 | 1.000 | 2536.3 | 1.158e+11 | 1.158e+11 | 8.913e+10 | 6.266e+10 | 4.69e+03 | 4.69e+03 |

**Total CNREL 5-MW ref Mass:**  347,460 t

### Relative error (Generated − Reference) / Reference × 100

| Elevation [m] | HtFract | TMassDen [kg/m] | TwFAStif [N·m²] | TwSSStif [N·m²] | TwGJStif [N·m²] | TwEAStif [N] | TwFAIner [kg·m] | TwSSIner [kg·m] |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0.00% | 0.00% | 0.0030% | 0.0016% | 0.0016% | 0.0148% | 0.0145% | 0.00% | 0.00% |
| 0.00% | 0.00% | 0.0019% | 0.0019% | 0.0019% | 0.0146% | 0.0232% | 0.00% | 0.00% |
| 0.00% | 0.00% | 0.0033% | 0.0130% | 0.0130% | 0.0056% | 0.0000% | 0.00% | 0.00% |
| 0.00% | 0.00% | 0.0031% | 0.0025% | 0.0025% | 0.0098% | 0.0267% | 0.00% | 0.00% |
| 0.00% | 0.00% | 0.0035% | 0.0088% | 0.0088% | 0.0114% | 0.0479% | 0.00% | 0.00% |
| 0.00% | 0.00% | 0.0023% | 0.0000% | 0.0000% | 0.0134% | 0.0041% | 0.00% | 0.00% |
| 0.00% | 0.00% | 0.0017% | 0.0041% | 0.0041% | 0.0158% | 0.0056% | 0.00% | 0.00% |
| 0.00% | 0.00% | 0.0015% | 0.0242% | 0.0242% | 0.0189% | 0.0061% | 0.00% | 0.00% |
| 0.00% | 0.00% | 0.0023% | 0.0233% | 0.0233% | 0.0302% | 0.0066% | 0.00% | 0.00% |
| 0.00% | 0.00% | 0.0043% | 0.0212% | 0.0212% | 0.0092% | 0.0044% | 0.00% | 0.00% |
| 0.00% | 0.00% | 0.0035% | 0.0086% | 0.0086% | 0.0090% | 0.0016% | 0.00% | 0.00% |

## Summary

- All discrepancies are **well below 0.05%**.
- Differences are attributable to **rounding and numerical precision**.
- The generated CSF tower properties **faithfully reproduce** the NREL 5-MW reference.

This comparison confirms the library's ability to accurately handle **continuously varying tapered sections** in high-stakes engineering applications.

## NREL 5-MW References & Official Documentation

This project was developed and validated using the following official engineering standards and technical references:

### Wind Energy Reference Models
* **NREL 5-MW Reference Wind Turbine**: The tower validation is based on the official technical report:
  > *Jonkman, J., Butterfield, S., Musial, W., and Scott, G., "Definition of a 5-MW Reference Wind Turbine for Offshore System Development," NREL Technical Report NREL/TP-500-38060, February 2009.*
  * [**Download Official PDF (NREL)**](https://www.nrel.gov/docs/fy09osti/38060.pdf)
  * [**OpenFAST Documentation**](https://openfast.readthedocs.io/en/main/)
  * [**NREL Wind Research**](https://www.nrel.gov/wind/)

    
---

## 7. CSF Documentation and In-Depth Code Commentary

The library is designed with a **"self-documenting code"** approach. For developers and engineers who wish to dive deeper into the mathematical implementations or extend the library's functionality:

* **Well-Commented Source**: The main file `section_field.py` is extensively documented with internal comments, docstrings, and explicit assumptions.
* **Inline Instructions**: Every core function (from the Sutherland-Hodgman clipping to the Gaussian quadrature integrals) includes a description of its input parameters and expected physical units.
* **Developer Friendly**: You can find detailed explanations of the vertex-mapping logic and the stiffness matrix assembly directly above the respective function definitions.

---

## 8. Practical Example: Continuously Tapered T-Beam
This section demonstrates how to model a structural member where the geometry transitions smoothly between two different T-profiles.

### The Engineering Challenge
In standard FEM, a tapered beam is often approximated as a series of stepped prismatic segments. **CSF** instead treats the member as a **continuous ruled solid**, capturing the exact cubic variation of the moment of inertia $I(z)$ and the shift of the elastic centroid $C_y(z)$ without discretization errors.

<img width="456" height="469" alt="tsec3d" src="https://github.com/user-attachments/assets/03884190-0e15-43b4-a45d-b0ba9cacbbb7" />

<img width="503" height="464" alt="tsec2d" src="https://github.com/user-attachments/assets/a39e6e6e-afd1-43dd-b755-7299d211cd55" />

<details>python
<summary>Click to expand the full T-Beam Python example</summary>

```
    # ----------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------
    # 1. DEFINE START SECTION (Z = 0)
    # ----------------------------------------------------------------------------------
    #   GUIDELINES FOR POLYGON CONSTRUCTION:
    # - COUNTER-CLOCKWISE POLYGON
    # - VERTICES ORDER: You MUST define vertices in COUNTER-CLOCKWISE (CCW) order.
    #   This is MANDATORY for the Shoelace/Green's Theorem algorithm to compute a 
    #   POSITIVE Area and correct Moments of Inertia. Clockwise order will result 
    #   in negative area values and mathematically incorrect results.
    # - WEIGHT: Use 1.0 for solid parts and -1.0 to define voids/holes.
    # - The start section here is a T-shape composed of two not overlapping polygons:
    #   a "flange" (top horizontal) and a "web" (vertical stem).
    # ----------------------------------------------------------------------------------

    # Flange Definition: Rectangle from (-1, -0.2) to (1, 0.2)
    # Order: Bottom-Left -> Bottom-Right -> Top-Right -> Top-Left (CCW)
    poly0_start = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )
    
    # Web Definition: Rectangle from (-0.2, -1.0) to (0.2, 0.2)
    # Order: Bottom-Left -> Bottom-Right -> Top-Right -> Top-Left (CCW)
    poly1_start = Polygon(
        vertices=(Pt(-0.2, -1.0), Pt(0.2, -1.0),  Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    )

    # ----------------------------------------------------------------------------------
    # 2. DEFINE END SECTION (Z = 10)
    # ----------------------------------------------------------------------------------
    # GEOMETRIC CONSISTENCY:
    # - To enable linear interpolation (tapering), the end section must contain the 
    #   same number of polygons with the same names as the start section.
    # - The web depth here increases linearly from 1.0 down to 2.5 (negative Y direction),
    #   creating a tapered profile along the longitudinal Z-axis.
    # ----------------------------------------------------------------------------------

    # Flange remains unchanged for this prismatic top part
    poly0_end = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )
    
    # Web becomes deeper: Y-bottom moves from -1.0 to -2.5
    # MAINTAIN CCW ORDER: Bottom-Left -> Bottom-Right -> Top-Right -> Top-Left
    poly1_end = Polygon(
        vertices=(Pt(-0.2, -2.5), Pt(0.2, -2.5), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    )
    
    # ----------------------------------------------------------------------------------
    # 3. CREATE SECTIONS WITH Z-COORDINATES
    # ----------------------------------------------------------------------------------
    # Sections act as containers for polygons at a specific coordinate along the beam axis.
    # All polygons defined at Z=0.0 are grouped into s0, and those at Z=10.0 into s1.
    # ----------------------------------------------------------------------------------

    s0 = Section(polygons=(poly0_start, poly1_start), z=0.0)
    s1 = Section(polygons=(poly0_end, poly1_end), z=10.0)

    # --------------------------------------------------------
    # 4. INITIALIZE CONTINUOUS SECTION FIELD
    # --------------------------------------------------------
    # A linear interpolator is used to generate intermediate
    # sections between Z = 0 and Z = 10.
    field = ContinuousSectionField(section0=s0, section1=s1)


    # --------------------------------------------------------
    # 5. PRIMARY SECTION PROPERTIES (Z = 5.0)
    # --------------------------------------------------------
    # Properties are computed at mid-span.
    sec_mid = field.section(5.0)
    props = section_properties(sec_mid)
    
    print("\n" + "="*40)
    print("PRIMARY PROPERTIES AT Z=5.0 (Centroidal)")
    print("="*40)
    print(f"A:   {props['A']:.4f}      # Net Cross-Sectional Area")
    print(f"Cx:  {props['Cx']:.4f}     # Horizontal Centroid location (Global X)")
    print(f"Cy:  {props['Cy']:.4f}     # Vertical Centroid location (Global Y)")
    print(f"Ix:  {props['Ix']:.4f}     # Second Moment of Area about Centroidal X-axis")
    print(f"Iy:  {props['Iy']:.4f}     # Second Moment of Area about Centroidal Y-axis")
    print(f"Ixy: {props['Ixy']:.4f}    # Product of Inertia (Measure of asymmetry)")
    print(f"J:   {props['J']:.4f}      # Polar Moment of Area (Ix + Iy)")

    # 2. DERIVED PROPERTIES (Radius of Gyration, Principal Axes)
    derived = section_derived_properties(props)
    print("\n" + "-"*40)
    print("DERIVED GEOMETRIC PROPERTIES")
    print("-"*40)
    print(f"rx:  {derived['rx']:.4f}     # Radius of Gyration about X (sqrt(Ix/A))")
    print(f"ry:  {derived['ry']:.4f}     # Radius of Gyration about Y (sqrt(Iy/A))")
    print(f"I1:  {derived['I1']:.4f}     # Maximum Principal Moment of Area")
    print(f"I2:  {derived['I2']:.4f}     # Minimum Principal Moment of Area")
    print(f"Deg: {derived['theta_deg']:.2f}°   # Principal Axis Rotation Angle")

    # --------------------------------------------------------
    # 7. STATICAL MOMENT OF AREA (Q)
    # --------------------------------------------------------
    # Computed at the neutral axis (y = Cy).
    # Used in shear stress calculations.)
    Q_na = section_statical_moment_partial(sec_mid, y_cut=props['Cy'])
    print("\n" + "-"*40)
    print("SHEAR ANALYSIS PROPERTIES")
    print("-"*40)
    print(f"Q_na: {Q_na:.4f}    # Statical Moment of Area above Neutral Axis (for Shear Stress)")

    # 8. VOLUMETRIC PROPERTIES
    total_vol = integrate_volume(field)
    print("\n" + "="*40)
    print("GLOBAL FIELD PROPERTIES (3D)")
    print("="*40)
    print(f"Total Volume: {total_vol:.4f} # Total material volume of the ruled solid")
    # Technical Explanation for the negative Cy
    print("\n" + "-"*50)
    print("TECHNICAL NOTE ON COORDINATES:")
    print("-"*50)
    print("The negative value for 'Cy' is physically correct.")
    print("In this model, the flange is centered at y=0, while the web")
    print("extends downwards (from y=0.2 to y=-1.0 at Z=0, and y=-2.5 at Z=10).")
    print("Since the majority of the T-section's mass is located below the")
    print("global X-axis (y=0), the centroid MUST have a negative Y-coordinate.")
    print("This indicates the geometric center is below the drawing origin.")
    print("-"*50)


    # --------------------------------------------------------
    # 9. VISUALIZATION
    # --------------------------------------------------------
    # - 2D section plot at Z = 5.0
    # - 3D ruled solid visualization
    viz = Visualizer(field)
    
    # Generate 2D plot for the specified slice
    viz.plot_section_2d(z=5.0)
    
    # Generate 3D plot of the interpolated solid
    # line_percent determines the density of the longitudinal ruled lines
    viz.plot_volume_3d(line_percent=100.0, seed=1)

    import matplotlib.pyplot as plt
    plt.show()
```
</details>

---

### How to Cite this Library
<details>
<summary>Click for BibTeX citation</summary>

```bibtex
@software{boscu_continuous_2025,
  author = {Boscu, Giovanni},
  title = {Continuous Section Field (CSF): A geometric and mechanical engine for non-prismatic structural members},
  year = {2025},
  publisher = {Zenodo},
  version = {v1.0.0},
  doi = {10.5281/zenodo.18063427},
  url = {https://doi.org/10.5281/zenodo.18063427}
}
```
---
## License
This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.
