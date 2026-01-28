# Geometry‑Derived Benchmark Data  
## Acciona AW3000 Concrete Tower — Control Dataset (H = 120 m)

This document defines a **geometry‑derived benchmark dataset** for the Acciona AW3000–type
120 m concrete wind turbine tower.

It is derived **exclusively** from the authoritative project geometry and from
**explicit calculation assumptions** stated below.

No numerical model, software, or solver is implied.
All values can be recomputed independently using the formulas provided.

---

## 1. Scope and Purpose

This dataset is intended to be used as a **control reference** for:

- verification of section‑property generators,
- analytical cross‑checks,
- FEM or beam‑model benchmarking,
- independent research and reproducibility studies.

Only quantities that can be **unambiguously reconstructed** are included.

---

## 2. Source Geometry (Authoritative)

The tower is modeled as a **perfect hollow frustum** with linear tapering.

| Station | Height z (m) | Outer Diameter Do (m) | Wall Thickness t (m) |
|:--|--:|--:|--:|
| Base | 0 | 13.00 | 0.80 |
| S1 | 30 | 10.75 | 0.66 |
| S2 | 60 | 8.50 | 0.52 |
| S3 | 90 | 6.25 | 0.39 |
| Top | 120 | 4.00 | 0.25 |

---

## 3. Derived Diameters (Concrete Annulus)

The inner diameter is computed directly from geometry:

```text
Di(z) = Do(z) − 2 · t(z)
```

| Station | Do (m) | t (m) | Di (m) |
|:--|--:|--:|--:|
| Base | 13.00 | 0.80 | 11.40 |
| S1 | 10.75 | 0.66 | 9.43 |
| S2 | 8.50 | 0.52 | 7.46 |
| S3 | 6.25 | 0.39 | 5.47 |
| Top | 4.00 | 0.25 | 3.50 |

---

## 4. Effective Steel Ring — Calculation Model

Steel reinforcement (passive + active) is **not modeled discretely**.
For control calculations, it is represented as an **equivalent thin circular ring**
embedded within the concrete wall.

### 4.1 Steel Areas

| Station | Passive As (m²) | Active Ap (m²) | Total Steel A_s,tot (m²) |
|:--|--:|--:|--:|
| Base | 0.300 | 0.100 | 0.400 |
| S1 | 0.200 | 0.100 | 0.300 |
| S2 | 0.130 | 0.100 | 0.230 |
| S3 | 0.085 | 0.100 | 0.185 |
| Top | 0.060 | 0.100 | 0.160 |

---

### 4.2 Effective Steel Diameter Assumption

The equivalent steel ring is centered at the **mid‑thickness diameter**:

```text
D_mid(z) = Do(z) − t(z)
```

The ring is assumed sufficiently thin so that its area satisfies:

```text
A_ring = A_s,tot
```

This assumption preserves:
- total steel area,
- radial position inside the wall,
- mass and stiffness equivalence at section level.

---

## 5. Reference Control Formulas (Circular Annulus)

All benchmark quantities are computed using standard closed‑form expressions.

### 5.1 Concrete‑Only Section

```text
A_c  = (pi/4)  · (Do^2 − Di^2)
I_c  = (pi/64) · (Do^4 − Di^4)
J_c  = 2 · I_c
```

---

### 5.2 Steel Equivalent Ring (Thin Ring Approximation)

For a thin ring of area `A_s,tot` located at radius `R = D_mid / 2`:

```text
I_s ≈ A_s,tot · R^2
J_s ≈ 2 · I_s
```

These expressions are used **only** for control and comparison purposes.

---

## 6. Geometry‑Derived Benchmark Values

### 6.1 Concrete‑Only Reference

| z (m) | A_c (m²) | I_c (m⁴) |
|---:|---:|---:|
| 0 | 30.661944 | 572.918429 |
| 30 | 20.921122 | 267.381617 |
| 60 | 13.036353 | 104.210649 |
| 90 | 7.179796 | 30.955421 |
| 120 | 2.945243 | 5.200195 |

---

### 6.2 Steel Equivalent Ring (Control Values)

| z (m) | A_s,tot (m²) | D_mid (m) | I_s (m⁴) |
|---:|---:|---:|---:|
| 0 | 0.400 | 12.20 | 14.884 |
| 30 | 0.300 | 10.09 | 7.630 |
| 60 | 0.230 | 7.98 | 3.656 |
| 90 | 0.185 | 5.86 | 1.589 |
| 120 | 0.160 | 3.75 | 0.563 |

---

## 7. Notes on Interpretation

- All values in this document are **geometry‑derived**.
- No homogenization, weighting, or solver‑specific logic is applied.
- The effective steel ring is a **calculation abstraction**, not a physical layout.
- The dataset is intended for **transparent, repeatable control checks**.

---

## 8. Reproducibility Statement

Any user can reproduce the values in this document using:
- the geometry table in Section 2,
- the steel areas in Section 4,
- the formulas in Sections 5.1 and 5.2.

No additional assumptions are required.
