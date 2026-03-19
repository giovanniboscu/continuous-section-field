# CSF Actions

python3 -m csf.CSFActions j_sv_geometry.yaml j_sv_action.yaml

python3 -m csf.CSFActions annulus.yaml annulus_action.yaml
# De Saint-Venant Torsional Constant — Additivity in Cross-Section Solvers (CSF)

## 1. Background

The De Saint-Venant torsional constant $J$ (also written $I_t$) governs the torsional stiffness of a cross-section in the Saint-Venant torsion theory:

$$M_t = G \cdot J \cdot \vartheta'$$

where $G$ is the shear modulus and $\vartheta'$ is the twist per unit length.

When a cross-section is assembled from multiple independent components, a CSF (Cross-Section Field solver / pre-processor) may compute $J$ by **summing the contributions** of each component. This document states when that approach is valid and when it is not.

---

## 2. Elemental Formulas

### 2.1 Thin open wall (slender rectangle)

$$J_{\text{wall}} = \frac{b \, t^3}{3}$$

where $b$ is the wall length and $t$ is the thickness.

### 2.2 Closed cell (Bredt formula)

$$J_{\text{cell}} = \frac{4 A^2}{\displaystyle\oint \frac{ds}{t}}$$

where $A$ is the area enclosed by the mid-line of the cell.

### 2.3 General additive form (CSF implementation)

For a section composed of $n_c$ closed cells and $n_w$ open walls:

$$\boxed{J = \sum_{k=1}^{n_c} J_{\text{cell},k} + \sum_{i=1}^{n_w} J_{\text{wall},i}}$$

---

## 3. Hypotheses for Validity of Additivity

The summation above is **valid if and only if** all of the following conditions hold:

| # | Hypothesis | Physical meaning |
|---|---|---|
| H1 | **No torsional interaction** between components | Components do not share a closed contour; the Prandtl stress function $\phi$ is independent across parts |
| H2 | **Same unit twist** $\vartheta'$ for all components | All parts rotate together as a rigid body about the same longitudinal axis (kinematic compatibility) |
| H3 | **Open walls are truly open** | Tangential flow reverses at free ends; no circulation around a closed loop |
| H4 | **Junction effects neglected** | Stress concentrations and stiffening at corners/junctions are ignored, consistent with thin-wall assumptions |

> **All four conditions must hold simultaneously.**
> Violation of any single hypothesis invalidates the simple sum.

---

## 4. When Additivity Holds

| Section type | Additivity | Notes |
|---|---|---|
| Thin open section (flat plates, T, L, I, channel) | ✅ Valid | Classic result; walls meet at a node but never close |
| Multiple **separate** closed cells (no shared walls) | ✅ Valid | Each cell contributes independently via Bredt |
| **Separate** closed cell + **separate** open walls (not connected) | ✅ Valid | No interaction; H1 satisfied by geometry |
| Closed cell + open walls **modelled as non-interacting** (CSF assumption) | ✅ Valid as model | Acceptable approximation when wall thickness $\ll$ cell thickness |

---

## 5. When Additivity Does NOT Hold

| Section type | Issue |
|---|---|
| Box girder with **connected** protruding flanges | Flanges share wall with cell → interaction; Prandtl function is continuous across junction |
| Multi-cell sections with **shared walls** | Shared wall participates in two cells simultaneously; Bredt system must be solved globally |
| Open walls **welded/bonded to a cell** | Closed contour is modified; simple sum overestimates or underestimates $J$ |
| Thick-walled sections | Thin-wall assumption breaks down; full Saint-Venant warping analysis required |

> **Warning for CSF users:** if the geometry is assembled by connecting open walls to the boundary of a closed cell, the non-interaction hypothesis (H1) is violated. The CSF must either apply a corrected formulation or flag the configuration explicitly.

---

## 6. Practical Implication for CSF

When a CSF sums contributions:

$$J_{\mathrm{CSF}} = J_{\mathrm{cell}} + J_{\mathrm{left,wall}} + J_{\mathrm{right,wall}} + \cdots$$

the result is **exact within the model** provided H1–H4 are enforced by the geometry definition (i.e. components are tagged as independent and do not share contour segments).

If components share contour segments, the CSF should:

1. Detect shared walls and switch to a **multi-cell Bredt system**.
2. Add open-wall contributions only for **truly free** (unshared) wall segments.
3. Document which components are treated as non-interacting in the output report.

---

## 7. Summary

```
J = Σ J_cell (Bredt, independent cells)
  + Σ J_wall (b·t³/3, independent open walls)

Valid when:
  - components do not share closed contours         [H1]
  - all components have the same twist θ'           [H2]
  - open walls have free ends (no closed loop)      [H3]
  - junction stress concentrations are neglected    [H4]

Not valid when:
  - walls are physically connected to a cell
  - cells share walls
  - section is thick-walled
```

---

## 8. References

- Timoshenko, S.P. & Goodier, J.N. — *Theory of Elasticity*, McGraw-Hill
- Vlasov, V.Z. — *Thin-Walled Elastic Beams*, Israel Program for Scientific Translations
- Pilkey, W.D. — *Analysis and Design of Elastic Beams*, Wiley
- EN 1993-1-3 — Eurocode 3, Annex C (thin-walled open sections)
