# Determination of Elastic Modulus Reduction Due to Concrete Degradation  
## Formal Procedure Based on EN 1992-1-1 (Eurocode 2)

---

# 1. Normative Framework

The present formulation is derived from:

EN 1992-1-1, Eq. (3.2)
EN 1992-1-1, Eq. (3.5)

**EN 1992-1-1 — Eurocode 2: Design of Concrete Structures – Part 1-1: General Rules and Rules for Buildings**

Relevant clauses:

- Section 3.1.2 — Compressive strength
- Section 3.1.3 — Modulus of elasticity
- Equation (3.2):
  
  $$
  f_{cm} = f_{ck} + 8
  $$

- Equation (3.5):

$$
E_{cm} = 22000 ( f_{cm} / 10 )^{0.3}
$$

Eurocode 2 defines the mechanical relationship between compressive strength and elastic modulus for normal-weight structural concrete.

The degradation model introduced below is an engineering assumption. Eurocode 2 does not prescribe a universal degradation factor.

---

# 2. Reference (Sound) Concrete

## Step 1 — Characteristic Strength

From the selected concrete class:

$$
f_{ck}
$$

where:

- $f_{ck}$ = characteristic cylinder compressive strength [MPa]

---

## Step 2 — Mean Compressive Strength

According to EN 1992-1-1 Eq. (3.2):

$$
f_{cm} = f_{ck} + 8
$$

---

## Step 3 — Secant Elastic Modulus of Sound Concrete

From EN 1992-1-1 Eq. (3.5):

$$
E_{cm,s} = 22000 \left( \frac{f_{cm}}{10} \right)^{0.3}
$$

Substituting Step 2:

$$
E_{cm,s} = 22000 \left( \frac{f_{ck} + 8}{10} \right)^{0.3}
$$

---

# 3. Degradation Model

Concrete degradation is represented by a proportional reduction of the characteristic strength:

$$
f_{ck,d} = \alpha f_{ck}
$$

where:

- $\alpha \in (0,1]$ = degradation factor  
- $f_{ck,d}$ = degraded characteristic strength

---

# 4. Degraded Material Properties

## Step 4 — Degraded Mean Strength

Applying EC2 Eq. (3.2):

$$
f_{cm,d} = f_{ck,d} + 8
$$

Substituting the degradation model:

$$
f_{cm,d} = \alpha f_{ck} + 8
$$

---

## Step 5 — Degraded Elastic Modulus

Using EC2 Eq. (3.5):

$$
E_{cm,d} = 22000 \left( \frac{f_{cm,d}}{10} \right)^{0.3}
$$

Substituting:

$$
E_{cm,d} = 22000 \left( \frac{\alpha f_{ck} + 8}{10} \right)^{0.3}
$$

---

# 5. Modulus Reduction Law

## Step 6 — Definition of Modulus Ratio

The elastic modulus reduction factor is defined as:

$$
w = \frac{E_{cm,d}}{E_{cm,s}}
$$

Substituting the expressions derived above:

$$
w =
\frac{
22000 \left( \frac{\alpha f_{ck} + 8}{10} \right)^{0.3}
}{
22000 \left( \frac{f_{ck} + 8}{10} \right)^{0.3}
}
$$

Canceling common factors:

$$
w(\alpha, f_{ck}) =
\left(
\frac{\alpha f_{ck} + 8}
     {f_{ck} + 8}
\right)^{0.3}
$$

This quantity is dimensionless.

---

# 6. Relative Reduction of Elastic Modulus

The relative decrease of elastic modulus is:

$$
\Delta E = 1 - w
$$

Therefore:

$$
\Delta E(\alpha, f_{ck}) =
1 -
\left(
\frac{\alpha f_{ck} + 8}
     {f_{ck} + 8}
\right)^{0.3}
$$

---

# 7. Summary of the Complete Analytical Chain

Given:

- Concrete class → $f_{ck}$
- Degradation factor → $\alpha$

The complete sequence is:

$$
f_{ck,d} = \alpha f_{ck}
$$

$$
f_{cm,d} = \alpha f_{ck} + 8
$$

$$
E_{cm,d} = 22000 \left( \frac{\alpha f_{ck} + 8}{10} \right)^{0.3}
$$

$$
w =
\left(
\frac{\alpha f_{ck} + 8}
     {f_{ck} + 8}
\right)^{0.3}
$$

$$
\Delta E = 1 - w
$$

---

# 8. Scope and Applicability

This formulation:

- Is fully consistent with EN 1992-1-1 mechanical relationships.
- Applies to normal-weight structural concrete.
- Assumes degradation is representable through reduction of $f_{ck}$.
- Does not account for creep, cracking, nonlinear damage, or thermal reduction curves (fire design is treated in EN 1992-1-2).

The degradation factor $\alpha$ is an engineering modeling parameter and must be justified separately.
