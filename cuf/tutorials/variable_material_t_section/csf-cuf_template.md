## Building the T-section example step by step

The example is organized in three directories:

```text
.
├── models
│   ├── t_noprismatic_csf.yaml
│   └── action.yaml
├── problems
│   ├── bending_halfwave.yaml
│   └── torsion_halfwave.yaml
└── cases
    ├── bending_halfwave_legendre_N08.yaml
    └── torsion_halfwave_legendre_N08.yaml
```

The files are separated according to their role in the analysis.

### Step 1 - Build and inspect the physical model

The physical model is defined in:

```text
models/t_noprismatic_csf.yaml
```

This is the CSF description of the structure.

It contains the information needed to define the physical beam before any CUF analysis is introduced:

* the beam length;
* the T-shaped cross-section;
* the variation of the section along the beam;
* the material definition;
* the spatial variation of the material properties.

The second file in the same directory is:

```text
models/action.yaml
```

This file will be used with the CSF tools to inspect the model defined in `t_noprismatic_csf.yaml`.

To run the inspection, move into the `models` directory and execute:

```bash
csf-actions t_noprismatic_csf.yaml action.yaml
```

Before proceeding to the structural analysis, we will use these tools to check the model directly. In particular, we will verify the geometry of the T section, its variation along the beam, and the associated material field.

This is an important step because the CUF solver will subsequently use this CSF model as its physical description of the structure.

<img width="1289" height="484" alt="immagine" src="https://github.com/user-attachments/assets/69cfbfc3-9dee-44de-a18a-1421f67865c6" />

*Figure - 1 cross-sections of the non-prismatic T-shaped model at `z = 0` and `z = 1000`. The section is composed of two physical polygons: the upper flange (`top_flange`, ID=0) and the web (`web`, ID=1). The change in their dimensions between the two locations shows the non-prismatic variation of the geometry along the beam. The vertex and edge identifiers shown in the plots will later be used to identify the physical surface on which the CUF load is applied.*

<img width="1294" height="476" alt="immagine" src="https://github.com/user-attachments/assets/483c2407-c174-463e-8833-3fdac0a32561" />

Figure - 2 Three-dimensional view of the non-prismatic T-shaped CSF model and its material fields. The section geometry varies along the longitudinal coordinate `Z`. In this example, the CSF `weight` field shown on the left represents the elastic modulus \(E\), while the `shear weight` field shown on the right represents the shear modulus \(G\). The color variation shows how the material stiffness changes along the member and provides a direct visual check of the material distribution defined in the CSF model.*****

<img width="1000" height="480" alt="immagine" src="https://github.com/user-attachments/assets/27c3d474-3ef1-49bf-bc82-66f437e9577c" />


*Figure 3 - Longitudinal distribution of the CSF `weight` field for the two polygons of the T section. In this example, `weight` represents the elastic modulus \(E\). The `top_flange` keeps a constant value of `71700` along the full beam length, while the `web` varies linearly from `71700` at `z = 0` to `57360` at `z = 1000`. The plot confirms that the prescribed elastic-modulus variation is applied only to the web, while the flange remains homogeneous.*

<img width="994" height="879" alt="immagine" src="https://github.com/user-attachments/assets/a2610114-38a6-4d9a-9c5a-7a4ff4b150b0" />

*Figure 4 - Variation of the main geometric properties of the non-prismatic T section along the longitudinal coordinate `Z`. The plots show the cross-sectional area \(A\), the second moments of area \(I_x\) and \(I_y\), and the polar second moment of area \(I_p\). All four quantities decrease from `z = 0` to `z = 1000` as a consequence of the progressive reduction of the T-section dimensions. This provides a direct check that the non-prismatic geometry defined in the CSF model is reflected consistently in the section properties used by the structural analysis.*


### Step 2 - Define the CUF case

Once the physical CSF model has been inspected and verified, we can define the CUF analysis.

For the bending example, the case file is:

```text
cases/bending_halfwave_legendre_N08.yaml
```

This is the main input file passed to the CUF solver. It does not redefine the geometry or the material model. Instead, it connects the structural problem already defined on the CSF model with the numerical choices used by the CUF formulation.

```yaml
# CSF-CUF bending half-wave v2 test: scaled_legendre, N=08.
case:
  name: double_t_bending_halfwave_legendre_N08

problem:
  yaml: ../problems/bending_halfwave.yaml
  adapter: csf.cuf.adapters.problem.surface_halfwave

cuf:
  basis: scaled_legendre
  order: 8

longitudinal:
  method: finite_element
  elements: 1
  order: 6

section_integration:
  method: fixed_gauss_polygon
  gauss_order: 6

sampling:
  stations: [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30,
             0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65,
             0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]
  displacement_samples: 201
  stress_grid: 31

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/bending_halfwave_legendre_N08
```

The file can be read from top to bottom as a description of how the analysis is assembled.

#### Case name

```yaml
case:
  name: double_t_bending_halfwave_legendre_N08
```

The `case` block gives the analysis a unique name. It is useful for distinguishing this run from other analyses that may use a different problem, CUF expansion, expansion order, or output directory.

#### Structural problem

```yaml
problem:
  yaml: ../problems/bending_halfwave.yaml
  adapter: csf.cuf.adapters.problem.surface_halfwave
```

The CUF case does not define the load directly.

Instead, it points to a separate problem file:

```text
problems/bending_halfwave.yaml
```

The `adapter` tells the solver how that problem file must be interpreted. Here the already implemented `surface_halfwave` adapter is used. It describes a distributed load acting on a physical surface of the CSF model, with a half-wave variation along the longitudinal direction.

We will inspect `bending_halfwave.yaml` in the next step. At that point we will identify the loaded surface directly on the CSF geometry and explain the load amplitude and direction.

#### CUF transverse expansion

```yaml
cuf:
  basis: scaled_legendre
  order: 8
```

This block defines the CUF approximation over the cross-section.

`basis: scaled_legendre` selects the already implemented scaled Legendre transverse expansion, while

```yaml
order: 8
```

sets its transverse order to \(N=8\).

This order belongs to the CUF expansion over the section. It must not be confused with the longitudinal polynomial order defined later in the file.

The CSF model continues to provide the actual section geometry and material distribution; the CUF basis provides the mathematical functions used to represent the displacement field over that physical section.

#### Longitudinal representation

```yaml
longitudinal:
  method: finite_element
  elements: 1
  order: 6
```

The CUF expansion describes the variation of the solution over the cross-section. A separate approximation is required along the longitudinal coordinate.

In this example, the longitudinal domain is represented by one interval:

```yaml
elements: 1
```

and the polynomial order used for the longitudinal approximation is:

```yaml
order: 6
```

Thus, `longitudinal.order` controls the polynomial approximation along the beam axis, whereas `cuf.order` controls the transverse CUF expansion over the cross-section. They are independent parameters.

It is also important not to confuse `longitudinal.order` with the order of numerical integration.

The longitudinal integrals are evaluated with Gauss-Legendre quadrature. Since no explicit `longitudinal.gauss_order` is given in this case, the solver first generates a requested quadrature order automatically. It then estimates the minimum quadrature required by the complete longitudinal integrand, taking into account the longitudinal polynomial approximation, the variation of the CUF basis caused by the changing section geometry, the cross-sectional measure, and the material variation.

The effective longitudinal Gauss order is therefore allowed to increase when the estimated minimum is higher than the initially requested value.

For material laws that are constant or affine along the beam, the material contribution is detected automatically. If a custom non-affine polynomial variation of the material is introduced, its maximum polynomial degree can be supplied explicitly through `longitudinal.material_polynomial_degree`.

This affects the longitudinal **integration order**, not `longitudinal.order` itself.

#### Section integration

```yaml
section_integration:
  method: fixed_gauss_polygon
  gauss_order: 6
```

The CUF formulation also requires numerical integration over the physical cross-section.

Here the section is integrated polygon by polygon on the CSF geometry using Gaussian quadrature.

`gauss_order: 6` is the requested section quadrature order. The selected CUF basis can declare a higher minimum requirement; when this happens, the solver automatically uses the larger value.

The value written in the case should therefore be understood as the requested minimum, while the effective section quadrature can be higher.

#### Sampling

```yaml
sampling:
  stations: [0.00, 0.05, ..., 0.95, 1.00]
  displacement_samples: 201
  stress_grid: 31
```

These parameters control how the solved field is inspected during post-processing.

The `stations` values are normalized longitudinal positions:

- `0.00` is the beginning of the beam;
- `0.50` is the mid-span section;
- `1.00` is the end of the beam.

The intermediate values define the additional sections at which results are evaluated.

`displacement_samples` controls the sampling used for displacement evaluation, while `stress_grid` controls the grid used for stress evaluation over the section.

These settings do not change the structural solution itself. They control how densely the solved continuous field is queried and reported.

#### Output

```yaml
output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/bending_halfwave_legendre_N08
```

The `output` block selects the standard CUF post-processing adapter and specifies the directory in which the results of this case will be written.

### Output adapter

```yaml
output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/bending_halfwave_legendre_N08
```

The `output` block specifies how the solved CUF field is post-processed.

```yaml
adapter: csf.cuf.adapters.output.post
```

selects the standard CSF-CUF output adapter. The structural solution has already been computed at this stage: the adapter does not modify the model or solve the problem again. Its role is to query the solved physical displacement field and convert the requested results into a readable output.

The results are written in the directory specified by:

```yaml
directory: ../output/bending_halfwave_legendre_N08
```

For this example, the standard adapter produces a `response.txt` file containing the displacement response at the longitudinal stations requested in the `sampling` block.

A shortened extract is:

```text
CSF-CUF RESPONSE
======================
problem.type = surface_halfwave

STATION RESPONSES
-----------------
x/L    x [mm]    y [mm]    z [mm]    point       ux [mm]      uy [mm]      uz [mm]

0.00     0.0       0.0       0.0      center      ...
0.00     0.0     -33.0      75.0      plus        ...
0.00     0.0      12.5     -50.0      minus       ...
0.00     0.0       0.0     -50.0      bottom_mid  ...

0.05    50.0     -32.525    73.875    plus        ...
```

Each row identifies both the longitudinal position and the actual physical point at which the solved field is evaluated.

`x/L` is the normalized longitudinal coordinate, `x` is the corresponding physical coordinate, `y` and `z` locate the point on the current CSF section, and `ux`, `uy`, `uz` are the three displacement components.

The physical coordinates are reported explicitly because the section may change along the member. For example, the point labelled `plus` moves as the T section tapers; the post-processor therefore evaluates the solution on the actual CSF geometry at each requested station rather than assuming a fixed transverse position.

The names such as `center`, `plus`, `minus`, and `bottom_mid` identify the reference points used for this response and make it possible to follow the same physical locations along the member.

Keeping the output procedure in a separate adapter also preserves the modular structure of CSF-CUF: the solver produces the structural solution, while the output adapter determines how that solution is inspected and reported.




---


### Step 3 - Define the structural problems

The CUF case introduced in Step 2 points to a separate file containing the physical definition of the structural problem.

For this example, two problem files are provided:

```text
problems/bending_halfwave.yaml
problems/torsion_halfwave.yaml
```

Both problems use the same T-shaped CSF model defined and inspected in Step 1. They differ in the applied load and in the way that load is associated with the physical CSF geometry.

---

#### Problem 1 - Bending half-wave

**Problem file**

```text
problems/bending_halfwave.yaml
```

```yaml
model:
  csf_yaml: ../models/t_noprismatic_csf.yaml

problem:
  type: surface_halfwave

  surface:
    polygon_name: web
    edge_start_point_id: 0

  amplitude: -10.0
```

##### Physical model

```yaml
model:
  csf_yaml: ../models/t_noprismatic_csf.yaml
```

The problem uses the same non-prismatic T-shaped CSF model already inspected in Step 1. Geometry and material properties are therefore not defined again here.

##### Load definition

```yaml
problem:
  type: surface_halfwave

  surface:
    polygon_name: web
    edge_start_point_id: 0

  amplitude: -10.0
```

`surface_halfwave` selects the already implemented surface half-wave loading law.

The loaded physical surface is identified directly from the CSF geometry through:

```yaml
surface:
  polygon_name: web
  edge_start_point_id: 0
```

In this example, the load acts on the edge of the `web` polygon that starts from vertex `0`. These are the same physical identifiers displayed during the geometry inspection in Step 1.

The prescribed traction acts in the global `z` direction and varies along the beam according to:

```text
amplitude * sin(pi * (x - x0) / L)
```

The sign of `amplitude` defines the direction of the load along global `z`.

##### Current geometric limitation

The selected edge must be horizontal in the transverse section, meaning that its two vertices must have the same global `z` coordinate at both CSF end sections.

The edge may, however, move to a different global `z` level along the beam. The resulting inclined physical surface is accounted for by the load projection.

##### Boundary conditions

The `surface_halfwave` problem also defines the support conditions associated with this predefined structural scheme.

At both longitudinal ends:

- all global `y` displacement amplitudes are constrained;
- all global `z` displacement amplitudes are constrained.

The remaining rigid translation in global `x` is removed by imposing:

```text
u_x(x_start, y=0, z=0) = 0
```

Therefore, this problem definition contains both the bending load and the boundary conditions required for the test.

---

#### Problem 2 - Torsion half-wave

**Problem file**

```text
problems/torsion_halfwave.yaml
```

```yaml
model:
  csf_yaml: ../models/t_noprismatic_csf.yaml

problem:
  type: torsion_halfwave
  amplitude: 10.0
```

##### Physical model

```yaml
model:
  csf_yaml: ../models/t_noprismatic_csf.yaml
```

The torsion problem uses exactly the same CSF geometry and material field as the bending problem.

##### Load definition

```yaml
problem:
  type: torsion_halfwave
  amplitude: 10.0
```

`torsion_halfwave` selects the already implemented torsional half-wave loading law.

The problem applies two opposite loads in the global `z` direction, with longitudinal intensities:

```text
+ amplitude * sin(pi * (x - x0) / L)
- amplitude * sin(pi * (x - x0) / L)
```

The two physical load trajectories are selected automatically from the CSF geometry:

- the positive load follows the leftmost CSF vertex on the maximum-`z` boundary;
- the negative load follows the rightmost CSF vertex on the minimum-`z` boundary.

Their opposite signs generate the torsional action.

Unlike the bending problem, no surface selector is required in the YAML because the two load points are determined automatically by the predefined torsion adapter.

##### Current geometric limitation

The load points must correspond to actual CSF vertices. The adapter follows those physical vertices as the section changes along the beam.

The line-pair load is defined per unit global longitudinal coordinate `x`; no additional trajectory-length factor is introduced.

##### Boundary conditions

The `torsion_halfwave` problem also defines its support conditions.

At both longitudinal ends:

- all global `y` displacement amplitudes are constrained;
- all global `z` displacement amplitudes are constrained.

The remaining rigid translation in global `x` is removed by imposing:

```text
u_x(x_start, y=0, z=0) = 0
```

Therefore, this problem definition contains the torsional load, the automatic load trajectories, and the boundary conditions required for the test.

---

These two problems are examples of the loading schemes already available in the current CSF-CUF implementation. Other predefined load types are also provided, and new problem or loading adapters can be added without modifying the CUF solver core.


### Step 3 - Run the CUF case

Once the physical CSF model, the structural problem, and the CUF case have been defined, the analysis can be launched from the tutorial directory with:

```bash
csf-cuf cases/bending_halfwave_legendre_N08.yaml
```

The solver prints a detailed execution report. This report is useful because it shows not only whether the analysis completed successfully, but also the numerical model that was actually assembled and solved.

The main parts of the output are explained below.

---

#### 1. Analysis identification

The first block summarizes the selected case:

```text
CSF-CUF solver
==============
case                = double_t_bending_halfwave_legendre_N08
problem             = .../problems/bending_halfwave.yaml
CSF model           = .../models/t_noprismatic_csf.yaml
solver public output= u(x,y,z)
CUF order           = 8
longitudinal FE     = 1 x order 6
```

The solver confirms:

- the case that is being executed;
- the structural problem file;
- the CSF physical model;
- the CUF transverse order;
- the selected longitudinal representation.

The line

```text
solver public output= u(x,y,z)
```

is especially important. The final public result of the solver is the continuous physical displacement field:

$$ \mathbf{u}(x,y,z)=\left(u_x(x,y,z),u_y(x,y,z),u_z(x,y,z)\right) $$

The generalized CUF unknowns are therefore an internal representation of the solution. After the algebraic system has been solved, the solver reconstructs the physical displacement field that can be evaluated at points of the CSF member.

---

#### 2. Section quadrature

The first numerical check concerns integration over the cross-section:

```text
[quadrature] section Gauss requested = 6
[quadrature] section Gauss effective = 9
[quadrature] CUF basis minimum     = 9
```

The case file requested:

```yaml
section_integration:
  gauss_order: 6
```

but the active CUF basis requires at least `9` Gauss points for this analysis.

The solver therefore automatically increases the sectional quadrature:

```text
requested = 6
basis minimum = 9
effective = 9
```

The important value is the **effective** order, because this is the order actually used during assembly.

---

#### 3. Longitudinal quadrature

The solver performs a separate check for integration along the beam:

```text
[quadrature] longitudinal degree estimate = 31
[quadrature] longitudinal variation axes  = y,z
[quadrature] longitudinal material varies = true
[quadrature] longitudinal material degree = 1 (automatic)
[quadrature] longitudinal Gauss requested = 15
[quadrature] longitudinal Gauss minimum   = 16
[quadrature] longitudinal Gauss effective = 16
```

The line

```text
longitudinal degree estimate = 31
```

is a conservative estimate of the polynomial complexity that must be integrated along the member. It includes the contributions associated with the longitudinal approximation and with quantities that vary along the beam, including the transverse CUF basis, the section geometry, and the material field.

It is **not** the same quantity as:

```text
CUF order = 8
```

or the longitudinal polynomial order shown earlier.

```text
longitudinal variation axes = y,z
```

indicates that the changing CSF geometry introduces longitudinal variation through both transverse coordinates.

The next two lines:

```text
longitudinal material varies = true
longitudinal material degree = 1 (automatic)
```

show that the solver has detected a varying material field and has automatically identified its longitudinal polynomial contribution as degree `1`.

In this case no explicit longitudinal Gauss order was written in the YAML. The solver generates its baseline quadrature request automatically:

```text
longitudinal Gauss requested = 15
```

It then compares this value with the minimum required by the estimated longitudinal degree:

```text
longitudinal Gauss minimum = 16
```

and finally uses:

```text
longitudinal Gauss effective = 16
```

Again, the **effective** value is the one actually used by the solver.

---

#### 4. CUF basis ready

The first main solver stage ends with:

```text
[1/4] model/basis ready: domains from CSF, M=45
```

`domains from CSF` confirms that the physical cross-sectional domains are obtained directly from the CSF model.

`M=45` is the number of active transverse functions generated by the selected `scaled_legendre` expansion at order \(N=8\).

These functions are indexed by:

```text
tau = 1, ..., 45
```

and are used to represent the displacement field over the physical cross-section.

---

#### 5. CUF matrix assembly

The next stage assembles the global system:

```text
[assembly] element 1/1 started: 2025 CUF pairs
```

With `M=45`, the solver must evaluate all combinations of transverse functions:

$$ 45 \times 45 = 2025 $$

These are the CUF function pairs involved in the stiffness assembly.

The progress lines:

```text
[assembly] element 1/1 tau=1/45 pairs=45/2025 ...
[assembly] element 1/1 tau=10/45 pairs=450/2025 ...
[assembly] element 1/1 tau=20/45 pairs=900/2025 ...
...
[assembly] element 1/1 tau=45/45 pairs=2025/2025 ...
```

show how far the assembly has progressed.

For each line:

- `tau` identifies the current transverse function;
- `pairs` reports how many CUF pairs have been processed;
- `entries` reports how many sparse matrix contributions have been accumulated;
- `elapsed` is the total elapsed assembly time;
- `build_pair` is the time spent computing the CUF pair contributions;
- `scatter` is the time spent inserting those contributions into the global sparse structure.

The completed assembly is summarized by:

```text
[assembly] element 1/1 complete elapsed=16.6s ...
[assembly] triplets complete elapsed=16.6s entries=855883
[assembly] COO->CSR complete elapsed=0.0s nnz=855883
[assembly] loads complete elapsed=0.0s total=16.7s
```

The matrix is first accumulated as sparse triplets and then converted from COO to CSR format for the subsequent numerical operations.

`nnz` means **number of stored non-zero entries**.

The load vector defined by the structural problem is assembled immediately afterward.

---

#### 6. Global degrees of freedom

The next solver milestone is:

```text
[2/4] global assembly complete: DOFs=945
```

The assembled displacement problem contains `945` generalized CUF degrees of freedom.

This number results from combining:

- the longitudinal representation;
- the `45` transverse CUF functions;
- the three displacement components.

These are the unknown displacement quantities before the constraint equations are added to the augmented system.

---

#### 7. Stiffness matrix `K`

The solver then reports diagnostics for the global stiffness matrix:

```text
[matrix-diagnostic] K shape=(945, 945) nnz=855883 ...
```

`K` is the assembled CUF stiffness matrix.

```text
shape=(945, 945)
```

is consistent with the `945` generalized displacement unknowns.

The additional quantities are numerical diagnostics:

- `nnz`: number of stored non-zero entries;
- `abs_nonzero_min`: smallest absolute non-zero coefficient;
- `abs_nonzero_max`: largest absolute non-zero coefficient;
- `frobenius`: Frobenius norm of the matrix;
- `diag_abs_positive_min`: smallest positive absolute diagonal coefficient;
- `diag_abs_max`: largest absolute diagonal coefficient;
- `diag_zeros`: number of exactly zero diagonal terms.

The following line:

```text
[matrix-diagnostic] K norms row_l2_min_median_max=(...)
```

reports the minimum, median, and maximum Euclidean norms of the matrix rows and columns.

These quantities are numerical diagnostics. They are not physical displacements, stresses, or forces.

---

#### 8. Constraint matrix `A`

The structural constraints are represented by a separate matrix:

```text
[matrix-diagnostic] A shape=(181, 945) nnz=195 ...
```

`A` has `945` columns because the constraints act on the same `945` generalized displacement unknowns.

For this problem it contains `181` constraint equations.

With `M=45`, the implemented bending problem imposes the transverse end constraints together with one additional condition that removes the remaining rigid global-`x` translation.

The solver also checks the numerical rank of the constraint matrix:

```text
[matrix-diagnostic] A spectrum numerical_rank=181/181
...
condition=1.525619431063e+00
```

The result:

```text
numerical_rank = 181/181
```

shows that all `181` constraint equations are numerically independent at the reported tolerance.

---

#### 9. Augmented KKT system

The stiffness equations and the constraint equations are combined into one augmented system.

The system has the compact form:

$$ \begin{bmatrix} K & A^T \\ A & 0 \end{bmatrix}\begin{bmatrix} q \\ \lambda \end{bmatrix}=\begin{bmatrix} f \\ b \end{bmatrix} $$

where:

- `K` is the CUF stiffness matrix;
- `A` is the constraint matrix;
- `q` contains the generalized displacement unknowns;
- `lambda` contains the Lagrange multipliers associated with the constraints;
- `f` is the structural load vector;
- `b` is the right-hand side of the constraint equations.

The solver reports:

```text
[matrix-diagnostic] KKT shape=(1126, 1126) nnz=856273 ...
```

The matrix size follows directly from the displacement unknowns and the constraint equations:

$$ 1126 = 945 + 181 $$

The line:

```text
K_to_A_frobenius_ratio=3.997018928538e+08
```

compares the numerical scale of the stiffness block with the constraint block. The very large ratio indicates that the two parts of the KKT system operate at very different numerical scales.

---

#### 10. KKT diagnostic checkpoint

Before the linear solve, the complete algebraic system is saved:

```text
[diagnostic-v3] pre-spsolve checkpoint saved:
matrix=.../diagnostics/kkt_checkpoint/kkt_matrix.npz
rhs=.../diagnostics/kkt_checkpoint/rhs.npy
shape=(1126, 1126)
nnz=856273
```

The files are:

```text
diagnostics/kkt_checkpoint/kkt_matrix.npz
diagnostics/kkt_checkpoint/rhs.npy
```

They contain the exact sparse KKT matrix and right-hand side immediately before the solve.

This checkpoint is useful for:

- inspecting the numerical system independently;
- reproducing the linear solve;
- comparing different solver versions;
- performing strict regression tests.

The following hashes:

```text
[diagnostic-v3] SHA256 indptr=...
                         indices=...
                         data=...
                         rhs=...
```

are fingerprints of:

- the sparse matrix row structure (`indptr`);
- the column indices (`indices`);
- the numerical coefficients (`data`);
- the right-hand side (`rhs`).

If all four hashes are identical between two runs, the stored KKT system and its right-hand side are identical.

These files are numerical diagnostics; they are not the final physical displacement field.

---

#### 11. Ill-conditioning warning and equilibration

For this case the solver detects a poorly conditioned original KKT matrix:

```text
LinAlgWarning: Original KKT matrix is ill-conditioned
(rcond=8.03057e-19):
equilibration will be applied before the solve.
```

`rcond` is a reciprocal condition estimate. A very small value indicates that the algebraic system is numerically difficult to solve in its original scaling.

This message does **not** mean that the analysis has failed.

The solver automatically applies equilibration:

```text
[kkt-equilibration]
iterations=8
iterations_requested=8
iterations_performed=8
original_rcond=8.030567733991e-19
equilibrated_rcond=5.239671863586e-09
scale_min=3.963236039126e-05
scale_max=1.102447621678e+04
```

Equilibration rescales the algebraic equations to reduce their numerical imbalance before the direct solve.

It does not change:

- the CSF geometry;
- the material field;
- the CUF formulation;
- the applied load;
- the physical boundary conditions.

The improvement from:

```text
8.03e-19
```

to approximately:

```text
5.24e-09
```

shows that the scaling substantially improves the numerical conditioning of the system used for the solve.

The next line:

```text
[matrix-diagnostic] equilibration-scales
primal_min_median_max=(...)
multiplier_min_median_max=(...)
```

reports the scaling ranges applied respectively to the displacement unknowns and to the constraint multipliers.

---

#### 12. Linear solution and residual check

After solving the KKT system:

```text
[3/4] solve complete
```

the solver verifies the result:

```text
[verification] residual mean = -1.554559e-10
[verification] residual standard deviation = 3.280431e-09
[verification] equation-term scale = 3.025907e+05
```

The residual measures how closely the computed solution satisfies the assembled equations.

Here the residual is extremely small compared with the characteristic equation-term scale.

This provides an important numerical verification of the solved system, especially because the KKT matrix required equilibration before the direct solve.

---

#### 13. Optional solution checkpoint

The next message is:

```text
[solution-checkpoint] skipped: selected expansion does not export physical power coefficients
```

This message concerns an optional persistent representation of the solved displacement field.

For this run, the selected expansion does not provide the physical power coefficients required by that checkpoint mechanism, so this additional file is not written.

This is **not an error** and it does not invalidate the analysis.

The standard continuous displacement field is still reconstructed normally.

---

#### 14. Continuous displacement field ready

The final main solver stage is:

```text
[4/4] u(x,y,z) ready: elapsed=17.093 s
```

At this point the generalized CUF solution has been converted into the physical continuous displacement field:

$$ \mathbf{u}(x,y,z)=\left(u_x,u_y,u_z\right) $$

This is the principal public result of the solver.

The field can be evaluated at valid physical coordinates of the CSF member instead of being restricted to the internal generalized unknowns used during assembly.

The total elapsed solver time is also reported.

For this example, the detailed timing printed earlier shows that most of the computational cost is associated with the CUF pair assembly.

---

#### 15. Output adapter

Finally, the output adapter defined in the case is executed:

```text
written: .../output/bending_halfwave_legendre_N08/response.txt
```

and the solver ends with:

```text
continuous displacement field = READY
output directory              = .../output/bending_halfwave_legendre_N08
  response.txt
```

A successful execution therefore produces two distinct results:

1. the continuous physical displacement field `u(x,y,z)`;
2. the files generated by the selected output adapter.

For this case, the standard output adapter writes:

```text
output/bending_halfwave_legendre_N08/response.txt
```

The content of `response.txt` can then be inspected to see the displacement response at the sampling stations defined in the case file.

---

#### The complete solver path

The four numbered stages summarize the entire analysis:

```text
[1/4] model/basis ready
[2/4] global assembly complete
[3/4] solve complete
[4/4] u(x,y,z) ready
```

In compact form:

```text
CSF physical model
        +
CUF transverse basis
        |
        v
global CUF assembly
        |
        v
K + constraints
        |
        v
augmented KKT system
        |
        v
linear solution
        |
        v
continuous displacement field
u(x,y,z)
        |
        v
output adapter
        |
        v
response.txt
```

This is the complete execution path from the physical CSF description to the final CUF displacement response.


The structural problem files therefore define **what is applied to the physical CSF model and how it is constrained**, while the CUF case defined in Step 2 specifies **how that problem is approximated and solved**.

