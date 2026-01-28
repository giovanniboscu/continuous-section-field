# AW3000 — New Reference Table (Closed-Form, with Steel)

This document rebuilds the **reference table from scratch** using **ideal closed-form** formulas for a circular annulus, and includes steel area with homogenization weights.

## Inputs

- Concrete weight: **CLS = 1.00**
- Steel weight: **Steel = 3.14**

Geometry per station:

| Station | z (m) | Do (m) | t (m) | Di = Do-2t (m) | Rm (m) | As (m²) | Ap (m²) | Ast=As+Ap (m²) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Base (0 m) | 0 | 13.00 | 0.80 | 11.40 | 6.10 | 0.300 | 0.100 | 0.400 |
| S1 (30 m) | 30 | 10.75 | 0.66 | 9.43 | 5.04 | 0.200 | 0.100 | 0.300 |
| S2 (60 m) | 60 | 8.50 | 0.52 | 7.46 | 3.99 | 0.130 | 0.100 | 0.230 |
| S3 (90 m) | 90 | 6.25 | 0.39 | 5.47 | 2.93 | 0.085 | 0.100 | 0.185 |
| Top (120 m) | 120 | 4.00 | 0.25 | 3.50 | 1.88 | 0.060 | 0.100 | 0.160 |

## Formulas (concrete annulus)

- Area:  A = (π/4)·(Do² − Di²)
- Inertia (Ix=Iy):  I = (π/64)·(Do⁴ − Di⁴)
- Polar moment:  Jp = 2·I
- Saint-Venant torsion (circular annulus):  Jsv = Jp
- Thin-wall Bredt (approx.):  Jb ≈ 2π·Rm³·t

Derived:
- Radius of gyration: r = sqrt(I/A)
- Section modulus: W = I / Ro  (Ro=Do/2)


## Concrete-only (pure geometry)

| Key | Unit | Base (0 m) | S1 (30 m) | S2 (60 m) | S3 (90 m) | Top (120 m) |
|---|---|---:|---:|---:|---:|---:|
| Area A_c | m² | 30.66 | 20.92 | 13.04 | 7.18 | 2.95 |
| Inertia Ix=Iy (I_c) | m⁴ | 572.92 | 267.38 | 104.21 | 30.96 | 5.20 |
| Polar Moment Jp_c | m⁴ | 1145.84 | 534.76 | 208.42 | 61.91 | 10.40 |
| J Saint-Venant (Jsv_c) | m⁴ | 1145.84 | 534.76 | 208.42 | 61.91 | 10.40 |
| J Bredt (Jb_c) | m⁴ | 1140.93 | 532.48 | 207.54 | 61.64 | 10.35 |
| Radius of Gyration r_c | m | 4.32 | 3.57 | 2.83 | 2.08 | 1.33 |
| Section Modulus W_c | m³ | 88.14 | 49.75 | 24.52 | 9.91 | 2.60 |

## Composite (homogenized) — CLS=1, Steel=3.14

Assumption for steel inertia: **steel area Ast is smeared as a thin ring at mean radius Rm**, so `Jp_s = Ast·Rm²` and `Ix_s = Iy_s = 0.5·Jp_s`.

| Key | Unit | Base (0 m) | S1 (30 m) | S2 (60 m) | S3 (90 m) | Top (120 m) |
|---|---|---:|---:|---:|---:|---:|
| Effective Area A_eff = A_c + 3.14·Ast | m²(eq) | 31.92 | 21.86 | 13.76 | 7.76 | 3.45 |
| Effective Inertia Ix=Iy (I_eff) | m⁴(eq) | 596.29 | 279.37 | 109.96 | 33.45 | 6.08 |
| Effective Polar Moment Jp_eff = 2·I_eff | m⁴(eq) | 1192.57 | 558.74 | 219.92 | 66.90 | 12.17 |
| Effective J Saint-Venant Jsv_eff | m⁴(eq) | 1192.57 | 558.74 | 219.92 | 66.90 | 12.17 |
| Effective J Bredt-like Jb_eff | m⁴(eq) | 1187.67 | 556.46 | 219.04 | 66.62 | 12.12 |
| Effective Radius of Gyration r_eff | m | 4.32 | 3.57 | 2.83 | 2.08 | 1.33 |
| Effective Section Modulus W_eff | m³(eq) | 91.74 | 51.98 | 25.87 | 10.70 | 3.04 |


# CSF Composite Results Table — Concrete + Steel (2 decimals)

Section-selected analysis results at the five stations (values rounded to **2 decimals**).

| Key | Unit | Base (0 m) | S1 (30 m) | S2 (60 m) | S3 (90 m) | Top (120 m) |
|---|---|---:|---:|---:|---:|---:|
| Height (z) | m | 0 | 30 | 60 | 90 | 120 |
| Area A | m² | 31.39 | 21.67 | 13.74 | 7.61 | 3.27 |
| Centroid Cx | m | -0.00 | -0.00 | 0.00 | -0.00 | -0.00 |
| Centroid Cy | m | -0.00 | -0.00 | 0.00 | -0.00 | -0.00 |
| Inertia Ix | m⁴ | 584.02 | 275.61 | 109.24 | 32.69 | 5.75 |
| Inertia Iy | m⁴ | 584.02 | 275.61 | 109.24 | 32.69 | 5.75 |
| Product Ixy | m⁴ | 0.00 | -0.00 | 0.00 | 0.00 | 0.00 |
| Polar Moment J | m⁴ | 1168.04 | 551.22 | 218.48 | 65.38 | 11.51 |
| Principal I1 | m⁴ | 584.02 | 275.61 | 109.24 | 32.69 | 5.75 |
| Principal I2 | m⁴ | 584.02 | 275.61 | 109.24 | 32.69 | 5.75 |
| Radius rx | m | 4.31 | 3.57 | 2.82 | 2.07 | 1.33 |
| Radius ry | m | 4.31 | 3.57 | 2.82 | 2.07 | 1.33 |
| Section Modulus Wx | m³ | 89.85 | 51.28 | 25.70 | 10.46 | 2.88 |
| Section Modulus Wy | m³ | 89.85 | 51.28 | 25.70 | 10.46 | 2.88 |
| K_torsion | m⁴ | 20.78 | 10.00 | 4.08 | 1.28 | 0.25 |
| First Moment Q_na | m³ | 60.91 | 34.76 | 17.43 | 7.10 | 1.95 |
| J_sv | m⁴ | 309.48 | 188.22 | 99.60 | 42.21 | 11.76 |
| J_s_vroark | m⁴ | 1028.06 | 485.16 | 192.30 | 57.55 | 10.13 |
| J_s_vroark_fidelity | - | 0.10 | 0.10 | 0.10 | 0.10 | 0.10 |


