# Thin-Wall Verification Cases (`@wall`)

This directory contains validation and regression cases for the CSF `@wall`
thin-wall torsional formulation.

The purpose of these tests is to evaluate the consistency of the CSF open
thin-walled Saint-Venant torsional indicator, `J_sv_wall`, against an
independent finite-element section analysis.

The cases are intended to support reproducible verification of the `@wall`
classification used for open thin-walled components.

## Included Cases

The verification set contains the following geometry files:

- `c-shape.yaml`
- `e-shape.yaml`
- `f-shape.yaml`
- `h1-shaped.yaml`
- `h-rot-shaped.yaml`
- `i-shaped.yaml`
- `l-shape.yaml`
- `m2-shape.yaml`
- `m-shape.yaml`
- `t-shapep.yaml`
- `t-uniqshape.yaml`

Together, these files cover several representative open thin-wall layouts,
including channel-like, E/F/H/I/L/T-shaped sections, rotated configurations,
and multi-branch wall geometries.

## Verification Strategy

For each geometry:

1. CSF computes the thin-wall torsional indicator `J_sv_wall`;
2. an independent section analysis is executed through `sectionproperties`;
3. the torsional quantities are compared;
4. the relative difference is evaluated against a prescribed tolerance.

The same action workflow is reused across the cases so that the reported
quantities remain consistent.

## Generated Outputs

The test runner produces:

- per-case CSF analysis reports;
- per-case `sectionproperties` reports;
- a CSV summary suitable for automated processing;
- a formatted text summary for direct inspection.

Typical reported quantities include:

- geometric properties;
- centroid coordinates;
- inertia tensors;
- section moduli;
- thin-wall torsional indicators;
- comparison errors against the reference solution.

## Demonstrative Failure Cases

Some geometries are intentionally retained even when they exceed the selected
verification tolerance.

These cases are not accidental failures. They are included as demonstrative
stress cases to show where the simplified open thin-wall approximation becomes
less representative of the finite-element torsional response.

In particular, compact, strongly branched, or locally non-uniform wall layouts
may produce larger deviations. Keeping these cases in the test set documents
the practical limits of the `@wall` indicator and prevents the verification
suite from containing only favourable examples.

## Interpretation

The test set includes both positive verification cases and demonstrative failure
cases. Passing cases support the regular use of the `@wall` formulation for
representative open thin-walled layouts. Failing cases identify configurations
where the simplified indicator should be interpreted with caution or checked
against a higher-fidelity section analysis.

This makes the directory suitable both for regression testing and for
supporting the numerical verification material referenced in the paper.
