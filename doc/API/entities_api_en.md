# API Reference - `entities.py`

This document covers the top-level classes and functions defined in `src/csf/entities.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/entities.py`
- Output file: `doc/API/entities_api_en.md`
- Top-level function definitions found: `0`.
- Top-level classes found: `4`.
- Duplicate function names found: `0`.

## Public API index

- `CSFError` - line 5
- `Pt` - line 13
- `Polygon` - line 47
- `Section` - line 109

## API details

## Classes

### `CSFError`

**Source lines:** `5-6`

```python
class CSFError(ValueError)
```

**Summary:** Docstring absent.

### `Pt`

**Source lines:** `13-44`

**Decorators**

- `dataclass(frozen=True)`

```python
class Pt
```

**Summary:** Docstring absent.

**Methods visible in the code**

- `lerp` - line 17

#### Method details

##### `Pt.lerp`

**Source lines:** `17-44`

```python
def lerpself, other: 'Pt', z_real: float, length: float
```

**Summary:** Calculates the interpolated point at a specific distance using slopes.

**Docstring details**

```text
Args:
    self start point
    other (Pt): Ending point (top).
    z_real (float): relative Distance from the starting point (0 to length).
    length (float): Total vertical length of the segment.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `other` | `positional or keyword` | `'Pt'` | `-` |
| `z_real` | `positional or keyword` | `float` | `-` |
| `length` | `positional or keyword` | `float` | `-` |

**Returns:** `'Pt'`

**Function/method calls visible in the code**

`Pt`, `abs`

### `Polygon`

**Source lines:** `47-104`

**Decorators**

- `dataclass(frozen=True)`

```python
class Polygon
```

**Summary:** Docstring absent.

**Methods visible in the code**

- `__post_init__` - line 55

#### Method details

##### `Polygon.__post_init__`

**Source lines:** `55-104`

```python
def __post_init__self
```

**Summary:** Validation steps executed automatically after object initialization.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`len`, `range`, `ValueError`, `abs`, `object.__setattr__`

### `Section`

**Source lines:** `109-156`

**Decorators**

- `dataclass(frozen=True)`

```python
class Section
```

**Summary:** Docstring absent.

**Methods visible in the code**

- `__post_init__` - line 113

#### Method details

##### `Section.__post_init__`

**Source lines:** `113-156`

```python
def __post_init__self
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `TypeError`
- `ValueError`

**Function/method calls visible in the code**

`isinstance`, `set`, `enumerate`, `TypeError`, `len`, `ValueError`, `seen_names.add`, `poly.name.strip`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
