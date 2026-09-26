# I-Shape - Prismatic and Tapered Beam Comparison

[Reproducibility](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/reproducibility.md)

## Purpose of this example

The purpose of this example is to show how the CSF-CUF framework separates the CUF computational core from the components that define a specific structural problem. Cross-section geometry and material description, transverse expansion, longitudinal FEM approximation, loads and boundary conditions are provided as independent components, while the CUF core itself remains unchanged.

To make this separation explicit, two closely related I-section cases are considered: the original prismatic configuration from Carrera et al. (2010) and a non-prismatic configuration obtained by reducing the web height along the beam axis. All the other analysis settings are kept unchanged.

Between the two analyses, **only the cross-section geometry is changed**. The CUF formulation, the longitudinal and transverse approximations, the loads, and the remaining analysis settings are kept unchanged.

The cross-section is provided independently through the **Continuous Section Field (CSF)**. During the analysis, the CUF solver requests from CSF the section information required at each longitudinal position.

The results of both cases are then compared with independent three-dimensional finite-element models (FEM3D).

## Starting geometry

The reference geometry is the prismatic I-section considered in:

> E. Carrera and G. Giunta,  
> "Refined Beam Theories Based on a Unified Formulation",  
> *International Journal of Applied Mechanics*, 2(1), 117–143, 2010.  
> DOI: [10.1142/S1758825110000500](https://doi.org/10.1142/S1758825110000500)

Starting from this section, two geometries are analysed:

- **Prismatic case:** the I-section remains constant along the beam.
- **Tapered case:** the cross-section varies continuously along the beam, with the clear web height decreasing from $a = 100\ \mathrm{mm}$ to $a = 20\ \mathrm{mm}$, corresponding to an **80% reduction**.

Only the prismatic section geometry is taken from the reference paper. The tapered geometry is generated from it by continuously reducing the web height along the beam.

## Ingredients of the analysis

Each CSF–CUF analysis combines three independent components:

- the **model**, which describes the beam geometry and material data and is defined entirely in YAML;
- the **problem**, which defines loads and boundary conditions by referencing a reusable Python implementation and configuring it through YAML;
- the **case**, which assembles the analysis by referencing reusable Python implementations for the transverse expansion, the longitudinal shape functions, and the other numerical components, while their orders, discretization, integration settings, and solver parameters are specified in YAML.

The Python components are implemented once and can then be reused across different analyses, while the YAML files provide the problem-specific configuration and composition.

In the present comparison, only the **model geometry** changes between the two analyses; the **problem definition and numerical approximation are kept unchanged**. Separate problem and case files are used only to keep the two runs and their outputs cleanly separated.

### Model

The **model** is defined entirely in YAML - no Python code required. It contains the beam length and the CSF description of the cross-section (geometry, polygons, material data), from which CSF provides the physical cross-section at any longitudinal coordinate $x$.

- in the **prismatic model**, the initial and final I-sections are identical;
- in the **tapered model**, the final section has an 80% reduced web height, with intermediate sections generated continuously between the two ends.

- [Prismatic I-section model](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/models/carrera_i_shaped_prism.yaml)

<p align="center">
  <img width="480" height="330" alt="Prismatic I-section" src="https://github.com/user-attachments/assets/f34bf086-a345-4a35-a003-a5951564f472" />
</p>

- [Tapered I-section model](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/models/carrera_i_shaped_taper80.yaml)

<p align="center">
  <img width="700" height="270" alt="Tapered I-section" src="https://github.com/user-attachments/assets/ad73144d-3579-4511-9604-66471f88a2ff" />
</p>

### Problem

The **problem** defines how the beam is loaded and constrained, independently of the section geometry - it answers "what is done to the beam?", not "what is the beam?".

The problem logic is **implemented in Python**, while its parameters and selection can be **configured and driven from YAML**. Once implemented, the same problem definition can therefore be reused across different models and cases without modifying the solver core.

The same loading and boundary-condition scheme is used for both geometries: a **transverse surface load with a half-wave sinusoidal variation along the beam axis**, applied to the lower flange, with matching boundary conditions at the ends.

- [Prismatic problem](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/problems/prism_table9.yaml)
- [Tapered problem](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/problems/taper_table9.yaml)

### Case

The **case** combines a model and a problem, and specifies the transverse CUF basis and order, the longitudinal finite-element approximation, and the numerical integration settings.

It is the **entry file passed to the `csf-cuf` solver**. From this file, the solver resolves the selected model, problem, reusable numerical components, and all settings required to assemble and run the analysis.

Unlike the model, which is pure YAML, the **transverse expansion and the longitudinal shape functions are implemented in Python**; once defined, they can be selected and configured from the case YAML and reused across different models, problems, and cases.

The same numerical approximation is used in both analyses - only the cross-section geometry provided by the model differs.

- [Prismatic case](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/cases/prism/lagrange_table9_N18_E1.yaml)
- [Tapered case](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/cases/taper/lagrange_table9_N18_E1.yaml)

## Running the analyses

```bash
csf-cuf cases/prism/lagrange_table9_N18_E1.yaml
csf-cuf cases/taper/lagrange_table9_N18_E1.yaml
```

The output location is defined in each case file's `output` section.

## Independent FEM3D comparison

The same two geometries are also analysed with independent three-dimensional finite-element models, at several points on the perimeter of the I-section:

- prismatic CSF–CUF vs. prismatic FEM3D;
- tapered CSF–CUF vs. tapered FEM3D.

The full set of comparison plots, for every vertex and displacement component, is here:

[FEM3D – prismatic vs. tapered comparison plots](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape/fem3d/prism_vs_taper)

Details on the numerical settings, model construction, and full reproducibility of the calculations are provided separately in the [reproducibility guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/reproducibility.md).
