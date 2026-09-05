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
