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
