# csf_sp User Guide

**Bridge between CSF section models and sectionproperties**

---

## 1. What is csf_sp

`csf_sp` is a command-line tool that reads a **CSF YAML file**, samples the section geometry at one or more positions along the member axis, and computes **cross-sectional properties** using [sectionproperties](https://sectionproperties.readthedocs.io) as the calculation engine. No Python code is required - a YAML file and a single command are enough.

The tool handles arbitrary polygon nesting, multi-material sections (via weighted polygons), closed thin-walled cells (`@cell`), open thin-walled walls (`@wall`), and prismatic or tapered geometry.

---

## 2. The YAML File

A CSF YAML file describes the cross-section of a structural member using two reference sections, **S0** and **S1**, placed at two positions `z0` and `z1` along the member axis. CSF interpolates the geometry and material properties continuously between the two ends.

### 2.1 Basic structure

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        <polygon_name>:
          weight: 1.0
          vertices:
            - [x0, y0]
            - [x1, y1]
            - ...
    S1:
      z: 10.0
      polygons:
        <polygon_name>:
          weight: 1.0
          vertices:
            - [x0, y0]
            - ...
```

> **Prismatic section**: for a constant cross-section along the member, copy S0 into S1 with the desired z coordinate. CSF will treat the geometry as constant.

### 2.2 Polygons

Each polygon is defined by an ordered list of vertices in the section plane (x, y). Vertices should be listed in **counter-clockwise (CCW)** order to produce a positive area. The polygon is automatically closed - there is no need to repeat the first vertex.

**Polygon name**: a unique identifier within the section. The same name must appear in both S0 and S1 - this is how CSF pairs the corresponding polygons across the two reference sections.

**Volume pairing by order**: each polygon in S0 is geometrically paired with the polygon at the same position in S1. The first polygon in S0 is paired with the first polygon in S1, the second with the second, and so on. Each pair subtends a continuous volume along the member between the two reference sections. The global section geometry is the union of all these volumes.

**Name validation for weight laws**: polygon names are used to associate custom weight laws `w(z)`. If a name used in a weight law does not match a valid polygon pair in the model, the input is rejected immediately at load time.

### 2.3 Weight

`weight` is a scalar factor that scales the contribution of a polygon to the section properties. It can represent:

- a material ratio: `weight = E / E_ref` (dimensionless)
- an elastic modulus E directly (e.g. MPa), if used consistently
- any other physical quantity that scales with area

Common conventions:

| Value | Meaning |
|---|---|
| `1.0` | full solid material |
| `0.0` | void - if nested inside another polygon, removes that area from the parent |
| `> 1.0` | stiffer material (e.g. steel inside concrete) |
| `0 < w < 1` | degraded or partially contributing region |

> For a deeper treatment of how `weight` is used to homogenize the section and map material properties, see the [CSF Longitudinally-Varying Homogenization Guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSFLongitudinally-varying-homogenization-user-guide.md).

> **Nesting is automatic**: the containment relationship between polygons is detected from the geometry. You never need to declare which polygon is the parent - CSF infers it from the vertex coordinates.

### 2.4 Weight variation along z

The weight of each polygon can change from S0 to S1. CSF linearly interpolates the weight at any intermediate z. To keep the weight constant, use the same value in both sections.

For non-linear variation, a custom Python expression can be added under `weight_laws`:

```yaml
  weight_laws:
    - 'polygon_name_s0,polygon_name_s1: 1.0 - 0.3 * (z / L)'
```

> The two names in the law (`s0_name,s1_name`) identify the polygon in S0 and its counterpart in S1 respectively. They can be different - CSF matches them by name, not by position. Using the same name in both sections is a common convention but not a requirement.

### 2.5 Closed thin-walled cells (@cell)

A closed thin-walled cell is declared by appending `@cell` to the polygon name. The vertex list must contain both the **outer loop (CCW)** and the **inner loop (CW)**, separated by a repeated first vertex that marks the end of the outer loop.

```yaml
        box@cell:
          weight: 1.0
          vertices:
            # Outer loop (CCW)
            - [-0.10, -0.15]
            - [ 0.10, -0.15]
            - [ 0.10,  0.15]
            - [-0.10,  0.15]
            - [-0.10, -0.15]   # repeated first vertex: end of outer loop
            # Inner loop (CW)
            - [-0.08, -0.13]
            - [-0.08,  0.13]
            - [ 0.08,  0.13]
            - [ 0.08, -0.13]
            - [-0.08, -0.13]   # end of inner loop
```

> ⚠ The outer loop must be CCW (positive signed area) and the inner loop must be CW (negative signed area). CSF validates this at load time and raises an error if the orientations are inconsistent.

> **Alternative without @cell**: the slit encoding is not mandatory. The same hollow section can be described using two plain polygons - an outer solid (`weight = 1.0`) and an inner void (`weight = 0.0`) nested inside it. In that case no special suffix is needed. The difference is that `@cell` also activates the Bredt-Batho torsional constant; without it, `J_sv_cell` will be zero.

CSF computes the **Saint-Venant torsional constant** for `@cell` polygons using the Bredt-Batho formula:

```
J = 4 × Am² / (s / t)
```

where `Am` is the area enclosed by the median line, `s` is the median perimeter, and `t` is the wall thickness (estimated geometrically or declared via `@t=` in the name).

> For the full derivation and background of the Bredt-Batho formula used for `@cell` and the open thin-wall formula used for `@wall`, see the [Saint-Venant Torsional Constant reference](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md).

### 2.6 Open thin-walled walls (@wall)

An open thin-walled wall is declared by appending `@wall` to the polygon name. The polygon is a simple rectangle - no slit encoding, no repeated vertices. It is just a standard four-vertex polygon.

```yaml
        web@wall:
          weight: 1.0
          vertices:
            - [-0.02, -0.15]
            - [ 0.02, -0.15]
            - [ 0.02,  0.15]
            - [-0.02,  0.15]
```

CSF computes the Saint-Venant torsional contribution for each `@wall` polygon using the open thin-wall formula:

```
J_i = (1/3) × b × t³
```

where `b` is the wall length and `t` is the wall thickness. The total torsional constant is the sum over all `@wall` polygons.

**Declaring thickness explicitly**: by default CSF estimates `t` geometrically as `t_est = 2A / P`. For better accuracy, declare the thickness directly in the polygon name using `@t=`:

```yaml
        web@wall@t=0.02:
          weight: 1.0
          vertices:
            - [-0.01, -0.15]
            - [ 0.01, -0.15]
            - [ 0.01,  0.15]
            - [-0.01,  0.15]
```

> If `@t=` is specified only in S0 (not in S1), CSF treats that value as constant along the entire element length.

---

## 3. Running csf_sp

### 3.1 Single station

```bash
python -m csf.utils.csf_sp --yaml=my_section.yaml --z=15.0
```

### 3.2 With plot

```bash
python -m csf.utils.csf_sp --yaml=my_section.yaml --z=15.0 --plot
```

### 3.3 Multiple stations via run-config

Create a run-config YAML file:

```yaml
station_sets:
  my_stations: [0, 5, 10, 15, 20, 25, 30]
```

Then run:

```bash
python -m csf.utils.csf_sp --yaml=my_section.yaml \
  --run-config=stations.yaml --station-set=my_stations
```

### 3.4 Mesh size

The `--mesh` option controls the maximum element area for the sectionproperties mesh (default: 1.0, in the same length units as your YAML). Smaller values give more accurate results but take longer.

```bash
python -m csf.utils.csf_sp --yaml=my_section.yaml --z=15.0 --mesh=0.1
```

---

## 4. Output Properties

The sectionproperties output is printed to the terminal. The most relevant properties for structural use are:

| Property | Unit | Description |
|---|---|---|
| `e.a` | length² | Effective area (weight × area, summed over all polygons) |
| `cx`, `cy` | length | Centroid coordinates (weighted) |
| `e.ixx_c` | length⁴ | Second moment of area about centroidal X-axis |
| `e.iyy_c` | length⁴ | Second moment of area about centroidal Y-axis |
| `e.ixy_c` | length⁴ | Product of inertia about centroidal axes |
| `e.zxx+/-` | length³ | Elastic section modulus about X (top / bottom fibre) |
| `e.zyy+/-` | length³ | Elastic section modulus about Y (left / right fibre) |
| `rx`, `ry` | length | Radius of gyration |
| `e.j` | length⁴ | Saint-Venant torsional constant (FEM warping, connected sections only) |

> For a single-material section with all weights = 1, `e.a` equals the geometric net area.

> For the full list of output properties and the mapping between CSF property names and sectionproperties names, see the [Section Full Analysis reference](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/sectionfullanalysis.md).

---

## 5. Domain and Limits

### What csf_sp handles

- Arbitrary polygon nesting at any depth
- Polygons with positive, zero, or fractional weights
- Multi-material sections (each polygon carries its own weight)
- Prismatic sections (S0 = S1) and tapered sections (S0 ≠ S1)
- Weight variation along z (linear or custom law)
- Closed thin-walled cells (`@cell`) with automatic Bredt-Batho J
- Open thin-walled walls (`@wall`) with automatic open thin-wall J
- Disjoint regions (multiple disconnected polygons)

### Known limitations

- Warping analysis (`e.j`) is **skipped** when the section contains disjoint regions. A warning is printed. Use the CSF native `J_sv_cell` (Bredt-Batho) for closed cells in that case.
- Negative weights are accepted by CSF but may produce unexpected results in the sectionproperties material mapping.
- The mesh size affects accuracy. For thin-walled sections, a fine mesh is recommended.

---

## 6. Examples

### Example 1 - Solid rectangle (prismatic)

A 0.4 × 0.6 m rectangle, constant along a 10 m member.

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            - [-0.20, -0.30]
            - [ 0.20, -0.30]
            - [ 0.20,  0.30]
            - [-0.20,  0.30]
    S1:
      z: 10.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            - [-0.20, -0.30]
            - [ 0.20, -0.30]
            - [ 0.20,  0.30]
            - [-0.20,  0.30]
```

```bash
python -m csf.utils.csf_sp --yaml=rect.yaml --z=5.0 --plot
```

Expected: `e.a = 0.24`, `cx = cy = 0`, `e.ixx_c = 0.00720`, `e.iyy_c = 0.00320`

---

### Example 2 - Hollow box (closed cell)

A 0.20 × 0.30 m box with wall thickness 0.02 m, prismatic over 10 m.

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        box@cell:
          weight: 1.0
          vertices:
            - [-0.10, -0.15]
            - [ 0.10, -0.15]
            - [ 0.10,  0.15]
            - [-0.10,  0.15]
            - [-0.10, -0.15]
            - [-0.08, -0.13]
            - [-0.08,  0.13]
            - [ 0.08,  0.13]
            - [ 0.08, -0.13]
            - [-0.08, -0.13]
    S1:
      z: 10.0
      polygons:
        box@cell:
          weight: 1.0
          vertices:
            - [-0.10, -0.15]
            - [ 0.10, -0.15]
            - [ 0.10,  0.15]
            - [-0.10,  0.15]
            - [-0.10, -0.15]
            - [-0.08, -0.13]
            - [-0.08,  0.13]
            - [ 0.08,  0.13]
            - [ 0.08, -0.13]
            - [-0.08, -0.13]
```

Expected: `e.a = 0.0184`, `J_sv_cell ≈ 0.000224 m⁴` (Bredt-Batho), `e.j ≈ 0.000232 m⁴` (FEM)

---

### Example 3 - I-section (open thin-walled walls)

A simplified I-section with web and two flanges, each declared as `@wall`. Wall thickness is declared explicitly via `@t=`.

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        web@wall@t=0.02:
          weight: 1.0
          vertices:
            - [-0.01, -0.15]
            - [ 0.01, -0.15]
            - [ 0.01,  0.15]
            - [-0.01,  0.15]
        top_flange@wall@t=0.02:
          weight: 1.0
          vertices:
            - [-0.10,  0.15]
            - [ 0.10,  0.15]
            - [ 0.10,  0.17]
            - [-0.10,  0.17]
        bot_flange@wall@t=0.02:
          weight: 1.0
          vertices:
            - [-0.10, -0.17]
            - [ 0.10, -0.17]
            - [ 0.10, -0.15]
            - [-0.10, -0.15]
    S1:
      z: 10.0
      polygons:
        web@wall@t=0.02:
          weight: 1.0
          vertices:
            - [-0.01, -0.15]
            - [ 0.01, -0.15]
            - [ 0.01,  0.15]
            - [-0.01,  0.15]
        top_flange@wall@t=0.02:
          weight: 1.0
          vertices:
            - [-0.10,  0.15]
            - [ 0.10,  0.15]
            - [ 0.10,  0.17]
            - [-0.10,  0.17]
        bot_flange@wall@t=0.02:
          weight: 1.0
          vertices:
            - [-0.10, -0.17]
            - [ 0.10, -0.17]
            - [ 0.10, -0.15]
            - [-0.10, -0.15]
```

> The three polygons are declared as `@wall` so CSF applies the open thin-wall torsion formula to each. The total `J_sv_wall = Σ (1/3) × b × t³`.

---

### Example 4 - Composite section (concrete + steel bar)

A 0.40 × 0.60 m concrete section (E = 30 000 MPa) with an embedded steel bar (E = 210 000 MPa). Weights are absolute elastic moduli.

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        concrete:
          weight: 30000
          vertices:
            - [-0.20, -0.30]
            - [ 0.20, -0.30]
            - [ 0.20,  0.30]
            - [-0.20,  0.30]
        steel:
          weight: 210000
          vertices:
            - [-0.04, -0.04]
            - [ 0.04, -0.04]
            - [ 0.04,  0.04]
            - [-0.04,  0.04]
    S1:
      z: 10.0
      polygons:
        concrete:
          weight: 30000
          vertices:
            - [-0.20, -0.30]
            - [ 0.20, -0.30]
            - [ 0.20,  0.30]
            - [-0.20,  0.30]
        steel:
          weight: 210000
          vertices:
            - [-0.04, -0.04]
            - [ 0.04, -0.04]
            - [ 0.04,  0.04]
            - [-0.04,  0.04]
```

> The steel polygon is nested inside concrete. CSF automatically computes the effective contribution as `w_eff = 210 000 − 30 000 = 180 000 MPa`. You do not need to subtract the concrete area manually.

Expected: `e.a = 30 000 × 0.24 + 180 000 × 0.0064 = 9 504` (units: MPa × m²)

---

*csf_sp - part of the [continuous-section-field (csfpy)](https://github.com/giovanniboscu/continuous-section-field) package | GPL-3.0*
