# API Reference - `csf_torsion_fem.py`

This document covers the top-level classes and functions defined in `src/csf/utils/csf_torsion_fem.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/utils/csf_torsion_fem.py`
- Output file: `docs/API/utils_csf_torsion_fem_api_en.md`
- Top-level function definitions found: `33`.
- Top-level classes found: `5`.
- Duplicate function names found: `0`.

## Module docstring

```text
csf_torsion_fem.py

Dedicated Saint-Venant torsion FEM tool for CSF YAML models.

Purpose
-------
This module loads a generic CSF YAML model, samples one or more z-stations,
builds the active 2D cross-section topology, meshes it automatically, assigns
the resolved CSF shear carrier G_i / shear_w_i to each material region, and
builds a reusable torsion FEM pipeline.  The CSF/topology/mesh/material layer is
independent from the selected torsion formulation.

It intentionally does not read CSV exports and does not use sectionproperties
for the torsion solve.  The only sectional result produced here is the FEM unit-twist torsional stiffness through a selectable formulation.

The first implemented formulation is:

    prandtl-dirichlet

which solves the Prandtl stress-function problem for simply connected/open
sections.  Other formulations can be added to the registry without changing
the CSF YAML loader, topology bridge, mesh generator, material mapping, CLI
station handling, or output layer.

Dependencies
------------
Required at runtime:
    pip install numpy scipy pyyaml shapely triangle scikit-fem csfpy

Notes
-----
- scikit-fem is used as the mesh container for the generated triangular mesh.
- The CSF-to-FEM pipeline is formulation-independent.
- Each torsion formulation is implemented as a registered solver function.
- The linear systems are assembled explicitly here to keep every formulation
  transparent and independent from sectionproperties.
- CSF geometry/material loading is done directly from YAML through CSFReader.
- Missing inputs are command-line parameters; no structural or material default
  is invented silently.
```

## Public API index

- `PolygonInput` - line 86
- `NodeShape` - line 100
- `MeshPayload` - line 108
- `TorsionResult` - line 120
- `SolverOutput` - line 701
- `def _format_text_blockheader: str, lines: List[str]` - line 146
- `def _format_reader_issuesissues: List[Any], header: str` - line 152
- `def load_yamlpath: str | Path` - line 171
- `def _load_station_setrun_config_path: Path, station_set_name: str` - line 201
- `def _parse_z_valuesargs: argparse.Namespace` - line 236
- `def _name_has_cell_tagname: str` - line 272
- `def _read_optional_shear_widx_polygon: int, poly: Any` - line 277
- `def polygon_inputs_from_fieldfield: Any, z: float` - line 297
- `def _make_polygoncoords: List[Tuple[float, float]], label: str` - line 336
- `def _split_cell_polygonvertices: List[Tuple[float, float]], label: str` - line 348
- `def _looks_like_slit_encoded_polygonvertices: List[Tuple[float, float]]` - line 379
- `def _collect_childrenpolygon_inputs: Dict[int, PolygonInput]` - line 386
- `def _union_or_raisepolys: List[ShapelyPolygon], label: str` - line 393
- `def _polygon_parts_from_geometrygeom: BaseGeometry, label: str` - line 400
- `def _build_node_shapespolygon_inputs: Dict[int, PolygonInput]` - line 421
- `def compute_node_local_domainspolygon_inputs: Dict[int, PolygonInput]` - line 450
- `def _add_ringvertices: List[Tuple[float, float]], vertex_map: Dict[Tuple[float, float], int], points: List[Tuple[float, float]], segments: List[Tuple[int, int]], precision: int` - line 471
- `def _active_regions_from_domainspolygon_inputs: Dict[int, PolygonInput], local_domains: Dict[int, List[ShapelyPolygon]], require_shear: bool` - line 495
- `def build_meshpolygon_inputs: Dict[int, PolygonInput], mesh_max_area: float, min_angle: float, boundary_precision: int, require_shear: bool=True` - line 534
- `def mesh_diagnosticsmesh_payload: MeshPayload` - line 618
- `def print_mesh_diagnosticsmesh_payload: MeshPayload, *, z: float, mesh_max_area: float, min_angle: float` - line 662
- `def register_formulationname: str` - line 714
- `def available_formulations` - line 728
- `def solve_torsionmesh_payload: MeshPayload, formulation: str, *, pin_node: int` - line 733
- `def _triangle_geometrypoints: np.ndarray, tri: np.ndarray` - line 755
- `def _boundary_nodes_from_trianglestriangles: np.ndarray` - line 779
- `def solve_prandtl_dirichletmesh_payload: MeshPayload, pin_node: int=0` - line 802
- `def analyse_field_at_zfield: Any, z: float, mesh_max_area: float, min_angle: float, boundary_precision: int, pin_node: int, formulation: str, debug: bool=False` - line 894
- `def _result_to_rowresult: TorsionResult` - line 934
- `def _print_tableresults: Sequence[TorsionResult]` - line 949
- `def _write_jsonpath: Path, results: Sequence[TorsionResult]` - line 963
- `def _build_arg_parser` - line 968
- `def mainargv: Optional[Sequence[str]]=None` - line 1042

## API details

## Classes

### `PolygonInput`

**Source lines:** `86-96`

**Decorators**

- `dataclass(frozen=True)`

```python
class PolygonInput
```

**Summary:** Sampled CSF polygon payload used by this torsion FEM backend.

### `NodeShape`

**Source lines:** `100-104`

**Decorators**

- `dataclass(frozen=True)`

```python
class NodeShape
```

**Summary:** Cached geometric payload for one CSF polygon node.

### `MeshPayload`

**Source lines:** `108-116`

**Decorators**

- `dataclass(frozen=True)`

```python
class MeshPayload
```

**Summary:** Triangular mesh and per-element shear carrier.

### `TorsionResult`

**Source lines:** `120-138`

**Decorators**

- `dataclass(frozen=True)`

```python
class TorsionResult
```

**Summary:** Result for one sampled station.

**Methods visible in the code**

- `reduction_ratio` - line 134

#### Method details

##### `TorsionResult.reduction_ratio`

**Source lines:** `134-138`

**Decorators**

- `property`

```python
def reduction_ratioself
```

**Summary:** Return GJ_fem / integral(G*r^2 dA).

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`float`

### `SolverOutput`

**Source lines:** `701-707`

**Decorators**

- `dataclass(frozen=True)`

```python
class SolverOutput
```

**Summary:** Raw output returned by one torsion formulation backend.

## Functions

## CSF YAML loading

### `_format_text_block`

**Source lines:** `146-149`

```python
def _format_text_blockheader: str, lines: List[str]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `header` | `positional or keyword` | `str` | `-` |
| `lines` | `positional or keyword` | `List[str]` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`out.extend`, `join`, `str`

### `_format_reader_issues`

**Source lines:** `152-168`

```python
def _format_reader_issuesissues: List[Any], header: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `issues` | `positional or keyword` | `List[Any]` | `-` |
| `header` | `positional or keyword` | `str` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`join`, `str`, `getattr`, `lines.append`

### `load_yaml`

**Source lines:** `171-198`

```python
def load_yamlpath: str | Path
```

**Summary:** Load a CSF YAML model and return the ContinuousSectionField object.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `path` | `positional or keyword` | `str | Path` | `-` |

**Returns:** `Any`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`Path`, `validate_text`, `list`, `yaml_path.read_text`, `SystemExit`, `read_file`, `str`, `_format_text_block`, `getattr`, `CSFReader`, `_format_reader_issues`

## Top-level functions

### `_load_station_set`

**Source lines:** `201-233`

```python
def _load_station_setrun_config_path: Path, station_set_name: str
```

**Summary:** Load a station set from a YAML run-config/action file.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `run_config_path` | `positional or keyword` | `Path` | `-` |
| `station_set_name` | `positional or keyword` | `str` | `-` |

**Returns:** `List[float]`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`data.get`, `enumerate`, `yaml.safe_load`, `isinstance`, `SystemExit`, `out.append`, `run_config_path.read_text`, `type`, `float`, `sorted`, `station_sets.keys`

### `_parse_z_values`

**Source lines:** `236-264`

```python
def _parse_z_valuesargs: argparse.Namespace
```

**Summary:** Resolve z-stations explicitly from CLI arguments.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `args` | `positional or keyword` | `argparse.Namespace` | `-` |

**Returns:** `List[float]`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`set`, `values.extend`, `args.z_list.split`, `SystemExit`, `token.strip`, `_load_station_set`, `seen.add`, `unique.append`, `float`, `values.append`, `Path`

### `_make_polygon`

**Source lines:** `336-345`

```python
def _make_polygoncoords: List[Tuple[float, float]], label: str
```

**Summary:** Build a shapely polygon without silently repairing invalid geometry.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `coords` | `positional or keyword` | `List[Tuple[float, float]]` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `ShapelyPolygon`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ShapelyPolygon`, `ValueError`

### `_split_cell_polygon`

**Source lines:** `348-376`

```python
def _split_cell_polygonvertices: List[Tuple[float, float]], label: str
```

**Summary:** Split a slit-encoded @cell/@closed polygon into outer and inner loops.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `vertices` | `positional or keyword` | `List[Tuple[float, float]]` | `-` |
| `label` | `positional or keyword` | `str` | `-` |

**Returns:** `Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`range`, `_make_polygon`, `len`, `ValueError`, `abs`

### `_looks_like_slit_encoded_polygon`

**Source lines:** `379-383`

```python
def _looks_like_slit_encoded_polygonvertices: List[Tuple[float, float]]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `vertices` | `positional or keyword` | `List[Tuple[float, float]]` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`any`, `len`, `range`

### `_collect_children`

**Source lines:** `386-390`

```python
def _collect_childrenpolygon_inputs: Dict[int, PolygonInput]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |

**Returns:** `Dict[Optional[int], List[int]]`

**Function/method calls visible in the code**

`polygon_inputs.items`, `append`, `children.setdefault`

### `_union_or_raise`

**Source lines:** `393-397`

```python
def _union_or_raisepolys: List[ShapelyPolygon], label: str
```

**Summary:** Docstring absent.

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

**Source lines:** `400-418`

```python
def _polygon_parts_from_geometrygeom: BaseGeometry, label: str
```

**Summary:** Extract polygonal area parts and ignore lower-dimensional leftovers.

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

### `_build_node_shapes`

**Source lines:** `421-447`

```python
def _build_node_shapespolygon_inputs: Dict[int, PolygonInput]
```

**Summary:** Build support regions and parent cutout envelopes for all CSF nodes.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |

**Returns:** `Dict[int, NodeShape]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`polygon_inputs.items`, `_looks_like_slit_encoded_polygon`, `_make_polygon`, `NodeShape`, `_split_cell_polygon`, `ShapelyPolygon`, `ValueError`, `list`

### `compute_node_local_domains`

**Source lines:** `450-463`

```python
def compute_node_local_domainspolygon_inputs: Dict[int, PolygonInput]
```

**Summary:** Compute each node local domain as support minus direct child envelopes.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |

**Returns:** `Dict[int, List[ShapelyPolygon]]`

**Function/method calls visible in the code**

`_collect_children`, `_build_node_shapes`, `_polygon_parts_from_geometry`, `region.difference`, `children.get`, `_union_or_raise`

### `build_mesh`

**Source lines:** `534-608`

```python
def build_meshpolygon_inputs: Dict[int, PolygonInput], mesh_max_area: float, min_angle: float, boundary_precision: int, require_shear: bool=True
```

**Summary:** Build a constrained triangular mesh and return a scikit-fem MeshTri payload.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |
| `mesh_max_area` | `positional or keyword` | `float` | `-` |
| `min_angle` | `positional or keyword` | `float` | `-` |
| `boundary_precision` | `positional or keyword` | `int` | `-` |
| `require_shear` | `positional or keyword` | `bool` | `True` |

**Returns:** `MeshPayload`

**Returned dictionary keys visible in the code**

`vertices`, `segments`, `regions`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`compute_node_local_domains`, `_active_regions_from_domains`, `triangle_lib.triangulate`, `np.asarray`, `reshape`, `astype`, `np.any`, `MeshTri`, `MeshPayload`, `SystemExit`, `_add_ring`, `poly.representative_point`, `tri_regions.append`, `sorted`, `np.ascontiguousarray`, `list`, `representative_point`, `holes.append`, `np.rint`, `G_by_region.get`, `np.isfinite`, `set`, `float`, `int`, `ShapelyPolygon`

### `print_mesh_diagnostics`

**Source lines:** `662-692`

```python
def print_mesh_diagnosticsmesh_payload: MeshPayload, *, z: float, mesh_max_area: float, min_angle: float
```

**Summary:** Print human-readable diagnostics before solving.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `mesh_payload` | `positional or keyword` | `MeshPayload` | `-` |
| `z` | `keyword-only` | `float` | `-` |
| `mesh_max_area` | `keyword-only` | `float` | `-` |
| `min_angle` | `keyword-only` | `float` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`mesh_diagnostics`, `print`, `get`

### `analyse_field_at_z`

**Source lines:** `894-926`

```python
def analyse_field_at_zfield: Any, z: float, mesh_max_area: float, min_angle: float, boundary_precision: int, pin_node: int, formulation: str, debug: bool=False
```

**Summary:** Run the complete CSF YAML -> mesh -> selected torsion FEM pipeline for one station.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `mesh_max_area` | `positional or keyword` | `float` | `-` |
| `min_angle` | `positional or keyword` | `float` | `-` |
| `boundary_precision` | `positional or keyword` | `int` | `-` |
| `pin_node` | `positional or keyword` | `int` | `-` |
| `formulation` | `positional or keyword` | `str` | `-` |
| `debug` | `positional or keyword` | `bool` | `False` |

**Returns:** `TorsionResult`

**Function/method calls visible in the code**

`polygon_inputs_from_field`, `build_mesh`, `solve_torsion`, `TorsionResult`, `float`, `print_mesh_diagnostics`, `int`, `str`

### `main`

**Source lines:** `1042-1065`

```python
def mainargv: Optional[Sequence[str]]=None
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `argv` | `positional or keyword` | `Optional[Sequence[str]]` | `None` |

**Returns:** `int`

**Function/method calls visible in the code**

`parse_args`, `_parse_z_values`, `load_yaml`, `_print_table`, `analyse_field_at_z`, `results.append`, `_write_json`, `print`, `_build_arg_parser`, `float`, `int`, `str`, `bool`

## CSF sampled polygons and topology

### `_name_has_cell_tag`

**Source lines:** `272-274`

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

### `_read_optional_shear_w`

**Source lines:** `277-294`

```python
def _read_optional_shear_widx_polygon: int, poly: Any
```

**Summary:** Read the sampled CSF shear carrier if it is explicitly exposed.

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

### `polygon_inputs_from_field`

**Source lines:** `297-333`

```python
def polygon_inputs_from_fieldfield: Any, z: float
```

**Summary:** Sample a CSF field and return topology-aware polygon inputs.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `Dict[int, PolygonInput]`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`field.section`, `field.build_direct_children_map`, `children_map.items`, `enumerate`, `float`, `str`, `_read_optional_shear_w`, `PolygonInput`, `hasattr`, `SystemExit`, `getattr`, `parent_of.get`, `_name_has_cell_tag`

## Triangle mesh generation

### `_add_ring`

**Source lines:** `471-492`

```python
def _add_ringvertices: List[Tuple[float, float]], vertex_map: Dict[Tuple[float, float], int], points: List[Tuple[float, float]], segments: List[Tuple[int, int]], precision: int
```

**Summary:** Append a polygon ring to the global PSLG vertex/segment lists.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `vertices` | `positional or keyword` | `List[Tuple[float, float]]` | `-` |
| `vertex_map` | `positional or keyword` | `Dict[Tuple[float, float], int]` | `-` |
| `points` | `positional or keyword` | `List[Tuple[float, float]]` | `-` |
| `segments` | `positional or keyword` | `List[Tuple[int, int]]` | `-` |
| `precision` | `positional or keyword` | `int` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`list`, `enumerate`, `len`, `ValueError`, `vertex_map.get`, `ids.append`, `round`, `points.append`, `segments.append`, `float`

### `_active_regions_from_domains`

**Source lines:** `495-531`

```python
def _active_regions_from_domainspolygon_inputs: Dict[int, PolygonInput], local_domains: Dict[int, List[ShapelyPolygon]], require_shear: bool
```

**Summary:** Return active polygon parts with positive shear carrier.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon_inputs` | `positional or keyword` | `Dict[int, PolygonInput]` | `-` |
| `local_domains` | `positional or keyword` | `Dict[int, List[ShapelyPolygon]]` | `-` |
| `require_shear` | `positional or keyword` | `bool` | `-` |

**Returns:** `Tuple[List[Tuple[int, ShapelyPolygon, float, str]], Dict[int, str]]`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`polygon_inputs.items`, `float`, `enumerate`, `SystemExit`, `local_domains.get`, `regions.append`

## Debug diagnostics

### `mesh_diagnostics`

**Source lines:** `618-659`

```python
def mesh_diagnosticsmesh_payload: MeshPayload
```

**Summary:** Return explicit mesh diagnostics used to validate a torsion run.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `mesh_payload` | `positional or keyword` | `MeshPayload` | `-` |

**Returns:** `Dict[str, Any]`

**Returned dictionary keys visible in the code**

`nodes`, `elements`, `boundary_nodes`, `free_nodes`, `bbox`, `element_area_min`, `element_area_max`, `element_area_mean`, `G_min`, `G_max`, `regions`, `region_counts`, `region_names`

**Function/method calls visible in the code**

`_boundary_nodes_from_triangles`, `np.zeros`, `int`, `np.asarray`, `sorted`, `np.count_nonzero`, `np.min`, `np.max`, `float`, `_triangle_geometry`, `elem_areas.append`, `set`, `str`, `np.mean`, `mesh_payload.region_names.items`, `mesh_payload.element_region.tolist`

## Torsion FEM formulation registry

### `register_formulation`

**Source lines:** `714-725`

```python
def register_formulationname: str
```

**Summary:** Register a torsion formulation by CLI/API name.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `name` | `positional or keyword` | `str` | `-` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`, `isinstance`

### `available_formulations`

**Source lines:** `728-730`

```python
def available_formulations
```

**Summary:** Return the registered torsion formulation names.

**Returns:** `List[str]`

**Function/method calls visible in the code**

`sorted`, `TORSION_FORMULATIONS.keys`

### `solve_torsion`

**Source lines:** `733-747`

```python
def solve_torsionmesh_payload: MeshPayload, formulation: str, *, pin_node: int
```

**Summary:** Dispatch the torsion solve to a registered formulation backend.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `mesh_payload` | `positional or keyword` | `MeshPayload` | `-` |
| `formulation` | `positional or keyword` | `str` | `-` |
| `pin_node` | `keyword-only` | `int` | `-` |

**Returns:** `SolverOutput`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`solver`, `SystemExit`, `available_formulations`

## Shared element helpers

### `_triangle_geometry`

**Source lines:** `755-776`

```python
def _triangle_geometrypoints: np.ndarray, tri: np.ndarray
```

**Summary:** Return area, shape-function gradients, centroid and centroid tuple.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `positional or keyword` | `np.ndarray` | `-` |
| `tri` | `positional or keyword` | `np.ndarray` | `-` |

**Returns:** `Tuple[float, np.ndarray, np.ndarray, Tuple[float, float]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`abs`, `np.mean`, `ValueError`, `np.array`, `float`

## and gradients consistent with the signed determinant.

### `_boundary_nodes_from_triangles`

**Source lines:** `779-798`

```python
def _boundary_nodes_from_trianglestriangles: np.ndarray
```

**Summary:** Return the sorted node ids lying on the exterior mesh boundary.

**Docstring details**

```text
Boundary edges are triangle edges that occur exactly once in the element
connectivity.  These nodes receive the Prandtl stress-function Dirichlet
condition phi = 0 for simply connected Saint-Venant torsion.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `triangles` | `positional or keyword` | `np.ndarray` | `-` |

**Returns:** `np.ndarray`

**Function/method calls visible in the code**

`sorted`, `np.asarray`, `int`, `edge_count.get`, `edge_count.items`

### `solve_prandtl_dirichlet`

**Source lines:** `802-891`

**Decorators**

- `register_formulation('prandtl-dirichlet')`

```python
def solve_prandtl_dirichletmesh_payload: MeshPayload, pin_node: int=0
```

**Summary:** Solve Saint-Venant torsion with the Prandtl stress function.

**Docstring details**

```text
This replaces the earlier warping-field prototype.  The previous prototype
could collapse to the polar stiffness integral GIp for coarse/symmetric
meshes; that is not an acceptable torsion result for general sections.

Formulation used here for unit twist theta = 1:

    div((1 / G) grad(phi)) = -2
    phi = 0 on the external boundary

Weak form:

    integral_A (1 / G) grad(phi) . grad(v) dA = integral_A 2 v dA

Post-processing:

    GJ = 2 * integral_A phi dA

Scope:
- correct target for simply connected solid/open sections;
- conservative first implementation for holes because all boundary
  components are set to phi = 0.  General multiply-connected closed cells
  require one unknown constant per inner boundary plus compatibility
  constraints, and should not be silently hidden in this module.

The pin_node argument is kept for CLI compatibility but is not used by this
Dirichlet Prandtl solve.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `mesh_payload` | `positional or keyword` | `MeshPayload` | `-` |
| `pin_node` | `positional or keyword` | `int` | `0` |

**Returns:** `SolverOutput`

**Raises visible in the code**

- `SystemExit`

**Function/method calls visible in the code**

`register_formulation`, `np.zeros`, `enumerate`, `tocsr`, `_boundary_nodes_from_triangles`, `np.ones`, `spsolve`, `SolverOutput`, `float`, `_triangle_geometry`, `np.full`, `np.any`, `SystemExit`, `coo_matrix`, `np.mean`, `np.outer`, `int`, `rows.append`, `cols.append`, `data.append`

## Output helpers and CLI

### `_result_to_row`

**Source lines:** `934-946`

```python
def _result_to_rowresult: TorsionResult
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `result` | `positional or keyword` | `TorsionResult` | `-` |

**Returns:** `Dict[str, Any]`

**Returned dictionary keys visible in the code**

`z`, `GJ_fem`, `GIp_mesh`, `GJ_over_GIp`, `area_mesh`, `nodes`, `elements`, `mesh_max_area`, `min_angle`, `formulation`

### `_print_table`

**Source lines:** `949-960`

```python
def _print_tableresults: Sequence[TorsionResult]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `results` | `positional or keyword` | `Sequence[TorsionResult]` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`print`, `len`

### `_write_json`

**Source lines:** `963-965`

```python
def _write_jsonpath: Path, results: Sequence[TorsionResult]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `path` | `positional or keyword` | `Path` | `-` |
| `results` | `positional or keyword` | `Sequence[TorsionResult]` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`path.write_text`, `_result_to_row`, `json.dumps`

### `_build_arg_parser`

**Source lines:** `968-1039`

```python
def _build_arg_parser
```

**Summary:** Docstring absent.

**Returns:** `argparse.ArgumentParser`

**Function/method calls visible in the code**

`argparse.ArgumentParser`, `ap.add_argument`, `available_formulations`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
