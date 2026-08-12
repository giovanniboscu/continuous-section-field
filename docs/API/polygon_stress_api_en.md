# API Reference - `polygon_stress.py`

This document covers the top-level classes and functions defined in `src/csf/polygon_stress.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/polygon_stress.py`
- Output file: `docs/API/polygon_stress_api_en.md`
- Top-level function definitions found: `73`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Module docstring

```text
Polygon-level stress analyses for a continuous section field.

The public functions are re-exported by :mod:`csf.section_field` so existing
imports from that module remain valid. Imports back into ``section_field``
are local to function calls to avoid a module-import cycle.
```

## Public API index

- `def analyse_polygon_centroid_axis_shearsection_field, z: float, Mx: float, My: float, *, dz: float | None=None, derivative_rtol: float=1e-08, derivative_atol: float=1e-10, max_refinements: int=20, debug: bool=False` - line 18
- `def _section_active_bboxsection: Section` - line 450
- `def _jourawski_global_axis_scan*, original_section: Section, transformed_section: Section, axis: str, coord_min: float, coord_max: float, num_subdivisions: int, Cx: float, Cy: float, dbx: float, dby: float` - line 469
- `def _jourawski_value_at_coord*, original_section: Section, transformed_section: Section, axis: str, coord: float, Cx: float, Cy: float, dbx: float, dby: float` - line 515
- `def _section_active_cut_width_and_polygons*, section: Section, axis: str, coord: float` - line 590
- `def _group_scan_values_by_polygon*, scan_values: list[dict[str, object]], polygon_count: int` - line 663
- `def _jourawski_polygon_shear_weightabspoly: Polygon` - line 703
- `def _jourawski_polygon_is_active_for_bpoly: Polygon` - line 718
- `def _jourawski_normalized_sectionsection: Section` - line 726
- `def _jourawski_reference_weightabssection: Section` - line 751
- `def _section_partial_first_moments*, section: Section, axis: str, coord: float, Cx: float, Cy: float` - line 760
- `def _clip_polygon_half_plane*, poly: Polygon, axis: str, coord: float` - line 798
- `def _interpolate_point_on_segmentp1: Pt, p2: Pt, t: float` - line 837
- `def _polygon_area_from_pointspoints: list[Pt]` - line 844
- `def _cut_edge_tc1: float, c2: float, coord: float` - line 859
- `def _polygon_line_segments*, poly: Polygon, axis: str, coord: float` - line 873
- `def _unique_sortedvalues: list[float]` - line 914
- `def _mean_scan_tauvalues: list[dict[str, object]]` - line 926
- `def _empty_scan_value` - line 933
- `def _min_scan_valuevalues: list[dict[str, object]]` - line 955
- `def _max_scan_valuevalues: list[dict[str, object]]` - line 961
- `def analyse_polygon_jourawski_shear_stresssection_field, z: float, Tx: float, Ty: float, *, num_sudx: int=30, num_sudy: int=30, debug: bool=False` - line 967
- `def _jourawski_v2_positive_half_plane_resultant*, section_field, z: float, N: float, Mx: float, My: float, axis: str, coord: float` - line 1424
- `def analyse_jourawski_shear_stress_v2section_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, *, dN_dz: float=0.0, num_sudx: int=30, num_sudy: int=30, cut_coords_x: list[float] | tuple[float, ...] | None=None, cut_coords_y: list[float] | tuple[float, ...] | None=None, dz: float | None=None, debug: bool=False` - line 1532
- `def _navier_section_statesection_field, z: float, N: float, Mx: float, My: float` - line 1808
- `def _navier_sigma_at_point*, poly: Polygon, x: float, y: float, state: dict[str, object]` - line 1861
- `def _clip_points_half_plane*, points: list[Pt], axis: str, coord: float, keep_positive: bool` - line 1886
- `def _clip_polygon_quadrant*, poly: Polygon, x: float, y: float, x_positive: bool, y_positive: bool` - line 1951
- `def _polygon_area_centroid_from_pointspoints: list[Pt]` - line 1985
- `def _navier_resultant_over_points*, poly: Polygon, points: list[Pt], state: dict[str, object]` - line 2015
- `def _navier_quadrant_resultant*, poly: Polygon, state: dict[str, object], x: float, y: float, x_positive: bool, y_positive: bool` - line 2050
- `def analyse_navier_four_quadrant_resultantssection_field, z: float, N: float, Mx: float, My: float, x: float, y: float` - line 2074
- `def analyse_navier_four_quadrant_resultant_derivativessection_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, x: float, y: float, *, dN_dz: float=0.0, dz: float | None=None, derivative_rtol: float=1e-08, derivative_atol: float=1e-08, max_refinements: int=20` - line 2273
- `def _potential_polygon_geometrypoly: Polygon` - line 2710
- `def _potential_polygon_componentsgeometry` - line 2750
- `def _potential_children_mapsection_field, z: float, polygon_count: int` - line 2774
- `def _potential_occupied_regionssection_field, z: float` - line 2820
- `def _potential_signed_triangle_areapoints` - line 2969
- `def _potential_initial_trianglesregions: list[dict[str, object]]` - line 2985
- `def _potential_refine_trianglestriangles: list[dict[str, object]], refinements: int` - line 3077
- `def _potential_refine_triangles_comb_controlledtriangles: list[dict[str, object]], section_field, z: float, *, num_sudx: int, num_sudy: int` - line 3142
- `def _plot_potential_mesh_controlled*, section_field, z: float, nodes, connectivity, initial_triangle_count: int, refinement_info: dict[str, object]` - line 3413
- `def evaluate_navier_local_shear_potential_triangle_fieldsolution: dict[str, object], *, x: float, y: float, polygon_idx: int | None=None` - line 3463
- `def _potential_triangle_direct_csf_meshsection_field, z: float, regions: list[dict[str, object]], *, max_triangle_area: float | None=None, min_angle: float | None=None` - line 3557
- `def _plot_potential_mesh_triangle*, section_field, z: float, mesh: dict[str, object]` - line 4224
- `def _potential_merge_meshtriangles: list[dict[str, object]]` - line 4284
- `def _plot_potential_mesh*, section_field, z: float, nodes, connectivity, initial_triangle_count: int, mesh_refinements: int` - line 4371
- `def _potential_comb_gridsection_field, z: float, *, num_sudx: int, num_sudy: int` - line 4425
- `def _potential_comb_network_nodessection_field, z: float, *, num_sudx: int, num_sudy: int` - line 4575
- `def plot_navier_local_shear_potential_comb_nodessection_field, z: float, *, num_sudx: int=20, num_sudy: int=20` - line 4715
- `def _potential_comb_merge_nodesnetwork: dict[str, object]` - line 4864
- `def _potential_comb_region_membership*, nodes, regions: list[dict[str, object]], tolerance: float` - line 4906
- `def _potential_comb_point_segment_distance*, x: float, y: float, p0: tuple[float, float], p1: tuple[float, float]` - line 4949
- `def _potential_comb_region_outward_normalgeometry, *, x: float, y: float, tolerance: float` - line 4976
- `def _potential_comb_gfd_weights*, query_point: tuple[float, float], region_node_indices, nodes, tree, operator: str, normal: tuple[float, float] | None=None, stencil_size: int=12, max_stencil_size: int=40` - line 5061
- `def analyse_navier_local_shear_potential_combsection_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, *, dN_dz: float=0.0, dz: float | None=None, num_sudx: int=5, num_sudy: int=5, stencil_size: int=12, max_stencil_size: int=40, solver_atol: float=1e-10, solver_btol: float=1e-10, solver_maxiter: int | None=None` - line 5185
- `def evaluate_navier_local_shear_potential_combresult: dict[str, object], *, x: float, y: float, polygon_idx: int | None=None` - line 5593
- `def plot_navier_local_shear_potential_combsection_field, z: float, *, num_sudx: int=20, num_sudy: int=20` - line 5667
- `def _potential_triangle_area_gradientspoints` - line 5771
- `def _potential_derivative_contextsection_field, *, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, dz: float | None` - line 5813
- `def _potential_sigma_z_at_pointderivative_context: dict[str, object], *, polygon_idx: int, x: float, y: float` - line 6010
- `def _potential_point_segment_parameter*, x: float, y: float, p0: Pt, p1: Pt` - line 6052
- `def _potential_boundary_velocity_at_pointderivative_context: dict[str, object], *, x: float, y: float, geometry_tolerance: float` - line 6092
- `def _potential_edge_normal_from_triangle*, p0, p1, triangle_centroid` - line 6175
- `def _potential_edge_normal_between_triangles*, p0, p1, centroid_i, centroid_j` - line 6212
- `def _potential_mesh_edgesconnectivity` - line 6246
- `def _potential_connected_components*, node_count: int, connectivity` - line 6274
- `def _potential_triangle_cut_intervalpoints, *, axis: str, value: float, tolerance: float` - line 6319
- `def _potential_partial_chord_flowstriangle_rows: list[dict[str, object]], *, x: float, y: float, tolerance: float` - line 6386
- `def analyse_navier_local_shear_potential_triangle_meshsection_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, *, dN_dz: float=0.0, dz: float | None=None, max_triangle_area: float | None=None, min_angle: float | None=None, plot_mesh: bool=False, validation_points: tuple[tuple[float, float], ...] | None=None, compatibility_rtol: float=1e-08, compatibility_atol: float=1e-06` - line 6477
- `def analyse_navier_local_shear_potential_controlled_meshsection_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, *, dN_dz: float=0.0, dz: float | None=None, num_sudx: int=5, num_sudy: int=5, plot_mesh: bool=False, validation_points: tuple[tuple[float, float], ...] | None=None, compatibility_rtol: float=1e-08, compatibility_atol: float=1e-06` - line 7383
- `def analyse_navier_local_shear_potentialsection_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, *, dN_dz: float=0.0, dz: float | None=None, mesh_refinements: int=4, plot_mesh: bool=False, validation_points: tuple[tuple[float, float], ...] | None=None, compatibility_rtol: float=1e-08, compatibility_atol: float=1e-06` - line 8271
- `def analyse_polygon_navier_stresssection_field, z: float, N: float, Mx: float, My: float` - line 9134

## API details

## Functions

## Top-level functions

### `analyse_polygon_centroid_axis_shear`

**Source lines:** `18-447`

```python
def analyse_polygon_centroid_axis_shearsection_field, z: float, Mx: float, My: float, *, dz: float | None=None, derivative_rtol: float=1e-08, derivative_atol: float=1e-10, max_refinements: int=20, debug: bool=False
```

**Summary:** Compute the flexural centroid-axis shear contribution.

**Docstring details**

```text
The adopted reduced formulation is:

    tau_x = sigma_zz_M * dCx/dz
    tau_y = sigma_zz_M * dCy/dz

where ``sigma_zz_M`` is the Navier stress generated only by ``Mx`` and
``My``. The axial-force contribution is excluded by evaluating Navier
stresses with ``N=0``.

The resulting centroid-axis shear field is self-equilibrated:

    integral_A(tau_x dA) = 0
    integral_A(tau_y dA) = 0

The global centroid is calculated from the complete axial-flexural CSF
section. Centroid values are cached per ``section_field`` and station.

No Jourawski contribution is calculated by this function.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `Mx` | `positional or keyword` | `float` | `-` |
| `My` | `positional or keyword` | `float` | `-` |
| `dz` | `keyword-only` | `float | None` | `None` |
| `derivative_rtol` | `keyword-only` | `float` | `1e-08` |
| `derivative_atol` | `keyword-only` | `float` | `1e-10` |
| `max_refinements` | `keyword-only` | `int` | `20` |
| `debug` | `keyword-only` | `bool` | `False` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`z`, `Mx`, `My`, `Cx`, `Cy`, `dCx_dz`, `dCy_dz`, `section`, `polygons`, `step`, `derivative_scheme`, `derivative_dz_mode`, `derivative_converged`, `derivative_refinements`, `derivative_change_x`, `derivative_change_y`, `idx`, `name`, `weightabs`, `sigma_min`, `x_sigma_min`, `y_sigma_min`, `sigma_max`, `x_sigma_max`, `y_sigma_max`, `sigma_extreme`, `x_sigma_extreme`, `y_sigma_extreme`, `tau_governing`, `tau_governing_direction`, `tau_governing_bound`, `x_tau_governing`, `y_tau_governing`, `derivative_step`

**Raises visible in the code**

- `ValueError`
- `RuntimeError`

**Function/method calls visible in the code**

`float`, `int`, `max`, `getattr`, `centroid_cache.get`, `analyse_polygon_navier_stress`, `ValueError`, `weakref.WeakKeyDictionary`, `setattr`, `_global_centroid`, `_sample_derivative`, `range`, `RuntimeError`, `min`, `_converged_derivative`, `derivative.update`, `_scale_extrema`, `polygon_rows.append`, `section_result.update`, `math.isfinite`, `section_full_analysis`, `abs`, `section_field.section`, `current.update`, `str`

### `_section_active_bbox`

**Source lines:** `450-467`

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

**Source lines:** `469-512`

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

**Source lines:** `515-586`

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

**Source lines:** `590-660`

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

**Source lines:** `663-700`

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

**Source lines:** `703-715`

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

**Source lines:** `718-723`

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

**Source lines:** `726-748`

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

**Source lines:** `751-757`

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

**Source lines:** `760-795`

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

**Source lines:** `798-835`

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

**Source lines:** `837-841`

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

**Source lines:** `844-856`

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

**Source lines:** `859-871`

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

**Source lines:** `873-910`

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

**Source lines:** `914-923`

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

**Source lines:** `926-930`

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

**Source lines:** `933-953`

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

**Source lines:** `955-958`

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

**Source lines:** `961-964`

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

### `analyse_polygon_jourawski_shear_stress`

**Source lines:** `967-1421`

```python
def analyse_polygon_jourawski_shear_stresssection_field, z: float, Tx: float, Ty: float, *, num_sudx: int=30, num_sudy: int=30, debug: bool=False
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
The scan teeth are the minimum and maximum coordinates of every polygon
bounding box, limited to the active-section bounding box.

Along x:
    x_teeth = sorted unique polygon xmin/xmax coordinates

Along y:
    y_teeth = sorted unique polygon ymin/ymax coordinates

The scan coordinates are the union of two independent schemes.

Global uniform scan:
    num_sudx cell centres over the full active x bounding-box interval
    num_sudy cell centres over the full active y bounding-box interval

Local one-sided tooth concentration:
    deltaX_i = interval_length_x / (2 * num_sudx**2)
    deltaY_i = interval_length_y / (2 * num_sudy**2)

For every interval between two consecutive teeth, additional coordinates
are placed at geometrically increasing distances:

    delta, 2*delta, 4*delta, ...

from both interval ends. Exact tooth coordinates are not evaluated.
Duplicate coordinates from the global and local schemes are
tolerance-deduplicated.

Polygon bounding boxes are used only to construct the scan coordinates.
The Jourawski calculation, active cut width, partial first moments and
shear-carrier redistribution remain unchanged.

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
| `num_sudx` | `keyword-only` | `int` | `30` |
| `num_sudy` | `keyword-only` | `int` | `30` |
| `debug` | `keyword-only` | `bool` | `False` |

**Returns:** `list[dict[str, object]]`

**Returned dictionary keys visible in the code**

`idx`, `name`, `weight`, `weight_ref`, `weight_norm`, `tau_x_min`, `x_tau_x_min`, `y_tau_x_min`, `tau_x_max`, `x_tau_x_max`, `y_tau_x_max`, `tau_y_min`, `x_tau_y_min`, `y_tau_y_min`, `tau_y_max`, `x_tau_y_max`, `y_tau_y_max`, `coord_tau_y_max`, `tau_reference_y_max`, `b_weighted_y_max`, `Sx_part_y_max`, `Sy_part_y_max`, `tau_x_mean`, `tau_y_mean`, `scan_count_x`, `scan_count_y`, `grid_x`, `grid_y`, `converged_x`, `converged_y`, `relative_change_x`, `relative_change_y`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`int`, `section_field.section`, `_jourawski_normalized_section`, `section_properties`, `float`, `_section_active_bbox`, `_axis_teeth`, `_global_uniform_coords`, `_local_concentrated_coords_between_teeth`, `_sorted_unique_coords`, `_scan_axis`, `_group_scan_values_by_polygon`, `enumerate`, `ValueError`, `abs`, `sorted`, `range`, `zip`, `print`, `str`, `_min_scan_value`, `_max_scan_value`, `rows.append`, `min`, `max`, `teeth.append`, `len`, `any`, `coords.append`, `_jourawski_value_at_coord`, `unique_values.append`, `scan_values.append`, `_mean_scan_tau`, `bool`, `math.isfinite`

### `_jourawski_v2_positive_half_plane_resultant`

**Source lines:** `1424-1529`

```python
def _jourawski_v2_positive_half_plane_resultant*, section_field, z: float, N: float, Mx: float, My: float, axis: str, coord: float
```

**Summary:** Integrate the Navier longitudinal resultant on one positive half-plane.

**Docstring details**

```text
For ``axis == "y"`` the retained region is ``Y >= coord``.
For ``axis == "x"`` the retained region is ``X >= coord``.

The integration uses the same affine Navier field as
:func:`analyse_polygon_navier_stress` and follows the CSF occupied-region
rule for nested polygons, so direct children are subtracted from the parent
with the parent Navier field and are then added with their own field.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `keyword-only` | `not annotated` | `-` |
| `z` | `keyword-only` | `float` | `-` |
| `N` | `keyword-only` | `float` | `-` |
| `Mx` | `keyword-only` | `float` | `-` |
| `My` | `keyword-only` | `float` | `-` |
| `axis` | `keyword-only` | `str` | `-` |
| `coord` | `keyword-only` | `float` | `-` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`z`, `axis`, `coord`, `N_partial`, `area_partial`

**Raises visible in the code**

- `ValueError`
- `TypeError`

**Function/method calls visible in the code**

`float`, `_navier_section_state`, `getattr`, `len`, `enumerate`, `ValueError`, `build_children`, `_clip_polygon_half_plane`, `_navier_resultant_over_points`, `children_map.get`, `isinstance`, `TypeError`, `int`, `tuple`, `abs`, `raw_children.items`

### `analyse_jourawski_shear_stress_v2`

**Source lines:** `1532-1805`

```python
def analyse_jourawski_shear_stress_v2section_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, *, dN_dz: float=0.0, num_sudx: int=30, num_sudy: int=30, cut_coords_x: list[float] | tuple[float, ...] | None=None, cut_coords_y: list[float] | tuple[float, ...] | None=None, dz: float | None=None, debug: bool=False
```

**Summary:** Compute mean shear stress on global Jourawski cuts from dN_partial/dz.

**Docstring details**

```text
This is a cut-resultant formulation. It does not reconstruct the complete
two-dimensional shear-stress field and it does not redistribute the mean
cut stress with ``shear_weight``.

For each fixed global cut, define the positive-side Navier resultant

    N_c(z) = integral_{A_c(z)} sigma_zz dA

with ``A_c = {X >= x_c}`` for a vertical cut and
``A_c = {Y >= y_c}`` for a horizontal cut. The cut shear flow is evaluated
directly from longitudinal equilibrium as

    q_c = dN_c / dz

and the mean stress is

    tau_mean = q_c / b_c

where ``b_c`` is the total active intersection length of the cut at the
requested station.

The sign ``q_c = +dN_c/dz`` is consistent with the existing Jourawski
convention because the retained region is always the positive half-plane.
In a prismatic homogeneous section this reduces to the existing
Jourawski result.

The local section-force variation used for the derivative follows the
existing CSF conventions

    dMy/dz = Tx
    dMx/dz = Ty

while ``dN_dz`` is explicit and defaults to zero.

Because ``Section(z)`` and the Navier field are reevaluated at every
derivative station, the derivative includes changes of geometry, centroid,
inertia and axial-flexural ``weight`` automatically.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `N` | `positional or keyword` | `float` | `-` |
| `Mx` | `positional or keyword` | `float` | `-` |
| `My` | `positional or keyword` | `float` | `-` |
| `Tx` | `positional or keyword` | `float` | `-` |
| `Ty` | `positional or keyword` | `float` | `-` |
| `dN_dz` | `keyword-only` | `float` | `0.0` |
| `num_sudx` | `keyword-only` | `int` | `30` |
| `num_sudy` | `keyword-only` | `int` | `30` |
| `cut_coords_x` | `keyword-only` | `list[float] | tuple[float, ...] | None` | `None` |
| `cut_coords_y` | `keyword-only` | `list[float] | tuple[float, ...] | None` | `None` |
| `dz` | `keyword-only` | `float | None` | `None` |
| `debug` | `keyword-only` | `bool` | `False` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`section`, `tau_x_scan`, `tau_y_scan`, `dN_partial_dz`, `step`, `derivative_scheme`, `z`, `N`, `Mx`, `My`, `Tx`, `Ty`, `dN_dz`, `xmin`, `xmax`, `ymin`, `ymax`, `dz`, `formulation`, `positive_half_plane`, `uses_shear_weight`, `N_minus`, `N_0`, `N_plus`, `axis`, `coord`, `b_total`, `shear_flow`, `tau_mean`, `N_partial`, `N_1`, `N_2`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `int`, `max`, `section_field.section`, `_section_active_bbox`, `_explicit_or_uniform_coords`, `_scan`, `ValueError`, `sorted`, `_force_state`, `_jourawski_v2_positive_half_plane_resultant`, `_partial_resultant`, `print`, `_uniform_cell_centres`, `min`, `_section_active_cut_width_and_polygons`, `_derivative`, `rows.append`, `math.isfinite`, `range`, `unique.append`, `abs`, `row.update`, `len`

### `_navier_section_state`

**Source lines:** `1808-1858`

```python
def _navier_section_statesection_field, z: float, N: float, Mx: float, My: float
```

**Summary:** Return the complete scalar state required by the general Navier formula.

**Docstring details**

```text
This helper centralizes the exact algebra used by
:func:`analyse_polygon_navier_stress` so subsequent regional integrations
(including Four-Quadrant resultants) can evaluate the same Navier field
without duplicating its formulation.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `N` | `positional or keyword` | `float` | `-` |
| `Mx` | `positional or keyword` | `float` | `-` |
| `My` | `positional or keyword` | `float` | `-` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`section`, `z`, `A`, `Cx`, `Cy`, `Ix`, `Iy`, `Ixy`, `D`, `axial`, `bx`, `by`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `section_field.section`, `section_full_analysis`, `ValueError`

### `_navier_sigma_at_point`

**Source lines:** `1861-1882`

```python
def _navier_sigma_at_point*, poly: Polygon, x: float, y: float, state: dict[str, object]
```

**Summary:** Evaluate the existing general Navier field at one polygon point.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `keyword-only` | `Polygon` | `-` |
| `x` | `keyword-only` | `float` | `-` |
| `y` | `keyword-only` | `float` | `-` |
| `state` | `keyword-only` | `dict[str, object]` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`float`

### `_clip_points_half_plane`

**Source lines:** `1886-1948`

```python
def _clip_points_half_plane*, points: list[Pt], axis: str, coord: float, keep_positive: bool
```

**Summary:** Clip polygon points against one Cartesian half-plane.

**Docstring details**

```text
``keep_positive=True`` keeps x >= coord or y >= coord.
``keep_positive=False`` keeps x <= coord or y <= coord.

Boundary points are retained on both sides. This is intentional: quadrant
boundaries have zero area, so it does not alter regional resultants and it
keeps the clipping numerically stable at vertices lying on a cut.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `keyword-only` | `list[Pt]` | `-` |
| `axis` | `keyword-only` | `str` | `-` |
| `coord` | `keyword-only` | `float` | `-` |
| `keep_positive` | `keyword-only` | `bool` | `-` |

**Returns:** `list[Pt]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `enumerate`, `ValueError`, `len`, `_value`, `_inside`, `min`, `_interpolate_point_on_segment`, `clipped.append`, `abs`, `max`

### `_clip_polygon_quadrant`

**Source lines:** `1951-1982`

```python
def _clip_polygon_quadrant*, poly: Polygon, x: float, y: float, x_positive: bool, y_positive: bool
```

**Summary:** Return the polygon portion contained in one quadrant about (x, y).

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `keyword-only` | `Polygon` | `-` |
| `x` | `keyword-only` | `float` | `-` |
| `y` | `keyword-only` | `float` | `-` |
| `x_positive` | `keyword-only` | `bool` | `-` |
| `y_positive` | `keyword-only` | `bool` | `-` |

**Returns:** `list[Pt]`

**Function/method calls visible in the code**

`list`, `_clip_points_half_plane`, `len`, `abs`, `float`, `bool`, `_polygon_area_from_points`

### `_polygon_area_centroid_from_points`

**Source lines:** `1985-2012`

```python
def _polygon_area_centroid_from_pointspoints: list[Pt]
```

**Summary:** Return signed area and centroid for a clipped polygon point list.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `positional or keyword` | `list[Pt]` | `-` |

**Returns:** `tuple[float, float, float]`

**Function/method calls visible in the code**

`enumerate`, `len`, `float`, `abs`

### `_navier_resultant_over_points`

**Source lines:** `2015-2047`

```python
def _navier_resultant_over_points*, poly: Polygon, points: list[Pt], state: dict[str, object]
```

**Summary:** Integrate the existing affine Navier field exactly over one polygon part.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `keyword-only` | `Polygon` | `-` |
| `points` | `keyword-only` | `list[Pt]` | `-` |
| `state` | `keyword-only` | `dict[str, object]` | `-` |

**Returns:** `dict[str, float]`

**Returned dictionary keys visible in the code**

`area`, `cx`, `cy`, `N`

**Function/method calls visible in the code**

`_polygon_area_centroid_from_points`, `_navier_sigma_at_point`, `abs`, `float`

### `analyse_navier_four_quadrant_resultant_derivatives`

**Source lines:** `2273-2596`

```python
def analyse_navier_four_quadrant_resultant_derivativessection_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, x: float, y: float, *, dN_dz: float=0.0, dz: float | None=None, derivative_rtol: float=1e-08, derivative_atol: float=1e-08, max_refinements: int=20
```

**Summary:** Differentiate the four Navier regional resultants along ``z``.

**Docstring details**

```text
The four resultants are those returned by
:func:`analyse_navier_four_quadrant_resultants` for the fixed Cartesian
cuts through ``(x, y)``.  At every shifted station the complete actual
``Section(z)`` is rebuilt, so geometry, material participation, centroid
and inertia changes are all included in the numerical derivative.

Only the local first derivatives of the section actions are required.
The action path used by the finite-difference stencil is the local tangent
path

    N(z + ds)  = N  + dN_dz * ds
    Mx(z + ds) = Mx + Ty     * ds
    My(z + ds) = My + Tx     * ds

which follows the same CSF sign convention used by the existing
Jourawski implementation: dMx/dz = Ty and dMy/dz = Tx.

This function returns only longitudinal derivatives of regional normal
force.  It does not infer or distribute local shear flows on the two
internal quadrant boundaries.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `N` | `positional or keyword` | `float` | `-` |
| `Mx` | `positional or keyword` | `float` | `-` |
| `My` | `positional or keyword` | `float` | `-` |
| `Tx` | `positional or keyword` | `float` | `-` |
| `Ty` | `positional or keyword` | `float` | `-` |
| `x` | `positional or keyword` | `float` | `-` |
| `y` | `positional or keyword` | `float` | `-` |
| `dN_dz` | `keyword-only` | `float` | `0.0` |
| `dz` | `keyword-only` | `float | None` | `None` |
| `derivative_rtol` | `keyword-only` | `float` | `1e-08` |
| `derivative_atol` | `keyword-only` | `float` | `1e-08` |
| `max_refinements` | `keyword-only` | `int` | `20` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`z`, `N`, `Mx`, `My`, `Tx`, `Ty`, `x`, `y`, `dN_dz`, `derivative_rtol`, `derivative_atol`, `pp`, `mp`, `mm`, `pm`, `dN_pp_dz`, `dN_mp_dz`, `dN_mm_dz`, `dN_pm_dz`, `dN_above_dz`, `dN_below_dz`, `dN_right_dz`, `dN_left_dz`, `dN_sum_dz`, `dN_residual_dz`, `step`, `derivative_scheme`, `section`, `N_pp`, `N_mp`, `N_mm`, `N_pm`, `N_sum`, `N_residual`, `derivative_dz_mode`, `derivative_converged`, `derivative_refinements`, `derivative_max_change`, `dMx_dz`, `dMy_dz`

**Raises visible in the code**

- `ValueError`
- `RuntimeError`

**Function/method calls visible in the code**

`float`, `int`, `scalar_values.items`, `max`, `_resultants_at_delta`, `derivative.update`, `ValueError`, `_actions_at_delta`, `analyse_navier_four_quadrant_resultants`, `_sample_derivative`, `range`, `RuntimeError`, `_converged_derivative`, `math.isfinite`, `sum`, `min`, `_differentiate_values`, `derivatives.values`, `abs`, `current.update`, `zip`

### `_potential_children_map`

**Source lines:** `2774-2817`

```python
def _potential_children_mapsection_field, z: float, polygon_count: int
```

**Summary:** Return the direct, index-based CSF containment topology.

**Docstring details**

```text
The local solver follows the same structural rule used elsewhere in CSF:
polygon names are labels only; parent/child relationships are identified by
polygon indices. Only *direct* children are subtracted from a parent. This
avoids double subtraction in nested hierarchies and keeps the local shear
domain consistent with Four-Quadrant occupied-region integration.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `polygon_count` | `positional or keyword` | `int` | `-` |

**Returns:** `dict[int, tuple[int, ...]]`

**Raises visible in the code**

- `TypeError`
- `ValueError`

**Function/method calls visible in the code**

`getattr`, `build_children`, `children_map.items`, `float`, `isinstance`, `TypeError`, `int`, `tuple`, `raw_children.items`, `ValueError`

### `_potential_occupied_regions`

**Source lines:** `2820-2966`

```python
def _potential_occupied_regionssection_field, z: float
```

**Summary:** Build non-overlapping occupied material regions at one station.

**Docstring details**

```text
The same CSF rule used by Four-Quadrant integration is applied:

    occupied(parent) = parent - direct_children(parent)

A polygon with non-positive shear participation is treated as a void only
when its axial-flexural participation is also negligible. A polygon that
carries longitudinal stress but has no positive shear carrier makes the
elliptic potential problem degenerate and is therefore rejected explicitly.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `tuple[list[dict[str, object]], object]`

**Returned dictionary keys visible in the code**

`polygon_idx`, `name`, `geometry`, `shear_weightabs`, `weightabs`

**Raises visible in the code**

- `ValueError`
- `ImportError`

**Function/method calls visible in the code**

`section_field.section`, `len`, `_potential_children_map`, `enumerate`, `max`, `unary_union`, `float`, `ValueError`, `_potential_polygon_geometry`, `children_map.get`, `occupied_geometry.append`, `zip`, `regions.append`, `ImportError`, `geometry.difference`, `_jourawski_polygon_shear_weightabs`, `getattr`, `math.isfinite`, `covers`, `abs`, `int`, `str`, `geometry_i.intersection`, `geometry.buffer`

### `_potential_initial_triangles`

**Source lines:** `2985-3074`

```python
def _potential_initial_trianglesregions: list[dict[str, object]]
```

**Summary:** Build the initial conforming triangulation of every occupied shear region.

**Docstring details**

```text
Constrained Delaunay triangulation is used so polygon boundaries and holes
remain explicit mesh edges. Every generated triangle inherits the source
polygon index, label and ``shear_weightabs`` value. The summed triangle area
is checked against the occupied Shapely area; a mismatch is treated as a
mesh-construction failure rather than tolerated as numerical drift.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `regions` | `positional or keyword` | `list[dict[str, object]]` | `-` |

**Returns:** `list[dict[str, object]]`

**Returned dictionary keys visible in the code**

`points`, `polygon_idx`, `name`, `shear_weightabs`

**Raises visible in the code**

- `RuntimeError`
- `ImportError`
- `ValueError`

**Function/method calls visible in the code**

`float`, `_potential_polygon_components`, `max`, `RuntimeError`, `ImportError`, `constrained_delaunay_triangles`, `abs`, `np.asarray`, `_potential_signed_triangle_area`, `triangles.append`, `str`, `component.covers`, `ValueError`, `triangle_geometry.representative_point`, `list`, `int`

### `_potential_refine_triangles`

**Source lines:** `3077-3138`

```python
def _potential_refine_trianglestriangles: list[dict[str, object]], refinements: int
```

**Summary:** Uniformly refine every triangle into four children.

**Docstring details**

```text
Mid-edge subdivision is used because it preserves conformity when adjacent
parent triangles share the same merged edge. Refinement changes only the
numerical resolution: polygon identity and shear participation are inherited
unchanged by every child triangle.

The hard upper bound protects callers from accidentally creating a mesh
whose memory cost grows as 4**refinements.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `triangles` | `positional or keyword` | `list[dict[str, object]]` | `-` |
| `refinements` | `positional or keyword` | `int` | `-` |

**Returns:** `list[dict[str, object]]`

**Returned dictionary keys visible in the code**

`points`, `polygon_idx`, `name`, `shear_weightabs`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`int`, `range`, `ValueError`, `np.asarray`, `refined.append`, `str`, `float`

### `_potential_refine_triangles_comb_controlled`

**Source lines:** `3142-3410`

```python
def _potential_refine_triangles_comb_controlledtriangles: list[dict[str, object]], section_field, z: float, *, num_sudx: int, num_sudy: int
```

**Summary:** Conformingly refine only triangle edges that exceed the local comb spacing.

**Docstring details**

```text
The physical/model assumptions are unchanged.  This function controls only
the numerical triangulation used by the existing P1 potential FEM.

Procedure
---------
1. Build the geometry-driven comb:
     - teeth depend only on CSF geometry;
     - num_sudx / num_sudy subdivide each tooth interval.
2. For every triangle edge, compare its x/y projections with the smallest
   comb spacing crossed by that projection.
3. Mark only edges that are too large.
4. Split every marked edge at its midpoint.  The edge marks are global, so
   both triangles sharing an edge receive the same split and the mesh stays
   conforming.
5. Repeat until no edge violates the comb target.

No triangle is refined merely because another, unrelated triangle needs
refinement.  No GFD stencil or nearest-neighbour selection is involved.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `triangles` | `positional or keyword` | `list[dict[str, object]]` | `-` |
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `num_sudx` | `keyword-only` | `int` | `-` |
| `num_sudy` | `keyword-only` | `int` | `-` |

**Returns:** `tuple[list[dict[str, object]], dict[str, object]]`

**Returned dictionary keys visible in the code**

`points`, `polygon_idx`, `name`, `shear_weightabs`, `pass`, `triangles_before`, `marked_edges`, `triangles_after`, `strategy`, `num_sudx`, `num_sudy`, `x_teeth`, `y_teeth`, `x_comb_lines`, `y_comb_lines`, `passes`, `history`, `key_tolerance`

**Raises visible in the code**

- `RuntimeError`
- `ValueError`

**Function/method calls visible in the code**

`int`, `_potential_comb_grid`, `tuple`, `max`, `list`, `range`, `RuntimeError`, `ValueError`, `float`, `_point_key`, `min`, `abs`, `_minimum_crossed_spacing`, `bool`, `np.asarray`, `_potential_signed_triangle_area`, `set`, `history.append`, `len`, `bisect.bisect_left`, `np.isfinite`, `_oriented`, `str`, `round`, `bisect.bisect_right`, `candidates.append`, `_edge_requires_split`, `_edge_key`, `refined.append`, `marked_edges.add`, `_child`

### `_plot_potential_mesh_controlled`

**Source lines:** `3413-3460`

```python
def _plot_potential_mesh_controlled*, section_field, z: float, nodes, connectivity, initial_triangle_count: int, refinement_info: dict[str, object]
```

**Summary:** Plot the final comb-controlled conforming P1 triangulation.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `keyword-only` | `not annotated` | `-` |
| `z` | `keyword-only` | `float` | `-` |
| `nodes` | `keyword-only` | `not annotated` | `-` |
| `connectivity` | `keyword-only` | `not annotated` | `-` |
| `initial_triangle_count` | `keyword-only` | `int` | `-` |
| `refinement_info` | `keyword-only` | `dict[str, object]` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ImportError`

**Function/method calls visible in the code**

`plt.subplots`, `ax.triplot`, `section_field.section`, `ax.set_aspect`, `ax.set_xlabel`, `ax.set_ylabel`, `ax.set_title`, `fig.tight_layout`, `plt.show`, `float`, `xs.append`, `ys.append`, `ax.plot`, `ImportError`, `int`, `len`

### `evaluate_navier_local_shear_potential_triangle_field`

**Source lines:** `3463-3552`

```python
def evaluate_navier_local_shear_potential_triangle_fieldsolution: dict[str, object], *, x: float, y: float, polygon_idx: int | None=None
```

**Summary:** Sample the piecewise-constant P1 shear field at one physical point.

**Docstring details**

```text
If the point lies exactly on a shared triangle edge, all covering triangles
of the requested polygon are averaged.  This affects only post-processing
at a measure-zero set of points; it does not alter the FEM solution.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `solution` | `positional or keyword` | `dict[str, object]` | `-` |
| `x` | `keyword-only` | `float` | `-` |
| `y` | `keyword-only` | `float` | `-` |
| `polygon_idx` | `keyword-only` | `int | None` | `None` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`x`, `y`, `polygon_idx`, `triangle_count_at_point`, `tau_x`, `tau_y`, `rows`, `geometries`, `tree`

**Raises visible in the code**

- `ValueError`
- `ImportError`

**Function/method calls visible in the code**

`float`, `solution.get`, `Point`, `tree.query`, `np.atleast_1d`, `ValueError`, `list`, `int`, `covers`, `ImportError`, `math.isfinite`, `ShapelyPolygon`, `STRtree`, `selected.append`, `len`, `sum`

### `_potential_triangle_direct_csf_mesh`

**Source lines:** `3557-4221`

```python
def _potential_triangle_direct_csf_meshsection_field, z: float, regions: list[dict[str, object]], *, max_triangle_area: float | None=None, min_angle: float | None=None
```

**Summary:** Build the potential-FEM mesh directly from CSF polygon vertices/segments.

**Docstring details**

```text
Shapely is not used anywhere in this mesh-construction/classification path.

Mesh construction
-----------------
1. Read the actual ``Section(z)`` CSF polygons.
2. Build one PSLG directly from their vertices and boundary segments.
3. Validate that constrained segments do not cross except at shared PSLG
   vertices. No automatic nodding or geometric correction is performed.
4. Call Triangle once.
5. Classify every returned triangle by the CSF containment hierarchy using
   its centroid. Because every CSF polygon boundary is a constrained PSLG
   edge, the centroid identifies the already-delimited face; it does not
   approximate an interface location.
6. Keep triangles whose deepest containing CSF polygon is an active shear
   region and discard triangles belonging to void/outside faces.

``max_triangle_area`` and ``min_angle`` are passed directly to Triangle.
With both set to ``None`` no size/quality refinement parameter is imposed
by CSF.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `regions` | `positional or keyword` | `list[dict[str, object]]` | `-` |
| `max_triangle_area` | `keyword-only` | `float | None` | `None` |
| `min_angle` | `keyword-only` | `float | None` | `None` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`vertices`, `segments`, `nodes`, `triangles`, `polygon_indices`, `names`, `shear_weights`, `merge_tolerance`, `backend`, `triangle_options`, `max_triangle_area`, `min_angle`, `pslg_vertex_count`, `pslg_segment_count`, `normalized_duplicate_vertex_count`, `pslg_hole_count`, `pslg_region_seed_count`, `triangle_total_count`, `discarded_outside_triangle_count`, `discarded_void_triangle_count`, `discarded_triangle_count`, `active_triangle_count`, `all_triangle_area`, `domain_area`, `mesh_area`

**Raises visible in the code**

- `ValueError`
- `RuntimeError`
- `ImportError`

**Function/method calls visible in the code**

`float`, `section_field.section`, `len`, `enumerate`, `max`, `_potential_children_map`, `children_map.items`, `set`, `np.asarray`, `range`, `triangle_lib.triangulate`, `np.unique`, `astype`, `expected_occupied_area.items`, `ValueError`, `raw_coordinates.append`, `zip`, `abs`, `normalized_coordinates.append`, `raw_polygon_area.append`, `parent_of.get`, `int`, `_depth`, `vertex_lookup.get`, `vertices.append`, `append`, `polygon_vertex_ids.append`, `RuntimeError`, `math.hypot`, `bool`, `_segment_bbox`, `_cross`, `intersection`, `format`, `sum`, `_potential_signed_triangle_area`, `active_region_by_polygon.get`, `kept_connectivity.append`, `kept_polygon_indices.append`, `kept_shear_weights.append`, `kept_names.append`, `kept_connectivity_array.reshape`, `ImportError`, `coordinate_values.extend`, `_signed_polygon_area`, `cleaned.append`, `_same_vertex`, `cleaned.pop`, `segment_set.add`, `segments.append`, `_point_on_segment`, `np.linalg.norm`, `_proper_or_unrepresented_intersection`, `Decimal`, `expected_occupied_area.values`, `np.mean`, `str`, `inverse.reshape`, `math.isfinite`, `round`, `vertex_lookup.setdefault`, `_vertex_id`, `min`, `_point_in_polygon`, `children_map.get`

### `_plot_potential_mesh_triangle`

**Source lines:** `4224-4280`

```python
def _plot_potential_mesh_triangle*, section_field, z: float, mesh: dict[str, object]
```

**Summary:** Plot the Triangle PSLG P1 mesh without altering the solve.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `keyword-only` | `not annotated` | `-` |
| `z` | `keyword-only` | `float` | `-` |
| `mesh` | `keyword-only` | `dict[str, object]` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ImportError`

**Function/method calls visible in the code**

`plt.subplots`, `ax.triplot`, `section_field.section`, `ax.set_aspect`, `ax.set_xlabel`, `ax.set_ylabel`, `ax.set_title`, `fig.tight_layout`, `plt.show`, `float`, `xs.append`, `ys.append`, `ax.plot`, `ImportError`, `len`, `int`

### `_potential_merge_mesh`

**Source lines:** `4284-4367`

```python
def _potential_merge_meshtriangles: list[dict[str, object]]
```

**Summary:** Merge geometrically coincident triangle vertices into global mesh nodes.

**Docstring details**

```text
Triangulation is performed region-by-region, so the same physical interface
may initially contain duplicate coordinates. A scale-aware coordinate key
merges those duplicates. This is required for displacement/potential
continuity and for detecting two-sided material-interface edges.

The returned arrays keep triangle-to-polygon metadata alongside connectivity
so material participation can remain piecewise constant by CSF region.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `triangles` | `positional or keyword` | `list[dict[str, object]]` | `-` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`nodes`, `triangles`, `polygon_indices`, `names`, `shear_weights`, `merge_tolerance`

**Raises visible in the code**

- `RuntimeError`

**Function/method calls visible in the code**

`max`, `float`, `node_lookup.get`, `len`, `nodes.append`, `tuple`, `connectivity.append`, `polygon_indices.append`, `names.append`, `shear_weights.append`, `np.asarray`, `int`, `RuntimeError`, `str`, `abs`, `round`, `node_id`, `set`

### `_plot_potential_mesh`

**Source lines:** `4371-4421`

```python
def _plot_potential_mesh*, section_field, z: float, nodes, connectivity, initial_triangle_count: int, mesh_refinements: int
```

**Summary:** Plot the already-generated potential mesh without changing the solve.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `keyword-only` | `not annotated` | `-` |
| `z` | `keyword-only` | `float` | `-` |
| `nodes` | `keyword-only` | `not annotated` | `-` |
| `connectivity` | `keyword-only` | `not annotated` | `-` |
| `initial_triangle_count` | `keyword-only` | `int` | `-` |
| `mesh_refinements` | `keyword-only` | `int` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ImportError`

**Function/method calls visible in the code**

`plt.subplots`, `ax.triplot`, `section_field.section`, `ax.set_aspect`, `ax.set_xlabel`, `ax.set_ylabel`, `ax.set_title`, `fig.tight_layout`, `plt.show`, `float`, `xs.append`, `ys.append`, `ax.plot`, `ImportError`, `int`, `len`

### `_potential_comb_network_nodes`

**Source lines:** `4575-4712`

```python
def _potential_comb_network_nodessection_field, z: float, *, num_sudx: int, num_sudy: int
```

**Summary:** Build only the point network associated with the 2D comb.

**Docstring details**

```text
Two node families are generated:

1. comb-crossing nodes:
   intersections x_comb x y_comb that belong to the occupied shear domain;

2. polygon-intersection nodes:
   intersections between every horizontal/vertical comb line and the exact
   boundaries of the CSF polygons.

No cells, triangles, finite elements, PDE equations or shear stresses are
generated here.  This helper is only a geometric preview of the proposed
point network.

If a comb line is exactly coincident with a polygon edge, the overlap is
represented in this preview by the endpoints of the coincident segment.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `num_sudx` | `keyword-only` | `int` | `-` |
| `num_sudy` | `keyword-only` | `int` | `-` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`grid`, `comb_nodes`, `polygon_nodes`

**Raises visible in the code**

- `ImportError`

**Function/method calls visible in the code**

`_potential_comb_grid`, `np.asarray`, `section_field.section`, `max`, `list`, `float`, `np.full`, `abs`, `polygon_node_map.setdefault`, `str`, `hasattr`, `LineString`, `polygon_node_map.values`, `tuple`, `ImportError`, `int`, `intersects_xy`, `comb_nodes.append`, `_potential_polygon_geometry`, `_store_point`, `_collect_points`, `round`, `boundary.intersection`

### `plot_navier_local_shear_potential_comb_nodes`

**Source lines:** `4715-4854`

```python
def plot_navier_local_shear_potential_comb_nodessection_field, z: float, *, num_sudx: int=20, num_sudy: int=20
```

**Summary:** Plot the proposed point network before any PDE discretization.

**Docstring details**

```text
The plot shows:
- the 2D comb;
- valid x/y comb-crossing nodes inside/on the occupied shear domain;
- intersections between comb lines and exact CSF polygon boundaries.

No numerical field equation is assembled or solved.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `num_sudx` | `keyword-only` | `int` | `20` |
| `num_sudy` | `keyword-only` | `int` | `20` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`z`, `num_sudx`, `num_sudy`, `x_teeth`, `y_teeth`, `x_coords`, `y_coords`, `comb_node_count`, `polygon_node_count`, `comb_nodes`, `polygon_nodes`

**Raises visible in the code**

- `ImportError`

**Function/method calls visible in the code**

`_potential_comb_network_nodes`, `list`, `set`, `plt.subplots`, `section_field.section`, `ax.set_aspect`, `ax.set_xlabel`, `ax.set_ylabel`, `ax.set_title`, `ax.legend`, `fig.tight_layout`, `plt.show`, `float`, `str`, `hasattr`, `LineString`, `domain.intersection`, `any`, `_draw_clipped_line`, `xs.append`, `ys.append`, `ax.plot`, `ax.scatter`, `int`, `len`, `tuple`, `ImportError`, `abs`

### `_potential_comb_region_membership`

**Source lines:** `4906-4946`

```python
def _potential_comb_region_membership*, nodes, regions: list[dict[str, object]], tolerance: float
```

**Summary:** Classify every physical comb node by occupied CSF region membership.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `nodes` | `keyword-only` | `not annotated` | `-` |
| `regions` | `keyword-only` | `list[dict[str, object]]` | `-` |
| `tolerance` | `keyword-only` | `float` | `-` |

**Returns:** `tuple[list[tuple[int, ...]], list[list[int]]]`

**Raises visible in the code**

- `ImportError`

**Function/method calls visible in the code**

`STRtree`, `enumerate`, `ShapelyPoint`, `tree.query`, `sorted`, `node_regions.append`, `ImportError`, `float`, `int`, `set`, `tuple`, `append`, `geometry.covers`, `matches.append`, `geometry.boundary.distance`

### `_potential_comb_point_segment_distance`

**Source lines:** `4949-4973`

```python
def _potential_comb_point_segment_distance*, x: float, y: float, p0: tuple[float, float], p1: tuple[float, float]
```

**Summary:** Return clamped segment parameter, distance and segment length.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `x` | `keyword-only` | `float` | `-` |
| `y` | `keyword-only` | `float` | `-` |
| `p0` | `keyword-only` | `tuple[float, float]` | `-` |
| `p1` | `keyword-only` | `tuple[float, float]` | `-` |

**Returns:** `tuple[float, float, float]`

**Function/method calls visible in the code**

`map`, `min`, `max`, `float`, `math.hypot`, `math.sqrt`

### `_potential_comb_region_outward_normal`

**Source lines:** `4976-5058`

```python
def _potential_comb_region_outward_normalgeometry, *, x: float, y: float, tolerance: float
```

**Summary:** Return the outward unit normal of one occupied region at a boundary node.

**Docstring details**

```text
At a geometric corner the normalized sum of all incident outward segment
normals is used.  This is a pointwise collocation convention only; corners
have zero boundary measure and do not alter the continuous Neumann problem.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geometry` | `positional or keyword` | `not annotated` | `-` |
| `x` | `keyword-only` | `float` | `-` |
| `y` | `keyword-only` | `float` | `-` |
| `tolerance` | `keyword-only` | `float` | `-` |

**Returns:** `tuple[float, float]`

**Raises visible in the code**

- `RuntimeError`
- `ImportError`

**Function/method calls visible in the code**

`max`, `_potential_polygon_components`, `sum`, `math.hypot`, `RuntimeError`, `float`, `ImportError`, `list`, `zip`, `_potential_comb_point_segment_distance`, `ShapelyPoint`, `geometry.covers`, `incident.append`, `geometry.distance`

### `analyse_navier_local_shear_potential_comb`

**Source lines:** `5185-5590`

```python
def analyse_navier_local_shear_potential_combsection_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, *, dN_dz: float=0.0, dz: float | None=None, num_sudx: int=5, num_sudy: int=5, stencil_size: int=12, max_stencil_size: int=40, solver_atol: float=1e-10, solver_btol: float=1e-10, solver_maxiter: int | None=None
```

**Summary:** Solve the CSF local shear-potential equation on the approved 2D comb points.

**Docstring details**

```text
Numerical method
----------------
This implementation deliberately does not create triangles, quadrilateral
cells or cut cells.  The physical nodes are exactly the union of:

1. valid x/y comb intersections inside the occupied shear domain;
2. intersections of x/y comb lines with CSF polygon boundaries.

The same scalar-potential closure already used by the P1 FEM path is kept:

    tau = G_like * grad(phi)
    div(tau) = -partial(sigma_zz)/partial(z).

The new numerical discretization is quadratic generalized finite difference
(GFD) collocation on that point network.  Interior nodes enforce the PDE;
external-boundary nodes enforce the moving-boundary normal-flux condition;
two-region interface nodes enforce the established normal-flux jump.

The local quadratic stencil starts at ``stencil_size`` nearest points in the
same occupied CSF region and is enlarged only when the six-term polynomial
basis is rank deficient.  This is a point-stencil choice, not a mesh-quality
rule.  The only geometric refinement remains ``num_sudx``/``num_sudy``.

One potential value is stored per unique physical node.  Continuity of phi
across a two-region interface is therefore automatic.  Junctions where more
than two active shear regions meet at exactly one collocation point are not
silently approximated and are rejected explicitly in this first graph/GFD
implementation.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `N` | `positional or keyword` | `float` | `-` |
| `Mx` | `positional or keyword` | `float` | `-` |
| `My` | `positional or keyword` | `float` | `-` |
| `Tx` | `positional or keyword` | `float` | `-` |
| `Ty` | `positional or keyword` | `float` | `-` |
| `dN_dz` | `keyword-only` | `float` | `0.0` |
| `dz` | `keyword-only` | `float | None` | `None` |
| `num_sudx` | `keyword-only` | `int` | `5` |
| `num_sudy` | `keyword-only` | `int` | `5` |
| `stencil_size` | `keyword-only` | `int` | `12` |
| `max_stencil_size` | `keyword-only` | `int` | `40` |
| `solver_atol` | `keyword-only` | `float` | `1e-10` |
| `solver_btol` | `keyword-only` | `float` | `1e-10` |
| `solver_maxiter` | `keyword-only` | `int | None` | `None` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`method`, `z`, `N`, `Mx`, `My`, `Tx`, `Ty`, `num_sudx`, `num_sudy`, `node_count`, `comb_node_count_raw`, `polygon_node_count_raw`, `gauge_count`, `physical_equation_count`, `equation_count`, `derivative_step`, `derivative_scheme`, `solver_istop`, `solver_iterations`, `solver_normr`, `solver_normar`, `solver_conda`, `scaled_residual_inf`, `stencil_size_min`, `stencil_size_max`, `stencil_condition_max`, `nodes`, `phi`, `node_regions`, `equation_kind`, `_regions`, `_region_global_indices`, `_region_trees`, `_geometry_tolerance`, `_stencil_size`, `_max_stencil_size`

**Raises visible in the code**

- `NotImplementedError`
- `RuntimeError`
- `ImportError`

**Function/method calls visible in the code**

`float`, `_potential_comb_network_nodes`, `list`, `_potential_comb_merge_nodes`, `_potential_comb_region_membership`, `int`, `_potential_derivative_context`, `enumerate`, `_potential_polygon_components`, `tocsr`, `np.asarray`, `lsmr`, `abs`, `NotImplementedError`, `len`, `region_global_indices.append`, `region_trees.append`, `zip`, `rhs_values.append`, `equation_kind.append`, `tuple`, `ShapelyPoint`, `bool`, `_potential_comb_gfd_weights`, `stencil_conditions.append`, `stencil_sizes.append`, `_potential_sigma_z_at_point`, `append_equation`, `RuntimeError`, `max`, `str`, `ImportError`, `cKDTree`, `np.linalg.norm`, `_potential_comb_region_outward_normal`, `_potential_boundary_velocity_at_point`, `_navier_sigma_at_point`, `math.sqrt`, `row_indices.append`, `col_indices.append`, `matrix_values.append`, `coo_matrix`, `np.max`, `math.isfinite`, `covers`, `np.abs`, `min`, `component.covers`, `boundary.distance`, `buffer`, `coefficients.get`, `component.boundary.distance`

### `plot_navier_local_shear_potential_comb`

**Source lines:** `5667-5768`

```python
def plot_navier_local_shear_potential_combsection_field, z: float, *, num_sudx: int=20, num_sudy: int=20
```

**Summary:** Plot the geometry-driven 2D comb before any potential-field discretization.

**Docstring details**

```text
Geometric teeth are determined only by the CSF section geometry.  Every
interval between two consecutive teeth is then divided into ``num_sudx``
or ``num_sudy`` equal sub-intervals along the corresponding axis.

The comb is clipped to the occupied CSF shear domain and the exact CSF
polygon boundaries are overlaid.  No finite-element mesh is generated and
no potential equation is solved.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `num_sudx` | `keyword-only` | `int` | `20` |
| `num_sudy` | `keyword-only` | `int` | `20` |

**Returns:** `dict[str, object]`

**Raises visible in the code**

- `ImportError`

**Function/method calls visible in the code**

`_potential_comb_grid`, `list`, `set`, `plt.subplots`, `section_field.section`, `ax.set_aspect`, `ax.set_xlabel`, `ax.set_ylabel`, `ax.set_title`, `fig.tight_layout`, `plt.show`, `float`, `hasattr`, `LineString`, `domain.intersection`, `any`, `_draw_clipped_line`, `xs.append`, `ys.append`, `ax.plot`, `ImportError`, `int`, `grid.items`, `len`, `abs`

### `_potential_derivative_context`

**Source lines:** `5813-6007`

```python
def _potential_derivative_contextsection_field, *, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, dz: float | None
```

**Summary:** Build a common second-order z-derivative stencil for stress and geometry.

**Docstring details**

```text
The same stencil is used for:
- the complete Navier-stress derivative at fixed physical (x, y);
- vertex velocities dx/dz and dy/dz used by moving-boundary conditions.

Keeping those derivatives on one stencil is important: the domain motion
and the stress source must represent the same local section evolution.

The neighbouring section-action states use the established CSF tangent
convention

    dMx/dz = Ty
    dMy/dz = Tx,

while N is held constant in this first implementation. Interior stations
use a second-order central difference; CSF endpoints use second-order
one-sided formulas.

``dz=None`` does not perform an iterative convergence search here. It selects
a small scale-based step (1e-5 times the CSF length). Callers that require a
controlled derivative step can pass ``dz`` explicitly.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `keyword-only` | `float` | `-` |
| `N` | `keyword-only` | `float` | `-` |
| `Mx` | `keyword-only` | `float` | `-` |
| `My` | `keyword-only` | `float` | `-` |
| `Tx` | `keyword-only` | `float` | `-` |
| `Ty` | `keyword-only` | `float` | `-` |
| `dz` | `keyword-only` | `float | None` | `-` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`z`, `step`, `scheme`, `dz_mode`, `offsets`, `coefficients`, `denominator`, `states`, `base_state`, `vertex_velocity`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `max`, `len`, `states.values`, `enumerate`, `ValueError`, `min`, `set`, `actions_at_offset`, `_navier_section_state`, `range`, `vertex_velocity.append`, `tuple`, `math.isfinite`, `zip`, `velocities.append`

### `_potential_sigma_z_at_point`

**Source lines:** `6010-6049`

```python
def _potential_sigma_z_at_pointderivative_context: dict[str, object], *, polygon_idx: int, x: float, y: float
```

**Summary:** Evaluate partial(sigma_zz)/partial(z) at a fixed global point.

**Docstring details**

```text
The point coordinates are intentionally *not* convected with a polygon.
Each stencil station reconstructs the complete Navier state of its actual
CSF section and evaluates that state at the same spatial (x, y). This is the
Eulerian derivative required by the local equilibrium equation.

Geometry variation, centroid motion, inertia variation, polygon
``weightabs`` variation and the local action gradients are therefore all
differentiated together rather than introduced as separate correction
terms.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `derivative_context` | `positional or keyword` | `dict[str, object]` | `-` |
| `polygon_idx` | `keyword-only` | `int` | `-` |
| `x` | `keyword-only` | `float` | `-` |
| `y` | `keyword-only` | `float` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`zip`, `float`, `_navier_sigma_at_point`, `int`

### `_potential_point_segment_parameter`

**Source lines:** `6052-6089`

```python
def _potential_point_segment_parameter*, x: float, y: float, p0: Pt, p1: Pt
```

**Summary:** Project a physical point onto one finite polygon edge.

**Docstring details**

```text
The clamped segment parameter is later used to interpolate the two endpoint
velocities of that moving CSF edge. The returned distance is the geometric
criterion used to decide whether a finite-element boundary quadrature point
belongs to the original CSF edge.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `x` | `keyword-only` | `float` | `-` |
| `y` | `keyword-only` | `float` | `-` |
| `p0` | `keyword-only` | `Pt` | `-` |
| `p1` | `keyword-only` | `Pt` | `-` |

**Returns:** `tuple[float, float]`

**Function/method calls visible in the code**

`float`, `min`, `math.hypot`, `max`

### `_potential_boundary_velocity_at_point`

**Source lines:** `6092-6172`

```python
def _potential_boundary_velocity_at_pointderivative_context: dict[str, object], *, x: float, y: float, geometry_tolerance: float
```

**Summary:** Return the in-plane velocity of a physical CSF boundary/interface point.

**Docstring details**

```text
Vertex correspondence between the endpoint sections defines the motion of
each CSF polygon edge. Once a mesh quadrature point is mapped back to such an
edge, its velocity is obtained by linear interpolation between the two edge
endpoint velocities.

Shared material interfaces can be represented by the boundaries of two
different polygons. In that case all matching geometric descriptions must
predict the same physical velocity. The consistency check is deliberate:
applying two incompatible interface motions would make the Neumann jump
condition mechanically undefined.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `derivative_context` | `positional or keyword` | `dict[str, object]` | `-` |
| `x` | `keyword-only` | `float` | `-` |
| `y` | `keyword-only` | `float` | `-` |
| `geometry_tolerance` | `keyword-only` | `float` | `-` |

**Returns:** `tuple[float, float]`

**Raises visible in the code**

- `RuntimeError`
- `ValueError`

**Function/method calls visible in the code**

`enumerate`, `max`, `RuntimeError`, `sum`, `len`, `abs`, `float`, `_potential_point_segment_parameter`, `candidates.append`, `ValueError`

### `_potential_edge_normal_from_triangle`

**Source lines:** `6175-6209`

```python
def _potential_edge_normal_from_triangle*, p0, p1, triangle_centroid
```

**Summary:** Return the unit normal directed out of one adjacent triangle.

**Docstring details**

```text
Mesh edges are stored without orientation. The trial right-hand normal is
therefore tested against the triangle centroid and reversed when necessary.
On a one-sided edge this produces the outward normal of the active
finite-element domain.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `p0` | `keyword-only` | `not annotated` | `-` |
| `p1` | `keyword-only` | `not annotated` | `-` |
| `triangle_centroid` | `keyword-only` | `not annotated` | `-` |

**Returns:** `tuple[float, float]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `math.hypot`, `ValueError`

### `_potential_edge_normal_between_triangles`

**Source lines:** `6212-6243`

```python
def _potential_edge_normal_between_triangles*, p0, p1, centroid_i, centroid_j
```

**Summary:** Return a deterministic unit normal from material side i to material side j.

**Docstring details**

```text
This orientation is used only to write the moving-interface jump condition
with a consistent sign. Reversing both the normal and the i/j ordering would
produce the same physical weak contribution.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `p0` | `keyword-only` | `not annotated` | `-` |
| `p1` | `keyword-only` | `not annotated` | `-` |
| `centroid_i` | `keyword-only` | `not annotated` | `-` |
| `centroid_j` | `keyword-only` | `not annotated` | `-` |

**Returns:** `tuple[float, float]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`float`, `math.hypot`, `ValueError`

### `_potential_mesh_edges`

**Source lines:** `6246-6271`

```python
def _potential_mesh_edgesconnectivity
```

**Summary:** Build the edge-to-adjacent-triangles topology of the conforming mesh.

**Docstring details**

```text
One adjacent triangle identifies an external/void boundary edge. Two
adjacent triangles identify an internal mesh edge and may also represent a
material interface when their polygon indices differ. More than two adjacent
triangles would be non-manifold and is rejected.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `connectivity` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `dict[tuple[int, int], list[int]]`

**Raises visible in the code**

- `RuntimeError`

**Function/method calls visible in the code**

`enumerate`, `edges.items`, `int`, `append`, `len`, `RuntimeError`, `edges.setdefault`

### `_potential_connected_components`

**Source lines:** `6274-6316`

```python
def _potential_connected_components*, node_count: int, connectivity
```

**Summary:** Return the node-connected components of the active shear mesh.

**Docstring details**

```text
A pure-Neumann potential problem has one additive constant for each
disconnected component. The component list is therefore used to create one
independent zero-mean gauge equation per component rather than assuming the
section is geometrically connected.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `node_count` | `keyword-only` | `int` | `-` |
| `connectivity` | `keyword-only` | `not annotated` | `-` |

**Returns:** `list[list[int]]`

**Function/method calls visible in the code**

`list`, `range`, `find`, `map`, `union`, `int`, `append`, `grouped.values`, `grouped.setdefault`

### `_potential_triangle_cut_interval`

**Source lines:** `6319-6383`

```python
def _potential_triangle_cut_intervalpoints, *, axis: str, value: float, tolerance: float
```

**Summary:** Intersect one P1 triangle with a global horizontal or vertical validation cut.

**Docstring details**

```text
The local shear field is constant inside each triangle, so only the length
of the cut segment inside that triangle is required for chord integration.
Cuts coincident with a complete triangle edge are rejected because ownership
would otherwise be ambiguous; validation points should be moved slightly.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `positional or keyword` | `not annotated` | `-` |
| `axis` | `keyword-only` | `str` | `-` |
| `value` | `keyword-only` | `float` | `-` |
| `tolerance` | `keyword-only` | `float` | `-` |

**Returns:** `tuple[float, float] | None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`range`, `float`, `len`, `min`, `max`, `ValueError`, `abs`, `values.append`, `any`, `unique.append`

### `_potential_partial_chord_flows`

**Source lines:** `6386-6474`

```python
def _potential_partial_chord_flowstriangle_rows: list[dict[str, object]], *, x: float, y: float, tolerance: float
```

**Summary:** Integrate the recovered shear field over the four half-chords through a point.

**Docstring details**

```text
``H_L`` and ``H_R`` integrate tau_y to the left and right of the point on
the horizontal chord. ``V_B`` and ``V_T`` integrate tau_x below and above
the point on the vertical chord.

These four scalar flows are the quantities that enter the independent
Four-Quadrant equilibrium identities. No fitting or correction is applied
to them.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `triangle_rows` | `positional or keyword` | `list[dict[str, object]]` | `-` |
| `x` | `keyword-only` | `float` | `-` |
| `y` | `keyword-only` | `float` | `-` |
| `tolerance` | `keyword-only` | `float` | `-` |

**Returns:** `dict[str, float]`

**Returned dictionary keys visible in the code**

`H_L`, `H_R`, `V_B`, `V_T`

**Function/method calls visible in the code**

`np.asarray`, `_potential_triangle_cut_interval`, `float`, `max`, `min`

### `analyse_navier_local_shear_potential_triangle_mesh`

**Source lines:** `6477-7378`

```python
def analyse_navier_local_shear_potential_triangle_meshsection_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, *, dN_dz: float=0.0, dz: float | None=None, max_triangle_area: float | None=None, min_angle: float | None=None, plot_mesh: bool=False, validation_points: tuple[tuple[float, float], ...] | None=None, compatibility_rtol: float=1e-08, compatibility_atol: float=1e-06
```

**Summary:** Recover a local in-plane shear field from complete Navier equilibrium.

**Docstring details**

```text
Mechanical definition
---------------------
At the requested station the function first constructs the complete CSF
Navier stress field ``sigma_zz(x, y, z)`` using the physical section
geometry, polygon ``weightabs`` values and the supplied section actions.
Its longitudinal derivative is then evaluated at fixed global coordinates.

The local shear field is selected through the minimum-complementary-energy
closure

    tau = G_like * grad(phi),

with

    div(tau) = -partial(sigma_zz) / partial(z),

or equivalently

    div(G_like * grad(phi))
        = -partial(sigma_zz) / partial(z).

``G_like`` is the sampled polygon ``shear_weightabs``. It is not derived
from ``weightabs`` inside this routine and it is not replaced by a global
effective shear modulus.

This formulation is deliberately based on the derivative of the *complete*
Navier field. Centroid motion, inertia variation, material participation
variation and action gradients are therefore already contained in the
source. They must not be added again as independent taper or centroid
corrections.

Action-gradient convention
--------------------------
The local neighbouring action states follow the CSF convention

    dMx/dz = Ty
    dMy/dz = Tx.

``N`` is currently held constant. Accordingly ``dN_dz`` is accepted only
when it is zero; see "Axial distributed loading" below.

Occupied-region topology
------------------------
The transverse domain is built with the same index-based containment rule
used by the Four-Quadrant routines:

    occupied(parent)
        = parent - union(direct children).

This prevents double counting of nested material polygons. A region with
negligible ``weightabs`` and negligible ``shear_weightabs`` acts as a true
void and remains excluded from the active domain. A region carrying Navier
stress but having no positive shear carrier is rejected because the
elliptic closure would be locally degenerate.

Moving external boundaries
--------------------------
CSF vertex correspondence defines an in-plane boundary velocity

    v = (dx/dz, dy/dz).

On an external moving boundary the reduced traction condition is

    tau . n = sigma_zz * v_n,

where ``n`` is the outward unit normal and ``v_n = v . n``. A fixed external
boundary has ``v_n = 0`` and therefore carries zero prescribed normal shear
traction in this reduced problem.

Moving material interfaces
--------------------------
When two active regions share a moving interface, the weak jump condition is

    (tau_i - tau_j) . n
        = (sigma_zz_i - sigma_zz_j) * v_n.

Thus a fixed interface reduces automatically to continuity of normal shear
traction. The interface velocity is checked from both polygon descriptions;
inconsistent CSF interface kinematics raise an error instead of being
averaged silently.

Finite-element representation
-----------------------------
The actual CSF polygon vertices and boundary segments are passed directly
to the Python ``triangle`` wrapper around Shewchuk's Triangle library as
one PSLG. Shapely is not used for mesh construction or triangle material
classification.

``max_triangle_area`` is the direct Triangle maximum-area constraint.
``min_angle`` is the direct Triangle minimum-angle quality constraint.
Neither constraint is applied when its value is ``None``.

There is no CSF post-meshing refinement loop, no nearest-neighbour stencil,
no Triangle region seed and no Triangle hole seed. Each returned triangle
is classified by the CSF containment hierarchy; outside/void triangles are
discarded.

The scalar potential uses conforming P1 triangles. Consequently
``grad(phi)`` and the returned ``tau_x, tau_y`` are piecewise constant by
triangle.

Mesh visualization
------------------
When ``plot_mesh=True``, the final triangulation and the exact CSF polygon
boundaries are displayed after mesh generation and before FEM assembly.
The visualization is diagnostic only and does not modify the mesh, the
assembled system or the returned solution. Matplotlib is required only
when this option is enabled.

Pure-Neumann compatibility and gauge
------------------------------------
The local problem is Neumann-only. For every disconnected active component,
solvability requires equality between the integrated volume source and the
prescribed boundary/interface fluxes. The function evaluates and returns
those compatibility residuals.

Each connected component also has one arbitrary additive constant in
``phi``. A zero-mean constraint is introduced through a Lagrange multiplier
per component. Gauge multipliers are numerical nullspace controls, not
physical stress resultants.

Axial distributed loading
-------------------------
This implementation requires ``dN_dz == 0``.

A non-zero scalar ``dN_dz`` states only the change of the total axial
resultant. It does not specify how the corresponding axial body load,
surface load or transfer is distributed over the cross-section. Because
different local distributions can produce the same resultant derivative,
using ``dN_dz`` alone would make the local source underdetermined. The
function therefore raises ``NotImplementedError`` rather than inventing a
distribution.

Optional Four-Quadrant validation
---------------------------------
``validation_points`` are diagnostic only. They are never used in assembly
and cannot change the solution.

At each validation point the solved triangle field is integrated on four
half-chords to obtain

    H_L, H_R, V_B, V_T.

These are compared with the independently differentiated Navier regional
resultants using

    dN_pp/dz =  H_R + V_T
    dN_mp/dz =  H_L - V_T
    dN_mm/dz = -H_L - V_B
    dN_pm/dz = -H_R + V_B.

The comparison is returned under ``validation`` and acts as an integral
equilibrium check; no projection is performed to force agreement.

Returned data
-------------
The result dictionary contains:

- ``section``:
  station, actions, derivative convention and derivative-step metadata;
- ``mesh``:
  Triangle PSLG controls, node/triangle counts and mesh tolerances;
- ``resultants``:
  area-integrated ``Tx_recovered``, ``Ty_recovered`` and their differences
  from the prescribed ``Tx``, ``Ty``;
- ``equilibrium``:
  source, boundary and interface integrals, global/component compatibility
  residuals, linear-system residual and gauge multipliers;
- ``triangles``:
  one row per triangle with coordinates, polygon identity, area,
  ``shear_weightabs``, potential gradient and piecewise-constant
  ``tau_x, tau_y``;
- ``validation``:
  optional Four-Quadrant half-chord comparisons.

Interpretation and limits
-------------------------
This is a reduced sectional equilibrium closure, not a general
three-dimensional elasticity solver. The recovered field is the
complementary-energy-minimizing field within the adopted scalar-potential
model.

The implementation has been regression-tested so that existing Navier,
Jourawski, centroid-axis and Four-Quadrant calculations are unchanged when
this API is not called.

NumPy, SciPy and Shapely >= 2.1 are imported lazily and are required only
when this function is executed.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `N` | `positional or keyword` | `float` | `-` |
| `Mx` | `positional or keyword` | `float` | `-` |
| `My` | `positional or keyword` | `float` | `-` |
| `Tx` | `positional or keyword` | `float` | `-` |
| `Ty` | `positional or keyword` | `float` | `-` |
| `dN_dz` | `keyword-only` | `float` | `0.0` |
| `dz` | `keyword-only` | `float | None` | `None` |
| `max_triangle_area` | `keyword-only` | `float | None` | `None` |
| `min_angle` | `keyword-only` | `float | None` | `None` |
| `plot_mesh` | `keyword-only` | `bool` | `False` |
| `validation_points` | `keyword-only` | `tuple[tuple[float, float], ...] | None` | `None` |
| `compatibility_rtol` | `keyword-only` | `float` | `1e-08` |
| `compatibility_atol` | `keyword-only` | `float` | `1e-06` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`section`, `derivative`, `mesh`, `resultants`, `equilibrium`, `triangles`, `validation`, `z`, `N`, `Mx`, `My`, `Tx`, `Ty`, `dN_dz`, `step`, `scheme`, `dz_mode`, `strategy`, `triangle_options`, `max_triangle_area`, `min_angle`, `pslg_vertex_count`, `pslg_segment_count`, `normalized_duplicate_vertex_count`, `pslg_hole_count`, `pslg_region_seed_count`, `triangle_total_count`, `discarded_outside_triangle_count`, `discarded_void_triangle_count`, `discarded_triangle_count`, `active_triangle_count`, `domain_area`, `mesh_area`, `node_count`, `triangle_count`, `connected_components`, `boundary_edge_count`, `interface_edge_count`, `merge_tolerance`, `Tx_recovered`, `Ty_recovered`, `Tx_error`, `Ty_error`, `source_integral`, `external_boundary_flux_integral`, `interface_jump_integral`, `global_compatibility_residual`, `max_component_compatibility_residual`, `component_compatibility`, `linear_residual_inf`, `gauge_multipliers`, `compatibility_rtol`, `compatibility_atol`, `component`, `residual`, `tolerance`, `idx`, `polygon_idx`, `name`, `shear_weightabs`, `area`, `cx`, `cy`, `x0`, `y0`, `x1`, `y1`, `x2`, `y2`, `tau_x`, `tau_y`, `dN_pp_dz`, `dN_mp_dz`, `dN_mm_dz`, `dN_pm_dz`, `x`, `y`

**Raises visible in the code**

- `NotImplementedError`
- `ValueError`
- `RuntimeError`
- `ImportError`

**Function/method calls visible in the code**

`float`, `bool`, `items`, `_potential_derivative_context`, `_potential_occupied_regions`, `_potential_triangle_direct_csf_mesh`, `len`, `lil_matrix`, `np.zeros`, `enumerate`, `_potential_mesh_edges`, `map`, `max`, `edges.items`, `_potential_connected_components`, `constraint.tocsc`, `stiffness.tocsc`, `csc_matrix`, `bmat`, `np.concatenate`, `spsolve`, `np.asarray`, `abs`, `NotImplementedError`, `ValueError`, `RuntimeError`, `_plot_potential_mesh_triangle`, `_potential_triangle_area_gradients`, `int`, `triangle_gradients.append`, `np.mean`, `range`, `component_compatibility.append`, `np.max`, `triangle_rows.append`, `ImportError`, `math.isfinite`, `_potential_sigma_z_at_point`, `math.sqrt`, `np.linalg.norm`, `_potential_edge_normal_from_triangle`, `np.sum`, `np.abs`, `_potential_partial_chord_flows`, `analyse_navier_four_quadrant_resultant_derivatives`, `predicted.items`, `validation_rows.append`, `str`, `tuple`, `domain.boundary.distance`, `_potential_boundary_velocity_at_point`, `_navier_sigma_at_point`, `_potential_edge_normal_between_triangles`, `ShapelyPoint`

### `analyse_navier_local_shear_potential_controlled_mesh`

**Source lines:** `7383-8267`

```python
def analyse_navier_local_shear_potential_controlled_meshsection_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, *, dN_dz: float=0.0, dz: float | None=None, num_sudx: int=5, num_sudy: int=5, plot_mesh: bool=False, validation_points: tuple[tuple[float, float], ...] | None=None, compatibility_rtol: float=1e-08, compatibility_atol: float=1e-06
```

**Summary:** Recover a local in-plane shear field from complete Navier equilibrium.

**Docstring details**

```text
Mechanical definition
---------------------
At the requested station the function first constructs the complete CSF
Navier stress field ``sigma_zz(x, y, z)`` using the physical section
geometry, polygon ``weightabs`` values and the supplied section actions.
Its longitudinal derivative is then evaluated at fixed global coordinates.

The local shear field is selected through the minimum-complementary-energy
closure

    tau = G_like * grad(phi),

with

    div(tau) = -partial(sigma_zz) / partial(z),

or equivalently

    div(G_like * grad(phi))
        = -partial(sigma_zz) / partial(z).

``G_like`` is the sampled polygon ``shear_weightabs``. It is not derived
from ``weightabs`` inside this routine and it is not replaced by a global
effective shear modulus.

This formulation is deliberately based on the derivative of the *complete*
Navier field. Centroid motion, inertia variation, material participation
variation and action gradients are therefore already contained in the
source. They must not be added again as independent taper or centroid
corrections.

Action-gradient convention
--------------------------
The local neighbouring action states follow the CSF convention

    dMx/dz = Ty
    dMy/dz = Tx.

``N`` is currently held constant. Accordingly ``dN_dz`` is accepted only
when it is zero; see "Axial distributed loading" below.

Occupied-region topology
------------------------
The transverse domain is built with the same index-based containment rule
used by the Four-Quadrant routines:

    occupied(parent)
        = parent - union(direct children).

This prevents double counting of nested material polygons. A region with
negligible ``weightabs`` and negligible ``shear_weightabs`` acts as a true
void and remains excluded from the active domain. A region carrying Navier
stress but having no positive shear carrier is rejected because the
elliptic closure would be locally degenerate.

Moving external boundaries
--------------------------
CSF vertex correspondence defines an in-plane boundary velocity

    v = (dx/dz, dy/dz).

On an external moving boundary the reduced traction condition is

    tau . n = sigma_zz * v_n,

where ``n`` is the outward unit normal and ``v_n = v . n``. A fixed external
boundary has ``v_n = 0`` and therefore carries zero prescribed normal shear
traction in this reduced problem.

Moving material interfaces
--------------------------
When two active regions share a moving interface, the weak jump condition is

    (tau_i - tau_j) . n
        = (sigma_zz_i - sigma_zz_j) * v_n.

Thus a fixed interface reduces automatically to continuity of normal shear
traction. The interface velocity is checked from both polygon descriptions;
inconsistent CSF interface kinematics raise an error instead of being
averaged silently.

Finite-element representation
-----------------------------
Each occupied polygonal region is constrained-triangulated by Shapely.
The initial mesh is then refined conformingly only where triangle-edge
projections exceed the local geometry-driven comb spacing.

``num_sudx`` and ``num_sudy`` subdivide every interval between consecutive
geometric teeth and therefore control the local target resolution.  There
is no uniform 1->4 refinement level.

The scalar potential uses conforming P1 triangles. Consequently
``grad(phi)`` and the returned ``tau_x, tau_y`` are piecewise constant by
triangle.

Mesh visualization
------------------
When ``plot_mesh=True``, the final triangulation and the exact CSF polygon
boundaries are displayed after mesh generation and before FEM assembly.
The visualization is diagnostic only and does not modify the mesh, the
assembled system or the returned solution. Matplotlib is required only
when this option is enabled.

Pure-Neumann compatibility and gauge
------------------------------------
The local problem is Neumann-only. For every disconnected active component,
solvability requires equality between the integrated volume source and the
prescribed boundary/interface fluxes. The function evaluates and returns
those compatibility residuals.

Each connected component also has one arbitrary additive constant in
``phi``. A zero-mean constraint is introduced through a Lagrange multiplier
per component. Gauge multipliers are numerical nullspace controls, not
physical stress resultants.

Axial distributed loading
-------------------------
This implementation requires ``dN_dz == 0``.

A non-zero scalar ``dN_dz`` states only the change of the total axial
resultant. It does not specify how the corresponding axial body load,
surface load or transfer is distributed over the cross-section. Because
different local distributions can produce the same resultant derivative,
using ``dN_dz`` alone would make the local source underdetermined. The
function therefore raises ``NotImplementedError`` rather than inventing a
distribution.

Optional Four-Quadrant validation
---------------------------------
``validation_points`` are diagnostic only. They are never used in assembly
and cannot change the solution.

At each validation point the solved triangle field is integrated on four
half-chords to obtain

    H_L, H_R, V_B, V_T.

These are compared with the independently differentiated Navier regional
resultants using

    dN_pp/dz =  H_R + V_T
    dN_mp/dz =  H_L - V_T
    dN_mm/dz = -H_L - V_B
    dN_pm/dz = -H_R + V_B.

The comparison is returned under ``validation`` and acts as an integral
equilibrium check; no projection is performed to force agreement.

Returned data
-------------
The result dictionary contains:

- ``section``:
  station, actions, derivative convention and derivative-step metadata;
- ``mesh``:
  node/triangle counts, refinement level and mesh tolerances;
- ``resultants``:
  area-integrated ``Tx_recovered``, ``Ty_recovered`` and their differences
  from the prescribed ``Tx``, ``Ty``;
- ``equilibrium``:
  source, boundary and interface integrals, global/component compatibility
  residuals, linear-system residual and gauge multipliers;
- ``triangles``:
  one row per triangle with coordinates, polygon identity, area,
  ``shear_weightabs``, potential gradient and piecewise-constant
  ``tau_x, tau_y``;
- ``validation``:
  optional Four-Quadrant half-chord comparisons.

Interpretation and limits
-------------------------
This is a reduced sectional equilibrium closure, not a general
three-dimensional elasticity solver. The recovered field is the
complementary-energy-minimizing field within the adopted scalar-potential
model.

The implementation has been regression-tested so that existing Navier,
Jourawski, centroid-axis and Four-Quadrant calculations are unchanged when
this API is not called.

NumPy, SciPy and Shapely >= 2.1 are imported lazily and are required only
when this function is executed.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `N` | `positional or keyword` | `float` | `-` |
| `Mx` | `positional or keyword` | `float` | `-` |
| `My` | `positional or keyword` | `float` | `-` |
| `Tx` | `positional or keyword` | `float` | `-` |
| `Ty` | `positional or keyword` | `float` | `-` |
| `dN_dz` | `keyword-only` | `float` | `0.0` |
| `dz` | `keyword-only` | `float | None` | `None` |
| `num_sudx` | `keyword-only` | `int` | `5` |
| `num_sudy` | `keyword-only` | `int` | `5` |
| `plot_mesh` | `keyword-only` | `bool` | `False` |
| `validation_points` | `keyword-only` | `tuple[tuple[float, float], ...] | None` | `None` |
| `compatibility_rtol` | `keyword-only` | `float` | `1e-08` |
| `compatibility_atol` | `keyword-only` | `float` | `1e-06` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`section`, `derivative`, `mesh`, `resultants`, `equilibrium`, `triangles`, `validation`, `z`, `N`, `Mx`, `My`, `Tx`, `Ty`, `dN_dz`, `step`, `scheme`, `dz_mode`, `strategy`, `initial_triangle_count`, `num_sudx`, `num_sudy`, `refinement_passes`, `refinement_history`, `x_teeth`, `y_teeth`, `x_comb_lines`, `y_comb_lines`, `node_count`, `triangle_count`, `connected_components`, `boundary_edge_count`, `interface_edge_count`, `merge_tolerance`, `Tx_recovered`, `Ty_recovered`, `Tx_error`, `Ty_error`, `source_integral`, `external_boundary_flux_integral`, `interface_jump_integral`, `global_compatibility_residual`, `max_component_compatibility_residual`, `component_compatibility`, `linear_residual_inf`, `gauge_multipliers`, `compatibility_rtol`, `compatibility_atol`, `component`, `residual`, `tolerance`, `idx`, `polygon_idx`, `name`, `shear_weightabs`, `area`, `cx`, `cy`, `x0`, `y0`, `x1`, `y1`, `x2`, `y2`, `tau_x`, `tau_y`, `dN_pp_dz`, `dN_mp_dz`, `dN_mm_dz`, `dN_pm_dz`, `x`, `y`

**Raises visible in the code**

- `NotImplementedError`
- `ValueError`
- `RuntimeError`
- `ImportError`

**Function/method calls visible in the code**

`float`, `int`, `bool`, `items`, `_potential_derivative_context`, `_potential_occupied_regions`, `_potential_initial_triangles`, `_potential_refine_triangles_comb_controlled`, `_potential_merge_mesh`, `len`, `lil_matrix`, `np.zeros`, `enumerate`, `_potential_mesh_edges`, `map`, `max`, `edges.items`, `_potential_connected_components`, `constraint.tocsc`, `stiffness.tocsc`, `csc_matrix`, `bmat`, `np.concatenate`, `spsolve`, `np.asarray`, `abs`, `NotImplementedError`, `ValueError`, `RuntimeError`, `_plot_potential_mesh_controlled`, `_potential_triangle_area_gradients`, `triangle_gradients.append`, `np.mean`, `range`, `component_compatibility.append`, `np.max`, `triangle_rows.append`, `ImportError`, `math.isfinite`, `_potential_sigma_z_at_point`, `math.sqrt`, `np.linalg.norm`, `_potential_edge_normal_from_triangle`, `np.sum`, `np.abs`, `_potential_partial_chord_flows`, `analyse_navier_four_quadrant_resultant_derivatives`, `predicted.items`, `validation_rows.append`, `str`, `tuple`, `domain.boundary.distance`, `_potential_boundary_velocity_at_point`, `_navier_sigma_at_point`, `_potential_edge_normal_between_triangles`, `ShapelyPoint`

### `analyse_navier_local_shear_potential`

**Source lines:** `8271-9131`

```python
def analyse_navier_local_shear_potentialsection_field, z: float, N: float, Mx: float, My: float, Tx: float, Ty: float, *, dN_dz: float=0.0, dz: float | None=None, mesh_refinements: int=4, plot_mesh: bool=False, validation_points: tuple[tuple[float, float], ...] | None=None, compatibility_rtol: float=1e-08, compatibility_atol: float=1e-06
```

**Summary:** Recover a local in-plane shear field from complete Navier equilibrium.

**Docstring details**

```text
Mechanical definition
---------------------
At the requested station the function first constructs the complete CSF
Navier stress field ``sigma_zz(x, y, z)`` using the physical section
geometry, polygon ``weightabs`` values and the supplied section actions.
Its longitudinal derivative is then evaluated at fixed global coordinates.

The local shear field is selected through the minimum-complementary-energy
closure

    tau = G_like * grad(phi),

with

    div(tau) = -partial(sigma_zz) / partial(z),

or equivalently

    div(G_like * grad(phi))
        = -partial(sigma_zz) / partial(z).

``G_like`` is the sampled polygon ``shear_weightabs``. It is not derived
from ``weightabs`` inside this routine and it is not replaced by a global
effective shear modulus.

This formulation is deliberately based on the derivative of the *complete*
Navier field. Centroid motion, inertia variation, material participation
variation and action gradients are therefore already contained in the
source. They must not be added again as independent taper or centroid
corrections.

Action-gradient convention
--------------------------
The local neighbouring action states follow the CSF convention

    dMx/dz = Ty
    dMy/dz = Tx.

``N`` is currently held constant. Accordingly ``dN_dz`` is accepted only
when it is zero; see "Axial distributed loading" below.

Occupied-region topology
------------------------
The transverse domain is built with the same index-based containment rule
used by the Four-Quadrant routines:

    occupied(parent)
        = parent - union(direct children).

This prevents double counting of nested material polygons. A region with
negligible ``weightabs`` and negligible ``shear_weightabs`` acts as a true
void and remains excluded from the active domain. A region carrying Navier
stress but having no positive shear carrier is rejected because the
elliptic closure would be locally degenerate.

Moving external boundaries
--------------------------
CSF vertex correspondence defines an in-plane boundary velocity

    v = (dx/dz, dy/dz).

On an external moving boundary the reduced traction condition is

    tau . n = sigma_zz * v_n,

where ``n`` is the outward unit normal and ``v_n = v . n``. A fixed external
boundary has ``v_n = 0`` and therefore carries zero prescribed normal shear
traction in this reduced problem.

Moving material interfaces
--------------------------
When two active regions share a moving interface, the weak jump condition is

    (tau_i - tau_j) . n
        = (sigma_zz_i - sigma_zz_j) * v_n.

Thus a fixed interface reduces automatically to continuity of normal shear
traction. The interface velocity is checked from both polygon descriptions;
inconsistent CSF interface kinematics raise an error instead of being
averaged silently.

Finite-element representation
-----------------------------
Each occupied polygonal region is constrained-triangulated. Uniform
refinement is then applied ``mesh_refinements`` times. The scalar potential
uses conforming P1 triangles. Consequently ``grad(phi)`` and the returned
``tau_x, tau_y`` are piecewise constant by triangle.

``mesh_refinements`` controls only numerical resolution. It does not change
the section model, the Navier source or the shear-participation field.

Mesh visualization
------------------
When ``plot_mesh=True``, the final triangulation and the exact CSF polygon
boundaries are displayed after mesh generation and before FEM assembly.
The visualization is diagnostic only and does not modify the mesh, the
assembled system or the returned solution. Matplotlib is required only
when this option is enabled.

Pure-Neumann compatibility and gauge
------------------------------------
The local problem is Neumann-only. For every disconnected active component,
solvability requires equality between the integrated volume source and the
prescribed boundary/interface fluxes. The function evaluates and returns
those compatibility residuals.

Each connected component also has one arbitrary additive constant in
``phi``. A zero-mean constraint is introduced through a Lagrange multiplier
per component. Gauge multipliers are numerical nullspace controls, not
physical stress resultants.

Axial distributed loading
-------------------------
This implementation requires ``dN_dz == 0``.

A non-zero scalar ``dN_dz`` states only the change of the total axial
resultant. It does not specify how the corresponding axial body load,
surface load or transfer is distributed over the cross-section. Because
different local distributions can produce the same resultant derivative,
using ``dN_dz`` alone would make the local source underdetermined. The
function therefore raises ``NotImplementedError`` rather than inventing a
distribution.

Optional Four-Quadrant validation
---------------------------------
``validation_points`` are diagnostic only. They are never used in assembly
and cannot change the solution.

At each validation point the solved triangle field is integrated on four
half-chords to obtain

    H_L, H_R, V_B, V_T.

These are compared with the independently differentiated Navier regional
resultants using

    dN_pp/dz =  H_R + V_T
    dN_mp/dz =  H_L - V_T
    dN_mm/dz = -H_L - V_B
    dN_pm/dz = -H_R + V_B.

The comparison is returned under ``validation`` and acts as an integral
equilibrium check; no projection is performed to force agreement.

Returned data
-------------
The result dictionary contains:

- ``section``:
  station, actions, derivative convention and derivative-step metadata;
- ``mesh``:
  node/triangle counts, refinement level and mesh tolerances;
- ``resultants``:
  area-integrated ``Tx_recovered``, ``Ty_recovered`` and their differences
  from the prescribed ``Tx``, ``Ty``;
- ``equilibrium``:
  source, boundary and interface integrals, global/component compatibility
  residuals, linear-system residual and gauge multipliers;
- ``triangles``:
  one row per triangle with coordinates, polygon identity, area,
  ``shear_weightabs``, potential gradient and piecewise-constant
  ``tau_x, tau_y``;
- ``validation``:
  optional Four-Quadrant half-chord comparisons.

Interpretation and limits
-------------------------
This is a reduced sectional equilibrium closure, not a general
three-dimensional elasticity solver. The recovered field is the
complementary-energy-minimizing field within the adopted scalar-potential
model.

The implementation has been regression-tested so that existing Navier,
Jourawski, centroid-axis and Four-Quadrant calculations are unchanged when
this API is not called.

NumPy, SciPy and Shapely >= 2.1 are imported lazily and are required only
when this function is executed.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `N` | `positional or keyword` | `float` | `-` |
| `Mx` | `positional or keyword` | `float` | `-` |
| `My` | `positional or keyword` | `float` | `-` |
| `Tx` | `positional or keyword` | `float` | `-` |
| `Ty` | `positional or keyword` | `float` | `-` |
| `dN_dz` | `keyword-only` | `float` | `0.0` |
| `dz` | `keyword-only` | `float | None` | `None` |
| `mesh_refinements` | `keyword-only` | `int` | `4` |
| `plot_mesh` | `keyword-only` | `bool` | `False` |
| `validation_points` | `keyword-only` | `tuple[tuple[float, float], ...] | None` | `None` |
| `compatibility_rtol` | `keyword-only` | `float` | `1e-08` |
| `compatibility_atol` | `keyword-only` | `float` | `1e-06` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`section`, `derivative`, `mesh`, `resultants`, `equilibrium`, `triangles`, `validation`, `z`, `N`, `Mx`, `My`, `Tx`, `Ty`, `dN_dz`, `step`, `scheme`, `dz_mode`, `initial_triangle_count`, `refinements`, `node_count`, `triangle_count`, `connected_components`, `boundary_edge_count`, `interface_edge_count`, `merge_tolerance`, `Tx_recovered`, `Ty_recovered`, `Tx_error`, `Ty_error`, `source_integral`, `external_boundary_flux_integral`, `interface_jump_integral`, `global_compatibility_residual`, `max_component_compatibility_residual`, `component_compatibility`, `linear_residual_inf`, `gauge_multipliers`, `compatibility_rtol`, `compatibility_atol`, `component`, `residual`, `tolerance`, `idx`, `polygon_idx`, `name`, `shear_weightabs`, `area`, `cx`, `cy`, `x0`, `y0`, `x1`, `y1`, `x2`, `y2`, `tau_x`, `tau_y`, `dN_pp_dz`, `dN_mp_dz`, `dN_mm_dz`, `dN_pm_dz`, `x`, `y`

**Raises visible in the code**

- `NotImplementedError`
- `ValueError`
- `RuntimeError`
- `ImportError`

**Function/method calls visible in the code**

`float`, `int`, `bool`, `items`, `_potential_derivative_context`, `_potential_occupied_regions`, `_potential_initial_triangles`, `_potential_refine_triangles`, `_potential_merge_mesh`, `len`, `lil_matrix`, `np.zeros`, `enumerate`, `_potential_mesh_edges`, `map`, `max`, `edges.items`, `_potential_connected_components`, `constraint.tocsc`, `stiffness.tocsc`, `csc_matrix`, `bmat`, `np.concatenate`, `spsolve`, `np.asarray`, `abs`, `NotImplementedError`, `ValueError`, `RuntimeError`, `_plot_potential_mesh`, `_potential_triangle_area_gradients`, `triangle_gradients.append`, `np.mean`, `range`, `component_compatibility.append`, `np.max`, `triangle_rows.append`, `ImportError`, `math.isfinite`, `_potential_sigma_z_at_point`, `math.sqrt`, `np.linalg.norm`, `_potential_edge_normal_from_triangle`, `np.sum`, `np.abs`, `_potential_partial_chord_flows`, `analyse_navier_four_quadrant_resultant_derivatives`, `predicted.items`, `validation_rows.append`, `str`, `tuple`, `domain.boundary.distance`, `_potential_boundary_velocity_at_point`, `_navier_sigma_at_point`, `_potential_edge_normal_between_triangles`, `ShapelyPoint`

### `analyse_polygon_navier_stress`

**Source lines:** `9134-9213`

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

`_navier_section_state`, `enumerate`, `str`, `float`, `min`, `max`, `rows.append`, `_navier_sigma_at_point`, `vertex_rows.append`, `ValueError`, `int`, `abs`

## integral equals the polygon area times its value at the polygon centroid.

### `_navier_quadrant_resultant`

**Source lines:** `2050-2071`

```python
def _navier_quadrant_resultant*, poly: Polygon, state: dict[str, object], x: float, y: float, x_positive: bool, y_positive: bool
```

**Summary:** Integrate the Navier field of ``poly`` over one quadrant clip.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `keyword-only` | `Polygon` | `-` |
| `state` | `keyword-only` | `dict[str, object]` | `-` |
| `x` | `keyword-only` | `float` | `-` |
| `y` | `keyword-only` | `float` | `-` |
| `x_positive` | `keyword-only` | `bool` | `-` |
| `y_positive` | `keyword-only` | `bool` | `-` |

**Returns:** `dict[str, float]`

**Function/method calls visible in the code**

`_clip_polygon_quadrant`, `_navier_resultant_over_points`, `float`, `bool`

### `analyse_navier_four_quadrant_resultants`

**Source lines:** `2074-2270`

```python
def analyse_navier_four_quadrant_resultantssection_field, z: float, N: float, Mx: float, My: float, x: float, y: float
```

**Summary:** Return Navier longitudinal-force resultants in the four quadrants.

**Docstring details**

```text
The point ``(x, y)`` defines two fixed Cartesian cuts of the actual
``Section(z)``. The quadrant convention is:

    pp : X >= x, Y >= y
    mp : X <= x, Y >= y
    mm : X <= x, Y <= y
    pm : X >= x, Y <= y

Each regional resultant is the exact area integral of the same affine
Navier field used by :func:`analyse_polygon_navier_stress`.

Polygon containment follows the CSF occupied-region rule:

    occupied(parent) = parent - direct_children(parent)

Therefore a parent polygon contributes only on its physically occupied
region, while each child contributes separately with its own ``weightabs``.
This prevents double counting in nested multi-material sections.

No shear equilibrium or longitudinal derivative is evaluated here. This
function only provides the Four-Quadrant Navier resultants at one station.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `N` | `positional or keyword` | `float` | `-` |
| `Mx` | `positional or keyword` | `float` | `-` |
| `My` | `positional or keyword` | `float` | `-` |
| `x` | `positional or keyword` | `float` | `-` |
| `y` | `positional or keyword` | `float` | `-` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`section`, `N_pp`, `N_mp`, `N_mm`, `N_pm`, `N_above`, `N_below`, `N_right`, `N_left`, `N_sum`, `N_residual`, `area_pp`, `area_mp`, `area_mm`, `area_pm`, `polygons`, `z`, `x`, `y`, `N`, `Mx`, `My`, `Cx`, `Cy`, `area`, `gross_area`, `gross_N`, `excluded_children`, `idx`, `name`, `weightabs`, `direct_children`, `quadrants`, `N_parent_field`

**Raises visible in the code**

- `TypeError`
- `ValueError`

**Function/method calls visible in the code**

`float`, `_navier_section_state`, `getattr`, `len`, `children_map.items`, `enumerate`, `build_children`, `children_map.get`, `polygon_rows.append`, `isinstance`, `TypeError`, `int`, `tuple`, `ValueError`, `_navier_quadrant_resultant`, `raw_children.items`, `_clip_polygon_quadrant`, `_navier_resultant_over_points`, `child_rows.append`, `abs`, `str`

## distribution required by the transverse equilibrium problem.

### `_potential_polygon_geometry`

**Source lines:** `2710-2747`

```python
def _potential_polygon_geometrypoly: Polygon
```

**Summary:** Convert one CSF polygon into a validated Shapely polygon.

**Docstring details**

```text
This helper performs only geometric validation. It does not apply CSF
containment, weights or shear participation. Those operations are handled
later so that raw polygon geometry and occupied material geometry remain
conceptually separate.

A zero-area, empty or self-invalid polygon cannot participate in the local
finite-element domain and is rejected immediately.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `poly` | `positional or keyword` | `Polygon` | `-` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`
- `ImportError`

**Function/method calls visible in the code**

`ShapelyPolygon`, `len`, `ValueError`, `ImportError`, `float`

### `_potential_polygon_components`

**Source lines:** `2750-2771`

```python
def _potential_polygon_componentsgeometry
```

**Summary:** Flatten a Shapely polygonal result into ordinary Polygon components.

**Docstring details**

```text
Difference operations used by the occupied-region construction may return
a Polygon, MultiPolygon or GeometryCollection. The potential mesh operates
on individual polygonal components, so this routine recursively extracts
only polygonal pieces and ignores non-area objects such as isolated lines
or points.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geometry` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `list[object]`

**Function/method calls visible in the code**

`str`, `getattr`, `components.extend`, `_potential_polygon_components`

## positive-area overlap is not.

### `_potential_signed_triangle_area`

**Source lines:** `2969-2982`

```python
def _potential_signed_triangle_areapoints
```

**Summary:** Return the signed area of one triangle.

**Docstring details**

```text
The sign is used only to enforce a consistent counter-clockwise orientation
before finite-element gradients are assembled. A positive orientation makes
the P1 gradient formulas and edge-normal conventions deterministic.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `float`

**Function/method calls visible in the code**

`float`

## Overlay the exact CSF polygon boundaries at the requested station.

### `_potential_comb_grid`

**Source lines:** `4425-4571`

```python
def _potential_comb_gridsection_field, z: float, *, num_sudx: int, num_sudy: int
```

**Summary:** Build the geometry-driven Cartesian comb used for mesh preview.

**Docstring details**

```text
The geometric teeth depend only on the current CSF section geometry:
polygon bounding-box minima/maxima are collected independently along x
and y and are retained exactly as comb boundaries.

``num_sudx`` and ``num_sudy`` do not generate teeth and do not define a
global background grid.  They specify how many equal sub-intervals are
created *between each pair of consecutive geometric teeth*:

    [x_i, x_(i+1)] -> num_sudx sub-intervals
    [y_j, y_(j+1)] -> num_sudy sub-intervals

The purpose of this helper is only to make that geometry-driven rule
visible before any potential-field discretization is selected.  It does
not assemble or solve the scalar-potential PDE.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section_field` | `positional or keyword` | `not annotated` | `-` |
| `z` | `positional or keyword` | `float` | `-` |
| `num_sudx` | `keyword-only` | `int` | `-` |
| `num_sudy` | `keyword-only` | `int` | `-` |

**Returns:** `dict[str, object]`

**Returned dictionary keys visible in the code**

`z`, `num_sudx`, `num_sudy`, `bbox`, `x_teeth`, `y_teeth`, `x_tooth_intervals`, `y_tooth_intervals`, `x_inserted`, `y_inserted`, `x_coords`, `y_coords`, `background_cell_count`, `regions`, `domain`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`int`, `float`, `section_field.section`, `_section_active_bbox`, `_axis_teeth`, `_subdivide_between_teeth`, `_potential_occupied_regions`, `ValueError`, `_unique_sorted`, `enumerate`, `tuple`, `max`, `min`, `teeth.append`, `zip`, `range`, `coords.append`, `inserted.append`, `len`

## Comb point-network potential solver (mesh-free GFD collocation)

### `_potential_comb_merge_nodes`

**Source lines:** `4864-4903`

```python
def _potential_comb_merge_nodesnetwork: dict[str, object]
```

**Summary:** Merge the two approved comb-node families into one geometric point set.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `network` | `positional or keyword` | `dict[str, object]` | `-` |

**Returns:** `tuple[object, float]`

**Raises visible in the code**

- `RuntimeError`
- `ImportError`

**Function/method calls visible in the code**

`max`, `np.asarray`, `abs`, `float`, `list`, `RuntimeError`, `ImportError`, `merged.setdefault`, `merged.values`, `len`, `int`, `round`

## Opposite incident normals can occur at a degenerate geometric point.

### `_potential_comb_gfd_weights`

**Source lines:** `5061-5182`

```python
def _potential_comb_gfd_weights*, query_point: tuple[float, float], region_node_indices, nodes, tree, operator: str, normal: tuple[float, float] | None=None, stencil_size: int=12, max_stencil_size: int=40
```

**Summary:** Return quadratic generalized-finite-difference weights at one point.

**Docstring details**

```text
A local quadratic polynomial is reconstructed from the nearest physical
comb nodes belonging to one occupied CSF region.  The polynomial basis is

    1, xi, eta, xi^2, xi*eta, eta^2,

with locally scaled coordinates.  The stencil is enlarged only when the
six-term basis is rank deficient.  No cell, triangle or element-quality
criterion enters the construction.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `query_point` | `keyword-only` | `tuple[float, float]` | `-` |
| `region_node_indices` | `keyword-only` | `not annotated` | `-` |
| `nodes` | `keyword-only` | `not annotated` | `-` |
| `tree` | `keyword-only` | `not annotated` | `-` |
| `operator` | `keyword-only` | `str` | `-` |
| `normal` | `keyword-only` | `tuple[float, float] | None` | `None` |
| `stencil_size` | `keyword-only` | `int` | `12` |
| `max_stencil_size` | `keyword-only` | `int` | `40` |

**Returns:** `tuple[object, object, dict[str, float | int]]`

**Returned dictionary keys visible in the code**

`stencil_size`, `rank`, `condition`, `radius`

**Raises visible in the code**

- `RuntimeError`
- `ImportError`
- `ValueError`

**Function/method calls visible in the code**

`np.asarray`, `max`, `min`, `float`, `range`, `np.linalg.pinv`, `len`, `RuntimeError`, `int`, `tree.query`, `astype`, `np.column_stack`, `ImportError`, `np.max`, `np.linalg.matrix_rank`, `np.linalg.cond`, `np.atleast_1d`, `np.linalg.norm`, `np.ones`, `map`, `ValueError`

## queried without rebuilding the point network or KD-trees.

### `evaluate_navier_local_shear_potential_comb`

**Source lines:** `5593-5664`

```python
def evaluate_navier_local_shear_potential_combresult: dict[str, object], *, x: float, y: float, polygon_idx: int | None=None
```

**Summary:** Evaluate phi, tau_x and tau_y from a solved comb/GFD potential field.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `result` | `positional or keyword` | `dict[str, object]` | `-` |
| `x` | `keyword-only` | `float` | `-` |
| `y` | `keyword-only` | `float` | `-` |
| `polygon_idx` | `keyword-only` | `int | None` | `None` |

**Returns:** `dict[str, float | int]`

**Returned dictionary keys visible in the code**

`region_idx`, `polygon_idx`, `phi`, `tau_x`, `tau_y`, `shear_weightabs`

**Raises visible in the code**

- `ValueError`
- `ImportError`

**Function/method calls visible in the code**

`float`, `ShapelyPoint`, `int`, `dict`, `ValueError`, `_potential_comb_gfd_weights`, `ImportError`, `enumerate`, `np.dot`, `covers`, `boundary.distance`

## Do not expose Shapely objects in the public diagnostic result.

### `_potential_triangle_area_gradients`

**Source lines:** `5771-5810`

```python
def _potential_triangle_area_gradientspoints
```

**Summary:** Return triangle area and constant P1 shape-function gradients.

**Docstring details**

```text
For a linear triangular potential

    phi = sum_i N_i * phi_i,

each ``grad(N_i)`` is constant. Therefore ``grad(phi)`` and the recovered
triangle shear vector ``G_like * grad(phi)`` are constant over the element.
Non-positive orientation is rejected because it would reverse the adopted
geometric conventions.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `points` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`map`, `ValueError`, `np.asarray`, `float`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
