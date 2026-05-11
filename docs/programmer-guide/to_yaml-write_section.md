# YAML Materialization functions - to_yaml & write_section

## Purpose

This guide explains a minimal CSF example that builds a tapered T-section, assigns axial and shear/torsion weight laws, writes the original parametric YAML model, and then writes a materialized YAML model over a selected interval.

The example shows the difference between two outputs:

- `tsection.yaml`: the original parametric CSF model, including active `weight_laws` and `shear_weight_laws`.
- `tsection1.yaml`: a materialized CSF model between `z = 5` and `z = 6`, where geometry and weights have already been evaluated.

The central point is that a materialized YAML file should not keep active laws. If the original laws are useful for traceability, they can be written as YAML comments only.

---

## 1. Python example overview

The Python script performs the following operations:

1. imports the required CSF objects and utility functions;
2. defines a start T-section at `z = 0`;
3. defines an end T-section at `z = 10`;
4. builds a `ContinuousSectionField`;
5. assigns axial/bending weight laws with `set_weight_laws(...)`;
6. assigns shear/torsion participation laws with `set_shear_weight_laws(...)`;
7. writes the parametric YAML model with `to_yaml(...)`;
8. writes a materialized YAML model with `write_section(...)`;
9. computes and prints section properties at `z = 5`;
10. plots the interpolated section and volume.

The two key output calls are:

```python
field.to_yaml("tsection.yaml")
field.write_section(5, 6, "tsection1.yaml")
```

These two calls are intentionally different. They do not represent the same semantic level of the model.

---

## 2. Geometry definition

The example defines a T-section using two non-overlapping rectangular polygons:

- `flange`: the horizontal top part;
- `web`: the vertical stem.

At `z = 0`, the flange is constant and the web extends down to `y = -1.0`.

```python
poly0_start = Polygon(
    vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
    weight=1.0,
    name="flange",
)

poly1_start = Polygon(
    vertices=(Pt(-0.2, -1.0), Pt(0.2, -1.0), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
    weight=1.0,
    name="web",
)
```

At `z = 10`, the flange remains unchanged, while the web becomes deeper and extends down to `y = -2.5`.

```python
poly0_end = Polygon(
    vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
    weight=1.0,
    name="flange",
)

poly1_end = Polygon(
    vertices=(Pt(-0.2, -2.5), Pt(0.2, -2.5), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
    weight=1.0,
    name="web",
)
```

The vertex order is counter-clockwise. This is required because CSF uses polygon area and moment formulas based on Green's theorem / shoelace-type expressions. Clockwise polygons would produce negative areas and invalid section properties.

---

## 3. Section pairing and interpolation

The two endpoint sections are created as:

```python
s0 = Section(polygons=(poly0_start, poly1_start), z=0.0)
s1 = Section(polygons=(poly0_end, poly1_end), z=10.0)

field = ContinuousSectionField(section0=s0, section1=s1)
```

Polygon pairing is positional:

```text
poly0_start <-> poly0_end   # flange
poly1_start <-> poly1_end   # web
```

For this example, the flange is geometrically constant. The web is linearly interpolated between its endpoint vertices.

For the lower web vertices:

```text
z = 0:   y = -1.0
z = 10:  y = -2.5
```

The linear interpolation is:

```text
y(z) = y0 + t * (y1 - y0)
t = (z - z0) / (z1 - z0)
```

At `z = 5`:

```text
t = 0.5
y = -1.0 + 0.5 * (-2.5 + 1.0) = -1.75
```

At `z = 6`:

```text
t = 0.6
y = -1.0 + 0.6 * (-2.5 + 1.0) = -1.9
```

These are the web coordinates written in the materialized YAML file.

---

## 4. Weight laws

The example assigns axial/bending participation laws with:

```python
field.set_weight_laws([
    "flange,flange:1.0 +t",
    "web,web:4.0 + t",
])
```

These laws override the polygon-level `weight` values when the section field is evaluated.

Therefore, although the original endpoint polygons are defined with:

```python
weight=1.0
```

for both `flange` and `web`, the effective weights are:

```text
flange: 1.0 + t
web:    4.0 + t
```

where:

```text
t = (z - 0) / (10 - 0)
```

The effective values are therefore:

| z | t | flange weight | web weight |
|---:|---:|---:|---:|
| 0 | 0.0 | 1.0 | 4.0 |
| 5 | 0.5 | 1.5 | 4.5 |
| 6 | 0.6 | 1.6 | 4.6 |
| 10 | 1.0 | 2.0 | 5.0 |

This is why the materialized file `tsection1.yaml` contains `weight: 1.5`, `weight: 4.5`, `weight: 1.6`, and `weight: 4.6`.

---

## 5. Shear/torsion weight laws

The script also assigns shear/torsion participation laws:

```python
field.set_shear_weight_laws([
    "iso(0.2)",
    "flange,flange:iso(0.1)",
])
```

The interpretation is:

- `iso(0.2)` defines the default shear/torsion participation law;
- `flange,flange:iso(0.1)` overrides that default for the `flange` polygon pair;
- `web` keeps the default law.

These laws are part of the parametric model. In a materialized export, they should either be resolved into the relevant effective values, if the schema supports those explicit fields, or kept only as comments for traceability.

---

## 6. Parametric export: `tsection.yaml`

The call:

```python
field.to_yaml("tsection.yaml")
```

writes the original parametric model.

A simplified version of the output is:

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        flange:
          weight: 1.0
          vertices:
            - [-1.0, -0.2]
            - [1.0, -0.2]
            - [1.0, 0.2]
            - [-1.0, 0.2]
        web:
          weight: 1.0
          vertices:
            - [-0.2, -1.0]
            - [0.2, -1.0]
            - [0.2, -0.2]
            - [-0.2, -0.2]
    S1:
      z: 10.0
      polygons:
        flange:
          weight: 1.0
          vertices:
            - [-1.0, -0.2]
            - [1.0, -0.2]
            - [1.0, 0.2]
            - [-1.0, 0.2]
        web:
          weight: 1.0
          vertices:
            - [-0.2, -2.5]
            - [0.2, -2.5]
            - [0.2, -0.2]
            - [-0.2, -0.2]
  weight_laws:
    - 'flange,flange: 1.0 +t'
    - 'web,web: 4.0 + t'
  shear_weight_laws:
    - 'iso(0.2)'
    - 'flange,flange: iso(0.1)'
```

This file is not materialized. It still contains active laws.

The polygon-level `weight` fields are the serialized/base polygon weights. The effective weights are defined by `weight_laws` when the field is evaluated.

---

## 7. Materialized export: `tsection1.yaml`

The call:

```python
field.write_section(5, 6, "tsection1.yaml")
```

writes a new CSF model between `z = 5` and `z = 6`.

This output is materialized:

- vertex coordinates have already been interpolated;
- `weight` values have already been evaluated from the active laws;
- active laws are not written back into the YAML data structure.

A simplified output is:

```yaml
CSF:
  sections:
    S0:
      z: 5.0
      polygons:
        flange:
          weight: 1.5
          vertices:
            - [-1.0, -0.2]
            - [1.0, -0.2]
            - [1.0, 0.2]
            - [-1.0, 0.2]
        web:
          weight: 4.5
          vertices:
            - [-0.2, -1.75]
            - [0.2, -1.75]
            - [0.2, -0.2]
            - [-0.2, -0.2]
    S1:
      z: 6.0
      polygons:
        flange:
          weight: 1.6
          vertices:
            - [-1.0, -0.2]
            - [1.0, -0.2]
            - [1.0, 0.2]
            - [-1.0, 0.2]
        web:
          weight: 4.6
          vertices:
            - [-0.2, -1.9]
            - [0.2, -1.9]
            - [0.2, -0.2]
            - [-0.2, -0.2]
```

This file is numerically self-contained over the interval `[5, 6]`.

---

## 8. Why laws are commented in the materialized YAML

A materialized YAML file should not keep active `weight_laws`, because the weights have already been evaluated.

However, the original laws are useful as traceability metadata. Therefore they can be appended as comments:

```yaml
# APPLIED_LAWS_TRACE:
# Re-applying them may change the result, especially for laws using w0/w1.
# They are kept for traceability only and must not be parsed/applied again.
# weight_laws:
#   - 'flange,flange: 1.0 +t'
#   - 'web,web: 4.0 + t'
# shear_weight_laws:
#   - 'iso(0.2)'
#   - 'flange,flange: iso(0.1)'
```

Because these lines are comments, they are ignored by YAML parsers.

This preserves the original modeling intent without reactivating the laws.

---

## 9. The idempotency issue

The important semantic distinction is:

```text
to_yaml()      -> parametric model, laws active
write_section() -> materialized model, laws already applied
```

If a materialized YAML file keeps active laws, reloading and exporting it again may change the result.

This is especially dangerous for laws that use endpoint-dependent variables such as:

```text
w0
w1
```

For example, if the original model has endpoint weights equal to `1.0`, but the materialized model writes effective endpoint weights such as `4.5` and `4.6`, then a later law using `w0` and `w1` would no longer refer to the original context.

Therefore the safe rule is:

```text
A materialized YAML file must not contain active laws unless the user explicitly wants an hybrid export.
```

The default behavior should be idempotent:

```text
write_section()
-> reload output YAML
-> write_section() again
-> weights should not be changed by re-applied laws
```

---

## 10. Recommended implementation policy

For this example, the recommended export policy is:

| Export method | Meaning | Laws written as active YAML? | Laws written as comments? |
|---|---|---:|---:|
| `to_yaml(...)` | original parametric model | yes | no |
| `write_section(...)` | materialized interval model | no | yes, optional trace |

This avoids ambiguity and makes the files easier to reason about.

A possible future option could be:

```python
write_section(..., keep_laws=False)
```

but the safe default for a materialized export is:

```python
keep_laws = False
```

---

## 11. Section properties check at `z = 5`

The script evaluates the field at mid-span:

```python
sec_mid = field.section(5.0)
props = section_properties(sec_mid)
```

The printed quantities include:

- area `A`;
- centroid coordinates `Cx`, `Cy`;
- centroidal second moments of area `Ix`, `Iy`;
- product of inertia `Ixy`.

Derived quantities are then computed with:

```python
derived = section_derived_properties(props)
```

The script prints:

- radii of gyration `rx`, `ry`;
- principal moments `I1`, `I2`;
- principal axis rotation angle `theta_deg`.

A statical moment of area is also computed at the neutral axis:

```python
Q_na = section_statical_moment_partial(sec_mid, y_cut=props['Cy'])
```

Finally, the total field volume is obtained with:

```python
total_vol = integrate_volume(field, 0, 10)
```

These checks are useful to verify that the interpolated geometry and weight laws are being applied consistently.

---

## 12. Visualization

The example uses:

```python
viz = Visualizer(field)
viz.plot_section_2d(z=5.0)
viz.plot_volume_3d(line_percent=100.0, seed=1)
```

The 2D plot verifies the interpolated section at `z = 5`.

The 3D plot verifies the ruled volume generated by linear interpolation between the endpoint polygons.

These plots are diagnostic only. They are not required for YAML export.

---

## 13. Minimal workflow

The minimal workflow is:

```python
field = ContinuousSectionField(section0=s0, section1=s1)

field.set_weight_laws([
    "flange,flange:1.0 +t",
    "web,web:4.0 + t",
])

field.set_shear_weight_laws([
    "iso(0.2)",
    "flange,flange:iso(0.1)",
])

field.to_yaml("tsection.yaml")
field.write_section(5, 6, "tsection1.yaml")
```

This produces:

```text
tsection.yaml   -> parametric model, active laws
tsection1.yaml  -> materialized model, evaluated weights, laws only as comments
```

---

## 14. Recommended wording for the Programmer Guide

`to_yaml(...)` writes the parametric CSF model. The endpoint sections are serialized together with the active weight laws and shear weight laws. When the model is later evaluated, these laws override the polygon-level weight fields for the selected polygon pairs.

`write_section(z0, z1, ...)` writes a materialized CSF model over the interval `[z0, z1]`. The endpoint sections in the generated file are evaluated sections: interpolated coordinates and effective weights have already been computed. For this reason, active `weight_laws` and `shear_weight_laws` are not written back into the YAML data structure. If needed, the original laws may be appended as commented traceability metadata under `APPLIED_LAWS_TRACE`.

This distinction prevents accidental re-application of laws when the materialized YAML is parsed again, especially for laws that depend on endpoint context such as `w0` and `w1`.
