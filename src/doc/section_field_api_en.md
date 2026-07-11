# API Reference - `section_field.py`

This document covers the top-level classes and functions defined in `src/csf/section_field.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/section_field.py`
- Output file: `src/doc/section_field_api_en.md`
- Top-level function definitions found: `91`.
- Top-level classes found: `0`.
- Duplicate function names found:
  - `execute_string_to_float` at lines 1801, 2043. The later definition is the active binding at import time.

## Module docstring

```text
Assumptions:
- Two endpoint sections exist at z0 and z1.
- Same number of polygons in start/end.
- For each polygon: same number of vertices in start/end.
- Vertex ordering is already consistent (your matching is given/assumed).
- Polygons are simple enough for shoelace formulas (no self-intersections).
```

## Public API index

- `def analyse_polygon_jourawski_shear_stresssection_field, z: float, Tx: float, Ty: float, *, num_sudx: int=100, num_sudy: int=100, debug: bool=False` - line 109
- `def _section_active_bboxsection: Section` - line 346
- `def _jourawski_global_axis_scan*, original_section: Section, transformed_section: Section, axis: str, coord_min: float, coord_max: float, num_subdivisions: int, Cx: float, Cy: float, dbx: float, dby: float` - line 365
- `def _jourawski_value_at_coord*, original_section: Section, transformed_section: Section, axis: str, coord: float, Cx: float, Cy: float, dbx: float, dby: float` - line 411
- `def _section_active_cut_width_and_polygons*, section: Section, axis: str, coord: float` - line 486
- `def _group_scan_values_by_polygon*, scan_values: list[dict[str, object]], polygon_count: int` - line 559
- `def _jourawski_polygon_shear_weightabspoly: Polygon` - line 599
- `def _jourawski_polygon_is_active_for_bpoly: Polygon` - line 614
- `def _jourawski_normalized_sectionsection: Section` - line 622
- `def _jourawski_reference_weightabssection: Section` - line 647
- `def _section_partial_first_moments*, section: Section, axis: str, coord: float, Cx: float, Cy: float` - line 656
- `def _clip_polygon_half_plane*, poly: Polygon, axis: str, coord: float` - line 692
- `def _interpolate_point_on_segmentp1: Pt, p2: Pt, t: float` - line 731
- `def _polygon_area_from_pointspoints: list[Pt]` - line 738
- `def _cut_edge_tc1: float, c2: float, coord: float` - line 753
- `def _polygon_line_segments*, poly: Polygon, axis: str, coord: float` - line 767
- `def _unique_sortedvalues: list[float]` - line 808
- `def _mean_scan_tauvalues: list[dict[str, object]]` - line 820
- `def _empty_scan_value` - line 827
- `def _min_scan_valuevalues: list[dict[str, object]]` - line 849
- `def _max_scan_valuevalues: list[dict[str, object]]` - line 855
- `def analyse_polygon_navier_stresssection_field, z: float, N: float, Mx: float, My: float` - line 866
- `def get_lobatto_intervalsz_min: float, z_max: float, n_intervals: int` - line 960
- `def compute_lobatto_integration_pointsz_min: float, z_max: float, n_points: int=5, L: float=None` - line 978
- `def _compute_station_datafield: Any, z_values: Sequence[float]` - line 1045
- `def _parse_optional_floatvalue: Any` - line 1123
- `def write_sap2000_template_packfield: Any, n_intervals: int=20, template_filename: str='export_template_pack.txt', *, mode: Literal['BOTH', 'CENTROIDAL_LINE', 'REFERENCE_LINE']='BOTH', section_prefix: str='SEC', material_name: str='S355', E_ref=None, nu=None, include_plot: bool=True, plot_filename: str='section_variation.png', show_plot: bool=True, z_values: Optional[List[float]]=None, plot_n: int=100, float_fmt: str='.9g'` - line 1127
- `def write_sap2000_geometry*args: Any, **kwargs: Any` - line 1486
- `def _csf__is_finite_numberx: Any` - line 1501
- `def _csf__ensure_parent_dir_existspath: str` - line 1510
- `def _csf__atomic_write_textpath: str, text: str` - line 1525
- `def _csf__section_to_Sz_dictsection_obj, nodesection: str` - line 1537
- `def _yaml_scalarv` - line 1601
- `def _simple_yaml_dumpdata, indent: int=0` - line 1625
- `def safe_evaluate_weight_zrelativeformula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float, print=True` - line 1651
- `def print_evaluation_reportvalue: float, report: dict` - line 1753
- `def execute_string_to_floatcode_string, x_value` - line 1801
- `def evaluate_shear_weight_formulaformula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, zt: float, w: float` - line 1816
- `def evaluate_weight_formulaformula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, zt: float` - line 1939
- `def execute_string_to_floatcode_string, z_val, t_val` - line 2043
- `def evaluate_weight_formula_zrelativeformula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float` - line 2075
- `def section_geometrysection: Section, fmt='.8f'` - line 2136
- `def section_print_analysisfull_analysis, fmt='.8f'` - line 2157
- `def section_full_analysis_keys` - line 2213
- `def write_opensees_geometryfield, n_points: int, E_ref=None, nu=None, filename: str='geometry.tcl'` - line 2240
- `def lookup_homogenized_elastic_modulusfilename: str, zt: float` - line 2483
- `def _resolve_eps_aobj: Any` - line 2606
- `def _resolve_eps_kobj: Any` - line 2610
- `def _poly_signed_area_centroidpts: Any, eps_a: float` - line 2618
- `def _principal_inertiasix: float, iy: float, ixy: float` - line 2661
- `def _roark_torsion_recta: float, b: float` - line 2675
- `def _equiv_rectangle_dimsA: float, i_min: float, eps_k: float` - line 2701
- `def compute_saint_venant_Jv2poly_input: Any` - line 2726
- `def calculate_t_eqpoints` - line 3080
- `def compute_saint_venant_J_cellsection: 'Section'` - line 3213
- `def compute_saint_venant_J_wallsection: 'Section'` - line 3729
- `def _poly_vertices_xypoly: Any` - line 3938
- `def _bbox_xyverts: Sequence[PointXY]` - line 3949
- `def _auto_grid_h_from_bboxverts: Sequence[PointXY], auto_n: int` - line 3958
- `def _point_on_segment_sqpx: float, py: float, ax: float, ay: float, bx: float, by: float, eps_l: float` - line 3975
- `def _point_in_poly_inclusivepx: float, py: float, verts: Sequence[PointXY], eps_l: float` - line 4015
- `def _build_inside_maskverts: Sequence[PointXY], xs: np.ndarray, ys: np.ndarray, eps_l: float` - line 4047
- `def _solve_poisson_sormask: np.ndarray, h: float, *, max_iter: int, tol: float, omega: float` - line 4068
- `def _sqx: float` - line 4120
- `def _is_near_zerox: float, eps: float` - line 4124
- `def _signed_area_centroid_xyverts: Sequence[tuple[float, float]]` - line 4134
- `def _poly_signed_area_centroid_xyverts: Sequence[PointXY]` - line 4168
- `def export_to_opensees_tclfield, K_12x12, filename='csf_model.tcl'` - line 4172
- `def assemble_element_stiffness_matrixfield: ContinuousSectionField, E_ref: float=1.0, nu: float=0.3, n_gauss: int=5` - line 4208
- `def polygon_inertia_about_originpoly: Polygon` - line 4308
- `def volume_polygon_list_report_datafield: 'ContinuousSectionField', z1: float, z2: float, n_points: int=20, *, do_debug_check: bool=False, debug_tol: float=1e-09` - line 4348
- `def volume_polygon_list_reportfield: ContinuousSectionField, z1: float, z2: float, *, n_points: int=20, outputs: list[Any] | None=None, fmt_display: str='0.6f', w_tol: float=0.0, do_debug_check: bool=False, debug_tol: float=1e-09` - line 4469
- `def emit_volume_polygon_list_reportreport: Dict[str, Any], *, outputs: List[Any] | None=None, fmt_display: str='0.6f', w_tol: float=0.0` - line 4519
- `def integrate_volumefield: 'ContinuousSectionField', z0: float, z1: float, n_points: int=20, *, idx: int | None=None` - line 4704
- `def section_full_analysissection: Section, compute_vroark=True` - line 4814
- `def polygon_statical_momentpoly: Polygon, y_axis: float` - line 4906
- `def section_statical_moment_partialsection: Section, y_cut: float, reference_axis: float | None=None` - line 4921
- `def section_derived_propertiesprops: Dict[str, float]` - line 5007
- `def section_stiffness_matrixsection: Section, E_ref: float=1.0` - line 5079
- `def _segments_intersectp1, p2, p3, p4` - line 5144
- `def polygon_has_self_intersectionspoly: Polygon` - line 5195
- `def get_points_distancepolygon: Polygon, i: int, j: int` - line 5297
- `def get_edge_lengthpolygon: Polygon, edge_idx: int` - line 5326
- `def list_polygons_with_contentscsf: ContinuousSectionField, z: float` - line 5345
- `def polygon_surface_w1_inners0self: Any, z: float` - line 5476
- `def polygon_surface_w1_inners0_singleself: ContinuousSectionField, z: float, idx: int` - line 5683
- `def export_polygon_vertices_csv_filesection: Section=None, field: ContinuousSectionField=None, zpos: float=None, exp_filename: str='csv_export.txt', z_values: Optional[List[float]]=None, fmt: str='{:.16g}'` - line 5897
- `def export_polygon_vertices_csvsection: Section=None, field: ContinuousSectionField=None, zpos: float=None, put=print, fmt='{:.16g}'` - line 5955
- `def section_propertiessection: Section` - line 6156
- `def _polygon_signed_area_and_centroidpoly: Polygon` - line 6263
- `def polygon_area_centroidpoly: Polygon` - line 6273

## API details

## Functions

## of each polygon (polygon area minus its immediate children areas).

### `analyse_polygon_jourawski_shear_stress`

**Source lines:** `109-344`

```python
def analyse_polygon_jourawski_shear_stresssection_field, z: float, Tx: float, Ty: float, *, num_sudx: int=100, num_sudy: int=100, debug: bool=False
```

**Summary:** Compute polygon-wise Jourawski shear-stress envelopes from global section scans.

**Docstring details**

```text
Conventions
-----------
- Tx is the shear component associated with My.
- Ty is the shear component associated with Mx.
- tau_x is evaluated from vertical cuts x = constant.
- tau_y is evaluated from horizontal cuts y = constant.

Scan rule
---------
The section is scanned once along x and once along y over the active-section
bounding box:

    deltaX = (xmax - xmin) / num_sudx
    deltaY = (ymax - ymin) / num_sudy

The sampled coordinates are cell centres, not extrema.

For each cut, Jourawski returns one mean shear stress over the full active
intersection length b. That line-average value is then redistributed among
the crossed polygon segments using their sampled shear carrier
``shear_weightabs`` and their actual segment length on the cut.

For one cut:
    tau_i = tau_ref * b_total * G_i / sum(G_j * b_j)

where G_i is the polygon ``shear_weightabs`` and b_i is the segment length
of the same cut inside polygon i. This preserves the cut resultant:
    sum(tau_i * b_i) = tau_ref * b_total.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `Tx` | `positional or keyword` | `float` | `-` |
| `Ty` | `positional or keyword` | `float` | `-` |
| `num_sudx` | `keyword-only` | `int` | `100` |
| `num_sudy` | `keyword-only` | `int` | `100` |
| `debug` | `keyword-only` | `bool` | `False` |

**Returns:** `list[dict[str, object]]`

**Returned dictionary keys visible in the code**

`idx`, `name`, `weight`, `weight_ref`, `weight_norm`, `tau_x_min`, `x_tau_x_min`, `y_tau_x_min`, `tau_x_max`, `x_tau_x_max`, `y_tau_x_max`, `tau_y_min`, `x_tau_y_min`, `y_tau_y_min`, `tau_y_max`, `x_tau_y_max`, `y_tau_y_max`, `coord_tau_y_max`, `tau_reference_y_max`, `b_weighted_y_max`, `Sx_part_y_max`, `Sy_part_y_max`, `tau_x_mean`, `tau_y_mean`, `scan_count_x`, `scan_count_y`, `grid_x`, `grid_y`, `converged_x`, `converged_y`, `relative_change_x`, `relative_change_y`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`int`, `section_field.section`, `_jourawski_normalized_section`, `section_properties`, `float`, `_section_active_bbox`, `_jourawski_global_axis_scan`, `_group_scan_values_by_polygon`, `enumerate`, `ValueError`, `abs`, `print`, `str`, `_min_scan_value`, `_max_scan_value`, `rows.append`, `len`, `_mean_scan_tau`, `bool`

## Top-level functions

### `_section_active_bbox`

**Source lines:** `346-363`

```python
def _section_active_bboxsection: Section
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `Section` | `-` |

**Returns:** `tuple[float, float, float, float]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`, `min`, `max`, `_jourawski_polygon_is_active_for_b`, `xs.append`, `ys.append`, `float`

### `_jourawski_global_axis_scan`

**Source lines:** `365-408`

```python
def _jourawski_global_axis_scan*, original_section: Section, transformed_section: Section, axis: str, coord_min: float, coord_max: float, num_subdivisions: int, Cx: float, Cy: float, dbx: float, dby: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `original_section` | `keyword-only` | `Section` | `-` |
| `transformed_section` | `keyword-only` | `Section` | `-` |
| `axis` | `keyword-only` | `str` | `-` |
| `coord_min` | `keyword-only` | `float` | `-` |
| `coord_max` | `keyword-only` | `float` | `-` |
| `num_subdivisions` | `keyword-only` | `int` | `-` |
| `Cx` | `keyword-only` | `float` | `-` |
| `Cy` | `keyword-only` | `float` | `-` |
| `dbx` | `keyword-only` | `float` | `-` |
| `dby` | `keyword-only` | `float` | `-` |

**Returns:** `list[dict[str, object]]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`int`, `range`, `ValueError`, `float`, `abs`, `_jourawski_value_at_coord`, `out.append`

### `_jourawski_value_at_coord`

**Source lines:** `411-482`

```python
def _jourawski_value_at_coord*, original_section: Section, transformed_section: Section, axis: str, coord: float, Cx: float, Cy: float, dbx: float, dby: float
```

**Summary:** Compute the mean Jourawski stress for one global cut.

**Docstring details**

```text
The stress value is global for the full active cut width b_total.
The localization is per intersected polygon segment and is stored in
cut_segments. The grouped polygon rows then receive the same tau but their
own segment midpoint coordinates.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `original_section` | `keyword-only` | `Section` | `-` |
| `transformed_section` | `keyword-only` | `Section` | `-` |
| `axis` | `keyword-only` | `str` | `-` |
| `coord` | `keyword-only` | `float` | `-` |
| `Cx` | `keyword-only` | `float` | `-` |
| `Cy` | `keyword-only` | `float` | `-` |
| `dbx` | `keyword-only` | `float` | `-` |
| `dby` | `keyword-only` | `float` | `-` |

**Returns:** `dict[str, object] | None`

**Returned dictionary keys visible in the code**

`tau`, `x`, `y`, `coord`, `axis`, `tau_reference`, `b_weighted`, `Sx_part`, `Sy_part`, `cut_segments`, `polygon_indices`

**Function/method calls visible in the code**

`_section_active_cut_width_and_polygons`, `_section_partial_first_moments`, `abs`, `float`, `dict`, `localized_segments.append`, `str`, `tuple`, `int`

### `_section_active_cut_width_and_polygons`

**Source lines:** `486-556`

```python
def _section_active_cut_width_and_polygons*, section: Section, axis: str, coord: float
```

**Summary:** Return the total active cut width and one localization record per polygon.

**Docstring details**

```text
For axis == "y", the cut is horizontal Y = coord. The segment endpoints are
x-like values, and the marker is placed at their length-weighted midpoint.

For axis == "x", the cut is vertical X = coord. The segment endpoints are
y-like values, and the marker is placed at their length-weighted midpoint.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `keyword-only` | `Section` | `-` |
| `axis` | `keyword-only` | `str` | `-` |
| `coord` | `keyword-only` | `float` | `-` |

**Returns:** `tuple[float, list[dict[str, object]]]`

**Returned dictionary keys visible in the code**

`polygon_idx`, `length`, `shear_weightabs`, `x`, `y`, `segment_x0`, `segment_y0`, `segment_x1`, `segment_y1`, `segments_other`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`enumerate`, `_polygon_line_segments`, `sum`, `_jourawski_polygon_shear_weightabs`, `cut_segments.append`, `float`, `_jourawski_polygon_is_active_for_b`, `abs`, `min`, `max`, `ValueError`, `int`, `tuple`

### `_group_scan_values_by_polygon`

**Source lines:** `559-596`

```python
def _group_scan_values_by_polygon*, scan_values: list[dict[str, object]], polygon_count: int
```

**Summary:** Assign global cut values to crossed polygons with per-polygon localization.

**Docstring details**

```text
Each cut has one tau value. Each crossed polygon receives a localized copy
whose x/y are the midpoint of that polygon's cut segment.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `scan_values` | `keyword-only` | `list[dict[str, object]]` | `-` |
| `polygon_count` | `keyword-only` | `int` | `-` |

**Returns:** `list[list[dict[str, object]]]`

**Function/method calls visible in the code**

`value.get`, `range`, `int`, `dict`, `localized.pop`, `float`, `append`

### `_jourawski_polygon_shear_weightabs`

**Source lines:** `599-611`

```python
def _jourawski_polygon_shear_weightabspoly: Polygon
```

**Summary:** Return the sampled shear carrier used for local cut redistribution.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `positional or keyword` | `Polygon` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`float`, `getattr`, `math.isfinite`, `hasattr`

### `_jourawski_polygon_is_active_for_b`

**Source lines:** `614-619`

```python
def _jourawski_polygon_is_active_for_bpoly: Polygon
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `positional or keyword` | `Polygon` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`getattr`, `float`, `math.isfinite`, `abs`

### `_jourawski_normalized_section`

**Source lines:** `622-644`

```python
def _jourawski_normalized_sectionsection: Section
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `Section` | `-` |

**Returns:** `tuple[Section, float, list[float]]`

**Function/method calls visible in the code**

`_jourawski_reference_weightabs`, `weight_norm_by_idx.append`, `transformed_polygons.append`, `Section`, `float`, `Polygon`, `tuple`, `getattr`

### `_jourawski_reference_weightabs`

**Source lines:** `647-653`

```python
def _jourawski_reference_weightabssection: Section
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `Section` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`, `float`, `math.isfinite`

### `_section_partial_first_moments`

**Source lines:** `656-689`

```python
def _section_partial_first_moments*, section: Section, axis: str, coord: float, Cx: float, Cy: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `keyword-only` | `Section` | `-` |
| `axis` | `keyword-only` | `str` | `-` |
| `coord` | `keyword-only` | `float` | `-` |
| `Cx` | `keyword-only` | `float` | `-` |
| `Cy` | `keyword-only` | `float` | `-` |

**Returns:** `tuple[float, float]`

**Function/method calls visible in the code**

`_clip_polygon_half_plane`, `_polygon_area_from_points`, `Polygon`, `polygon_area_centroid`, `float`, `len`, `abs`, `tuple`, `getattr`

### `_clip_polygon_half_plane`

**Source lines:** `692-729`

```python
def _clip_polygon_half_plane*, poly: Polygon, axis: str, coord: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `keyword-only` | `Polygon` | `-` |
| `axis` | `keyword-only` | `str` | `-` |
| `coord` | `keyword-only` | `float` | `-` |

**Returns:** `list[Pt]`

**Function/method calls visible in the code**

`len`, `range`, `float`, `_cut_edge_t`, `clipped.append`, `_interpolate_point_on_segment`

### `_interpolate_point_on_segment`

**Source lines:** `731-735`

```python
def _interpolate_point_on_segmentp1: Pt, p2: Pt, t: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `p1` | `positional or keyword` | `Pt` | `-` |
| `p2` | `positional or keyword` | `Pt` | `-` |
| `t` | `positional or keyword` | `float` | `-` |

**Returns:** `Pt`

**Function/method calls visible in the code**

`Pt`, `float`

### `_polygon_area_from_points`

**Source lines:** `738-750`

```python
def _polygon_area_from_pointspoints: list[Pt]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `positional or keyword` | `list[Pt]` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`len`, `range`, `float`

### `_cut_edge_t`

**Source lines:** `753-765`

```python
def _cut_edge_tc1: float, c2: float, coord: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `c1` | `positional or keyword` | `float` | `-` |
| `c2` | `positional or keyword` | `float` | `-` |
| `coord` | `positional or keyword` | `float` | `-` |

**Returns:** `float | None`

**Function/method calls visible in the code**

`float`, `abs`

### `_polygon_line_segments`

**Source lines:** `767-804`

```python
def _polygon_line_segments*, poly: Polygon, axis: str, coord: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `keyword-only` | `Polygon` | `-` |
| `axis` | `keyword-only` | `str` | `-` |
| `coord` | `keyword-only` | `float` | `-` |

**Returns:** `list[tuple[float, float]]`

**Function/method calls visible in the code**

`len`, `range`, `_unique_sorted`, `zip`, `float`, `_cut_edge_t`, `values.append`, `abs`, `segments.append`

### `_unique_sorted`

**Source lines:** `808-817`

```python
def _unique_sortedvalues: list[float]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `values` | `positional or keyword` | `list[float]` | `-` |

**Returns:** `list[float]`

**Function/method calls visible in the code**

`sorted`, `float`, `abs`, `out.append`, `math.isfinite`

### `_mean_scan_tau`

**Source lines:** `820-824`

```python
def _mean_scan_tauvalues: list[dict[str, object]]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `values` | `positional or keyword` | `list[dict[str, object]]` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`float`, `sum`, `len`

### `_empty_scan_value`

**Source lines:** `827-847`

```python
def _empty_scan_value
```

**Summary:** Docstring absent.

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`tau`, `x`, `y`, `coord`, `axis`, `tau_reference`, `b_weighted`, `Sx_part`, `Sy_part`, `polygon_indices`, `segment_length`, `segment_x0`, `segment_y0`, `segment_x1`, `segment_y1`, `shear_weightabs`, `shear_length_sum`, `tau_factor`

**Function/method calls visible in the code**

`float`, `tuple`

### `_min_scan_value`

**Source lines:** `849-852`

```python
def _min_scan_valuevalues: list[dict[str, object]]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `values` | `positional or keyword` | `list[dict[str, object]]` | `-` |

**Returns:** `dict[str, object]`

**Function/method calls visible in the code**

`min`, `_empty_scan_value`, `float`

### `_max_scan_value`

**Source lines:** `855-858`

```python
def _max_scan_valuevalues: list[dict[str, object]]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `values` | `positional or keyword` | `list[dict[str, object]]` | `-` |

**Returns:** `dict[str, object]`

**Function/method calls visible in the code**

`max`, `_empty_scan_value`, `float`

### `_csf__atomic_write_text`

**Source lines:** `1525-1534`

```python
def _csf__atomic_write_textpath: str, text: str
```

**Summary:** Write a file atomically:

**Docstring details**

```text
1) write to path + '.tmp'
  2) os.replace to final name
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `path` | `positional or keyword` | `str` | `-` |
| `text` | `positional or keyword` | `str` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`os.replace`, `open`, `f.write`

### `_csf__section_to_Sz_dict`

**Source lines:** `1537-1598`

```python
def _csf__section_to_Sz_dictsection_obj, nodesection: str
```

**Summary:** Convert a computed Section into the minimal YAML dict format:

**Docstring details**

```text
Sz:
    z: <float>
    polygons:
      <poly_name>:
        weight: <float>
        vertices:
          - [x, y]
          - [x, y]
          ...

Polygon weights are exported exactly as computed at z (already include w(z)).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_obj` | `positional or keyword` | `not annotated` | `-` |
| `nodesection` | `positional or keyword` | `str` | `-` |

**Returns:** `Dict[str, Any]`

**Returned dictionary keys visible in the code**

`weight`, `vertices`, `z`, `polygons`

**Raises visible in the code**

- `CSFError`

**Function/method calls visible in the code**

`enumerate`, `str`, `hasattr`, `CSFError`, `float`, `poly_name.split`, `lower`, `verts_out.append`, `getattr`, `globals`, `get`, `strip`

### `evaluate_weight_formula`

**Source lines:** `1939-2041`

```python
def evaluate_weight_formulaformula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, zt: float
```

**Summary:** Wrapper function intended for use within 'eval()' contexts.

**Docstring details**

```text
It bridges the string evaluation to the structural lookup logic.

Evaluates a string-based mathematical formula to determine the polygon weight at a 
        
Args:
    formula (str): The Python expression to evaluate.
    p0 (Polygon): The polygon definition at the start section (z=0).
    p1 (Polygon): The polygon definition at the end section (z=L).
    zt (float): real relative or normalized values
    normalize: how to interpred zt
    
Returns:
    float: The calculated weight (Elastic Modulus).
    
Raises:
    Exception: Propagates any error encountered during evaluation.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `formula` | `positional or keyword` | `str` | `-` |
| `p0` | `positional or keyword` | `Polygon` | `-` |
| `p1` | `positional or keyword` | `Polygon` | `-` |
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `zt` | `positional or keyword` | `float` | `-` |

**Returns:** `float`

**Returned dictionary keys visible in the code**

`w0`, `w1`, `z`, `t`, `L`, `math`, `np`, `d`, `d0`, `d1`, `E_lookup`, `T_lookup`, `int`, `float`, `bool`, `min`, `max`, `abs`, `round`, `sum`, `pow`, `len`, `range`, `sorted`, `enumerate`, `zip`, `list`, `tuple`, `dict`, `set`, `any`, `all`, `__builtins__`

**Function/method calls visible in the code**

`tuple`, `Polygon`, `float`, `lookup_homogenized_elastic_modulus`, `get_points_distance`, `eval`, `v0.lerp`, `zip`

### `write_opensees_geometry`

**Source lines:** `2240-2480`

```python
def write_opensees_geometryfield, n_points: int, E_ref=None, nu=None, filename: str='geometry.tcl'
```

**Summary:** Write a CSF-style OpenSees geometry file **as DATA** (to be parsed line-by-line),

**Docstring details**

```text
not as a Tcl script to be sourced.

--------------------------------------------------------------------------------
FILE CONTRACT (DATA, NOT Tcl)
--------------------------------------------------------------------------------
1) Exact stations (critical for reproducibility)
   We write the exact longitudinal stations used by CSF:
       # CSF_Z_STATIONS: z0 z1 ... zN-1
   A downstream builder must use these stations (no re-generation).

2) Section record format (data record that *resembles* OpenSees)
   We write one record per station:

       section CSF <tag> <A> <Iz> <Iy> <J_tors> <Cx> <Cy>

   IMPORTANT:
   - This is a DATA record. OpenSees Tcl would NOT accept the trailing <Cx> <Cy>.
   - Cx,Cy are appended for CSF parsers/builders (centroid offsets in section plane).
   - A, Iz, Iy, J_tors are station-wise CSF results computed from polygon-level E/G values.

3) Torsion export without tying the file to a single CSF torsion model
   CSF may provide multiple Saint-Venant torsion contributions
   (e.g., thin-walled cell and thin-walled open wall).

          Torsion selection policy:

     - If both J_sv_cell and J_sv_wall are present and > 0:
         J_tors = J_sv_cell + J_sv_wall
       (additive Saint-Venant contributions)

     - If only one of them is present and > 0:
         J_tors = that value

     - Legacy "Ip" is NOT automatically used here
       (avoids mixing distinct torsion models silently).

     - If no valid Saint-Venant contribution is available:
         fail-fast (explicit error; no silent torsion default).

--------------------------------------------------------------------------------
OUTPUT CONTENTS
--------------------------------------------------------------------------------
- Header comments
- # CSF_Z_STATIONS: exact z-coordinates
- Optional informational nodes (best-fit line through centroid offsets)
- geomTransf Linear 1 1 0 0 (simple default)
- One section record per station (as described above)

--------------------------------------------------------------------------------
REQUIREMENTS
--------------------------------------------------------------------------------
- numpy must be available
- section_full_analysis(sec, ...) must return at least:
    "A", "Ix", "Iy", "Cx", "Cy"
  and (for torsion export) at least one of:
    "J_sv_wall", "J_sv_cell"
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `not annotated` | `-` |
| `n_points` | `positional or keyword` | `int` | `-` |
| `E_ref` | `positional or keyword` | `not annotated` | `None` |
| `nu` | `positional or keyword` | `not annotated` | `None` |
| `filename` | `positional or keyword` | `str` | `'geometry.tcl'` |

**Returns:** `not annotated`

**Raises visible in the code**

- `raise`
- `KeyError`

**Function/method calls visible in the code**

`float`, `field.get_lobatto_integration_points`, `np.polyfit`, `field.section`, `section_full_analysis`, `results.append`, `cx_list.append`, `cy_list.append`, `print`, `np.isfinite`, `open`, `f.write`, `enumerate`, `KeyError`, `np.atleast_1d`, `warnings.warn`, `format`, `len`, `join`

### `_principal_inertias`

**Source lines:** `2661-2668`

```python
def _principal_inertiasix: float, iy: float, ixy: float
```

**Summary:** Principal inertias (eigenvalues) of the 2x2 centroidal inertia tensor.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `ix` | `positional or keyword` | `float` | `-` |
| `iy` | `positional or keyword` | `float` | `-` |
| `ixy` | `positional or keyword` | `float` | `-` |

**Returns:** `Tuple[float, float]`

**Function/method calls visible in the code**

`math.sqrt`

### `compute_saint_venant_J_cell`

**Source lines:** `3213-3672`

```python
def compute_saint_venant_J_cellsection: 'Section'
```

**Summary:** Compute closed-cell Saint-Venant torsional constant J_sv [m^4]

**Docstring details**

```text
for polygons tagged as @cell/@closed using a thin-walled closed-cell model.

Key parsing policy for @cell:
- OUTER loop is detected by the first repeated occurrence of the first vertex.
- INNER loop is the remaining tail after OUTER closure.
- INNER must be repeated endpoint
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `'Section'` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `CSFError`

**Function/method calls visible in the code**

`getattr`, `dataclass`, `enumerate`, `str`, `nm.lower`, `range`, `_signed_area_xy`, `abs`, `_perimeter_xy`, `CellGeometry`, `_find_cell_split_indices`, `_validate_cell_split_indices`, `_build_cell_geometry_from_indices`, `len`, `_poly_signed_area_centroid_xy`, `name.lower`, `low.find`, `set`, `float`, `_xy_list`, `_split_outer_inner_loops_global`, `_parse_t`, `_compute_J_cell_geom_from_global_mid_quantities`, `cell_polys.append`, `CSFError`, `_same_point`, `print`, `s.append`, `join`

### `compute_saint_venant_J_wall`

**Source lines:** `3729-3935`

```python
def compute_saint_venant_J_wallsection: 'Section'
```

**Summary:** Compute Saint-Venant torsional constant J_sv using "@WALL" polygons.

**Docstring details**

```text
Dispatch
--------
- If no polygon name contains "@WALL": return compute_saint_venant_J(section) (legacy).
- Otherwise: use open thin-walled approximation on polygons tagged with "@WALL".

Thickness choice per wall polygon
---------------------------------
- If polygon name contains "@t=<value>": use that thickness (meters).
- Else: estimate thickness via t := 2*A/P.

Returns
-------
float
    Effective Saint-Venant torsional constant J_sv [m^4].
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `'Section'` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`getattr`, `len`, `range`, `abs`, `name.lower`, `low.find`, `set`, `str`, `float`, `_poly_area_abs`, `_parse_thickness_from_name`, `_poly_perimeter`, `token_wall.lower`, `nm.lower`, `wall_polys.append`, `print`, `s.append`, `join`

### `_point_on_segment_sq`

**Source lines:** `3975-4012`

```python
def _point_on_segment_sqpx: float, py: float, ax: float, ay: float, bx: float, by: float, eps_l: float
```

**Summary:** Return True if point (px,py) lies on segment AB, with tolerance.

**Docstring details**

```text
No abs(); uses squared comparisons.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `px` | `positional or keyword` | `float` | `-` |
| `py` | `positional or keyword` | `float` | `-` |
| `ax` | `positional or keyword` | `float` | `-` |
| `ay` | `positional or keyword` | `float` | `-` |
| `bx` | `positional or keyword` | `float` | `-` |
| `by` | `positional or keyword` | `float` | `-` |
| `eps_l` | `positional or keyword` | `float` | `-` |

**Returns:** `bool`

### `_poly_signed_area_centroid_xy`

**Source lines:** `4168-4169`

```python
def _poly_signed_area_centroid_xyverts: Sequence[PointXY]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `verts` | `positional or keyword` | `Sequence[PointXY]` | `-` |

**Returns:** `Tuple[float, float, float]`

**Function/method calls visible in the code**

`_signed_area_centroid_xy`

### `export_to_opensees_tcl`

**Source lines:** `4172-4205`

```python
def export_to_opensees_tclfield, K_12x12, filename='csf_model.tcl'
```

**Summary:** Generates an OpenSees-ready .tcl file that defines the nodes and the stiffness-matrix element computed by CSF.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `not annotated` | `-` |
| `K_12x12` | `positional or keyword` | `not annotated` | `-` |
| `filename` | `positional or keyword` | `not annotated` | `'csf_model.tcl'` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`print`, `open`, `f.write`, `join`

### `polygon_has_self_intersections`

**Source lines:** `5195-5294`

```python
def polygon_has_self_intersectionspoly: Polygon
```

**Summary:** Returns True if the polygon has any self-intersection between NON-adjacent edges.

**Docstring details**

```text
This version is *robust*:
- Detects proper crossings (X-shaped intersections)
- Also detects "touching" (vertex on edge) and collinear overlaps

Why this matters:
- Your current _segments_intersect() uses a strict test (o1*o2 < 0 and o3*o4 < 0),
    which will NOT flag touching or collinear overlap. :contentReference[oaicite:1]{index=1}
- For ruled-surface interpolation across z, "touching" can appear due to numerical
    noise or twisting, and you typically want a warning.

Input model:
- poly.vertices: Tuple[Pt, ...]
- Pt has fields .x, .y
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `positional or keyword` | `Polygon` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`len`, `range`, `_sign`, `_orient`, `_on_segment`, `_segments_intersect_robust`, `min`, `max`

### `polygon_surface_w1_inners0`

**Source lines:** `5476-5680`

```python
def polygon_surface_w1_inners0self: Any, z: float
```

**Summary:** Compute the local occupied surface for every polygon at coordinate z using the rule:

**Docstring details**

```text
- w(polygon) = 1
  - w(direct inners) = 0

And its weighted counterpart:
  - A_w = A * w_eff

Structural rules:
- all topology, validation, and calculations are strictly index-based
- names are output labels only
- names must never trigger errors or logic branches

Required upstream structural fields:
- list_polygons_with_contents(self, z):
    * idx
    * container_idx
    * direct_children_idx
- self.inspect_section_entities(z):
    * idx
    * area_signed
    * weight_at_z

Output fields:
  - idx (int)
  - name (str | None)
  - container_name (str | None)
  - direct_inners (List[str | None])
  - w (float)
  - A (float)
  - A_w (float)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `Any` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `List[Dict[str, Any]]`

**Returned dictionary keys visible in the code**

`idx`, `name`, `container_name`, `direct_inners`, `w`, `shear_w`, `A`, `A_w`, `A_shear_w`

**Raises visible in the code**

- `TypeError`
- `AttributeError`
- `ValueError`

**Function/method calls visible in the code**

`float`, `list_polygons_with_contents`, `enumerate`, `self.inspect_section_entities`, `container_of.items`, `direct_inners_of.items`, `sorted`, `isinstance`, `TypeError`, `list`, `hasattr`, `AttributeError`, `container_of.keys`, `out.append`, `ValueError`, `direct_inners_labels.append`, `type`

### `export_polygon_vertices_csv_file`

**Source lines:** `5897-5953`

```python
def export_polygon_vertices_csv_filesection: Section=None, field: ContinuousSectionField=None, zpos: float=None, exp_filename: str='csv_export.txt', z_values: Optional[List[float]]=None, fmt: str='{:.16g}'
```

**Summary:** File wrapper for export_polygon_vertices_csv().

**Docstring details**

```text
Modes
-----
1) Single export:
   - section=...
   or
   - field=... and zpos=...

2) Multiple export:
   - field=... and z_values=[...]
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `Section` | `None` |
| `field` | `positional or keyword` | `ContinuousSectionField` | `None` |
| `zpos` | `positional or keyword` | `float` | `None` |
| `exp_filename` | `positional or keyword` | `str` | `'csv_export.txt'` |
| `z_values` | `positional or keyword` | `Optional[List[float]]` | `None` |
| `fmt` | `positional or keyword` | `str` | `'{:.16g}'` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`Path`, `out_path.parent.mkdir`, `ValueError`, `open`, `export_polygon_vertices_csv`, `f.write`, `float`

### `polygon_area_centroid`

**Source lines:** `6273-6277`

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

## NAVIER

### `analyse_polygon_navier_stress`

**Source lines:** `866-955`

```python
def analyse_polygon_navier_stresssection_field, z: float, N: float, Mx: float, My: float
```

**Summary:** Compute polygon-wise signed normal stresses from the general Navier formula.

**Docstring details**

```text
For each polygon all vertices are checked.

Returned stress values:
- sigma_min      : minimum signed vertex stress in the polygon
- sigma_max      : maximum signed vertex stress in the polygon
- sigma_extreme  : signed vertex stress selected by largest absolute value

The coordinates and vertex indices of all three governing values are returned.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `N` | `positional or keyword` | `float` | `-` |
| `Mx` | `positional or keyword` | `float` | `-` |
| `My` | `positional or keyword` | `float` | `-` |

**Returns:** `list[dict[str, object]]`

**Returned dictionary keys visible in the code**

`idx`, `name`, `weightabs`, `sigma_min`, `vertex_index_min`, `x_min`, `y_min`, `sigma_max`, `vertex_index_max`, `x_max`, `y_max`, `sigma_extreme`, `vertex_index`, `x`, `y`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`section_field.section`, `section_full_analysis`, `float`, `enumerate`, `ValueError`, `str`, `min`, `max`, `rows.append`, `vertex_rows.append`, `int`, `abs`

## Station generation

### `get_lobatto_intervals`

**Source lines:** `960-975`

```python
def get_lobatto_intervalsz_min: float, z_max: float, n_intervals: int
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `z_min` | `positional or keyword` | `float` | `-` |
| `z_max` | `positional or keyword` | `float` | `-` |
| `n_intervals` | `positional or keyword` | `int` | `-` |

**Returns:** `'np.ndarray'`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`np.asarray`, `ValueError`, `compute_lobatto_integration_points`

### `compute_lobatto_integration_points`

**Source lines:** `978-1037`

```python
def compute_lobatto_integration_pointsz_min: float, z_max: float, n_points: int=5, L: float=None
```

**Summary:** Calculates the global Z-coordinates for OpenSees integration points using

**Docstring details**

```text
the Gauss-Lobatto quadrature rule.

RATIONALE:
In finite element analysis (specifically for OpenSees forceBeamColumn elements), 
the Gauss-Lobatto rule is preferred because it includes the endpoints of the 
interval (z=0 and z=L). This is critical for detecting anomalies at the 
very base of the shaft (e.g., FHWA Soft Toe) or at the top connection.

ALGORITHM:
1. Generate the roots of the derivative of the (n-1)-th Legendre Polynomial.
2. These roots (plus -1.0 and 1.0) form the abscissae in the natural 
coordinate system [-1, 1].
3. Map these abscissae from [-1, 1] to the physical domain [z0, z1] or [0, L].

Args:
    n_points (int): Number of integration points. Must be >= 2.
    L (float, optional): Total length of the element. If None, it uses 
                        the distance between the two defined sections.

Returns:
    List[float]: A list of global Z-coordinates where OpenSees will 
                sample the section properties.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `z_min` | `positional or keyword` | `float` | `-` |
| `z_max` | `positional or keyword` | `float` | `-` |
| `n_points` | `positional or keyword` | `int` | `5` |
| `L` | `positional or keyword` | `float` | `None` |

**Returns:** `List[float]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `sorted`, `ValueError`, `roots_jacobi`, `np.concatenate`

## Core property sampling

### `_compute_station_data`

**Source lines:** `1045-1117`

```python
def _compute_station_datafield: Any, z_values: Sequence[float]
```

**Summary:** Sample the CSF field at the provided z positions and compute section properties.

**Docstring details**

```text
This function delegates the actual validation/computation to the CSF library's
analysis function. We intentionally do NOT "second-guess" the CSF analysis.

Expected CSF interface
----------------------
- field.section(z) -> a section object at that z
- csf.section_field.section_full_analysis(section,alpha) -> dict with keys like:
    'A', 'Cx', 'Cy', 'Ix', 'Iy', 'Ixy', 'Ip', ...
  (We fall back to sensible defaults if some keys are missing.)

Returns
-------
List[Dict[str, Any]]:
    Each dict contains:
      id (1-based),
      z,
      Cx, Cy,
      A, Ix, Iy, Ixy, J,
      plus any extra keys the analysis returns (stored under 'analysis_raw').

Raises
------
RuntimeError:
    If section_full_analysis cannot be imported.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `z_values` | `positional or keyword` | `Sequence[float]` | `-` |

**Returns:** `List[Dict[str, Any]]`

**Returned dictionary keys visible in the code**

`id`, `z`, `Cx`, `Cy`, `A`, `Ix`, `Iy`, `Ixy`, `Ip`, `analysis_raw`

**Function/method calls visible in the code**

`enumerate`, `field.section`, `section_full_analysis`, `analysis.get`, `out.append`, `float`

## Torsion: different libraries may report 'Ip' or 'K_torsion' etc.

### `_parse_optional_float`

**Source lines:** `1123-1126`

```python
def _parse_optional_floatvalue: Any
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `Any` | `-` |

**Returns:** `Optional[float]`

**Function/method calls visible in the code**

`float`

### `write_sap2000_template_pack`

**Source lines:** `1127-1482`

```python
def write_sap2000_template_packfield: Any, n_intervals: int=20, template_filename: str='export_template_pack.txt', *, mode: Literal['BOTH', 'CENTROIDAL_LINE', 'REFERENCE_LINE']='BOTH', section_prefix: str='SEC', material_name: str='S355', E_ref=None, nu=None, include_plot: bool=True, plot_filename: str='section_variation.png', show_plot: bool=True, z_values: Optional[List[float]]=None, plot_n: int=100, float_fmt: str='.9g'
```

**Summary:** Export a CSF field to a structured text pack for SAP2000 / OpenSees input.

**Docstring details**

```text
Produces four compact tables:
  1. SOLVER INPUT    - properties consumed directly by SAP2000 / OpenSees.
  2. SECTION QUALITY - derived verification properties (principal axes, moduli).
  3. TORSION QUALITY - torsion breakdown with fidelity indicator.
  4. STATION NAMES   - section name list for frame property assignment.

All section data comes from section_full_analysis() evaluated at the requested
stations - no interpolation, no silent fallback values.

Parameters
----------
field            : ContinuousSectionField with .s0.z, .s1.z, .section(z).
n_intervals      : Gauss-Lobatto intervals; stations = n_intervals + 1.
                   Ignored when z_values is provided.
template_filename: Output file path.
mode             : Retained for API compatibility; not used in output.
section_prefix   : Prefix for section name labels ("SEC" -> "SEC0001").
material_name    : Informational label written to the file header.
E_ref            : Reference Young's modulus; G_ref = E_ref / (2*(1+nu)). For reference only
                   Written to header only if provided.
nu               : Poisson's ratio; used to derive G_ref when E_ref is given. for referencep only
include_plot     : If True and matplotlib is available, saves a property plot.
plot_filename    : Path for the optional plot image.
show_plot        : If True, display the plot interactively.
z_values         : Explicit station list (strictly increasing, within field bounds).
                   No sorting or deduplication - invalid input raises ValueError.
plot_n           : Number of uniformly sampled stations used only for the plot curve.
                   The export tables still use Lobatto stations or z_values.
float_fmt        : Format spec for all numeric output fields.

Returns
-------
str : Path of the file written.

Raises
------
ValueError : On invalid z_values.
KeyError   : If section_full_analysis() does not return an expected key.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `n_intervals` | `positional or keyword` | `int` | `20` |
| `template_filename` | `positional or keyword` | `str` | `'export_template_pack.txt'` |
| `mode` | `keyword-only` | `Literal['BOTH', 'CENTROIDAL_LINE', 'REFERENCE_LINE']` | `'BOTH'` |
| `section_prefix` | `keyword-only` | `str` | `'SEC'` |
| `material_name` | `keyword-only` | `str` | `'S355'` |
| `E_ref` | `keyword-only` | `not annotated` | `None` |
| `nu` | `keyword-only` | `not annotated` | `None` |
| `include_plot` | `keyword-only` | `bool` | `True` |
| `plot_filename` | `keyword-only` | `str` | `'section_variation.png'` |
| `show_plot` | `keyword-only` | `bool` | `True` |
| `z_values` | `keyword-only` | `Optional[List[float]]` | `None` |
| `plot_n` | `keyword-only` | `int` | `100` |
| `float_fmt` | `keyword-only` | `str` | `'.9g'` |

**Returns:** `str`

**Returned dictionary keys visible in the code**

`id`, `z`, `A`, `Cx`, `Cy`, `Ix`, `Iy`, `Ixy`, `Ip`, `I1`, `I2`, `theta_deg`, `rx`, `ry`, `Wx`, `Wy`, `K_torsion`, `Q_na`, `J_sv_cell`, `J_sv_cell_t`, `J_sv_wall`, `J_sv_wall_t`, `J_s_vroark`, `J_s_vroark_fidelity`, `J_tors`, `method`

**Raises visible in the code**

- `ValueError`
- `raise`
- `KeyError`

**Function/method calls visible in the code**

`float`, `_compute_station_data`, `len`, `lines.append`, `_header`, `t3_headers.append`, `Path`, `str`, `ValueError`, `getattr`, `tolist`, `enumerate`, `range`, `np.atleast_1d`, `records.append`, `format`, `_row`, `vals.append`, `out_path.parent.mkdir`, `open`, `f.write`, `station_z.append`, `visualizer_plot_section_variation`, `_fmt`, `out_path.parent.exists`, `get_lobatto_intervals`, `isinstance`, `int`, `print`, `KeyError`, `join`, `rstrip`, `np.linspace`, `repr`, `warnings.warn`, `lbl.ljust`, `ljust`

## Write file

### `write_sap2000_geometry`

**Source lines:** `1486-1498`

```python
def write_sap2000_geometry*args: Any, **kwargs: Any
```

**Summary:** Backward-compatible wrapper.

**Docstring details**

```text
this function tried to generate a SAP2000 .s2k directly. In v2 we avoid
promising direct import correctness and instead generate a template pack.

Use:
    write_sap2000_template_pack(...)

This wrapper calls write_sap2000_template_pack with the provided arguments.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `*args` | `var positional` | `Any` | `-` |
| `**kwargs` | `var keyword` | `Any` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`write_sap2000_template_pack`

### `_csf__is_finite_number`

**Source lines:** `1501-1507`

```python
def _csf__is_finite_numberx: Any
```

**Summary:** Return True if x can be converted to a finite float.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `x` | `positional or keyword` | `Any` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`math.isfinite`, `float`

### `_csf__ensure_parent_dir_exists`

**Source lines:** `1510-1522`

```python
def _csf__ensure_parent_dir_existspath: str
```

**Summary:** Ensure the parent directory exists; otherwise raise CSFError.

**Docstring details**

```text
Note: we intentionally do NOT auto-create directories. This makes typos
in output paths fail fast and is easier to debug.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `path` | `positional or keyword` | `str` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `CSFError`

**Function/method calls visible in the code**

`os.path.dirname`, `os.path.abspath`, `CSFError`, `os.path.isdir`

## Example: "tower:tower" -> "tower".

### `_yaml_scalar`

**Source lines:** `1601-1622`

```python
def _yaml_scalarv
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `v` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`isinstance`, `str`, `any`, `v.item`, `s.replace`

## quote se serve

### `_simple_yaml_dump`

**Source lines:** `1625-1649`

```python
def _simple_yaml_dumpdata, indent: int=0
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `data` | `positional or keyword` | `not annotated` | `-` |
| `indent` | `positional or keyword` | `int` | `0` |

**Returns:** `str`

**Function/method calls visible in the code**

`isinstance`, `data.items`, `join`, `_yaml_scalar`, `out.append`, `_simple_yaml_dump`

## scalare singolo

### `safe_evaluate_weight_zrelative`

**Source lines:** `1651-1751`

```python
def safe_evaluate_weight_zrelativeformula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float, print=True
```

**Summary:** Evaluates a weight formula string safely by trapping all potential exceptions.

**Docstring details**

```text
This function performs:
1. Proactive File System check (pre-evaluation).
2. Mathematical evaluation via eval/evaluate_weight_formula.
3. Physical constraint validation (e.g., negative results).
4. Immediate visual reporting via print_evaluation_report.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `formula` | `positional or keyword` | `str` | `-` |
| `p0` | `positional or keyword` | `Polygon` | `-` |
| `p1` | `positional or keyword` | `Polygon` | `-` |
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `print` | `positional or keyword` | `not annotated` | `True` |

**Returns:** `tuple[float, dict]`

**Returned dictionary keys visible in the code**

`status`, `error_type`, `message`, `suggestion`, `z_pos`, `t_pos`, `formula`

**Function/method calls visible in the code**

`formula.strip`, `re.search`, `evaluate_weight_formula_zrelative`, `print_evaluation_report`, `float`, `match.group`, `report.update`, `os.path.exists`, `str`, `os.getcwd`

## Call the tabular printer before returning values

### `print_evaluation_report`

**Source lines:** `1753-1799`

```python
def print_evaluation_reportvalue: float, report: dict
```

**Summary:** Prints minimalist structured report with Timestamp.

**Docstring details**

```text
Designed for traceability.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `value` | `positional or keyword` | `float` | `-` |
| `report` | `positional or keyword` | `dict` | `-` |

**Returns:** `not annotated`

**Returned dictionary keys visible in the code**

`SUCCESS`, `WARNING`, `ERROR`

**Function/method calls visible in the code**

`icons.get`, `print`, `print_line`, `strftime`, `len`, `report.get`, `datetime.now`, `abs`

## Aligned to the right

### `execute_string_to_float`

**Source lines:** `1801-1813`

```python
def execute_string_to_floatcode_string, x_value
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `code_string` | `positional or keyword` | `not annotated` | `-` |
| `x_value` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Returned dictionary keys visible in the code**

`x`

**Function/method calls visible in the code**

`exec`, `float`, `workspace.get`

## We use .get() to avoid an error if 'risultato' is missing, then cast to float

### `evaluate_shear_weight_formula`

**Source lines:** `1816-1937`

```python
def evaluate_shear_weight_formulaformula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, zt: float, w: float
```

**Summary:** Evaluate a string-based shear-weight law.

**Docstring details**

```text
Differences from evaluate_weight_formula():
- The variable 'w' is available and represents the absolute weight at z.
- The special function iso(nu) is available.
- If iso(nu) is used, it must be the entire formula.

iso(nu) applies the isotropic relation:

    G = E / (2 * (1 + nu))

In CSF terms, if 'w' represents the absolute E-like weight,
iso(nu) returns the corresponding G-like shear weight.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `formula` | `positional or keyword` | `str` | `-` |
| `p0` | `positional or keyword` | `Polygon` | `-` |
| `p1` | `positional or keyword` | `Polygon` | `-` |
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `zt` | `positional or keyword` | `float` | `-` |
| `w` | `positional or keyword` | `float` | `-` |

**Returns:** `float`

**Returned dictionary keys visible in the code**

`w`, `w0`, `w1`, `z`, `t`, `L`, `math`, `np`, `d`, `d0`, `d1`, `E_lookup`, `T_lookup`, `iso`, `int`, `float`, `bool`, `min`, `max`, `abs`, `round`, `sum`, `pow`, `len`, `range`, `sorted`, `enumerate`, `zip`, `list`, `tuple`, `dict`, `set`, `any`, `all`, `__builtins__`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`formula.strip`, `re.fullmatch`, `tuple`, `Polygon`, `float`, `isinstance`, `ValueError`, `re.search`, `lookup_homogenized_elastic_modulus`, `get_points_distance`, `eval`, `v0.lerp`, `abs`, `zip`

## We disable __builtins__ for safety to ensure only provided tools are used.

### `execute_string_to_float`

**Source lines:** `2043-2072`

```python
def execute_string_to_floatcode_string, z_val, t_val
```

**Summary:** Executes a Python procedure from a string and returns a float.

**Docstring details**

```text
Uses 'z' and 't' as input variables.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `code_string` | `positional or keyword` | `not annotated` | `-` |
| `z_val` | `positional or keyword` | `not annotated` | `-` |
| `t_val` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Returned dictionary keys visible in the code**

`z`, `t`, `math`

**Raises visible in the code**

- `NameError`
- `raise`

**Function/method calls visible in the code**

`exec`, `float`, `NameError`, `print`

## The code string MUST save the final result in 'output'

### `evaluate_weight_formula_zrelative`

**Source lines:** `2075-2134`

```python
def evaluate_weight_formula_zrelativeformula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float
```

**Summary:** Evaluates a string-based mathematical formula to determine the polygon weight at a

**Docstring details**

```text
Args:
    formula (str): The Python expression to evaluate.
    p0 (Polygon): The polygon definition at the start section (z=0).
    p1 (Polygon): The polygon definition at the end section (z=L).
    z (float): real relative z
    
Returns:
    float: The calculated weight (Elastic Modulus).
    
Raises:
    Exception: Propagates any error encountered during evaluation.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `formula` | `positional or keyword` | `str` | `-` |
| `p0` | `positional or keyword` | `Polygon` | `-` |
| `p1` | `positional or keyword` | `Polygon` | `-` |
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`evaluate_weight_formula`

## "t": t,

### `section_geometry`

**Source lines:** `2136-2154`

```python
def section_geometrysection: Section, fmt='.8f'
```

**Summary:** Prints the section structure keeping the original table layout.

**Docstring details**

```text
Uses 'fmt' for all vertex coordinates.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `Section` | `-` |
| `fmt` | `positional or keyword` | `not annotated` | `'.8f'` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`print`, `join`, `len`, `format`

## Print using your exact original column widths

### `section_print_analysis`

**Source lines:** `2157-2211`

```python
def section_print_analysisfull_analysis, fmt='.8f'
```

**Summary:** Prints the structural analysis report for a cross-section.

**Docstring details**

```text
Args:
    full_analysis (dict): Dictionary containing the calculated properties.
    fmt (str): Optional Python format string for numerical output. 
               Defaults to ".8f" (fixed-point with 8 decimals). 
      
               Can be set to ".4e" for scientific notation or others.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `full_analysis` | `positional or keyword` | `not annotated` | `-` |
| `fmt` | `positional or keyword` | `not annotated` | `'.8f'` |

**Returns:** `not annotated`

**Raises visible in the code**

- `TypeError`

**Function/method calls visible in the code**

`print`, `isinstance`, `TypeError`, `format`, `float`, `len`, `fmt_val_or_pair`

## Using the 'fmt' parameter inside f-strings for all numerical values

### `section_full_analysis_keys`

**Source lines:** `2213-2238`

```python
def section_full_analysis_keys
```

**Summary:** Returns the ordered list of keys generated by the full analysis.

**Docstring details**

```text
Useful for mapping, CSV headers, or selective data extraction.
```

**Returns:** `List[str]`

## Write section data record

### `lookup_homogenized_elastic_modulus`

**Source lines:** `2483-2575`

```python
def lookup_homogenized_elastic_modulusfilename: str, zt: float
```

**Summary:** Retrieves the elastic modulus (E) for a given longitudinal coordinate (z)

**Docstring details**

```text
from an external lookup file.

ALGORITHM STRATEGY:
1. Parsing: The function reads a text file where each line contains a pair of 
   values: [coordinate_z, modulus_E].
2. Exact Match: If the requested 'z' matches a coordinate in the file, 
   the corresponding E is returned immediately.
3. Boundary Handling: If 'z' is outside the range defined in the file, 
   it performs flat extrapolation (returns the nearest boundary value).
4. Linear Interpolation (LERP): If 'z' falls between two points (z_i, E_i) 
   and (z_j, E_j), it calculates E via:
   E = E_i + (E_j - E_i) * (z - z_i) / (z_j - z_i)

FILE FORMAT ASSUMPTIONS:
- The file should be a space, tab, or comma-separated text file.
- Column 0: Z-coordinate (must be in increasing order for correct interpolation).
- Column 1: Elastic Modulus value.

Args:
    filename (str): Path to the lookup data file.
    zt (float): The current coordinate where the property is needed. can be both normalised or not

Returns:
    float: The interpolated or exact Elastic Modulus.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `filename` | `positional or keyword` | `str` | `-` |
| `zt` | `positional or keyword` | `float` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `FileNotFoundError`
- `ValueError`

**Function/method calls visible in the code**

`data.sort`, `range`, `os.path.exists`, `FileNotFoundError`, `open`, `ValueError`, `line.strip`, `len`, `abs`, `line.startswith`, `split`, `float`, `data.append`, `line.replace`

## Tolerance resolution (no hard-coded constants here)

### `_resolve_eps_a`

**Source lines:** `2606-2607`

```python
def _resolve_eps_aobj: Any
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `obj` | `positional or keyword` | `Any` | `-` |

**Returns:** `float`

### `_resolve_eps_k`

**Source lines:** `2610-2611`

```python
def _resolve_eps_kobj: Any
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `obj` | `positional or keyword` | `Any` | `-` |

**Returns:** `float`

## Signed polygon integrals (no abs())

### `_poly_signed_area_centroid`

**Source lines:** `2618-2658`

```python
def _poly_signed_area_centroidpts: Any, eps_a: float
```

**Summary:** Shoelace integration.

**Docstring details**

```text
Returns (A, Cx, Cy) with signed area A.
Under CSF preconditions polygons are CCW so A > 0.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `pts` | `positional or keyword` | `Any` | `-` |
| `eps_a` | `positional or keyword` | `float` | `-` |

**Returns:** `Tuple[float, float, float]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`len`, `range`, `ValueError`, `hasattr`, `float`

## Roark equivalent-rectangle torsion proxy

### `_roark_torsion_rect`

**Source lines:** `2675-2698`

```python
def _roark_torsion_recta: float, b: float
```

**Summary:** Roark-style torsion approximation for a solid rectangular section.

**Docstring details**

```text
Here a and b are the full side dimensions, with a >= b > 0:

    J ≈ a*b^3 * [
          1/3
        - 0.21*(b/a)*(1 - (b/a)^4/12)
    ]

This is the full-side form of the common half-side expression:

    J ≈ a_h*b_h^3 * [
          16/3
        - 3.36*(b_h/a_h)*(1 - (b_h/a_h)^4/12)
    ]
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `a` | `positional or keyword` | `float` | `-` |
| `b` | `positional or keyword` | `float` | `-` |

**Returns:** `float`

### `_equiv_rectangle_dims`

**Source lines:** `2701-2724`

```python
def _equiv_rectangle_dimsA: float, i_min: float, eps_k: float
```

**Summary:** Map (A, I_min) to equivalent rectangle dimensions (a >= b).

**Docstring details**

```text
Uses: I_min = (A * t^2) / 12  -> t = sqrt(12*I_min/A),  b = A/t
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `A` | `positional or keyword` | `float` | `-` |
| `i_min` | `positional or keyword` | `float` | `-` |
| `eps_k` | `positional or keyword` | `float` | `-` |

**Returns:** `Tuple[float, float]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`math.sqrt`, `ValueError`

## print(f"DEBIG _equiv_rectangle_dims A {A} i_min {i_min}")

### `compute_saint_venant_Jv2`

**Source lines:** `2726-3077`

```python
def compute_saint_venant_Jv2poly_input: Any
```

**Summary:** Estimate the Saint-Venant torsional constant J and a fidelity indicator.

**Docstring details**

```text
Returns (J_total, fidelity).

Strategy
--------
- Net geometric area and homogenised area via polygon_surface_w1_inners0.
- Equivalent Roark rectangle: shape from geometric bounding box, area from
  A_geom_net. Weight enters as linear multiplier w_total = Ao / A_geom_net.
- Fidelity = A_geom_net / Ag  (fill ratio of the geometric bounding box).
- Isoperimetric penalty: if the outer polygon is nearly circular
  (q_iso > 0.90), J and fidelity are forced to zero.
- Weight-dispersion penalty:  fid_final = fid * (1 - dev_weightabs^2).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly_input` | `positional or keyword` | `Any` | `-` |

**Returns:** `Tuple[float, float]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`any`, `_resolve_eps_a`, `Section`, `ContinuousSectionField`, `field.build_direct_children_map`, `compute_shear_areas`, `_geometric_bounding_box_dims`, `math.sqrt`, `_roark_torsion_rect`, `max`, `_isoperimetric_ratio`, `_shear_weightabs_deviation`, `enumerate`, `range`, `hasattr`, `list`, `np.vstack`, `np.unique`, `float`, `len`, `sum`, `_poly_signed_area_centroid`, `min`, `callable`, `outer_poly.vertices`, `print`, `math.isfinite`, `abs`, `children_map.get`, `np.empty`, `getattr`, `_xy_array`, `point_arrays.append`, `np.roll`, `np.any`, `ValueError`, `np.concatenate`, `int`, `values.append`, `poly_input.polygons`, `vertices_attr`, `np.mod`, `angle_arrays.append`, `np.cos`, `np.sin`, `xr.max`, `xr.min`, `yr.max`, `yr.min`, `np.argmin`, `math.hypot`, `str`, `np.abs`, `np.arctan2`, `np.round`, `_x`, `_y`, `p.vertices`

## Weight-dispersion penalty on fidelity

### `calculate_t_eq`

**Source lines:** `3080-3093`

```python
def calculate_t_eqpoints
```

**Summary:** Calcola t_eq = 2*A/P per poligono thin-walled.

**Docstring details**

```text
points: list [[x1,y1], [x2,y2], ..., [xn,yn]] linea mediana.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`np.array`, `np.diff`, `np.sum`, `np.abs`, `np.sqrt`, `np.dot`, `np.roll`

## Keep torsional stiffness non-negative

### `_poly_vertices_xy`

**Source lines:** `3938-3946`

```python
def _poly_vertices_xypoly: Any
```

**Summary:** Extract polygon vertices as plain (x, y) float tuples.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `positional or keyword` | `Any` | `-` |

**Returns:** `List[PointXY]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`getattr`, `ValueError`, `out.append`, `float`

### `_bbox_xy`

**Source lines:** `3949-3955`

```python
def _bbox_xyverts: Sequence[PointXY]
```

**Summary:** Axis-aligned bounding box for a vertex list.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `verts` | `positional or keyword` | `Sequence[PointXY]` | `-` |

**Returns:** `Tuple[float, float, float, float]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ValueError`, `min`, `max`

### `_auto_grid_h_from_bbox`

**Source lines:** `3958-3972`

```python
def _auto_grid_h_from_bboxverts: Sequence[PointXY], auto_n: int
```

**Summary:** Automatic grid spacing based on the polygon bounding box:

**Docstring details**

```text
h := min(span_x, span_y) / auto_n
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `verts` | `positional or keyword` | `Sequence[PointXY]` | `-` |
| `auto_n` | `positional or keyword` | `int` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`_bbox_xy`, `ValueError`, `float`

## Projection: 0 <= dot <= |AB|^2 (with tolerance)

### `_point_in_poly_inclusive`

**Source lines:** `4015-4044`

```python
def _point_in_poly_inclusivepx: float, py: float, verts: Sequence[PointXY], eps_l: float
```

**Summary:** Ray casting point-in-polygon, counting boundary as inside.

**Docstring details**

```text
No validation is performed; self-intersections may yield undefined results.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `px` | `positional or keyword` | `float` | `-` |
| `py` | `positional or keyword` | `float` | `-` |
| `verts` | `positional or keyword` | `Sequence[PointXY]` | `-` |
| `eps_l` | `positional or keyword` | `float` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`len`, `range`, `_point_on_segment_sq`

## Edge straddles horizontal line at py?

### `_build_inside_mask`

**Source lines:** `4047-4065`

```python
def _build_inside_maskverts: Sequence[PointXY], xs: np.ndarray, ys: np.ndarray, eps_l: float
```

**Summary:** Build boolean mask M[j,i] = True if grid node (xs[i], ys[j]) is inside polygon.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `verts` | `positional or keyword` | `Sequence[PointXY]` | `-` |
| `xs` | `positional or keyword` | `np.ndarray` | `-` |
| `ys` | `positional or keyword` | `np.ndarray` | `-` |
| `eps_l` | `positional or keyword` | `float` | `-` |

**Returns:** `np.ndarray`

**Function/method calls visible in the code**

`int`, `np.zeros`, `range`, `float`, `_point_in_poly_inclusive`

### `_solve_poisson_sor`

**Source lines:** `4068-4118`

```python
def _solve_poisson_sormask: np.ndarray, h: float, *, max_iter: int, tol: float, omega: float
```

**Summary:** Solve ∇²ψ = -2 on a masked grid using SOR, with ψ=0 outside.

**Docstring details**

```text
Stopping rule:
    max update magnitude <= tol
(implemented via squared values; no abs()).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `mask` | `positional or keyword` | `np.ndarray` | `-` |
| `h` | `positional or keyword` | `float` | `-` |
| `max_iter` | `keyword-only` | `int` | `-` |
| `tol` | `keyword-only` | `float` | `-` |
| `omega` | `keyword-only` | `float` | `-` |

**Returns:** `np.ndarray`

**Function/method calls visible in the code**

`np.zeros`, `range`, `int`

## Neighbor values, ψ=0 outside.

### `_sq`

**Source lines:** `4120-4121`

```python
def _sqx: float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `x` | `positional or keyword` | `float` | `-` |

**Returns:** `float`

### `_is_near_zero`

**Source lines:** `4124-4131`

```python
def _is_near_zerox: float, eps: float
```

**Summary:** Compare x to 0 using squared values to avoid abs().

**Docstring details**

```text
Note: This is for degeneracy guards only (division-by-zero avoidance).
It does not "fix" or "normalize" signs.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `x` | `positional or keyword` | `float` | `-` |
| `eps` | `positional or keyword` | `float` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`_sq`

### `_signed_area_centroid_xy`

**Source lines:** `4134-4165`

```python
def _signed_area_centroid_xyverts: Sequence[tuple[float, float]]
```

**Summary:** Shoelace formula.

**Docstring details**

```text
Returns (A, Cx, Cy) not weight
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `verts` | `positional or keyword` | `Sequence[tuple[float, float]]` | `-` |

**Returns:** `Tuple[float, float, float]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`len`, `range`, `ValueError`, `abs`

## Syntax: element matrixBeamColumn eleTag iNode jNode transfTag Klist

### `assemble_element_stiffness_matrix`

**Source lines:** `4208-4305`

```python
def assemble_element_stiffness_matrixfield: ContinuousSectionField, E_ref: float=1.0, nu: float=0.3, n_gauss: int=5
```

**Summary:** Assembles the complete 12x12 Timoshenko beam stiffness matrix with full EIxy coupling.

**Docstring details**

```text
DOF order (OpenSees compatible): [ux1,uy1,uz1,θx1,θy1,θz1 | ux2,uy2,uz2,θx2,θy2,θz2]
Full asymmetric section support (EIxy coupling) + Saint-Venant torsion.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `ContinuousSectionField` | `-` |
| `E_ref` | `positional or keyword` | `float` | `1.0` |
| `nu` | `positional or keyword` | `float` | `0.3` |
| `n_gauss` | `positional or keyword` | `int` | `5` |

**Returns:** `np.ndarray`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`abs`, `np.polynomial.legendre.leggauss`, `np.zeros`, `np.any`, `ValueError`, `section_stiffness_matrix`, `section_full_analysis`, `np.allclose`, `warnings.warn`, `field.section`, `np.diag`

## Physical bounds check

### `polygon_inertia_about_origin`

**Source lines:** `4308-4341`

```python
def polygon_inertia_about_originpoly: Polygon
```

**Summary:** Second moments about the origin (0,0) using standard polygon formulas.

**Docstring details**

```text
Returns (Ix, Iy, Ixy) about origin, INCLUDING poly.weight.

Notes:
- Works for simple polygons (non self-intersecting).
- Sign/orientation is handled by using signed cross; we then multiply by weight.
- For holes, you can use negative weight or a separate convention.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `positional or keyword` | `Polygon` | `-` |

**Returns:** `Tuple[float, float, float]`

**Function/method calls visible in the code**

`len`, `range`

## Volume polygon-list report helpers (reuses integrate_volume; no local integration)

### `volume_polygon_list_report_data`

**Source lines:** `4348-4467`

```python
def volume_polygon_list_report_datafield: 'ContinuousSectionField', z1: float, z2: float, n_points: int=20, *, do_debug_check: bool=False, debug_tol: float=1e-09
```

**Summary:** Build per-polygon volume report data between two stations.

**Docstring details**

```text
Design rules
------------
- Volumes are computed ONLY via integrate_volume(...).
- Descriptive columns (names, weights at endpoints, law labels) are obtained
  from field.inspect_section_entities(z).
- No additional validation/assumptions are introduced here; CSF preconditions
  are enforced upstream (parser/validator).

Parameters
----------
field:
    ContinuousSectionField instance.
z1, z2:
    Two absolute stations (order is preserved for reporting; integration uses [min,max]).
n_points:
    Gauss-Legendre points passed to integrate_volume.
do_debug_check:
    If True, checks (internally) that sum of per-polygon weighted volumes matches
    integrate_volume(idx=None) (within tolerance). Not printed by default.
debug_tol:
    Absolute tolerance used for the internal check.

Returns
-------
Dict[str, Any] with keys:
  - "z1", "z2", "n_points"
  - "rows": list of dict rows (one per polygon)
  - "tot_occ", "tot_hom"
  - "debug": dict (only meaningful if do_debug_check=True)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `'ContinuousSectionField'` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `z2` | `positional or keyword` | `float` | `-` |
| `n_points` | `positional or keyword` | `int` | `20` |
| `do_debug_check` | `keyword-only` | `bool` | `False` |
| `debug_tol` | `keyword-only` | `float` | `1e-09` |

**Returns:** `Dict[str, Any]`

**Returned dictionary keys visible in the code**

`z1`, `z2`, `n_points`, `rows`, `tot_occ`, `tot_hom`, `debug`, `enabled`, `v_total`, `sum_hom`, `delta`, `abs_tol`, `ok`, `id`, `s0_w`, `s1_w`, `weight_law`, `s0_name`, `s1_name`, `volume_occupied`, `homogenized_volume_occupied`

**Function/method calls visible in the code**

`float`, `field.inspect_section_entities`, `min`, `max`, `range`, `len`, `str`, `r1.get`, `integrate_volume`, `rows.append`, `int`, `r2.get`, `abs`, `bool`

## Per requirement: compare against weighted sum (homogenized column).

### `volume_polygon_list_report`

**Source lines:** `4469-4516`

```python
def volume_polygon_list_reportfield: ContinuousSectionField, z1: float, z2: float, *, n_points: int=20, outputs: list[Any] | None=None, fmt_display: str='0.6f', w_tol: float=0.0, do_debug_check: bool=False, debug_tol: float=1e-09
```

**Summary:** High-level API: build and emit the per-polygon volume report.

**Docstring details**

```text
This is a convenience wrapper around:
  - volume_polygon_list_report_data(...)
  - emit_volume_polygon_list_report(...)

Rules
-----
- No extra validation or assumptions are introduced here.
- Volumes come from integrate_volume (via volume_polygon_list_report_data).
- Metadata comes from field inspection (via volume_polygon_list_report_data).

Returns
-------
The report dict returned by volume_polygon_list_report_data(...).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `ContinuousSectionField` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `z2` | `positional or keyword` | `float` | `-` |
| `n_points` | `keyword-only` | `int` | `20` |
| `outputs` | `keyword-only` | `list[Any] | None` | `None` |
| `fmt_display` | `keyword-only` | `str` | `'0.6f'` |
| `w_tol` | `keyword-only` | `float` | `0.0` |
| `do_debug_check` | `keyword-only` | `bool` | `False` |
| `debug_tol` | `keyword-only` | `float` | `1e-09` |

**Returns:** `dict[str, Any]`

**Function/method calls visible in the code**

`volume_polygon_list_report_data`, `emit_volume_polygon_list_report`, `float`, `int`, `bool`, `str`

## Emit report to requested outputs (stdout/text/CSV)

### `emit_volume_polygon_list_report`

**Source lines:** `4519-4677`

```python
def emit_volume_polygon_list_reportreport: Dict[str, Any], *, outputs: List[Any] | None=None, fmt_display: str='0.6f', w_tol: float=0.0
```

**Summary:** Emit a volume polygon-list report (stdout/text/CSV) using the same formatting as actions.volume.

**Docstring details**

```text
Parameters
----------
report:
    Object returned by volume_polygon_list_report_data(...).
outputs:
    Output routing. If None/empty -> ["stdout"].
    - "stdout" prints the report.
    - any other string path:
        * ".csv" writes the CSV with the same field names as actions.volume
        * otherwise writes the text report.
fmt_display:
    Numeric formatting string passed to built-in format(...).
w_tol:
    Report header value (kept for backward compatibility; may be unused by the action logic).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `report` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `outputs` | `keyword-only` | `List[Any] | None` | `None` |
| `fmt_display` | `keyword-only` | `str` | `'0.6f'` |
| `w_tol` | `keyword-only` | `float` | `0.0` |

**Returns:** `None`

**Returned dictionary keys visible in the code**

`z1`, `z2`, `id`, `s0_w`, `s1_w`, `weight_law`, `s0_name`, `s1_name`, `volume_occupied`, `homogenized_volume_occupied`, `n_points`

**Raises visible in the code**

- `RuntimeError`

**Function/method calls visible in the code**

`float`, `int`, `list`, `any`, `isinstance`, `str`, `max`, `io.StringIO`, `report_blocks.append`, `Path`, `len`, `redirect_stdout`, `print`, `buf.getvalue`, `csv_rows.append`, `p.parent.exists`, `RuntimeError`, `p.suffix.lower`, `format`, `open`, `csv.DictWriter`, `w.writeheader`, `suffix.lower`, `w.writerow`, `f.write`, `_fmt`, `blk.endswith`

## adjust only the extraction line where we read the area.

### `integrate_volume`

**Source lines:** `4704-4812`

```python
def integrate_volumefield: 'ContinuousSectionField', z0: float, z1: float, n_points: int=20, *, idx: int | None=None
```

**Summary:** Integrate "volume-like" quantities over [z0, z1] using Gauss–Legendre quadrature.

**Docstring details**

```text
Two scenarios only
------------------
1) idx is None (LEGACY):
     Returns a single float:
       V_legacy = ∫ A_global(z) dz
     where A_global(z) is taken from:
       section_properties(field.section(z))["A"]
     (This preserves the existing legacy meaning: global area as defined by section_properties.)

2) idx is an int (0-based):
     Returns a tuple of two floats:
       (V_geom, V_weighted)
     computed for ONE polygon only, using the "occupied surface" rule:
       - polygon has w=1
       - direct inners have w=0

     At each z we use polygon_surface_w1_inners0[_single] to get:
       A_net(z) = occupied surface (w=1 on polygon, w=0 on direct inners)
       A_w(z)   = A_net(z) * w_eff(z)

     Then:
       V_geom     = ∫ A_net(z) dz
       V_weighted = ∫ A_w(z) dz

Notes
-----
- In idx mode we DO NOT call section_properties(...) to avoid mixing global weighted section logic.
- Integration uses |z1 - z0| so results are positive "volumes" regardless of interval direction.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `'ContinuousSectionField'` | `-` |
| `z0` | `positional or keyword` | `float` | `-` |
| `z1` | `positional or keyword` | `float` | `-` |
| `n_points` | `positional or keyword` | `int` | `20` |
| `idx` | `keyword-only` | `int | None` | `None` |

**Returns:** `float | tuple[float, float]`

**Raises visible in the code**

- `ValueError`
- `TypeError`

**Function/method calls visible in the code**

`float`, `abs`, `np.polynomial.legendre.leggauss`, `zip`, `ValueError`, `isinstance`, `TypeError`, `polygon_surface_w1_inners0_single`, `field.section`, `section_properties`, `_poly_A_pair_at_z`, `type`

## A_w(z)  : A_net(z) * w_eff(z)

### `section_full_analysis`

**Source lines:** `4814-4904`

```python
def section_full_analysissection: Section, compute_vroark=True
```

**Summary:** Perform a complete geometric and sectional analysis of a cross-section.

**Docstring details**

```text
The routine combines basic sectional properties with derived quantities such
as principal inertias, elastic section moduli, first statical moment at the
neutral axis, and selected torsional estimates.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `Section` | `-` |
| `compute_vroark` | `positional or keyword` | `not annotated` | `True` |

**Returns:** `not annotated`

**Function/method calls visible in the code**

`section_properties`, `section_derived_properties`, `section_statical_moment_partial`, `compute_saint_venant_J_cell`, `compute_saint_venant_J_wall`, `max`, `compute_saint_venant_Jv2`, `min`

## Return a single dictionary containing both base and derived properties.

### `polygon_statical_moment`

**Source lines:** `4906-4919`

```python
def polygon_statical_momentpoly: Polygon, y_axis: float
```

**Summary:** Computes the First Moment of Area (Statical Moment), Q, of a SINGLE polygon

**Docstring details**

```text
relative to a specific horizontal axis (y_axis).

TECHNICAL NOTES:
- Formula: Q = Area * (y_centroid - y_axis)
- Sign Convention: Positive if the polygon centroid is above the reference axis.
- Homogenization: Uses weighted area to account for holes or material density.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `positional or keyword` | `Polygon` | `-` |
| `y_axis` | `positional or keyword` | `float` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`polygon_area_centroid`

## Distance from the polygon centroid to the reference axis

### `section_statical_moment_partial`

**Source lines:** `4921-5004`

```python
def section_statical_moment_partialsection: Section, y_cut: float, reference_axis: float | None=None
```

**Summary:** Compute the statical moment Q of the portion of the section located ABOVE y_cut,

**Docstring details**

```text
with respect to a horizontal reference axis y = y_ref.

The section is processed polygon-by-polygon:
- Each polygon is clipped by the half-plane y >= y_cut.
- For the retained part, we compute its area and centroid.
- We accumulate Q = A_part * (Cy_part - y_ref), using signed area if the polygon
  representation supports signed contributions (e.g., holes via orientation/sign).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `Section` | `-` |
| `y_cut` | `positional or keyword` | `float` | `-` |
| `reference_axis` | `positional or keyword` | `float | None` | `None` |

**Returns:** `float`

**Function/method calls visible in the code**

`section_properties`, `len`, `range`, `all`, `Polygon`, `polygon_area_centroid`, `abs`, `clipped.append`, `tuple`, `Pt`

## Statical moment contribution of this clipped part about y = y_ref.

### `section_derived_properties`

**Source lines:** `5007-5070`

```python
def section_derived_propertiesprops: Dict[str, float]
```

**Summary:** Computes derived structural properties including principal moments of inertia,

**Docstring details**

```text
principal axis rotation, and radius of gyration.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `props` | `positional or keyword` | `Dict[str, float]` | `-` |

**Returns:** `Dict[str, float]`

**Returned dictionary keys visible in the code**

`I1`, `I2`, `theta_rad`, `theta_deg`, `rx`, `ry`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`math.sqrt`, `math.degrees`, `ValueError`, `abs`, `math.atan2`

## Stiffness Matrix Calculation

### `section_stiffness_matrix`

**Source lines:** `5079-5142`

```python
def section_stiffness_matrixsection: Section, E_ref: float=1.0
```

**Summary:** Assembles the 3x3 constitutive stiffness matrix relating generalized

**Docstring details**

```text
strains to internal forces (N, Mx, My).

   TECHNICAL SUMMARY:
   This function performs a numerical integration over the composite 
   polygonal domain to compute the sectional stiffness properties relative 
   to the global origin (0,0). It accounts for multi-material homogenization 
   via the polygon weighting system.

   STIFFNESS MATRIX FORMULATION:
   The resulting matrix K maps the axial strain (epsilon) and curvatures 
   (kappa_x, kappa_y) to the Resultant Normal Force (N) and Bending Moments (Mx, My):
   
       [ N  ]   [ EA    ESx   -ESy  ] [ epsilon ]
       [ Mx ] = [ ESx   EIxx  -EIxy ] [ kappa_x ]
       [ My ]   [ -ESy -EIxy   EIyy ] [ kappa_y ]

   COMPUTATIONAL STRATEGY:
   1. Fan Triangulation: 
      Each polygon is decomposed into triangles using a "fan" approach, 
      with the first vertex (v0) acting as the common pivot.
      
   2. Numerical Integration (Gauss Quadrature):
      For each triangular sub-domain, the function calls the Gaussian 
      integrator to retrieve optimal sampling points.
      
   3. Contribution Mapping:
      At each Gauss point (x, y) with differential area dA:
      - Axial Stiffness (EA): Σ E * dA
      - First Moments (ESx, ESy): Σ E * y * dA and Σ E * x * dA
      - Second Moments (EIxx, EIyy, EIxy): Σ E * y^2 * dA, Σ E * x^2 * dA, 
        and Σ E * x * y * dA.

   4. Homogenization:
      The 'poly.weight' parameter scales the reference Young's Modulus (E_ref), 
      allowing for the modeling of hollow sections (negative weights) or 
      composite structures with varying material stiffness.

   5. Symmetrization:
      Enforces the Maxwell-Betti reciprocal theorem by ensuring K[i,j] = K[j,i].

   RETURNS:
      A 3x3 NumPy array representing the cross-sectional stiffness tensor.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `Section` | `-` |
| `E_ref` | `positional or keyword` | `float` | `1.0` |

**Returns:** `np.ndarray`

**Function/method calls visible in the code**

`section_properties`, `props.get`, `np.array`

## E_ref acts as the global Young's Modulus scale.

### `_segments_intersect`

**Source lines:** `5144-5193`

```python
def _segments_intersectp1, p2, p3, p4
```

**Summary:** Determines if two finite line segments (p1-p2 and p3-p4) intersect in a 2D plane.

**Docstring details**

```text
TECHNICAL SUMMARY:
This function implements a robust geometric intersection test based on the 
'Orientation Test' (cross-product method). It is primarily used to detect 
self-intersections in homogenized polygons, ensuring the topological integrity 
of the cross-sectional boundaries.

MATHEMATICAL FORMULATION:
1. Orientation Primitive:
   The inner 'orient' function computes the signed area of the triangle formed 
   by points (a, b, c). 
   - If Result > 0: The sequence (a, b, c) is Counter-Clockwise (CCW).
   - If Result < 0: The sequence is Clockwise (CW).
   - If Result = 0: The points are Collinear.

2. Relative Orientation Logic:
   For two segments to intersect, the endpoints of each segment must lie on 
   opposite sides of the line defined by the other segment.
   - o1, o2 check points p3 and p4 relative to line p1-p2.
   - o3, o4 check points p1 and p2 relative to line p3-p4.

3. Intersection Criterion:
   The condition (o1 * o2 < 0) and (o3 * o4 < 0) identifies a 'Proper Intersection'.
   This occurs when the endpoints strictly straddle the opposing lines, 
   excluding collinear overlaps or shared endpoints to maintain computational 
   stability during polygon validation.

APPLICABILITY IN RULED SURFACE MODELING:
By preventing self-intersecting polygons, this function ensures that the 
Shoelace formula and Gaussian integration yield physically consistent results 
for the area and inertia of the tower sections.

RETURNS:
   - True: If segments p1-p2 and p3-p4 intersect.
   - False: Otherwise.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `p1` | `positional or keyword` | `not annotated` | `-` |
| `p2` | `positional or keyword` | `not annotated` | `-` |
| `p3` | `positional or keyword` | `not annotated` | `-` |
| `p4` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`orient`

## (i=0 edge is adjacent to the last edge).

### `get_points_distance`

**Source lines:** `5297-5321`

```python
def get_points_distancepolygon: Polygon, i: int, j: int
```

**Summary:** Calculates the Euclidean distance between vertex i and vertex j of a polygon.

**Docstring details**

```text
Indices i and j are 1-based (from 1 to N).

This can measure sides (if i, j are consecutive) or diagonals/distances 
between any two nodes of the polygon.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon` | `positional or keyword` | `Polygon` | `-` |
| `i` | `positional or keyword` | `int` | `-` |
| `j` | `positional or keyword` | `int` | `-` |

**Returns:** `float`

**Raises visible in the code**

- `IndexError`

**Function/method calls visible in the code**

`len`, `math.sqrt`, `IndexError`

## Core: Continuous section field (geometry-only)

### `get_edge_length`

**Source lines:** `5326-5342`

```python
def get_edge_lengthpolygon: Polygon, edge_idx: int
```

**Summary:** Calculates the length of the j-th edge of a polygon.

**Docstring details**

```text
edge_idx is 1-based (1 to N).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polygon` | `positional or keyword` | `Polygon` | `-` |
| `edge_idx` | `positional or keyword` | `int` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`len`, `math.sqrt`

## Edge j connects vertex j-1 to vertex j

### `list_polygons_with_contents`

**Source lines:** `5345-5473`

```python
def list_polygons_with_contentscsf: ContinuousSectionField, z: float
```

**Summary:** Return one record per polygon at coordinate z, including direct containment.

**Docstring details**

```text
Structural rules:
- polygon identity is strictly the local index in sec.polygons
- names are output labels only
- topology is consumed strictly as index-based data

Output fields:
  - idx (int): polygon index in the sampled section ordering at z
  - name (str | None): cleaned polygon label for output only
  - container_idx (int | None): direct container index, or None for a root polygon
  - container_name (str | None): cleaned label of the direct container, or None
  - direct_children_idx (List[int]): direct child indices
  - direct_children (List[str | None]): cleaned labels of the direct children
  - is_container (bool): True if the polygon has at least one direct child

Raises:
- TypeError / ValueError only for structural issues
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `csf` | `positional or keyword` | `ContinuousSectionField` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `List[Dict[str, Any]]`

**Returned dictionary keys visible in the code**

`idx`, `name`, `container_idx`, `container_name`, `direct_children_idx`, `direct_children`, `is_container`

**Raises visible in the code**

- `TypeError`
- `ValueError`

**Function/method calls visible in the code**

`csf.section`, `enumerate`, `csf.build_direct_children_map`, `children_idx_map.items`, `range`, `isinstance`, `TypeError`, `float`, `ValueError`, `hasattr`, `len`, `out.append`, `list`, `direct_children_labels.append`, `type`

## w_eff = w_eff_by_idx[idx]

### `polygon_surface_w1_inners0_single`

**Source lines:** `5683-5895`

```python
def polygon_surface_w1_inners0_singleself: ContinuousSectionField, z: float, idx: int
```

**Summary:** Compute the local occupied surface for one polygon at coordinate z using the rule:

**Docstring details**

```text
- w(polygon) = 1
  - w(direct inners) = 0

And its weighted counterpart:
  - A_w = A * w_eff

Structural rules:
- all topology, validation, and calculations are strictly index-based
- names are output labels only
- names must never trigger errors or logic branches

Required upstream structural fields:
- list_polygons_with_contents(self, z):
    * idx
    * container_idx
    * direct_children_idx
- self.inspect_section_entities(z):
    * idx
    * area_signed
    * weight_at_z

Output fields:
  - idx (int)
  - name (str | None)
  - container_name (str | None)
  - direct_inners (List[str | None])
  - w (float)
  - A (float)
  - A_w (float)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `ContinuousSectionField` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `idx` | `positional or keyword` | `int` | `-` |

**Returns:** `Dict[str, Any]`

**Returned dictionary keys visible in the code**

`idx`, `name`, `container_name`, `direct_inners`, `w`, `A`, `A_w`

**Raises visible in the code**

- `TypeError`
- `ValueError`
- `AttributeError`

**Function/method calls visible in the code**

`float`, `list_polygons_with_contents`, `enumerate`, `self.inspect_section_entities`, `set`, `isinstance`, `TypeError`, `ValueError`, `list`, `hasattr`, `AttributeError`, `visited.add`, `direct_inners_labels.append`, `type`

## Single export mode

### `export_polygon_vertices_csv`

**Source lines:** `5955-6152`

```python
def export_polygon_vertices_csvsection: Section=None, field: ContinuousSectionField=None, zpos: float=None, put=print, fmt='{:.16g}'
```

**Summary:** Export CSV with ALL coordinates.

**Docstring details**

```text
One row per vertex (recommended for CSV):
idx_polygon, idx_container, s0_name, s1_name, w, vertex_i, x, y

Sources:
- geometry: section.polygons -> poly.name, poly.vertices (Pt has .x .y)
- container + names: entities[*] by polygon name
- w: area_w["groups"][*]["w"] mapped by polygon name

Parameters
----------
fmt : str
    Python format string for floats, e.g. "{:.6f}", "{:.6g}", "{:.16g}".
    Applied to: w, x, y (when they are not None).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `Section` | `None` |
| `field` | `positional or keyword` | `ContinuousSectionField` | `None` |
| `zpos` | `positional or keyword` | `float` | `None` |
| `put` | `positional or keyword` | `not annotated` | `print` |
| `fmt` | `positional or keyword` | `not annotated` | `'{:.16g}'` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`field.section_area_by_weight`, `field.inspect_section_entities`, `build_w_by_idx`, `fmt.format`, `put`, `named_polys.values`, `polys_by_idx.values`, `name.lower`, `ValueError`, `field.section`, `any`, `isinstance`, `_apply_fmt`, `float`, `join`, `ent_by_name.get`, `ent.get`, `w_by_idx.get`, `shear_w_by_idx.get`, `math.isnan`, `enumerate`, `getattr`, `str`, `format`, `poisson_by_idx.get`, `min`, `fmt_num`, `low.find`, `s.replace`, `esc`

## put(",".join(esc(v) for v in row))

### `section_properties`

**Source lines:** `6156-6259`

```python
def section_propertiessection: Section
```

**Summary:** Computes the integral geometric properties for a composite cross-section.

**Docstring details**

```text
TECHNICAL SUMMARY:
This function performs a multi-pass integration over a set of weighted 
polygons to derive the global geometric constants. It manages homogenization 
by algebraically summing contributions, allowing for the representation of 
complex domains with voids or varying material densities.

ALGORITHMIC WORKFLOW:
1. First-Order Moments (Area and Centroid):
   - Aggregates the weighted area (A) and the first moments of area (Qx, Qy) 
     for all constituent polygons.
   - Locates the global centroid (Cx, Cy) of the composite section.

2. Second-Order Moments (Inertia about Origin):
   - Computes the area moments of inertia (Ix, Iy) and the product of 
     inertia (Ixy) relative to the global coordinate origin (0,0).

3. Translation of Axes (Parallel Axis Theorem):
   - Applies the Huygens-Steiner Theorem to shift the moments of inertia 
     from the global origin to the newly calculated centroidal axes:
     I_centroid = I_origin - A * d^2
   - This transformation ensures the properties are intrinsic to the 
     section's geometry, independent of the global coordinate system.

4. Polar Moment Extraction:
   - Derives the Polar Second Moment of Area (J) about the centroid as 
     the sum of the orthogonal centroidal moments (Ix + Iy).

RETURNS:
   A comprehensive dictionary containing:
   - 'A': Net weighted area.
   - 'Cx', 'Cy': Centroidal coordinates.
   - 'Ix', 'Iy', 'Ixy': Second moments of area about centroidal axes.
   - 'Ip': Polar moment of area.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `Section` | `-` |

**Returns:** `Dict[str, float]`

**Returned dictionary keys visible in the code**

`z`, `A`, `Cx`, `Cy`, `Ix`, `Iy`, `Ixy`, `Ip`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`polygon_area_centroid`, `poly_cache.append`, `abs`, `ValueError`, `polygon_inertia_about_origin`

## Parallel axis theorem to centroid

### `_polygon_signed_area_and_centroid`

**Source lines:** `6263-6271`

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

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
