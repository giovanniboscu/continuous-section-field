# CSF-CUF Architecture

## 1. Objective

This document defines and tracks the architecture of the CSF-CUF computational project.

The objective is to implement the complete computational chain

```text
CSF
-> CSF-CUF Bridge
-> CUF Solver
-> u(x,y,z)
-> strain
-> stress
```

starting from the generalized CSF-CUF formulation already developed and from the numerical validation against the Carrera-Giunta prismatic benchmark.

This document is intended to remain active and to be updated as the implementation evolves.

---

## 2. Architectural separation

The project is divided into three principal levels:

```text
CSF
 |
 v
CSF-CUF Bridge
 |
 v
CUF Solver
```

Each level has a distinct responsibility.

### 2.1 CSF

CSF is responsible for the longitudinal sectional state.

At every longitudinal coordinate `x`, CSF provides the geometrical and constitutive description of the current cross-section.

Conceptually,


$$ \mathcal{S}(x)=\{\Omega^k(x),\mathbf{C}^k(x,y,z)\}_{k=1}^{N_\Omega}. $$

CSF therefore owns:

- sectional geometry;
- transverse sub-domains;
- material assignment;
- constitutive fields;
- longitudinal evolution of geometry;
- longitudinal evolution of constitutive properties.

CSF does not own the CUF approximation, the longitudinal structural solution, or the global boundary-value problem.

### 2.2 CSF-CUF Bridge

The CSF-CUF Bridge converts the sectional information supplied by CSF into the quantities required by the CUF formulation.

The bridge is responsible for the reusable computational chain

$$ \mathcal{S}(x)\longrightarrow\mathbf{C}^k(x,y,z)\longrightarrow J_{\tau,\phi s,\xi}^{mn}(x)\longrightarrow\mathbf{K}_{\tau s}(x). $$

Its principal API levels are therefore:

1. constitutive coefficients `C`;
2. generalized sectional coefficients `J`;
3. generic CUF fundamental nucleus `K`.

The bridge does not solve the longitudinal structural problem.

### 2.3 CUF Solver

The CUF Solver interrogates the bridge and solves the longitudinal structural problem.

The solver owns:

- longitudinal domain;
- global loading data;
- boundary conditions;
- longitudinal approximation or discretization;
- integration points required by the selected solution method;
- global assembly;
- numerical solution;
- generalized displacement amplitudes;
- reconstruction of the three-dimensional displacement field;
- strain recovery;
- stress recovery.

The solver must not need to know how the physical cross-section is internally represented by CSF.

---

## 3. Constitutive provider

The constitutive layer must be reusable and independent of the particular CUF basis.

The generic constitutive interface must provide the local matrix

$$ \mathbf{C}^k(x,y,z) $$

and individual coefficients

$$ C_{mn}^k(x,y,z). $$

Conceptually:

```text
ConstitutiveProvider
    matrix(x, domain_id, y, z)
    coefficient(x, domain_id, m, n, y, z)
```

The bridge must consume this generic interface rather than depend directly on a particular material parametrization.

### 3.1 Initial isotropic two-field specialization

The first reusable specialization is the two-field closure based on

$$ E_k(x) $$

and

$$ G_k(x). $$

Define

$$ \lambda_k(x)=G_k(x)\frac{E_k(x)-2G_k(x)}{3G_k(x)-E_k(x)}. $$

Then

$$ C_{11}^k=C_{22}^k=C_{33}^k=\lambda_k+2G_k. $$

$$ C_{12}^k=C_{13}^k=C_{23}^k=\lambda_k. $$

$$ C_{44}^k=C_{55}^k=C_{66}^k=G_k. $$

This is an initial constitutive specialization, not a restriction of the generic bridge architecture.

Future constitutive providers may include orthotropic, fully anisotropic, tabulated, or functional material laws without changing the `J` and `K` APIs.

---

## 4. Section provider

The sectional interface provides the transverse geometry associated with the current longitudinal coordinate.

Conceptually:

```text
SectionProvider
    state(x)
    domains(x)
    domain(x, domain_id)
    boundaries(x, domain_id)
```

For each domain, the bridge must be able to obtain the integration region

$$ \Omega^k(x). $$

The same interface must support both constant and longitudinally varying sections.

For a prismatic beam,

$$ \Omega^k(x)=\Omega^k. $$

For a non-prismatic beam,

$$ \Omega^k=\Omega^k(x). $$

---

## 5. CUF basis interface

The CUF basis is independent of the CSF sectional representation.

The basis interface must provide the transverse functions and the transverse derivatives required by the generalized sectional coefficients.

Conceptually:

```text
CUFBasis
    size
    value(tau, y, z)
    derivative(tau, direction, y, z)
```

The initial validation basis is the fourth-order Maclaurin basis used for the Carrera-Giunta benchmark.

The architecture must not depend on the Maclaurin basis specifically.

---

## 6. Generalized sectional coefficient API

The primary bridge quantity is the generalized sectional coefficient

$$ J_{\tau,\phi s,\xi}^{mn,k}(x)=\int_{\Omega^k(x)}C_{mn}^k(x,y,z)F_{\tau,\phi}(y,z)F_{s,\xi}(y,z)\,d\Omega. $$

The assembled sectional coefficient is

$$ J_{\tau,\phi s,\xi}^{mn}(x)=\sum_{k=1}^{N_\Omega}J_{\tau,\phi s,\xi}^{mn,k}(x). $$

The bridge must expose a generic API capable of evaluating these quantities without assuming a particular section geometry, material law, or solver.

Conceptually:

```text
bridge.J(
    x,
    tau,
    test_derivative,
    s,
    trial_derivative,
    constitutive_i,
    constitutive_j
)
```

The API must also permit access to domain-level contributions when required for verification and diagnostics.

---

## 7. Generic fundamental nucleus API

The second principal bridge output is the generic CUF fundamental nucleus

$$ \mathbf{K}_{\tau s}(x). $$

For each ordered pair `(tau, s)`, the bridge constructs the corresponding 3-by-3 CUF operator block from the required `J` coefficients.

Conceptually:

```text
bridge.K_block(x, tau, s)
```

For a general CSF state, the entries of `K` may contain longitudinally varying coefficients and longitudinal differential operators.

Therefore `K_block` must not assume that the result is already a numerical algebraic matrix.

The bridge provides the operator structure.

The solver determines how that operator is discretized or specialized longitudinally.

This distinction is essential for supporting both prismatic and non-prismatic problems.

---

## 8. Bridge contract

The core bridge contract is

```text
x
 |
 v
CSF sectional state
 |
 +--> geometry Omega^k(x)
 |
 +--> constitutive field C^k(x,y,z)
 |
 v
CUF basis
 |
 v
J coefficients
 |
 v
generic K block
```

In compact mathematical form,

$$ x\longrightarrow\mathcal{S}(x)\longrightarrow J_{\tau,\phi s,\xi}^{mn}(x)\longrightarrow\mathbf{K}_{\tau s}(x). $$

The solver is a consumer of this contract.

---

## 9. Solver contract

The solver receives the global structural problem independently of the bridge.

Conceptually:

```text
CUFProblem
    longitudinal_domain
    basis
    loads
    boundary_conditions
    solver_options

LongitudinalSolver
    bridge
    problem
    solve()
```

During assembly or evaluation, the solver queries the bridge at the longitudinal coordinates required by the selected numerical method.

Conceptually:

```text
for x in required_longitudinal_points:
    K = bridge.K_block(x, tau, s)
```

The solver then performs the selected longitudinal specialization or discretization.

The final solution object should expose, at minimum:

```text
displacement(x, y, z)
strain(x, y, z)
stress(x, y, z)
```

The final physical displacement field is

$$ \mathbf{u}(x,y,z). $$

---

## 10. Validation strategy

The implementation must be developed together with reproducible numerical validation.

### 10.1 Benchmark 1: Carrera-Giunta prismatic beam

Reference:

*Refined Beam Theories Based on a Unified Formulation*.

Purpose:

- verify the constant-section limit;
- verify the constitutive provider;
- verify the CUF basis;
- verify the `J` coefficients;
- verify the generic `K` construction;
- reproduce the fourth-order CUF algebraic system;
- reproduce the `N = 4` values of Table 2;
- reconstruct the complete numerical displacement field.

In this benchmark,

$$ \mathcal{S}(x)=\mathcal{S}_{\mathrm{ref}}. $$

Therefore the bridge must return longitudinally constant sectional coefficients.

### 10.2 Benchmark 2: tapered I-beam

Reference:

Patni et al., *Efficient modelling of beam-like structures with general non-prismatic, curved geometry*.

The first geometric target is Table 1.

The reference dimensions are:

```text
L       = 10000 mm
bf      = 250 mm
hf      = 16 mm
bw      = 6 mm
hw(0)   = 900 mm
hw(L)   = 100 mm
```

Purpose:

- verify a longitudinally varying sectional state;
- verify variable transverse domains;
- verify evaluation of `J(x)`;
- verify construction of `K(x)`;
- exercise the same bridge API used for the prismatic benchmark without introducing a benchmark-specific bridge.

The solver and the bridge must remain separate.

---

## 11. Development rules

The following rules apply throughout implementation.

1. Benchmark target values must never enter the model solution.
2. No fitting to reference numerical results is permitted.
3. No undocumented physical datum may be introduced.
4. Numerical approximations must be explicit and reproducible.
5. Every constitutive coefficient must be traceable to the constitutive provider.
6. Every generalized sectional coefficient must be traceable to the sectional state, constitutive field, and CUF basis.
7. Every `K` term must be traceable to the generalized CSF-CUF formulation.
8. The bridge must remain independent of the longitudinal solution method.
9. The solver must not contain section-specific geometry logic.
10. The same bridge implementation must support both prismatic and non-prismatic sectional states.
11. Reference values are used only for verification after the corresponding model output has been computed.

---

## 12. Initial implementation sequence

The initial development sequence is:

```text
1. ConstitutiveProvider API
2. Isotropic E-G constitutive provider
3. SectionProvider API
4. CUFBasis API
5. Maclaurin CUF basis implementation
6. Generic J API
7. J domain contribution API
8. Generic K_block API
9. Carrera-Giunta bridge regression tests
10. CUFProblem definition
11. Longitudinal solver
12. displacement / strain / stress recovery
13. complete Carrera-Giunta regression
14. tapered I-beam SectionProvider
15. variable J(x) verification
16. non-prismatic solver validation
```

---

## 13. Repository organization

The current development branch is

```text
feature/csf-cuf
```

The architecture document is intended to remain under

```text
docs/model/csf_cuf_architecture.md
```

The implementation and test directories will be fixed when the existing repository package structure is mapped to the CSF-CUF components.

This document must be updated whenever a stable architectural decision changes the bridge or solver contract.
