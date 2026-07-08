# API Reference - `section_field.py`

This document covers the top-level functions defined in `section_field.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Top-level function definitions found: `68`.
- Top-level classes found: `0`.
- `analyse_polygon_jourawski_shear_stress(...)` - line 111
- `analyse_polygon_navier_stress(...)` - line 868
- `get_lobatto_intervals(...)` - line 115
- `get_lobatto_intervals(z_min: float, z_max: float, n_intervals: int) -> 'np.ndarray'` - line 115
- `compute_lobatto_integration_points(z_min: float, z_max: float, n_points: int = 5, L: float = None) -> List[float]` - line 133
- `write_sap2000_template_pack(field: Any, n_intervals: int = 20, template_filename: str = 'export_template_pack.txt', *, mode: Literal['BOTH', 'CENTROIDAL_LINE', 'REFERENCE_LINE'] = 'BOTH', section_prefix: str = 'SEC', material_name: str = 'S355', E_ref: Optional[float] = None, nu: Optional[float] = None, include_plot: bool = True, plot_filename: str = 'section_variation.png', show_plot: bool = True, z_values: Optional[List[float]] = None, plot_n: int = 100, float_fmt: str = '.9g') -> str` - line 275
- `write_sap2000_geometry(*args: Any, **kwargs: Any) -> str` - line 632
- `safe_evaluate_weight_zrelative(formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float, print = True) -> tuple[float, dict]` - line 797
- `print_evaluation_report(value: float, report: dict)` - line 899
- `evaluate_shear_weight_formula(formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, zt: float, w: float) -> float` - line 962
- `evaluate_weight_formula(formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, zt: float) -> float` - line 1085
- `evaluate_weight_formula_zrelative(formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float) -> float` - line 1221
- `section_geometry(section: Section, fmt = '.8f')` - line 1282
- `section_print_analysis(full_analysis, fmt = '.8f')` - line 1303
- `section_full_analysis_keys() -> List[str]` - line 1359
- `write_opensees_geometry(field, n_points: int, E_ref: float = 210000000000.0, nu: float = 0.3, filename: str = 'geometry.tcl')` - line 1386
- `lookup_homogenized_elastic_modulus(filename: str, zt: float) -> float` - line 1617
- `compute_saint_venant_Jv2(poly_input: Any) -> Tuple[float, float]` - line 1860
- `calculate_t_eq(points)` - line 2209
- `compute_saint_venant_J_cell(section: 'Section') -> float` - line 2342
- `compute_saint_venant_J_wall(section: 'Section') -> float` - line 2858
- `export_to_opensees_tcl(field, K_12x12, filename = 'csf_model.tcl')` - line 3301
- `assemble_element_stiffness_matrix(field: ContinuousSectionField, E_ref: float = 1.0, nu: float = 0.3, n_gauss: int = 5) -> np.ndarray` - line 3337
- `polygon_inertia_about_origin(poly: Polygon) -> Tuple[float, float, float]` - line 3437
- `volume_polygon_list_report_data(field: 'ContinuousSectionField', z1: float, z2: float, n_points: int = 20, *, do_debug_check: bool = False, debug_tol: float = 1e-09) -> Dict[str, Any]` - line 3477
- `volume_polygon_list_report(field: ContinuousSectionField, z1: float, z2: float, *, n_points: int = 20, outputs: list[Any] | None = None, fmt_display: str = '0.6f', w_tol: float = 0.0, do_debug_check: bool = False, debug_tol: float = 1e-09) -> dict[str, Any]` - line 3598
- `emit_volume_polygon_list_report(report: Dict[str, Any], *, outputs: List[Any] | None = None, fmt_display: str = '0.6f', w_tol: float = 0.0) -> None` - line 3648
- `integrate_volume(field: 'ContinuousSectionField', z0: float, z1: float, n_points: int = 20, *, idx: int | None = None) -> float | tuple[float, float]` - line 3833
- `section_full_analysis(section: Section, compute_vroark = True)` - line 3944
- `polygon_statical_moment(poly: Polygon, y_axis: float) -> float` - line 4036
- `section_statical_moment_partial(section: Section, y_cut: float, reference_axis: float | None = None) -> float` - line 4051
- `section_derived_properties(props: Dict[str, float]) -> Dict[str, float]` - line 4137
- `section_stiffness_matrix(section: Section, E_ref: float = 1.0) -> np.ndarray` - line 4209
- `polygon_has_self_intersections(poly: Polygon) -> bool` - line 4325
- `get_points_distance(polygon: Polygon, i: int, j: int) -> float` - line 4427
- `get_edge_length(polygon: Polygon, edge_idx: int) -> float` - line 4456
- `list_polygons_with_contents(csf: ContinuousSectionField, z: float) -> List[Dict[str, Any]]` - line 4475
- `polygon_surface_w1_inners0(self: Any, z: float) -> List[Dict[str, Any]]` - line 4606
- `polygon_surface_w1_inners0_single(self: ContinuousSectionField, z: float, idx: int) -> Dict[str, Any]` - line 4813
- `export_polygon_vertices_csv_file(section: Section = None, field: ContinuousSectionField = None, zpos: float = None, exp_filename: str = 'csv_export.txt', z_values: Optional[List[float]] = None, fmt: str = '{:.16g}')` - line 5027
- `export_polygon_vertices_csv(section: Section = None, field: ContinuousSectionField = None, zpos: float = None, put = print, fmt = '{:.16g}')` - line 5085
- `section_properties(section: Section) -> Dict[str, float]` - line 5286
- `polygon_area_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]` - line 5403

## Internal/helper index

- `_compute_station_data(field: Any, z_values: Sequence[float]) -> List[Dict[str, Any]]` - line 197
- `_csf__is_finite_number(x: Any) -> bool` - line 647
- `_csf__ensure_parent_dir_exists(path: str) -> None` - line 656
- `_csf__atomic_write_text(path: str, text: str) -> None` - line 671
- `_csf__section_to_Sz_dict(section_obj, nodesection: str) -> Dict[str, Any]` - line 683
- `_yaml_scalar(v)` - line 747
- `_simple_yaml_dump(data, indent: int = 0) -> str` - line 771
- `_resolve_eps_a(obj: Any) -> float` - line 1740
- `_resolve_eps_k(obj: Any) -> float` - line 1744
- `_poly_signed_area_centroid(pts: Any, eps_a: float) -> Tuple[float, float, float]` - line 1752
- `_principal_inertias(ix: float, iy: float, ixy: float) -> Tuple[float, float]` - line 1795
- `_roark_torsion_rect(a: float, b: float) -> float` - line 1809
- `_equiv_rectangle_dims(A: float, i_min: float, eps_k: float) -> Tuple[float, float]` - line 1835
- `_poly_vertices_xy(poly: Any) -> List[PointXY]` - line 3067
- `_bbox_xy(verts: Sequence[PointXY]) -> Tuple[float, float, float, float]` - line 3078
- `_auto_grid_h_from_bbox(verts: Sequence[PointXY], auto_n: int) -> float` - line 3087
- `_point_on_segment_sq(px: float, py: float, ax: float, ay: float, bx: float, by: float, eps_l: float) -> bool` - line 3104
- `_point_in_poly_inclusive(px: float, py: float, verts: Sequence[PointXY], eps_l: float) -> bool` - line 3144
- `_build_inside_mask(verts: Sequence[PointXY], xs: np.ndarray, ys: np.ndarray, eps_l: float) -> np.ndarray` - line 3176
- `_solve_poisson_sor(mask: np.ndarray, h: float, *, max_iter: int, tol: float, omega: float) -> np.ndarray` - line 3197
- `_sq(x: float) -> float` - line 3249
- `_is_near_zero(x: float, eps: float) -> bool` - line 3253
- `_signed_area_centroid_xy(verts: Sequence[tuple[float, float]]) -> Tuple[float, float, float]` - line 3263
- `_poly_signed_area_centroid_xy(verts: Sequence[PointXY]) -> Tuple[float, float, float]` - line 3297
- `_segments_intersect(p1, p2, p3, p4) -> bool` - line 4274
- `_polygon_signed_area_and_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]` - line 5393

# API details


## Station generation


### `get_lobatto_intervals`

**Source lines:** `115-130`

```python
def get_lobatto_intervals(z_min: float, z_max: float, n_intervals: int) -> 'np.ndarray'
```

**Summary:** Docstring absent.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `z_min` | `float` | `-` |
| `z_max` | `float` | `-` |
| `n_intervals` | `int` | `-` |

**Returns:** `'np.ndarray'`


### `compute_lobatto_integration_points`

**Source lines:** `133-189`

```python
def compute_lobatto_integration_points(z_min: float, z_max: float, n_points: int = 5, L: float = None) -> List[float]
```

**Summary:** Calculates the global Z-coordinates for OpenSees integration points using the Gauss-Lobatto quadrature rule.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `z_min` | `float` | `-` |
| `z_max` | `float` | `-` |
| `n_points` | `int` | `5` |
| `L` | `float` | `None` |

**Returns:** `List[float]`


## Field sampling and solver export


### `_compute_station_data`

**Source lines:** `197-269`

```python
def _compute_station_data(field: Any, z_values: Sequence[float]) -> List[Dict[str, Any]]
```

**Summary:** Sample the CSF field at the provided z positions and compute section properties.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `field` | `Any` | `-` |
| `z_values` | `Sequence[float]` | `-` |

**Returns:** `List[Dict[str, Any]]`


### `write_sap2000_template_pack`

**Source lines:** `275-628`

```python
def write_sap2000_template_pack(field: Any, n_intervals: int = 20, template_filename: str = 'export_template_pack.txt', *, mode: Literal['BOTH', 'CENTROIDAL_LINE', 'REFERENCE_LINE'] = 'BOTH', section_prefix: str = 'SEC', material_name: str = 'S355', E_ref: Optional[float] = None, nu: Optional[float] = None, include_plot: bool = True, plot_filename: str = 'section_variation.png', show_plot: bool = True, z_values: Optional[List[float]] = None, plot_n: int = 100, float_fmt: str = '.9g') -> str
```

**Summary:** Export a CSF field to a structured text pack for SAP2000 / OpenSees input.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `field` | `Any` | `-` |
| `n_intervals` | `int` | `20` |
| `template_filename` | `str` | `'export_template_pack.txt'` |
| `mode` | `Literal['BOTH', 'CENTROIDAL_LINE', 'REFERENCE_LINE']` | `'BOTH'` |
| `section_prefix` | `str` | `'SEC'` |
| `material_name` | `str` | `'S355'` |
| `E_ref` | `Optional[float]` | `None` |
| `nu` | `Optional[float]` | `None` |
| `include_plot` | `bool` | `True` |
| `plot_filename` | `str` | `'section_variation.png'` |
| `show_plot` | `bool` | `True` |
| `z_values` | `Optional[List[float]]` | `None` |
| `plot_n` | `int` | `100` |
| `float_fmt` | `str` | `'.9g'` |

**Returns:** `str`


### `write_sap2000_geometry`

**Source lines:** `632-644`

```python
def write_sap2000_geometry(*args: Any, **kwargs: Any) -> str
```

**Summary:** Backward-compatible wrapper.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `*args` | `Any` | `-` |
| `**kwargs` | `Any` | `-` |

**Returns:** `str`


### `write_opensees_geometry`

**Source lines:** `1386-1614`

```python
def write_opensees_geometry(field, n_points: int, E_ref: float = 210000000000.0, nu: float = 0.3, filename: str = 'geometry.tcl')
```

**Summary:** Write a CSF-style OpenSees geometry file **as DATA** (to be parsed line-by-line), not as a Tcl script to be sourced.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `field` | `not annotated` | `-` |
| `n_points` | `int` | `-` |
| `E_ref` | `float` | `210000000000.0` |
| `nu` | `float` | `0.3` |
| `filename` | `str` | `'geometry.tcl'` |

**Returns:** `not annotated`


### `export_to_opensees_tcl`

**Source lines:** `3301-3334`

```python
def export_to_opensees_tcl(field, K_12x12, filename = 'csf_model.tcl')
```

**Summary:** Generates an OpenSees-ready .tcl file that defines the nodes and the stiffness-matrix element computed by CSF.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `field` | `not annotated` | `-` |
| `K_12x12` | `not annotated` | `-` |
| `filename` | `not annotated` | `'csf_model.tcl'` |

**Returns:** `not annotated`


## YAML and file helpers


### `_csf__is_finite_number`

**Source lines:** `647-653`

```python
def _csf__is_finite_number(x: Any) -> bool
```

**Summary:** Return True if x can be converted to a finite float.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `x` | `Any` | `-` |

**Returns:** `bool`


### `_csf__ensure_parent_dir_exists`

**Source lines:** `656-668`

```python
def _csf__ensure_parent_dir_exists(path: str) -> None
```

**Summary:** Ensure the parent directory exists; otherwise raise CSFError.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `path` | `str` | `-` |

**Returns:** `None`


### `_csf__atomic_write_text`

**Source lines:** `671-680`

```python
def _csf__atomic_write_text(path: str, text: str) -> None
```

**Summary:** Write a file atomically: 1) write to path + '.tmp' 2) os.replace to final name

**Parameters**

| Name | Type | Default |
|---|---|---|
| `path` | `str` | `-` |
| `text` | `str` | `-` |

**Returns:** `None`


### `_csf__section_to_Sz_dict`

**Source lines:** `683-744`

```python
def _csf__section_to_Sz_dict(section_obj, nodesection: str) -> Dict[str, Any]
```

**Summary:** Convert a computed Section into the minimal YAML dict format:

**Parameters**

| Name | Type | Default |
|---|---|---|
| `section_obj` | `not annotated` | `-` |
| `nodesection` | `str` | `-` |

**Returns:** `Dict[str, Any]`

**Returned dictionary keys visible in the code**

`nodesection`


### `_yaml_scalar`

**Source lines:** `747-768`

```python
def _yaml_scalar(v)
```

**Summary:** Docstring absent.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `v` | `not annotated` | `-` |

**Returns:** `not annotated`


### `_simple_yaml_dump`

**Source lines:** `771-795`

```python
def _simple_yaml_dump(data, indent: int = 0) -> str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `data` | `not annotated` | `-` |
| `indent` | `int` | `0` |

**Returns:** `str`


## Weight-law evaluation


### `safe_evaluate_weight_zrelative`

**Source lines:** `797-897`

```python
def safe_evaluate_weight_zrelative(formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float, print = True) -> tuple[float, dict]
```

**Summary:** Evaluates a weight formula string safely by trapping all potential exceptions.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `formula` | `str` | `-` |
| `p0` | `Polygon` | `-` |
| `p1` | `Polygon` | `-` |
| `z0` | `float` | `-` |
| `z1` | `float` | `-` |
| `z` | `float` | `-` |
| `print` | `not annotated` | `True` |

**Returns:** `tuple[float, dict]`


### `print_evaluation_report`

**Source lines:** `899-945`

```python
def print_evaluation_report(value: float, report: dict)
```

**Summary:** Prints minimalist structured report with Timestamp. Designed for traceability.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `value` | `float` | `-` |
| `report` | `dict` | `-` |

**Returns:** `not annotated`



### `evaluate_shear_weight_formula`

**Source lines:** `962-1083`

```python
def evaluate_shear_weight_formula(formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, zt: float, w: float) -> float
```

**Summary:** Evaluate a string-based shear-weight law.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `formula` | `str` | `-` |
| `p0` | `Polygon` | `-` |
| `p1` | `Polygon` | `-` |
| `z0` | `float` | `-` |
| `z1` | `float` | `-` |
| `zt` | `float` | `-` |
| `w` | `float` | `-` |

**Returns:** `float`


### `evaluate_weight_formula`

**Source lines:** `1085-1187`

```python
def evaluate_weight_formula(formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, zt: float) -> float
```

**Summary:** Wrapper function intended for use within 'eval()' contexts. It bridges the string evaluation to the structural lookup logic.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `formula` | `str` | `-` |
| `p0` | `Polygon` | `-` |
| `p1` | `Polygon` | `-` |
| `z0` | `float` | `-` |
| `z1` | `float` | `-` |
| `zt` | `float` | `-` |

**Returns:** `float`


### `evaluate_weight_formula_zrelative`

**Source lines:** `1221-1280`

```python
def evaluate_weight_formula_zrelative(formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float) -> float
```

**Summary:** Evaluates a string-based mathematical formula to determine the polygon weight at a

**Parameters**

| Name | Type | Default |
|---|---|---|
| `formula` | `str` | `-` |
| `p0` | `Polygon` | `-` |
| `p1` | `Polygon` | `-` |
| `z0` | `float` | `-` |
| `z1` | `float` | `-` |
| `z` | `float` | `-` |

**Returns:** `float`


### `lookup_homogenized_elastic_modulus`

**Source lines:** `1617-1709`

```python
def lookup_homogenized_elastic_modulus(filename: str, zt: float) -> float
```

**Summary:** Retrieves the elastic modulus (E) for a given longitudinal coordinate (z) from an external lookup file.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `filename` | `str` | `-` |
| `zt` | `float` | `-` |

**Returns:** `float`


## Section display and reports


### `section_geometry`

**Source lines:** `1282-1300`

```python
def section_geometry(section: Section, fmt = '.8f')
```

**Summary:** Prints the section structure keeping the original table layout. Uses 'fmt' for all vertex coordinates.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `section` | `Section` | `-` |
| `fmt` | `not annotated` | `'.8f'` |

**Returns:** `not annotated`


### `section_print_analysis`

**Source lines:** `1303-1357`

```python
def section_print_analysis(full_analysis, fmt = '.8f')
```

**Summary:** Prints the structural analysis report for a cross-section.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `full_analysis` | `not annotated` | `-` |
| `fmt` | `not annotated` | `'.8f'` |

**Returns:** `not annotated`


### `section_full_analysis_keys`

**Source lines:** `1359-1384`

```python
def section_full_analysis_keys() -> List[str]
```

**Summary:** Returns the ordered list of keys generated by the full analysis. Useful for mapping, CSV headers, or selective data extraction.

**Returns:** `List[str]`


### `volume_polygon_list_report_data`

**Source lines:** `3477-3596`

```python
def volume_polygon_list_report_data(field: 'ContinuousSectionField', z1: float, z2: float, n_points: int = 20, *, do_debug_check: bool = False, debug_tol: float = 1e-09) -> Dict[str, Any]
```

**Summary:** Build per-polygon volume report data between two stations.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `field` | `'ContinuousSectionField'` | `-` |
| `z1` | `float` | `-` |
| `z2` | `float` | `-` |
| `n_points` | `int` | `20` |
| `do_debug_check` | `bool` | `False` |
| `debug_tol` | `float` | `1e-09` |

**Returns:** `Dict[str, Any]`

**Returned dictionary keys visible in the code**

`z1`, `z2`, `n_points`, `rows`, `tot_occ`, `tot_hom`, `debug`


### `volume_polygon_list_report`

**Source lines:** `3598-3645`

```python
def volume_polygon_list_report(field: ContinuousSectionField, z1: float, z2: float, *, n_points: int = 20, outputs: list[Any] | None = None, fmt_display: str = '0.6f', w_tol: float = 0.0, do_debug_check: bool = False, debug_tol: float = 1e-09) -> dict[str, Any]
```

**Summary:** High-level API: build and emit the per-polygon volume report.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `field` | `ContinuousSectionField` | `-` |
| `z1` | `float` | `-` |
| `z2` | `float` | `-` |
| `n_points` | `int` | `20` |
| `outputs` | `list[Any] | None` | `None` |
| `fmt_display` | `str` | `'0.6f'` |
| `w_tol` | `float` | `0.0` |
| `do_debug_check` | `bool` | `False` |
| `debug_tol` | `float` | `1e-09` |

**Returns:** `dict[str, Any]`


### `emit_volume_polygon_list_report`

**Source lines:** `3648-3806`

```python
def emit_volume_polygon_list_report(report: Dict[str, Any], *, outputs: List[Any] | None = None, fmt_display: str = '0.6f', w_tol: float = 0.0) -> None
```

**Summary:** Emit a volume polygon-list report (stdout/text/CSV) using the same formatting as actions.volume.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `report` | `Dict[str, Any]` | `-` |
| `outputs` | `List[Any] | None` | `None` |
| `fmt_display` | `str` | `'0.6f'` |
| `w_tol` | `float` | `0.0` |

**Returns:** `None`


## Volume integration


### `integrate_volume`

**Source lines:** `3833-3941`

```python
def integrate_volume(field: 'ContinuousSectionField', z0: float, z1: float, n_points: int = 20, *, idx: int | None = None) -> float | tuple[float, float]
```

**Summary:** Integrate "volume-like" quantities over [z0, z1] using Gauss–Legendre quadrature.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `field` | `'ContinuousSectionField'` | `-` |
| `z0` | `float` | `-` |
| `z1` | `float` | `-` |
| `n_points` | `int` | `20` |
| `idx` | `int | None` | `None` |

**Returns:** `float | tuple[float, float]`


## Section properties and stiffness


### `section_full_analysis`

**Source lines:** `3944-4034`

```python
def section_full_analysis(section: Section, compute_vroark = True)
```

**Summary:** Perform a complete geometric and sectional analysis of a cross-section.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `section` | `Section` | `-` |
| `compute_vroark` | `not annotated` | `True` |

**Returns:** `not annotated`


### `section_properties`

**Source lines:** `5286-5389`

```python
def section_properties(section: Section) -> Dict[str, float]
```

**Summary:** Computes the integral geometric properties for a composite cross-section.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `section` | `Section` | `-` |

**Returns:** `Dict[str, float]`

**Returned dictionary keys visible in the code**

`z`, `A`, `Cx`, `Cy`, `Ix`, `Iy`, `Ixy`, `Ip`


### `section_derived_properties`

**Source lines:** `4137-4200`

```python
def section_derived_properties(props: Dict[str, float]) -> Dict[str, float]
```

**Summary:** Computes derived structural properties including principal moments of inertia, principal axis rotation, and radius of gyration.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `props` | `Dict[str, float]` | `-` |

**Returns:** `Dict[str, float]`

**Returned dictionary keys visible in the code**

`I1`, `I2`, `theta_rad`, `theta_deg`, `rx`, `ry`


### `polygon_statical_moment`

**Source lines:** `4036-4049`

```python
def polygon_statical_moment(poly: Polygon, y_axis: float) -> float
```

**Summary:** Computes the First Moment of Area (Statical Moment), Q, of a SINGLE polygon relative to a specific horizontal axis (y_axis).

**Parameters**

| Name | Type | Default |
|---|---|---|
| `poly` | `Polygon` | `-` |
| `y_axis` | `float` | `-` |

**Returns:** `float`


### `section_statical_moment_partial`

**Source lines:** `4051-4134`

```python
def section_statical_moment_partial(section: Section, y_cut: float, reference_axis: float | None = None) -> float
```

**Summary:** Compute the statical moment Q of the portion of the section located ABOVE y_cut, with respect to a horizontal reference axis y = y_ref.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `section` | `Section` | `-` |
| `y_cut` | `float` | `-` |
| `reference_axis` | `float | None` | `None` |

**Returns:** `float`


### `section_stiffness_matrix`

**Source lines:** `4209-4272`

```python
def section_stiffness_matrix(section: Section, E_ref: float = 1.0) -> np.ndarray
```

**Summary:** Assembles the 3x3 constitutive stiffness matrix relating generalized strains to internal forces (N, Mx, My).

**Parameters**

| Name | Type | Default |
|---|---|---|
| `section` | `Section` | `-` |
| `E_ref` | `float` | `1.0` |

**Returns:** `np.ndarray`


### `assemble_element_stiffness_matrix`

**Source lines:** `3337-3434`

```python
def assemble_element_stiffness_matrix(field: ContinuousSectionField, E_ref: float = 1.0, nu: float = 0.3, n_gauss: int = 5) -> np.ndarray
```

**Summary:** Assembles the complete 12x12 Timoshenko beam stiffness matrix with full EIxy coupling.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `field` | `ContinuousSectionField` | `-` |
| `E_ref` | `float` | `1.0` |
| `nu` | `float` | `0.3` |
| `n_gauss` | `int` | `5` |

**Returns:** `np.ndarray`


### `polygon_inertia_about_origin`

**Source lines:** `3437-3470`

```python
def polygon_inertia_about_origin(poly: Polygon) -> Tuple[float, float, float]
```

**Summary:** Second moments about the origin (0,0) using standard polygon formulas. Returns (Ix, Iy, Ixy) about origin, INCLUDING poly.weight.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `poly` | `Polygon` | `-` |

**Returns:** `Tuple[float, float, float]`


### `polygon_area_centroid`

**Source lines:** `5403-5407`

```python
def polygon_area_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `poly` | `Polygon` | `-` |

**Returns:** `Tuple[float, Tuple[float, float]]`


### `_polygon_signed_area_and_centroid`

**Source lines:** `5393-5401`

```python
def _polygon_signed_area_and_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]
```

**Summary:** Shoelace. with no weight

**Parameters**

| Name | Type | Default |
|---|---|---|
| `poly` | `Polygon` | `-` |

**Returns:** `Tuple[float, Tuple[float, float]]`


## Saint-Venant and torsion utilities


### `compute_saint_venant_Jv2`

**Source lines:** `1860-2206`

```python
def compute_saint_venant_Jv2(poly_input: Any) -> Tuple[float, float]
```

**Summary:** Estimate the Saint-Venant torsional constant J and a fidelity indicator.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `poly_input` | `Any` | `-` |

**Returns:** `Tuple[float, float]`


### `compute_saint_venant_J_cell`

**Source lines:** `2342-2801`

```python
def compute_saint_venant_J_cell(section: 'Section') -> float
```

**Summary:** Compute closed-cell Saint-Venant torsional constant J_sv [m^4] for polygons tagged as @cell/@closed using a thin-walled closed-cell model.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `section` | `'Section'` | `-` |

**Returns:** `float`


### `compute_saint_venant_J_wall`

**Source lines:** `2858-3064`

```python
def compute_saint_venant_J_wall(section: 'Section') -> float
```

**Summary:** Compute Saint-Venant torsional constant J_sv using "@WALL" polygons.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `section` | `'Section'` | `-` |

**Returns:** `float`


### `calculate_t_eq`

**Source lines:** `2209-2222`

```python
def calculate_t_eq(points)
```

**Summary:** Calcola t_eq = 2*A/P per poligono thin-walled. points: list [[x1,y1], [x2,y2], ..., [xn,yn]] linea mediana.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `points` | `not annotated` | `-` |

**Returns:** `not annotated`


### `_resolve_eps_a`

**Source lines:** `1740-1741`

```python
def _resolve_eps_a(obj: Any) -> float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `obj` | `Any` | `-` |

**Returns:** `float`


### `_resolve_eps_k`

**Source lines:** `1744-1745`

```python
def _resolve_eps_k(obj: Any) -> float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `obj` | `Any` | `-` |

**Returns:** `float`


### `_poly_signed_area_centroid`

**Source lines:** `1752-1792`

```python
def _poly_signed_area_centroid(pts: Any, eps_a: float) -> Tuple[float, float, float]
```

**Summary:** Shoelace integration.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `pts` | `Any` | `-` |
| `eps_a` | `float` | `-` |

**Returns:** `Tuple[float, float, float]`


### `_principal_inertias`

**Source lines:** `1795-1802`

```python
def _principal_inertias(ix: float, iy: float, ixy: float) -> Tuple[float, float]
```

**Summary:** Principal inertias (eigenvalues) of the 2x2 centroidal inertia tensor.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `ix` | `float` | `-` |
| `iy` | `float` | `-` |
| `ixy` | `float` | `-` |

**Returns:** `Tuple[float, float]`


### `_roark_torsion_rect`

**Source lines:** `1809-1832`

```python
def _roark_torsion_rect(a: float, b: float) -> float
```

**Summary:** Roark-style torsion approximation for a solid rectangular section.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `a` | `float` | `-` |
| `b` | `float` | `-` |

**Returns:** `float`


### `_equiv_rectangle_dims`

**Source lines:** `1835-1858`

```python
def _equiv_rectangle_dims(A: float, i_min: float, eps_k: float) -> Tuple[float, float]
```

**Summary:** Map (A, I_min) to equivalent rectangle dimensions (a >= b).

**Parameters**

| Name | Type | Default |
|---|---|---|
| `A` | `float` | `-` |
| `i_min` | `float` | `-` |
| `eps_k` | `float` | `-` |

**Returns:** `Tuple[float, float]`


## Polygon geometry predicates and utilities


### `_poly_vertices_xy`

**Source lines:** `3067-3075`

```python
def _poly_vertices_xy(poly: Any) -> List[PointXY]
```

**Summary:** Extract polygon vertices as plain (x, y) float tuples.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `poly` | `Any` | `-` |

**Returns:** `List[PointXY]`


### `_bbox_xy`

**Source lines:** `3078-3084`

```python
def _bbox_xy(verts: Sequence[PointXY]) -> Tuple[float, float, float, float]
```

**Summary:** Axis-aligned bounding box for a vertex list.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `verts` | `Sequence[PointXY]` | `-` |

**Returns:** `Tuple[float, float, float, float]`


### `_auto_grid_h_from_bbox`

**Source lines:** `3087-3101`

```python
def _auto_grid_h_from_bbox(verts: Sequence[PointXY], auto_n: int) -> float
```

**Summary:** Automatic grid spacing based on the polygon bounding box:

**Parameters**

| Name | Type | Default |
|---|---|---|
| `verts` | `Sequence[PointXY]` | `-` |
| `auto_n` | `int` | `-` |

**Returns:** `float`


### `_point_on_segment_sq`

**Source lines:** `3104-3141`

```python
def _point_on_segment_sq(px: float, py: float, ax: float, ay: float, bx: float, by: float, eps_l: float) -> bool
```

**Summary:** Return True if point (px,py) lies on segment AB, with tolerance.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `px` | `float` | `-` |
| `py` | `float` | `-` |
| `ax` | `float` | `-` |
| `ay` | `float` | `-` |
| `bx` | `float` | `-` |
| `by` | `float` | `-` |
| `eps_l` | `float` | `-` |

**Returns:** `bool`


### `_point_in_poly_inclusive`

**Source lines:** `3144-3173`

```python
def _point_in_poly_inclusive(px: float, py: float, verts: Sequence[PointXY], eps_l: float) -> bool
```

**Summary:** Ray casting point-in-polygon, counting boundary as inside.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `px` | `float` | `-` |
| `py` | `float` | `-` |
| `verts` | `Sequence[PointXY]` | `-` |
| `eps_l` | `float` | `-` |

**Returns:** `bool`


### `_build_inside_mask`

**Source lines:** `3176-3194`

```python
def _build_inside_mask(verts: Sequence[PointXY], xs: np.ndarray, ys: np.ndarray, eps_l: float) -> np.ndarray
```

**Summary:** Build boolean mask M[j,i] = True if grid node (xs[i], ys[j]) is inside polygon.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `verts` | `Sequence[PointXY]` | `-` |
| `xs` | `np.ndarray` | `-` |
| `ys` | `np.ndarray` | `-` |
| `eps_l` | `float` | `-` |

**Returns:** `np.ndarray`


### `_solve_poisson_sor`

**Source lines:** `3197-3247`

```python
def _solve_poisson_sor(mask: np.ndarray, h: float, *, max_iter: int, tol: float, omega: float) -> np.ndarray
```

**Summary:** Solve ∇²ψ = -2 on a masked grid using SOR, with ψ=0 outside.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `mask` | `np.ndarray` | `-` |
| `h` | `float` | `-` |
| `max_iter` | `int` | `-` |
| `tol` | `float` | `-` |
| `omega` | `float` | `-` |

**Returns:** `np.ndarray`


### `_sq`

**Source lines:** `3249-3250`

```python
def _sq(x: float) -> float
```

**Summary:** Docstring absent.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `x` | `float` | `-` |

**Returns:** `float`


### `_is_near_zero`

**Source lines:** `3253-3260`

```python
def _is_near_zero(x: float, eps: float) -> bool
```

**Summary:** Compare x to 0 using squared values to avoid abs().

**Parameters**

| Name | Type | Default |
|---|---|---|
| `x` | `float` | `-` |
| `eps` | `float` | `-` |

**Returns:** `bool`


### `_signed_area_centroid_xy`

**Source lines:** `3263-3294`

```python
def _signed_area_centroid_xy(verts: Sequence[tuple[float, float]]) -> Tuple[float, float, float]
```

**Summary:** Shoelace formula. Returns (A, Cx, Cy) not weight

**Parameters**

| Name | Type | Default |
|---|---|---|
| `verts` | `Sequence[tuple[float, float]]` | `-` |

**Returns:** `Tuple[float, float, float]`


### `_poly_signed_area_centroid_xy`

**Source lines:** `3297-3298`

```python
def _poly_signed_area_centroid_xy(verts: Sequence[PointXY]) -> Tuple[float, float, float]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `verts` | `Sequence[PointXY]` | `-` |

**Returns:** `Tuple[float, float, float]`


### `_segments_intersect`

**Source lines:** `4274-4323`

```python
def _segments_intersect(p1, p2, p3, p4) -> bool
```

**Summary:** Determines if two finite line segments (p1-p2 and p3-p4) intersect in a 2D plane.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `p1` | `not annotated` | `-` |
| `p2` | `not annotated` | `-` |
| `p3` | `not annotated` | `-` |
| `p4` | `not annotated` | `-` |

**Returns:** `bool`


### `polygon_has_self_intersections`

**Source lines:** `4325-4424`

```python
def polygon_has_self_intersections(poly: Polygon) -> bool
```

**Summary:** Returns True if the polygon has any self-intersection between NON-adjacent edges.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `poly` | `Polygon` | `-` |

**Returns:** `bool`


### `get_points_distance`

**Source lines:** `4427-4451`

```python
def get_points_distance(polygon: Polygon, i: int, j: int) -> float
```

**Summary:** Calculates the Euclidean distance between vertex i and vertex j of a polygon. Indices i and j are 1-based (from 1 to N).

**Parameters**

| Name | Type | Default |
|---|---|---|
| `polygon` | `Polygon` | `-` |
| `i` | `int` | `-` |
| `j` | `int` | `-` |

**Returns:** `float`


### `get_edge_length`

**Source lines:** `4456-4472`

```python
def get_edge_length(polygon: Polygon, edge_idx: int) -> float
```

**Summary:** Calculates the length of the j-th edge of a polygon. edge_idx is 1-based (1 to N).

**Parameters**

| Name | Type | Default |
|---|---|---|
| `polygon` | `Polygon` | `-` |
| `edge_idx` | `int` | `-` |

**Returns:** `float`


## Polygon content and surface accounting


### `list_polygons_with_contents`

**Source lines:** `4475-4603`

```python
def list_polygons_with_contents(csf: ContinuousSectionField, z: float) -> List[Dict[str, Any]]
```

**Summary:** Return one record per polygon at coordinate z, including direct containment.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `csf` | `ContinuousSectionField` | `-` |
| `z` | `float` | `-` |

**Returns:** `List[Dict[str, Any]]`


### `polygon_surface_w1_inners0`

**Source lines:** `4606-4810`

```python
def polygon_surface_w1_inners0(self: Any, z: float) -> List[Dict[str, Any]]
```

**Summary:** Compute the local occupied surface for every polygon at coordinate z using the rule: - w(polygon) = 1 - w(direct inners) = 0

**Parameters**

| Name | Type | Default |
|---|---|---|
| `z` | `float` | `-` |

**Returns:** `List[Dict[str, Any]]`


### `polygon_surface_w1_inners0_single`

**Source lines:** `4813-5025`

```python
def polygon_surface_w1_inners0_single(self: ContinuousSectionField, z: float, idx: int) -> Dict[str, Any]
```

**Summary:** Compute the local occupied surface for one polygon at coordinate z using the rule: - w(polygon) = 1 - w(direct inners) = 0

**Parameters**

| Name | Type | Default |
|---|---|---|
| `z` | `float` | `-` |
| `idx` | `int` | `-` |

**Returns:** `Dict[str, Any]`

**Returned dictionary keys visible in the code**

`idx`, `name`, `container_name`, `direct_inners`, `w`, `A`, `A_w`


## CSV export


### `export_polygon_vertices_csv_file`

**Source lines:** `5027-5083`

```python
def export_polygon_vertices_csv_file(section: Section = None, field: ContinuousSectionField = None, zpos: float = None, exp_filename: str = 'csv_export.txt', z_values: Optional[List[float]] = None, fmt: str = '{:.16g}')
```

**Summary:** File wrapper for export_polygon_vertices_csv().

**Parameters**

| Name | Type | Default |
|---|---|---|
| `section` | `Section` | `None` |
| `field` | `ContinuousSectionField` | `None` |
| `zpos` | `float` | `None` |
| `exp_filename` | `str` | `'csv_export.txt'` |
| `z_values` | `Optional[List[float]]` | `None` |
| `fmt` | `str` | `'{:.16g}'` |

**Returns:** `not annotated`


### `export_polygon_vertices_csv`

**Source lines:** `5085-5282`

```python
def export_polygon_vertices_csv(section: Section = None, field: ContinuousSectionField = None, zpos: float = None, put = print, fmt = '{:.16g}')
```

**Summary:** Export CSV with ALL coordinates.

**Parameters**

| Name | Type | Default |
|---|---|---|
| `section` | `Section` | `None` |
| `field` | `ContinuousSectionField` | `None` |
| `zpos` | `float` | `None` |
| `put` | `not annotated` | `print` |
| `fmt` | `not annotated` | `'{:.16g}'` |

**Returns:** `not annotated`


# Notes from the source structure

- `execute_string_to_float` is defined twice. The definition at line 1189 overrides the earlier definition at line 947 in normal Python import semantics.
- Several functions with leading underscore are imported by `continuous_section_field.py`; they are listed here because they are present in the module, even if they are internal by naming convention.
- `section_full_analysis()` returns the union of `section_properties()` and `section_derived_properties()`, then adds torsion-related quantities before returning `{**props, **derived}`.
- `section_properties()` returns `z`, `A`, `Cx`, `Cy`, `Ix`, `Iy`, `Ixy`, and `Ip`.
- `section_full_analysis_keys()` lists a subset of the full analysis keys used for mapping, CSV headers, or selective extraction.
