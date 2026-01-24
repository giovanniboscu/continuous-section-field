# CSF – Torsional Constant Policy (README-P)

## Purpose

This document defines **how the Saint-Venant torsional constant is computed and selected in CSF** (Continuous Section Field), and **why multiple torsional indicators exist**.

The goal is **physical correctness, geometric consistency, and solver independence**, avoiding ad‑hoc rules tied to specific profile families (I, H, tube, etc.).

The policy described here is the result of systematic validation against:
- classical thin‑walled theory,
- closed‑cell torsion (Bredt / Batho),
- standard steel sections (e.g. IPE 600),
- CSF’s polygon‑based geometric representation.

---

## Background

In CSF, cross‑sections are described as **sets of polygons** carrying a scalar `weight`.

- Polygons represent **geometric domains**, not predefined beam types.
- `weight` acts as a **scalar multiplier** (e.g. modular ratio, material factor).

Because of this design:
- CSF **cannot rely on profile‑specific formulas** (e.g. “if I‑section then …”),
- torsional properties must be derived **from geometry alone**,
- the validity domain of each torsional model must be **explicitly controlled**.

This leads to the introduction of **multiple torsional quantities**, each valid in a specific regime.

---

## Torsional Quantities in CSF

CSF may compute up to three torsional indicators.

---

### 1. `J_sv` — Saint‑Venant torsional constant (engineering)

**Intended use**: open thin‑walled sections.

Classical thin‑walled approximation (plain‑text form):

J ≈ sum( b_i * t_i^3 / 3 )

where:
- t_i = equivalent strip thickness
- b_i = midline length of the strip

In CSF:
- each polygon is treated as a *candidate thin strip*,
- an equivalent thickness is estimated as:

  t ≈ 2 * A / P

- a corresponding midline length is estimated as:

  b ≈ A / t

**Important notes**:
- This model is meaningful **only if the polygon represents a thin lamina**.
- It is the **reference torsional constant for open sections**.

Typical use cases:
- I, H, U, L steel sections,
- plate‑built thin‑walled members,
- validation against tabulated open‑section torsional constants.

---

### 2. `J_s_vroark` — Closed‑cell torsional constant (Bredt / Roark)

**Intended use**: closed thin‑walled cells.

Single‑cell Bredt–Batho formula (plain‑text form):

J ≈ 4 * A_cell^2 * t / P_mean

where:
- A_cell = area enclosed by the wall midline
- t = wall thickness
- P_mean = mean perimeter of the cell

In CSF:
- closed cells are detected **geometrically**, not by polygon count,
- outer and inner contours are identified by containment tests,
- the inner contour area is used as a robust proxy for A_cell.

**Important notes**:
- This model is **not valid for open sections**.
- It is automatically ignored if the closed‑cell assumptions are not met **

Typical use cases:
- tubes and box sections,
- hollow piles,
- thin‑walled closed steel shells.

---

### 3. `K_torsion` — Semi‑empirical fallback

Always defined, but low fidelity.

Plain‑text approximation:

K ≈ A^4 / (40 * Ip)

where:
- Ip = Ix + Iy

**Notes**:
- Used only as a **last‑resort fallback**.
- Not intended for accurate torsional modelling.

---

## Fidelity Index

`J_s_vroark_fidelity` is a **dimensionless reliability indicator** in the range [0, 1].

It measures whether the assumptions behind closed‑cell torsion are satisfied.

It accounts for:
- thin‑walled ratio (t / R),
- geometric regularity,
- applicability of Roark‑style corrections.

Interpretation guideline:

- > 0.6  → closed‑cell model applicable
- 0.3–0.6 → borderline validity
- < 0.3  → outside validity domain

---

## Selection Policy (Core of CSF)

CSF **never blindly trusts a single torsional formula**.

The torsional constant exposed to solvers or reports is selected according to the following logic.

---

### Step 1 — Closed‑cell check

If:
- a closed cell is detected **geometrically**, and
- J_s_vroark_fidelity ≥ threshold (recommended: 0.6),

then:

→ **Use `J_s_vroark`**

---

### Step 2 — Open‑section case

If no closed cell is detected **or** fidelity is below threshold:

→ **Use `J_sv`**

This applies to:
- IPE / HE / UPN sections,
- any section that does not enclose an area.

---

### Step 3 — Fallback

If neither model produces a valid value:

→ **Use `K_torsion` as a fallback**, with a warning.

---

## Example: IPE 600 Validation

For an IPE 600 modelled with:
- exact flange and web dimensions,
- internal fillet approximation,
- open geometry,

CSF produces:
- J_sv ≈ 1.3e‑6 m^4  → consistent with tabulated It
- J_s_vroark ≈ 3.1e‑5 m^4 with fidelity = 0.16 → automatically discarded

This confirms:
- correct geometric modelling,
- correct open‑section torsion handling,
- correct gating of closed‑cell formulas.

---

## Design Principles

This policy ensures that CSF:
- is **geometry‑driven**, not profile‑driven,
- avoids hidden assumptions,
- exposes validity domains explicitly,
- supports meaningful numerical comparisons,
- keeps torsion **solver‑independent**.

---

## Final Note

If a different torsional interpretation is required (e.g. warping torsion, Vlasov theory, composite interaction), it must be implemented **as a separate model**, not by weakening these rules.

This document defines the **baseline, defensible torsional behaviour** of CSF.
