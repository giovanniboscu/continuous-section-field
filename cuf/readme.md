
# A CUF Solver 


>[https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/readme.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/hollow_rectangle_validation/readme.md)
>
>The solver implements the Carrera Unified Formulation (CUF), with CSF (Continuous Section Field) providing the continuous field description of the cross-section geometry and material properties along the structural member.



This repository provides a framework for building and running models based on the Carrera Unified Formulation (CUF).

It is not intended as a theoretical introduction to CUF. Its purpose is to provide a parametric and reusable implementation that can be used directly from external model definitions.

The model is described through YAML files containing the geometry, material distribution, loads, boundary conditions, and the transverse expansion rule. From these inputs, the framework builds and runs the corresponding CUF model.

The solver core is independent of the specific cross-section geometry. Geometric and constitutive information is supplied by an external CSF-based section provider, which is queried by the CUF implementation during model construction and evaluation. This keeps the description of the physical problem separate from the numerical formulation and allows the same solver core to operate on different section configurations without embedding section-specific assumptions in the solver.

The repository includes two complete workflows.

The first is a **prismatic model**, derived from the 2010 Carrera and Giunta reference case. It is organized to reproduce the final benchmark tables for the more complex cross-section, providing a direct and repeatable reference case.

> **Original reference:**  
> E. Carrera and G. Giunta, *Refined Beam Theories Based on a Unified Formulation*,  
> International Journal of Applied Mechanics, Vol. 2, No. 1 (2010), pp. 117-143.  
> DOI: [10.1142/S1758825110000500](https://doi.org/10.1142/S1758825110000500)

The second is a **tapered model**, in which both geometry and material properties vary along the beam axis. It uses the same CUF core and the same CSF-based interface, showing how the framework can move from a classical prismatic benchmark to a genuinely variable-section problem without changing the solver architecture.

From a user's point of view, the expected workflow is therefore simple: define the physical model and the analysis parameters in YAML, run the corresponding model, and inspect the resulting displacement and stress outputs. The CUF machinery remains inside the framework, while the model definition stays external, explicit, and replaceable.


### CSF–CUF Documentation

* [CUF displacement expansion for CSF coupling](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_displacement_expansionf_coupling.md)
* [Formal extension of CUF to variable sections through CSF](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md)
* [Numerical validation against Carrera & Giunta](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_numerical_validation_carrera_giunta.md)
* [CSF–CUF sectional constitutive interface](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_sectional_constitutive_interface.md)



<!--

# DRAFT
# CSF-CUF Validation Commands

Run all commands from:

```bash
/home/giarrettu/github/continuous-section-field/cuf
```

## Prismatic double-T - Table 9 bending

```bash
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table9_N10.yaml
```

---

## Theoretical formulation and validation

The theoretical basis of the implementation can be found in the following documents:

- [Formal variable-section extension](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md)
- [Displacement expansion and CSF-CUF coupling](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_displacement_expansionf_coupling.md)
- [Sectional constitutive interface](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_sectional_constitutive_interface.md)
- [Numerical validation against Carrera and Giunta](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_numerical_validation_carrera_giunta.md)

-->
