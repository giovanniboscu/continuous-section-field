# `J_s_vroark` - torsional constant estimate: usage guide

## What it is

CSF provides two complementary outputs related to the Saint-Venant torsional constant `J` at a given station:

| Output | Method | Cost |
|---|---|---|
| `J_s_vroark` | Roark formula applied to an equivalent rectangle built from effective section quantities | zero - always available |
| `e.j` | FEM warping solve via `sectionproperties` | requires `csf_sp` |
| `J_s_vroark_fidelity` | geometric indicator derived from the equivalent rectangle | zero - always available |

`J_s_vroark` is a fast proxy. `e.j` is the FEM reference used here for comparison.

---

## How `J_s_vroark` is computed

The implementation follows this sequence.

### 1. Build effective section quantities

For a section made of one or more polygons, CSF first computes effective area and effective centroidal inertias using polygon weights `w_i`:

```text
A_tot = Σ (w_i * A_i)
```

and, after the effective centroid is found,

```text
Ix  = Σ w_i * (Ix_i  + A_i * dy_i^2)
Iy  = Σ w_i * (Iy_i  + A_i * dx_i^2)
Ixy = Σ w_i * (Ixy_i + A_i * dx_i * dy_i)
```

So `w` enters the calculation **before** the Roark step, through the effective section quantities.

### 2. Compute principal inertias

From `Ix`, `Iy`, `Ixy`, CSF computes the principal inertias and keeps:

```text
I_min = min(I1, I2)
```

### 3. Build the equivalent rectangle

The equivalent rectangle is reconstructed from `A_tot` and `I_min`.
For a rectangle with long side `a` and short side `t`:

```text
a * t = A_tot
(a * t^3) / 12 = I_min
```

which gives:

```text
t_eq = sqrt(12 * I_min / A_tot)
a_eq = A_tot / t_eq
```

with dimensions ordered so that `a_eq >= t_eq`.

### 4. Apply the Roark rectangle formula

`J_s_vroark` is then computed by applying the Roark torsion formula for a **solid rectangle** to `(a_eq, t_eq)`.

So the logic is:

```text
weighted section quantities
-> equivalent rectangle
-> Roark rectangle formula
-> J_s_vroark
```

---

## How `J_s_vroark_fidelity` is currently computed

The current implementation derives fidelity from the equivalent rectangle.

### Aspect-ratio term

For non-circular solid sections, fidelity is the short-to-long side ratio of the equivalent rectangle:

```text
fidelity = t_eq / a_eq
```

So:

- square equivalent rectangle -> `fidelity = 1`
- elongated equivalent rectangle -> lower fidelity

### Isoperimetric penalty

A further penalty is applied only for very compact outer shapes:

```text
Q = 4 * pi * A / P^2
```

If `Q > 0.90`, fidelity is reduced by multiplying by `(1 - Q)`.
This is meant to penalize shapes such as circles or ellipses, where a rectangle-based Roark mapping is structurally poor.

Important: this fidelity is computed from the **equivalent rectangle built after weighting**, not by comparing `J_s_vroark` with `e.j`.

---

## Validation dataset - effect of polygon weight `w`

| Case | w | `J_s_vroark` | `J_s_vroark_fidelity` | `e.j` |
|---|---:|---:|---:|---:|
| `square_1` | 1.0 | 0.14083333 | 1.00000000 | 0.14057750 |
| `square_1` | 0.5 | 0.02861003 | 0.50000000 | 0.07028875 |
| `rect_sqr2` | 1.0 | 0.56333333 | 1.00000000 | 0.56230860 |
| `rect_sqr2` | 0.5 | 0.11444010 | 0.50000000 | 0.28115430 |
| `3boxtriangl` | 1.0 | 1.04757001 | 0.86428571 | 0.93005250 |
| `3boxtriangl` | 0.5 | 0.25749000 | 0.50000000 | 0.46368000 |
| `complexboxes` | 1.0 | 2.67006702 | 0.44445209 | 1.60937700 |
| `complexboxes` | 0.5 | 0.86876799 | 0.88890418 | 0.80468870 |
| `complexboxes2` | * | 20.76646218 | 0.91926779 | 25.08619000 |
| `complexboxesw1` | 1.0 | 2.67006702 | 0.44445209 | 1.60937700 |
| `complexboxesw0.5` | 0.5 | 0.86876799 | 0.88890418 | 0.80468870 |

`*` means mixed polygon weights were used directly from the YAML.

---

## Observations from the dataset

1. For `w = 1` and solid rectangular cases, `J_s_vroark` is very close to `e.j`.
   - `square_1`: `0.14083333` vs `0.14057750`
   - `rect_sqr2`: `0.56333333` vs `0.56230860`

2. When `w` changes, both `J_s_vroark` and `e.j` change, but not in the same way.
   This is expected because `J_s_vroark` is obtained from a Roark rectangle built from weighted effective quantities, while `e.j` comes from the FEM solve used in `csf_sp`.

3. The current fidelity is internally coherent with the implemented mapping, because it is derived from the equivalent rectangle after weighting.

4. The current fidelity should not be read as a direct error estimate against `e.j`.
   It is a geometric indicator of the equivalent-rectangle mapping used by the current implementation.

---

## Practical reading of the outputs

Use the outputs this way:

- `J_s_vroark` -> fast torsional constant estimate from the Roark-equivalent-rectangle method
- `e.j` -> FEM reference from `sectionproperties`
- `J_s_vroark_fidelity` -> current geometric indicator attached to the equivalent-rectangle mapping

So the intended structure is:

```text
J estimate     -> J_s_vroark
FEM reference  -> e.j
0..1 indicator -> J_s_vroark_fidelity
```

---

## Recommended workflow

```text
At a station z:
  1. Read J_s_vroark and J_s_vroark_fidelity from CSF output.
  2. If a fast mesh-free estimate is sufficient, use J_s_vroark.
  3. If a FEM reference is needed, run:
       python3 -m csf.utils.csf_sp --yaml <file>.yaml --z=<z>
     and read e.j.
  4. Compare the two on representative stations when validating a geometry class.
```
