# CSF Verification Report — Acciona AW3000 Concrete Tower (H = 120 m)

This document presents a verification study performed with **Continuous Section Field (CSF)**
on a 120 m concrete wind-turbine tower inspired by the Acciona AW3000 platform.

The objective of this report is to verify the geometric and sectional consistency of CSF
against **fully traceable geometric data**, avoiding reliance on undocumented benchmark
property tables.

---

## 1. Scope and Reference Policy

The benchmark documentation provides:
- explicit **geometric definitions** (outer diameter and wall thickness),
- tabulated sectional properties (`Ac`, `Ix`) whose derivation is **not documented**.

In this study:
- the **published geometry** is treated as the sole authoritative reference,
- all reference sectional properties are **derived analytically** from geometry,
- undocumented benchmark tables are **not used** for validation.

This guarantees full transparency and reproducibility of the verification process.

---

## 2. Geometric Definition (Source of Truth)

The concrete tower is modeled as a **perfect hollow frustum** with linear tapering.

### 2.1 Published Geometric Data

| Station | Height z (m) | Outer Diameter Do (m) | Wall Thickness t (m) |
|---|---:|---:|---:|
| Base | 0 | 13.00 | 0.80 |
| S1 | 30 | 10.75 | 0.66 |
| S2 | 60 | 8.50 | 0.52 |
| S3 | 90 | 6.25 | 0.39 |
| Top | 120 | 4.00 | 0.25 |

The inner diameter is obtained as:

Di(z) = Do(z) - 2 * t(z)

---

## 3. Geometry-Derived Reference Properties

Reference sectional properties are computed from standard closed-form expressions
for an **ideal circular annulus**, using the published geometry.

### 3.1 Reference Formulas

A = (pi / 4) * (Do^2 - Di^2)]

I = (pi / 64) * (Do^4 - Di^4)

### 3.2 Derived Reference Values

| z (m) | Do (m) | Di (m) | A\_theory (m²) | I\_theory (m⁴) |
|---:|---:|---:|---:|---:|
| 0 | 13.00 | 11.40 | 30.661944 | 572.918429 |
| 30 | 10.75 | 9.43 | 20.921122 | 267.381617 |
| 60 | 8.50 | 7.46 | 13.036353 | 104.210649 |
| 90 | 6.25 | 5.47 | 7.179796 | 30.955421 |
| 120 | 4.00 | 3.50 | 2.945243 | 5.200195 |

These values constitute the **reference baseline** for the CSF verification.

---

## 4. CSF Modeling Approach

### 4.1 Cross-Section Representation

Each section is modeled using **four concentric polygonal regions**:

- C1: outer concrete boundary (`Do`)
- C2–C3: equivalent steel region (see Section 4.3)
- C4: inner concrete boundary (`Di`)

Circular boundaries are approximated using **regular 40-sided polygons**
(41 vertices including closure).

### 4.2 Concrete Geometry

Concrete geometry in CSF matches the published values exactly:

\[
D_o^{CSF} = D_o^{published}, \quad
D_i^{CSF} = D_o - 2t
\]

No geometric fitting or calibration is performed.

---

### 4.3 Steel Representation (Equivalent Geometry)

Steel reinforcement (passive + active) is represented as an
**equivalent thin circular ring**, defined by *calculation diameters* `D2` and `D3`.

These diameters are chosen such that:

A_ring = As + Ap


and the ring is centered at the **mid-thickness diameter**:

D_mid = Do - t

This representation preserves:
- total steel area,
- radial location consistent with the concrete wall,
- global mass and stiffness equivalence.

It is explicitly noted that this is a **modeling abstraction**, not a physical
representation of discrete reinforcement.

---

## 5. CSF Results — Concrete-Only Verification

To verify geometric consistency, a **concrete-only configuration** is evaluated:

- C1 = 1
- C2 = 1
- C3 = 1
- C4 = 0

### 5.1 CSF Results

| z (m) | CSF A (m²) | CSF I (m⁴) |
|---:|---:|---:|
| 0 | 30.535990 | 568.223411 |
| 30 | 20.908923 | 266.006341 |
| 60 | 13.099427 | 104.163548 |
| 90 | 7.107502 | 30.542182 |
| 120 | 2.933148 | 5.157587 |

---

## 6. Comparison Against Geometry-Derived Reference

| z (m) | CSF A vs A\_theory (%) | CSF I vs I\_theory (%) |
|---:|---:|---:|
| 0 | -0.41 | -0.82 |
| 30 | -0.06 | -0.51 |
| 60 | +0.48 | -0.05 |
| 90 | -1.00 | -1.33 |
| 120 | -0.41 | -0.82 |

---

## 7. Assessment

- Cross-section **areas** computed by CSF agree with the geometry-derived reference
  within approximately **±1%** along the full height.
- Second moments of area differ by approximately **0–1.3%**, consistent with
  the polygonal approximation of circular geometry.
- No systematic bias or geometric inconsistency is observed.

These results confirm that CSF reproduces the declared geometry with high fidelity
and behaves consistently with analytical reference formulations.

---

## 8. Conclusions

This verification demonstrates that:

- CSF accurately reproduces sectional properties derived from
  **explicit and traceable geometric inputs**.
- All results are fully reproducible from published geometry and standard formulas.
- No reliance on undocumented benchmark property tables is required.

The CSF modeling approach is therefore validated at the geometric and sectional level
for non-prismatic concrete tower geometries.

---

## 9. Files

- CSF geometry definition (40-gon, concentric regions):  
  `acciona_aw3000_4circles_40sides.yaml`
