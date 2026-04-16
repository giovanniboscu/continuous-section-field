# == DRAFT ==
# csf_sp User Guide

**Bridge between CSF section models and sectionproperties**

---

## 1. What is csf_sp

`csf_sp` bridges [CSF](https://github.com/giovanniboscu/continuous-section-field) and [sectionproperties](https://sectionproperties.readthedocs.io):
You describe your cross-section once in a YAML file and get the full sectionproperties result set. Use it as a standalone tool with no Python code required, or import it directly as a Python library in your own pipeline.

**The key advantage over using sectionproperties directly**: CSF interpolates geometry
and material properties *continuously* along the member axis. A single YAML file
describes a tapered or composite member completely; csf_sp samples it at whatever
stations you need, giving you `A(z)`, `EI(z)`, `J(z)` as a continuous field rather
than a set of disconnected cross-sections.

### Quick start

Write a YAML file, run one command:

```yaml
# box.yaml  - hollow rectangular box, prismatic over 10 m
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [-0.10, -0.15]
            - [ 0.10, -0.15]
            - [ 0.10,  0.15]
            - [-0.10,  0.15]
        inner:
          weight: 0.0
          vertices:
            - [-0.08, -0.13]
            - [ 0.08, -0.13]
            - [ 0.08,  0.13]
            - [-0.08,  0.13]
    S1:
      z: 10.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [-0.10, -0.15]
            - [ 0.10, -0.15]
            - [ 0.10,  0.15]
            - [-0.10,  0.15]
        inner:
          weight: 0.0
          vertices:
            - [-0.08, -0.13]
            - [ 0.08, -0.13]
            - [ 0.08,  0.13]
            - [-0.08,  0.13]
```

```bash
python -m csf.utils.csf_sp --yaml=box.yaml --z=5.0 --plot
```

> A void (hole) is simply a polygon with `weight = 0.0` nested inside a solid one.
> In the example above, `inner` is the hollow core - CSF detects automatically that
> it is inside `outer` and subtracts it. For the solid, `weight = 1.0` or the elastic
> modulus directly (e.g. `weight = 210000` for steel in MPa). [weight details](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSFLongitudinally-varying-homogenization-user-guide.md)

That is all. csf_sp reads the YAML, samples the section at z = 5.0, meshes it,
runs the sectionproperties FEM analysis, and prints the full result table including
`e.j` (Saint-Venant torsional constant via warping FEM).

For programmatic access - useful when you need `J(z)` over many stations - two
public API functions are available:

```python
from csf.utils.csf_sp import load_yaml, analyse

field = load_yaml("box.yaml")
sec   = analyse(field, z=5.0)   # returns a sectionproperties Section object

print(sec.get_ej())              # J FEM warping  →  2.324106e-04
print(sec.get_eic())             # (Ixx_c, Iyy_c, Ixy_c)
```

The returned object is a native `sectionproperties.analysis.Section` - the complete
SP API is available for any further post-processing.

---

## 2. The YAML File

A CSF YAML file describes the cross-section of a structural member using two reference
sections, **S0** and **S1**, placed at two positions along the member axis. CSF
interpolates geometry and material properties continuously between the two ends.

### 2.1 Polygons

Each section is made of one or more **polygons**. A polygon is a closed region defined
by an ordered list of vertices in the section plane (x, y). Vertices must be listed in
**counter-clockwise (CCW)** order to produce a positive area. The polygon is closed automatically - no need to
repeat the first vertex.

> If vertices are listed clockwise the area will be negative and results will be
> incorrect. For full details on polygon construction see the
> [CSF Fundamentals](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSF_Fundamentals.md).

Each polygon has a **name** and a **weight**. It is not required to use the same in S0 and S1, CSF  pairs the two ends of each component by its order.
The weight controls how much the
polygon contributes to the section properties (see section 2.4).

**Nesting is automatic**: if one polygon is geometrically inside another, CSF detects the containment from the vertex coordinates. No explicit declaration is needed. Note that weight: 0.0 must still be set explicitly on the inner polygon -containment is detected from geometry, but the physical contribution is always a user decision

### 2.2 Tapered section

When S0 and S1 have different vertices, CSF interpolates the geometry continuously.
This example shows a hollow rectangular tower that tapers from 0.20 × 0.30 m at the
base to 0.12 × 0.20 m at the top:

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [-0.10, -0.15]
            - [ 0.10, -0.15]
            - [ 0.10,  0.15]
            - [-0.10,  0.15]
        inner:
          weight: 0.0
          vertices:
            - [-0.08, -0.13]
            - [ 0.08, -0.13]
            - [ 0.08,  0.13]
            - [-0.08,  0.13]
    S1:
      z: 30.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [-0.06, -0.10]
            - [ 0.06, -0.10]
            - [ 0.06,  0.10]
            - [-0.06,  0.10]
        inner:
          weight: 0.0
          vertices:
            - [-0.04, -0.08]
            - [ 0.04, -0.08]
            - [ 0.04,  0.08]
            - [-0.04,  0.08]
```

```bash
python -m csf.utils.csf_sp --yaml=tapered.yaml --z=15.0
```

At z = 15.0 (mid-height) the section is interpolated - outer dimensions are 0.16 × 0.25 m,
halfway between the two ends.

> **Prismatic section**: for a constant cross-section along the member, copy S0 into S1
> with the desired z coordinate. CSF will treat the geometry as constant.

### 2.3 Multi-material section

Each polygon can carry a different `weight` representing its material stiffness. The
simplest convention is dimensionless (ratio relative to a reference material), but
absolute elastic moduli work equally well as long as the convention is consistent.

A concrete section with an embedded steel bar - weights are absolute elastic moduli
in MPa:

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

The steel polygon is nested inside concrete. CSF automatically computes the effective
contribution as `w_eff = 210 000 − 30 000 = 180 000 MPa`. You do not need to subtract
the concrete area manually.

Expected: `e.a = 30 000 × 0.24 + 180 000 × 0.0064 = 9 504` (MPa × m²)

Common weight conventions:

| Value | Meaning |
|---|---|
| `1.0` | full solid material |
| `0.0` | void - if nested inside another polygon, removes that area from the parent |
| `> 1.0` | stiffer material (e.g. steel inside concrete) |
| `0 < w < 1` | degraded or partially contributing region |

> For a deeper treatment of how `weight` is used to homogenize the section and map
> material properties, see the [CSF Longitudinally-Varying Homogenization Guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSFLongitudinally-varying-homogenization-user-guide.md).

### 2.4 Weight variation along z

Weight can vary from S0 to S1 - CSF linearly interpolates at any intermediate z.
This example models a degraded zone where stiffness drops from 100% at the base
to 70% at the top:

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        section:
          weight: 1.0
          vertices:
            - [-0.20, -0.30]
            - [ 0.20, -0.30]
            - [ 0.20,  0.30]
            - [-0.20,  0.30]
    S1:
      z: 30.0
      polygons:
        section:
          weight: 0.7
          vertices:
            - [-0.20, -0.30]
            - [ 0.20, -0.30]
            - [ 0.20,  0.30]
            - [-0.20,  0.30]
```

At z = 15.0 the weight is interpolated to 0.85 - `e.a` will be `0.85 × 0.24 = 0.204`.

### 2.5 Custom weight law

For non-linear variation, add a `weight_laws` block with a Python expression.
This example applies a parabolic stiffness reduction - full section at both ends,
72% at mid-span:

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        section:
          weight: 1.0
          vertices:
            - [-0.20, -0.30]
            - [ 0.20, -0.30]
            - [ 0.20,  0.30]
            - [-0.20,  0.30]
    S1:
      z: 30.0
      polygons:
        section:
          weight: 1.0
          vertices:
            - [-0.20, -0.30]
            - [ 0.20, -0.30]
            - [ 0.20,  0.30]
            - [-0.20,  0.30]
  weight_laws:
    - 'section,section: 1.0 - 0.28 * (1 - (z / L)**2)'
```

The two names in the law (`s0_name,s1_name`) identify the polygon in S0 and S1. Using the same name
in both sections is a common convention but not a requirement. If a name used in a
weight law does not match a valid polygon pair, the input is rejected at load time.

For the full syntax and available variables (`z`, `t`, `w0`, `w1`, `L`, `np`,
lookup tables), see the [CSF details](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSFLongitudinally-varying-homogenization-user-guide.md).

### 2.6 Fast analytical torsional constant (optional)

csf_sp always computes `e.j` via sectionproperties warping FEM - this is the rigorous
value and works for any section shape.

If you need a **faster analytical torsional constant** along many stations without
running the FEM mesh each time, CSF provides two native alternatives activated by
classification suffixes in the polygon name:

- `@cell` - closed thin-walled cell → Bredt-Batho `J_sv_cell`
- `@wall` - open thin-walled wall → open thin-wall formula `J_sv_wall`

These are CSF-level features that bypass sectionproperties entirely and are
significantly faster for thin-walled sections. For full details see the
[CSF documentation](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSF_Fundamentals.md).

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

The `--mesh` option controls the maximum element area for the sectionproperties mesh
(default: 1.0, in the same length units as your YAML). Smaller values give more
accurate results but take longer.

```bash
python -m csf.utils.csf_sp --yaml=my_section.yaml --z=15.0 --mesh=0.1
```

---

## 4. Output Properties

The sectionproperties output is printed to the terminal. The most relevant properties
for structural use are:

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

> For the full list of output properties and the mapping between CSF property names and
> sectionproperties names, see the [Section Full Analysis reference](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/sectionfullanalysis.md).

---

## 5. Domain and Limits

### What csf_sp handles

- Arbitrary polygon nesting at any depth
- Polygons with positive, zero, or fractional weights
- Multi-material sections (each polygon carries its own weight)
- Prismatic sections (S0 = S1) and tapered sections (S0 ≠ S1)
- Weight variation along z (linear or custom law)
- Disjoint regions (multiple disconnected polygons)

### Known limitations

- Warping analysis (`e.j`) is **skipped** when the section contains disjoint regions. A warning is printed.
- Negative weights are accepted by CSF but may produce unexpected results in the sectionproperties material mapping.
- The mesh size affects accuracy. For thin-walled sections, a fine mesh is recommended.
-  `csf_sp` is currently limited to CSF geometries defined by two end sections, `S0` and `S1`.
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

### Example 2 - Hollow box (prismatic)

A 0.20 × 0.30 m hollow box with wall thickness 0.02 m, prismatic over 10 m.
The inner void is declared as a nested polygon with `weight = 0.0`.

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [-0.10, -0.15]
            - [ 0.10, -0.15]
            - [ 0.10,  0.15]
            - [-0.10,  0.15]
        inner:
          weight: 0.0
          vertices:
            - [-0.08, -0.13]
            - [ 0.08, -0.13]
            - [ 0.08,  0.13]
            - [-0.08,  0.13]
    S1:
      z: 10.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [-0.10, -0.15]
            - [ 0.10, -0.15]
            - [ 0.10,  0.15]
            - [-0.10,  0.15]
        inner:
          weight: 0.0
          vertices:
            - [-0.08, -0.13]
            - [ 0.08, -0.13]
            - [ 0.08,  0.13]
            - [-0.08,  0.13]
```

Expected: `e.a = 0.0184`, `e.j ≈ 0.000232 m⁴` (FEM warping)

---

### Example 3 - Tapered hollow tower

A hollow rectangular tower tapering from 0.20 × 0.30 m at the base to 0.12 × 0.20 m
at the top over 30 m. The section properties vary continuously along z.

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [-0.10, -0.15]
            - [ 0.10, -0.15]
            - [ 0.10,  0.15]
            - [-0.10,  0.15]
        inner:
          weight: 0.0
          vertices:
            - [-0.08, -0.13]
            - [ 0.08, -0.13]
            - [ 0.08,  0.13]
            - [-0.08,  0.13]
    S1:
      z: 30.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [-0.06, -0.10]
            - [ 0.06, -0.10]
            - [ 0.06,  0.10]
            - [-0.06,  0.10]
        inner:
          weight: 0.0
          vertices:
            - [-0.04, -0.08]
            - [ 0.04, -0.08]
            - [ 0.04,  0.08]
            - [-0.04,  0.08]
```

```bash
python -m csf.utils.csf_sp --yaml=tapered.yaml \
  --run-config=stations.yaml --station-set=all
```

---

### Example 4 - Composite section (concrete + steel bar)

A 0.40 × 0.60 m concrete section (E = 30 000 MPa) with an embedded steel bar
(E = 210 000 MPa). Weights are absolute elastic moduli.

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

> The steel polygon is nested inside concrete. CSF automatically computes the effective
> contribution as `w_eff = 210 000 − 30 000 = 180 000 MPa`. You do not need to subtract
> the concrete area manually.

Expected: `e.a = 30 000 × 0.24 + 180 000 × 0.0064 = 9 504` (units: MPa × m²)

---

## 7. Multiple Stations

### 7.1 Via CLI run-config

To analyse several positions along the member in one command, create a small
run-config YAML file that lists the stations:

```yaml
# run_config.yaml
station_sets:
  my_stations: [0.0, 2.5, 5.0, 7.5, 10.0]
```

Then pass it to csf_sp together with the CSF model:

```bash
python -m csf.utils.csf_sp --yaml=csf_sp_example.yaml \
  --run-config=run_config.yaml --station-set=my_stations
```

csf_sp will print the full sectionproperties table for each station, separated by
a horizontal rule.

### 7.2 Via Python API

The same station list can be iterated programmatically:

```python
from csf.utils.csf_sp import load_yaml, analyse

field = load_yaml("csf_sp_example.yaml")

stations = [0.0, 2.5, 5.0, 7.5, 10.0]

for z in stations:
    sec = analyse(field, z=z)
    ej  = sec.get_ej()
    eic = sec.get_eic()
    print(f"z={z:5.1f}  e.j={ej:.4e}  e.ixx_c={eic[0]:.4e}  e.iyy_c={eic[1]:.4e}")
```

---

## 8. Legacy CSV Input

csf_sp can also read the geometry export block produced by the CSF
`section_selected_analysis` action, without reloading the original YAML model.

### 8.1 CSV format

```
## GEOMETRY EXPORT ##
# z=0.0
idx_polygon,idx_container,s0_name,s1_name,w,vertex_i,x,y
0,,outer,outer,1.0,0,-0.10,-0.15
0,,outer,outer,1.0,1, 0.10,-0.15
...
1,0,inner,inner,0.0,0,-0.08,-0.13
...
```

### 8.2 CLI usage

```bash
python -m csf.utils.csf_sp out/section_analysis.csv
```

To select a specific z station when the file contains multiple blocks:

```bash
python -m csf.utils.csf_sp out/section_analysis.csv --z=5.0
```

---

## 9. Python API

csf_sp exposes two public functions for programmatic use.
Everything else in the module is private implementation detail.

### 9.1 `load_yaml(path)`

Loads a CSF YAML file and returns the `ContinuousSectionField` object.

```python
from csf.utils.csf_sp import load_yaml

field = load_yaml("csf_sp_example.yaml")
```

The field object can also be constructed directly via the CSF Python API without
a YAML file:

```python
from csf import ContinuousSectionField, Section, Polygon, Pt
from csf.utils.csf_sp import analyse

outer = Polygon(vertices=(Pt(-0.10,-0.15), Pt(0.10,-0.15),
                           Pt(0.10,0.15),  Pt(-0.10,0.15)), weight=1.0, name="outer")
inner = Polygon(vertices=(Pt(-0.08,-0.13), Pt(0.08,-0.13),
                           Pt(0.08,0.13),  Pt(-0.08,0.13)), weight=0.0, name="inner")
s0 = Section(polygons=(outer, inner), z=0.0)
s1 = Section(polygons=(outer, inner), z=10.0)
field = ContinuousSectionField(section0=s0, section1=s1)
```

### 9.2 `analyse(field, z, mesh=1.0)`

Samples the CSF field at `z`, builds and meshes the sectionproperties geometry,
and returns a fully analysed `sectionproperties.analysis.Section` object.

```python
from csf.utils.csf_sp import load_yaml, analyse

field = load_yaml("csf_sp_example.yaml")
sec   = analyse(field, z=0.0, mesh=1.0)
```

**Important**: csf_sp always assigns `Material` objects to regions so that weighted
(homogenized) properties are computed correctly. This means SP treats every section
as composite. Always use the modulus-weighted getters even when all polygon weights
equal 1.0:

| Use | Instead of |
|---|---|
| `sec.get_ea()` | `sec.get_area()` |
| `sec.get_eic()` | `sec.get_ic()` |
| `sec.get_ej()` | `sec.get_j()` |
| `sec.get_eip()` | `sec.get_ip()` |
| `sec.get_ez()` | `sec.get_z()` |
| `sec.get_rc()` | - |

### 9.3 Full example

**`csf_sp_example.yaml`** - hollow rectangular box, prismatic over 10 m:

```yaml
# csf_sp_example.yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [-0.10, -0.15]
            - [ 0.10, -0.15]
            - [ 0.10,  0.15]
            - [-0.10,  0.15]
        inner:
          weight: 0.0
          vertices:
            - [-0.08, -0.13]
            - [ 0.08, -0.13]
            - [ 0.08,  0.13]
            - [-0.08,  0.13]
    S1:
      z: 10.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [-0.10, -0.15]
            - [ 0.10, -0.15]
            - [ 0.10,  0.15]
            - [-0.10,  0.15]
        inner:
          weight: 0.0
          vertices:
            - [-0.08, -0.13]
            - [ 0.08, -0.13]
            - [ 0.08,  0.13]
            - [-0.08,  0.13]
```

**`csf_sp_example.py`** - analyses all stations and prints full SP output + individual getters:

```python
"""
csf_sp public API - full sectionproperties output verification

Expected output matches CLI:
    python3 -m csf.utils.csf_sp --yaml=csf_sp_example.yaml \
        --run-config=run_config.yaml --station-set=all
"""

from csf.utils.csf_sp import load_yaml, analyse

# 1. Load the CSF field from YAML
field = load_yaml("csf_sp_example.yaml")

# 2. Station list - matches run_config.yaml station_set 'all'
stations = [0.0, 2.5, 5.0, 7.5, 10.0]

for z in stations:

    print("\n" + "=" * 60)
    print(f"z = {z}")
    print("=" * 60)

    # 3. Sample and analyse
    sec = analyse(field, z=z, mesh=1.0)

    # 4. Full display - matches CLI output exactly
    #
    # Note: csf_sp always assigns Material objects to SP regions so
    # that weighted (homogenized) properties are computed correctly.
    # Use modulus-weighted getters even when all weights equal 1.0.
    sec.display_results()

    # 5. Individual property access via SP native composite API
    ea         = sec.get_ea()           # effective area (e.a)
    cx, cy     = sec.get_c()            # centroid (cx, cy)
    eig        = sec.get_eig()          # (e.ixx_g, e.iyy_g, e.ixy_g)
    eic        = sec.get_eic()          # (e.ixx_c, e.iyy_c, e.ixy_c)
    ez         = sec.get_ez()           # (e.zxx+, e.zxx-, e.zyy+, e.zyy-)
    eip        = sec.get_eip()          # (e.i11_c, e.i22_c)
    phi        = sec.get_phi()          # principal axis angle
    rc         = sec.get_rc()           # (rx, ry) centroidal radii of gyration
    ej         = sec.get_ej()           # e.j (FEM warping)
    x_se, y_se = sec.get_sc()           # shear centre
    egamma     = sec.get_egamma()       # warping constant
    eas        = sec.get_eas()          # (e.a_sx, e.a_sy) shear areas

    print(f"\nIndividual property access")
    print("-" * 40)
    print(f"e.a              : {ea:.6e}")
    print(f"cx               : {cx:.6e}")
    print(f"cy               : {cy:.6e}")
    print(f"e.ixx_g          : {eig[0]:.6e}")
    print(f"e.iyy_g          : {eig[1]:.6e}")
    print(f"e.ixy_g          : {eig[2]:.6e}")
    print(f"e.ixx_c          : {eic[0]:.6e}")
    print(f"e.iyy_c          : {eic[1]:.6e}")
    print(f"e.ixy_c          : {eic[2]:.6e}")
    print(f"e.zxx+           : {ez[0]:.6e}")
    print(f"e.zxx-           : {ez[1]:.6e}")
    print(f"e.zyy+           : {ez[2]:.6e}")
    print(f"e.zyy-           : {ez[3]:.6e}")
    print(f"e.i11_c          : {eip[0]:.6e}")
    print(f"e.i22_c          : {eip[1]:.6e}")
    print(f"phi              : {phi:.6e}")
    print(f"rx               : {rc[0]:.6e}")
    print(f"ry               : {rc[1]:.6e}")
    print(f"e.j (FEM)        : {ej:.6e}")
    print(f"x_se             : {x_se:.6e}")
    print(f"y_se             : {y_se:.6e}")
    print(f"e.gamma          : {egamma:.6e}")
    print(f"e.a_sx           : {eas[0]:.6e}")
    print(f"e.a_sy           : {eas[1]:.6e}")
```

Expected output of `sec.display_results()`:

```
     Section Properties      
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Property  ┃         Value ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ area      │  1.840000e-02 │
│ perimeter │  1.000000e+00 │
│ mass      │  1.840000e-02 │
│ e.a       │  1.840000e-02 │
│ e.ixx_g   │  2.156533e-04 │
│ e.iyy_g   │  1.112533e-04 │
│ cx        │ -3.682752e-19 │
│ cy        │ -7.365504e-19 │
│ e.ixx_c   │  2.156533e-04 │
│ e.iyy_c   │  1.112533e-04 │
│ e.zxx+    │  1.437689e-03 │
│ e.zxx-    │  1.437689e-03 │
│ e.zyy+    │  1.112533e-03 │
│ e.zyy-    │  1.112533e-03 │
│ rx        │  1.082603e-01 │
│ ry        │  7.775845e-02 │
│ e.i11_c   │  2.156533e-04 │
│ e.i22_c   │  1.112533e-04 │
│ phi       │  0.000000e+00 │
│ e_eff     │  1.000000e+00 │
│ g_eff     │  5.000000e-01 │
│ nu_eff    │  0.000000e+00 │
│ e.j       │  2.324106e-04 │
│ x_se      │ -2.622612e-17 │
│ y_se      │  1.630298e-16 │
│ e.gamma   │  5.970124e-08 │
│ e.a_sx    │  5.721224e-03 │
│ e.a_sy    │  1.042444e-02 │
└───────────┴───────────────┘
```

Expected output of individual getters:

```
e.a    : 1.840000e-02
e.ixx_c: 2.156533e-04
e.iyy_c: 1.112533e-04
e.j    : 2.324106e-04
rx     : 1.082603e-01
ry     : 7.775845e-02
```

---

# Extracting sectionproperties Composite Results

The `csf_sp` interface builds a `sectionproperties` model with material data attached to the geometry. Since the section is handled by `sectionproperties` as a composite/material-based model, the corresponding composite result accessors are used.

In this validation example, the assigned material has `E = 1.0`. Therefore the stiffness-weighted values returned by `sectionproperties` are numerically equal to the corresponding geometric quantities. In practical terms, `EA` can be compared with `A`, while `EIx` and `EIy` can be compared with `Ix` and `Iy`.

```python
# ---------------------------------------------------------------------------
# 5) Extract sectionproperties composite results.
# ---------------------------------------------------------------------------
# csf_sp builds a material-based sectionproperties model.
# Therefore sectionproperties treats the result as a composite analysis and
# exposes stiffness-weighted quantities through get_ea(), get_eic(), etc.
#
# In this test the material has E = 1.0, so the stiffness-weighted values are
# numerically equal to the corresponding geometric values:
#   EA  -> A
#   EIx -> Ix
#   EIy -> Iy
```

```
"""
CSF-SP integration example with ordinary CSF no-cell geometry.

Purpose
-------
This script compares geometric properties between:

1) CSF ordinary composite geometry:
   - outer polygon with weight = 1.0
   - inner polygon with weight = 0.0

2) sectionproperties geometry generated through csf_sp from the same CSF field.

No @cell polygon is used in this script.
No slit-encoded polygon is used in this script.
No J_sv_cell check is performed in this script.

Expected result
---------------
A, Cx, Cy, Ix, Iy, Ixy, rx and ry should match between CSF and
sectionproperties up to numerical precision.
"""

from csf import (
    ContinuousSectionField,
    Section,
    Polygon,
    Pt,
    section_full_analysis,
    section_full_analysis_keys,
)
from csf.utils.csf_sp import analyse

import matplotlib.pyplot as plt


Z0 = 0.0
Z1 = 10.0
Z_CHECK = 0.0
MESH_SIZE = 1e-4


# ---------------------------------------------------------------------------
# 1) Define the physical section as ordinary CSF polygons.
# ---------------------------------------------------------------------------
# Outer loop: CCW irregular boundary.
outer_vertices = (
    Pt(-0.14, -0.16),
    Pt( 0.08, -0.18),
    Pt( 0.15, -0.08),
    Pt( 0.13,  0.12),
    Pt( 0.02,  0.18),
    Pt(-0.12,  0.14),
    Pt(-0.17,  0.02),
)

# Inner loop source order.
# It is reversed below because ordinary CSF polygons are expected as
# standalone CCW loops after upstream validation.
inner_vertices_source = (
    Pt(-0.09, -0.10),
    Pt(-0.11,  0.03),
    Pt(-0.05,  0.10),
    Pt( 0.05,  0.11),
    Pt( 0.10,  0.02),
    Pt( 0.08, -0.09),
    Pt(-0.02, -0.13),
)

inner_vertices = tuple(reversed(inner_vertices_source))


# ---------------------------------------------------------------------------
# 2) Build the ordinary CSF field.
# ---------------------------------------------------------------------------
# The inner polygon has weight = 0.0, so it acts as an explicit void in the
# ordinary composite geometry path.
outer = Polygon(
    vertices=outer_vertices,
    weight=1.0,
    name="outer",
)

inner = Polygon(
    vertices=inner_vertices,
    weight=0.0,
    name="inner",
)

s0 = Section(polygons=(outer, inner), z=Z0)
s1 = Section(polygons=(outer, inner), z=Z1)

field = ContinuousSectionField(section0=s0, section1=s1)


# ---------------------------------------------------------------------------
# 3) Run sectionproperties through csf_sp from the same ordinary CSF field.
# ---------------------------------------------------------------------------
plt.close("all")

sec_sp = analyse(field, z=Z_CHECK, mesh=MESH_SIZE)


# Show the sectionproperties geometry.
ax = sec_sp.geometry.plot_geometry(
    labels=("points", "facets", "control_points"),
    cp=True,
)
ax.plot(0.0, 0.0, marker="x", markersize=8)
ax.text(0.0, 0.0, "  void")
ax.set_aspect("equal", adjustable="box")
plt.show(block=True)


# Show the generated sectionproperties mesh.
ax = sec_sp.plot_mesh(materials=False)
ax.set_aspect("equal", adjustable="box")
plt.show(block=True)


# Print the full sectionproperties result table.
sec_sp.display_results()


# ---------------------------------------------------------------------------
# 4) Run CSF ordinary geometry analysis.
# ---------------------------------------------------------------------------
sec_at_z = field.section(Z_CHECK)
analysis = section_full_analysis(sec_at_z)

print("\nCSF ordinary geometry full analysis at z = 0.0")
for key in section_full_analysis_keys():
    print(f"{key}: {analysis[key]}")


# ---------------------------------------------------------------------------
# 5) Extract sectionproperties composite results.
# ---------------------------------------------------------------------------
# csf_sp builds a material-based sectionproperties model.
# Therefore sectionproperties treats the result as a composite analysis and
# exposes stiffness-weighted quantities through get_ea(), get_eic(), etc.
#
# In this test the material has E = 1.0, so the stiffness-weighted values are
# numerically equal to the corresponding geometric values:
#   EA  -> A
#   EIx -> Ix
#   EIy -> Iy
sp_area = sec_sp.get_ea()

sp_qx, sp_qy = sec_sp.get_eq()
sp_cx = sp_qy / sp_area
sp_cy = sp_qx / sp_area

sp_ixx, sp_iyy, sp_ixy = sec_sp.get_eic()

sp_rx = (sp_ixx / sp_area) ** 0.5
sp_ry = (sp_iyy / sp_area) ** 0.5


# ---------------------------------------------------------------------------
# 6) Build geometric comparison.
# ---------------------------------------------------------------------------
geometry_comparison = (
    ("A",   analysis["A"],   sp_area),
    ("Cx",  analysis["Cx"],  sp_cx),
    ("Cy",  analysis["Cy"],  sp_cy),
    ("Ix",  analysis["Ix"],  sp_ixx),
    ("Iy",  analysis["Iy"],  sp_iyy),
    ("Ixy", analysis["Ixy"], sp_ixy),
    ("rx",  analysis["rx"],  sp_rx),
    ("ry",  analysis["ry"],  sp_ry),
)


def print_comparison(title, rows):
    """Print a fixed-width side-by-side comparison table."""
    print(f"\n{title}")
    print(f"{'Property':<12} {'CSF':>20} {'SP':>20} {'Delta':>20} {'RelDelta':>14}")
    print("-" * 91)

    for name, csf_value, sp_value in rows:
        delta = csf_value - sp_value
        rel_delta = delta / sp_value if abs(sp_value) > 0.0 else 0.0
        print(
            f"{name:<12} "
            f"{csf_value:>20.12e} "
            f"{sp_value:>20.12e} "
            f"{delta:>20.12e} "
            f"{rel_delta:>14.6e}"
        )


print_comparison(
    "CSF ordinary no-cell geometry vs sectionproperties at z = 0.0",
    geometry_comparison,
)

print("\nExpected torsion flags for ordinary no-cell geometry")
print(f"J_sv_cell: {analysis['J_sv_cell']}")
print(f"J_sv_wall: {analysis['J_sv_wall']}")
```
Result
```
     Section Properties      
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Property  ┃         Value ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ area      │  5.380000e-02 │
│ perimeter │  1.127355e+00 │
│ mass      │  5.380000e-02 │
│ e.a       │  5.380000e-02 │
│ e.qx      │ -3.220000e-04 │
│ e.qy      │ -5.331667e-04 │
│ e.ixx_g   │  6.303150e-04 │
│ e.iyy_g   │  5.086483e-04 │
│ e.ixy_g   │  8.129167e-06 │
│ cx        │ -9.910161e-03 │
│ cy        │ -5.985130e-03 │
│ e.ixx_c   │  6.283878e-04 │
│ e.iyy_c   │  5.033646e-04 │
│ e.ixy_c   │  4.938095e-06 │
│ e.zxx+    │  3.378699e-03 │
│ e.zxx-    │  3.611115e-03 │
│ e.zyy+    │  3.147796e-03 │
│ e.zyy-    │  3.144263e-03 │
│ my_xx     │  3.383777e-03 │
│ my_yy     │  3.136146e-03 │
│ rx        │  1.080744e-01 │
│ ry        │  9.672755e-02 │
│ e.i11_c   │  6.285825e-04 │
│ e.i22_c   │  5.031698e-04 │
│ phi       │ -2.258346e+00 │
│ e.z11+    │  3.361057e-03 │
│ e.z11-    │  3.690234e-03 │
│ e.z22+    │  3.092575e-03 │
│ e.z22-    │  3.125483e-03 │
│ my_11     │  3.361057e-03 │
│ my_22     │  3.092575e-03 │
│ r11       │  1.080911e-01 │
│ r22       │  9.670884e-02 │
│ e_eff     │  1.000000e+00 │
│ g_eff     │  5.000000e-01 │
│ nu_eff    │  0.000000e+00 │
│ e.j       │  1.042028e-03 │
│ x_se      │ -1.374820e-02 │
│ y_se      │ -1.710883e-03 │
│ x1_se     │ -4.003485e-03 │
│ y2_se     │  4.119688e-03 │
│ x_st      │ -1.374820e-02 │
│ y_st      │ -1.710883e-03 │
│ e.gamma   │  7.463910e-08 │
│ e.a_sx    │  2.574289e-02 │
│ e.a_sy    │  2.948160e-02 │
│ e.a_s11   │  2.564617e-02 │
│ e.a_s22   │  2.960948e-02 │
│ beta_x+   │  1.181022e-02 │
│ beta_x-   │ -1.181022e-02 │
│ beta_y+   │ -1.388617e-02 │
│ beta_y-   │  1.388617e-02 │
│ beta_11+  │  1.130160e-02 │
│ beta_11-  │ -1.130160e-02 │
│ beta_22+  │ -1.437516e-02 │
│ beta_22-  │  1.437516e-02 │
└───────────┴───────────────┘


CSF ordinary geometry full analysis at z = 0.0
A: 0.053799999999999994
Cx: -0.009910161090458499
Cy: -0.0059851301115241735
Ix: 0.0006283877881040894
Iy: 0.0005033645657786039
Ixy: 4.938094795539014e-06
Ip: 0.0011317523538826933
I1: 0.0006285825267822652
I2: 0.0005031698271004281
rx: 0.1080743744411999
ry: 0.09672754878921305
Wx: 0.0033786990805516697
Wy: 0.003144263053840845
K_torsion: 0.0001850621932629167
Q_na: 0.0026194701134895897
J_sv_wall: 0.0
J_sv_cell: 0.0
J_s_vroark: 0.0003234390889725317
J_s_vroark_fidelity: 0.47936764158394424

CSF ordinary no-cell geometry vs sectionproperties at z = 0.0
Property                      CSF                   SP                Delta       RelDelta
-------------------------------------------------------------------------------------------
A              5.380000000000e-02   5.380000000000e-02  -4.857225732735e-17  -9.028301e-16
Cx            -9.910161090458e-03  -9.910161090459e-03   1.387778780781e-17  -1.400359e-15
Cy            -5.985130111524e-03  -5.985130111524e-03  -5.204170427930e-18   8.695167e-16
Ix             6.283877881041e-04   6.283877881041e-04   4.336808689942e-19   6.901485e-16
Iy             5.033645657786e-04   5.033645657786e-04  -2.168404344971e-19  -4.307821e-16
Ixy            4.938094795539e-06   4.938094795539e-06   8.131516293641e-20   1.646691e-14
rx             1.080743744412e-01   1.080743744412e-01   9.714451465470e-17   8.988672e-16
ry             9.672754878921e-02   9.672754878921e-02   2.775557561563e-17   2.869459e-16

Expected torsion flags for ordinary no-cell geometry
J_sv_cell: 0.0
J_sv_wall: 0.0

```


---
*csf_sp - part of the [continuous-section-field (csfpy)](https://github.com/giovanniboscu/continuous-section-field) package | GPL-3.0*
