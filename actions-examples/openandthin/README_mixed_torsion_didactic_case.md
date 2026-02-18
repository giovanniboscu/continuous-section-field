# Mixed Torsion Example in CSF  
## A Didactic, Science-of-Structures Style Case Study

## 1. Purpose of this example

This example is designed as a **teaching case** for torsion in thin-walled and mixed cross-sections, using CSF (Continuous Section Field).  
It is intentionally simple in geometry but rich in mechanics:

- open thin-walled components (`@wall@t=...`)
- closed thin-walled cell (`@cell@t=...`)
- optional solid core (untagged polygon)
- linear section variation from **S0** to **S1**

The case is ideal for showing, side by side, three different torsional quantities available in CSF:

- `J_sv` (legacy/solid Saint-Venant path)
- `J_sv_wall` (open thin-walled approximation)
- `J_sv_cell` (closed thin-walled Bredt–Batho)

---

## 2. Conceptual framework

### 2.1 Saint-Venant torsion: why different formulas exist

In structural mechanics, torsional response depends strongly on cross-section topology and wall thickness assumptions:

1. **Solid (or generally “full-domain”) Saint-Venant torsion**  
   Uses a domain-based torsion model and returns a torsional constant \(J\) representing full-section resistance according to that model.

2. **Open thin-walled torsion**  
   For slender plate-like walls (open sections), torsional stiffness is much lower than closed cells.  
   In classical thin-wall theory, contributions often scale like \( \sim b\,t^3 \) at element level.

3. **Closed thin-walled torsion (Bredt–Batho)**  
   Closed cells develop membrane-like shear flow around the loop, producing much higher torsional stiffness than open walls of similar material amount.  
   A standard constant-thickness formula is:

$$
J_{\text{cell}} = \frac{4 A_m^2}{\int \frac{ds}{t}} \quad \Rightarrow \quad
\text{if } t=\text{const},\; J_{\text{cell}} = \frac{4 A_m^2 t}{b_m}
$$

where:
- \(A_m\): area enclosed by the cell midline
- \(b_m\): midline perimeter
- \(t\): wall thickness

---

## 3. CSF modeling language for this case

### 3.1 Tags used

- `@wall` → polygon contributes to open thin-wall torsion branch
- `@cell` (or `@closed`) → polygon interpreted as closed cell encoding
- `@t=<value>` → explicit thickness override (recommended for didactic clarity)

### 3.2 Why explicit `@t` is pedagogically useful

Using explicit thickness:
- removes ambiguity from automatic estimators (e.g., \(t=2A/P\))
- makes dimensional reasoning transparent
- allows controlled scaling studies (e.g., 20% reduction in geometry and thickness)

---

## 4. Geometry idea (minimal mixed pattern)

The baseline mixed pattern has:

- left plate wall (`left_web@wall@t=...`)
- right plate wall (`right_web@wall@t=...`)
- one centered closed box cell (`cell_box@cell@t=...`), slit-encoded with outer and inner loops

Then S1 is built as a scaled version of S0 (example: 0.8), optionally including thickness scaling.

---

## 5. Reference numerical outputs used in this note

From your run:

### S0 (z = 0.0)

- \(A = 0.0071596\)
- \(I_x = 4.4291 \times 10^{-6}\)
- \(I_y = 1.1842 \times 10^{-5}\)
- \(J_{sv} = 1.6271 \times 10^{-5}\)
- \(J_{sv,wall} = 1.3333 \times 10^{-7}\)
- \(J_{sv,cell} = 1.8197 \times 10^{-6}\)

### S1 (z = 20.0)

- \(A = 0.0050053\)
- \(I_x = 1.8791 \times 10^{-6}\)
- \(I_y = 4.9156 \times 10^{-6}\)
- \(J_{sv} = 6.7947 \times 10^{-6}\)
- \(J_{sv,wall} = 8.5333 \times 10^{-8}\)
- \(J_{sv,cell} = 9.3171 \times 10^{-7}\)

(All units consistent with your CSF model conventions.)

---

## 6. Comparative table (S0 vs S1)

$$
\text{ratio} = \frac{\text{value at } z=20}{\text{value at } z=0}
$$

| Quantity | S0 | S1 | Ratio S1/S0 |
|---|---:|---:|---:|
| \(A\) | 0.0071596 | 0.0050053 | 0.699 |
| \(I_x\) | 4.4291e-06 | 1.8791e-06 | 0.424 |
| \(I_y\) | 1.1842e-05 | 4.9156e-06 | 0.415 |
| \(J_{sv}\) | 1.6271e-05 | 6.7947e-06 | 0.418 |
| \(J_{sv,wall}\) | 1.3333e-07 | 8.5333e-08 | 0.640 |
| \(J_{sv,cell}\) | 1.8197e-06 | 9.3171e-07 | 0.512 |

### Interpretation of these ratios

- `J_sv_wall` ratio \( \approx 0.64 = 0.8^2 \) is consistent with your chosen wall scaling in this setup.
- `J_sv_cell` ratio \( \approx 0.512 = 0.8^3 \) is consistent with closed-cell behavior for this controlled scaling pattern.
- `J_sv` (legacy/solid path) follows its own domain-based trend (~0.418 here), and **must not** be expected to match wall/cell ratios term by term.

---

## 7. Why this example is excellent for teaching

This single model lets students see, in one place:

1. **Topology effect**: open vs closed flow paths
2. **Modeling path effect**: solid-domain vs thin-wall formulas
3. **Scaling effect**: how changing geometry/thickness changes each torsional descriptor
4. **Tag-driven mechanics**: explicit model declaration, no hidden profile recognition

It is a concrete demonstration that *“torsion constant” is not one universal number independent of assumptions.*

---

## 8. Important caution for documentation

## Do not mix interpretations of \(J\)

The three outputs are not interchangeable:

- `J_sv`: full-section Saint-Venant path (legacy/domain model)
- `J_sv_wall`: open thin-wall approximation
- `J_sv_cell`: closed thin-wall Bredt–Batho

For a mixed model, comparing magnitudes is informative, but **equating** them is incorrect.

---

## 9. Closed-cell encoding requirements in CSF

For `@cell` polygons (slit encoding), ensure:

1. Outer loop explicitly closed (repeat first outer point)
2. Inner loop explicitly closed (repeat first inner point)
3. Non-degenerate areas
4. Explicit `@t=...` when strict mode is enabled
5. Robust loop pairing (resampling + cyclic phase alignment) for non-rectangular shapes

This is especially important for circles/ellipses and arbitrary smooth closed contours.

---

## 10. Suggested “book-style” exercises

1. **Geometry-only scaling test**  
   Scale coordinates by factor \(\lambda\), keep `@t` fixed; compare measured \(J\) ratios.

2. **Geometry + thickness scaling test**  
   Scale both coordinates and `@t` by \(\lambda\); verify expected trends for wall and cell branches.

3. **Cell shape sensitivity**  
   Replace rectangular cell with polygonal ring approximating a circle; compare `J_sv_cell` convergence with number of sides.

4. **Mixed-core extension**  
   Add a solid central core and discuss why `J_sv` may rise strongly while `J_sv_cell` still tracks thin-wall logic.

---


Use this order in docs:

1. **Physical assumptions** (solid vs wall vs cell)
2. **Tag syntax and strictness policy**
3. **Minimal mixed YAML**
4. **Numerical table at S0 and S1**
5. **Ratio analysis and scaling interpretation**
6. **Warnings and non-interchangeability of \(J\) outputs**
7. **Validation/consistency checks**

---
In short, it is an excellent bridge between **classical Scienza delle Costruzioni** torsion theory and **modern declarative computational modeling** in CSF.
