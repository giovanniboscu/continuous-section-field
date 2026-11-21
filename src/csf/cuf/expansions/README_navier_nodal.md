# Longitudinal basis plugins

The longitudinal approximation is isolated from the longitudinal finite-element
implementation.

```text
YAML
  longitudinal.basis
          |
          v
LongitudinalBasisPlugin registry
          |
          v
LongitudinalBasis API
          |
          v
Longitudinal FEM
```

The FEM does not import or branch on concrete shape-function families.

## YAML

The longitudinal FEM partition and the longitudinal basis are independent.
The partition must be declared in exactly one of two ways.

Uniform partition by element count:

```yaml
longitudinal:
  method: finite_element
  elements: 12
  basis: lagrange
  order: 6
  basis_options: {}
  gauss_order: 15
```

Explicit normalized element boundaries:

```yaml
longitudinal:
  method: finite_element
  element_boundaries: [0.0, 0.15, 0.30, 0.70, 1.0]
  basis: lagrange
  order: 6
  basis_options: {}
  gauss_order: 15
```

`elements` and `element_boundaries` are mutually exclusive and one of them is
required. `element_boundaries` are normalized longitudinal coordinates in
`[0, 1]`: the first value must be `0`, the last value must be `1`, and values
must be strictly increasing. The FEM discretizer maps them internally to the
physical CSF longitudinal domain.

`basis` selects the longitudinal shape-function plugin, and `order` is the
user-facing longitudinal approximation order **as interpreted by that plugin**.
The plugin does not own or modify the finite-element partition.

### Configuration parameters: approximation versus integration

| YAML key | Responsibility | Meaning |
| --- | --- | --- |
| `method: finite_element` | Discretization method | Keeps the existing longitudinal finite-element formulation and assembly. |
| `elements` / `element_boundaries` | FE mesh | Defines the longitudinal partition, independently of the basis. |
| `basis` | Longitudinal kinematics | Selects the family of longitudinal shape functions (for example, `lagrange` or `navier_nodal`). |
| `order` | Longitudinal kinematics | Selects the approximation order within the chosen family. Its interpretation is family-specific. |
| `basis_options` | Basis plugin | Optional family-specific settings; `navier_nodal` currently accepts no nonempty options. |
| `gauss_order` | **Numerical integration** | Requests the number of **Gauss-Legendre quadrature points per longitudinal element**. It does not select a shape-function family or change the number of longitudinal DOFs. |

The three notions of **transverse CUF expansion order**, **longitudinal
shape-function order**, and **longitudinal quadrature order** must be kept
separate. In particular, a Carrera-Giunta Table 9 test with transverse
Maclaurin order `N=10` may use `longitudinal.order: 6` and
`longitudinal.gauss_order: 30`: these are three independent parameters.

The term *Legendre* also requires care: **Gauss-Legendre** identifies the
numerical integration rule, not the longitudinal shape functions. A
Legendre-polynomial longitudinal approximation, if provided by a registered
plugin, is a separate choice through `longitudinal.basis`. The built-in
longitudinal bases documented here are `lagrange` and `navier_nodal`.

The solver may increase the effective number of Gauss points above the
requested value to satisfy the basis's integration requirement or numerical
recommendation; see [Numerical integration](#numerical-integration).

## Plugin contract

A longitudinal plugin registers a `LongitudinalBasisPlugin` and builds a
`LongitudinalBasis`. The mathematical API is:

- `order`
- `size`
- `polynomial_degree`: integer for a polynomial basis, or `None` for a
  non-polynomial basis (such as `navier_nodal`)
- `values(xi)`
- `derivatives_reference(xi)`
- `minimum_gauss_order(coefficient_polynomial_degree=...)`: returns a
  quadrature requirement for polynomial bases, or a conservative numerical
  recommendation for non-polynomial bases
- `LagrangeLongitudinalBasis.interpolation_values(xi, nodes)` (Lagrange plugin only): cardinal interpolation weights on caller-supplied nodes; does not modify the element basis
- optional `power_coefficients()` for compiled-field persistence

The current `finite_element` topology supports the explicit capability
`NodalC0LongitudinalBasis`, which additionally supplies `reference_nodes`.
This is a topology requirement of the current FEM adapter, not a Lagrange
assumption. Unsupported topologies are rejected explicitly.

Built-in plugins are discovered lazily from this directory. Adding another
module does not require a family-specific branch in the solver or registry.
The basis may recommend quadrature resolution, but the **numerical integration
is still performed by the solver**, not by the shape-function plugin.

## External basis file

`longitudinal.basis` may also be a Python file path. The existing built-in
syntax is unchanged:

```yaml
longitudinal:
  method: finite_element
  elements: 2
  basis: lagrange
  order: 6
```

To load a custom basis from outside the installed `src` tree, use a path:

```yaml
longitudinal:
  method: finite_element
  elements: 2
  basis: ./my_longitudinal_basis.py
  order: 6
```

Relative paths are resolved from the directory containing the case YAML. The
external file registers one `LongitudinalBasisPlugin` with the same
`register_longitudinal_basis_plugin()` API used by built-in modules.

The current `finite_element` implementation still requires
`NodalC0LongitudinalBasis`. External loading does not add non-nodal topology or
additional inter-element constraints.

See `cuf/external_longitudinal_basis/` for an external example numerically
equivalent to the built-in `lagrange` basis.

## Arbitrary-node interpolation (e.g. MITC tying points)

The built-in Lagrange plugin also exposes a dedicated operation for interpolation
on a separate set of nodes, without changing `values()`, `reference_nodes`, or
longitudinal displacement DOFs:

```python
import numpy as np

# 'basis' is the existing Lagrange longitudinal plugin instance,
# already obtained through the solver's plugin registry.
# Example: longitudinal polynomial order 3 -> three Barlow points.
barlow_points, _ = np.polynomial.legendre.leggauss(3)
xi_gauss = 0.37
weights = basis.interpolation_values(xi_gauss, barlow_points)

# B_at_barlow contains shear kinematic operator coefficients at each tying point.
# Once the solver has computed it, the MITC values at xi_gauss are:
# B_mitc = weights @ B_at_barlow
```

The selection of tying points is **not** a responsibility of the Lagrange
plugin. It is delegated to a separate numerical-method component in the solver.
This method computes only interpolation weights, not sectional integrals or
MITC-corrected stiffness blocks.

## Navier-harmonic nodal FE basis (`navier_nodal`)

The built-in `navier_nodal` plugin is a non-polynomial, trigonometric,
**nodal C0** longitudinal basis. It is compatible with the existing generic
`finite_element` method and all its usual nodal connectivity. For example:

```yaml
longitudinal:
  method: finite_element
  elements: 1
  basis: navier_nodal
  order: 6
  basis_options: {}
  gauss_order: 30
```

On each element use `t=(xi+1)/2`, with the reference coordinate
`xi` in `[-1, 1]`. For `order=N`, its function space is:

```text
span{1, cos(pi*t), sin(k*pi*t), k=1,...,N-1}
```

For `navier_nodal`, `order` is the **number of equal nodal intervals on each
element**, rather than a polynomial degree or the number of global Navier modes.
Thus `order: 6` means **seven longitudinal nodal points and seven local shape
functions** per displacement component on each element. Its approximation
space is specifically:

```text
span{1, cos(pi*t), sin(pi*t), sin(2*pi*t), sin(3*pi*t),
     sin(4*pi*t), sin(5*pi*t)}
```

Consequently **one element with `order >= 2` exactly contains both the first
Navier sine and cosine half-waves**. The cardinal shape functions are
constructed from a discrete-sine-transform basis with `N+1` real nodal DOFs,
so neighboring elements can share endpoint displacements. The shape values
and derivatives are analytic. The finite-element assembly and CUF fundamental
nucleus do not have a branch for this concrete family.

**This is not the component-specific, single-mode global Navier ansatz used in
Carrera and Giunta (2010).** It is a conforming FE space that includes their
first longitudinal modes; it also includes additional admissible functions,
and enforces supports through the usual FE constraints. To reproduce that
particular analytical solution exactly as an ansatz, a separate component-wise
modal topology would be necessary.

## Numerical integration

The longitudinal Gauss-Legendre rule integrates stiffness and force terms
involving longitudinal shape functions, their derivatives, and physical
coefficients provided by the CSF-CUF formulation. **It does not approximate
or construct the shape functions themselves.** Sectional quadrature is
configured and evaluated separately.

The longitudinal `gauss_order` refers to the **number of integration points
per longitudinal element**, not to the degree of a polynomial, the CUF
transverse order, or the number of harmonic modes. The solver uses the
following selection rule:

```text
longitudinal Gauss effective =
    max(longitudinal Gauss requested, longitudinal Gauss minimum)
```

The basis provides the minimum/recommended value through
`minimum_gauss_order(coefficient_polynomial_degree=...)`. The polynomial
coefficient estimate includes the engine's contributions from transverse
variation, geometry, and material properties.

- **Lagrange:** `polynomial_degree` is finite; the existing polynomial-degree
  Gauss-Legendre rule is retained.
- **Navier nodal:** `polynomial_degree=None`, since trigonometric functions
  have no finite polynomial degree. The current plugin recommends
  `3*order + 6 + ceil(D/2)` Gauss points, where `D` is the engine's
  estimated polynomial degree of the remaining coefficients. This is an
  *integration-resolution heuristic*, **not an exactness theorem**.

For a typical Table 9 case with `longitudinal.order: 6` and coefficient
degree `D=2`, the recommendation is **25**; a request for
`gauss_order: 30` therefore uses **30 integration points**. For a different
geometry, constitutive field, or expansion, the recommendation may change.

The November 2026 solver compatibility fix preserves `None` rather than
attempting `int(None)` in `_longitudinal_gauss_requirement()`, delegates the
quadrature estimate to the basis interface, and reports
`longitudinal degree estimate = non-polynomial` for `navier_nodal`. It does
**not** modify the fundamental CUF nucleus, the CSF physical model, or the
Lagrange quadrature rule.

Some constant-coefficient trigonometric integrals can be evaluated in closed
form, but the current general-purpose FE solver still evaluates them by
numerical quadrature. For `navier_nodal`, repeat calculations with increased
`gauss_order` to verify quadrature convergence; a large value such as `30`
is not by itself a general proof of exact integration.

## Present limitations

- `correctionMITC` / Barlow polynomial tying is unsupported for this basis.
- The polynomial-only, self-contained `.cuf.npz` compiled displacement
  checkpoint is skipped; standard in-memory displacement/stress recovery
  still works normally.
- For multiple elements, the trigonometric functions are defined locally on
  each element, not globally over the whole beam.

## Carrera-Giunta benchmark interpretation

The example above uses **one longitudinal FE element**, the `navier_nodal`
shape-function family, `order: 6` (seven local nodal functions), and
`gauss_order: 30` (30 requested integration points). The transverse
Maclaurin order is configured independently (for example, `N=10` in
Table 9). Changing the transverse order does not implicitly change the
longitudinal base or its integration point count.

The nodal trigonometric FE calculation is **not** the component-specific
modal Navier discretization in Carrera and Giunta (2010). Benchmark
comparisons must distinguish (i) published modal Navier values, (ii)
CSF-CUF FE with Lagrange longitudinal basis, and (iii) CSF-CUF FE with
`navier_nodal`. Close agreement of their displacement maxima is useful
verification evidence, but does not alone establish longitudinal mesh
convergence or numerical integration convergence.

For derivation, tests, and benchmark YAML variants, see the standalone
`NAVIER_NODAL_IMPLEMENTATION.md` supplied with the implementation package.
