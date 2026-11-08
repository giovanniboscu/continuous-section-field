# Appendix A - The H20 Three-Dimensional Reference Model
## Geometry, interpolation, solution and verification

The H20 model is an independent three-dimensional elastic solution of the tapered I-shaped member. Its purpose is to provide a detailed solid reference with which the CSF-CUF displacement and reconstructed stresses can be compared at common physical points.

### Terms

| Term | Meaning |
|---|---|
| **H20 brick** | A solid element with twenty displacement nodes: eight corners and twelve edge midpoints. |
| **Shape function** | A function that interpolates a field value within a finite element using its nodal values. |
| **Isoparametric mapping** | The representation of the element's physical shape using the same interpolation framework as its displacement field. |
| **Gaussian integration** | A numerical rule for evaluating integrals at selected points with associated weights. |
| **Sparse solver** | A method for solving the linear system while storing mainly its nonzero coefficients. |
| **Patch test** | A controlled calculation with a known answer, used to check an element or numerical operation. |

## 1. Input and mesh construction

The physical three-region YAML is [`../models/carrera_i_shaped_taper80.yaml`](../models/carrera_i_shaped_taper80.yaml). It defines the two end sections, the constant flange modulus, the linearly varying web modulus and the isotropic material law.

[`run_bending_fem3d_h20.py`](run_bending_fem3d_h20.py) uses the shared geometric mesh helper in [`run_bending_fem3d_v2.py`](run_bending_fem3d_v2.py) to establish a conforming three-region topology. It upgrades every solid cell by adding shared edge-midpoint nodes, producing twenty-node elements with consistent connectivity across the mesh.

The quadratic shape functions describe both geometry and displacement within the element. The implementation checks the physical Jacobian for positive values at sampled internal points, rejecting invalid element geometry.

## 2. Loading and material assignment

The bottom surface is represented by quadratic faces with eight nodes. The code integrates the prescribed global-$z$ half-wave traction using Gaussian quadrature on the true, inclined physical face and assembles the equivalent nodal loads.

Material properties are read from the same CSF physical model. In the saved solid mesh, the web modulus for each element is evaluated at its longitudinal midpoint. The flanges keep constant modulus. All regions use Poisson ratio $\nu=0.3$.

The loading is expressed in **N and mm**, with traction amplitude **-1 MPa**. The integrated global-$z$ force is approximately **-42,050.505066 N** and is independent of the chosen mesh level.

## 3. The displacement solution

The standard reported backend is implemented in [`h20_scipy_solver.py`](h20_scipy_solver.py). It assembles the linear-elastic stiffness using **3 x 3 x 3 Gaussian integration** and solves the sparse equilibrium system with SciPy.

The end supports prevent displacement in global $y$ and $z$. An axial reference removes rigid translation in global $x$. The code saves the resulting displacement field in an NPZ checkpoint together with the mesh, material arrays, nodal loads, support metadata and numerical solver identification.

The optional OpenSeesPy backend uses `20NodeBrick`. The source contains [`verify_h20_backends.py`](verify_h20_backends.py) to compare a small model with the SciPy result. The published numerical series in this study uses **SciPy**, so a successful OpenSeesPy installation is not required for its reproduction.

## 4. Verification built into the implementation

The following checks test different stages of the finite-element computation:

1. The quadratic solid and face shape functions satisfy partition-of-unity and interpolation identities.
2. The isoparametric geometry has a positive Jacobian at the selected test points.
3. The integrated nodal surface force matches the known half-wave resultant in a simple test.
4. A manufactured displacement $u_z=x^2$ reproduces the expected interior equilibrium term $r_z=2G$ for constant isotropic modulus.
5. The mesh convergence driver records the nodal load sum, solved displacement extrema and independent strong-form residuals for every level.

Run the element tests from the scenario root:

```bash
python3 fem3d/run_bending_fem3d_h20.py --self-test
```

## 5. Running one H20 mesh

The following example produces a solved T4 checkpoint without running the full convergence sequence:

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

To create a mesh checkpoint without solving the displacement system, add `--mesh-only`. That option is useful for checking geometry and element counts, but it does not produce a solved reference field.

For the complete six-level sequence, use [`run_h20_convergence.py`](run_h20_convergence.py), following [the convergence chapter](../FEM3Dmesh-convergence-criterion.md).

## 6. Recovering local equilibrium

[`h20_strong_residual.py`](h20_strong_residual.py) reads a saved solved checkpoint and reconstructs the local stress-divergence vector. Stress is obtained from the H20 displacement derivatives, transformed from the local element coordinates to physical coordinates, and combined with the stored elastic properties.

A sample command is:

```bash
python3 fem3d/h20_strong_residual.py \
  fem3d/output/h20_convergence/T4_h20.npz \
  --max-elements 0 \
  --gauss 2 \
  --output fem3d/output/h20_convergence/T4_gauss2.json
```

This command performs numerical differentiation and residual integration on an existing solution. The distinction between this diagnostic and the solved equilibrium equations is developed in [the interior equilibrium chapter](../FEM3D-H20-CUF-equilibrium.md).

## 7. Outputs and further reading

| Output | Meaning |
|---|---|
| `T4_h20.npz` | Saved T4 element coordinates, connectivity, materials, displacements and loads. |
| `T4.log` | Text log of the T4 driver execution. |
| `T4_strong_residual.json` | One-point-per-element interior equilibrium statistics from the convergence series. |
| `convergence.md` | The compact table automatically produced by the convergence runner. |
| `figures/*.png` | Figures generated from stored convergence checkpoints and residual summaries. |

For the full scientific context return to [the main study](../README.md). For the exact command order use [Reproducibility](../reproducibility.md).
