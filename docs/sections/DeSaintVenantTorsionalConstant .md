un# De Saint-Venant Torsional Constant - Cell and Wall Contributions in CSF

## How CSF Reports and Exports J

> When presenting a cross-section, the CSF reports the De Saint-Venant torsional constant $J$ broken down into **two separate contributions**:
>
> - $J_{\mathrm{sv,cell}}$ — contribution from all closed cells (Bredt formula)
> - $J_{\mathrm{sv,wall}}$ — contribution from all open thin walls
>
> These two quantities are reported **individually** in the section output, so the user can inspect the relative weight of each contribution.
>
> When exporting to **OpenSees** or **SAP2000**, the CSF provides a single scalar $J$ obtained by **direct summation**:
>
> $$\boxed{J_{\mathrm{sv}} = J_{\mathrm{sv,cell}} + J_{\mathrm{sv,wall}}}$$
>
> This summation is valid under the non-interaction hypotheses documented in the sections below.

---

## 1. Background

The De Saint-Venant torsional constant $J_{\mathrm{sv}}$ governs the torsional stiffness of a cross-section:

$$M_t = G \cdot J_{\mathrm{sv}} \cdot \vartheta'$$

where $G$ is the shear modulus and $\vartheta'$ is the twist per unit length.

For sections composed of both closed cells and open walls, the CSF decomposes $J_{\mathrm{sv}}$ into two physically distinct contributions, computed independently and then summed.

---

## 2. The Two Contributions

### 2.1 Closed-cell contribution — $J_{\mathrm{sv,cell}}$

Each closed cell $k$ contributes via the **Bredt formula**:

$$J_{\mathrm{sv,cell},k} = \frac{4 A_k^2}{\displaystyle\oint_k \frac{ds}{t}}$$

where $A_k$ is the area enclosed by the mid-line of cell $k$.

The total closed-cell contribution is:

$$J_{\mathrm{sv,cell}} = \sum_{k=1}^{n_c} J_{\mathrm{sv,cell},k}$$

### 2.2 Open-wall contribution — $J_{\mathrm{sv,wall}}$

Each thin open wall $i$ (slender rectangle) contributes:

$$J_{\mathrm{sv,wall},i} = \frac{b_i \, t_i^3}{3}$$

where $b_i$ is the wall length and $t_i$ is the thickness.

The total open-wall contribution is:

$$J_{\mathrm{sv,wall}} = \sum_{i=1}^{n_w} J_{\mathrm{sv,wall},i}$$

### 2.3 Total torsional constant

$$\boxed{J_{\mathrm{sv}} = J_{\mathrm{sv,cell}} + J_{\mathrm{sv,wall}}}$$

---

## 3. How CSF Presents the Results

The CSF reports the two contributions **separately** before combining them:

| Quantity | Formula | Description |
|---|---|---|
| $J_{\mathrm{sv,cell}}$ | $\sum_k \dfrac{4A_k^2}{\oint ds/t}$ | Sum over all closed cells |
| $J_{\mathrm{sv,wall}}$ | $\sum_i \dfrac{b_i t_i^3}{3}$ | Sum over all open walls |
| $J_{\mathrm{sv}}$ | $J_{\mathrm{sv,cell}} + J_{\mathrm{sv,wall}}$ | **Total — used for export** |

This breakdown allows the user to verify that each component is physically meaningful and to assess the relative importance of cells vs. walls in the torsional response.

---

## 4. Hypotheses for Validity of the Summation

The sum $J_{\mathrm{sv}} = J_{\mathrm{sv,cell}} + J_{\mathrm{sv,wall}}$ is **valid if and only if** all of the following conditions hold:

| # | Hypothesis | Physical meaning |
|---|---|---|
| H1 | **No torsional interaction** between cells and walls | Components do not share a closed contour; the Prandtl stress function $\phi$ is independent across parts |
| H2 | **Same unit twist** $\vartheta'$ for all components | All parts rotate together as a rigid body about the same axis (kinematic compatibility) |
| H3 | **Open walls are truly open** | Tangential flow reverses at free ends; no circulation around a closed loop |
| H4 | **Junction effects neglected** | Stress concentrations at corners/junctions are ignored, consistent with thin-wall assumptions |

> **All four conditions must hold simultaneously.**
> Violation of any single hypothesis invalidates the simple sum.

---

## 5. When the Summation Holds

| Configuration | Valid | Notes |
|---|---|---|
| Separate closed cells + separate open walls | Valid | No shared contour; H1 satisfied by geometry |
| Open walls modelled as non-interacting with cells | Valid as model | Good approximation when $t_{\mathrm{wall}} \ll t_{\mathrm{cell}}$ |
| Thin open section only (T, L, I, channel) | Valid | $J_{\mathrm{sv,cell}} = 0$; classic result |
| Multiple independent closed cells | Valis | Each cell via Bredt, no shared walls |

## 6. When the Summation Does NOT Hold

| Configuration | Issue |
|---|---|
| Open walls physically connected to a cell boundary | H1 violated; interaction modifies both $J_{\mathrm{sv,cell}}$ and $J_{\mathrm{sv,wall}}$ |
| Multi-cell sections with shared walls | Shared wall participates in two cells; global Bredt system required |
| Box girder with welded protruding flanges | Flange and cell share a contour segment; simple sum over/underestimates $J_{\mathrm{sv}}$ |
| Thick-walled sections | Thin-wall assumption breaks down; full Saint-Venant warping analysis required |

> **Warning:** if cells and walls share contour segments in the geometry definition, the CSF summation is no longer valid. The solver should detect shared walls and switch to a coupled multi-cell formulation.

---

## 7. Summary

```
CSF reports separately:
  J_sv_cell  =  Σ_k  4·A_k² / ∮(ds/t)     [Bredt, closed cells]
  J_sv_wall  =  Σ_i  b_i·t_i³ / 3          [thin open walls]

CSF exports (OpenSees, SAP2000):
  J_sv  =  J_sv_cell  +  J_sv_wall

Valid when (H1–H4):
  - cells and walls do not share closed contours
  - all components have the same twist θ'
  - open walls have free ends
  - junction effects are neglected

Not valid when:
  - walls are connected to a cell boundary
  - cells share walls
  - section is thick-walled
```

---

## 8. References

- Timoshenko, S.P. & Goodier, J.N. — *Theory of Elasticity*, McGraw-Hill
- Vlasov, V.Z. — *Thin-Walled Elastic Beams*, Israel Program for Scientific Translations
- Pilkey, W.D. — *Analysis and Design of Elastic Beams*, Wiley
- EN 1993-1-3 — Eurocode 3, Annex C (thin-walled open sections)
