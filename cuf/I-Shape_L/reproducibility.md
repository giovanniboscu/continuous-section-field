# Chapter III - Reproducing the Tapered I-Section Study
## From physical inputs to numerical results and figures

A reproducible numerical study requires more than an image of its result. The geometry, material law, applied load, discretization, solution files and evaluation method must be specified well enough for an independent reader to repeat the calculation. This chapter provides the complete command-line sequence for the H20 and CSF-CUF models.

### Working vocabulary

| Term | Meaning |
|---|---|
| **Model YAML** | The text file describing the section geometry and elastic properties. |
| **Problem YAML** | The text file defining the supports and applied load for CUF. |
| **Case YAML** | The text file choosing the CUF expansion, longitudinal discretization and solver settings. |
| **NPZ** | A compressed NumPy archive containing solved fields or recovered numerical samples. |
| **Driver** | A Python program that builds, solves or evaluates a specific numerical model. |
| **Post-processing** | Recovering and plotting displacements, strains, stresses or equilibrium measures from saved results. |
| **Common-point comparison** | Evaluating the two numerical solutions at precisely the same physical coordinates. |

The commands below use **Linux or another system with a bash-compatible shell**. They are executed from `continuous-section-field/cuf/I-Shape_L` unless otherwise indicated. A complete run of the structural solvers can be expensive. The supplied solved checkpoints permit the comparison and plotting stages to be executed independently.

## 1. Prepare the environment

From a clone of the project, activate a suitable Python environment and install the project and numerical dependencies:

```bash
cd continuous-section-field
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
python3 -m pip install numpy scipy pyyaml matplotlib
export MPLBACKEND=Agg
cd cuf/I-Shape_L
```

The source includes the `csf-cuf` command and the CSF Python modules. The three-dimensional reference documented here uses the SciPy backend. OpenSeesPy is optional and is not needed to reproduce the reported numerical values.

Check that the main entry points are available:

```bash
csf-cuf --help
python3 fem3d/run_bending_fem3d_h20.py --self-test
python3 compare_fem3d_h20_cuf_equilibrium.py --version
python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 --help
```

The equilibrium comparator should identify its version as **`H20-CUF same-point comparison v3 (section-bin regression fix)`**. The plotting module is the H20-capable `plot_strain_stress_boundary_v10` source installed under `src/csf/cuf/tools/`.

## 2. Understand the input files

The reference model is described by a small set of readable text files.

| File | Role |
|---|---|
| [`models/carrera_i_shaped_taper80.yaml`](models/carrera_i_shaped_taper80.yaml) | Physical section with three material regions; input to the H20 mesh driver. |
| [`models/carrera_i_shaped_taper80_l9_web3.yaml`](models/carrera_i_shaped_taper80_l9_web3.yaml) | Equivalent section divided into nine quadrilateral CUF domains. |
| [`problems/taper_table9_l9_web3.yaml`](problems/taper_table9_l9_web3.yaml) | Applied half-wave traction on the three lower CUF edges. |
| [`cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml`](cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml) | L9 transverse functions, ten longitudinal elements, integration and solver settings. |

The H20 solver creates its own quadratic solid discretization from the three-region physical model. The CUF solver uses the nine-domain model. Both operate on the same beam geometry, with the same support conditions and loading law.

The source modules required for the H20 run are placed together in `fem3d/`: `run_h20_convergence.py`, `run_bending_fem3d_h20.py`, `run_bending_fem3d_v2.py`, `h20_scipy_solver.py` and `h20_strong_residual.py`. They must remain in that directory because the driver imports its sibling modules. The model and case YAML files remain in their existing subdirectories.

## 3. Produce the CSF-CUF solution

The case file selects the nine L9 domains and ten longitudinal finite elements, each using polynomial order six.

To solve the case, run from `cuf/I-Shape_L`:

```bash
csf-cuf cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml
```

The solver produces five equilibration checkpoints, from `eq1` to `eq5`, using the same numerical discretization.

The equilibration procedure and the meaning of the `solver.equilibration.iterations` parameter are described in [CSF-CUF Solver Equilibration Iterations](../docs/CSF_CUF_solver_equilibration_iterations.md).

### 3.1 Verify the stability of the CSF-CUF solution

The stability of the saved solution with respect to the solver-equilibration iterations is evaluated using the [CUF checkpoint stability verification script](verify_cuf_eq_stability.py).

Run:

```bash
python3 verify_cuf_eq_stability.py
```

The script compares `eq1` with each subsequent checkpoint (`eq2`–`eq5`) and also compares consecutive checkpoints.

The verification includes:

- Displacement components \(u_x\), \(u_y\), and \(u_z\) at the sampled physical points.
- Available displacement coefficients stored in the `.cuf.npz` checkpoints.
- Maximum absolute differences and RMS differences between solutions.
- Numerical stability assessment using specified absolute and relative tolerances.

The generated reports are available in the [CSF-CUF checkpoint stability diagnostics](diagnostics/cuf_eq_stability/):

- [Stability verification report](diagnostics/cuf_eq_stability/summary.md)
- [Detailed numerical results](diagnostics/cuf_eq_stability/summary.csv)

These results document the variation of the numerical solution as the solver-equilibration iterations increase.

### 3.2 Reference checkpoint

The reference used for the subsequent FEM3D H20 versus CSF-CUF comparisons is `eq1`:

```text
output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/
  carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz
```

This checkpoint stores the data needed to reconstruct the CUF displacement field at physical points. It can be reused for all subsequent comparisons and plots without executing the structural solver again.


## 4. Produce the FEM3D H20 reference solution

The FEM3D reference discretization is selected through the displacement convergence study documented in [Chapter II — H20 Mesh Convergence](FEM3Dmesh-convergence-criterion.md).

The study identifies **T4** as the reference mesh, based on the 0.1% convergence criterion for the minimum vertical displacement. This selection concerns displacement convergence and does not imply convergence of all reconstructed stresses or local equilibrium residuals.

### 4.1 Run the selected H20 solution

The selected T4 discretization uses 3,072 H20 elements and 16,081 nodes, with the following subdivision parameters:

| Parameter | Value |
|---|---:|
| `nx` | 48 |
| `ny-left` | 2 |
| `ny-web` | 4 |
| `ny-right` | 2 |
| `nz-flange` | 2 |
| `nz-web` | 8 |

From `cuf/I-Shape_L`, execute:

```bash
python3 fem3d/run_bending_fem3d_h20.py \
  models/carrera_i_shaped_taper80.yaml \
  fem3d/output/h20_convergence/T4_h20.npz \
  --backend scipy \
  --nx 48 \
  --ny-left 2 \
  --ny-web 4 \
  --ny-right 2 \
  --nz-flange 2 \
  --nz-web 8 \
  --amplitude -1.0
```

The command constructs the selected H20 mesh, assembles and solves the three-dimensional linear-elastic problem, and saves the resulting displacement field.

The reference checkpoint is:

```text
fem3d/output/h20_convergence/T4_h20.npz
```

In the supplied reference solution, the minimum vertical displacement is **-1.71702156 mm**, and the total nodal load in the global z direction is approximately **-42,050.505066 N**.

This checkpoint is used in the subsequent displacement and equilibrium comparisons with the CSF-CUF `eq1` solution.

### 4.2 Relationship with the mesh-convergence study

The command above solves only the selected T4 reference mesh. It does not repeat the mesh-convergence study.

To reproduce the complete refinement sequence, including the displacement convergence criterion and the strong-form residual diagnostics, follow the execution procedure in [Chapter II — H20 Mesh Convergence](FEM3Dmesh-convergence-criterion.md), Section 6.

The complete convergence study produces the sequence of solved H20 checkpoints and associated diagnostic results. The single-mesh command above is sufficient when only the selected T4 solution is required for the subsequent FEM3D–CUF comparisons.

The H20 implementation and additional solver options are described in [Appendix A — The H20 Three-Dimensional Reference Model](fem3d/README_H20.md).

## 5. Draw the convergence curves

The following operation uses the saved solutions and residual JSON files. It does **not** rerun the finite-element system:

```bash
python3 fem3d/plot_h20_convergence.py
```

Three PNG files are written to:

```text
fem3d/output/h20_convergence/figures/
  min_uz_vs_mesh.png
  relative_change_vs_mesh.png
  interior_residual_vs_mesh.png
```

The first chart tracks minimum vertical displacement, the second shows its relative change, and the third shows the one-point-per-element interior equilibrium diagnostic.

## 6. Compare interior equilibrium at identical physical points

Once the two reference checkpoints exist, the common-point comparator evaluates H20 and CUF on the same integration points inside each H20 element. The command below reproduces the reported full T4 comparison:

```bash
PYTHONPATH=../../src python3 compare_fem3d_h20_cuf_equilibrium.py \
  --fem fem3d/output/h20_convergence/T4_h20.npz \
  --cuf output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \
  --csf models/carrera_i_shaped_taper80_l9_web3.yaml \
  --max-elements 0 \
  --gauss 2 \
  --sections 40 \
  --output-dir diagnostics/h20_vs_cuf_T4_v3
```

`--max-elements 0` means that **all** H20 elements are examined. `--gauss 2` means that two interior sample positions are used in each local coordinate direction, or **eight points per element**. Thus 3,072 elements generate **24,576 common physical points**. `--sections 40` groups their results into 40 longitudinal intervals without changing the underlying sample positions.

The output includes `summary.json`, `summary.md`, `h20_cuf_common_points.csv`, `h20_cuf_sections.csv`, and PNG graphs of the three equilibrium equations and their combined norm. The CSV files are generated on demand and do not need to be distributed with a compact source package.

For a quick preliminary calculation one may choose a positive `--max-elements` value. That is a **subsample**, not the full-volume reference used in this book. The equations and numerical interpretation are developed in [the equilibrium chapter](FEM3D-H20-CUF-equilibrium.md), Part I.

## 7. Compare external and interface tractions

A second program checks the force transmitted through the lower loaded surface, the free external surfaces, and the physical web-flange interfaces:

```bash
PYTHONPATH=../../src python3 compare_fem3d_h20_cuf_surface_equilibrium.py \
  --fem fem3d/output/h20_convergence/T4_h20.npz \
  --cuf output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \
  --csf models/carrera_i_shaped_taper80_l9_web3.yaml \
  --load-amplitude -1.0 \
  --face-gauss 2 \
  --domain-nx 40 \
  --sections 40 \
  --max-faces 0 \
  --output-dir diagnostics/h20_vs_cuf_T4_surfaces
```

Here `--face-gauss 2` evaluates each quadratic face at four Gaussian sample positions. The script includes the inclined physical face area in the integration and checks the loaded-surface resultant against the nodal force array.

To verify the generated numerical tables independently:

```bash
python3 verify_h20_cuf_surface_outputs.py \
  diagnostics/h20_vs_cuf_T4_surfaces
```

The verifier recomputes weighted surface statistics from the generated CSV files and checks the load integral. The expected successful completion is `ALL TESTS PASS`. Surface forces and physical material interfaces are explained in [the equilibrium chapter](FEM3D-H20-CUF-equilibrium.md), Part II.

## 8. Generate longitudinal, cross-sectional and perimeter plots

The plotting module reconstructs displacement, strain and stress from the saved CUF checkpoint. When supplied with the H20 checkpoint, it also overlays the FEM result on longitudinal curves and polygon-perimeter curves. Cross-sectional color maps show the CUF fields.

The provided launcher uses the H20-capable module name `csf.cuf.tools.plot_strain_stress_boundary_v10`:

```bash
bash generate_all_plots_H20_CUF.sh
```

By default it generates longitudinal plots and transverse/perimeter plots at **$x=250$, $500$ and $750$ mm** under `plot_results/all_H20_CUF/`. To restrict the stations or set a different output directory, use environment variables:

```bash
STATIONS='500' OUT='plot_results/H20_selected' \
  bash generate_all_plots_H20_CUF.sh
```

The program writes PNG figures and, by default, the corresponding numerical CSV files. Each figure CSV has the same base name as its PNG under a sibling `figure_csv/` directory. Some sampled fields are also saved in NPZ form. [The plotting chapter](plot_results/README.md) explains how to read these outputs and how to identify a physical point on a closed sectional perimeter.

Before any figure is created, the launcher checks that the FEM checkpoint contains 20-node elements and the displacement and material arrays needed for H20 reconstruction. It records the validated element and node counts in the run log.

The plotting launcher requires the H20 plotting module to be installed at its stated Python import path. An unavailable plotting module is an explicit error; the script does not silently substitute another reader.

## 9. Check reference-file identity

The source comparison records SHA-256 checksums for its inputs. These identify the precise checkpoints behind the results in the book. On the supplied saved dataset, the command

```bash
sha256sum \
  fem3d/output/h20_convergence/T4_h20.npz \
  output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \
  models/carrera_i_shaped_taper80_l9_web3.yaml
```

produces the following recorded hashes, in the same order:

```text
525444c97c7614ded0263c7475372f3c7a564127e1418912b424bb4e421251c1
67b2b69b6522e52d37dc1dbb505b6381e69f435a24d22fae5e7b54971a438705
66ef4fc835f426a645f949f41d28e2225dd0a2556b9b84a1446f954ca0a300b5
```

A fresh solve may produce different binary hashes because of software versions and numerical representation. For an independently regenerated run, compare the **physical and numerical results**, not only the file hashes.

## 10. Order of execution and expected outputs

| Stage | Command or program | Main output |
|---|---|---|
| Physical input | Read model, problem and case YAML | Defined geometry, materials, supports and load |
| CUF solve | `csf-cuf ...yaml` | `eq1.cuf.npz` checkpoint |
| H20 solve and refinement | `fem3d/run_h20_convergence.py` | `T4_h20.npz`, convergence table and JSON diagnostics |
| Convergence figures | `fem3d/plot_h20_convergence.py` | Three PNG plots |
| Common-point equilibrium | `compare_fem3d_h20_cuf_equilibrium.py` | Interior equilibrium tables and PNG plots |
| Physical-surface equilibrium | `compare_fem3d_h20_cuf_surface_equilibrium.py` | Surface statistics, sampled data and PNG plots |
| Independent surface verification | `verify_h20_cuf_surface_outputs.py` | Pass/fail confirmation |
| Displacement/strain/stress plots | `generate_all_plots_H20_CUF.sh` | Longitudinal, sectional and perimeter PNG plots |

Each step reads the results of preceding steps through documented files rather than through an interactive plotting session. That separation allows the numerical solve, the equilibrium diagnostics, and the graphical presentation to be repeated independently.
