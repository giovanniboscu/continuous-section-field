# Same-point FEM3D H20 vs CSF-CUF

FEM H20 elements used: **3072/3072**; common physical points: **24576**; Gauss per axis: **2**.

Both models evaluated at the exact same physical positions in the FEM x,y,z coordinate system.
Values below are Jacobian-weighted over the accepted **element/domain interiors**.

| Quantity | FEM3D H20 RMS | CSF-CUF RMS | CUF/FEM |
|---|---:|---:|---:|
| div_x (MPa/mm) | 0.13127148 | 0.11150557 | 0.849427 |
| div_y (MPa/mm) | 0.040396612 | 0.036151823 | 0.894922 |
| div_z (MPa/mm) | 0.039093686 | 0.027340426 | 0.699357 |
| div_norm (MPa/mm) | 0.14280197 | 0.12036588 | 0.842887 |

| Component | Common-point displacement difference RMS (mm) |
|---|---:|
| x | 2.8301864e-05 |
| y | 4.7422615e-06 |
| z | 0.00036838549 |

Common-sample min uz: FEM3D = -1.71644178 mm; CUF = -1.71585071 mm.
These are minima ON THE COMMON SAMPLED POINTS, not global displacement extrema.

## Interpretation

CUF/FEM < 1 means CUF has a smaller interior strong-equilibrium RMS for that component.
These metrics do NOT establish a global equilibrium ranking: traction jumps and external-surface tractions are not included.
FEM3D H20 freezes E within each element, while CSF-CUF evaluates the continuous x-dependent material.
The reported RMS values are evaluated at common physical quadrature points using consistent integration weights.

## Documentation

- [Scenario overview](../../README.md)
- [FEM3D H20 vs CSF-CUF equilibrium analysis](../../FEM3D-H20-CUF-equilibrium.md)
