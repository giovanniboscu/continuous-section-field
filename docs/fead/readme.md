
**Abstract**

This paper presents a computational implementation of the Carrera Unified Formulation (CUF) based on the introduction of the Continuous Section Field (CSF) as a primary object describing the geometric and material state of a beam cross-section along its longitudinal axis.

The Continuous Section Field is represented as an independent computational object, providing the sectional geometry and constitutive description at any requested longitudinal coordinate, independently of the transverse displacement expansion, longitudinal finite-element discretization, and numerical quadrature.

Its integration into CUF is established through the sectional integrals, whose longitudinally varying coefficients enter the fundamental nuclei while preserving the underlying variational formulation.

This organization enables a CUF computational core that is independent of any specific geometric or material model, allowing different physical sectional descriptions to be used without modifying the core formulation.

The work establishes the mathematical connection between the continuous sectional description and CUF and presents its realization within a computational framework.
