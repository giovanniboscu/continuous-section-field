## Building the T-section example step by step

The CUF input is organized in three directories:

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

**Coordinate convention.** In the inspection figures below, the longitudinal coordinate of the CSF model is labelled `Z`. In the CUF and FEM3D formulation used in the following steps, the beam axis is denoted by `x`, while `y` and `z` are the transverse coordinates. These are coordinate-label conventions for the same physical member; from Step 2 onward, this tutorial uses `x` as the longitudinal structural coordinate.

<img width="1289" height="484" alt="immagine" src="https://github.com/user-attachments/assets/69cfbfc3-9dee-44de-a18a-1421f67865c6" />

*Figure 1 - Cross-sections of the non-prismatic T-shaped model at `z = 0` and `z = 1000`. The section is composed of two physical polygons: the upper flange (`top_flange`, ID=0) and the web (`web`, ID=1). The change in their dimensions between the two locations shows the non-prismatic variation of the geometry along the beam. The vertex and edge identifiers shown in the plots will later be used to identify the physical surface on which the CUF load is applied.*

<img width="1294" height="476" alt="immagine" src="https://github.com/user-attachments/assets/483c2407-c174-463e-8833-3fdac0a32561" />

*Figure 2 - Three-dimensional view of the non-prismatic T-shaped CSF model and its material fields. The section geometry varies along the longitudinal coordinate `Z`. In this example, the CSF `weight` field shown on the left represents the elastic modulus \(E\), while the `shear weight` field shown on the right represents the shear modulus \(G\). The color variation shows how the material stiffness changes along the member and provides a direct visual check of the material distribution defined in the CSF model.*

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

solver:
  equilibration:
    iterations: 8

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

The `problem` block connects the CUF case to the physical structural problem to be solved.

The case file does not define the applied load or the associated boundary conditions directly. Instead, those are kept in a separate problem file:

```text
problems/bending_halfwave.yaml
```

This separation is deliberate. The problem file describes **what is applied to the physical CSF model and how the structure is constrained**, while the case file describes **how that problem is represented and solved with CUF**.

The `yaml` entry selects the problem definition, while the `adapter` selects the implementation that translates that problem into the corresponding CUF load and constraint contributions.

In this example, the `surface_halfwave` adapter is used for a distributed load acting on a physical surface of the CSF model with a half-wave variation along the longitudinal direction.

The complete contents of `bending_halfwave.yaml` are examined in **Step 3**, where the CSF model reference, loaded surface, load amplitude and direction, and boundary conditions are described explicitly.


<img width="1448" height="1086" alt="04bd6629-961a-4db7-a0b4-5ad262a771f0" src="https://github.com/user-attachments/assets/d4ad542d-86b1-4a6c-a2f0-eb769af62d81" />


<img width="1536" height="1024" alt="torsion" src="https://github.com/user-attachments/assets/9b4adc06-2528-489d-875d-9f97b57d01dc" />


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

The `section_integration` block is optional and can normally be omitted from the case file.

When it is omitted, the solver automatically determines a valid section quadrature order from the CUF order and the minimum requirement declared by the selected CUF basis.

An explicit section integration setting is only needed when a specific quadrature order is requested. The following `gauss_order: 30` block is an illustrative example; the actual case shown above requests `gauss_order: 6`:

```yaml
section_integration:
  method: fixed_gauss_polygon
  gauss_order: 30
```

The CUF formulation requires numerical integration over the physical cross-section. The section is integrated polygon by polygon on the CSF geometry using Gaussian quadrature.

`gauss_order` specifies a user-requested quadrature order. The selected CUF basis can declare a higher minimum requirement. In that case, the solver automatically uses the larger value.

Therefore, the value specified in the case acts as a requested minimum and never reduces the quadrature below the requirement imposed by the CUF basis.

For example, if `gauss_order: 30` is specified and the CUF basis requires a minimum order of 18, the solver uses 30. If the basis requires 32, the solver uses 32.

In normal cases, `section_integration` can simply be omitted and the automatic selection can be used.


#### Solver equilibration

The `solver` block is optional. If it is omitted, the solver uses the default equilibration setting of **8 iterations**.

The case file shown above does not include this block because the default value of `8` is already active.

Therefore, the following block:

```yaml
solver:
  equilibration:
    iterations: 8
```

is optional and simply states explicitly the default behavior.

`equilibration.iterations` specifies the number of equilibration iterations applied to the assembled algebraic system before its solution.

Equilibration acts on the numerical scaling of the assembled system. It does not modify the physical CSF model, the CUF basis, the applied loads, or the boundary conditions. Its purpose is to improve the numerical behavior of the linear system, particularly when the assembled equations contain coefficients with substantially different magnitudes.

A different number of iterations can be specified explicitly when needed.



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

The `response.txt` output discussed in this example contains the displacement response. `stress_grid` becomes relevant when stress evaluation is requested by the post-processing workflow.

#### Output

```yaml
output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/bending_halfwave_legendre_N08
```

The `output` block selects the standard CUF post-processing adapter and specifies the directory in which the results of this case will be written.

##### Output adapter details

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


### Step 4 - Run the CUF case

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

During the solution of the augmented KKT system, the solver evaluates its numerical conditioning.

If the original system is detected as poorly conditioned, the solver reports a warning such as:

```text
LinAlgWarning: Original KKT matrix is ill-conditioned
(rcond=...):
equilibration will be applied before the solve.
```

`rcond` is a reciprocal condition estimate. A very small value indicates that the algebraic system is numerically difficult to solve in its original scaling.

The solver can then apply equilibration before factorization. The corresponding diagnostic block reports:

```text
[kkt-equilibration]
iterations=...
iterations_requested=...
iterations_performed=...
original_rcond=...
equilibrated_rcond=...
scale_min=...
scale_max=...
```

Equilibration rescales the algebraic equations to reduce their numerical imbalance before the direct solve.

It does not change:

* the CSF geometry;
* the material field;
* the CUF formulation;
* the applied load;
* the physical boundary conditions.

The equilibration strategy and its parameters are configurable directly from the case YAML, as described above.

The additional diagnostic:

```text
[matrix-diagnostic] equilibration-scales
primal_min_median_max=(...)
multiplier_min_median_max=(...)
```

reports the scaling ranges applied respectively to the displacement unknowns and to the constraint multipliers.

When reproducing the example, the actual conditioning estimates, scaling factors, and final solution diagnostics are reported directly by the solver.


---

#### 12. Linear solution and residual check

After solving the KKT system:

```text
[3/4] solve complete
```

the solver verifies the result:

```text
[verification] residual mean = ...
[verification] residual standard deviation = ...
[verification] equation-term scale = ...
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


---

### Step 5 - Inspect the generated results

#### Results produced by the output adapter

After the solution has been completed, the output adapter configured in the case file

```yaml
output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/bending_halfwave_legendre_N08
```

post-processes the computed displacement field and writes the selected response quantities to the output directory.

For this case, the main result file is:

```text
response.txt
```

The file contains the displacement response at the longitudinal stations requested in the `sampling.stations` block. At each station, the response is evaluated at a set of reference points of the current physical cross-section.

The output has the following structure:

```text
x/L       x [mm]             y [mm]               z [mm]               point         ux [mm]             uy [mm]             uz [mm]
0.00      0.000000000000e+00  0.000000000000e+00   0.000000000000e+00   center        ...
0.00      0.000000000000e+00 -3.300000000000e+01   7.500000000000e+01   plus          ...
0.00      0.000000000000e+00  1.250000000000e+01  -5.000000000000e+01   minus         ...
0.00      0.000000000000e+00  0.000000000000e+00  -5.000000000000e+01   bottom_mid    ...
```

The columns have the following meaning:

- `x/L` is the normalized longitudinal coordinate;
- `x [mm]` is the corresponding physical longitudinal coordinate;
- `y [mm]` and `z [mm]` identify the physical position of the reported point on the current cross-section;
- `point` identifies the reference point;
- `ux [mm]`, `uy [mm]`, and `uz [mm]` are the three global displacement components evaluated at that physical point.

In this example, four reference points are reported at every station:

```text
center
plus
minus
bottom_mid
```

Because the beam is non-prismatic, the physical coordinates of some of these points vary with `x`. The output therefore reports both the reference-point label and its actual physical coordinates at every longitudinal station.

The output adapter converts the solved field `u(x,y,z)` into a compact set of directly readable physical displacement results. It does not perform a new structural solution; it queries and reports the displacement field obtained by the CUF analysis.

---

### Step 6 - Verify against the FEM3D reference model

#### Verification with the FEM3D reference model

The CUF results can be verified against the three-dimensional finite-element reference model included in:

```text
t_section/fem3d/fem/
```

The directory contains the two problem-specific drivers:

```text
run_bending_halfwave.py
run_torsion_halfwave.py
```

Both drivers start from the same CSF model and from the same loading and boundary-condition definitions used by the corresponding CUF cases. The geometry and material state are read from the CSF model through the CSF API, while the three-dimensional finite-element model is built independently and solved with OpenSees.

From the `t_section/fem3d` directory, the two FEM3D reference analyses can be generated with:

```bash
python3 fem/run_bending_halfwave.py
python3 fem/run_torsion_halfwave.py
```

The resulting files are written to:

```text
t_section/fem3d/output/bending_halfwave_model2
t_section/fem3d/output/torsion_halfwave_model2
```

For each problem, the FEM3D analysis produces:

```text
torsion_halfwave_model2/fem3d_native_displacements.csv
torsion_halfwave_model2/station_extrema.csv
torsion_halfwave_model2/summary.txt
torsion_halfwave_model2/station_points.csv

bending_halfwave_model2/fem3d_native_displacements.csv
bending_halfwave_model2/station_extrema.csv
bending_halfwave_model2/summary.txt
bending_halfwave_model2/station_points.csv
```

The files have different purposes:

- `fem3d_native_displacements.csv` contains the displacement field at all FEM3D nodes;
- `station_extrema.csv` reports the maximum absolute displacement components at the selected longitudinal stations;
- `summary.txt` contains the main information and checks associated with the FEM3D analysis;
- `station_points.csv` contains the displacement components evaluated at the same reference-point roles used by the CUF post-processing and is therefore the file used for the direct CUF/FEM3D comparison.

For convenience, these FEM3D reference results are already included in the repository, so reproducing the OpenSees analyses is not required in order to generate the comparison plots.

From the same `t_section/fem3d` directory, the graphical comparison between the CUF responses and the FEM3D reference solutions is produced with:

```bash
python plot_halfwave_outputs.py
```

The script automatically scans the CUF output directory, identifies the supported bending and torsion `response.txt` files, associates them with the corresponding FEM3D `station_points.csv` files, and generates separate displacement plots for `ux`, `uy`, and `uz`.

A typical execution reports:

```text
CUF scan root: .../t_section/output
Found 2 supported response file(s):
  [bending] bending_halfwave_legendre_N08 -> .../output/bending_halfwave_legendre_N08/response.txt
  [torsion] torsion_halfwave_legendre_N08 -> .../output/torsion_halfwave_legendre_N08/response.txt

FEM3D references:
  bending -> .../fem3d/output/bending_halfwave_model2/station_points.csv
  torsion -> .../fem3d/output/torsion_halfwave_model2/station_points.csv
```

A common vertical scale is then determined for each physical problem and displacement component so that the CUF and FEM3D curves are compared on the same graphical scale.

The generated figures are written under:

```text
t_section/fem3d/plots_halfwave/
```

with separate subdirectories for the bending and torsion cases. For the present examples, the generated files are:

```text
bending_halfwave_legendre_N08/displacement_ux_along_beam.png
bending_halfwave_legendre_N08/displacement_uy_along_beam.png
bending_halfwave_legendre_N08/displacement_uz_along_beam.png

torsion_halfwave_legendre_N08/displacement_ux_along_beam.png
torsion_halfwave_legendre_N08/displacement_uy_along_beam.png
torsion_halfwave_legendre_N08/displacement_uz_along_beam.png
```

The comparison is therefore performed between two independent numerical descriptions of the same physical problem: the CUF solution obtained from the cross-section expansion and longitudinal approximation, and the full three-dimensional finite-element solution obtained with OpenSees. The FEM3D reference is not part of the CUF solution procedure; it is included only as an independent verification of the displacement response.

---

#### Graphical comparison with the FEM3D reference

The displacement responses obtained with the CUF model can be compared directly with the FEM3D reference results through the plots generated by:

```bash
python plot_halfwave_outputs.py
```

The figures below show the longitudinal evolution of the three displacement components evaluated at the same reference points for the CUF and FEM3D models.

##### Bending half-wave

For the bending case, the CUF solution obtained with the scaled Legendre expansion at \(N=8\) is already essentially superimposed on the FEM3D reference over the beam length at the reported reference points. This is observed consistently for the three displacement components and provides a strong direct verification of the present \(N=8\) response. A formal convergence statement with respect to the transverse order would, however, require a dedicated study with increasing values of \(N\).

**Longitudinal displacement \(u_x\)**

[Open bending \(u_x\) plot](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/bending_halfwave_legendre_N08/displacement_ux_along_beam.png)

![Bending half-wave: CUF vs FEM3D, ux](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/bending_halfwave_legendre_N08/displacement_ux_along_beam.png?raw=1)

**Transverse displacement \(u_y\)**

[Open bending \(u_y\) plot](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/bending_halfwave_legendre_N08/displacement_uy_along_beam.png)

![Bending half-wave: CUF vs FEM3D, uy](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/bending_halfwave_legendre_N08/displacement_uy_along_beam.png?raw=1)

**Transverse displacement \(u_z\)**

[Open bending \(u_z\) plot](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/bending_halfwave_legendre_N08/displacement_uz_along_beam.png)

![Bending half-wave: CUF vs FEM3D, uz](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/bending_halfwave_legendre_N08/displacement_uz_along_beam.png?raw=1)

The bending comparison is therefore a strong direct verification of the CUF solution for the present model: at \(N=8\), the CUF and FEM3D curves are already essentially superimposed at the level shown by these displacement plots. This graphical agreement should be interpreted as a verification of the reported response, not as a formal proof of convergence with respect to \(N\).

##### Torsion half-wave

The same comparison can be performed for the torsional half-wave problem.

**Longitudinal displacement \(u_x\)**

[Open torsion \(u_x\) plot](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/torsion_halfwave_legendre_N08/displacement_ux_along_beam.png)

![Torsion half-wave: CUF vs FEM3D, ux](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/torsion_halfwave_legendre_N08/displacement_ux_along_beam.png?raw=1)

**Transverse displacement \(u_y\)**

[Open torsion \(u_y\) plot](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/torsion_halfwave_legendre_N08/displacement_uy_along_beam.png)

![Torsion half-wave: CUF vs FEM3D, uy](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/torsion_halfwave_legendre_N08/displacement_uy_along_beam.png?raw=1)

**Transverse displacement \(u_z\)**

[Open torsion \(u_z\) plot](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/torsion_halfwave_legendre_N08/displacement_uz_along_beam.png)

![Torsion half-wave: CUF vs FEM3D, uz](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/t_section/fem3d/plots_halfwave/torsion_halfwave_legendre_N08/displacement_uz_along_beam.png?raw=1)

For torsion, the \(N=8\) comparison should be regarded as an intermediate verification rather than as a final convergence result. A visible difference with the FEM3D reference remains in the present comparison, so it is preferable to repeat the CUF analysis with higher values of \(N\) and verify whether the displacement curves stabilize and approach a converged solution.

A useful convergence check is to repeat the torsion case for increasing transverse expansion orders and compare each result with both the previous CUF order and the FEM3D reference. Once the CUF curves become insensitive to further increases of \(N\), any remaining difference can no longer be attributed to the CUF transverse order alone. A further interpretation of that residual difference would also require checking the convergence of the FEM3D discretization.


---

## Reproducibility

A complete command-by-command reproducibility guide for the non-prismatic variable-material T-section tutorial is available here:

[`cuf/tutorials/variable_material_t_section/reproducibility.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/reproducibility.md)

The guide covers installation from a clean environment, CSF model inspection, CUF bending and torsion analyses, result inspection, and comparison against the FEM3D (OpenSees) reference solution.

Tested on Ubuntu/debian with Python 3.12.


