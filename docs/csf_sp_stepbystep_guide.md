# From sectionproperties to CSF: A Step-by-Step Guide

**Progressive examples - Python API and YAML**

This guide walks through a complete set of working examples that show how to move
from native sectionproperties usage to the CSF declarative model. Each group is
self-contained and can be run independently.

All examples use the same base geometry: a rectangle 50 × 100 mm (b × h) that may
taper and carry a varying weight along its length.

---

## Prerequisites

```bash
pip install sectionproperties
pip install csfpy          # installs the csf package including csf_sp
```

Imports used across all examples:

```python
from csf import ContinuousSectionField, Section, Polygon, Pt
from csf import section_full_analysis, section_full_analysis_keys
from csf.utils.csf_sp import load_yaml, analyse
```

---

## Group A - Native sectionproperties (baseline)

### A1 · `sp_example.py`

The canonical sectionproperties example from the official README.
A 50 × 100 mm rectangle, geometric analysis only, no material.

```python
from sectionproperties.pre.library import rectangular_section
from sectionproperties.analysis import Section

geom = rectangular_section(d=100, b=50)
geom.create_mesh(mesh_sizes=[5])
sec = Section(geometry=geom)
sec.calculate_geometric_properties()

area = sec.get_area()
ixx_c, iyy_c, ixy_c = sec.get_ic()
print(f"Area = {area:.0f} mm²")
print(f"Ixx = {ixx_c:.0f} mm⁴, Iyy = {iyy_c:.0f} mm⁴")
```

**Output:**
```
Area = 5000 mm²
Ixx = 4166667 mm⁴, Iyy = 1041667 mm⁴
```

> **Note on getters**: sectionproperties distinguishes between geometric sections
> (`get_area`, `get_ic`) and composite/material sections (`get_ea`, `get_eic`).
> CSF always assigns `Material` objects to regions, so all csf_sp examples must use
> the composite getters - even when all polygon weights equal 1.0.

---

## Group B - CSF Python API + sectionproperties

These examples construct the CSF field entirely in Python - no YAML file required.
The geometry YAML approach is covered in Group C.

### B1 · `csf_sp_step2_api.py` - Prismatic section, weight 1.0

Equivalent to A1 but built through the CSF API. Results must be identical.

```python
from csf import ContinuousSectionField, Section, Polygon, Pt
from csf.utils.csf_sp import analyse

b = 50.0
h = 100.0

rect_s0 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h), Pt(0.0, h)),
    weight=1.0,
    name="rect",
)

rect_s1 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h), Pt(0.0, h)),
    weight=1.0,
    name="rect",
)

s0 = Section(polygons=(rect_s0,), z=0.0)
s1 = Section(polygons=(rect_s1,), z=1.0)

field = ContinuousSectionField(section0=s0, section1=s1)

sec  = analyse(field, z=0.5, warping=False)
area = sec.get_ea()
ixx_c, iyy_c, ixy_c = sec.get_eic()
print(f"Area = {area:.0f} mm²")
print(f"Ixx = {ixx_c:.0f} mm⁴, Iyy = {iyy_c:.0f} mm⁴")
```

**Output:**
```
Area = 5000 mm²
Ixx = 4166667 mm⁴, Iyy = 1041667 mm⁴
```

---

### B2 · `csf_sp_step3_api.py` - Linear weight variation, constant geometry

Weight varies linearly from 1.0 at z=0 to 2.0 at z=2. Geometry is constant.
`area` (geometric) stays fixed; `e.a` (homogenized) scales with weight.

```python
from csf import ContinuousSectionField, Section, Polygon, Pt
from csf.utils.csf_sp import analyse

b = 50.0
h = 100.0

rect_s0 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h), Pt(0.0, h)),
    weight=1.0,
    name="rect",
)

rect_s1 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h), Pt(0.0, h)),
    weight=2.0,
    name="rect",
)

s0 = Section(polygons=(rect_s0,), z=0.0)
s1 = Section(polygons=(rect_s1,), z=2.0)

field = ContinuousSectionField(section0=s0, section1=s1)

for z in [0.0, 1.0, 2.0]:
    sec  = analyse(field, z=z, warping=False)
    area = sec.get_area()
    ea   = sec.get_ea()
    ixx_c, iyy_c, ixy_c = sec.get_eic()
    print(f"z={z:.1f}  area={area:.0f}  e.a={ea:.0f}  Ixx={ixx_c:.0f}")
```

**Output:**
```
z=0.0  area=5000  e.a=5000  Ixx=4166667
z=1.0  area=5000  e.a=7500  Ixx=6250000
z=2.0  area=5000  e.a=10000  Ixx=8333333
```

---

### B3 · `csf_sp_step4_api.py` - Parabolic weight law via API

Same boundary weights (1.0 → 2.0) but with a parabolic custom law.
At z=1.0 the weight is 1.25 instead of 1.5 - the curve rises more slowly than linear.

```python
from csf import ContinuousSectionField, Section, Polygon, Pt
from csf.utils.csf_sp import analyse

b = 50.0
h = 100.0

rect_s0 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h), Pt(0.0, h)),
    weight=1.0,
    name="rect",
)

rect_s1 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h), Pt(0.0, h)),
    weight=2.0,
    name="rect",
)

s0 = Section(polygons=(rect_s0,), z=0.0)
s1 = Section(polygons=(rect_s1,), z=2.0)

field = ContinuousSectionField(section0=s0, section1=s1)

field.set_weight_laws([
    "rect,rect: w0 + (w1 - w0) * (z / L)**2",
])

for z in [0.0, 1.0, 2.0]:
    sec  = analyse(field, z=z, warping=False)
    area = sec.get_area()
    ea   = sec.get_ea()
    ixx_c, iyy_c, ixy_c = sec.get_eic()
    print(f"z={z:.1f}  area={area:.0f}  e.a={ea:.0f}  Ixx={ixx_c:.0f}")
```

**Output:**
```
z=0.0  area=5000  e.a=5000  Ixx=4166667
z=1.0  area=5000  e.a=6250  Ixx=5208333
z=2.0  area=5000  e.a=10000  Ixx=8333333
```

---

### B4 · `csf_sp_step6_api.py` - Sinusoidal weight law via API

Same boundary weights but with a half-cosine law.
At z=1.0 (mid-point) the weight is exactly 1.5 - symmetric about mid-span.

```python
from csf import ContinuousSectionField, Section, Polygon, Pt
from csf.utils.csf_sp import analyse

b = 50.0
h = 100.0

rect_s0 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h), Pt(0.0, h)),
    weight=1.0,
    name="rect",
)

rect_s1 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h), Pt(0.0, h)),
    weight=2.0,
    name="rect",
)

s0 = Section(polygons=(rect_s0,), z=0.0)
s1 = Section(polygons=(rect_s1,), z=2.0)

field = ContinuousSectionField(section0=s0, section1=s1)

field.set_weight_laws([
    "rect,rect: w0 + (w1 - w0) * 0.5 * (1 - np.cos(np.pi * z / L))",
])

for z in [0.0, 1.0, 2.0]:
    sec  = analyse(field, z=z, warping=False)
    area = sec.get_area()
    ea   = sec.get_ea()
    ixx_c, iyy_c, ixy_c = sec.get_eic()
    print(f"z={z:.1f}  area={area:.0f}  e.a={ea:.0f}  Ixx={ixx_c:.0f}")
```

**Output:**
```
z=0.0  area=5000  e.a=5000  Ixx=4166667
z=1.0  area=5000  e.a=7500  Ixx=6250000
z=2.0  area=5000  e.a=10000  Ixx=8333333
```

> **Law comparison at z=1.0 (mid-point):**
>
> | Law | e.a at z=1.0 |
> |---|---|
> | Linear (default) | 7500 |
> | Parabolic | 6250 |
> | Sinusoidal | 7500 |
>
> Linear and sinusoidal coincide at the mid-point by symmetry.
> The difference is visible at intermediate stations (z=0.5, z=1.5).

---

### B5 · `csf_sp_step7_api.py` - Variable geometry + variable weight

S0: 50×100 mm, S1: 50×50 mm. Weight 1.0→2.0 with parabolic law.
`area` decreases geometrically; `e.a` is the combined effect of both fields.
Geometry and weight are **independent** in CSF.

```python
from csf import ContinuousSectionField, Section, Polygon, Pt
from csf.utils.csf_sp import analyse

b  = 50.0
h0 = 100.0
h1 = 50.0

rect_s0 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h0), Pt(0.0, h0)),
    weight=1.0,
    name="rect",
)

rect_s1 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h1), Pt(0.0, h1)),
    weight=2.0,
    name="rect",
)

s0 = Section(polygons=(rect_s0,), z=0.0)
s1 = Section(polygons=(rect_s1,), z=2.0)

field = ContinuousSectionField(section0=s0, section1=s1)

field.set_weight_laws([
    "rect,rect: w0 + (w1 - w0) * (z / L)**2",
])

for z in [0.0, 1.0, 2.0]:
    sec  = analyse(field, z=z, warping=False)
    area = sec.get_area()
    ea   = sec.get_ea()
    ixx_c, iyy_c, ixy_c = sec.get_eic()
    print(f"z={z:.1f}  area={area:.0f}  e.a={ea:.0f}  Ixx={ixx_c:.0f}")
```

**Output:**
```
z=0.0  area=5000  e.a=5000  Ixx=4166667
z=1.0  area=3750  e.a=4687  Ixx=2197266
z=2.0  area=2500  e.a=5000  Ixx=1041667
```

---

### B6 · `csf_sp_step7_api_vs_csf.py` - SP vs CSF full comparison

Same model as B5. At each station, sectionproperties results are printed
alongside the complete CSF `section_full_analysis` output in a side-by-side table.
Warping is enabled so that `e.j` (FEM) can be compared against `J_s_vroark` (Roark).

```python
from csf import ContinuousSectionField, Section, Polygon, Pt
from csf import section_full_analysis, section_full_analysis_keys
from csf.utils.csf_sp import analyse

b  = 50.0
h0 = 100.0
h1 = 50.0

rect_s0 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h0), Pt(0.0, h0)),
    weight=1.0,
    name="rect",
)

rect_s1 = Polygon(
    vertices=(Pt(0.0, 0.0), Pt(b, 0.0), Pt(b, h1), Pt(0.0, h1)),
    weight=2.0,
    name="rect",
)

s0 = Section(polygons=(rect_s0,), z=0.0)
s1 = Section(polygons=(rect_s1,), z=2.0)

field = ContinuousSectionField(section0=s0, section1=s1)

field.set_weight_laws([
    "rect,rect: w0 + (w1 - w0) * (z / L)**2",
])

SKIP_KEYS = {"J_sv_wall", "J_sv_cell"}

for z in [0.0, 1.0, 2.0]:
    sec = analyse(field, z=z, warping=True)

    sp_ea                   = sec.get_ea()
    sp_cx, sp_cy            = sec.get_c()
    sp_ixx, sp_iyy, sp_ixy  = sec.get_eic()
    sp_rx, sp_ry            = sec.get_rc()
    sp_ej                   = sec.get_ej()   # FEM warping torsional constant

    sp = {
        "A":   sp_ea,
        "Cx":  sp_cx,
        "Cy":  sp_cy,
        "Ix":  sp_ixx,
        "Iy":  sp_iyy,
        "Ixy": sp_ixy,
        "rx":  sp_rx,
        "ry":  sp_ry,
    }

    csf_sec  = field.section(z)
    csf_data = section_full_analysis(csf_sec)

    print(f"\nz = {z:.1f}")
    print(f"  {'Key':<25} {'CSF':>20} {'SP':>20}")
    print(f"  {'-'*67}")
    for key in section_full_analysis_keys():
        if key in SKIP_KEYS:
            continue
        csf_val = csf_data[key]
        sp_val  = sp.get(key, "")
        sp_str  = f"{sp_val:>20.4f}" if sp_val != "" else f"{'-':>20}"
        print(f"  {key:<25} {csf_val:>20.4f} {sp_str}")

    # Torsional constant - two different methods
    print(f"  {'---':<25}")
    print(f"  {'J_s_vroark (CSF/Roark)':<25} {csf_data['J_s_vroark']:>20.4f} {'-':>20}")
    print(f"  {'e.j (SP/FEM warping)':<25} {'-':>20} {sp_ej:>20.4f}")
    print(f"  {'J_s_vroark_fidelity':<25} {csf_data['J_s_vroark_fidelity']:>20.4f} {'-':>20}")
```

**Output:**
```
z = 0.0
  Key                                        CSF                   SP
  -------------------------------------------------------------------
  A                                    5000.0000            5000.0000
  Cx                                     25.0000              25.0000
  Cy                                     50.0000              50.0000
  Ix                                4166666.6667         4166666.6667
  Iy                                1041666.6667         1041666.6667
  Ixy                                     0.0000               0.0000
  rx                                     28.8675              28.8675
  ry                                     14.4338              14.4338
  ...
  ---
  J_s_vroark (CSF/Roark)            2861002.6042                    -
  e.j (SP/FEM warping)                         -         2858521.5336
  J_s_vroark_fidelity                     0.5000                    -

z = 1.0
  ...
  J_s_vroark (CSF/Roark)            2602599.3827                    -
  e.j (SP/FEM warping)                         -         2294071.5928
  J_s_vroark_fidelity                     0.5333                    -

z = 2.0
  ...
  J_s_vroark (CSF/Roark)            2861002.6042                    -
  e.j (SP/FEM warping)                         -         1757213.7478
  J_s_vroark_fidelity                     0.5000                    -
```

> **Torsional constant comparison:**
>
> | z | J_s_vroark (Roark) | e.j (FEM) | delta % |
> |---|---|---|---|
> | 0.0 | 2 861 003 | 2 858 522 | 0.09% ✓ |
> | 1.0 | 2 602 599 | 2 294 072 | 11.8% |
> | 2.0 | 2 861 003 | 1 757 214 | 38.7% |
>
> At z=0.0 (50×100 mm, aspect ratio 2:1) the two methods agree within 0.1%.
> At z=1.0 and z=2.0 the section becomes squarer (aspect ratio approaching 1:1)
> and Roark diverges progressively from the FEM result.
> The `J_s_vroark_fidelity` indicator (0.50–0.53, borderline range) correctly
> signals that the Roark approximation is outside its most reliable domain.
> For solid rectangular sections with aspect ratio near 1:1, the FEM warping
> result from sectionproperties is the more reliable value.

---

## Group C - CSF YAML geometry + sectionproperties

The same cases above can be driven entirely from YAML files.
YAML and API are interchangeable - results are identical.

### C1 · Prismatic section, weight 1.0

**`rect_50x100.yaml`**

```yaml
# rect_50x100.yaml  - 50 x 100 mm rectangle, prismatic
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            - [ 0.0,   0.0]
            - [50.0,   0.0]
            - [50.0, 100.0]
            - [ 0.0, 100.0]
    S1:
      z: 1.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            - [ 0.0,   0.0]
            - [50.0,   0.0]
            - [50.0, 100.0]
            - [ 0.0, 100.0]
```

```python
from csf.utils.csf_sp import load_yaml, analyse

field = load_yaml("rect_50x100.yaml")
sec   = analyse(field, z=0.5, warping=False)
area  = sec.get_ea()
ixx_c, iyy_c, ixy_c = sec.get_eic()
print(f"Area = {area:.0f} mm²")
print(f"Ixx = {ixx_c:.0f} mm⁴, Iyy = {iyy_c:.0f} mm⁴")
```

Or via CLI:
```bash
python -m csf.utils.csf_sp --yaml=rect_50x100.yaml --z=0.5 --no-warping
```

---

### C2 · Variable geometry + parabolic weight law

**`rect_50x100_law_var.yaml`**

```yaml
# rect_50x100_law_var.yaml  - tapered rectangle with parabolic weight law
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            - [ 0.0,   0.0]
            - [50.0,   0.0]
            - [50.0, 100.0]
            - [ 0.0, 100.0]
    S1:
      z: 2.0
      polygons:
        rect:
          weight: 2.0
          vertices:
            - [ 0.0,   0.0]
            - [50.0,   0.0]
            - [50.0,  50.0]
            - [ 0.0,  50.0]
  weight_laws:
    - 'rect,rect: w0 + (w1 - w0) * (z / L)**2'
```

```python
from csf.utils.csf_sp import load_yaml, analyse

field = load_yaml("rect_50x100_law_var.yaml")

for z in [0.0, 1.0, 2.0]:
    sec  = analyse(field, z=z, warping=False)
    area = sec.get_area()
    ea   = sec.get_ea()
    ixx_c, iyy_c, ixy_c = sec.get_eic()
    print(f"z={z:.1f}  area={area:.0f}  e.a={ea:.0f}  Ixx={ixx_c:.0f}")
```

The weight law in the YAML can be overridden at runtime via the Python API:

```python
field = load_yaml("rect_50x100_law_var.yaml")

# Override with sinusoidal law
field.set_weight_laws([
    "rect,rect: w0 + (w1 - w0) * 0.5 * (1 - np.cos(np.pi * z / L))",
])
```

> **YAML quoting note**: when a law contains a lookup function with a filename
> argument, the filename uses single quotes inside the expression. In that case
> the outer YAML string must use double quotes to avoid a conflict:
>
> ```yaml
> weight_laws:
>   # WRONG - inner single quotes conflict with outer single quotes
>   - 'rect,rect: E_lookup('data.txt') * w0'
>
>   # CORRECT - use double quotes as outer delimiter
>   - "rect,rect: E_lookup('data.txt') * w0"
> ```

---

## Group D - CSF Actions YAML

CSF Actions are a YAML-driven pipeline that run a sequence of operations on a
loaded CSF field without writing any Python code.

### D1 · Action file for the tapered rectangle

**`rect_50x100_law_var_actions.yaml`**

```yaml
CSF_ACTIONS:
  stations:
    station_ends:  [0.0, 2.0]
    station_3pt:   [0.0, 1.0, 2.0]
    station_mid:   [1.0]

  actions:
    # 3D ruled-surface visualization
    - plot_volume_3d:
        params:
          line_percent: 100.0
          title: "Tapered rectangle - ruled volume"

    # 2D cross-section outlines at 3 stations
    - plot_section_2d:
        stations: [station_3pt]
        output: [stdout, out/sections2d.jpg]

    # Continuous property variation plot along z
    - plot_properties:
        output: [stdout, out/properties.png]
        properties: [A, Ix, Iy, Ip]
        params:
          num_points: 80

    # Volume report (occupied and homogenized)
    - volume:
        stations: station_ends
        output: [stdout, out/rectangle_volume.txt]
        params:
          n_points: 20
          fmt_display: ".6f"
          w_tol: 0.0

    # Full section analysis + geometry CSV export at 3 stations
    - section_selected_analysis:
        stations: station_3pt
        output:
          - stdout
          - out/sel_properties.txt
        properties: [geometry, A, Cx, Cy, Ix, Iy, Ixy, Ip, I1, I2,
                     rx, ry, Wx, Wy, Q_na, J_s_vroark, J_s_vroark_fidelity]

    # SAP2000 / OpenSeesPy export with 11 Gauss-Lobatto stations
    - write_sap2000_geometry:
        output: [out/rectangle_sap2000.txt]
        params:
          n_intervals: 10
          material_name: "S355"
          E_ref: 2.1e+11
          nu: 0.30
          mode: "BOTH"
          include_plot: True
          plot_filename: "out/rectangle_variation.jpg"
```

**Run:**
```bash
mkdir out
csf-actions rect_50x100_law_var.yaml rect_50x100_law_var_actions.yaml
```

**Output files produced in `out/`:**

| File | Content |
|---|---|
| `sections2d_001/2/3.jpg` | 2D cross-section plots at z=0, 1, 2 |
| `properties.png` | Continuous A, Ix, Iy, Ip variation along z |
| `rectangle_volume.txt` | Occupied and homogenized volume report |
| `sel_properties.txt` | Section properties + geometry CSV at 3 stations |
| `rectangle_sap2000.txt` | 4-table solver pack (11 Gauss-Lobatto stations) |
| `rectangle_variation.jpg` | Property variation plot from SAP2000 action |

**Volume report (`rectangle_volume.txt`):**
```
Total Occupied Volume:            7500.000000
Total Occupied Homogenized Volume: 9583.333333
```

**SAP2000 pack structure (`rectangle_sap2000.txt`):**

The file contains four tables:

- `TABLE 1 - SOLVER INPUT`: z, A, Ix, Iy, Ixy, Ip, J_tors, G_ref, Cx, Cy, method
- `TABLE 2 - SECTION QUALITY`: z, I1, I2, theta_deg, rx, ry, Wx, Wy, Q_na, K_torsion
- `TABLE 3 - TORSION QUALITY`: z, J_sv_cell, J_sv_wall, J_s_vroark, J_s_vroark_fidelity, J_tors, method
- `TABLE 4 - STATION NAMES`: id, z, section_name (SEC0001 ... SEC0011)

Stations are distributed using Gauss-Lobatto quadrature (`n_intervals=10` → 11 stations):
```
z = 0, 0.066, 0.216, 0.435, 0.704, 1.0, 1.296, 1.565, 1.784, 1.934, 2.0
```

> **Note on J_tors**: this model has no `@cell` or `@wall` polygon - no
> Saint-Venant torsional constant is available. TABLE 3 shows `J_tors = 0`
> with `J_tors skip` on all stations. This is expected and flagged by a warning.

---

## Summary

| Example | File | Geometry | Weight law | Tool |
|---|---|---|---|---|
| SP baseline | `sp_example.py` | Python | - | sectionproperties |
| Prismatic w=1 | `csf_sp_step2_api.py` | API | - | CSF+SP |
| Linear weight | `csf_sp_step3_api.py` | API | linear (default) | CSF+SP |
| Parabolic law | `csf_sp_step4_api.py` | API | parabolic | CSF+SP |
| Sinusoidal law | `csf_sp_step6_api.py` | API | sinusoidal | CSF+SP |
| Tapered + law | `csf_sp_step7_api.py` | API | parabolic | CSF+SP |
| SP vs CSF table | `csf_sp_step7_api_vs_csf.py` | API | parabolic | CSF+SP |
| Prismatic YAML | `rect_50x100.yaml` | YAML | - | CSF+SP |
| Tapered YAML | `rect_50x100_law_var.yaml` | YAML | parabolic | CSF+SP |
| Full pipeline | `rect_50x100_law_var_actions.yaml` | YAML | parabolic | CSF Actions |

---

*csf_sp - part of the [continuous-section-field (csfpy)](https://github.com/giovanniboscu/continuous-section-field) package | GPL-3.0*
