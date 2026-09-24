# Numerical Equilibration in CSF-CUF

## Purpose

CSF-CUF applies numerical equilibration at solver level to improve the scaling of the assembled algebraic system before the linear solve.

The procedure acts only on the algebraic representation of the problem. It does **not** modify:

- the CSF geometry;
- the material law;
- the CUF cross-sectional expansion;
- the expansion order `N`;
- the longitudinal finite-element interpolation;
- the loads;
- the boundary conditions;
- the constraint definitions;
- the quadrature rules;
- the physical displacement field being approximated.

Its role is to reduce large scale differences among the equations and unknowns of the assembled system so that the numerical solver works on a better balanced matrix.

A typical case configuration is:

```yaml
solver:
  equilibration:
    iterations: 3
```

The parameter `iterations` controls the number of equilibration passes performed before the final solve.

> Equilibration iterations are numerical scaling passes. They are not nonlinear iterations, load increments, Newton iterations, or iterations of the physical model.

---

## 1. Algebraic system solved by CSF-CUF

After assembly, an unconstrained linear CSF-CUF problem can be written as

```math
K q = f
```

where:

- `K` is the assembled stiffness matrix;
- `q` is the vector of global generalized CUF unknowns;
- `f` is the assembled load vector.

When constraints are enforced through an augmented system, the numerical solver may instead receive a KKT-type system of the form

```math
\begin{bmatrix}
K & C^T \\
C & 0
\end{bmatrix}
\begin{bmatrix}
q \\
\lambda
\end{bmatrix}
=
\begin{bmatrix}
f \\
g
\end{bmatrix}
```

In that case, equilibration acts on the complete assembled algebraic system that is passed to the linear solver. It does not redefine the constraints themselves.

For the remainder of this document, the generic notation

```math
A x = b
```

is used for either the standard stiffness system or the complete augmented system.

---

## 2. Why equilibration is useful in CSF-CUF

The CUF approximation can be enriched by increasing the cross-sectional order. As the approximation becomes richer, the global system contains contributions associated with basis functions of different orders and potentially very different numerical magnitudes.

This effect is especially relevant when several of the following are present at the same time:

- high CUF expansion order;
- different expansion families;
- heterogeneous material properties;
- non-prismatic geometry;
- strong stiffness contrasts;
- constraints or augmented equations;
- localized loads;
- large differences among generalized unknown scales.

The physical model may remain perfectly well defined while the assembled matrix becomes poorly scaled in floating-point arithmetic.

A poorly scaled matrix can lead to:

- stronger sensitivity to round-off;
- reduced numerical accuracy during factorization;
- less reliable pivots;
- larger forward error for the same residual level;
- stronger dependence of the computed solution on the numerical solver and scaling strategy.

Equilibration is introduced in CSF-CUF to reduce this algebraic sensitivity.

---

## 3. Numerical idea

Let the assembled system be

```math
A x = b
```

and introduce a diagonal scaling matrix

```math
D = \mathrm{diag}(d_1,d_2,\ldots,d_n)
```

A symmetric scaling can be written as

```math
\widetilde{A} = D A D
```

with the right-hand side transformed consistently,

```math
\widetilde{b} = D b
```

so that the scaled system becomes

```math
\widetilde{A}\,\widetilde{x} = \widetilde{b}
```

and the original variables are recovered consistently from the accumulated scaling.

The objective is not to change the equations represented by the system, but to present an algebraically equivalent system to the numerical solver with better balanced magnitudes.

Because the scaling is applied symmetrically, matrix symmetry is preserved when the original matrix is symmetric.

---

## 4. Iterative equilibration in CSF-CUF

CSF-CUF allows the scaling operation to be repeated several times.

At a conceptual level, one equilibration sequence is:

1. assemble the original algebraic system;
2. inspect the current matrix magnitudes;
3. compute a diagonal scaling for the current pass;
4. apply the scaling to matrix and right-hand side;
5. repeat for the requested number of passes;
6. solve the final equilibrated system;
7. recover the solution in the original variables.

If the scaling matrix computed at pass `k` is denoted by `D_k`, the accumulated scaling after `m` passes is

```math
D_{\mathrm{tot}} = D_1 D_2 \cdots D_m
```

and the final matrix can be represented conceptually as

```math
A_m = D_{\mathrm{tot}} A_0 D_{\mathrm{tot}}
```

with the right-hand side transformed consistently.

The repeated passes are useful because one scaling step may not be sufficient to balance a strongly heterogeneous high-order system.

---

## 5. Meaning of `solver.equilibration.iterations`

Example:

```yaml
solver:
  equilibration:
    iterations: 3
```

means that CSF-CUF performs three equilibration passes before the final linear solve.

This parameter is a **numerical solver parameter**.

It is not:

- a CUF approximation order;
- a mesh-refinement parameter;
- a material parameter;
- a load parameter;
- a convergence iteration of the structural model.

Two runs that differ only in `solver.equilibration.iterations` represent the same physical model but use different numerical scalings of the same assembled problem.

In exact arithmetic, equivalent scalings should lead to the same physical solution. In finite precision, differences can appear when the original system is sensitive to conditioning.

For this reason, a visible change in the final CSF-CUF response when the number of equilibration passes is changed should be interpreted as evidence of **numerical sensitivity of the algebraic solve**.

---

## 6. What equilibration changes

Equilibration changes the numerical scaling of the assembled equations.

It can affect:

- the magnitude distribution of matrix entries;
- the relative scale of rows and columns;
- the numerical condition of the system;
- the quality of the factorization;
- the effect of floating-point round-off;
- the final attainable solver accuracy.

These are numerical properties of the algebraic system.

---

## 7. What equilibration does not change

Equilibration does not redefine the CSF-CUF model.

It does not change:

- geometry;
- cross-section definition;
- material distribution;
- constitutive coefficients;
- CUF basis family;
- CUF order;
- longitudinal interpolation;
- longitudinal mesh;
- section quadrature;
- longitudinal quadrature;
- loads;
- supports;
- prescribed displacements;
- internal constraint definitions;
- reconstructed physical field `u(x,y,z)`.

The model is assembled first. Equilibration is applied afterward to the resulting algebraic problem.

This separation is important: **CSF-CUF modelling choices define the problem; equilibration only changes how that problem is numerically presented to the linear solver.**

---

## 8. Equilibration and the KKT system

When CSF-CUF uses an augmented system for constraints, the solver does not equilibrate only the structural stiffness block in isolation. The relevant numerical object is the complete system that is actually solved.

Using the generic KKT form

```math
\mathcal{K} =
\begin{bmatrix}
K & C^T \\
C & 0
\end{bmatrix}
```

the generic solve is

```math
\mathcal{K} z = r
```

with

```math
z =
\begin{bmatrix}
q \\
\lambda
\end{bmatrix}
```

and

```math
r =
\begin{bmatrix}
f \\
g
\end{bmatrix}
```

The same equilibration principle is then applied to `\mathcal{K}` as the assembled algebraic matrix.

This is important because the structural unknowns and constraint-related unknowns can naturally occur at very different numerical scales.

---

## 9. Why repeated equilibration can matter

A single scaling pass may reduce the largest scale differences but still leave residual imbalance in other rows and columns.

Repeated equilibration allows the scaling to be updated using the matrix produced by the previous pass.

For a difficult CSF-CUF system, this may progressively improve the balance seen by the solver.

However, the number of passes must not be interpreted as a monotonic accuracy parameter.

A larger value does not automatically mean a more accurate physical solution.

The useful range should be assessed numerically for the model under study.

---

## 10. Practical interpretation in CSF-CUF validation

When validating a high-order CSF-CUF case, it is useful to study two independent numerical directions:

```math
\text{CUF order} = N
```

and

```math
\text{equilibration passes} = m
```

The response can then be regarded as a numerical map

```math
R = R(N,m)
```

where `R` is any monitored quantity, for example:

- a displacement component;
- a maximum displacement;
- a stress component;
- a strain component;
- a section response;
- a pointwise reconstructed field value.

This separation is useful because changing `N` modifies the approximation space, whereas changing `m` modifies only the numerical scaling of the assembled system.

A stable result should ideally become insensitive to small changes in `m` once sufficient equilibration has been reached.

---

## 11. Recommended diagnostics

For high-order CSF-CUF runs, the following quantities are useful to record together with the physical outputs:

- expansion family;
- CUF order `N`;
- longitudinal element count;
- longitudinal interpolation order;
- equilibration pass count;
- matrix size;
- matrix nonzero count;
- KKT size when present;
- minimum scaling factor;
- maximum scaling factor;
- scaling dynamic range;
- matrix norm before equilibration;
- matrix norm after equilibration;
- residual norm;
- relative residual;
- selected displacement values;
- selected stress or strain values;
- maxima and their locations.

If a condition estimate is available, it should also be recorded before and after equilibration.

The objective is to distinguish three different effects:

1. approximation-order convergence;
2. solver sensitivity to matrix scaling;
3. local oscillatory behaviour of reconstructed or derived fields.

---

## 12. Displacements and derived quantities

A CSF-CUF solution can show stable global displacements while local strains or stresses remain more sensitive.

This is not contradictory.

Strains and stresses depend on spatial derivatives of the displacement approximation. Derivatives can amplify high-order local oscillations that may be almost invisible in the displacement field itself.

For this reason, equilibration studies should not be judged only from one global displacement value.

A robust check should include both:

- primary displacement quantities;
- local derived quantities such as strains and stresses.

---

## 13. Equilibration does not replace approximation control

Numerical equilibration addresses the conditioning and scaling of the algebraic system.

It does not replace choices related to approximation quality.

If a high-order result develops local oscillations, possible actions belong to a different level of the model, for example:

- reducing or changing the cross-sectional expansion order;
- changing the expansion family;
- refining the longitudinal discretization;
- using a more local section description;
- using a piecewise or spatially adapted approximation;
- refining the geometric or material representation where required.

These operations change the approximation or discretization. Equilibration does not.

---

## 14. Recommended CSF-CUF verification procedure

For a given benchmark:

### Step 1 - Keep the physical model fixed

Do not change:

- geometry;
- materials;
- loads;
- supports;
- constraint definitions;
- quadrature policy;
- longitudinal mesh.

### Step 2 - Vary the CUF order

Use a sequence such as

```math
N = 1,2,\ldots,N_{\max}
```

and observe the evolution of the physical response.

### Step 3 - Vary equilibration independently

For selected orders, vary

```math
m = \text{number of equilibration passes}
```

without changing any modelling parameter.

### Step 4 - Compare algebraic and physical indicators

Look for a region in which:

- residuals are consistently small;
- neighbouring values of `m` give essentially the same physical response;
- displacements are stable;
- local stresses and strains are stable enough for the intended use;
- the solution remains consistent with available reference data.

### Step 5 - Identify the onset of numerical sensitivity

If increasing `N` causes the solution to become increasingly sensitive to `m`, this is a useful indication that algebraic conditioning is becoming important for that particular model.

No universal CUF order threshold should be inferred from one benchmark.


---

## 15. Terminology used in CSF-CUF

The preferred term in the project documentation is:

**numerical equilibration**

A more descriptive expression is:

**iterative symmetric diagonal equilibration of the assembled algebraic system**

The procedure should not be described as a modification of the physical model.

It is also preferable not to assign a standard named algorithm unless the exact scale-factor update implemented in the code revision being documented has been verified directly from the source.

---

## 16. Summary

CSF-CUF separates the physical model from the numerical treatment of the resulting algebraic equations.

The modelling layer defines geometry, materials, loads, constraints, quadrature, CUF expansion, and longitudinal interpolation.

The solver then receives the assembled algebraic system.

Numerical equilibration acts at this final stage to improve matrix scaling before solution.

Its purpose is therefore precise:

**improve the numerical representation of the assembled CSF-CUF system without changing the CSF-CUF model that generated it.**
