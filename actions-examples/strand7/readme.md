# CSF Moving Internal Hole Example
<img width="456" height="477" alt="Screenshot 2026-06-16 at 10 34 50" src="https://github.com/user-attachments/assets/5db934cc-7fce-46ee-99ac-540d4bea333d" />

<img width="998" height="437" alt="Screenshot 2026-06-16 at 10 34 43" src="https://github.com/user-attachments/assets/e4d9ade9-922d-4eb7-b64a-5e109d192b49" />
<img width="481" height="479" alt="Screenshot 2026-06-16 at 10 34 37" src="https://github.com/user-attachments/assets/7c078427-6e3c-4068-aaca-73d94c696ccb" />
<img width="452" height="474" alt="Screenshot 2026-06-16 at 10 34 22" src="https://github.com/user-attachments/assets/b0e1852e-10e6-4cf8-81c7-05793ddab9e1" />


## Purpose

This example defines a CSF member with a constant outer rectangular section and an internal rectangular void that moves from the upper part of the section to the lower part along the member axis.

The case is intended to show a sectional geometry variation that is not a global scaling of the whole cross-section.

## Geometry

Member length:

```text<img width="1177" height="484" alt="Screenshot 2026-06-16 at 10 32 01" src="https://github.com/user-attachments/assets/a188e644-3856-4ce4-8ba6-a41a5dac4ca5" />

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

<img width="362" height="473" alt="Screenshot 2026-06-16 at 10 31 35" src="https://github.com/user-attachments/assets/3a8fa70e-cc6b-42d4-b793-84a88e39d15d" />


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
