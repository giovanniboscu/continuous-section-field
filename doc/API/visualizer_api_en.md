# API Reference - `visualizer.py`

This document covers the top-level classes and functions defined in `src/csf/visualizer.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/visualizer.py`
- Output file: `doc/API/visualizer_api_en.md`
- Top-level function definitions found: `1`.
- Top-level classes found: `1`.
- Duplicate function names found: `0`.

## Public API index

- `Visualizer` - line 95
- `def plot_section_variationstations_data: Sequence[Dict[str, Any]], plot_stations_data: Optional[Sequence[Dict[str, Any]]]=None, filename: str='section_variation.png', show: bool=False` - line 27

## API details

## Classes

### `Visualizer`

**Source lines:** `95-1687`

```python
class Visualizer
```

**Summary:** Adds 2D and 3D plotting utilities on top of a ContinuousSectionField.

**Methods visible in the code**

- `__init__` - line 100
- `plot_weight` - line 107
- `plot_shear_weight` - line 289
- `plot_properties` - line 483
- `plot_section_2d` - line 835
- `plot_volume_3d` - line 1061

#### Method details

##### `Visualizer.__init__`

**Source lines:** `100-101`

```python
def __init__self, field: ContinuousSectionField
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `field` | `positional or keyword` | `ContinuousSectionField` | `-` |

**Returns:** `not annotated`

##### `Visualizer.plot_weight`

**Source lines:** `107-284`

```python
def plot_weightself, num_points=100, tol=1e-12, poly_indices_to_plot=None
```

**Summary:** Plot w(z) per polygon pair, skipping polygons with w(z) == 0 for all sampled z.

**Docstring details**

```text
Skipped polygons are listed in a figure note.
Min/Max markers are shown on each plotted curve.

Parameters
----------
num_points : int
    Number of z sample points in [s0.z, s1.z].
tol : float
    Absolute tolerance used to classify a polygon as "zero-flat" over sampled z.
poly_indices_to_plot : list[int] | tuple[int] | set[int] | None
    Optional explicit polygon indices to plot (0-based). Can include gaps (e.g., [0, 2, 5]).
    If provided, only indices in this list are considered, after removing zero-flat polygons.
    Indices out of range are ignored.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `num_points` | `positional or keyword` | `not annotated` | `100` |
| `tol` | `positional or keyword` | `not annotated` | `1e-12` |
| `poly_indices_to_plot` | `positional or keyword` | `not annotated` | `None` |

**Returns:** `not annotated`

**Raises visible in the code**

- `TypeError`

**Function/method calls visible in the code**

`np.linspace`, `len`, `range`, `np.asarray`, `np.all`, `set`, `print`, `set_xlabel`, `fig_w.suptitle`, `fig_w.tight_layout`, `self.field._interpolate_weight`, `append`, `np.isclose`, `zero_polys.append`, `plot_indices.append`, `isinstance`, `TypeError`, `int`, `plt.subplots`, `list`, `ax.plot`, `ax.scatter`, `ax.annotate`, `ax.set_ylim`, `ax.set_ylabel`, `ax.grid`, `ax.set_title`, `fig_w.text`, `float`, `requested.append`, `np.ravel`, `np.argmin`, `np.argmax`, `max`, `join`, `abs`

##### `Visualizer.plot_shear_weight`

**Source lines:** `289-478`

```python
def plot_shear_weightself, num_points=100, tol=1e-12, poly_indices_to_plot=None
```

**Summary:** Plot w(z) per polygon pair, skipping polygons with w(z) == 0 for all sampled z.

**Docstring details**

```text
Skipped polygons are listed in a figure note.
Min/Max markers are shown on each plotted curve.

Parameters
----------
num_points : int
    Number of z sample points in [s0.z, s1.z].
tol : float
    Absolute tolerance used to classify a polygon as "zero-flat" over sampled z.
poly_indices_to_plot : list[int] | tuple[int] | set[int] | None
    Optional explicit polygon indices to plot (0-based). Can include gaps (e.g., [0, 2, 5]).
    If provided, only indices in this list are considered, after removing zero-flat polygons.
    Indices out of range are ignored.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `num_points` | `positional or keyword` | `not annotated` | `100` |
| `tol` | `positional or keyword` | `not annotated` | `1e-12` |
| `poly_indices_to_plot` | `positional or keyword` | `not annotated` | `None` |

**Returns:** `not annotated`

**Raises visible in the code**

- `TypeError`

**Function/method calls visible in the code**

`np.linspace`, `len`, `range`, `np.asarray`, `np.all`, `set`, `print`, `set_xlabel`, `fig_w.suptitle`, `fig_w.tight_layout`, `self.field._interpolate_weight`, `self.field._interpolate_shear_weight`, `append`, `np.isclose`, `zero_polys.append`, `plot_indices.append`, `isinstance`, `TypeError`, `int`, `plt.subplots`, `list`, `ax.plot`, `ax.scatter`, `ax.annotate`, `ax.set_ylim`, `ax.set_ylabel`, `ax.grid`, `ax.set_title`, `fig_w.text`, `float`, `requested.append`, `np.ravel`, `np.argmin`, `np.argmax`, `max`, `join`, `abs`

##### `Visualizer.plot_properties`

**Source lines:** `483-831`

```python
def plot_propertiesself, keys_to_plot=None, alpha=1, title: str='Plot Properties', num_points=100
```

**Summary:** Plot the evolution of selected section properties along the Z-axis.

**Docstring details**

```text
Generic behavior for returned values:
- If a property is scalar -> plot on left y-axis.
- If a property returns a pair (left_value, right_value):
    * left_value  is plotted on left y-axis
    * right_value is plotted on right y-axis (twin axis)

Title behavior:
- Right side (top): min/max summary of left channel (same style as before)
- Left side  (top): only t(z0), t(z1) when right channel exists

Args:
    keys_to_plot (list[str] | None):
        Property keys to plot (e.g., ["A", "Ix", "Iy"]).
        If None, defaults to empty list.
    alpha (float):
        Passed through to section_full_analysis.
    num_points (int):
        Number of z samples between s0.z and s1.z.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `keys_to_plot` | `positional or keyword` | `not annotated` | `None` |
| `alpha` | `positional or keyword` | `not annotated` | `1` |
| `title` | `positional or keyword` | `str` | `'Plot Properties'` |
| `num_points` | `positional or keyword` | `not annotated` | `100` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`np.linspace`, `len`, `plt.subplots`, `fig.suptitle`, `plt.cm.viridis`, `enumerate`, `set_xlabel`, `plt.tight_layout`, `list`, `self.field.section`, `section_full_analysis`, `str`, `zip`, `np.asarray`, `np.isfinite`, `bool`, `int`, `float`, `ax.plot`, `ax.scatter`, `np.isclose`, `ax.set_ylim`, `ax.set_ylabel`, `ax.grid`, `ax.text`, `print`, `dict.fromkeys`, `np.any`, `ax.twinx`, `ax_r.plot`, `ax_r.set_ylabel`, `ax_r.grid`, `np.argmin`, `np.argmax`, `ax.annotate`, `max`, `lower`, `append`, `isinstance`, `abs`, `dict`

##### `Visualizer.plot_section_2d`

**Source lines:** `835-1058`

```python
def plot_section_2dself, z: float, show_ids: bool=True, show_weights: bool=True, show_vertex_ids: bool=False, show_legenda: bool=True, title: Optional[str]=None, ax=None
```

**Summary:** Draw the 2D section at a given longitudinal coordinate z.

**Docstring details**

```text
This implementation places the legend BELOW the plot and computes layout
dynamically from real rendered sizes (no fixed "magic" vertical offsets).

Why this version is robust
--------------------------
- Legend is anchored in FIGURE coordinates, not AXES coordinates.
- After first draw, legend height is measured from renderer bbox.
- Bottom subplot margin is then adjusted to reserve exactly enough space.
- Legend is finally repositioned inside that reserved strip.

Result:
- No overlap between legend and axes.
- No clipping/cut-off of legend text.
- Works with different font sizes, DPI, and label lengths.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `show_ids` | `positional or keyword` | `bool` | `True` |
| `show_weights` | `positional or keyword` | `bool` | `True` |
| `show_vertex_ids` | `positional or keyword` | `bool` | `False` |
| `show_legenda` | `positional or keyword` | `bool` | `True` |
| `title` | `positional or keyword` | `Optional[str]` | `None` |
| `ax` | `positional or keyword` | `not annotated` | `None` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`self.field.section`, `enumerate`, `self.field.build_direct_children_map`, `children_map.items`, `range`, `ax.set_aspect`, `ax.set_xlabel`, `ax.set_ylabel`, `ax.grid`, `ax.set_title`, `fig.canvas.draw`, `plt.subplots`, `ax.plot`, `line.get_color`, `poly_colors.append`, `len`, `float`, `_w_abs_z`, `fig.set_constrained_layout`, `min`, `ax.legend`, `fig.canvas.get_renderer`, `leg.get_window_extent`, `bbox.transformed`, `ax.text`, `container_id_by_sec.append`, `getattr`, `Line2D`, `strip`, `legend_labels.append`, `max`, `fig.transFigure.inverted`, `fig.subplots_adjust`, `xs.append`, `ys.append`, `sum`, `legend_handles.append`, `HandlerTuple`

##### `Visualizer.plot_volume_3d`

**Source lines:** `1061-1687`

```python
def plot_volume_3dself, show_end_sections: bool=True, line_percent: float=100.0, seed: int | str=0, title: str='Ruled volume (vertex-connection lines)', ax=None, equalize_z: bool=False
```

**Summary:** Draw the 3D ruled "skeleton":

**Docstring details**

```text
- endpoint section outlines (optional)
- straight lines connecting corresponding vertices (ruled generators)
- ability to display only a percentage of those lines for readability

Parameters
----------
equalize_z : bool, default False
    If True, the visual box is proportional to the real data ranges
    (1 unit along Z = 1 unit along X/Y).  Achieved by passing the
    actual data ranges to ``set_box_aspect`` — no coordinates or
    axis limits are modified.  When False the plot is identical to
    the original.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `show_end_sections` | `positional or keyword` | `bool` | `True` |
| `line_percent` | `positional or keyword` | `float` | `100.0` |
| `seed` | `positional or keyword` | `int | str` | `0` |
| `title` | `positional or keyword` | `str` | `'Ruled volume (vertex-connection lines)'` |
| `ax` | `positional or keyword` | `not annotated` | `None` |
| `equalize_z` | `positional or keyword` | `bool` | `False` |

**Returns:** `not annotated`

**Returned dictionary keys visible in the code**

`x`, `y`, `z`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`isinstance`, `self.field.section`, `_thickness_line_from_section_points`, `_random.Random`, `_rng.shuffle`, `len`, `defaultdict`, `enumerate`, `sum`, `z_planes.append`, `edges_by_style.items`, `ax.set_xlim`, `ax.set_ylim`, `ax.set_zlim`, `ax.set_xlabel`, `ax.set_ylabel`, `ax.set_zlabel`, `ax.set_title`, `seed.strip`, `seed_str.lower`, `int`, `max`, `zip`, `range`, `_interpolate_vertex`, `_add_edge`, `plt.figure`, `fig.add_subplot`, `ax.view_init`, `extend`, `_to_float_or_none`, `_normalize_weight`, `lines_by_polygon.append`, `polygon_base_colors.append`, `list`, `Normalize`, `ScalarMappable`, `sm.set_array`, `ax.figure.colorbar`, `cbar.set_label`, `np.linspace`, `cbar.set_ticks`, `cbar.set_ticklabels`, `min`, `ax.set_box_aspect`, `_set_axes_equal_3d`, `abs`, `float`, `poly_lines.append`, `sorted`, `z_planes_local.append`, `ax.plot`, `LinearSegmentedColormap.from_list`, `seed_lower.startswith`, `isdigit`, `z_values.append`, `values.append`, `np.ceil`, `_add_polygon_boundary`, `eligible_polygon_indices.append`, `eligible_counts.append`, `getattr`, `poly_weights.append`, `_get_semantic_color`, `math.ceil`, `math.floor`, `append`, `global_numeric_weights.append`, `poly_numeric_weights.append`, `_add_generator_segment`, `ValueError`

## Functions

## Top-level functions

### `plot_section_variation`

**Source lines:** `27-89`

```python
def plot_section_variationstations_data: Sequence[Dict[str, Any]], plot_stations_data: Optional[Sequence[Dict[str, Any]]]=None, filename: str='section_variation.png', show: bool=False
```

**Summary:** Plot a quick visual preview of how a few properties vary along z.

**Docstring details**

```text
stations_data:
    Station dictionaries used as markers, typically Lobatto or user stations.

plot_stations_data:
    Optional denser station dictionaries used for continuous plot curves.
    If None, stations_data is used for both curves and markers.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `stations_data` | `positional or keyword` | `Sequence[Dict[str, Any]]` | `-` |
| `plot_stations_data` | `positional or keyword` | `Optional[Sequence[Dict[str, Any]]]` | `None` |
| `filename` | `positional or keyword` | `str` | `'section_variation.png'` |
| `show` | `positional or keyword` | `bool` | `False` |

**Returns:** `str`

**Function/method calls visible in the code**

`plt.subplots`, `ax1.plot`, `ax1.set_ylabel`, `ax1.grid`, `ax1.legend`, `ax1.set_title`, `ax2.plot`, `ax2.set_xlabel`, `ax2.set_ylabel`, `ax2.grid`, `ax2.legend`, `plt.tight_layout`, `plt.savefig`, `plt.show`, `plt.close`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
