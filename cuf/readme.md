
# A CUF Solver 


>[CSF–CUF tutorial: non-prismatic variable-material T-section](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/tutorials/variable_material_t_section/README.md)
>
>The solver implements the Carrera Unified Formulation (CUF), with CSF (Continuous Section Field) providing the continuous field description of the cross-section geometry and material properties along the structural member.


The implementation of CSF–CUF is based on a simple guiding idea: the numerical solver should not contain the physical description of the structure.

Instead, the solver should request the geometric and material information it needs from an external continuous description of the problem, at the position where that information is required.

This changes the direction in which the model is constructed. Geometry and material are not reduced in advance to a set of solver-specific sectional properties. They remain part of an independent physical description, represented by the Continuous Section Field (CSF), which the CUF formulation queries during assembly.

The same principle is applied to the transverse approximation. The expansion law is not embedded in the CUF core, but is provided through an independent interface. The solver therefore operates on the information supplied by the section description and by the selected expansion law without containing assumptions about a particular geometry, material distribution, or approximation family.

This separation is the main architectural principle behind the implementation:

**physical description → transverse representation → CUF formulation**

The objective is to preserve the CUF formulation while changing the way the physical problem is made available to it.

## Why use CUF?

For many structural problems, a three-dimensional finite element model is the most immediate and established choice.

CUF follows a different philosophy: rather than relying primarily on spatial discretization, it requires the analyst to explicitly choose how the structural response is represented over the cross-section.

This additional freedom is one of CUF's main strengths, but also one of the main barriers to its practical use. Without an existing infrastructure, applying CUF to a new problem may first require developing and validating the numerical model itself.

CSF–CUF was created to reduce this barrier without hiding the modelling choices that define the CUF approach.

This repository provides a general-purpose framework for building and running beam models based on the Carrera Unified Formulation.

Models are defined externally through YAML files specifying geometry, material distribution, loads, boundary conditions, longitudinal discretization, and the transverse expansion rule.

Geometry and material properties are supplied by the Continuous Section Field, which acts as a general section provider along the beam axis. During assembly, the CUF solver queries this continuous description at the current longitudinal position.

Variable cross-sections are therefore represented directly through their physical sectional state, rather than by embedding a particular reference-to-physical coordinate mapping in the CUF solver. The longitudinal variation of geometry and material belongs to the sectional description, while the CUF formulation operates on the physical section made available at each position.

The CUF core is consequently independent of the specific section geometry and material distribution.

Likewise, transverse expansion laws are treated as interchangeable components through a common interface. Different CUF approximation families can therefore be introduced without modifying the solver core.

The resulting architecture keeps four aspects distinct:

* the physical description of geometry and materials;
* the transverse expansion law;
* the CUF numerical formulation;
* the longitudinal finite-element discretization.

The objective is not to implement a CUF model tailored to a particular benchmark, geometry, or expansion family, but to provide a reusable framework in which these components can be varied independently.

In practice, users can modify the physical model, the material distribution, the longitudinal discretization, or the transverse expansion law without having to modify the CUF solver core.

## An open implementation

This repository is open for a reason: it is meant to be explored, questioned, tested, and challenged.

If you are a student, a researcher, or simply curious about how and why the method works, use it, experiment with it, and ask questions.

The goal is not to impose a way of doing things, but to propose one. If something is unclear, if you think something could be improved, or if you have an idea for a different implementation, that is exactly the kind of interaction this project is meant to encourage.


### Mathematical Formulation of the CSF–CUF Coupling

* [Formulation for Directly Prescribed Variable Sections](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md)
* [CUF displacement expansion for CSF coupling](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_displacement_expansionf_coupling.md)

* [Numerical validation against Carrera & Giunta](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_numerical_validation_carrera_giunta.md)
* [CSF–CUF sectional constitutive interface](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_sectional_constitutive_interface.md)



### References

* E. Carrera, G. Giunta, **“Refined Beam Theories Based on a Unified Formulation”**, *International Journal of Applied Mechanics*, 2(1) (2010), 117–143. [DOI](https://doi.org/10.1142/S1758825110000500).


- G. Giunta, S. Belouettar, E. Carrera, **“Analysis of FGM Beams by Means of Classical and Advanced Theories”**, *Mechanics of Advanced Materials and Structures*, 17 (2010), 622-635.

- S. O. Ojo, P. M. Weaver, **“Efficient strong Unified Formulation for stress analysis of non-prismatic beam structures”**, 2021.
