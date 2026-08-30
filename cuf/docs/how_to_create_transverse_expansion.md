# DRAFT

# How to Implement a Custom Transverse Expansion in CSF–CUF

## Purpose

This guide explains how to add a new transverse expansion to the CSF–CUF
solver without modifying the CUF core.

The solver is designed so that the transverse kinematic approximation is an
isolated component. A custom expansion is responsible for constructing and
evaluating its own basis. The CUF core only consumes the values returned by
the common basis interface.

The displacement field retains the unified form

```math
\mathbf{u}(x,y,z) = \sum_{\tau=1}^{M} F_\tau(x,y,z)\,\mathbf{u}_\tau(x).
```

For every requested term $\tau$ and physical point $(x,y,z)$, the
expansion supplies

```math
F_\tau, \qquad F_{\tau,y}, \qquad F_{\tau,z}.
```

The core remains responsible for sectional integration, fundamental nuclei,
longitudinal finite elements, global assembly, loads, constraints, the KKT
solution, and field recovery.

## Architecture

The runtime path is:

```text
case YAML
    |
    |  cuf.basis + cuf.order + cuf.basis_options
    v
expansion registry
    |
    v
selected expansion plugin
    |
    |-- section_provider
    |-- continuous_section_field
    |
    |  builds one CUFBasis implementation
    v
basis evaluation at (x,y,z)
    |
    |  F_tau, F_tau,y, F_tau,z
    v
CUF core
```

A custom expansion must not require a new solver or changes to the CUF
fundamental nuclei.

The expansion interface deliberately separates approximation logic from physical
model ownership. The plugin receives the parsed expansion options together with
two read-only model views. It may remain completely geometry-independent, use the
normalized `section_provider`, or inspect the complete `continuous_section_field`
when its mathematical definition requires richer section context. No
basis-specific interpretation is added to the solver core.

## Relevant Files

```text
csf/cuf/
├── core/
│   ├── basis.py
│   └── basis_plugins.py
├── expansions/
│   ├── __init__.py
│   ├── scaled_legendre.py
│   ├── scaled_maclaurin.py
│   └── scaled_maclaurin_tensor.py
├── numerics.py
└── solver/
    └── engine.py
```

To add a new expansion, normally create one new module below:

```text
csf/cuf/expansions/
```

Do not add an `if/elif` branch to `solver/engine.py` or
`core/basis_plugins.py`.

## Step 1 — Choose the YAML Name

Choose a unique, stable identifier. The self-contained example used throughout
this guide is called `my_expansion`.

It is a total-degree monomial basis in the physical transverse coordinates:

```math
F_{p,q}(y,z)=y^p z^q, \qquad p\ge0, \qquad q\ge0, \qquad p+q\le N.
```

The terms are ordered first by total degree and then by descending power of
`y`. For `order: 2`, the ordering is therefore:

```text
tau = 1  ->  (p,q) = (0,0)  ->  1
tau = 2  ->  (p,q) = (1,0)  ->  y
tau = 3  ->  (p,q) = (0,1)  ->  z
tau = 4  ->  (p,q) = (2,0)  ->  y^2
tau = 5  ->  (p,q) = (1,1)  ->  yz
tau = 6  ->  (p,q) = (0,2)  ->  z^2
```

The YAML selector is:

```yaml
cuf:
  basis: my_expansion
  order: 2
```

The identifier is the plugin name. It is not the Python class name.

This example requires no expansion-specific parameters, so `basis_options` is
omitted. The plugin will reject a non-empty `basis_options` mapping rather than
silently ignoring it.

## Step 2 — Implement `CUFBasis`

The mandatory interface is defined by `CUFBasis` in `core/basis.py`.

For the example above, the basis implementation is complete and contains no
placeholder evaluation methods:

```python
from csf.cuf.core.basis import CUFBasis


class MyExpansionBasis(CUFBasis):
    """Total-degree monomial basis in the physical y-z coordinates."""

    def __init__(self, *, order: int) -> None:
        if not isinstance(order, int):
            raise TypeError("my_expansion order must be an integer")
        if order < 1:
            raise ValueError("my_expansion order must be >= 1")

        self._order = order
        self._terms = tuple(
            (p, degree - p)
            for degree in range(order + 1)
            for p in range(degree, -1, -1)
        )

    @property
    def order(self) -> int:
        return self._order

    @property
    def size(self) -> int:
        return len(self._terms)

    def definition(self, tau: int) -> tuple[int, int]:
        """Return the (p,q) exponents associated with one CUF index."""
        return self._term(tau)

    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        p, q = self._term(tau)
        return float((float(y) ** p) * (float(z) ** q))

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        p, q = self._term(tau)
        y = float(y)
        z = float(z)

        if direction == "y":
            if p == 0:
                return 0.0
            return float(p * (y ** (p - 1)) * (z ** q))

        if direction == "z":
            if q == 0:
                return 0.0
            return float(q * (y ** p) * (z ** (q - 1)))

        raise ValueError("direction must be 'y' or 'z'")

    def _term(self, tau: int) -> tuple[int, int]:
        if not isinstance(tau, int):
            raise TypeError("tau must be an integer")
        if not 1 <= tau <= self.size:
            raise IndexError(f"tau must be in 1..{self.size}, got {tau}")
        return self._terms[tau - 1]
```

For `order = N`, this construction gives

```math
M=\frac{(N+1)(N+2)}{2}.
```

The optional argument `x` is accepted because it belongs to the common
interface, but this particular example does not use it: its functions are
explicitly functions of the physical coordinates `y` and `z` only.

### Meaning of `size`

`size` is the total number $M$ of transverse expansion functions.

For each longitudinal generalized node, the solver creates three displacement
unknowns for every transverse term. Therefore the expansion must define a
deterministic ordering

```math
\tau=1,2,\ldots,M.
```

The following must remain stable throughout a single analysis:

- `size`;
- the meaning of each index `tau`;
- the ordering of the terms.

Internal geometric data may vary with $x$, but term $\tau$ must retain the
same logical identity at every longitudinal station.

### Scalar return values

The mandatory methods evaluate one term at a time. They return scalars:

```python
F_tau = basis.value(tau, y, z, x=x)
Fy_tau = basis.derivative(tau, "y", y, z, x=x)
Fz_tau = basis.derivative(tau, "z", y, z, x=x)
```

They must return finite real numbers for every valid query.

### The evaluation point

The solver chooses the physical point $(x,y,z)$. The expansion must evaluate
its functions at exactly that point. It must not silently replace or move the
solver's quadrature point.

The same interface is used during:

- sectional integration;
- displacement recovery;
- strain and stress recovery;
- physical pointwise boundary constraints.

### Use of `x`

`x` is optional in the common evaluation signature because many expansions
depend only on the transverse coordinates `(y,z)`. A section-aware expansion
may require the longitudinal coordinate explicitly:

```python
if x is None:
    raise ValueError("section_dependent_expansion requires the longitudinal coordinate x")
```

A section-aware expansion may retain either model interface supplied by its
plugin builder. For normalized sectional information it may use:

```python
domains = self._section_provider.domains(float(x))
```

When it needs the complete CSF model, it may instead use:

```python
section = self._continuous_section_field.section(float(x))
```

These are complementary interfaces. The expansion decides which level of model
information it requires. Geometry and material definitions remain owned by the
CSF model; the expansion only reads and interprets them for its own approximation.

The expansion, not the CUF core, is responsible for interpreting the current
section state and constructing any internal points, mappings, topology, or cached
metadata that it requires.

## Step 3 — Validate `basis_options`

The plugin receives `basis_options` as a normal Python dictionary. The example
basis needs no additional configuration, so every non-empty mapping is
rejected explicitly:

```python
def _reject_options(options):
    if options:
        raise ValueError(
            "my_expansion does not accept cuf.basis_options; "
            f"received {sorted(options)}"
        )
```

This keeps the example deterministic: its complete mathematical definition is
`order` plus the fixed monomial ordering defined above.

For another expansion that does need extra parameters, validate all supported
keys inside the plugin before constructing the basis. Do not read the YAML file
directly from the expansion; the case parser has already read it and passes the
mapping to the selected plugin.

Do not duplicate CSF geometry or material definitions inside
`basis_options`. Geometry and material remain in the CSF model.

## Step 4 — Implement the Plugin Builder

The builder connects the generic plugin interface to the specific basis class.
Every expansion builder receives both `section_provider` and
`continuous_section_field`. They provide two complementary levels of access
to the physical model:

- `section_provider` exposes the normalized sectional interface used by the CUF solver;
- `continuous_section_field` exposes the complete Continuous Section Field model.

A simple expansion may use neither of them. A section-aware expansion may retain
either or both in its basis object and query them when evaluating at a given `x`.
The example below is geometry-independent, so it deliberately ignores both:

```python
def _build(
    *,
    order,
    section_provider,
    continuous_section_field,
    options,
):
    _reject_options(options)
    del section_provider
    del continuous_section_field
    return MyExpansionBasis(order=order)
```

`MyExpansionBasis` performs the order validation itself. The builder therefore
only validates plugin-specific options and constructs the ready-to-use basis.

A different expansion may pass `section_provider`, `continuous_section_field`,
or both to its basis constructor. This allows the expansion to inspect the
current physical section or other information carried by the complete CSF model
without adding expansion-specific logic to the CUF core. The builder and the
basis must treat the supplied model context as read-only and must not modify
the CSF model or global solver state.

## Step 5 — Declare the Section Quadrature Requirement

Each expansion must declare a conservative minimum number of transverse Gauss
points. For this polynomial example, use:

```python
def _section_gauss_minimum(basis):
    if not isinstance(basis, MyExpansionBasis):
        raise TypeError("my_expansion received an incompatible basis")
    return int(basis.order) + 1
```

This function returns a positive integer. The solver uses

```python
effective_order = max(
    requested_section_gauss_order,
    plugin.minimum_section_gauss_order(basis),
)
```

The correct rule depends on the approximation space and on the sectional
integration method. Derive it from the highest degree or complexity of the
products used by the CUF nuclei, including combinations such as

```math
F_\tau F_s, \quad F_{\tau,y}F_s, \quad F_{\tau,z}F_{s,y}, \quad F_{\tau,y}F_{s,y}, \quad F_{\tau,z}F_{s,z}.
```

If no exact polynomial rule is available, return a documented conservative
minimum and verify it numerically by increasing the Gauss order.

Do not put a basis-name condition in the solver engine.

## Step 6 — Declare the Longitudinal Degree Contribution

The solver estimates a safe longitudinal quadrature order. The expansion owns
the contribution caused by its transverse basis when the CSF section varies
along $x$.

For this example, implement:

```python
def _longitudinal_transverse_degree(basis):
    if not isinstance(basis, MyExpansionBasis):
        raise TypeError("my_expansion received an incompatible basis")
    return 2 * int(basis.order)
```

This value is not necessarily the polynomial degree of one basis function. It
is the conservative longitudinal degree contribution associated with the
transverse products appearing in the sectional coefficients when the section
changes along $x$.

The plugin must return a non-negative integer.

The solver adds this contribution to the independently determined degrees
associated with:

- the varying sectional measure;
- the material law;
- the longitudinal finite-element shape functions.

If the expansion is not polynomial in the relevant variables, define and
document a safe integration requirement appropriate to its formulation. Do
not hide under-integration by returning zero without justification.

## Step 7 — Register the Expansion

Create exactly one new file:

```text
csf/cuf/expansions/my_expansion.py
```

For this example, the file is completely self-contained. It does not import a
second `my_expansion_basis.py` module and it contains no undefined helper
methods:

```python
# Version: CSF-CUF custom transverse expansion example v1 - 2026-08-29
"""Self-contained total-degree monomial transverse expansion example."""

from csf.cuf.core.basis import CUFBasis
from csf.cuf.core.basis_plugins import (
    CUFBasisPlugin,
    register_cuf_basis_plugin,
)


class MyExpansionBasis(CUFBasis):
    """Total-degree monomial basis in the physical y-z coordinates."""

    def __init__(self, *, order: int) -> None:
        if not isinstance(order, int):
            raise TypeError("my_expansion order must be an integer")
        if order < 1:
            raise ValueError("my_expansion order must be >= 1")

        self._order = order
        self._terms = tuple(
            (p, degree - p)
            for degree in range(order + 1)
            for p in range(degree, -1, -1)
        )

    @property
    def order(self) -> int:
        return self._order

    @property
    def size(self) -> int:
        return len(self._terms)

    def definition(self, tau: int) -> tuple[int, int]:
        return self._term(tau)

    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        p, q = self._term(tau)
        return float((float(y) ** p) * (float(z) ** q))

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        p, q = self._term(tau)
        y = float(y)
        z = float(z)

        if direction == "y":
            if p == 0:
                return 0.0
            return float(p * (y ** (p - 1)) * (z ** q))

        if direction == "z":
            if q == 0:
                return 0.0
            return float(q * (y ** p) * (z ** (q - 1)))

        raise ValueError("direction must be 'y' or 'z'")

    def _term(self, tau: int) -> tuple[int, int]:
        if not isinstance(tau, int):
            raise TypeError("tau must be an integer")
        if not 1 <= tau <= self.size:
            raise IndexError(f"tau must be in 1..{self.size}, got {tau}")
        return self._terms[tau - 1]


def _reject_options(options):
    if options:
        raise ValueError(
            "my_expansion does not accept cuf.basis_options; "
            f"received {sorted(options)}"
        )


def _build(
    *,
    order,
    section_provider,
    continuous_section_field,
    options,
):
    _reject_options(options)
    del section_provider
    del continuous_section_field
    return MyExpansionBasis(order=order)


def _section_gauss_minimum(basis):
    if not isinstance(basis, MyExpansionBasis):
        raise TypeError("my_expansion received an incompatible basis")
    return int(basis.order) + 1


def _longitudinal_transverse_degree(basis):
    if not isinstance(basis, MyExpansionBasis):
        raise TypeError("my_expansion received an incompatible basis")
    return 2 * int(basis.order)


register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="my_expansion",
        builder=_build,
        section_gauss_minimum=_section_gauss_minimum,
        longitudinal_transverse_degree=(
            _longitudinal_transverse_degree
        ),
    )
)
```

The complete implementation required by this worked example is therefore in a
single file. Both `section_provider` and `continuous_section_field` appear in
`_build()` because they are part of the common plugin contract. This basis is
geometry-independent and intentionally uses neither.

Modules under `csf.cuf.expansions` are discovered automatically. No edit to
the central registry is required.

Plugin names must be unique. Duplicate registration raises an error.

### Self-contained smoke test

After creating `my_expansion.py`, run:

```python
from csf.cuf.expansions.my_expansion import MyExpansionBasis


basis = MyExpansionBasis(order=2)

assert basis.size == 6
assert basis.definition(1) == (0, 0)
assert basis.definition(2) == (1, 0)
assert basis.definition(3) == (0, 1)
assert basis.definition(4) == (2, 0)
assert basis.definition(5) == (1, 1)
assert basis.definition(6) == (0, 2)

# At y=2 and z=3 the basis is [1, 2, 3, 4, 6, 9].
expected = (1.0, 2.0, 3.0, 4.0, 6.0, 9.0)
computed = tuple(
    basis.value(tau, 2.0, 3.0)
    for tau in range(1, basis.size + 1)
)
assert computed == expected

# tau=5 is yz, so d(yz)/dy=z and d(yz)/dz=y.
assert basis.derivative(5, "y", 2.0, 3.0) == 3.0
assert basis.derivative(5, "z", 2.0, 3.0) == 2.0

print("my_expansion self-contained smoke test: PASSED")
```

The test uses only the class defined in the new expansion module and checks the
same `tau` ordering documented in Step 1.

## Step 8 — Optional Vectorized Evaluation

The scalar methods are sufficient for correctness. An expansion may optionally
provide

```python
def values(
    self,
    y: float,
    z: float,
    *,
    x: float | None = None,
):
    ...
```

It must return a NumPy array with shape

```python
(self.size,)
```

and must be algebraically equivalent to:

```python
np.asarray([
    self.value(tau, y, z, x=x)
    for tau in range(1, self.size + 1)
])
```

Implement this only after the scalar path is correct and tested.

## Step 9 — Optional Compiled Factor Evaluation

For repeated sectional integration, an expansion may optionally implement
`compile_factors(factors)`.

Each input item is:

```python
(tau, derivative)
```

where `derivative` is one of:

```python
None
"y"
"z"
```

The returned callable must evaluate the requested factors in exactly the same
order and return an array of shape `(len(factors),)`.

This is a performance extension, not a correctness requirement. If an
expansion depends on $x$ or on section-specific state and the compiled path
cannot reproduce that dependence exactly, do not implement it. The core will
use the generic scalar fallback.

## Step 10 — Optional Closed-Form Diagnostic Support

The normal CUF solution uses numerical sectional integration and requires only
`value()` and `derivative()`.

The experimental closed-form sectional comparator additionally expects
monomial metadata such as:

```python
exponents(tau)
scales
```

These members are not mandatory. Implement them only if every basis function
has the exact representation expected by that diagnostic.

A valid expansion can operate fully without closed-form diagnostic support.

## Rules for a Section-Dependent Expansion

If the expansion derives internal data from the physical model at `x`, it owns
all of the following responsibilities:

- obtaining the required current state from `section_provider` and/or
  `continuous_section_field`;
- constructing or retrieving its internal points and topology;
- evaluating the correct term at the solver's physical point;
- evaluating exact or consistently derived $y$- and $z$-derivatives;
- keeping `size` constant during the analysis;
- keeping every `tau` logically consistent along $x$;
- managing its own cache without mixing data belonging to different values of
  $x$;
- returning zero outside a term's support when using local functions;
- rejecting evaluation when the required longitudinal context is missing.

The CUF core must not know how those tasks are performed.

## Continuity and Piecewise Functions

The interface does not require the basis to be one global polynomial.
Piecewise functions are permitted provided that the approximation satisfies
the continuity requirements of the chosen formulation.

For a standard weak elasticity formulation, a globally $C^0$ displacement
field is normally sufficient. First derivatives may be discontinuous across
internal cell boundaries. The expansion is responsible for returning the
correct derivative on each piece.

If derivative discontinuities cross an integration region, the declared
quadrature strategy must still integrate the piecewise products reliably.
This may require section-aware subdivision or another integration rule. Do not
assume that merely increasing the polynomial Gauss order always resolves a
piecewise integration problem.

## Loads, Constraints, and Recovery

The expansion is used outside stiffness integration as well.

### Loads

Generalized loads are produced by projecting physical loads onto the same
transverse basis. Ensure that `value()` is valid wherever the problem adapter
evaluates or integrates the load.

### Pointwise constraints

A physical end constraint has the form

```math
u_i(x_{\mathrm{end}},y,z) = \sum_\tau F_\tau(x_{\mathrm{end}},y,z) q_{\tau i}^{\mathrm{end}}.
```

An expansion requiring $x$ must therefore also be evaluable at both
longitudinal ends. When constructing `PointwiseBoundaryConstraintMapper`, an
adapter should provide `x_start` and `x_end` for such a basis.

### Recovery

Displacement recovery uses `value()`. Strain and stress recovery use
`value()` together with both transverse derivatives. A basis that works only
during assembly but fails during arbitrary field queries is incomplete.

## Validation Checklist

### 1. Registration

```python
from csf.cuf.core.basis_plugins import (
    available_cuf_basis_plugins,
)
from csf.cuf.expansions.my_expansion import MyExpansionBasis


assert "my_expansion" in available_cuf_basis_plugins()

basis = MyExpansionBasis(order=2)
assert basis.size == 6
assert basis.definition(5) == (1, 1)
assert basis.value(5, 2.0, 3.0) == 6.0
assert basis.derivative(5, "y", 2.0, 3.0) == 3.0
assert basis.derivative(5, "z", 2.0, 3.0) == 2.0
```

### 2. Configuration validation

Verify:

- defaults work when `basis_options` is omitted;
- every supported option is type-checked;
- invalid ranges are rejected;
- unknown keys are rejected;
- malformed YAML mappings produce clear errors.

### 3. Kronecker or analytical properties

Test every mathematical property specific to the basis. Examples include:

- partition of unity;
- Kronecker-delta interpolation;
- polynomial completeness;
- symmetry;
- exact reproduction of rigid-body modes;
- exact analytical derivatives.

### 4. Scalar/vectorized equivalence

If `values()` exists, compare it against all scalar calls at many points.
The difference should be zero or within an explicitly justified floating-point
tolerance.

### 5. Derivative verification

Compare analytical derivatives against an independent check at interior
points. A centered finite difference may be used only as a test oracle, not as
the production derivative implementation.

### 6. Quadrature convergence

For representative sectional products, increase the sectional Gauss order and
verify stabilization. Confirm that the plugin minimum is conservative.

Repeat the test for prismatic and variable sections.

### 7. Matrix properties

Verify:

- finite matrix entries;
- expected symmetry;
- no unintended zero-energy modes;
- constraint matrix rank;
- KKT residual;
- conditioning trends as the expansion order increases.

### 8. Physical benchmarks

Use at least:

- one bending problem;
- one torsion problem;
- one prismatic section;
- one variable section;
- one independent analytical or FEM reference.

### 9. Recovery

Query displacement, strain, and stress at arbitrary interior and boundary
points. Assembly success alone is not sufficient.

### 10. Regression isolation

Adding a new expansion must not change existing expansion results. Re-run at
least one validated Maclaurin and one validated Legendre case and compare:

- `basis.size` and term ordering;
- effective transverse and longitudinal Gauss orders;
- KKT shape and number of nonzeros;
- checkpoint hashes for matrix structure, matrix data, and RHS;
- residuals;
- final displacements.

## Common Errors

### Editing the solver for every basis

Incorrect:

```python
if case.cuf.basis == "my_expansion":
    ...
```

Put construction and numerical requirements in the plugin instead.

### Reading the YAML directly inside the basis

The basis should receive parsed `options`. It should not reopen the case file.

### Changing `size` with `x`

The global DOF layout is built from one fixed `size`. Changing it during
integration invalidates assembly.

### Renumbering `tau` with `x`

Coordinates or internal geometry may change, but the logical identity of a
generalized unknown must not change.

### Ignoring derivatives

Correct displacement values alone are insufficient. The CUF strain operator
uses both $F_{\tau,y}$ and $F_{\tau,z}$.

### Implementing only the assembly path

The same basis must work in constraints and post-processing.

### Underestimating quadrature

The plugin owns both sectional and longitudinal integration requirements.
An underestimated value can produce apparently converged but incorrect
results.

### Premature optimization

Implement and validate the scalar interface first. Add `values()` and
`compile_factors()` only after exact equivalence has been demonstrated.

## Minimal Completion Criteria

A custom expansion is ready for use only when:

1. its module is discovered and registered automatically;
2. its YAML name selects the correct plugin;
3. all options are validated locally;
4. `size`, `value()`, and `derivative()` satisfy the common contract;
5. term numbering remains stable along $x$;
6. sectional and longitudinal quadrature requirements are declared;
7. assembly, constraints, displacement recovery, and strain/stress recovery
   all work;
8. numerical and physical validation cases pass;
9. existing Maclaurin and Legendre regressions remain unchanged;
10. no basis-specific branch has been added to the CUF core.

Once these conditions are satisfied, the expansion is a self-contained CSF–CUF
component and can evolve independently of the solver core.
