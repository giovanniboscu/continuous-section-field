# 02 - Plotting Sections and Volume

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

[boxcell.yaml](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/boxcell.yaml)


```python
# CSF YAML reader and controlled issue reporting.
from csf.io.csf_reader import CSFReader
from csf.io.csf_issues import CSFIssues

# Matplotlib is used to display the figures created by the CSF Visualizer.
import matplotlib.pyplot as plt

# CSF public entities, field representation, visualization,
# and sectional-analysis utilities.
from csf import (
    Pt, Polygon, Section, ContinuousSectionField, Visualizer,
    section_full_analysis, section_print_analysis, section_full_analysis_keys
)


# Read, validate, and build the ContinuousSectionField defined in the YAML file.
# read_file() returns a ReadResult containing the field and any detected issues.
res = CSFReader().read_file("boxcell.yaml")

# A ReadResult is valid when no ERROR issues are present.
# If validation fails, print the controlled CSF issue report and stop execution.
if not res.ok:
    print(CSFIssues.format_report(res.issues))
    raise SystemExit(1)

# Retrieve the validated ContinuousSectionField created by the reader.
field = res.field


# Evaluate the continuous field at z = 10.0, obtaining the corresponding
# interpolated cross-section.
sec = field.section(10.0)

# Perform the complete sectional analysis of the selected section.
# The returned dictionary includes geometric properties, centroid,
# inertias, principal properties, section moduli, statical moment,
# and available Saint-Venant torsional estimates.
out = section_full_analysis(sec)


# Create a visualizer associated with the ContinuousSectionField.
viz = Visualizer(field)

# Plot the 3D ruled skeleton of the field.
# line_percent=100.0 displays all vertex-connection generator lines.
# seed controls generator-line selection when only a percentage is displayed.
# equalize_z=False leaves the Z-axis without real-range aspect equalization.
viz.plot_volume_3d(
    line_percent=100.0,
    seed=42,
    equalize_z=False
)

# Plot the 2D cross-section evaluated at z = 0.
# Polygon IDs are not displayed; the other visualization options
# retain their default values.
viz.plot_section_2d(
    z=0,
    show_ids=False
)

# Display all Matplotlib figures created above.
plt.show()


```

---

## `plot_volume_3d(...)`

```python
plot_volume_3d(
    show_end_sections=True,
    line_percent=100.0,
    seed=0,
    title="Ruled volume (vertex-connection lines)",
    ax=None
)
```

### Parameters
- `show_end_sections` (`bool`, default `True`)  
  Plot outlines at `z0` and `z1`.

- `line_percent` (`float`, default `100.0`)  
  Percentage of vertex-connection lines to draw (`0..100`).  
  Out-of-range values raise `ValueError`.

- `seed` (`int | str`, default `0`)  
  Controls line sampling and, optionally, line coloring.

  - Integer values keep the standard seeded behavior for reproducible subsampling when `line_percent < 100`.
  - String value `"w"` activates weight-based coloring of the generator lines using `w(z)`, with default weight-resolution `100`.
  - String value `"w<number>"` activates the same weight-based coloring, with `<number>` interpreted as the weight-resolution used by the graphic engine.

- `title` (`str`)  
  Plot title.

- `ax` (matplotlib 3D axis or `None`)  
  Reuse an existing axis or create a new one.

### Returns
- `ax`: the 3D axis used for plotting.

### Notes
- In weight-color mode (`seed="w"` or `seed="w<number>"`), the lines forming the ruled volume are colored according to the variation of `w(z)`.
- `seed="w"` is equivalent to using weight-resolution `100`.
- If `w(z)` is constant, the lines are drawn in **black**.
- If `w(z)` varies:
  - **red** = weight at full value (`w ≈ 1.0`, intact shell)
  - **blue** = weight reduced relative to its maximum


### Notes
- Sections are sampled at `self.field.z0` and `self.field.z1`.
- Generator lines connect corresponding vertices.
- Equal 3D scaling is applied.

---

## `plot_section_2d(...)`

```python
    
    plot_section_2d(
        z=zsec_val,
        show_ids = True,
        show_weights = True,
        show_vertex_ids = False,
        title = "plot 2d",
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
