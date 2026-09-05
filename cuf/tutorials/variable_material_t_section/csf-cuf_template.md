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

This is the main input file passed to the CUF solver. It does not redefine the geometry or the material model. Instead, it connects the structural problem to the numerical choices used by CUF.

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

The file can be read from top to bottom as a description of how the analysis will be performed.

#### Case name

```yaml
case:
  name: double_t_bending_halfwave_legendre_N08
```

The `case` block gives the analysis a unique name. This name identifies this particular combination of physical problem and CUF approximation.

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

This separation is useful because the same physical problem can be reused with different CUF approximations.

The `adapter` tells CUF which already implemented problem formulation must be used to interpret that file. In this case, the selected formulation is `surface_halfwave`, which represents a distributed load applied to a physical surface of the CSF model with a half-wave variation along the beam.

We will inspect `bending_halfwave.yaml` in the next step, where the loaded surface and the load amplitude will be identified explicitly.

#### CUF transverse expansion

```yaml
cuf:
  basis: scaled_legendre
  order: 8
```

This block specifies how the displacement field is approximated over the cross-section.

Here the analysis uses the already implemented `scaled_legendre` expansion with order `8`.

The CSF model still provides the actual geometry and material distribution. The CUF expansion defines the mathematical functions used to represent the displacement field over that physical section.

#### Longitudinal approximation

```yaml
longitudinal:
  method: finite_element
  elements: 1
  order: 6
```

The transverse expansion describes the solution over the cross-section, but the solution must also vary along the beam axis.

In this example, the longitudinal direction is approximated using the finite-element formulation provided by the solver, with one longitudinal element of order `6`.

It is important to distinguish these two orders:

- `cuf.order: 8` controls the transverse approximation over the cross-section;
- `longitudinal.order: 6` controls the approximation along the beam axis.

They describe two different directions of the same three-dimensional displacement field.

#### Section integration

```yaml
section_integration:
  method: fixed_gauss_polygon
  gauss_order: 6
```

CUF requires numerical integration over the physical cross-section.

Here the integration is performed polygon by polygon on the CSF geometry using Gaussian quadrature.

The requested Gauss order is `6`. The solver may increase it when the selected CUF expansion requires a higher integration order.

#### Sampling

```yaml
sampling:
  stations: [0.00, 0.05, ..., 0.95, 1.00]
  displacement_samples: 201
  stress_grid: 31
```

These parameters control where and how densely the computed solution is inspected during post-processing.

The `stations` values are normalized positions along the beam:

- `0.00` corresponds to the beginning of the beam;
- `0.50` corresponds to its midpoint;
- `1.00` corresponds to the end.

The remaining values control the sampling density used for displacement and stress evaluation.

They do not change the structural solution itself; they control how the results are evaluated and reported.

#### Output

```yaml
output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/bending_halfwave_legendre_N08
```

Finally, the `output` block selects the standard CUF post-processing procedure and specifies where the results of this case will be written.






---


### Step 2 - Define the structural problems

Once the physical model has been inspected and verified, we can define what loading condition will be applied to it.


Two problem files are provided:

```text
problems/bending_halfwave.yaml
problems/torsion_halfwave.yaml
```

They describe two different static problems applied to the same CSF model.

The first defines a **bending half-wave problem**, while the second defines a **torsion half-wave problem**.

At this stage, the purpose of these files is to describe the physical problem: which part of the CSF model is loaded and how the load varies along the beam.

The geometry and material are not defined again here. They remain those of the CSF model created in Step 1.



### Step 3 - Define the CUF analyses

The final input files are the CUF cases:

```text
cases/bending_halfwave_legendre_N08.yaml
cases/torsion_halfwave_legendre_N08.yaml
```

Each case connects one of the previously defined structural problems to a particular CUF approximation.

In this example, both analyses use the already available **scaled Legendre expansion** with transverse order \(N=8\).

The case files also specify the remaining numerical choices required by the solver, such as:

* the longitudinal approximation;
* the numerical integration settings;
* the sampling of the solution;
* the output location.

The physical model is therefore defined only once and can be reused by different structural problems and different CUF analyses.

The complete organization of the example can be read as:

```text
t_noprismatic_csf.yaml
        ↓
inspect geometry and material
        ↓
bending_halfwave.yaml     torsion_halfwave.yaml
        ↓                         ↓
bending case               torsion case
        ↓                         ↓
      CUF solution              CUF solution
```
