# API Reference - `Continuous_section_field.py`

This document covers the APIs defined in this file only; imported symbols from other modules are not documented here as standalone APIs.

## Module

### Local dependencies used by the file

```python
from .entities import Pt, Polygon, Section, CSFError
from csf.section_field import section_properties
from .section_field import (
    CSFDumper, XY,
    _csf__is_finite_number, _csf__atomic_write_text,
    _csf__ensure_parent_dir_exists,
    _bbox_xy, _point_in_poly_inclusive, _point_on_segment_sq,
    polygon_has_self_intersections, polygon_inertia_about_origin,
    section_print_analysis, _signed_area_centroid_xy,
    _simple_yaml_dump, _csf__section_to_Sz_dict,
)
from .section_field import (
    compute_lobatto_integration_points,
    section_full_analysis,
    evaluate_weight_formula,
    evaluate_weight_formula_zrelative,
    evaluate_shear_weight_formula,
)
```

## Class `ContinuousSectionField`

```python
class ContinuousSectionField:
```

Represents a continuous sectional field between two endpoint `Section` objects, `section0` and `section1`.

### Internal state initialized by the constructor

| Attribute | Source in code |
|---|---|
| `self.s0` | start section |
| `self.s1` | end section |
| `self.z0` | `section0.z` |
| `self.z1` | `section1.z` |
| `self.weight_laws` | initialized as `None` |
| `self.shear_weight_laws_default` | initialized as `None` |
| `self.shear_weight_laws` | initialized as `None` |

### Constructor validations

- `section0.polygons` and `section1.polygons` must have the same length.
- `section0.z` and `section1.z` must be different.
- Each homologous polygon pair must have the same number of vertices.

---

## Constructor

### `__init__`

```python
def __init__(self, section0: Section, section1: Section)
```

Initializes the continuous section field from two reference sections.

| Parameter | Type | Description |
|---|---|---|
| `section0` | `Section` | Start section. |
| `section1` | `Section` | End section. |

**Raises**

| Error | Condition |
|---|---|
| `ValueError` | Different number of polygons in `section0` and `section1`. |
| `ValueError` | Equal `z` coordinates in the two sections. |
| `ValueError` | Different number of vertices in homologous polygons. |

---

## Public class API

### `section`

```python
def section(self, z: float) -> Section
```

Evaluates the continuous section field at the absolute coordinate `z` and returns a new `Section`.

| Parameter | Type | Description |
|---|---|---|
| `z` | `float` | Absolute longitudinal coordinate to evaluate. |

**Returns**

| Type | Description |
|---|---|
| `Section` | Interpolated section at `z`, containing a tuple of `Polygon` objects. |

**Behavior visible in the code**

- Checks that `z` lies within `[self.z0, self.z1]`.
- Interpolates homologous polygon vertices through `v0.lerp(v1, origz, lenght)`.
- Applies `weight_laws` when present.
- Applies `shear_weight_laws` when present.
- Computes `weight`, `weightabs`, `shear_weight`, and `shear_weightabs` for generated polygons.
- Resolves topology tags in polygon names: `@cell`, `@wall`, `@closed`.
- Resolves `@t=...` when present.
- Raises an error when `@cell` is used without `@t`.
- Returns `Section(polygons=tuple(polys), z=float(z))`.

**Raises**

| Error | Condition |
|---|---|
| `CSFError` | `z` is outside `[self.z0, self.z1]`. |
| `CSFError` | Invalid or incompatible topology tags in polygon names. |
| `CSFError` | `@cell` without thickness tag `@t`. |
| `ValueError` | Invalid weight or shear-weight formula during interpolation. |

---

### `inspect_section_entities`

```python
def inspect_section_entities(self, z: float) -> List[Dict[str, Any]]
```

Inspects all polygon entities in the section evaluated at `z`.

| Parameter | Type | Description |
|---|---|---|
| `z` | `float` | Longitudinal coordinate to inspect. |

**Returns**

`List[Dict[str, Any]]`, with one record per polygon.

Fields returned by the code:

| Field | Type |
|---|---|
| `idx` | `int` |
| `name` | `str | None` |
| `s0_name` | `str | None` |
| `s1_name` | `str | None` |
| `s0_weight` | `float` |
| `s1_weight` | `float` |
| `weight_at_z` | `float` |
| `weight_abs_z` | `float` |
| `shear_weight_at_z` | `float` |
| `shear_weight_abs_at_z` | `float` |
| `poisson` | `float` |
| `weight_law` | `str | None` |
| `area_signed` | `float` |
| `is_container` | `bool` |
| `direct_children` | `List[str | None]` |
| `container_idx` | `int | None` |
| `container_name` | `str | None` |

**Rules documented in the code**

- Topology is index-based.
- Names are labels only.
- No structural branch depends on polygon names or tags.

---

### `build_direct_children_map`

```python
def build_direct_children_map(self, z: float) -> Dict[int, List[int]]
```

Builds the direct parent-to-children polygon map.

| Parameter | Type | Description |
|---|---|---|
| `z` | `float` | Longitudinal coordinate used to validate section evaluation. |

**Returns**

```python
Dict[parent_idx, List[child_idx]]
```

**Rules documented in the code**

- Polygon identity is the polygon index in `self.s0.polygons`.
- Names are not used.
- Only direct children are returned.
- Polygons without children do not appear as keys.

**Raises**

| Error | Condition |
|---|---|
| `TypeError` | `z` is not numeric. |
| `ValueError` | `self.section(z)` returns `None`. |
| `ValueError` | `self.s0` has no `polygons` attribute. |
| `ValueError` | Invalid container index. |
| `ValueError` | A polygon is its own container. |
| `ValueError` | A polygon has multiple direct containers. |

---

### `get_container_polygon_index`

```python
def get_container_polygon_index(self, poly: "Polygon", i: int)
```

Returns the 0-based index of the immediate container of `poly` in `self.s0.polygons`.

| Parameter | Type | Description |
|---|---|---|
| `poly` | `Polygon` | Polygon to classify. |
| `i` | `int` | Polygon index. |

**Returns**

| Type | Description |
|---|---|
| `int | None` | Immediate container index, or `None`. |

**Code note**

The result is cached by polygon index.

---

### `write_section`

```python
def write_section(self, z0: float, z1: float, yaml_path: str) -> None
```

Writes a CSF YAML section generated from two evaluated coordinates.

| Parameter | Type | Description |
|---|---|---|
| `z0` | `float` | First coordinate to evaluate. |
| `z1` | `float` | Second coordinate to evaluate. |
| `yaml_path` | `str` | Output YAML path. |

**Behavior visible in the code**

- Checks that `z0` and `z1` lie within `[min(self.s0.z, self.s1.z), max(self.s0.z, self.s1.z)]`.
- Checks that `z0` and `z1` are finite numbers.
- Evaluates `self.section(z0)` and `self.section(z1)`.
- Converts the evaluated sections into `S0` and `S1` dictionaries.
- Writes the structure:

```yaml
CSF:
  sections:
    S0: ...
    S1: ...
```

- Does not serialize active laws as re-applicable laws.
- Appends any `weight_laws` and `shear_weight_laws` only as `APPLIED_LAWS_TRACE` comments.
- Uses atomic writing through `_csf__atomic_write_text`.

**Raises**

| Error | Condition |
|---|---|
| `CSFError` | `z0` or `z1` outside the field domain. |
| `CSFError` | `z0` or `z1` is not finite. |
| `CSFError` | Failed `Section -> dict` conversion. |
| `CSFError` | YAML backend unavailable. |
| `CSFError` | YAML serialization failure. |
| `CSFError` | File writing failure. |

---

### `section_area_list_report`

```python
def section_area_list_report(
    self,
    z: float,
    w_tol: float = 0.0,
    zero_w_eps: float = 0.0,
    group_mode: str = "weight",
) -> None
```

Prints an accountant-style area listing for the section at `z`, grouped by absolute weight `w_abs`.

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `z` | `float` | - | Longitudinal coordinate. |
| `w_tol` | `float` | `0.0` | Weight grouping tolerance. |
| `zero_w_eps` | `float` | `0.0` | Passed to `section_area_by_weight`. |
| `group_mode` | `str` | `"weight"` | Grouping mode. Only `"weight"` is supported by the code. |

**Output**

Prints to stdout:

- polygon listing;
- `A_net`;
- `A*w`;
- `Occupied Total Surface`;
- `Homogenized area`.

**Raises**

| Error | Condition |
|---|---|
| `ValueError` | `group_mode` is not `"weight"`. |
| `ValueError` | Polygon index out of range in the report. |

---

### `section_area_by_weight`

```python
def section_area_by_weight(
    self,
    z: float,
    w_tol: float = 0.0,
    include_per_polygon: bool = False,
    debug: bool = False,
    zero_w_eps: float = 0.0,
) -> Dict[str, Any]
```

Computes the area breakdown at `z`, grouped by absolute weight `w_abs`.

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `z` | `float` | - | Longitudinal coordinate. |
| `w_tol` | `float` | `0.0` | Weight grouping tolerance. |
| `include_per_polygon` | `bool` | `False` | Includes detailed per-polygon records. |
| `debug` | `bool` | `False` | Prints diagnostic information. |
| `zero_w_eps` | `float` | `0.0` | Threshold used to exclude near-zero contributions from `total_area_nonzero`. |

**Returns**

```python
{
    "z": float,
    "total_area": float,
    "total_area_nonzero": float,
    "total_area_geometric": float,
    "groups": list,
    "per_polygon": list,  # only if include_per_polygon=True
}
```

**Rules documented in the code**

- Polygon identity is the polygon index.
- Names are not used for topology, matching, or grouping.
- Direct-children topology comes from `build_direct_children_map(z)`.
- The net geometric area of a polygon is:

```python
area_geom_net[i] = area_geom[i] - sum(area_geom[j] for j in direct_children[i])
```

- The effective area is:

```python
total_area = sum(area_geom_net[i] * w_abs[i])
```

---

### `to_dict`

```python
def to_dict(self, include_weight_laws=True)
```

Converts the CSF object into a Python dictionary.

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `include_weight_laws` | not annotated | `True` | If true, includes `weight_laws` and `shear_weight_laws` when present. |

**Returns**

Main dictionary structure:

```python
{
    "CSF": {
        "sections": {
            "S0": ...,
            "S1": ...,
        },
        "weight_laws": ...,        # if present and requested
        "shear_weight_laws": ...,  # if present and requested
    }
}
```

---

### `to_yaml`

```python
def to_yaml(
    self,
    filepath: Optional[str] = None,
    include_weight_laws: bool = True,
) -> str
```

Serializes the CSF object to YAML.

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `filepath` | `Optional[str]` | `None` | If provided, writes the YAML text to this file. |
| `include_weight_laws` | `bool` | `True` | Passed to `to_dict`. |

**Returns**

| Type | Description |
|---|---|
| `str` | Generated YAML text. |

**Behavior visible in the code**

- Uses `yaml.dump(..., Dumper=CSFDumper, sort_keys=False, allow_unicode=True, indent=2, default_flow_style=False)` if `yaml` is available.
- Otherwise uses `_simple_yaml_dump(data) + "\n"`.
- Writes to `filepath` only when `filepath` is provided.

---

### `get_lobatto_integration_points`

```python
def get_lobatto_integration_points(
    self,
    n_points: int = 5,
    L: float | None = None,
) -> List[float]
```

Returns Lobatto integration points by delegating to `compute_lobatto_integration_points`.

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `n_points` | `int` | `5` | Number of requested points. |
| `L` | `float | None` | `None` | Parameter passed to the external function. |

**Returns**

| Type | Description |
|---|---|
| `List[float]` | Points computed between `self.s0.z` and `self.s1.z`. |

---

### `set_shear_weight_laws`

```python
def set_shear_weight_laws(
    self,
    laws: Union[List[str], Dict[Union[int, str], str]],
) -> None
```

Sets shear-weight variation laws.

| Parameter | Type | Description |
|---|---|---|
| `laws` | `Union[List[str], Dict[Union[int, str], str]]` | List or dictionary of laws. |

**Rules documented in the code**

- A list item without `:` is interpreted as the global default shear-weight law.
- A list item with `:` is interpreted as a polygon-specific shear-weight law.
- Polygon indices are 0-based.
- Polygon-name mapping follows the same S0/S1 homology logic used by `set_weight_laws`.

**Accepted formats in the code**

List:

```python
[
    "default_formula",
    "polygon_name: formula",
    "s0_polygon_name,s1_polygon_name: formula",
]
```

Dictionary:

```python
{
    0: "formula",
    "polygon_name": "formula",
}
```

**Raises**

| Error | Condition |
|---|---|
| `ValueError` | `laws` is neither a list nor a dictionary. |
| `ValueError` | Invalid item or formula. |
| `ValueError` | Multiple default laws declared. |
| `KeyError` | Polygon name not found. |
| `IndexError` | Index out of range. |
| `ValueError` | S0/S1 homology mismatch. |

---

### `set_weight_laws`

```python
def set_weight_laws(
    self,
    laws: Union[List[str], Dict[Union[int, str], str]],
) -> None
```

Sets `weight` variation laws.

| Parameter | Type | Description |
|---|---|---|
| `laws` | `Union[List[str], Dict[Union[int, str], str]]` | The current body handles list input; dictionary input is explicitly rejected. |

**Rules documented in the code**

- If a polygon name is not found, an error is raised.
- If S0/S1 homology fails, an error is raised.
- Laws are stored internally with 1-based indices.
- Tags `@cell`, `@wall`, and `@closed` are stripped from names during resolution.

**Handled list format**

```python
[
    "s0_polygon_name,s1_polygon_name: formula",
    "polygon_name: formula",
]
```

**Important code note**

The signature declares `Dict[Union[int, str], str]`, but the branch:

```python
elif isinstance(laws, dict):
    raise ValueError(f"Critical Error: not valid {laws} ")
```

explicitly rejects dictionaries.

**Raises**

| Error | Condition |
|---|---|
| `ValueError` | `laws` is neither a list nor a dictionary. |
| `KeyError` | Polygon name not found. |
| `ValueError` | S0/S1 homology mismatch. |
| `ValueError` | Invalid formula during midpoint validation. |
| `ValueError` | Dictionary input. |

---

## Public module helpers

### `polygon_area_centroid`

```python
def polygon_area_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]
```

Computes polygon area and centroid through `_polygon_signed_area_and_centroid`.

| Parameter | Type | Description |
|---|---|---|
| `poly` | `Polygon` | Polygon to evaluate. |

**Returns**

```python
(poly.weight * A_signed, (Cx, Cy))
```

---

### `section_data`

```python
def section_data(field: ContinuousSectionField, z: float) -> dict
```

Returns a snapshot of the section at absolute coordinate `z`.

| Parameter | Type | Description |
|---|---|---|
| `field` | `ContinuousSectionField` | Section field to query. |
| `z` | `float` | Absolute coordinate. |

**Returns**

```python
{
    "section": section,
    "properties": props,
}
```

where:

- `section = field.section(z)`
- `props = section_properties(section)`

---

## Internal helpers present in the file

These symbols are present in the file but have a leading underscore; therefore they are treated as internal.

### `_get_container_polygon_index_uncached`

```python
def _get_container_polygon_index_uncached(self, poly: "Polygon", i: int)
```

Computes the immediate container without using the cache.

**Returns**

`int | None`.

---

### `_section_to_dict`

```python
@staticmethod
def _section_to_dict(sec)
```

Converts a `Section` into a dictionary:

```python
{
    "z": float(sec.z),
    "polygons": {
        polygon_name: ...
    }
}
```

Raises `ValueError` if duplicate polygon names are found in the section.

---

### `_polygon_to_dict`

```python
@staticmethod
def _polygon_to_dict(poly)
```

Converts a `Polygon` into a dictionary:

```python
{
    "weight": float(poly.weight),
    "vertices": ...
}
```

---

### `_determine_magnitude`

```python
def _determine_magnitude(self) -> None
```

Computes a geometric scale from the bounding boxes of `self.s0` and `self.s1`, then updates tolerances in `_tol`.

---

### `_strip_model_tags`

```python
def _strip_model_tags(self, name: str) -> str
```

Normalizes a polygon name by removing everything from `@cell`, `@wall`, or `@closed` onward.

**Code note**

The file contains two definitions with the same name. In Python, the last definition in the class is the active one.

---

### `_validate_inputs`

```python
def _validate_inputs(self) -> None
```

Checks:

- same number of polygons in `self.s0` and `self.s1`;
- same number of vertices for each homologous polygon pair.

---

### `_interpolate_weight`

```python
def _interpolate_weight(
    self,
    w0: float,
    w1: float,
    z: float,
    p0: Polygon,
    p1: Polygon,
    law: Optional[str],
) -> float
```

Interpolates weight.

**Behavior visible in the code**

- If `law` is a non-empty string, uses `evaluate_weight_formula`.
- Otherwise uses linear interpolation:

```python
w0 + (w1 - w0) / L_val * z
```

---

### `_interpolate_shear_weight`

```python
def _interpolate_shear_weight(
    self,
    w: float,
    w0: float,
    w1: float,
    z: float,
    p0: Polygon,
    p1: Polygon,
    law: Optional[str],
) -> float
```

Interpolates shear-weight.

**Behavior visible in the code**

- If `law` is a non-empty string, uses `evaluate_shear_weight_formula`.
- Otherwise returns `w`.

---

### `_to_t`

```python
def _to_t(self, z: float) -> float
```

Converts `z` into a normalized coordinate over `[self.z0, self.z1]`.

Raises `ValueError` if `z` is outside the domain.

---

### `_polygon_signed_area_and_centroid`

```python
def _polygon_signed_area_and_centroid(
    poly: Polygon,
) -> Tuple[float, Tuple[float, float]]
```

Computes signed area and centroid through the shoelace formula, without applying weight.

---

### `_set_axes_equal_3d`

```python
def _set_axes_equal_3d(ax) -> None
```

Matplotlib helper for adjusting 3D axes while preserving a consistent scale in the `X-Y` plane.

---

## Elements not documented as standalone API

The final block under:

```python
if __name__ == "__main__":
```

is demonstration/execution code and is not documented as API.
