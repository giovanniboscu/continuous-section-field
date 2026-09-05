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

The structural problem files therefore define **what is applied to the physical CSF model and how it is constrained**, while the CUF case defined in Step 2 specifies **how that problem is approximated and solved**.

### Step 3 - Run the CUF case

Once the CSF model, structural problem, and CUF case have been defined, the analysis can be launched directly from the case file:

```bash
csf-cuf cases/bending_halfwave_legendre_N08.yaml
```

The solver prints a detailed execution report. The output is useful not only for checking that the analysis completed successfully, but also for understanding the numerical model that was actually assembled and solved.

The main parts of the output are described below.

#### Analysis identification

The first block summarizes the input selected by the case:

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

The solver confirms the case name, the structural problem file, and the CSF physical model that has been loaded.

```text
CUF order = 8
```

confirms that the selected transverse expansion is being used with order \(N=8\).

The line

```text
solver public output = u(x,y,z)
```

is particularly important. The final result exposed by the solver is the continuous physical displacement field

\[
\mathbf{u}(x,y,z)
=
\left(
u_x(x,y,z),
u_y(x,y,z),
u_z(x,y,z)
\right).
\]

The internal generalized CUF degrees of freedom are therefore not the final public result: after the algebraic system has been solved, they are recovered into a field that can be evaluated at physical points of the beam.

---

#### Automatic quadrature checks

Before assembling the system, the solver checks whether the integration orders requested in the case are sufficient.

```text
[quadrature] section Gauss requested = 6
[quadrature] section Gauss effective = 9
[quadrature] CUF basis minimum     = 9
```

The case requested section Gauss order `6`, but the `scaled_legendre` expansion at \(N=8\) requires at least `9`. The solver therefore uses:

```text
effective = max(requested, basis minimum) = 9
```

This automatic increase prevents the selected CUF expansion from being integrated with an insufficient sectional quadrature order.

The longitudinal check is reported separately:

```text
[quadrature] longitudinal degree estimate = 31
[quadrature] longitudinal variation axes  = y,z
[quadrature] longitudinal material varies = true
[quadrature] longitudinal material degree = 1 (automatic)
[quadrature] longitudinal Gauss requested = 15
[quadrature] longitudinal Gauss minimum   = 16
[quadrature] longitudinal Gauss effective = 16
```

`longitudinal degree estimate = 31` is the solver's estimate of the polynomial complexity that must be integrated along the beam after the contributions of the longitudinal approximation, the changing transverse geometry, the CUF basis, and the material variation have been combined.

```text
longitudinal variation axes = y,z
```

means that the CSF section changes along the member in both transverse directions relevant to the CUF basis.

```text
longitudinal material varies = true
longitudinal material degree = 1 (automatic)
```

confirms that the solver has detected a longitudinal material variation. In this example its polynomial contribution is automatically recognized as degree `1`, consistent with the linear material variation introduced in the CSF model.

The initially requested longitudinal Gauss order is `15`, but the estimated degree requires at least `16`. The effective value is therefore increased to `16`.

The important distinction is that these values are **integration orders**. They must not be confused with `cuf.order` or `longitudinal.order`.

---

#### CUF basis size

The first main solver stage ends with:

```text
[1/4] model/basis ready: domains from CSF, M=45
```

`domains from CSF` confirms that the physical cross-sectional domains used by CUF come directly from the CSF model.

`M=45` is the number of active transverse CUF expansion functions for the selected `scaled_legendre` basis at \(N=8\).

The transverse functions are indexed by

\[
\tau = 1,\ldots,M.
\]

Each one contributes generalized displacement amplitudes to the global problem.

---

#### Assembly of the CUF system

The next stage builds the global structural equations:

```text
[assembly] element 1/1 started: 2025 CUF pairs
```

Since \(M=45\), the assembly must evaluate all ordered pairs of transverse functions:

\[
M^2 = 45^2 = 2025.
\]

These are the \((\tau,s)\) combinations required to construct the CUF stiffness contributions.

The progress lines:

```text
[assembly] element 1/1 tau=1/45  pairs=45/2025   ...
[assembly] element 1/1 tau=10/45 pairs=450/2025  ...
...
[assembly] element 1/1 tau=45/45 pairs=2025/2025 ...
```

show the progress of this calculation.

`entries` is the number of sparse matrix contributions accumulated during assembly. The timing fields distinguish the time spent building each CUF pair from the time spent scattering those contributions into the global sparse representation.

At the end:

```text
[assembly] triplets complete elapsed=16.6s entries=855883
[assembly] COO->CSR complete elapsed=0.0s nnz=855883
[assembly] loads complete elapsed=0.0s total=16.7s
```

the stiffness contributions have been collected and converted into the sparse matrix format used by the solver.

`nnz` means **number of non-zero matrix entries**.

The external load vector is then assembled using the structural problem defined in `bending_halfwave.yaml`.

---

#### Global degrees of freedom

The completed assembly reports:

```text
[2/4] global assembly complete: DOFs=945
```

The unconstrained CUF system contains `945` generalized displacement degrees of freedom.

This number is determined by the longitudinal representation, the `45` transverse CUF functions, and the three displacement components associated with every active generalized position.

The important point is that `DOFs=945` is the size of the unknown displacement vector before the constraint equations are added.

---

#### Stiffness matrix \(K\)

The solver then prints numerical diagnostics for the assembled stiffness matrix:

```text
[matrix-diagnostic] K shape=(945, 945) nnz=855883 ...
```

`K` is the global CUF stiffness matrix.

```text
shape=(945, 945)
```

matches the `945` generalized displacement unknowns.

The remaining values are numerical diagnostics:

- `nnz` is the number of non-zero entries;
- `abs_nonzero_min` and `abs_nonzero_max` give the smallest and largest absolute non-zero matrix entries;
- `frobenius` is the Frobenius norm of the matrix;
- `diag_abs_positive_min` and `diag_abs_max` describe the magnitude range of its non-zero diagonal entries;
- `diag_zeros=0` confirms that no exactly zero diagonal entries are present.

The following line:

```text
[matrix-diagnostic] K norms row_l2_min_median_max=(...)
```

reports the minimum, median, and maximum Euclidean norms of the rows and columns. These values are diagnostic information used to reveal large differences in numerical scale inside the assembled system.

They should not be interpreted as physical response quantities.

---

#### Constraint matrix \(A\)

The boundary conditions defined by the structural problem are represented separately:

```text
[matrix-diagnostic] A shape=(181, 945) nnz=195 ...
```

`A` is the constraint matrix.

It has `945` columns because the constraints act on the same `945` generalized displacement unknowns.

It has `181` rows because this bending problem generates `181` independent constraint equations. With \(M=45\), these are the transverse end constraints together with the additional axial rigid-body anchor described in the problem definition.

The next diagnostic is especially useful:

```text
[matrix-diagnostic] A spectrum numerical_rank=181/181
...
condition=1.525619431063e+00
```

The reported numerical rank is equal to the number of rows:

```text
181 / 181
```

so no linear dependence is detected among the imposed constraints at the reported numerical tolerance.

---

#### KKT system

The displacement equations and the constraint equations are combined into the augmented KKT system:


`[K  A^T; A  0] [q; λ] = [f; b]`

where:

- \(q\) contains the generalized CUF displacement unknowns;
- \(\lambda\) contains the Lagrange multipliers associated with the constraints;
- \(f\) is the assembled load vector;
- \(b\) is the constraint right-hand side.

The log reports:

```text
[matrix-diagnostic] KKT shape=(1126, 1126) nnz=856273 ...
```

The size follows directly from:

\[
1126 = 945 + 181.
\]

The diagnostic

```text
K_to_A_frobenius_ratio=3.997018928538e+08
```

shows that the stiffness and constraint blocks have very different numerical scales. This is one of the quantities useful when examining the conditioning of the augmented system.

---

#### Diagnostic KKT checkpoint

Immediately before solving, the complete sparse KKT system is saved:

```text
[diagnostic-v3] pre-spsolve checkpoint saved:
matrix=.../diagnostics/kkt_checkpoint/kkt_matrix.npz
rhs=.../diagnostics/kkt_checkpoint/rhs.npy
```

The two files contain:

```text
kkt_matrix.npz
rhs.npy
```

and allow the exact algebraic system sent to the linear solver to be inspected or reproduced independently.

The log also records the matrix shape, sparse format information, data types, and whether the sparse indices are sorted and canonical.

The SHA256 values:

```text
SHA256 indptr=...
       indices=...
       data=...
       rhs=...
```

are fingerprints of the sparse matrix structure, its numerical coefficients, and the right-hand side. They are useful for strict regression tests: two runs that produce the same hashes have produced exactly the same stored KKT data and right-hand side.

These diagnostic checkpoint files are not the physical displacement result; they are a snapshot of the algebraic system before the solve.

---

#### Ill-conditioning and automatic equilibration

For this case the solver detects that the original KKT matrix is poorly conditioned:

```text
LinAlgWarning: Original KKT matrix is ill-conditioned
(rcond=8.03057e-19):
equilibration will be applied before the solve.
```

`rcond` is a reciprocal condition estimate. A very small value indicates a numerically ill-conditioned or strongly unbalanced matrix.

This warning does **not** mean that the analysis has failed. The solver responds by applying numerical equilibration before solving:

```text
[kkt-equilibration]
iterations=8
original_rcond=8.030567733991e-19
equilibrated_rcond=5.239671863586e-09
```

Equilibration rescales the equations and unknown blocks to reduce their numerical imbalance. It does not change the physical model, the CUF formulation, the load, or the boundary conditions.

The improvement from the original to the equilibrated `rcond` shows that the rescaling has substantially improved the numerical conditioning of the system used for the direct solve.

The following line:

```text
[matrix-diagnostic] equilibration-scales
primal_min_median_max=(...)
multiplier_min_median_max=(...)
```

reports the scaling factors applied to the displacement unknowns (`primal`) and to the constraint multipliers (`multiplier`). These are purely numerical scaling quantities.

---

#### Solution and residual verification

After the linear system is solved:

```text
[3/4] solve complete
```

the solver checks the recovered solution against the assembled equations:

```text
[verification] residual mean = -1.554559e-10
[verification] residual standard deviation = 3.280431e-09
[verification] equation-term scale = 3.025907e+05
```

The residual measures how closely the computed solution satisfies the original algebraic equations.

Here the residual fluctuations are extremely small compared with the characteristic equation-term scale, providing a numerical check that the solved system is being satisfied to high precision.

This verification is particularly important after equilibration: the solver does not rely only on the fact that the linear solver returned a solution, but checks the resulting equations numerically.

---

#### Optional solution checkpoint

The next message is:

```text
[solution-checkpoint] skipped:
selected expansion does not export physical power coefficients
```

This refers to the optional persistent compiled displacement checkpoint.

For this `scaled_legendre` run, the selected expansion does not provide the physical power-coefficient representation required by that checkpoint format, so the persistent solution checkpoint is not written.

This is **not an analysis error**. The solved displacement field is still constructed immediately afterward and the normal output is produced.

---

#### Continuous physical displacement field

The final solver stage is:

```text
[4/4] u(x,y,z) ready: elapsed=17.093 s
```

At this point the algebraic CUF solution has been transformed into the physical continuous field

\[
\mathbf u(x,y,z).
\]

This is the main public result of the solver. It can be queried at arbitrary valid physical points of the CSF beam rather than only at the internal generalized degrees of freedom.

The reported `elapsed` time is the total solver time for this run. The detailed timing above shows that, in this particular case, most of that time is spent in CUF matrix assembly.

---

#### Post-processing output

After the displacement field is ready, the output adapter selected in the case is executed:

```text
written: .../output/bending_halfwave_legendre_N08/response.txt
```

The final confirmation is:

```text
continuous displacement field = READY
output directory              = .../output/bending_halfwave_legendre_N08
  response.txt
```

A successful run therefore ends with two distinct results:

1. the in-memory continuous displacement field `u(x,y,z)`, which is the public structural solution;
2. the files generated by the selected output adapter, in this case `response.txt`.

The content of `response.txt` can then be inspected using the sampling stations defined in the case.

---

#### Reading the four solver stages at a glance

The numbered messages summarize the complete analysis pipeline:

```text
[1/4] model/basis ready
[2/4] global assembly complete
[3/4] solve complete
[4/4] u(x,y,z) ready
```

They correspond to:

```text
CSF physical model + CUF basis
              |
              v
      global CUF assembly
              |
              v
    constrained KKT solution
              |
              v
 continuous physical field
          u(x,y,z)
              |
              v
       output adapter
              |
              v
        response.txt
```

This sequence is the central execution path of the CSF-CUF analysis.

