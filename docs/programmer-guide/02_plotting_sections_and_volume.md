# 02 — Plotting Sections and Volume

## Purpose

After checking numeric outputs, use plots to validate geometry and interpolation along `z`.

This chapter covers:
- 2D section view at a given station,
- 3D ruled volume from `S0` to `S1`,
- quick visual checks for consistency and modeling errors.

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

# 3D ruled skeleton (30% of generator lines for readability)
viz.plot_volume_3d(line_percent=30.0, seed=42)

# 2D section at selected z
viz.plot_section_2d(z=zsec_val, show_ids=False)

plt.show()
```

---

## `plot_volume_3d(...)`

```python
plot_volume_3d(
    show_end_sections: bool = True,
    line_percent: float = 100.0,
    seed: int = 0,
    title: str = "Ruled volume (vertex-connection lines)",
    ax=None
)
```

### Parameters
- `show_end_sections` (`bool`, default `True`)  
  Plot outlines at `z0` and `z1`.

- `line_percent` (`float`, default `100.0`)  
  Percentage of vertex-connection lines to draw (`0..100`).  
  Out-of-range values raise `ValueError`.

- `seed` (`int`, default `0`)  
  Random seed for reproducible subsampling when `line_percent < 100`.

- `title` (`str`)  
  Plot title.

- `ax` (matplotlib 3D axis or `None`)  
  Reuse existing axis or create a new one.

### Returns
- `ax`: the 3D axis used for plotting.

### Notes
- Sections are sampled at `self.field.z0` and `self.field.z1`.
- Generator lines connect corresponding vertices.
- Equal 3D scaling is applied.

---

## `plot_section_2d(...)`

```python
plot_section_2d(
    z: float,
    show_ids: bool = True,
    show_weights: bool = True,
    show_vertex_ids: bool = False,
    title: Optional[str] = None,
    ax=None,
)
```

### Parameters
- `z` (`float`, required)  
  Station where the section is evaluated (`self.field.section(z)`).

- `show_ids` (`bool`, default `True`)  
  Show polygon IDs inside polygons.

- `show_weights` (`bool`, default `True`)  
  Weight-display flag in API (legend currently includes relative `w`).

- `show_vertex_ids` (`bool`, default `False`)  
  Show vertex numbering on each polygon.

- `title` (`Optional[str]`)  
  Custom title; default is `Section at z=<value>`.

- `ax` (matplotlib axis or `None`)  
  Reuse existing axis or create a new one.

### Returns
- `ax`: the 2D axis used for plotting.

### Notes
- Legend is placed below the axes to avoid overlap.
- Plot includes equal aspect ratio, grid, and `X/Y` labels.
- Internal mapping supports container-aware legend metadata (`container` info).
