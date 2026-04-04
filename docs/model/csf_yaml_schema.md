# CSF YAML Schema - Formal Specification

**Version:** 1.0 (proposal)
**Repository:** [giovanniboscu/continuous-section-field](https://github.com/giovanniboscu/continuous-section-field)

---

## Overview

A CSF YAML file describes a **Continuous Section Field** - a ruled solid defined
by two polygonal end sections and a set of weight laws that modulate the stiffness
contribution of each polygon along the member axis.

The file is both human-readable and machine-parseable. It contains:

- the complete geometry of the two end sections
- the structural type and weight of each polygon
- optional weight laws as Python expressions
- optional metadata

---

## Design principles

**Separation of geometry and physics.** The polygon geometry (vertices) describes
shape only. The structural role is carried by two independent fields:

- `weight` - stiffness ratio relative to the reference material
- `type` - structural classification of the polygon

**No internal tags in names.** Polygon names are free descriptive identifiers.
Internal implementation tags such as `@cell` or `@wall` do not belong in the
name field and carry no semantic meaning in the schema.

**Self-contained.** A CSF file contains everything needed to reconstruct the
section field - geometry, weights, and laws - without external references
other than optional lookup data files.

---

## Top-level structure

```yaml
CSF:
  metadata:     # optional
  sections:
    S0:         # required — base section
    S1:         # required — head section
  weight_laws:  # optional — list of law expressions
```

---

## 1. metadata (optional)

Descriptive information about the model. Not used in computation.

```yaml
CSF:
  metadata:
    name: "RC Bridge Pier"
    description: "Hollow rectangular pier, tapered, H=70m"
    author: "Giovanni Boscu"
    date: "2026-04-04"
    version: "1.0"
    reference_material: "C35/45 concrete"
    reference_E: 34000.0
    units:
      length: "m"
      force:  "N"
    tags:
      - bridge
      - RC
      - hollow-section
```

| Field | Type | Description |
|---|---|---|
| `name` | string | Short identifier |
| `description` | string | Free text |
| `author` | string | Creator |
| `date` | string | ISO 8601 date |
| `reference_material` | string | Human-readable label for the w = 1 material |
| `reference_E` | float | Stiffness of reference material [force/length²] |
| `units.length` | string | Length unit assumed throughout the file |
| `units.force` | string | Force unit assumed throughout the file |
| `tags` | list[string] | Searchable keywords |

> **Note on reference_E:** All section properties computed by CSF are homogenized
> with respect to the reference material. To recover physical stiffness in a solver:
> `EA = reference_E × A_CSF` and `EI = reference_E × Ix_CSF`.

---

## 2. sections (required)

Exactly two sections must be defined: `S0` at the base (z = z0) and `S1` at the
head (z = z1), with `z1 > z0`.

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        <name>:
          type: <polygon_type>
          vertices:
            - [x0, y0]
            - [x1, y1]
            - ...
          weight: <float>
    S1:
      z: 70.0
      polygons:
        <name>:
          type: <polygon_type>
          vertices:
            - [x0, y0]
            - ...
          weight: <float>
```

### 2.1 Section fields

| Field | Type | Required | Description |
|---|---|---|---|
| `z` | float | yes | Absolute elevation [length unit] |
| `polygons` | map | yes | Named polygon definitions |

### 2.2 Polygon fields

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | yes | Structural classification (see table below) |
| `vertices` | list[[float,float]] | yes | Ordered vertex list [x, y] |
| `weight` | float | yes | Stiffness ratio w = E_material / E_reference |

### 2.3 Polygon types

The `type` field carries the structural meaning of the polygon. It is independent
of the polygon name.

| type | Winding | weight | Description |
|---|---|---|---|
| `shell` | CCW | > 0 | Solid section — full wall without void |
| `hollow_cell` | CCW outer + CW inner (bridged) | > 0 | Hollow closed section encoded as a single polygon. Enables Bredt–Batho torsion formula (J_sv_cell). |
| `outer` | CCW | > 0 | Outer contour of a hollow section (paired with `inner_void`) |
| `inner_void` | CW | 0.0 | Inner void of a hollow section (paired with `outer`) |
| `bar` | CCW | > 0 | Reinforcement bar or similar inclusion |

> **hollow_cell vs outer + inner_void:**
> Use `hollow_cell` when the Bredt–Batho closed-cell torsion formula is required
> (structurally correct for thin-walled closed sections).
> Use `outer` + `inner_void` when a separate void polygon is preferred for
> visualization or when the section is open.

### 2.4 Polygon naming

Names are free descriptive strings. Recommended conventions:

| Example name | Meaning |
|---|---|
| `shell` | Single solid shell component |
| `shell_outer`, `shell_inner` | Hollow section, separate polygons |
| `rebar_row1_1` … `rebar_row1_N` | Bars of outer reinforcement row |
| `rebar_row2_1` … `rebar_row2_N` | Bars of inner reinforcement row |

Polygon names must be unique on its own section S0 and S1.

### 2.5 Vertex winding convention

- **Material polygons** (`shell`, `outer`, `bar`, `hollow_cell` outer loop): **counter-clockwise (CCW)**
- **Void polygons** (`inner_void`, `hollow_cell` inner loop): **clockwise (CW)**

Vertices form a closed loop - the last vertex connects back to the first.
A minimum of 3 vertices is required.

### 2.6 Weight reference values

| Material | Typical E [MPa] | weight (vs C35/45) | weight (vs S355) |
|---|---|---|---|
| Concrete C30/37 | 33 000 | 0.971 | — |
| Concrete C35/45 | 34 000 | 1.000 | — |
| Concrete C40/50 | 35 000 | 1.029 | — |
| Steel rebar B450C | 200 000 | 5.882 | — |
| Steel shell S355 | 210 000 | — | 1.000 |
| Void | — | 0.000 | 0.000 |
| Degraded material | variable | 0.0–1.0 | 0.0–1.0 |

---

## 3. weight_laws (optional)

A list of strings, each assigning a weight law to one polygon pair.

```yaml
CSF:
  weight_laws:
    - 'shell,shell: 1.0 - 0.10*(z/L)'
    - 'rebar_row1_1,rebar_row1_1: T_lookup(''bar_weight.txt'')*w0'
    - 'rebar_row1_2,rebar_row1_2: T_lookup(''bar_weight.txt'')*w0'
```

### 3.1 Law string format

```
'<s0_polygon_name>,<s1_polygon_name>: <expression>'
```

The polygon pair identifies which ruled solid the law applies to.
The expression is a Python expression evaluated at each integration point along z.

### 3.2 Variables available in expressions

| Variable | Type | Description |
|---|---|---|
| `z` | float | Physical coordinate [length] — from z0 to z1 |
| `t` | float | Normalized coordinate — t = (z − z0) / (z1 − z0) ∈ [0, 1] |
| `L` | float | Total member length = z1 − z0 |
| `w0` | float | Polygon weight at S0 |
| `w1` | float | Polygon weight at S1 |
| `np` | module | NumPy namespace (np.exp, np.maximum, np.sin, ...) |

### 3.3 Lookup functions

| Function | Coordinate | Description |
|---|---|---|
| `E_lookup('file.txt')` | z [physical] | Linear interpolation vs absolute z coordinate |
| `T_lookup('file.txt')` | t [0, 1] | Linear interpolation vs normalized t coordinate |

**Lookup file format** — two columns, space or tab separated:

```
# coordinate    w_factor
# lines starting with # are ignored
0.000000        1.000
0.628571        1.000
0.657143        0.660
1.000000        0.660
```

> **T_lookup vs E_lookup:** Prefer `T_lookup` when the law should be independent
> of the member length. If `z1` changes, `T_lookup` files do not need to be updated.

### 3.4 Expression examples

```python
# No variation (constant weight)
"1.0"

# Linear reduction: 10% from base to head
"1.0 - 0.10*(z/L)"

# Gaussian dip centred at 1/3 of height (e.g. segment joint)
"np.maximum(0.84, 1.0 - 0.10*np.exp(-((z-0.33*L)**2)/(2*(0.03*L)**2)))"

# Two Gaussian dips near segment joints (HISTWIN-type steel tower)
"np.maximum(0.84, 1.0 - 0.10*np.exp(-((z-0.286*L)**2)/(2*(0.03*L)**2)) - 0.14*np.exp(-((z-0.636*L)**2)/(2*(0.03*L)**2)))"

# Data-driven rebar curtailment (normalized coordinate)
"T_lookup('bar_weight.txt') * w0"

# Data-driven degradation from inspection data (physical coordinate)
"E_lookup('inspection_data.txt') * w0"

# Smooth sigmoidal step change (e.g. bar diameter change at z=44m in L=70m)
"w0 * (0.66 + 0.34 / (1.0 + np.exp(-20.0*(z/L - 0.629))))"
```

---

## 4. Complete examples

### 4.1 Steel wind tower (circular hollow, with degradation law)

```yaml
CSF:
  metadata:
    name: "HISTWIN-type steel tower"
    reference_material: "Steel S355"
    reference_E: 210000.0
    units:
      length: "m"

  sections:
    S0:
      z: 0.0
      polygons:
        shell:
          type: hollow_cell
          vertices:
            - [2.15, 0.0]
            - ...            # 128 vertices for circular approximation
          weight: 1.0
    S1:
      z: 76.15
      polygons:
        shell:
          type: hollow_cell
          vertices:
            - [1.50, 0.0]
            - ...
          weight: 1.0

  weight_laws:
    - >
      shell,shell: np.maximum(0.84,
        1.0
        - 0.10*np.exp(-((z-0.286*L)**2)/(2*(0.03*L)**2))
        - 0.14*np.exp(-((z-0.636*L)**2)/(2*(0.03*L)**2)))
```

### 4.2 RC bridge pier (hollow rectangular, with rebar curtailment)

```yaml
CSF:
  metadata:
    name: "RC Bridge Pier"
    reference_material: "C35/45 concrete, Ecm=34000 MPa"
    reference_E: 34000.0
    units:
      length: "m"

  sections:
    S0:
      z: 0.0
      polygons:
        shell:
          type: hollow_cell
          vertices:
            - [3.0, 1.75]
            - ...            # 120 vertices, rounded rectangle 6x3.5m t=0.5m
          weight: 1.0
        rebar_row1_1:
          type: bar
          vertices:
            - [2.84, 1.59]
            - ...            # 4-vertex square approximation of phi32 bar
          weight: 5.88
        # ... rebar_row1_2 to rebar_row1_120
    S1:
      z: 70.0
      polygons:
        shell:
          type: hollow_cell
          vertices:
            - [2.5, 1.25]
            - ...            # 120 vertices, rounded rectangle 5x2.5m t=0.4m
          weight: 1.0
        rebar_row1_1:
          type: bar
          vertices:
            - [2.34, 1.09]
            - ...
          weight: 5.88
        # ...

  weight_laws:
    - 'shell,shell: 1.0 - 0.10*(z/L)'
    - 'rebar_row1_1,rebar_row1_1: T_lookup(''bar_weight.txt'')*w0'
    # ... one entry per bar
```

---

## 5. Validation rules

A valid CSF file must satisfy all of the following:

| Rule | Description |
|---|---|
| `S1.z > S0.z` | Head elevation must be strictly greater than base elevation |
| Polygon names match | Every polygon in S0 must have a counterpart with the same name in S1 |
| `weight >= 0` | Negative weights are not physically defined |
| `weight == 0` implies void | A zero-weight polygon contributes nothing to section properties |
| At least 3 vertices | Degenerate polygons (1 or 2 vertices) are invalid |
| Vertices are finite | NaN and Inf coordinates are invalid |
| `hollow_cell` is unique per section | At most one hollow_cell polygon per section (current implementation) |

---

## 6. Homogenization - critical note for solver integration

All CSF section properties (A, Ix, Iy, J, ...) are **homogenized** with respect
to the reference material:

```
A_eff  = ∫ w(z) dA
Ix_eff = ∫ w(z) · y² dA
```

When feeding CSF output to a structural solver, apply the reference stiffness
consistently:

```
EA  = reference_E × A_CSF
EIx = reference_E × Ix_CSF
GJ  = G_reference × J_CSF
```

Do not add material contributions separately in the solver - they are already
encoded in the weight field.

---

## 7. Extension points (reserved for future versions)

The following fields are reserved and not currently parsed:

```yaml
polygons:
  shell:
    type: hollow_cell
    vertices: [...]
    weight: 1.0
    material:           # future: named material block
      name: "C35/45"
      E: 34000.0
      nu: 0.20
    thickness: 0.50     # future: nominal wall thickness for thin-wall checks

integration:            # future: quadrature settings
  n_points: 20
  method: "gauss-legendre"

coordinate_system:      # future: local axis orientation
  angle_deg: 0.0
```

---

*CSF YAML Schema v1.0 - proposal*
*giovanniboscu/continuous-section-field*
*April 2026*
