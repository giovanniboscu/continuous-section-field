# Mixed Torsion Example in CSF  
## A Didactic, Science-of-Structures Style Case Study

## 1. Purpose of this example

This example is designed as a **teaching case** for torsion in mixed thin-walled cross-sections using CSF (Continuous Section Field).  
It is intentionally simple in geometry but rich in mechanics:

- open thin-walled components (`@wall@t=...`)
- closed thin-walled cell (`@cell@t=...`)
- linear section variation from **S0** to **S1**

The case is useful for showing, side by side, the two torsional quantities explicitly computed in this mixed setting:

- `J_sv_wall` for the open thin-walled branch
- `J_sv_cell` for the closed thin-walled branch

The central interpretive point is not the existence of a single generic torsional constant, but the need to understand how these two contributions are computed and combined.

---

## 2. Conceptual framework

### 2.1 Why different torsional formulas exist

In structural mechanics, torsional response depends strongly on cross-section topology and on the assumptions used for the model.

1. **Open thin-walled torsion**  
   For slender plate-like open walls, torsional stiffness is relatively low.  
   In classical thin-wall theory, the contribution typically scales with `b * t^3` at element level.

2. **Closed thin-walled torsion (Bredt–Batho)**  
   Closed cells develop a shear flow around the loop and therefore provide much higher torsional stiffness than open walls with comparable material amount.  
   For constant thickness,

   `J_cell = 4 * A_m^2 / ∫(ds / t)`

   and, if `t` is constant,

   `J_cell = 4 * A_m^2 * t / b_m`

where:
- `A_m` is the area enclosed by the cell midline
- `b_m` is the midline perimeter
- `t` is the wall thickness

---

## 3. CSF modeling language for this case

### 3.1 Tags used

- `@wall` → polygon contributes to the open thin-wall torsion branch
- `@cell` → polygon is interpreted as a closed-cell encoding
- `@t=<value>` → explicit thickness override

### 3.2 Why explicit `@t` is pedagogically useful

Using explicit thickness:

- removes ambiguity from automatic thickness estimators
- makes dimensional reasoning transparent
- allows controlled scaling studies
- keeps the comparison between `J_sv_wall` and `J_sv_cell` fully explicit

---

## 4. Geometry idea

The baseline mixed pattern contains:

- one left plate wall (`left_web@wall@t=...`)
- one right plate wall (`right_web@wall@t=...`)
- one centered closed box cell (`cell_box@cell@t=...`), encoded through outer and inner loops

Then `S1` is built as a scaled version of `S0`.

This produces a compact example in which open-wall and closed-cell torsion coexist in the same section description, while still remaining easy to inspect.

---

## 5. Interpretation of the torsional outputs

This example requires particular care in how `J_sv_wall` and `J_sv_cell` are interpreted.

CSF computes:

- `J_sv_wall` on the open thin-walled branch
- `J_sv_cell` on the closed-cell branch

CSF then sums these contributions.

However, this sum must be interpreted correctly:

> `J_sv_wall` and `J_sv_cell` are computed through distinct torsional paths based on different modeling assumptions.  
> Their sum in CSF is an algebraic combination of separate contributions.  
> It must **not** be interpreted as evidence of mutual torsional participation or reciprocal torsional redistribution between the open-wall branch and the closed-cell branch.

This is the main didactic message of the example.

---

## 6. Numerical results

The numerical values for this note should be updated only from a fresh rerun of the model.

For that reason, the previous numerical block is intentionally omitted here.

When the model is rerun, this section should report, at minimum, the following quantities at `z = 0` and `z = L`:

- `A`
- `Ix`
- `Iy`
- `J_sv_wall`
- `J_sv_cell`

A useful presentation format is a two-station comparison table with a short ratio analysis.

---

## 7. Why this example is useful for teaching

This single model allows students to see, in one place:

1. **Topology effect**: open versus closed torsional paths
2. **Modeling effect**: different torsional branches computed from different assumptions
3. **Scaling effect**: how geometry and thickness variation influence each branch
4. **Declarative modeling effect**: the mechanics follow explicit tags, not hidden profile recognition

It shows concretely that torsional interpretation depends on the branch being evaluated.

---

## 8. Important caution for documentation

## Do not merge the meanings of `J_sv_wall` and `J_sv_cell`

The two outputs are not interchangeable.

- `J_sv_wall` refers to the open thin-walled branch
- `J_sv_cell` refers to the closed thin-walled branch

In a mixed section, comparing their magnitudes can be informative, but identifying them as if they represented the same physical torsional mechanism is incorrect.

The fact that CSF sums them does not remove the distinction between the two underlying models.

---

## 9. Closed-cell encoding requirements in CSF

For `@cell` polygons encoded with a slit representation, ensure:

1. the outer loop is explicitly closed
2. the inner loop is explicitly closed
3. the loop areas are non-degenerate
4. explicit `@t=...` is provided when strict mode requires it

These conditions are especially important for robust didactic examples, because they keep the link between the declared geometry and the torsional interpretation clear.

---

## 10. Suggested book-style exercises

1. **Geometry-only scaling test**  
   Scale the coordinates by a factor `λ` while keeping `@t` fixed, then compare the changes in `J_sv_wall` and `J_sv_cell`.

2. **Geometry plus thickness scaling test**  
   Scale both the coordinates and `@t` by a factor `λ`, then compare the trends in the two torsional branches.

3. **Cell shape sensitivity test**  
   Replace the rectangular cell with a polygonal ring approximating a circle, and compare how `J_sv_cell` changes with the number of sides.

4. **Wall-to-cell balance study**  
   Modify the relative size of the walls and the cell and observe how the summed result changes while the two branches remain conceptually distinct.

---

## 11. Suggested order for documentation

Use this order in technical documentation:

1. **Physical assumptions** (`@wall` branch versus `@cell` branch)
2. **Tag syntax and strictness policy**
3. **Minimal mixed YAML**
4. **Numerical table at S0 and S1**
5. **Ratio analysis and scaling interpretation**
6. **Warning about non-interchangeability of `J_sv_wall` and `J_sv_cell`**
7. **Consistency checks**

---

## 12. Final takeaway

This example is a strong bridge between **classical structural torsion theory** and **declarative computational modeling in CSF**.

Its key lesson is precise:

> In a mixed torsion example, `J_sv_wall` and `J_sv_cell` must be read as distinct modeled contributions.  
> CSF sums them, but no reciprocal torsional participation between the two branches should be inferred from that sum.
