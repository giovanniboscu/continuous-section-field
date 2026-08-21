# DRAFT

# CSF-CUF: a reproducible experimentation platform for CUF beam models

## 1. Making CUF more accessible 

The Carrera Unified Formulation (CUF) provides a general framework for constructing refined structural theories without committing in advance to a single beam kinematics.

A central CUF idea is that the three-dimensional displacement field can be expanded through a set of transverse approximation functions:

$$ \mathbf{u}(x,y,z) = \sum_{\tau} F_{\tau}(y,z)\, \mathbf{u}_{\tau}(x). $$

Here:

- $x$ is the longitudinal coordinate along the member axis;
- $y$ and $z$ are the transverse coordinates;
- $F_{\tau}(y,z)$ are transverse approximation functions;
- $\mathbf{u}_{\tau}(x)$ are the corresponding longitudinal unknowns.

Changing the transverse approximation makes it possible to construct theories with different levels of refinement while retaining a common variational structure.

This is one of the most attractive aspects of CUF: a large family of structural models can be described within the same conceptual framework.

At the same time, this generality can make CUF difficult to approach experimentally. A user who wants to test a new section, a different material distribution, a longitudinally varying member, or simply a different approximation order should not have to rebuild the mechanical formulation around each new example.

The CSF-CUF project is intended to reduce that barrier.

---

## 2. From a sectional model to CUF coefficients

The Python implementation developed here follows the formal coupling described in:

[`csf_cuf_formal_variable_section_extension.md`](./csf_cuf_formal_variable_section_extension.md)

The key idea is to keep the CUF kinematic and variational structure separate from the physical description of the cross-section.

The Continuous Section Field (CSF) provides the sectional state at every longitudinal coordinate:

$$ \mathcal{S}(x) \longrightarrow \lbrace \Omega^k(x), \mathbf{C}^k(x,y,z) \rbrace. $$

For each sub-domain $k$:

- $\Omega^k(x)$ is the physical sectional domain at coordinate $x$;
- $\mathbf{C}^k(x,y,z)$ is its constitutive matrix.

CUF then supplies the transverse approximation functions and their derivatives.

The sectional coefficients required by the CUF fundamental nucleus are obtained numerically from the current CSF state. In generalized form,

$$ J_{\tau,\phi s,\xi}^{mn,k}(x) = \int_{\Omega^k(x)} C_{mn}^{k}(x,y,z) F_{\tau,\phi}(y,z) F_{s,\xi}(y,z) \,d\Omega. $$

The global coefficient is obtained by summing the contributions of the sectional sub-domains:

$$ J_{\tau,\phi s,\xi}^{mn}(x) = \sum_{k=1}^{N_\Omega} J_{\tau,\phi s,\xi}^{mn,k}(x). $$

The complete data path is therefore

$$ \mathcal{S}(x) \longrightarrow \lbrace \Omega^k(x), \mathbf{C}^{k}(x,y,z) \rbrace \longrightarrow J_{\tau,\phi s,\xi}^{mn,k}(x) \longrightarrow J_{\tau,\phi s,\xi}^{mn}(x) \longrightarrow \text{CUF nucleus}. $$

No analytical longitudinal expression for the sectional coefficients is required.

---

## 3. A strict separation between model and solver

This separation is the central software principle of the project.

The CUF solver does not need to know whether a sub-domain is a flange, a web, a concrete region, a steel reinforcement, a degraded region, or part of a tapered section.

It does not need to reconstruct the geometry.

It does not need to assign a global material.

Instead, at a requested coordinate $x$, CSF supplies the geometry and constitutive state of every sectional domain.

Conceptually,

$$ \boxed{ \text{CSF} = \text{section geometry} + \text{material state} } $$

while

$$ \boxed{ \text{CUF engine} = \text{kinematics} + \text{sectional integration} + \text{fundamental nucleus} + \text{longitudinal solution} } $$

This makes the physical model independent from the numerical solver.

The same CUF engine can therefore operate on very different CSF descriptions without introducing geometry-specific or material-specific branches into the solver.

---

## 4. Constant-section validation

The first role of the implementation is verification against established CUF results.

A constant sectional state can be written as

$$ \mathcal{S}(x)=\mathcal{S}_0. $$

In this limit, the CSF-CUF implementation can be compared directly with published constant-section CUF benchmarks.

This is important because the constant-section case provides a controlled validation environment before introducing longitudinal variability.

The repository therefore treats published constant-section examples as validation cases: the geometry, material, CUF approximation and published observables can be reproduced and compared quantitatively.

Once this limiting case is verified, the same numerical machinery can be used without changing the solver for a variable sectional state.

---

## 5. Variable-section experiments

The next step is not a different solver.

It is simply a different CSF model.

A variable sectional state is represented by

$$ \mathcal{S}(x)\neq\text{constant}. $$

The variation may involve geometry,

$$ \Omega^k=\Omega^k(x), $$

material,

$$ \mathbf{C}^k=\mathbf{C}^k(x,y,z), $$

or both.

This distinction is intentionally broader than the usual separation between *prismatic* and *non-prismatic* members.

A member may keep the same external geometry while its material participation changes along the axis. Conversely, the geometry may vary while the material remains uniform. CSF can represent both situations through the same sectional interface.

For this reason, the project uses the more general language:

- **constant section** for a longitudinally invariant sectional state;
- **variable section** when the sectional state evolves along the member.

---

## 6. Lowering the barrier to CUF experimentation

The objective of this Python project is not only to reproduce one benchmark.

It is to make CUF experimentation easier to set up, reproduce, modify and share.

A user should be able to define a physical model through CSF, choose an analysis configuration, run the CUF engine, and inspect the results without rewriting the solver.

The intended workflow is

$$ \boxed{ \text{CSF model} + \text{analysis case} + \text{CUF engine} \longrightarrow \text{reproducible experiment} } $$

The CSF model contains the physical sectional description.

The analysis case contains choices such as:

- CUF approximation family and order;
- longitudinal discretization;
- numerical quadrature;
- loads;
- boundary conditions;
- requested recovery points and output settings.

The solver itself remains unchanged.

This separation substantially lowers the threshold for trying a new idea. A user interested in a different geometry or material distribution can work primarily on the model definition rather than on the mechanics code.

A user interested in approximation order, longitudinal discretization or recovery can modify the analysis case without redefining the physical member.

---

## 7. A platform for reproducible and shareable experiments

The longer-term purpose is to make the repository a place where CUF-based experiments can be shared as complete, reproducible cases.

An experiment can be represented by a small set of files, for example:

```text
experiment_name/
├── model.yaml
├── case.yaml
├── reference_results.csv
└── README.md
```

The solver does not need to be copied into every experiment.

This creates a common environment in which users can share:

- constant-section validation cases;
- variable-section studies;
- tapered members;
- multi-material sections;
- longitudinal material variation;
- degradation laws;
- alternative CUF approximation orders;
- numerical convergence studies;
- comparisons with analytical, numerical or experimental references.

The important point is that these experiments remain comparable because they use the same model-to-solver interface.

The repository can therefore distinguish three complementary activities:

### Validation

Published reference problems used to verify the implementation.

### Examples

Controlled demonstrations showing how the framework can be used.

### Experiments

User-defined studies intended to explore, compare and share new configurations.

---

## 8. Why CSF is useful here

The value of CSF becomes particularly clear when the problem moves beyond a single constant, homogeneous section.

Rather than embedding section-specific assumptions into the CUF solver, CSF acts as a continuously evaluable provider of sectional information.

At any longitudinal position,

$$ x \longrightarrow \mathcal{S}(x) \longrightarrow \lbrace \Omega^k(x), \mathbf{C}^k(x,y,z) \rbrace. $$

The CUF formulation can then operate on that sectional state without knowing how it was generated.

This means that the same solver architecture can remain valid while the sectional model becomes progressively more complex.

The separation is therefore not only a software convenience. It is what makes systematic experimentation possible.

---

## 9. Project direction

The present implementation should be understood as an open experimentation layer around the formal CSF-CUF coupling.

Its goals are to:

- preserve the general CUF kinematic and variational structure;
- obtain sectional data directly from CSF;
- avoid geometry-specific and material-specific assumptions in the solver;
- validate the constant-section limit against published CUF benchmarks;
- extend the same machinery to variable sectional states;
- make numerical experiments easy to define and reproduce;
- encourage users to share models, cases and results.

The broader objective is simple:

> make refined CUF beam modelling easier to explore without reducing the generality that makes CUF interesting in the first place.

The formal basis of the implementation is described in:

[`Formal CSF-CUF coupling for a continuous longitudinal section model`](./csf_cuf_formal_variable_section_extension.md)
