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


# From EC2 Degradation Formula to CSF Weight Law

## 1. Starting point: the modulus ratio

From the EC2 degradation procedure, the modulus ratio is:

$$
w(\alpha, f_{ck}) =
\left(
\frac{\alpha \, f_{ck} + 8}{f_{ck} + 8}
\right)^{0.3}
$$

This is a dimensionless scalar in `(0, 1]`.  
It is exactly what CSF expects as a polygon weight.

---

## 2. Mapping to CSF variables

In CSF, a weight law expression has access to:

| CSF variable | Meaning |
|---|---|
| `w0` | weight at start section (z = z0) |
| `w1` | weight at end section (z = z1) |
| `z` | physical coordinate along the member |
| `L` | total member length |
| `np` | NumPy namespace |

The EC2 formula depends on two engineering parameters:

| Parameter | Meaning |
|---|---|
| `alpha` | degradation factor ∈ (0, 1] — varies along z |
| `fck` | characteristic compressive strength [MPa] — material constant |

`fck` is a known constant for a given concrete class.  
`alpha` is the modeling parameter that the engineer specifies.

---

## 3. Case A — uniform degradation (alpha constant)

If degradation is uniform along the member, `alpha` is a scalar constant.  
The weight law becomes a constant expression:

```python
fck = 30.0    # e.g. C30/37
alpha = 0.70  # 30% strength reduction

section_field.set_weight_laws([
    "concrete,concrete : ((alpha * fck + 8) / (fck + 8)) ** 0.3",
])
```

`alpha` and `fck` are Python variables defined before the call.  
The string expression is evaluated by CSF at each integration point,
where `alpha` and `fck` are captured from the enclosing scope.

---

## 4. Case B — longitudinally varying degradation (alpha = alpha(z))

If degradation varies along z (e.g. more severe at the base), `alpha`
can be expressed as a function of `z` directly inside the law string:

```python
fck = 30.0

# Example: linear degradation from 1.0 at z=0 to 0.60 at z=L
section_field.set_weight_laws([
    "concrete,concrete : (((1.0 - 0.40 * z / L) * fck + 8) / (fck + 8)) ** 0.3",
])
```

Or using `w0` and `w1` if the boundary weight values are already known:

```python
section_field.set_weight_laws([
    "concrete,concrete : w0 + (w1 - w0) * (z / L)",
])
```

This last form is the linear default — it bypasses the EC2 formula and
interpolates directly between the two boundary modulus ratios.

---

## 5. Case C — data-driven degradation from external file

If `alpha(z)` comes from an inspection campaign or a corrosion model,
it can be stored in a lookup file and consumed via `E_lookup`:

```txt
# alpha_profile.txt  (key = z in meters)
0.0   1.00
2.0   0.92
5.0   0.80
8.0   0.72
10.0  0.65
```

```python
fck = 30.0

section_field.set_weight_laws([
    "concrete,concrete : ((E_lookup('alpha_profile.txt') * fck + 8) / (fck + 8)) ** 0.3",
])
```

Here `E_lookup('alpha_profile.txt')` returns `alpha(z)` at the current
integration point, and the EC2 formula is applied directly.

---

## 6. Summary

The derivation is a direct substitution:

1. Take the EC2 modulus ratio formula:
   `w = ((alpha * fck + 8) / (fck + 8)) ** 0.3`

2. Decide how `alpha` varies along z (constant, linear, or data-driven).

3. Write `alpha` as a function of the CSF variables (`z`, `L`, `w0`, `w1`,
   or `E_lookup`) and substitute into the formula string.

4. Pass the string to `set_weight_laws()`.

The formula string is a standard Python expression evaluated by CSF
at each integration station along the member.

