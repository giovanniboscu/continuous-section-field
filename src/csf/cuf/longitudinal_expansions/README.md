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

`order` remains the user-facing longitudinal approximation order. `basis`
selects the plugin implementation. The basis plugin does not own or modify the
finite-element partition.

## Plugin contract

A longitudinal plugin registers a `LongitudinalBasisPlugin` and builds a
`LongitudinalBasis`. The mathematical API is:

- `order`
- `size`
- `polynomial_degree`
- `values(xi)`
- `derivatives_reference(xi)`
- `LagrangeLongitudinalBasis.interpolation_values(xi, nodes)` (Lagrange plugin only): cardinal interpolation weights on caller-supplied nodes; does not modify the element basis
- optional `power_coefficients()` for compiled-field persistence

The current `finite_element` topology supports the explicit capability
`NodalC0LongitudinalBasis`, which additionally supplies `reference_nodes`.
This is a topology requirement of the current FEM adapter, not a Lagrange
assumption. Unsupported topologies are rejected explicitly.

Built-in plugins are discovered lazily from this directory. Adding another
module does not require changes to the solver or registry.

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
