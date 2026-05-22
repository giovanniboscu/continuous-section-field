# Validation comparison - all scenarios

This report compares the CSF-OpenSees tip response against an independent analytical reference.

## Conceptual structure

Two configurations are compared. The undegraded NREL tower is used as the baseline validation case. The degraded tower is used as the critical convergence case, because localized stiffness variation makes coarse piecewise discretizations less reliable.

The same beam formulation exhibits markedly different convergence behaviour depending on the smoothness of the underlying sectional stiffness field.

## Key quantities

- `Uy`: transverse tip displacement.
- `Rz`: torsional tip rotation.
- `Section evaluations`: number of CSF section evaluations used by the model.
- Relative error: `(OpenSees - reference) / reference`, reported as a percentage.

## Case A - undegraded NREL tower

This case validates the CSF-OpenSees coupling on a smooth, undegraded reference configuration. The response converges rapidly, showing that a small number of beam elements is sufficient when the sectional stiffness variation is regular.

The strongest visual evidence for this case is provided by the convergence plots:

![Undegraded NREL tower - tip displacement convergence](openseeslab_output_NREL-5-MW/plot_tip_displacement_convergence.png)

![Undegraded NREL tower - tip torsional rotation convergence](openseeslab_output_NREL-5-MW/plot_tip_torsional_rotation_convergence.png)

| Model | Elements | Section evaluations | Uy OpenSees | Uy reference | Uy rel. error | Rz OpenSees | Rz reference | Rz rel. error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Uniform-4 | 4 | 13 | 4.424887e-01 | 4.425810e-01 | -0.0208% | 1.355401e-03 | 1.355541e-03 | -0.0103% |
| Uniform-6 | 6 | 19 | 4.425633e-01 | 4.425810e-01 | -0.0040% | 1.355434e-03 | 1.355541e-03 | -0.0079% |
| Uniform-8 | 8 | 25 | 4.425762e-01 | 4.425810e-01 | -0.0011% | 1.355440e-03 | 1.355541e-03 | -0.0075% |
| Uniform-12 | 12 | 37 | 4.425811e-01 | 4.425810e-01 | 0.0000% | 1.355442e-03 | 1.355541e-03 | -0.0073% |
| Uniform-16 | 16 | 49 | 4.425820e-01 | 4.425810e-01 | 0.0002% | 1.355442e-03 | 1.355541e-03 | -0.0073% |
| Uniform-24 | 24 | 73 | 4.425823e-01 | 4.425810e-01 | 0.0003% | 1.355443e-03 | 1.355541e-03 | -0.0073% |
| Uniform-32 | 32 | 97 | 4.425823e-01 | 4.425810e-01 | 0.0003% | 1.355443e-03 | 1.355541e-03 | -0.0073% |

## Case B - degraded NREL tower

This case introduces localized stiffness degradation. The low-order piecewise discretizations show a less regular convergence pattern, highlighting the need for finer sectional sampling when the stiffness field varies sharply along the tower.

The degraded configuration shows that convergence cannot be assumed from coarse beam discretizations, even when the same formulation and integration strategy are used.

The strongest visual evidence for this case is provided by the convergence plots:

![Degraded NREL tower - tip displacement convergence](openseeslab_output_NREL-5-MW-degr/plot_tip_displacement_convergence.png)

![Degraded NREL tower - tip torsional rotation convergence](openseeslab_output_NREL-5-MW-degr/plot_tip_torsional_rotation_convergence.png)

| Model | Elements | Section evaluations | Uy OpenSees | Uy reference | Uy rel. error | Rz OpenSees | Rz reference | Rz rel. error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Uniform-4 | 4 | 13 | 4.515337e-01 | 4.510653e-01 | 0.1039% | 1.384136e-03 | 1.381202e-03 | 0.2124% |
| Uniform-6 | 6 | 19 | 4.517698e-01 | 4.510653e-01 | 0.1562% | 1.383296e-03 | 1.381202e-03 | 0.1516% |
| Uniform-8 | 8 | 25 | 4.502834e-01 | 4.510653e-01 | -0.1733% | 1.378374e-03 | 1.381202e-03 | -0.2048% |
| Uniform-12 | 12 | 37 | 4.514388e-01 | 4.510653e-01 | 0.0828% | 1.382211e-03 | 1.381202e-03 | 0.0730% |
| Uniform-16 | 16 | 49 | 4.510459e-01 | 4.510653e-01 | -0.0043% | 1.381071e-03 | 1.381202e-03 | -0.0095% |
| Uniform-24 | 24 | 73 | 4.510696e-01 | 4.510653e-01 | 0.0010% | 1.381111e-03 | 1.381202e-03 | -0.0066% |
| Uniform-32 | 32 | 97 | 4.510665e-01 | 4.510653e-01 | 0.0003% | 1.381101e-03 | 1.381202e-03 | -0.0073% |

## Observations

The undegraded configuration converges rapidly even with a limited number of beam elements.

The degraded configuration requires finer discretization to recover stable convergence, confirming the sensitivity of piecewise beam models to localized sectional degradation.

The convergence plots are the most effective material for the paper, because they show the conceptual difference between a smooth sectional field and a degraded sectional field more clearly than the numerical table alone.

## Input files

- Analytical reference: `analytical_reference.txt`.
- OpenSees tip response: `openseeslab_tip_response.csv`.
