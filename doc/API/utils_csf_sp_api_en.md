# API Reference - `csf_sp.py`

This document covers the top-level classes and functions defined in `src/csf/utils/csf_sp.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/utils/csf_sp.py`
- Output file: `doc/API/utils_csf_sp_api_en.md`
- Top-level function definitions found: `42`.
- Top-level classes found: `3`.
- Duplicate function names found: `0`.

## Module docstring

```text
Bridge between CSF and sectionproperties.

This tool uses sectionproperties as the finite-element-based section analysis
backend where applicable.

sectionproperties:
https://github.com/robbievanleeuwen/section-properties
License: MIT


This module exposes a compact but non-trivial topology bridge between CSF and
sectionproperties. The important point is that the bridge does *not* rebuild a
section by hand as one outer contour plus a flat list of holes. Instead, it
transfers the CSF nesting structure node by node.

Supported input modes
---------------------
1. Legacy text mode: parse one or more ``## GEOMETRY EXPORT ##`` blocks.
2. YAML mode: load a CSF model, sample ``field.section(z)``, read direct
   container topology from the field, and build the sectionproperties input.

Core bridge policy
------------------
- Every CSF polygon node contributes its own *local domain*.
- A node local domain is the node support region minus the outer envelopes of
  its direct children.
- Positive-weight nodes become active sectionproperties regions.
- Zero-weight nodes are still topologically important: their local domains are
  treated as explicit void candidates when hole seeds are computed.

Why this matters
----------------
This policy preserves general nesting for homogenized geometric properties and
fixes an important failure mode: a zero-weight void may disappear from the SP
view when it touches another region exactly on the boundary, especially in deep
nested topologies. The bridge therefore computes local domains for *all* nodes,
not only for active ones.

Torsion carrier policy
----------------------
sectionproperties reports composite Saint-Venant torsion as ``e.j`` because its
torsion assembly is weighted by the value stored as ``elastic_modulus``.

For the native sectionproperties run, CSF maps the axial/bending carrier to
``elastic_modulus``. The native ``sec.get_ej()`` result is therefore reported as
the sectionproperties native ``e.j`` result.

For CSF torsion, this bridge can also perform a dedicated torsion-only carrier
run where the value passed to sectionproperties as ``elastic_modulus`` is the
resolved CSF shear carrier ``G_i`` / ``shear_w_i``. The resulting
sectionproperties ``e.j`` value from that second run is reported as a CSF
torsion-carrier result, not as a native sectionproperties ``g.j`` output.
```

## Public API index

- `Row` - line 91
- `PolygonInput` - line 107
- `NodeShape` - line 121
- `def _parse_optional_ints: str` - line 133
- `def _parse_optional_floats: str` - line 140
- `def _require_defined_poissonidx_polygon: int, value: Any` - line 147
- `def _read_optional_shear_widx_polygon: int, poly: Any` - line 164
- `def strip_wall_cell_suffixname: str` - line 194
- `def _name_has_cell_tagname: str` - line 218
- `def _read_geometry_export_blockstext: str` - line 228
- `def _group_rows_by_polygonrows: Iterable[Row]` - line 332
- `def _rows_to_polygon_inputsrows: List[Row]` - line 339
- `def _select_z_blockblocks: Dict[float, List[Row]], requested_z: Optional[float]` - line 411
- `def _format_text_blockheader: str, lines: List[str]` - line 429
- `def _format_reader_issuesissues: List[Any], header: str` - line 436
- `def _make_yaml_snippettext: str, line_no: int, col_no: Optional[int]=None` - line 467
- `def _load_run_config_yamlrun_config_path: Path` - line 486
- `def _load_field_from_yamlyaml_path: Path` - line 519
- `def _load_station_setrun_config_path: Path, station_set_name: str` - line 556
- `def _polygon_inputs_from_fieldfield, z: float` - line 593
- `def _make_polygoncoords: List[Tuple[float, float]], label: str` - line 661
- `def _split_cell_polygonvertices: List[Tuple[float, float]], label: str` - line 688
- `def _collect_childrenpolygon_inputs: Dict[int, PolygonInput]` - line 757
- `def _make_materialweight: float, poisson: float, label: str` - line 767
- `def _geometry_from_regionregion: ShapelyPolygon, poly: PolygonInput, label: str` - line 795
- `def _union_or_raisepolys: List[ShapelyPolygon], label: str` - line 801
- `def _polygon_parts_from_geometrygeom: BaseGeometry, label: str` - line 809
- `def _looks_like_slit_encoded_polygonvertices: List[Tuple[float, float]]` - line 841
- `def _build_node_shapespolygon_inputs: Dict[int, PolygonInput]` - line 854
- `def _compute_node_local_domainspolygon_inputs: Dict[int, PolygonInput]` - line 912
- `def _build_sectionproperties_geometrypolygon_inputs: Dict[int, PolygonInput], local_domains: Dict[int, List[ShapelyPolygon]]` - line 953
- `def _polygon_list_from_sectionproperties_geometrygeom: Geometry | CompoundGeometry` - line 987
- `def _interior_ring_polygonsregion_polys: List[ShapelyPolygon]` - line 1013
- `def _compute_effective_hole_pointsregion_polys: List[ShapelyPolygon], polygon_inputs: Dict[int, PolygonInput], local_domains: Dict[int, List[ShapelyPolygon]]` - line 1036
- `def _apply_effective_hole_pointsgeom: Geometry | CompoundGeometry, polygon_inputs: Dict[int, PolygonInput], local_domains: Dict[int, List[ShapelyPolygon]]` - line 1081
- `def _geometry_is_connectedgeom: Geometry | CompoundGeometry, tol: float=1e-08` - line 1108
- `def _make_torsion_carrier_inputspolygon_inputs: Dict[int, PolygonInput]` - line 1138
- `def _build_meshed_geometrypolygon_inputs: Dict[int, PolygonInput], mesh: float` - line 1175
- `def _compute_torsion_carrier_resultpolygon_inputs: Dict[int, PolygonInput], mesh: float` - line 1187
- `def _print_torsion_resultssec: Section, polygon_inputs: Dict[int, PolygonInput], mesh: float` - line 1216
- `def _analyse_one_geometryz: float, polygon_inputs: Dict[int, PolygonInput], mesh: float, plot: bool, warping: bool=True` - line 1249
- `def main` - line 1307
- `def load_yamlpath: 'str | Path'` - line 1404
- `def analysefield: Any, z: float, mesh: float=1.0, warping: bool=True` - line 1429
- `def analyse_torsion_carrierfield: Any, z: float, mesh: float=1.0` - line 1494

## API details

## Classes

### `Row`

**Source lines:** `91-103`

**Decorators**

- `dataclass(frozen=True)`

```python
class Row
```

**Summary:** One CSV geometry row from a CSF export block.

### `PolygonInput`

**Source lines:** `107-117`

**Decorators**

- `dataclass(frozen=True)`

```python
class PolygonInput
```

**Summary:** Minimal polygon payload consumed by the sectionproperties backend.

### `NodeShape`

**Source lines:** `121-125`

**Decorators**

- `dataclass(frozen=True)`

```python
class NodeShape
```

**Summary:** Cached geometric payload for one CSF polygon node.

## Functions

## Generic helpers

### `_parse_optional_int`

**Source lines:** `133-137`

```python
def _parse_optional_ints: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `s` | `positional or keyword` | `str` | `-` |

**Returns:** `Optional[int]`

**Function/method calls visible in the code**

`strip`, `int`

### `_parse_optional_float`

**Source lines:** `140-144`

```python
def _parse_optional_floats: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `s` | `positional or keyword` | `str` | `-` |

**Returns:** `Optional[float]`

**Function/method calls visible in the code**

`strip`, `float`

### `_require_defined_poisson`

**Source lines:** `147-161`

```python
def _require_defined_poissonidx_polygon: int, value: Any
```

**Summary:** Return a defined Poisson ratio or stop explicitly.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `idx_polygon` | `positional or keyword` | `int` | `-` |
| `value` | `positional or keyword` | `Any` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`math.isnan`, `float`, `SystemExit`

### `_read_optional_shear_w`

**Source lines:** `164-191`

```python
def _read_optional_shear_widx_polygon: int, poly: Any
```

**Summary:** Read the sampled CSF shear carrier when it is explicitly available.

**Docstring details**

```text
No default value is invented here. If the sampled polygon does not expose a
shear carrier, the torsion-carrier run is reported as unavailable.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `idx_polygon` | `positional or keyword` | `int` | `-` |
| `poly` | `positional or keyword` | `Any` | `-` |

**Returns:** `Optional[float]`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`getattr`, `math.isnan`, `hasattr`, `float`, `SystemExit`

## Top-level functions

### `strip_wall_cell_suffix`

**Source lines:** `194-215`

```python
def strip_wall_cell_suffixname: str
```

**Summary:** Remove the first occurrence of '@cell', '@wall', or '@closed'

**Docstring details**

```text
and everything after it.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `name` | `positional or keyword` | `str` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`name.lower`, `min`, `low.find`

### `_name_has_cell_tag`

**Source lines:** `218-220`

```python
def _name_has_cell_tagname: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `name` | `positional or keyword` | `str` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`lower`

### `_group_rows_by_polygon`

**Source lines:** `332-336`

```python
def _group_rows_by_polygonrows: Iterable[Row]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `rows` | `positional or keyword` | `Iterable[Row]` | `-` |

**Returns:** `Dict[int, List[Row]]`

**Function/method calls visible in the code**

`append`, `grouped.setdefault`

### `_rows_to_polygon_inputs`

**Source lines:** `339-408`

```python
def _rows_to_polygon_inputsrows: List[Row]
```

**Summary:** Convert text-export rows to polygon inputs.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `rows` | `positional or keyword` | `List[Row]` | `-` |

**Returns:** `Dict[int, PolygonInput]`

**Raises visible in the code**

- `ValueError`
- `SystemExit`

**Function/method calls visible in the code**

`_group_rows_by_polygon`, `grouped.items`, `sorted`, `float`, `_require_defined_poisson`, `PolygonInput`, `ValueError`, `SystemExit`, `print`, `_name_has_cell_tag`

### `_select_z_block`

**Source lines:** `411-421`

```python
def _select_z_blockblocks: Dict[float, List[Row]], requested_z: Optional[float]
```

**Summary:** Select one z block from legacy geometry-export text.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `blocks` | `positional or keyword` | `Dict[float, List[Row]]` | `-` |
| `requested_z` | `positional or keyword` | `Optional[float]` | `-` |

**Returns:** `Tuple[float, List[Row]]`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`sorted`, `blocks.keys`, `SystemExit`

### `_load_run_config_yaml`

**Source lines:** `486-516`

```python
def _load_run_config_yamlrun_config_path: Path
```

**Summary:** Read and parse the run-config YAML with clear parser errors.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `run_config_path` | `positional or keyword` | `Path` | `-` |

**Returns:** `Dict[str, Any]`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`run_config_path.read_text`, `yaml.safe_load`, `isinstance`, `SystemExit`, `getattr`, `_make_yaml_snippet`, `int`

### `_load_field_from_yaml`

**Source lines:** `519-553`

```python
def _load_field_from_yamlyaml_path: Path
```

**Summary:** Rough-validate first, then load the CSF field through the official reader.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `yaml_path` | `positional or keyword` | `Path` | `-` |

**Returns:** `not annotated`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`validate_text`, `list`, `yaml_path.read_text`, `SystemExit`, `read_file`, `str`, `_format_text_block`, `getattr`, `CSFReader`, `_format_reader_issues`

### `_load_station_set`

**Source lines:** `556-590`

```python
def _load_station_setrun_config_path: Path, station_set_name: str
```

**Summary:** Load one station set from a small YAML run-config file.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `run_config_path` | `positional or keyword` | `Path` | `-` |
| `station_set_name` | `positional or keyword` | `str` | `-` |

**Returns:** `List[float]`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`_load_run_config_yaml`, `data.get`, `enumerate`, `SystemExit`, `out.append`, `isinstance`, `station_set_name.strip`, `type`, `float`, `sorted`, `station_sets.keys`

### `_polygon_inputs_from_field`

**Source lines:** `593-653`

```python
def _polygon_inputs_from_fieldfield, z: float
```

**Summary:** Build polygon inputs directly from ``field.section(z)``.

**Docstring details**

```text
IMPORTANT:
This function is intentionally topology-driven. It does not try to infer
holes from polygon orientation or from boolean operations. Instead it reads:
- the sampled polygon coordinates,
- the sampled absolute weights,
- the sampled absolute shear carrier when present,
- the direct container relation from the CSF field.

The rest of the bridge assumes that the polygon ordering used by
``field.section(z)`` and the indices referenced by
``field.build_direct_children_map(z)`` are consistent.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `Dict[int, PolygonInput]`

**Raises visible in the code**

- `ValueError`
- `SystemExit`

**Function/method calls visible in the code**

`field.section`, `field.build_direct_children_map`, `children_map.items`, `enumerate`, `float`, `str`, `_read_optional_shear_w`, `_require_defined_poisson`, `PolygonInput`, `hasattr`, `ValueError`, `getattr`, `SystemExit`, `print`, `parent_of.get`, `_name_has_cell_tag`

### `_geometry_from_region`

**Source lines:** `795-798`

```python
def _geometry_from_regionregion: ShapelyPolygon, poly: PolygonInput, label: str
```

**Summary:** Convert one shapely region to one sectionproperties Geometry carrying CSF material data.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `region` | `positional or keyword` | `ShapelyPolygon` | `-` |
| `poly` | `positional or keyword` | `PolygonInput` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `Geometry`

**Function/method calls visible in the code**

`_make_material`, `Geometry`

### `_union_or_raise`

**Source lines:** `801-806`

```python
def _union_or_raisepolys: List[ShapelyPolygon], label: str
```

**Summary:** Union helper with explicit error on empty output.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polys` | `positional or keyword` | `List[ShapelyPolygon]` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `BaseGeometry`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`unary_union`, `ValueError`

### `_polygon_parts_from_geometry`

**Source lines:** `809-838`

```python
def _polygon_parts_from_geometrygeom: BaseGeometry, label: str
```

**Summary:** Extract polygon parts from a shapely result.

**Docstring details**

```text
Lower-dimensional leftovers created by exact boundary contact are ignored.
The bridge only accepts polygonal area regions as valid domain pieces.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geom` | `positional or keyword` | `BaseGeometry` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `List[ShapelyPolygon]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`enumerate`, `out.append`, `list`, `ValueError`

### `_looks_like_slit_encoded_polygon`

**Source lines:** `841-851`

```python
def _looks_like_slit_encoded_polygonvertices: List[Tuple[float, float]]
```

**Summary:** Detect a slit-encoded multi-loop polygon by an early repeated first vertex.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `vertices` | `positional or keyword` | `List[Tuple[float, float]]` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`range`, `len`

### `_build_node_shapes`

**Source lines:** `854-903`

```python
def _build_node_shapespolygon_inputs: Dict[int, PolygonInput]
```

**Summary:** Build cached support regions and parent-cutout envelopes for each node.

**Docstring details**

```text
support_region:
- standard polygon -> full polygon area
- @cell polygon     -> outer shell with intrinsic inner hole

outer_envelope:
- the polygon area that must be removed from the direct parent domain
- standard polygon -> full polygon
- @cell polygon     -> outer shell only
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |

**Returns:** `Dict[int, NodeShape]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`polygon_inputs.items`, `_looks_like_slit_encoded_polygon`, `_make_polygon`, `NodeShape`, `_split_cell_polygon`, `ShapelyPolygon`, `ValueError`, `list`

### `_build_sectionproperties_geometry`

**Source lines:** `953-984`

```python
def _build_sectionproperties_geometrypolygon_inputs: Dict[int, PolygonInput], local_domains: Dict[int, List[ShapelyPolygon]]
```

**Summary:** Build the sectionproperties geometry from parsed polygon inputs.

**Docstring details**

```text
IMPORTANT SEPARATION OF ROLES:
- ``w > 0`` local-domain pieces -> active SP regions
- ``w = 0`` local-domain pieces -> not active material, but still topological
  void candidates handled later when hole seeds are computed

This separation is what keeps the bridge consistent with CSF when explicit
voids touch other regions exactly on the boundary.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |
| `local_domains` | `positional or keyword` | `Dict[int, List[ShapelyPolygon]]` | `-` |

**Returns:** `Geometry | CompoundGeometry`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`polygon_inputs.items`, `CompoundGeometry`, `enumerate`, `ValueError`, `len`, `local_domains.get`, `pieces.append`, `_geometry_from_region`

### `_polygon_list_from_sectionproperties_geometry`

**Source lines:** `987-1010`

```python
def _polygon_list_from_sectionproperties_geometrygeom: Geometry | CompoundGeometry
```

**Summary:** Extract shapely polygon regions from a sectionproperties geometry object.

**Docstring details**

```text
The bridge only creates polygon-based regions, so any non-polygon payload is
treated as an internal error.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geom` | `positional or keyword` | `Geometry | CompoundGeometry` | `-` |

**Returns:** `List[ShapelyPolygon]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`isinstance`, `enumerate`, `list`, `polys.append`, `ValueError`

### `_interior_ring_polygons`

**Source lines:** `1013-1026`

```python
def _interior_ring_polygonsregion_polys: List[ShapelyPolygon]
```

**Summary:** Convert all interior rings of active regions into polygonal void candidates.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `region_polys` | `positional or keyword` | `List[ShapelyPolygon]` | `-` |

**Returns:** `List[ShapelyPolygon]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`enumerate`, `ShapelyPolygon`, `out.append`, `ValueError`

### `_apply_effective_hole_points`

**Source lines:** `1081-1100`

```python
def _apply_effective_hole_pointsgeom: Geometry | CompoundGeometry, polygon_inputs: Dict[int, PolygonInput], local_domains: Dict[int, List[ShapelyPolygon]]
```

**Summary:** Add CSF-derived hole seeds without deleting hole seeds already found by SP.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geom` | `positional or keyword` | `Geometry | CompoundGeometry` | `-` |
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |
| `local_domains` | `positional or keyword` | `Dict[int, List[ShapelyPolygon]]` | `-` |

**Returns:** `Geometry | CompoundGeometry`

**Function/method calls visible in the code**

`_polygon_list_from_sectionproperties_geometry`, `_compute_effective_hole_points`, `list`, `getattr`

### `_compute_torsion_carrier_result`

**Source lines:** `1187-1213`

```python
def _compute_torsion_carrier_resultpolygon_inputs: Dict[int, PolygonInput], mesh: float
```

**Summary:** Compute the CSF torsion-carrier result through a dedicated SP run.

**Docstring details**

```text
The returned value is the sectionproperties ``e.j`` value obtained after
substituting the carrier:

    E_SP := G_i / shear_w_i

It is intentionally not named ``g.j`` because sectionproperties does not
expose a native ``g.j`` result.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |
| `mesh` | `positional or keyword` | `float` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`_make_torsion_carrier_inputs`, `_build_meshed_geometry`, `Section`, `sec.calculate_geometric_properties`, `sec.calculate_warping_properties`, `float`, `_geometry_is_connected`, `ValueError`, `sec.get_ej`

### `_print_torsion_results`

**Source lines:** `1216-1241`

```python
def _print_torsion_resultssec: Section, polygon_inputs: Dict[int, PolygonInput], mesh: float
```

**Summary:** Print native SP torsion and CSF torsion-carrier output.

**Docstring details**

```text
The second value is labelled as a CSF carrier result, not as an SP-native
``g.j`` quantity.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `sec` | `positional or keyword` | `Section` | `-` |
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |
| `mesh` | `positional or keyword` | `float` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`print`, `float`, `sec.get_ej`, `_compute_torsion_carrier_result`

### `analyse_torsion_carrier`

**Source lines:** `1494-1527`

```python
def analyse_torsion_carrierfield: Any, z: float, mesh: float=1.0
```

**Summary:** Return the CSF torsion-carrier result at a station.

**Docstring details**

```text
This performs a dedicated sectionproperties torsion-only run after replacing
the normal axial/bending carrier by the resolved CSF shear carrier:

    E_SP := G_i / shear_w_i

The returned scalar is the sectionproperties ``e.j`` value from that carrier
run. It is intentionally exposed as a CSF torsion-carrier result, not as a
native sectionproperties ``g.j`` output.

Parameters
----------
field:
    A ``ContinuousSectionField`` instance.
z:
    Longitudinal coordinate at which to sample the section.
mesh:
    Maximum triangular element area for the sectionproperties mesh.

Returns
-------
float
    The carrier-weighted torsional result computed with ``E_SP := G_i``.

Raises
------
ValueError
    If the sampled CSF model does not expose ``shear_w`` for every polygon,
    or if the active carrier geometry is disconnected.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `mesh` | `positional or keyword` | `float` | `1.0` |

**Returns:** `float`

**Function/method calls visible in the code**

`_polygon_inputs_from_field`, `_compute_torsion_carrier_result`, `float`

## Legacy text mode

### `_read_geometry_export_blocks`

**Source lines:** `228-329`

```python
def _read_geometry_export_blockstext: str
```

**Summary:** Return {z_value: [rows]} for each geometry export block found in the text.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |

**Returns:** `Dict[float, List[Row]]`

**Raises visible in the code**

- `ValueError`
- `SystemExit`

**Function/method calls visible in the code**

`text.splitlines`, `len`, `strip`, `ValueError`, `s.startswith`, `raw.strip`, `next`, `rows.append`, `float`, `csv.reader`, `lower`, `SystemExit`, `Row`, `c.strip`, `enumerate`, `int`, `_parse_optional_int`, `_parse_optional_float`, `s.split`

## YAML mode

### `_format_text_block`

**Source lines:** `429-433`

```python
def _format_text_blockheader: str, lines: List[str]
```

**Summary:** Join a header and a list of diagnostic lines into one printable block.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `header` | `positional or keyword` | `str` | `-` |
| `lines` | `positional or keyword` | `List[str]` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`out.extend`, `join`, `str`

### `_format_reader_issues`

**Source lines:** `436-464`

```python
def _format_reader_issuesissues: List[Any], header: str
```

**Summary:** Format CSFReader issues into a readable multi-line message.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `issues` | `positional or keyword` | `List[Any]` | `-` |
| `header` | `positional or keyword` | `str` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`join`, `str`, `getattr`, `lines.append`, `isinstance`, `context.get`

### `_make_yaml_snippet`

**Source lines:** `467-483`

```python
def _make_yaml_snippettext: str, line_no: int, col_no: Optional[int]=None
```

**Summary:** Build a compact YAML snippet around a specific location.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |
| `line_no` | `positional or keyword` | `int` | `-` |
| `col_no` | `positional or keyword` | `Optional[int]` | `None` |

**Returns:** `str`

**Function/method calls visible in the code**

`text.splitlines`, `max`, `min`, `range`, `join`, `len`, `out.append`

## sectionproperties backend

### `_make_polygon`

**Source lines:** `661-685`

```python
def _make_polygoncoords: List[Tuple[float, float]], label: str
```

**Summary:** Build a shapely polygon without silently fixing invalid geometry.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `coords` | `positional or keyword` | `List[Tuple[float, float]]` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `ShapelyPolygon`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ShapelyPolygon`, `print`, `ValueError`, `len`, `explain_validity`

### `_split_cell_polygon`

**Source lines:** `688-754`

```python
def _split_cell_polygonvertices: List[Tuple[float, float]], label: str
```

**Summary:** Split a slit-encoded @cell polygon into OUTER and INNER loops.

**Docstring details**

```text
Policy:
- OUTER loop is detected by the first repeated occurrence of the first vertex.
- INNER loop is the remaining tail after OUTER closure.
- INNER explicit repeated endpoint is optional.
- If the tail closes back to the first OUTER vertex, that last point is dropped.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `vertices` | `positional or keyword` | `List[Tuple[float, float]]` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`range`, `_make_polygon`, `abs`, `len`, `ValueError`, `print`

## first OUTER vertex after the INNER loop. That point is not part of INNER.

### `_collect_children`

**Source lines:** `757-764`

```python
def _collect_childrenpolygon_inputs: Dict[int, PolygonInput]
```

**Summary:** Build parent -> child polygon id mapping.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |

**Returns:** `Dict[Optional[int], List[int]]`

**Function/method calls visible in the code**

`polygon_inputs.items`, `append`, `children.setdefault`

### `_make_material`

**Source lines:** `767-792`

```python
def _make_materialweight: float, poisson: float, label: str
```

**Summary:** Build a sectionproperties material from the current carrier and Poisson data.

**Docstring details**

```text
Bridge convention:
- the current carrier is mapped to sectionproperties ``elastic_modulus``
- ``poisson`` is mapped to ``poissons_ratio``
- sectionproperties internally uses ``elastic_modulus`` as the torsion carrier
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `weight` | `positional or keyword` | `float` | `-` |
| `poisson` | `positional or keyword` | `float` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `Material`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`math.isnan`, `Material`, `ValueError`, `float`

## Compute local domains for every node, including zero-weight nodes.

### `_compute_node_local_domains`

**Source lines:** `912-950`

```python
def _compute_node_local_domainspolygon_inputs: Dict[int, PolygonInput]
```

**Summary:** Build the local domain partition for every CSF node.

**Docstring details**

```text
THIS IS THE CENTRAL TOPOLOGICAL STEP OF THE BRIDGE.

Local-domain policy:
- start from the node support region
- remove the outer envelopes of all direct children
- keep only polygonal area pieces

Why this is computed for *all* nodes, including ``w = 0``:
- a zero-weight node does not become an active SP region,
- but its local domain may still be a real explicit void in the CSF model,
- and that void must survive exact boundary-touching and deep nesting cases.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |

**Returns:** `Dict[int, List[ShapelyPolygon]]`

**Function/method calls visible in the code**

`_collect_children`, `_build_node_shapes`, `_polygon_parts_from_geometry`, `region.difference`, `children.get`, `_union_or_raise`

## exactly on the boundary.

### `_compute_effective_hole_points`

**Source lines:** `1036-1078`

```python
def _compute_effective_hole_pointsregion_polys: List[ShapelyPolygon], polygon_inputs: Dict[int, PolygonInput], local_domains: Dict[int, List[ShapelyPolygon]]
```

**Summary:** Compute robust hole seed points for explicit CSF voids.

**Docstring details**

```text
Policy:
- only zero-weight CSF nodes create global void candidates;
- interior rings of active regions are not promoted to global voids;
- @cell intrinsic inner loops remain local to the @cell geometry.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `region_polys` | `positional or keyword` | `List[ShapelyPolygon]` | `-` |
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |
| `local_domains` | `positional or keyword` | `Dict[int, List[ShapelyPolygon]]` | `-` |

**Returns:** `List[Tuple[float, float]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`unary_union`, `polygon_inputs.items`, `_union_or_raise`, `candidate_union.difference`, `_polygon_parts_from_geometry`, `enumerate`, `void_candidates.extend`, `part.representative_point`, `hole_points.append`, `local_domains.get`, `ValueError`, `float`

## CONNECTEDNESS POLICY USED ONLY BY THE BRIDGE

### `_geometry_is_connected`

**Source lines:** `1108-1130`

```python
def _geometry_is_connectedgeom: Geometry | CompoundGeometry, tol: float=1e-08
```

**Summary:** Return True when active regions are connected.

**Docstring details**

```text
Connectivity uses snapping only as a topological test.
The physical geometry passed to sectionproperties is not modified.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geom` | `positional or keyword` | `Geometry | CompoundGeometry` | `-` |
| `tol` | `positional or keyword` | `float` | `1e-08` |

**Returns:** `bool`

**Function/method calls visible in the code**

`_polygon_list_from_sectionproperties_geometry`, `unary_union`, `snap`

## Torsion carrier helpers

### `_make_torsion_carrier_inputs`

**Source lines:** `1138-1172`

```python
def _make_torsion_carrier_inputspolygon_inputs: Dict[int, PolygonInput]
```

**Summary:** Replace the normal CSF carrier ``w`` with the resolved shear carrier.

**Docstring details**

```text
This is the explicit carrier substitution used by the torsion-only run:

    E_SP := G_i / shear_w_i

No fallback is applied. If the sampled CSF model does not provide shear_w
for every polygon node, the torsion-carrier result is not computed.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |

**Returns:** `Dict[int, PolygonInput]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`polygon_inputs.items`, `ValueError`, `float`, `replace`

### `_build_meshed_geometry`

**Source lines:** `1175-1184`

```python
def _build_meshed_geometrypolygon_inputs: Dict[int, PolygonInput], mesh: float
```

**Summary:** Build the meshed sectionproperties geometry for a given carrier field.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |
| `mesh` | `positional or keyword` | `float` | `-` |

**Returns:** `Tuple[Geometry | CompoundGeometry, Dict[int, List[ShapelyPolygon]]]`

**Function/method calls visible in the code**

`_compute_node_local_domains`, `_build_sectionproperties_geometry`, `_apply_effective_hole_points`, `geom.create_mesh`

## Analysis helpers

### `_analyse_one_geometry`

**Source lines:** `1249-1299`

```python
def _analyse_one_geometryz: float, polygon_inputs: Dict[int, PolygonInput], mesh: float, plot: bool, warping: bool=True
```

**Summary:** Mesh, analyse, and print one station.

**Docstring details**

```text
Execution order matters:
1. compute local domains for all CSF nodes
2. build active SP geometry from positive-weight pieces only
3. inject hole seeds from actual voids, including zero-weight nodes
4. mesh
5. compute geometric properties
6. compute warping only if the final active geometry is connected according
   to the bridge policy implemented in ``_geometry_is_connected``
7. when warping is available, print both the native SP ``e.j`` result and
   the CSF torsion-carrier result obtained by the dedicated ``E_SP := G_i``
   run
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `z` | `positional or keyword` | `float` | `-` |
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |
| `mesh` | `positional or keyword` | `float` | `-` |
| `plot` | `positional or keyword` | `bool` | `-` |
| `warping` | `positional or keyword` | `bool` | `True` |

**Returns:** `None`

**Function/method calls visible in the code**

`_build_meshed_geometry`, `Section`, `sec.calculate_geometric_properties`, `print`, `sec.display_results`, `_geometry_is_connected`, `_print_torsion_results`, `geom.plot_geometry`, `sec.plot_mesh`, `plt.show`, `sec.calculate_warping_properties`

## CLI

### `main`

**Source lines:** `1307-1386`

```python
def main
```

**Summary:** Command-line entry point.

**Returns:** `None`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`argparse.ArgumentParser`, `ap.add_argument`, `ap.parse_args`, `args.path.read_text`, `_read_geometry_export_blocks`, `_select_z_block`, `_rows_to_polygon_inputs`, `_analyse_one_geometry`, `_load_field_from_yaml`, `enumerate`, `SystemExit`, `_load_station_set`, `_polygon_inputs_from_field`, `float`, `print`

## may change without notice.

### `load_yaml`

**Source lines:** `1404-1426`

```python
def load_yamlpath: 'str | Path'
```

**Summary:** Load a CSF model from a YAML file and return the field object.

**Docstring details**

```text
This is a thin public wrapper around the internal YAML loader. The returned
object is a ``ContinuousSectionField`` instance that can be passed directly
to :func:`analyse`.

Parameters
----------
path:
    Path to the CSF YAML file (``str`` or :class:`pathlib.Path`).

Returns
-------
ContinuousSectionField
    The loaded CSF field, ready for sampling.

Raises
------
SystemExit
    If the file cannot be read or the CSF model fails validation.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `path` | `positional or keyword` | `'str | Path'` | `-` |

**Returns:** `Any`

**Function/method calls visible in the code**

`_load_field_from_yaml`, `Path`

### `analyse`

**Source lines:** `1429-1491`

```python
def analysefield: Any, z: float, mesh: float=1.0, warping: bool=True
```

**Summary:** Analyse a CSF field at a given longitudinal position.

**Docstring details**

```text
Samples the CSF field at ``z``, builds the sectionproperties geometry,
meshes it, and runs the geometric analysis. Warping analysis is also
performed when the active geometry is connected.

The returned :class:`sectionproperties.analysis.Section` object exposes the
full sectionproperties API.

Torsion note
------------
``sec.get_ej()`` is the native sectionproperties result. It is an ``e.j``
result because sectionproperties weights composite torsion with the value
stored as ``elastic_modulus``.

To compute the CSF torsion-carrier result based on the resolved shear field,
use :func:`analyse_torsion_carrier`. That helper performs a dedicated
torsion-only run with:

    E_SP := G_i / shear_w_i

and returns the resulting sectionproperties ``e.j`` value as a CSF
torsion-carrier result.

Parameters
----------
field:
    A ``ContinuousSectionField`` instance, typically obtained from
    :func:`load_yaml` or constructed directly via the CSF Python API.
z:
    Longitudinal coordinate at which to sample the section.
mesh:
    Maximum triangular element area for the sectionproperties mesh.
    Smaller values give more accurate results at the cost of speed.
warping:
    If ``True`` (default), warping properties (native ``e.j``, shear centre,
    etc.) are computed when the geometry is connected. Set to ``False`` to
    skip the warping FEM.

Returns
-------
sectionproperties.analysis.Section
    A fully analysed Section object. Geometric properties are always
    available. Warping properties are available only when warping is enabled
    and the geometry is connected.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `mesh` | `positional or keyword` | `float` | `1.0` |
| `warping` | `positional or keyword` | `bool` | `True` |

**Returns:** `'Section'`

**Function/method calls visible in the code**

`_polygon_inputs_from_field`, `_build_meshed_geometry`, `Section`, `sec.calculate_geometric_properties`, `float`, `_geometry_is_connected`, `sec.calculate_warping_properties`, `print`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
