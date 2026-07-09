# API Reference - `sp_csf.py`

This document covers the top-level classes and functions defined in `src/csf/utils/sp_csf.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/utils/sp_csf.py`
- Output file: `doc/API/utils_sp_csf_api_en.md`
- Top-level function definitions found: `51`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Module docstring

```text
Bridge between CSF and sectionproperties.

This tool uses sectionproperties as the finite-element-based section analysis
backend where applicable.

sectionproperties:
https://github.com/robbievanleeuwen/section-properties
License: MIT

sp_to_csf.py
============

Convert one or two sectionproperties sections to a CSF YAML file.

Supports:
- Prismatic sections (S0 = S1, same section type and dimensions)
- Tapered sections  (S0 != S1, same section type, different dimensions)
- Morphing          (S0 and S1 of different section types)
- Offset            (independent dx/dy translation of S0 and S1)
- Twist             (rotation of S0 and S1 around their centroid)
- Generic section pre-processing via sectionproperties' alignment/shift/rotate tools

Centroid alignment
------------------
When --morph is used (or S0 and S1 are of different types/sizes), the two
sections will in general have different centroid positions in the SP coordinate
system. By default (auto-align mode), sp_to_csf computes the centroid of each
section and applies the offset needed to align them in the CSF coordinate
system. The reference point is the centroid of S0.

Auto-alignment can be disabled with --no-align. In that case the raw SP
coordinates are used, and you can supply explicit offsets with --dx0/dy0/dx1/dy1.

If explicit --dx1/dy1 are provided, auto-alignment is skipped for S1.
Same for --dx0/dy0 and S0.

Usage (CLI)
-----------
  # Prismatic RHS
  python sp_to_csf.py rectangular_hollow_section \
    --s0 d=200,b=150,t=10,r_out=15,n_r=8,z=0 \
    --s1 d=200,b=150,t=10,r_out=15,n_r=8,z=10

  # Tapered RHS
  python sp_to_csf.py rectangular_hollow_section \
    --s0 d=300,b=200,t=12,r_out=20,n_r=8,z=0 \
    --s1 d=200,b=150,t=8,r_out=15,n_r=8,z=10

  # Morph RHS -> CHS (centroids auto-aligned)
  python sp_to_csf.py rectangular_hollow_section \
    --morph circular_hollow_section \
    --s0 d=4000,b=4000,t=30,r_out=300,n_r=16,z=0 \
    --s1 d=2500,t=18,n=48,z=70000 \
    --n=96 --name=tower --out=wind_tower.yaml

  # Morph with twist
  python sp_to_csf.py rectangular_hollow_section \
    --morph circular_hollow_section \
    --s0 d=200,b=150,t=10,r_out=15,n_r=8,z=0 \
    --s1 d=180,t=8,n=32,z=10 \
    --twist1=45

  # Disable auto-align, supply manual offsets
  python sp_to_csf.py rectangular_hollow_section \
    --morph circular_hollow_section \
    --s0 d=200,b=200,t=10,r_out=20,n_r=8,z=0 \
    --s1 d=150,t=8,n=32,z=10 \
    --no-align --dx1=25 --dy1=25

Usage (library)
---------------
  from sp_to_csf import sp_to_csf_yaml, sp_sections_to_csf_yaml
  from sectionproperties.pre.library import rectangular_hollow_section, circular_hollow_section

  sp_to_csf_yaml(
      rectangular_hollow_section(d=4000, b=4000, t=30, r_out=300, n_r=16),
      circular_hollow_section(d=2500, t=18, n=48),
      z0=0.0, z1=70000.0,
      n=96, name="tower",
      output_path="wind_tower.yaml",
  )

  sp_sections_to_csf_yaml(
      "rectangular_section",
      {"d": 200, "b": 150, "z": 0.0, "align_center": True},
      "rectangular_section",
      {"d": 200, "b": 150, "z": 10.0, "x_offset": 25.0, "angle": 15.0},
      output_path="rectangles.yaml",
      auto_align=False,
  )
```

## Public API index

- `def _signed_areapts: Sequence[Point]` - line 106
- `def _fmt_floatvalue: float, precision: int=6` - line 121
- `def _poly_blockname: str, weight: float, vertices: Sequence[Point], indent: int=8, precision: int=6` - line 129
- `def _translate_pointspts: Sequence[Point], dx: float=0.0, dy: float=0.0, precision: int=6` - line 159
- `def _rotate_pointspts: Sequence[Point], angle_deg: float, cx: float=0.0, cy: float=0.0, precision: int=6` - line 176
- `def _same_pointp0: Point, p1: Point, tol: float=1e-12` - line 209
- `def _find_axis_start_on_edgepts: Sequence[Point], cx: float, cy: float, tol: float=1e-12` - line 213
- `def _rotate_contour_to_axis_startpts: Sequence[Point], cx: float, cy: float, tol: float=1e-12` - line 260
- `def _resample_contourpts: Sequence[Point], n: int` - line 303
- `def _morph_ring_to_verticescoords: Any, n: int, cx: float, cy: float, precision: int=6` - line 336
- `def _native_ring_to_verticescoords: Any, cx: float, cy: float, precision: int=6` - line 361
- `def _cell_vertices_from_outer_innerouter: Sequence[Point], inner: Sequence[Point]` - line 385
- `def _draw_radius_pointspt: Point, r: float, theta: float, n: int, ccw: bool=True, phi: float=1.5707963267948966` - line 415
- `def _polyline_lengthpts: Sequence[Point]` - line 438
- `def _resample_open_polylinepts: Sequence[Point], n: int` - line 446
- `def _allocate_feature_countsfeatures: Sequence[Tuple[str, Sequence[Point], Sequence[Point]]], n: int` - line 476
- `def _polygon_centroidpts: Sequence[Point]` - line 509
- `def _require_section_paramparams: dict, key: str, section_name: str` - line 529
- `def _scaled_reference_yparams: dict, reference_params: Optional[dict]` - line 536
- `def _i_like_feature_blocksparams: dict, section_name: str` - line 550
- `def _channel_like_feature_blocksparams: dict, section_name: str` - line 616
- `def _angle_like_feature_blocksparams: dict, section_name: str` - line 665
- `def _tee_like_feature_blocksparams: dict, section_name: str` - line 719
- `def _rectangle_feature_blocksparams: dict, reference_params: Optional[dict]` - line 775
- `def _section_feature_blockssection_name: str, params: dict, reference_params: Optional[dict]=None` - line 805
- `def _i_section_to_tee_feature_verticesparams_s0: dict, params_s1: dict, n: int, precision: int` - line 828
- `def _features_to_verticesfeatures: Sequence[Tuple[str, Sequence[Point], Sequence[Point]]], n: int, precision: int` - line 928
- `def _feature_vertices_for_pairsection_s0: str, section_s1: str, params_s0: dict, params_s1: dict, n: int, precision: int` - line 960
- `def _write_feature_morph_yamlsection_s0: str, section_s1: str, params_s0: dict, params_s1: dict, z0: float, z1: float, output_path: 'str | Path', n: int, name: str, comment: Optional[str], solid_weight: float, indent: int, precision: int, dx0: Optional[float], dy0: Optional[float], dx1: Optional[float], dy1: Optional[float], twist0_deg: float, twist1_deg: float, auto_align: bool` - line 996
- `def _import_sp_geometry_types` - line 1100
- `def _flatten_geometry_to_polygonsgeometry: Any` - line 1115
- `def geometry_centroidgeometry: Any` - line 1141
- `def _geometry_centroidgeometry: Any` - line 1146
- `def _pair_to_blockspoly_s0: Any, poly_s1: Any, base_name: str, n: Optional[int], solid_weight: float, void_weight: float, indent: int, precision: int, dx0: float, dy0: float, dx1: float, dy1: float, twist0_deg: float, twist1_deg: float, morph_mode: str='perimeter', cell: bool=False` - line 1162
- `def sp_to_csf_yamlgeometry_s0: Any, geometry_s1: Any, z0: float, z1: float, output_path: 'str | Path', n: Optional[int]=None, name: Optional[str]=None, comment: Optional[str]=None, solid_weight: float=1.0, void_weight: float=0.0, indent: int=8, precision: int=6, dx0: Optional[float]=None, dy0: Optional[float]=None, dx1: Optional[float]=None, dy1: Optional[float]=None, twist0_deg: float=0.0, twist1_deg: float=0.0, auto_align: bool=True, morph_mode: str='perimeter', cell: bool=False` - line 1264
- `def _coercevalue: str` - line 1447
- `def _parse_section_paramsraw: str` - line 1465
- `def _extract_required_zparams: dict, section_label: str` - line 1478
- `def _parse_bool_paramvalue: Any, key: str, section_name: str` - line 1488
- `def _parse_float_paramvalue: Any, key: str, section_name: str` - line 1498
- `def _split_section_paramssection_name: str, params: dict` - line 1508
- `def _transform_has_translationtransform: dict, tol: float=1e-12` - line 1555
- `def _transform_is_activetransform: dict, tol: float=1e-12` - line 1566
- `def _validate_transform_pairsection_s0: str, section_s1: str, transform_s0: dict, transform_s1: dict, auto_align: bool` - line 1572
- `def _apply_standalone_section_transformgeometry: Any, transform: dict` - line 1609
- `def _apply_dependent_section_transformgeometry: Any, reference_geometry: Any, transform: dict` - line 1625
- `def _build_geometrysection_name: str, params: dict` - line 1646
- `def _build_transformed_section_pairsection_s0: str, section_s1: str, params_s0: dict, params_s1: dict, auto_align: bool, morph_mode: str` - line 1668
- `def sp_sections_to_csf_yamlsection_s0: str, params_s0: dict, section_s1: Optional[str], params_s1: dict, output_path: 'str | Path', n: Optional[int]=None, name: Optional[str]=None, comment: Optional[str]=None, solid_weight: float=1.0, void_weight: float=0.0, indent: int=8, precision: int=6, dx0: Optional[float]=None, dy0: Optional[float]=None, dx1: Optional[float]=None, dy1: Optional[float]=None, twist0_deg: float=0.0, twist1_deg: float=0.0, auto_align: bool=True, morph_mode: str='perimeter', cell: bool=False` - line 1721
- `def _generate_actions_yamloutput_path: Path, z0: float, z1: float, title: str='CSF Tower', precision: int=6` - line 1840
- `def main` - line 1901

## API details

## Functions

## Basic polygon helpers

### `_signed_area`

**Source lines:** `106-114`

```python
def _signed_areapts: Sequence[Point]
```

**Summary:** Signed area of a closed polygon. Positive = CCW, Negative = CW.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `pts` | `positional or keyword` | `Sequence[Point]` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`len`, `range`

## YAML formatting helpers

### `_fmt_float`

**Source lines:** `121-126`

```python
def _fmt_floatvalue: float, precision: int=6
```

**Summary:** Format a float compactly for YAML output.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `float` | `-` |
| `precision` | `positional or keyword` | `int` | `6` |

**Returns:** `str`

**Function/method calls visible in the code**

`rstrip`, `float`

### `_poly_block`

**Source lines:** `129-156`

```python
def _poly_blockname: str, weight: float, vertices: Sequence[Point], indent: int=8, precision: int=6
```

**Summary:** Return one CSF polygon block in YAML format.

**Docstring details**

```text
CSF requires the polygon name as a mapping key:
    tower:
      weight: 1.0
      vertices:
        - [x, y]
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `name` | `positional or keyword` | `str` | `-` |
| `weight` | `positional or keyword` | `float` | `-` |
| `vertices` | `positional or keyword` | `Sequence[Point]` | `-` |
| `indent` | `positional or keyword` | `int` | `8` |
| `precision` | `positional or keyword` | `int` | `6` |

**Returns:** `str`

**Function/method calls visible in the code**

`join`, `lines.append`, `_fmt_float`

### `_translate_points`

**Source lines:** `159-169`

```python
def _translate_pointspts: Sequence[Point], dx: float=0.0, dy: float=0.0, precision: int=6
```

**Summary:** Translate a point list by (dx, dy).

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `pts` | `positional or keyword` | `Sequence[Point]` | `-` |
| `dx` | `positional or keyword` | `float` | `0.0` |
| `dy` | `positional or keyword` | `float` | `0.0` |
| `precision` | `positional or keyword` | `int` | `6` |

**Returns:** `List[Point]`

**Function/method calls visible in the code**

`round`

## Rotation helper

### `_rotate_points`

**Source lines:** `176-202`

```python
def _rotate_pointspts: Sequence[Point], angle_deg: float, cx: float=0.0, cy: float=0.0, precision: int=6
```

**Summary:** Rotate a point list by angle_deg degrees (CCW) around (cx, cy).

**Docstring details**

```text
Applied after resampling and translation so it does not affect
vertex-to-vertex correspondence.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `pts` | `positional or keyword` | `Sequence[Point]` | `-` |
| `angle_deg` | `positional or keyword` | `float` | `-` |
| `cx` | `positional or keyword` | `float` | `0.0` |
| `cy` | `positional or keyword` | `float` | `0.0` |
| `precision` | `positional or keyword` | `int` | `6` |

**Returns:** `List[Point]`

**Function/method calls visible in the code**

`math.radians`, `math.cos`, `math.sin`, `abs`, `list`, `result.append`, `round`

## Morphing helpers

### `_same_point`

**Source lines:** `209-210`

```python
def _same_pointp0: Point, p1: Point, tol: float=1e-12
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `p0` | `positional or keyword` | `Point` | `-` |
| `p1` | `positional or keyword` | `Point` | `-` |
| `tol` | `positional or keyword` | `float` | `1e-12` |

**Returns:** `bool`

**Function/method calls visible in the code**

`abs`

### `_find_axis_start_on_edge`

**Source lines:** `213-257`

```python
def _find_axis_start_on_edgepts: Sequence[Point], cx: float, cy: float, tol: float=1e-12
```

**Summary:** Find the exact start position on the positive local x semi-axis.

**Docstring details**

```text
Translates the contour to centroid, then finds the first intersection
of the contour with the ray y=0, x>=0. Returns (edge_index, edge_t).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `pts` | `positional or keyword` | `Sequence[Point]` | `-` |
| `cx` | `positional or keyword` | `float` | `-` |
| `cy` | `positional or keyword` | `float` | `-` |
| `tol` | `positional or keyword` | `float` | `1e-12` |

**Returns:** `Tuple[int, float]`

**Function/method calls visible in the code**

`len`, `range`, `max`, `min`, `abs`, `candidates.append`

## Fallback: rightmost vertex

### `_rotate_contour_to_axis_start`

**Source lines:** `260-300`

```python
def _rotate_contour_to_axis_startpts: Sequence[Point], cx: float, cy: float, tol: float=1e-12
```

**Summary:** Rotate a ring so the first point is on the positive x semi-axis.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `pts` | `positional or keyword` | `Sequence[Point]` | `-` |
| `cx` | `positional or keyword` | `float` | `-` |
| `cy` | `positional or keyword` | `float` | `-` |
| `tol` | `positional or keyword` | `float` | `1e-12` |

**Returns:** `List[Point]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`len`, `_find_axis_start_on_edge`, `ValueError`, `_same_point`, `rotated.append`, `cleaned.append`

## Top-level functions

### `_resample_contour`

**Source lines:** `303-333`

```python
def _resample_contourpts: Sequence[Point], n: int
```

**Summary:** Resample a closed polygon to exactly n equidistant points.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `pts` | `positional or keyword` | `Sequence[Point]` | `-` |
| `n` | `positional or keyword` | `int` | `-` |

**Returns:** `List[Point]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`len`, `range`, `ValueError`, `arc.append`, `result.append`

### `_morph_ring_to_vertices`

**Source lines:** `336-358`

```python
def _morph_ring_to_verticescoords: Any, n: int, cx: float, cy: float, precision: int=6
```

**Summary:** Convert a Shapely ring to n equidistant CCW vertices aligned to

**Docstring details**

```text
the positive x semi-axis of the local (centroid-centered) frame.

Used for morph mode (different section types) where resampling is needed
to match vertex count between S0 and S1.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `coords` | `positional or keyword` | `Any` | `-` |
| `n` | `positional or keyword` | `int` | `-` |
| `cx` | `positional or keyword` | `float` | `-` |
| `cy` | `positional or keyword` | `float` | `-` |
| `precision` | `positional or keyword` | `int` | `6` |

**Returns:** `List[Point]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`_rotate_contour_to_axis_start`, `_resample_contour`, `len`, `ValueError`, `_signed_area`, `list`, `float`, `reversed`, `round`

### `_native_ring_to_vertices`

**Source lines:** `361-382`

```python
def _native_ring_to_verticescoords: Any, cx: float, cy: float, precision: int=6
```

**Summary:** Convert a Shapely ring to CCW vertices using the native SP order.

**Docstring details**

```text
Native mode is meant for prismatic/tapered sections generated by the same
sectionproperties constructor. In that case sectionproperties already emits
corresponding vertices in a consistent parametric order. Therefore this
function must not insert points and must not cyclically shift the ring: both
operations can break the native correspondence for tapered sections.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `coords` | `positional or keyword` | `Any` | `-` |
| `cx` | `positional or keyword` | `float` | `-` |
| `cy` | `positional or keyword` | `float` | `-` |
| `precision` | `positional or keyword` | `int` | `6` |

**Returns:** `List[Point]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`len`, `ValueError`, `_signed_area`, `list`, `float`, `reversed`, `round`

### `_cell_vertices_from_outer_inner`

**Source lines:** `385-410`

```python
def _cell_vertices_from_outer_innerouter: Sequence[Point], inner: Sequence[Point]
```

**Summary:** Return the CSF @cell vertex sequence from one exterior and one hole.

**Docstring details**

```text
The exterior ring is written first with CCW orientation. The inner ring is
written after it with CW orientation. Both rings are explicitly closed.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `outer` | `positional or keyword` | `Sequence[Point]` | `-` |
| `inner` | `positional or keyword` | `Sequence[Point]` | `-` |

**Returns:** `List[Point]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`list`, `ValueError`, `_signed_area`, `outer_pts.append`, `inner_pts.append`, `len`, `reversed`

### `_allocate_feature_counts`

**Source lines:** `476-506`

```python
def _allocate_feature_countsfeatures: Sequence[Tuple[str, Sequence[Point], Sequence[Point]]], n: int
```

**Summary:** Allocate the total vertex count over independent geometric features.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `features` | `positional or keyword` | `Sequence[Tuple[str, Sequence[Point], Sequence[Point]]]` | `-` |
| `n` | `positional or keyword` | `int` | `-` |

**Returns:** `List[int]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`sum`, `len`, `ValueError`, `max`, `_polyline_length`, `int`, `range`

### `_polygon_centroid`

**Source lines:** `509-526`

```python
def _polygon_centroidpts: Sequence[Point]
```

**Summary:** Return the centroid of a non-self-intersecting polygon ring.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `pts` | `positional or keyword` | `Sequence[Point]` | `-` |

**Returns:** `Point`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`len`, `range`, `abs`, `ValueError`

### `_require_section_param`

**Source lines:** `529-533`

```python
def _require_section_paramparams: dict, key: str, section_name: str
```

**Summary:** Read a required section parameter with a clear error message.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `params` | `positional or keyword` | `dict` | `-` |
| `key` | `positional or keyword` | `str` | `-` |
| `section_name` | `positional or keyword` | `str` | `-` |

**Returns:** `Any`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`

### `_scaled_reference_y`

**Source lines:** `536-547`

```python
def _scaled_reference_yparams: dict, reference_params: Optional[dict]
```

**Summary:** Return a stable lower split height for rectangle-compatible features.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `params` | `positional or keyword` | `dict` | `-` |
| `reference_params` | `positional or keyword` | `Optional[dict]` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`float`, `max`, `_require_section_param`, `min`

### `_i_like_feature_blocks`

**Source lines:** `550-613`

```python
def _i_like_feature_blocksparams: dict, section_name: str
```

**Summary:** Return a fixed feature sequence for an I-like section outline.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `params` | `positional or keyword` | `dict` | `-` |
| `section_name` | `positional or keyword` | `str` | `-` |

**Returns:** `List[Tuple[str, List[Point]]]`

**Function/method calls visible in the code**

`float`, `int`, `_draw_radius_points`, `_require_section_param`

### `_channel_like_feature_blocks`

**Source lines:** `616-662`

```python
def _channel_like_feature_blocksparams: dict, section_name: str
```

**Summary:** Return an I-compatible feature sequence for a channel outline.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `params` | `positional or keyword` | `dict` | `-` |
| `section_name` | `positional or keyword` | `str` | `-` |

**Returns:** `List[Tuple[str, List[Point]]]`

**Function/method calls visible in the code**

`float`, `int`, `_draw_radius_points`, `_require_section_param`

### `_angle_like_feature_blocks`

**Source lines:** `665-716`

```python
def _angle_like_feature_blocksparams: dict, section_name: str
```

**Summary:** Return a fixed feature sequence for an L-section outline.

**Docstring details**

```text
The sequence is anchored on the geometric features that must remain matched
during morphing: the two outer toe regions, the inner root radius, and the
three straight branches linking them.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `params` | `positional or keyword` | `dict` | `-` |
| `section_name` | `positional or keyword` | `str` | `-` |

**Returns:** `List[Tuple[str, List[Point]]]`

**Function/method calls visible in the code**

`float`, `int`, `_draw_radius_points`, `_require_section_param`

### `_tee_like_feature_blocks`

**Source lines:** `719-772`

```python
def _tee_like_feature_blocksparams: dict, section_name: str
```

**Summary:** Return an I-compatible feature sequence for a tee outline.

**Docstring details**

```text
Missing lower-flange features are collapsed to zero-length polylines so the
generic feature matcher can reuse the same label sequence.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `params` | `positional or keyword` | `dict` | `-` |
| `section_name` | `positional or keyword` | `str` | `-` |

**Returns:** `List[Tuple[str, List[Point]]]`

**Function/method calls visible in the code**

`float`, `int`, `_draw_radius_points`, `_require_section_param`

### `_rectangle_feature_blocks`

**Source lines:** `775-802`

```python
def _rectangle_feature_blocksparams: dict, reference_params: Optional[dict]
```

**Summary:** Return an I-compatible feature sequence collapsed onto a rectangle.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `params` | `positional or keyword` | `dict` | `-` |
| `reference_params` | `positional or keyword` | `Optional[dict]` | `-` |

**Returns:** `List[Tuple[str, List[Point]]]`

**Function/method calls visible in the code**

`float`, `_scaled_reference_y`, `_require_section_param`

### `_section_feature_blocks`

**Source lines:** `805-825`

```python
def _section_feature_blockssection_name: str, params: dict, reference_params: Optional[dict]=None
```

**Summary:** Return a fixed feature sequence for supported feature morph families.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_name` | `positional or keyword` | `str` | `-` |
| `params` | `positional or keyword` | `dict` | `-` |
| `reference_params` | `positional or keyword` | `Optional[dict]` | `None` |

**Returns:** `List[Tuple[str, List[Point]]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`, `_i_like_feature_blocks`, `_channel_like_feature_blocks`, `_rectangle_feature_blocks`, `_angle_like_feature_blocks`, `_tee_like_feature_blocks`

### `_i_section_to_tee_feature_vertices`

**Source lines:** `828-925`

```python
def _i_section_to_tee_feature_verticesparams_s0: dict, params_s1: dict, n: int, precision: int
```

**Summary:** Build matched I-section and tee-section rings feature by feature.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `params_s0` | `positional or keyword` | `dict` | `-` |
| `params_s1` | `positional or keyword` | `dict` | `-` |
| `n` | `positional or keyword` | `int` | `-` |
| `precision` | `positional or keyword` | `int` | `-` |

**Returns:** `Tuple[List[Point], List[Point]]`

**Function/method calls visible in the code**

`float`, `int`, `_draw_radius_points`, `_features_to_vertices`, `_require_section_param`

### `_features_to_vertices`

**Source lines:** `928-957`

```python
def _features_to_verticesfeatures: Sequence[Tuple[str, Sequence[Point], Sequence[Point]]], n: int, precision: int
```

**Summary:** Convert paired feature polylines into matched closed-ring vertices.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `features` | `positional or keyword` | `Sequence[Tuple[str, Sequence[Point], Sequence[Point]]]` | `-` |
| `n` | `positional or keyword` | `int` | `-` |
| `precision` | `positional or keyword` | `int` | `-` |

**Returns:** `Tuple[List[Point], List[Point]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`_allocate_feature_counts`, `zip`, `vertices_s0.extend`, `vertices_s1.extend`, `ValueError`, `_signed_area`, `list`, `_resample_open_polyline`, `len`, `reversed`, `round`

### `_feature_vertices_for_pair`

**Source lines:** `960-993`

```python
def _feature_vertices_for_pairsection_s0: str, section_s1: str, params_s0: dict, params_s1: dict, n: int, precision: int
```

**Summary:** Return matched vertices for supported feature morph pairs.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_s0` | `positional or keyword` | `str` | `-` |
| `section_s1` | `positional or keyword` | `str` | `-` |
| `params_s0` | `positional or keyword` | `dict` | `-` |
| `params_s1` | `positional or keyword` | `dict` | `-` |
| `n` | `positional or keyword` | `int` | `-` |
| `precision` | `positional or keyword` | `int` | `-` |

**Returns:** `Tuple[List[Point], List[Point]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`_section_feature_blocks`, `_features_to_vertices`, `_i_section_to_tee_feature_vertices`, `ValueError`, `zip`

### `_write_feature_morph_yaml`

**Source lines:** `996-1094`

```python
def _write_feature_morph_yamlsection_s0: str, section_s1: str, params_s0: dict, params_s1: dict, z0: float, z1: float, output_path: 'str | Path', n: int, name: str, comment: Optional[str], solid_weight: float, indent: int, precision: int, dx0: Optional[float], dy0: Optional[float], dx1: Optional[float], dy1: Optional[float], twist0_deg: float, twist1_deg: float, auto_align: bool
```

**Summary:** Write a CSF YAML file using a feature-aware morph map.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_s0` | `positional or keyword` | `str` | `-` |
| `section_s1` | `positional or keyword` | `str` | `-` |
| `params_s0` | `positional or keyword` | `dict` | `-` |
| `params_s1` | `positional or keyword` | `dict` | `-` |
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `output_path` | `positional or keyword` | `'str | Path'` | `-` |
| `n` | `positional or keyword` | `int` | `-` |
| `name` | `positional or keyword` | `str` | `-` |
| `comment` | `positional or keyword` | `Optional[str]` | `-` |
| `solid_weight` | `positional or keyword` | `float` | `-` |
| `indent` | `positional or keyword` | `int` | `-` |
| `precision` | `positional or keyword` | `int` | `-` |
| `dx0` | `positional or keyword` | `Optional[float]` | `-` |
| `dy0` | `positional or keyword` | `Optional[float]` | `-` |
| `dx1` | `positional or keyword` | `Optional[float]` | `-` |
| `dy1` | `positional or keyword` | `Optional[float]` | `-` |
| `twist0_deg` | `positional or keyword` | `float` | `-` |
| `twist1_deg` | `positional or keyword` | `float` | `-` |
| `auto_align` | `positional or keyword` | `bool` | `-` |

**Returns:** `Tuple[Path, Point, Point]`

**Function/method calls visible in the code**

`Path`, `_feature_vertices_for_pair`, `_polygon_centroid`, `_translate_points`, `_rotate_points`, `join`, `output_path.write_text`, `header_lines.append`, `_fmt_float`, `_poly_block`

### `_geometry_centroid`

**Source lines:** `1146-1155`

```python
def _geometry_centroidgeometry: Any
```

**Summary:** Return the centroid (cx, cy) of the union of all polygons in a

**Docstring details**

```text
sectionproperties geometry object.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geometry` | `positional or keyword` | `Any` | `-` |

**Returns:** `Tuple[float, float]`

**Raises visible in the code**

- `ImportError`

**Function/method calls visible in the code**

`_flatten_geometry_to_polygons`, `unary_union`, `ImportError`

### `_parse_bool_param`

**Source lines:** `1488-1494`

```python
def _parse_bool_paramvalue: Any, key: str, section_name: str
```

**Summary:** Validate a boolean section-level transform parameter.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `Any` | `-` |
| `key` | `positional or keyword` | `str` | `-` |
| `section_name` | `positional or keyword` | `str` | `-` |

**Returns:** `bool`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`isinstance`, `ValueError`

### `_parse_float_param`

**Source lines:** `1498-1504`

```python
def _parse_float_paramvalue: Any, key: str, section_name: str
```

**Summary:** Validate a numeric section-level transform parameter.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `Any` | `-` |
| `key` | `positional or keyword` | `str` | `-` |
| `section_name` | `positional or keyword` | `str` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `isinstance`, `ValueError`

### `_split_section_params`

**Source lines:** `1508-1551`

```python
def _split_section_paramssection_name: str, params: dict
```

**Summary:** Split raw section parameters into SP constructor args and transform args.

**Docstring details**

```text
The split is explicit on purpose. If a parameter belongs to the transform
layer, it must not silently flow into the sectionproperties constructor.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_name` | `positional or keyword` | `str` | `-` |
| `params` | `positional or keyword` | `dict` | `-` |

**Returns:** `Tuple[dict, dict]`

**Returned dictionary keys visible in the code**

`align_center`, `align_to`, `x_offset`, `y_offset`, `angle`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`params.items`, `_parse_bool_param`, `lower`, `isinstance`, `ValueError`, `_parse_float_param`, `value.strip`, `join`, `sorted`

### `_transform_has_translation`

**Source lines:** `1555-1562`

```python
def _transform_has_translationtransform: dict, tol: float=1e-12
```

**Summary:** Return True if the transform contains any translation-like request.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `transform` | `positional or keyword` | `dict` | `-` |
| `tol` | `positional or keyword` | `float` | `1e-12` |

**Returns:** `bool`

**Function/method calls visible in the code**

`abs`

### `_transform_is_active`

**Source lines:** `1566-1568`

```python
def _transform_is_activetransform: dict, tol: float=1e-12
```

**Summary:** Return True if any section-level transform is effectively requested.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `transform` | `positional or keyword` | `dict` | `-` |
| `tol` | `positional or keyword` | `float` | `1e-12` |

**Returns:** `bool`

**Function/method calls visible in the code**

`_transform_has_translation`, `abs`

### `_validate_transform_pair`

**Source lines:** `1572-1605`

```python
def _validate_transform_pairsection_s0: str, section_s1: str, transform_s0: dict, transform_s1: dict, auto_align: bool
```

**Summary:** Validate pairwise section-level transform semantics.

**Docstring details**

```text
The rules are intentionally strict. If the relative placement of S0 and S1
is not fully determined by the explicit parameters, the function stops.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_s0` | `positional or keyword` | `str` | `-` |
| `section_s1` | `positional or keyword` | `str` | `-` |
| `transform_s0` | `positional or keyword` | `dict` | `-` |
| `transform_s1` | `positional or keyword` | `dict` | `-` |
| `auto_align` | `positional or keyword` | `bool` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`, `_transform_has_translation`

### `_apply_standalone_section_transform`

**Source lines:** `1609-1621`

```python
def _apply_standalone_section_transformgeometry: Any, transform: dict
```

**Summary:** Apply the transforms that do not depend on the other section.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geometry` | `positional or keyword` | `Any` | `-` |
| `transform` | `positional or keyword` | `dict` | `-` |

**Returns:** `Any`

**Function/method calls visible in the code**

`result.align_center`, `result.shift_section`, `abs`, `result.rotate_section`

### `_apply_dependent_section_transform`

**Source lines:** `1625-1642`

```python
def _apply_dependent_section_transformgeometry: Any, reference_geometry: Any, transform: dict
```

**Summary:** Apply a transform that contains an explicit align_to dependency.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geometry` | `positional or keyword` | `Any` | `-` |
| `reference_geometry` | `positional or keyword` | `Any` | `-` |
| `transform` | `positional or keyword` | `dict` | `-` |

**Returns:** `Any`

**Function/method calls visible in the code**

`geometry.align_to`, `result.shift_section`, `abs`, `result.rotate_section`

### `_build_geometry`

**Source lines:** `1646-1664`

```python
def _build_geometrysection_name: str, params: dict
```

**Summary:** Build one sectionproperties geometry from pure constructor parameters.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_name` | `positional or keyword` | `str` | `-` |
| `params` | `positional or keyword` | `dict` | `-` |

**Returns:** `Any`

**Raises visible in the code**

- `ValueError`
- `ImportError`

**Function/method calls visible in the code**

`sorted`, `getattr`, `fn`, `intersection`, `ValueError`, `ImportError`, `params.items`, `set`

### `_build_transformed_section_pair`

**Source lines:** `1668-1717`

```python
def _build_transformed_section_pairsection_s0: str, section_s1: str, params_s0: dict, params_s1: dict, auto_align: bool, morph_mode: str
```

**Summary:** Build S0 and S1 and apply deterministic section-level SP transforms.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_s0` | `positional or keyword` | `str` | `-` |
| `section_s1` | `positional or keyword` | `str` | `-` |
| `params_s0` | `positional or keyword` | `dict` | `-` |
| `params_s1` | `positional or keyword` | `dict` | `-` |
| `auto_align` | `positional or keyword` | `bool` | `-` |
| `morph_mode` | `positional or keyword` | `str` | `-` |

**Returns:** `Tuple[Any, Any, dict, dict]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`_split_section_params`, `_validate_transform_pair`, `_build_geometry`, `ValueError`, `_apply_standalone_section_transform`, `_apply_dependent_section_transform`, `_transform_is_active`

### `sp_sections_to_csf_yaml`

**Source lines:** `1721-1833`

```python
def sp_sections_to_csf_yamlsection_s0: str, params_s0: dict, section_s1: Optional[str], params_s1: dict, output_path: 'str | Path', n: Optional[int]=None, name: Optional[str]=None, comment: Optional[str]=None, solid_weight: float=1.0, void_weight: float=0.0, indent: int=8, precision: int=6, dx0: Optional[float]=None, dy0: Optional[float]=None, dx1: Optional[float]=None, dy1: Optional[float]=None, twist0_deg: float=0.0, twist1_deg: float=0.0, auto_align: bool=True, morph_mode: str='perimeter', cell: bool=False
```

**Summary:** High-level API using section names + parameter dictionaries.

**Docstring details**

```text
The dictionaries may contain both sectionproperties constructor parameters and
the explicit section-level transform keys:
    - align_center : bool
    - align_to     : top | bottom | left | right
    - x_offset     : float
    - y_offset     : float
    - angle        : float (degrees CCW)

The transform layer is applied before the existing CSF export layer. The two
layers are kept separate on purpose so the current exporter semantics remain
unchanged.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_s0` | `positional or keyword` | `str` | `-` |
| `params_s0` | `positional or keyword` | `dict` | `-` |
| `section_s1` | `positional or keyword` | `Optional[str]` | `-` |
| `params_s1` | `positional or keyword` | `dict` | `-` |
| `output_path` | `positional or keyword` | `'str | Path'` | `-` |
| `n` | `positional or keyword` | `Optional[int]` | `None` |
| `name` | `positional or keyword` | `Optional[str]` | `None` |
| `comment` | `positional or keyword` | `Optional[str]` | `None` |
| `solid_weight` | `positional or keyword` | `float` | `1.0` |
| `void_weight` | `positional or keyword` | `float` | `0.0` |
| `indent` | `positional or keyword` | `int` | `8` |
| `precision` | `positional or keyword` | `int` | `6` |
| `dx0` | `positional or keyword` | `Optional[float]` | `None` |
| `dy0` | `positional or keyword` | `Optional[float]` | `None` |
| `dx1` | `positional or keyword` | `Optional[float]` | `None` |
| `dy1` | `positional or keyword` | `Optional[float]` | `None` |
| `twist0_deg` | `positional or keyword` | `float` | `0.0` |
| `twist1_deg` | `positional or keyword` | `float` | `0.0` |
| `auto_align` | `positional or keyword` | `bool` | `True` |
| `morph_mode` | `positional or keyword` | `str` | `'perimeter'` |
| `cell` | `positional or keyword` | `bool` | `False` |

**Returns:** `Path`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`_extract_required_z`, `_build_transformed_section_pair`, `sp_to_csf_yaml`, `ValueError`, `_split_section_params`, `_write_feature_morph_yaml`, `_transform_is_active`

## Feature-aware morph helpers

### `_draw_radius_points`

**Source lines:** `415-435`

```python
def _draw_radius_pointspt: Point, r: float, theta: float, n: int, ccw: bool=True, phi: float=1.5707963267948966
```

**Summary:** Generate radius points using sectionproperties' draw_radius convention.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `pt` | `positional or keyword` | `Point` | `-` |
| `r` | `positional or keyword` | `float` | `-` |
| `theta` | `positional or keyword` | `float` | `-` |
| `n` | `positional or keyword` | `int` | `-` |
| `ccw` | `positional or keyword` | `bool` | `True` |
| `phi` | `positional or keyword` | `float` | `1.5707963267948966` |

**Returns:** `List[Point]`

**Function/method calls visible in the code**

`max`, `range`, `result.append`, `math.cos`, `math.sin`

### `_polyline_length`

**Source lines:** `438-443`

```python
def _polyline_lengthpts: Sequence[Point]
```

**Summary:** Return the open-polyline length.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `pts` | `positional or keyword` | `Sequence[Point]` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`zip`

### `_resample_open_polyline`

**Source lines:** `446-473`

```python
def _resample_open_polylinepts: Sequence[Point], n: int
```

**Summary:** Sample n points along an open polyline, including start but excluding end.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `pts` | `positional or keyword` | `Sequence[Point]` | `-` |
| `n` | `positional or keyword` | `int` | `-` |

**Returns:** `List[Point]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`zip`, `range`, `len`, `ValueError`, `arc.append`, `result.append`

## sectionproperties extraction helpers

### `_import_sp_geometry_types`

**Source lines:** `1100-1112`

```python
def _import_sp_geometry_types
```

**Summary:** Import Geometry and CompoundGeometry from sectionproperties.

**Returns:** `Tuple[Any, Any]`

**Raises visible in the code**

- `ImportError`

**Function/method calls visible in the code**

`ImportError`

### `_flatten_geometry_to_polygons`

**Source lines:** `1115-1138`

```python
def _flatten_geometry_to_polygonsgeometry: Any
```

**Summary:** Return the Shapely polygons contained in a sectionproperties geometry.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geometry` | `positional or keyword` | `Any` | `-` |

**Returns:** `List[Any]`

**Raises visible in the code**

- `ImportError`
- `TypeError`

**Function/method calls visible in the code**

`_import_sp_geometry_types`, `isinstance`, `list`, `ImportError`, `TypeError`, `polygons.extend`, `polygons.append`, `type`

### `geometry_centroid`

**Source lines:** `1141-1144`

```python
def geometry_centroidgeometry: Any
```

**Summary:** Return the centroid (cx, cy) of the union of all polygons in a

**Docstring details**

```text
sectionproperties geometry object.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geometry` | `positional or keyword` | `Any` | `-` |

**Returns:** `Tuple[float, float]`

**Function/method calls visible in the code**

`_geometry_centroid`

## Pairwise block builder

### `_pair_to_blocks`

**Source lines:** `1162-1257`

```python
def _pair_to_blockspoly_s0: Any, poly_s1: Any, base_name: str, n: Optional[int], solid_weight: float, void_weight: float, indent: int, precision: int, dx0: float, dy0: float, dx1: float, dy1: float, twist0_deg: float, twist1_deg: float, morph_mode: str='perimeter', cell: bool=False
```

**Summary:** Convert one polygon pair (exterior + holes) into matching CSF YAML blocks.

**Docstring details**

```text
Both sections must have the same number of holes.
Offset and twist are applied after resampling/alignment.

When cell=True, each polygon must have exactly one hole. The exterior and
the hole are written as one CSF @cell polygon.

n=None (native mode): use SP native vertices without resampling.
    Correct for tapered sections of the same type — SP generates
    vertices in the same parametric order for both sections.
n=int (resample mode): resample both rings to n equidistant points.
    Required for morph mode where section types differ.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly_s0` | `positional or keyword` | `Any` | `-` |
| `poly_s1` | `positional or keyword` | `Any` | `-` |
| `base_name` | `positional or keyword` | `str` | `-` |
| `n` | `positional or keyword` | `Optional[int]` | `-` |
| `solid_weight` | `positional or keyword` | `float` | `-` |
| `void_weight` | `positional or keyword` | `float` | `-` |
| `indent` | `positional or keyword` | `int` | `-` |
| `precision` | `positional or keyword` | `int` | `-` |
| `dx0` | `positional or keyword` | `float` | `-` |
| `dy0` | `positional or keyword` | `float` | `-` |
| `dx1` | `positional or keyword` | `float` | `-` |
| `dy1` | `positional or keyword` | `float` | `-` |
| `twist0_deg` | `positional or keyword` | `float` | `-` |
| `twist1_deg` | `positional or keyword` | `float` | `-` |
| `morph_mode` | `positional or keyword` | `str` | `'perimeter'` |
| `cell` | `positional or keyword` | `bool` | `False` |

**Returns:** `Tuple[List[str], List[str]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`list`, `_process`, `enumerate`, `len`, `ValueError`, `_translate_points`, `_rotate_points`, `_poly_block`, `zip`, `blocks_s0.append`, `blocks_s1.append`, `_native_ring_to_vertices`, `_morph_ring_to_vertices`, `base_name.lower`, `_cell_vertices_from_outer_inner`

## Public API

### `sp_to_csf_yaml`

**Source lines:** `1264-1427`

```python
def sp_to_csf_yamlgeometry_s0: Any, geometry_s1: Any, z0: float, z1: float, output_path: 'str | Path', n: Optional[int]=None, name: Optional[str]=None, comment: Optional[str]=None, solid_weight: float=1.0, void_weight: float=0.0, indent: int=8, precision: int=6, dx0: Optional[float]=None, dy0: Optional[float]=None, dx1: Optional[float]=None, dy1: Optional[float]=None, twist0_deg: float=0.0, twist1_deg: float=0.0, auto_align: bool=True, morph_mode: str='perimeter', cell: bool=False
```

**Summary:** Convert two sectionproperties geometries to a CSF YAML file.

**Docstring details**

```text
Parameters
----------
geometry_s0, geometry_s1 : Geometry or CompoundGeometry
    Start and end sections. May be of different types (morphing).
z0, z1 : float
    z-coordinates of S0 and S1.
output_path : str or Path
    Output YAML file path.
n : int or None
    Number of vertices per ring after resampling.
    None (default): native mode — use SP vertices without resampling.
        Correct for tapered sections of the same type (same n_r).
    int: resample mode — equidistant arc-length resampling.
        Required for morph mode (different section types).
        Use higher values for sections with sharp corners (>= 64).
name : str, optional
    Polygon base name (default: "section").
comment : str, optional
    Comment added to the YAML header.
solid_weight : float
    Weight of exterior polygons (default 1.0).
void_weight : float
    Weight of interior rings / holes (default 0.0).
dx0, dy0 : float, optional
    Explicit offset for S0. If None and auto_align=True, computed
    automatically so that the S0 centroid maps to the origin.
dx1, dy1 : float, optional
    Explicit offset for S1. If None and auto_align=True, computed
    automatically so that the S1 centroid aligns with the S0 centroid.
twist0_deg, twist1_deg : float
    Rotation of S0 and S1 around their centroid in degrees CCW (default 0).
auto_align : bool
    If True (default), automatically offset S0 and S1 so their centroids
    coincide in the CSF coordinate frame. Explicit dx/dy values override
    auto-alignment for the respective section.
cell : bool
    If True, export one @cell polygon by joining the exterior ring and the
    clockwise hole ring into a single vertex sequence.

Returns
-------
Path
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geometry_s0` | `positional or keyword` | `Any` | `-` |
| `geometry_s1` | `positional or keyword` | `Any` | `-` |
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `output_path` | `positional or keyword` | `'str | Path'` | `-` |
| `n` | `positional or keyword` | `Optional[int]` | `None` |
| `name` | `positional or keyword` | `Optional[str]` | `None` |
| `comment` | `positional or keyword` | `Optional[str]` | `None` |
| `solid_weight` | `positional or keyword` | `float` | `1.0` |
| `void_weight` | `positional or keyword` | `float` | `0.0` |
| `indent` | `positional or keyword` | `int` | `8` |
| `precision` | `positional or keyword` | `int` | `6` |
| `dx0` | `positional or keyword` | `Optional[float]` | `None` |
| `dy0` | `positional or keyword` | `Optional[float]` | `None` |
| `dx1` | `positional or keyword` | `Optional[float]` | `None` |
| `dy1` | `positional or keyword` | `Optional[float]` | `None` |
| `twist0_deg` | `positional or keyword` | `float` | `0.0` |
| `twist1_deg` | `positional or keyword` | `float` | `0.0` |
| `auto_align` | `positional or keyword` | `bool` | `True` |
| `morph_mode` | `positional or keyword` | `str` | `'perimeter'` |
| `cell` | `positional or keyword` | `bool` | `False` |

**Returns:** `Path`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`Path`, `_flatten_geometry_to_polygons`, `_geometry_centroid`, `enumerate`, `join`, `output_path.write_text`, `ValueError`, `len`, `zip`, `_pair_to_blocks`, `blocks_s0.extend`, `blocks_s1.extend`, `header_lines.append`, `_fmt_float`

## CLI helpers and section-level transforms

### `_coerce`

**Source lines:** `1447-1462`

```python
def _coercevalue: str
```

**Summary:** Coerce a CLI token to bool, int, float, or leave it as string.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `str` | `-` |

**Returns:** `Any`

**Function/method calls visible in the code**

`lower`, `int`, `float`, `value.strip`

### `_parse_section_params`

**Source lines:** `1465-1475`

```python
def _parse_section_paramsraw: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `raw` | `positional or keyword` | `str` | `-` |

**Returns:** `dict`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`raw.split`, `token.strip`, `token.split`, `_coerce`, `ValueError`, `k.strip`, `v.strip`

### `_extract_required_z`

**Source lines:** `1478-1485`

```python
def _extract_required_zparams: dict, section_label: str
```

**Summary:** Read the required z coordinate for one endpoint section.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `params` | `positional or keyword` | `dict` | `-` |
| `section_label` | `positional or keyword` | `str` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `ValueError`, `isinstance`

## CLI entry point

### `_generate_actions_yaml`

**Source lines:** `1840-1898`

```python
def _generate_actions_yamloutput_path: Path, z0: float, z1: float, title: str='CSF Tower', precision: int=6
```

**Summary:** Generate a default CSF actions YAML file for quick exploration.

**Docstring details**

```text
Includes:
- plot_volume_3d        — 3D ruled volume visualization
- plot_properties       — continuous property variation along z
- plot_section_2d       — 2D cross-section at 3 stations (base, mid, top)
- section_selected_analysis — full property table at mid-height
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `output_path` | `positional or keyword` | `Path` | `-` |
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `title` | `positional or keyword` | `str` | `'CSF Tower'` |
| `precision` | `positional or keyword` | `int` | `6` |

**Returns:** `Path`

**Function/method calls visible in the code**

`round`, `output_path.write_text`, `_fmt_float`

## Full section property table at mid-height

### `main`

**Source lines:** `1901-2123`

```python
def main
```

**Summary:** Docstring absent.

**Returns:** `int`

**Function/method calls visible in the code**

`argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_args`, `_geometry_centroid`, `print`, `_parse_section_params`, `_extract_required_z`, `_build_transformed_section_pair`, `sp_to_csf_yaml`, `_transform_is_active`, `with_name`, `_generate_actions_yaml`, `_write_feature_morph_yaml`, `with_suffix`, `Path`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
