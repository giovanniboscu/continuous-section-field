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

```
    # =================================================================
    # 3D and 2D
    # =================================================================
    viz = Visualizer(section_field)
    ax = viz.plot_volume_3d(line_percent=30.0, seed=42)

   
    viz.plot_section_2d(z=zsec_val,show_ids=False)  
    plt.show()
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

---

# `plot_section_2d` — Input Parameters

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

Draws the 2D cross-section of a `ContinuousSectionField` at a given longitudinal coordinate `z`.

This implementation is designed to keep the legend below the plot without overlap/clipping, using rendered-size-aware layout behavior.

## Parameters

### `z` (`float`, required)
Longitudinal coordinate where the section is sampled.
- The function evaluates `sec = self.field.section(z)`.
- This is the only required input parameter.

### `show_ids` (`bool`, default: `True`)
If `True`, writes polygon IDs inside each polygon.
- IDs are shown as `ID=<index>`.
- Position is the simple mean of vertex coordinates for each polygon.

### `show_weights` (`bool`, default: `True`)
Flag intended for weight-related display behavior.
- Current implementation always includes relative weight `w` in legend labels.
- The parameter is part of the public signature and should be kept documented for API consistency.

### `show_vertex_ids` (`bool`, default: `False`)
If `True`, writes vertex indices near polygon vertices.
- Vertex numbering starts at `1` for each polygon.
- Text color matches the polygon outline color.

### `title` (`Optional[str]`, default: `None`)
Custom axis title.
- If `None`, title is auto-generated as: `Section at z=<value>`.

### `ax` (matplotlib axis, default: `None`)
Target axis for plotting.
- If `None`, a new figure/axis is created.
- If provided, plotting uses that existing axis and its figure.

## Return Value

### `ax`
Returns the matplotlib axis used for plotting (created or provided).

## What the function computes internally

- Polygon outline plotting (with automatic closure when needed).
- Optional in-plot annotations (`show_ids`, `show_vertex_ids`).
- Container mapping (derived from `self.field.s0` relationships and remapped by polygon name).
- Relative and reconstructed absolute weights at `z` along containment chains.
- Legend entries including:
  - polygon `ID`
  - relative weight `w`
  - polygon `name`
  - `container` ID (or `None`)

## Notes for documentation

- Legend title is: `Polygons (w is relative)`.
- Axes styling:
  - equal aspect ratio
  - `X` / `Y` labels
  - dotted grid
- The function performs a final canvas draw (`fig.canvas.draw()`) to finalize layout.
