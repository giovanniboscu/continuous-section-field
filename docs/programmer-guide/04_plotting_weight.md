# 04 - Plotting weight & shear_weight

## Purpose

Use weight and shear weight plots to verify how each polygon weight `w(z)` and shear weight evolve along the member axis.

This chapter covers:
- per-polygon weight interpolation plots — `plot_weight` / `set_weight_laws`
- per-polygon shear weight interpolation plots — `plot_shear_weight` / `set_shear_weight_laws`

---

## Imports

```python
# --- Core CSF imports used in this minimal example ---
from csf import (
    Pt, Polygon, Section, ContinuousSectionField, Visualizer,
    section_full_analysis, section_print_analysis, section_full_analysis_keys
)

import matplotlib.pyplot as plt
```

---

## Example

CSF automatically interpolates along `z` the weight specified for each section.  
See the example below.



 "weight=1.0,
 weight=1.5,"
 

```python
# --- Core CSF imports used in this minimal example ---
from csf import (
    Pt, Polygon, Section, ContinuousSectionField, Visualizer,
    section_full_analysis, section_print_analysis, section_full_analysis_keys
)

import matplotlib.pyplot as plt

# -------------------------------------------------------
# 1) Geometry definition with API objects
# -------------------------------------------------------
# We build a simple section from two rectangles:
# - upperpart
# - lowerpart
# Then we define start section (S0) and end section (S1).

if __name__ == "__main__":
    # Optional file name placeholder (not used in this snippet)
    geometryfile = "geometry.tcl"

    # Geometric parameters
    h = 1.20
    hb = 0.40
    b = 0.30

    # --- S0 polygons (z = 0.0) ---
    poly_top_start = Polygon(
        vertices=(
            Pt(-b/2,  0.0),
            Pt( b/2,  0.0),
            Pt( b/2,  h/2),
            Pt(-b/2,  h/2),
        ),
        weight=1.0,  # <=
        name="upperpart",
    )

    poly_bottom_start = Polygon(
        vertices=(
            Pt(-b/2, -h/2),
            Pt( b/2, -h/2),
            Pt( b/2,  0.0),
            Pt(-b/2,  0.0),
        ),
        weight=1.5,  # <=
        name="lowerpart",
    )

    # --- S1 polygons (z = L) ---
    # upperpart unchanged, lowerpart modified (different depth)
    poly_top_end = Polygon(
        vertices=(
            Pt(-b/2,  0.0),
            Pt( b/2,  0.0),
            Pt( b/2,  h/2),
            Pt(-b/2,  h/2),
        ),
        weight=1.0,
        name="upperpart",
    )

    poly_bottom_end = Polygon(
        vertices=(
            Pt(-b/2, -hb/4),
            Pt( b/2, -hb/4),
            Pt( b/2,  0.0),
            Pt(-b/2,  0.0),
        ),
        weight=1.0,
        name="lowerpart",
    )

    # -------------------------------------------------------
    # Section field instantiation
    # -------------------------------------------------------
    # Define start/end sections and create the continuous field.
    L = 10.0

    s0 = Section(polygons=(poly_bottom_start, poly_top_start), z=0.0)
    s1 = Section(polygons=(poly_bottom_end,   poly_top_end),   z=L)

    section_field = ContinuousSectionField(section0=s0, section1=s1)

    # -------------------------------------------------------
    # Extract one section and print 
    # -------------------------------------------------------
    # Here z = 10.0, so this is exactly the end section (S1).
    zsec_val = 10.0
    sec_at_z = section_field.section(zsec_val)

    # =================================================================
    # Plot weight
    # =================================================================
    viz = Visualizer(section_field)
    viz.plot_weight(num_points=100, poly_indices_to_plot=None)  # None = all polygons
    plt.show()
```

if no custom law is provided, interpolation is linear by default
![Figure_1](https://github.com/user-attachments/assets/2c576be1-1dfb-46b0-abb6-c5fd8886edc7)

---

## `plot_weight(...)`

```python
plot_weight(self, num_points=100, poly_indices_to_plot=None)
```

Plot interpolated polygon weights `w(z)` along the member axis, using one subplot per polygon.

### Parameters

- `num_points` (`int`, default: `100`)  
  Number of sampling points between `self.field.s0.z` and `self.field.s1.z`.
- `poly_indices_to_plot` (`list[int]` or `None`, default: `None`)  
  List of **0-based** polygon indices to include in the plot. If `None`, all polygons are plotted.

### Behavior

- Sampling coordinates are generated with `np.linspace(z_start, z_end, num_points)`.
- For each sampled `z` and each polygon index `i`, the function evaluates:
  - `p0 = self.field.s0.polygons[i]`
  - `p1 = self.field.s1.polygons[i]`
  - optional law from `self.field.weight_laws[i+1]` (if present)
  - interpolated weight via `self.field._interpolate_weight(...)`
- One subplot is generated per polygon with:
  - curve `w(z)`
  - y-label: `s0 <name0> - s1 <name1>`
  - automatic y-limits with margin
  - grid and per-polygon title

### Output

- Produces matplotlib plots (`plt.show()`).
- No explicit return value.

---

## `set_weight_laws(...)`

```python
section_field.set_weight_laws([
    "lowerpart,lowerpart: put your function w(z) or w(t) here",
])
```
The independent variable can be either `z` (physical coordinate) or `t` (normalized coordinate in `[0, 1]`).

The following variables are available in weight-law expressions:

| Variable | Meaning | Example Law Expression |
| :--- | :--- | :--- |
| **`z`** | Physical coordinate along the member (from start to end) | `w0 * (1 + 0.2 * z / L)` |
| **`t`** | Normalized coordinate in `[0, 1]` | `w0 + (w1 - w0) * t` |
| **`w0`** | Weight at the start section (`z = z0`) | `w0 * 1.5` |
| **`w1`** | Weight at the end section (`z = z1`) | `w1 / 2` |
| **`L`** | Total physical length of the member | `w0 + (z / L) * 0.1` |
| **`np`** | NumPy namespace | `np.sin(...)`, `np.exp(...)`, `np.sqrt(...)` |

The following helper functions are available in weight-law expressions.

**Important:** polygon vertex indexing is **1-based** (the first vertex is `1`, not `0`).

| Function | Meaning | Example Law Expression |
| :--- | :--- | :--- |
| **`d(i, j)`** | Distance between vertex `i` and `j` at the **current** `z` | `w0 * d(1, 2)` |
| **`d0(i, j)`** | Distance between vertex `i` and `j` at the **start** section (`z = z0`) | `w0 * (d(1,2) / d0(1,2))` |
| **`d1(i, j)`** | Distance between vertex `i` and `j` at the **end** section (`z = z1`) | `w1 * (d(1,2) / d1(1,2))` |
| **`E_lookup(file)`** | Interpolated scalar read from an external text file | `E_lookup('stiffness.txt')` |
| **`T_lookup(file)`** | Interpolated scalar read from an external text file using normalized `t` in `[0, 1]` | `T_lookup('stiffness.txt')` |

### Half-cosine smooth ramp

```python
section_field.set_weight_laws([
    "lowerpart,lowerpart : w0 + (w1 - w0) * 0.5 * (1 - np.cos(np.pi * z / L))",
])
```

This represents a half-cosine smooth degradation law (cosine ramp), with gradual variation from `w0` to `w1`.

![Figure_11](https://github.com/user-attachments/assets/8e142df7-f5db-4128-a2ad-9dfcbec0ea54)

### 3-step piecewise law on normalized `t`

```python
section_field.set_weight_laws([
    "lowerpart,lowerpart : np.where(t < 1/3, w0, np.where(t < 2/3, 0.5*(w0 + w1), w1))",
])
```

![Figure_12](https://github.com/user-attachments/assets/81645c39-f894-4228-8b1f-0dabac953319)

---

# External Lookup Files for `E_lookup(...)` and `T_lookup(...)`

Lookup functions read values from a plain text **key-value** table.

`T_lookup(...)` and `E_lookup(...)` return numeric values, so they can be used directly inside mathematical expressions.

```python
section_field.set_weight_laws([
    "lowerpart,lowerpart: E_lookup('put the file name here') * z / L",
])
```

- `E_lookup(file)` uses **`z`** as the lookup key (physical coordinate).
- `T_lookup(file)` uses **`t`** as the lookup key (normalized coordinate in `[0, 1]`).

## File Format

Use a text file with two columns per row:

`key value`

- Column 1: key (`z` for `E_lookup`, `t` for `T_lookup`)
- Column 2: scalar value
- Rows should be ordered by increasing key.

---

## Example for `E_lookup(...)` (key = `z`)

```txt
# stiffness_z.txt
0.0   2.10e11
2.0   2.05e11
5.0   1.95e11
8.0   1.85e11
10.0  1.80e11
```

```python
section_field.set_weight_laws([
    "lowerpart,lowerpart : E_lookup('stiffness_z.txt')",
])
```

## Example for `T_lookup(...)` (key = `t` in `[0, 1]`)

```txt
# stiffness_t.txt
0.00  1.00
0.25  0.92
0.50  0.85
0.75  0.78
1.00  0.70
```

```python
section_field.set_weight_laws([
    "lowerpart,lowerpart : T_lookup('stiffness_t.txt')",
])
```

## Normalized lookup-file example

Create a text file named `wnormlookup.txt`:

```txt
# t    value
0.000000 1.000000
0.100000 0.892000
0.200000 0.808000
0.300000 0.748000
0.400000 0.712000
0.500000 0.700000
0.600000 0.712000
0.700000 0.748000
0.800000 0.808000
0.900000 0.892000
1.000000 1.00000
```

```python
section_field.set_weight_laws([
    "lowerpart,lowerpart: T_lookup('wnormlookup.txt')"
])

viz = Visualizer(section_field)
viz.plot_weight(num_points=100, poly_indices_to_plot=None)  # None = all polygons
plt.show()
```

![Figure_17](https://github.com/user-attachments/assets/2ccaca88-25fd-49be-8450-b1d113ee9159)

## Non-normalized lookup-file example

Create a text file named `zlookup_exponential.txt`:

```txt
# z    value
0.000000 1.000000
1.000000 0.525197
2.000000 0.332157
3.000000 0.253672
4.000000 0.221763
5.000000 0.208790
6.000000 0.203515
7.000000 0.201370
8.000000 0.200499
9.000000 0.200144
10.000000 0.200000
```

```python
section_field.set_weight_laws([
    "lowerpart,lowerpart: E_lookup('zlookup_exponential.txt')"
])

viz = Visualizer(section_field)
viz.plot_weight(num_points=100, poly_indices_to_plot=None)  # None = all polygons
plt.show()
```

![Figure_15](https://github.com/user-attachments/assets/3580a98c-e368-412f-bda3-b83cb8d8e940)

---

# Shear weight laws — `set_shear_weight_laws(...)`

```python
set_shear_weight_laws(self, laws)
```

Define per-polygon shear weight laws, analogous to `set_weight_laws` but governing the shear stiffness contribution of each polygon along the member axis.

The syntax mirrors `set_weight_laws`:

```python
section_field.set_shear_weight_laws([
    "poly_name_s0, poly_name_s1 : expression",
])
```

---

## Expression modes

### 1. Isotropic declaration — `iso(nu)`

```python
section_field.set_shear_weight_laws([
    "lowerpart,lowerpart : iso(0.2)",
])
```

The shorthand `iso(nu)` declares the polygon as **isotropic** with Poisson's ratio `nu`.  
Internally this is equivalent to `w / (2 * (1 + nu))`, but it is stored as an explicit isotropy flag.

> **Important for `csf_sp` export:** only laws written as `iso(nu)` are recognised by the `csf_sp` bridge and exported to SP as isotropic sections. A numerically equivalent formula (see case 2 below) is evaluated correctly at runtime but is **not** flagged as isotropic during export.

---

### 2. Isotropic-equivalent formula (not flagged for export)

```python
section_field.set_shear_weight_laws([
    "lowerpart,lowerpart : w / (2 * (1 + 0.2))",
])
```

This produces the same numerical result as `iso(0.2)` but is treated as a generic expression. The `csf_sp` bridge will **not** export this polygon as an isotropic section toward SP.

Use `iso(nu)` whenever SP-export compatibility is required.

---

### 3. Non-isotropic, dependent on `weight_laws`

The variable `w` inside a shear weight expression refers to the **interpolated weight** returned by the corresponding `weight_laws` entry at the same `z`. This allows the shear law to track the flexural weight law:

```python
section_field.set_shear_weight_laws([
    "lowerpart,lowerpart : w + t / 4",
])
```

Here the shear weight evolves as the flexural weight `w(z)` plus a linear ramp `t/4`.

---

### 4. Non-isotropic, fully autonomous

The shear law can also be completely independent of `weight_laws`, using only the standard variables (`z`, `t`, `np`, lookup functions, etc.):

```python
section_field.set_shear_weight_laws([
    "lowerpart,lowerpart : t / 4 + 0.28",
])
```

In this case the shear weight varies solely according to the expression, with no reference to the flexural weight.

---

## Available variables and functions

All variables and helper functions available in `set_weight_laws` expressions are also available in `set_shear_weight_laws` expressions, with the addition of:

| Variable | Meaning |
| :--- | :--- |
| **`w`** | Interpolated flexural weight at the current `z`, as defined by the corresponding `weight_laws` entry |

---

## `plot_shear_weight(...)`

```python
plot_shear_weight(self, num_points=100, poly_indices_to_plot=None)
```

Plot interpolated polygon shear weights along the member axis, using one subplot per polygon. Behaviour and parameters are identical to `plot_weight`.

### Parameters

- `num_points` (`int`, default: `100`)  
  Number of sampling points between `self.field.s0.z` and `self.field.s1.z`.
- `poly_indices_to_plot` (`list[int]` or `None`, default: `None`)  
  List of **0-based** polygon indices to include in the plot. If `None`, all polygons are plotted.

---

## Selective polygon plotting

Both `plot_weight` and `plot_shear_weight` accept a `poly_indices_to_plot` argument to restrict the output to a subset of polygons. This is useful when a section contains many polygons and only a few are of interest.

```python
viz = Visualizer(section_field)

# Plot only the first polygon (index 0) for both weight and shear weight
viz.plot_weight(num_points=100, poly_indices_to_plot=[0])
viz.plot_shear_weight(num_points=100, poly_indices_to_plot=[0])

plt.show()
```

Pass a list with multiple indices to plot more than one polygon:

```python
viz.plot_weight(num_points=100, poly_indices_to_plot=[0, 1])
viz.plot_shear_weight(num_points=100, poly_indices_to_plot=[0, 1])
```

If `poly_indices_to_plot` is omitted or set to `None`, all polygons are plotted (original behaviour).
