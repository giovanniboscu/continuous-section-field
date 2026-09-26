# `longitudinal_lagrange_blend`

This expansion plugin makes the transverse CUF basis explicitly dependent on
the CSF-CUF longitudinal coordinate `x`.

In CSF-CUF coordinates:

- `x` is the beam axis;
- `y,z` are the cross-section coordinates.

The plugin defines

```text
F_tau(x,y,z) = sum_i L_i(x) F_tau^(i)(x,y,z)
```

where `L_i(x)` are Lagrange interpolation weights through user-defined axial
states. For ordinary transverse child expansions, which do not themselves
depend on `x`, this is simply

```text
F_tau(x,y,z) = sum_i L_i(x) F_tau^(i)(y,z)
```

and the plugin supplies the exact longitudinal derivative

```text
dF_tau/dx = sum_i dL_i/dx F_tau^(i)
```

More generally, if a child expansion also depends on `x`, the full product
rule is used:

```text
dF_tau/dx = sum_i [dL_i/dx F_tau^(i) + L_i dF_tau^(i)/dx]
```

No solver special case is introduced. The existing generic `F(x,y,z)` / `dF/dx`
contract is used.

## YAML example

```yaml
cuf:
  basis: longitudinal_lagrange_blend
  order: 8
  basis_options:
    interpolation: lagrange
    size_policy: strict
    states:
      - x_fraction: 0.0
        basis: scaled_legendre
        order: 8

      - x_fraction: 1.0
        basis: scaled_maclaurin
        order: 8
```

`x_fraction` is mapped to the physical CSF longitudinal domain. A state may
instead use an explicit physical `x` coordinate.

`cuf.order` is the default child order when a state does not provide its own
`order`.

## Basis-size policy

The default is:

```yaml
size_policy: strict
```

All child expansions must then have the same number of basis functions. This
keeps the meaning of the global `tau` index unambiguous.

For an intentionally nested hierarchy, different child sizes can be admitted
with:

```yaml
size_policy: zero_pad
```

The largest child size becomes the global size and missing higher `tau` terms
are treated as zero at smaller states. Use this only when the selected child
bases have a compatible hierarchical `tau` ordering.

Example:

```yaml
cuf:
  basis: longitudinal_lagrange_blend
  order: 8
  basis_options:
    size_policy: zero_pad
    states:
      - x_fraction: 0.0
        basis: scaled_legendre
        order: 4
      - x_fraction: 1.0
        basis: scaled_legendre
        order: 8
```

This makes the higher Legendre terms vanish at the first state and emerge
continuously along `x` through the Lagrange weights.

## Relation to node-dependent kinematics

The plugin exposes the mathematical idea needed by CSF-CUF: the transverse
expansion itself is a field `F_tau(x,y,z)`.

The node-dependent-kinematics literature often keeps this axial dependence
implicit by writing separate cross-section functions at axial interpolation
nodes and multiplying them by longitudinal Lagrange functions. Here that
axial dependence is moved explicitly inside the expansion plugin so the core
only sees `F`, `dF/dy`, `dF/dz`, and `dF/dx`.
