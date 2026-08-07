# DRAFT
# CSF Global Chord-Equilibrium Formulation

## 1. Purpose

This note defines a global equilibrium formulation for recovering the **mean shear stress on a section chord** from a Continuous Section Field (CSF).

The formulation is based on the continuous availability of the complete section

```math
\mathrm{Section}(z)
```

at every longitudinal coordinate \(z\).

The formulation is **global**: it does not construct the shear result by adding separate correction terms for taper, moving boundaries, centroid variation, inertia variation, material variation, or other non-prismatic effects.

Instead, the complete longitudinal normal-stress state is evaluated on the actual section at each \(z\), integrated over the actual geometry, and differentiated only at the level of a physical resultant.

```math
\boxed{
\mathrm{Section}(z)
\rightarrow
\sigma_{zz}(x,y,z)
\rightarrow
SN(y,z)
\rightarrow
N^{+}(y,z)
\rightarrow
q(y,z)
\rightarrow
\bar{\tau}_{yz}(y,z)
}
```

---

## 2. Mechanical basis

At each longitudinal coordinate \(z\), CSF provides the actual section

```math
\mathrm{Section}(z).
```

The section actions are

```math
N(z), \qquad M_x(z), \qquad M_y(z).
```

Using the adopted Navier formulation, these define the complete longitudinal normal-stress field

```math
\boxed{
\sigma_{zz}(x,y,z)
}
```

over the actual cross-sectional domain

```math
\Omega(z).
```

Conceptually,

```math
\boxed{
\left[
\mathrm{Section}(z),
N(z),
M_x(z),
M_y(z)
\right]
\rightarrow
\sigma_{zz}(x,y,z)
}
```

All geometric and material information required by the adopted Navier formulation is taken directly from the actual `Section(z)`.

No additional kinematic hypothesis is introduced by the chord-equilibrium construction.

---

## 3. Navier chord state: \(SN(y,z)\)

Consider the horizontal chord

```math
Y=y
```

of the section at longitudinal coordinate \(z\).

The **Navier chord state**

```math
\boxed{
SN(y,z)
}
```

is the restriction of the complete Navier section state to the actual intersection between the line \(Y=y\) and `Section(z)`.

For each physical chord segment \(s\), \(SN(y,z)\) contains at least

```math
x_s^{-}(y,z),
\qquad
x_s^{+}(y,z),
\qquad
L_s(y,z),
```

together with the polygon identity and the corresponding longitudinal stress law

```math
\sigma_{zz,s}(x,y,z).
```

The total geometric chord length is

```math
\boxed{
L(y,z)
=
\sum_{s\in SN(y,z)} L_s(y,z)
}
```

with

```math
L_s(y,z)=x_s^{+}(y,z)-x_s^{-}(y,z).
```

If the chord crosses disconnected parts of the section, all physical segments are retained separately.

---

## 4. Longitudinal force carried by one chord

For a fixed chord coordinate \(y\),

```math
\boxed{
F_N(y,z)
=
\sum_{s\in SN(y,z)}
\int_{x_s^-}^{x_s^+}
\sigma_{zz,s}(x,y,z)\,dx
}
```

is the longitudinal normal-force contribution per unit vertical coordinate carried by the complete chord.

For an affine Navier stress field inside a polygon segment,

```math
\int_{x_s^-}^{x_s^+}
\sigma_{zz,s}(x,y,z)\,dx
=
L_s
\frac{
\sigma_{zz,s}(x_s^-,y,z)
+
\sigma_{zz,s}(x_s^+,y,z)
}{2}.
```

---

## 5. Longitudinal resultant above a chord

For a selected chord \(Y=y\), define the portion of the section above the chord as

```math
\Omega^{+}(y,z).
```

The longitudinal resultant carried by that portion is

```math
\boxed{
N^{+}(y,z)
=
\int_{\Omega^{+}(y,z)}
\sigma_{zz}(x,\eta,z)\,dA
}
```

or, using the chord-state notation explicitly,

```math
\boxed{
N^{+}(y,z)
=
\int_y^{y_{\max}(z)}
\left[
\sum_{s\in SN(\eta,z)}
\int_{x_s^-(\eta,z)}^{x_s^+(\eta,z)}
\sigma_{zz,s}(x,\eta,z)\,dx
\right]d\eta
}
```

Define

```math
g(\eta,z)
=
\sum_{s\in SN(\eta,z)}
\int_{x_s^-(\eta,z)}^{x_s^+(\eta,z)}
\sigma_{zz,s}(x,\eta,z)\,dx.
```

Then

```math
\boxed{
N^{+}(y,z)
=
\int_y^{y_{\max}(z)}
g(\eta,z)\,d\eta
}
```

with \(g(\eta,z)=F_N(\eta,z)\).

Both the stress field and the integration domain depend on \(z\).

---

## 6. Global equilibrium

The longitudinal equilibrium of \(\Omega^{+}(y,z)\) gives the shear flow transmitted through the chord:

```math
\boxed{
q(y,z)
=
-
\frac{\partial N^{+}(y,z)}{\partial z}
}
```

where the sign depends on the adopted conventions.

Physically,

```math
\boxed{
q(y,z)
=
\int_{C(y,z)}
\tau_{yz}(s)\,ds
}
```

and

```math
[q]
=
\frac{\mathrm{force}}{\mathrm{length}}.
```

The derivative is taken on the **complete physical resultant** \(N^{+}(y,z)\).

No decomposition into separate centroid, inertia, material, action-derivative, or taper terms is required.

---

## 7. Leibniz expansion of the global derivative

The global formulation above is sufficient by itself.

Expanding the derivative with Leibniz's rule shows explicitly why it already contains the geometric moving-boundary contributions of a varying section.

### 7.1 Moving upper boundary

Starting from

```math
N^{+}(y,z)
=
\int_y^{y_{\max}(z)}
g(\eta,z)\,d\eta,
```

the lower limit \(y\) is fixed with respect to \(z\), while \(y_{\max}(z)\) may vary.

Therefore,

```math
\boxed{
\frac{\partial N^{+}}{\partial z}
=
\int_y^{y_{\max}(z)}
\frac{\partial g}{\partial z}(\eta,z)\,d\eta
+
g(y_{\max}(z),z)
\frac{dy_{\max}}{dz}
}
```

The second term is the contribution generated by the moving upper boundary.

If the upper boundary is a vertex and the local chord length tends to zero,

```math
g(y_{\max}(z),z)=0,
```

so this term vanishes automatically.

### 7.2 Moving lateral boundaries of each chord segment

For each segment \(s\),

```math
g_s(\eta,z)
=
\int_{x_s^-(\eta,z)}^{x_s^+(\eta,z)}
\sigma_{zz,s}(x,\eta,z)\,dx.
```

A second application of Leibniz's rule gives

```math
\boxed{
\frac{\partial g_s}{\partial z}
=
\int_{x_s^-}^{x_s^+}
\frac{\partial \sigma_{zz,s}}{\partial z}\,dx
+
\sigma_{zz,s}(x_s^+,\eta,z)
\frac{\partial x_s^+}{\partial z}
-
\sigma_{zz,s}(x_s^-,\eta,z)
\frac{\partial x_s^-}{\partial z}
}
```

Summing over all segments gives the complete derivative of \(g\).

---

## 8. Expanded form

Combining the two Leibniz steps,

```math
\boxed{
\begin{aligned}
\frac{\partial N^{+}}{\partial z}
={}&
\int_y^{y_{\max}(z)}
\sum_s
\int_{x_s^-}^{x_s^+}
\frac{\partial \sigma_{zz,s}}{\partial z}
\,dx\,d\eta
\\
&+
\int_y^{y_{\max}(z)}
\sum_s
\left[
\sigma_{zz,s}^{+}
\frac{\partial x_s^{+}}{\partial z}
-
\sigma_{zz,s}^{-}
\frac{\partial x_s^{-}}{\partial z}
\right]d\eta
\\
&+
g(y_{\max}(z),z)
\frac{dy_{\max}}{dz}.
\end{aligned}
}
```

where

```math
\sigma_{zz,s}^{+}
=
\sigma_{zz,s}(x_s^+,\eta,z),
\qquad
\sigma_{zz,s}^{-}
=
\sigma_{zz,s}(x_s^-,\eta,z).
```

The three terms represent:

1. variation of the complete Navier stress field on the instantaneous geometry;
2. migration of the lateral boundaries of the chord segments;
3. migration of the upper boundary of the integrated section portion.

The last two are moving-boundary contributions of the type commonly associated with non-prismatic or Resal effects.

They are **not additional correction terms** introduced into the CSF formulation. They appear only when the single global derivative is expanded analytically.

```math
\boxed{
\text{global derivative}
\equiv
\text{stress-state variation}
+
\text{moving-boundary contributions}
}
```

---

## 9. Internal moving interfaces

If two adjacent segments share a moving interface \(x_i(z)\), the two associated boundary terms combine as

```math
\boxed{
\left(
\sigma_{zz,L}
-
\sigma_{zz,R}
\right)
\frac{dx_i}{dz}
}
```

Therefore:

- if the interface is only an artificial subdivision of the same continuous stress field, the two stresses coincide and the term cancels;
- if the interface separates regions with different longitudinal stress states, the contribution generally does not cancel.

Thus a true moving material or participation boundary can modify the longitudinal resultant.

---

## 10. Numerical evaluation

The global formulation does not require the expanded Leibniz expression to be evaluated term by term.

A natural numerical implementation is

```math
\boxed{
\frac{\partial N^{+}(y,z)}{\partial z}
\approx
\frac{
N^{+}(y,z+\Delta z)
-
N^{+}(y,z-\Delta z)
}{
2\Delta z
}
}
```

with each resultant independently evaluated on its corresponding actual section:

```math
\mathrm{Section}(z-\Delta z),
\qquad
\mathrm{Section}(z+\Delta z).
```

The Leibniz expansion provides the analytical interpretation of what is already contained in this global derivative.

---

## 11. Mean shear stress on the chord

The **mean shear stress on the complete chord** is defined by

```math
q(y,z)
=
\bar{\tau}_{yz}(y,z)L(y,z).
```

Therefore,

```math
\boxed{
\bar{\tau}_{yz}(y,z)
=
\frac{q(y,z)}{L(y,z)}
}
```

and

```math
\boxed{
\bar{\tau}_{yz}(y,z)
=
-
\frac{1}{L(y,z)}
\frac{\partial N^{+}(y,z)}{\partial z}
}
```

This satisfies

```math
\boxed{
\int_{C(y,z)}
\tau_{yz}(s)\,ds
=
\bar{\tau}_{yz}(y,z)L(y,z)
=
q(y,z)
}
```

without assuming that the true local shear stress is uniform along the chord.

---

## 12. Why the formulation is naturally non-prismatic

The non-prismatic character follows directly from the continuous section field

```math
\boxed{
z
\mapsto
\mathrm{Section}(z)
}
```

At different \(z\), the polygon geometry, chord topology, centroid, section inertias, material participation, stress distribution, internal interfaces, and the domain \(\Omega^{+}(y,z)\) may all change.

These effects are already contained when the complete section state is recomputed at each \(z\).

Thus the formulation is not

```math
\text{classical Jourawski}
+
\text{taper correction}
+
\text{material correction}
+
\text{centroid correction}
+\cdots
```

but

```math
\boxed{
\text{complete section state}
\rightarrow
\text{complete longitudinal resultant}
\rightarrow
\text{equilibrium}
}
```

---

## 13. Present scope

The present formulation stops at the **mean shear stress on the complete chord**.

It does not yet determine the local distribution

```math
\tau_{yz}(s)
```

among individual chord segments or different materials.

That requires a separate local-equilibrium and/or compatibility treatment and should not be mixed into the global chord-equilibrium formulation unless its physical basis is established independently.

---

## 14. Compact statement

```math
\boxed{
N^{+}(y,z)
=
\int_{\Omega^{+}(y,z)}
\sigma_{zz}\,dA
}
```

```math
\boxed{
q(y,z)
=
-
\frac{\partial N^{+}(y,z)}{\partial z}
}
```

```math
\boxed{
\bar{\tau}_{yz}(y,z)
=
\frac{q(y,z)}{L(y,z)}
=
-
\frac{1}{L(y,z)}
\frac{\partial N^{+}(y,z)}{\partial z}
}
```

The continuous dependence of `Section(z)` on \(z\) makes geometry variation, material variation, and moving-boundary effects part of the same global equilibrium statement rather than separate correction terms.
