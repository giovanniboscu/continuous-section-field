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
- optional `power_coefficients()` for compiled-field persistence

The current `finite_element` formulation supports nodal longitudinal basis functions with C0 continuity between adjacent elements.
This is a topology requirement of the current FEM adapter, not a Lagrange
assumption. Unsupported topologies are rejected explicitly.

Built-in plugins are discovered lazily from this directory. Adding another
module does not require changes to the solver or registry.
