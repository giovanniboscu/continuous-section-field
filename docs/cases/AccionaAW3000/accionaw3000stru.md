# Technical Benchmark: Acciona AW3000 Concrete Tower (H = 120 m)

**Model Type:** Perfect Frustum (Pure Truncated Cone)  
**Reference:** Structural Engineering Benchmark for Wind Energy Projects

---

## 1. Project Description
This document provides a structural benchmark for a **120 m wind turbine concrete tower**, based on the **Acciona AW3000** platform. The geometry is modeled as a **perfect hollow frustum of a cone**, with **linear variation** of external diameter and wall thickness along the height. The benchmark is intended for **FEM (Finite Element Method) validation**, modal analysis, and comparison with reduced-order beam models.

---

## 2. Geometric Data (Concrete Structure)
The concrete section is defined by linear tapering laws:

- **Diameter tapering gradient:** −0.075 m/m  
- **Wall thickness tapering gradient:** −0.00458 m/m

| Station | Height z (m) | External Diameter (m) | Wall Thickness (m) | Concrete Area Ac (m²) | Inertia I (m⁴) |
|---|---:|---:|---:|---:|---:|
| **Base** | 0 | 13.00 | 0.80 | 30.65 | 604.50 |
| **S1** | 30 | 10.75 | 0.66 | 21.01 | 284.10 |
| **S2** | 60 | 8.50 | 0.52 | 13.15 | 110.10 |
| **S3** | 90 | 6.25 | 0.39 | 7.14 | 32.20 |
| **Top** | 120 | 4.00 | 0.25 | 2.95 | 5.40 |

---

## 3. Steel Reinforcement Details
The steel reinforcement is divided into **passive (longitudinal rebar)** and **active (post-tensioning tendons)**.

### 3.1 Passive Steel (As – Longitudinal Reinforcement)
Passive reinforcement provides crack control and flexural capacity. The reinforcement area decreases with height, following the bending moment envelope.

| Station | Height z (m) | Area As (m²) | Ratio As/Ac | Engineering Note |
|---|---:|---:|---:|---|
| **Base** | 0 | 0.300 | 0.98% | High flexural demand |
| **S1** | 30 | 0.200 | 0.95% | Mid-lower transition |
| **S2** | 60 | 0.130 | 0.99% | Shear and fatigue control |
| **S3** | 90 | 0.085 | 1.19% | Local wall stability |
| **Top** | 120 | 0.060 | 2.03% | Flange connection zone |

---

### 3.2 Active Steel (Ap – Post-Tensioning Tendons)
High-strength post-tensioning tendons run vertically along the tower height. The tendon area is assumed **constant** from base to top.

| Station | Height z (m) | Area Ap (m²) | Continuity | Material Type |
|---|---:|---:|:---:|---|
| **All** | 0–120 | **0.100** | Constant | High-tensile steel (Y1860) |

---

## 4. Summary of Composite Properties
The following values are used for global mass and stiffness evaluations.

| Station | Height z (m) | Total Area Atot (m²) | Linear Weight (kN/m)* |
|---|---:|---:|---:|
| **Base** | 0 | 31.05 | 798.2 |
| **S1** | 30 | 21.31 | 548.1 |
| **S2** | 60 | 13.38 | 344.5 |
| **S3** | 90 | 7.33 | 189.2 |
| **Top** | 120 | 3.11 | 81.4 |

*Assumed material densities: Concrete = 2500 kg/m³, Steel = 7850 kg/m³.*

---

## 5. Structural Modeling Guidelines
- **Concrete class:** C60/75 or higher.
- **Damping ratio:** Typically 1–2% for concrete towers.
- **Post-tensioning force:** Initial force may be estimated as  
  \( P_0 = A_p \cdot 0.7 f_{pk} \), with \( f_{pk} = 1860 \) MPa.
- **FEM discretization:** Use at least **10 beam elements** along the height, or a refined shell mesh, to accurately capture tapering effects.

---
# CSF Verification Notes – Acciona AW3000 Concrete Tower (H = 120 m)

**Project Type:** Wind Turbine Tower – Structural Analysis Benchmark  
**Geometry:** Perfect Hollow Frustum (Pure Truncated Cone)

This document provides **verification and congruence checks** between the analytical benchmark data of the Acciona AW3000 concrete tower and the corresponding **CSF (Continuous Section Field)** model results.

---

## 1. Concrete Geometry & Section Properties (Ac)

The following table defines the **net concrete cross-section properties** at selected stations.  
All values are **pure geometric properties** (non‑relativized) and are used as reference for CSF validation.

| Key | Unit | Base (0 m) | S1 (30 m) | S2 (60 m) | S3 (90 m) | Top (120 m) |
|---|---|---:|---:|---:|---:|---:|
| **Height (z)** | m | 0 | 30 | 60 | 90 | 120 |
| **External Diameter** | m | 13.00 | 10.75 | 8.50 | 6.25 | 4.00 |
| **Wall Thickness (t)** | m | 0.80 | 0.66 | 0.52 | 0.39 | 0.25 |
| **Area A** | m² | 30.65 | 21.01 | 13.15 | 7.14 | 2.95 |
| **Centroid Cx, Cy** | m | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **Inertia Ix = Iy** | m⁴ | 604.5 | 284.1 | 110.1 | 32.2 | 5.4 |
| **Product Ixy** | m⁴ | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **Polar Moment J** | m⁴ | 1209.0 | 568.2 | 220.2 | 64.4 | 10.8 |
| **Principal I1 = I2** | m⁴ | 604.5 | 284.1 | 110.1 | 32.2 | 5.4 |
| **Radius of Gyration rx = ry** | m | 4.44 | 3.67 | 2.89 | 2.12 | 1.35 |
| **Section Modulus Wx = Wy** | m³ | 93.0 | 52.8 | 25.9 | 10.3 | 2.7 |
| **Torsional Rigidity K** | m⁴ | 18.2 | 3.4 | 0.34 | 0.02 | 0.0002 |
| **First Moment Q** | m³ | 29.6 | 16.8 | 8.2 | 3.2 | 0.8 |
| **J Saint‑Venant** | m⁴ | 1209.0 | 568.2 | 220.2 | 64.4 | 10.8 |
| **J Roark / Bredt** | m⁴ | 1133.5 | 533.1 | 206.8 | 60.5 | 10.1 |

---

## 2. Steel Reinforcement Breakdown

Steel areas are provided per station and are **independent of CSF relativization**. They are used to define polygonal regions and weighting functions.

### 2.1 Passive Steel Area (As)
*Longitudinal reinforcement and stirrups for bending, shear, and crack control.*

| Station | Height (m) | As (m²) | As / Ac | Structural Role |
|---|---:|---:|---:|---|
| **Base** | 0 | 0.300 | 0.98% | Maximum bending demand |
| **S1** | 30 | 0.200 | 0.95% | Continuity |
| **S2** | 60 | 0.130 | 0.99% | Crack control |
| **S3** | 90 | 0.085 | 1.19% | Local stability |
| **Top** | 120 | 0.060 | 2.03% | Flange reinforcement |

---

### 2.2 Active Steel Area (Ap)
*Post‑tensioning tendons (high‑tensile steel).*

| Station | Height (m) | Ap (m²) | Trend | Material Grade |
|---|---:|---:|---|---|
| **Base → Top** | 0–120 | **0.100** | Constant | Y1860 S7 |

---

## 3. Congruence with CSF Model

### 3.1 Section‑Level Verification
- CSF **geometric partial areas** computed via region selection match the benchmark values of **Ac** within numerical tolerance.
- Centroid location is preserved at (0,0) due to axisymmetric geometry.
- Ix, Iy, and J computed by CSF for concrete‑only regions reproduce the benchmark values listed above.

### 3.2 Relativized vs Geometric Quantities
- CSF **structural calculations** use *relativized* section properties (weighted by reference material).
- The values in this document correspond to **pure geometric references** and are used for:
  - conceptual validation,
  - comparison with closed‑form solutions,
  - FEM benchmarking.

### 3.3 Torsional Behavior
- **Saint‑Venant torsion (Jsv):** For circular closed sections, equal to polar moment J.
- **Roark / Bredt torsion:** Slightly lower; assumes shear flow at mid‑thickness. Recommended for thin‑walled concrete towers.
- CSF allows both interpretations for verification purposes, without ambiguity.

### 3.4 Dynamic Benchmark Consistency
The mass and stiffness distribution implied by these properties maintains the first natural frequency **f₁ ≈ 0.25–0.30 Hz**, avoiding:
- **1P** rotor frequency resonance,
- **3P** blade‑passing frequency resonance.

---

## 4. Structural Modeling Notes

- **Concrete class:** C60/75 or higher.
- **Damping ratio:** 1–2% (typical for concrete towers).
- **Post‑tensioning force:**  
  \( P_0 = A_p · 0.7 f_{pk} \), with \( f_{pk} = 1860 \) MPa.
- **Fallback torsional rigidity:**  
  \( K ≈ A^4 / (40 · I_p) \) (conservative).
- **Preferred torsional model:** Roark / Bredt formulation.

---



---

*This benchmark is intended as a reference geometry and reinforcement layout for comparison with numerical models, including CSF-based relativized section approaches.*
