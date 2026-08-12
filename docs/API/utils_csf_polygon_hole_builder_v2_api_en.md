# API Reference - `csf_polygon_hole_builder_v2.py`

This document covers the top-level classes and functions defined in `src/csf/utils/csf_polygon_hole_builder_v2.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/utils/csf_polygon_hole_builder_v2.py`
- Output file: `docs/API/utils_csf_polygon_hole_builder_v2_api_en.md`
- Top-level function definitions found: `9`.
- Top-level classes found: `1`.
- Duplicate function names found: `0`.

## Module docstring

```text
csf_polygon_hole_builder_v1.py

Generates a CSF geometry YAML with two stations (S0, S1) for a ring-like shape.

Two modeling modes
------------------
SINGLE_POLE = False
    Writes ONE polygon per station using a single flattened vertex stream that encodes
    two closed loops:
      - outer loop: CCW
      - inner loop: CW  (hole encoding via signed-area convention)
    Each loop is explicitly closed by repeating its first vertex.

SINGLE_POLE = True
    Writes TWO polygons per station:
      - outer polygon with weight = 1.0
      - inner polygon (void) with weight = 0.0
    Both polygons are emitted CCW (CSF precondition).

YAML format emitted
-------------------
CSF:
  sections:
    S0:
      z: <z0>
      polygons:
        <outer_name>: ...
        [<void_name>: ...]   # only if SINGLE_POLE=True
    S1:
      z: <z1>
      polygons:
        <outer_name>: ...
        [<void_name>: ...]   # only if SINGLE_POLE=True
```

## Public API index

- `Pt` - line 48
- `def make_tagged_namebase: str='poly'` - line 53
- `def make_void_namebase: str='void'` - line 58
- `def regular_ngon_on_bbox_ccwcenter: Pt, lx: float, ly: float, n_sides: int, start_angle: float` - line 63
- `def reverse_looploop: List[Pt]` - line 86
- `def build_multi_loop_streaminner_loop: List[Pt], outer_loop: List[Pt]` - line 98
- `def _fmt_floatx: float` - line 110
- `def _write_yaml_with_headerpath: str, header_lines: List[str], body_lines: List[str]` - line 115
- `def build_yaml_body_singlepolyouter_name: str, z0: float, z1: float, w0: float, w1: float, stream0: List[Pt], stream1: List[Pt]` - line 121
- `def build_yaml_body_twopolyouter_name: str, void_name: str, z0: float, z1: float, w_outer0: float, w_outer1: float, outer0: List[Pt], outer1: List[Pt], void0: List[Pt], void1: List[Pt]` - line 153

## API details

## Classes

### `Pt`

**Source lines:** `48-50`

**Decorators**

- `dataclass(frozen=True)`

```python
class Pt
```

**Summary:** Docstring absent.

## Functions

## Geometry primitives

### `make_tagged_name`

**Source lines:** `53-55`

```python
def make_tagged_namebase: str='poly'
```

**Summary:** Return a polygon name tagged for the thin-wall path (name only).

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `base` | `positional or keyword` | `str` | `'poly'` |

**Returns:** `str`

### `make_void_name`

**Source lines:** `58-60`

```python
def make_void_namebase: str='void'
```

**Summary:** Return a conventional name for the void polygon.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `base` | `positional or keyword` | `str` | `'void'` |

**Returns:** `str`

### `regular_ngon_on_bbox_ccw`

**Source lines:** `63-83`

```python
def regular_ngon_on_bbox_ccwcenter: Pt, lx: float, ly: float, n_sides: int, start_angle: float
```

**Summary:** Build a CCW n-gon sampled on an axis-aligned ellipse that fits the given bounding box.

**Docstring details**

```text
The loop is returned *not closed* (no repeated first point).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `center` | `positional or keyword` | `Pt` | `-` |
| `lx` | `positional or keyword` | `float` | `-` |
| `ly` | `positional or keyword` | `float` | `-` |
| `n_sides` | `positional or keyword` | `int` | `-` |
| `start_angle` | `positional or keyword` | `float` | `-` |

**Returns:** `List[Pt]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`range`, `ValueError`, `pts.append`, `Pt`, `math.cos`, `math.sin`

### `reverse_loop`

**Source lines:** `86-95`

```python
def reverse_looploop: List[Pt]
```

**Summary:** Reverse loop traversal while keeping the same start vertex.

**Docstring details**

```text
If loop = [p0, p1, ..., p_{n-1}] (CCW), the returned loop is:
  [p0, p_{n-1}, ..., p1] (CW)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `loop` | `positional or keyword` | `List[Pt]` | `-` |

**Returns:** `List[Pt]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`len`, `ValueError`, `list`, `reversed`

## Top-level functions

### `build_multi_loop_stream`

**Source lines:** `98-107`

```python
def build_multi_loop_streaminner_loop: List[Pt], outer_loop: List[Pt]
```

**Summary:** Encode two loops into one flattened vertex stream with explicit loop closures.

**Docstring details**

```text
Encoding:
  inner + [inner[0]] + outer + [outer[0]]
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `inner_loop` | `positional or keyword` | `List[Pt]` | `-` |
| `outer_loop` | `positional or keyword` | `List[Pt]` | `-` |

**Returns:** `List[Pt]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`, `len`

### `_fmt_float`

**Source lines:** `110-112`

```python
def _fmt_floatx: float
```

**Summary:** Deterministic float formatting for YAML.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `x` | `positional or keyword` | `float` | `-` |

**Returns:** `str`

### `_write_yaml_with_header`

**Source lines:** `115-118`

```python
def _write_yaml_with_headerpath: str, header_lines: List[str], body_lines: List[str]
```

**Summary:** Write YAML by prepending a comment header.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `path` | `positional or keyword` | `str` | `-` |
| `header_lines` | `positional or keyword` | `List[str]` | `-` |
| `body_lines` | `positional or keyword` | `List[str]` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`open`, `f.write`, `join`

### `build_yaml_body_singlepoly`

**Source lines:** `121-150`

```python
def build_yaml_body_singlepolyouter_name: str, z0: float, z1: float, w0: float, w1: float, stream0: List[Pt], stream1: List[Pt]
```

**Summary:** Build YAML body for one polygon per station (multi-loop stream).

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `outer_name` | `positional or keyword` | `str` | `-` |
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `w0` | `positional or keyword` | `float` | `-` |
| `w1` | `positional or keyword` | `float` | `-` |
| `stream0` | `positional or keyword` | `List[Pt]` | `-` |
| `stream1` | `positional or keyword` | `List[Pt]` | `-` |

**Returns:** `List[str]`

**Function/method calls visible in the code**

`lines.append`, `_fmt_float`

### `build_yaml_body_twopoly`

**Source lines:** `153-195`

```python
def build_yaml_body_twopolyouter_name: str, void_name: str, z0: float, z1: float, w_outer0: float, w_outer1: float, outer0: List[Pt], outer1: List[Pt], void0: List[Pt], void1: List[Pt]
```

**Summary:** Build YAML body for two polygons per station: outer (w=1) and void (w=0).

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `outer_name` | `positional or keyword` | `str` | `-` |
| `void_name` | `positional or keyword` | `str` | `-` |
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `w_outer0` | `positional or keyword` | `float` | `-` |
| `w_outer1` | `positional or keyword` | `float` | `-` |
| `outer0` | `positional or keyword` | `List[Pt]` | `-` |
| `outer1` | `positional or keyword` | `List[Pt]` | `-` |
| `void0` | `positional or keyword` | `List[Pt]` | `-` |
| `void1` | `positional or keyword` | `List[Pt]` | `-` |

**Returns:** `List[str]`

**Function/method calls visible in the code**

`lines.append`, `_fmt_float`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
