# csf_sp User Guide

**Bridge between CSF section models and sectionproperties**

---

## 1. What is csf_sp

`csf_sp` bridges [CSF](https://github.com/giovanniboscu/continuous-section-field) and [sectionproperties](https://sectionproperties.readthedocs.io):
you describe your cross-section once in a YAML file and get the full sectionproperties
result set - area, moments of inertia, warping constant, shear areas and more - at any
position along the member axis. No Python code required.

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

### 2.5 Tapered section example

S0 and S1 can have different vertices - CSF interpolates the geometry continuously.
This example shows a rectangular section that tapers from 0.20 × 0.30 m at the base
to 0.12 × 0.20 m at the top over a 30 m member:

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

At z = 15.0 (mid-span) the section is interpolated - outer dimensions are
0.16 × 0.25 m, halfway between the two ends.

### 2.6 Weight variation along z

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

### 2.7 Custom weight law

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

> The two names in the law (`s0_name,s1_name`) identify the polygon in S0 and S1.
> They can be different - CSF matches by name, not by position.
> Using the same name in both sections is a common convention but not a requirement.
> If a name used in a weight law does not match a valid polygon pair, the input is
> rejected immediately at load time.

For the full syntax and available variables (`z`, `t`, `w0`, `w1`, `L`, `np`,
lookup tables), see the [CSF Weight Laws guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSFLongitudinally-varying-homogenization-user-guide.md).

### 2.8 Fast analytical torsional constant (optional)

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

## 7. Multiple Stations

### 7.1 Via CLI run-config

To analyse several positions along the member in one command, create a small run-config YAML file that lists the stations:

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

csf_sp will print the full sectionproperties table for each station, separated by a horizontal rule.

### 7.2 Via Python API

The same station list can be iterated programmatically using the `load_yaml` and `analyse` public API functions:

```python
from csf.utils.csf_sp import load_yaml, analyse

field = load_yaml("csf_sp_example.yaml")

stations = [0.0, 2.5, 5.0, 7.5, 10.0]

for z in stations:
    sec = analyse(field, z=z)
    ej  = sec.get_ej()           # Saint-Venant J (FEM warping)
    eic = sec.get_eic()          # (e.ixx_c, e.iyy_c, e.ixy_c)
    print(f"z={z:5.1f}  e.j={ej:.4e}  e.ixx_c={eic[0]:.4e}  e.iyy_c={eic[1]:.4e}")
```

For the prismatic `csf_sp_example.yaml` (S0 = S1) all stations return identical values.
For a tapered section (S0 ≠ S1) the properties vary continuously along z.

---

## 8. Legacy CSV Input

csf_sp can also read the geometry export block produced by the CSF `section_selected_analysis` action.
This allows running sectionproperties on any section that has already been exported to CSV,
without reloading the original YAML model.

### 8.1 CSV format

The CSV export block is appended automatically by the `section_selected_analysis` action and looks like this:

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

The file may contain one or more export blocks at different z values.

### 8.2 CLI usage

Pass the CSV file path as a positional argument (no `--yaml` flag):

```bash
python -m csf.utils.csf_sp out/section_analysis.csv
```

To select a specific z station when the file contains multiple blocks:

```bash
python -m csf.utils.csf_sp out/section_analysis.csv --z=5.0
```

### 8.3 Example

Given the following CSV file saved as `out/section_export.csv`:

```
## GEOMETRY EXPORT ##
# z=0.0
idx_polygon,idx_container,s0_name,s1_name,w,vertex_i,x,y
0,,outer,outer,1.000000,0,-0.100000,-0.150000
0,,outer,outer,1.000000,1, 0.100000,-0.150000
0,,outer,outer,1.000000,2, 0.100000, 0.150000
0,,outer,outer,1.000000,3,-0.100000, 0.150000
1,0,inner,inner,0.000000,0,-0.080000,-0.130000
1,0,inner,inner,0.000000,1, 0.080000,-0.130000
1,0,inner,inner,0.000000,2, 0.080000, 0.130000
1,0,inner,inner,0.000000,3,-0.080000, 0.130000
```

Run:

```bash
python -m csf.utils.csf_sp out/section_export.csv
```

Expected output: same sectionproperties table as `--yaml=csf_sp_example.yaml --z=0`.

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

The field object can also be constructed directly via the CSF Python API without a YAML file:

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
# Simple hollow rectangular box section - prismatic over 10 m
# outer: 0.20 x 0.30 m, wall thickness: 0.02 m

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

*csf_sp — part of the [continuous-section-field (csfpy)](https://github.com/giovanniboscu/continuous-section-field) package | GPL-3.0*
