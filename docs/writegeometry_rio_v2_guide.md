# writegeometry_rio_v2 - User Guide

Generates a CSF-compatible YAML geometry file for a **single segment** with
two boundary cross-sections (S0 at `z0`, S1 at `z1`). The section shape is a
hollow rounded rectangle with optional reinforcement on two concentric rows and
optional degradation weight laws.

---

## Invocation

```bash
python3 -m csf.utils.writegeometry_rio_v2  [OPTIONS]  --out path/to/output.yaml
```

---

## Cross-section shape — the three cases

The shape is controlled entirely by `dx`, `dy`, and `R`.
The **same rules apply to both S0 and S1 independently.**

```
   ┌──────── dx ────────┐
   │    ╭──────────╮    │  ─┐
   │    │          │    │   │
   dy   │  inner   │   dy   │
   │    │   void   │    │   │
   │    ╰──────────╯    │   │
   └────────────────────┘  ─┘
         └── tg ──┘
```

### Case 1 — Circle

Set `R = dx/2 = dy/2`.  The four corners become full arcs and the rectangle
degenerates to a circle of diameter `dx`.  The condition `dx == dy` is not
enforced by the code, but only `dx == dy == 2*R` produces a true circle.

```bash
# Circle: diameter 1.0 m, wall thickness 0.10 m
--s0-dx 1.0  --s0-dy 1.0  --s0-R 0.5  --s0-tg 0.10
```

### Case 2 — Rounded rectangle

`0 < R < min(dx, dy) / 2`.  Standard hollow section with four rounded corners.
This is the most common case (as in the UrbanViaduct example).

```bash
# 2.0 × 1.0 m, corner radius 0.20 m, wall 0.20 m
--s0-dx 2.0  --s0-dy 1.0  --s0-R 0.20  --s0-tg 0.20
```

### Case 3 — Sharp rectangle

`R = 0`.  Perfectly square corners.

> **Constraint:** with `R = 0` rebar placement will fail if
> `n_bars_row1 > 0`.  Either set `n_bars_row1 = 0` or use
> `R >= dist_row1_outer` (see Rebar section below).

```bash
# 2.0 × 1.0 m sharp rectangle, no rebar
--s0-dx 2.0  --s0-dy 1.0  --s0-R 0.0  --s0-tg 0.20
--n-bars-row1 0  --n-bars-row2 0
--dist-row1-outer 0.0  --dist-row2-inner 0.0
```

---

## Solid vs hollow section

The inner void is derived automatically:

```
inner_dx = dx - 2 * tg
inner_dy = dy - 2 * tg
inner_R  = max(R - tg, 0)
```

To obtain a **solid section** set `tg >= min(dx, dy) / 2`.
The inner contour collapses and the polygon encodes the full solid cross-section.

```bash
# Solid 1.0 × 1.0 m square — tg = 0.5 = dx/2
--s0-dx 1.0  --s0-dy 1.0  --s0-R 0.1  --s0-tg 0.5
```

---

## Complete parameter reference

### Longitudinal coordinates

| Argument | Required | Description |
|----------|----------|-------------|
| `--z0`   | ✓ | Bottom elevation of the segment [m] |
| `--z1`   | ✓ | Top elevation — must be > z0 [m] |

### Section geometry (S0 and S1 independently)

| Argument | Required | Description |
|----------|----------|-------------|
| `--s0-x`, `--s0-y` | ✓ | Centroid coordinates of S0 [m] |
| `--s0-dx`, `--s0-dy` | ✓ | Outer bounding rectangle dimensions [m] |
| `--s0-R` | ✓ | Corner radius — `0` → sharp, `dx/2=dy/2` → circle |
| `--s0-tg` | ✓ | Wall thickness [m] |
| `--s0-t-cell` | ✓ | Cell-thickness tag — use `0` if not needed (see below) |
| `--s1-*` | ✓ | Same parameters for the top section S1 |

### Discretisation

| Argument | Required | Description |
|----------|----------|-------------|
| `--N` | ✓ | Number of points along the perimeter of each loop |
| `--singlepolygon` | ✓ | `true` → single-polygon encoding (recommended); `false` → two separate polygons |
| `--twist-deg` | — | Rotation of S1 relative to S0 [degrees], default 0 |

### Reinforcement

Row 1 follows the **outer contour** inward by `dist_row1_outer`.
Row 2 follows the **inner contour** outward by `dist_row2_inner`.

| Argument | Required | Description |
|----------|----------|-------------|
| `--n-bars-row1` | ✓ | Number of bars in outer row (`0` = no outer row) |
| `--n-bars-row2` | ✓ | Number of bars in inner row (`0` = no inner row) |
| `--area-bar-row1` | ✓ | Area of one bar, outer row [m²] |
| `--area-bar-row2` | ✓ | Area of one bar, inner row [m²] |
| `--dist-row1-outer` | ✓ | Cover + bar radius from outer face [m] |
| `--dist-row2-inner` | ✓ | Cover + bar radius from inner void face [m] |
| `--rebar-weight` | ✓ | Homogenisation weight for all bars (`1.0` = steel, `0.0` = ignore) |

> **Constraint — minimum R for rebar:**
> `R` must be ≥ `dist_row1_outer` when `n_bars_row1 > 0`.
> If `R = 0` and bars are requested the script raises a `ValueError`.

### Degradation weight laws (optional)

Weight laws instruct the CSF engine to interpolate a property (area, stiffness)
along the segment according to a named law.  They are appended as a
`weight_laws` list in the YAML and linked by polygon name.

| Argument | Default | Description |
|----------|---------|-------------|
| `--bars-row1-law` | `""` | Law name for each bar in row 1 |
| `--bars-row2-law` | `""` | Law name for each bar in row 2 |
| `--s0-law` | `""` | Law name for the shell polygon |
| `--s1-law` | `""` | Must equal `--s0-law` — the shell is one paired entry |

The law string is written verbatim into the YAML.  Common values: `"linear"`,
`"quadratic"`, or any law identifier understood by the CSF reader.

When a law is provided each polygon gets its own explicit entry:

```yaml
weight_laws:
  - rebar_row1_1,rebar_row1_1: linear
  - rebar_row1_2,rebar_row1_2: linear
  ...
  - cell_base@cell,cell_head@cell: linear
```

### Cell-thickness tag (`--s0-t-cell`, `--s1-t-cell`)

When non-zero, the cell polygon name receives an `@t=value` suffix:

```yaml
# t-cell = 0      →  cell_base@cell
# t-cell = 0.35   →  cell_base@cell@t=0.35
```

This tag is used by the CSF engine to identify which cell-thickness value is
associated with the degradation law.  Set to `0` when no degradation law is
applied to the shell.

---

## Worked examples

### 1 — Circular hollow section, single rebar row

```bash
python3 -m csf.utils.writegeometry_rio_v2 \
  --z0 0.0   --z1 10.0 \
  --s0-x 0   --s0-y 0   --s0-dx 1.0  --s0-dy 1.0  --s0-R 0.5  --s0-tg 0.10  --s0-t-cell 0 \
  --s1-x 0   --s1-y 0   --s1-dx 0.8  --s1-dy 0.8  --s1-R 0.4  --s1-tg 0.08  --s1-t-cell 0 \
  --N 64  --singlepolygon true \
  --n-bars-row1 12  --n-bars-row2 0 \
  --area-bar-row1 0.000314  --area-bar-row2 0.000314 \
  --dist-row1-outer 0.05    --dist-row2-inner 0.0 \
  --rebar-weight 1.0 \
  --out circle.yaml
```

### 2 — Sharp rectangle, no rebar

`R = 0` is only valid when both rebar rows are disabled.

```bash
python3 -m csf.utils.writegeometry_rio_v2 \
  --z0 0.0   --z1 10.0 \
  --s0-x 0   --s0-y 0   --s0-dx 2.0  --s0-dy 1.0  --s0-R 0.0  --s0-tg 0.20  --s0-t-cell 0 \
  --s1-x 0   --s1-y 0   --s1-dx 1.6  --s1-dy 0.8  --s1-R 0.0  --s1-tg 0.15  --s1-t-cell 0 \
  --N 64  --singlepolygon true \
  --n-bars-row1 0  --n-bars-row2 0 \
  --area-bar-row1 0.000314  --area-bar-row2 0.000314 \
  --dist-row1-outer 0.0     --dist-row2-inner 0.0 \
  --rebar-weight 1.0 \
  --out rect_sharp.yaml
```

### 3 — Rounded rectangle, two rebar rows

```bash
python3 -m csf.utils.writegeometry_rio_v2 \
  --z0 0.0   --z1 10.0 \
  --s0-x 0   --s0-y 0   --s0-dx 2.0  --s0-dy 1.0  --s0-R 0.20  --s0-tg 0.20  --s0-t-cell 0 \
  --s1-x 0   --s1-y 0   --s1-dx 1.6  --s1-dy 0.8  --s1-R 0.15  --s1-tg 0.15  --s1-t-cell 0 \
  --N 64  --singlepolygon true \
  --n-bars-row1 16  --n-bars-row2 12 \
  --area-bar-row1 0.000491  --area-bar-row2 0.000314 \
  --dist-row1-outer 0.05    --dist-row2-inner 0.04 \
  --rebar-weight 1.0 \
  --out rounded_rect.yaml
```

### 4 — Rounded rectangle with degradation laws on bars and shell

`--s0-law` and `--s1-law` must be **identical**.

```bash
python3 -m csf.utils.writegeometry_rio_v2 \
  --z0 0.0   --z1 10.0 \
  --s0-x 0   --s0-y 0   --s0-dx 2.0  --s0-dy 1.0  --s0-R 0.20  --s0-tg 0.20  --s0-t-cell 0.20 \
  --s1-x 0   --s1-y 0   --s1-dx 1.6  --s1-dy 0.8  --s1-R 0.15  --s1-tg 0.15  --s1-t-cell 0.15 \
  --N 64  --singlepolygon true \
  --n-bars-row1 16  --n-bars-row2 12 \
  --area-bar-row1 0.000491  --area-bar-row2 0.000314 \
  --dist-row1-outer 0.05    --dist-row2-inner 0.04 \
  --rebar-weight 1.0 \
  --bars-row1-law "linear" \
  --bars-row2-law "linear" \
  --s0-law "linear"  --s1-law "linear" \
  --out degradation.yaml
```

### 5 — Twisted top section (morphing tower)

`--twist-deg` rotates only S1.  S0 is always at 0°.

```bash
python3 -m csf.utils.writegeometry_rio_v2 \
  --z0 0.0   --z1 10.0 \
  --s0-x 0   --s0-y 0   --s0-dx 2.0  --s0-dy 1.0  --s0-R 0.20  --s0-tg 0.20  --s0-t-cell 0 \
  --s1-x 0   --s1-y 0   --s1-dx 2.0  --s1-dy 1.0  --s1-R 0.20  --s1-tg 0.20  --s1-t-cell 0 \
  --twist-deg 45 \
  --N 64  --singlepolygon true \
  --n-bars-row1 16  --n-bars-row2 0 \
  --area-bar-row1 0.000314  --area-bar-row2 0.000314 \
  --dist-row1-outer 0.05    --dist-row2-inner 0.0 \
  --rebar-weight 1.0 \
  --out twist45.yaml
```

---

## Constraints and error conditions

| Condition | Error raised |
|-----------|-------------|
| `z1 <= z0` | `ValueError: z1 must be > z0` |
| `R < dist_row1_outer` with `n_bars_row1 > 0` | `ValueError: Invalid rounded-rectangle offset` |
| `s0_law != s1_law` (both non-empty) | `ValueError: s0_law and s1_law must match` |
| `n_bars < 0` | `ValueError: number of bars must be >= 0` |
| `area_bar <= 0` | `ValueError: single-bar areas must be > 0` |

---

## YAML output structure

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        cell_base@cell:          # main hollow polygon (singlepolygon=true)
          weight: 1.0
          vertices: [[x0,y0], [x1,y1], ...]
        rebar_row1_1:            # one entry per bar
          weight: 1.0
          vertices: [[xa,ya], ...]
        rebar_row2_1:
          weight: 1.0
          vertices: [...]
    S1:
      z: 10.0
      polygons: { ... }          # same structure
  weight_laws:                   # only present when laws are specified
    - rebar_row1_1,rebar_row1_1: linear
    - cell_base@cell,cell_head@cell: linear
```
