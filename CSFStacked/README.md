# CSFStacked — Stack multiple `ContinuousSectionField` segments

`CSFStacked` is a small container that **impila (stacks)** multiple `ContinuousSectionField` objects along the **global** member axis `z`, providing:

- deterministic **global z → segment dispatch**
- explicit handling of **internal junctions**
- optional strict **contiguity** validation (no overlaps, no gaps)
- convenience wrappers for `section(z)` and `section_full_analysis(z)`
- a global 3D plotting helper (`plot_volume_3d_global`)

This is useful when a member is naturally described by **multiple consecutive CSF fields** (e.g., left taper + constant middle + right taper, segmented blades, repairs/patch segments, etc.).

---

## 1) Data model

### SegmentSpec (optional builder input)

`SegmentSpec` is a lightweight input record used by `build_from_specs()`:

- `tag`: string identifier
- `z0`, `z1`: global interval bounds
- `polygons_s0`, `polygons_s1`: polygons at `z0` and `z1`

Notes:
- Polygon **names** should be consistent between `s0` and `s1` to support side-surface pairing.
- For each polygon name, **vertex count** must match between `s0` and `s1`.

### StackSegment (runtime)
Internally, each segment is stored as:

- `tag`
- `z_start`, `z_end`
- `field`: the `ContinuousSectionField` for that interval

---

## 2) Interval and junction policy

`CSFStacked` enforces a deterministic interval ownership rule:

- first segment: **[z_start, z_end]**
- any other segment: **(z_start, z_end]**

Consequences:
- global left edge and global right edge are included
- **internal junctions belong to the segment on the left** by default

If you need the right-side segment at a junction, you can request it explicitly through `junction_side="right"` in `field_at()`, `section()`, and `section_full_analysis()`.

---

## 3) Building a stack

There are two common ways to build a stack.

### A) Append pre-built fields (most common)

```python
from csf import CSFStacked
from csf.io.csf_reader import CSFReader

# Example: load 2 independent CSF fields from YAML
f0 = CSFReader().read_file("stacked_0.yaml").field
f1 = CSFReader().read_file("stacked_1.yaml").field

stack = CSFStacked(eps_z=1e-10)
stack.append(f0)
stack.append(f1)

# Optional: ensure no overlaps and (optionally) strict contiguity
stack.validate_contiguity(require_contiguity=True)
```

What `append(field)` does:
- reads `z_start = field.s0.z`, `z_end = field.s1.z`
- checks `z_end > z_start`
- appends the segment and keeps segments sorted by `z_start`

### B) Build from polygon specs (builder mode)

```python
from csf import Pt, Polygon, CSFStacked
from csf.CSFStacked import SegmentSpec  # (module path may vary by your package layout)

# Define polygons at z0 and z1 (example only)
poly0 = Polygon(name="outer", vertices=(Pt(0,0), Pt(1,0), Pt(1,1), Pt(0,1)), weight=1.0)
poly1 = Polygon(name="outer", vertices=(Pt(0,0), Pt(2,0), Pt(2,1), Pt(0,1)), weight=1.0)

specs = [
    SegmentSpec(tag="segA", z0=0.0, z1=5.0, polygons_s0=(poly0,), polygons_s1=(poly1,)),
]

stack = CSFStacked()
stack.build_from_specs(specs)
stack.validate_contiguity(require_contiguity=True)
```

Under the hood:
- each spec becomes a `Section(z0)` and `Section(z1)`
- then one `ContinuousSectionField(section0=s0, section1=s1)`
- then it is stored as a `StackSegment`

---

## 4) Querying sections and properties on the global axis

### Get the owning field at global `z`

```python
field = stack.field_at(z=3.2)                    # default: junction_side="left"
field_r = stack.field_at(z=5.0, junction_side="right")
```

### Get the interpolated section at `z`

```python
sec = stack.section(z=3.2)
```

### Run a full section analysis at `z`

```python
sa = stack.section_full_analysis(z=3.2)
print(sa["A"], sa["Iy"], sa["Iz"])
```

`section_full_analysis(z)` is a convenience wrapper that calls:
1) `stack.section(z)`  
2) `section_full_analysis(section)`

---

## 5) Global 3D plot (quick verification)

`plot_volume_3d_global()` draws a global 3D representation of the stacked ruled surfaces.

```python
fig, ax = stack.plot_volume_3d_global(
    n_points_per_segment=10,
    show_caps=True,
)
```

This is intended as a **debug/verification** view (geometry continuity, segment order, etc.).

---

## 6) Fast integration example with PyCBA (beam bending)

Below is a minimal pattern used in `stacked_csf_example.py`: extract `EI(z)` from the stacked CSF and run a 1D beam analysis with PyCBA.

Assumptions:
- Euler–Bernoulli bending with `EI = E * Iy`
- piecewise-constant `EI` per solver element (midpoint sampling)

```python
import numpy as np
import pycba as cba

E = 2.1e11  # Pa (example)
P = -1.0e4  # N  (example tip load)

# Discretize the global axis
n = 40
z_min = stack.segments[0].z_start
z_max = stack.segments[-1].z_end
dz = (z_max - z_min) / (n - 1)

# Midpoint EI sampling (one EI per element)
ei_list = []
for i in range(n - 1):
    z_mid = (z_min + i * dz) + dz / 2.0
    Iy = stack.section_full_analysis(z_mid)["Iy"]
    ei_list.append(E * Iy)

# Boundary conditions (example: clamped at node 0)
R = [0] * (n * 2)
R[0], R[1] = -1, -1

beam = cba.BeamAnalysis([dz] * (n - 1), ei_list, R)
beam.add_pl(n - 1, P, dz)   # point load at free end
beam.analyze()

# Extract maximum vertical displacement (typical PyCBA result layout)
disp = np.max(np.abs(beam.beam_results.results.D[0::2]))
print("Max vertical displacement:", disp)
```

Why midpoint sampling:
- it guarantees you are sampling **inside** each solver element (not exactly at junctions)
- it reduces ambiguity when `z` matches a segment boundary

---

## 7) Practical notes

- Call `validate_contiguity()` early when building stacks, especially if segment endpoints come from multiple sources.
- If you query exactly at an internal junction `z = z_i`, decide whether you want the left or right segment:
  - default policy uses the **left** segment (deterministic)
  - use `junction_side="right"` if you need the segment on the right
- `CSFStacked` does not “merge” segments into a single field; it dispatches queries to the correct segment field.
