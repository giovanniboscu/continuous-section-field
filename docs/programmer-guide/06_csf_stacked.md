# CSFStacked.py — Reference (classes, dataclasses, and methods)

## Analyzed file
`CSFStacked.py`
## What `CSFStacked` is for

`CSFStacked` is a container class used to combine **multiple `ContinuousSectionField` objects** into a single global model along the `z` axis.

It is useful when a member is represented by **multiple consecutive CSF segments** (for example: tapered + constant + tapered regions), and you want to query the model with a **single global API** instead of handling each segment manually.

With `CSFStacked`, you can:

- store one or many CSF fields in a deterministic stacked order
- query the active field at any global coordinate `z`
- handle internal junctions explicitly (`left` / `right`)
- retrieve interpolated sections globally (`section(z)`)
- run section analysis globally (`section_full_analysis(z)`)
- validate segment contiguity / detect overlaps or gaps
- plot the full stacked geometry in a single 3D global view

In short, `CSFStacked` adds a **global dispatch and management layer** on top of multiple CSF segments, while keeping the underlying `ContinuousSectionField` logic unchanged.

This document describes **all main elements defined in the file**:
- dataclass `SegmentSpec`
- dataclass `StackSegment`
- class `CSFStacked`
- all class methods (public and internal)

---

## 1) `SegmentSpec` (dataclass, frozen=True)

### Purpose
**Generic input specification** used to build a stacked segment before creating the `ContinuousSectionField`.

### Fields
- `tag: str` — segment identifier
- `z0: float` — global start coordinate of the segment
- `z1: float` — global end coordinate of the segment
- `polygons_s0: Tuple[Polygon, ...]` — polygons at the start section (`z0`)
- `polygons_s1: Tuple[Polygon, ...]` — polygons at the end section (`z1`)

### Practical notes
- Polygon names should be consistent between `z0` and `z1` for side-surface pairing.
- For each paired polygon, the number of vertices must match.

### Example
```python
spec = SegmentSpec(
    tag="seg_A",
    z0=0.0,
    z1=5.0,
    polygons_s0=(p0,),
    polygons_s1=(p1,),
)
```

---

## 2) `StackSegment` (dataclass)

### Purpose
Internal runtime container representing a stack segment that has already been built.

### Fields
- `tag: str`
- `z_start: float`
- `z_end: float`
- `field: ContinuousSectionField`

### Example (typically created internally)
```python
runtime_seg = StackSegment(
    tag="seg_0",
    z_start=0.0,
    z_end=5.0,
    field=field,
)
```

---

# 3) `CSFStacked`

## General purpose
Stacked container for multiple `ContinuousSectionField` objects, with:
- global dispatch on `z`
- explicit junction handling
- contiguity/overlap validation
- global queries (`section`, `section_full_analysis`)
- global 3D plot of the stacked volume

---

## Methods of class `CSFStacked`

## 3.1) `__init__(self, eps_z: float = 1e-10)`

### Meaning
Initializes the container:
- `self.eps_z`: numerical tolerance on `z`
- `self.segments`: empty list of `StackSegment`

### Why `eps_z` is important
It is used for robust floating-point comparisons on:
- global bounds
- internal junctions
- contiguity checks
- range checks

### Default
Yes, it has a default: `1e-10`.

### Example
```python
stack = CSFStacked()               # uses eps_z = 1e-10
stack_loose = CSFStacked(eps_z=1e-8)
```

---

## 3.2) `append(self, field: ContinuousSectionField) -> None`

### Meaning
Adds an already built `ContinuousSectionField` to the stack.

### What it does
- reads `field.s0.z` and `field.s1.z`
- validates `z_end > z_start`
- creates a `StackSegment` with automatic tag (`seg_0`, `seg_1`, ...)
- appends the segment
- sorts segments by `z_start`

### Example
```python
stack.append(field0)
stack.append(field1)
```

### Note
`append` adds **one field per call**, but the stack can contain **many fields**.

---

## 3.3) `field_at(self, z: float, junction_side: str = "left") -> ContinuousSectionField`

### Meaning
Returns the active `ContinuousSectionField` at global coordinate `z`.

### Junction handling
If `z` matches an internal junction:
- `junction_side="left"` → field on the left
- `junction_side="right"` → field on the right

### Example
```python
f = stack.field_at(3.0)
fL = stack.field_at(5.0, junction_side="left")
fR = stack.field_at(5.0, junction_side="right")
```

### Possible errors
- empty stack
- invalid `junction_side`
- `z` outside the global domain
- `z` not mappable (inconsistent stack)

---

## 3.4) `make_field_from_polygons(z0, z1, polygons_s0, polygons_s1)` *(staticmethod)*

### Meaning
Convenience factory to create a `ContinuousSectionField` from two polygon sets at `z0` and `z1`.

### Validations
- `z1 > z0`
- `polygons_s0` and `polygons_s1` are not empty

### Example
```python
field = CSFStacked.make_field_from_polygons(
    z0=0.0,
    z1=4.0,
    polygons_s0=[p0],
    polygons_s1=[p1],
)
```

---

## 3.5) `add_segment_spec(self, spec: SegmentSpec) -> None`

### Meaning
Creates a `ContinuousSectionField` from a `SegmentSpec` and adds it to the stack.

### Important note
Here the segment is added using the spec `tag`.
Unlike `append()`, there is **no automatic sort** after a single insertion.

### Example
```python
stack.add_segment_spec(spec)
```

---

## 3.6) `build_from_specs(self, specs: List[SegmentSpec], sort_by_z: bool = True) -> None`

### Meaning
Rebuilds the entire stack from a list of `SegmentSpec`.

### What it does
- resets `self.segments = []`
- adds each spec with `add_segment_spec()`
- optionally sorts by `z_start`

### Example
```python
stack.build_from_specs(specs, sort_by_z=True)
```

### Recommended use
Data-driven workflows (YAML / generators / benchmark cases).

---

## 3.7) `validate_contiguity(self, require_contiguity: bool = True) -> None`

### Meaning
Validates:
- segments with valid end coordinates
- absence of overlap
- (optional) strict contiguity without gaps

### Example
```python
stack.validate_contiguity(require_contiguity=True)
```

### Behavior
- overlap: always an error
- gap: error only if `require_contiguity=True`

---

## 3.8) `_find_segment(self, z: float) -> StackSegment` *(internal)*

### Meaning
Returns the segment containing `z`, using a deterministic interval policy.

### Policy
- first segment: `[z_start, z_end]`
- following segments: `(z_start, z_end]`

Consequence: an internal junction belongs to the left segment.

### Example (debug/internal use)
```python
seg = stack._find_segment(5.0)
print(seg.tag)
```

---

## 3.9) `section(self, z: float, junction_side: str = "left")`

### Meaning
Returns the interpolated `Section` at global coordinate `z`.

### Implementation (conceptually)
- `field_at(...)`
- `.section(z)` on the selected field

### Example
```python
sec = stack.section(2.5)
sec_j = stack.section(5.0, junction_side="right")
```

---

## 3.10) `section_full_analysis(self, z: float, junction_side: str = "left") -> float`

### Meaning
Runs `section_full_analysis(sec)` on the global section at `z`.

### Note on return type
In the file, the type hint is `-> float`, but in many CSF versions `section_full_analysis(...)` returns a structured output (e.g., a dict). It is safer to treat it as **generic analysis output** and verify in your version.

### Example
```python
out = stack.section_full_analysis(2.5)
print(out)
```

---

## 3.11) `_compute_axis_bounds_with_margin(self, xs, ys, zs, margin_ratio=0.10)` *(internal)*

### Meaning
Computes `(xmin,xmax)`, `(ymin,ymax)`, `(zmin,zmax)` bounds with axis-wise margins.

### Return
```python
((xmin, xmax), (ymin, ymax), (zmin, zmax), (dx, dy, dz))
```

### Useful features
- validates non-empty input
- validates `margin_ratio >= 0`
- handles degenerate axes (`dx`, `dy`, `dz` null) by expanding to a unit span

### Example (technical)
```python
bounds = stack._compute_axis_bounds_with_margin(
    xs=[0, 2], ys=[0, 1], zs=[0, 10], margin_ratio=0.1
)
```

---

## 3.12) `_apply_box_limits(ax, bounds) -> None` *(internal staticmethod)*

### Meaning
Applies axis limits and box aspect to a Matplotlib 3D axis.

### Example
```python
bounds = stack._compute_axis_bounds_with_margin([0,1], [0,2], [0,3])
CSFStacked._apply_box_limits(ax, bounds)
```

### What it sets
- `xlim`, `ylim`, `zlim`
- `set_box_aspect((dx, dy, dz))`

---

## 3.13) `plot_volume_3d_global(...)`

### Signature
```python
plot_volume_3d_global(
    line_percent=100.0,
    seed=1,
    margin_ratio=0.10,
    display_scale=(1.0, 1.0, 1.0),
    box_aspect_scale=(1.0, 1.0, 1.0),
    wire=False,
    colors=True,
)
```

### Meaning
Renders the entire stacked volume in a single global 3D plot (Matplotlib), without `Poly3DCollection`.

### Supported modes
- `wire=False, colors=True` → colored solid
- `wire=False, colors=False` → grayscale solid
- `wire=True, colors=True` → polygon-colored wireframe
- `wire=True, colors=False` → gray/black wireframe

### Example
```python
ax = stack.plot_volume_3d_global(
    wire=False,
    colors=True,
    seed=1,
    margin_ratio=0.08,
    display_scale=(1.0, 1.0, 1.0),
    box_aspect_scale=(1.0, 1.0, 1.0),
)

import matplotlib.pyplot as plt
plt.show()
```

### Key parameters
- `display_scale`: visual scaling on displayed coordinates (X,Y,Z)
- `box_aspect_scale`: 3D box aspect scaling
- `wire`: wireframe vs filled surfaces
- `colors`: color palette vs grayscale
- `seed`: deterministic color assignment by polygon name

### Extended description
The method:
1. validates inputs
2. creates a seeded palette and a color map for `poly.name`
3. iterates through all segments
4. extracts start/end sections of each segment
5. pairs polygons by name
6. draws end caps and side surfaces (or wireframe)
7. accumulates global coordinates
8. sets global limits and aspect
9. returns `ax`

### Attention
In the shown file, `line_percent` is validated but does not appear to be effectively used in the rendering logic.

---

## 3.14) `global_bounds(self)`

### Meaning
Returns the global `z` bounds of the stack as `(z_min, z_max)`.

### Example
```python
zmin, zmax = stack.global_bounds()
print(zmin, zmax)
```

### Errors
- `ValueError` if the stack is empty

---

# Minimal complete example (recommended workflow)

```python
# 1) Build the stack
stack = CSFStacked(eps_z=1e-10)
stack.append(field0)   # one field per call
stack.append(field1)   # ... but fields can be multiple

# 2) Validate geometric consistency along z
stack.validate_contiguity(require_contiguity=True)

# 3) Global queries
sec = stack.section(2.5)
out = stack.section_full_analysis(2.5)

# 4) Global bounds
zmin, zmax = stack.global_bounds()

# 5) Global plot
ax = stack.plot_volume_3d_global(wire=False, colors=True)

import matplotlib.pyplot as plt
plt.show()
```

---

# Final note

Methods with `_` prefix (`_find_segment`, `_compute_axis_bounds_with_margin`, `_apply_box_limits`) are internal utilities; normal usage should go through public methods (`append`, `build_from_specs`, `validate_contiguity`, `field_at`, `section`, `section_full_analysis`, `plot_volume_3d_global`, `global_bounds`).
