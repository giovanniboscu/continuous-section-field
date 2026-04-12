# CSF Analysis

To run the CSF analysis, execute:

```bash
python3 -m csf.CSFActions ipe600.yaml ipe600_actions.yaml
python3 -m csf.CSFActions mixedthin.yaml mixedthin_action.yaml
```

# Saint-Venant Torsional Contributions in CSF

## 1. Background

In Saint-Venant torsion theory, the torsional moment is written as:

`M_t = G * J * theta'`

where:
- `G` is the shear modulus
- `J` is the Saint-Venant torsional constant
- `theta'` is the twist per unit length

In CSF, mixed thin-walled sections may produce two distinct torsional contributions:

- `J_sv_wall` for open thin-walled walls
- `J_sv_cell` for closed thin-walled cells

These two quantities must be interpreted carefully.
CSF may sum them algebraically, but this does **not** imply mutual torsional interaction between the wall branch and the cell branch.

---

## 2. Elemental formulas

### 2.1 Thin open wall

For a slender rectangular wall strip:

`J_wall = b * t^3 / 3`

where:
- `b` is the wall length
- `t` is the wall thickness

### 2.2 Closed thin-walled cell

For a closed thin-walled cell:

`J_cell = 4 * A_m^2 / integral(ds / t)`

where:
- `A_m` is the area enclosed by the cell midline
- `t` is the wall thickness

For constant thickness, this reduces to:

`J_cell = 4 * A_m^2 * t / b_m`

where `b_m` is the midline perimeter.

---

## 3. Interpretation of additivity in CSF

When CSF reports:

`J_total = J_sv_cell + J_sv_wall`

this must be read as an **algebraic aggregation of separate modeled contributions**.

This interpretation is meaningful when the model assumes:

| # | Assumption | Meaning |
|---|---|---|
| H1 | No mutual torsional interaction is modeled between branches | The wall branch and the cell branch are evaluated separately |
| H2 | Same twist rate `theta'` is assumed | Contributions are referred to the same sectional twist measure |
| H3 | Open-wall contribution is evaluated with open thin-wall logic | No closed-cell circulation is assigned to that branch |
| H4 | Closed-cell contribution is evaluated with closed-cell logic | Bredt-type shear flow is assigned only to the cell branch |

All four assumptions belong to the **chosen modeling framework**.

---

## 4. What the sum means

The sum

`J_sv_cell + J_sv_wall`

means that CSF combines two torsional contributions computed from two different mechanical branches under a common twist rate.

It does **not** mean that:
- the open walls and the closed cell torsionally redistribute shear flow between each other,
- the reported sum is a fully coupled torsional solution for the physical section.

So the sum is legitimate **as a model-level aggregation**, not as proof of reciprocal torsional participation.

---

## 5. Practical implication for mixed sections

For a mixed section containing both `@wall` and `@cell` components, attention is required in reading the result.

- `J_sv_wall` represents the open-wall branch
- `J_sv_cell` represents the closed-cell branch
- their sum is the quantity reported by CSF when both branches are active

This is useful for didactic and modeling purposes, but the user must keep in mind that the two branches are computed separately and then aggregated.

---

## 6. Summary

```text
In CSF:

J_total = J_sv_cell + J_sv_wall

Interpretation:
- J_sv_cell  -> closed thin-walled cell contribution
- J_sv_wall  -> open thin-walled wall contribution

The sum is an algebraic combination of separate modeled contributions
under a common twist rate.

It must not be interpreted as mutual torsional interaction or
as a fully coupled torsional redistribution between the two branches.
```

---

## 7. References

- Timoshenko, S.P. and Goodier, J.N. — *Theory of Elasticity*
- Vlasov, V.Z. — *Thin-Walled Elastic Beams*
- Pilkey, W.D. — *Analysis and Design of Elastic Beams*
