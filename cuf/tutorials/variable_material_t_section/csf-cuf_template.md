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

<img width="994" height="879" alt="immagine" src="https://github.com/user-attachments/assets/a2610114-38a6-4d9a-9c5a-7a4ff4b150b0" />
*Figure - Longitudinal distribution of the elastic modulus assigned to each CSF polygon. The `top_flange` keeps a constant elastic modulus of `71700` along the entire beam, while the `web` varies continuously from `71700` at `z = 0` to `57360` at `z = 1000`. This plot provides a direct verification that the material stiffness is not uniform over the whole T section and that the prescribed longitudinal variation is correctly associated with the intended polygon.*
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
