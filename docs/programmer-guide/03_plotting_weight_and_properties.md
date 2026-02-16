# 02 — Plotting propertis

## Purpose

After checking numeric outputs, use plots propertis along  `z` 

This chapter covers:
-  plots propertis

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
![properties](https://github.com/user-attachments/assets/d0193807-26eb-48ef-bba2-482047e95366)

---


# `plot_properties`

## `plot_properties(...)`

```python
plot_properties(self, keys_to_plot=None, alpha=1, num_points=100)
```

# `plot_properties` — Input Parameters

```python
plot_properties(self, keys_to_plot=None, alpha=1, num_points=100)
```

Plot the evolution of selected section properties along `z`, highlighting min/max values and their corresponding `z` positions.

## Parameters

- `keys_to_plot` (`list[str] | None`, default: `None`)  
  Property keys to evaluate and plot (for example: `["A", "Ix", "Iy"]`).  
  If `None`, it is treated as an empty list (no properties plotted).

- `alpha` (`float`, default: `1`)  
  Forwarded to `section_full_analysis(...)` for API consistency.

- `num_points` (`int`, default: `100`)  
  Number of sampling points between `self.field.s0.z` and `self.field.s1.z`.

## Behavior

- Sampling coordinates are generated with `np.linspace(z_start, z_end, num_points)`.
- For each sampled `z`, the function evaluates:
  - interpolated section: `self.field.section(z)`
  - section properties: `section_full_analysis(current_section, alpha=alpha)`
- For each requested key:
  - values below `EPS_L` are set to `0.0`
  - missing keys are stored as `NaN` (to preserve array alignment)
- One subplot is created per key.
- Min and max are computed on finite values only and shown:
  - as markers on the curve
  - in subplot title: `min=<...>@z=<...>  max=<...>@z=<...>`
  - in stdout: `min=... at z=... | max=... at z=...`

## Output

- Produces matplotlib plots (`plt.show()`).
- No explicit return value.

## Notes

- If `keys_to_plot` is empty, the function shows an empty figure and returns.
- The x-axis label includes the selected `alpha` value.
