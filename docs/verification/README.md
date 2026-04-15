# Verification Benchmarks

This directory contains verification benchmarks for the CSF integration workflow.

The benchmarks are intended to provide readable numerical evidence that CSF section models remain consistent when evaluated through independent or complementary analysis paths. 

## Scope

The verification cases cover three main model classes:

- ordinary weighted polygonal geometries;
- slit-encoded closed thin-walled cells;
- open thin-walled wall geometries.

Each case compares the direct CSF result with the result obtained through the `csf_sp` integration layer and `sectionproperties`.

## Verification approach

The general procedure is:

1. define a CSF section field;
2. evaluate the section properties directly with CSF;
3. convert the same geometry through `csf_sp`;
4. evaluate the converted model with `sectionproperties`;
5. compare the resulting quantities at selected stations along `z`.

For ordinary geometric quantities, the comparison is expected to match at numerical precision.

For torsional quantities, the comparison is interpreted with a wider tolerance when CSF and `sectionproperties` use different formulations.

## Compared quantities

The geometric checks generally include:

- area;
- centroid coordinates;
- centroidal second moments of area;
- product of inertia;
- polar second moment;
- principal second moments;
- radii of gyration.

For thin-walled cases, the benchmarks also check that the expected CSF path is activated:

- `J_sv_cell` for closed `@cell` geometries;
- `J_sv_wall` for open `@wall` geometries.

## Role of the reports

The generated reports provide:

- the benchmark purpose;
- the model description;
- the comparison method;
- the tolerances used;
- station-wise numerical tables;
- final pass/fail summaries.

They are meant to be readable verification records, not just raw test logs.

## Relation to automated tests

These benchmarks can be used in two complementary ways:

- as documentation-oriented verification examples, producing detailed reports;
- as the basis for compact automated regression tests with numerical assertions.

The report-oriented versions are useful for review, publication support, and external technical discussion. The automated versions are useful for continuous integration and implementation safety.

## Interpretation

A successful benchmark run shows that:

- the CSF geometry model is evaluated consistently;
- the `csf_sp` conversion preserves the intended geometry and weights;
- `sectionproperties` returns results consistent with the direct CSF path;
- the selected thin-walled path, when present, is activated as expected.

These benchmarks are therefore cross-verification references for CSF and its `sectionproperties` integration.
