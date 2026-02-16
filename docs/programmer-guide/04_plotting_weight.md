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

## Minimal Example

```python
viz = Visualizer(section_field)

viz.plot_weight(num_points=100)

plt.show()
```

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
