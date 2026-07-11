# Introduction to the CSF Stress APIs

CSF provides two polygon-wise stress-analysis functions for evaluating a section at a specified longitudinal station `z`:

- `analyse_polygon_navier_stress`
- `analyse_polygon_jourawski_shear_stress`

The functions operate directly on a `section_field` and return one result row for each polygon of the evaluated section.

They are intended for section-level stress evaluation. The user supplies the internal actions acting at the selected station.

---

# Navier normal stress

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

# CSF Stress APIs

This document shows the basic use of the CSF stress APIs.

The two APIs covered are:

- Navier normal stress
- Jourawski shear stress

---

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
