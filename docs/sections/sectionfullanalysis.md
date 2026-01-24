# CSF – Section Full Analysis Output

This document explains **all quantities reported by the CSF _Section Full Analysis_**.

It is intended as a **clear, engineering-oriented reference** for users who want to:
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
Total **net cross-sectional area**, including the effect of polygon weights.

Plain-text formula:

A = sum( w_i * A_i )

where:
- A_i = signed area of polygon i
- w_i = polygon weight

**Notes**
- Can be reduced or increased by weighted sub-domains.
- Must be non-zero for a valid section.

---

## 2. Centroid Cx

**Key:** `Cx`

Horizontal coordinate of the **geometric centroid**.

Plain-text formula:

Cx = sum( w_i * A_i * x_i ) / sum( w_i * A_i )

---

## 3. Centroid Cy

**Key:** `Cy`

Vertical coordinate of the **geometric centroid**.

Plain-text formula:

Cy = sum( w_i * A_i * y_i ) / sum( w_i * A_i )

---

## 4. Inertia Ix

**Key:** `Ix`

Second moment of area about the **centroidal X-axis**.

Computed using Green’s theorem with parallel-axis correction.

---

## 5. Inertia Iy

**Key:** `Iy`

Second moment of area about the **centroidal Y-axis**.

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

J = Ix + Iy

**Notes**
- Purely geometric.
- **Not** a torsional stiffness for non-circular sections.

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

Plain-text formula:

rx = sqrt( Ix / A )

Represents the distribution of area relative to the X-axis.

---

## 11. Radius of Gyration ry

**Key:** `ry`

Plain-text formula:

ry = sqrt( Iy / A )

---

## 12. Elastic Section Modulus Wx

**Key:** `Wx`

Elastic section modulus for bending about the **X-axis**.

Plain-text formula:

Wx = Ix / c_y,max

where c_y,max is the maximum distance from the centroid to the extreme fibers.

---

## 13. Elastic Section Modulus Wy

**Key:** `Wy`

Elastic section modulus for bending about the **Y-axis**.

Plain-text formula:

Wy = Iy / c_x,max

---

## 14. Torsional Rigidity K

**Key:** `K_torsion`

Semi-empirical torsional stiffness approximation.

Plain-text formula:

K ≈ A^4 / (40 * Ip)

where Ip = Ix + Iy.

**Notes**
- Always defined.
- Low physical fidelity.
- Used only as a **fallback**.

---

## 15. First Moment of Area Q

**Key:** `Q_na`

First moment of area about the **neutral axis**.

Used in shear stress estimation:

Q = integral( y * dA ) about the neutral axis

---

## 16. Torsional Constant (Saint-Venant)

**Key:** `J_sv`

Effective Saint-Venant torsional constant.

**Definition (open thin-walled sections)**:

J ≈ sum( b_i * t_i^3 / 3 )

where:
- t_i = equivalent strip thickness
- b_i = strip midline length

**Notes**
- Valid primarily for **open thin-walled sections**.
- Used as the **reference torsional constant** when no closed cell is detected.

---

## 17. Torsional Constant (Roark / Bredt)

**Key:** `J_s_vroark`

Closed-cell torsional constant based on Bredt–Batho / Roark thin-walled theory.

Plain-text formula:

J ≈ 4 * A_cell^2 * t / P

where:
- A_cell = area enclosed by the wall midline
- t = wall thickness
- P = cell perimeter

**Notes**
- Applicable **only to closed thin-walled cells**.
- Automatically ignored for open sections **

---

## 18. Roark Fidelity Index

**Key:** `J_s_vroark_fidelity`

Dimensionless reliability index in the range [0, 1].

Interpretation:

- > 0.6 : model applicable
- 0.3 – 0.6 : borderline validity
- < 0.3 : outside validity domain

**Notes**
- Used to gate the use of `J_s_vroark` **

---

## Final Remarks

- CSF deliberately exposes **multiple torsional indicators**.
- **Selection is policy-driven**, not profile-driven **
- This guarantees transparency, robustness, and solver independence.

For the formal torsional selection rules, see:

**README-P.md – CSF Torsional Constant Policy**
