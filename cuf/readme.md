
# A CUF Solver 


>[CSF–CUF tutorial: non-prismatic variable-material T-section](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/README.md)
>
>The solver implements the Carrera Unified Formulation (CUF), with CSF (Continuous Section Field) providing the continuous field description of the cross-section geometry and material properties along the structural member.


Why use CUF? For many structural problems, a three-dimensional finite element model is the most immediate and established choice. CUF follows a different philosophy: rather than relying primarily on spatial discretization, it requires the analyst to explicitly choose how the structural response is represented over the cross-section. This additional freedom is one of CUF’s main strengths, but also one of the main barriers to its practical use. Without an existing infrastructure, applying CUF to a new problem may first require developing and validating the numerical model itself. CSF–CUF was created to reduce this barrier, without hiding the modelling choices that define the CUF approach.


This repository is open for a reason: it is meant to be explored, questioned, tested, and even challenged. If you are a student, a researcher, or simply curious about how and why the method works, use it, experiment with it, and ask questions.
The goal is not to impose a way of doing things, but to propose one. If something is unclear, if you think something could be improved, or if you have an idea for a different implementation, that is exactly the kind of interaction this project is meant to encourage.


This repository provides a general-purpose framework for building and running beam models based on the Carrera Unified Formulation (CUF).

The implementation is designed around a clear separation between the physical description of the problem and the CUF numerical formulation. Models are defined externally through YAML files specifying geometry, material distribution, loads, boundary conditions, longitudinal discretization, and the transverse expansion rule.

Geometry and material properties are supplied by a Continuous Section Field (CSF), which acts as a general section provider along the beam axis. The CUF solver queries this continuous description during assembly, rather than embedding assumptions about a particular cross-section or longitudinal variation into the solver itself.

Variable cross-sections are represented directly in physical coordinates through the sectional state, rather than through a reference-to-physical coordinate mapping. The longitudinal variation of geometry and material is therefore carried by the sectional description, while the CUF formulation operates directly on the physical section provided at each longitudinal position.

The CUF core is consequently independent of the specific section geometry and material distribution. Likewise, transverse expansion laws are treated as interchangeable components through a common interface, allowing different CUF approximation families to be introduced without modifying the solver core.

The resulting architecture keeps the section and material description, CUF formulation, longitudinal finite-element discretization, and transverse expansion law as distinct components. The objective is not to implement a CUF model tailored to a particular benchmark, geometry, or expansion family, but to provide a reusable solver in which these components can be varied independently.

In practice, users can define and modify the physical model and select the transverse expansion law without having to interact with or modify the CUF solver core.



### Mathematical Formulation of the CSF–CUF Coupling

* [Formulation for Directly Prescribed Variable Sections](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md)
* [CUF displacement expansion for CSF coupling](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_displacement_expansionf_coupling.md)

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
