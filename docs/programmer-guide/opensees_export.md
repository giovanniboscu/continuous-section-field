# OpenSees Export Guide

## Purpose

This section explains how the CSF OpenSees export example works and how to reuse it in your own workflow.

The example is split into two scripts:

* `example/csf_opensees_lab.py`: builds a `ContinuousSectionField` and writes the OpenSees geometry data file.
* `example/csf_opensees_check.py`: reads that exported file and uses it as input data for an OpenSeesPy model.

In the provided check example, the structural verification problem is a cantilever beam with a concentrated tip load. The goal of `csf_opensees_check.py` is not to define the only valid OpenSees workflow, but to provide a clear template for reading `geometry.tcl` and building an OpenSeesPy model from CSF-exported station data.

---

## Win11 note: installing OpenSeesPy before running the check script

If you are using Windows 11 and `openseespy` is not installed yet, `csf_opensees_check.py` cannot run, because the script imports OpenSeesPy directly:

```python
import openseespy.opensees as ops
```

Before running the check example, install OpenSeesPy by following this setup guide:

[OpenSeesPy setup for Win11](./openseespy_win11_setup.md)

If you are working inside a virtual environment, activate that environment first and then run the same commands inside it.

---

## 1. Export side: `csf_opensees_lab.py`

### What this script does

The exporter script creates a non-prismatic CSF section field, evaluates it, plots it, and writes an OpenSees-compatible geometry data file.

The main output file is:

```python
geometryfile = "geometry.tcl"
```

### Step 1 - Define the start and end polygons

The script defines polygons at `z = 0` and `z = L`.

Example:

```python
poly_top_start = Polygon(
    vertices=(
        Pt(-b/2,  0.0),
        Pt( b/2,  0.0),
        Pt( b/2,  h/2),
        Pt(-b/2,  h/2),
    ),
    weight=E,
    name="upperpart@wall",
)
```

and:

```python
poly_bottom_start = Polygon(
    vertices=(
        Pt(-b/2, -h/2),
        Pt( b/2, -h/2),
        Pt( b/2,  0.0),
        Pt(-b/2,  0.0),
    ),
    weight=E,
    name="lowerpart@wall",
)
```

The same pattern is used for the end section:

```python
poly_top_end = Polygon(...)
poly_bottom_end = Polygon(...)
```

In this example, the upper part remains constant while the lower part changes height at the end section.

The polygon weights belong to the CSF model. Therefore, when the OpenSees geometry file is exported, the resulting station properties already contain the CSF weights used at export time.

### Step 2 - Build the two sections and the continuous field

```python
L = 10.0

s0 = Section(polygons=(poly_bottom_start, poly_top_start), z=0.0)
s1 = Section(polygons=(poly_bottom_end, poly_top_end), z=L)

section_field = ContinuousSectionField(section0=s0, section1=s1)
```

This is the core CSF object used to evaluate sections along the beam axis.

### Step 3 - Evaluate and inspect one section

The script evaluates one section and prints a full analysis:

```python
zsec_val = 10.0
sec_mid = section_field.section(zsec_val)

full_analysis = section_full_analysis(sec_mid)
section_print_analysis(full_analysis, fmt=".5f")
```

This is useful for quick verification before exporting.

### Step 4 - Plot geometry and section properties

The script uses `Visualizer` to inspect both geometry and property evolution:

```python
viz = Visualizer(section_field)
viz.plot_section_2d(z=0, show_vertex_ids=True, show_weights=False)
viz.plot_section_2d(z=10, show_vertex_ids=True, show_weights=False)
viz.plot_volume_3d(line_percent=100.0, seed=1)

vizprop = Visualizer(section_field)
vizprop.plot_properties(['Cy', 'Ix', 'Iy', 'Ip'])
```

These plots are diagnostic only. They are not required for the OpenSees export itself.

### Step 5 - Write the OpenSees data file

The actual export is done here:

```python
write_opensees_geometry(
    section_field,
    E_ref=1,
    nu=0,
    n_points=10,
    filename=geometryfile,
)
```

This call writes `geometry.tcl`.

The exported section quantities are already evaluated by CSF using the weights present in the `ContinuousSectionField` at export time.

### Important note on `set_weight_laws(...)`

In the provided script, the export is executed before the later call to `set_weight_laws(...)`:

```python
write_opensees_geometry(section_field, E_ref=1, nu=0, n_points=10, filename=geometryfile)

section_field.set_weight_laws([
    f"upperpart,upperpart : 7.85",
    f"lowerpart,lowerpart: 2.5"
])
```

This means that the generated `geometry.tcl` reflects the state of `section_field` at the moment of the export.

If a different weighted state must be used in the OpenSees file, the corresponding weights or weight laws must be applied before calling:

```python
write_opensees_geometry(...)
```

A later `set_weight_laws(...)` call does not modify an already-written `geometry.tcl`.

---

## 2. What `geometry.tcl` is

In this workflow, `geometry.tcl` is treated as a data file, not as a Tcl script to be sourced blindly.

The reader in `csf_opensees_check.py` expects records such as:

```tcl
# CSF_Z_STATIONS: z0 ... zN-1
geomTransf Linear 1 vx vy vz
section CSF tag A Iz Iy J xc yc
```

The meaning is:

* `CSF_Z_STATIONS`: exact station coordinates exported by CSF.
* `geomTransf Linear`: orientation vector used to reconstruct the local basis.
* `section CSF ...`: one station record per exported CSF section.
* `xc yc`: centroid offsets in the local section plane.

The `node` lines in `geometry.tcl`, if present, are treated as informational only by the Python reader.

The check script reads `geometry.tcl` as CSF data and then creates OpenSeesPy objects from that data.

---

## 3. Section stiffness convention

The OpenSees check example uses the following convention:

```python
E_OPENSEES = 1.0
G_OPENSEES = 1.0
```

This is intentional.

CSF exports station properties that are already equivalent with respect to the weights used in the CSF model. Therefore, the OpenSees `Elastic` section is created with unit scalar carriers:

```python
ops.section(
    "Elastic",
    int(s.tag),
    float(E_OPENSEES),
    float(s.A),
    float(s.Iz),
    float(s.Iy),
    float(G_OPENSEES),
    float(s.J),
)
```

With `E_OPENSEES = 1.0` and `G_OPENSEES = 1.0`, OpenSees uses directly:

```text
E*A  = A
E*Iz = Iz
E*Iy = Iy
G*J  = J
```

In this interface, `A`, `Iz`, `Iy`, and `J` are the CSF-exported station quantities. They must not be re-multiplied by physical `E` and `G` in OpenSees.

### Why this matters

OpenSees `section Elastic` accepts one scalar `E` and one scalar `G` for the whole section. It does not know the internal CSF zone-wise weights used to build the exported section quantities.

Therefore, the current workflow is:

```text
CSF applies the section weights
CSF exports equivalent station quantities
OpenSees receives those quantities with E = 1 and G = 1
```

Do not mix this convention with a second material application in OpenSees. Doing so would double-count the material contribution.

A different workflow would be possible only if CSF exported purely geometric properties with unit weights. In that alternative case, OpenSees would need physical `E` and `G`. That is not the convention used by the current example.

---

## 4. Reader side: `csf_opensees_check.py`

## What this script is for

The check script is a template reader and builder.

Its first purpose is to parse `geometry.tcl` into a structured Python object. Its second purpose is to show one possible way to create an OpenSeesPy model using only the sections exported by CSF.

Minimal parser use:

```python
geom = parse_csf_geometry("geometry.tcl")
# geom.z_stations, geom.sections, geom.vecxz are now available
```

Most users only need the parser and can replace the OpenSeesPy builder with their own modelling logic.

### Parsed data structures

Each station section is represented as:

```python
@dataclass
class SectionCSF:
    tag: int
    A: float
    Iz: float
    Iy: float
    J: float
    xc: float = 0.0
    yc: float = 0.0
```

The full parsed geometry is stored in:

```python
@dataclass
class GeometryCSF:
    L: float
    n_stations: int
    vecxz: np.ndarray
    sections: List[SectionCSF]
    file_node1: Optional[np.ndarray] = None
    file_node2: Optional[np.ndarray] = None
    z_stations: Optional[List[float]] = None
```

### What the parser reads

The parser reads:

* optional beam length from the header;
* optional `CSF_Z_STATIONS`;
* `geomTransf Linear`;
* all `section CSF` records;
* optional `node` lines, treated as informational only.

The parser does not read `section Elastic` records from `geometry.tcl`. The OpenSees `Elastic` sections are created later inside the Python builder.

### Station coordinates

The preferred source for station coordinates is:

```tcl
# CSF_Z_STATIONS: z0 ... zN-1
```

The relevant settings are:

```python
PREFER_CSF_Z_STATIONS = True
ALLOW_FALLBACK_IF_MISSING_Z_STATIONS = True
DISC = "lobatto"  # "lobatto" or "uniform"
```

If `CSF_Z_STATIONS` is present, the script uses the exact station coordinates exported by CSF.

If `CSF_Z_STATIONS` is missing and fallback is enabled, the script generates stations using either Gauss-Lobatto or uniform spacing. This fallback is useful for debugging, but it does not provide strict reproducibility with respect to the original CSF export.

---

## 5. Building the OpenSees model from the exported data

### Minimal usage

The minimum usage pattern is:

```python
geom = parse_csf_geometry("geometry.tcl")
uy = run_csf_opensees(geom, verbose=True)
```

The `main()` function in the script does exactly that:

```python
def main() -> None:
    geom = parse_csf_geometry(GEOMETRY_FILE)
    uy = run_csf_opensees(geom, verbose=True)
    print(f"\nUy_tip = {uy:.6e} (in model length units)")
```

### Local basis and centroid axis

The script first computes the station coordinates:

```python
z_stations, using_csf_z = _compute_station_z(geom)
```

Then it builds a local orthonormal basis from the member axis and the exported `vecxz`:

```python
e1, e2, e3 = build_local_basis(axis, geom.vecxz)
```

Centroid offsets from the file are mapped into 3D coordinates as:

```python
cen_xyz = ref_xyz + float(s.xc) * e1 + float(s.yc) * e2
```

The reader does not guess centroid positions. It reconstructs them from the exported station data.

### Reference nodes and centroid nodes

The builder creates:

* reference nodes, used for boundary conditions and loads;
* centroid nodes, used by the beam elements;
* rigid beam links between reference nodes and centroid nodes.

The rigid links require the OpenSees constraints handler:

```python
ops.constraints("Transformation")
```

This topology allows the model to preserve centroid offsets while still applying supports and loads at reference-axis nodes.

---

## 6. Integration strategy

The script supports three integration modes:

```python
INTEGRATION_MODE = "auto"  # "auto" | "member_lobatto" | "segment_endpoints"
```

### `auto`

In `auto` mode, the script checks whether centroid offsets vary along the member.

Centroid variation is detected from all stations:

```python
xc_all = np.array([float(s.xc) for s in secs], dtype=float)
yc_all = np.array([float(s.yc) for s in secs], dtype=float)

tilt = (xc_all.max() - xc_all.min() > TILT_TOL) or (
    yc_all.max() - yc_all.min() > TILT_TOL
)
```

If centroid offsets are constant, the script uses one element over the full member with N-point Gauss-Lobatto integration.

If centroid offsets vary, the script switches to segmented elements between consecutive stations.

### `member_lobatto`

This mode forces a single `forceBeamColumn` element over the full member.

It is allowed only when centroid offsets are constant. If centroid offsets vary, the script raises an error.

This mode also requires the exported stations to match true Gauss-Lobatto nodes. The check is strict:

```python
max_diff = float(np.max(np.abs(s_from_file - s_theory)))

if max_diff >= LOBATTO_MATCH_TOL:
    raise ValueError(...)
```

No trapezoid fallback is used in `member_lobatto`.

The section tags used at integration points come directly from `geometry.tcl`.

### `segment_endpoints`

This mode always creates one element per station interval.

Each segment uses the two end sections only:

```python
ops.beamIntegration(
    "UserDefined",
    intTag,
    2,
    secI, secJ,
    0.0, 1.0,
    0.5, 0.5,
)
```

This corresponds to endpoint sampling on each station interval.

### Why segmentation is used when centroid offsets vary

A single `forceBeamColumn` element has only two element nodes. It cannot represent a varying centroid axis unless that variation is discarded.

When centroid offsets vary along the member, the script creates nodes at every station so that the centroid axis is represented explicitly.

This is why `auto` uses:

* one full-member element when centroid offsets are constant;
* station-to-station segmented elements when centroid offsets vary.

---

## 7. No invented intermediate sections

The check script does not create new interpolated section records for internal integration points.

The sections used by the OpenSees builder come from `geometry.tcl`.

In member-level Lobatto mode, the full-member integration points correspond to the exported CSF stations.

In segmented endpoint mode, each element uses the two station sections at its ends.

This keeps the OpenSeesPy builder tied to the data exported by CSF.

---

## 8. Torsion

OpenSees `section Elastic` uses a single scalar `J` in `G*J`.

In this workflow:

```text
G = 1
G*J = J
```

Therefore, the `J` value exported by CSF must already be the intended torsional quantity for the station.

The trailing comment in `geometry.tcl`, if present, is informational only. The parser reads the numeric `J` field from the `section CSF` record.

---

## 9. Why the check example uses a cantilever with a concentrated load

The example verification problem is intentionally simple:

```python
FY_TIP = -50000.0
```

The model is fixed at the base reference node and loaded at the tip reference node:

```python
ops.fix(int(base_ref_node), 1, 1, 1, 1, 1, 1)

ops.timeSeries("Linear", 1)
ops.pattern("Plain", 1, 1)
ops.load(int(tip_ref_node), 0.0, float(FY_TIP), 0.0, 0.0, 0.0, 0.0)
```

This is not intended as a full structural benchmark. It is a compact and readable example that demonstrates:

* how to parse the CSF export;
* how to reconstruct stations and local axes;
* how to define OpenSees sections from exported CSF station data;
* how to build an element topology from exported stations;
* how to run a simple static check.

`csf_opensees_check.py` should therefore be read primarily as a template for reading `geometry.tcl`, not as a fixed solver workflow.

---

## 10. Typical workflow

A typical programmer workflow is:

1. Build a `ContinuousSectionField` in CSF.
2. Assign the intended CSF weights or weight laws before export.
3. Export station-wise OpenSees data with `write_opensees_geometry(...)`.
4. Read the exported `geometry.tcl` with `parse_csf_geometry(...)`.
5. Use `run_csf_opensees(...)` as a starting template.
6. Replace the example cantilever loads, supports, and analysis settings with your own model logic.

Minimal sequence:

```python
# Export side
write_opensees_geometry(
    section_field,
    E_ref=1,
    nu=0,
    n_points=10,
    filename="geometry.tcl",
)

# Read/build side
geom = parse_csf_geometry("geometry.tcl")
uy = run_csf_opensees(geom, verbose=True)
```

---

## 11. What you should customize in real projects

In real use, the parts most likely to be customized are:

* support conditions;
* load definition;
* integration mode;
* element assembly strategy;
* output requests;
* post-processing;
* whether to use `run_csf_opensees(...)` directly or replace it with a project-specific OpenSeesPy builder.

The part that should remain stable is the interface:

```text
CSF exports station data to geometry.tcl
Python parses section CSF records
OpenSees sections are created from those exported station records
OpenSees uses E = 1 and G = 1 because the exported quantities are already CSF-equivalent
```

This separation keeps the CSF export deterministic and traceable while allowing the OpenSees builder to evolve independently.

---

## 12. Common mistakes to avoid

### Do not source `geometry.tcl` blindly as Tcl

In this workflow, `geometry.tcl` is a data file. The Python reader parses it and builds the OpenSeesPy model.

### Do not expect `section Elastic` records in `geometry.tcl`

The exported records read by the current parser are:

```tcl
section CSF tag A Iz Iy J xc yc
```

The OpenSees `Elastic` sections are created later by the Python builder.

### Do not reapply physical `E` and `G` in OpenSees

The current CSF export already includes the effect of the weights used in the CSF model.

The OpenSees builder therefore uses:

```python
E_OPENSEES = 1.0
G_OPENSEES = 1.0
```

Applying physical `E` and `G` again in OpenSees would double-count the material contribution.

### Do not apply `set_weight_laws(...)` after export expecting it to change `geometry.tcl`

Only the state of `section_field` at the moment of:

```python
write_opensees_geometry(...)
```

is written to `geometry.tcl`.

### Do not use `member_lobatto` with varying centroid offsets

A single element cannot represent a varying centroid axis. Use `auto` or `segment_endpoints` when centroid offsets vary along the member.

---

## 13. Minimal example snippets

### Export

```python
section_field = ContinuousSectionField(section0=s0, section1=s1)

write_opensees_geometry(
    section_field,
    E_ref=1,
    nu=0,
    n_points=10,
    filename="geometry.tcl",
)
```

### Read

```python
geom = parse_csf_geometry("geometry.tcl")
```

### Run the example check

```python
uy = run_csf_opensees(geom, verbose=True)
print(f"Uy_tip = {uy:.6e}")
```

These three steps summarize the example pipeline.
