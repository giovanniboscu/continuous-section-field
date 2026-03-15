# CSF Validation vs SectionProperties

## Overview

This merge request introduces a validation benchmark comparing **CSF (Continuous Section Field)** results with the FEM‑based library **SectionProperties**.

The objective is to verify:

* correctness of the CSF geometric integration
* consistency of section properties
* behaviour of the thin‑walled torsion model (`@cell`)

The benchmark uses a parametrically generated **twisted tower cross‑section** whose geometry evolves continuously along the beam axis.

---

# Continuous Section Field Concept

The key idea behind CSF is the **Continuous Section Field** concept.

Instead of defining a beam as a sequence of discrete cross‑sections, CSF treats the section as a **continuous geometric field along the longitudinal coordinate `z`**.

The modelling workflow is therefore:

1. **Parametric geometry definition**
   Base and head sections are defined through a small number of geometric parameters.

2. **Continuous geometric evolution**
   Geometry varies smoothly along `z` through interpolation of parameters and transformations (such as twist).

3. **Direct recomputation of properties**
   Section properties are recomputed analytically from the evolving geometry at any location `z`.

This approach provides several advantages:

* no need for tabulated discrete sections
* no structural mesh required for property evaluation
* section properties remain fully consistent with the current geometry

The method is particularly well suited for **non‑prismatic members**.

---

# Geometry Generation

The geometry used for this benchmark is generated with the script:

```
writegeometry_v6_twist.py
```

This script produces a parametric tower whose cross‑section evolves between two shapes while applying a twist along the member axis.

All parameters of the geometry are **fully configurable**, including:

* base section geometry
* head section geometry
* wall thickness values
* rounded corner radius
* discretization resolution
* twist angle between the end stations

Because the geometry is parameterized, the entire benchmark can be regenerated with different parameter values.

---

# Parameter Set Used in This Validation

```
# -------------------------
# Axial domain
# -------------------------
z0 = 0.0
z1 = 40.0

# ===== Base circular annulus =====
tf_cell = 0
tg_base = 0.40
cx = 0.0
cy = 0.0
de = 10.0

# ===== Head rounded‑rectangle annulus =====
th_cell = 0
tg_head = 0.20
rcx = 0.0
rcy = 0.0
rdx = 6.0
rdy = 4.0
R = 1.0

# ===== Twist between S0 and S1 =====
twist_deg = 90

# ===== Discretization =====
N = 128
```

The cross‑section therefore evolves from a **circular annulus at the base** to a **rounded‑rectangle annulus at the tower head**, while undergoing a **90° twist** along the height.

---

# Sections Analysed

The following stations were evaluated:

```
z = 0, 5, 10, 15, 20,
24, 26, 28, 29, 30,
31, 32, 33, 34, 35,
36, 37, 38, 40
```

For each section the properties were computed using:

```
CSF → analytical polygon integration
SP  → FEM geometry solver (SectionProperties)
```

---

# Property Mapping

| CSF       | SectionProperties |
| --------- | ----------------- |
| A         | area              |
| Ix        | e.ixx_c           |
| Iy        | e.iyy_c           |
| Wx        | e.zxx+            |
| Wy        | e.zyy+            |
| J_sv_cell | e.j               |

---

# Results

## Mean and Maximum Relative Error

| Property | Mean error | Max error  |
| -------- | ---------- | ---------- |
| Area     | 0.000011 % | 0.000023 % |
| Ix       | 0.000013 % | 0.000043 % |
| Iy       | 0.000004 % | 0.000009 % |
| Wx       | 0.000010 % | 0.000038 % |
| Wy       | 0.000011 % | 0.000039 % |
| J        | 0.432 %    | 1.145 %    |

---

# Interpretation

## Geometric Properties

Area, centroid and inertia tensors match **within numerical rounding**.

Both CSF and SectionProperties integrate polygon geometry using Green's theorem (shoelace formula), therefore near‑exact agreement is expected.

---

## Section Modulus

When the correct SectionProperties properties (`e.zxx+`, `e.zyy+`) are used, the section moduli match almost exactly.


---

## Torsion Constant

The only systematic difference occurs in the torsional constant.

Mean difference:

≈ 0.4 %

Maximum difference:

≈ 1.15 %

This behaviour is expected because the models differ:

| CSF                               | SectionProperties        |
| --------------------------------- | ------------------------ |
| Bredt–Batho thin‑wall closed cell | FEM Saint‑Venant torsion |

Thin‑wall analytical torsion and FEM torsion typically differ by about **1%** for irregular closed sections.

---

# Behaviour Along the Tower

The maximum deviation occurs around:

```
z ≈ 24 – 28
```

This corresponds to the region where:

* the geometry transitions strongly toward the rounded‑rectangle head section
* the twist rotates the principal axes relative to the global axes

As the section approaches the symmetric head configuration, the difference between the two models rapidly decreases:

```
J difference < 0.02 %
```

---

# Why This Is a Strong Validation Example

This benchmark is already a validation case because it combines several sources of geometric and numerical complexity in a single reproducible example:

* **shape transition** from circular annulus to rounded-rectangle annulus
* **continuous twist** along the member axis
* **closed thin-walled behaviour** relevant to torsion
* **continuous recomputation** of section properties rather than interpolation between predefined sections
* **comparison against an independent FEM-based solver**


---

# Benchmark

A natural next step would be to extend the validation with a small **parametric sensitivity set** based on the same script.

For example, the benchmark could be repeated for a few additional twist values such as:

```
twist_deg = 0, 30, 60, 90
```

and possibly for one or two additional thickness ratios.

This would make the validation stronger for three reasons:

1. **It would show that the agreement is not accidental for a single configuration.**
   The method would be validated over a family of continuously varying geometries.

2. **It would demonstrate robustness with respect to geometric complexity.**
   Increasing twist directly increases axis rotation and geometric irregularity.

3. **It would better highlight the CSF philosophy.**
   Since the geometry is fully parametric, the entire benchmark can be regenerated in seconds by changing only a few parameters.

The user defines geometry parametrically, and CSF recomputes the section properties directly from the evolving continuous field.

---

# Suggested Positioning in the Merge Request

A useful way to frame this benchmark is the following:

> This is not merely a comparison on one arbitrary section. It is a validation of a continuous parametric geometry workflow, where the section evolves smoothly along the member axis and properties are recomputed directly from geometry at every station.

This wording better emphasizes the methodological value of the example.

---

# Conclusion

The benchmark confirms that:

* CSF geometric integration is **numerically exact**
* section properties match an independent FEM solver
* torsion differences are consistent with the theoretical difference between **Bredt–Batho thin‑wall torsion** and **Saint‑Venant FEM torsion**

No anomalies or systematic errors were detected.

This validation highlights both the **accuracy** and the **conceptual elegance** of the **Continuous Section Field** approach, where section properties are derived directly from a continuously evolving parametric geometry.
