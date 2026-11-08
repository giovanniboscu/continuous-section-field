# CSF-CUF equilibration-checkpoint stability

**Result:** PASS

**Scope:** sampled displacements and the available saved coefficient arrays.

**Compared coefficient fields:** `solved_nodal_domain_natural_coefficients`.

**Input directory:** `output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3`

**Checkpoints:** eq1, eq2, eq3, eq4, eq5

**Criterion:** `max|b-a| <= 1.000e-09 + 1.000e-08 * max(max|a|, max|b|)`.
The scale is calculated per response component or coefficient array, not pointwise.
The absolute tolerance is expressed in the native units of the compared data
(mm for displacements and physical displacement coefficients).

## Comparison with eq1

| Checkpoint | Report u max diff (mm) | DOF coefficient max diff | Reconstructed-field coefficient max diff | Result |
|---|---:|---:|---:|---|
| eq2 | 2.000011e-12 | not evaluated | 7.565282e-12 | PASS |
| eq3 | 1.869707e-12 | not evaluated | 6.947110e-12 | PASS |
| eq4 | 1.899980e-12 | not evaluated | 6.572298e-12 | PASS |
| eq5 | 1.700029e-12 | not evaluated | 6.401546e-12 | PASS |

## Detailed checks

| Pair | Mode | Data | Max abs diff | RMS diff | Relative max | Allowed | PASS |
|---|---|---|---:|---:|---:|---:|---|
| eq1 -> eq2 | vs_reference | `ux` (response) | 1.599998e-12 | 1.140543e-12 | 4.968608e-12 | 4.220214e-09 | PASS |
| eq1 -> eq2 | vs_reference | `uy` (response) | 4.020000e-13 | 2.270070e-13 | 2.353143e-10 | 1.017084e-09 | PASS |
| eq1 -> eq2 | vs_reference | `uz` (response) | 2.000011e-12 | 1.140545e-12 | 4.489369e-12 | 5.454995e-09 | PASS |
| eq1 -> eq2 | vs_reference | `u_xyz` (response) | 2.000011e-12 | 9.404279e-13 | 4.489369e-12 | 5.454995e-09 | PASS |
| eq1 -> eq2 | vs_reference | `solved_nodal_domain_natural_coefficients` (checkpoint) | 7.565282e-12 | 1.036614e-12 | 4.415218e-12 | 1.813456e-08 | PASS |
| eq1 -> eq3 | vs_reference | `ux` (response) | 1.700029e-12 | 1.235585e-12 | 5.279243e-12 | 4.220214e-09 | PASS |
| eq1 -> eq3 | vs_reference | `uy` (response) | 1.869707e-12 | 9.850272e-13 | 1.094450e-09 | 1.017084e-09 | PASS |
| eq1 -> eq3 | vs_reference | `uz` (response) | 1.700029e-12 | 8.972273e-13 | 3.816007e-12 | 5.454995e-09 | PASS |
| eq1 -> eq3 | vs_reference | `u_xyz` (response) | 1.869707e-12 | 1.049121e-12 | 4.196879e-12 | 5.454995e-09 | PASS |
| eq1 -> eq3 | vs_reference | `solved_nodal_domain_natural_coefficients` (checkpoint) | 6.947110e-12 | 1.211833e-12 | 4.054443e-12 | 1.813456e-08 | PASS |
| eq1 -> eq4 | vs_reference | `ux` (response) | 1.700029e-12 | 1.185327e-12 | 5.279243e-12 | 4.220214e-09 | PASS |
| eq1 -> eq4 | vs_reference | `uy` (response) | 1.453686e-12 | 7.588726e-13 | 8.509276e-10 | 1.017084e-09 | PASS |
| eq1 -> eq4 | vs_reference | `uz` (response) | 1.899980e-12 | 9.979220e-13 | 4.264832e-12 | 5.454995e-09 | PASS |
| eq1 -> eq4 | vs_reference | `u_xyz` (response) | 1.899980e-12 | 9.961150e-13 | 4.264832e-12 | 5.454995e-09 | PASS |
| eq1 -> eq4 | vs_reference | `solved_nodal_domain_natural_coefficients` (checkpoint) | 6.572298e-12 | 1.105796e-12 | 3.835697e-12 | 1.813456e-08 | PASS |
| eq1 -> eq5 | vs_reference | `ux` (response) | 1.100009e-12 | 6.683590e-13 | 3.415950e-12 | 4.220214e-09 | PASS |
| eq1 -> eq5 | vs_reference | `uy` (response) | 1.223000e-12 | 5.641520e-13 | 7.158938e-10 | 1.017084e-09 | PASS |
| eq1 -> eq5 | vs_reference | `uz` (response) | 1.700029e-12 | 9.246720e-13 | 3.816007e-12 | 5.454995e-09 | PASS |
| eq1 -> eq5 | vs_reference | `u_xyz` (response) | 1.700029e-12 | 7.348446e-13 | 3.816007e-12 | 5.454995e-09 | PASS |
| eq1 -> eq5 | vs_reference | `solved_nodal_domain_natural_coefficients` (checkpoint) | 6.401546e-12 | 9.510576e-13 | 3.736044e-12 | 1.813456e-08 | PASS |
| eq1 -> eq2 | consecutive | `ux` (response) | 1.599998e-12 | 1.140543e-12 | 4.968608e-12 | 4.220214e-09 | PASS |
| eq1 -> eq2 | consecutive | `uy` (response) | 4.020000e-13 | 2.270070e-13 | 2.353143e-10 | 1.017084e-09 | PASS |
| eq1 -> eq2 | consecutive | `uz` (response) | 2.000011e-12 | 1.140545e-12 | 4.489369e-12 | 5.454995e-09 | PASS |
| eq1 -> eq2 | consecutive | `u_xyz` (response) | 2.000011e-12 | 9.404279e-13 | 4.489369e-12 | 5.454995e-09 | PASS |
| eq1 -> eq2 | consecutive | `solved_nodal_domain_natural_coefficients` (checkpoint) | 7.565282e-12 | 1.036614e-12 | 4.415218e-12 | 1.813456e-08 | PASS |
| eq2 -> eq3 | consecutive | `ux` (response) | 4.000134e-13 | 2.140998e-13 | 1.242195e-12 | 4.220214e-09 | PASS |
| eq2 -> eq3 | consecutive | `uy` (response) | 1.481000e-12 | 7.604637e-13 | 8.669162e-10 | 1.017084e-09 | PASS |
| eq2 -> eq3 | consecutive | `uz` (response) | 4.999889e-13 | 2.499965e-13 | 1.122311e-12 | 5.454995e-09 | PASS |
| eq2 -> eq3 | consecutive | `u_xyz` (response) | 1.481000e-12 | 4.784148e-13 | 3.324358e-12 | 5.454995e-09 | PASS |
| eq2 -> eq3 | consecutive | `solved_nodal_domain_natural_coefficients` (checkpoint) | 4.847339e-12 | 5.928614e-13 | 2.828983e-12 | 1.813456e-08 | PASS |
| eq3 -> eq4 | consecutive | `ux` (response) | 2.999823e-13 | 1.225095e-13 | 9.315601e-13 | 4.220214e-09 | PASS |
| eq3 -> eq4 | consecutive | `uy` (response) | 4.170000e-13 | 2.264463e-13 | 2.440946e-10 | 1.017084e-09 | PASS |
| eq3 -> eq4 | consecutive | `uz` (response) | 2.000067e-13 | 1.040807e-13 | 4.489493e-13 | 5.454995e-09 | PASS |
| eq3 -> eq4 | consecutive | `u_xyz` (response) | 4.170000e-13 | 1.603323e-13 | 9.360280e-13 | 5.454995e-09 | PASS |
| eq3 -> eq4 | consecutive | `solved_nodal_domain_natural_coefficients` (checkpoint) | 1.031753e-12 | 1.500113e-13 | 6.021473e-13 | 1.813456e-08 | PASS |
| eq4 -> eq5 | consecutive | `ux` (response) | 9.000023e-13 | 6.271968e-13 | 2.794853e-12 | 4.220214e-09 | PASS |
| eq4 -> eq5 | consecutive | `uy` (response) | 2.274781e-12 | 1.308249e-12 | 1.331563e-09 | 1.017084e-09 | PASS |
| eq4 -> eq5 | consecutive | `uz` (response) | 1.999512e-13 | 7.637070e-14 | 4.488247e-13 | 5.454995e-09 | PASS |
| eq4 -> eq5 | consecutive | `u_xyz` (response) | 2.274781e-12 | 8.387934e-13 | 5.106137e-12 | 5.454995e-09 | PASS |
| eq4 -> eq5 | consecutive | `solved_nodal_domain_natural_coefficients` (checkpoint) | 8.764268e-12 | 1.157127e-12 | 5.114966e-12 | 1.813456e-08 | PASS |

## Interpretation

PASS indicates that the compared displacement data meet the selected tolerance
over eq1..eq5. The compared coefficient fields, when present, are listed above.
