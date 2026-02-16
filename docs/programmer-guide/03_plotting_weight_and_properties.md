# 02 — Plotting propertis and polygon weigth

## Purpose

After checking numeric outputs, use plots propertis and weigth along  `z` 

This chapter covers:
-  plots propertis
-  weigth
---

## Imports

```python
from csf import (
    Pt, Polygon, Section, ContinuousSectionField, Visualizer,
    section_full_analysis, section_print_analysis, section_full_analysis_keys
)
import matplotlib.pyplot as plt
```

---

## Minimal Example

```python
viz = Visualizer(section_field)

viz.plot_properties( ["A","I1","I2","Ixy","J_s_vroark","J_s_vroark_fidelity",])

plt.show()

```

---


# `plot_properties` and `plot_weight` — Input Parameters

## `plot_properties(...)`

```python
plot_properties(self, keys_to_plot=None, alpha=1, num_points=100)
```

Plot selected section properties along `z` and report min/max values with their corresponding `z` locations.

### Parameters

- `keys_to_plot` (`list[str] | None`, default: `None`)  
  Property keys to evaluate/plot (for example: `["A", "Ix", "Iy"]`).  
  If `None`, it is treated as an empty list (no series plotted).

- `alpha` (`float`, default: `1`)  
  Passed to `section_full_analysis(...)` for API consistency.

- `num_points` (`int`, default: `100`)  
  Number of sampling points between `self.field.s0.z` and `self.field.s1.z`.

### Behavior Notes

- Sections are evaluated at `np.linspace(z_start, z_end, num_points)`.
- Missing keys are stored as `NaN` to keep alignment with `z_values`.
- For each key, the function computes:
  - `min(value)` with `z_min`
  - `max(value)` with `z_max`
- Min/max points are marked on each curve.
- Subplot title format:  
  `min=<...>@z=<...>  max=<...>@z=<...>`
- Prints one summary line per key to stdout.

### Return

- No explicit return value (plot is shown with `plt.show()`).

---

## `plot_weight(...)`

```python
plot_weight(self, num_points=100)
```

Plot interpolated polygon weights `w(z)` along the member axis, one subplot per polygon.

### Parameters

- `num_points` (`int`, default: `100`)  
  Number of sampling points between `self.field.s0.z` and `self.field.s1.z`.

### Behavior Notes

- For each sampled `z` and each polygon index `i`, the function computes:
  - `p0 = self.field.s0.polygons[i]`
  - `p1 = self.field.s1.polygons[i]`
  - optional law from `self.field.weight_laws[i+1]` (if available)
  - interpolated weight via `self.field._interpolate_weight(...)`
- Produces one subplot per polygon with:
  - y-label: `s0 <name0> - s1 <name1>`
  - auto y-limits with margin
  - grid and per-polygon title
- Adds global figure title with interpolation point count.

### Return

- No explicit return value (plot is shown with `plt.show()`).
