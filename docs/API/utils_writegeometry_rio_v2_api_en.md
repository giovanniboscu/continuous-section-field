# API Reference - `writegeometry_rio_v2.py`

This document covers the top-level classes and functions defined in `src/csf/utils/writegeometry_rio_v2.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/utils/writegeometry_rio_v2.py`
- Output file: `docs/API/utils_writegeometry_rio_v2_api_en.md`
- Top-level function definitions found: `19`.
- Top-level classes found: `2`.
- Duplicate function names found: `0`.

## Public API index

- `CleanDumper` - line 9
- `Point` - line 14
- `def _repr_pointdumper, data` - line 18
- `def signed_areavertices` - line 28
- `def close_looppoints` - line 40
- `def to_pointsvertices` - line 50
- `def parse_boolvalue` - line 54
- `def rotate_pointspoints, cx, cy, angle_deg` - line 65
- `def rounded_rect_loopcx, cy, dx, dy, R, n, ccw=True` - line 75
- `def make_squarecx, cy, area` - line 120
- `def ensure_ccwpoints` - line 126
- `def build_single_cell_verticesouter_loop, inner_loop` - line 133
- `def offset_rounded_rect_paramscx, cy, dx, dy, R, offset` - line 138
- `def expand_rounded_rect_paramscx, cy, dx, dy, R, offset` - line 149
- `def build_rebar_centers_on_two_rowscx, cy, outer_dx, outer_dy, outer_R, inner_dx, inner_dy, inner_R, n_row1, n_row2, d_row1_outer, d_row2_inner` - line 160
- `def build_section_geometrycx, cy, dx, dy, R, tg, N, n_bars_row1, n_bars_row2, dist_row1_outer, dist_row2_inner, twist_deg=0.0` - line 190
- `def get_rebar_areaargs, row, section_name` - line 256
- `def build_section_dictz, section_geom, name, t_val, args` - line 284
- `def _pair_entrys0_name, s1_name, law` - line 317
- `def build_weight_lawsargs` - line 322
- `def build_geometryargs` - line 369

## API details

## Classes

### `CleanDumper`

**Source lines:** `9-11`

```python
class CleanDumper(yaml.SafeDumper)
```

**Summary:** Docstring absent.

**Methods visible in the code**

- `ignore_aliases` - line 10

#### Method details

##### `CleanDumper.ignore_aliases`

**Source lines:** `10-11`

```python
def ignore_aliasesself, data
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `data` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

### `Point`

**Source lines:** `14-15`

```python
class Point(list)
```

**Summary:** Docstring absent.

## Functions

## YAML output helpers

### `_repr_point`

**Source lines:** `18-19`

```python
def _repr_pointdumper, data
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `dumper` | `positional or keyword` | `not annotated` | `-` |
| `data` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`dumper.represent_sequence`, `list`

## Geometry helpers

### `signed_area`

**Source lines:** `28-37`

```python
def signed_areavertices
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `vertices` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`len`, `range`

### `close_loop`

**Source lines:** `40-47`

```python
def close_looppoints
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

### `to_points`

**Source lines:** `50-51`

```python
def to_pointsvertices
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `vertices` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`Point`, `float`

### `parse_bool`

**Source lines:** `54-62`

```python
def parse_boolvalue
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Raises visible in the code**

- `argparse.ArgumentTypeError`

**Function/method calls visible in the code**

`isinstance`, `lower`, `argparse.ArgumentTypeError`, `strip`, `str`

### `rotate_points`

**Source lines:** `65-72`

```python
def rotate_pointspoints, cx, cy, angle_deg
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `positional or keyword` | `not annotated` | `-` |
| `cx` | `positional or keyword` | `not annotated` | `-` |
| `cy` | `positional or keyword` | `not annotated` | `-` |
| `angle_deg` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`math.radians`, `math.cos`, `math.sin`, `out.append`

## Top-level functions

### `rounded_rect_loop`

**Source lines:** `75-117`

```python
def rounded_rect_loopcx, cy, dx, dy, R, n, ccw=True
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cx` | `positional or keyword` | `not annotated` | `-` |
| `cy` | `positional or keyword` | `not annotated` | `-` |
| `dx` | `positional or keyword` | `not annotated` | `-` |
| `dy` | `positional or keyword` | `not annotated` | `-` |
| `R` | `positional or keyword` | `not annotated` | `-` |
| `n` | `positional or keyword` | `not annotated` | `-` |
| `ccw` | `positional or keyword` | `not annotated` | `True` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`max`, `sum`, `cum.append`, `at_s`, `list`, `range`, `reversed`, `len`, `math.cos`, `math.sin`

### `ensure_ccw`

**Source lines:** `126-130`

```python
def ensure_ccwpoints
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`close_loop`, `signed_area`, `list`, `reversed`

### `build_single_cell_vertices`

**Source lines:** `133-135`

```python
def build_single_cell_verticesouter_loop, inner_loop
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `outer_loop` | `positional or keyword` | `not annotated` | `-` |
| `inner_loop` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`close_loop`

## The same generator is used for both base and head.

### `make_square`

**Source lines:** `120-123`

```python
def make_squarecx, cy, area
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cx` | `positional or keyword` | `not annotated` | `-` |
| `cy` | `positional or keyword` | `not annotated` | `-` |
| `area` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`math.sqrt`

## The inner loop is expected in single-polygon orientation.

### `offset_rounded_rect_params`

**Source lines:** `138-146`

```python
def offset_rounded_rect_paramscx, cy, dx, dy, R, offset
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cx` | `positional or keyword` | `not annotated` | `-` |
| `cy` | `positional or keyword` | `not annotated` | `-` |
| `dx` | `positional or keyword` | `not annotated` | `-` |
| `dy` | `positional or keyword` | `not annotated` | `-` |
| `R` | `positional or keyword` | `not annotated` | `-` |
| `offset` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`

### `expand_rounded_rect_params`

**Source lines:** `149-157`

```python
def expand_rounded_rect_paramscx, cy, dx, dy, R, offset
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cx` | `positional or keyword` | `not annotated` | `-` |
| `cy` | `positional or keyword` | `not annotated` | `-` |
| `dx` | `positional or keyword` | `not annotated` | `-` |
| `dy` | `positional or keyword` | `not annotated` | `-` |
| `R` | `positional or keyword` | `not annotated` | `-` |
| `offset` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`

### `build_rebar_centers_on_two_rows`

**Source lines:** `160-187`

```python
def build_rebar_centers_on_two_rowscx, cy, outer_dx, outer_dy, outer_R, inner_dx, inner_dy, inner_R, n_row1, n_row2, d_row1_outer, d_row2_inner
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cx` | `positional or keyword` | `not annotated` | `-` |
| `cy` | `positional or keyword` | `not annotated` | `-` |
| `outer_dx` | `positional or keyword` | `not annotated` | `-` |
| `outer_dy` | `positional or keyword` | `not annotated` | `-` |
| `outer_R` | `positional or keyword` | `not annotated` | `-` |
| `inner_dx` | `positional or keyword` | `not annotated` | `-` |
| `inner_dy` | `positional or keyword` | `not annotated` | `-` |
| `inner_R` | `positional or keyword` | `not annotated` | `-` |
| `n_row1` | `positional or keyword` | `not annotated` | `-` |
| `n_row2` | `positional or keyword` | `not annotated` | `-` |
| `d_row1_outer` | `positional or keyword` | `not annotated` | `-` |
| `d_row2_inner` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`offset_rounded_rect_params`, `rounded_rect_loop`, `expand_rounded_rect_params`

## Row 2 is generated by expanding outward from the inner contour.

### `build_section_geometry`

**Source lines:** `190-253`

```python
def build_section_geometrycx, cy, dx, dy, R, tg, N, n_bars_row1, n_bars_row2, dist_row1_outer, dist_row2_inner, twist_deg=0.0
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cx` | `positional or keyword` | `not annotated` | `-` |
| `cy` | `positional or keyword` | `not annotated` | `-` |
| `dx` | `positional or keyword` | `not annotated` | `-` |
| `dy` | `positional or keyword` | `not annotated` | `-` |
| `R` | `positional or keyword` | `not annotated` | `-` |
| `tg` | `positional or keyword` | `not annotated` | `-` |
| `N` | `positional or keyword` | `not annotated` | `-` |
| `n_bars_row1` | `positional or keyword` | `not annotated` | `-` |
| `n_bars_row2` | `positional or keyword` | `not annotated` | `-` |
| `dist_row1_outer` | `positional or keyword` | `not annotated` | `-` |
| `dist_row2_inner` | `positional or keyword` | `not annotated` | `-` |
| `twist_deg` | `positional or keyword` | `not annotated` | `0.0` |

**Returns:** `not annotated`

**Returned dictionary keys visible in the code**

`outer`, `inner_ccw`, `main_single`, `row1_centers`, `row2_centers`

**Function/method calls visible in the code**

`max`, `rounded_rect_loop`, `list`, `build_single_cell_vertices`, `build_rebar_centers_on_two_rows`, `reversed`, `rotate_points`, `ensure_ccw`

## Rebuild the single-polygon representation from normalized loops.

### `get_rebar_area`

**Source lines:** `256-281`

```python
def get_rebar_areaargs, row, section_name
```

**Summary:** Return the equivalent square area for a rebar row at one section.

**Docstring details**

```text
Backward compatibility:
- If only --area-bar-row1 / --area-bar-row2 are provided, the same
  bar area is used in S0 and S1.
- If section-specific values are provided, they override the generic
  value only for the matching section.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `args` | `positional or keyword` | `not annotated` | `-` |
| `row` | `positional or keyword` | `not annotated` | `-` |
| `section_name` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`

### `build_section_dict`

**Source lines:** `284-314`

```python
def build_section_dictz, section_geom, name, t_val, args
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `z` | `positional or keyword` | `not annotated` | `-` |
| `section_geom` | `positional or keyword` | `not annotated` | `-` |
| `name` | `positional or keyword` | `not annotated` | `-` |
| `t_val` | `positional or keyword` | `not annotated` | `-` |
| `args` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Returned dictionary keys visible in the code**

`z`, `polygons`, `weight`, `vertices`

**Function/method calls visible in the code**

`get_rebar_area`, `enumerate`, `float`, `to_points`, `ensure_ccw`, `make_square`

## Row 2 bars are written independently to preserve the original naming/output scheme.

### `_pair_entry`

**Source lines:** `317-319`

```python
def _pair_entrys0_name, s1_name, law
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `s0_name` | `positional or keyword` | `not annotated` | `-` |
| `s1_name` | `positional or keyword` | `not annotated` | `-` |
| `law` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

## Each weight-law entry is emitted as one compact string in the YAML list.

### `build_weight_laws`

**Source lines:** `322-363`

```python
def build_weight_lawsargs
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `args` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`range`, `ValueError`, `weight_laws.append`, `len`, `_pair_entry`

## Main builder logic

### `build_geometry`

**Source lines:** `369-414`

```python
def build_geometryargs
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `args` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Returned dictionary keys visible in the code**

`CSF`, `sections`, `S0`, `S1`

**Function/method calls visible in the code**

`build_section_geometry`, `build_weight_laws`, `build_section_dict`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
