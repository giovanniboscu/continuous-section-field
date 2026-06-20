# CSF Moving Internal Hole Example

## Purpose

This example defines a CSF member with a constant outer rectangular section and an internal rectangular void that moves from the upper part of the section to the lower part along the member axis.

The case is intended to show a sectional geometry variation that is not a global scaling of the whole cross-section. The net participating area remains constant, while the sectional inertia properties vary because the void changes position inside the section.

This example is provided as additional repository material for illustrating CSF containment behaviour.

## Geometry

Member length:

```text
z = 0.0 to z = 10.0
```

Outer rectangle:

```text
width  = 0.80
height = 0.80
weight = 1.0
```

Internal rectangular void:

```text
width  = 0.30
height = 0.20
weight = 0.0
```

At `S0`, the void is located in the upper part of the section.

At `S1`, the void is located in the lower part of the section.

The outer rectangle is unchanged between `S0` and `S1`.

The internal void keeps the same dimensions and translates from the upper part of the section to the lower part.

The net participating area is:

```text
A = 0.640000 - 0.060000 = 0.580000
```

## Section dimensions at end stations

All coordinates are given in the local cross-section plane.

### Station `S0` - `z = 0.0`

| Region          | Weight |         x-range |         y-range | Width | Height |     Area |      Centroid |
| --------------- | -----: | --------------: | --------------: | ----: | -----: | -------: | ------------: |
| Outer rectangle |    1.0 | `[-0.40, 0.40]` | `[-0.40, 0.40]` |  0.80 |   0.80 | 0.640000 |  `(0.0, 0.0)` |
| Internal void   |    0.0 | `[-0.15, 0.15]` |  `[0.10, 0.30]` |  0.30 |   0.20 | 0.060000 | `(0.0, 0.20)` |

### Station `S1` - `z = 10.0`

| Region          | Weight |         x-range |          y-range | Width | Height |     Area |       Centroid |
| --------------- | -----: | --------------: | ---------------: | ----: | -----: | -------: | -------------: |
| Outer rectangle |    1.0 | `[-0.40, 0.40]` |  `[-0.40, 0.40]` |  0.80 |   0.80 | 0.640000 |   `(0.0, 0.0)` |
| Internal void   |    0.0 | `[-0.15, 0.15]` | `[-0.30, -0.10]` |  0.30 |   0.20 | 0.060000 | `(0.0, -0.20)` |

## Figures
<img width="662" height="578" alt="image" src="https://github.com/user-attachments/assets/bb85afe1-97df-4a4b-8d0a-424a9422581c" />
<img width="1022" height="758" alt="image" src="https://github.com/user-attachments/assets/b56e1f8d-bbda-430a-9baa-6ea8c8f88e69" />
<img width="662" height="578" alt="image" src="https://github.com/user-attachments/assets/b7f78cf8-ce17-4927-b103-8940bcf4ad96" />
<img width="662" height="578" alt="image" src="https://github.com/user-attachments/assets/b92f9cb0-1b6c-4f40-8855-d3c59b91f01f" />

## Input files

The case uses:

```text
geometry.yaml
actions.yaml
```

## Run command

```bash
csf-actions geometry.yaml actions.yaml
```

<img width="362" height="473" alt="Screenshot 2026-06-16 at 10 31 35" src="https://github.com/user-attachments/assets/3a8fa70e-cc6b-42d4-b793-84a88e39d15d" />

## Main expected behaviour

The net area remains constant because the outer rectangle and the void area are unchanged.

The second moment `Ix` and the polar second moment `Ip` vary because the void changes position within the section.

The maximum values occur near the middle of the member, where the void is closest to the section centroid.

## Selected reference values for the updated geometry

|    z |          A |         Ix |         Ip |
| ---: | ---------: | ---------: | ---------: |
|  1.0 | 0.58000000 | 0.03223844 | 0.06592177 |
|  2.0 | 0.58000000 | 0.03297995 | 0.06666329 |
|  3.0 | 0.58000000 | 0.03350961 | 0.06719294 |
|  4.0 | 0.58000000 | 0.03382740 | 0.06751074 |
|  5.0 | 0.58000000 | 0.03393333 | 0.06761667 |
|  6.0 | 0.58000000 | 0.03382740 | 0.06751074 |
|  7.0 | 0.58000000 | 0.03350961 | 0.06719294 |
|  8.0 | 0.58000000 | 0.03297995 | 0.06666329 |
|  9.0 | 0.58000000 | 0.03223844 | 0.06592177 |
| 10.0 | 0.58000000 | 0.03128506 | 0.06496839 |

## Volume check

The same case also reports the occupied and homogenized volumes along the member.

The gross outer volume is:

```text
0.80 × 0.80 × 10.0 = 6.400000
```

The moving internal void has volume:

```text
0.30 × 0.20 × 10.0 = 0.600000
```

Since the void has zero participation, the homogenized participating volume is:

```text
6.400000 - 0.600000 = 5.800000
```

The volume report is:

```text
Total Occupied Volume:             6.400000
Total Occupied Homogenized Volume: 5.800000
```

The volume report therefore confirms the containment interpretation: the internal void is geometrically present but does not contribute to the homogenized participating volume.

## Text report

A plain-text report is provided in:

```text
selected_analysis.txt
```
