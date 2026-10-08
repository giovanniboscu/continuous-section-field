# DRAFT

# From the Physical Problem to the CUF Model

## I want to analyse this beam. What do I need to decide?

Before thinking about input files or software commands, separate the few choices that define the analysis.

### 1. What is the beam?

Define:

- **geometry**
- **material**
- possible **variation along the beam**

### 2. What is the problem?

Define:

- **loads**
- **boundary conditions**

### 3. How do I represent the solution?

Here we adopt **CUF**.

Choose:

- the **transverse expansion**
- the **expansion order**
- the **longitudinal finite-element approximation**

In CUF, the transverse functions approximate the displacement over the cross-section, while the finite-element shape functions approximate it along the beam axis.

### 4. How do these parts work together?

The formulation keeps geometry and material external and general up to the evaluation of the CUF nuclei.

They are therefore not embedded in a case-specific CUF formulation: the geometric and constitutive descriptions provide the quantities required by the CUF formulation where they are needed.

This separation approach allows the geometry to be described externally and queried by the CSF core at the required points, without modifying the formulation.



### 5. Why is this separation useful?

In a traditional CUF derivation, the cross-section geometry and material distribution enter the formal expressions used to evaluate the sectional terms of the Fundamental Nucleus.

In CSF-CUF, this information is kept outside the CUF formulation and is provided by the section model only when the required quantities are evaluated.

The transverse and longitudinal approximation functions remain explicitly defined, while the physical section is represented by a continuous section provider.

Conceptually:

```text
Traditional CUF
geometry + material
        |
        v
case-specific formal sectional expressions
        |
        v
CUF Fundamental Nucleus
        |
        v
assembly
```

```text
CSF-CUF
transverse and longitudinal expansions
        |
        v
generic CUF Fundamental Nucleus
        ^
        |
continuous section/material provider
        |
        v
numerical evaluation at the required points
        |
        v
assembly
```

The immediate consequence is that the CUF nucleus does not need to be reformulated when the physical section changes.

The same formulation can query different geometries, material distributions, or sections varying along the beam axis through the same section-provider interface.

In this sense, the continuous section description replaces the need for a case-specific symbolic specialization of the sectional contribution while preserving the same CUF kinematic and finite-element framework.

That is the basic organization. Now we can build the first example.
