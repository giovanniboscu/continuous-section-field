# CUF suspicious-order report

This report flags **local spikes** in the FEM3D error sequence. It is a diagnostic heuristic, not a proof that an order is mathematically invalid.

- Spike threshold: `2.5x` local baseline
- Minimum significant RMS error: `0.0001` of the case/component FEM3D peak
- The first available N is never flagged merely because it is a low order.
- Interior N values are compared with their two immediate neighbours.
- The last available N is compared with the median of preceding orders.

## Summary by N

| Case | N | Severity | Flagged channels | Max spike score |
|---|---:|---|---:|---:|
| `bending_lagrange` | 16 | **HIGH** | 3 | 12.69 |
| `bending_lagrange` | 21 | **LOW** | 1 | 3.18 |
| `bending_legendre` | 16 | **LOW** | 1 | 2.90 |
| `bending_legendre` | 21 | **HIGH** | 4 | 116.08 |
| `torsion_lagrange` | 16 | **HIGH** | 4 | 13.71 |
| `torsion_lagrange` | 22 | **LOW** | 1 | 2.54 |
| `torsion_legendre` | 24 | **MEDIUM** | 5 | 7.04 |

## Detailed flags

| Case | N | Component | Point | Severity | RMS error [mm] | Baseline [mm] | Spike score | x/L at max error |
|---|---:|---|---|---|---:|---:|---:|---:|
| `bending_lagrange` | 16 | `uy` | `bottom_mid` | **HIGH** | 6.181832e-04 | 6.466261e-05 | 9.56 | 0.55 |
| `bending_lagrange` | 16 | `uy` | `center` | **HIGH** | 3.472232e-04 | 2.736195e-05 | 12.69 | 0.55 |
| `bending_lagrange` | 16 | `uy` | `minus` | **MEDIUM** | 6.869898e-04 | 9.866670e-05 | 6.96 | 0.40 |
| `bending_lagrange` | 21 | `uy` | `plus` | **LOW** | 2.562316e-04 | 8.059452e-05 | 3.18 | 0.05 |
| `bending_legendre` | 16 | `uy` | `minus` | **LOW** | 9.126402e-05 | 3.145862e-05 | 2.90 | 0.85 |
| `bending_legendre` | 21 | `uy` | `bottom_mid` | **HIGH** | 3.597502e-03 | 6.438221e-05 | 55.88 | 0.65 |
| `bending_legendre` | 21 | `uy` | `center` | **HIGH** | 1.988270e-03 | 3.481635e-05 | 57.11 | 0.60 |
| `bending_legendre` | 21 | `uy` | `minus` | **HIGH** | 4.647461e-03 | 4.003712e-05 | 116.08 | 0.35 |
| `bending_legendre` | 21 | `uy` | `plus` | **HIGH** | 1.438724e-03 | 6.530328e-05 | 22.03 | 0.20 |
| `torsion_lagrange` | 16 | `ux` | `bottom_mid` | **HIGH** | 1.214563e-04 | 9.771762e-06 | 12.43 | 0.00 |
| `torsion_lagrange` | 16 | `ux` | `center` | **HIGH** | 8.158671e-05 | 5.948812e-06 | 13.71 | 0.75 |
| `torsion_lagrange` | 16 | `uz` | `bottom_mid` | **MEDIUM** | 5.109743e-05 | 8.839050e-06 | 5.78 | 0.60 |
| `torsion_lagrange` | 16 | `uz` | `center` | **HIGH** | 5.252025e-05 | 5.231277e-06 | 10.04 | 0.90 |
| `torsion_lagrange` | 22 | `uz` | `center` | **LOW** | 1.734113e-05 | 6.818694e-06 | 2.54 | 0.30 |
| `torsion_legendre` | 24 | `ux` | `bottom_mid` | **MEDIUM** | 2.260265e-04 | 4.782570e-05 | 4.73 | 0.45 |
| `torsion_legendre` | 24 | `ux` | `center` | **MEDIUM** | 1.904714e-04 | 3.692193e-05 | 5.16 | 0.10 |
| `torsion_legendre` | 24 | `ux` | `plus` | **LOW** | 3.266565e-04 | 1.258100e-04 | 2.60 | 0.00 |
| `torsion_legendre` | 24 | `uz` | `bottom_mid` | **MEDIUM** | 8.287509e-05 | 1.565166e-05 | 5.29 | 0.10 |
| `torsion_legendre` | 24 | `uz` | `center` | **MEDIUM** | 6.449289e-05 | 9.161485e-06 | 7.04 | 0.30 |
