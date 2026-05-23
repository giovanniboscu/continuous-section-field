# CSF/OpenSees nodal absolute-resultant report

## Models

- Model 0 - uniform 4 (4 elements): segmented beam model, 4 elements, 13 CSF section calls.
- Model 1 - uniform 6 (6 elements): segmented beam model, 6 elements, 19 CSF section calls.
- Model 2 - uniform 8 (8 elements): segmented beam model, 8 elements, 25 CSF section calls.
- Model 3 - uniform 12 (12 elements): segmented beam model, 12 elements, 37 CSF section calls.
- Model 4 - uniform 16 (16 elements): segmented beam model, 16 elements, 49 CSF section calls.
- Model 5 - uniform 24 (24 elements): segmented beam model, 24 elements, 73 CSF section calls.
- Model 6 - uniform 32 (32 elements): segmented beam model, 32 elements, 97 CSF section calls.

## Structural case

- Scheme: cantilever tower/beam.
- Boundary condition: fixed base at z=0.
- FY_tip = 1.200000e+06
- FZ_tip = -5.000000e+06
- MX_tip = 8.000000e+06
- MZ_tip = 3.000000e+06
- WY_dist = 8.000000e+03

## Comparison rule

This report lists only the nodal/end action resultants returned by OpenSees.
All sampled model nodes are retained for each discretization.
No action interpolation, no nodal deltas, no trunk representative values, and no midpoint section-sampling stations are reported.

## Tip response

| Model | N_elems | CSF section calls | Uy_tip | Rz_tip |
|---|---:|---:|---:|---:|
| Model 0 - uniform 4 (4 elements) | 4 | 13 | 4.42488712e-01 | 1.35540136e-03 |
| Model 1 - uniform 6 (6 elements) | 6 | 19 | 4.42563279e-01 | 1.35543436e-03 |
| Model 2 - uniform 8 (8 elements) | 8 | 25 | 4.42576250e-01 | 1.35544002e-03 |
| Model 3 - uniform 12 (12 elements) | 12 | 37 | 4.42581135e-01 | 1.35544213e-03 |
| Model 4 - uniform 16 (16 elements) | 16 | 49 | 4.42581965e-01 | 1.35544249e-03 |
| Model 5 - uniform 24 (24 elements) | 24 | 73 | 4.42582274e-01 | 1.35544262e-03 |
| Model 6 - uniform 32 (32 elements) | 32 | 97 | 4.42582326e-01 | 1.35544265e-03 |

## Nodal samples

| Model | N_elems | CSF section calls | nodal samples |
|---|---:|---:|---:|
| Model 0 - uniform 4 (4 elements) | 4 | 13 | 5 |
| Model 1 - uniform 6 (6 elements) | 6 | 19 | 7 |
| Model 2 - uniform 8 (8 elements) | 8 | 25 | 9 |
| Model 3 - uniform 12 (12 elements) | 12 | 37 | 13 |
| Model 4 - uniform 16 (16 elements) | 16 | 49 | 17 |
| Model 5 - uniform 24 (24 elements) | 24 | 73 | 25 |
| Model 6 - uniform 32 (32 elements) | 32 | 97 | 33 |

## Output files

- `openseeslab_raw_nodal_values.csv`: absolute nodal OpenSees resultants N, T, MB, MT for every sampled node of every model.
- `openseeslab_tip_response.csv`: tip displacement and torsional rotation for each model.
- `plot_N/T/MB/MT_raw_nodal_values.png`: absolute nodal OpenSees resultants. MB is the bending moment magnitude (transverse to element axis); MT is the torsional moment magnitude (along element axis).
