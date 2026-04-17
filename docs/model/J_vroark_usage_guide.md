# `J_s_vroark` as torsional constant substitute: usage guide

## Background

CSF computes two torsion-related indicators for each cross-section station:

- **`J_s_vroark`**: Saint-Venant torsional constant estimated via Roark's formulas, using an equivalent-rectangle mapping of the net cross-section geometry.
- **`J_s_vroark_fidelity`**: a dimensionless reliability indicator in [0, 1] that measures how well the equivalent-rectangle approximation represents the actual section shape. It is computed from geometric properties of the cross-section and does not require any FEM solve.
- **`e.j`**: Saint-Venant torsional constant computed by `sectionproperties` via full FEM warping analysis. This is the reference value.

`J_s_vroark` is a fast, mesh-free estimate available at every station along the member axis without launching a FEM solve. `e.j` is accurate but requires calling `csf_sp` explicitly for each station of interest.

---

## Validation dataset

Five tapered members were analysed at three stations each (z = 0, 40, 80 m), with 50% reduction in cross-section dimensions from base to top. For each station, `J_s_vroark`, `e.j`, and — where applicable — the closed-form analytical reference were compared.

### Case 1 — Square solid section, 2.0 × 2.0 → 1.0 × 1.0 m

Analytical reference: `J = 0.1406 · a⁴` (Roark, solid square).

| z (m) | a (m) | `J_s_vroark` | `e.j` FEM | J analytical | Δ vroark / FEM | Δ FEM / analytical |
|---|---|---|---|---|---|---|
| 0 | 2.000 | 2.25333 | 2.24939 | 2.24960 | +0.175% | -0.009% |
| 40 | 1.500 | 0.71297 | 0.71171 | 0.71179 | +0.177% | -0.011% |
| 80 | 1.000 | 0.14083 | 0.14059 | 0.14060 | +0.171% | -0.007% |

`J_s_vroark_fidelity` = **1.000** (constant along the member).

*Fidelity = 1.0 for square sections — this is the reference case for which the Roark mapping is exact. FEM agrees with analytical to within 0.01%.*

---

### Case 2 — Rectangular solid section, 3.0 × 2.0 → 1.5 × 1.0 m

Analytical reference: `J = β · b · d³` with `β = 0.1958` for `b/d = 2/3` (Roark table).

| z (m) | d × b (m) | `J_s_vroark` | `e.j` FEM | J analytical | Δ vroark / FEM |
|---|---|---|---|---|---|
| 0 | 3.0 × 2.0 | 4.68593 | 4.69829 | 4.699 | +0.26% |
| 40 | 2.25 × 1.50 | 1.48266 | 1.48656 | 1.486 | +0.26% |
| 80 | 1.5 × 1.0 | 0.29287 | 0.29365 | 0.294 | +0.27% |

`J_s_vroark_fidelity` = **0.666** (constant — depends only on aspect ratio `b/d`, not scale).

*The fidelity is constant along the entire tapered member because taper is geometrically similar: b/d = 2/3 is preserved at every station. The systematic error (~0.27%) is small and consistent.*

---

### Case 3 — Circular solid section, d = 2.0 → 1.0 m

Analytical reference: `J = π · d⁴ / 32` (exact for circle).

| z (m) | d (m) | `J_s_vroark` | `e.j` FEM | J analytical | Δ vroark / FEM | Δ FEM / analytical |
|---|---|---|---|---|---|---|
| 0 | 2.000 | 1.37665 | 1.56406 | 1.57080 | **-12.1%** | -0.43% |
| 40 | 1.500 | 0.43558 | 0.49488 | 0.49701 | **-12.1%** | -0.43% |
| 80 | 1.000 | 0.08604 | 0.09775 | 0.09817 | **-12.1%** | -0.43% |

`J_s_vroark_fidelity` = **0.00051** (constant, after isoperimetric penalty).

The isoperimetric penalty correctly drives fidelity to near zero — the circle is now unambiguously flagged as inapplicable for `J_s_vroark`. Use `e.j` from sectionproperties.

The FEM error of -0.43% vs analytical is caused by the 64-vertex polygonal discretisation of the circle, not by CSF or sectionproperties.

---

### Case 4 — Thin-walled square hollow section, t = 0.05 → 0.025 m (t/d = 0.025)

Analytical reference: Bredt formula `J = 4 · A_m² · t / s_m` (valid for thin-walled closed sections).

| z (m) | d (m) | t (m) | `J_s_vroark` | `e.j` FEM | J Bredt | Δ vroark / FEM | Δ FEM / Bredt |
|---|---|---|---|---|---|---|---|
| 0 | 2.000 | 0.050 | 0.00251 | 0.37572 | 0.37080 | **-99.3%** | +1.3% |
| 40 | 1.500 | 0.038 | 0.00080 | 0.11888 | 0.11730 | **-99.3%** | +1.3% |
| 80 | 1.000 | 0.025 | 0.00016 | 0.02348 | 0.02318 | **-99.3%** | +1.3% |

`J_s_vroark_fidelity` = **0.051** (constant).

*`J_s_vroark` is off by almost two orders of magnitude. The fidelity correctly signals complete inapplicability. The FEM value `e.j` agrees with Bredt to within +1.3%, a small systematic overestimate expected for thin-walled sections at this mesh size.*

---

### Case 5 — Thick-walled square hollow section, t = 0.40 → 0.20 m (t/d = 0.20)

| z (m) | d (m) | t (m) | `J_s_vroark` | `e.j` FEM | J Bredt | Δ vroark / FEM | Δ FEM / Bredt |
|---|---|---|---|---|---|---|---|
| 0 | 2.000 | 0.400 | 0.72448 | 1.89096 | 1.638 | **-61.7%** | +15.4% |
| 40 | 1.500 | 0.300 | 0.22923 | 0.59831 | 0.518 | **-61.7%** | +15.5% |
| 80 | 1.000 | 0.200 | 0.04528 | 0.11818 | 0.102 | **-61.7%** | +15.7% |

`J_s_vroark_fidelity` = **0.471** (constant).

*The thick wall puts the section in a regime between solid and thin-walled: Bredt overestimates by +15% (it assumes thin walls), and vroark underestimates by -62%. The fidelity of 0.471 correctly places this in an intermediate, unreliable zone. Use `e.j`.*

---

## Summary table

| # | Section | Type | t/d | Fidelity | Δ vroark / FEM | Verdict |
|---|---|---|---|---|---|---|
| 1 | Square solid | solid | — | **1.000** | +0.18% | ✅ use vroark |
| 2 | Rectangular solid b/d = 2/3 | solid | — | **0.666** | +0.27% | ✅ use vroark |
| 3 | Circular solid | solid | — | **0.955** | -12.1% | ❌ use `e.j` |
| 4 | Square hollow thin wall | hollow | 0.025 | **0.051** | -99.3% | ❌ use `e.j` |
| 5 | Square hollow thick wall | hollow | 0.200 | **0.471** | -61.7% | ❌ use `e.j` |

---

## How fidelity is computed

`J_s_vroark_fidelity` combines two independent checks:

**1. Aspect-ratio score** (original): derived from the equivalent rectangle dimensions `a` and `b`. Approaches 1.0 for square sections (`a = b`), decreases for elongated sections. A rectangle 3×1 scores ~0.67, a rectangle 2×1 scores ~0.79.

**2. Isoperimetric penalty** (added in v1.x): the aspect-ratio score is blind to circular shapes — a circle and a square both have `a ≈ b` and would score equally. The penalty uses the isoperimetric ratio `Q = 4πA/P²`, which equals 1.0 only for a perfect circle and decreases for all other shapes (square: Q ≈ 0.785, rectangle 2:1: Q ≈ 0.698, ellipse: Q ≈ 0.97). When `Q > 0.90`, fidelity is scaled by `(1 - Q)`, driving it toward zero. This correctly flags circular and elliptical sections where Roark produces ~12% systematic error regardless of how compact the section looks.

| Shape | Q isoperimetric | Aspect-ratio fidelity | Final fidelity | Δ vroark/FEM |
|---|---|---|---|---|
| Circle (64 vertices) | 0.9994 | 0.955 | **0.00051** | -12.4% ❌ |
| Ellipse 4×5 m | ~0.970 | high | **~0.03** | — |
| Square 1:1 | 0.785 | 1.000 | **1.000** | +0.18% ✅ |
| Rectangle 1.5:1 | 0.723 | 0.666 | **0.666** | +0.26% ✅ |
| Rectangle 2:1 | 0.698 | 0.500 | **0.500** | +0.08% ✅ |
| Rectangle 3:1 | 0.637 | 0.333 | **0.333** | +0.03% ✅ |
| Square hollow thin | 0.785 | 0.051 | **0.051** | -99.3% ❌ |

---

## Decision rules

### When `J_s_vroark` is reliable

Use `J_s_vroark` as a substitute for `e.j` when **all** of the following conditions hold:

1. `J_s_vroark_fidelity ≥ 0.3`
2. The section is **solid** (no holes, no enclosed voids)
3. The section is **not circular or elliptical** (isoperimetric penalty will drive fidelity to near zero)

Under these conditions, the expected error is below 0.3% — decreasing as the section becomes more elongated.

> Note: fidelity reflects **section shape**, not accuracy of `J_s_vroark` for solid sections.
> A rectangle 3:1 scores fidelity 0.333 but the J error is only +0.03%.
> Low fidelity on a solid section means elongated geometry, not unreliable J.

### When to always use `e.j`

Use `e.j` (from `csf_sp`) in any of the following situations:

- The section has an **enclosed void** (hollow tube, box section, pipe) — regardless of wall thickness or fidelity
- The section is **circular or elliptical** — fidelity will appear high but vroark systematically underestimates J
- `J_s_vroark_fidelity < 0.5` — the equivalent-rectangle mapping does not represent the section geometry
- The application is **load-bearing structural design** and accuracy below 5% is required

### When to always use `e.j` regardless of fidelity

- The section has an **enclosed void** (hollow tube, box section, pipe)
- The section is **circular or elliptical** (fidelity will be near zero after isoperimetric penalty)
- `J_s_vroark_fidelity < 0.3` for any reason

---

## Practical workflow recommendation

```
For each member station along z:
  1. Read J_s_vroark and J_s_vroark_fidelity from CSF actions output
  2. If fidelity >= 0.8 AND section is solid AND section is not circular:
       → use J_s_vroark directly (fast, no FEM needed)
  3. Otherwise:
       → launch: python3 -m csf.utils.csf_sp --yaml <file>.yaml --z=<z>
       → use e.j from sectionproperties FEM output
```

For tapered members with geometrically similar cross-sections, fidelity is constant along the entire member axis. A single fidelity check at any station is sufficient to classify the entire member.

---

## Notes on `e.j` accuracy

`e.j` from `sectionproperties` is computed via FEM warping analysis. Its accuracy depends on mesh size (`mesh_sizes` parameter in `csf_sp`). The default `mesh_sizes = 1.0` was used throughout this validation. Residual errors observed:

- Solid sections: < 0.5% vs analytical
- Thin hollow sections: ~+1.3% vs Bredt (small FEM overestimate, conservative for design)
- Circular sections with 64-vertex polygon: -0.43% vs π·d⁴/32

For tighter tolerances, reduce `mesh_sizes` when calling `csf_sp`.

---

*Validation performed with CSF + sectionproperties integration (`csf_sp`). All cases use tapered members over 80 m with 50% reduction in cross-section dimensions. Stations at z = 0, 40, 80 m.*
