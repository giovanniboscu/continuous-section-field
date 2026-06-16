# CSF - Section Full Analysis Output

This document explains **all quantities reported by the CSF _Section Full Analysis_**. It is intended as a clear, engineering-oriented reference for users who want to:

- understand what each value represents,
- know how it is computed in CSF,
- understand the **validity domain and limitations** of each quantity.

Whenever a quantity depends on a specific modelling choice or policy defined elsewhere (e.g. torsion selection rules), this is explicitly noted.

[CSF–sectionproperties mapping table](#csfsectionproperties-mapping-table)

---

## General Notes
CSF computes section quantities from polygon geometry and scalar participation fields. `weight` defines the axial/bending participation field $w_i$ and is used for `A`, `Cx`, `Cy`, flexural inertias, section moduli, and related weighted sectional properties. `shear_weight` defines the shear/torsion participation field $k_i$ and is used for shear/torsion-related quantities where required. Weights act as scalar multipliers and do not modify polygon geometry; no assumptions are made about profile families.


---

## Section property quantities (1–15)

### 1. Area (A)

**Key:** `A`

**Definition** - Total cross-sectional area, including the effect of polygon weights.

`A = Σ_i ( w_i · A_i )`

where `A_i` is the signed area of polygon `i` and `w_i` is the polygon weight.

**Notes**
- Can be reduced or increased by weighted sub-domains.
- Must be non-zero for a valid section.

### 2. Centroid Cx

**Key:** `Cx`

Horizontal coordinate of the geometric centroid.

`Cx = Σ_i ( w_i · A_i · x_i ) / Σ_i ( w_i · A_i )`

### 3. Centroid Cy

**Key:** `Cy`

Vertical coordinate of the geometric centroid.

`Cy = Σ_i ( w_i · A_i · y_i ) / Σ_i ( w_i · A_i )`

### 4. Inertia Ix

**Key:** `Ix`

Second moment of area about the centroidal X-axis. Computed using Green's theorem with parallel-axis correction.

### 5. Inertia Iy

**Key:** `Iy`

Second moment of area about the centroidal Y-axis.

### 6. Inertia Ixy

**Key:** `Ixy`

Product of inertia about centroidal axes.

### 7. Polar Moment (Ip)

**Key:** `Ip`

Polar second moment of area:

`Ip = Ix + Iy`

**Notes**
- Purely geometric.
- **Not** a torsional stiffness for non-circular sections.

### 8. Principal Inertia I1

**Key:** `I1`

Major principal second moment of area.

### 9. Principal Inertia I2

**Key:** `I2`

Minor principal second moment of area.

### 10. Radius of Gyration rx

**Key:** `rx`

`rx = sqrt( Ix / A )`

Represents the distribution of area relative to the X-axis.

### 11. Radius of Gyration ry

**Key:** `ry`

`ry = sqrt( Iy / A )`

### 12. Elastic Section Modulus Wx

**Key:** `Wx`

Elastic section modulus for bending about the X-axis.

`Wx = Ix / c_y,max`

where `c_y,max` is the maximum distance from the centroid to the extreme fibres.

### 13. Elastic Section Modulus Wy

**Key:** `Wy`

Elastic section modulus for bending about the Y-axis.

`Wy = Iy / c_x,max`

### 14. Torsional Rigidity K

**Key:** `K_torsion`

Semi-empirical torsional stiffness approximation.

`K ≈ A^4 / ( 40 · Ip )`,  with `Ip = Ix + Iy`.

**Notes**
- Always defined.
- Low physical fidelity.

### 15. First Moment of Area (Q_na)

**Key:** `Q_na`

First moment of area of the portion of the section located on one side of the neutral axis (used in shear-stress evaluation).

Let the neutral axis be the centroidal axis `y = 0`. Then:

`Q_na(z) = Σ_i w_i(z) · ∫_{A_i(y > 0)} y dA`

where the integral is taken over the sub-area above the neutral axis (the lower portion may equivalently be used in absolute value).

**Notes**
- Over the entire section, `∫_A y dA = 0` for centroidal axes; `Q_na` is therefore computed over a **partial** area, not the full section.
- Typical use in shear-stress estimation: `tau = V · Q / ( I · b )`, where `Q` is the first moment of the sub-area cut by the neutral axis, evaluated consistently with the same weighted section model.

---

## Torsion constants (16–19)

The torsional constants computed from polygons tagged `@cell` or `@wall` are CSF thin-wall estimates. They provide fast geometry-based approximations and, depending on the polygon geometry, may reach a very acceptable level of accuracy. The assessment of applicability and accuracy remains the user's responsibility. For a more complete torsional analysis, CSF can be coupled with `sectionproperties` through the `csf_sp` bridge.

CSF reports several torsion-related quantities; use the right one for the geometry:

- **`J_sv_cell` / `J_sv_wall`** (§16–17) - thin-walled estimates for sections tagged as closed cells / open walls.
- **`J_s_vroark`** (§18) - equivalent-rectangle estimate for compact solid sections (tag-free).
- **`K_torsion`** (§14) - low-fidelity empirical fallback, always defined.

For the validity hypotheses of the cell–wall summation, see [Saint-Venant Torsional Constant - CSF summation assumptions](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md).

### Tags: `@cell` and `@wall`

In CSF, `@cell` and `@wall` are **tags applied to polygon names**. They classify specific polygons for dedicated thin-walled torsion calculations:

- `@cell` → polygon is treated as a **closed thin-walled cell**
- `@wall` → polygon is treated as an **open thin-walled wall**

These tags are **not geometric operations**: they do not modify the shape. They only define which polygons are included in the corresponding torsional path.

**Selection rule** (case-insensitive):

- Cell path: name contains `@cell` or `@closed`
- Wall path: name contains `@wall`

All other polygons are **ignored** by these functions and do not contribute to `J_sv`.

> In section-analysis outputs, `J_sv_cell` and `J_sv_wall` may carry the torsional contribution together with the associated thickness parameter `t` when the tagged geometry is represented by a single polygon.

**Behavior.** `J_sv` (both `@cell` and `@wall`) is computed exclusively from the tagged polygons:

- only their **midline geometry** and **thickness** are used;
- each tagged polygon is treated as an **independent entity**;
- there is **no interaction** with other polygons (including nesting/composition).

Any additional polygons or inclusions (e.g. rebars, inner shapes):

- do **not** modify the wall path,
- do **not** contribute to `J_sv`,
- may still contribute to homogenized/global properties (`A`, `Ix`, `Iy`, …).

**Example.**

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        outer@cell:
          weight: 1.0
          # Thin-walled slit-cell example.
          # The outer loop is a 3x3 rectangle written in CCW order.
          # The repeated point [2.0, 3.0] explicitly closes the outer loop.
          # After that, the vertex stream continues with the inner loop.
          # The inner polygon is  kept very close to the outer boundary
          # so that the section represents a genuinely thin profile.
          # The inner loop is written in CW order.
          vertices:
            # Outer loop (CCW)
            - [2.0, 3.0]
            - [2.0, 2.0]
            - [5.0, 2.0]
            - [5.0, 5.0]

```

Interpretation:

- `outer_shell@cell` → used to compute `J_sv_cell`
- `inner_void` → ignored in `J_sv_cell` (even if inside)
- `rebar_row_*` → ignored in `J_sv_cell`, but included in `A`, `Ix`, `Iy`

**Key point.** `@cell` / `@wall` define **which polygons enter the torsional model**, not how the global geometry is composed.

![softwarex_props](https://github.com/user-attachments/assets/c4b03d5c-544c-4d18-9821-e05facd651b7)

### Thickness handling

A thickness may be encoded in the polygon name as `...@t=<value>` (metres, e.g. `...@t=0.010`). Parsing rules: `@t=` is case-insensitive; parsing stops at the first character not in `0–9 . + - e E`; the thickness must be strictly positive (`t > 0`) or it is rejected.

**Priority.** For each tagged polygon the thickness is selected as follows:

```text
1. explicit thickness from polygon name: @t=<value>
2. automatic geometric estimate
```

The explicit form has priority (e.g. `polygon_name@wall@t=0.02`); if `@t=` is present, the estimator is not used.

**Geometric estimate (no `@t=`):**

- `@cell` → `t = 2A / P`, where `A` is the cell area and `P` is the total cell perimeter (outer + inner). Assumes a thin-walled closed cell of uniform thickness.
- `@wall` → `t_global = ( P − sqrt( P² − 16A ) ) / 4`, obtained from the rectangular-strip relations `A = L·t`, `P = 2L + 2t` solved for the smaller dimension `t`. For open walls `t_global` is preferred over `2A/P` because `2A/P` underestimates the thickness of a strip.

**Variation along the member axis.** If the thickness is given at both reference stations `S0` and `S1`, it is linearly interpolated: `t(z) = t0 + (t1 − t0)·(z − z0)/(z1 − z0)`. If given at only one station, it is held constant: `t(z) = t_provided`. If given at neither, the geometric estimate above is evaluated at each station.

**Summary.**

```text
@wall@t=<value>  -> explicit thickness
@wall            -> Tglobal estimate
@cell            -> 2A/P estimate
```

| Case | Behavior |
|---|---|
| `t` not provided | geometric estimate per station |
| `t` provided at both `S0` and `S1` | linear interpolation |
| `t` provided at one section only | constant thickness |

> The routines `compute_saint_venant_J_cell(section)` and `compute_saint_venant_J_wall(section)` do **not** solve the general Saint-Venant boundary-value problem (Prandtl stress function / warping). They compute **model-based** torsion constants under thin-walled assumptions, restricted to user-selected polygons.

### 16. `compute_saint_venant_J_cell` - `J_sv_cell`

**Key:** `J_sv_cell`

**Purpose.** Compute a closed single-cell torsional constant using a Bredt–Batho style formula for a thin-walled closed section with (assumed) constant thickness. This function uses only polygons tagged `@cell` or `@closed`. If no `@cell` polygons are present, the current implementation returns `0`.

**Vertex encoding.** A single `@cell` polygon encodes **two closed loops** concatenated into one `vertices` array (the "slit" encoding): exactly one outer boundary and one inner boundary. Multiple holes inside the same `@cell` polygon are not supported.

**Orientation convention** (input): outer loop counter-clockwise (CCW), inner loop clockwise (CW). The routine may internally normalize orientation for midline construction, but consistent encoding reduces failure modes.

**Minimal YAML example.**

```yaml
CSF:
  sections:
    S0:
      z: 0.000000
      polygons:
        box1@cell: # or box1@cell@t=1
          weight: 1.000000
          vertices:
            # OUTER loop (CCW)
            - [0.0, 0.0]
            - [10.0, 0.0]
            - [10.0, 6.0]
            - [0.0, 6.0]
            - [0.0, 0.0]
            # bridge to inner start
            - [1.0, 1.0]
            # INNER loop (CW)
            - [1.0, 5.0]
            - [9.0, 5.0]
            - [9.0, 1.0]
            - [1.0, 1.0]
    S1:
      z: 10.000000
      polygons:
        box1@cell: # or box1@cell@t=1
          weight: 1.000000
          vertices:
            # OUTER loop (CCW)
            - [0.0, 0.0]
            - [10.0, 0.0]
            - [10.0, 6.0]
            - [0.0, 6.0]
            - [0.0, 0.0]
            # bridge to inner start
            - [1.0, 1.0]
            # INNER loop (CW)
            - [1.0, 5.0]
            - [9.0, 5.0]
            - [9.0, 1.0]
            - [1.0, 1.0]
```

**Practical checklist.** A `@cell` polygon is valid if all of the following hold:

1. name includes `@cell` (or `@closed`);
2. when an explicit thickness is provided, the name includes `@t=<t>` with `t > 0`;
3. `vertices` contains **two** loops;
4. the outer loop encloses the inner loop and has the larger area magnitude.

### 17. `compute_saint_venant_J_wall` - `J_sv_wall`

**Key:** `J_sv_wall`

**Purpose.** Compute a torsional constant for open thin-walled components, using polygons tagged `@wall`. This is an open-section thin-walled approximation applied per selected polygon, with an optional thickness override. If no `@wall` polygons are present, the current implementation returns `0`.

**Formula.** For each open wall `i`,

$$
J_{\mathrm{sv,wall},i} \approx \frac{b_i\, t_i^3}{3} = \frac{A_i\, t_i^2}{3}
$$

where `b_i` is the wall length, `t_i` the effective thickness, and `A_i = b_i t_i` the polygon area; the two forms are identical. The total is `J_sv_wall = Σ_i J_sv,wall,i`. (Thickness selection and estimation follow the **Thickness handling** section above.)

**Geometry requirements.** The `@wall` routine does not reconstruct cells and does not support multi-loop encodings; it treats each `@wall` polygon as a single material patch. Each patch must be a **thin strip** ("rectanguloid"): two long edges along the midline, two short edges across the thickness, with midline length `b ≫ t`. If the patch is not strip-like, the formula `J ≈ A t²/3` is not a valid model. Prefer an explicit thickness for strips with noticeable curvature, non-rectangular ends, varying width, or local fillets/indentations.

**Assumptions and limitations.**

- Intended for open thin-walled components represented as wall polygons.
- Thickness may be user-specified (`@t=`) or estimated; the estimator is a geometric proxy and does not verify thin-wall validity.
- Warping and shear-deformation effects are **not** modelled; no warping constants are computed.
- Only tagged polygons are considered; untagged geometry is ignored.
- Not intended for compact solids or general thick-walled regions.

**Recommended modelling pattern.** Model an open thin-walled section as a set of separate wall patches, one polygon per patch (web plates, flange plates, stiffener plates). Each patch can have its own `weight` and its own `@t=`.

**Minimal YAML example.** A thin rectangular strip of length `b = 1.0 m` and thickness `t = 0.02 m`:

$$
J \approx \frac{b\,t^3}{3} = \frac{1.0\cdot 0.02^3}{3} = 2.666\times 10^{-6}\,\mathrm{m}^4
$$

```yaml
CSF:
  sections:
    S0:
      z: 0
      polygons:
        strip@wall@t=0.02:
          weight: 1
          vertices:
            # A thin strip (single loop): 1.0 x 0.02
            - [0.00, 0.00]
            - [1.00, 0.00]
            - [1.00, 0.02]
            - [0.00, 0.02]
            - [0.00, 0.00]
```

**Practical checklist.** A polygon is valid for `@wall` torsion if all of the following hold:

1. name includes `@wall`;
2. `vertices` define **one** closed loop (no concatenated loops);
3. the polygon represents a thin strip (midline length `b ≫ t`);
4. thickness is provided as `@t=...` (recommended);
5. if the thickness varies physically, the wall is split into multiple patches with separate polygons.

### 18. Torsional Constant - Roark equivalent rectangle (`J_s_vroark`)

**Key:** `J_s_vroark`

General-purpose torsional constant estimate obtained by mapping the composite section to an **equivalent solid rectangle** (from effective area and principal inertias) and applying Roark's torsion formula for a solid rectangle.

**Notes**
- Tag-free: independent of `@cell` / `@wall`.
- Not a thin-walled closed-cell (Bredt–Batho) formulation; closed/open thin-walled torsion is handled by the dedicated `@cell` / `@wall` paths.
- The equivalent-rectangle mapping is a heuristic procedure internal to CSF. Only the final torsion formula is from Roark; no literature reference exists for the mapping step itself.
- Intended for compact solid sections (e.g. solid piles, filled profiles) where `@cell` / `@wall` tagging is not applicable. Check `J_s_vroark_fidelity` before use: reliable only when fidelity ≥ 0.9

### 19. Roark Fidelity Index (`J_s_vroark_fidelity`)

**Key:** `J_s_vroark_fidelity` - **Range:** `[0, 1]`

**References:**
- [J_s_vroark usage guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/J_vroark_usage_guide.md)
- Engineering note: `roark_torsional_indicator_note.md` (conceptual background on `J_s_vroark` and the fidelity mechanism)

**What it means.** `J_s_vroark_fidelity` is a **geometric validity indicator** for the equivalent-rectangle mapping behind `J_s_vroark`. It answers a single question: *is this cross-section still close enough to a filled rectangle for a Roark rectangle formula to be meaningful?* It is not a torsion value, and it does not measure physical accuracy in absolute terms - it measures whether the simplifying assumptions of the Roark method still hold for the current geometry.

Use it to:

- decide whether `J_s_vroark` can be trusted for the current section,
- identify regions along `z` where the Roark mapping degrades,
- flag sections that require a different torsion method (`J_sv_cell` for closed thin-walled shapes, `J_sv_wall` for open thin-walled shapes).

Do **not** use it as:

- an absolute, method-independent accuracy metric,
- a substitute for a physically rigorous torsion computation,
- a quantitative estimate of the error on `J_s_vroark`.

**How to read the value.**

- **≥ 0.9** - compact, rectangle-like section; `J_s_vroark` is a reasonable estimate.
- **0.8 – 0.9** - borderline geometry (mild asymmetry or light non-structural material); `J_s_vroark` remains usable, with visible error.
- **< 0.8** - geometry no longer rectangle-like (T, H, I, internal voids, extreme weight dispersion); discard `J_s_vroark` in favour of  `J_sv_wall`.

A practical rule for automated pipelines is to reject `J_s_vroark` whenever fidelity drops below 0.9

**How to read the fidelity plot along `z`.**

1. **Prefer trend over point values.** Persistent degradation over a `z` interval is meaningful; an isolated sharp point often corresponds to a principal-inertia branch swap (`Ix − Iy` changing sign), not a solver failure.
2. **Correlate with the inertias.** Plot `Ix`, `Iy`, and `I2` together. Kinks in fidelity frequently align with principal-axis rotations, which are geometric transitions rather than errors.
3. **Cross-check the torsion value.** Where fidelity is high, compare `J_s_vroark` with `J_sv_wall` when available. Agreement at high fidelity increases confidence in all three methods for that section family. This combination avoids misreading isolated curves.

**Suggested wording for reports.**

> `J_s_vroark_fidelity` quantifies the geometric validity of the equivalent-rectangle mapping used to compute `J_s_vroark`. It reflects how close the actual cross-section is to a filled rectangle, not the absolute error on the torsional constant. Values above 0.9 indicate reliable Roark applicability; values below 0.8 indicate that the section should be treated with a thin-walled or full Saint-Venant method.

---

## A note on Adhémar Jean Claude Barré de Saint-Venant

The torsional constant *J* that this library estimates and validates bears the name of Adhémar Jean Claude Barré de Saint-Venant (1797–1886), one of the founders of the mathematical theory of elasticity.

In his 1855 memoir *Mémoire sur la torsion des prismes*, Saint-Venant solved the torsion problem for prismatic bars of arbitrary cross-section, a result that had resisted earlier attempts by Coulomb and Navier. His approach introduced the warping function, reduced the problem to a boundary-value equation, and produced exact solutions for elliptical and rectangular sections that remain in use today.

The formula implemented in `_roark_torsion_rect` is a compact approximation of Saint-Venant's exact series solution for the rectangle, later tabulated by Roark (1938) and condensed into continuous form by Timoshenko & Goodier (1951). The FEM warping analysis performed by `sectionproperties` solves the same boundary-value problem numerically, for arbitrary geometry, using the mathematical framework Saint-Venant laid down nearly 170 years ago.

> *"The problem of torsion is one of the most beautiful in the whole of mathematical physics."* - attributed to Saint-Venant

---

## CSF–sectionproperties mapping table

| CSF | SP field | Type | Notes |
|---|---|---|---|
| `A` | `e.a` | homogenized | do **not** map to `area` |
| `Cx` | `cx` | centroid | geometric centroid coordinate |
| `Cy` | `cy` | centroid | geometric centroid coordinate |
| `Ix` | `e.ixx_c` | homogenized | centroidal second moment |
| `Iy` | `e.iyy_c` | homogenized | centroidal second moment |
| `Ixy` | `e.ixy_c` | homogenized | centroidal product of inertia |
| `Ip` | `e.ixx_c + e.iyy_c` | derived homogenized | this is **not** `e.j` |
| `I1` | `e.i11_c` | homogenized | principal second moment |
| `I2` | `e.i22_c` | homogenized | principal second moment |
| `rx` | `rx` | homogenized-derived | consistent with `sqrt(e.ixx_c / e.a)` |
| `ry` | `ry` | homogenized-derived | consistent with `sqrt(e.iyy_c / e.a)` |
| `Wx` | `e.zxx+`, `e.zxx-` | homogenized | CSF computes `Wx = Ix / c_y,max`, i.e. the controlling modulus `min(e.zxx+, e.zxx-)` |
| `Wy` | `e.zyy+`, `e.zyy-` | homogenized | CSF computes `Wy = Iy / c_x,max`, i.e. the controlling modulus `min(e.zyy+, e.zyy-)` |
| `J_sv_cell` / `J_sv_wall` | `e.j` | torsion comparison | `sectionproperties` reports `e.j` on the E-weighted transformed section, whereas CSF evaluates torsion using the shear/torsion participation field, i.e. the G-based weighting. Use this mapping as a comparison of torsional constants, not as an identical material-weighting convention. |
| `Q_na` | - | CSF-only | first moment of area |

> **Important note on torsion mapping.** The mapping to `sectionproperties` field `e.j` is not a strict equivalence of material weighting conventions. In the native `sectionproperties` composite run, `e.j` is associated with the elastic-modulus weighting used by the SP material definition. In CSF, torsion may instead be governed by the independent shear/torsion participation field, i.e. by a G-based weighting. When axial/bending and shear/torsion participation differ, the CSF-consistent torsional value should be obtained through the dedicated CSF/SP torsion-carrier bridge. See [CSF and sectionproperties torsion carrier bridge](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csf_sp_user_guide.md#spissue).

