# Global Chord-Equilibrium Formulation for CSF

## 1. Purpose

This note defines a global equilibrium formulation for recovering the **mean shear stress on a section chord** from a Continuous Section Field (CSF).

The formulation is built around the continuous availability of the complete section

```math
\mathrm{Section}(z)
```
at any longitudinal coordinate $z$.

The key idea is to avoid decomposing the longitudinal variation into separate contributions such as:

- curvature derivatives;
- centroid derivatives;
- inertia derivatives;
- material derivatives;
- taper corrections;
- special non-prismatic terms.

Instead, the complete longitudinal normal-stress state is evaluated on the actual section available at each $z$, integrated over the actual geometry, and differentiated only at the level of a physical resultant.

The formulation therefore remains global:

```math
\text{section state}
\;\rightarrow\;
\text{longitudinal resultant}
\;\rightarrow\;
\text{equilibrium}
\;\rightarrow\;
\text{mean chord shear stress}.
```
It is not constructed as a sum of special correction terms.

---

## 2. Mechanical basis

The longitudinal normal stress is obtained from the adopted general Navier formulation.

The mechanical assumptions are therefore those already inherent in the Navier model itself. No additional kinematic hypothesis is introduced by the chord-equilibrium construction described here.

At each longitudinal coordinate $z$, the section is the actual CSF section:

```math
\mathrm{Section}(z).
```
The section actions are assumed available as functions of $z$, in particular:

```math
N(z), \qquad M_x(z), \qquad M_y(z).
```
These actions are section resultants and therefore do not depend on the chord coordinate $y$.

The Navier calculation uses the geometry and the axial-flexural material participation of the actual polygons present in $\mathrm{Section}(z)$.

---

## 3. The Navier chord state: $SN(y,z)$

Consider the horizontal chord

```math
Y=y
```
of the section at longitudinal coordinate $z$.

The **Navier chord state**

```math
\boxed{SN(y,z)}
```
is defined as the complete information required to describe the intersection of that chord with the actual section and the longitudinal Navier stress carried by every intersected segment.

For each chord segment $s$, $SN(y,z)$ contains at least:

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
It may also retain the native polygon data available from CSF, such as topology identifiers and material-participation quantities.

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
L_s(y,z)=x_s^{+}-x_s^{-}.
```
If the chord crosses disconnected parts of the section, all physical segments are retained separately in $SN(y,z)$.

No equivalent single rectangle, homogenized width, or flattened chord geometry is introduced.

---

## 4. Longitudinal force carried by one chord

For a fixed chord coordinate $y$, the longitudinal force contribution per unit height is obtained by summing the contributions of all chord segments:

```math
\boxed{
F_N(y,z)
=
\sum_{s\in SN(y,z)}
\int_{x_s^-}^{x_s^+}
\sigma_{zz,s}(x,y,z)\,dx
}
```
For a Navier field that is affine in $x$ inside a polygon segment, the integral over an individual segment can be evaluated exactly as

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
Thus the full chord contribution is obtained directly from the actual segment geometry and the actual Navier stress field.

---

## 5. Longitudinal resultant above a chord: $N^{+}(y,z)$

For a selected chord $Y=y$, define the portion of the section above the chord as

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
\int_{y}^{y_{\max}(z)}
\left[
\sum_{s\in SN(\eta,z)}
\int_{x_s^-}^{x_s^+}
\sigma_{zz,s}(x,\eta,z)\,dx
\right]
d\eta
}
```
This definition is central to the formulation.

At each $z$, $N^{+}(y,z)$ is recomputed on the **actual section geometry** and from the **actual Navier stress state**.

Therefore $N^{+}(y,z)$ depends on both:

```math
\sigma_{zz}(x,y,z)
```
and

```math
\Omega^{+}(y,z).
```
Consequently, when the section varies longitudinally, the variation of $N^{+}$ automatically includes both:

- the variation of the longitudinal stress field;
- the variation of the integration domain itself.

This is the point at which the continuous availability of $\mathrm{Section}(z)$ becomes essential.

---

## 6. Global equilibrium and chord shear flow

The longitudinal equilibrium of the portion $\Omega^{+}(y,z)$ gives the shear flow transmitted through the chord:

```math
\boxed{
q(y,z)
=
-
\frac{\partial N^{+}(y,z)}{\partial z}
}
```
where the sign depends on the adopted section-axis and stress-resultant conventions.

The physical meaning of $q(y,z)$ is

```math
\boxed{
q(y,z)
=
\int_{C(y,z)}
\tau_{yz}(s)\,ds
}
```
where $C(y,z)$ is the complete physical chord.

Its dimensions are

```math
[q]=\frac{\mathrm{force}}{\mathrm{length}}.
```
The derivative is taken on the **complete physical resultant** $N^{+}(y,z)$.

No decomposition is required into separate causes such as

```math
N'(z),\quad
M_x'(z),\quad
M_y'(z),\quad
C_x'(z),\quad
C_y'(z),\quad
I_x'(z),\quad
I_y'(z),
```
or explicit geometry/material correction terms.

All such effects are already contained in the change of the complete quantity $N^{+}(y,z)$.

For numerical evaluation, a central difference may be used:

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
with each value of $N^{+}$ evaluated independently from the corresponding actual section

```math
\mathrm{Section}(z-\Delta z),
\qquad
\mathrm{Section}(z+\Delta z).
```
---

## 7. Mean shear stress on the chord

The formulation does not require the local shear-stress distribution along the chord.

The **mean shear stress on the complete chord** is defined as the constant stress that produces the same shear flow $q(y,z)$:

```math
q(y,z)
=
\bar{\tau}_{yz}(y,z)\,L(y,z).
```
Therefore,

```math
\boxed{
\bar{\tau}_{yz}(y,z)
=
\frac{q(y,z)}{L(y,z)}
}
```
and, using the equilibrium expression,

```math
\boxed{
\bar{\tau}_{yz}(y,z)
=
-
\frac{1}{L(y,z)}
\frac{\partial N^{+}(y,z)}{\partial z}
}
```
This is the final mean-chord quantity of the present formulation.

It satisfies

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

## 8. Why the formulation is naturally non-prismatic

The formulation does not introduce a separate non-prismatic correction.

The non-prismatic behavior enters because

```math
\boxed{
z\mapsto \mathrm{Section}(z)
}
```
is continuous.

At different longitudinal coordinates, the following may all change:

- polygon geometry;
- chord length;
- chord topology;
- centroid position;
- section inertias;
- material participation;
- longitudinal normal-stress distribution;
- the domain $\Omega^{+}(y,z)$.

These changes are already represented when $SN(y,z)$ and $N^{+}(y,z)$ are recomputed from the actual $\mathrm{Section}(z)$.

Thus

```math
\frac{\partial N^{+}(y,z)}{\partial z}
```
is the derivative of a complete physical resultant over a longitudinally varying section, rather than the sum of separately derived special terms.

The formulation is therefore equally applicable, within the assumptions of the adopted Navier model, to:

- prismatic sections;
- non-prismatic sections;
- polygonal sections;
- heterogeneous sections;
- sections with longitudinally varying geometry;
- sections with longitudinally varying material participation.

---

## 9. Compact formulation

The complete chain is

```math
\boxed{
\mathrm{Section}(z)
\;\rightarrow\;
SN(y,z)
\;\rightarrow\;
N^{+}(y,z)
\;\rightarrow\;
q(y,z)
\;\rightarrow\;
\bar{\tau}_{yz}(y,z)
}
```
with

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
and

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
The formulation is global in the sense that equilibrium is applied to the complete longitudinal resultant of the actual section portion, rather than assembled from special correction terms.

---

## 10. Present scope

The present formulation intentionally stops at the **mean shear stress on the complete chord**.

It does not yet attempt to determine the local distribution

```math
\tau_{yz}(s)
```
among individual chord segments or different materials.

That would require a separate local-equilibrium or compatibility treatment and should not be introduced into the global formulation unless its physical basis is established independently.

The global formulation above should therefore be treated as complete at the level of the mean Jourawski-type chord stress.
