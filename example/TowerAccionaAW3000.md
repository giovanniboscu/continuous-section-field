# Technical Benchmark: Acciona AW3000 Acciona AW3000 Acciona AW3000 Acciona AW3000 Concrete Tower (H = 120m)
**Model Type:** Perfect Frustum (Pure Truncated Cone)  
**Reference:** Structural Engineering Benchmark for Wind Energy Projects

---

## 1. Project Description
This document provides a structural benchmark for a 120m wind turbine tower, based on the **Acciona AW3000** platform. The geometry is modeled as a **perfect hollow frustum of a cone** with linear variation of diameter and wall thickness. This model is ideal for FEM (Finite Element Method) validation and modal analysis.

---

## 2. Geometric Data (Concrete Structure)
The concrete section is defined by a linear tapering function.
* **Tapering Gradient (Diameter):** -0.075 m/m
* **Tapering Gradient (Thickness):** -0.00458 m/m

| Station | Height ($z$) [m] | Ext. Diameter [m] | Wall Thickness [m] | Concrete Area $A_c$ [m²] | Inertia $I$ [m⁴] |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Base** | 0 | 13.00 | 0.80 | 30.65 | 604.50 |
| **S1** | 30 | 10.75 | 0.66 | 21.01 | 284.10 |
| **S2** | 60 | 8.50 | 0.52 | 13.15 | 110.10 |
| **S3** | 90 | 6.25 | 0.39 | 7.14 | 32.20 |
| **Top** | 120 | 4.00 | 0.25 | 2.95 | 5.40 |

---

## 3. Steel Reinforcement Details
The steel layout is categorized into passive (rebar) and active (post-tensioning) components.

### 3.1 Passive Steel ($A_s$ - Longitudinal Rebar)
Reinforcement used for structural integrity and crack control. The area decreases with height following the bending moment reduction.

| Station | Height ($z$) [m] | Area $A_s$ [m²] | Ratio ($A_s/A_c$) | Engineering Note |
| :--- | :--- | :--- | :--- | :--- |
| **Base** | 0 | 0.300 | 0.98% | High flexural demand |
| **S1** | 30 | 0.200 | 0.95% | Mid-lower transition |
| **S2** | 60 | 0.130 | 0.99% | Shear & Fatigue control |
| **S3** | 90 | 0.085 | 1.19% | Local wall stability |
| **Top** | 120 | 0.060 | 2.03% | Flange connection zone |

### 3.2 Active Steel ($A_p$ - Post-Tensioning Tendons)
High-strength tendons running vertically through the tower. This area remains constant from base to top.

| Station | Height ($z$) [m] | Area $Ap$ [m²] | Continuity | Material Type |
| :--- | :--- | :--- | :--- | :--- |
| **All** | 0 - 120 | **0.100** | **Constant** | High-Tensile Steel (Y1860) |

---

## 4. Summary of Composite Properties
Combined values for mass and stiffness calculations.

| Station | Height ($z$) [m] | Total Area $A_{tot}$ [m²] | Linear Weight [kN/m]* |
| :--- | :--- | :--- | :--- |
| **Base** | 0 | 31.05 | 798.2 |
| **S1** | 30 | 21.31 | 548.1 |
| **S2** | 60 | 13.38 | 344.5 |
| **S3** | 90 | 7.33 | 189.2 |
| **Top** | 120 | 3.11 | 81.4 |

*\* Assumed densities: Concrete = 2500 kg/m³, Steel = 7850 kg/m³.*

---

## 5. Structural Modeling Guidelines
- **Material Grade:** Use Concrete **C60/75** or higher.
- **Damping:** Typically 1% to 2% for concrete towers.
- **Post-Tensioning Force:** Calculate initial force as $P_0 = A_p \cdot 0.7 f_{pk}$ (where $f_{pk} = 1860 MPa$).
- **Mesh Suggestion:** For FEM, use at least 10 beam elements or a fine shell mesh to capture the tapering effect accurately.
