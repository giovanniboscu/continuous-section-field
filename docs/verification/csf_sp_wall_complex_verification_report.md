# CSF-SP Complex @wall Verification Report

Source code: [`csf_sp_wall_complex_verification.py`](./csf_sp_wall_complex_verification.py)

## Model

This benchmark verifies a complex open built-up thin-walled section.

The section is represented by several non-overlapping finite-thickness rectangular wall plates. The plates may share boundaries, but no plate area is intentionally overlapped.

Two CSF fields are used:

1. an ordinary reference field with the same wall plates and no `@wall` tags;
2. a tagged field with the same wall plates named as `@wall@t=...` polygons.

The geometry is uniformly scaled from S0 to S1. The comparison is made at multiple stations along `z`.

Geometry absolute tolerance: `1.0e-08`
Geometry relative tolerance: `1.0e-06`
Torsion absolute tolerance: `1.0e-06`
Torsion relative tolerance: `2.0e-01`
Mesh size: `0.03`

### Geometric check: CSF ordinary complex wall vs csf_sp @wall at z = 0.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 1.134420000000e+01 | 1.134420000000e+01 | -7.105427357601e-15 | -6.263489e-16 | yes |
| Cx | 1.230990285785e-02 | 1.230990285785e-02 | -7.459310946700e-16 | -6.059602e-14 | yes |
| Cy | 2.357501630789e-01 | 2.357501630789e-01 | -1.498801083244e-15 | -6.357582e-15 | yes |
| Ix | 1.566931773311e+02 | 1.566931773311e+02 | 2.842170943040e-14 | 1.813845e-16 | yes |
| Iy | 2.309260581131e+01 | 2.309260581131e+01 | 1.776356839400e-14 | 7.692319e-16 | yes |
| Ixy | -4.772873572733e-01 | -4.772873572733e-01 | -4.996003610813e-15 | 1.046750e-14 | yes |
| Ip | 1.797857831424e+02 | 1.797857831424e+02 | 5.684341886081e-14 | 3.161730e-16 | yes |
| I1 | 1.566948824160e+02 | 1.566948824160e+02 | 5.684341886081e-14 | 3.627650e-16 | yes |
| I2 | 2.309090072643e+01 | 2.309090072643e+01 | 2.842170943040e-14 | 1.230862e-15 | yes |
| rx | 3.716533965734e+00 | 3.716533965734e+00 | 1.332267629550e-15 | 3.584705e-16 | yes |
| ry | 1.426755429200e+00 | 1.426755429200e+00 | 1.110223024625e-15 | 7.781453e-16 | yes |

### Torsion check: CSF J_sv_wall vs sectionproperties e.j at z = 0.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| J_sv_wall | 7.243986400000e-01 | 7.430751613167e-01 | -1.867652131674e-02 | -2.513409e-02 | yes |

Expected `@wall` torsion flags:

- `J_sv_wall`: `0.7243986400000001`
- `J_sv_cell`: `0.0`

### Geometric check: CSF ordinary complex wall vs csf_sp @wall at z = 2.5

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 1.056400264500e+01 | 1.056400264500e+01 | 1.598721155460e-14 | 1.513367e-15 | yes |
| Cx | 1.187905625782e-02 | 1.187905625782e-02 | 2.602085213965e-16 | 2.190481e-14 | yes |
| Cy | 2.274989073712e-01 | 2.274989073712e-01 | 2.498001805407e-16 | 1.098028e-15 | yes |
| Ix | 1.358811896159e+02 | 1.358811896159e+02 | -2.842170943040e-14 | -2.091659e-16 | yes |
| Iy | 2.002544592188e+01 | 2.002544592188e+01 | -3.552713678801e-15 | -1.774100e-16 | yes |
| Ixy | -4.138940507786e-01 | -4.138940507786e-01 | -9.547918011776e-15 | 2.306851e-14 | yes |
| Ip | 1.559066355378e+02 | 1.559066355378e+02 | -2.842170943040e-14 | -1.822995e-16 | yes |
| I1 | 1.358826682314e+02 | 1.358826682314e+02 | -2.842170943040e-14 | -2.091636e-16 | yes |
| I2 | 2.002396730638e+01 | 2.002396730638e+01 | 0.000000000000e+00 | 0.000000e+00 | yes |
| rx | 3.586455276934e+00 | 3.586455276934e+00 | -2.664535259100e-15 | -7.429440e-16 | yes |
| ry | 1.376818989178e+00 | 1.376818989178e+00 | -1.110223024625e-15 | -8.063682e-16 | yes |

### Torsion check: CSF J_sv_wall vs sectionproperties e.j at z = 2.5

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| J_sv_wall | 6.281840130880e-01 | 6.443142329364e-01 | -1.613021984849e-02 | -2.503471e-02 | yes |

Expected `@wall` torsion flags:

- `J_sv_wall`: `0.6281840130879504`
- `J_sv_cell`: `0.0`

### Geometric check: CSF ordinary complex wall vs csf_sp @wall at z = 5.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 9.811598580000e+00 | 9.811598580000e+00 | -5.329070518201e-15 | -5.431399e-16 | yes |
| Cx | 1.144820965780e-02 | 1.144820965780e-02 | -3.382710778155e-16 | -2.954795e-14 | yes |
| Cy | 2.192476516634e-01 | 2.192476516634e-01 | 4.163336342344e-16 | 1.898919e-15 | yes |
| Ix | 1.172146462558e+02 | 1.172146462558e+02 | 1.421085471520e-14 | 1.212379e-16 | yes |
| Iy | 1.727447019328e+01 | 1.727447019328e+01 | 1.421085471520e-14 | 8.226507e-16 | yes |
| Ixy | -3.570357669559e-01 | -3.570357669559e-01 | 1.887379141863e-15 | -5.286247e-15 | yes |
| Ip | 1.344891164491e+02 | 1.344891164491e+02 | 2.842170943040e-14 | 2.113309e-16 | yes |
| I1 | 1.172159217480e+02 | 1.172159217480e+02 | 1.421085471520e-14 | 1.212366e-16 | yes |
| I2 | 1.727319470112e+01 | 1.727319470112e+01 | 1.421085471520e-14 | 8.227114e-16 | yes |
| rx | 3.456376588133e+00 | 3.456376588133e+00 | 8.881784197001e-16 | 2.569681e-16 | yes |
| ry | 1.326882549156e+00 | 1.326882549156e+00 | 8.881784197001e-16 | 6.693723e-16 | yes |

### Torsion check: CSF J_sv_wall vs sectionproperties e.j at z = 5.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| J_sv_wall | 5.418878586933e-01 | 5.562553972423e-01 | -1.436753854900e-02 | -2.582903e-02 | yes |

Expected `@wall` torsion flags:

- `J_sv_wall`: `0.5418878586932661`
- `J_sv_cell`: `0.0`

### Geometric check: CSF ordinary complex wall vs csf_sp @wall at z = 7.5

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 9.086987805000e+00 | 9.086987805000e+00 | -7.105427357601e-15 | -7.819343e-16 | yes |
| Cx | 1.101736305777e-02 | 1.101736305777e-02 | -1.734723475977e-17 | -1.574536e-15 | yes |
| Cy | 2.109963959556e-01 | 2.109963959556e-01 | 8.604228440845e-16 | 4.077903e-15 | yes |
| Ix | 1.005407749285e+02 | 1.005407749285e+02 | 5.684341886081e-14 | 5.653768e-16 | yes |
| Iy | 1.481716385444e+01 | 1.481716385444e+01 | 8.881784197001e-15 | 5.994254e-16 | yes |
| Ixy | -3.062471613709e-01 | -3.062471613709e-01 | 1.160183060733e-14 | -3.788388e-14 | yes |
| Ip | 1.153579387829e+02 | 1.153579387829e+02 | 7.105427357601e-14 | 6.159461e-16 | yes |
| I1 | 1.005418689810e+02 | 1.005418689810e+02 | 5.684341886081e-14 | 5.653706e-16 | yes |
| I2 | 1.481606980198e+01 | 1.481606980198e+01 | 1.421085471520e-14 | 9.591514e-16 | yes |
| rx | 3.326297899332e+00 | 3.326297899332e+00 | 1.776356839400e-15 | 5.340342e-16 | yes |
| ry | 1.276946109134e+00 | 1.276946109134e+00 | 8.881784197001e-16 | 6.955489e-16 | yes |

### Torsion check: CSF J_sv_wall vs sectionproperties e.j at z = 7.5

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| J_sv_wall | 4.648039044409e-01 | 4.776615917564e-01 | -1.285768731548e-02 | -2.691798e-02 | yes |

Expected `@wall` torsion flags:

- `J_sv_wall`: `0.46480390444092123`
- `J_sv_cell`: `0.0`

### Geometric check: CSF ordinary complex wall vs csf_sp @wall at z = 10.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| A | 8.390170320000e+00 | 8.390170320000e+00 | -3.552713678801e-15 | -4.234376e-16 | yes |
| Cx | 1.058651645775e-02 | 1.058651645775e-02 | 7.806255641896e-17 | 7.373772e-15 | yes |
| Cy | 2.027451402479e-01 | 2.027451402479e-01 | 2.275957200482e-15 | 1.122571e-14 | yes |
| Ix | 8.571244661645e+01 | 8.571244661645e+01 | -9.947598300641e-14 | -1.160578e-15 | yes |
| Iy | 1.263184381445e+01 | 1.263184381445e+01 | -1.953992523340e-14 | -1.546878e-15 | yes |
| Ixy | -2.610800790933e-01 | -2.610800790933e-01 | -1.221245327088e-15 | 4.677666e-15 | yes |
| Ip | 9.834429043089e+01 | 9.834429043089e+01 | -1.136868377216e-13 | -1.156009e-15 | yes |
| I1 | 8.571337931179e+01 | 8.571337931179e+01 | -8.526512829121e-14 | -9.947703e-16 | yes |
| I2 | 1.263091111911e+01 | 1.263091111911e+01 | -1.421085471520e-14 | -1.125085e-15 | yes |
| rx | 3.196219210531e+00 | 3.196219210531e+00 | -8.881784197001e-16 | -2.778841e-16 | yes |
| ry | 1.227009669112e+00 | 1.227009669112e+00 | -6.661338147751e-16 | -5.428921e-16 | yes |

### Torsion check: CSF J_sv_wall vs sectionproperties e.j at z = 10.0

| Property | CSF | SP | Delta | RelDelta | OK |
|---|---:|---:|---:|---:|:---:|
| J_sv_wall | 3.962519671729e-01 | 4.073321611424e-01 | -1.108019396950e-02 | -2.720186e-02 | yes |

Expected `@wall` torsion flags:

- `J_sv_wall`: `0.3962519671729024`
- `J_sv_cell`: `0.0`

## Global summary

- Stations checked: `5`
- Geometry properties per station: `11`
- Maximum geometry absolute delta: `1.136868377216e-13`
- Maximum geometry relative delta: `6.059602e-14`
- Maximum torsion absolute delta: `1.867652131674e-02`
- Maximum torsion relative delta: `2.720186e-02`
- Overall status: `PASS`
