# DRAFT 
# Local Shear-Stress Recovery from Longitudinal Navier Equilibrium in CSF

## 1. Purpose

This document describes the local shear-stress formulation implemented in
`csf.polygon_stress.analyse_navier_local_shear_potential()`.

The formulation is intended for non-prismatic and longitudinally varying CSF
members whose cross-section is described continuously by

```math
\mathcal{S}(z).
```

At every station $z$, CSF provides the actual polygonal geometry together with
independent polygon-level participation fields for axial-flexural and
shear-torsional behaviour.

The objective of the present formulation is to recover a local in-plane shear
field

```math
\boldsymbol{\tau}(x,y,z)
=
\begin{bmatrix}
\tau_x(x,y,z)\\
\tau_y(x,y,z)
\end{bmatrix}
```

from the longitudinal variation of the complete Navier normal-stress field.

The central equation is

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

with

```math
\boxed{
\boldsymbol{\tau}
=
G_{\mathrm{like}}\,\nabla_{xy}\phi
}
```

where the local G-like coefficient is the CSF polygon quantity
`shear_weightabs`.

The formulation is a **reduced sectional equilibrium closure**. It is not a
replacement for a general three-dimensional elasticity solution.

---

## 2. CSF sectional fields

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

For a point $(x,y)$ belonging to polygon $p$, CSF evaluates

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

where

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

and not through an independently added taper term.

### 2.2 Shear participation: `shear_weight`

The polygon-level `shear_weight` field enters the local closure through

```math
G_{\mathrm{like}}(x,y,z)
=
\texttt{shear\_weightabs}(x,y,z).
```

It does **not** create the equilibrium source. The source is determined by the
longitudinal derivative of the complete Navier field.

Instead, `shear_weight` governs how a locally admissible shear field is selected
when more than one distribution of $(\tau_x,\tau_y)$ can satisfy the same
equilibrium information.

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
\text{local shear-distribution metric}
}
```

The two quantities are therefore intentionally independent in CSF.

---

## 3. Longitudinal equilibrium

Neglecting body-force terms in the local transverse equilibrium statement, the
$z$-direction equilibrium equation is

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

or, in compact form,

```math
\boxed{
\nabla_{xy}\cdot\boldsymbol{\tau}
=
s
}
```

with

```math
s(x,y,z)
=
-\frac{\partial\sigma_{zz}}{\partial z}.
```

This equation is the mechanical source of the new formulation.

---

## 4. Why the complete Navier derivative is used

The derivative is taken on the complete physical Navier stress, not on separate
terms introduced after the fact.

At fixed global coordinates $(x,y)$,

```math
\frac{\partial\sigma_{zz}}{\partial z}
```

contains, simultaneously:

- the gradients of the section actions;
- geometric variation of the polygons;
- motion of the weighted centroid;
- variation of $I_x$, $I_y$ and $I_{xy}$;
- variation of polygon `weightabs`;
- changes in occupied-region topology when applicable.

For the current CSF sign convention,

```math
\boxed{
\frac{dM_x}{dz}=T_y,
\qquad
\frac{dM_y}{dz}=T_x
}
```

is used when neighbouring action states are constructed.

The current public implementation requires

```math
\boxed{
\frac{dN}{dz}=0.
}
```

A non-zero scalar $dN/dz$ specifies only the variation of the total axial
resultant. It does not specify the local distribution of the corresponding
axial body load, surface load or transfer mechanism over the section. The code
therefore rejects non-zero `dN_dz` rather than inventing a local source.

---

## 5. Eulerian derivative at a fixed physical point

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

At the CSF endpoints, second-order one-sided stencils are used.

The same longitudinal stencil is also used to obtain boundary and interface
velocities. This is important because the stress source and the moving-domain
kinematics must represent the same local section evolution.

---

## 6. Why equilibrium alone is not sufficient in two dimensions

The local equation

```math
\nabla\cdot\boldsymbol{\tau}=s
```

is one scalar equation for two unknown components,

```math
\tau_x(x,y),\qquad \tau_y(x,y).
```

Therefore local equilibrium alone does not generally determine a unique shear
field.

This was exposed explicitly by the Four-Quadrant formulation.

---

## 7. Four-Quadrant equilibrium

For a fixed physical point $(x_0,y_0)$, divide the current section into four
regions:

```math
\Omega^{++}
=
\Omega\cap\{x\ge x_0,\ y\ge y_0\},
```

```math
\Omega^{-+}
=
\Omega\cap\{x<x_0,\ y\ge y_0\},
```

```math
\Omega^{--}
=
\Omega\cap\{x<x_0,\ y<y_0\},
```

```math
\Omega^{+-}
=
\Omega\cap\{x\ge x_0,\ y<y_0\}.
```

The corresponding Navier normal-force resultants are

```math
N^{\alpha\beta}(x_0,y_0,z)
=
\int_{\Omega^{\alpha\beta}(z)}
\sigma_{zz}(x,y,z)\,dA.
```

Define

```math
D_{++}=\frac{dN^{++}}{dz},\qquad
D_{-+}=\frac{dN^{-+}}{dz},
```

```math
D_{--}=\frac{dN^{--}}{dz},\qquad
D_{+-}=\frac{dN^{+-}}{dz}.
```

Now introduce four half-chord shear flows:

- $H_L$: integral of $\tau_y$ on the horizontal chord to the left of the point;
- $H_R$: integral of $\tau_y$ on the horizontal chord to the right;
- $V_B$: integral of $\tau_x$ on the vertical chord below the point;
- $V_T$: integral of $\tau_x$ on the vertical chord above the point.

Local equilibrium gives

```math
\boxed{
D_{++}=H_R+V_T
}
```

```math
\boxed{
D_{-+}=H_L-V_T
}
```

```math
\boxed{
D_{--}=-H_L-V_B
}
```

```math
\boxed{
D_{+-}=-H_R+V_B.
}
```

The total derivative satisfies

```math
D_{++}+D_{-+}+D_{--}+D_{+-}
=
\frac{dN}{dz}.
```

For the current formulation, $dN/dz=0$.

### 7.1 Rank deficiency

The four equations above are not independent. Their rank is three when total
axial equilibrium is satisfied.

Consequently, the Four-Quadrant resultants determine all integral equilibrium
information but leave exactly **one scalar degree of freedom** in the split
between horizontal and vertical shear flow.

For example,

```math
H_L+H_R
=
D_{++}+D_{-+}
=
\frac{dN^{+y}}{dz},
```

while

```math
V_T+V_B
=
D_{++}+D_{+-}
=
\frac{dN^{+x}}{dz}.
```

Four-Quadrant is therefore an exact integral-equilibrium framework, but not by
itself a unique local closure.

---

## 8. Local closure by a scalar potential

The missing local degree of freedom is closed by requiring

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

For piecewise constant `shear_weightabs`, this is an elliptic equation with
piecewise constant coefficient.

### 8.1 Variational interpretation

The same field can be interpreted as the admissible equilibrium field that
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

subject to the local equilibrium and boundary/interface constraints.

If `shear_weightabs` is proportional to the physical shear modulus $G$, this
functional is proportional to the complementary shear energy. If it is used as
a dimensionless CSF participation factor, it should be interpreted as the
corresponding G-like distribution metric. A common multiplicative scaling of
$G_{\mathrm{like}}$ changes $\phi$ but does not change the recovered
$\boldsymbol{\tau}$; the **relative spatial distribution** is what governs the
closure.

---

## 9. Mechanical role of `shear_weight`

The role of `shear_weight` must be distinguished from the role of `weight`.

The equilibrium source is

```math
s=-\partial_z\sigma_{zz},
```

and therefore originates from the axial-flexural field.

`shear_weight` enters only through

```math
\boldsymbol{\tau}
=G_{\mathrm{like}}\nabla\phi.
```

It controls the energetic preference among different equilibrium-admissible
local distributions.

A region with a relatively large $G_{\mathrm{like}}$ can carry a given shear
stress with a smaller potential gradient,

```math
\nabla\phi
=
\frac{\boldsymbol{\tau}}{G_{\mathrm{like}}}.
```

Conversely, a region with small positive $G_{\mathrm{like}}$ is relatively more
expensive in the complementary-energy metric.

### 9.1 Important special case: one-dimensional rectangular shear

Consider a rectangular section whose solution is independent of $x$ and for
which

```math
\tau_x=0,
\qquad
\tau_y=\tau_y(y).
```

Equilibrium reduces to

```math
\boxed{
\frac{d\tau_y}{dy}
=
-\frac{\partial\sigma_{zz}}{\partial z}.
}
```

Once one boundary traction is prescribed, $\tau_y(y)$ is already determined by
equilibrium. In that special situation, changing $G_{\mathrm{like}}$ mainly
changes the potential gradient,

```math
\frac{d\phi}{dy}
=
\frac{\tau_y}{G_{\mathrm{like}}},
```

rather than the physical $\tau_y$ distribution itself.

This is why the first direct 3D rectangular benchmark strongly validates the
complete Navier source and the moving-boundary equilibrium, but is not by itself
the strongest possible test of the role of `shear_weight` in selecting a
fully two-dimensional field.

The role of `shear_weight` becomes genuinely discriminating when both
$\tau_x$ and $\tau_y$ are active and multiple two-dimensional distributions
satisfy the same divergence constraint.

---

## 10. Moving external boundaries

A non-prismatic CSF polygon boundary changes position with $z$.

Let a point on the transverse boundary have in-plane velocity

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

This condition is not an optional taper correction. It is the boundary term
required by equilibrium on a moving physical boundary.

For a fixed boundary,

```math
v_n=0,
```

and therefore

```math
\boldsymbol{\tau}\cdot\mathbf{n}=0.
```

### 10.1 Example: moving lower horizontal face

For a lower boundary

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

This is exactly the lower-face traction condition previously obtained in the
analytical non-prismatic rectangular benchmark.

---

## 11. Moving material interfaces

Consider an internal interface shared by active regions $i$ and $j$.

For a moving interface with in-plane normal velocity $v_n$, continuity of the
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

and the equation reduces to

```math
\boxed{
\boldsymbol{\tau}_i\cdot\mathbf{n}
=
\boldsymbol{\tau}_j\cdot\mathbf{n}.
}
```

Thus normal shear traction is continuous across a fixed material interface.

The implementation checks interface velocity from both polygon descriptions.
Inconsistent interface kinematics raise an error rather than being silently
averaged.

---

## 12. Occupied-region topology

CSF permits nested polygons. Geometry must therefore be integrated over
**occupied material regions**, not over every gross polygon independently.

The adopted rule is

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

This is the same index-based containment rule used by the Four-Quadrant
integration. Polygon names are labels only and do not participate in structural
topology.

A region with negligible `weightabs` and negligible `shear_weightabs` behaves
as a true void. A region carrying Navier stress but having no positive shear
carrier is rejected because the elliptic local closure would be degenerate in
that region.

---

## 13. Weak form

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

On internal material interfaces, the corresponding jump term is assembled from

```math
\left(\sigma_{zz,i}-\sigma_{zz,j}\right)v_n.
```

---

## 14. Finite-element discretization of the potential

Each occupied polygonal region is constrained-triangulated and then uniformly
refined.

The scalar potential is approximated using linear P1 triangular shape
functions:

```math
\phi_h(x,y)
=
\sum_{a=1}^{3}
N_a(x,y)\,\phi_a
```

inside each triangle.

Because $N_a$ is linear,

```math
\nabla N_a=\text{constant in each triangle},
```

therefore

```math
\nabla\phi_h=\text{constant in each triangle}
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

which reduces, for a constant coefficient and P1 triangle, to

```math
\mathbf{K}_e
=
G_{\mathrm{like}}A_e
\mathbf{B}^T\mathbf{B}.
```

The source vector is

```math
\mathbf{f}_{s,e}
=
-\int_{\Omega_e}
s\,\mathbf{N}\,dA.
```

A three-point degree-2 triangle quadrature is used in the implementation.

---

## 15. Pure-Neumann character and gauge

The local problem is Neumann-only. Therefore the potential is defined only up
to an additive constant in each connected active component.

If there are $m$ disconnected components,

```math
\phi
\rightarrow
\phi+C_k
```

is arbitrary independently in every component $k$.

The implementation introduces one zero-mean gauge constraint per connected
component using Lagrange multipliers.

The resulting algebraic system has the saddle-point structure

```math
\begin{bmatrix}
\mathbf{K} & \mathbf{C}\\
\mathbf{C}^T & \mathbf{0}
\end{bmatrix}
\begin{bmatrix}
\boldsymbol{\phi}\\
\boldsymbol{\lambda}
\end{bmatrix}
=
\begin{bmatrix}
\mathbf{f}\\
\mathbf{0}
\end{bmatrix}.
```

The multipliers $\boldsymbol{\lambda}$ are numerical gauge quantities. They are
not physical stresses or section resultants.

---

## 16. Compatibility condition

A pure-Neumann problem is solvable only if the integrated source is compatible
with the prescribed normal flux.

For one connected active domain,

```math
\boxed{
\int_\Omega s\,dA
=
\int_{\partial\Omega}q_n\,ds
}
```

with additional interface contributions where required by the piecewise-domain
assembly.

Because

```math
s=-\partial_z\sigma_{zz},
```

this is the local-PDE counterpart of the global longitudinal-force balance.

The implementation reports global and per-component compatibility residuals
explicitly. The gauge is not used to hide an incompatible source/flux state.

---

## 17. Recovered section resultants

After solving,

```math
\tau_x=G_{\mathrm{like}}\frac{\partial\phi}{\partial x},
\qquad
\tau_y=G_{\mathrm{like}}\frac{\partial\phi}{\partial y}.
```

The recovered section shear resultants are

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

These are reported together with

```math
T_x^{\mathrm{rec}}-T_x
```

and

```math
T_y^{\mathrm{rec}}-T_y.
```

They are equilibrium diagnostics; the field is not rescaled to force their
agreement.

---

## 18. Four-Quadrant as an independent validation path

Four-Quadrant is not required to solve the potential problem.

When optional validation points $(x_0,y_0)$ are supplied, the already-computed
piecewise-constant shear field is integrated along the four half-chords:

```math
H_L,
\quad H_R,
\quad V_B,
\quad V_T.
```

These are then compared with the independent derivatives of the regional Navier
resultants:

```math
D_{++},\quad D_{-+},\quad D_{--},\quad D_{+-}.
```

The comparison is

```math
D_{++}
\stackrel{?}{=}
H_R+V_T,
```

```math
D_{-+}
\stackrel{?}{=}
H_L-V_T,
```

```math
D_{--}
\stackrel{?}{=}
-H_L-V_B,
```

```math
D_{+-}
\stackrel{?}{=}
-H_R+V_B.
```

No correction or projection is applied after this comparison.

Thus:

```math
\boxed{
\text{Four-Quadrant validates integral equilibrium}
}
```

while

```math
\boxed{
\text{the potential formulation supplies the local closure.}
}
```

---

## 19. Relationship with Jourawski

Jourawski remains a separate CSF recovery path.

The new potential formulation must not be interpreted as

```math
\tau
=
\tau_{\mathrm{Jourawski}}
+
\tau_{\mathrm{potential}}.
```

That would generally double-count equilibrium contributions.

The potential solver consumes the **complete** source

```math
-\partial_z\sigma_{zz}^{\mathrm{Navier}}
```

directly and returns the complete reduced-equilibrium shear field associated
with that source and the imposed moving-boundary/interface conditions.

In the special rectangular non-prismatic benchmark, it was verified that

```math
\tau_y^{\mathrm{potential}}
\approx
\tau_y^{\mathrm{Jourawski}}
+
\tau_y^{\mathrm{nonprismatic}},
```

where the right-hand side was obtained independently from the previously
derived analytical decomposition.

This equality is a validation result for that benchmark. The general algorithm
does not internally perform this decomposition.

---

## 20. Relationship with the earlier centroid-axis approximation

An earlier diagnostic approximation used

```math
\tau_x^{C}
=
\sigma_{zz,M}\frac{dC_x}{dz},
```

```math
\tau_y^{C}
=
\sigma_{zz,M}\frac{dC_y}{dz}.
```

That field captures only the projection associated with motion of the global
centroid axis.

The new formulation is fundamentally broader because

```math
-\partial_z\sigma_{zz}
```

differentiates the complete Navier field and therefore includes all relevant
section-property, geometry and participation variations simultaneously.

The centroid-axis field remains useful as a diagnostic approximation, but it is
not added to the potential solution.

---

## 21. Validation sequence

The formulation was introduced incrementally so each new level could be checked
without changing previously validated paths.

### 21.1 Navier refactor regression

The Navier state was centralized in shared internal helpers. Existing Navier
results and exception behaviour remained exactly unchanged.

### 21.2 Four-Quadrant conservation on a real nested section

For the degraded prestressed-concrete pole with 80 polygons and 16 direct
containment links, occupied-region Four-Quadrant integration gave a maximum
axial-resultant residual of approximately

```math
5.1\times10^{-7}\ \mathrm{N},
```

with a maximum relative residual of approximately

```math
4.5\times10^{-13}.
```

### 21.3 Rectangular analytical benchmark

For the varying-height, varying-participation rectangular section, the
Four-Quadrant derivative reproduced the independently derived complete
Jourawski plus non-prismatic field with a maximum relative error of order

```math
2.7\times10^{-9}.
```

This established that differentiation of the complete Navier resultant already
contains the classical action-gradient and non-prismatic contributions without
adding separate correction terms.

### 21.4 Two-component local potential check

An auxiliary state with both $T_x\neq0$ and $T_y\neq0$ was used so that both
$\tau_x$ and $\tau_y$ had to be recovered simultaneously.

The local potential field reproduced the independent expected fields to errors
of order

```math
10^{-5}\ \mathrm{Pa},
```

and satisfied all four local Four-Quadrant equations to approximately

```math
10^{-4}\ \mathrm{N/m}.
```

### 21.5 Oblique two-dimensional polygon

A genuinely oblique non-prismatic quadrilateral was then used with

```math
M_x\neq0,
\qquad
M_y\neq0,
\qquad
T_x\neq0,
\qquad
T_y\neq0,
```

and with all external boundaries moving.

The maximum relative Four-Quadrant error decreased under mesh refinement from
approximately

```math
0.354\%\rightarrow0.204\%\rightarrow0.100\%.
```

When the same benchmark was run directly through the core implementation, the
relative error decreased further with successive uniform refinements:

```math
1.079\%
\rightarrow
0.207\%
\rightarrow
0.0231\%
\rightarrow
0.0080\%.
```

This demonstrated convergence of the local horizontal/vertical shear split
selected by the potential closure.

---

## 22. First direct comparison with a 3D continuum FEM model

The first direct continuum validation uses a deliberately simple but
mechanically complete benchmark:

- simply supported beam;
- $L=10\ \mathrm{m}$;
- uniformly distributed load $q=20\ \mathrm{kN/m}$;
- rectangular section of constant width $b=0.30\ \mathrm{m}$;
- fixed top face $y=0.30\ \mathrm{m}$;
- lower face varying from $-0.30$ to $-0.70\ \mathrm{m}$;
- two material/participation regions separated at $y=0$;
- lower `weight` varying from $1.0$ to $0.45$;
- isotropic `shear_weight` law with $\nu=0.25$;
- comparison station $z=3\ \mathrm{m}$.

The prescribed beam actions at that station are

```math
N=0,
\qquad
M_x=210000\ \mathrm{N\,m},
\qquad
M_y=0,
```

```math
T_x=0,
\qquad
T_y=40000\ \mathrm{N}.
```

### 22.1 Independence of the 3D comparison

The CSF field is solved once using

```python
analyse_navier_local_shear_potential(
    section_field=field,
    z=3.0,
    N=0.0,
    Mx=210000.0,
    My=0.0,
    Tx=0.0,
    Ty=40000.0,
    dN_dz=0.0,
    dz=1.0e-4,
    mesh_refinements=7,
    validation_points=None,
)
```

No OpenSees quantity enters this calculation.

The continuum model uses OpenSees SSPbrick elements. The 3D stress components
are sampled at the SSPbrick integration points located at the same physical
station $z=3\ \mathrm{m}$.

The direct comparisons are

```math
\boxed{
\sigma_{zz}^{\mathrm{CSF}}(x_i,y_i)
\leftrightarrow
\sigma_{zz}^{3D}(x_i,y_i,z)
}
```

```math
\boxed{
\tau_x^{\mathrm{CSF}}(x_i,y_i)
\leftrightarrow
\tau_{zx}^{3D}(x_i,y_i,z)
}
```

and

```math
\boxed{
\tau_y^{\mathrm{CSF}}(x_i,y_i)
\leftrightarrow
\tau_{yz}^{3D}(x_i,y_i,z).
}
```

The primary comparison is therefore **local point-to-point**, not a
Four-Quadrant chord average.

### 22.2 Global shear resultant

For the combined refined 3D mesh,

```math
T_y^{3D}
=
40000.0000005\ \mathrm{N},
```

while the independent CSF potential solution gives

```math
T_y^{\mathrm{CSF}}
=
40000.0000044\ \mathrm{N}.
```

Thus

```math
\boxed{
T_y^{\mathrm{CSF}}
\simeq
T_y^{3D}
\simeq
40000\ \mathrm{N}
}
```

to numerical precision.

### 22.3 Local stress errors on the combined refined mesh

The area-weighted normalized errors are approximately

```math
\boxed{
\varepsilon_{L^2}(\sigma_{zz})
=0.144\%
}
```

```math
\boxed{
\varepsilon_{L^2}(\tau_y)
=0.493\%
}
```

and for the complete two-component shear vector,

```math
\boxed{
\varepsilon_{L^2}(\boldsymbol{\tau})
=0.505\%.
}
```

The maximum normalized $\tau_y$ error is approximately

```math
0.787\%.
```

No fitting, stress rescaling or action matching is applied to obtain these
values.

### 22.4 Residual three-dimensional effects

The reduced rectangular CSF solution is essentially independent of $x$ and
predicts

```math
\tau_x\approx0.
```

The refined 3D continuum solution retains a small but non-zero through-width
component. In the combined refined case,

```math
\max|\tau_{zx}^{3D}|
\approx
968\ \mathrm{Pa},
```

while

```math
\max|\tau_{yz}^{3D}|
\approx
3.05\times10^5\ \mathrm{Pa}.
```

Thus the secondary 3D shear component is only about

```math
0.32\%
```

of the dominant shear scale.

This residual three-dimensional structure explains why increasingly refined
SSPbrick fields need not converge pointwise to a strictly sectional,
$x$-invariant reduced field.

---

## 23. What the 3D benchmark validates

The direct SSPbrick comparison provides independent evidence for the chain

```math
\boxed{
\mathcal{S}(z),\ N,M_x,M_y,T_x,T_y
\rightarrow
\sigma_{zz}^{\mathrm{Navier}}
\rightarrow
-\partial_z\sigma_{zz}
\rightarrow
\phi
\rightarrow
\boldsymbol{\tau}
}
```

without deriving the CSF shear field from the 3D result.

For the rectangular benchmark, it strongly validates:

1. differentiation of the complete Navier field as the equilibrium source;
2. the moving-boundary traction condition;
3. recovery of the correct global shear resultant;
4. the local reduced shear distribution;
5. consistency with an independent three-dimensional continuum model.

It does **not**, by itself, prove that the scalar-potential closure is the exact
3D elasticity solution for every arbitrary section.

In particular, because the rectangular benchmark is nearly one-dimensional in
the section plane, it is not the strongest validation of the role of spatially
varying `shear_weight` in selecting between competing two-dimensional shear
paths. That role is exercised more directly by the oblique two-component
benchmarks.

---

## 24. API summary

The public core function is

```python
def analyse_navier_local_shear_potential(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
    Tx: float,
    Ty: float,
    *,
    dN_dz: float = 0.0,
    dz: float | None = None,
    mesh_refinements: int = 4,
    validation_points: tuple[tuple[float, float], ...] | None = None,
    compatibility_rtol: float = 1.0e-8,
    compatibility_atol: float = 1.0e-6,
) -> dict[str, object]:
    ...
```

The returned dictionary contains the following main blocks:

- `section`: station, actions and derivative metadata;
- `mesh`: node count, triangle count and connected components;
- `resultants`: recovered $T_x$, $T_y$ and their residuals;
- `equilibrium`: source/flux compatibility, linear-system residual and gauges;
- `triangles`: piecewise-constant $\tau_x$, $\tau_y$ and potential gradients;
- `validation`: optional Four-Quadrant comparisons.

`validation_points=None` means that Four-Quadrant is not used at all in that
run. This was the setting used for the direct OpenSees 3D benchmark.

---

## 25. Interpretation of the formulation

The formulation can be summarized in four distinct layers.

### Layer 1 -- axial-flexural state

```math
\boxed{
\texttt{weight}
\rightarrow
\sigma_{zz}^{\mathrm{Navier}}
}
```

### Layer 2 -- local longitudinal equilibrium

```math
\boxed{
\nabla\cdot\boldsymbol{\tau}
=
-\partial_z\sigma_{zz}
}
```

### Layer 3 -- local closure

```math
\boxed{
\boldsymbol{\tau}
=
\texttt{shear\_weightabs}\,\nabla\phi
}
```

### Layer 4 -- independent validation

```math
\boxed{
\text{Four-Quadrant}
\quad\text{and}\quad
\text{3D continuum FEM}
}
```

This separation is important. `weight` and `shear_weight` are not interchangeable,
and Four-Quadrant is not the algorithm used to generate the local shear field.

---

## 26. Current limitations

The present implementation intentionally retains the following limits.

1. **No non-zero `dN_dz` without a local axial-load model.**  
   A scalar axial resultant gradient is insufficient to define the local source.

2. **Reduced sectional model.**  
   The method does not reproduce every 3D Poisson, warping, support or
   through-width effect of a continuum solid.

3. **Positive active shear carrier.**  
   An active stressed material region requires positive `shear_weightabs` for
   the elliptic closure.

4. **Mesh-dependent local representation.**  
   With P1 triangles, the recovered shear field is piecewise constant and local
   point values converge with mesh refinement.

5. **Potential closure is a modelling assumption beyond equilibrium.**  
   Equilibrium and moving-boundary/interface conditions are mechanical balance
   requirements. The minimum-complementary-energy scalar-potential choice is the
   additional closure that makes the local two-component field unique.

---

## 27. Recommended validation hierarchy for future CSF examples

For a new non-prismatic section, the following hierarchy is recommended.

1. Verify Navier resultant reconstruction.
2. Verify local-potential Neumann compatibility.
3. Verify recovered $T_x$ and $T_y$.
4. Use Four-Quadrant points to verify the local H/V split.
5. Check convergence under potential-mesh refinement.
6. When possible, compare the same-point field with an independent 3D continuum
   model.
7. Distinguish residual 3D effects from actual failure of sectional equilibrium.

This sequence keeps equilibrium verification, closure verification and continuum
validation conceptually separate.

---

## 28. Compact formulation

The complete formulation can be condensed to

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
\qquad\text{on moving external boundaries},\\[4pt]

(\boldsymbol{\tau}_i-\boldsymbol{\tau}_j)\cdot\mathbf{n}
&=
(\sigma_{zz,i}-\sigma_{zz,j})v_n
\qquad\text{on moving interfaces}.
\end{aligned}
}
```

The formulation therefore uses the continuous CSF section itself as the source
of both the normal-stress evolution and the boundary/interface kinematics. No
additional empirical non-prismatic shear term is required.
