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

The implementation follows this separation directly.


That is the basic organization. Now we can build the first example.
