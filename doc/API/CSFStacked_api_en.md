# API Reference - `CSFStacked.py`

This document covers the top-level classes and functions defined in `src/csf/CSFStacked.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/CSFStacked.py`
- Output file: `doc/API/CSFStacked_api_en.md`
- Top-level function definitions found: `0`.
- Top-level classes found: `3`.
- Duplicate function names found: `0`.

## Public API index

- `SegmentSpec` - line 20
- `StackSegment` - line 42
- `CSFStacked` - line 50

## API details

## Classes

### `SegmentSpec`

**Source lines:** `20-38`

**Decorators**

- `dataclass(frozen=True)`

```python
class SegmentSpec
```

**Summary:** Generic input specification for one stacked segment.

**Docstring details**

```text
Attributes:
- tag: segment identifier
- z0, z1: global z-interval for the segment
- polygons_s0: tuple of polygons at z0
- polygons_s1: tuple of polygons at z1

Notes:
- Polygon names should be consistent between z0 and z1 for side-surface pairing.
- For each polygon name, vertex count must match between z0 and z1.
```

### `StackSegment`

**Source lines:** `42-47`

**Decorators**

- `dataclass`

```python
class StackSegment
```

**Summary:** Runtime segment container: interval + CSF field.

### `CSFStacked`

**Source lines:** `50-1058`

```python
class CSFStacked
```

**Summary:** CSFStacked stacked container for multiple ContinuousSectionField objects.

**Docstring details**

```text
Design goals:
- CSFStacked geometry (any number of polygons per section)
- Global z dispatch
- Internal junction sections excluded by definition
- Explicit validation and clear errors
```

**Methods visible in the code**

- `__init__` - line 61
- `append` - line 65
- `append2` - line 111
- `field_at` - line 162
- `make_field_from_polygons` - line 168
- `build_from_specs` - line 184
- `validate_contiguity` - line 211
- `_find_segment` - line 239
- `section` - line 296
- `section_full_analysis` - line 299
- `_compute_axis_bounds_with_margin` - line 304
- `_apply_box_limits` - line 350
- `plot_weight` - line 358
- `plot_properties` - line 391
- `plot_section_2d` - line 642
- `plot_volume_3d` - line 686
- `plot_volume_3d_global` - line 729
- `global_bounds` - line 1049

#### Method details

##### `CSFStacked.__init__`

**Source lines:** `61-63`

```python
def __init__self, eps_z: float=1e-10
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `eps_z` | `positional or keyword` | `float` | `1e-10` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`float`

##### `CSFStacked.append`

**Source lines:** `65-108`

```python
def appendself, field: ContinuousSectionField
```

**Summary:** Append one pre-built ContinuousSectionField to the stack.

**Docstring details**

```text
...
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `field` | `positional or keyword` | `ContinuousSectionField` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`
- `RuntimeError`

**Function/method calls visible in the code**

`StackSegment`, `self.segments.append`, `float`, `ValueError`, `RuntimeError`, `len`

##### `CSFStacked.append2`

**Source lines:** `111-160`

```python
def append2self, field: ContinuousSectionField
```

**Summary:** Append one pre-built ContinuousSectionField to the stack.

**Docstring details**

```text
Stacking contract (strict, no hidden reordering):
- The new segment must have valid local bounds (z_end > z_start).
- If the stack is not empty, the new segment must start exactly after the
  previous segment, within ``self.eps_z`` tolerance.
- Gaps and overlaps are rejected immediately at append time.

Notes
-----
This method does not sort segments. The user-provided order is the stack order.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `field` | `positional or keyword` | `ContinuousSectionField` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `StackSegment`, `self.segments.append`, `ValueError`, `len`

##### `CSFStacked.field_at`

**Source lines:** `162-165`

```python
def field_atself, z: float, junction_side: str='left'
```

**Summary:** Return the segment field mapped from global z.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `junction_side` | `positional or keyword` | `str` | `'left'` |

**Returns:** `ContinuousSectionField`

**Function/method calls visible in the code**

`self._find_segment`, `float`

##### `CSFStacked.make_field_from_polygons`

**Source lines:** `168-182`

**Decorators**

- `staticmethod`

```python
def make_field_from_polygonsz0: float, z1: float, polygons_s0: Sequence[Polygon], polygons_s1: Sequence[Polygon]
```

**Summary:** Create one ContinuousSectionField from two generic polygon sets.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `polygons_s0` | `positional or keyword` | `Sequence[Polygon]` | `-` |
| `polygons_s1` | `positional or keyword` | `Sequence[Polygon]` | `-` |

**Returns:** `ContinuousSectionField`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`Section`, `ContinuousSectionField`, `ValueError`, `tuple`, `float`

##### `CSFStacked.build_from_specs`

**Source lines:** `184-209`

```python
def build_from_specsself, specs: List[SegmentSpec], sort_by_z: bool=False
```

**Summary:** Build the full stack from a list of ``SegmentSpec`` objects.

**Docstring details**

```text
Notes
-----
- Specs are consumed in the provided order (stack semantics).
- Automatic reordering is intentionally not supported.
- Contiguity/coherence is enforced by ``append()`` for each built segment.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `specs` | `positional or keyword` | `List[SegmentSpec]` | `-` |
| `sort_by_z` | `positional or keyword` | `bool` | `False` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`, `self.make_field_from_polygons`, `self.append`

##### `CSFStacked.validate_contiguity`

**Source lines:** `211-235`

```python
def validate_contiguityself, require_contiguity: bool=True
```

**Summary:** Validate ordering, overlap, and optional strict contiguity.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `require_contiguity` | `positional or keyword` | `bool` | `True` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`enumerate`, `ValueError`, `abs`

##### `CSFStacked._find_segment`

**Source lines:** `239-293`

```python
def _find_segmentself, z: float, junction_side: str='left'
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `junction_side` | `positional or keyword` | `str` | `'left'` |

**Returns:** `StackSegment`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `enumerate`, `ValueError`, `abs`, `len`

##### `CSFStacked.section`

**Source lines:** `296-297`

```python
def sectionself, z: float, junction_side: str='left'
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `junction_side` | `positional or keyword` | `str` | `'left'` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`section`, `float`, `self.field_at`

##### `CSFStacked.section_full_analysis`

**Source lines:** `299-302`

```python
def section_full_analysisself, z: float, junction_side: str='left'
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `junction_side` | `positional or keyword` | `str` | `'left'` |

**Returns:** `float`

**Function/method calls visible in the code**

`self.section`, `section_full_analysis`

##### `CSFStacked._compute_axis_bounds_with_margin`

**Source lines:** `304-347`

```python
def _compute_axis_bounds_with_marginself, xs: Sequence[float], ys: Sequence[float], zs: Sequence[float], margin_ratio: float=0.1
```

**Summary:** Compute axis-aligned limits with independent margins per axis.

**Docstring details**

```text
Returns:
    ((xmin, xmax), (ymin, ymax), (zmin, zmax), (dx, dy, dz))
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `xs` | `positional or keyword` | `Sequence[float]` | `-` |
| `ys` | `positional or keyword` | `Sequence[float]` | `-` |
| `zs` | `positional or keyword` | `Sequence[float]` | `-` |
| `margin_ratio` | `positional or keyword` | `float` | `0.1` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`, `min`, `max`

##### `CSFStacked._apply_box_limits`

**Source lines:** `350-356`

**Decorators**

- `staticmethod`

```python
def _apply_box_limitsax, bounds
```

**Summary:** Apply precomputed limits and set data-proportional box aspect.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `ax` | `positional or keyword` | `not annotated` | `-` |
| `bounds` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`ax.set_xlim`, `ax.set_ylim`, `ax.set_zlim`, `ax.set_box_aspect`

##### `CSFStacked.plot_weight`

**Source lines:** `358-388`

```python
def plot_weightself, z: float, poly_indices_to_plot=None, num_points: int=100, tol: float=1e-12, junction_side: str='left'
```

**Summary:** Plot the weight distributions for the segment selected by global ``z``.

**Docstring details**

```text
Dispatch policy
---------------
- The target segment is selected through ``field_at(...)`` using the same
  ``z`` and ``junction_side`` policy used by the other stacked wrappers.
- Once the correct segment is identified, a ``Visualizer`` is instantiated
  from that field and the plotting call is delegated to it.

Notes
-----
All plotting parameters are forwarded unchanged so that the stacked API
remains aligned with the single-field plotting API.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `poly_indices_to_plot` | `positional or keyword` | `not annotated` | `None` |
| `num_points` | `positional or keyword` | `int` | `100` |
| `tol` | `positional or keyword` | `float` | `1e-12` |
| `junction_side` | `positional or keyword` | `str` | `'left'` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`self.field_at`, `Visualizer`, `vis.plot_weight`, `float`

##### `CSFStacked.plot_properties`

**Source lines:** `391-640`

```python
def plot_propertiesself, keys_to_plot=None, alpha: float=1, title: str=None, num_points: int=100, show_junctions: bool=True
```

**Summary:** Plot selected section properties over the full CSFStacked domain.

**Docstring details**

```text
One continuous curve is evaluated inside each stacked segment. Internal
junctions are kept as segment boundaries, so discontinuities are not
hidden by interpolating across adjacent fields.

Parameters
----------
keys_to_plot : list[str] | None
    Property keys to plot, e.g. ["A", "Ix", "Iy", "Ip"].
    If None or empty, nothing is plotted.
alpha : float
    Kept for API alignment with Visualizer.plot_properties.
title : str | None
    Figure title. If None, a default stack-wide title is used.
num_points : int
    Number of sample points per stacked segment.
show_junctions : bool
    If True, draw vertical dotted lines at internal segment junctions.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `keys_to_plot` | `positional or keyword` | `not annotated` | `None` |
| `alpha` | `positional or keyword` | `float` | `1` |
| `title` | `positional or keyword` | `str` | `None` |
| `num_points` | `positional or keyword` | `int` | `100` |
| `show_junctions` | `positional or keyword` | `bool` | `True` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`np.concatenate`, `len`, `plt.subplots`, `fig.suptitle`, `plt.cm.viridis`, `enumerate`, `set_xlabel`, `plt.tight_layout`, `ValueError`, `list`, `np.linspace`, `z_by_segment.append`, `self.global_bounds`, `str`, `segment_slices.append`, `float`, `zip`, `np.asarray`, `np.isfinite`, `bool`, `int`, `ax.scatter`, `np.isclose`, `ax.set_ylim`, `ax.set_ylabel`, `ax.grid`, `ax.text`, `print`, `dict.fromkeys`, `abs`, `seg.field.section`, `section_full_analysis`, `slice`, `np.any`, `ax.plot`, `ax.twinx`, `ax_r.set_ylabel`, `ax_r.grid`, `np.argmin`, `np.argmax`, `ax.annotate`, `max`, `props.get`, `ax.axvline`, `ax_r.plot`, `lower`, `isinstance`, `append`, `_to_float_or_nan`

##### `CSFStacked.plot_section_2d`

**Source lines:** `642-683`

```python
def plot_section_2dself, z: float, junction_side: str='left', show_ids: bool=True, show_weights: bool=True, show_vertex_ids: bool=False, show_legenda: bool=False, title: Optional[str]=None, ax=None
```

**Summary:** Plot the 2D section at global coordinate ``z`` using stacked dispatch.

**Docstring details**

```text
Dispatch policy
---------------
- The target segment is selected through ``field_at(...)`` using the same
  ``z`` and ``junction_side`` policy already used by ``section()`` and
  ``section_full_analysis()``.
- Once the correct segment is identified, a Visualizer is instantiated
  from that field and the call is delegated to it.

Notes
-----
All plotting parameters are forwarded unchanged so that the stacked API
stays aligned with the single-field plotting API.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `junction_side` | `positional or keyword` | `str` | `'left'` |
| `show_ids` | `positional or keyword` | `bool` | `True` |
| `show_weights` | `positional or keyword` | `bool` | `True` |
| `show_vertex_ids` | `positional or keyword` | `bool` | `False` |
| `show_legenda` | `positional or keyword` | `bool` | `False` |
| `title` | `positional or keyword` | `Optional[str]` | `None` |
| `ax` | `positional or keyword` | `not annotated` | `None` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`self.field_at`, `Visualizer`, `vis.plot_section_2d`, `float`

##### `CSFStacked.plot_volume_3d`

**Source lines:** `686-727`

```python
def plot_volume_3dself, z: float, junction_side: str='left', show_end_sections: bool=True, line_percent: float=100.0, seed: int=0, title: str=None, ax=None, equalize_z: bool=False
```

**Summary:** Plot the 3D ruled volume of the stacked segment selected by global ``z``.

**Docstring details**

```text
Dispatch policy
---------------
- The target segment is selected through ``field_at(...)`` using the same
  ``z`` and ``junction_side`` policy already used by ``section()`` and
  ``plot_section_2d()``.
- Once the correct segment is identified, a ``Visualizer`` is instantiated
  from that field and the plotting call is delegated to it.

Notes
-----
All plotting parameters are forwarded unchanged so that the stacked API
remains aligned with the single-field plotting API.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `junction_side` | `positional or keyword` | `str` | `'left'` |
| `show_end_sections` | `positional or keyword` | `bool` | `True` |
| `line_percent` | `positional or keyword` | `float` | `100.0` |
| `seed` | `positional or keyword` | `int` | `0` |
| `title` | `positional or keyword` | `str` | `None` |
| `ax` | `positional or keyword` | `not annotated` | `None` |
| `equalize_z` | `positional or keyword` | `bool` | `False` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`self.field_at`, `Visualizer`, `vis.plot_volume_3d`, `float`

##### `CSFStacked.plot_volume_3d_global`

**Source lines:** `729-1047`

```python
def plot_volume_3d_globalself, title: str=None, line_percent: float=100.0, seed: int=1, margin_ratio: float=0.1, display_scale: tuple[float, float, float]=(1.0, 1.0, 1.0), box_aspect_scale: tuple[float, float, float]=(1.0, 1.0, 1.0), wire: bool=False, colors: bool=True, line_width: float=1.0
```

**Summary:** Render the full stacked volume in one global 3D plot.

**Docstring details**

```text
Supported combinations:
- wire=False, colors=True  : filled colored solids + edges
- wire=False, colors=False : filled grayscale solids + edges
- wire=True,  colors=True  : wireframe with per-polygon colors
- wire=True,  colors=False : wireframe in grayscale/black

Optimizations vs. original
--------------------------
- All filled faces (caps + side quads) are batched into one
  ``Poly3DCollection`` per color, replacing O(N) ``plot_surface``
  / ``plot_trisurf`` calls with a single ``add_collection3d``.
- All edge segments of the same (linewidth, color) style are
  concatenated with NaN separators and drawn with a single
  ``ax.plot`` call, replacing O(N*M) individual calls.
- Geometry data are accumulated as plain lists and converted to
  NumPy arrays only at render time (avoids repeated small allocs).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `title` | `positional or keyword` | `str` | `None` |
| `line_percent` | `positional or keyword` | `float` | `100.0` |
| `seed` | `positional or keyword` | `int` | `1` |
| `margin_ratio` | `positional or keyword` | `float` | `0.1` |
| `display_scale` | `positional or keyword` | `tuple[float, float, float]` | `(1.0, 1.0, 1.0)` |
| `box_aspect_scale` | `positional or keyword` | `tuple[float, float, float]` | `(1.0, 1.0, 1.0)` |
| `wire` | `positional or keyword` | `bool` | `False` |
| `colors` | `positional or keyword` | `bool` | `True` |
| `line_width` | `positional or keyword` | `float` | `1.0` |

**Returns:** `not annotated`

**Returned dictionary keys visible in the code**

`x`, `y`, `z`

**Raises visible in the code**

- `ValueError`
- `TypeError`

**Function/method calls visible in the code**

`random.Random`, `rng.shuffle`, `plt.figure`, `fig.add_subplot`, `ax.view_init`, `ax.set_proj_type`, `defaultdict`, `faces_by_color.items`, `edges_by_style.items`, `ax.set_xlabel`, `ax.set_ylabel`, `ax.set_zlabel`, `ax.set_title`, `ValueError`, `isinstance`, `TypeError`, `extend`, `len`, `range`, `seg.field.section`, `sorted`, `Poly3DCollection`, `ax.add_collection3d`, `ax.plot`, `max`, `ax.set_xlim`, `ax.set_ylim`, `ax.set_zlim`, `ax.set_box_aspect`, `_add_edge`, `append`, `_get_poly_color`, `np.array`, `np.full`, `list`, `min`, `set`, `zip`, `_add_polygon_edges`, `_add_cap_faces`, `x0.tolist`, `x1.tolist`, `y0.tolist`, `y1.tolist`, `abs`, `p0_map.keys`, `p1_map.keys`, `zz0.tolist`, `zz1.tolist`, `int`, `tolist`, `np.ceil`, `np.linspace`

##### `CSFStacked.global_bounds`

**Source lines:** `1049-1058`

```python
def global_boundsself
```

**Summary:** Return global z bounds of the stacked segments as (z_min, z_max).

**Docstring details**

```text
Raises if the stack is empty.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`min`, `max`, `ValueError`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
