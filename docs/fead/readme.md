# DRAFT

**Abstract**

This paper presents a computational implementation of the Carrera Unified Formulation (CUF) based on the introduction of the Continuous Section Field (CSF) as a primary object describing the geometric and material state of a beam cross-section along its longitudinal axis.

The Continuous Section Field is represented as an independent computational object, providing the sectional geometry and constitutive description at any requested longitudinal coordinate, independently of the transverse displacement expansion, longitudinal finite-element discretization, and numerical quadrature.

Its integration into CUF is established through the sectional integrals, whose longitudinally varying coefficients enter the fundamental nuclei while preserving the underlying variational formulation.

This organization enables a CUF computational core that is independent of any specific geometric or material model, allowing different physical sectional descriptions to be used without modifying the core formulation.

The work establishes the mathematical connection between the continuous sectional description and CUF and presents its realization within a computational framework.

# 1. Introduction

The Carrera Unified Formulation (CUF) provides a general framework for constructing refined structural models through systematic expansions of the displacement field over the beam cross-section. The choice of transverse expansion and the longitudinal approximation determines the numerical representation of the displacement field. A distinct computational question is how to provide the solver with the physical cross-sectional geometry and material properties without embedding a particular geometric or constitutive model in its core.

This paper presents a computational implementation of CUF organized around the **Continuous Section Field (CSF)**. The central idea is to treat the physical sectional state as a primary, independently defined function of the longitudinal position. Let $x$ denote the longitudinal coordinate of a beam of length $L$, and let $(y,z)$ denote the transverse coordinates. The sectional state is written as

$$
\mathcal{S}(x) = \bigl\{\Omega(x),\,\mathbf{C}(x,y,z)\bigr\}, \qquad 0 \leq x \leq L,
$$

where $\Omega(x)$ is the physical cross-sectional domain and $\mathbf{C}(x,y,z)$ is the local constitutive matrix defined over that domain. This description accommodates both prismatic and non-prismatic members, as well as longitudinal and sectional variations of material properties. It is specified independently of the transverse displacement basis, longitudinal finite-element mesh, and numerical quadrature.

In the proposed implementation, $\mathcal{S}(x)$ is not merely a formal notation. It is realized as a computational object that can be evaluated at longitudinal positions requested by the solver. The object supplies the geometry and constitutive information required for sectional integration. The CUF computational core can consequently operate on different physical sectional descriptions without being specialized to any one of them. Independence here concerns the organization of the model and the solver; the numerical response necessarily remains dependent on the supplied geometry and material properties.

Establishing this organization requires an explicit mathematical connection between the continuous sectional description and CUF. The geometric domains and constitutive matrices supplied by CSF enter the sectional integrals, producing coefficients that vary along the beam and contribute to the CUF fundamental nuclei. The underlying variational formulation is retained. The theoretical section of this paper develops this connection; the implementation section then explains how the corresponding mathematical responsibilities are represented in the software.

The implementation is accompanied by a numerical study of a tapered I-shaped member, with an independent three-dimensional finite-element reference. The study is intended to demonstrate the computational realization of the proposed separation and to make its numerical behavior directly inspectable. The complete source code, physical model definitions, numerical configurations, execution procedures, and results are publicly available so that the reported analyses can be reproduced and checked.

The mathematical formulation is documented in the [CSF–CUF Continuous Geometry and Material Field Formulation](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/CSF_CUF_Continuous_Geometry_and_Material_Field_Formulation.md). The reproducible numerical case and its supporting materials are available in the [I-Shape_L repository directory](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape_L).

The contribution of the paper is therefore a computational realization of CUF in which a continuous physical sectional description is a first-class object, together with the mathematical coupling needed to use that object in the CUF formulation and a publicly reproducible numerical demonstration.
