# CSF – Section Full Analysis Output

This document explains **all quantities reported by the CSF _Section Full Analysis_**.

It is intended as a **clear, engineering‑oriented reference** for users who want to:
- understand what each value represents,
- know how it is computed in CSF,
- understand **the validity domain and limitations** of each quantity.

Whenever a quantity depends on **a specific modelling choice or policy** defined elsewhere (e.g. torsion selection rules), this is marked with **double asterisks `**`** and explicitly noted.

---

## General Notes

- All quantities are computed **purely from geometry and polygon weights**.
- No assumptions are made about profile families (I, H, box, tube, etc.).
- Polygon `weight` is treated as a **scalar field multiplier** (e.g. modular ratio, material factor).
- Negative weights are allowed and represent **subtractive domains**.

---

## 1. Area (A)

**Key:** `A`

**Definition**  
Total **net cross‑sectional area**, including the effect of polygon weights.

\[ A = \sum_i w_i A_i \]

where:
- \(A_i\) is the signed area of polygon *i*,
- \(w_i\) is its weight.

**Notes**
- Can be reduced or increased by weighted sub‑domains.
- Must be non‑zero for a valid section.

---

## 2. Centroid Cx

**Key:** `Cx`

Horizontal coordinate of the **geometric centroid**.

\[ C_x = \frac{\sum w_i A_i x_i}{\sum w_i A_i} \]

---

## 3. Centroid Cy

**Key:** `Cy`

Vertical coordinate of the **geometric centroid**.

\[ C_y = \frac{\sum w_i A_i y_i}{\sum w_i A_i} \]

---

## 4. Inertia Ix

**Key:** `Ix`

Second moment of area about the **centroidal X‑axis**.

Computed using Green’s theorem and parallel‑axis correction.

---

## 5. Inertia Iy

**Key:** `Iy`

Second moment of area about the **centroidal Y‑axis**.

---

## 6. Inertia Ixy

**Key:** `Ixy`

Product of inertia about centroidal axes.

**Notes**
- Zero value indicates symmetry with respect to X or Y axes.

---

## 7. Polar Moment (J)

**Key:** `J`

Polar second moment of area:

\[ J = I_x + I_y \]

**Notes**
- Purely geometric.
- **Not** a torsional stiffness for non‑circular sections.

---

## 8. Principal Inertia I1

**Key:** `I1`

Major principal second moment of area.

---

## 9. Principal Inertia I2

**Key:** `I2`

Minor principal second moment of area.

---

## 10. Radius of Gyration rx

**Key:** `rx`

\[ r_x = \sqrt{\frac{I_x}{A}} \]

Represents the distribution of area relative to the X‑axis.

---

## 11. Radius of Gyration ry

**Key:** `ry`

\[ r_y = \sqrt{\frac{I_y}{A}} \]

---

## 12. Elastic Section Modulus Wx

**Key:** `Wx`

Elastic section modulus for bending about the **X‑axis**:

\[ W_x = \frac{I_x}{c_{y,\max}} \]

where \(c_{y,\max}\) is the maximum distance from the centroid to extreme fibers.

---

## 13. Elastic Section Modulus Wy

**Key:** `Wy`

Elastic section modulus for bending about the **Y‑axis**.

---

## 14. Torsional Rigidity K

**Key:** `K_torsion`

Semi‑empirical torsional stiffness approximation:

\[ K \approx \frac{A^4}{40\,I_p} \]

where \(I_p = I_x + I_y\).

**Notes**
- Always defined.
- Low physical fidelity.
- Used only as a **fallback**.

---

## 15. First Moment of Area Q

**Key:** `Q_na`

First moment of area about the **neutral axis**.

Used in shear stress estimation:

\[ \tau = \frac{VQ}{Ib} \]

---

## 16. Torsional Constant (Saint‑Venant)

**Key:** `J_sv`

Effective Saint‑Venant torsional constant.

**Definition**
- For **open thin‑walled sections**:

\[ J \approx \sum_i \frac{b_i t_i^3}{3} \]

where:
- \(t_i\) is an equivalent strip thickness,
- \(b_i\) is the strip midline length.

**Notes**
- Valid only when polygons represent **thin laminae**.
- Used as the **reference torsional constant for open sections**.

---

## 17. Torsional Constant (Roark / Bredt)

**Key:** `J_s_vroark`

Closed‑cell torsional constant based on Bredt–Batho / Roark thin‑walled theory.

\[ J \approx \frac{4 A_{cell}^2 t}{P} \]

**Notes**
- Applicable **only to closed thin‑walled cells**.
- Automatically ignored for open sections.
- **Selected only if fidelity is sufficient** **

---

## 18. Roark Fidelity Index

**Key:** `J_s_vroark_fidelity`

Dimensionless reliability index in \([0,1]\).

**Interpretation**:

| Value | Meaning |
|------:|--------|
| > 0.6 | Model applicable |
| 0.3–0.6 | Borderline |
| < 0.3 | Outside validity |

**Notes**
- Used to gate the use of `J_s_vroark` **

---

## Final Remarks

- CSF deliberately exposes **multiple torsional indicators**.
- **Selection is policy‑driven**, not profile‑driven **
- This ensures transparency, robustness, and solver independence.

For the formal torsional selection rules, see:

> **README‑P.md — CSF Torsional Constant Policy**
