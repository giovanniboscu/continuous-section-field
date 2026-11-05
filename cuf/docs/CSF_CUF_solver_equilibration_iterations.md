# CSF-CUF solver: role of `equilibration.iterations`

> **GitHub rendering note:** display equations use fenced `math` blocks and inline equations use `$...$`, avoiding LaTeX macros that GitHub does not accept.

## 1. Purpose

The YAML block

```yaml
solver:
  correctionMITC: true
  verifyMITCAssembly: true
  equilibration:
    iterations: [1, 2, 3, 4, 5]
```

configures three distinct numerical aspects of the CSF-CUF solution procedure:

| Parameter | Role |
|---|---|
| `correctionMITC: true` | Enables the MITC correction used by the CUF formulation. |
| `verifyMITCAssembly: true` | Enables the numerical verification of the MITC-related assembly. |
| `equilibration.iterations` | Requests one or more matrix-equilibration levels before solving the assembled linear system. |

The parameter discussed in this document is:

```yaml
equilibration:
  iterations: [1, 2, 3, 4, 5]
```

Its purpose is **numerical scaling of the assembled algebraic system**. It does not change the beam model, the CUF kinematics, the CSF geometry, the material field, the loads, or the boundary conditions.

---

## 2. What the list `[1, 2, 3, 4, 5]` means

The list does **not** mean that one structural solution is progressively iterated five times until convergence.

Instead, the solver evaluates a family of solutions obtained after different numbers of equilibration sweeps:

```text
eq1  -> solve after 1 equilibration sweep
eq2  -> solve after 2 equilibration sweeps
eq3  -> solve after 3 equilibration sweeps
eq4  -> solve after 4 equilibration sweeps
eq5  -> solve after 5 equilibration sweeps
```

Therefore,

```yaml
iterations: [1, 2, 3, 4, 5]
```

requests **five separate numerical realizations of the same physical problem**.

The physical model is identical in every case. Only the amount of algebraic equilibration applied to the linear system changes.

This distinction is important:

```text
CUF model convergence       != matrix equilibration sensitivity
transverse-order convergence != matrix equilibration sensitivity
longitudinal refinement      != matrix equilibration sensitivity
stress recovery              != matrix equilibration
```

The `eq1`-`eq5` series is primarily a **numerical robustness and scaling check**.

---

## 3. Algebraic system before equilibration

After the CSF-CUF formulation has been assembled and the constraints have been introduced, the solver reaches a linear system of the form

```math
\mathbf{K}\mathbf{q}=\mathbf{f},
```

where:

- $\mathbf{K}$ is the global CUF stiffness matrix;
- $\mathbf{q}$ is the vector of generalized CUF degrees of freedom;
- $\mathbf{f}$ is the global load vector.

For high-order CUF approximations, different generalized coordinates can naturally have very different numerical scales. This may produce large differences between matrix coefficients and can make the algebraic system more sensitive to floating-point roundoff.

The problem becomes especially relevant when the model combines, for example:

- high transverse expansion order;
- different displacement components;
- derivatives of high-order basis functions;
- strongly non-uniform cross-sections;
- variable material fields;
- large differences among stiffness contributions;
- high-order longitudinal interpolation.

The role of equilibration is to reduce this numerical imbalance before the linear system is solved.

---

## 4. What an equilibration sweep does

An equilibration sweep computes scaling factors from the current matrix and applies them consistently to the algebraic system.

Conceptually, a diagonal scaling matrix can be written as

```math
\mathbf{D}=\mathrm{diag}(d_1,d_2,\ldots,d_n).
```

A symmetric scaling of the stiffness matrix has the form

```math
\widetilde{\mathbf{K}}
=
\mathbf{D}\,\mathbf{K}\,\mathbf{D},
```

with a corresponding transformation of the right-hand side and unknown vector.

The exact physical system is not altered by this transformation. The objective is to obtain a numerically better-scaled algebraic problem.

In the current CSF-CUF solver implementation, successive equilibration sweeps recompute scaling factors from the matrix produced by the previous sweep and apply the scaling symmetrically to rows and columns.

Thus an `eqN` solution corresponds to solving the system after **N successive equilibration sweeps**.

Schematically:

```text
Original assembled system
        |
        v
   equilibration #1 ----> eq1 solution
        |
        v
   equilibration #2 ----> eq2 solution
        |
        v
   equilibration #3 ----> eq3 solution
        |
        v
   equilibration #4 ----> eq4 solution
        |
        v
   equilibration #5 ----> eq5 solution
```

The transformation accumulated over several sweeps is tracked so that the solution can be mapped back to the original physical generalized coordinates.

---

## 5. Why more than one sweep can be useful

A single scaling pass can significantly reduce the largest scale differences in the matrix, but it does not necessarily make all rows and columns equally well balanced.

After the first transformation, the matrix has changed. A second sweep can therefore compute a new set of scaling factors from the already-scaled matrix.

The same argument applies to further sweeps.

The practical question is not whether five sweeps are intrinsically better than one. The useful question is:

> Does the computed physical solution remain invariant when the amount of matrix equilibration is changed?

This is why a list such as

```yaml
iterations: [1, 2, 3, 4, 5]
```

is particularly useful for validation and numerical diagnostics.

---

## 6. What should remain unchanged between `eq1` and `eq5`

In exact arithmetic, all equilibration levels represent the same original system and therefore the same physical solution.

Consequently, the following reconstructed quantities should remain essentially unchanged when moving from `eq1` to `eq5`:

- generalized displacements;
- physical displacement components $u_x,u_y,u_z$;
- strains;
- stresses;
- section resultants;
- reactions;
- derived response quantities.

Small differences are expected because the systems are solved in finite-precision arithmetic.

If the results are practically identical from `eq1` to `eq5`, the solution is numerically insensitive to the selected equilibration depth.

For example, a result such as

```text
eq1 ~= eq2 ~= eq3 ~= eq4 ~= eq5
```

for displacements and stresses is a useful indication that the physical response is not being selected by an arbitrary scaling choice.

This behavior has been observed in the CSF-CUF validation runs in which the `eq1`-`eq5` solutions produced essentially identical displacement fields, with differences at approximately floating-point numerical levels.

---

## 7. What a difference between equilibration levels means

If a response quantity changes appreciably between `eq1`, `eq2`, ..., `eq5`, the physical problem has not changed. The difference therefore indicates **numerical sensitivity of the algebraic solution**.

For example:

```text
eq1 -> u_z = -10.40 mm
eq2 -> u_z = -10.40 mm
eq3 -> u_z = -10.40 mm
```

is stable with respect to equilibration.

In contrast,

```text
eq1 -> u_z = -10.40 mm
eq2 -> u_z = -10.17 mm
eq3 -> u_z =  -9.81 mm
```

would indicate that the numerical solution is strongly dependent on algebraic scaling and therefore deserves further investigation.

Possible causes include:

- severe ill-conditioning;
- excessive transverse expansion order;
- nearly linearly dependent basis functions;
- large scale separation among generalized coordinates;
- poorly scaled constraints;
- insufficient numerical integration accuracy;
- a discretization that has reached a numerically unstable regime.

The equilibration series is therefore a **diagnostic of algebraic robustness**, not a substitute for physical or discretization convergence studies.

---

## 8. Equilibration is not a nonlinear iteration

The term `iterations` can be misleading if read outside the solver context.

Here it does not denote Newton-Raphson iterations, constitutive iterations, load increments, or iterations of the physical equilibrium equations.

The CSF-CUF static problem remains a linear structural problem of the form

```math
\mathbf{K}\mathbf{q}=\mathbf{f}.
```

The equilibration loop acts on the **numerical representation of this linear system**.

Therefore:

```text
iterations: [1,2,3,4,5]
```

must be interpreted as

```text
requested numbers of matrix-equilibration sweeps
```

and not as

```text
five iterations required to obtain the structural solution.
```

---

## 9. Equilibration is not stress equilibration

The word *equilibration* can also suggest equilibrium recovery of stresses. That is not its role here.

This solver option does not perform a post-processing correction such as

```math
\nabla\cdot\boldsymbol{\sigma}+\mathbf{b}=0
```

on the reconstructed stress field.

It does not smooth stresses and it does not impose local strong equilibrium after the CUF solution has been obtained.

The operation takes place at the algebraic solver level, before the final physical solution is reconstructed.

Hence:

```text
solver.equilibration.iterations
```

is a **matrix-scaling control**, not a stress-recovery control.

---

## 10. Equilibration is not a CUF-order convergence study

Suppose a transverse expansion is evaluated for several orders:

```text
N = 4, 6, 8, 10, 12, ...
```

and each order is solved using

```yaml
equilibration:
  iterations: [1, 2, 3, 4, 5]
```

Two independent numerical questions are then being investigated.

### 10.1 CUF-order convergence

This compares, for example,

```text
N4  vs N6  vs N8  vs N10 ...
```

and determines whether the transverse approximation is converging.

### 10.2 Equilibration sensitivity

This compares

```text
eq1 vs eq2 vs eq3 vs eq4 vs eq5
```

at a fixed CUF order and determines whether the numerical result is sensitive to matrix scaling.

These tests must not be mixed.

A solution can be:

- stable with respect to equilibration but not yet converged with respect to CUF order;
- converged with respect to CUF order but numerically sensitive to equilibration;
- stable in both senses;
- unstable in both senses.

---

## 11. Relationship with longitudinal refinement

The same distinction applies to longitudinal discretization.

Changing, for example,

```yaml
element_boundaries: [0.0, 0.1, 0.2, ..., 1.0]
```

changes the longitudinal approximation space and therefore changes the discrete physical model.

Changing

```yaml
iterations: [1, 2, 3, 4, 5]
```

does not change that approximation space.

It only changes how the same assembled algebraic system is scaled before solution.

Therefore the following are separate investigations:

| Test | What is changed | Main purpose |
|---|---|---|
| Transverse-order study | CUF transverse basis/order | Approximation convergence |
| Longitudinal refinement | Longitudinal elements/order | Approximation convergence |
| Quadrature refinement | Integration points/order | Integration accuracy |
| `eq1`-`eq5` comparison | Matrix scaling depth | Algebraic robustness |

---

## 12. Interaction with MITC options

The complete YAML block is

```yaml
solver:
  correctionMITC: true
  verifyMITCAssembly: true
  equilibration:
    iterations: [1, 2, 3, 4, 5]
```

These settings operate at different stages.

A useful conceptual sequence is:

```text
CSF geometry/material field
        |
        v
CUF kinematics and transverse expansion
        |
        v
longitudinal discretization
        |
        v
numerical integration
        |
        v
MITC-corrected term evaluation
        |
        v
MITC assembly verification
        |
        v
global K and f
        |
        v
matrix equilibration (eq1 ... eq5)
        |
        v
linear solution
        |
        v
back-transformation to physical CUF DOFs
        |
        v
reconstruction of u, strain and stress
```

Thus, `correctionMITC` changes how selected strain/stiffness terms are treated during formulation/assembly, while `equilibration.iterations` acts later on the already assembled algebraic system.

The two controls should therefore not be interpreted as different stages of the same correction algorithm.

---

## 13. Output interpretation

When several equilibration levels are requested, the run produces distinguishable results associated with the requested levels, conventionally identified as

```text
eq1
eq2
eq3
eq4
eq5
```

Typical case outputs use these labels in filenames, for example:

```text
..._eq1.cuf.npz
..._eq2.cuf.npz
...
..._eq5.cuf.npz
```

and textual response/diagnostic files such as

```text
response_eq1.txt
response_eq2.txt
...
response_eq5.txt
```

The `.cuf.npz` checkpoint contains the solved CUF state used by subsequent displacement, strain, and stress reconstruction.

Post-processing does not perform another matrix equilibration. It reconstructs the physical fields from the already solved checkpoint.

---

## 14. Residuals and the original system

A meaningful numerical verification must ultimately refer back to the original, unscaled structural equations.

Let $\mathbf{q}^{(m)}$ be the physical solution obtained after $m$ equilibration sweeps. The residual with respect to the original system is

```math
\mathbf{r}^{(m)}
=
\mathbf{K}\mathbf{q}^{(m)}-\mathbf{f}.
```

A normalized residual can then be defined, for example, as

```math
\eta_r^{(m)}
=
\frac{\|\mathbf{r}^{(m)}\|}
{\max\left(\|\mathbf{f}\|,1\right)}.
```

This is preferable to assessing only the residual of the scaled system, because the physical solution must satisfy the original equations.

The current solver diagnostics evaluate residuals after mapping the solution back to the original system. This is the correct reference for comparing `eq1`, `eq2`, ..., `eq5`.

A lower residual after a larger number of equilibration sweeps can indicate a numerically cleaner solve, but it does not by itself establish convergence of the CUF approximation.

---

## 15. Conditioning and what the current diagnostic does not prove

Matrix equilibration is intended to improve algebraic scaling and can often improve the numerical behavior of an ill-scaled system.

However, **equilibration is not identical to a condition-number calculation**.

A complete conditioning study would explicitly evaluate quantities such as

```math
\kappa(\mathbf{K})
=
\|\mathbf{K}\|\,\|\mathbf{K}^{-1}\|
```

or a reciprocal condition estimate before and after scaling.

In the current solver diagnostics, the fields labelled `original_rcond` and `equilibrated_rcond` are not used as an actual computed per-iteration condition-number history; they remain diagnostic placeholders rather than a quantitative conditioning measurement.

Consequently, the safest interpretation of the `eq1`-`eq5` comparison is empirical and direct:

1. compare physical solutions;
2. compare residuals against the original system;
3. verify that increasing the number of scaling sweeps does not materially alter the response.

This establishes **solution robustness with respect to equilibration** even when an explicit condition-number estimate is not available.

---

## 16. Recommended use in validation cases

For validation and research cases, the following configuration is useful:

```yaml
solver:
  correctionMITC: true
  verifyMITCAssembly: true
  equilibration:
    iterations: [1, 2, 3, 4, 5]
```

The recommended interpretation is:

### Step 1 - solve all requested equilibration levels

Obtain the `eq1`-`eq5` solutions.

### Step 2 - compare primary displacements

For example:

```text
u_x(eq1), ..., u_x(eq5)
u_y(eq1), ..., u_y(eq5)
u_z(eq1), ..., u_z(eq5)
```

### Step 3 - compare stress quantities

Stress fields are more sensitive because derivatives of the displacement approximation are involved. Therefore they are an important test of equilibration sensitivity.

### Step 4 - compare residual diagnostics

Check the residual of each physical solution against the original unscaled system.

### Step 5 - separate this result from approximation convergence

Only after equilibration sensitivity has been assessed should conclusions about transverse-order or longitudinal convergence be drawn from the corresponding discretization studies.

---

## 17. When `iterations: [1]` is sufficient

Once a class of models has demonstrated that

```text
eq1 ~= eq2 ~= eq3 ~= eq4 ~= eq5
```

for the quantities of interest, using only

```yaml
equilibration:
  iterations: [1]
```

can be sufficient for routine production runs of the same numerical regime.

The five-level configuration remains valuable for:

- new transverse expansions;
- very high CUF orders;
- strongly tapered members;
- highly graded materials;
- new constraint formulations;
- unusually large stiffness contrasts;
- cases showing oscillatory or unexpected displacement/stress behavior;
- formal validation studies.

---

## 18. When several equilibration levels should be retained

Keep

```yaml
iterations: [1, 2, 3, 4, 5]
```

when the objective is to demonstrate that the numerical result does not depend on the scaling procedure.

This is particularly useful in a research repository because it provides an internal reproducibility check:

> the same physical CUF problem is solved through several algebraically equivalent scaled systems, and the reconstructed physical response is compared across them.

Agreement among the solutions is therefore evidence of numerical robustness of the linear solve.

---

## 19. What `iterations` does not control

The parameter does **not** control any of the following:

| Quantity | Controlled by `equilibration.iterations`? |
|---|---:|
| CSF geometry | No |
| Material variation law | No |
| CUF transverse basis | No |
| CUF transverse order | No |
| Longitudinal finite-element order | No |
| Number of longitudinal elements | No |
| Section quadrature | No |
| Longitudinal Gauss quadrature | No |
| MITC activation | No |
| MITC assembly verification | No |
| Loads | No |
| Boundary conditions | No |
| Stress-recovery algorithm | No |
| Strong-equilibrium reconstruction | No |
| Physical nonlinear iterations | No |
| Matrix scaling depth | **Yes** |

---

## 20. Scientific interpretation

The most useful scientific interpretation of

```yaml
iterations: [1, 2, 3, 4, 5]
```

is the following:

> The same discrete CSF-CUF structural problem is solved after one through five successive matrix-equilibration sweeps. The resulting physical responses can be compared to quantify sensitivity of the linear solution to algebraic scaling. In exact arithmetic the solutions are equivalent; differences observed in finite precision measure numerical sensitivity rather than a change in the structural model.

This makes the parameter particularly useful in high-order CUF analyses, where the algebraic system may span very different numerical scales.

---

## 21. Recommended documentation wording

A concise description suitable for a YAML reference is:

```text
solver.equilibration.iterations
    List of matrix-equilibration sweep counts to evaluate before solving the
    assembled CUF system. Each value produces an algebraically equivalent
    solution of the same physical problem (e.g. eq1, eq2, ...). Comparing the
    resulting physical responses provides a numerical-sensitivity check with
    respect to matrix scaling. This parameter is not a nonlinear iteration count,
    a CUF convergence criterion, or a stress-equilibration procedure.
```

A shorter table entry can be written as:

| YAML key | Meaning |
|---|---|
| `solver.equilibration.iterations` | Number(s) of successive matrix-equilibration sweeps to test before solving. A list such as `[1,2,3,4,5]` generates the `eq1`-`eq5` family used to assess numerical sensitivity to algebraic scaling. |

---

## 22. Final summary

For

```yaml
solver:
  correctionMITC: true
  verifyMITCAssembly: true
  equilibration:
    iterations: [1, 2, 3, 4, 5]
```

the solver performs the same physical CSF-CUF analysis using five different equilibration depths.

The key points are:

1. `iterations` refers to **matrix-equilibration sweeps**.
2. `[1,2,3,4,5]` requests the `eq1`-`eq5` family of solutions.
3. The physical model is unchanged between these solutions.
4. Equilibration rescales the algebraic system to reduce numerical imbalance.
5. Successive sweeps recompute and apply scaling to the already-scaled system.
6. The physical solution is transformed back to the original CUF generalized coordinates.
7. Agreement among `eq1`-`eq5` is evidence of robustness with respect to algebraic scaling.
8. Differences among them indicate numerical sensitivity and should be investigated.
9. This test is independent of transverse-order convergence, longitudinal refinement, quadrature convergence, and MITC verification.
10. It is not a stress-equilibration procedure and not a nonlinear convergence loop.

The solver implementation is located in the CSF-CUF solver package:

[CSF-CUF solver source](https://github.com/giovanniboscu/continuous-section-field/tree/main/src/csf/cuf/solver)
