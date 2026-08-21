# CSF-CUF algebraic solution verification

## Purpose

After the augmented CSF-CUF linear system has been solved, the solver verifies
how closely the computed numerical solution satisfies the **complete system of
linear equations**.

This verification is descriptive. It does **not** apply an acceptance tolerance,
it does **not** produce a PASS/FAIL status, and it does **not** stop
post-processing because a residual exceeds a prescribed threshold.

A calculation is stopped only when a usable numerical solution cannot be
obtained, for example because the algebraic system is rank deficient or the
solver returns non-finite values.

## Complete algebraic system

Let the complete augmented system be

$$
M x = d,
$$

where:

- $M$ is the complete augmented matrix, including the structural equations and
  the linear constraints;
- $x$ is the complete numerical solution vector, including the primal unknowns
  and the Lagrange multipliers;
- $d$ is the complete right-hand-side vector.

The verification is performed independently for every equation, i.e. for every
row $i$ of the system.

## 1. Contribution of one unknown to one equation

For equation $i$ and unknown $j$, define

$$
t_{ij} = M_{ij} x_j,
$$

where:

- $M_{ij}$ is the coefficient in row $i$, column $j$ of the complete matrix;
- $x_j$ is the computed value of unknown $j$;
- $t_{ij}$ is the contribution of unknown $j$ to equation $i$.

## 2. Computed left-hand side of equation $i$

All contributions belonging to row $i$ are summed:

$$
L_i = \sum_j t_{ij}.
$$

$L_i$ is therefore the left-hand side obtained by substituting the computed
solution into equation $i$.

## 3. Algebraic disequilibrium of equation $i$

Let $d_i$ be the right-hand-side value of equation $i$.

The algebraic disequilibrium of that equation is

$$
r_i = L_i - d_i.
$$

An exactly satisfied equation would have $r_i=0$. In floating-point arithmetic,
a small nonzero value is generally expected.

## 4. Magnitude of the contributions in equation $i$

To measure the numerical size of the terms participating in the equation
without allowing positive and negative terms to cancel each other, define

$$
S_i = \sum_j |t_{ij}|.
$$

$S_i$ is the total magnitude of the left-hand-side contributions.

## 5. Scale of equation $i$

The scale of the complete equation is

$$
C_i = S_i + |d_i|.
$$

This represents the magnitude of the quantities actually involved in that row
before numerical cancellation is allowed to hide their size.

## 6. Relative algebraic disequilibrium of equation $i$

The relative algebraic disequilibrium is

$$
\eta_i = \frac{|r_i|}{C_i}.
$$

Equivalently,

$$
\eta_i =
\frac{
\left|\sum_j M_{ij}x_j-d_i\right|
}{
\sum_j |M_{ij}x_j|+|d_i|
}.
$$

If $C_i=0$ and $r_i=0$, the equation is identically satisfied and the solver
defines $\eta_i=0$.

No tolerance is applied to $\eta_i$. It is a numerical measure of how closely
that specific equation is satisfied relative to the magnitude of the terms
that form it.

## 7. Verification of the complete system

The calculation above is repeated for every equation:

$$
\eta_1,\eta_2,\ldots,\eta_m,
$$

where $m$ is the total number of equations in the augmented system.

The concise quantity presented by the solver is the largest value:

$$
\boxed{
\eta_{\max} = \max_i \eta_i
}
$$

Thus $\eta_{\max}$ is the relative algebraic disequilibrium of the equation that
closes worst in the complete solved system.

It is reported as a **verification quantity only**. The solver does not convert
it into a PASS/FAIL decision and does not compare it with a built-in acceptance
threshold.

## Runtime output

The normal solver output reports the result in the form

```text
[3/4] solve complete
[verification] maximum relative algebraic disequilibrium = 9.850000e-16
```

The value shown above is only an example of the output format.
