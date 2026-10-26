# MITC B2 shear-locking convergence suite

This extends the previous single-element B2 test to **1, 2, 4 and 8 longitudinal B2 elements**, each tested **MITC OFF and ON** (8 solver runs). It is designed to expose shear locking and assess convergence without changing CSF-CUF software sources.

## Installation

Extract the ZIP **into the existing `cuf/c-shape/` folder**, merging the `cases/`, `models/`, `problems/`, and `mitc_tests/` directories. No existing v01 case or output name is overwritten. The package assumes the existing `expansions/lagrangeL9_v4.py` and installed `csf-cuf` command, plus the existing `csf.cuf.adapters.problem.c_section_cantilever_point_load` and `csf.cuf.adapters.output.post` adapters.

## Run (from `cuf/c-shape/`)

```bash
bash mitc_tests/run_all_B2.sh
```

This saves per-run logs under `mitc_tests/logs/` and runs the result comparison automatically when all eight cases complete. To run selected cases manually:

```bash
csf-cuf cases/mitc_locking_rect_B2_N02_off.yaml
csf-cuf cases/mitc_locking_rect_B2_N02_on.yaml
csf-cuf cases/mitc_locking_rect_B2_N04_off.yaml
csf-cuf cases/mitc_locking_rect_B2_N04_on.yaml
csf-cuf cases/mitc_locking_rect_B2_N08_off.yaml
csf-cuf cases/mitc_locking_rect_B2_N08_on.yaml
```

To create the comparison after manual runs:

```bash
python3 mitc_tests/compare_results.py
```

Reports are written to `mitc_tests/reports/mitc_B2_convergence.txt` and `.csv`. The comparison reads `response.txt` from each `output/mitc_locking_rect_B2_Nxx_off|on` directory, at the tracked tip centroid `(x,y,z)=(5000,0,0)` mm.

## Parameter control

| Parameter | All eight cases |
|---|---|
| CSF geometry | One 100 x 100 mm rectangular polygon, prismatic |
| Beam length | 5000 mm, L/h=50 |
| Material | E=75000 MPa, nu=0.33 |
| Constraint | Full clamp at x=0 by existing cantilever adapter |
| Applied force | Point load Fz=-100 N at (5000,0,0) mm |
| CUF transverse basis | existing `lagrangeL9_v4.py`, `cuf.order: 2` |
| FE basis | `lagrange`, longitudinal order 1 (B2) |
| FE partitions | 1, 2, 4, 8 equal-length elements |
| Longitudinal Gauss | 15 per element |
| Section Gauss | 9 |
| Equilibration | 5 |
| Sampling | stations [0, 0.5, 1], 201 displacement samples |

Within each OFF/ON pair, only `correctionMITC` changes the assembled stiffness. `verifyMITCAssembly` follows the ON setting as a **diagnostic only**, and does not modify the solution. `correctionMITC: false` is the ordinary CUF case; `true` is MITC.

The package intentionally does not introduce `require_prismatic` or other geometry/basis restrictions: only the test geometry is prismatic.

## Reference and expected behavior

- `I_y = b h^3 / 12 = 8,333,333.333 mm^4`.
- Euler-Bernoulli tip deflection: `u_z(L) = Fz L^3 / (3 E I_y) = -6.666666667 mm`.
- This is a slender-beam bending reference, **not an exact three-dimensional elasticity reference**. The same L9 transverse model and the concentrated-load approximation can contribute residual errors.
- Without MITC, coarse B2 elements should suffer from excessive apparent shear stiffness and markedly underpredict the tip displacement.
- With MITC, tip displacement should be much larger in magnitude for a coarse mesh and should approach the reference as the mesh is refined; **monotonic convergence or a numerical pass threshold is not imposed**.

Previous archive `mitc_locking_rect.tar` yielded for 1 B2 element (centroid, tip): **OFF = -0.007087099 mm**, **ON = -4.464409631 mm**. The new N01 pair reproduces the same physical configuration and can be used as a regression baseline. No numerical comparison or solver execution for the new N02/N04/N08 cases has been performed here.

### Interpretation

Plot or tabulate `u_z(L)` versus number of B2 elements, side by side for ON and OFF. Compare the displacement difference to the Euler-Bernoulli reference. A meaningful MITC demonstration is a markedly better coarse-mesh solution and faster convergence. The assembly verification `PASS` checks internal numeric consistency for the sampled CUF pair, **not** independent correctness of the MITC theory or an entire stiffness matrix.
