# Validation comparison - NREL-5-MW-degr

This report compares the CSF-OpenSees tip response against an independent analytical reference.

## Conceptual structure

Two configurations are compared. The undegraded NREL tower is used as the baseline validation case. The degraded tower is used as the critical convergence case, because localized stiffness variation makes coarse piecewise discretizations less reliable.

## Key quantities

- `Uy`: transverse tip displacement.
- `Rz`: torsional tip rotation.
- `Section evaluations`: number of CSF section evaluations used by the model.
- Relative error: `100 * (OpenSees - reference) / reference`.

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
