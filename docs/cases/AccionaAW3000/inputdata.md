# Project Geometry and Reinforcement Data  
## Acciona AW3000 Concrete Tower — Reference Input Dataset (H = 120 m)

This document collects the **authoritative project input data** for a 120 m concrete wind‑turbine tower inspired by the Acciona AW3000 platform.
---

## 1. Project Description

- **Structure type:** Reinforced concrete wind turbine tower  
- **Total height:** 120 m  
- **Geometric idealization:** Perfect hollow frustum (pure truncated cone)  
- **Variation law:** Linear along the vertical axis  

The tower geometry is defined exclusively by:
- outer diameter `Do(z)`,
- wall thickness `t(z)`.

---

## 2. Concrete Geometry (Authoritative)

### 2.1 Tapering Laws

- **Outer diameter gradient:** −0.075 m/m  
- **Wall thickness gradient:** −0.00458 m/m  

Both quantities vary linearly with height.

---

### 2.2 Concrete Geometry by Station

| Station | Height z (m) | Outer Diameter Do (m) | Wall Thickness t (m) |
|:--|--:|--:|--:|
| Base | 0 | 13.00 | 0.80 |
| S1 | 30 | 10.75 | 0.66 |
| S2 | 60 | 8.50 | 0.52 |
| S3 | 90 | 6.25 | 0.39 |
| Top | 120 | 4.00 | 0.25 |

---

### 2.3 Derived Inner Diameter

The inner diameter of the concrete section is defined as:

```text
Di(z) = Do(z) − 2 · t(z)
```

This relation applies at all heights.

---

## 3. Concrete Section Areas (Geometric)

The following concrete areas are **geometric quantities**, derived from the published geometry.
They represent the net concrete cross‑section only.

| Station | Height z (m) | Concrete Area Ac (m²) |
|:--|--:|--:|
| Base | 0 | 30.65 |
| S1 | 30 | 21.01 |
| S2 | 60 | 13.15 |
| S3 | 90 | 7.14 |
| Top | 120 | 2.95 |

---

## 4. Steel Reinforcement — Overview

Steel reinforcement is divided into:
- **Passive steel** (longitudinal reinforcement and stirrups),
- **Active steel** (post‑tensioning tendons).

The data below describe **sectional steel areas only**.
No assumptions are made here regarding stiffness, prestress level, or structural interaction.

---

## 5. Passive Steel Reinforcement (As)

Passive reinforcement provides bending capacity, crack control, and local stability.
The area varies with height, reflecting the bending moment envelope.

| Station | Height z (m) | Passive Steel Area As (m²) | As / Ac (%) |
|:--|--:|--:|--:|
| Base | 0 | 0.300 | 0.98 |
| S1 | 30 | 0.200 | 0.95 |
| S2 | 60 | 0.130 | 0.99 |
| S3 | 90 | 0.085 | 1.19 |
| Top | 120 | 0.060 | 2.03 |

---

## 6. Active Steel Reinforcement (Ap)

Active reinforcement consists of vertical post‑tensioning tendons.
The tendon area is assumed **constant along the height**.

| Height range (m) | Active Steel Area Ap (m²) | Description |
|:--|--:|--|
| 0 – 120 | 0.100 | High‑tensile post‑tensioning steel |

---

## 7. Combined Section Areas (Concrete + Steel)

These values are provided for **mass and global capacity estimation only**.
They do not imply any homogenization or stiffness model.

| Station | Height z (m) | Concrete Ac (m²) | Passive As (m²) | Active Ap (m²) | Total Area Atot (m²) |
|:--|--:|--:|--:|--:|--:|
| Base | 0 | 30.65 | 0.300 | 0.100 | 31.05 |
| S1 | 30 | 21.01 | 0.200 | 0.100 | 21.31 |
| S2 | 60 | 13.15 | 0.130 | 0.100 | 13.38 |
| S3 | 90 | 7.14 | 0.085 | 0.100 | 7.33 |
| Top | 120 | 2.95 | 0.060 | 0.100 | 3.11 |

---

## 8. Material Density Assumptions (Reference)

The following densities are commonly adopted for preliminary evaluations:

- **Concrete:** 2500 kg/m³  
- **Steel:** 7850 kg/m³  

These values may be adjusted depending on code provisions or project‑specific requirements.

---

## 9. Intended Use of This Dataset

This dataset is suitable as a **neutral reference input** for:

- analytical section calculations,
- FEM shell or beam models,
- reduced‑order beam formulations,
- parametric and sensitivity studies,
- academic research and teaching,
- independent cross‑verification of numerical tools.

No specific modeling approach is implied or required.

---

## 10. Scope Limitation

This document:
- contains **input data only**,
- does **not** prescribe a modeling method,
- does **not** include solver‑dependent quantities,
- does **not** contain validation or verification results.

All derived properties and comparisons must be documented separately.
