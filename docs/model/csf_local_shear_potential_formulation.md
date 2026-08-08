# DRAFT
# Local Shear-Stress Recovery from Longitudinal Navier Equilibrium in CSF

## 1. Purpose

This document describes the reduced local shear-stress formulation used with the
Continuous Section Field (CSF) representation

```math
\mathcal{S}(z).
```

At every longitudinal station $z$, CSF provides the actual polygonal section
geometry together with polygon-level axial-flexural and shear-torsional
participation fields.

The objective is to recover the local in-plane shear field

```math
\boldsymbol{\tau}(x,y,z)
=
\begin{bmatrix}
\tau_x(x,y,z)\\
\tau_y(x,y,z)
\end{bmatrix}
```

from the longitudinal variation of the complete Navier normal-stress field.

The central equations are

```math
\boxed{
\nabla_{xy}\!\cdot
\left(
G_{\mathrm{like}}\,\nabla_{xy}\phi
\right)
=
-\frac{\partial\sigma_{zz}}{\partial z}
}
```

and

```math
\boxed{
\boldsymbol{\tau}
=
G_{\mathrm{like}}\,\nabla_{xy}\phi.
}
```

The formulation is a **reduced sectional equilibrium closure**. It is not a
replacement for a general three-dimensional elasticity solution.

---

## 2. CSF sectional representation

The formulation relies on the fact that the complete section is available as a
continuous longitudinal object,

```math
z\longmapsto\mathcal{S}(z),
```

rather than through a small predefined set of geometric parameters.

This distinction is essential. The shear formulation does not need to know
whether the section changes because of height, width, centroid position,
polygon shape, material participation, or several simultaneous effects. Those
changes are already represented by $\mathcal{S}(z)$ and enter through the
resulting normal-stress field.

CSF keeps two participation mechanisms conceptually separate.

### 2.1 Axial-flexural participation: `weight`

The polygon-level `weight` field governs the contribution of each region to the
axial-flexural section properties and therefore to the Navier normal-stress
field.

At a station $z$, let the weighted section properties be

```math
A(z),\qquad
C_x(z),\qquad
C_y(z),\qquad
I_x(z),\qquad
I_y(z),\qquad
I_{xy}(z).
```

For a point $(x,y)$ belonging to polygon $p$, the Navier field is written as

```math
\sigma_{zz,p}(x,y,z)
=
w_p(z)
\left[
\frac{N}{A}
+b_x(x-C_x)
+b_y(y-C_y)
\right],
```

with

```math
D=I_xI_y-I_{xy}^2,
```

```math
b_x
=
\frac{M_yI_x-M_xI_{xy}}{D},
```

and

```math
b_y
=
\frac{M_xI_y-M_yI_{xy}}{D}.
```

Here $w_p(z)$ denotes the sampled polygon `weightabs`.

Thus the axial-flexural field enters the local shear formulation through

```math
\boxed{
\texttt{weight}
\;\longrightarrow\;
\sigma_{zz}
\;\longrightarrow\;
-\partial_z\sigma_{zz}
}
```

and not through an independently added taper correction.

### 2.2 Shear participation: `shear_weight`

The polygon-level `shear_weight` field enters the local closure through

```math
G_{\mathrm{like}}(x,y,z)
=
\texttt{shear\_weightabs}(x,y,z).
```

It does **not** generate the equilibrium source. The source is determined by
the longitudinal derivative of the complete Navier field.

Instead, `shear_weight` controls the local metric used to select one admissible
two-component shear field when equilibrium alone does not determine a unique
split between $\tau_x$ and $\tau_y$.

Schematically,

```math
\boxed{
\texttt{weight}
\rightarrow
\text{normal-stress source}
}
```

while

```math
\boxed{
\texttt{shear\_weight}
\rightarrow
\text{local shear-distribution metric}.
}
```

The two fields are therefore intentionally independent in the CSF
representation.

---

## 3. Longitudinal equilibrium

Neglecting body-force terms in the local $z$-direction equilibrium statement,

```math
\frac{\partial\sigma_{zx}}{\partial x}
+
\frac{\partial\sigma_{zy}}{\partial y}
+
\frac{\partial\sigma_{zz}}{\partial z}
=0.
```

Defining

```math
\tau_x=\sigma_{zx},
\qquad
\tau_y=\sigma_{zy},
```

gives

```math
\boxed{
\frac{\partial\tau_x}{\partial x}
+
\frac{\partial\tau_y}{\partial y}
=
-\frac{\partial\sigma_{zz}}{\partial z}
}
```

or

```math
\boxed{
\nabla_{xy}\cdot\boldsymbol{\tau}
=
s
}
```

with

```math
\boxed{
s(x,y,z)
=
-\frac{\partial\sigma_{zz}}{\partial z}.
}
```

This equilibrium equation is the mechanical source of the formulation.

---

## 4. Why the complete Navier derivative is used

The derivative is taken on the **complete Navier stress field**, not on separate
geometric or mechanical terms introduced after the fact.

At fixed global coordinates $(x,y)$,

```math
\left.
\frac{\partial\sigma_{zz}}{\partial z}
\right|_{x,y}
```

contains the longitudinal effect of all quantities that are represented in
$\mathcal{S}(z)$ and in the adopted Navier reconstruction, including:

- gradients of the section actions;
- continuous variation of polygon geometry;
- motion of the weighted centroid;
- variation of $I_x$, $I_y$, and $I_{xy}$;
- variation of polygon `weightabs`;
- continuous variation of occupied material regions, provided that the local
  sectional evolution remains differentiable over the longitudinal stencil.

For the current CSF sign convention,

```math
\boxed{
\frac{dM_x}{dz}=T_y,
\qquad
\frac{dM_y}{dz}=T_x
}
```

is used when neighbouring action states are constructed.

The current formulation requires

```math
\boxed{
\frac{dN}{dz}=0.
}
```

A non-zero scalar $dN/dz$ specifies only the variation of the total axial
resultant. It does not define the local distribution of the corresponding axial
body load, surface load, or transfer mechanism over the section. A local source
should therefore not be invented from $dN/dz$ alone.

The important point is that

```math
\boxed{
\frac{\partial\sigma_{zz}}{\partial z}
\text{ represents the combined longitudinal effect of the quantities already
contained in the CSF sectional model and the adopted normal-stress recovery.}
}
```

It should not be interpreted as containing physical effects that are absent
from that reduced model.

---

## 5. Eulerian longitudinal derivative

The longitudinal derivative is evaluated at fixed global $(x,y)$ coordinates.
It is therefore an Eulerian derivative of the stress field.

For an interior station,

```math
\left.
\frac{\partial\sigma_{zz}}{\partial z}
\right|_{x,y}
\approx
\frac{
\sigma_{zz}(x,y,z+\Delta z)
-
\sigma_{zz}(x,y,z-\Delta z)
}{2\Delta z}.
```

At the CSF endpoints, one-sided stencils can be used.

The same longitudinal description is used for the kinematics of moving
boundaries and interfaces. This keeps the stress source and the sectional
geometry evolution consistent with the same underlying field $\mathcal{S}(z)$.

---

## 6. Why equilibrium alone is not sufficient

The equation

```math
\nabla_{xy}\cdot\boldsymbol{\tau}=s
```

is one scalar equation for two unknown functions,

```math
\tau_x(x,y),
\qquad
\tau_y(x,y).
```

Therefore local longitudinal equilibrium does not generally determine a unique
two-component shear field.

An additional closure is required.

---

## 7. Scalar-potential closure

The local field is closed by requiring

```math
\boxed{
\boldsymbol{\tau}
=
G_{\mathrm{like}}\nabla\phi.
}
```

Substitution into longitudinal equilibrium gives

```math
\boxed{
\nabla\cdot
\left(
G_{\mathrm{like}}\nabla\phi
\right)
=
s
=
-\frac{\partial\sigma_{zz}}{\partial z}.
}
```

For piecewise constant `shear_weightabs`, this is an elliptic equation with a
piecewise constant coefficient.

### 7.1 Variational interpretation

The same field can be interpreted as the equilibrium-admissible field that
minimizes

```math
\boxed{
\Pi_\tau
=
\frac{1}{2}
\int_\Omega
\frac{
\tau_x^2+\tau_y^2
}{G_{\mathrm{like}}}
\,dA
}
```

subject to local equilibrium and the boundary/interface conditions.

If `shear_weightabs` is proportional to a physical shear modulus $G$, the
functional is proportional to complementary shear energy. If it is used as a
dimensionless CSF participation factor, it is interpreted as the corresponding
G-like distribution metric.

A common multiplicative scaling of $G_{\mathrm{like}}$ changes $\phi$ but not
the recovered $\boldsymbol{\tau}$; the relative spatial distribution of
$G_{\mathrm{like}}$ governs the closure.

---

## 8. Moving external boundaries

A non-prismatic polygon boundary changes position with $z$.

Let a point on the sectional boundary have in-plane velocity

```math
\mathbf{v}
=
\begin{bmatrix}
\dfrac{dx}{dz}\\[4pt]
\dfrac{dy}{dz}
\end{bmatrix},
```

and let

```math
\mathbf{n}
=
\begin{bmatrix}
n_x\\
n_y
\end{bmatrix}
```

be the outward unit normal in the section plane.

The normal velocity is

```math
v_n=\mathbf{v}\cdot\mathbf{n}.
```

For the three-dimensional surface generated by that moving sectional boundary,
the traction-free condition gives the reduced $z$-traction condition

```math
\boxed{
\boldsymbol{\tau}\cdot\mathbf{n}
=
\sigma_{zz}\,v_n.
}
```

This is not an empirical taper correction. It is the boundary term required by
equilibrium on the physical surface generated by the evolving section.

For a fixed boundary,

```math
v_n=0,
```

and therefore

```math
\boldsymbol{\tau}\cdot\mathbf{n}=0.
```

### 8.1 Classical slope term as a special case

For a lower horizontal boundary

```math
y=y_b(z),
```

with outward normal

```math
\mathbf{n}=(0,-1),
```

its normal velocity is

```math
v_n=-y_b'(z).
```

Hence

```math
-\tau_y
=
\sigma_{zz}(-y_b'),
```

or

```math
\boxed{
\tau_y
=
\sigma_{zz}\,y_b'(z).
}
```

Thus a classical explicit geometric-slope term of the form

```math
\text{boundary slope}\times\text{normal stress}
```

appears naturally as a special case of the general moving-boundary condition.
The general formulation does not need to introduce a predefined height
function $h(z)$ or its derivative as a separate correction term: the complete
section evolution is already supplied by $\mathcal{S}(z)$.

---

## 9. Moving material interfaces

Consider an internal interface shared by active regions $i$ and $j$.

For an interface with in-plane normal velocity $v_n$, continuity of the
three-dimensional $z$ traction gives

```math
\boxed{
\left(
\boldsymbol{\tau}_i
-
\boldsymbol{\tau}_j
\right)
\cdot\mathbf{n}
=
\left(
\sigma_{zz,i}
-
\sigma_{zz,j}
\right)v_n.
}
```

For a fixed interface,

```math
v_n=0,
```

and therefore

```math
\boxed{
\boldsymbol{\tau}_i\cdot\mathbf{n}
=
\boldsymbol{\tau}_j\cdot\mathbf{n}.
}
```

Thus the normal shear traction is continuous across a fixed material interface.

---

## 10. Occupied material regions

CSF permits nested polygons. Geometry must therefore be integrated over
**occupied material regions**, not over every gross polygon independently.

The occupied region of polygon $i$ is

```math
\boxed{
\Omega_i^{\mathrm{occ}}
=
\Omega_i
\setminus
\bigcup_{j\in\mathrm{children}(i)}
\Omega_j.
}
```

Only direct children are subtracted.

A region with negligible `weightabs` and negligible `shear_weightabs` behaves
as a void. A region that carries Navier normal stress but has no positive shear
carrier is incompatible with the present elliptic closure.

---

## 11. Weak form

Let

```math
s=-\frac{\partial\sigma_{zz}}{\partial z}.
```

The strong form in an active region is

```math
\nabla\cdot(G_{\mathrm{like}}\nabla\phi)=s.
```

Using a scalar test function $v$ and integrating by parts gives

```math
\int_\Omega
G_{\mathrm{like}}
\nabla\phi\cdot\nabla v
\,dA
=
\int_{\partial\Omega}
q_n v\,ds
-
\int_\Omega
s v\,dA,
```

where

```math
q_n=\boldsymbol{\tau}\cdot\mathbf{n}.
```

On moving external boundaries,

```math
q_n=\sigma_{zz}v_n.
```

On moving internal interfaces, the corresponding jump term is determined by

```math
\left(
\sigma_{zz,i}-\sigma_{zz,j}
\right)v_n.
```

---

## 12. Finite-element discretization of the potential

The occupied polygonal regions are triangulated and the scalar potential is
approximated with linear P1 triangular shape functions,

```math
\phi_h(x,y)
=
\sum_{a=1}^{3}
N_a(x,y)\,\phi_a.
```

Because $N_a$ is linear,

```math
\nabla N_a
=
\text{constant in each triangle},
```

so that

```math
\nabla\phi_h
=
\text{constant in each triangle}
```

and

```math
\boxed{
\boldsymbol{\tau}_h
=
G_{\mathrm{like}}\nabla\phi_h
}
```

is piecewise constant by triangle.

The elemental stiffness matrix is

```math
\boxed{
\mathbf{K}_e
=
\int_{\Omega_e}
G_{\mathrm{like}}
\mathbf{B}^T\mathbf{B}\,dA
}
```

and, for constant $G_{\mathrm{like}}$ in a P1 triangle,

```math
\mathbf{K}_e
=
G_{\mathrm{like}}A_e
\mathbf{B}^T\mathbf{B}.
```

The source contribution is

```math
\mathbf{f}_{s,e}
=
-\int_{\Omega_e}
s\,\mathbf{N}\,dA.
```

The important point is that the divergence equation is enforced in the weak
finite-element sense. It is not evaluated by directly differentiating a
piecewise-constant recovered shear field inside each triangle.

---

## 13. Pure-Neumann character, compatibility, and gauge

The local problem is Neumann-only. Therefore the potential is defined only up
to an additive constant in each connected active component.

For each component,

```math
\phi
\rightarrow
\phi+C
```

leaves the physical shear field unchanged.

A gauge condition is therefore required numerically, but the gauge has no
physical stress or resultant meaning.

The Neumann problem is solvable only if the source and the prescribed normal
flux are compatible. For one connected active domain,

```math
\boxed{
\int_\Omega s\,dA
=
\int_{\partial\Omega}q_n\,ds
}
```

with the corresponding interface contributions in a piecewise domain.

Because

```math
s=-\partial_z\sigma_{zz},
```

this compatibility condition is the local-PDE counterpart of longitudinal
force balance.

---

## 14. Recovered resultants

After solving the potential,

```math
\tau_x
=
G_{\mathrm{like}}\frac{\partial\phi}{\partial x},
\qquad
\tau_y
=
G_{\mathrm{like}}\frac{\partial\phi}{\partial y}.
```

The recovered sectional shear resultants are

```math
\boxed{
T_x^{\mathrm{rec}}
=
\int_\Omega\tau_x\,dA
}
```

and

```math
\boxed{
T_y^{\mathrm{rec}}
=
\int_\Omega\tau_y\,dA.
}
```

They are equilibrium diagnostics. The local field should not be rescaled simply
to force agreement with the prescribed resultants.

---

## 15. Validation structure

The local-potential solution and its validation should remain conceptually
separate.

### 15.1 Integral equilibrium

Four-Quadrant checks can be used as an independent integral-equilibrium test.
They are not required to generate the local potential solution and no
post-correction is applied from them.

Their purpose is to verify that derivatives of regional Navier resultants are
consistent with shear flows integrated from the already recovered local field.

### 15.2 Three-dimensional continuum verification

A stronger external verification is obtained by constructing a three-dimensional
continuum discretization from the **same CSF model** and solving it independently.

The distinction is:

```math
\boxed{
\text{same sectional representation}
\;\neq\;
\text{same mechanical or numerical formulation}.
}
```

The CSF potential formulation and the OpenSees 3D continuum solution may use the
same geometry and participation information sampled from

```math
\mathcal{S}(z),
```

while remaining independent in their governing formulation and discretization.

The relevant comparison is local, at the same physical points, between

```math
\sigma_{zz}^{\mathrm{CSF}}
\quad\text{and}\quad
\sigma_{zz}^{3D},
```

and between

```math
\boldsymbol{\tau}^{\mathrm{CSF}}
\quad\text{and}\quad
\boldsymbol{\tau}^{3D}.
```

Such a comparison validates the reduced formulation without using the 3D stress
solution to construct the CSF field.

---

## 16. Relationship with Jourawski and explicit non-prismatic corrections

Jourawski remains a separate recovery path.

The potential solution must not be interpreted as

```math
\tau
=
\tau_{\mathrm{Jourawski}}
+
\tau_{\mathrm{potential}}.
```

That would generally double-count equilibrium contributions.

The potential solver consumes the complete source

```math
-\partial_z\sigma_{zz}^{\mathrm{Navier}}
```

and returns the reduced-equilibrium shear field associated with that source and
with the imposed boundary/interface conditions.

For simple non-prismatic geometries, classical terms involving an explicit
geometric slope can reappear as special cases. For example, the moving-boundary
condition gives

```math
\tau_y
=
\sigma_{zz}\,y_b'(z)
```

on a moving horizontal face.

The distinction is therefore not that CSF eliminates the mechanics represented
by such terms. Rather, CSF does not need to introduce each geometric derivative
as a separate model-specific correction. The geometry is represented first by
$\mathcal{S}(z)$, and the required local equilibrium terms follow from the
longitudinal evolution of the resulting stress field and of the physical
boundaries.

This can be summarized as

```math
\boxed{
\mathcal{S}(z)
\longrightarrow
\sigma_{zz}(x,y,z)
\longrightarrow
-\partial_z\sigma_{zz}
\longrightarrow
\text{local shear equilibrium}.
}
```

---

## 17. Scope and limitations

The present formulation intentionally remains a reduced sectional model.

1. **Normal-stress source.**  The source is limited to effects represented in
   the adopted Navier field and in the CSF sectional representation.

2. **No arbitrary non-zero $dN/dz$ without a local axial-load model.**  A scalar
   axial resultant gradient is insufficient to define the local distribution of
   the corresponding axial source.

3. **Potential closure.**  The scalar-potential relation

   ```math
   \boldsymbol{\tau}=G_{\mathrm{like}}\nabla\phi
   ```

   is an additional modelling assumption beyond equilibrium.

4. **Reduced-dimensional character.**  The method does not reproduce every
   three-dimensional Poisson, warping, support, or through-width effect of a
   continuum solid.

5. **Positive active shear carrier.**  A stressed material region requires a
   positive active `shear_weightabs` for the present elliptic closure.

6. **Differentiable local section evolution.**  The longitudinal derivative and
   moving-boundary kinematics require a sufficiently regular local evolution of
   the sectional model over the differentiation stencil.

7. **Mesh-dependent local representation.**  With P1 triangles, the recovered
   shear field is piecewise constant and local values converge under mesh
   refinement.

---

## 18. Compact formulation

The complete reduced formulation can be condensed to

```math
\boxed{
\begin{aligned}
\sigma_{zz}
&=
\sigma_{zz}
\left[
\mathcal{S}(z),\texttt{weight},N,M_x,M_y
\right],\\[4pt]

s
&=
-\left.
\frac{\partial\sigma_{zz}}{\partial z}
\right|_{x,y},\\[4pt]

\nabla\cdot
\left(
G_{\mathrm{like}}\nabla\phi
\right)
&=
s,\\[4pt]

G_{\mathrm{like}}
&=
\texttt{shear\_weightabs},\\[4pt]

\boldsymbol{\tau}
&=
G_{\mathrm{like}}\nabla\phi,\\[4pt]

\boldsymbol{\tau}\cdot\mathbf{n}
&=
\sigma_{zz}v_n
\qquad
\text{on moving external boundaries},\\[4pt]

(\boldsymbol{\tau}_i-\boldsymbol{\tau}_j)\cdot\mathbf{n}
&=
(\sigma_{zz,i}-\sigma_{zz,j})v_n
\qquad
\text{on moving interfaces}.
\end{aligned}
}
```

The essential modelling sequence is therefore

```math
\boxed{
\mathcal{S}(z)
\rightarrow
\sigma_{zz}^{\mathrm{Navier}}
\rightarrow
-\partial_z\sigma_{zz}
\rightarrow
\phi
\rightarrow
\boldsymbol{\tau}.
}
```

The continuous CSF section is the common source of the normal-stress evolution
and of the moving boundary/interface kinematics. No additional empirical
non-prismatic shear term is required by the formulation.
