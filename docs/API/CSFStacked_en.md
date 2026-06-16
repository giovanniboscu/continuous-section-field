# API Reference — `CSFStacked.py`

This document covers the dataclasses and APIs defined in `CSFStacked.py`.

## Module summary

- Top-level functions found: `0`.
- Classes found: `3`.
- Main runtime class: `CSFStacked`.
- Supporting dataclasses: `SegmentSpec`, `StackSegment`.

## Local dependencies used by the file

```python
from .entities import Pt, Polygon, Section
from .section_field import section_full_analysis
from .visualizer import Visualizer
from .continuous_section_field import ContinuousSectionField
```

---

# Dataclasses

## `SegmentSpec`

```python
@dataclass(frozen=True)
class SegmentSpec:
    tag: str
    z0: float
    z1: float
    polygons_s0: Tuple[Polygon, ...]
    polygons_s1: Tuple[Polygon, ...]
```

Generic input specification for one stacked segment.

| Field | Type | Description |
|---|---|---|
| `tag` | `str` | Segment identifier. |
| `z0` | `float` | Global start coordinate of the segment. |
| `z1` | `float` | Global end coordinate of the segment. |
| `polygons_s0` | `Tuple[Polygon, ...]` | Polygons at `z0`. |
| `polygons_s1` | `Tuple[Polygon, ...]` | Polygons at `z1`. |

**Notes from the code**

- Polygon names should be consistent between `z0` and `z1` for side-surface pairing.
- For each polygon name, vertex count must match between `z0` and `z1`.

---

## `StackSegment`

```python
@dataclass
class StackSegment:
    tag: str
    z_start: float
    z_end: float
    field: ContinuousSectionField
```

Runtime segment container storing the global interval and the associated `ContinuousSectionField`.

| Field | Type | Description |
|---|---|---|
| `tag` | `str` | Segment identifier. |
| `z_start` | `float` | Segment start coordinate. |
| `z_end` | `float` | Segment end coordinate. |
| `field` | `ContinuousSectionField` | Field associated with the segment. |

---

# Class `CSFStacked`

```python
class CSFStacked:
```

Stacked container for multiple `ContinuousSectionField` objects.

## Design goals documented in the code

- Multiple stacked `ContinuousSectionField` objects.
- Any number of polygons per section.
- Global `z` dispatch.
- Internal junction sections excluded by definition.
- Explicit validation and clear errors.

## Constructor

### `__init__`

```python
def __init__(self, eps_z: float = 1e-10)
```

Initializes an empty stack.

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `eps_z` | `float` | `1e-10` | Longitudinal tolerance used for contiguity and junction tests. |

## Initialized state

```python
self.eps_z = float(eps_z)
self.segments: List[StackSegment] = []
```

---

# Public API

## `append`

```python
def append(self, field: ContinuousSectionField) -> None
```

Appends one pre-built `ContinuousSectionField` to the stack.

| Parameter | Type | Description |
|---|---|---|
| `field` | `ContinuousSectionField` | Segment field to append. |

## Behavior visible in the code

- Reads bounds from `field.s0.z` and `field.s1.z`.
- Requires `z_end > z_start`.
- If the stack is not empty, the incoming field must start at the previous segment end within `self.eps_z`.
- Rejects overlaps, wrong order, and positive gaps larger than `self.eps_z`.
- Creates a `StackSegment` with tag `seg_<index>`.

## Raises

| Error | Condition |
|---|---|
| `RuntimeError` | Failure while reading `field.s0.z` or `field.s1.z`. |
| `ValueError` | Invalid field bounds. |
| `ValueError` | Overlap or wrong append order. |
| `ValueError` | Gap between consecutive segments. |

---

## `append2`

```python
def append2(self, field: ContinuousSectionField) -> None
```

Appends one pre-built `ContinuousSectionField` to the stack.

## Behavior visible in the code

`append2()` implements the same contiguity contract as `append()` but without the `try/except` wrapper around bound extraction.

## Contract documented in the code

- The new segment must have valid local bounds: `z_end > z_start`.
- If the stack is not empty, the new segment must start immediately after the previous segment within `self.eps_z`.
- Gaps and overlaps are rejected at append time.
- Segments are not sorted; user-provided order is the stack order.

---

## `field_at`

```python
def field_at(
    self,
    z: float,
    junction_side: str = "left",
) -> ContinuousSectionField
```

Returns the segment field mapped from global coordinate `z`.

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `z` | `float` | — | Global coordinate. |
| `junction_side` | `str` | `"left"` | Side used when `z` lies on an internal junction. Allowed values: `"left"`, `"right"`. |

**Returns**

| Type | Description |
|---|---|
| `ContinuousSectionField` | Field selected by `_find_segment(...)`. |

---

## `make_field_from_polygons`

```python
@staticmethod
def make_field_from_polygons(
    z0: float,
    z1: float,
    polygons_s0: Sequence[Polygon],
    polygons_s1: Sequence[Polygon],
) -> ContinuousSectionField
```

Creates one `ContinuousSectionField` from two polygon sets.

| Parameter | Type | Description |
|---|---|---|
| `z0` | `float` | Segment start coordinate. |
| `z1` | `float` | Segment end coordinate. |
| `polygons_s0` | `Sequence[Polygon]` | Start polygons. |
| `polygons_s1` | `Sequence[Polygon]` | End polygons. |

**Returns**

| Type | Description |
|---|---|
| `ContinuousSectionField` | Field created from `Section(polygons=tuple(...), z=...)`. |

**Raises**

| Error | Condition |
|---|---|
| `ValueError` | `z1 <= z0`. |
| `ValueError` | Either polygon sequence is empty. |

---

## `build_from_specs`

```python
def build_from_specs(
    self,
    specs: List[SegmentSpec],
    sort_by_z: bool = False,
) -> None
```

Builds the full stack from a list of `SegmentSpec` objects.

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `specs` | `List[SegmentSpec]` | — | Segment specifications to consume in order. |
| `sort_by_z` | `bool` | `False` | If `True`, the method raises an error. Automatic reordering is not supported. |

## Behavior visible in the code

- Rejects `sort_by_z=True`.
- Clears `self.segments`.
- Builds each field through `make_field_from_polygons(...)`.
- Appends each field through `append(...)`.

## Raises

| Error | Condition |
|---|---|
| `ValueError` | `sort_by_z=True`. |
| `ValueError` | Any error propagated from `make_field_from_polygons(...)` or `append(...)`. |

---

## `validate_contiguity`

```python
def validate_contiguity(
    self,
    require_contiguity: bool = True,
) -> None
```

Validates stack ordering, overlap, and optional strict contiguity.

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `require_contiguity` | `bool` | `True` | If true, gaps between segments are rejected. |

## Raises

| Error | Condition |
|---|---|
| `ValueError` | Stack is empty. |
| `ValueError` | Segment has `z_end <= z_start`. |
| `ValueError` | Overlap between consecutive segments. |
| `ValueError` | Gap between consecutive segments when `require_contiguity=True`. |

---

## `section`

```python
def section(
    self,
    z: float,
    junction_side: str = "left",
)
```

Returns the section at global coordinate `z`.

## Behavior visible in the code

Delegates to:

```python
self.field_at(z, junction_side=junction_side).section(float(z))
```

---

## `section_full_analysis`

```python
def section_full_analysis(
    self,
    z: float,
    junction_side: str = "left",
) -> float
```

Runs `section_full_analysis` on the section selected at global coordinate `z`.

## Behavior visible in the code

```python
sec = self.section(z, junction_side=junction_side)
out = section_full_analysis(sec)
return out
```

**Note**

The return annotation is `float`, but the imported `section_full_analysis(sec)` is returned directly. In the related source already processed, `section_full_analysis` returns a dictionary-like analysis result, not a scalar.

---

## `plot_weight`

```python
def plot_weight(
    self,
    z: float,
    poly_indices_to_plot=None,
    num_points: int = 100,
    tol: float = 1e-12,
    junction_side: str = "left",
)
```

Plots weight distributions for the segment selected by global `z`.

## Behavior visible in the code

- Selects the segment field through `field_at(...)`.
- Creates `Visualizer(field)`.
- Delegates to `Visualizer.plot_weight(...)`.

---

## `plot_properties`

```python
def plot_properties(
    self,
    keys_to_plot=None,
    alpha: float = 1,
    title: str = None,
    num_points: int = 100,
    show_junctions: bool = True,
)
```

Plots selected section properties over the full stacked domain.

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `keys_to_plot` | not annotated | `None` | Property keys to plot. `"geometry"` is filtered out. |
| `alpha` | `float` | `1` | Kept for API alignment. It is not passed to `section_full_analysis` in the current body. |
| `title` | `str` | `None` | Figure title. If `None`, a stack-wide default is generated. |
| `num_points` | `int` | `100` | Number of sample points per segment. |
| `show_junctions` | `bool` | `True` | If true, draws vertical dotted lines at internal segment junctions. |

## Behavior visible in the code

- Raises if the stack is empty.
- Raises if `num_points < 2`.
- Samples each segment independently with `np.linspace(seg.z_start, seg.z_end, num_points)`.
- Calls `section_full_analysis(current_section, compute_vroark=need_vroark)`.
- Sets `need_vroark=True` when `J_s_vroark` or `J_s_vroark_fidelity` is requested.
- Does not interpolate across adjacent fields when plotting; segment curves are drawn separately.
- Supports scalar values and 2-item sequence values.
- Adds min/max markers and text on left-axis data.
- Uses right-axis plotting when a property returns a pair.
- Returns the Matplotlib axes list.

---

## `plot_section_2d`

```python
def plot_section_2d(
    self,
    z: float,
    junction_side: str = "left",
    show_ids: bool = True,
    show_weights: bool = True,
    show_vertex_ids: bool = False,
    show_legenda: bool = False,
    title: Optional[str] = None,
    ax=None,
)
```

Plots the 2D section at global coordinate `z` using stacked dispatch.

## Behavior visible in the code

- Selects the target field through `field_at(z, junction_side=...)`.
- Creates `Visualizer(field)`.
- Builds a title including the selected segment range.
- Delegates to `Visualizer.plot_section_2d(...)`.
- Returns the result of `Visualizer.plot_section_2d(...)`.

---

## `plot_volume_3d`

```python
def plot_volume_3d(
    self,
    z: float,
    junction_side: str = "left",
    show_end_sections: bool = True,
    line_percent: float = 100.0,
    seed: int = 0,
    title: str = None,
    ax=None,
    equalize_z: bool = False,
)
```

Plots the 3D ruled volume of the stacked segment selected by global `z`.

## Behavior visible in the code

- Selects the target field through `field_at(z, junction_side=...)`.
- Creates `Visualizer(field)`.
- If `title is None`, creates a title from the selected field range.
- Delegates to `Visualizer.plot_volume_3d(...)`.
- Returns the result of `Visualizer.plot_volume_3d(...)`.

---

## `plot_volume_3d_global`

```python
def plot_volume_3d_global(
    self,
    title: str = None,
    line_percent: float = 100.0,
    seed: int = 1,
    margin_ratio: float = 0.10,
    display_scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
    box_aspect_scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
    wire: bool = False,
    colors: bool = True,
    line_width: float = 1.0,
)
```

Renders the full stacked volume in one global 3D plot.

## Supported combinations documented in the code

| `wire` | `colors` | Result |
|---:|---:|---|
| `False` | `True` | filled colored solids + edges |
| `False` | `False` | filled grayscale solids + edges |
| `True` | `True` | wireframe with per-polygon colors |
| `True` | `False` | wireframe in grayscale/black |

## Behavior visible in the code

- Validates `line_percent`, `margin_ratio`, `display_scale`, `box_aspect_scale`, `wire`, `colors`, and `line_width`.
- Creates a 3D Matplotlib figure.
- Iterates through all stack segments.
- Evaluates each segment at `seg.z_start` and `seg.z_end`.
- Matches polygons between endpoint sections by polygon name.
- Raises if matching polygons have different vertex counts.
- Applies optional display scaling to `X`, `Y`, and `Z`.
- Batches filled faces through `Poly3DCollection`.
- Batches edge segments by style and draws each style in one `ax.plot(...)` call.
- Computes global limits from all accumulated vertices.
- Applies `box_aspect_scale`.
- Returns the Matplotlib 3D axes object.

## Raises

| Error | Condition |
|---|---|
| `ValueError` | `line_percent` outside `[0, 100]`. |
| `ValueError` | `margin_ratio < 0`. |
| `ValueError` | Any `display_scale` value `<= 0`. |
| `ValueError` | Any `box_aspect_scale` value `<= 0`. |
| `TypeError` | `wire` is not `bool`. |
| `TypeError` | `colors` is not `bool`. |
| `ValueError` | `line_width <= 0`. |
| `ValueError` | Matched polygons have different vertex counts. |

---

## `global_bounds`

```python
def global_bounds(self)
```

Returns global `z` bounds of the stacked segments.

## Returns

```python
(z_min, z_max)
```

## Raises

| Error | Condition |
|---|---|
| `ValueError` | Stack is empty. |

---

# Internal methods

## `_find_segment`

```python
def _find_segment(
    self,
    z: float,
    junction_side: str = "left",
) -> StackSegment
```

Returns the `StackSegment` mapped from global `z`.

## Junction policy documented in the code

- External boundaries are unambiguous and always map to the outer segments.
- Internal junctions are handled explicitly through `junction_side`:
  - `"left"` maps to the segment on the left of the junction.
  - `"right"` maps to the segment on the right of the junction.

## Raises

| Error | Condition |
|---|---|
| `ValueError` | Stack is empty. |
| `ValueError` | `junction_side` is not `"left"` or `"right"`. |
| `ValueError` | `z` outside the global stack domain. |
| `ValueError` | `z` cannot be mapped to any segment. |

---

## `_compute_axis_bounds_with_margin`

```python
def _compute_axis_bounds_with_margin(
    self,
    xs: Sequence[float],
    ys: Sequence[float],
    zs: Sequence[float],
    margin_ratio: float = 0.10,
)
```

Computes axis-aligned limits with independent margins per axis.

## Returns

```python
((xmin, xmax), (ymin, ymax), (zmin, zmax), (dx, dy, dz))
```

## Raises

| Error | Condition |
|---|---|
| `ValueError` | Empty coordinate lists. |
| `ValueError` | `margin_ratio < 0`. |

---

## `_apply_box_limits`

```python
@staticmethod
def _apply_box_limits(ax, bounds) -> None
```

Applies precomputed limits and sets data-proportional box aspect.
