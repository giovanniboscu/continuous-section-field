.
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

In the CUF formulation, cross-section geometry and material properties enter the evaluation of the sectional contributions to the Fundamental Nucleus. These contributions can be evaluated analytically or numerically, depending on the adopted implementation.

In CSF-CUF, the geometric and material descriptions are provided independently by a continuous section model, which is queried whenever the corresponding quantities are required during numerical integration.

The transverse and longitudinal approximation functions remain explicitly defined according to the CUF kinematic framework, while the physical section is represented by an independent continuous field provider.

Conceptually:

**CUF with Explicit Sectional Data**

```text
Kinematic expansions    Geometry and material
         \                    /
          \                  /
           CUF sectional terms
                   |
                   v
       Analytical or numerical
             evaluation
                   |
                   v
                Assembly
```

**CUF with CSF-Provided Sectional Data**

```text
Transverse and           Continuous CSF
longitudinal expansions  geometry/material fields
          \                   /
           \                 /
            \               /
         CUF Fundamental Nucleus
                   |
                   v
         Pointwise evaluation
                   |
                   v
          Numerical integration
                   |
                   v
                Assembly
```

The immediate consequence is that the CUF mechanical formulation remains unchanged when the physical section changes.

CSF-CUF enhances the operational generality of the CUF framework by providing geometry and material properties through independent continuous fields, queried during numerical integration. This allows the same computational core to accommodate different cross-sections, material distributions, and longitudinal variations without modifying the underlying CUF kinematic assumptions, variational formulation, or finite-element framework.

That is the basic organization. Now we can build the first example.
