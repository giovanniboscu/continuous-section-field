# CSF Verification Report — Acciona AW3000 Concrete Tower (H = 120 m)
This report summarizes the first CSF validation runs performed on a simplified 120 m concrete wind-turbine tower benchmark (AW3000-style). The tower is represented with two stations (z = 0 m and z = 120 m) and four concentric circular regions approximated by 40-sided polygons.
## 1. Geometry model used in CSF
Two stations were defined:
- **S0 (z = 0 m)**: D1=13.000000, D2=12.210436, D3=12.189564, D4=11.400000 (m)
- **S1 (z = 120 m)**: D1=4.000000, D2=3.763581, D3=3.736419, D4=3.500000 (m)

Region meaning:
- **C1 (D1)**: outer concrete boundary
- **C2 (D2)**: outer boundary of the *steel equivalent ring*
- **C3 (D3)**: inner boundary of the steel ring (concrete resumes)
- **C4 (D4)**: inner concrete boundary (central void / hole)

All circles are modeled as regular **40-gons** (41 vertices including closure).
## 2. Weighting concept (W)
CSF computes *weighted/relativized* section properties. With nested polygons, the effective weight in each annular region is the difference between the child and its immediate container (parent).

For the concentric case:
- Effective weight in **C1→C2** ring is **W(C1)**
- Effective weight in **C2→C3** ring is **W(C2) − W(C1)**
- Effective weight in **C3→C4** ring is **W(C3) − W(C2)**
- Effective weight in the **hole** is **W(C4) − W(C3)** (typically forced to 0)
## 3. Benchmark reference values
The benchmark provides concrete-only geometric properties at five stations (0, 30, 60, 90, 120 m). Key targets used here:
- Concrete net area **Ac**
- Second moment of area **Ix = Iy**
## 4. Test Case A — Concrete geometry only (benchmark Ac/I check)
**Weights:** C1=1, C2=1, C3=1, C4=0
This configuration forces the field to be 1 in the entire concrete wall up to the benchmark inner diameter (hole at C4), excluding steel effects.

### A.1 Comparison vs benchmark
| z (m) | CSF A (m²) | Bench Ac (m²) | ΔA (%) | CSF Ix (m⁴) | Bench Ix (m⁴) | ΔIx (%) |
|---:|---:|---:|---:|---:|---:|---:|
|   0 |  30.535990 |      30.65 |  -0.372 |  568.223411 |       604.5 |  -6.001 |
|  30 |  20.908923 |      21.01 |  -0.481 |  266.006341 |       284.1 |  -6.369 |
|  60 |  13.099427 |      13.15 |  -0.385 |  104.163548 |       110.1 |  -5.392 |
|  90 |   7.107502 |       7.14 |  -0.455 |   30.542182 |        32.2 |  -5.149 |
| 120 |   2.933148 |       2.95 |  -0.571 |    5.157587 |         5.4 |  -4.489 |

**Observations (Test Case A):**
- **Area** matches closely (errors ~0.4–0.6%), consistent with a 40-gon approximation.
- **Ix** is consistently ~4–6% lower than the benchmark table. This is larger than the 40-gon discretization error and suggests that the benchmark **Ix** values are not strictly consistent with (D, t) if interpreted as a perfect circular annulus.
## 5. Test Case B — Composite, density-homogenized section (steel total area)
Goal: include the steel equivalent ring (C2–C3) using a density ratio relative to concrete.

**Intended weights (density ratio):** C1=1, C2=3.14, C3=1, C4=0
- 3.14 ≈ 7850/2500 (steel/concrete density ratio)
- The steel ring adds an equivalent contribution proportional to (C2 − 1)

### B.1 Run actually posted by user
The numerical output pasted in the chat corresponds to **C2=3.24** (not 3.14). Those values are kept below as a recorded run.
| z (m) | CSF Aeq (C2=3.24) | CSF Ix (C2=3.24) |
|---:|---:|---:|
|   0 |      31.388437 |     584.018120 |
|  30 |      21.666868 |     275.607621 |
|  60 |      13.740627 |     109.240231 |
|  90 |       7.609716 |      32.690907 |
| 120 |       3.274135 |       5.754526 |

### B.2 Expected adjustment to C2=3.14
For this nested-ring configuration, the steel contribution scales linearly with **(C2−1)**. Therefore, moving from 3.24 to 3.14 scales only the steel increment by:

- scale = (3.14−1)/(3.24−1) = **0.955357**

Approximate adjusted values (same geometry, same discretization):
| z (m) | Aeq (C2=3.14) | Ix (C2=3.14) |
|---:|---:|---:|
|   0 |      31.350381 |     583.312999 |
|  30 |      21.633031 |     275.178993 |
|  60 |      13.712002 |     109.013593 |
|  90 |       7.587296 |      32.594982 |
| 120 |       3.258912 |       5.727877 |

**Interpretation (Test Case B):**
- **Aeq** is a *concrete-equivalent* area for mass (and, if desired, stiffness) scaling; it is not equal to the geometric area Ac.
- The increase from Test Case A to Test Case B is driven by the thin steel ring (C2–C3) multiplied by (ρs/ρc − 1).
## 6. Notes / limitations
- The steel reinforcement is represented as a **continuous thin ring**, calibrated to match the *total* steel area (As+Ap). This reproduces mass-equivalent effects but does not represent the discrete bar/tendon layout.
- If you need **As** and **Ap** separately, you must introduce **two distinct steel regions** (or two independent weighting fields).
- The benchmark table appears to use a different convention or rounding for inertia values (Ix) than the pure annulus formula implied by (D, t). CSF results are internally consistent with the supplied diameters and the polygonal discretization.
## 7. Files
- CSF geometry YAML (40-gon, 4 rings): `acciona_aw3000_4circles_40sides.yaml`
