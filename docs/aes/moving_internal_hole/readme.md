# CSF Moving Internal Hole Example

## Purpose

This example defines a CSF member with a constant outer rectangular section and an internal rectangular void that moves from the upper part of the section to the lower part along the member axis.

The case is intended to show a sectional geometry variation that is not a global scaling of the whole cross-section.

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

| Region | Weight | x-range | y-range | Width | Height | Area | Centroid |
|---|---:|---:|---:|---:|---:|---:|---:|
| Outer rectangle | 1.0 | `[-0.40, 0.40]` | `[-0.40, 0.40]` | 0.80 | 0.80 | 0.640000 | `(0.0, 0.0)` |
| Internal void | 0.0 | `[-0.15, 0.15]` | `[0.10, 0.30]` | 0.30 | 0.20 | 0.060000 | `(0.0, 0.20)` |

### Station `S1` - `z = 10.0`

| Region | Weight | x-range | y-range | Width | Height | Area | Centroid |
|---|---:|---:|---:|---:|---:|---:|---:|
| Outer rectangle | 1.0 | `[-0.40, 0.40]` | `[-0.40, 0.40]` | 0.80 | 0.80 | 0.640000 | `(0.0, 0.0)` |
| Internal void | 0.0 | `[-0.15, 0.15]` | `[-0.30, -0.10]` | 0.30 | 0.20 | 0.060000 | `(0.0, -0.20)` |

## Figures

<img width="455" height="403" alt="Screenshot 2026-06-16 at 10 44 49" src="https://github.com/user-attachments/assets/f2b6df10-895e-497e-9a4b-81af48c69e8a" />

<img width="1014" height="758" alt="image" src="https://github.com/user-attachments/assets/8e852def-3b29-4a10-9990-806a91193500" />


<img width="455" height="401" alt="Screenshot 2026-06-16 at 10 44 37" src="https://github.com/user-attachments/assets/0d9c2abf-1dd8-497c-a6cb-3a3786977632" />

<img width="316" height="476" alt="Screenshot 2026-06-16 at 10 45 03" src="https://github.com/user-attachments/assets/24dc8ec5-9019-41d8-b9e8-f6a784f0ede7" />

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

The polar second moment `Ip` varies because the void changes position within the section.

## Selected reference values for the updated geometry

| z | A | Ip |
|---:|---:|---:|
| 1.0 | 0.58000000 | 0.06592177 |
| 2.0 | 0.58000000 | 0.06666329 |
| 3.0 | 0.58000000 | 0.06719294 |
| 4.0 | 0.58000000 | 0.06751074 |
| 5.0 | 0.58000000 | 0.06761667 |
| 6.0 | 0.58000000 | 0.06751074 |
| 7.0 | 0.58000000 | 0.06719294 |
| 8.0 | 0.58000000 | 0.06666329 |
| 9.0 | 0.58000000 | 0.06592177 |
| 10.0 | 0.58000000 | 0.06496839 |

## Text report

A plain-text report is provided in:

```text
report.txt
```
