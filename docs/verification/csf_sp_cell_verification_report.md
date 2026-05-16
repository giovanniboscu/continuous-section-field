# CSF-SP @cell Verification Report

## Model

This benchmark verifies a slit-encoded `@cell` polygon converted through `csf_sp` into a `sectionproperties` model.

Two CSF fields are used:

1. an ordinary reference field with `outer weight = 1.0` and `inner weight = 0.0`, used for geometric quantities;
2. a slit-encoded `@cell` field, used for `csf_sp` conversion and `J_sv_cell` evaluation.

The geometric comparison is expected to match at numerical precision. The torsional comparison checks consistency between CSF `J_sv_cell` and `sectionproperties` `e.j`, using a looser tolerance because the two paths use different torsion formulations.

Geometry absolute tolerance: `1.0e-09`
Geometry relative tolerance: `1.0e-07`
Torsion absolute tolerance: `1.0e-08`
Torsion relative tolerance: `1.0e-01`
Mesh size: `0.0001`

### Geometric check: CSF ordinary reference vs csf_sp @cell at z = 0.0

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

### Torsion check: CSF J_sv_cell vs sectionproperties e.j at z = 0.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| J_sv_cell | 1.062409393301e-03 | 1.042027764982e-03 | 2.038162831885e-05 | 1.955958e-02 | yes |

Expected `@cell` torsion flags:

- `J_sv_cell`: `(0.0010624093933009307, 0.05815589402152802)`
- `J_sv_wall`: `0.0`

### Geometric check: CSF ordinary reference vs csf_sp @cell at z = 5.0

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

### Torsion check: CSF J_sv_cell vs sectionproperties e.j at z = 5.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| J_sv_cell | 8.008614568896e-04 | 7.852298462031e-04 | 1.563161068650e-05 | 1.990705e-02 | yes |

Expected `@cell` torsion flags:

- `J_sv_cell`: `(0.0008008614568895788, 0.05458010812177368)`
- `J_sv_wall`: `0.0`

### Geometric check: CSF ordinary reference vs csf_sp @cell at z = 10.0

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

### Torsion check: CSF J_sv_cell vs sectionproperties e.j at z = 10.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| J_sv_cell | 5.908006935839e-04 | 5.787142501257e-04 | 1.208644345821e-05 | 2.088499e-02 | yes |

Expected `@cell` torsion flags:

- `J_sv_cell`: `(0.000590800693583933, 0.05100249183648975)`
- `J_sv_wall`: `0.0`

## Global summary

- Stations checked: `3`
- Geometry properties per station: `11`
- Maximum geometry absolute delta: `9.714451465470e-17`
- Maximum geometry relative delta: `2.301475e-14`
- Maximum torsion absolute delta: `2.038162831885e-05`
- Maximum torsion relative delta: `2.088499e-02`
- Overall status: `PASS`
