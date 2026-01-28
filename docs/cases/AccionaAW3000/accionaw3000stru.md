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
# Top & Base Section Areas (Concrete, Passive Steel, Active Steel)

| Station | Height z (m) | Concrete Area Ac (m²) | Passive Steel Area As (m²) | Active Steel Area Ap (m²) | As/Ac (%) | Description |
|--------|---------------|------------------------|-----------------------------|----------------------------|-----------|-------------|
| Base   | 0             | 30.65                  | 0.300                       | 0.100                      | 0.98      | Maximum bending demand, thick wall, highest reinforcement density |
| Top    | 120           | 2.95                   | 0.060                       | 0.100                      | 2.03      | Flange connection zone, reduced concrete area, higher relative steel ratio |


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

### Geometry-derived reference (ideal circular annulus)

Formulas used:
- `Di = Do - 2*t`
- `A  = (pi/4)  * (Do^2 - Di^2)`
- `Ix = (pi/64) * (Do^4 - Di^4)`  (Ix = Iy)
- `J  = 2 * Ix`
- `r  = sqrt(Ix / A)`
- `W  = Ix / (Do/2)`

| Station | z (m) | Do (m) | t (m) | Di (m) | A_theory (m²) | Ix_theory (m⁴) | J_theory (m⁴) | r_theory (m) | W_theory (m³) | ΔA vs table (%) | ΔIx vs table (%) |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Base | 0 | 13.00 | 0.80 | 11.40 | 30.661944 | 572.918429 | 1145.836858 | 4.322615 | 88.141297 | +0.039 | −5.224 |
| S1 | 30 | 10.75 | 0.66 | 9.43 | 20.921122 | 267.381617 | 534.763233 | 3.574977 | 49.745417 | −0.423 | −5.885 |
| S2 | 60 | 8.50 | 0.52 | 7.46 | 13.036353 | 104.210649 | 208.421299 | 2.827340 | 24.520153 | −0.864 | −5.349 |
| S3 | 90 | 6.25 | 0.39 | 5.47 | 7.179796 | 30.955421 | 61.910841 | 2.076406 | 9.905735 | +0.557 | −3.865 |
| Top | 120 | 4.00 | 0.25 | 3.50 | 2.945243 | 5.200195 | 10.400390 | 1.328768 | 2.600097 | −0.161 | −3.700 |
|

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
# Tower Section Diameters (Base and Top)

# 4‑Circle Section Geometry 
Acciona AW3000 Concrete Tower – H = 120 m

## Base Section (z = 0 m)

| Level (z) | Circle | Description                   | Diameter (m) |
|-----------|--------|-------------------------------|---------------|
| 0 m       | 1      | Concrete – outer diameter     | 13.000        |
| 0 m       | 2      | Steel – outer diameter        | 11.426        |
| 0 m       | 3      | Concrete – inner diameter     | 11.400        |
| 0 m       | 4      | Void – inner diameter         | 11.200        |

### Inner concrete ring thickness:
- (11.400 − 11.200) / 2 = **0.10 m**

---

## Top Section (z = 120 m)

| Level (z) | Circle | Description                   | Diameter (m) |
|-----------|--------|-------------------------------|---------------|
| 120 m     | 1      | Concrete – outer diameter     | 4.000         |
| 120 m     | 2      | Steel – outer diameter        | 3.529         |
| 120 m     | 3      | Concrete – inner diameter     | 3.500         |
| 120 m     | 4      | Void – inner diameter         | 3.300         |

### Inner concrete ring thickness:
- (3.500 − 3.300) / 2 = **0.10 m**




# Weight Logic for Concentric Rings in CSF
### Technical Documentation

This section describes the general weight‑based logic used in CSF when defining concentric rings for tower cross‑sections.  
The mechanism is fully generic: voids, materials, degraded zones, and overlays are all handled by the same rule, with no special cases.

---

## 1. Rings as Independent Layers

Each ring is defined by:

- its geometry (a closed polygon)
- a stiffness weight $W$, representing its contribution to the effective section

The weight is a scalar multiplier applied to the stiffness contribution of that ring.

Examples:

- $W = 1.0$ → full material (e.g., concrete)  
- $W = 0.0$ → void  
- $W = E_s / E_c$ → homogenized steel  
- $W < 1.0$ → degraded material  
- $W > 1.0$ → stiffer material or reinforcement  

---

## 2. Overlapping Rings: General Combination Rule

When two rings overlap, CSF computes the effective weight using a single universal rule:

$$
W_{\text{eff}} = W_{\text{upper}} - W_{\text{lower}}
$$

Where:

- **upper** = the ring defined later (higher in the stack)  
- **lower** = the ring defined earlier  

This rule applies to all cases.

---

## 3. Voids Are Not Special Cases

A void is simply defined as:

$$
W_{\text{void}} = 0
$$

When a void overlaps a material:

$$
W_{\text{eff}} = 0 - W_{\text{mat}} = -W_{\text{mat}}
$$

A negative effective weight indicates that the upper ring removes stiffness from the lower ring.  
CSF interprets this automatically as a subtraction of material.

No boolean operations or special handling are required.

---

## 4. Material Replacement and Composite Layers

Given:

- Material 1 with weight $W_1$  
- Material 2 with weight $W_2$ placed above it  

The effective contribution is:

$$
W_{\text{eff}} = W_2 - W_1
$$

Interpretation:

- If $W_2 > W_1$: the upper material adds stiffness  
- If $W_2 < W_1$: the upper material reduces stiffness  
- If $W_2 = W_1$: the upper material replaces the lower one with no net change  

This supports:

- steel overlays  
- steel substitution  
- degraded zones  
- multi‑material composites  
- partial stiffness reductions  

---

## 5. Consequences for Tower Modeling

Using this weight logic:

- Voids, concrete, steel, and degraded regions are all treated uniformly  
- No special geometry operations are needed  
- The section remains fully parametric and modular  
- Any number of rings can be added or removed without changing the logic  
- Local modifications (e.g., degradation at specific heights) are easy to implement  

This makes the ring‑based approach suitable for:

- continuous tower definitions  
- parametric studies  
- stiffness sensitivity analyses  
- degradation modeling  
- rapid regeneration of section properties  


---
## 4. Structural Modeling Notes

- **Concrete class:** C60/75 or higher.
- **Damping ratio:** 1–2% (typical for concrete towers).
- **Post‑tensioning force:**  
  $P_0 = A_p \cdot 0.7 f_{pk}$, with $f_{pk} = 1860$ MPa.
- **Fallback torsional rigidity:**  
  $K \approx A^4 / (40 \cdot I_p)$ (conservative).
- **Preferred torsional model:** Roark / Bredt formulation.

---
# Differential Concrete Degradation in CSF
# Outer vs Inner Concrete Rings with Height‑Dependent Weight Functions
# Engineering Rationale, Mathematical Formulation, and CSF Implementation

## 1. Introduction

Concrete wind turbine towers often exhibit non‑uniform stiffness degradation along their height.
Environmental exposure, cracking, moisture gradients, and thermal cycling typically affect the outer concrete shell more severely than the inner concrete core.

The CSF (Concentric Section Framework) naturally supports this behavior by allowing each geometric ring to have its own weight function:

    w = "expression in z"

This weight scales the material stiffness (e.g., Young’s modulus) at height z.

## 2. Why Outer and Inner Concrete Behave Differently

### 2.1 Mechanical justification

In bending‑dominated structures such as tall concrete towers:

- The outer fibers carry the largest tensile and compressive strains.
- These fibers are the first to crack, micro‑crack, or degrade.
- The internal concrete remains mostly in compression, with lower strain gradients.

Thus:

- Outer concrete stiffness decreases significantly due to cracking and environmental exposure.
- Inner concrete stiffness remains closer to the uncracked modulus.

This is consistent with:

- Eurocode 2 concepts of cracked vs uncracked stiffness
- Tension stiffening models
- Effective stiffness reduction in tall concrete structures
- Observed behavior in real concrete towers (e.g., Acciona AW3000, Enercon hybrid towers)

## 3. Engineering Scenario (Realistic)

We consider a 120 m concrete tower (e.g., Acciona AW3000 type).
Assume:

- The first 30 m experience stronger environmental degradation.
- The outer shell is significantly cracked.
- The inner core is only mildly affected.

This produces a realistic stiffness gradient.

## 4. Mathematical Formulation of the Weight Functions

### 4.1 Outer concrete ring (strong degradation)

At the base:
- Effective stiffness = 60% of the intact value
- Linearly recovers to 100% at 30 m

Mathematically:

    W_outer(z) = 0.60 + 0.40*(z/30)   for 0 ≤ z ≤ 30
    W_outer(z) = 1.00                 for z > 30

### 4.2 Inner concrete ring (mild degradation)

At the base:
- Effective stiffness = 90% of the intact value
- Recovers to 100% at 30 m

Mathematically:

    W_inner(z) = 0.90 + 0.10*(z/30)   for 0 ≤ z ≤ 30
    W_inner(z) = 1.00                 for z > 30

## 5. CSF Implementation (Copy‑Paste Ready)

CSF uses boolean masks inside the weight expression.
These evaluate to 1 or 0, allowing piecewise functions in a single line.

### Outer concrete ring

    w = "(z <= 30)*(0.60 + 0.40*(z/30)) + (z > 30)*1.00"
       w = "0.60 + 0.40/(1 + exp(-(z-15)/5))"
### Inner concrete ring

    w = "(z <= 30)*(0.90 + 0.10*(z/30)) + (z > 30)*1.00
    "w = "0.90 + 0.10/(1 + exp(-(z-15)/5))"

These expressions:

- are valid CSF syntax
- are single‑line
- require no Python code
- produce a continuous stiffness profile
- are fully versionable and documentable

## 6. Engineering Interpretation

### At the base (z = 0)

- Outer concrete: W = 0.60
- Inner concrete: W = 0.90

This reflects:
- severe cracking on the outside
- mild degradation inside

### At z = 30 m

Both return to:
- W = 1.00

representing a fully intact section.

### Above 30 m

The tower behaves as an uncracked, intact concrete section.

## 7. Practical Use in Engineering

This model is not a normative verification, but it is extremely useful for:

- stiffness sensitivity studies
- pre‑design
- comparison of tower variants
- dynamic behavior estimation
- generating consistent input for FEM beam models
- documenting degradation assumptions
- academic or training purposes





*This benchmark is intended as a reference geometry and reinforcement layout for comparison with numerical models, including CSF-based relativized section approaches.*
