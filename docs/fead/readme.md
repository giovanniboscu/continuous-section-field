# DRAFT

**Abstract**

This paper presents a computational implementation of the Carrera Unified Formulation (CUF) based on the introduction of the Continuous Section Field (CSF) as a primary object describing the geometric and material state of a beam cross-section along its longitudinal axis.

The Continuous Section Field is represented as an independent computational object, providing the sectional geometry and constitutive description at any requested longitudinal coordinate, independently of the transverse displacement expansion, longitudinal finite-element discretization, and numerical quadrature.

Its integration into CUF is established through the sectional integrals, whose longitudinally varying coefficients enter the fundamental nuclei while preserving the underlying variational formulation.

This organization enables a CUF computational core that is independent of any specific geometric or material model, allowing different physical sectional descriptions to be used without modifying the core formulation.

The work establishes the mathematical connection between the continuous sectional description and CUF and presents its realization within a computational framework.
# 1. Introduction

The Carrera Unified Formulation (CUF) provides a systematic framework for constructing refined structural models through expansions of the displacement field over the beam cross-section. Within this framework, the transverse approximation and the longitudinal discretization can be selected according to the requirements of the analysis. A distinct computational question concerns the representation of the physical beam itself: how can a CUF solver use varying sectional geometry and material properties without embedding a particular geometric or constitutive model in its computational core?

This work addresses that question through the **Continuous Section Field (CSF)**. Let \(x\) denote the longitudinal coordinate of the beam, and let \(y\) and \(z\) denote the transverse coordinates. The sectional state is represented by the function

\[
\mathcal S(x)=\{\Omega(x),\mathbf C(x,y,z)\},
\]

where \(\Omega(x)\) is the physical cross-sectional domain at position \(x\), and \(\mathbf C(x,y,z)\) is the constitutive matrix defined over that domain. This function describes the physical section independently of the transverse displacement expansion, the longitudinal finite-element mesh, and the numerical quadrature. In the implementation presented here, the continuous sectional field is an explicit computational object: the solver queries it at the longitudinal positions required by the analysis.

Connecting this object to CUF requires a corresponding mathematical treatment. The geometry and constitutive properties supplied by the sectional field enter the sectional integrations and produce coefficients that vary along the beam axis. These coefficients are retained in the CUF fundamental nuclei and in the associated weak-form assembly. Thus, the separation between physical description and numerical approximation is not merely a software convention; it is supported by an explicit connection to the variational formulation. The theoretical formulation is developed in the following section.

The principal contribution of this paper is a **computational implementation of CUF organized around this continuous sectional object**, together with the formulation required to integrate it into the CUF computational core. The resulting architecture allows different geometric configurations and material distributions to be supplied without specializing the core to a particular physical section. The work does not propose a replacement for CUF; it makes explicit and implements a way to connect its numerical approximation to an independently defined continuous physical model.

A numerical demonstration considers a tapered I-shaped beam with longitudinally varying geometry and material properties. The CSF–CUF results are compared with an independently constructed three-dimensional finite-element model of the same physical problem. The case is intended both to examine the numerical behavior of the implementation and to make the correspondence between the two descriptions inspectable.

**Reproducibility is an integral part of the study.** The source code, physical-model definitions, analysis configurations, execution procedures, and numerical results are made publicly available so that the reported experiment can be reconstructed and checked. The theoretical formulation and the complete numerical case are documented at the following locations:

- [CSF–CUF continuous geometry and material field formulation](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/CSF_CUF_Continuous_Geometry_and_Material_Field_Formulation.md)
- [I-Shape_L: implementation, numerical comparison, and reproducibility material](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape_L)

The remainder of the paper presents the mathematical connection between CSF and CUF, describes the computational implementation, and examines the numerical comparison and its reproducibility before drawing the conclusions.
