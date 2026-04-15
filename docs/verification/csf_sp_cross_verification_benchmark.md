# == DRAFFT ==
# CSF-sectionproperties Cross-Verification Benchmark

## Purpose

This verification benchmark checks the numerical consistency between CSF and the `csf_sp` integration layer, which converts a CSF-defined section field into a `sectionproperties` model.

The objective is to verify that a complex ordinary CSF geometry produces the same section properties when evaluated directly by CSF and when passed through `csf_sp` to `sectionproperties`.

This is a cross-verification test: CSF and `sectionproperties` follow different implementation paths, but they are expected to return the same homogenized geometric quantities for the same section model.

## Test case

The benchmark uses a non-prismatic cross-section varying along the longitudinal coordinate `z`.

The model includes:

- one irregular outer polygon with `weight = 1.0`;
- two explicit void polygons with `weight = 0.0`;
- one locally stiffer insert with `weight = 1.8`;
- one locally degraded insert with `weight = 0.35`;
- matching polygon topology between the start and end sections;
- multiple verification stations along `z`.

No `@cell` polygon is used in this benchmark. The test is limited to ordinary CSF geometry and weighted polygon composition.

## Compared quantities

At each verification station, the following quantities are compared:

- `A`
- `Cx`
- `Cy`
- `Ix`
- `Iy`
- `Ixy`
- `Ip`
- `I1`
- `I2`
- `rx`
- `ry`

The comparison is performed between:

1. the direct CSF section analysis;
2. the `sectionproperties` result obtained through `csf_sp`.

## Composite result extraction

The `csf_sp` interface builds a `sectionproperties` model with material data attached to the geometry. Since the section is handled by `sectionproperties` as a composite/material-based model, the corresponding composite result accessors are used.

In this benchmark, the CSF polygon weight acts as the effective material scale. Therefore, the stiffness-weighted quantities returned by `sectionproperties` are compared with the corresponding CSF homogenized quantities:

- `EA` is compared with `A`;
- `EIx` is compared with `Ix`;
- `EIy` is compared with `Iy`;
- `EIxy` is compared with `Ixy`.

## Torsion flags

Because this is an ordinary no-cell geometry test, the expected CSF torsion flags are:

```text
J_sv_cell = 0.0
J_sv_wall = 0.0
```

This confirms that no thin-walled `@cell` or `@wall` path is activated during the benchmark.

## Acceptance criteria

The benchmark checks the absolute and relative differences between CSF and `sectionproperties`.

Recommended tolerances:

```python
ABS_TOL = 1.0e-9
REL_TOL = 1.0e-7
```

A station passes when each compared quantity satisfies at least one of the following conditions:

```text
abs(delta) <= ABS_TOL
abs(relative_delta) <= REL_TOL
```

The benchmark passes only if all checked quantities pass at all stations.

## Role in the test suite

This benchmark can be used in two forms:

1. as an automated regression test, with compact numerical assertions;
2. as a verification example, with a detailed report for documentation and external review.

The automated test protects the `csf_sp` integration from regressions.

The verification example provides a readable numerical trace showing that the CSF geometry model and the `sectionproperties` conversion path remain consistent on a complex weighted, non-prismatic geometry.

## Interpretation

A successful run demonstrates that:

- CSF evaluates the weighted ordinary geometry correctly;
- `csf_sp` preserves the same geometry and weights during conversion;
- `sectionproperties` returns section properties consistent with the direct CSF path;
- non-prismatic interpolation along `z` remains consistent across both analysis routes.

This benchmark is therefore a suitable CSF-sectionproperties cross-verification benchmark for ordinary weighted geometries.
