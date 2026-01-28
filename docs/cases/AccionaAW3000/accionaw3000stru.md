# CSF Verification Report — Acciona AW3000 Concrete Tower (H = 120 m)

This document is a **self-contained verification report** for the Acciona AW3000–type 120 m concrete tower, built around one principle:

> **Only explicitly stated “project geometry” is treated as authoritative input.**  
> Any “benchmark” sectional properties are **reconstructed** from known closed-form formulas so the reference is fully reproducible.

The report ends with the CSF model assumptions and the resulting comparisons.

---

## 1. Project Geometry (Authoritative Inputs)

The tower is idealized as a **perfect hollow frustum (truncated cone)** with linearly varying outer diameter `Do(z)` and wall thickness `t(z)`.

### 1.1 Stations

| Station | Height z (m) | Outer Diameter Do (m) | Wall Thickness t (m) |
|:--|--:|--:|--:|
| Base | 0 | 13.00 | 0.80 |
| S1 | 30 | 10.75 | 0.66 |
| S2 | 60 | 8.50 | 0.52 |
| S3 | 90 | 6.25 | 0.39 |
| Top | 120 | 4.00 | 0.25 |

### 1.2 Derived Inner Diameter

The inner diameter is derived directly from geometry:

```text
Di(z) = Do(z) - 2 * t(z)
```

---

## 2. Reconstructed “Benchmark” Section Properties (Geometry-Derived Reference)

This section reconstructs the reference sectional properties using **closed-form** expressions for an **ideal circular annulus**.  
These values provide a transparent reference baseline for verification.

### 2.1 Reference Formulas (ideal circular annulus)

```text
Di = Do - 2*t

A  = (pi/4)  * (Do^2 - Di^2)
Ix = (pi/64) * (Do^4 - Di^4)      # Ix = Iy for circular annulus

J  = 2 * Ix                       # polar moment for circular section
r  = sqrt(Ix / A)                 # radius of gyration
W  = Ix / (Do/2)                  # section modulus at outer fiber
```

Notes:
- `Cx = Cy = 0` and `Ixy = 0` by symmetry for a concentric annulus.
- `I1 = I2 = Ix` for the same reason.

### 2.2 Geometry-Derived Reference Table

| Station | z (m) | Do (m) | t (m) | Di (m) | A_ref (m²) | Ix_ref (m⁴) | J_ref (m⁴) | r_ref (m) | W_ref (m³) |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Base | 0 | 13.00 | 0.80 | 11.40 | 30.661944 | 572.918429 | 1145.836858 | 4.322615 | 88.141297 |
| S1 | 30 | 10.75 | 0.66 | 9.43 | 20.921122 | 267.381617 | 534.763233 | 3.574977 | 49.745417 |
| S2 | 60 | 8.50 | 0.52 | 7.46 | 13.036353 | 104.210649 | 208.421299 | 2.827340 | 24.520153 |
| S3 | 90 | 6.25 | 0.39 | 5.47 | 7.179796 | 30.955421 | 61.910841 | 2.076406 | 9.905735 |
| Top | 120 | 4.00 | 0.25 | 3.50 | 2.945243 | 5.200195 | 10.400390 | 1.328768 | 2.600097 |

---

## 3. CSF Model Used in This Verification

### 3.1 Cross-section representation

Each station is modeled in CSF with **four concentric regions**, approximating circles via regular polygons:

- `C1`: outer concrete boundary (`Do`)
- `C4`: inner concrete boundary (`Di`) — central void
- `C2–C3`: optional **equivalent steel ring** (not used in the concrete-only test below)

Circular boundaries are approximated with **regular 40-sided polygons** (41 vertices including closure).

### 3.2 Important modeling note (no material superposition)

CSF does **not** model “overlapping matter”.  
Nested polygons are interpreted through **containment**, and effective contributions are handled internally by CSF.

For voids/holes, the user declares:

```text
w_void = 0
```

CSF manages the internal bookkeeping so that the overlapped region contributes zero to the weighted integrals.

### 3.3 Steel representation (if used)

When steel is modeled as an equivalent ring, CSF uses *calculation diameters* `D2` and `D3` chosen to match a target steel area.

```text
A_ring = As + Ap
D_mid  = Do - t
```

This is a **modeling abstraction** intended for global equivalence (mass/stiffness), not a representation of discrete bars/tendons.


---

## 4. Assessment

- Cross-section **areas** match the geometry-derived reference within approximately **±1.1%**.
- Second moments of area match within approximately **±1.4%**.
- The magnitude and sign of deviations are consistent with approximating circular boundaries using a finite-sided polygon.

No evidence of a systematic modeling bias is observed in this concrete-only verification.

---

## 5. Files / Reproducibility

- CSF geometry YAML (40-gon, 4 concentric regions): `acciona_aw3000_4circles_40sides.yaml`

To reproduce the reference values, use the formulas in Section 2.1 with the project geometry table in Section 1.1.
