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


## YAML Configuration Reference

The [CSF-CUF YAML Configuration Reference](docs/yaml_reference/readme.md) describes how to translate a physical structural problem and the corresponding numerical modelling choices into the configuration files used by the solver.

The configuration follows the separation of responsibilities adopted throughout CSF-CUF: geometry and materials are provided by CSF, the physical problem defines loads and boundary conditions, and the numerical case selects the CUF expansion, longitudinal finite-element approximation, integration settings, and output processing.

The documentation is organized into three complementary references:

- **[Case Configuration](docs/yaml_reference/case_configuration.md)** — Describes the numerical case configuration, including transverse CUF expansions, built-in and external basis plugins, longitudinal approximation and element partitioning, quadrature, solver settings, and adapter selection.

- **[Problem Configuration](docs/yaml_reference/problem_configuration.md)** — Describes how a structural problem references the CSF geometry and material model, specifies physical loads, and interacts with the selected load and constraint adapters.

- **[Output Configuration](docs/yaml_reference/output_configuration.md)** — Describes result sampling, output adapters, exported data, displacement fields, stresses, and numerical diagnostics.

These documents distinguish the general configuration interfaces from the options provided by individual plugins and adapters. They describe alternative modelling arrangements rather than prescribing a single CUF expansion, structural problem, or numerical discretization.

For a complete executable example, see the [CSF-CUF Quick Start](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/quickstart).
