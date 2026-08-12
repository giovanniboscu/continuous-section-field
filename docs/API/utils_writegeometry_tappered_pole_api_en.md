# API Reference - `writegeometry_tappered_pole.py`

This document covers the top-level classes and functions defined in `src/csf/utils/writegeometry_tappered_pole.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/utils/writegeometry_tappered_pole.py`
- Output file: `docs/API/utils_writegeometry_tappered_pole_api_en.md`
- Top-level function definitions found: `29`.
- Top-level classes found: `3`.
- Duplicate function names found: `0`.

## Module docstring

```text
Generate a CSF YAML geometry for a tapered circular hollow pole
with radial onion levels split into angular sector cells.

Naming convention used by this generator:
- concrete polygon id: <sector>_<level>_<type>
- steel polygon id:    <bar>_<host_level>_S

where:
- sector/bar numbering starts from 0;
- level is one-based and follows the radial order of the input radii;
- type is C for concrete, CH for the concrete host level of the bars, S for steel.

The polygon order is identical at S0 and S1. CSF pairs corresponding polygons by
order, while names are used for law assignment.
```

## Public API index

- `CleanDumper` - line 28
- `Point` - line 33
- `SectionParameters` - line 45
- `def _repr_pointdumper, data` - line 37
- `def parse_csv_floatsvalue: str` - line 51
- `def parse_csv_namesvalue: str` - line 61
- `def parse_index_lawvalue: str` - line 68
- `def parse_sector_lawvalue: str` - line 82
- `def parse_bar_lawvalue: str` - line 100
- `def validate_radiiradii: list[float], label: str` - line 114
- `def close_looppoints: list[list[float]]` - line 122
- `def to_pointsvertices: Iterable[Iterable[float]]` - line 130
- `def arc_pointscx: float, cy: float, radius: float, theta_a: float, theta_b: float, n_steps: int` - line 134
- `def annular_sector_verticescx: float, cy: float, inner_radius: float, outer_radius: float, theta_a: float, theta_b: float, arc_steps: int` - line 156
- `def circle_loopcx: float, cy: float, radius: float, n: int, theta0_deg: float=0.0` - line 178
- `def disk_verticescx: float, cy: float, radius: float, n: int, theta0_deg: float` - line 193
- `def concrete_sector_namesector_index: int, layer_index: int, bar_host_layer_index: int` - line 197
- `def bar_namebar_index: int, bar_host_layer_index: int` - line 203
- `def bar_verticescx: float, cy: float, guide_radius: float, bar_radius: float, bar_sides: int, bar_index: int, n_bars: int, theta0_deg: float, center_offset_deg: float, bar_theta0_deg: float` - line 208
- `def validate_bar_fitradii: list[float], bar_guide_radius: float, bar_radius: float, host_layer_index: int, label: str` - line 228
- `def validate_sector_indexlayer_idx: int, sector_idx: int, n_layers: int, n_sectors: int, label: str` - line 248
- `def validate_bar_indexbar_idx: int, n_bars: int, label: str` - line 255
- `def generated_concrete_namesargs` - line 260
- `def generated_bar_namesargs` - line 268
- `def build_section_polygonsargs, params: SectionParameters` - line 274
- `def add_law_entrylaws: dict[str, str], name: str, law: str` - line 330
- `def law_strings_from_maplaws: dict[str, str]` - line 335
- `def build_lawsargs` - line 339
- `def build_geometryargs` - line 395
- `def commented_law_blocksweight_laws: list[str], shear_weight_laws: list[str]` - line 437
- `def make_parser` - line 451
- `def main` - line 507

## API details

## Classes

### `CleanDumper`

**Source lines:** `28-30`

```python
class CleanDumper(yaml.SafeDumper)
```

**Summary:** Docstring absent.

**Methods visible in the code**

- `ignore_aliases` - line 29

#### Method details

##### `CleanDumper.ignore_aliases`

**Source lines:** `29-30`

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

**Source lines:** `33-34`

```python
class Point(list)
```

**Summary:** Docstring absent.

### `SectionParameters`

**Source lines:** `45-48`

**Decorators**

- `dataclass(frozen=True)`

```python
class SectionParameters
```

**Summary:** Docstring absent.

## Functions

## Top-level functions

### `_repr_point`

**Source lines:** `37-38`

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

### `parse_csv_floats`

**Source lines:** `51-58`

```python
def parse_csv_floatsvalue: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `str` | `-` |

**Returns:** `list[float]`

**Raises visible in the code**

- `argparse.ArgumentTypeError`

**Function/method calls visible in the code**

`part.strip`, `argparse.ArgumentTypeError`, `value.split`, `float`

### `parse_csv_names`

**Source lines:** `61-65`

```python
def parse_csv_namesvalue: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `str` | `-` |

**Returns:** `list[str]`

**Raises visible in the code**

- `argparse.ArgumentTypeError`

**Function/method calls visible in the code**

`part.strip`, `argparse.ArgumentTypeError`, `value.split`

### `parse_index_law`

**Source lines:** `68-79`

```python
def parse_index_lawvalue: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `str` | `-` |

**Returns:** `tuple[int, str]`

**Raises visible in the code**

- `argparse.ArgumentTypeError`

**Function/method calls visible in the code**

`value.split`, `law.strip`, `argparse.ArgumentTypeError`, `int`, `idx_text.strip`

### `parse_sector_law`

**Source lines:** `82-97`

```python
def parse_sector_lawvalue: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `str` | `-` |

**Returns:** `tuple[int, int, str]`

**Raises visible in the code**

- `argparse.ArgumentTypeError`

**Function/method calls visible in the code**

`value.split`, `law.strip`, `len`, `argparse.ArgumentTypeError`, `int`, `layer_text.strip`, `sector_text.strip`

### `parse_bar_law`

**Source lines:** `100-111`

```python
def parse_bar_lawvalue: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `str` | `-` |

**Returns:** `tuple[int, str]`

**Raises visible in the code**

- `argparse.ArgumentTypeError`

**Function/method calls visible in the code**

`value.split`, `law.strip`, `argparse.ArgumentTypeError`, `int`, `idx_text.strip`

### `validate_radii`

**Source lines:** `114-119`

```python
def validate_radiiradii: list[float], label: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `radii` | `positional or keyword` | `list[float]` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`zip`, `len`, `ValueError`

### `close_loop`

**Source lines:** `122-127`

```python
def close_looppoints: list[list[float]]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `positional or keyword` | `list[list[float]]` | `-` |

**Returns:** `list[list[float]]`

### `to_points`

**Source lines:** `130-131`

```python
def to_pointsvertices: Iterable[Iterable[float]]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `vertices` | `positional or keyword` | `Iterable[Iterable[float]]` | `-` |

**Returns:** `list[Point]`

**Function/method calls visible in the code**

`Point`, `float`

### `arc_points`

**Source lines:** `134-153`

```python
def arc_pointscx: float, cy: float, radius: float, theta_a: float, theta_b: float, n_steps: int
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cx` | `positional or keyword` | `float` | `-` |
| `cy` | `positional or keyword` | `float` | `-` |
| `radius` | `positional or keyword` | `float` | `-` |
| `theta_a` | `positional or keyword` | `float` | `-` |
| `theta_b` | `positional or keyword` | `float` | `-` |
| `n_steps` | `positional or keyword` | `int` | `-` |

**Returns:** `list[list[float]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`, `range`, `math.cos`, `math.sin`

### `annular_sector_vertices`

**Source lines:** `156-175`

```python
def annular_sector_verticescx: float, cy: float, inner_radius: float, outer_radius: float, theta_a: float, theta_b: float, arc_steps: int
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cx` | `positional or keyword` | `float` | `-` |
| `cy` | `positional or keyword` | `float` | `-` |
| `inner_radius` | `positional or keyword` | `float` | `-` |
| `outer_radius` | `positional or keyword` | `float` | `-` |
| `theta_a` | `positional or keyword` | `float` | `-` |
| `theta_b` | `positional or keyword` | `float` | `-` |
| `arc_steps` | `positional or keyword` | `int` | `-` |

**Returns:** `list[Point]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`arc_points`, `to_points`, `ValueError`, `list`, `close_loop`, `reversed`

### `circle_loop`

**Source lines:** `178-190`

```python
def circle_loopcx: float, cy: float, radius: float, n: int, theta0_deg: float=0.0
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cx` | `positional or keyword` | `float` | `-` |
| `cy` | `positional or keyword` | `float` | `-` |
| `radius` | `positional or keyword` | `float` | `-` |
| `n` | `positional or keyword` | `int` | `-` |
| `theta0_deg` | `positional or keyword` | `float` | `0.0` |

**Returns:** `list[list[float]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`math.radians`, `ValueError`, `range`, `math.cos`, `math.sin`

### `disk_vertices`

**Source lines:** `193-194`

```python
def disk_verticescx: float, cy: float, radius: float, n: int, theta0_deg: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cx` | `positional or keyword` | `float` | `-` |
| `cy` | `positional or keyword` | `float` | `-` |
| `radius` | `positional or keyword` | `float` | `-` |
| `n` | `positional or keyword` | `int` | `-` |
| `theta0_deg` | `positional or keyword` | `float` | `-` |

**Returns:** `list[Point]`

**Function/method calls visible in the code**

`to_points`, `close_loop`, `circle_loop`

### `concrete_sector_name`

**Source lines:** `197-200`

```python
def concrete_sector_namesector_index: int, layer_index: int, bar_host_layer_index: int
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `sector_index` | `positional or keyword` | `int` | `-` |
| `layer_index` | `positional or keyword` | `int` | `-` |
| `bar_host_layer_index` | `positional or keyword` | `int` | `-` |

**Returns:** `str`

### `bar_name`

**Source lines:** `203-205`

```python
def bar_namebar_index: int, bar_host_layer_index: int
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `bar_index` | `positional or keyword` | `int` | `-` |
| `bar_host_layer_index` | `positional or keyword` | `int` | `-` |

**Returns:** `str`

### `bar_vertices`

**Source lines:** `208-225`

```python
def bar_verticescx: float, cy: float, guide_radius: float, bar_radius: float, bar_sides: int, bar_index: int, n_bars: int, theta0_deg: float, center_offset_deg: float, bar_theta0_deg: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cx` | `positional or keyword` | `float` | `-` |
| `cy` | `positional or keyword` | `float` | `-` |
| `guide_radius` | `positional or keyword` | `float` | `-` |
| `bar_radius` | `positional or keyword` | `float` | `-` |
| `bar_sides` | `positional or keyword` | `int` | `-` |
| `bar_index` | `positional or keyword` | `int` | `-` |
| `n_bars` | `positional or keyword` | `int` | `-` |
| `theta0_deg` | `positional or keyword` | `float` | `-` |
| `center_offset_deg` | `positional or keyword` | `float` | `-` |
| `bar_theta0_deg` | `positional or keyword` | `float` | `-` |

**Returns:** `list[Point]`

**Function/method calls visible in the code**

`math.radians`, `disk_vertices`, `math.cos`, `math.sin`

### `validate_bar_fit`

**Source lines:** `228-245`

```python
def validate_bar_fitradii: list[float], bar_guide_radius: float, bar_radius: float, host_layer_index: int, label: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `radii` | `positional or keyword` | `list[float]` | `-` |
| `bar_guide_radius` | `positional or keyword` | `float` | `-` |
| `bar_radius` | `positional or keyword` | `float` | `-` |
| `host_layer_index` | `positional or keyword` | `int` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`, `len`

### `validate_sector_index`

**Source lines:** `248-252`

```python
def validate_sector_indexlayer_idx: int, sector_idx: int, n_layers: int, n_sectors: int, label: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `layer_idx` | `positional or keyword` | `int` | `-` |
| `sector_idx` | `positional or keyword` | `int` | `-` |
| `n_layers` | `positional or keyword` | `int` | `-` |
| `n_sectors` | `positional or keyword` | `int` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`

### `validate_bar_index`

**Source lines:** `255-257`

```python
def validate_bar_indexbar_idx: int, n_bars: int, label: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `bar_idx` | `positional or keyword` | `int` | `-` |
| `n_bars` | `positional or keyword` | `int` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`

### `generated_concrete_names`

**Source lines:** `260-265`

```python
def generated_concrete_namesargs
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `args` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `list[str]`

**Function/method calls visible in the code**

`range`, `len`, `names.append`, `concrete_sector_name`

### `generated_bar_names`

**Source lines:** `268-271`

```python
def generated_bar_namesargs
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `args` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `list[str]`

**Function/method calls visible in the code**

`bar_name`, `range`

### `build_section_polygons`

**Source lines:** `274-327`

```python
def build_section_polygonsargs, params: SectionParameters
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `args` | `positional or keyword` | `not annotated` | `-` |
| `params` | `positional or keyword` | `SectionParameters` | `-` |

**Returns:** `dict`

**Returned dictionary keys visible in the code**

`weight`, `vertices`

**Function/method calls visible in the code**

`math.radians`, `range`, `len`, `float`, `concrete_sector_name`, `bar_name`, `annular_sector_vertices`, `bar_vertices`

### `add_law_entry`

**Source lines:** `330-332`

```python
def add_law_entrylaws: dict[str, str], name: str, law: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `laws` | `positional or keyword` | `dict[str, str]` | `-` |
| `name` | `positional or keyword` | `str` | `-` |
| `law` | `positional or keyword` | `str` | `-` |

**Returns:** `None`

### `law_strings_from_map`

**Source lines:** `335-336`

```python
def law_strings_from_maplaws: dict[str, str]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `laws` | `positional or keyword` | `dict[str, str]` | `-` |

**Returns:** `list[str]`

**Function/method calls visible in the code**

`laws.items`

### `build_laws`

**Source lines:** `339-392`

```python
def build_lawsargs
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `args` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `tuple[list[str], list[str]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`len`, `range`, `validate_sector_index`, `concrete_sector_name`, `add_law_entry`, `generated_bar_names`, `validate_bar_index`, `law_strings_from_map`, `ValueError`, `bar_name`

### `build_geometry`

**Source lines:** `395-434`

```python
def build_geometryargs
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `args` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `dict`

**Returned dictionary keys visible in the code**

`CSF`, `sections`, `S0`, `S1`, `z`, `polygons`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`validate_radii`, `SectionParameters`, `len`, `ValueError`, `validate_bar_fit`, `float`, `build_section_polygons`

### `commented_law_blocks`

**Source lines:** `437-448`

```python
def commented_law_blocksweight_laws: list[str], shear_weight_laws: list[str]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `weight_laws` | `positional or keyword` | `list[str]` | `-` |
| `shear_weight_laws` | `positional or keyword` | `list[str]` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`join`, `lines.append`

### `make_parser`

**Source lines:** `451-504`

```python
def make_parser
```

**Summary:** Docstring absent.

**Returns:** `argparse.ArgumentParser`

**Function/method calls visible in the code**

`argparse.ArgumentParser`, `parser.add_argument`, `Path`

### `main`

**Source lines:** `507-539`

```python
def main
```

**Summary:** Docstring absent.

**Returns:** `None`

**Function/method calls visible in the code**

`make_parser`, `parser.parse_args`, `build_geometry`, `build_laws`, `commented_law_blocks`, `print`, `args.out.open`, `yaml.dump`, `len`, `f.write`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
