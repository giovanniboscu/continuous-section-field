# CSF Verification Report — Acciona AW3000 Concrete Tower (H = 120 m)

This report summarizes validation runs performed with **CSF (Continuous Section Field)**
on a simplified benchmark model of a 120 m concrete wind-turbine tower
(Acciona AW3000–type geometry).

The purpose of this report is to document:
- the **input geometry and weights** used in CSF,
- the resulting **section properties**,
- and their **comparison with published benchmark values**.

No internal CSF algorithms or weighting mechanics are discussed here.
Only declared inputs and computed results are reported.

---

## 1. Geometry Model Used in CSF

The tower is modeled using **two longitudinal stations**:

- **S0 (z = 0 m)**  
  D1 = 13.000000 m  
  D2 = 12.210436 m  
  D3 = 12.189564 m  
  D4 = 11.400000 m  

- **S1 (z = 120 m)**  
  D1 = 4.000000 m  
  D2 = 3.763581 m  
  D3 = 3.736419 m  
  D4 = 3.500000 m  

### Region Definition

Each cross-section is composed of four concentric regions:

- **C1 (D1)** — outer concrete boundary  
- **C2 (D2)** — outer boundary of the steel-equivalent ring  
- **C3 (D3)** — inner boundary of the steel ring (concrete resumes)  
- **C4 (D4)** — inner concrete boundary (central void)

All circular regions are represented as **regular 40-sided polygons**
(41 vertices including closure).

---

## 2. Weight Assignment Used in CSF

Each region is assigned an **absolute weight value**.

CSF internally handles containment and weighting during section-property
evaluation. No manual subtraction, layering, or geometric manipulation
is performed at the user level.

The absolute weight values used in each test case are reported explicitly
in the “Assigned Weights” blocks of Sections 4 and 5.

---

## 3. Benchmark Reference Values

The reference benchmark provides **concrete-only** geometric properties
at five elevations:

- z = 0 m
- z = 30 m
- z = 60 m
- z = 90 m
- z = 120 m

The primary comparison targets are:

- Net concrete area **Ac**
- Second moment of area **Ix = Iy**

---

## 4. Test Case A — Concrete Geometry Only  
*(Benchmark Ac / Ix consistency check)*

### Assigned Weights

- C1 = 1  
- C2 = 1  
- C3 = 1  
- C4 = 0  

This configuration represents a purely concrete section with a central void
and excludes any steel contribution.

### 4.1 Comparison with Benchmark

| z (m) | CSF A (m²) | Bench Ac (m²) | ΔA (%) | CSF Ix (m⁴) | Bench Ix (m⁴) | ΔIx (%) |
|---:|---:|---:|---:|---:|---:|---:|
|   0 | 30.535990 | 30.65 | -0.372 | 568.223411 | 604.5 | -6.001 |
|  30 | 20.908923 | 21.01 | -0.481 | 266.006341 | 284.1 | -6.369 |
|  60 | 13.099427 | 13.15 | -0.385 | 104.163548 | 110.1 | -5.392 |
|  90 |  7.107502 |  7.14 | -0.455 |  30.542182 |  32.2 | -5.149 |
| 120 |  2.933148 |  2.95 | -0.571 |   5.157587 |   5.4 | -4.489 |

### Observations (Test Case A)

- **Area (A)** agreement is within ~0.4–0.6%, consistent with the
  40-gon geometric approximation.
- **Second moment of area (Ix)** is consistently ~4–6% lower than the
  benchmark values.
- The inertia discrepancy exceeds the expected polygonal discretization
  error and suggests that the benchmark **Ix** values are not strictly
  consistent with a perfect circular annulus derived directly from
  the published `(D, t)` data.

---

## 5. Test Case B — Composite Section  
*(Density-homogenized steel contribution)*

### Objective

Include the steel-equivalent ring (`C2–C3`) using a density-based
homogenization relative to concrete, while preserving the same geometry
and central void.

### Assigned Weights (density ratio)

- C1 = 1  
- C2 = 3.14  
- C3 = 1  
- C4 = 0  

where:

- `3.14 ≈ ρ_steel / ρ_concrete ≈ 7850 / 2500`

### 5.1 CSF Results (Composite Section)

| z (m) | CSF A_eq (m²) | CSF Ix (m⁴) |
|---:|---:|---:|
|   0 | 31.388437 | 584.018120 |
|  30 | 21.666868 | 275.607621 |
|  60 | 13.740627 | 109.240231 |
|  90 |  7.609716 |  32.690907 |
| 120 |  3.274135 |   5.754526 |

### Interpretation (Test Case B)

- **A_eq** represents a *concrete-equivalent* area suitable for mass scaling
  (and, if required, stiffness scaling); it is not a geometric area.
- Differences relative to Test Case A arise exclusively from the
  steel-equivalent region, while the concrete geometry remains unchanged.

CSF-computed cross-section areas agree with the benchmark within ±0.6%.
Second moments of area are consistently lower than the benchmark values,
with deviations ranging from approximately 4.5% to 6.4%.


---

## 6. Notes and Limitations

- Steel reinforcement is modeled as a **continuous thin annular region**
  calibrated to match the *total* steel area.
  This approach reproduces global mass-equivalent effects but does **not**
  represent discrete bar or tendon layouts.
- If separate contributions of **As** and **Ap** are required, they must be
  modeled as **distinct regions** with independent weight assignments.
- The benchmark inertia values appear to follow a convention or rounding
  scheme different from the pure annular formulation implied by `(D, t)`.
  CSF results are internally consistent with the supplied diameters and the
  adopted polygonal discretization.

---

## 7. Files

- CSF geometry definition (40-gon, four concentric regions):  
  `acciona_aw3000_4circles_40sides.yaml`
