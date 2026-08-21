# CSF-CUF algebraic solution verification

## Purpose

After the augmented CSF-CUF linear system has been solved, the solver reports a
small set of descriptive quantities that allow the user to inspect the numerical
quality of the computed algebraic solution.

The verification is deliberately simple:

- no acceptance tolerance is applied;
- no PASS/FAIL status is produced;
- no residual value stops post-processing once a finite solution has been found.

A calculation is stopped only when a usable numerical solution cannot be
obtained, for example because the system is rank deficient, dimensions are
invalid, or non-finite values are present.

## Complete linear system

Let the complete augmented system be

$$
M x = d,
$$

where:

- $M$ is the complete augmented matrix;
- $x$ is the complete numerical solution vector;
- $d$ is the complete right-hand-side vector.

The verification uses the same complete matrix and right-hand side that were
passed to the linear solver.

## Residual of each equation

After solving the system, the solution $x$ is substituted back into every
linear equation.

The residual vector is

$$
r = Mx-d.
$$

Therefore, for equation $i$,

$$
r_i=(Mx-d)_i.
$$

There is one residual $r_i$ for every equation of the complete augmented
system. An exactly satisfied equation would have $r_i=0$. In floating-point
arithmetic, small nonzero residuals are normally present.

The residual signs are retained. No absolute value is applied.

## 1. Residual mean

For $n$ equations, the arithmetic mean of the residuals is

$$
\bar r = \frac{1}{n}\sum_{i=1}^{n} r_i.
$$

This quantity describes the average signed residual of the complete system.

## 2. Residual standard deviation

The population standard deviation of the residuals is

$$
\sigma_r =
\sqrt{
\frac{1}{n}
\sum_{i=1}^{n}(r_i-\bar r)^2
}.
$$

This quantity describes how widely the individual equation residuals are
spread around their mean.

## 3. Equation-term scale

For every active coefficient $M_{ij}$ of the assembled sparse matrix, the
corresponding term appearing in an equation is

$$
t_{ij}=M_{ij}x_j.
$$

All active $t_{ij}$ values from the complete augmented system are collected.
Their population standard deviation is

$$
\sigma_t = \operatorname{std}(t_{ij}).
$$

The solver reports $\sigma_t$ as the **equation-term scale**.

Only active coefficients of the assembled sparse matrix are included. Implicit
zero matrix coefficients are not equation terms and are therefore not included
in this statistic.

No absolute value, maximum, minimum, normalization ratio, or acceptance
threshold is used.

## Interpretation

The solver presents three descriptive values:

1. residual mean $\bar r$;
2. residual standard deviation $\sigma_r$;
3. equation-term scale $\sigma_t$.

The first two describe the residual population. The third gives the numerical
scale of the individual terms that form the solved equations.

The solver does not combine these quantities into another index and does not
compare them with a prescribed limit. Their interpretation is left to the user.

## Runtime output

The normal solver output has the form

```text
[3/4] solve complete
[verification] residual mean = ...
[verification] residual standard deviation = ...
[verification] equation-term scale = ...
```

The three quantities are descriptive verification data only. They do not
constitute a convergence gate.
