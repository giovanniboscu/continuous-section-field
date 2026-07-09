# API Reference - `continuous_section_field.py`

This document covers the top-level classes and functions defined in `src/csf/continuous_section_field.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/continuous_section_field.py`
- Output file: `src/doc/continuous_section_field_api_en.md`
- Top-level function definitions found: `4`.
- Top-level classes found: `1`.
- Duplicate function names found: `0`.

## Public API index

- `ContinuousSectionField` - line 30
- `def _polygon_signed_area_and_centroidpoly: Polygon` - line 2222
- `def polygon_area_centroidpoly: Polygon` - line 2232
- `def section_datafield: ContinuousSectionField, z: float` - line 2239
- `def _set_axes_equal_3dax` - line 2301

## API details

## Classes

### `ContinuousSectionField`

**Source lines:** `30-2216`

```python
class ContinuousSectionField
```

**Summary:** Docstring absent.

**Methods visible in the code**

- `inspect_section_entities` - line 38
- `build_direct_children_map` - line 192
- `get_container_polygon_index` - line 266
- `_get_container_polygon_index_uncached` - line 283
- `write_section` - line 572
- `_section_to_dict` - line 724
- `_polygon_to_dict` - line 739
- `section_area_list_report` - line 751
- `section_area_by_weight` - line 888
- `_determine_magnitude` - line 1118
- `to_dict` - line 1206
- `to_yaml` - line 1248
- `get_lobatto_integration_points` - line 1274
- `__init__` - line 1288
- `L` - line 1313
- `_strip_model_tags` - line 1317
- `_strip_model_tags` - line 1330
- `set_shear_weight_laws` - line 1340
- `set_weight_laws` - line 1548
- `_validate_inputs` - line 1674
- `_interpolate_weight` - line 1685
- `_interpolate_shear_weight` - line 1718
- `_to_t` - line 1745
- `section` - line 1753

#### Method details

##### `ContinuousSectionField.inspect_section_entities`

**Source lines:** `38-190`

```python
def inspect_section_entitiesself, z: float
```

**Summary:** Perform a sterile inspection of all polygon entities at longitudinal coordinate z.

**Docstring details**

```text
Structural rules:
- topology is strictly index-based
- names are labels only
- no structural branch depends on polygon names or tags

Returned fields:
- idx (int)
- name (str | None)
- s0_name (str | None)
- s1_name (str | None)
- s0_weight (float)
- s1_weight (float)
- weight_at_z (float)
- weight_abs_z (float)
- weight_law (str | None)
- area_signed (float)
- is_container (bool)
- direct_children (List[str | None])
- container_idx (int | None)
- container_name (str | None)

Raises:
- TypeError / ValueError only for structural issues
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `List[Dict[str, Any]]`

**Returned dictionary keys visible in the code**

`idx`, `name`, `s0_name`, `s1_name`, `s0_weight`, `s1_weight`, `weight_at_z`, `weight_abs_z`, `shear_weight_at_z`, `shear_weight_abs_at_z`, `poisson`, `weight_law`, `area_signed`, `is_container`, `direct_children`, `container_idx`, `container_name`

**Raises visible in the code**

- `TypeError`
- `ValueError`

**Function/method calls visible in the code**

`self.section`, `self.build_direct_children_map`, `children_map.items`, `enumerate`, `isinstance`, `TypeError`, `float`, `ValueError`, `hasattr`, `_polygon_signed_area_and_centroid`, `records.append`, `list`, `str`, `direct_children_labels.append`, `len`, `type`

##### `ContinuousSectionField.build_direct_children_map`

**Source lines:** `192-263`

```python
def build_direct_children_mapself, z: float
```

**Summary:** Build the direct parent-to-children mapping for polygons at coordinate z.

**Docstring details**

```text
Structural rules:
- polygon identity is strictly the polygon index in self.s0.polygons
- names are never used
- topology is expressed strictly as indices

Output:
- Dict[parent_idx, List[child_idx]]

Notes:
- The section at z is evaluated only to validate that z is admissible.
- The containment topology is taken from the stable S0 polygon ordering.
- Only direct children are returned.
- Polygons with no children do not appear as keys.

Raises:
- TypeError if z is not numeric or if self.s0.polygons is not a valid sequence
- ValueError for invalid topology or invalid container indices
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `Dict[int, List[int]]`

**Raises visible in the code**

- `TypeError`
- `ValueError`

**Function/method calls visible in the code**

`self.section`, `enumerate`, `isinstance`, `TypeError`, `float`, `ValueError`, `hasattr`, `self.get_container_polygon_index`, `append`, `len`, `type`

##### `ContinuousSectionField.get_container_polygon_index`

**Source lines:** `266-281`

```python
def get_container_polygon_indexself, poly: 'Polygon', i: int
```

**Summary:** Return the index (0-based) of the immediate container of `poly` in self.s0.polygons.

**Docstring details**

```text
Cached by polygon index because topology is assumed fixed.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `poly` | `positional or keyword` | `'Polygon'` | `-` |
| `i` | `positional or keyword` | `int` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`self._get_container_polygon_index_uncached`, `hasattr`

##### `ContinuousSectionField._get_container_polygon_index_uncached`

**Source lines:** `283-569`

```python
def _get_container_polygon_index_uncachedself, poly: 'Polygon', i: int
```

**Summary:** Return the index (0-based) of the *immediate container* of `poly` in self.s0.polygons.

**Docstring details**

```text
Returns the index of the immediate container polygon (smallest-area polygon that contains `poly`),
not the outermost/global container.
Logic (as requested):
1) Take polygon p (= poly).
2) Collect all other polygons that contain p.
3) Pick pp such that pp contains p and there is no other polygon between them
    (i.e., no q with p ⊂ q ⊂ pp). Polygons may touch (boundary counts as inside).

Debug:
- Enable with: self.debug_container = True
- No global variables are used to activate debug output.

Returns
-------
int | None
    Index of the immediate container polygon, or None if no container exists.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `poly` | `positional or keyword` | `'Polygon'` | `-` |
| `i` | `positional or keyword` | `int` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`bool`, `_get_coincident_previous_polygon_index`, `len`, `getattr`, `float`, `_strip_closure`, `_area_abs`, `_bbox`, `_dbg`, `enumerate`, `min`, `range`, `abs`, `all`, `_poly_inside`, `_poly_coincident_general`, `print`, `max`, `_point_on_segment`, `_bbox_contains`, `candidates.append`, `immediate.append`, `_point_in_poly`, `_point_on_polygon_boundary`

##### `ContinuousSectionField.write_section`

**Source lines:** `572-718`

```python
def write_sectionself, z0: float, z1: float, yaml_path: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `yaml_path` | `positional or keyword` | `str` | `-` |

**Returns:** `None`

**Returned dictionary keys visible in the code**

`CSF`, `sections`

**Raises visible in the code**

- `CSFError`
- `raise`

**Function/method calls visible in the code**

`yaml_path.strip`, `_csf__ensure_parent_dir_exists`, `self.section`, `strip`, `s.find`, `min`, `max`, `CSFError`, `all`, `float`, `shear_weight_laws_yaml.append`, `_csf__section_to_Sz_dict`, `applied_laws_comments.append`, `_csf__atomic_write_text`, `str`, `get`, `_csf__is_finite_number`, `_strip_model_suffix`, `weight_laws_yaml.append`, `globals`, `safe_dump`, `dump`, `join`, `yml.rstrip`, `type`

##### `ContinuousSectionField._section_to_dict`

**Source lines:** `724-736`

**Decorators**

- `staticmethod`

```python
def _section_to_dictsec
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `sec` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Returned dictionary keys visible in the code**

`z`, `polygons`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ContinuousSectionField._polygon_to_dict`, `float`, `items`, `isinstance`, `ValueError`, `globals`

##### `ContinuousSectionField._polygon_to_dict`

**Source lines:** `739-748`

**Decorators**

- `staticmethod`

```python
def _polygon_to_dictpoly
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Returned dictionary keys visible in the code**

`weight`, `vertices`

**Function/method calls visible in the code**

`float`, `XY`

##### `ContinuousSectionField.section_area_list_report`

**Source lines:** `751-886`

```python
def section_area_list_reportself, z: float, w_tol: float=0.0, zero_w_eps: float=0.0, group_mode: str='weight'
```

**Summary:** Print an accountant-style area listing at section z, grouped by ABSOLUTE weight (w_abs),

**Docstring details**

```text
and include the two requested totals:

    Occupied Total Surface: sum(A_net)
    Homogenized area:       sum(A*w) where A*w = A_net * w_abs

Sterile/accounting intent:
- A_net is the polygon signed area as computed (no abs()).
With CCW-only polygons, A_net should be positive.
- W in the table is w_abs (absolute weight along the container chain).
w_tol bins W for grouping/printing only; the product A*w uses the RAW w_abs.

Parameters
----------
z : float
    Longitudinal coordinate where the section is sampled.
w_tol : float
    Grouping tolerance for weights. If > 0, weights are rounded to the nearest multiple
    of w_tol for grouping/printing purposes only.
zero_w_eps : float
    Passed through to the underlying computation (kept for consistency with your API).
    This report's totals are defined strictly by the table columns, not by zero_w_eps.
group_mode : str
    Currently only "weight" is supported. Kept as a label in the header.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `w_tol` | `positional or keyword` | `float` | `0.0` |
| `zero_w_eps` | `positional or keyword` | `float` | `0.0` |
| `group_mode` | `positional or keyword` | `str` | `'weight'` |

**Returns:** `None`

**Returned dictionary keys visible in the code**

`w_group`, `w_abs_raw`, `idx`, `s0_name`, `s1_name`, `a_net`, `a_w`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`self.section_area_by_weight`, `res.get`, `len`, `max`, `rows.sort`, `sum`, `print`, `ValueError`, `int`, `float`, `getattr`, `rows.append`, `str`, `_bin_weight`, `round`

##### `ContinuousSectionField.section_area_by_weight`

**Source lines:** `888-1115`

```python
def section_area_by_weightself, z: float, w_tol: float=0.0, include_per_polygon: bool=False, debug: bool=False, zero_w_eps: float=0.0
```

**Summary:** Compute area breakdown at section z grouped by ABSOLUTE weight (w_abs).

**Docstring details**

```text
This implementation is strictly index-based:
- polygon identity is the polygon index
- names are never used for topology, matching, or grouping
- direct-children topology is taken from S0 through build_direct_children_map(z)

Geometric reporting rule:
- For each polygon i, the reported geometric area is:
    area_geom_net[i] = area_geom[i] - sum(area_geom[j] for j in direct_children[i])
- This subtraction is purely geometric and does not depend on weight.
- Children are subtracted even if their weight is zero.

Effective area rule:
- The effective homogenized area is computed from the net geometric area
of each polygon multiplied by its absolute weight sampled on the section:
    total_area = sum(area_geom_net[i] * w_abs[i])

Args:
    z: Longitudinal coordinate where the section is sampled.
    w_tol: Grouping tolerance for absolute weights. If > 0, weights are rounded
        to the nearest multiple of w_tol for grouping purposes only.
    include_per_polygon: If True, includes detailed per-polygon data in output.
    debug: If True, prints debug information to stdout.
    zero_w_eps: Threshold for considering an absolute weight as zero when
                computing total_area_nonzero. If |w_abs| <= zero_w_eps,
                that polygon contribution is excluded from the nonzero sum.

Returns:
    Dictionary containing:
    - z: Coordinate (float)
    - total_area: Effective homogenized area = sum(area_net * w_abs)
    - total_area_nonzero: Effective homogenized area excluding |w_abs| <= zero_w_eps
    - total_area_geometric: Total net geometric surface = sum(area_net)
    - groups: List of absolute-weight groups with accumulated net geometric areas
    - per_polygon: (Optional) Detailed per-polygon data
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `w_tol` | `positional or keyword` | `float` | `0.0` |
| `include_per_polygon` | `positional or keyword` | `bool` | `False` |
| `debug` | `positional or keyword` | `bool` | `False` |
| `zero_w_eps` | `positional or keyword` | `float` | `0.0` |

**Returns:** `Dict[str, Any]`

**Returned dictionary keys visible in the code**

`z`, `total_area`, `total_area_nonzero`, `total_area_geometric`, `groups`, `w`, `area`, `polygons`, `idx`, `container_idx`, `children_idx`, `w_rel`, `w_abs`, `area_geom`

**Raises visible in the code**

- `ValueError`
- `TypeError`

**Function/method calls visible in the code**

`self.section`, `len`, `self.build_direct_children_map`, `direct_children_map.items`, `direct_children.items`, `enumerate`, `range`, `sum`, `sorted`, `ValueError`, `_polygon_signed_area_and_centroid`, `float`, `bin_weight`, `append`, `per_polygon_records.append`, `groups.values`, `print`, `hasattr`, `isinstance`, `TypeError`, `round`, `list`, `abs`, `type`

##### `ContinuousSectionField._determine_magnitude`

**Source lines:** `1118-1202`

```python
def _determine_magnitudeself
```

**Summary:** Compute a global geometric magnitude (scale) from the model's geometry and

**Docstring details**

```text
define tolerance values derived from that scale.

This method is intentionally self-contained (no external helper functions),
so it can be called once after object construction.

It defines:
  - self.SCALE: characteristic length scale of the model
  - self._tol.EPS_L: linear/length tolerance (geometry predicates, intersections)
  - self._tol.EPS_A: area tolerance (degeneracy checks on areas, section integrals)
  - self._tol.EPS_K_ATOL / self._tol.EPS_K_RTOL: tolerances for matrix/numerical checks
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`float`, `max`, `getattr`, `abs`

##### `ContinuousSectionField.to_dict`

**Source lines:** `1206-1245`

```python
def to_dictself, include_weight_laws=True
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `include_weight_laws` | `positional or keyword` | `not annotated` | `True` |

**Returns:** `not annotated`

**Returned dictionary keys visible in the code**

`CSF`, `sections`, `S0`, `S1`

**Function/method calls visible in the code**

`sorted`, `shear_out.append`, `self._section_to_dict`, `out.append`, `self.QuotedStr`

##### `ContinuousSectionField.to_yaml`

**Source lines:** `1248-1266`

```python
def to_yamlself, filepath: Optional[str]=None, include_weight_laws: bool=True
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `filepath` | `positional or keyword` | `Optional[str]` | `None` |
| `include_weight_laws` | `positional or keyword` | `bool` | `True` |

**Returns:** `str`

**Function/method calls visible in the code**

`self.to_dict`, `yaml.dump`, `_simple_yaml_dump`, `open`, `f.write`

##### `ContinuousSectionField.get_lobatto_integration_points`

**Source lines:** `1274-1284`

```python
def get_lobatto_integration_pointsself, n_points: int=5, L: float | None=None
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `n_points` | `positional or keyword` | `int` | `5` |
| `L` | `positional or keyword` | `float | None` | `None` |

**Returns:** `List[float]`

**Function/method calls visible in the code**

`compute_lobatto_integration_points`

##### `ContinuousSectionField.__init__`

**Source lines:** `1288-1310`

```python
def __init__self, section0: Section, section1: Section
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `section0` | `positional or keyword` | `Section` | `-` |
| `section1` | `positional or keyword` | `Section` | `-` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`self._determine_magnitude`, `self._validate_inputs`, `len`, `ValueError`

##### `ContinuousSectionField.L`

**Source lines:** `1313-1315`

**Decorators**

- `property`

```python
def Lself
```

**Summary:** Return the absolute longitudinal length of the CSF segment.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`abs`, `float`

##### `ContinuousSectionField._strip_model_tags`

**Source lines:** `1317-1328`

```python
def _strip_model_tagsname: str
```

**Summary:** Remove everything starting from @cell or @wall (case-insensitive).

**Docstring details**

```text
If neither tag exists, return original trimmed name.
Examples:
  "MP1_outer@cell@t=0.05" -> "MP1_outer"
  "legA@wall@alpha=0.8"   -> "legA"
  "poly_no_tags"          -> "poly_no_tags"
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `name` | `positional or keyword` | `str` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`strip`, `re.sub`

##### `ContinuousSectionField._strip_model_tags`

**Source lines:** `1330-1337`

```python
def _strip_model_tagsself, name: str
```

**Summary:** Normalize polygon name for matching:

**Docstring details**

```text
- trim spaces
- remove everything starting from @cell, @wall, or @closed (case-insensitive)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `name` | `positional or keyword` | `str` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`strip`, `str`, `re.sub`

##### `ContinuousSectionField.set_shear_weight_laws`

**Source lines:** `1340-1543`

```python
def set_shear_weight_lawsself, laws: Union[List[str], Dict[Union[int, str], str]]
```

**Summary:** Set shear-weight variation laws.

**Docstring details**

```text
Rules:
- List item without ':' is the global default shear-weight law.
- List item with ':' is a polygon-specific shear-weight law.
- Polygon indices are 0-based.
- Polygon-name mapping follows the same S0/S1 homology logic used by set_weight_laws().
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `laws` | `positional or keyword` | `Union[List[str], Dict[Union[int, str], str]]` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`
- `KeyError`
- `IndexError`

**Function/method calls visible in the code**

`len`, `isinstance`, `normalized_map.items`, `ValueError`, `self._strip_model_tags`, `range`, `str`, `item.strip`, `item.split`, `left.strip`, `formula.strip`, `laws.items`, `valid_names0.index`, `valid_names1.index`, `name.strip`, `left.split`, `KeyError`, `IndexError`, `key.strip`

##### `ContinuousSectionField.set_weight_laws`

**Source lines:** `1548-1669`

```python
def set_weight_lawsself, laws: Union[List[str], Dict[Union[int, str], str]]
```

**Summary:** Sets weight variation laws.

**Docstring details**

```text
If a polygon name is not found or homology fails, it raises an error 
to prevent falling back to default linear behavior.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `laws` | `positional or keyword` | `Union[List[str], Dict[Union[int, str], str]]` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`
- `KeyError`

**Function/method calls visible in the code**

`len`, `isinstance`, `normalized_map.items`, `ValueError`, `self._strip_model_tags`, `enumerate`, `str`, `item.split`, `tuple`, `abs`, `left.strip`, `formula.strip`, `evaluate_weight_formula`, `left.split`, `KeyError`, `valid_names0.index`, `valid_names1.index`, `v0.lerp`, `zip`

##### `ContinuousSectionField._validate_inputs`

**Source lines:** `1674-1683`

```python
def _validate_inputsself
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

`enumerate`, `len`, `ValueError`, `zip`

##### `ContinuousSectionField._interpolate_weight`

**Source lines:** `1685-1714`

```python
def _interpolate_weightself, w0: float, w1: float, z: float, p0: Polygon, p1: Polygon, law: Optional[str]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `w0` | `positional or keyword` | `float` | `-` |
| `w1` | `positional or keyword` | `float` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `p0` | `positional or keyword` | `Polygon` | `-` |
| `p1` | `positional or keyword` | `Polygon` | `-` |
| `law` | `positional or keyword` | `Optional[str]` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`abs`, `isinstance`, `law.strip`, `evaluate_weight_formula`, `ValueError`

##### `ContinuousSectionField._interpolate_shear_weight`

**Source lines:** `1718-1742`

```python
def _interpolate_shear_weightself, w: float, w0: float, w1: float, z: float, p0: Polygon, p1: Polygon, law: Optional[str]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `w` | `positional or keyword` | `float` | `-` |
| `w0` | `positional or keyword` | `float` | `-` |
| `w1` | `positional or keyword` | `float` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `p0` | `positional or keyword` | `Polygon` | `-` |
| `p1` | `positional or keyword` | `Polygon` | `-` |
| `law` | `positional or keyword` | `Optional[str]` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`isinstance`, `law.strip`, `evaluate_shear_weight_formula`, `ValueError`

##### `ContinuousSectionField._to_t`

**Source lines:** `1745-1749`

```python
def _to_tself, z: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `ValueError`, `min`, `max`

##### `ContinuousSectionField.section`

**Source lines:** `1753-2216`

```python
def sectionself, z: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `Section`

**Raises visible in the code**

- `CSFError`

**Function/method calls visible in the code**

`abs`, `enumerate`, `Section`, `re.search`, `float`, `_extract_topology`, `_parse_t`, `_left_of_at`, `CSFError`, `zip`, `tuple`, `get_shear_weight_law`, `parse_iso`, `self._interpolate_weight`, `self._interpolate_shear_weight`, `self.get_container_polygon_index`, `_resolve_topology_and_t_from_names`, `Polygon`, `polys.append`, `lower`, `_norm_name`, `str`, `s.lower`, `low.find`, `set`, `_interp_linear`, `strip`, `s.find`, `self.weight_laws.get`, `print`, `_build_interpolated_polygon_name`, `m.group`, `int`, `len`, `v0.lerp`, `buf.append`, `join`, `_fmt_t`

## Functions

## Digestor: Section properties (2D polygon-based)

### `_polygon_signed_area_and_centroid`

**Source lines:** `2222-2230`

```python
def _polygon_signed_area_and_centroidpoly: Polygon
```

**Summary:** Shoelace.

**Docstring details**

```text
with no weight
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `positional or keyword` | `Polygon` | `-` |

**Returns:** `Tuple[float, Tuple[float, float]]`

**Function/method calls visible in the code**

`_signed_area_centroid_xy`

### `polygon_area_centroid`

**Source lines:** `2232-2236`

```python
def polygon_area_centroidpoly: Polygon
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `positional or keyword` | `Polygon` | `-` |

**Returns:** `Tuple[float, Tuple[float, float]]`

**Function/method calls visible in the code**

`_polygon_signed_area_and_centroid`

## with weight

### `section_data`

**Source lines:** `2239-2292`

```python
def section_datafield: ContinuousSectionField, z: float
```

**Summary:** z is ABSOLUTE

**Docstring details**

```text
Extracts the complete geometric state and physical properties of a section 
at a specific longitudinal coordinate (z).

TECHNICAL SUMMARY:
This function acts as a high-level accessor for the Continuous Section Field. 
It performs a synchronized extraction of both the interpolated boundary 
geometry and the corresponding integral properties (Area, First/Second Moments). 
It provides a discrete "snapshot" of a 3D ruled solid at any point along 
its integration path.

WORKFLOW AND DATA ARCHITECTURE:
1. Geometric Reconstruction:
   The function first invokes the internal Linear Interpolation (LERP) 
   mechanism to reconstruct the homogenized polygonal boundaries at 
   coordinate 'z'. This ensures topological consistency across the 
   longitudinal domain.

2. Property Integration:
   Once the geometry is established, the 'section_properties' engine 
   is executed to compute the sectional digest. This involves:
   - Zeroth Moment: Area (A).
   - First Moments: Centroidal coordinates (Cx, Cy).
   - Second Moments: Moments of inertia (Ix, Iy, Ixy) and the Polar 
     Moment (J).

3. Data Encapsulation:
   The results are packaged into a dictionary structure, decoupling the 
   raw geometric data (vertices/polygons) from the derived structural 
   parameters.

APPLICABILITY:
This function is the standard interface for structural analysis routines 
that require local stiffness or stress evaluation at specific points 
along a non-prismatic member.

RETURNS:
   A dictionary containing:
   - 'section': The Section object (polygonal boundaries at z).
   - 'properties': A dictionary of computed geometric constants.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `ContinuousSectionField` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `dict`

**Returned dictionary keys visible in the code**

`section`, `properties`

**Function/method calls visible in the code**

`field.section`, `section_properties`

## Visualization helpers

### `_set_axes_equal_3d`

**Source lines:** `2301-2357`

```python
def _set_axes_equal_3dax
```

**Summary:** Configures 3D axis limits to perform a 'selective zoom' and maintain

**Docstring details**

```text
consistent aspect ratios for cross-sectional visualization.

TECHNICAL SUMMARY:
This function normalizes the viewport of a Matplotlib 3D projection. 
It ensures that the horizontal plane (X-Y) is scaled isotropically 
(equal aspect ratio) to prevent geometric distortion of the sections, 
while allowing the longitudinal axis (Z) to retain its full physical 
extent for structural context.

ALGORITHMIC LOGIC:
1. Limit Extraction:
   Retrieves current bounding box limits for X, Y, and Z dimensions 
   to determine the object's spatial center.

2. Planar Isotropic Scaling:
   Calculates a maximum radius based on the spans of X and Y. By 
   applying this radius symmetrically to both horizontal axes, the 
   function ensures that circles or ellipses appear without 
   eccentricity distortion.

3. Longitudinal Preservation:
   Unlike standard 'equal axis' commands, this logic preserves the 
   original Z-limits. This is crucial for high-aspect-ratio solids, 
   ensuring the entire height is visible within the frame.

4. Box Aspect Ratio:
   Sets the 'box_aspect' to (1, 1, 2) to force a vertical emphasis, 
   making slender solids visually representative of their physical 
   proportions.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `ax` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`ax.get_xlim3d`, `ax.get_ylim3d`, `ax.get_zlim3d`, `abs`, `ax.set_xlim3d`, `ax.set_ylim3d`, `ax.set_zlim3d`, `ax.set_box_aspect`, `sum`, `max`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
