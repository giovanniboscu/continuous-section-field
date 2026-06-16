# API Reference - `visualizer.py`

This document covers the APIs defined in `visualizer.py`.

## Module summary

- Top-level functions found: `1`.
- Top-level classes found: `1`.
- Main class: `Visualizer`.
- Plotting backend: `matplotlib.pyplot`.

## Local dependencies used by the file

```python
from .continuous_section_field import ContinuousSectionField
from .continuous_section_field import _set_axes_equal_3d
from .section_field import section_full_analysisa
```

The file also uses NumPy, Matplotlib, `LinearSegmentedColormap`, `Normalize`, and `ScalarMappable`.

---

# Top-level functions

## `plot_section_variation`

```python
def plot_section_variation(
    stations_data: Sequence[Dict[str, Any]],
    plot_stations_data: Optional[Sequence[Dict[str, Any]]] = None,
    filename: str = "section_variation.png",
    show: bool = False,
) -> str
```

Plots a quick preview of selected section-property variation along `z`.

## Parameters

| Name | Type | Default | Description |
|---|---|---:|---|
| `stations_data` | `Sequence[Dict[str, Any]]` | - | Station dictionaries used as markers. |
| `plot_stations_data` | `Optional[Sequence[Dict[str, Any]]]` | `None` | Optional denser station dictionaries used for continuous plot curves. If `None`, `stations_data` is used. |
| `filename` | `str` | `"section_variation.png"` | Output image filename. |
| `show` | `bool` | `False` | If true, displays the plot interactively. Otherwise closes the figure after saving. |

## Required station keys

The function reads the following keys from each station dictionary:

| Key | Used for |
|---|---|
| `z` | horizontal axis |
| `A` | area curve |
| `Ix` | `I33 (Ix)` curve |
| `Iy` | `I22 (Iy)` curve |
| `Ip` | polar moment curve |

## Returns

| Type | Description |
|---|---|
| `str` | The output filename. |

---

# Class `Visualizer`

```python
class Visualizer:
```

Adds 2D and 3D plotting utilities on top of a `ContinuousSectionField`.

## Constructor

### `__init__`

```python
def __init__(self, field: ContinuousSectionField)
```

Stores the input field as:

```python
self.field = field
```

| Parameter | Type | Description |
|---|---|---|
| `field` | `ContinuousSectionField` | CSF field used by all plotting methods. |

---

# Public methods

## `plot_weight`

```python
def plot_weight(
    self,
    num_points=100,
    tol=1e-12,
    poly_indices_to_plot=None,
)
```

Plots `w(z)` for polygon pairs. Polygons whose sampled `w(z)` is zero for all sampled stations are skipped.

## Parameters

| Name | Type | Default | Description |
|---|---|---:|---|
| `num_points` | not annotated | `100` | Number of sampled `z` points between `self.field.s0.z` and `self.field.s1.z`. |
| `tol` | not annotated | `1e-12` | Absolute tolerance used to classify a polygon as zero-flat. |
| `poly_indices_to_plot` | not annotated | `None` | Optional explicit list/tuple/set of 0-based polygon indices to plot. |

## Behavior visible in the code

- Samples `z` with `np.linspace(z_start, z_end, num_points)`.
- Evaluates each polygon weight using `self.field._interpolate_weight(...)`.
- Uses `self.field.weight_laws` when present.
- Skips polygons whose sampled weight is zero within `tol`.
- Filters by `poly_indices_to_plot` when provided.
- Creates at most two polygon plots per figure.
- Marks minimum and maximum weight values on each curve.
- Returns `None`.

## Errors

| Error | Condition |
|---|---|
| `TypeError` | `poly_indices_to_plot` is not `list`, `tuple`, `set`, or `None`. |
| `TypeError` | `poly_indices_to_plot` contains non-integer values. |

---

## `plot_shear_weight`

```python
def plot_shear_weight(
    self,
    num_points=100,
    tol=1e-12,
    poly_indices_to_plot=None,
)
```

Plots shear-weight distribution along `z` for polygon pairs.

## Parameters

| Name | Type | Default | Description |
|---|---|---:|---|
| `num_points` | not annotated | `100` | Number of sampled `z` points between `self.field.s0.z` and `self.field.s1.z`. |
| `tol` | not annotated | `1e-12` | Absolute tolerance used to classify a polygon as zero-flat. |
| `poly_indices_to_plot` | not annotated | `None` | Optional explicit list/tuple/set of 0-based polygon indices to plot. |

## Behavior visible in the code

- Samples `z` with `np.linspace(z_start, z_end, num_points)`.
- Evaluates the base weight using `self.field._interpolate_weight(...)`.
- Evaluates shear-weight using `self.field._interpolate_shear_weight(...)`.
- Uses `self.field.weight_laws` and `self.field.shear_weight_laws` when present.
- Skips polygons whose sampled shear-weight is zero within `tol`.
- Filters by `poly_indices_to_plot` when provided.
- Creates at most two polygon plots per figure.
- Marks minimum and maximum values on each curve.
- Returns `None`.

## Errors

| Error | Condition |
|---|---|
| `TypeError` | `poly_indices_to_plot` is not `list`, `tuple`, `set`, or `None`. |
| `TypeError` | `poly_indices_to_plot` contains non-integer values. |

---

## `plot_properties`

```python
def plot_properties(
    self,
    keys_to_plot=None,
    alpha=1,
    title: str = "Plot Properties",
    num_points=100,
)
```

Plots selected section properties along the field coordinate `z`.

## Parameters

| Name | Type | Default | Description |
|---|---|---:|---|
| `keys_to_plot` | not annotated | `None` | Property keys to plot. `"geometry"` is explicitly filtered out. |
| `alpha` | not annotated | `1` | Present in the signature. In the current method body, this parameter is not passed to `section_full_analysis`. |
| `title` | `str` | `"Plot Properties"` | Figure title. |
| `num_points` | not annotated | `100` | Number of sampled `z` points. |

## Behavior visible in the code

- Removes duplicate keys while preserving order.
- Removes any key whose lowercase form is `"geometry"`.
- If `keys_to_plot` is empty or `None`, returns without plotting.
- Samples `z` with `np.linspace(z_start, z_end, num_points)`.
- Calls:

```python
section_full_analysis(
    current_section,
    compute_vroark=need_vroark,
)
```

- Sets `need_vroark=True` only when `J_s_vroark` or `J_s_vroark_fidelity` is requested.
- For scalar properties, plots the value on the left y-axis.
- For 2-item sequences, plots the first item on the left y-axis and the second item on a right twin y-axis.
- Adds min/max markers and min/max text for the left-axis data.
- Returns `None`.

## Notes from the code

- The `alpha` argument appears in the signature and docstring but is not used as an argument in the call to `section_full_analysis`.
- Right-axis values are labelled as `thickness t`.

---

## `plot_section_2d`

```python
def plot_section_2d(
    self,
    z: float,
    show_ids: bool = True,
    show_weights: bool = True,
    show_vertex_ids: bool = False,
    show_legenda: bool = False,
    title: Optional[str] = None,
    ax=None,
)
```

Draws the 2D section at a given longitudinal coordinate `z`.

## Parameters

| Name | Type | Default | Description |
|---|---|---:|---|
| `z` | `float` | - | Longitudinal coordinate to evaluate. |
| `show_ids` | `bool` | `True` | If true, writes polygon IDs inside the plot. |
| `show_weights` | `bool` | `True` | Present in the signature. In the current method body it is not used. |
| `show_vertex_ids` | `bool` | `False` | If true, writes vertex indices. |
| `show_legenda` | `bool` | `False` | Present in the signature, but the method sets `show_legenda=True` internally. |
| `title` | `Optional[str]` | `None` | Plot title. If `None`, uses `Section at z=<z>`. |
| `ax` | not annotated | `None` | Optional Matplotlib axes. If `None`, a new figure and axes are created. |

## Behavior visible in the code

- Evaluates the section through `self.field.section(z)`.
- Draws each polygon outline.
- Optionally labels vertices.
- Optionally labels polygon IDs.
- Builds direct children mapping through `self.field.build_direct_children_map(z)`.
- Reconstructs absolute weights through the container chain.
- Builds legend entries with:
  - polygon ID;
  - relative weight `w`;
  - polygon name;
  - container ID.
- Sets equal aspect ratio.
- Places the legend below the axes.
- Returns the Matplotlib axes object.

## Notes from the code

- `show_weights` is not used in the current method body.
- `show_legenda` is overwritten inside the method with `show_legenda=True`, so the default argument does not control the final behavior in the current implementation.

---

## `plot_volume_3d`

```python
def plot_volume_3d(
    self,
    show_end_sections: bool = True,
    line_percent: float = 100.0,
    seed: int | str = 0,
    title: str = "Ruled volume (vertex-connection lines)",
    ax=None,
    equalize_z: bool = False,
)
```

Draws a 3D ruled skeleton of the CSF member.

## Parameters

| Name | Type | Default | Description |
|---|---|---:|---|
| `show_end_sections` | `bool` | `True` | If true, draws endpoint section outlines. |
| `line_percent` | `float` | `100.0` | Percentage of generator lines to display. |
| `seed` | `int | str` | `0` | Numeric seed for color shuffling, or string mode for semantic coloring. |
| `title` | `str` | `"Ruled volume (vertex-connection lines)"` | Plot title. |
| `ax` | not annotated | `None` | Optional Matplotlib 3D axes. If `None`, a new figure and 3D axes are created. |
| `equalize_z` | `bool` | `False` | If true, uses data ranges in `set_box_aspect`; otherwise uses `_set_axes_equal_3d(ax)`. |

## `seed` modes

| `seed` value | Behavior |
|---|---|
| integer | Standard color-by-polygon mode. |
| `"w"` | Semantic coloring by `weightabs`, default resolution. |
| `"wN"` | Semantic coloring by `weightabs`, with resolution `N`; example: `"w100"`. |
| `"s"` | Semantic coloring by `shear_weightabs`, default resolution. |
| `"sN"` | Semantic coloring by `shear_weightabs`, with resolution `N`; example: `"s100"`. |

## Behavior visible in the code

- Builds endpoint sections at `self.field.z0` and `self.field.z1`.
- Draws polygon boundaries when `show_end_sections=True`.
- Connects corresponding vertices with ruled generator segments.
- Supports line subsampling through `line_percent`.
- Groups 3D line segments by style before rendering.
- In semantic coloring mode:
  - `w` uses `weightabs`;
  - `s` uses `shear_weightabs`;
  - a colorbar is added.
- Sets explicit `x`, `y`, and `z` limits.
- Sets axis labels `X`, `Y`, `Z`.
- Returns the Matplotlib 3D axes object.

## Errors

| Error | Condition |
|---|---|
| `ValueError` | Unknown string value for `seed`. |

## Notes from the code

- Allowed string modes in the error message mention only `w`/`wN`, but the implementation also accepts `s`/`sN`.
- When `equalize_z=False`, axis scaling is delegated to `_set_axes_equal_3d(ax)`.
