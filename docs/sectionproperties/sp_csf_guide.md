# == DRAFTT ==
`sectionproperties` is used as the analysis backend for the generated/interpolated sections. 
Please refer to the original project and its license:
https://github.com/robbievanleeuwen/section-properties
# sp_csf - User Guide

**Convert sectionproperties parametric sections to CSF YAML**

`sp_csf.py` bridges the sectionproperties parametric section library and the
CSF declarative geometry model. It takes one or two sectionproperties section
objects and writes a CSF-ready YAML file that can be loaded directly by
`csf-actions` or `csf_sp`.

---

## Installation

```bash
pip install sectionproperties shapely
pip install csfpy

```

`sp_csf.py` is a single-file script - no additional installation required.
Place it in your working directory and run it directly.

---

## Concepts

### Modes

| Mode | Description |
|---|---|
| **Prismatic** | S0 and S1 are the same section type with the same dimensions |
| **Tapered** | S0 and S1 are the same section type with different dimensions |
| **Morph** | S0 and S1 are different section types (e.g. I-section → circular) |

### Vertex resampling

sectionproperties constructs geometry as Shapely polygons with varying numbers
of vertices depending on section type and discretisation parameters (`n_r`, `n`).
CSF interpolates vertex-by-vertex between S0 and S1, so both sections must have
the same number of vertices per ring.

`sp_csf` resamples every ring to exactly `n` equidistant points along the
perimeter. The start point of each ring is fixed at the intersection with the
positive x semi-axis of the local (centroid-centered) frame, ensuring consistent
vertex correspondence between S0 and S1.

### Centroid auto-alignment

sectionproperties generates sections with varying centroid positions depending on
section type and dimensions. For example, a `rectangular_hollow_section` with
`d=200, b=150` has its centroid at `(75, 100)` in the SP coordinate frame, while
a `circular_hollow_section` with `d=180` has its centroid at `(0, 0)`.

When `auto_align=True` (the default), `sp_csf` automatically computes the
offset needed to align both centroids in the CSF coordinate frame. The reference
point is the centroid of S0, which is mapped to the origin. S1 is shifted by the
same amount so that its centroid coincides with S0's centroid.

Auto-alignment can be disabled with `--no-align`. In that case, raw SP coordinates
are used and you can supply explicit offsets with `--dx0/dy0/dx1/dy1`.

### Twist

A twist angle (in degrees, CCW) can be applied independently to S0 and S1. The
rotation is applied around the polygon centroid, after resampling and translation.
This allows modelling a member whose cross-section rotates from base to top -
for example a helical wind turbine tower or a twisted architectural column.

---

## CLI Reference

```
python3 -m csf.utils.sp_csf  <section_s0> [options]
```

### Required arguments

| Argument | Description |
|---|---|
| `section` | Section name for S0 (from `sectionproperties.pre.library`) |
| `--s0 key=val,...` | S0 parameters. **Must include `z=<float>`** |
| `--s1 key=val,...` | S1 parameters. **Must include `z=<float>`** |

### Optional arguments

| Argument | Default | Description |
|---|---|---|
| `--morph <section>` | - | Section name for S1 if different from S0 |
| `--n` | 64 | Vertices per ring after resampling |
| `--name` | `section` | Polygon base name in the YAML |
| `--out` | `<s0>_to_<s1>.yaml` | Output YAML file path |
| `--no-align` | off | Disable centroid auto-alignment |
| `--dx0`, `--dy0` | auto | Explicit offset for S0 (overrides auto-align) |
| `--dx1`, `--dy1` | auto | Explicit offset for S1 (overrides auto-align) |
| `--twist0` | 0.0 | Rotation of S0 in degrees CCW |
| `--twist1` | 0.0 | Rotation of S1 in degrees CCW |
| `--precision` | 6 | Decimal places for coordinates |

### Parameter format

Section parameters are passed as a comma-separated `key=value` string:

```
--s0 d=200,b=150,t=10,r_out=15,n_r=8,z=0.0
```

The key `z` sets the CSF z-coordinate of that section and is not passed to
sectionproperties. All other keys are forwarded directly to the SP library
function.

---

## CLI Examples

### Prismatic section

Same section at both ends - the simplest case.

```bash
python3 -m csf.utils.sp_csf rectangular_hollow_section \
  --s0 d=200,b=150,t=10,r_out=15,n_r=8,z=0 \
  --s1 d=100,b=150,t=10,r_out=15,n_r=8,z=10 \
   --gen-actions 
```

```bash
python3 -m csf.utils.sp_csf circular_hollow_section \
  --s0 d=500,t=20,n=48,z=0 \
  --s1 d=100,t=20,n=48,z=30 \
  --name=pipe --out=pipe.yaml \
   --gen-actions 
```

### Tapered section

Same section type, different dimensions at S0 and S1.

```bash
python3 -m csf.utils.sp_csf  rectangular_hollow_section \
  --s0 d=300,b=200,t=12,r_out=20,n_r=8,z=0 \
  --s1 d=100,b=150,t=8,r_out=15,n_r=8,z=10 \
  --out=rhs_tapered.yaml \
   --gen-actions 
```

```bash
python3 -m csf.utils.sp_csf i_section \
  --s0 d=400,b=200,t_f=15,t_w=10,r=18,n_r=8,z=0 \
  --s1 d=250,b=150,t_f=10,t_w=7,r=12,n_r=8,z=8 \
  --out=i_tapered.yaml \
   --gen-actions 
```

> **Note**: for tapered sections, `n_r` and `n` (discretisation parameters)
> must be identical in `--s0` and `--s1` to guarantee the same vertex count.

### Morphing between different section types

Use `--morph` to specify a different section type at S1. Centroids are
auto-aligned by default.

```bash
# I-section → circular section
python3 -m csf.utils.sp_csf  i_section \
  --morph circular_section \
  --s0 d=200,b=100,t_f=10,t_w=6,r=12,n_r=8,z=0 \
  --s1 d=150,n=32,z=10 \
  --n=256 --out=i_to_circle.yaml \
   --gen-actions 
```

```bash
# RHS → CHS (hollow → hollow)
python3 -m csf.utils.sp_csf  rectangular_hollow_section \
  --morph circular_hollow_section \
  --s0 d=200,b=150,t=10,r_out=15,n_r=8,z=0 \
  --s1 d=180,t=8,n=32,z=12 \
  --n=64 --out=rhs_to_chs.yaml \
   --gen-actions 
```

```bash
# Wind tower: square hollow → circular hollow over 70 m
python3 -m csf.utils.sp_csf  rectangular_hollow_section \
  --morph circular_hollow_section \
  --s0 d=4000,b=4000,t=30,r_out=300,n_r=16,z=0 \
  --s1 d=2500,t=18,n=48,z=70000 \
  --n=96 --name=tower --out=wind_tower.yaml \
   --gen-actions 
```

### Twist

Apply a rotation to S1 to model a member that twists from base to top.

```bash
# RHS → CHS with 45° twist at top
python3 -m csf.utils.sp_csf  rectangular_hollow_section \
  --morph circular_hollow_section \
  --s0 d=200,b=150,t=10,r_out=15,n_r=8,z=0 \
  --s1 d=180,t=8,n=32,z=10 \
  --twist1=45 --out=rhs_to_chs_twist45.yaml \
   --gen-actions 
```

```bash
# Prismatic RHS with 70° pure twist along the member
python3 -m csf.utils.sp_csf  rectangular_hollow_section  \
 --s0 d=200,b=150,t=10,r_out=15,n_r=8,z=0  \
 --s1 d=150,b=100,t=10,r_out=15,n_r=8,z=10 \
 --twist1=70 --out=rhs_twist90.yaml \
 --gen-actions
```

### Manual offset (auto-align disabled)

Disable auto-alignment and control offsets explicitly.

```bash
python3 -m csf.utils.sp_csf rectangular_hollow_section \
  --morph circular_hollow_section \
  --s0 d=200,b=200,t=10,r_out=20,n_r=8,z=0 \
  --s1 d=150,t=8,n=32,z=10 \
  --no-align --dx1=25 --dy1=25 \
  --out=manual_offset.yaml \
  --gen-actions 
```

### Offset S1 relative to S0 (eccentric connection)

Both centroids aligned, then S1 shifted by an additional offset.

```bash
python3 -m csf.utils.sp_csf  circular_hollow_section \
  --s0 d=400,t=15,n=48,z=0 \
  --s1 d=300,t=12,n=48,z=10 \
  --dx1=50 --out=chs_eccentric.yaml \
  --gen-actions 
```

> When `auto_align=True` (default) and an explicit `--dx1` is provided, the
> explicit value is used directly - auto-alignment is skipped for S1.

---

## Python API Reference

### `sp_csf_yaml`

```python
"""
    pip install -e .
    pip install sectionproperties

or, if sectionproperties is installed through a CSF extra in your setup:

    pip install -e ".[sp]"
"""

from pathlib import Path

from sectionproperties.pre.library import (
    circular_hollow_section,
    rectangular_hollow_section,
)

from csf.utils.sp_csf import sp_to_csf_yaml


# ---------------------------------------------------------------------------
# Test 1: tapered RHS in native mode
# ---------------------------------------------------------------------------
#
# Same section family:
#
#     rectangular_hollow_section -> rectangular_hollow_section
#
# Because both sections are generated by the same sectionproperties constructor,
# the native vertex order is meaningful and should be preserved.
#
# Therefore:
#
#     morph_mode = "native"
#     n          = None
#
# This avoids unnecessary resampling and keeps the original sectionproperties
# point correspondence.

geometry_s0 = rectangular_hollow_section(
    d=300.0,
    b=200.0,
    t=12.0,
    r_out=20.0,
    n_r=8,
)

geometry_s1 = rectangular_hollow_section(
    d=200.0,
    b=150.0,
    t=8.0,
    r_out=15.0,
    n_r=8,
)

output_path_1 = Path("out_rhs_tapered_native.yaml")

result_path_1 = sp_to_csf_yaml(
    geometry_s0=geometry_s0,
    geometry_s1=geometry_s1,
    z0=0.0,
    z1=10.0,
    output_path=output_path_1,
    n=None,
    name="rhs",
    comment="Tapered RHS generated from sectionproperties using native mode",
    solid_weight=1.0,
    void_weight=0.0,
    indent=8,
    precision=6,
    dx0=None,
    dy0=None,
    dx1=None,
    dy1=None,
    twist0_deg=0.0,
    twist1_deg=0.0,
    auto_align=True,
    morph_mode="native",
)


# ---------------------------------------------------------------------------
# Test 2: RHS -> CHS morph in perimeter mode
# ---------------------------------------------------------------------------
#
# Different section families:
#
#     rectangular_hollow_section -> circular_hollow_section
#
# Because the two sections do not come from the same sectionproperties
# constructor, the native vertex order cannot be used directly.
#
# Therefore:
#
#     morph_mode = "perimeter"
#     n          = 96
#
# The exporter resamples each ring to the same number of vertices using
# perimeter-based arc-length sampling.

geometry_s0 = rectangular_hollow_section(
    d=300.0,
    b=200.0,
    t=12.0,
    r_out=20.0,
    n_r=8,
)

geometry_s1 = circular_hollow_section(
    d=180.0,
    t=8.0,
    n=64,
)

output_path_2 = Path("out_rhs_to_chs_perimeter.yaml")

result_path_2 = sp_to_csf_yaml(
    geometry_s0=geometry_s0,
    geometry_s1=geometry_s1,
    z0=0.0,
    z1=10.0,
    output_path=output_path_2,
    n=96,
    name="rhs_to_chs",
    comment="Morph RHS to CHS generated from sectionproperties using perimeter mode",
    solid_weight=1.0,
    void_weight=0.0,
    indent=8,
    precision=6,
    dx0=None,
    dy0=None,
    dx1=None,
    dy1=None,
    twist0_deg=0.0,
    twist1_deg=0.0,
    auto_align=True,
    morph_mode="perimeter",
)


# ---------------------------------------------------------------------------
# Test 3: RHS -> CHS morph with explicit offset and twist
# ---------------------------------------------------------------------------
#
# This is the same section-family morph as Test 2, but with explicit placement.
#
# Here auto_align is disabled because explicit offsets are supplied.
#
# Parameters:
#
#     dx0, dy0   : manual translation of S0
#     dx1, dy1   : manual translation of S1
#     twist0_deg : rotation of S0 in degrees CCW
#     twist1_deg : rotation of S1 in degrees CCW
#     auto_align : False
#
# This is useful when the relative placement of S0 and S1 is part of the
# intended CSF model.

geometry_s0 = rectangular_hollow_section(
    d=300.0,
    b=200.0,
    t=12.0,
    r_out=20.0,
    n_r=8,
)

geometry_s1 = circular_hollow_section(
    d=180.0,
    t=8.0,
    n=64,
)

output_path_3 = Path("out_rhs_to_chs_twisted_offset.yaml")

result_path_3 = sp_to_csf_yaml(
    geometry_s0=geometry_s0,
    geometry_s1=geometry_s1,
    z0=0.0,
    z1=10.0,
    output_path=output_path_3,
    n=96,
    name="rhs_to_chs_twisted",
    comment="Morph RHS to CHS with explicit offsets and twist",
    solid_weight=1.0,
    void_weight=0.0,
    indent=8,
    precision=6,
    dx0=0.0,
    dy0=0.0,
    dx1=25.0,
    dy1=10.0,
    twist0_deg=0.0,
    twist1_deg=30.0,
    auto_align=False,
    morph_mode="perimeter",
)


print("Generated CSF YAML files:")
print(f"  - {result_path_1}")
print(f"  - {result_path_2}")
print(f"  - {result_path_3}")
```

**Returns**: `Path` - the output file path.

**Centroid alignment behaviour**:

| `auto_align` | `dx1` provided | Result |
|---|---|---|
| `True` | No | S1 centroid auto-aligned to S0 centroid |
| `True` | Yes | Explicit `dx1` used, auto-align skipped for S1 |
| `False` | No | Raw SP coordinates, no offset |
| `False` | Yes | Explicit `dx1` applied |

---

## API Examples

### Prismatic circular hollow section

```python
from sp_csf import sp_csf_yaml
from sectionproperties.pre.library import circular_hollow_section

geom = circular_hollow_section(d=500, t=20, n=48)

sp_csf_yaml(
    geom, geom,
    z0=0.0, z1=30.0,
    n=48, name="pipe",
    output_path="pipe.yaml",
)
```

### Tapered I-section

```python
sp_to_csf_yaml(
    i_section(d=400, b=200, t_f=25, t_w=10, r=18, n_r=8),
    i_section(d=250, b=150, t_f=10, t_w=27,  r=12, n_r=128),
    z0=0.0, z1=30.0,
    n=256, name="beam",
    output_path="i_tapered.yaml",
)
```

### Morphing: RHS → CHS (centroids auto-aligned)

```python
from pathlib import Path
from csf.utils.sp_csf import sp_to_csf_yaml
from sectionproperties.pre.library import rectangular_hollow_section,circular_hollow_section


sp_to_csf_yaml(
    rectangular_hollow_section(d=200, b=150, t=10, r_out=15, n_r=8),
    circular_hollow_section(d=180, t=8, n=32),
    z0=0.0, z1=12.0,
    n=128, name="section",
    output_path="rhs_to_chs.yaml",
)
```

### Wind tower: square hollow → circular hollow

```python
from pathlib import Path
from csf.utils.sp_csf import sp_to_csf_yaml
from sectionproperties.pre.library import rectangular_hollow_section,circular_hollow_section


sp_to_csf_yaml(
    rectangular_hollow_section(d=4000, b=4000, t=30, r_out=300, n_r=16),
    circular_hollow_section(d=2500, t=18, n=48),
    z0=0.0, z1=70000.0,
    n=96, name="tower",
    comment="Wind tower - square base tapering to circular top",
    output_path="wind_tower.yaml",
)
```

### Morph with twist

```python
from sp_csf import sp_csf_yaml
from sectionproperties.pre.library import rectangular_hollow_section, circular_hollow_section

sp_csf_yaml(
    rectangular_hollow_section(d=200, b=150, t=10, r_out=15, n_r=8),
    circular_hollow_section(d=180, t=8, n=32),
    z0=0.0, z1=10.0,
    n=64, name="section",
    twist1_deg=45.0,
    output_path="rhs_to_chs_twist45.yaml",
)
```

### Prismatic section with pure twist

```python
from pathlib import Path
from csf.utils.sp_csf import sp_to_csf_yaml
from sectionproperties.pre.library import rectangular_hollow_section,circular_hollow_section

geomS0 = rectangular_hollow_section(
    d=300.0,
    b=200.0,
    t=12.0,
    r_out=20.0,
    n_r=8,
)

geomS1 = rectangular_hollow_section(
    d=200.0,
    b=100.0,
    t=8.0,
    r_out=20.0,
    n_r=8,
)


sp_to_csf_yaml(
    geomS0, geomS1,
    z0=0.0, z1=10.0,
    n=128, name="section",
    twist1_deg=90.0,
    output_path="rhs_twist90.yaml",
)
```

### Manual centroid control

```python
from pathlib import Path
from csf.utils.sp_csf import sp_to_csf_yaml,geometry_centroid
from sectionproperties.pre.library import rectangular_hollow_section,circular_hollow_section

geom_s0 = rectangular_hollow_section(d=200, b=200, t=10, r_out=20, n_r=8)
geom_s1 = circular_hollow_section(d=150, t=8, n=32)

# Inspect centroids before writing

cx0, cy0 = geometry_centroid(geom_s0)
cx1, cy1 = geometry_centroid(geom_s1)
print(f"S0 centroid: ({cx0:.3f}, {cy0:.3f})")
print(f"S1 centroid: ({cx1:.3f}, {cy1:.3f})")

# Disable auto-align, apply manual offset
sp_to_csf_yaml(
    geom_s0, geom_s1,
    z0=0.0, z1=10.0,
    n=64, name="section",
    auto_align=False,
    dx1=25.0, dy1=25.0,
    output_path="manual_offset.yaml",
)
```

---

## Supported section types

All sections from `sectionproperties.pre.library` that do not require material
arguments (`conc_mat`, `steel_mat`) are supported. The full list:

```
angle_section            box_girder_section       bulb_section
cee_section              channel_section          circular_hollow_section
circular_section         circular_section_by_area cruciform_section
elliptical_hollow_section elliptical_section      i_girder_section
i_section                mono_i_section           nastran_bar
nastran_box              nastran_box1             nastran_chan
nastran_chan1            nastran_chan2             nastran_cross
nastran_dbox             nastran_fcross           nastran_gbox
nastran_h                nastran_hat              nastran_hat1
nastran_hexa             nastran_i                nastran_i1
nastran_l                nastran_rod              nastran_tee
nastran_tee1             nastran_tee2             nastran_tube
nastran_tube2            nastran_zed              polygon_hollow_section
rectangular_hollow_section rectangular_section   super_t_girder_section
tapered_flange_channel   tapered_flange_i_section tee_section
triangular_radius_section triangular_section      zed_section
```

---

# Rules and constraints

**Topology rule**: S0 and S1 must have the same number of polygons and the same
number of holes per polygon. A solid section cannot morph to a hollow one.

---

**Discretisation rule**: for tapered sections (same section type), `n_r` and `n`
must be identical in `--s0` and `--s1` to guarantee the same vertex count after
SP generates the geometry.

---

**Morph mode**: when `--morph` is used, vertex correspondence is established
purely by arc-length position, starting from the positive x semi-axis. The
quality of the morph depends on how similar the two shapes are. For very
different shapes, increase `n` to capture both contours accurately.

### `sp_csf.py` API distinction

`sp_csf.py` exposes two different API levels.

### 1. `sp_to_csf_yaml(...)`

This is the geometry-based API.

It receives already-built `sectionproperties` geometry objects:

```python
sp_to_csf_yaml(
    geometry_s0=geometry_s0,
    geometry_s1=geometry_s1,
    ...
)
```

Supported `morph_mode` values:

```text
native
perimeter
```

Use this when the geometries have already been created in Python.

### 2. `sp_sections_to_csf_yaml(...)`

This is the section-name API.

It receives section names and parameter dictionaries:

```python
sp_sections_to_csf_yaml(
    section_s0="rectangular_section",
    params_s0={...},
    section_s1="circular_section",
    params_s1={...},
    ...
)
```

Supported `morph_mode` values:

```text
native
perimeter
feature
```

Use this when the API must build the `sectionproperties` geometries itself.

## Key difference

`feature` mode needs semantic section information, such as:

```text
i_section
tee_section
channel_section
rectangular_section
angle_section
```

That information is available in `sp_sections_to_csf_yaml(...)`.

It is not available in `sp_to_csf_yaml(...)`, because that function receives only already-built geometry objects.

## Summary

```text
sp_to_csf_yaml           -> geometry objects      -> native, perimeter
sp_sections_to_csf_yaml  -> section names + args  -> native, perimeter, feature
```

```
"""
case1_sp_to_csf_yaml_flat.py

Case 1: geometry-based API.

This example uses sp_to_csf_yaml(...).

The sectionproperties geometries are created first, then passed to CSF.
No helper functions are used.
"""

from sectionproperties.pre.library import rectangular_section

from csf.utils.sp_csf import sp_to_csf_yaml


geometry_s0 = rectangular_section(
    d=200.0,
    b=100.0,
)

geometry_s1 = rectangular_section(
    d=300.0,
    b=150.0,
)

result_path = sp_to_csf_yaml(
    geometry_s0=geometry_s0,
    geometry_s1=geometry_s1,
    z0=0.0,
    z1=10.0,
    output_path="case1_sp_to_csf_yaml.yaml",
    n=None,
    name="rect",
    comment="Case 1: geometry-based API",
    solid_weight=1.0,
    void_weight=0.0,
    indent=8,
    precision=6,
    dx0=None,
    dy0=None,
    dx1=None,
    dy1=None,
    twist0_deg=0.0,
    twist1_deg=0.0,
    auto_align=True,
    morph_mode="native",
)

print(f"Written: {result_path}")
```

```
"""
case2_sp_sections_to_csf_yaml_flat.py

Case 2: section-name API.

This example uses sp_sections_to_csf_yaml(...).

The API receives section names and parameter dictionaries.
No helper functions are used.
"""

from csf.utils.sp_csf import sp_sections_to_csf_yaml


result_path = sp_sections_to_csf_yaml(
    section_s0="rectangular_section",
    params_s0={
        "d": 200.0,
        "b": 100.0,
        "z": 0.0,
    },
    section_s1="rectangular_section",
    params_s1={
        "d": 300.0,
        "b": 150.0,
        "z": 10.0,
    },
    output_path="case2_sp_sections_to_csf_yaml.yaml",
    n=None,
    name="rect",
    comment="Case 2: section-name API",
    solid_weight=1.0,
    void_weight=0.0,
    indent=8,
    precision=6,
    dx0=None,
    dy0=None,
    dx1=None,
    dy1=None,
    twist0_deg=0.0,
    twist1_deg=0.0,
    auto_align=True,
    morph_mode="native",
)

print(f"Written: {result_path}")
```







---

**Hole matching**: if S0 has one hole (hollow section), S1 must also have
exactly one hole. The exterior ring morphs to the exterior ring; each hole
morphs to the corresponding hole by index.

**Twist note**: twist does not affect vertex correspondence - it is applied
after resampling. A twisted prismatic section has the same cross-sectional
area at every station; the twist is a rigid-body rotation, not a shape change.

---

## Output format

The generated YAML is a standard CSF geometry file, ready to use with any
CSF tool:


### Analysis note

`sp_csf.py` is an export bridge, not an analysis wrapper.

It does not call the `sectionproperties` analysis API. Geometry analysis remains
on the `sectionproperties` side, through `Section(...)` and its calculation
methods.

```bash
# Analyse with csf_sp
python -m csf.utils.csf_sp --yaml=wind_tower.yaml --z=35000 --plot

# Run CSF actions
csf-actions wind_tower.yaml actions.yaml

# Load in Python
from csf.utils.csf_sp import load_yaml, analyse
field = load_yaml("wind_tower.yaml")
sec = analyse(field, z=35000.0)
print(sec.get_ea())
```

---

*sp_csf.py - part of the [continuous-section-field (csfpy)](https://github.com/giovanniboscu/continuous-section-field) ecosystem*
