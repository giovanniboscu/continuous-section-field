# Validation comparison - all scenarios

This report compares the CSF-OpenSees tip response against an independent analytical reference.

## Conceptual structure

Two configurations are compared. The undegraded NREL tower is used as the baseline validation case. The degraded tower is used as the critical convergence case, because localized stiffness variation makes coarse piecewise discretizations less reliable.

## Key quantities

- `Uy`: transverse tip displacement.
- `Rz`: torsional tip rotation.
- `Section evaluations`: number of CSF section evaluations used by the model.
- Relative error: `100 * (OpenSees - reference) / reference`.

## Case A - undegraded NREL tower

This case validates the CSF-OpenSees coupling on a smooth, undegraded reference configuration. The response converges rapidly, showing that a small number of beam elements is sufficient when the sectional stiffness variation is regular.

| Model | Elements | Section evaluations | Uy OpenSees | Uy reference | Uy rel. error [%] | Rz OpenSees | Rz reference | Rz rel. error [%] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Uniform-4 | 4 | 13 | 4.424887e-01 | 4.425810e-01 | -2.084342e-02 | 1.355401e-03 | 1.355489e-03 | -6.486277e-03 |
| Uniform-6 | 6 | 19 | 4.425633e-01 | 4.425810e-01 | -3.995270e-03 | 1.355434e-03 | 1.355489e-03 | -4.051630e-03 |
| Uniform-8 | 8 | 25 | 4.425762e-01 | 4.425810e-01 | -1.064610e-03 | 1.355440e-03 | 1.355489e-03 | -3.634435e-03 |
| Uniform-12 | 12 | 37 | 4.425811e-01 | 4.425810e-01 | 3.933018e-05 | 1.355442e-03 | 1.355489e-03 | -3.478278e-03 |
| Uniform-16 | 16 | 49 | 4.425820e-01 | 4.425810e-01 | 2.266791e-04 | 1.355442e-03 | 1.355489e-03 | -3.451879e-03 |
| Uniform-24 | 24 | 73 | 4.425823e-01 | 4.425810e-01 | 2.965142e-04 | 1.355443e-03 | 1.355489e-03 | -3.442054e-03 |
| Uniform-32 | 32 | 97 | 4.425823e-01 | 4.425810e-01 | 3.082899e-04 | 1.355443e-03 | 1.355489e-03 | -3.440399e-03 |

## Case B - degraded NREL tower

This case introduces localized stiffness degradation. The low-order piecewise discretizations show a less regular convergence pattern, highlighting the need for finer sectional sampling when the stiffness field varies sharply along the tower.

| Model | Elements | Section evaluations | Uy OpenSees | Uy reference | Uy rel. error [%] | Rz OpenSees | Rz reference | Rz rel. error [%] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Uniform-4 | 4 | 13 | 4.515337e-01 | 4.510653e-01 | 1.038552e-01 | 1.384136e-03 | 1.381149e-03 | 2.162109e-01 |
| Uniform-6 | 6 | 19 | 4.517698e-01 | 4.510653e-01 | 1.561789e-01 | 1.383296e-03 | 1.381149e-03 | 1.554297e-01 |
| Uniform-8 | 8 | 25 | 4.502834e-01 | 4.510653e-01 | -1.733444e-01 | 1.378374e-03 | 1.381149e-03 | -2.009401e-01 |
| Uniform-12 | 12 | 37 | 4.514388e-01 | 4.510653e-01 | 8.280051e-02 | 1.382211e-03 | 1.381149e-03 | 7.687473e-02 |
| Uniform-16 | 16 | 49 | 4.510459e-01 | 4.510653e-01 | -4.293960e-03 | 1.381071e-03 | 1.381149e-03 | -5.669813e-03 |
| Uniform-24 | 24 | 73 | 4.510696e-01 | 4.510653e-01 | 9.574450e-04 | 1.381111e-03 | 1.381149e-03 | -2.754317e-03 |
| Uniform-32 | 32 | 97 | 4.510665e-01 | 4.510653e-01 | 2.796429e-04 | 1.381101e-03 | 1.381149e-03 | -3.477114e-03 |

## Input files

- Analytical reference: `analytical_reference.txt`.
- OpenSees tip response: `openseeslab_tip_response.csv`.
