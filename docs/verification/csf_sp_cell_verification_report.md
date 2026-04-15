# CSF-SP @cell Verification Report

## Purpose

This verification report checks the consistency of the CSF `@cell` workflow against the `csf_sp` integration path and `sectionproperties`.

The test verifies two separate aspects:

1. **Geometric consistency**  
   A direct CSF ordinary reference model is compared against the `sectionproperties` model generated from a slit-encoded `@cell` polygon through `csf_sp`.

2. **Torsional consistency**  
   CSF `J_sv_cell` is compared with the `sectionproperties` composite torsion result `e.j`.

The geometric comparison is expected to match at numerical precision. The torsional comparison is expected to be close, but not identical, because CSF and `sectionproperties` use different torsional formulations.

## Model

The verification uses two equivalent CSF representations of the same section:

### 1. Ordinary reference geometry

The ordinary CSF model uses:

- one outer polygon with `weight = 1.0`;
- one inner void polygon with `weight = 0.0`;
- no `@cell` tag.

This model is used as the geometric reference for:

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

### 2. Slit-encoded `@cell` geometry

The `@cell` model uses one slit-encoded polygon containing:

- the outer loop;
- a repeated outer start vertex;
- the inner loop tail;
- a repeated inner start vertex.

This model is passed to `csf_sp`, which builds the corresponding `sectionproperties` geometry. It is also used by CSF to compute `J_sv_cell`.

## Compared quantities

At each station, the report compares:

| Group | CSF quantity | sectionproperties quantity |
|---|---|---|
| Geometry | `A` | `EA` |
| Geometry | `Cx` | `Cx` |
| Geometry | `Cy` | `Cy` |
| Geometry | `Ix` | `EIx` |
| Geometry | `Iy` | `EIy` |
| Geometry | `Ixy` | `EIxy` |
| Geometry | `Ip` | `EIx + EIy` |
| Geometry | `I1` | principal value from `EIx`, `EIy`, `EIxy` |
| Geometry | `I2` | principal value from `EIx`, `EIy`, `EIxy` |
| Geometry | `rx` | `sqrt(EIx / EA)` |
| Geometry | `ry` | `sqrt(EIy / EA)` |
| Torsion | `J_sv_cell` | `e.j` |

The `csf_sp` model is handled by `sectionproperties` as a composite/material-based section. The composite accessors are therefore used. In this verification, the effective material scale is `E = 1.0`, so the stiffness-weighted quantities are numerically comparable to the corresponding CSF geometric quantities.

## Acceptance criteria

The geometric comparison uses strict numerical tolerances:

```python
GEOM_ABS_TOL = 1.0e-9
GEOM_REL_TOL = 1.0e-7
```

The torsional comparison uses a looser tolerance:

```python
TORSION_ABS_TOL = 1.0e-8
TORSION_REL_TOL = 1.0e-1
```

The looser torsion tolerance is intentional. CSF computes `J_sv_cell` through its `@cell` Saint-Venant thin-walled/Bredt-type path, while `sectionproperties` computes `e.j` numerically.

A row passes when at least one of the following conditions is true:

```text
abs(delta) <= absolute_tolerance
abs(relative_delta) <= relative_tolerance
```

## Results

The verification was run at three stations:

```text
z = 0.0
z = 5.0
z = 10.0
```

## Station z = 0.0

### Geometric check

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 5.380000000000e-02 | 5.380000000000e-02 | -4.857225732735e-17 | -9.028301e-16 | yes |
| Cx | -9.910161090458e-03 | -9.910161090459e-03 | 1.387778780781e-17 | -1.400359e-15 | yes |
| Cy | -5.985130111524e-03 | -5.985130111524e-03 | -5.204170427930e-18 | 8.695167e-16 | yes |
| Ix | 6.283877881041e-04 | 6.283877881041e-04 | 4.336808689942e-19 | 6.901485e-16 | yes |
| Iy | 5.033645657786e-04 | 5.033645657786e-04 | -2.168404344971e-19 | -4.307821e-16 | yes |
| Ixy | 4.938094795539e-06 | 4.938094795539e-06 | 8.131516293641e-20 | 1.646691e-14 | yes |
| Ip | 1.131752353883e-03 | 1.131752353883e-03 | 2.168404344971e-19 | 1.915971e-16 | yes |
| I1 | 6.285825267823e-04 | 6.285825267823e-04 | 4.336808689942e-19 | 6.899347e-16 | yes |
| I2 | 5.031698271004e-04 | 5.031698271004e-04 | -2.168404344971e-19 | -4.309488e-16 | yes |
| rx | 1.080743744412e-01 | 1.080743744412e-01 | 9.714451465470e-17 | 8.988672e-16 | yes |
| ry | 9.672754878921e-02 | 9.672754878921e-02 | 2.775557561563e-17 | 2.869459e-16 | yes |

### Torsion check

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| J_sv_cell | 1.062409393301e-03 | 1.042027764982e-03 | 2.038162831885e-05 | 1.955958e-02 | yes |

Expected CSF torsion flags:

```text
J_sv_cell = (0.0010624093933009307, 0.05815589402152802)
J_sv_wall = 0.0
```

## Station z = 5.0

### Geometric check

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 4.693137500000e-02 | 4.693137500000e-02 | -2.775557561563e-17 | -5.914077e-16 | yes |
| Cx | -9.087906721960e-03 | -9.087906721960e-03 | -5.030698080333e-17 | 5.535596e-15 | yes |
| Cy | -6.635096634892e-03 | -6.635096634892e-03 | 3.209238430557e-17 | -4.836762e-15 | yes |
| Ix | 4.759304908935e-04 | 4.759304908935e-04 | 1.084202172486e-19 | 2.278068e-16 | yes |
| Iy | 3.778090642033e-04 | 3.778090642033e-04 | -2.710505431214e-19 | -7.174273e-16 | yes |
| Ixy | 2.613078530387e-06 | 2.613078530387e-06 | 6.013933925506e-20 | 2.301475e-14 | yes |
| Ip | 8.537395550967e-04 | 8.537395550967e-04 | -2.168404344971e-19 | -2.539890e-16 | yes |
| I1 | 4.760000306857e-04 | 4.760000306857e-04 | 5.421010862428e-20 | 1.138868e-16 | yes |
| I2 | 3.777395244111e-04 | 3.777395244111e-04 | -2.710505431214e-19 | -7.175594e-16 | yes |
| rx | 1.007024705655e-01 | 1.007024705655e-01 | 4.163336342344e-17 | 4.134294e-16 | yes |
| ry | 8.972315722127e-02 | 8.972315722127e-02 | -1.387778780781e-17 | -1.546734e-16 | yes |

### Torsion check

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| J_sv_cell | 8.008614568896e-04 | 7.852298462031e-04 | 1.563161068650e-05 | 1.990705e-02 | yes |

Expected CSF torsion flags:

```text
J_sv_cell = (0.000800861456889579, 0.054580108121773684)
J_sv_wall = 0.0
```

## Station z = 10.0

### Geometric check

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 4.053050000000e-02 | 4.053050000000e-02 | -1.387778780781e-17 | -3.424036e-16 | yes |
| Cx | -8.266457770486e-03 | -8.266457770486e-03 | 2.428612866368e-17 | -2.937912e-15 | yes |
| Cy | -7.251131863658e-03 | -7.251131863658e-03 | 6.938893903907e-18 | -9.569394e-16 | yes |
| Ix | 3.529385494377e-04 | 3.529385494377e-04 | -5.421010862428e-20 | -1.535965e-16 | yes |
| Iy | 2.773537739282e-04 | 2.773537739282e-04 | -1.084202172486e-19 | -3.909095e-16 | yes |
| Ixy | 9.824524845831e-07 | 9.824524845831e-07 | -2.117582368136e-21 | -2.155404e-15 | yes |
| Ip | 6.302923233659e-04 | 6.302923233659e-04 | -1.084202172486e-19 | -1.720158e-16 | yes |
| I1 | 3.529513172188e-04 | 3.529513172188e-04 | -5.421010862428e-20 | -1.535909e-16 | yes |
| I2 | 2.773410061471e-04 | 2.773410061471e-04 | -5.421010862428e-20 | -1.954637e-16 | yes |
| rx | 9.331652708790e-02 | 9.331652708790e-02 | 0.000000000000e+00 | 0.000000e+00 | yes |
| ry | 8.272295869345e-02 | 8.272295869345e-02 | 0.000000000000e+00 | 0.000000e+00 | yes |

### Torsion check

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| J_sv_cell | 5.908006935839e-04 | 5.787142501257e-04 | 1.208644345821e-05 | 2.088499e-02 | yes |

Expected CSF torsion flags:

```text
J_sv_cell = (0.0005908006935839331, 0.051002491836489756)
J_sv_wall = 0.0
```

## Global summary

```text
stations checked: 3
geometry properties per station: 11
maximum geometry absolute delta: 9.714451465470e-17
maximum geometry relative delta: 2.301475e-14
maximum torsion absolute delta: 2.038162831885e-05
maximum torsion relative delta: 2.088499e-02
overall status: PASS
```

## Interpretation

The geometric conversion from slit-encoded `@cell` geometry through `csf_sp` is consistent with the ordinary CSF reference model at numerical precision.

The torsional comparison also passes. The maximum relative difference between CSF `J_sv_cell` and `sectionproperties` `e.j` is approximately `2.09%`, which is acceptable for this verification because the two values come from different torsion formulations.

This benchmark is therefore a valid CSF-SP `@cell` cross-verification case.


Source code: [`csf_sp_cell_verification.py`](./csf_sp_cell_verification.py)
