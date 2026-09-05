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

Before proceeding to the structural analysis, we will use these tools to check the model directly. In particular, we will verify the geometry of the T section, its variation along the beam, and the associated material field.

This is an important step because the CUF solver will subsequently use this CSF model as its physical description of the structure.

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
