# CSF-SP Complex Integration Verification Report

Source code: [`csf_sp_complex_integration_verification.py`](./csf_sp_complex_integration_verification.py)

## Purpose

This verification report checks the numerical consistency between CSF and the `csf_sp` integration path, which converts a CSF-defined section field into a `sectionproperties` model.

The objective is to verify that a complex ordinary CSF geometry produces the same homogenized section properties when evaluated directly by CSF and when converted through `csf_sp` to `sectionproperties`.

This is a cross-verification benchmark: CSF and `sectionproperties` follow different implementation paths, but they are expected to return the same section properties for the same weighted geometry.

## Test case

The benchmark uses a non-prismatic cross-section varying along the longitudinal coordinate `z`.

The model includes:

- one irregular outer polygon with `weight = 1.0`;
- two explicit void polygons with `weight = 0.0`;
- one locally stiffer insert with `weight = 1.8`;
- one locally degraded insert with `weight = 0.35`;
- matching polygon topology between the start and end sections;
- five verification stations along `z`.

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

A row passes when each compared quantity satisfies at least one of the following conditions:

```text
abs(delta) <= ABS_TOL
abs(relative_delta) <= REL_TOL
```

The benchmark passes only if all checked quantities pass at all stations.

## Results

Command:

```bash
python3 csf_sp_complex_integration_verification.py
```

### Station z = 0.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 7.043700000000e-01 | 7.043700000000e-01 | -1.998401444325e-15 | -2.837147e-15 | yes |
| Cx | -1.376232188575e-02 | -1.376232188575e-02 | -4.857225732735e-17 | 3.529365e-15 | yes |
| Cy | -2.348093568248e-02 | -2.348093568248e-02 | 4.510281037540e-17 | -1.920827e-15 | yes |
| Ix | 3.614475287650e-02 | 3.614475287650e-02 | -1.040834085586e-16 | -2.879627e-15 | yes |
| Iy | 5.577584276285e-02 | 5.577584276285e-02 | 1.873501354055e-16 | 3.358983e-15 | yes |
| Ixy | -1.955377116209e-04 | -1.955377116209e-04 | -7.155734338404e-18 | 3.659516e-14 | yes |
| Ip | 9.192059563935e-02 | 9.192059563935e-02 | 8.326672684689e-17 | 9.058550e-16 | yes |
| I1 | 5.577779024535e-02 | 5.577779024535e-02 | 1.942890293094e-16 | 3.483269e-15 | yes |
| I2 | 3.614280539400e-02 | 3.614280539400e-02 | -1.110223024625e-16 | -3.071768e-15 | yes |
| rx | 2.265281637717e-01 | 2.265281637717e-01 | -2.775557561563e-17 | -1.225259e-16 | yes |
| ry | 2.813990618952e-01 | 2.813990618952e-01 | 8.881784197001e-16 | 3.156295e-15 | yes |

Expected torsion flags:

```text
J_sv_cell: 0.0
J_sv_wall: 0.0
```

### Station z = 2.5

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 6.507703125000e-01 | 6.507703125000e-01 | 2.220446049250e-16 | 3.412027e-16 | yes |
| Cx | -1.201422252795e-02 | -1.201422252795e-02 | -4.770489558936e-16 | 3.970702e-14 | yes |
| Cy | -2.278881777925e-02 | -2.278881777925e-02 | 1.040834085586e-17 | -4.567302e-16 | yes |
| Ix | 3.086169492745e-02 | 3.086169492745e-02 | 1.734723475977e-17 | 5.620960e-16 | yes |
| Iy | 4.768952499226e-02 | 4.768952499226e-02 | -6.245004513517e-17 | -1.309513e-15 | yes |
| Ixy | -1.846575171269e-04 | -1.846575171268e-04 | -1.176359357147e-17 | 6.370493e-14 | yes |
| Ip | 7.855121991970e-02 | 7.855121991970e-02 | -4.163336342344e-17 | -5.300155e-16 | yes |
| I1 | 4.769155105822e-02 | 4.769155105822e-02 | -6.245004513517e-17 | -1.309457e-15 | yes |
| I2 | 3.085966886149e-02 | 3.085966886149e-02 | 1.734723475977e-17 | 5.621329e-16 | yes |
| rx | 2.177689818415e-01 | 2.177689818415e-01 | 0.000000000000e+00 | 0.000000e+00 | yes |
| ry | 2.707058443801e-01 | 2.707058443801e-01 | -2.220446049250e-16 | -8.202431e-16 | yes |

Expected torsion flags:

```text
J_sv_cell: 0.0
J_sv_wall: 0.0
```

### Station z = 5.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 5.993012500000e-01 | 5.993012500000e-01 | 5.551115123126e-16 | 9.262646e-16 | yes |
| Cx | -1.025999201848e-02 | -1.025999201848e-02 | -6.938893903907e-18 | 6.763060e-16 | yes |
| Cy | -2.210352785849e-02 | -2.210352785849e-02 | -4.510281037540e-17 | 2.040525e-15 | yes |
| Ix | 2.618271426189e-02 | 2.618271426189e-02 | 3.816391647149e-17 | 1.457600e-15 | yes |
| Iy | 4.051810647931e-02 | 4.051810647931e-02 | -5.551115123126e-17 | -1.370033e-15 | yes |
| Ixy | -1.717681279173e-04 | -1.717681279173e-04 | -7.399679827214e-18 | 4.307947e-14 | yes |
| Ip | 6.670082074119e-02 | 6.670082074119e-02 | -2.775557561563e-17 | -4.161205e-16 | yes |
| I1 | 4.052016432708e-02 | 4.052016432708e-02 | -6.245004513517e-17 | -1.541209e-15 | yes |
| I2 | 2.618065641411e-02 | 2.618065641411e-02 | 3.122502256758e-17 | 1.192675e-15 | yes |
| rx | 2.090185070210e-01 | 2.090185070210e-01 | 5.551115123126e-17 | 2.655801e-16 | yes |
| ry | 2.600171411264e-01 | 2.600171411264e-01 | -3.330669073875e-16 | -1.280942e-15 | yes |

Expected torsion flags:

```text
J_sv_cell: 0.0
J_sv_wall: 0.0
```

### Station z = 7.5

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 5.499628125000e-01 | 5.499628125000e-01 | 1.332267629550e-15 | 2.422469e-15 | yes |
| Cx | -8.498783203713e-03 | -8.498783203713e-03 | -1.127570259385e-16 | 1.326743e-14 | yes |
| Cy | -2.142593140294e-02 | -2.142593140294e-02 | 1.491862189340e-16 | -6.962881e-15 | yes |
| Ix | 2.205968566952e-02 | 2.205968566952e-02 | 2.428612866368e-17 | 1.100928e-15 | yes |
| Iy | 3.418965116089e-02 | 3.418965116089e-02 | 2.775557561563e-17 | 8.118122e-16 | yes |
| Ixy | -1.573942826912e-04 | -1.573942826912e-04 | 1.230569465771e-17 | -7.818387e-14 | yes |
| Ip | 5.624933683041e-02 | 5.624933683041e-02 | 4.857225732735e-17 | 8.635170e-16 | yes |
| I1 | 3.419169311152e-02 | 3.419169311152e-02 | 2.775557561563e-17 | 8.117637e-16 | yes |
| I2 | 2.205764371889e-02 | 2.205764371889e-02 | 2.428612866368e-17 | 1.101030e-15 | yes |
| rx | 2.002778856123e-01 | 2.002778856123e-01 | -1.387778780781e-16 | -6.929266e-16 | yes |
| ry | 2.493335225387e-01 | 2.493335225387e-01 | -1.942890293094e-16 | -7.792335e-16 | yes |

Expected torsion flags:

```text
J_sv_cell: 0.0
J_sv_wall: 0.0
```

### Station z = 10.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 5.027550000000e-01 | 5.027550000000e-01 | 1.221245327088e-15 | 2.429106e-15 | yes |
| Cx | -6.729586644257e-03 | -6.729586644257e-03 | -7.546047120499e-17 | 1.121324e-14 | yes |
| Cy | -2.075704534681e-02 | -2.075704534681e-02 | 2.428612866368e-17 | -1.170019e-15 | yes |
| Ix | 1.844649152890e-02 | 1.844649152890e-02 | -5.204170427930e-17 | -2.821225e-15 | yes |
| Iy | 2.863517673185e-02 | 2.863517673185e-02 | -2.081668171172e-17 | -7.269619e-16 | yes |
| Ixy | -1.420188784234e-04 | -1.420188784234e-04 | 6.884683795283e-18 | -4.847724e-14 | yes |
| Ip | 4.708166826075e-02 | 4.708166826075e-02 | -6.938893903907e-17 | -1.473799e-15 | yes |
| I1 | 2.863715593174e-02 | 2.863715593174e-02 | -2.081668171172e-17 | -7.269116e-16 | yes |
| I2 | 1.844451232901e-02 | 1.844451232901e-02 | -4.857225732735e-17 | -2.633426e-15 | yes |
| rx | 1.915484707796e-01 | 1.915484707796e-01 | -4.996003610813e-16 | -2.608219e-15 | yes |
| ry | 2.386556578459e-01 | 2.386556578459e-01 | -3.885780586188e-16 | -1.628195e-15 | yes |

Expected torsion flags:

```text
J_sv_cell: 0.0
J_sv_wall: 0.0
```

## Global summary

```text
stations checked: 5
properties per station: 11
maximum absolute delta: 1.998401444325e-15
maximum relative delta: 7.818387e-14
overall status: PASS
```

## Interpretation

The benchmark passes at all five stations.

The maximum absolute difference is `1.998401444325e-15` and the maximum relative difference is `7.818387e-14`, which are numerical round-off levels for this comparison.

This confirms that the ordinary weighted CSF geometry is preserved by the `csf_sp` conversion path and that `sectionproperties` returns results consistent with the direct CSF analysis for this complex non-prismatic weighted geometry.
