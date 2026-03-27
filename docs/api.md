# CSF API Reference

> **Continuous Section Field** — Python engine for non-prismatic structural members.  
> Version: see `pyproject.toml` | License: GPL-3.0

---

## Table of Contents

1. [Geometry Primitives](#1-geometry-primitives)
   - [Pt](#pt)
   - [Polygon](#polygon)
   - [Section](#section)
2. [ContinuousSectionField](#2-continuoussectionfield)
   - [Constructor](#constructor)
   - [section()](#section)
   - [set_weight_laws()](#set_weight_laws)
   - [inspect_section_entities()](#inspect_section_entities)
   - [build_direct_children_map()](#build_direct_children_map)
   - [get_container_polygon_index()](#get_container_polygon_index)
   - [section_area_by_weight()](#section_area_by_weight)
   - [section_area_list_report()](#section_area_list_report)
   - [get_opensees_integration_points()](#get_opensees_integration_points)
   - [write_section()](#write_section)
   - [to_yaml()](#to_yaml)
3. [Section Analysis](#3-section-analysis)
   - [section_properties()](#section_properties)
   - [section_full_analysis()](#section_full_analysis)
   - [section_derived_properties()](#section_derived_properties)
   - [section_stiffness_matrix()](#section_stiffness_matrix)
   - [section_statical_moment_partial()](#section_statical_moment_partial)
   - [section_full_analysis_keys()](#section_full_analysis_keys)
4. [Polygon Utilities](#4-polygon-utilities)
   - [polygon_area_centroid()](#polygon_area_centroid)
   - [polygon_inertia_about_origin()](#polygon_inertia_about_origin)
   - [polygon_statical_moment()](#polygon_statical_moment)
   - [polygon_has_self_intersections()](#polygon_has_self_intersections)
   - [get_points_distance()](#get_points_distance)
   - [get_edge_length()](#get_edge_length)
   - [poly_from_string()](#poly_from_string)
5. [Torsion](#5-torsion)
   - [compute_saint_venant_Jv2()](#compute_saint_venant_jv2)
   - [compute_saint_venant_J_wall()](#compute_saint_venant_j_wall)
   - [compute_saint_venant_J_cell()](#compute_saint_venant_j_cell)
6. [Volume Integration](#6-volume-integration)
   - [integrate_volume()](#integrate_volume)
   - [volume_polygon_list_report()](#volume_polygon_list_report)
   - [volume_polygon_list_report_data()](#volume_polygon_list_report_data)
7. [Element Stiffness](#7-element-stiffness)
   - [assemble_element_stiffness_matrix()](#assemble_element_stiffness_matrix)
8. [Export](#8-export)
   - [write_opensees_geometry()](#write_opensees_geometry)
   - [write_sap2000_template_pack()](#write_sap2000_template_pack)
   - [export_to_opensees_tcl()](#export_to_opensees_tcl)
   - [export_polygon_vertices_csv()](#export_polygon_vertices_csv)
   - export_polygon_vertices_csv_file
10. [Quadrature Utilities](#9-quadrature-utilities)
   - [get_lobatto_intervals()](#get_lobatto_intervals)
11. [Weight Law Utilities](#10-weight-law-utilities)
    - [evaluate_weight_formula()](#evaluate_weight_formula)
    - [safe_evaluate_weight_zrelative()](#safe_evaluate_weight_zrelative)
    - [lookup_homogenized_elastic_modulus()](#lookup_homogenized_elastic_modulus)
12. [Visualization](#11-visualization)
    - [Visualizer](#visualizer)
13. [Exceptions](#12-exceptions)
    - [CSFError](#csferror)
14. [Module-level Constants](#13-module-level-constants)

---

## 1. Geometry Primitives

### `Pt`

```python
@dataclass(frozen=True)
class Pt:
    x: float
    y: float
```

Immutable 2D point. Used as the atomic vertex type throughout CSF.

| Attribute | Type | Description |
|-----------|------|-------------|
| `x` | `float` | Horizontal coordinate |
| `y` | `float` | Vertical coordinate |

#### `Pt.lerp(other, z_real, length) → Pt`

Linear interpolation between two vertices along the longitudinal axis.

| Parameter | Type | Description |
|-----------|------|-------------|
| `other` | `Pt` | End vertex |
| `z_real` | `float` | Distance from start (relative, 0 → `length`) |
| `length` | `float` | Total length of the interpolation segment |

**Returns:** `Pt` — interpolated point.

> **Note:** Returns `self` unchanged if `abs(length) < EPS_L`.

---

### `Polygon`

```python
@dataclass(frozen=True)
class Polygon:
    vertices:  Tuple[Pt, ...]
    weight:    float = 1.0
    name:      str   = ""
    weightabs: float = 1.0
```

Immutable closed polygon with homogenization weight.

| Attribute | Type | Description |
|-----------|------|-------------|
| `vertices` | `Tuple[Pt, ...]` | Vertex sequence in **Counter-Clockwise (CCW)** order |
| `weight` | `float` | Relative homogenization coefficient. Use negative values for voids/holes |
| `name` | `str` | Unique label within a section. Supports topology tags (see below) |
| `weightabs` | `float` | Absolute homogenization coefficient (computed internally at interpolation time) |

**Validation (raised at construction):**

- Fewer than 3 vertices → `ValueError`
- Clockwise or zero-area polygon → `ValueError`
- Area below `EPS_A` → `ValueError`

#### Polygon naming conventions and topology tags

Tags are appended to the base name with `@`:

| Tag | Meaning |
|-----|---------|
| `@wall` | Open thin-walled segment (Saint-Venant `J_wall`) |
| `@cell` or `@closed` | Closed thin-walled cell (Bredt-Batho `J_cell`) |
| `@t=<value>` | Explicit wall thickness in model units (e.g. `web@wall@t=0.012`) |

Tags are case-insensitive. Only one topology tag per name is allowed.

**Example:**
```python
from csf.section_field import Pt, Polygon

rect = Polygon(
    vertices=(Pt(0, 0), Pt(1, 0), Pt(1, 1), Pt(0, 1)),
    weight=1.0,
    name="flange",
)
```

---

### `Section`

```python
@dataclass(frozen=True)
class Section:
    polygons: Tuple[Polygon, ...]
    z:        float
```

Immutable cross-section at a given longitudinal coordinate.

| Attribute | Type | Description |
|-----------|------|-------------|
| `polygons` | `Tuple[Polygon, ...]` | Ordered tuple of polygons. All names must be unique |
| `z` | `float` | Absolute longitudinal coordinate |

**Validation (raised at construction):**

- Empty polygon tuple → `ValueError`
- Duplicate polygon names → `ValueError`
- Empty or whitespace-only polygon name → `ValueError`
- Non-`Polygon` element in tuple → `TypeError`
- `polygons` is not a `tuple` → `TypeError`

**Example:**
```python
from csf.section_field import Pt, Polygon, Section

s0 = Section(
    polygons=(
        Polygon(vertices=(Pt(-1,-0.2), Pt(1,-0.2), Pt(1,0.2), Pt(-1,0.2)), weight=1.0, name="flange"),
        Polygon(vertices=(Pt(-0.2,-1), Pt(0.2,-1), Pt(0.2,-0.2), Pt(-0.2,-0.2)), weight=1.0, name="web"),
    ),
    z=0.0,
)
```

---

## 2. ContinuousSectionField

The main engine. Stores two endpoint sections and provides interpolation and analysis at any longitudinal coordinate.

### Constructor

```python
ContinuousSectionField(section0: Section, section1: Section)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `section0` | `Section` | Start section at `z0` |
| `section1` | `Section` | End section at `z1` |

**Raises:**
- `ValueError` — if the two sections have a different number of polygons, or if `section0.z == section1.z`
- `ValueError` — if any polygon pair has a different number of vertices

**Internal attributes set at construction:**

| Attribute | Description |
|-----------|-------------|
| `s0`, `s1` | Start/end `Section` objects |
| `z0`, `z1` | Start/end absolute coordinates |
| `weight_laws` | `None` initially; set via `set_weight_laws()` |

**Example:**
```python
from csf.section_field import ContinuousSectionField

field = ContinuousSectionField(section0=s0, section1=s1)
```

---

### `section()`

```python
field.section(z: float) → Section
```

Returns the interpolated `Section` at absolute coordinate `z`.

- Vertices are linearly interpolated between `s0` and `s1`.
- Weights are interpolated via `_interpolate_weight()`, applying custom laws if set.
- Relative and absolute weights are both computed and stored in each returned `Polygon`.
- Topology tags (`@cell`, `@wall`, `@t=`) are resolved and propagated to the interpolated polygon name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `z` | `float` | Absolute coordinate in `[z0, z1]` |

**Returns:** `Section`

**Raises:** `CSFError` if `z` is outside `[z0, z1]`

---

### `set_weight_laws()`

```python
field.set_weight_laws(laws: Union[List[str], Dict[Union[int, str], str]]) → None
```

Defines custom weight variation laws along `z` for individual polygons.

Laws can be:
- **Python expression strings** evaluated at each `z` (e.g. `"w0 + (w1-w0)*t"`)
- **Numeric constants** (e.g. `"210e9"`)
- **File lookups** via `E_lookup('file.csv')` or `T_lookup('file.csv')`

#### Input formats

**List of strings** (name-based, preferred):
```python
field.set_weight_laws([
    "flange,flange: 1.0",
    "web,web: w0 + (w1-w0)*t**2",
])
```

**Dictionary** (index-based, 1-indexed):
```python
field.set_weight_laws({1: "1.0", 2: "w0 + (w1-w0)*t**2"})
```

#### Variables available in formula strings

| Variable | Description |
|----------|-------------|
| `w0` | Weight of the polygon at `s0` |
| `w1` | Weight of the polygon at `s1` |
| `z` | Relative coordinate from `z0` (= `z_abs - z0`) |
| `t` | Normalized coordinate in `[0, 1]` |
| `L` | Total field length (`z1 - z0`) |
| `d(i,j)` | Distance between vertices `i` and `j` at current `z` |
| `d0(i,j)` | Distance between vertices at `s0` |
| `d1(i,j)` | Distance between vertices at `s1` |
| `E_lookup(file)` | Interpolated value from a CSV file (column 0 = z, column 1 = E) |
| `T_lookup(file)` | Same but uses normalized `t` as lookup coordinate |
| `math`, `np` | Python `math` module and NumPy |

**Raises:**
- `KeyError` — polygon name not found in `s0` or `s1`
- `ValueError` — formula fails to evaluate at midpoint, or homology mismatch

---

### `inspect_section_entities()`

```python
field.inspect_section_entities(z: float) → List[Dict[str, Any]]
```

Sterile inspection of all polygon metadata at coordinate `z`. Does not modify state.

**Returns:** one dict per polygon with keys:

| Key | Type | Description |
|-----|------|-------------|
| `idx` | `int` | 0-based polygon index |
| `name` | `str\|None` | Polygon name at `z` |
| `s0_name` | `str\|None` | Name in `s0` |
| `s1_name` | `str\|None` | Name in `s1` |
| `s0_weight` | `float` | Weight in `s0` |
| `s1_weight` | `float` | Weight in `s1` |
| `weight_at_z` | `float` | Relative weight at `z` |
| `weight_abs_z` | `float` | Absolute weight at `z` (sum along container chain) |
| `weight_law` | `str\|None` | Active law string, or `None` |
| `area_signed` | `float` | Signed geometric area (CCW → positive) |
| `is_container` | `bool` | `True` if the polygon has direct children |
| `direct_children` | `List[str\|None]` | Names of direct child polygons |
| `container_idx` | `int\|None` | Index of direct parent, or `None` |
| `container_name` | `str\|None` | Name of direct parent, or `None` |

---

### `build_direct_children_map()`

```python
field.build_direct_children_map(z: float) → Dict[int, List[int]]
```

Returns the direct parent → children index map for polygons at `z`.

Topology is derived from `s0` geometry (stable ordering). Only polygons that have at least one direct child appear as keys.

**Returns:** `Dict[parent_idx, List[child_idx]]`

---

### `get_container_polygon_index()`

```python
field.get_container_polygon_index(poly: Polygon, i: int) → Optional[int]
```

Returns the 0-based index of the immediate container (direct parent) of `poly` in `s0.polygons`, or `None` if `poly` is a root polygon.

The immediate container is the smallest-area polygon that strictly contains `poly` with no intermediate polygon between them.

---

### `section_area_by_weight()`

```python
field.section_area_by_weight(
    z: float,
    w_tol: float = 0.0,
    include_per_polygon: bool = False,
    debug: bool = False,
    zero_w_eps: float = 0.0,
) → Dict[str, Any]
```

Computes area breakdown grouped by absolute weight at `z`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `z` | `float` | Longitudinal coordinate |
| `w_tol` | `float` | Grouping tolerance for weights |
| `include_per_polygon` | `bool` | If `True`, adds per-polygon detail records |
| `debug` | `bool` | Print debug table to stdout |
| `zero_w_eps` | `float` | Threshold for excluding near-zero weights from `total_area_nonzero` |

**Returns dict keys:**

| Key | Description |
|-----|-------------|
| `z` | Coordinate |
| `total_area` | Effective homogenized area = Σ(A_net × w_abs) |
| `total_area_nonzero` | Same but excluding \|w_abs\| ≤ `zero_w_eps` |
| `total_area_geometric` | Total net geometric surface = Σ A_net |
| `groups` | List of weight-grouped dicts (`w`, `area`, `polygons`, `area_fraction`) |
| `per_polygon` | *(optional)* Per-polygon detail records |

---

### `section_area_list_report()`

```python
field.section_area_list_report(
    z: float,
    w_tol: float = 0.0,
    zero_w_eps: float = 0.0,
    group_mode: str = "weight",
) → None
```

Prints an accountant-style area listing at `z` to stdout. Grouped by absolute weight. Includes totals for occupied surface and homogenized area.

---

### `get_opensees_integration_points()`

```python
field.get_opensees_integration_points(n_points: int = 5, L: float = None) → List[float]
```

Returns absolute `z` coordinates for Gauss-Lobatto integration points compatible with OpenSees `forceBeamColumn` elements.

| Parameter | Type | Description |
|-----------|------|-------------|
| `n_points` | `int` | Number of integration points (≥ 2). Includes both endpoints |
| `L` | `float\|None` | Override total length. If `None`, uses `z1 - z0` |

**Returns:** sorted list of absolute `z` coordinates.

---

### `write_section()`

```python
field.write_section(z0: float, z1: float, yaml_path: str) → None
```

Exports the interpolated sections at `z0` and `z1` to a YAML file.

Output includes polygon vertices, weights, and active weight laws. Write is atomic (temp file + rename).

**Raises:** `CSFError` on invalid coordinates, serialization failure, or I/O error.

---

### `to_yaml()`

```python
field.to_yaml(filepath: Optional[str] = None, include_weight_laws: bool = True) → str
```

Serializes the full field (both endpoint sections and weight laws) to a YAML string.

If `filepath` is provided, also writes to disk.

**Returns:** YAML string.

---

## 3. Section Analysis

### `section_properties()`

```python
section_properties(section: Section) → Dict[str, float]
```

Computes primary geometric properties of a composite cross-section.

Uses the Shoelace formula for area and centroid, then applies the Parallel Axis Theorem to compute centroidal moments of inertia. Polygon weights are applied as homogenization scalars.

**Returns:**

| Key | Description |
|-----|-------------|
| `z` | Longitudinal coordinate of the section |
| `A` | Net weighted area |
| `Cx` | Horizontal centroid coordinate |
| `Cy` | Vertical centroid coordinate |
| `Ix` | Second moment of area about centroidal X-axis |
| `Iy` | Second moment of area about centroidal Y-axis |
| `Ixy` | Product of inertia about centroidal axes |
| `Ip` | Polar moment of area (= Ix + Iy) |

**Raises:** `ValueError` if the composite area is near zero.

---

### `section_full_analysis()`

```python
section_full_analysis(section: Section) → Dict[str, Any]
```

Comprehensive analysis. Extends `section_properties()` with derived and advanced properties.

**Returns all keys from `section_properties()` plus:**

| Key | Description |
|-----|-------------|
| `I1` | Major principal second moment of area |
| `I2` | Minor principal second moment of area |
| `theta_rad` | Principal axis rotation angle (radians) |
| `theta_deg` | Principal axis rotation angle (degrees) |
| `rx` | Radius of gyration about centroidal X |
| `ry` | Radius of gyration about centroidal Y |
| `Wx` | Elastic section modulus about X (= Ix / y_max) |
| `Wy` | Elastic section modulus about Y (= Iy / x_max) |
| `K_torsion` | Semi-empirical torsional stiffness (≈ A⁴ / 40·Ip) |
| `Q_na` | First moment of area at the neutral axis |
| `J_sv_cell` | Saint-Venant J for closed thin-walled cells (Bredt-Batho) |
| `J_sv_wall` | Saint-Venant J for open thin-walled walls |
| `J_s_vroark` | Roark equivalent-rectangle torsion approximation |
| `J_s_vroark_fidelity` | Reliability index for Roark approximation (1.0 = thin-walled, 0.0 = compact) |

> **Torsion guidance:** For hollow closed sections use `J_sv_cell`. For open thin-walled profiles use `J_sv_wall`. `K_torsion` is a fallback for solid compact sections or when no `@wall`/`@cell` tags are present.

---

### `section_derived_properties()`

```python
section_derived_properties(props: Dict[str, float]) → Dict[str, float]
```

Computes principal axes and radii of gyration from a `section_properties()` dict.

| Parameter | Type | Description |
|-----------|------|-------------|
| `props` | `dict` | Output of `section_properties()` |

**Returns:** `I1`, `I2`, `theta_rad`, `theta_deg`, `rx`, `ry`

---

### `section_stiffness_matrix()`

```python
section_stiffness_matrix(section: Section, E_ref: float = 1.0) → np.ndarray
```

Returns the 3×3 constitutive stiffness matrix relating generalized strains to internal forces (N, Mx, My).

```
[ N  ]   [ EA    ESy   -ESx  ]   [ ε   ]
[ Mx ] = [ ESy   EIy   -EIxy ] × [ κx  ]
[ My ]   [-ESx  -EIxy   EIx  ]   [ κy  ]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `section` | `Section` | Cross-section to analyze |
| `E_ref` | `float` | Reference Young's modulus scale factor |

**Returns:** `np.ndarray` of shape `(3, 3)`

---

### `section_statical_moment_partial()`

```python
section_statical_moment_partial(
    section: Section,
    y_cut: float,
    reference_axis: Optional[float] = None,
) → float
```

Computes the first moment of area Q of the portion of the section above `y_cut`, about a horizontal reference axis.

Uses polygon clipping (Sutherland-Hodgman style) to isolate the portion above the cut.

| Parameter | Type | Description |
|-----------|------|-------------|
| `y_cut` | `float` | Horizontal cut coordinate |
| `reference_axis` | `float\|None` | Reference axis for Q. Defaults to the section centroid `Cy` |

**Returns:** `float` — statical moment Q.

---

### `section_full_analysis_keys()`

```python
section_full_analysis_keys() → List[str]
```

Returns the ordered list of keys produced by `section_full_analysis()`. Useful for CSV headers, mapping, or selective extraction.

---

## 4. Polygon Utilities

### `polygon_area_centroid()`

```python
polygon_area_centroid(poly: Polygon) → Tuple[float, Tuple[float, float]]
```

Returns `(weighted_area, (Cx, Cy))` for a single polygon using the Shoelace formula.

Weight is applied as a scalar to the signed area.

---

### `polygon_inertia_about_origin()`

```python
polygon_inertia_about_origin(poly: Polygon) → Tuple[float, float, float]
```

Returns `(Ix, Iy, Ixy)` about the global origin `(0, 0)`, including polygon weight.

---

### `polygon_statical_moment()`

```python
polygon_statical_moment(poly: Polygon, y_axis: float) → float
```

First moment of area of a polygon about a horizontal axis at `y_axis`.

Q = A × (Cy − y_axis), where Cy is the polygon centroid.

---

### `polygon_has_self_intersections()`

```python
polygon_has_self_intersections(poly: Polygon) → bool
```

Returns `True` if any two non-adjacent edges of the polygon intersect (including touching and collinear overlaps).

Uses a robust orientation test with tolerance `EPS_L`. Polygons with fewer than 4 vertices always return `False`.

---

### `get_points_distance()`

```python
get_points_distance(polygon: Polygon, i: int, j: int) → float
```

Euclidean distance between vertex `i` and vertex `j` of a polygon (0-based indices).

Primarily used inside weight law formula strings as `d(i, j)`.

---

### `get_edge_length()`

```python
get_edge_length(polygon: Polygon, edge_idx: int) → float
```

Length of the `edge_idx`-th edge (1-based). Edge `k` connects vertex `k-1` to vertex `k`.

---

### `poly_from_string()`

```python
poly_from_string(s: str, weight: float = 1.0, name: str = "") → Polygon
```

Convenience constructor. Parses a space-separated string of `x,y` pairs.

```python
rect = poly_from_string("-0.5,-0.5  0.5,-0.5  0.5,0.5  -0.5,0.5", weight=1.0, name="box")
```

---

## 5. Torsion

CSF provides three independent Saint-Venant torsion models. Each targets a different cross-section topology.

| Function | Model | Use when |
|----------|-------|----------|
| `compute_saint_venant_Jv2()` | Roark equivalent rectangle | Solid compact sections, fallback |
| `compute_saint_venant_J_wall()` | Open thin-walled (Σ b·t³/3) | Open profiles: I, C, L, T sections |
| `compute_saint_venant_J_cell()` | Bredt-Batho closed cell | Hollow tubes, box girders |

### `compute_saint_venant_Jv2()`

```python
compute_saint_venant_Jv2(poly_input: Any, verbose: bool = False) → Tuple[float, float]
```

Roark-style torsion approximation via equivalent solid rectangle mapping.

Works on both a single `Polygon` and a full `Section` (representation-invariant: aggregation happens before mapping).

**Returns:** `(J_total, fidelity)` where `fidelity ∈ (0, 1]` (1.0 = thin-walled, 0.0 = compact square).

---

### `compute_saint_venant_J_wall()`

```python
compute_saint_venant_J_wall(section: Section) → float  # or Tuple[float, float]
```

Open thin-walled Saint-Venant constant for polygons tagged with `@wall`.

For each `@wall` polygon:
- If `@t=<value>` is present: uses that thickness.
- Otherwise: estimates `t = 2·A / P`.

Contribution per wall: `J_i = A·t² / 3`

**Returns:**
- If a single `@wall` polygon: `(J_total, t)` tuple.
- If multiple `@wall` polygons: `J_total` scalar.
- If no `@wall` polygons: `0.0`.

---

### `compute_saint_venant_J_cell()`

```python
compute_saint_venant_J_cell(section: Section) → float  # or Tuple[float, float]
```

Closed thin-walled (Bredt-Batho) torsional constant for polygons tagged with `@cell` or `@closed`.

Expects a slit-encoded polygon (outer loop + inner loop joined by a radial bridge). Loops are auto-detected from repeated vertices.

Formula: `J ≈ 4·A_m²·t / b_m`

where `A_m` is the median enclosed area and `b_m` is the median perimeter.

**Returns:**
- If a single `@cell` polygon: `(J_total, t)` tuple.
- If multiple `@cell` polygons: `J_total` scalar.
- If no `@cell` polygons: `0.0`.

**Raises:** `CSFError` on degenerate geometry or invalid thickness.

---

## 6. Volume Integration

### `integrate_volume()`

```python
integrate_volume(
    field: ContinuousSectionField,
    z0: float,
    z1: float,
    n_points: int = 20,
    *,
    idx: Optional[int] = None,
) → Union[float, Tuple[float, float]]
```

Gauss-Legendre integration of cross-sectional area over `[z0, z1]`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `z0`, `z1` | `float` | Integration bounds (absolute) |
| `n_points` | `int` | Number of Gauss-Legendre quadrature points |
| `idx` | `int\|None` | If `None`: legacy mode (global area). If integer: single polygon mode |

**Returns:**
- `idx=None`: `float` — V = ∫ A(z) dz
- `idx=int`: `(V_geom, V_weighted)` — occupied and homogenized volumes for polygon `idx`

---

### `volume_polygon_list_report()`

```python
volume_polygon_list_report(
    field: ContinuousSectionField,
    z1: float,
    z2: float,
    *,
    n_points: int = 20,
    outputs: Optional[List[Any]] = None,
    fmt_display: str = "0.6f",
    w_tol: float = 0.0,
    do_debug_check: bool = False,
    debug_tol: float = 1e-9,
) → Dict[str, Any]
```

High-level API: builds and emits the per-polygon volume report between two stations.

`outputs` routing:
- `"stdout"` — prints to terminal
- `"path/to/file.txt"` — writes text report
- `"path/to/file.csv"` — writes CSV

**Returns:** report dict (same as `volume_polygon_list_report_data()`).

---

### `volume_polygon_list_report_data()`

```python
volume_polygon_list_report_data(
    field, z1, z2, n_points=20,
    *, do_debug_check=False, debug_tol=1e-9
) → Dict[str, Any]
```

Low-level data builder. Returns per-polygon volume records without emitting output.

**Returns dict keys:** `z1`, `z2`, `n_points`, `rows`, `tot_occ`, `tot_hom`, `debug`

Each row in `rows`:

| Key | Description |
|-----|-------------|
| `id` | Polygon index |
| `s0_w`, `s1_w` | Absolute weight at `z1` and `z2` |
| `weight_law` | Active law string |
| `s0_name`, `s1_name` | Polygon names |
| `volume_occupied` | Geometric volume (unweighted) |
| `homogenized_volume_occupied` | Weighted volume |

---

## 7. Element Stiffness

### `assemble_element_stiffness_matrix()`

```python
assemble_element_stiffness_matrix(
    field: ContinuousSectionField,
    E_ref: float = 1.0,
    nu: float = 0.3,
    n_gauss: int = 5,
) → np.ndarray
```

Assembles the complete 12×12 Timoshenko beam stiffness matrix with full EIxy coupling.

DOF order (OpenSees compatible):
```
[ux1, uy1, uz1, θx1, θy1, θz1 | ux2, uy2, uz2, θx2, θy2, θz2]
```

Uses Gauss-Legendre quadrature along the element axis. Torsion is taken from `J_sv_wall` or `J_sv_cell` if available, otherwise falls back to the Roark approximation.

**Returns:** `np.ndarray` of shape `(12, 12)`, symmetrized.

**Raises:**
- `ValueError` — negative diagonal stiffness detected
- `ValueError` — element length near zero

---

## 8. Export

### `write_opensees_geometry()`

```python
write_opensees_geometry(
    field: ContinuousSectionField,
    n_points: int,
    E_ref: float = 2.1e11,
    nu: float = 0.30,
    filename: str = "geometry.tcl",
) → None
```

Writes a CSF section data file intended to be **parsed as data**, not sourced as Tcl.

Each station produces one record:
```
section Elastic <tag> <E_ref> <A> <Iz> <Iy> <G_ref> <J_tors> <Cx> <Cy>
```

> **Important:** `Cx` and `Cy` are CSF-only fields appended for downstream parsers. Standard OpenSees Tcl would not accept them directly.

Torsion selection: `J_tors = J_sv_cell + J_sv_wall` if available; otherwise warns.

---

### `write_sap2000_template_pack()`

```python
write_sap2000_template_pack(
    field: ContinuousSectionField,
    n_intervals: int = 20,
    template_filename: str = "template.txt",
    *,
    mode: Literal["BOTH", "CENTROIDAL_LINE", "REFERENCE_LINE"] = "BOTH",
    section_prefix: str = "SEC",
    material_name: str = "S355",
    E_ref: Optional[float] = None,
    nu: Optional[float] = None,
    include_plot: bool = True,
    plot_filename: str = "section_variation.png",
    show_plot: bool = False,
    z_values: Optional[List[float]] = None,
    float_fmt: str = ".9g",
) → str
```

Generates a SAP2000 data pack text file. Not a direct import file — requires adaptation for specific SAP2000 versions.

`z_values` (if provided) must be strictly increasing and within `[z0, z1]`. If `None`, Gauss-Lobatto stations are used.

**Returns:** path of the written file.

---

### `export_to_opensees_tcl()`

```python
export_to_opensees_tcl(
    field: ContinuousSectionField,
    K_12x12: np.ndarray,
    filename: str = "csf_model.tcl",
) → None
```

Writes a complete OpenSees `.tcl` file defining 2 nodes and 1 `matrixBeamColumn` element from a precomputed 12×12 stiffness matrix.

---

### `export_polygon_vertices_csv()`

```python
export_polygon_vertices_csv(
    section: Optional[Section],
    field: ContinuousSectionField,
    zpos: Optional[float] = None,
    put=print,
    fmt: str = "{:.16g}",
) → None
```

Exports all polygon vertex coordinates to CSV format (one row per vertex).

Either `section` or both `field` + `zpos` must be provided (mutually exclusive).

CSV columns: `idx_polygon, idx_container, s0_name, s1_name, w, vertex_i, x, y`

---

## 9. Quadrature Utilities

### `get_lobatto_intervals()`

```python
get_lobatto_intervals(z_min: float, z_max: float, n_intervals: int) → np.ndarray
```

Computes Gauss-Lobatto station coordinates for `n_intervals` intervals (= `n_intervals + 1` stations). Both endpoints are included.

| Parameter | Type | Description |
|-----------|------|-------------|
| `z_min`, `z_max` | `float` | Physical interval bounds |
| `n_intervals` | `int` | Number of intervals (≥ 1) |

**Returns:** sorted `np.ndarray` of length `n_intervals + 1`.

---

## 10. Weight Law Utilities

### `evaluate_weight_formula()`

```python
evaluate_weight_formula(
    formula: str,
    p0: Polygon,
    p1: Polygon,
    z0: float,
    z1: float,
    zt: float,
) → float
```

Evaluates a weight law formula string at absolute coordinate `zt`. Used internally by `_interpolate_weight()`.

Runs in a sandboxed `eval()` with restricted builtins. See [set_weight_laws()](#set_weight_laws) for the full list of available variables.

---

### `safe_evaluate_weight_zrelative()`

```python
safe_evaluate_weight_zrelative(
    formula: str,
    p0: Polygon,
    p1: Polygon,
    z0: float,
    z1: float,
    z: float,
    print=True,
) → Tuple[float, dict]
```

Safe wrapper around `evaluate_weight_formula()` with full error trapping and structured reporting.

**Returns:** `(value, report_dict)`

Report dict keys: `status` (`"SUCCESS"`, `"WARNING"`, `"ERROR"`), `error_type`, `message`, `suggestion`, `z_pos`, `t_pos`, `formula`.

If `print=True`, emits a formatted inspector report to stdout.

---

### `lookup_homogenized_elastic_modulus()`

```python
lookup_homogenized_elastic_modulus(filename: str, zt: float) → float
```

Reads a two-column data file (`z`, `E`) and returns the interpolated value at `zt`.

- Boundary extrapolation: flat (nearest value).
- Internal interpolation: linear (LERP).
- Accepts comma, tab, or space delimiters.
- Lines starting with `#` are skipped.

**Raises:** `FileNotFoundError`, `ValueError` (no valid data in file).

---

## 11. Visualization

### `Visualizer`

```python
Visualizer(field: ContinuousSectionField)
```

Adds 2D and 3D plotting on top of a `ContinuousSectionField`.

#### `plot_section_2d()`

```python
viz.plot_section_2d(
    z: float,
    show_ids: bool = True,
    show_weights: bool = True,
    show_vertex_ids: bool = False,
    show_legenda: bool = False,
    title: Optional[str] = None,
    ax=None,
) → Axes
```

Draws the 2D cross-section at coordinate `z`. Returns the Matplotlib `Axes` object.

#### `plot_volume_3d()`

```python
viz.plot_volume_3d(
    show_end_sections: bool = True,
    line_percent: float = 100.0,
    seed: int = 0,
    title: str = "Ruled volume (vertex-connection lines)",
    ax=None,
) → Axes3D
```

Draws the 3D ruled solid skeleton (endpoint outlines + generator lines).

`line_percent` controls the fraction of generator lines shown (0–100). Useful for complex sections with many vertices.

#### `plot_properties()`

```python
viz.plot_properties(
    keys_to_plot: Optional[List[str]] = None,
    alpha: float = 1,
    num_points: int = 100,
) → None
```

Plots the evolution of selected section properties along `z`. One subplot per key.

Keys must match outputs of `section_full_analysis()`. If a property returns a `(value, thickness)` pair (e.g. torsion constants with `@cell`), the second value is plotted on a twin right axis.

#### `plot_weight()`

```python
viz.plot_weight(
    num_points: int = 100,
    tol: float = 1e-12,
    poly_indices_to_plot: Optional[List[int]] = None,
) → None
```

Plots `w(z)` for each polygon pair. Polygons with `w=0` for all sampled `z` are skipped and listed in a figure note. Min/max markers are shown on each curve.

---

## 12. Exceptions

### `CSFError`

```python
class CSFError(ValueError):
    ...
```

Raised for CSF-specific geometry or topology errors (invalid `z` bounds, degenerate polygon loops, incompatible topology tags, etc.).

Inherits from `ValueError` so it can be caught by broad `except ValueError` blocks.

---

## 13. Module-level Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `EPS_L` | `1e-12` | Linear/geometric tolerance (orientation tests, segment intersection) |
| `EPS_A` | `1e-12` | Area tolerance (degeneracy checks) |
| `EPS_K` | `1e-12` | Numerical/matrix absolute tolerance |
| `EPS_K_RTOL` | `1e-10` | Relative tolerance for matrix checks |
| `EPS_K_ATOL` | `1e-12` | Absolute tolerance for matrix checks |
| `DDEBUG` | `False` | Global debug flag (internal use) |

> **Note:** For models with large physical dimensions, `ContinuousSectionField` recomputes scale-aware tolerances internally via `_determine_magnitude()` after construction. The module-level constants above are used as fallbacks and for standalone functions.
