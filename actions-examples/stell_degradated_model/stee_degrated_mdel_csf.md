# Offshore Steel Platform Degradation Model
## Parametric Reconstruction Dataset and Rationale (Engineering-Grade Scenario)

**File name:** `HSEReport-degration-complete-github.md`  
**Language:** English  
**Date:** 2026-02-09  
**Status:** Scenario-based model (plausible, not case-calibrated)

---

## 1) Purpose

This document provides a complete, reproducible, and internally consistent parametric dataset to draw and analyze separated tubular elements (CHS members) for an offshore steel platform degradation study.

It includes:

1. Geometry values ready for drawing (outer diameter, inner diameter, length).
2. A shared degradation law `w(z)` along elevation.
3. Element-wise parameters `(beta, sigma, z0)` with explicit engineering justification.
4. Clear boundaries between assumption and measurement.

---

## 2) Scope and interpretation

This dataset is intended for:

- conceptual structural modelling,
- sensitivity studies,
- scenario comparison,
- preliminary simulation workflows (e.g., section-property scaling, stiffness envelopes).

This dataset is **not** an as-built reconstruction of a specific asset, because no deterministic asset-level package is available (e.g., certified GA/isometric, full node connectivity, tolerance classes, shop revisions, inspection map per member).

---

## 3) Geometry basis and reconstruction strategy

### 3.1 Member shape convention

All members are represented as Circular Hollow Sections (CHS):

- Outer diameter `Do` fixed by member type.
- Wall thickness `t` defined by inventory (range or fixed value).
- Inner diameter derived as:

```text
Di = Do - 2*t
```

### 3.2 Why outer diameter is kept constant

For corrosion modelling in tubular offshore members, it is common in first-order engineering models to keep nominal `Do` and apply loss on wall thickness `t(z)`, i.e. variation in `Di(z)`.  
This is practical and consistent with many inspection datasets that report remaining thickness rather than a re-surveyed changing external envelope.

---

## 4) Deterministic drawing values (base scenario)

For rows with thickness ranges, the base value is the midpoint:

```text
t_base = (t_min + t_max) / 2
```

Derived inner diameter for drawing:

```text
Di_base = Do - 2*t_base
```

| ID | Element | Do [m] | t_base [mm] | L [m] | t_base [m] | Di_base [m] |
|---|---:|---:|---:|---:|---:|---:|
| MP-1 | Main pile (typical) | 1.80 | 50.0 | 85 | 0.0500 | 1.700 |
| MP-2 | Main pile (large) | 2.40 | 62.5 | 90 | 0.0625 | 2.275 |
| CG-1 | Conductor guide | 1.20 | 30.0 | 65 | 0.0300 | 1.140 |
| JL-1 | Jacket leg (typical) | 1.40 | 37.5 | 60 | 0.0375 | 1.325 |
| HB-1 | Horizontal brace | 0.80 | 16.0 | 12 | 0.0160 | 0.768 |
| DB-1 | Diagonal brace | 0.60 | 14.0 | 18 | 0.0140 | 0.572 |
| MB-1 | Mudline brace | 0.50 | 12.0 | 8 | 0.0120 | 0.476 |

---

## 5) Degradation law w(z)

A shared parametric law is applied to all members:

```text
w(z) = 1 - beta * exp( - (z - z0)^2 / (2*sigma^2) )
```

Where:

- `w(z)` = normalized property multiplier at elevation `z`,
- `beta` = maximum degradation amplitude for that member,
- `z0` = elevation of peak aggressiveness (reference near mean sea level),
- `sigma` = vertical spread (critical-band width).

---

## 6) Chosen parameters and full table

### 6.1 Shared parameters

- sigma = 1.5 m for all members (moderate splash-band width).
- z0 = 0.0 m for all members (local mean-sea-level reference).

### 6.2 Element-wise beta values

beta is differentiated by vulnerability class.  
Rationale: thinner members generally exhibit larger **relative** stiffness/property loss for comparable absolute thickness loss.

| ID | Element | Do [m] | t_base [mm] | L [m] | Di_base [m] | beta [-] | sigma [m] | z0 [m] | w_min = 1 - beta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MP-1 | Main pile (typical) | 1.80 | 50.0 | 85 | 1.700 | 0.28 | 1.5 | 0.0 | 0.72 |
| MP-2 | Main pile (large) | 2.40 | 62.5 | 90 | 2.275 | 0.24 | 1.5 | 0.0 | 0.76 |
| CG-1 | Conductor guide | 1.20 | 30.0 | 65 | 1.140 | 0.32 | 1.5 | 0.0 | 0.68 |
| JL-1 | Jacket leg (typical) | 1.40 | 37.5 | 60 | 1.325 | 0.30 | 1.5 | 0.0 | 0.70 |
| HB-1 | Horizontal brace | 0.80 | 16.0 | 12 | 0.768 | 0.36 | 1.5 | 0.0 | 0.64 |
| DB-1 | Diagonal brace | 0.60 | 14.0 | 18 | 0.572 | 0.38 | 1.5 | 0.0 | 0.62 |
| MB-1 | Mudline brace | 0.50 | 12.0 | 8 | 0.476 | 0.40 | 1.5 | 0.0 | 0.60 |

---

## 7) Exhaustive rationale for parameter choices

### 7.1 Why Gaussian-like envelope

A Gaussian envelope provides a compact and stable representation of a localized corrosive maximum around splash-zone elevation, with smooth decay above and below.

Advantages:

- minimal parameter set `(beta, sigma, z0)`,
- numerical smoothness for optimization/FEM pipelines,
- straightforward sensitivity analysis.

### 7.2 Why single z0

The same `z0` is chosen for all members to maintain a common environmental reference (mean sea level in local datum).  
This is appropriate in a first-pass platform-level model; member-specific `z0` can be introduced after field calibration.

### 7.3 Why single sigma

A single `sigma = 1.5 m` is used to preserve model comparability across members under a moderate sea-state assumption.  
This avoids embedding unverified complexity before data-backed calibration.

### 7.4 Why differentiated beta

`beta` is the dominant damage-amplitude parameter and is varied by member class:

- **Lower beta in larger/thicker primary members** (MP-2, MP-1): stronger reserve against relative loss.
- **Higher beta in slender braces** (HB-1, DB-1, MB-1): greater relative sensitivity to thickness reduction.
- **Intermediate values** for conductor and jacket leg classes (CG-1, JL-1).

This is an engineering prior, not a direct measurement.

### 7.5 Physical interpretation of w_min

```text
w_min = 1 - beta
```

`w_min` is the minimum normalized property at `z = z0`.  
Example: `beta = 0.40` implies a 40% reduction in the modelled normalized property at peak zone.

---

## 8) How to draw separated elements

For each row:

1. Create a CHS with `Do`, `Di_base`, length `L`.
2. Assign local axis `z in [0, L]`.
3. Centerline at `(x, y) = (0, 0)` for element-local drawing.
4. Apply `w(z)` as property multiplier in analysis (not as direct geometric taper unless explicitly converted).

---

## 9) Recommended scenario set (for robustness)

Use three sensitivity families:

- **Low degradation:** `beta_i - 0.05` (floored at 0.10),
- **Base degradation:** table values,
- **High degradation:** `beta_i + 0.05` (capped at 0.60),

with optional `sigma in {1.0, 1.5, 2.5} m` sweeps.

This provides uncertainty bands without claiming deterministic field truth.

---

## 10) Limits and compliance statement

This reconstruction is:

- plausible and technically coherent,
- reproducible as a scenario dataset,
- not deterministic as-built without per-member inspection-calibrated data.

Therefore, any claim of exact asset condition must be avoided unless validated against UT/NDT evidence.

---

## 11) Bibliographic references (verified, citable)

1. **Health and Safety Executive (HSE), UK**  
   Offshore key programme reports (includes KP3 context).  
   https://www.hse.gov.uk/offshore/programmereports.htm

2. **Health and Safety Executive (HSE), UK**  
   Research report index listing RR748 (KP3 inspection analysis).  
   https://www.hse.gov.uk/research/rrhtm/701-800.htm

3. **DNV**  
   DNV-RP-C203: Fatigue design of offshore steel structures (official standard page).  
   https://www.dnv.com/energy/standards-guidelines/dnv-rp-c203-fatigue-design-of-offshore-steel-structures/

4. **Melchers, R. E. (2006)**  
   Recent progress in modeling seawater corrosion of structural steel.  
   *Journal of Materials in Civil Engineering*, 18(3), 415–422.  
   DOI landing: https://ascelibrary.org/doi/10.1061/%28ASCE%290899-1561%282006%2918%3A3%28415%29

5. **Paik, J. K., & Thayamballi, A. K. (2003)**  
   *Ultimate Limit State Design of Steel-Plated Structures*. Wiley.

---

## Appendix A — Direct formula legend

```text
w(z) = 1 - beta * exp( - (z - z0)^2 / (2*sigma^2) )
```

Use `(beta, sigma, z0)` from each table row (shared `sigma` and `z0` in this base model).
