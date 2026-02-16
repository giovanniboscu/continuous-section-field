# 04 - Plotting Weight

## Purpose

Use weight plots to verify how each polygon weight `w(z)` evolves along the member axis.

This chapter covers:
- per-polygon weight interpolation plots

---

## Imports

```python
# --- Core CSF imports used in this minimal example ---
from csf import (
    Pt, Polygon, Section, ContinuousSectionField,Visualizer,
    section_full_analysis, section_print_analysis,section_full_analysis_keys
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
    Pt, Polygon, Section, ContinuousSectionField,Visualizer,
    section_full_analysis, section_print_analysis,section_full_analysis_keys
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
        weight=1.0,#<=
        name="upperpart",
    )

    poly_bottom_start = Polygon(
        vertices=(
            Pt(-b/2, -h/2),
            Pt( b/2, -h/2),
            Pt( b/2,  0.0),
            Pt(-b/2,  0.0),
        ),
        weight=1.5, # <= 
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
    # Extract one section and print full analysis
    # -------------------------------------------------------
    # Here z = 10.0, so this is exactly the end section (S1).
    zsec_val = 10.0
    sec_at_z = section_field.section(zsec_val)

    # =================================================================
    # Plot weight
    # =================================================================
    viz = Visualizer(section_field)
    viz.plot_weight(num_points=100)
    plt.show()
```
![Figure_1](https://github.com/user-attachments/assets/2c576be1-1dfb-46b0-abb6-c5fd8886edc7)

---

## `plot_weight(...)`

```python
plot_weight(self, num_points=100)
```

Plot interpolated polygon weights `w(z)` along the member axis, using one subplot per polygon.

## custom weight law

The weight can also be defined in functional form using this syntax:


```python
section_field.set_weight_laws([
    "startsection,endsection : f(z) or f(t)",
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


The following helper functions are available in weight-law expressions:

### Geometric and Data Functions

The following helper functions are available in weight-law expressions.

**Important:** polygon vertex indexing is **1-based** (the first vertex is `1`, not `0`).

### Geometric and Data Functions

| Function | Meaning | Example Law Expression |
| :--- | :--- | :--- |
| **`d(i, j)`** | Distance between vertex `i` and `j` at the **current** `z` | `w0 * d(1, 2)` |
| **`d0(i, j)`** | Distance between vertex `i` and `j` at the **start** section (`z = z0`) | `w0 * (d(1,2) / d0(1,2))` |
| **`d1(i, j)`** | Distance between vertex `i` and `j` at the **end** section (`z = z1`) | `w1 * (d(1,2) / d1(1,2))` |
| **`E_lookup(file)`** | Interpolated scalar read from an external text file | `E_lookup('stiffness.txt')` |
| **`T_lookup(file)`** | Interpolated scalar read from an external text file using normalized `t` in `[0, 1]` | `T_lookup('stiffness.txt')` |


# External Lookup Files for `E_lookup(...)` and `T_lookup(...)`

Lookup functions read values from a plain text **key-value** table.

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

Usage in a law expression:

```python

    # -------------------------------------------------------
    # Extract one section and print full analysis
    # -------------------------------------------------------
    # Here z = 10.0, so this is exactly the end section (S1).
    zsec_val = 10.0
    sec_at_z = section_field.section(zsec_val)

    section_field.set_weight_laws([
        "lowerpart,lowerpart : w0 + (w1 - w0) * 0.5 * (1 - np.cos(np.pi * z / L))", 
    ])
    
    # =================================================================
    # Plot weight
    # =================================================================
    viz = Visualizer(section_field)
    viz.plot_weight(num_points=100)
    plt.show()


```

---

## Example for `T_lookup(...)` (key = `t` in `[0, 1]`)

```txt
# stiffness_t.txt
0.00  1.00
0.25  0.92
0.50  0.85
0.75  0.78
1.00  0.70
```

Usage in a law expression:

```python
"T_lookup('stiffness_t.txt')"
```
For example, the following law can be defined along `z`:

```python
section_field.set_weight_laws([
    "lowerpart,lowerpart : w0 + (w1 - w0) * 0.5 * (1 - np.cos(np.pi * z / L))",
])
```

This represents a half-cosine smooth degradation law (also called a cosine ramp degradation), with gradual variation from w0 to w1 along the member length.



## Parameters

- `num_points` (`int`, default: `100`)  
  Number of sampling points between `self.field.s0.z` and `self.field.s1.z`.

## Behavior

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

## Output

- Produces matplotlib plots (`plt.show()`).
- No explicit return value.
