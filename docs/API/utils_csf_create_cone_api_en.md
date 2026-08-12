# API Reference - `csf_create_cone.py`

This document covers the top-level classes and functions defined in `src/csf/utils/csf_create_cone.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/utils/csf_create_cone.py`
- Output file: `docs/API/utils_csf_create_cone_api_en.md`
- Top-level function definitions found: `5`.
- Top-level classes found: `3`.
- Duplicate function names found: `0`.

## Module docstring

```text
csf_crete_cone_v3.py

CSF YAML generator for a tapered circular member with:
  - Outer concrete ring
  - Middle steel ring
  - Inner concrete ring
  - Central hole (void)

This version writes the rings *explicitly* in the YAML so you can SEE them.
Each ring is defined by two polygons:
  (outer boundary, weight +W) and (inner boundary, weight -W)

Radial layout (outside -> inside)
---------------------------------
R0 > R1 > R2 > R3 >= 0

  Outer concrete ring: r in [R1, R0] with weight Wc_outer
  Steel ring         : r in [R2, R1] with weight Ws
  Inner concrete ring: r in [R3, R2] with weight Wc_inner
  Hole (void)        : r in [0,  R3] with weight 0

Transformed-section weights
---------------------------
W = E_material / E_ref (dimensionless)

Typical choice:
  E_ref = E_concrete
  -> concrete weight = 1.0
  -> steel weight    ~ E_steel / E_concrete (e.g., 200/30 ≈ 6.67)

YAML formatting
--------------
- Vertices as:  - [x, y]
- Floats with 6 decimals.

Dependencies
------------
- PyYAML:  python -m pip install pyyaml
```

## Public API index

- `CSFDumper` - line 57
- `RingRadii4` - line 105
- `Weights3` - line 118
- `def _repr_floatdumper: yaml.Dumper, value: float` - line 62
- `def _repr_pointdumper: yaml.Dumper, value: tuple` - line 66
- `def circle_polygonradius_m: float, n_sides: int, phase_rad: float=0.0, center_xy_m: Point=(0.0, 0.0)` - line 78
- `def build_section_explicit_3rings_holez_m: float, radii: RingRadii4, weights: Weights3, n_sides: int, phase_rad: float=0.0` - line 133
- `def main` - line 209

## API details

## Classes

### `CSFDumper`

**Source lines:** `57-59`

```python
class CSFDumper(yaml.SafeDumper)
```

**Summary:** Safe dumper with CSF-friendly float/vertex formatting.

### `RingRadii4`

**Source lines:** `105-114`

**Decorators**

- `dataclass(frozen=True)`

```python
class RingRadii4
```

**Summary:** R0 > R1 > R2 > R3 >= 0

**Methods visible in the code**

- `validate` - line 112

#### Method details

##### `RingRadii4.validate`

**Source lines:** `112-114`

```python
def validateself
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`

### `Weights3`

**Source lines:** `118-126`

**Decorators**

- `dataclass(frozen=True)`

```python
class Weights3
```

**Summary:** Transformed-section weights: W = E/E_ref

**Methods visible in the code**

- `validate` - line 124

#### Method details

##### `Weights3.validate`

**Source lines:** `124-126`

```python
def validateself
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`

## Functions

## YAML Dumper: fixed float format + points as [x, y]

### `_repr_float`

**Source lines:** `62-63`

```python
def _repr_floatdumper: yaml.Dumper, value: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `dumper` | `positional or keyword` | `yaml.Dumper` | `-` |
| `value` | `positional or keyword` | `float` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`dumper.represent_scalar`

### `_repr_point`

**Source lines:** `66-67`

```python
def _repr_pointdumper: yaml.Dumper, value: tuple
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `dumper` | `positional or keyword` | `yaml.Dumper` | `-` |
| `value` | `positional or keyword` | `tuple` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`dumper.represent_sequence`, `list`

## Geometry

### `circle_polygon`

**Source lines:** `78-97`

```python
def circle_polygonradius_m: float, n_sides: int, phase_rad: float=0.0, center_xy_m: Point=(0.0, 0.0)
```

**Summary:** CCW polygon approximation of a circle. Returns (x, y) tuples.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `radius_m` | `positional or keyword` | `float` | `-` |
| `n_sides` | `positional or keyword` | `int` | `-` |
| `phase_rad` | `positional or keyword` | `float` | `0.0` |
| `center_xy_m` | `positional or keyword` | `Point` | `(0.0, 0.0)` |

**Returns:** `List[tuple]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`range`, `ValueError`, `verts.append`, `math.cos`, `math.sin`

## CSF section builder (EXPLICIT rings)

### `build_section_explicit_3rings_hole`

**Source lines:** `133-187`

```python
def build_section_explicit_3rings_holez_m: float, radii: RingRadii4, weights: Weights3, n_sides: int, phase_rad: float=0.0
```

**Summary:** Explicit rings (each ring = outer(+W) + inner(-W)):

**Docstring details**

```text
Outer concrete ring: [R1, R0]
  Steel ring         : [R2, R1]
  Inner concrete ring: [R3, R2]
  Hole               : [0,  R3] (weight 0) produced by the last minus.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `z_m` | `positional or keyword` | `float` | `-` |
| `radii` | `positional or keyword` | `RingRadii4` | `-` |
| `weights` | `positional or keyword` | `Weights3` | `-` |
| `n_sides` | `positional or keyword` | `int` | `-` |
| `phase_rad` | `positional or keyword` | `float` | `0.0` |

**Returns:** `Dict`

**Returned dictionary keys visible in the code**

`conc_outer_plus_R0`, `conc_outer_minus_R1`, `steel_plus_R1`, `steel_minus_R2`, `conc_inner_plus_R2`, `conc_inner_minus_R3`, `z`, `polygons`, `weight`, `vertices`

**Function/method calls visible in the code**

`radii.validate`, `weights.validate`, `float`, `circle_polygon`

## from pole_utils import RingRadii4, Weights3, build_section_explicit_3rings_hole, CSFDumper

### `main`

**Source lines:** `209-316`

```python
def main
```

**Summary:** Docstring absent.

**Returns:** `None`

**Returned dictionary keys visible in the code**

`CSF`, `sections`, `S0`, `S1`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`max`, `RingRadii4`, `Weights3`, `build_section_explicit_3rings_hole`, `print`, `keys`, `ValueError`, `open`, `yaml.dump`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
