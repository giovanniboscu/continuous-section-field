# CSF Polygon Geometry Guide: `@cell` and `@wall`

This guide covers the **geometric construction** of tagged polygons in CSF.  
It does not describe the underlying torsion calculations - those are documented in the [section analysis reference](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/sectionfullanalysis.md).

---

## Overview

CSF supports two torsion-related polygon tags:

| Tag | Section type | Loop structure |
|-----|-------------|----------------|
| `@cell` | Closed thin-walled cell | Two closed loops in the same `vertices` list: outer + inner |
| `@wall` | Open thin-walled strip | One closed loop per polygon |

The tag is embedded directly in the polygon name key in the YAML definition.  
Tags control which calculation path CSF uses. They do not change the section interpolation rules.

---

## Part 1 - `@cell`: Closed Cell Polygon

### Concept

A `@cell` polygon defines a **closed thin-walled cell** for Saint-Venant torsion using the Bredt-Batho thin-walled cell formulation.

The geometry is encoded as **one YAML polygon entry** whose `vertices` list contains **two closed loops**:

- an **outer loop** - the external boundary of the cell wall
- an **inner loop** - the internal void boundary

Both loops must be explicitly closed. For each loop, the last vertex must coincide with the first vertex. This closure is what allows CSF to identify the outer and inner parts of the cell geometry.

The inner loop represents a void. Its orientation must therefore subtract area from the outer loop.

> **Always verify the result with a section plot before using it in analysis.**

---

### Construction Rules

#### Loop orientation

The standard convention is:

- outer loop → **CCW** (counter-clockwise) → positive area contribution
- inner loop → **CW** (clockwise) → negative area contribution

The net signed area must be positive:

```text
A_net = A_outer - A_inner > 0
```

#### Loop closure

Each loop must be closed independently:

```text
outer: P0 → P1 → ... → Pn → P0
inner: Q0 → Q1 → ... → Qm → Q0
```

The outer loop and the inner loop are placed one after the other in the same `vertices` list. The transition from the closed outer loop to the closed inner loop is only the start of the next loop; it is not a geometric part of the section.

#### Vertex sequence

```text
outer loop, CCW, closed
inner loop, CW, closed
```

---

### Thickness: `@t=`

The wall thickness `t` can be:

- **specified explicitly** in the polygon name: `@t=<value>`; for example, `@cell@t=0.03`
- **omitted**: CSF estimates it as `t = 2A / P`, where `A` is the cell wall area and `P` is the total perimeter

If thickness is specified at both `S0` and `S1`, CSF interpolates it linearly along `z`.  
If specified at only one section, it is treated as constant.

---

### Naming Syntax

```text
<base_name>@cell
<base_name>@cell@t=<value>
```

Examples:

```text
box_section@cell
box_section@cell@t=0.03
wall_outer@cell@t=0.015
```

The base name is used as a label. Polygon pairing across sections remains index-based.

---

### Example 1 - Rectangular Hollow Box

A rectangular box section: outer `10 × 6`, inner void `4 × 2` offset from the corner.

```text
Outer loop, CCW:  (0,0) → (10,0) → (10,6) → (0,6) → (0,0)
Inner loop, CW:   (3,2) → (3,4) → (7,4) → (7,2) → (3,2)
```

Net area:

```text
A_net = A_outer - A_inner = 60 - 8 = 52
```

```yaml
CSF:
  sections:
    S0:
      z: 0.000000
      polygons:
        box@cell@t=0.03:
          weight: 1.000000
          vertices:
            # OUTER loop, CCW, closed
            - [0.0, 0.0]
            - [10.0, 0.0]
            - [10.0, 6.0]
            - [0.0, 6.0]
            - [0.0, 0.0]

            # INNER loop, CW, closed
            - [3.0, 2.0]
            - [3.0, 4.0]
            - [7.0, 4.0]
            - [7.0, 2.0]
            - [3.0, 2.0]

    S1:
      z: 10.000000
      polygons:
        box@cell@t=0.03:
          weight: 1.000000
          vertices:
            # OUTER loop, CCW, closed
            - [0.0, 0.0]
            - [10.0, 0.0]
            - [10.0, 6.0]
            - [0.0, 6.0]
            - [0.0, 0.0]

            # INNER loop, CW, closed
            - [3.0, 2.0]
            - [3.0, 4.0]
            - [7.0, 4.0]
            - [7.0, 2.0]
            - [3.0, 2.0]
```

---

### Checklist - `@cell` polygon

- [ ] Name contains `@cell`
- [ ] `vertices` contains exactly two closed loops: outer + inner
- [ ] Outer loop is CCW
- [ ] Inner loop is CW
- [ ] Each loop is closed independently: last vertex equals first vertex
- [ ] Net signed area is positive
- [ ] Thickness is provided via `@t=` or left for CSF to estimate as `t = 2A/P`
- [ ] Same polygon count and vertex count at `S0` and `S1`
- [ ] Section plot verified

---

## Part 2 - `@wall`: Open Section Strip

### Concept

A `@wall` polygon defines an **open thin-walled strip** - a web, flange, or plate - for open-section torsion.

Each `@wall` polygon encodes **one single closed loop**.  
There is no inner loop and no void.

The polygon must represent a **thin elongated strip**: its length must be much larger than its thickness. The formula `J ≈ b t³ / 3` is a thin-strip approximation and is only meaningful under this condition.

> Do not use `@wall` for compact or block-like shapes. The result will not be physically meaningful.

---

### Construction Rules

- Define the strip as a standard closed polygon.
- The polygon should look like an offset of a centerline: two long parallel sides and two short closing ends.
- Use one polygon per strip patch: web, flange, stiffener, or similar part.
- Do not combine multiple physical strips into one `@wall` polygon.

---

### Thickness: `@t=`

The wall thickness `t` can be:

- **specified explicitly** in the polygon name: `@t=<value>`; this is recommended for complex or irregular strips
- **omitted**: CSF estimates it as `t = 2A / P`

For non-rectangular or irregular strips, use explicit `@t=`.

---

### Naming Syntax

```text
<base_name>@wall
<base_name>@wall@t=<value>
```

Examples:

```text
web@wall@t=0.02
flange_top@wall@t=0.015
stiffener@wall
```

---

### Example 2 - C-Section: Three Strips

A C-section modeled as three separate `@wall` strips: top flange, web, bottom flange.

```text
Section layout, approximate:

  ┌────────────────┐   ← top flange
  │
  │                    ← web
  │
  └────────────────┘   ← bottom flange
```

Each strip is a thin rectangle. Thickness `t = 0.02`. Flange length is `4.0`; web height is `8.0`.

```yaml
CSF:
  sections:
    S0:
      z: 0.000000
      polygons:

        flange_top@wall@t=0.02:
          weight: 1.000000
          vertices:
            # Thin horizontal strip: top flange
            # Length = 4.0, thickness = 0.02
            - [0.00, 8.00]
            - [4.00, 8.00]
            - [4.00, 8.02]
            - [0.00, 8.02]
            - [0.00, 8.00]

        web@wall@t=0.02:
          weight: 1.000000
          vertices:
            # Thin vertical strip: web
            # Height = 8.0, thickness = 0.02
            - [0.00, 0.00]
            - [0.02, 0.00]
            - [0.02, 8.00]
            - [0.00, 8.00]
            - [0.00, 0.00]

        flange_bottom@wall@t=0.02:
          weight: 1.000000
          vertices:
            # Thin horizontal strip: bottom flange
            # Length = 4.0, thickness = 0.02
            - [0.00, 0.00]
            - [4.00, 0.00]
            - [4.00, 0.02]
            - [0.00, 0.02]
            - [0.00, 0.00]

    S1:
      z: 10.000000
      polygons:

        flange_top@wall@t=0.02:
          weight: 1.000000
          vertices:
            - [0.00, 8.00]
            - [4.00, 8.00]
            - [4.00, 8.02]
            - [0.00, 8.02]
            - [0.00, 8.00]

        web@wall@t=0.02:
          weight: 1.000000
          vertices:
            - [0.00, 0.00]
            - [0.02, 0.00]
            - [0.02, 8.00]
            - [0.00, 8.00]
            - [0.00, 0.00]

        flange_bottom@wall@t=0.02:
          weight: 1.000000
          vertices:
            - [0.00, 0.00]
            - [4.00, 0.00]
            - [4.00, 0.02]
            - [0.00, 0.02]
            - [0.00, 0.00]
```

> **Note:** Polygon pairing between `S0` and `S1` is index-based. The polygon order, as read by the parser, must remain consistent.

---

### Checklist - `@wall` polygon

- [ ] Name contains `@wall`
- [ ] `vertices` defines one single closed loop
- [ ] Polygon is a thin strip: length ≫ thickness
- [ ] One polygon per physical strip: web, flange, stiffener, or similar part
- [ ] Thickness is provided via `@t=` or left for CSF to estimate as `t = 2A/P`
- [ ] Same polygon count and vertex count at `S0` and `S1`
- [ ] Section plot verified

---

## When to Use Which Tag

| Situation | Use |
|-----------|-----|
| Hollow box, tube, closed cell | `@cell` |
| Web plate, flange plate, open strip | `@wall` |
| Section is closed and walls are thin | `@cell` |
| Section is open: C, I, L, angle | `@wall`, one polygon per strip |
| Mixed section: closed cell + open stiffeners | Both tags in the same section |

---

## Multiple `@cell` Polygons

A section may contain more than one `@cell` polygon. Each `@cell` polygon defines an independent closed cell.

Use a distinct base name for each cell:

```text
cell_left@cell@t=0.02
cell_right@cell@t=0.02
```

Polygon pairing between sections remains index-based, as for all other polygons.

> **Note:** CSF computes Bredt-Batho torsion independently for each cell. If two cells share a physical wall, the shared wall must be modeled explicitly in the geometry; it cannot be inferred from two adjacent `@cell` polygons.

---

## Multiple `@wall` Polygons

A section will typically contain more than one `@wall` polygon: one per physical strip, such as web, flange, or stiffener.

There is no limit on the number of `@wall` polygons in a section. The C-section example above uses three.

Use a distinct base name for each wall polygon.

---

## Automated Geometry Generation

For complex or morphing sections, such as towers with varying geometry from base to top, geometry can be generated programmatically.

See the example script:  
[Parametric CSF Geometry Guide](https://github.com/giovanniboscu/continuous-section-field/tree/main/actions-examples/variable_tower)

This script builds multi-section YAML definitions automatically, including twist along the member axis.

---

## General Rules

- Polygon pairing between sections is **index-based**: list order, not name-based.
- The same polygon count must be maintained at every reference section.
- The same vertex count must be maintained for each paired polygon at every reference section.
- CSF does not auto-correct geometry. Invalid orientation or topology must be fixed by the user.
