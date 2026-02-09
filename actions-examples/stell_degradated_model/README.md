# CSF Example: Closed-Cell CHS with Splash-Zone Weight Law

This example demonstrates a **reproducible CSF workflow** for a circular hollow steel member (CHS), using:

- `@cell` closed-cell torsion (`J_sv_cell`, Bredt-Batho),
- explicit wall thickness tag `@t=...`,
- a position-dependent degradation law `w(z)`.

It is suitable as a repository example because it is simple, transparent, and numerically self-consistent.

---

## 1) Problem setup

We model a tubular steel member (MP-1) with nominal geometry:

- Outer diameter: `Do = 1.80 m`
- Inner diameter: `Di = 1.70 m`
- Member length: `L = 85.0 m`

So the wall thickness is deterministic:

```text
t = (Do - Di) / 2 = (1.80 - 1.70) / 2 = 0.05 m
```

That is why the polygon tag is:

```text
@t=0.05
```

---

## 2) Why `@cell` is used

The section is a **closed thin-walled ring**, so `@cell` is the correct modeling mode for closed-cell Saint-Venant torsion using a Bredt-Batho style formulation.

Example naming:

- Outer polygon: `MP1_outer@cell@t=0.05`
- Inner polygon: `MP1_inner`

---

## 3) Weight law used in this example

We apply a splash-zone-like law:

```python
1.0 - 0.28 * np.exp(-((z - 0.0)**2) / (2.0 * 1.5**2))
```

Parameters:

- `beta = 0.28` (max reduction amplitude),
- `z0 = 0.0 m` (critical elevation center),
- `sigma = 1.5 m` (critical band width).

Interpretation:

- At `z = 0`, `w = 0.72` (maximum degradation in this scenario).
- Far from `z0`, `w -> 1.0` (nominal behavior).

> Note: this is a **scenario law**, not a site-calibrated measurement unless validated with field inspection data.

---

## 4) Inspector verification (expected)

For this exact formula and `L=85`:

- `z = 0.0`  -> expected `w = 0.72`
- `z = 85.0` -> expected `w ≈ 1.0`

Example inspector output confirms:

- `RESULT W: 0.72` at `z=0`
- `RESULT W: 1` at `z=85`

---

## 5) Section-analysis consistency checks

### At z = 85.0 (near nominal, w ≈ 1)

Observed:

- `A = 0.27477898`
- `Ix = Iy = 0.10523243`
- `J_sv_cell = 0.21031429`

Checks:

- For a circular ring, `Ix = Iy` (expected by symmetry).
- `J` is close to `Ix + Iy` for this geometry/discretization:
  - `Ix + Iy = 0.21046486`
  - close to computed `J_sv_cell = 0.21031429` (small discretization difference).

### At z = 0.0 (w = 0.72)

Observed:

- `A = 0.19784086`
- `Ix = Iy = 0.07576735`
- `J_sv_cell = 0.15142629`

Ratios vs nominal section (`z=85`) are all approximately `0.72`, consistent with applied law in this workflow.

---

## 6) Critical implementation notes

### 6.1 `@t` unit is meters

`@t=1.0` would be physically wrong for this case and can inflate torsional results drastically.  
For MP-1, use `@t=0.05`.

### 6.2 Name matching with model tags

When matching law references by polygon name, normalize names by removing suffixes from:

- `@cell`
- `@wall`
- `@closed`

Example normalization:

- `MP1_outer@cell@t=0.05` -> `MP1_outer`

### 6.3 Keep name logic deterministic

A robust approach is:

- parse/normalize names once for matching,
- then use polygon indices for actual law assignment.

### 6.4 Self-intersection warnings and tagged polygons

If your encoding intentionally uses tagged/modeling polygons that may trigger generic checks, you can skip warning emission for names containing `@cell/@wall/@closed` in that specific diagnostic path.

---

## 8) Reproducibility checklist

- [x] Explicit geometry (`Do`, `Di`, `L`)
- [x] Explicit thickness tag (`@t=0.05`)
- [x] Explicit law formula (`w(z)`)
- [x] Inspector values at two reference positions
- [x] Section outputs consistent with law behavior
- [x] Naming normalization rules documented

---

## 9) Engineering interpretation

This example represents a **localized degradation scenario** near `z=0`:

- not full collapse,
- not uniform deterioration,
- not a calibrated as-built condition unless tied to inspection data.

Use it as a clear reference implementation for:

- CSF law wiring,
- closed-cell torsion pipeline validation,
- regression tests in CI.

---

## 10) Suggested repository placement

Recommended files:

- `examples/mp1_cell_wlaw/README.md` (this document)
- `examples/mp1_cell_wlaw/mp1_geometry.yaml`
- `examples/mp1_cell_wlaw/mp1_actions.yaml`
- optional: `examples/mp1_cell_wlaw/expected_outputs.txt`

This structure makes validation and future regression checks straightforward.
