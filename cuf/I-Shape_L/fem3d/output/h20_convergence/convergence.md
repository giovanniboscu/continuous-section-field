# H20 convergence study

Same physical geometry, materials, supports and surface load across all mesh levels.
H20 internal stress divergence estimated by physical-volume-weighted quadrature.
Element interfaces and surface traction residual are NOT included in this diagnostic.
Interior residual subsample: max 0 elements per mesh (0=all).

| Mesh | Elements | Nodes | min uz (mm) | Delta (%) | rms rx | rms ry | rms rz | rms norm | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| T0 | 48 | 379 | -1.6445 | — | 0.0545552 | 0.0207049 | 0.0308375 | 0.0659993 | CHECK_REFINEMENT |
| T1 | 144 | 941 | -1.70612 | 3.74737 | 0.0559917 | 0.0149761 | 0.0178636 | 0.0606503 | CHECK_REFINEMENT |
| T2 | 768 | 4201 | -1.71463 | 0.498361 | 0.0836308 | 0.0204571 | 0.0211743 | 0.0886621 | CHECK_REFINEMENT |
| T3 | 1536 | 8161 | -1.71699 | 0.137555 | 0.0839826 | 0.0204878 | 0.0205686 | 0.0888589 | CHECK_REFINEMENT |
| T4 | 3072 | 16081 | -1.71702 | 0.00210416 | 0.0842061 | 0.0205554 | 0.0204172 | 0.0890509 | STABLE_MIN_UZ |
| T6 | 4608 | 24001 | -1.71718 | 0.00932705 | 0.0842621 | 0.0205766 | 0.0203887 | 0.0891021 | STABLE_MIN_UZ |

A small change of a global displacement is a convergence indicator, not by itself a proof of local stress convergence.
