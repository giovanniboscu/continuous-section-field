# `CSFStacked` - Building a Continuous Member from Multiple CSF Elements

`CSFStacked` combines consecutive `ContinuousSectionField` objects into a single member defined over one global `z` coordinate.

The important idea is simple:

> A `ContinuousSectionField` describes the continuous evolution of one element between two sections.  
> `CSFStacked` joins several of those elements in sequence and provides one global interface to the whole member.

This is useful when a member cannot be represented conveniently by only one pair of end sections.

---

## 1. From one CSF element to a stacked member

A single `ContinuousSectionField` describes the evolution

```text
S0  -------------------->  S1
z0                          z1
```

between two sections.

Its geometry, polygon weights, shear weights, and other section data evolve continuously between those two stations.

`CSFStacked` extends this idea to several consecutive fields:

```text
field 0                 field 1                 field 2
S0  ---------------->  S1  ---------------->  S2  ---------------->  S3
z0                      z1                      z2                      z3

<--------------------------- CSFStacked ------------------------------>
                         global z
```

Each interval remains a normal `ContinuousSectionField`.

`CSFStacked` does **not** replace the individual fields and does not create a new interpolation law spanning the whole member. It stores the fields in order and dispatches each global `z` query to the field that owns that interval.

This distinction is important when adjacent elements have different interpolation laws, materials, topology, or geometric evolution.

---

## 2. What `CSFStacked` does

Given consecutive fields such as

```python
field_1: z = 0.0  -> 10.0
field_2: z = 10.0 -> 20.0
```

a stack can be created with:

```python
stack = CSFStacked()

stack.append(field_1)
stack.append(field_2)
```

The resulting object has the global domain

```text
0.0 <= z <= 20.0
```

and can answer queries such as:

```python
stack.section(4.0)
stack.section(15.0)
stack.field_at(17.0)
```

`CSFStacked` determines which field contains the requested global coordinate and delegates the operation to that field.

For example:

```text
z = 4.0   -> field_1
z = 15.0  -> field_2
```

---

# 3. Complete example: a two-element zig-zag member

The repository contains a compact example in:

```text
actions-examples/zigzag_element/
```

with:

```text
element_1.yaml
element_2.yaml
zigzag.py
```

The example deliberately uses very simple square sections so that the role of `CSFStacked` is visible directly from the coordinates.

---

## 3.1 First CSF element

The first element spans:

```text
z = 0.0 -> 10.0
```

At `z = 0`, the square is centred at approximately:

```text
x = 0
```

At `z = 10`, the same square is translated to:

```text
x = 1
```

Its YAML geometry is:

```yaml
# element_1.yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        section:
          weight: 1.0
          vertices:
            - [-0.4, -0.4]
            - [ 0.4, -0.4]
            - [ 0.4,  0.4]
            - [-0.4,  0.4]

    S1:
      z: 10.0
      polygons:
        section:
          weight: 1.0
          vertices:
            - [0.6, -0.4]
            - [1.4, -0.4]
            - [1.4,  0.4]
            - [0.6,  0.4]

  shear_weight_laws:
    - 'iso(0.2)'
```

So the first field produces a transverse displacement in the positive `x` direction:

```text
x

1.0                     +---------+
                        |         |
                        |   S1    |
                        |         |
                        +---------+
                      z = 10

0.0     +---------+
        |         |
        |   S0    |
        |         |
        +---------+
      z = 0
```

---

## 3.2 Second CSF element

The second element starts exactly where the first one ends:

```text
z = 10.0 -> 20.0
```

Its initial section is the translated square at `x = 1`, while its final section returns to `x = 0`:

```yaml
# element_2.yaml
CSF:
  sections:
    S0:
      z: 10.0
      polygons:
        section:
          weight: 1.0
          vertices:
            - [0.6, -0.4]
            - [1.4, -0.4]
            - [1.4,  0.4]
            - [0.6,  0.4]

    S1:
      z: 20.0
      polygons:
        section:
          weight: 1.0
          vertices:
            - [-0.4, -0.4]
            - [ 0.4, -0.4]
            - [ 0.4,  0.4]
            - [-0.4,  0.4]

  shear_weight_laws:
    - 'iso(0.2)'
```

The two fields therefore describe:

```text
x

1.0                       *
                         /   \
                       /       \
                     /           \
0.0        *                         *
           z=0       z=10            z=20

           field 1    |    field 2
```

The member first moves toward positive `x`, then returns.

A single `ContinuousSectionField` between `z=0` and `z=20` would not describe this geometry: its two end sections are identical, so the intermediate change of direction would be lost.

That is the basic reason for using `CSFStacked`.

---

# 4. Loading the two fields

Each YAML file is read independently with `CSFReader`.

```python
from csf.io.csf_reader import CSFReader
from csf.io.csf_issues import CSFIssues

rf1 = CSFReader().read_file("element_1.yaml")

if not rf1.ok:
    print(CSFIssues.format_report(rf1.issues))
    raise SystemExit(1)

rf2 = CSFReader().read_file("element_2.yaml")

if not rf2.ok:
    print(CSFIssues.format_report(rf2.issues))
    raise SystemExit(1)

f1 = rf1.field
f2 = rf2.field
```

At this point:

```text
f1 = ContinuousSectionField over [0, 10]
f2 = ContinuousSectionField over [10, 20]
```

They are still two independent CSF objects.

---

# 5. Creating the stack

Import `CSFStacked`:

```python
from csf.CSFStacked import CSFStacked
```

Create an empty stack:

```python
stack = CSFStacked(eps_z=1e-10)
```

Then append the fields in longitudinal order:

```python
stack.append(f1)
stack.append(f2)
```

The resulting structure is conceptually:

```text
stack.segments

[0]  seg_0   z = 0  -> 10    field = f1
[1]  seg_1   z = 10 -> 20    field = f2
```

The order is explicit. `CSFStacked` does not silently sort the fields.

---

## 5.1 Contiguity is checked when fields are appended

For two consecutive fields, the end of the first and the start of the second must coincide within `eps_z`.

For the zig-zag example:

```text
f1.s1.z = 10.0
f2.s0.z = 10.0
```

so the append is valid.

A gap is rejected:

```text
field 1: 0 -> 10
field 2: 11 -> 20

                 gap
                  |
0 ---------- 10   11 ---------- 20
```

An overlap is also rejected:

```text
field 1: 0 -> 10
field 2:  9 -> 20

               overlap
                  |
0 --------- 9 == 10 ----------- 20
```

This prevents an ambiguous global `z` mapping.

---

# 6. Querying the stacked member

Once the stack has been built, use global coordinates.

## `field_at(z)`

```python
field = stack.field_at(4.0)
```

returns the field covering `z=4`:

```text
field 1: [0, 10]
```

while:

```python
field = stack.field_at(15.0)
```

returns:

```text
field 2: [10, 20]
```

The caller does not need to determine the segment manually.

---

## `section(z)`

To obtain the actual interpolated section at a global coordinate:

```python
section = stack.section(5.0)
```

`CSFStacked` performs two operations:

```text
global z = 5
      |
      v
find the owning field
      |
      v
field 1
      |
      v
field_1.section(5)
      |
      v
Section at z = 5
```

Similarly:

```python
section = stack.section(17.0)
```

is evaluated by the second field.

This is the main stacked abstraction:

```text
global z -> correct ContinuousSectionField -> section
```

---

# 7. What happens exactly at a junction?

An internal junction belongs geometrically to both adjacent intervals.

In the example:

```text
field 1: [0, 10]
field 2: [10, 20]
              ^
            z=10
```

`CSFStacked` therefore provides the `junction_side` argument.

The default is:

```python
stack.section(10.0, junction_side="left")
```

which selects the field ending at the junction.

To select the field beginning at the junction:

```python
stack.section(10.0, junction_side="right")
```

The same policy is available through `field_at()`:

```python
left_field = stack.field_at(10.0, junction_side="left")
right_field = stack.field_at(10.0, junction_side="right")
```

For a geometrically and mechanically continuous junction, both sides normally describe the same junction section.

The distinction becomes important when a property, material assignment, interpolation rule, or other field data changes from one segment to the next.

`CSFStacked` does not hide such a discontinuity by interpolating across the junction.

---

# 8. Analysing a section

`section_full_analysis()` applies the normal CSF section analysis after dispatching the global coordinate to the correct segment.

```python
props = stack.section_full_analysis(7.5)
```

For example:

```python
print(props["A"])
print(props["Ix"])
print(props["Iy"])
```

The workflow is:

```text
z
|
v
CSFStacked
|
+--> select segment
     |
     +--> ContinuousSectionField.section(z)
          |
          +--> Section
               |
               +--> section_full_analysis(...)
```

No separate stacked section formulation is introduced.

---

# 9. Plotting the complete stacked geometry

The most direct way to see what the stack represents is:

```python
stack.plot_volume_3d_global(
    title="CSFStacked - two connected elements",
    wire=False,
    colors=True,
    box_aspect_scale=(1.0, 1.0, 0.5),
)
```

followed by:

```python
import matplotlib.pyplot as plt

plt.show()
```

Unlike `plot_volume_3d(z)`, which displays the individual segment containing `z`, `plot_volume_3d_global()` renders all stacked segments in one global coordinate system.

For the zig-zag example the resulting solid contains both changes of direction:

```text
z = 0   -> section centred at x = 0
z = 10  -> section centred at x = 1
z = 20  -> section centred at x = 0
```

---

# 10. Complete `zigzag.py`

The complete example is deliberately short:

```python
import matplotlib.pyplot as plt

from csf.CSFStacked import CSFStacked
from csf.io.csf_reader import CSFReader
from csf.io.csf_issues import CSFIssues


# Load and validate the first field.
rf1 = CSFReader().read_file("element_1.yaml")

if not rf1.ok:
    print(CSFIssues.format_report(rf1.issues))
    raise SystemExit(1)


# Load and validate the second field.
rf2 = CSFReader().read_file("element_2.yaml")

if not rf2.ok:
    print(CSFIssues.format_report(rf2.issues))
    raise SystemExit(1)


f1 = rf1.field
f2 = rf2.field


# Assemble the global stacked member.
stack = CSFStacked(eps_z=1e-10)

stack.append(f1)
stack.append(f2)


# Plot the complete geometry.
stack.plot_volume_3d_global(
    title="CSFStacked - two connected elements",
    wire=False,
    colors=True,
    box_aspect_scale=(1.0, 1.0, 0.5),
)

plt.show()
```

The important part is only:

```python
stack = CSFStacked()
stack.append(f1)
stack.append(f2)
```

Everything else in the example loads, validates, and visualises the two CSF fields.

---

# 11. Plotting one section from the global member

A section can be visualised without manually identifying its field:

```python
stack.plot_section_2d(
    z=15.0,
    show_ids=True,
    show_weights=True,
)
```

Because `z=15` lies inside `[10,20]`, the second field is selected automatically.

At a junction, the same left/right rule applies:

```python
stack.plot_section_2d(
    z=10.0,
    junction_side="right",
)
```

---

# 12. Plotting section properties over the whole stack

Properties can be evaluated over every segment using:

```python
stack.plot_properties(
    keys_to_plot=["A", "Ix", "Iy"],
    num_points=100,
    show_junctions=True,
)
```

Sampling is performed independently inside every stacked field.

Conceptually:

```text
field 1 samples           field 2 samples
|--------------------|    |--------------------|
0                   10   10                   20
```

The curves are not artificially connected by an interpolation law across an internal junction.

With:

```python
show_junctions=True
```

the internal boundaries are marked explicitly.

This makes the method suitable not only for geometrically continuous members but also for members whose sectional properties change from one CSF element to the next.

---

# 13. Global bounds

The longitudinal domain can be obtained with:

```python
z_min, z_max = stack.global_bounds()
```

For the zig-zag example:

```python
z_min == 0.0
z_max == 20.0
```

---

# 14. Alternative construction with `SegmentSpec`

`append()` is the clearest interface when the individual `ContinuousSectionField` objects already exist.

`CSFStacked` can also create fields directly from polygon sets.

A segment can be specified with:

```python
from csf.CSFStacked import SegmentSpec
```

```python
spec = SegmentSpec(
    tag="element_1",
    z0=0.0,
    z1=10.0,
    polygons_s0=polygons_at_z0,
    polygons_s1=polygons_at_z10,
)
```

Several specifications can then be assembled with:

```python
stack = CSFStacked()

stack.build_from_specs([
    spec_1,
    spec_2,
])
```

Internally, each specification is converted into a normal `ContinuousSectionField` and appended to the stack.

Automatic reordering is intentionally not performed. The specifications must already be supplied in their intended longitudinal order.

For normal YAML-based CSF workflows, however, the simpler pattern is:

```python
CSFReader -> ContinuousSectionField -> CSFStacked.append()
```

---

# 15. Public API overview

## Construction and assembly

### `CSFStacked(eps_z=1e-10)`

Creates an empty stacked container.

```python
stack = CSFStacked()
```

`eps_z` is the tolerance used when comparing longitudinal coordinates at segment boundaries.

---

### `append(field)`

Adds one `ContinuousSectionField` to the end of the stack.

```python
stack.append(field)
```

The new field must:

- have `z_end > z_start`;
- follow the already appended fields;
- start at the previous field end within `eps_z`;
- introduce neither a gap nor an overlap.

---

### `build_from_specs(specs, sort_by_z=False)`

Builds the stack from `SegmentSpec` objects.

```python
stack.build_from_specs(specs)
```

The supplied order is the stack order.

Passing:

```python
sort_by_z=True
```

is rejected because automatic reordering is not supported.

---

### `validate_contiguity(require_contiguity=True)`

Explicitly checks the segment sequence.

```python
stack.validate_contiguity()
```

It detects invalid intervals, overlaps, and - when requested - gaps.

---

# 16. Global dispatch API

### `field_at(z, junction_side="left")`

Returns the `ContinuousSectionField` responsible for global coordinate `z`.

```python
field = stack.field_at(12.0)
```

---

### `section(z, junction_side="left")`

Returns the section at global coordinate `z`.

```python
section = stack.section(12.0)
```

Equivalent in concept to:

```python
field = stack.field_at(12.0)
section = field.section(12.0)
```

---

### `section_full_analysis(z, junction_side="left")`

Returns the standard full section analysis for the section at `z`.

```python
properties = stack.section_full_analysis(12.0)
```

---

### `global_bounds()`

Returns:

```python
(z_min, z_max)
```

for the complete stack.

---

# 17. Plotting API

### `plot_section_2d(z, ...)`

Plots the section at a global coordinate.

```python
stack.plot_section_2d(z=12.0)
```

---

### `plot_weight(z, ...)`

Plots weight distributions for the field selected by global `z`.

```python
stack.plot_weight(z=12.0)
```

---

### `plot_volume_3d(z, ...)`

Plots only the stacked segment containing `z`.

```python
stack.plot_volume_3d(z=12.0)
```

---

### `plot_volume_3d_global(...)`

Plots all segments together.

```python
stack.plot_volume_3d_global()
```

This is normally the first plot to use when checking an assembled geometry.

---

### `plot_properties(keys_to_plot, ...)`

Evaluates and plots selected section properties over all stacked intervals.

```python
stack.plot_properties(
    keys_to_plot=["A", "Ix", "Iy"],
)
```

---

# 18. The key distinction

The difference between `ContinuousSectionField` and `CSFStacked` can be summarised as:

```text
ContinuousSectionField
    one continuous evolution between two endpoint sections

CSFStacked
    an ordered sequence of ContinuousSectionField objects
    exposed through one global z coordinate
```

For the zig-zag example:

```text
one field from z=0 to z=20
    cannot represent the intermediate reversal from x=0 -> 1 -> 0
    when its two endpoint sections are identical

two fields in CSFStacked
    field 1: x=0 -> 1
    field 2: x=1 -> 0
    preserve both geometric evolutions
```

`CSFStacked` therefore extends the CSF representation from a single ruled element to a piecewise continuous member while preserving the normal `ContinuousSectionField` formulation inside every segment.
