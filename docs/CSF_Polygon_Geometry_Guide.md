# CSF Polygon Geometry Guide: `@cell` and `@wall`

This guide covers the **geometric construction** of tagged polygons in CSF.  
It does not describe the underlying torsion calculations - those are documented in the [section analysis reference](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/sectionfullanalysis.md).

---

## Overview

CSF supports two torsion-related polygon tags:

| Tag | Section type | Loop structure |
|-----|-------------|----------------|
| `@cell` | Closed thin-walled cell | Two loops in one polygon (outer + inner) |
| `@wall` | Open thin-walled strip | One loop per polygon |

The tag is embedded directly in the polygon name key in the YAML definition.  
Tags control which calculation path CSF uses - they do not affect geometric pairing or interpolation rules.

---

## Part 1 - `@cell`: Closed Cell Polygon

### Concept

A `@cell` polygon defines a **closed thin-walled cell** for Saint-Venant torsion (Bredt–Batho method).

The geometry is encoded as **one single polygon** containing **two loops**:

- an **outer loop** - the external boundary of the cell wall
- an **inner loop** - the internal void boundary

The two loops are connected by a **bridge**: a segment that moves the path from one loop to the other. The bridge has no geometric meaning - it is just a traversal step.

The net area of the polygon (outer area minus inner area) must be **positive**.  
This is the only strict geometric constraint.

> **Always verify the result with a section plot before using it in analysis.**

---

### Construction Rules

#### Loop orientation

The standard convention is:

- outer loop → **CCW** (counter-clockwise) → positive area contribution
- inner loop → **CW** (clockwise) → negative area contribution

The net signed area (CCW + CW) must be positive.

The reverse is also valid - start from the inner loop CW, bridge out, close outer CCW - as long as the net area is positive.

#### The bridge

The bridge is a segment connecting the end of one loop to the start of the other.  
It is a traversal step only - it moves the path from one loop to the other.

#### Vertex sequence (standard pattern)

```
start at a point on the outer boundary
→ traverse outer loop CCW (return to start)
→ bridge: move to a point on the inner boundary
→ traverse inner loop CW (return to inner start)
```

---

### Thickness: `@t=`

The wall thickness `t` can be:

- **specified explicitly** in the polygon name: `@t=<value>` (e.g. `@cell@t=0.03`)
- **omitted**: CSF estimates it as `t = 2A / P` where `A` is the cell area and `P` is the total perimeter

If thickness is specified at both `S0` and `S1`, CSF interpolates linearly along `z`.  
If specified at only one section, it is treated as constant.

---

### Naming Syntax

```
<base_name>@cell
<base_name>@cell@t=<value>
```

Examples:

```
box_section@cell
box_section@cell@t=0.03
wall_outer@cell@t=0.015
```

The base name is used for polygon pairing across sections (index-based). Tags are metadata only.

---

### Example 1 - Rectangular Hollow Box

A rectangular box section: outer `10 × 6`, inner void `4 × 2` offset from corner.

```
Outer (CCW):  (0,0) → (10,0) → (10,6) → (0,6) → (0,0)
Bridge:       (0,0) → (3,2)
Inner (CW):   (3,2) → (3,4) → (7,4) → (7,2) → (3,2)
```

Net area: `A_outer - A_inner = 60 - 8 = 52`

```yaml
CSF:
  sections:
    S0:
      z: 0.000000
      polygons:
        box@cell@t=0.03:
          weight: 1.000000
          vertices:
            # OUTER loop (CCW)
            - [0.0, 0.0]
            - [10.0, 0.0]
            - [10.0, 6.0]
            - [0.0, 6.0]
            - [0.0, 0.0]
            # bridge to inner start
            - [3.0, 2.0]
            # INNER loop (CW)
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
            # OUTER loop (CCW)
            - [0.0, 0.0]
            - [10.0, 0.0]
            - [10.0, 6.0]
            - [0.0, 6.0]
            - [0.0, 0.0]
            # bridge to inner start
            - [3.0, 2.0]
            # INNER loop (CW)
            - [3.0, 4.0]
            - [7.0, 4.0]
            - [7.0, 2.0]
            - [3.0, 2.0]
```



---

### Checklist - `@cell` polygon

- [ ] Name contains `@cell`
- [ ] `vertices` encodes exactly two loops (outer + inner)
- [ ] Outer loop is CCW, inner loop is CW (or reversed, as long as net area is positive)
- [ ] Net area is positive
- [ ] Thickness provided via `@t=` or left for CSF to estimate (`t = 2A/P`)
- [ ] Same polygon count and vertex count at `S0` and `S1`
- [ ] Section plot verified

---

## Part 2 - `@wall`: Open Section Strip

### Concept

A `@wall` polygon defines an **open thin-walled strip** - a web, flange, or plate - for open-section torsion.

Unlike `@cell`, each `@wall` polygon encodes **one single closed loop**.  
There is no inner loop, no bridge, no void.

The polygon must represent a **thin elongated strip**: its length must be much larger than its thickness. The formula `J ≈ b t³ / 3` (thin strip approximation) is only valid when this condition holds.

> Do not use `@wall` for compact or block-like shapes. The result will not be physically meaningful.

---

### Construction Rules

- Define the strip as a standard closed CCW polygon.
- The polygon should look like an offset of a centerline: two long parallel sides, two short closing ends.
- One polygon per strip patch (web, flange, stiffener). Do not combine multiple strips in one polygon.

---

### Thickness: `@t=`

- **Specified**: `@t=<value>` in the polygon name (recommended for complex or irregular strips).
- **Omitted**: CSF estimates `t = 2A / P`. This is a rough geometric proxy - use explicit `@t=` when the strip is not a clean rectangle.

---

### Naming Syntax

```
<base_name>@wall
<base_name>@wall@t=<value>
```

Examples:

```
web@wall@t=0.02
flange_top@wall@t=0.015
stiffener@wall
```

---

### Example 2 - C-Section (Three Strips)

A C-section modeled as three separate `@wall` strips: top flange, web, bottom flange.

```
Section layout (approximate):

  ┌────────────────┐   ← top flange
  │                
  │                    ← web
  │                
  └────────────────┘   ← bottom flange
```

Each strip is a thin rectangle. Thickness `t = 0.02`. Flange length `= 4.0`, web height `= 8.0`.

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

        web@wall@t=0.02:
          weight: 1.000000
          vertices:
            # Thin vertical strip: web
            # Height = 8.0, thickness = 0.02
            - [0.00, 0.00]
            - [0.02, 0.00]
            - [0.02, 8.00]
            - [0.00, 8.00]

        flange_bottom@wall@t=0.02:
          weight: 1.000000
          vertices:
            # Thin horizontal strip: bottom flange
            # Length = 4.0, thickness = 0.02
            - [0.00, 0.00]
            - [4.00, 0.00]
            - [4.00, 0.02]
            - [0.00, 0.02]

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

        web@wall@t=0.02:
          weight: 1.000000
          vertices:
            - [0.00, 0.00]
            - [0.02, 0.00]
            - [0.02, 8.00]
            - [0.00, 8.00]

        flange_bottom@wall@t=0.02:
          weight: 1.000000
          vertices:
            - [0.00, 0.00]
            - [4.00, 0.00]
            - [4.00, 0.02]
            - [0.00, 0.02]
```

> **Note:** Polygon pairing between `S0` and `S1` is index-based - the order in the list must be consistent.

---

### Checklist - `@wall` polygon

- [ ] Name contains `@wall`
- [ ] `vertices` defines one single closed loop (no inner loop, no bridge)
- [ ] Polygon is a thin strip: length ≫ thickness
- [ ] One polygon per physical strip (web, flange, etc.)
- [ ] Thickness provided via `@t=` (recommended) or left for CSF to estimate
- [ ] Same polygon count and vertex count at `S0` and `S1`
- [ ] Section plot verified

---

## When to Use Which Tag

| Situation | Use |
|-----------|-----|
| Hollow box, tube, closed cell | `@cell` |
| Web plate, flange plate, open strip | `@wall` |
| Section is closed and walls are thin | `@cell` |
| Section is open (C, I, L, angle) | `@wall` (one polygon per strip) |
| Mixed: closed cell + open stiffeners | Both tags in the same section |

## Multiple @cell polygons (multi-cell sections)

A section may contain more than one `@cell` polygon. Each polygon defines an independent closed cell.

Use a distinct base name for each cell:
cell_left@cell@t=0.02
cell_right@cell@t=0.02
Polygon pairing between sections remains index-based, as for all other polygons.

> **Note:** CSF computes Bredt–Batho torsion independently for each cell. If two cells share a physical wall, the shared wall must be modeled explicitly in the geometry — it cannot be inferred from two adjacent `@cell` polygons.


## Multiple @wall polygons

A section will typically contain more than one `@wall` polygon — one per physical strip (web, flange, stiffener).

There is no limit on the number of `@wall` polygons in a section. The C-section example above uses three.

Use a distinct base name for each

---

## Automated Geometry Generation

For complex or morphing sections (e.g. towers with varying geometry from base to top), geometry can be generated programmatically.

See the example script:  
[Parametric CSF Geometry Guide](https://github.com/giovanniboscu/continuous-section-field/tree/main/actions-examples/variable_tower)

This script builds multi-section YAML definitions automatically, including twist along the member axis.

---

## General Rules (Both Tags)

- Polygon pairing between sections is **index-based** (list order), not name-based.
- The same vertex count must be maintained at every reference section for each polygon.

- CSF does not auto-correct geometry. Invalid orientation or topology must be fixed by the user.
