# OpenSees Export Guide

## Purpose

This section explains how the CSF OpenSees export example works and how to reuse it in your own workflow.

The example is split into two scripts:

- `example/csf_opensees_lab.py`: builds a `ContinuousSectionField` and writes the OpenSees geometry data file.
- `example/csf_opensees_check.py`: shows how to read that exported file and use it as input for an OpenSeesPy model.

In the provided check example, the structural verification problem is a **cantilever beam with a concentrated tip load**. The goal of `csf_opensees_check.py` is not to define the only valid OpenSees workflow, but to provide a **clear template for reading `geometry.tcl` and building a model from it**.

---

## Win11 note: installing OpenSeesPy before running the check script

If you are using **Windows 11** and `openseespy` is not installed yet, `csf_opensees_check.py` cannot run, because the script imports OpenSeesPy directly:

```python
import openseespy.opensees as ops
```

Before running the check example, install OpenSeesPy by following this setup guide:

[OpenSeesPy setup for Win11](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/opensees_win11_setup.md)

Typical commands on Windows 11 are:

```powershell
py -m pip install openseespy
py csf_opensees_check.py
```

If you are working inside a virtual environment, activate that environment first and then run the same commands inside it.

---

## 1. Export side: `csf_opensees_lab.py`

### What this script does

The exporter script creates a simple non-prismatic section field, evaluates it, plots it, and writes an OpenSees-compatible geometry file.

The main output file is:

```python
geometryfile = "geometry.tcl"
```

### Step 1 - Define the start and end polygons

The script defines polygons at `z = 0` and `z = L`.

```python
poly_top_start = Polygon(
    vertices=(
        Pt(-b/2,  0.0),
        Pt( b/2,  0.0),
        Pt( b/2,  h/2),
        Pt(-b/2,  h/2),
    ),
    weight=1,
    name="upperpart@wall",
)

poly_bottom_start = Polygon(
    vertices=(
        Pt(-b/2, -h/2),
        Pt( b/2, -h/2),
        Pt( b/2,  0.0),
        Pt(-b/2,  0.0),
    ),
    weight=1,
    name="lowerpart@wall",
)
```

The same pattern is used for the end section:

```python
poly_top_end = Polygon(...)
poly_bottom_end = Polygon(...)
```

In this example, the upper part remains constant while the lower part changes height at the end section.

### Step 2 - Build the two sections and the continuous field

```python
L = 10.0

s0 = Section(polygons=(poly_bottom_start, poly_top_start), z=0.0)
s1 = Section(polygons=(poly_bottom_end, poly_top_end), z=L)

section_field = ContinuousSectionField(section0=s0, section1=s1)
```

This is the core CSF object used for interpolation along the beam axis.

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

### Important note

In the provided script, the export is executed **before** the later call to `set_weight_laws(...)`:

```python
write_opensees_geometry(section_field, E_ref=1, nu=0, n_points=10, filename=geometryfile)

section_field.set_weight_laws([
    f"upperpart,upperpart : 7.85",
    f"lowerpart,lowerpart: 2.5"
])
```

This means that the generated `geometry.tcl` reflects the state of `section_field` **at export time**.
If you want the exported OpenSees file to include a different weighted state, the weight laws must be applied **before** calling `write_opensees_geometry(...)`.

---

## 2. What `geometry.tcl` is

In this workflow, `geometry.tcl` is treated as a **data file**, not as a Tcl script to be sourced blindly.

The reader in `csf_opensees_check.py` expects records such as:

```tcl
# CSF_Z_STATIONS: z0 z1 ... zN-1
geomTransf Linear 1 vx vy vz
section Elastic tag E A Iz Iy G J Cx Cy
```

The meaning is:

- `CSF_Z_STATIONS`: exact station coordinates exported by CSF
- `geomTransf Linear`: orientation vector used to reconstruct the local basis
- `section Elastic ...`: one station record per exported section
- trailing `Cx Cy`: centroid offsets in the local section plane

The check script explicitly states that `node` lines in the file are treated as informational only.

---

## 3. Reader side: `csf_opensees_check.py`

## What this script is for

The check script is a **template reader and builder**.

Its first purpose is to parse `geometry.tcl` into a structured Python object.
Its second purpose is to show one possible way to create an OpenSeesPy model using only the sections exported by CSF.

The script says this directly:

```python
geom = parse_csf_geometry("geometry.tcl")
# geom.z_stations, geom.sections, geom.vecxz are now available
```

### Parse the exported file

The parser is:

```python
def parse_csf_geometry(file_path: str) -> GeometryCSF:
    ...
```

It reads:

- beam length from the header, when available
- `CSF_Z_STATIONS`
- the `geomTransf Linear` vector
- all `section Elastic` lines
- optional node lines

It stores the result in:

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

Each station section is represented as:

```python
@dataclass
class SectionCSF:
    tag: int
    E: float
    A: float
    Iz: float
    Iy: float
    G: float
    J: float
    xc: float = 0.0
    yc: float = 0.0
```

This is the key interface between the CSF export and the OpenSees builder.

---

## 4. Building the OpenSees model from the exported data

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

### Material handling

The builder supports two material modes:

```python
MATERIAL_INPUT_MODE = "override"  # "override" or "from_file"
E_OVERRIDE = 2.1e11
NU_OVERRIDE = 0.30
G_OVERRIDE = None
```

The function that applies the policy is:

```python
def get_EG(sec: SectionCSF) -> Tuple[float, float]:
    ...
```

So:

- `from_file`: use `E` and `G` from `geometry.tcl`
- `override`: use constant values defined in the Python script

In both cases, `A`, `Iz`, `Iy`, `J`, `xc`, and `yc` are always read from the exported file.

### Integration strategy

The script supports three modes:

```python
INTEGRATION_MODE = "auto"  # "auto" | "member_lobatto" | "segment_endpoints"
```

#### `auto`

- If centroid offsets do not vary, the script uses one element over the full member.
- If centroid offsets vary, it switches to segmented elements between stations.

#### `member_lobatto`

- Forces a single `forceBeamColumn` element.
- Requires constant centroid offsets.
- Requires exported stations to match true Gauss-Lobatto nodes.

#### `segment_endpoints`

- Always creates one element per station interval.
- Uses two-point endpoint integration per segment.

This logic is implemented inside:

```python
def run_csf_opensees(geom: GeometryCSF, verbose: bool = True) -> float:
    ...
```

---

## 5. Why the check example uses a cantilever with a concentrated load

The example verification problem is intentionally simple:

```python
FY_TIP = -50000.0
```

The model is fixed at the base and loaded at the tip reference node:

```python
ops.fix(int(base_ref_node), 1, 1, 1, 1, 1, 1)

ops.timeSeries("Linear", 1)
ops.pattern("Plain", 1, 1)
ops.load(int(tip_ref_node), 0.0, float(FY_TIP), 0.0, 0.0, 0.0, 0.0)
```

This is not intended as a full structural benchmark. It is a compact and readable example that demonstrates:

- how to parse the CSF export
- how to reconstruct stations and local axes
- how to define OpenSees sections from file data
- how to build an element topology from exported stations
- how to run a simple static check

That is why `csf_opensees_check.py` should be read primarily as a **template for reading `geometry.tcl`**, not as a fixed solver workflow.

---

## 6. How the builder reconstructs the beam axis and centroid axis

The script first computes station coordinates:

```python
z_stations, using_csf_z = _compute_station_z(geom)
```

Then it builds a local orthonormal basis from the member axis and the exported `vecxz`:

```python
e1, e2, e3 = build_local_basis(axis, geom.vecxz)
```

Centroid offsets from the file are then mapped into 3D coordinates:

```python
cen_xyz = ref_xyz + float(s.xc) * e1 + float(s.yc) * e2
```

This is an important detail: the reader does not guess centroid positions. It reconstructs them from the exported station data.

---

## 7. Typical workflow

A typical programmer workflow is:

1. Build a `ContinuousSectionField` in CSF.
2. Export station-wise OpenSees data with `write_opensees_geometry(...)`.
3. Read the exported `geometry.tcl` with `parse_csf_geometry(...)`.
4. Use `run_csf_opensees(...)` as a starting template.
5. Replace the example cantilever loads, supports, and analysis settings with your own model logic.

Minimal sequence:

```python
# Export side
write_opensees_geometry(section_field, E_ref=1, nu=0, n_points=10, filename="geometry.tcl")

# Read/build side
geom = parse_csf_geometry("geometry.tcl")
uy = run_csf_opensees(geom, verbose=True)
```

---

## 8. What you should customize in real projects

In real use, the parts most likely to be customized are:

- support conditions
- load definition
- material override policy
- integration mode
- element assembly strategy
- output requests

The part that should remain stable is the interface:

- CSF exports station data to `geometry.tcl`
- the Python reader parses that file
- OpenSees sections are created directly from those exported station records

This separation is useful because it keeps the CSF export deterministic and traceable, while allowing the OpenSees builder to evolve independently.

---

## 9. Recommended wording for the Programmer Guide

`csf_opensees_lab.py` creates the `geometry.tcl` data file starting from a `ContinuousSectionField`. The script defines the geometry, evaluates the section field, and exports station-wise section data for OpenSees.

`csf_opensees_check.py` is a reference reader for that exported file. In the provided example, the verification problem is a cantilever beam under a concentrated tip load. The purpose of the script is to provide a practical template for parsing `geometry.tcl` and building an OpenSeesPy model from the exported CSF stations.

---

## 10. Minimal example snippets

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

These three steps summarize the whole example pipeline.
