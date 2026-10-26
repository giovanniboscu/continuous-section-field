# Archived MITC B2 verification audit

This audit examines archived files; it does not rerun the solver.

## Recomputed displacements and reference errors

| B2 | OFF [mm] | ON [mm] | OFF error to EB [%] | ON error to EB [%] |
|---:|---:|---:|---:|---:|
| 1 | -0.007087099 | -4.464409631 | 99.89369 | 33.03386 |
| 2 | -0.028239232 | -5.323041675 | 99.57641 | 20.15437 |
| 4 | -0.111444450 | -6.047428883 | 98.32833 | 9.28857 |
| 8 | -0.423803876 | -6.369662827 | 93.64294 | 4.45506 |

## Difference-based refinement indicator

For equal mesh halving, p_delta=log2(abs((u_h-u_h/2)/(u_h/2-u_h/4))). This is an indicator, not a guaranteed asymptotic convergence order.

| Mode | delta(1 to 2) [mm] | delta(2 to 4) [mm] | delta(4 to 8) [mm] | p_delta(1,2,4) | p_delta(2,4,8) |
|---|---:|---:|---:|---:|---:|
| OFF | -0.02115213 | -0.08320522 | -0.31235943 | -1.9759 | -1.9085 |
| ON | -0.85863204 | -0.72438721 | -0.32223394 | 0.2453 | 1.1687 |

MITC ON increments decrease with refinement; MITC OFF increments increase on these meshes. Neither is sufficient to establish the asymptotic order or the exact continuum limit.

## Archived solver diagnostics

| B2 | Mode | symmetry relative | KKT relative residual (inf) | verified MITC elements |
|---:|---|---:|---:|---:|
| 1 | OFF | 1.3561e-16 | 2.3730e-22 | 0 |
| 1 | ON | 1.3207e-16 | 1.8656e-21 | 1 |
| 2 | OFF | 1.4748e-16 | 2.3707e-22 | 0 |
| 2 | ON | 1.4509e-16 | 1.0527e-21 | 2 |
| 4 | OFF | 1.5346e-16 | 9.4588e-22 | 0 |
| 4 | ON | 1.4796e-16 | 3.8029e-21 | 4 |
| 8 | OFF | 1.4198e-16 | 9.4210e-21 | 0 |
| 8 | ON | 1.4222e-16 | 8.1951e-21 | 8 |

All eight logs report solve completion and global symmetry under the configured tolerance of 1e-10. The MITC diagnostics sample only pair (1,1), one entry per longitudinal element, and are internal comparisons rather than independent validation.

## Consistency checks

- Eight case names/output paths and tip-center response coordinates: PASS.
- Each B2 partition is uniform over [0,1]; order=1: PASS.
- Within each OFF/ON pair, physical problem, CUF basis, element mesh, integration and sampling settings are identical: PASS.
- Solver settings differ only in correctionMITC and verifyMITCAssembly: PASS.
- OFF/ON diagnostic flags and logged checks match: PASS.
- No numerical displacement PASS threshold was introduced.

## Not established

- Reaction balance, energy partition, complete pairwise MITC block validation, spurious modes, and independent 3D convergence require additional solver data or executions.
- Comparing with Euler-Bernoulli is a reference check, not a proof of convergence to the exact CUF/3D solution.
