# CSF Stress APIs

CSF provides two polygon-wise stress-analysis functions for evaluating a section at a specified longitudinal station `z`:

- `analyse_polygon_navier_stress`
- `analyse_polygon_jourawski_shear_stress`

The functions operate directly on a `section_field` and return one result row for each polygon of the evaluated section.

They are intended for section-level stress evaluation. The user supplies the internal actions acting at the selected station.

---

# 1. Navier normal stress

Use:

```python
analyse_polygon_navier_stress
```

to evaluate signed normal stresses produced by:

- axial force `N`;
- bending moment `Mx`;
- bending moment `My`.

For each polygon, the function evaluates the stress field at the polygon vertices and returns:

- the minimum signed normal stress;
- the maximum signed normal stress;
- the signed value with the largest absolute magnitude;
- the corresponding vertex indices and coordinates.

Typical use:

```text
section_field + z + N + Mx + My
                ↓
polygon-wise normal-stress extrema
```

This function is used for axial and bending stress checks.

---

# 2. Jourawski shear stress

Use:

```python
analyse_polygon_jourawski_shear_stress
```

to evaluate signed Jourawski shear stresses produced by:

- `Tx`, the shear component associated with the longitudinal gradient of `My`;
- `Ty`, the shear component associated with the longitudinal gradient of `Mx`.

For a beam action field:

```python
Tx = dMy_dz
Ty = dMx_dz
```

The function performs x-direction and y-direction section scans.

For each polygon, it returns:

- `tau_x_min`;
- `tau_x_max`;
- `tau_y_min`;
- `tau_y_max`;
- the coordinates associated with each value;
- scan and convergence information.

Typical use:

```text
section_field + z + Tx + Ty + scan subdivisions
                ↓
polygon-wise Jourawski shear-stress extrema
```

This function is used for transverse shear-stress checks.

---

# 3. Main distinction

The two functions evaluate different stress components:

| Function | Internal actions | Returned stress |
|---|---|---|
| `analyse_polygon_navier_stress` | `N`, `Mx`, `My` | Normal stress `sigma` |
| `analyse_polygon_jourawski_shear_stress` | `Tx`, `Ty` | Shear stress `tau` |

Both functions:

- evaluate the CSF section at station `z`;
- preserve the signs of the supplied actions;
- return polygon identity and stress locations;
- provide one result dictionary for each polygon.

---

# 4. Typical combined workflow

```python
z = 0.0

navier_rows = analyse_polygon_navier_stress(
    section_field=section_field,
    z=z,
    N=N,
    Mx=Mx,
    My=My,
)

shear_rows = analyse_polygon_jourawski_shear_stress(
    section_field=section_field,
    z=z,
    Tx=Tx,
    Ty=Ty,
    num_sudx=100,
    num_sudy=100,
    debug=False,
)
```

The returned rows can then be:

- written to CSV;
- summarized in a text report;
- matched to polygons in a graphical section report;
- filtered by polygon name or polygon index.

---

# 5. Polygon identification

The primary polygon identifier is:

```text
polygon index
```

The polygon name provides a readable identifier.

For report-to-plot verification, use:

```text
z + polygon index
```

and verify the associated polygon name, stress value and coordinates.

---

# 6. Sign convention

The APIs use the values supplied by the caller.

No automatic sign correction should be assumed.

The sign convention of:

- `N`;
- `Mx`;
- `My`;
- `Tx`;
- `Ty`;

must therefore be consistent with the action model used by the caller.

The returned stresses preserve the resulting sign.

---

# 7. Units

The APIs do not impose a unit system.

All inputs must use one consistent unit system.

For example, using:

```text
force  = N
length = m
moment = N·m
```

produces stresses in:

```text
Pa
```

---

# 8. Derived governing shear value

`tau_governing` is not returned directly by:

```python
analyse_polygon_jourawski_shear_stress
```

It is a derived report value.

For one polygon, it is selected from:

```text
tau_x_min
tau_x_max
tau_y_min
tau_y_max
```

using the largest absolute magnitude while preserving the original sign.

The associated direction and coordinates are taken from the selected source field.

---

# Detailed API Reference

# 1. Navier Stress API

## Function

```python
from csf.section_field import analyse_polygon_navier_stress
```

```python
analyse_polygon_navier_stress(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
) -> list[dict[str, object]]
```

## Input values

| Parameter | Type | Meaning |
|---|---:|---|
| `section_field` | CSF field | Continuous Section Field object |
| `z` | `float` | Section station |
| `N` | `float` | Signed axial force |
| `Mx` | `float` | Signed bending moment about the x axis |
| `My` | `float` | Signed bending moment about the y axis |

The force and moment signs are passed directly to the API.

## Basic example

```python
from csf.section_field import analyse_polygon_navier_stress

rows = analyse_polygon_navier_stress(
    section_field=section_field,
    z=0.0,
    N=-1.0e6,
    Mx=2.0e5,
    My=0.0,
)
```

## Output

The function returns one dictionary for each polygon.

Main output fields:

| Field | Meaning |
|---|---|
| `idx` | Polygon index |
| `name` | Polygon name |
| `sigma_min` | Minimum signed normal stress in the polygon |
| `sigma_max` | Maximum signed normal stress in the polygon |
| `sigma_extreme` | Signed normal stress with the largest absolute value |
| `vertex_index_min` | Vertex index corresponding to `sigma_min` |
| `x_min` | x coordinate corresponding to `sigma_min` |
| `y_min` | y coordinate corresponding to `sigma_min` |
| `vertex_index_max` | Vertex index corresponding to `sigma_max` |
| `x_max` | x coordinate corresponding to `sigma_max` |
| `y_max` | y coordinate corresponding to `sigma_max` |
| `vertex_index` | Vertex index corresponding to `sigma_extreme` |
| `x` | x coordinate corresponding to `sigma_extreme` |
| `y` | y coordinate corresponding to `sigma_extreme` |

## Reading the result

```python
for row in rows:
    print(
        row["idx"],
        row["name"],
        row["sigma_min"],
        row["sigma_max"],
        row["sigma_extreme"],
        row["x"],
        row["y"],
    )
```

` sigma_extreme ` preserves its original sign.

---

# 2. Jourawski Shear Stress API

## Function

```python
from csf.section_field import analyse_polygon_jourawski_shear_stress
```

```python
analyse_polygon_jourawski_shear_stress(
    section_field,
    z: float,
    Tx: float,
    Ty: float,
    num_sudx: int,
    num_sudy: int,
    debug: bool = False,
) -> list[dict[str, object]]
```

## Input values

| Parameter | Type | Meaning |
|---|---:|---|
| `section_field` | CSF field | Continuous Section Field object |
| `z` | `float` | Section station |
| `Tx` | `float` | Signed shear component associated with `My` |
| `Ty` | `float` | Signed shear component associated with `Mx` |
| `num_sudx` | `int` | Number of subdivisions used for the x-direction scan |
| `num_sudy` | `int` | Number of subdivisions used for the y-direction scan |
| `debug` | `bool` | Enables additional diagnostic output |

For a beam action field:

```python
Tx = dMy_dz
Ty = dMx_dz
```

## Basic example

```python
from csf.section_field import analyse_polygon_jourawski_shear_stress

rows = analyse_polygon_jourawski_shear_stress(
    section_field=section_field,
    z=0.0,
    Tx=0.0,
    Ty=-9.0e3,
    num_sudx=100,
    num_sudy=100,
    debug=False,
)
```

## Main output

The function returns one dictionary for each polygon.

| Field | Meaning |
|---|---|
| `idx` | Polygon index |
| `name` | Polygon name |
| `tau_x_min` | Minimum signed x-direction Jourawski shear stress |
| `tau_x_max` | Maximum signed x-direction Jourawski shear stress |
| `tau_y_min` | Minimum signed y-direction Jourawski shear stress |
| `tau_y_max` | Maximum signed y-direction Jourawski shear stress |
| `x_tau_x_min` | x coordinate corresponding to `tau_x_min` |
| `y_tau_x_min` | y coordinate corresponding to `tau_x_min` |
| `x_tau_x_max` | x coordinate corresponding to `tau_x_max` |
| `y_tau_x_max` | y coordinate corresponding to `tau_x_max` |
| `x_tau_y_min` | x coordinate corresponding to `tau_y_min` |
| `y_tau_y_min` | y coordinate corresponding to `tau_y_min` |
| `x_tau_y_max` | x coordinate corresponding to `tau_y_max` |
| `y_tau_y_max` | y coordinate corresponding to `tau_y_max` |
| `tau_x_mean` | Mean x-direction shear stress reported for the polygon |
| `tau_y_mean` | Mean y-direction shear stress reported for the polygon |
| `scan_count_x` | Number of x-direction scan values |
| `scan_count_y` | Number of y-direction scan values |
| `converged_x` | x-direction scan convergence flag |
| `converged_y` | y-direction scan convergence flag |

Weight-related fields may also be returned:

| Field | Meaning |
|---|---|
| `weight` | Polygon shear weight used at the section |
| `weight_ref` | Reference shear weight |
| `weight_norm` | Normalized shear weight |

## Reading the result

```python
for row in rows:
    print(
        row["idx"],
        row["name"],
        row["tau_x_min"],
        row["tau_x_max"],
        row["tau_y_min"],
        row["tau_y_max"],
    )
```

## Governing shear stress in one polygon

The signed governing value can be selected as follows:

```python
candidates = [
    ("x", row["tau_x_min"], row["x_tau_x_min"], row["y_tau_x_min"]),
    ("x", row["tau_x_max"], row["x_tau_x_max"], row["y_tau_x_max"]),
    ("y", row["tau_y_min"], row["x_tau_y_min"], row["y_tau_y_min"]),
    ("y", row["tau_y_max"], row["x_tau_y_max"], row["y_tau_y_max"]),
]

direction, tau_governing, x, y = max(
    candidates,
    key=lambda item: abs(item[1]),
)
```

`tau_governing` is the signed Jourawski shear-stress value with the largest absolute magnitude in the polygon.

The original sign is preserved.

## Returned governing values

| Value | Meaning |
|---|---|
| `tau_governing` | Signed shear stress with the largest absolute value |
| `direction` | `x` or `y`, according to the selected component |
| `x` | x coordinate associated with the selected value |
| `y` | y coordinate associated with the selected value |

---

# Minimal Combined Example

```python
from csf.section_field import (
    analyse_polygon_jourawski_shear_stress,
    analyse_polygon_navier_stress,
)

z = 0.0

navier_rows = analyse_polygon_navier_stress(
    section_field=section_field,
    z=z,
    N=-1.0e6,
    Mx=2.0e5,
    My=0.0,
)

shear_rows = analyse_polygon_jourawski_shear_stress(
    section_field=section_field,
    z=z,
    Tx=0.0,
    Ty=-9.0e3,
    num_sudx=100,
    num_sudy=100,
    debug=False,
)
```


## Complete in-code stress-analysis example

The following example provides a complete section-level workflow using the CSF stress APIs without external geometry or settings files.

A tapered rectangular member is defined directly in Python by specifying its start and end sections. CSF interpolates the geometry continuously along the longitudinal coordinate `z`, and the section at the selected station is generated from the resulting `ContinuousSectionField`.

The internal actions are prescribed directly at the evaluated station:

- `N`, `Mx`, and `My` are used by `analyse_polygon_navier_stress`;
- `Tx` and `Ty` are used by `analyse_polygon_jourawski_shear_stress`.

Their derivation from a beam solver or structural model is intentionally outside the scope of the example. This keeps the workflow focused on the use of the section-level APIs once the internal actions are known.

The example shows how to:

- construct a CSF model directly in Python;
- evaluate an interpolated section at a specified `z`;
- compute its main section properties;
- obtain polygon-wise Navier normal-stress extrema;
- obtain polygon-wise Jourawski shear-stress extrema;
- select the signed governing shear value while preserving its direction and coordinates.

The model contains one polygon, but the same workflow applies to sections composed of multiple polygons with different geometry or material weights.

```python
"""
Minimal end-to-end example of the CSF stress-analysis APIs.

The model is built directly in Python, without external geometry or
settings files. One section of a tapered rectangular field is evaluated
under prescribed internal actions.

Workflow:
    1. define the start and end sections;
    2. create the Continuous Section Field;
    3. select one station z;
    4. assign the internal actions at that station;
    5. compute Navier normal stresses;
    6. compute Jourawski shear stresses;
    7. print the polygon-wise governing results.

The derivation of the internal actions from a beam or structural model is
outside the scope of this section-level example.
"""

from csf import (
    ContinuousSectionField,
    Polygon,
    Pt,
    Section,
    section_properties,
)
from csf.section_field import (
    analyse_polygon_jourawski_shear_stress,
    analyse_polygon_navier_stress,
)


# ---------------------------------------------------------------------------
# 1. BUILD A TAPERED RECTANGULAR CONTINUOUS SECTION FIELD
# ---------------------------------------------------------------------------

L = 5.0

# Start section at z = 0.0.
#
# Rectangle dimensions:
#     width  = 0.40 m
#     height = 0.60 m
#
# Vertices are listed in counter-clockwise order.
start_rectangle = Polygon(
    vertices=(
        Pt(-0.20, -0.30),
        Pt(0.20, -0.30),
        Pt(0.20, 0.30),
        Pt(-0.20, 0.30),
    ),
    weight=1.0,
    name="rectangle",
)

# End section at z = L.
#
# Rectangle dimensions:
#     width  = 0.30 m
#     height = 0.40 m
#
# The polygon name, vertex count and vertex order match the start section,
# allowing CSF to interpolate the geometry continuously along z.
end_rectangle = Polygon(
    vertices=(
        Pt(-0.15, -0.20),
        Pt(0.15, -0.20),
        Pt(0.15, 0.20),
        Pt(-0.15, 0.20),
    ),
    weight=1.0,
    name="rectangle",
)

section_start = Section(
    polygons=(start_rectangle,),
    z=0.0,
)

section_end = Section(
    polygons=(end_rectangle,),
    z=L,
)

field = ContinuousSectionField(
    section0=section_start,
    section1=section_end,
)


# ---------------------------------------------------------------------------
# 2. SELECT THE STATION AND ASSIGN THE INTERNAL ACTIONS
# ---------------------------------------------------------------------------

# Section station to be evaluated.
z = 2.5

# Signed internal actions acting directly on the section at z.
#
# Navier uses:
#     N, Mx, My
#
# Jourawski uses:
#     Tx, Ty
#
# The values are prescribed inputs. 
N = -100_000.0   # Axial force [N]
Mx = 25_000.0    # Bending moment about the x axis [N·m]
My = 10_000.0    # Bending moment about the y axis [N·m]
Tx = 5_000.0     # Shear component associated with My [N]
Ty = -10_000.0   # Shear component associated with Mx [N]


# ---------------------------------------------------------------------------
# 3. COMPUTE THE SECTION PROPERTIES AT z
# ---------------------------------------------------------------------------

section_at_z = field.section(z)
properties = section_properties(section_at_z)


# ---------------------------------------------------------------------------
# 4. COMPUTE NAVIER NORMAL STRESSES
# ---------------------------------------------------------------------------

# One result dictionary is returned for each polygon.
navier_rows = analyse_polygon_navier_stress(
    section_field=field,
    z=z,
    N=N,
    Mx=Mx,
    My=My,
)


# ---------------------------------------------------------------------------
# 5. COMPUTE JOURAWSKI SHEAR STRESSES
# ---------------------------------------------------------------------------

# num_sudx and num_sudy control the scan resolution used to locate
# the shear-stress extrema.
shear_rows = analyse_polygon_jourawski_shear_stress(
    section_field=field,
    z=z,
    Tx=Tx,
    Ty=Ty,
    num_sudx=40,
    num_sudy=40,
    debug=False,
)


# ---------------------------------------------------------------------------
# 6. PRINT SECTION PROPERTIES AND APPLIED ACTIONS
# ---------------------------------------------------------------------------

print(f"Station z = {z:.3f} m")

print(
    f"A = {properties['A']:.6e} m², "
    f"Ix = {properties['Ix']:.6e} m⁴, "
    f"Iy = {properties['Iy']:.6e} m⁴, "
    f"Ixy = {properties['Ixy']:.6e} m⁴"
)

print(
    f"Actions: "
    f"N = {N:.6e} N, "
    f"Mx = {Mx:.6e} N·m, "
    f"My = {My:.6e} N·m, "
    f"Tx = {Tx:.6e} N, "
    f"Ty = {Ty:.6e} N"
)


# ---------------------------------------------------------------------------
# 7. PRINT POLYGON-WISE NAVIER RESULTS
# ---------------------------------------------------------------------------

print("\nNAVIER")

for row in navier_rows:
    # sigma_extreme is selected by absolute magnitude while preserving
    # the original sign and its coordinates.
    print(
        f"{row['idx']}:{row['name']}  "
        f"sigma_min = {row['sigma_min']:.6e} Pa  "
        f"sigma_max = {row['sigma_max']:.6e} Pa  "
        f"sigma_extreme = {row['sigma_extreme']:.6e} Pa  "
        f"at ({row['x']:.6e}, {row['y']:.6e})"
    )


# ---------------------------------------------------------------------------
# 8. PRINT POLYGON-WISE JOURAWSKI RESULTS
# ---------------------------------------------------------------------------

print("\nJOURAWSKI")

for row in shear_rows:
    # Select the signed governing value from the four shear extrema returned
    # for the polygon.
    candidates = [
        ("x", row["tau_x_min"], row["x_tau_x_min"], row["y_tau_x_min"]),
        ("x", row["tau_x_max"], row["x_tau_x_max"], row["y_tau_x_max"]),
        ("y", row["tau_y_min"], row["x_tau_y_min"], row["y_tau_y_min"]),
        ("y", row["tau_y_max"], row["x_tau_y_max"], row["y_tau_y_max"]),
    ]

    direction, tau_governing, x, y = max(
        candidates,
        key=lambda item: abs(item[1]),
    )

    print(
        f"{row['idx']}:{row['name']}  "
        f"tau_x_min = {row['tau_x_min']:.6e} Pa  "
        f"tau_x_max = {row['tau_x_max']:.6e} Pa  "
        f"tau_y_min = {row['tau_y_min']:.6e} Pa  "
        f"tau_y_max = {row['tau_y_max']:.6e} Pa"
    )

    print(
        f"  tau_governing = {tau_governing:.6e} Pa  "
        f"direction = {direction}  "
        f"at ({x:.6e}, {y:.6e})"
    )
```
