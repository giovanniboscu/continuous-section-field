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
height = 0.2666667
weight = 0.0
```

At `S0`, the void is located in the upper part of the section.

At `S1`, the void is located in the lower part of the section.

The outer rectangle is unchanged between `S0` and `S1`.

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

## Main expected behaviour

The net area remains constant because the outer rectangle and the void area are unchanged.

The polar second moment `Ip` varies because the void changes position within the section.

## Selected report values

| z | A | Ip |
|---:|---:|---:|
| 1.0 | 0.55999999 | 0.06400681 |
| 2.0 | 0.55999999 | 0.06540059 |
| 3.0 | 0.55999999 | 0.06639615 |
| 4.0 | 0.55999999 | 0.06699348 |
| 5.0 | 0.55999999 | 0.06719259 |
| 6.0 | 0.55999999 | 0.06699348 |
| 7.0 | 0.55999999 | 0.06639615 |
| 8.0 | 0.55999999 | 0.06540059 |
| 9.0 | 0.55999999 | 0.06400681 |
| 10.0 | 0.55999999 | 0.06221481 |

## Text report

A plain-text report is provided in:

```text
report.txt
```
