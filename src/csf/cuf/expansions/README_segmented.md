# DRAFT
# Direct segmented CUF expansion law

A piecewise longitudinal expansion is declared directly in the case file.
It is not a transverse basis plugin and does not use
`longitudinal_lagrange_blend`.

```yaml
cuf:
  segments:
    - x_start_fraction: 0.0
      x_end_fraction: 0.4
      basis: scaled_lagrange
      order: 8

    - x_start_fraction: 0.4
      x_end_fraction: 0.6
      basis: scaled_lagrange
      order: 22

    - x_start_fraction: 0.6
      x_end_fraction: 1.0
      basis: scaled_lagrange
      order: 8
```

Every segment owns its transverse `basis`, `order`, and optional
`basis_options`.  There is deliberately no top-level `cuf.order` for a
segmented model.

The solver builds the child transverse expansions through the normal plugin
registry, exposes the longitudinal boundaries, splits the internal FE
partition when a real expansion change occurs, and applies the existing
perfect-bond constraints at those interfaces.

`longitudinal_lagrange_blend` remains available only for a genuinely smooth
Lagrange interpolation of transverse states.
