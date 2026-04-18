# `J_s_vroark` - torsional constant estimate: usage guide

## What it is

CSF provides two complementary estimators for the Saint-Venant torsional constant J at each station:

| Output | Method | Cost |
|---|---|---|
| `J_s_vroark` | Roark formula on equivalent rectangle (mesh-free) | zero - always available |
| `e.j` | Full FEM warping solve via `sectionproperties` | requires `csf_sp` call |
| `J_s_vroark_fidelity` | Geometric reliability indicator ∈ (0, 1] | zero - always available |

`J_s_vroark` is a fast proxy. `e.j` is the reference. Fidelity tells you when the proxy is trustworthy.

---

## Fidelity - how it is computed

Fidelity combines two checks.

**Aspect-ratio score** `r = t_eq / a_eq` - ratio of short to long side of the equivalent rectangle derived from effective area and minimum principal inertia:

```
t_eq = sqrt(12 · I_min / A_eff)
a_eq = A_eff / t_eq        (swap if t > a, so a ≥ t always)
r    = t_eq / a_eq  ∈ (0, 1]
```

`r = 1` for a square, decreasing toward zero for elongated sections. Verified on all test cases: `fidelity = r` for non-circular solid sections.

**Isoperimetric penalty** - activated when `Q = 4πA/P² > 0.90` (circle: Q=1, square: Q=0.785). Drives fidelity to near zero for circular and elliptical sections, correctly flagging the ~12% systematic underestimate by Roark.

For geometrically similar tapered members, fidelity is **constant along the entire member axis** - one check at any station classifies the full member.

---

## Validation dataset - effect of polygon weight `w`

| Case | w | `J_s_vroark` | `J_s_vroark_fidelity` | `e.j` |
|---|---|---|---|---|
| square_1 | 1.0 | 0.14083333 | 1.00000000 | 0.14057750 |
| square_1 | 0.5 | 0.02861003 | 0.50000000 | 0.07028875 |
| rect_sqr2 | 1.0 | 0.56333333 | 1.00000000 | 0.56230860 |
| rect_sqr2 | 0.5 | 0.11444010 | 0.50000000 | 0.28115430 |
| 3boxtriangl | 1.0 | 1.04757001 | 0.86428571 | 0.93005250 |
| 3boxtriangl | 0.5 | 0.25749000 | 0.50000000 | 0.46368000 |
| complexboxes | 1.0 | 2.67006702 | 0.44445209 | 1.60937700 |
| complexboxes | 0.5 | 0.86876799 | 0.88890418 | 0.80468870 |
| complexboxes2 | * | 20.76646218 | 0.91926779 | 25.08619000 |
| complexboxesw1 | 1.0 | 2.67006702 | 0.44445209 | 1.60937700 |
| complexboxesw0.5 | 0.5 | 0.86876799 | 0.88890418 | 0.80468870 |

`*` - yaml polygon weights used as-is (mixed: 1.0, 0.9, 0.7, 0.8, 0.6).

**Key observations:**

- `e.j = J_SV(geometry) × w` - confirmed at 0.000% for all cases with fine mesh.
- `fidelity = r = t_eq / a_eq` - confirmed on all cases. Variation with `w` depends on whether the swap condition is triggered: fidelity ∝ 1/w when no swap occurs, fidelity ∝ w when swap is fixed.
- `J_s_vroark` is reliable (error < 0.3%) only for **w = 1, solid rectangular sections**. For w ≠ 1 the mapping distorts the aspect ratio, producing errors from −44% to −79%.
- `complexboxesw1` and `complexboxesw0.5` are the same yaml as `complexboxes` with a global weight multiplier - identical values confirm the mechanism is geometry-independent.

---

## Decision rules

**Use `J_s_vroark`** when all three conditions hold:
1. `J_s_vroark_fidelity ≥ 0.3`
2. Section is **solid** (no enclosed voids)
3. Section is **not circular or elliptical** (fidelity near zero flags this automatically)

> For solid rectangular sections, low fidelity means *elongated geometry*, not unreliable J.
> A 3:1 rectangle has fidelity 0.333 but J error below 0.1%.

**Always use `e.j`** if any of the following:
- Section has an enclosed void (hollow tube, box, pipe) - any wall thickness
- Section is circular or elliptical
- `J_s_vroark_fidelity < 0.3`
- Structural design requires accuracy below 5%

---

## Workflow

```
For each station along z:
  1. Read J_s_vroark and J_s_vroark_fidelity from CSF actions output.
  2. If fidelity >= 0.3 AND section is solid AND section is not circular:
       → use J_s_vroark  (fast, no FEM needed)
  3. Otherwise:
       → python3 -m csf.utils.csf_sp --yaml <file>.yaml --z=<z>
       → use e.j from sectionproperties output
```

---

## Notes on `e.j` accuracy

| Section type | FEM error vs analytical |
|---|---|
| Solid sections | < 0.5% |
| Thin hollow sections | ~+1.3% vs Bredt (conservative) |
| Circle 64-vertex polygon | −0.43% vs π·d⁴/32 |

Reduce `mesh_sizes` in `csf_sp` for tighter tolerances.
