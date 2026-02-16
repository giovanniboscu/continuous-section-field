# 02 - Plotting Sections and Volume

## Introduction

After verifying section properties programmatically, the next step is visual validation.

This chapter focuses on plotting workflows that help confirm geometry, interpolation quality, and model consistency along `z`.  
The goal is practical: quickly detect modeling mistakes before downstream structural analysis.

You will use plotting to inspect:

- section shape at selected stations,
- geometric evolution along the member axis,
- full volume representation from `S0` to `S1`,
- side-by-side comparisons between stations.

---
Import the import headers
```bash
# --- Core CSF imports used in this minimal example ---
from csf import (
    Pt, Polygon, Section, ContinuousSectionField,Visualizer,
    section_full_analysis, section_print_analysis,section_full_analysis_keys
)
```

# `plot_volume_3d` — Input Parameters

```python
plot_volume_3d(
    show_end_sections: bool = True,
    line_percent: float = 100.0,
    seed: int = 0,
    title: str = "Ruled volume (vertex-connection lines)",
    ax=None
)
```

Draws a 3D ruled skeleton of a `ContinuousSectionField` using:
- optional end-section outlines (`z0` and `z1`),
- straight generator lines between corresponding vertices,
- optional random subsampling of lines for readability.

## Parameters

### `show_end_sections` (`bool`, default: `True`)
If `True`, plots the polygon outlines of both endpoint sections (`z0` and `z1`).
- Useful to visualize the boundary transition between start and end geometry.
- If `False`, only generator lines are drawn.

### `line_percent` (`float`, default: `100.0`)
Percentage of generator lines to display.
- Valid range: `[0.0, 100.0]`
- `100.0` = draw all lines
- `< 100.0` = draw a random subset for cleaner visualization
- If outside `[0, 100]`, raises:
  - `ValueError("line_percent must be within [0, 100].")`

### `seed` (`int`, default: `0`)
Random seed used only when `line_percent < 100.0`.
- Ensures reproducible subsampling of generator lines.
- Same geometry + same seed + same `line_percent` => same selected lines.

### `title` (`str`, default: `"Ruled volume (vertex-connection lines)"`)
Title text applied to the 3D axis via `ax.set_title(title)`.

### `ax` (matplotlib 3D axis, default: `None`)
Target axis for plotting.
- If `None`, the function creates a new figure and 3D axis with default view:
  - `elev=15`, `azim=120`
- If provided, plotting is performed on the given axis.

## Return Value

### `ax`
Returns the matplotlib 3D axis used for plotting (created or provided).

## Notes

- The function samples sections at `self.field.z0` and `self.field.z1`.
- Generator lines are built by zipping:
  - polygons from start/end sections,
  - vertices from corresponding polygons.
- Axes are labeled (`X`, `Y`, `Z`) and normalized with `_set_axes_equal_3d(ax)`.
